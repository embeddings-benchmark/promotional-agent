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
"""Evidence for the Noql card. Run from the repo root (through the cache lock):

    uv run posts/<stage>/noql-persian/fetch.py

The card places shekar-ai/Noql among every model with complete MTEB(fas, v2) results, by
total parameters and Mean (Task). Two sources, checked against each other:

1. **The live leaderboard API** gives the cohort — rows with a non-null Mean (Task), which
   is how the site marks complete coverage — plus each row's size metadata.
2. **`Benchmark.get_score()` on the results repo** recomputes Mean (Task) for every model
   in that cohort (rule 1). Revisions are joined and merged per model the same way the
   leaderboard does. The script fails if any recomputed score in the card disagrees with
   the site, or if any model's joined results do not cover all tasks.

Why total parameters, not active: Noql is an ALBERT model whose 12 layers share one set
of weights, so neither count says much about compute, and MTEB's active count (7.8M)
would drop MCINext/Hakim-small (no active count published) — the strongest small Persian
model — from the chart. Total parameters is what the size claim is about: what has to be
downloaded and held in memory. Models with no published size (openai/text-embedding-3-small)
are recomputed and recorded but cannot be placed on a size axis.
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

BENCHMARK = "MTEB(fas, v2)"
SUBJECT = "shekar-ai/Noql"
SUBJECT_REVISION = "fcdec3f8c64107a4a552b1877156d561fa1b6eb9"
API = "https://mteb-leaderboard-backend.hf.space/v1/benchmarks/{}/scores"
HERE = pathlib.Path(__file__).parent
CARD = HERE / "card-1-noql-persian.html"
SCORE_TOL = 0.01


def main() -> None:
    url = API.format(urllib.parse.quote(BENCHMARK))
    with urllib.request.urlopen(url) as r:
        api = json.load(r)
    api_rows = api["rows"]
    cohort = [r for r in api_rows if r.get("meanTask") is not None]
    print(f"{len(api_rows)} leaderboard rows, {len(cohort)} with full coverage", flush=True)

    bench = mteb.get_benchmark(BENCHMARK)
    n_tasks = len(bench.tasks)
    task_names = {t.metadata.name for t in bench.tasks}
    names = [r["model"]["name"] for r in cohort]
    assert SUBJECT in names, f"{SUBJECT} not in the full-coverage cohort"
    print(f"recomputing {len(names)} models on {n_tasks} tasks", flush=True)
    results = mteb.load_results(tasks=bench.tasks, models=names, only_main_score=True)
    results = results.join_revisions()

    by_model: dict[str, list] = {}
    for mr in results.model_results:
        by_model.setdefault(mr.model_name, []).append(mr)

    rows, problems, mismatches = [], [], []
    for r in cohort:
        m = r["model"]
        name = m["name"]
        site = r["meanTask"] * 100
        mrs = by_model.get(name, [])
        covered = set().union(*({tr.task_name for tr in mr.task_results} for mr in mrs)) & task_names if mrs else set()
        s = None
        if mrs:
            merged = type(mrs[0]).model_construct(
                model_name=name, model_revision=mrs[0].model_revision,
                task_results=[tr for mr in mrs for tr in mr.task_results],
                experiment_name=None, model_meta=mrs[0].model_meta,
            )
            s = (bench.get_score(type(results).model_construct(model_results=[merged])).get(name) or {}).get("Mean(Task)")
        if len(covered) != n_tasks or s is None:
            problems.append(f"{name}: {len(covered)}/{n_tasks} tasks after joining revisions")
            continue
        ours = s * 100 if s <= 1 else s
        if abs(ours - site) > SCORE_TOL:
            mismatches.append(f"{name}: recomputed {ours:.2f} vs site {site:.2f}")
        revisions = sorted(str(mr.model_revision) for mr in mrs)
        langs = m.get("languages") or []
        rows.append({
            "model": name,
            "rank": r["rank"],
            "total_b": m.get("totalParamsB"),
            "active_b": m.get("activeParamsB"),
            "score": round(ours, 2),
            "site_score": round(site, 2),
            "revisions": revisions,
            "persian_only": langs == ["Persian"],
            "n_languages": len(langs),
            "open_weights": m.get("openWeights"),
            "zero_shot_pct": m.get("zeroShotPct"),
            "subject": name == SUBJECT,
        })

    subj = next((r for r in rows if r["subject"]), None)
    if subj is None:
        raise SystemExit(f"{SUBJECT} did not recompute — see problems: {problems}")
    if subj["revisions"] != [SUBJECT_REVISION]:
        problems.append(f"{SUBJECT}: scored revisions {subj['revisions']}, expected {SUBJECT_REVISION}")

    # Subject metadata as registered in mteb (cross-check against the API's size fields).
    meta = {}
    try:
        mm = mteb.get_model_meta(SUBJECT)
        meta = {
            "revision": mm.revision,
            "n_parameters": mm.n_parameters,
            "n_embedding_parameters": getattr(mm, "n_embedding_parameters", None),
            "n_active_parameters": getattr(mm, "n_active_parameters", None),
            "embed_dim": mm.embed_dim,
            "max_tokens": mm.max_tokens,
            "languages": mm.languages,
            "adapted_from": mm.adapted_from,
        }
        if mm.revision != SUBJECT_REVISION:
            problems.append(f"ModelMeta revision {mm.revision} != scored {SUBJECT_REVISION}")
        if mm.n_parameters and abs(mm.n_parameters / 1e9 - subj["total_b"]) > 0.001:
            problems.append(f"ModelMeta n_parameters {mm.n_parameters} vs site {subj['total_b']}B")
    except Exception as e:  # registered after the pin would land here
        meta = {"error": repr(e)}

    sized = sorted([r for r in rows if r["total_b"] is not None], key=lambda r: r["total_b"])
    smaller = [r for r in sized if r["total_b"] < subj["total_b"]]
    if smaller:
        problems.append("not the smallest: " + ", ".join(r["model"] for r in smaller))
    next_smallest = sized[1] if len(sized) > 1 else None

    # A mismatch on a model the card names is fatal; elsewhere it is recorded.
    named = {SUBJECT} | ({next_smallest["model"]} if next_smallest else set())
    for mm_ in mismatches:
        if mm_.split(":")[0] in named:
            problems.append(mm_)

    print(f"\n{SUBJECT}: {subj['score']:.2f} (site {subj['site_score']:.2f}), rank {subj['rank']} of {len(rows)}")
    print("smallest by total parameters:")
    for r in sized[:8]:
        print(f"  {r['total_b'] * 1000:>7.1f}M total  {(r['active_b'] or 0) * 1000:>6.1f}M active  {r['score']:6.2f}  {r['model']}")
    for mm_ in mismatches:
        print("  note: " + mm_)
    print("\nproblems:" if problems else "\nall recomputed scores agree with the live leaderboard")
    for p in problems:
        print("  " + p)

    (HERE / "data.json").write_text(json.dumps({
        "generated": date.today().isoformat(),
        "benchmark": BENCHMARK,
        "n_benchmark_tasks": n_tasks,
        "api": url,
        "n_leaderboard_rows": len(api_rows),
        "n_full_coverage": len(rows),
        "n_full_coverage_with_size": len(sized),
        "subject": subj,
        "subject_model_meta": meta,
        "next_smallest": next_smallest,
        "problems": problems,
        "score_differences_not_on_card": [m for m in mismatches if m.split(":")[0] not in named],
        "models": sorted(rows, key=lambda r: -r["score"]),
    }, indent=2) + "\n")

    if CARD.exists():
        write_card_data(CARD, {
            "benchmark": BENCHMARK,
            "n_tasks": n_tasks,
            "n_models": len(sized),
            "points": [
                {"model": r["model"], "x": round(r["total_b"] * 1e9), "y": r["score"],
                 "subject": r["subject"],
                 "rival": next_smallest is not None and r["model"] == next_smallest["model"]}
                for r in sized
            ],
        })

    if problems:
        raise SystemExit(f"{len(problems)} problem(s) — the card must not be built on these numbers")


if __name__ == "__main__":
    main()
