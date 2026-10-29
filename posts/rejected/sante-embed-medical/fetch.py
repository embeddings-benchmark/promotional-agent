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
"""Evidence for (not against) a decision on sante-embed. Run from the repo root:

    uv run posts/2-drafting/sante-embed-medical/fetch.py

Recomputes MTEB(Medical, v1) Mean(Task) with Benchmark.get_score() for the subject,
Singaraj/sante-embed, and the model it was fine-tuned from,
Alibaba-NLP/gte-Qwen2-1.5B-instruct, and checks both against the live leaderboard API.

The base model's results are split across two revision folders (5 tasks in its main
revision, 7 in `external`). Read revision by revision it looks like 5/12 coverage; the
leaderboard joins them into a full 12/12 row. So we join revisions and merge each
model's entries into one ModelResult before scoring, as the leaderboard does.

Also records, from the API: the size of the complete-coverage cohort, the subject's rank
in it, and how many of the top 20 MTEB(Multilingual, v2) / MTEB(eng, v2) models have no
complete Medical results ("who is missing").
"""

import json
import pathlib
import urllib.parse
import urllib.request
import warnings
from datetime import date

warnings.filterwarnings("ignore")

import mteb  # noqa: E402

BENCHMARK = "MTEB(Medical, v1)"
SUBJECT = "Singaraj/sante-embed"
BASE = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"
API = "https://mteb-leaderboard-backend.hf.space/v1/benchmarks/{}/scores"
HERE = pathlib.Path(__file__).parent
SCORE_TOL = 0.01  # points


def api_rows(benchmark: str) -> list[dict]:
    with urllib.request.urlopen(API.format(urllib.parse.quote(benchmark))) as r:
        return json.load(r)["rows"]


def main() -> None:
    med = api_rows(BENCHMARK)
    site = {r["model"]["name"]: r for r in med}
    complete = sorted([r for r in med if r["meanTask"] is not None], key=lambda r: -r["meanTask"])
    print(f"{len(med)} rows on {BENCHMARK}, {len(complete)} with complete coverage", flush=True)

    bench = mteb.get_benchmark(BENCHMARK)
    task_names = [t.metadata.name for t in bench.tasks]
    results = mteb.load_results(tasks=bench.tasks, models=[SUBJECT, BASE], only_main_score=True)
    results = results.join_revisions()

    by_model: dict[str, list] = {}
    for mr in results.model_results:
        by_model.setdefault(mr.model_name, []).append(mr)

    models, problems = {}, []
    for name in (SUBJECT, BASE):
        mrs = by_model[name]
        merged = type(mrs[0]).model_construct(
            model_name=name, model_revision=mrs[0].model_revision,
            task_results=[tr for mr in mrs for tr in mr.task_results],
            experiment_name=None, model_meta=mrs[0].model_meta,
        )
        per_rev = {str(mr.model_revision): sorted({tr.task_name for tr in mr.task_results} & set(task_names)) for mr in mrs}
        covered = set().union(*per_rev.values())
        s = bench.get_score(type(results).model_construct(model_results=[merged]))[name]["Mean(Task)"]
        ours = s * 100 if s <= 1 else s
        theirs = site[name]["meanTask"] * 100
        if len(covered) != len(task_names):
            problems.append(f"{name}: {len(covered)}/{len(task_names)} tasks")
        if abs(ours - theirs) > SCORE_TOL:
            problems.append(f"{name}: recomputed {ours:.2f} vs site {theirs:.2f}")
        per_task = {}
        for tr in merged.task_results:
            if tr.task_name in task_names:
                per_task[tr.task_name] = round(tr.get_score() * 100, 2)
        rank = next(i for i, r in enumerate(complete, 1) if r["model"]["name"] == name)
        models[name] = {
            "score": round(ours, 2), "site_score": round(theirs, 2),
            "rank_by_mean_task": rank, "site_rank_borda": site[name]["rank"],
            "zero_shot_pct": site[name]["zeroShotPct"],
            "trained_on_tasks": site[name]["trainedOnTasks"],
            "active_b": site[name]["activeParamsB"],
            "tasks_by_revision": per_rev, "per_task": per_task,
        }
        print(f"{name}: {ours:.2f} (site {theirs:.2f}), {len(covered)}/{len(task_names)} tasks, "
              f"rank {rank} by Mean(Task), site rank {site[name]['rank']}", flush=True)

    meta = mteb.get_model_meta(SUBJECT)
    try:
        zs = meta.zero_shot_percentage(bench.tasks)
    except Exception as e:  # API differs across mteb versions; the site value is recorded anyway
        zs = f"unavailable: {e}"
    sub, base = models[SUBJECT], models[BASE]
    diff = {t: round(sub["per_task"][t] - base["per_task"][t], 2) for t in task_names}

    missing = {}
    for b in ("MTEB(Multilingual, v2)", "MTEB(eng, v2)"):
        top = sorted([r for r in api_rows(b) if r["meanTask"] is not None], key=lambda r: r["rank"])[:20]
        miss = [r["model"]["name"] for r in top
                if r["model"]["name"] not in site or site[r["model"]["name"]]["meanTask"] is None]
        missing[b] = {"n_missing_of_top20": len(miss), "missing": miss}
        print(f"top 20 on {b}: {len(miss)} have no complete {BENCHMARK} results", flush=True)

    print(f"\nsubject minus base, Mean(Task): {sub['score'] - base['score']:+.2f}")
    for t, d in sorted(diff.items(), key=lambda x: x[1]):
        print(f"  {d:+6.2f}  {t}")
    print("\nproblems:" if problems else "\nrecomputed scores agree with the live leaderboard")
    for p in problems:
        print("  " + p)

    (HERE / "data.json").write_text(json.dumps({
        "generated": date.today().isoformat(),
        "benchmark": BENCHMARK,
        "n_benchmark_tasks": len(task_names),
        "api": API.format(urllib.parse.quote(BENCHMARK)),
        "n_leaderboard_rows": len(med),
        "n_complete": len(complete),
        "subject_modelmeta": {
            "languages": meta.languages, "training_datasets": sorted(meta.training_datasets or []),
            "adapted_from": meta.adapted_from, "n_parameters": meta.n_parameters,
            "n_active_parameters": meta.n_active_parameters, "max_tokens": meta.max_tokens,
            "zero_shot_percentage_on_benchmark": zs,
        },
        "models": models,
        "subject_minus_base_per_task": diff,
        "who_is_missing": missing,
        "problems": problems,
    }, indent=2, default=str) + "\n")

    if problems:
        raise SystemExit(f"{len(problems)} problem(s)")


if __name__ == "__main__":
    main()
