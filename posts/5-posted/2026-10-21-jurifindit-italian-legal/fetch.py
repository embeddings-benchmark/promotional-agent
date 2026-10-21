#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["mtebpost", "mteb==2.24.10"]
#
# [tool.uv.sources]
# mtebpost = { path = "../../..", editable = true }
#
# [tool.uv]
# exclude-newer = "2026-10-13T00:00:00Z"
# ///
"""Evidence for the JuriFindIT dataset post. Run from the repo root (through the cache lock
when other fetches may be running):

    uv run posts/4-scheduled/2026-10-21-jurifindit-italian-legal/fetch.py

mteb#5464 adds `JuriFindITRetrieval`, a single Italian legal retrieval task. results#719
and results#722 give it its first results. There is no benchmark to cite: the Italian
board that would have contained it (`MTEB(ita, v1)`, mteb#5479) was closed unmerged.

**How a single task is scored.** `Benchmark.get_score()` is the leaderboard's aggregation,
and it needs a benchmark. So the script wraps the one task in an ad-hoc
`mteb.Benchmark(tasks=[task])`; its `Mean(Task)` over one task *is* that task's main score
(nDCG@10). As a check on that equivalence, every score is also read straight off the
`TaskResult` (`get_score()` on the result object, which returns the main score) and the
script fails if the two differ. Both are then compared with the live leaderboard's
per-task endpoint, `/v1/tasks/JuriFindITRetrieval/scores`, and the script fails on any
disagreement above 0.01 points.

**Who is in the cohort.** Every model with a `JuriFindITRetrieval.json` anywhere in the
results repo, found by walking the refreshed cache, and checked against the set of models
the leaderboard API lists for the task. Revisions are joined the way the leaderboard joins
them (`join_revisions()`, then one merged `ModelResult` per model), copied from
`4-scheduled/2026-10-15-leaderboard-pareto-tag/fetch.py`.

Also recorded, because the post makes claims that depend on them:

- **What else MTEB has for Italian legal retrieval** — every non-superseded retrieval
  task with the `Legal` domain that covers Italian, with how its queries were made.
- **Each model's own metadata**: whether Italian is a declared language (peers must be
  built for the task), whether `JuriFindITRetrieval` is declared training data, and sizes.
- **`BAAI/bge-m3`**, the base of `albertobarnabo/bge-m3-italian`: whether it has a
  JuriFindIT result in any revision. Without one, no fine-tune-vs-base claim is possible.
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

TASK = "JuriFindITRetrieval"
API = "https://mteb-leaderboard-backend.hf.space/v1/tasks/{}/scores"
CACHE = pathlib.Path.home() / ".cache" / "mteb" / "remote" / "results"
HERE = pathlib.Path(__file__).parent
CARD = HERE / "card-1-jurifindit.html"
BASELINES = {"mteb/baseline-bm25s", "mteb/baseline-random-encoder"}
BASE_OF_FINETUNE = "BAAI/bge-m3"
TOL = 0.01  # points


def walk_cohort() -> dict[str, list[str]]:
    """model name -> revision folders holding a result for TASK, from the cache."""
    out: dict[str, list[str]] = {}
    for f in sorted(CACHE.glob(f"*/*/{TASK}.json")):
        rev_dir = f.parent
        meta = rev_dir / "model_meta.json"
        name = json.loads(meta.read_text())["name"] if meta.exists() else rev_dir.parent.name.replace("__", "/", 1)
        out.setdefault(name, []).append(rev_dir.name)
    return out


def main() -> None:
    task = mteb.get_task(TASK)
    md = task.metadata
    stats_file = pathlib.Path(mteb.__file__).parent / "descriptive_stats" / "Retrieval" / f"{TASK}.json"
    stats = json.loads(stats_file.read_text())["test"]
    print(f"{TASK}: main score {md.main_score}, langs {md.eval_langs}, domains {md.domains}")
    print(f"  {stats['num_queries']} queries, {stats['num_documents']} documents, "
          f"{stats['relevant_docs_statistics']['average_relevant_docs_per_query']:.2f} relevant per query", flush=True)

    # What else covers Italian legal retrieval.
    others = []
    for t in mteb.get_tasks(languages=["ita"], domains=["Legal"], task_types=["Retrieval"]):
        m = t.metadata
        others.append({
            "task": m.name, "annotations_creators": m.annotations_creators,
            "sample_creation": m.sample_creation, "description": m.description,
        })
        print(f"  ita legal retrieval: {m.name:30s} {m.annotations_creators} / {m.sample_creation}")

    # Refresh the cache (one cheap model), then find the cohort on disk.
    mteb.load_results(tasks=[task], models=["mteb/baseline-random-encoder"], only_main_score=True)
    on_disk = walk_cohort()
    names = sorted(on_disk)
    print(f"\n{len(names)} models with a {TASK} result on disk", flush=True)

    with urllib.request.urlopen(API.format(urllib.parse.quote(TASK)), timeout=60) as r:
        api_rows = json.load(r)["rows"]
    api = {r["model"]["name"]: r for r in api_rows}
    problems = []
    if set(api) != set(names):
        problems.append(f"cohort differs from API: disk-only {set(names) - set(api)}, api-only {set(api) - set(names)}")

    results = mteb.load_results(tasks=[task], models=names, only_main_score=True, download_latest=False)
    results = results.join_revisions()
    by_model: dict[str, list] = {}
    for mr in results.model_results:
        by_model.setdefault(mr.model_name, []).append(mr)

    bench = mteb.Benchmark(name=f"{TASK} (single task)", tasks=[task])
    rows = []
    for name in names:
        mrs = by_model.get(name, [])
        trs = [tr for mr in mrs for tr in mr.task_results if tr.task_name == TASK]
        if len(trs) != 1:
            problems.append(f"{name}: {len(trs)} {TASK} results after joining revisions")
            continue
        merged = type(mrs[0]).model_construct(
            model_name=name, model_revision=mrs[0].model_revision,
            task_results=[tr for mr in mrs for tr in mr.task_results],
            experiment_name=None, model_meta=mrs[0].model_meta,
        )
        agg = (bench.get_score(type(results).model_construct(model_results=[merged])).get(name) or {}).get("Mean(Task)")
        direct = trs[0].get_score()
        if agg is None:
            problems.append(f"{name}: get_score returned None")
            continue
        ours = agg * 100 if agg <= 1 else agg
        direct = direct * 100 if direct <= 1 else direct
        if abs(ours - direct) > TOL:
            problems.append(f"{name}: get_score {ours:.4f} vs TaskResult main score {direct:.4f}")
        site = api.get(name, {}).get("score")
        site = None if site is None else site * 100
        if site is None or abs(ours - site) > TOL:
            problems.append(f"{name}: recomputed {ours:.2f} vs leaderboard {site}")

        meta = mteb.get_model_meta(name)
        train = set(meta.training_datasets or ())  # a set of task names in mteb 2.24 (dict keys in older versions)
        langs = meta.languages or []
        rows.append({
            "model": name,
            "score": round(ours, 2),
            "site_score": None if site is None else round(site, 2),
            "baseline": name in BASELINES,
            "revisions": on_disk[name],
            "mteb_version": trs[0].mteb_version,
            "n_parameters": meta.n_parameters,
            "n_active_parameters": meta.n_active_parameters,
            "declares_italian": any(l.startswith("ita") for l in langs),
            "n_languages": len(langs),
            "task_in_training_data": TASK in train,
            "adapted_from": meta.adapted_from,
            "release_date": str(meta.release_date) if meta.release_date else None,
        })

    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        flag = "" if r["declares_italian"] or r["baseline"] else "  [no Italian declared]"
        flag += "  [TASK IN TRAINING DATA]" if r["task_in_training_data"] else ""
        print(f"  {i:>2}  {r['score']:6.2f}  site {r['site_score']}  {r['model']}{flag}")

    base_has = sorted(p.parent.name for p in CACHE.glob(f"{BASE_OF_FINETUNE.replace('/', '__')}/*/{TASK}.json"))
    print(f"\n{BASE_OF_FINETUNE} {TASK} results: {base_has or 'none'}")

    print("\nproblems:" if problems else "\nrecomputed scores agree with TaskResult main scores and the live leaderboard")
    for p in problems:
        print("  " + p)

    (HERE / "data.json").write_text(json.dumps({
        "generated": date.today().isoformat(),
        "task": TASK,
        "main_score": md.main_score,
        "eval_langs": md.eval_langs,
        "domains": md.domains,
        "annotations_creators": md.annotations_creators,
        "sample_creation": md.sample_creation,
        "reference": md.reference,
        "descriptive_stats_test": stats,
        "italian_legal_retrieval_tasks": others,
        "scoring": "Mean(Task) of mteb.Benchmark(tasks=[JuriFindITRetrieval]).get_score(), "
                   "equal to the task's main score; cross-checked against TaskResult.get_score() and the API",
        "api": API.format(urllib.parse.quote(TASK)),
        "base_model_check": {"model": BASE_OF_FINETUNE, "revisions_with_task": base_has},
        "problems": problems,
        "models": rows,
    }, indent=2, default=str) + "\n")

    if CARD.exists():
        write_card_data(CARD, {
            "task": TASK,
            "n_queries": stats["num_queries"],
            "n_documents": stats["num_documents"],
            "n_models": sum(1 for r in rows if not r["baseline"]),
            "rows": [{k: r[k] for k in ("model", "score", "baseline", "n_active_parameters", "n_parameters")} for r in rows],
        })

    if problems:
        raise SystemExit(f"{len(problems)} problem(s) — the card must not be built on these numbers")


if __name__ == "__main__":
    main()
