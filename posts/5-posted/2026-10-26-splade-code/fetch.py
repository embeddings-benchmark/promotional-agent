#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["mtebpost[leaderboard]", "mteb==2.24.10"]
#
# [tool.uv.sources]
# mtebpost = { path = "../../..", editable = true }
#
# [tool.uv]
# exclude-newer = "2026-10-13T00:00:00Z"
# ///
"""Evidence for the SPLADE-Code post. Run from the repo root:

    uv run posts/<stage>/splade-code/fetch.py

The post's numbers are on CoREB(v1); MTEB(Code, v1) is recomputed too, for the notes
(the models were trained on CoIR's training splits, which most of MTEB(Code, v1) is
built from, so it is not the board the post leans on — see post.md).

For both benchmarks:

1. **The live leaderboard API** gives every row with complete coverage (a null
   Mean (Task) is how the site marks partial coverage).
2. **`Benchmark.get_score()` on the results repo** recomputes Mean (Task) for every one
   of those models, after joining revisions and merging each model's entries into one
   (the leaderboard's view; see the pareto-tag post's fetch.py for why). Any score that
   differs from the site by more than SCORE_TOL is recorded, and fatal if it is a row
   the card shows.

Also answers "who is missing": of the top 20 complete MTEB(Code, v1) models (the
established code board), how many have complete CoREB(v1) results.
"""

import json
import pathlib
import urllib.parse
import urllib.request
import warnings
from datetime import date

warnings.filterwarnings("ignore")

import mteb  # noqa: E402

from mtebpost.cards import write_card_data  # noqa: E402

SUBJECTS = ["naver/splade-code-06B", "naver/splade-code-8B"]
BASELINE = "mteb/baseline-bm25s"
HEADLINE = "CoREB(v1)"
SECONDARY = "MTEB(Code, v1)"
API = "https://mteb-leaderboard-backend.hf.space/v1/benchmarks/{}/scores"
HERE = pathlib.Path(__file__).parent
CARD = HERE / "card-1-splade-code.html"
SCORE_TOL = 0.01
TOP_N = 10


def api_rows(name: str) -> tuple[str, list[dict]]:
    url = API.format(urllib.parse.quote(name))
    with urllib.request.urlopen(url) as r:
        return url, json.load(r)["rows"]


def recompute(bench, results, names: list[str]) -> dict[str, tuple[float | None, int, str]]:
    """name -> (Mean(Task) on 0-100, tasks covered, revisions joined)."""
    task_names = {t.metadata.name for t in bench.tasks}
    by_model: dict[str, list] = {}
    for mr in results.model_results:
        by_model.setdefault(mr.model_name, []).append(mr)
    out = {}
    for name in names:
        mrs = by_model.get(name, [])
        if not mrs:
            out[name] = (None, 0, "")
            continue
        trs = [tr for mr in mrs for tr in mr.task_results if tr.task_name in task_names]
        covered = {tr.task_name for tr in trs}
        merged = type(mrs[0]).model_construct(
            model_name=name, model_revision=mrs[0].model_revision, task_results=trs,
            experiment_name=None, model_meta=mrs[0].model_meta,
        )
        s = (bench.get_score(type(results).model_construct(model_results=[merged])).get(name) or {}).get("Mean(Task)")
        if s is not None and s <= 1:
            s *= 100
        out[name] = (s, len(covered), "+".join(sorted(str(mr.model_revision) for mr in mrs)))
    return out


