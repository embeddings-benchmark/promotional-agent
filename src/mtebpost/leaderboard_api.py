"""Live queries against the hosted MTEB leaderboard-backend API.

`model_release.py`'s only data source. Two reasons, not one:

- **Speed.** No ~190s `import mteb`, no ~4.5s-per-model local result load
  (docs/mteb-data.md) — a few HTTP calls instead.
- **Currency.** The local `mteb` package is version-pinned for reproducibility
  (pyproject.toml's `exclude-newer`), so it has no `ModelMeta` for anything registered
  after that pin date — in practice most recently-added models, since mteb ships fast
  ("8 releases in 12 days", CONTRIBUTING.md). `mtebpost.scoreboard`'s local path
  genuinely cannot see a model added last week; this API, being live, always can.
  colvec11-vidore/dinghy-law-family/mdenseon-mlateon already use it for this reason.

No aggregation happens here beyond an unweighted mean across tasks for a custom task
subset (`custom_scores`) — the same "Mean(Task)" `Benchmark.get_score()` computes
locally. For a registered benchmark, the API's own `meanTask` is used as-is rather than
recomputed, since it already comes from the same aggregation, server-side.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

API = "https://mteb-leaderboard-backend.hf.space"


def _get(path: str) -> dict:
    url = f"{API}{path}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"{url} failed: {e.code} {e.read().decode(errors='replace')}"
        ) from e


def _score100(v: float) -> float:
    """MTEB scores are 0-1 fractions in this API; the rest of the pipeline uses 0-100."""
    return round(v * 100, 2) if v <= 1 else round(v, 2)


@dataclass
class Entry:
    """Same shape/contract as `scoreboard.Entry` (`.complete`, `.plottable`,
    `.as_dict()`), so `model_release.py`'s cohort/pareto/radar/bars logic reads
    identically regardless of which module produced the entry. Parameter counts are
    raw values (not billions) to match card-data schemas that format them directly.
    """

    model: str
    score: float
    active_params: int | None
    total_params: int | None
    n_tasks: int
    n_benchmark_tasks: int
    release_date: str | None = None
    languages: tuple[str, ...] = ()
    modalities: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return self.n_tasks == self.n_benchmark_tasks

    @property
    def is_static(self) -> bool:
        return self.active_params == 0

    @property
    def plottable(self) -> bool:
        return self.complete and self.active_params is not None

    def as_dict(self) -> dict:
        return {
            "model": self.model, "score": self.score,
            "active_params": self.active_params, "total_params": self.total_params,
            "n_tasks": self.n_tasks, "n_benchmark_tasks": self.n_benchmark_tasks,
            "release_date": self.release_date,
            "languages": list(self.languages), "modalities": list(self.modalities),
            "complete": self.complete, "plottable": self.plottable,
        }


def _params(model_meta: dict) -> tuple[int | None, int | None]:
    active = model_meta.get("activeParamsB")
    total = model_meta.get("totalParamsB")
    return (
        round(active * 1e9) if active is not None else None,
        round(total * 1e9) if total is not None else None,
    )


def task_type(task: str) -> str:
    """The TaskType (e.g. "Retrieval") of a single task, from its own metadata."""
    return _get(f"/v1/tasks/{urllib.parse.quote(task)}")["type"]


def task_scores(task: str, *, subset: str | None = None) -> dict[str, dict]:
    """Per-model result for one task, keyed by model name; only models with a real
    (non-null) score are included.

    `subset` pins the result to one named subset (e.g. "de" on XMarket, a task with
    subsets per language) — needed because the API's top-level `score` is null
    whenever a model ran fewer than every subset the task has, which no
    single-language model could ever satisfy. Without `subset`, the plain `score`
    field is used (correct for a single-subset task).
    """
    data = _get(f"/v1/tasks/{urllib.parse.quote(task)}/scores")
    out: dict[str, dict] = {}
    for row in data["rows"]:
        if subset is not None:
            per_split = row["subsetScores"].get(subset)
            val = next(iter(per_split.values()), None) if per_split else None
        else:
            val = row["score"]
        if val is None:
            continue
        active, total = _params(row["model"])
        out[row["model"]["name"]] = {
            "score": val, "active_params": active, "total_params": total,
            "release_date": row["model"].get("releaseDate"),
            "languages": tuple(row["model"].get("languages") or ()),
            "modalities": tuple(row["model"].get("modalities") or ()),
        }
    return out


def custom_scores(
    tasks: list[str], *, subsets: dict[str, str] | None = None
) -> tuple[list[Entry], list[Entry], dict[str, dict[str, float]]]:
    """Score every model with a real result on ALL of `tasks` — Mean(Task), unweighted,
    the aggregation `Benchmark.get_score()` uses for an ad-hoc task list too.

    `subsets` maps a task name to the one subset that counts for it (see `task_scores`)
    — needed for any multi-language task in the list (XMarket -> "de", say).

    Returns (complete, partial, per_task): `complete` entries covered every task,
    `partial` cover at least one but not all — kept so a `fetch.py` can record what did
    not qualify and why, per CONTRIBUTING.md's "record every model that qualified" (and,
    symmetrically, every one that didn't). `per_task[model]` is `{task: score}` (0-100,
    whatever subset was used) for every model with at least one result, feeding a
    radar's per-task axes without a second round of API calls.
    """
    subsets = subsets or {}
    per_task_raw = {t: task_scores(t, subset=subsets.get(t)) for t in tasks}

    all_models: set[str] = set()
    for rows in per_task_raw.values():
        all_models |= set(rows)

    complete, partial = [], []
    per_task: dict[str, dict[str, float]] = {}
    for m in sorted(all_models):
        present = [t for t in tasks if m in per_task_raw[t]]
        vals = [per_task_raw[t][m]["score"] for t in present]
        meta = per_task_raw[present[0]][m]
        per_task[m] = {t: _score100(per_task_raw[t][m]["score"]) for t in present}
        entry = Entry(
            model=m, score=_score100(sum(vals) / len(vals)),
            active_params=meta["active_params"], total_params=meta["total_params"],
            n_tasks=len(present), n_benchmark_tasks=len(tasks),
            release_date=meta["release_date"],
            languages=meta["languages"], modalities=meta["modalities"],
        )
        (complete if len(present) == len(tasks) else partial).append(entry)

    complete.sort(key=lambda e: e.score, reverse=True)
    partial.sort(key=lambda e: e.score, reverse=True)
    return complete, partial, per_task


def model_types() -> dict[str, str]:
    """model name -> `ModelMeta.model_type` ("dense", "late-interaction", ...).

    Architecture is not part of an `Entry`, which is about scores and size — but on a
    board where one architecture family holds every top place it is the difference
    between a rank and an explanation of the rank (see the ViDoRe(v2) post). Read from
    the registry rather than inferred from a model's name.
    """
    out: dict[str, str] = {}
    for m in _get("/v1/models"):
        t = m.get("modelType")
        if isinstance(t, list):
            t = t[0] if t else None
        if t:
            out[m["name"]] = t
    return out


def benchmark_task_scores(benchmark: str) -> tuple[list[str], dict[str, dict[str, float]]]:
    """A benchmark's task list, plus every model's per-task scores *including* the models
    with partial coverage.

    `benchmark_scores()` drops any row the API gives no aggregate `meanTask` for, which
    is every model short of full coverage — exactly the rows needed to ask CONTRIBUTING's
    "who is missing" question about a young board, where one unrun task can be the only
    thing keeping a dozen models off it. Returns (tasks, per_model), `per_model[model]`
    being `{task: score}` (0-100) for the tasks that model actually ran.
    """
    data = _get(f"/v1/benchmarks/{urllib.parse.quote(benchmark)}/scores")
    per_model = {
        row["model"]["name"]: {
            t: _score100(v) for t, v in (row.get("scoresByTask") or {}).items()
            if v is not None
        }
        for row in data["rows"]
    }
    return list(data["tasks"]), {m: s for m, s in per_model.items() if s}


def benchmark_scores(benchmark: str) -> tuple[list[Entry], dict[str, dict[str, float]]]:
    """Every model's aggregate score on a *registered* benchmark, via
    `/v1/benchmarks/{name}/scores` — the same endpoint colvec11-vidore/
    dinghy-law-family/mdenseon-mlateon already use.

    Returns (entries, per_task_scores) — `per_task_scores[model]` is `{task: score}`
    (0-100), straight from the row's `scoresByTask`, for building a radar's axes
    without a second round of per-task API calls.
    """
    data = _get(f"/v1/benchmarks/{urllib.parse.quote(benchmark)}/scores")
    tasks = data["tasks"]
    entries = []
    per_task: dict[str, dict[str, float]] = {}
    for row in data["rows"]:
        if row.get("meanTask") is None:
            continue
        active, total = _params(row["model"])
        entries.append(Entry(
            model=row["model"]["name"], score=_score100(row["meanTask"]),
            active_params=active, total_params=total,
            n_tasks=sum(1 for v in row.get("scoresByTask", {}).values() if v is not None),
            n_benchmark_tasks=len(tasks),
            release_date=row["model"].get("releaseDate"),
            languages=tuple(row["model"].get("languages") or ()),
            modalities=tuple(row["model"].get("modalities") or ()),
        ))
        per_task[row["model"]["name"]] = {
            t: _score100(v) for t, v in row.get("scoresByTask", {}).items() if v is not None
        }
    entries.sort(key=lambda e: e.score, reverse=True)
    return entries, per_task