def main() -> None:
    head_url, head_api = api_rows(HEADLINE)
    sec_url, sec_api = api_rows(SECONDARY)
    head_cohort = [r for r in head_api if r.get("meanTask") is not None]
    sec_cohort = [r for r in sec_api if r.get("meanTask") is not None]
    print(f"{HEADLINE}: {len(head_api)} rows, {len(head_cohort)} complete; "
          f"{SECONDARY}: {len(sec_api)} rows, {len(sec_cohort)} complete", flush=True)

    head_b, sec_b = mteb.get_benchmark(HEADLINE), mteb.get_benchmark(SECONDARY)
    names = sorted({r["model"]["name"] for r in head_cohort + sec_cohort})
    tasks = list({t.metadata.name: t for t in [*head_b.tasks, *sec_b.tasks]}.values())
    print(f"recomputing {len(names)} models on {len(tasks)} tasks (~{len(names) * 4.5 / 60:.0f} min + import)", flush=True)
    results = mteb.load_results(tasks=tasks, models=names, only_main_score=True).join_revisions()

    problems, notes = [], []

    def board(bench, cohort, label):
        n_tasks = len(bench.tasks)
        ours = recompute(bench, results, [r["model"]["name"] for r in cohort])
        rows = []
        for r in cohort:
            name = r["model"]["name"]
            s, n, rev = ours[name]
            site = r["meanTask"] * 100
            row = {
                "model": name, "site_rank": r["rank"], "score": None if s is None else round(s, 2),
                "site_score": round(site, 2), "tasks": n, "revision": rev,
                "active_b": r["model"].get("activeParamsB"), "total_b": r["model"].get("totalParamsB"),
                "model_type": r["model"].get("modelType"), "zero_shot_pct": r.get("zeroShotPct"),
                "trained_on_tasks": r.get("trainedOnTasks"),
            }
            if s is None or n != n_tasks:
                row["problem"] = f"{label} {name}: {n}/{n_tasks} tasks recomputed"
            elif abs(s - site) > SCORE_TOL:
                row["problem"] = f"{label} {name}: recomputed {s:.2f} vs site {site:.2f}"
            rows.append(row)
        rows.sort(key=lambda x: -(x["score"] if x["score"] is not None else x["site_score"]))
        for i, x in enumerate(rows, 1):
            x["position"] = i  # by recomputed Mean (Task); the site's own rank is Borda
        return rows

    head = board(head_b, head_cohort, HEADLINE)
    sec = board(sec_b, sec_cohort, SECONDARY)

    shown = {x["model"] for x in head[:TOP_N]} | set(SUBJECTS) | {BASELINE}
    for x in head:
        if "problem" in x:
            (problems if x["model"] in shown else notes).append(x["problem"])
    for x in sec:
        if "problem" in x:
            (problems if x["model"] in SUBJECTS else notes).append(x["problem"])

    # Who is missing: the established code board's top 20 (subjects excluded), and
    # whether each has complete CoREB(v1) results.
    head_names = {x["model"] for x in head}
    top_code = [x for x in sec if x["model"] not in SUBJECTS][:20]
    missing = [x["model"] for x in top_code if x["model"] not in head_names]

    best = head[0]
    print(f"\n{HEADLINE} (recomputed, {len(head)} complete):")
    for x in head:
        mark = "*" if x["model"] in SUBJECTS else " "
        print(f" {mark}{x['position']:>3} site#{x['site_rank']:>3} {x['score']!s:>6} (site {x['site_score']:6.2f}) {x['model']}")
    for s in SUBJECTS:
        x = next(x for x in head if x["model"] == s)
        print(f"  {s}: {x['score']:.2f}, {best['score'] - x['score']:.2f} behind {best['model']}")
    print(f"\n{SECONDARY} (recomputed, {len(sec)} complete), top 25:")
    for x in sec[:25]:
        mark = "*" if x["model"] in SUBJECTS else " "
        print(f" {mark}{x['position']:>3} site#{x['site_rank']:>3} {x['score']!s:>6} (site {x['site_score']:6.2f}) zs={x['zero_shot_pct']} {x['model']}")
    print(f"\nwho is missing: {len(missing)} of the top 20 {SECONDARY} models have no complete {HEADLINE} results:")
    for m in missing:
        print("  " + m)
    print("\nproblems:" if problems else "\nevery shown score agrees with the live leaderboard")
    for p in problems:
        print("  " + p)
    for n in notes:
        print("  note: " + n)

    (HERE / "data.json").write_text(json.dumps({
        "generated": date.today().isoformat(),
        "subjects": SUBJECTS,
        "apis": {HEADLINE: head_url, SECONDARY: sec_url},
        "problems": problems,
        "notes": notes,
        "who_is_missing": {
            "question": f"of the top 20 complete {SECONDARY} models (subjects excluded), which have no complete {HEADLINE} results",
            "top20": [x["model"] for x in top_code],
            "missing": missing,
        },
        HEADLINE: {"n_tasks": len(head_b.tasks), "n_complete": len(head), "models": head},
        SECONDARY: {"n_tasks": len(sec_b.tasks), "n_complete": len(sec), "models": sec},
    }, indent=2) + "\n")

    if CARD.exists():
        card_rows = []
        for x in head[:TOP_N]:
            card_rows.append({"model": x["model"], "score": x["score"], "params": x["total_b"] and round(x["total_b"] * 1e9),
                              "rank": x["position"], "subject": x["model"] in SUBJECTS, "type": x["model_type"]})
        bl = next(x for x in head if x["model"] == BASELINE)
        card_rows.append({"model": bl["model"], "score": bl["score"], "params": 0,
                          "rank": bl["position"], "baseline": True, "type": bl["model_type"]})
        write_card_data(CARD, {
            "benchmark": HEADLINE, "n_tasks": len(head_b.tasks), "n_models": len(head),
            "best": best["score"], "rows": card_rows,
        })

    if problems:
        raise SystemExit(f"{len(problems)} disagreement(s) — the card must not be built on these numbers")


if __name__ == "__main__":
    main()
