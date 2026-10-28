"""Cohort selection and chart-shape recommendation for `model_addition` posts.

Every model-release post answers the same three questions before it can pick a card:
who are the fair peers (full task coverage, same benchmark — CONTRIBUTING.md's
"complete task coverage only" rule), does the subject sit on a size/score Pareto
frontier, and if not, is there one clear rival worth a head-to-head. Answering those
by hand, differently each time, is most of the bespoke work in every model_addition
`fetch.py` so far (see bekko-thread, dinghy-law-family, colvec11-vidore,
mdenseon-mlateon) — this module answers them once, on top of `leaderboard_api.py`.

The three answers map onto the three card shapes already proven in production:

- **pareto** — scatter, size vs score, frontier shaded (bekko card-1-frontier).
- **radar** — one spoke per task type (or per task, for a domain-narrow cohort),
  subject against one named rival (bekko card-2-tasks).
- **bars** — ranked list, subject(s) highlighted (colvec11-vidore, dinghy-law-family,
  mdenseon-mlateon). The default: always defensible, no story required.

`recommend_chart()` is advice, not a silent decision — a `fetch.py` prints the
reasoning and still writes exactly one card, chosen by whoever is drafting the post.
Overriding it is normal, not a bug: the heuristic cannot see whether a "radar-eligible"
rival is actually the comparison worth making (CONTRIBUTING's "one post, one claim").

Runs entirely on `leaderboard_api` (the live leaderboard-backend), not the local `mteb`
library. The local package is version-pinned for reproducibility (pyproject.toml's
`exclude-newer`), so it has no `ModelMeta` for anything registered after that pin
date — in practice most freshly-registered models, which is exactly the subject of a
model_addition post. The API is also just faster: no ~190s import, no per-model local
result load.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mtebpost.leaderboard_api import Entry, benchmark_scores, custom_scores

# Task types whose main metric is a centered/normalized score that can go negative
# (e.g. InstructionReranking's p-MRR). A radar's radial axis starts at zero, so a
# negative value has no honest position on it — excluded rather than clamped, which
# would silently understate how badly a model does on that axis.
NEGATIVE_METRIC_TASK_TYPES = frozenset({"InstructionReranking", "InstructionRetrieval"})


@dataclass
class Cohort:
    benchmark: str
    subjects: list[Entry]
    peers: list[Entry]  # full-coverage peers, subjects excluded, sorted desc by score
    excluded: list[Entry]  # scored but not comparable (partial coverage / no size)
    # Every scored model, before the size/language/modality filters that produced
    # `peers` — radar_card_data() looks a "highlight" rival up here, since it is often
    # deliberately outside a size-banded cohort (the whole point is comparing against
    # something larger).
    pool: list[Entry] = field(default_factory=list)
    # model -> {task_name: score}, for every model in `pool` that has any result —
    # radar_card_data's per-task-type/per-task axes.
    per_task: dict[str, dict[str, float]] = field(default_factory=dict)
    tasks: tuple[str, ...] = ()
    # The size band peers were searched within, when cohort() was given max_active — the
    # search criterion, not just the largest peer actually found. pareto_card_data() uses
    # this for its "≤ Nm active params" context line rather than the observed max, since
    # a peer band that happens to bottom out early should not understate how wide the
    # search was.
    max_active: float | None = None

    @property
    def all_comparable(self) -> list[Entry]:
        """Subjects and peers together, sorted by score — the ranking a bars card shows."""
        return sorted(self.subjects + self.peers, key=lambda e: e.score, reverse=True)

    @property
    def n_benchmark_tasks(self) -> int:
        """Task count for the card's "N tasks" line — any entry agrees, since they were
        all scored against the same benchmark. Does not assume a subject exists: a
        benchmark_addition post with no single "subject" model (see BRIGHT-Pro) still
        has a real task count to report.
        """
        for e in self.subjects + self.peers + self.excluded:
            return e.n_benchmark_tasks
        return 0


def cohort(
    subjects: list[str],
    benchmark: str | list[str],
    *,
    name: str | None = None,
    subsets: dict[str, str] | None = None,
    max_active: float | None = None,
    min_active: float = 0,
    text_only: bool = True,
    min_languages: int = 1,
) -> Cohort:
    """Subject scores plus every full-coverage peer on the same benchmark.

    `name` labels a custom task list on the card's axis and in evidence (e.g. "German
    retrieval (MTEB subset)") — without it, four or more tasks fall back to "N tasks",
    which is accurate but says nothing a reader can picture. Ignored when `benchmark`
    is already a registered name.

    `benchmark` is either a registered name ("MTEB(Multilingual, v2)") or an explicit
    task list — the latter for a subject whose own results don't cover a full
    registered benchmark (a fine-tune evaluated on a hand-picked domain slice, the
    common case for a smaller lab's release). Either way scoring is Mean(Task), the
    same unweighted aggregation `Benchmark.get_score()` uses, so the "full coverage"
    rule still applies — just scoped to the tasks actually run rather than stretched to
    a benchmark nobody submitted to.

    `subsets` maps a task name to the one subset that counts for it — needed for any
    multi-language task in an explicit task list (XMarket -> "de", say), since the API
    reports no aggregate score for a model that ran fewer than every subset a task has.

    `max_active` bands peers by size instead of comparing the whole field — like
    bekko's frontier. A Pareto claim needs the band: almost everything is smaller than
    the largest model on any board, so "smaller and just as good" is only a claim a
    size-restricted cohort can support.

    `min_languages > 1` on a multilingual benchmark keeps English-only peers out — they
    score low because they were never built for the task, which both flatters the
    subject and misrepresents the peer (CONTRIBUTING.md's cohort-fairness rule).
    """
    if isinstance(benchmark, str):
        all_entries, per_task_all = benchmark_scores(benchmark)
        bench_name = benchmark
        task_list: tuple[str, ...] = ()
        # benchmark_scores() only returns rows with a non-null Mean(Task) at all, so
        # "excluded" here means partial coverage — not comparable, per CONTRIBUTING's
        # complete-coverage rule.
        #
        # Completeness only, deliberately *not* `Entry.plottable`: a model whose
        # parameter count is unpublished is perfectly comparable by score, and dropping
        # it silently shortens the board a rank claim is counted against (a proprietary
        # API model has no size to publish and is exactly the kind of entrant a rank
        # should be measured against). A size axis needs a size, and the two builders
        # that draw one enforce it themselves: pareto_card_data() drops sizeless points,
        # and `max_active` below bands peers by a size they must therefore have. This
        # also matches the custom-task-list branch, which has always split on coverage
        # alone.
        complete_pool = [e for e in all_entries if e.complete]
        excluded_pool = [e for e in all_entries if not e.complete]
    else:
        complete_pool, excluded_pool, per_task_all = custom_scores(benchmark, subsets=subsets)
        bench_name = name or (
            " + ".join(benchmark) if len(benchmark) <= 3 else f"{len(benchmark)} tasks"
        )
        task_list = tuple(benchmark)

    pool = complete_pool + excluded_pool
    by_name = {e.model: e for e in pool}
    missing = [s for s in subjects if s not in by_name]
    if missing:
        raise SystemExit(f"no results on {bench_name} for: {missing}")

    def keep(e: Entry) -> bool:
        if text_only and e.modalities and "text" not in e.modalities:
            return False
        if min_languages > 1 and len(e.languages) < min_languages:
            return False
        if max_active is not None and (
            e.active_params is None or not (min_active <= e.active_params <= max_active)
        ):
            return False
        return True

    subject_entries = [by_name[s] for s in subjects]
    peers = [
        e for e in complete_pool
        if e.model not in subjects and keep(e)
    ]
    excluded = [e for e in excluded_pool if e.model not in subjects]

    return Cohort(
        benchmark=bench_name, subjects=subject_entries, peers=peers, excluded=excluded,
        pool=pool, per_task=per_task_all, tasks=task_list, max_active=max_active,
    )


def pareto_frontier(entries: list[Entry]) -> list[Entry]:
    """Entries on the size/score frontier: nothing both smaller and higher-scoring.

    Mirrors the staircase the pareto card draws — this only answers which entries
    qualify, sorted by size ascending, the same order the card walks to draw it.
    """
    ordered = sorted(
        (e for e in entries if e.active_params is not None),
        key=lambda e: (e.active_params, -e.score),
    )
    frontier: list[Entry] = []
    best = float("-inf")
    for e in ordered:
        if e.score > best:
            frontier.append(e)
            best = e.score
    return frontier


def is_pareto(subject: Entry, peers: list[Entry]) -> bool:
    """True if no peer is both no-larger and higher-scoring than the subject."""
    if subject.active_params is None:
        return False
    return not any(
        p.active_params is not None
        and p.active_params <= subject.active_params
        and p.score > subject.score
        for p in peers
    )


def nearest_rival(subject: Entry, peers: list[Entry], *, max_gap: float = 2.0) -> Entry | None:
    """The closest-scoring peer at least as large as the subject, if within `max_gap`.

    A radar needs one named rival worth a head-to-head — this suggests a candidate
    (closest score among larger models) rather than picking one silently. Confirming
    it is the comparison actually worth making is still a drafting decision, per
    CONTRIBUTING.md's "one post, one claim": a same-lab prior generation or a specific
    well-known model may be the better story even when it is not the closest score.
    """
    if subject.active_params is None:
        return None
    larger = [
        p for p in peers
        if p.active_params is not None and p.active_params > subject.active_params
    ]
    if not larger:
        return None
    closest = min(larger, key=lambda p: abs(p.score - subject.score))
    return closest if abs(closest.score - subject.score) <= max_gap else None


@dataclass
class ChartRecommendation:
    chart: str  # "pareto" | "radar" | "bars"
    reason: str
    per_subject: dict[str, str] = field(default_factory=dict)


def recommend_chart(coh: Cohort, *, radar_max_gap: float = 2.0) -> ChartRecommendation:
    """Advisory chart pick per the decision tree in this module's docstring.

    Evaluated per subject, then combined: pareto wins if any subject qualifies (an
    efficiency claim is usually the strongest available), else radar if any subject has
    a rival within `radar_max_gap`, else bars.
    """
    per_subject: dict[str, str] = {}
    pareto_subjects = []
    radar_subjects: dict[str, Entry] = {}

    for s in coh.subjects:
        if is_pareto(s, coh.peers):
            per_subject[s.model] = "pareto: non-dominated among peers"
            pareto_subjects.append(s)
            continue
        rival = nearest_rival(s, coh.peers, max_gap=radar_max_gap)
        if rival:
            gap = abs(rival.score - s.score)
            # nearest_rival() only returns entries with a known, larger active_params
            # than a subject with a known active_params, so both are non-None here.
            ratio = (rival.active_params or 0) / (s.active_params or 1)
            per_subject[s.model] = (
                f"radar: {rival.model} within {gap:.2f} at {ratio:.1f}x the size"
            )
            radar_subjects[s.model] = rival
        else:
            per_subject[s.model] = "bars: no size-efficiency or single-rival story found"

    if pareto_subjects:
        names = ", ".join(s.model for s in pareto_subjects)
        return ChartRecommendation(
            "pareto", f"non-dominated among {len(coh.peers)} peers on {coh.benchmark}: {names}",
            per_subject,
        )
    if radar_subjects:
        model, rival = next(iter(radar_subjects.items()))
        return ChartRecommendation(
            "radar", f"{model} vs {rival.model} — {per_subject[model]}", per_subject,
        )
    return ChartRecommendation(
        "bars",
        f"no size-efficiency or single-rival story among {len(coh.peers)} peers on "
        f"{coh.benchmark}; ranked list is the safe default",
        per_subject,
    )


# ---------------------------------------------------------------------------------
# Card-data builders. Each returns exactly the #card-data schema the matching
# templates/model-release/card-*.html expects — pass the result straight to
# mtebpost.cards.write_card_data().
# ---------------------------------------------------------------------------------


def pareto_card_data(coh: Cohort, *, reference: Entry | None = None) -> dict:
    """Schema for templates/model-release/card-pareto.html.

    `reference` is a scale marker outside the peer band (see bekko: Qwen3-Embedding-8B)
    — it answers "where is the field overall" without stretching the axis to fit it.
    """
    subj_names = {s.model for s in coh.subjects}
    # A scatter needs a numeric x for every point — an entry with unknown active_params
    # has no honest position on this axis and is dropped, same as `Entry.plottable`
    # already excludes it from is_pareto()'s dominance check.
    plot_entries = [e for e in coh.peers + coh.subjects if e.active_params is not None]
    points = [
        {
            "model": e.model, "x": e.active_params, "total": e.total_params, "y": e.score,
            **({"subject": True} if e.model in subj_names else {}),
        }
        for e in plot_entries
    ]
    if reference is not None and reference.plottable:
        points.append({
            "model": reference.model, "x": reference.active_params,
            "total": reference.total_params, "y": reference.score, "reference": True,
        })
    return {
        "benchmark": coh.benchmark,
        "n_tasks": coh.n_benchmark_tasks,
        "max_active_params": coh.max_active or max((e.active_params or 0) for e in plot_entries),
        "n_models": len(plot_entries),
        "points": points,
    }


def radar_card_data(
    coh: Cohort,
    roles: dict[str, str],
    *,
    exclude_task_types: frozenset[str] = NEGATIVE_METRIC_TASK_TYPES,
    task_types: dict[str, str] | None = None,
) -> dict:
    """Schema for templates/model-release/card-radar.html.

    `roles` maps model name -> "subject" | "highlight" | "reference", exactly the
    series to draw (bekko: one subject, one highlight rival, up to a few reference
    peers). A "highlight" rival is often *outside* a size-banded cohort by design (the
    whole point is comparing against something larger) — this fetches any role model
    missing from `coh` directly, rather than requiring every radar series to already be
    in the peer band `cohort()` was built with.

    Axes are per-task-type means when `task_types` maps each of `coh.tasks`/the
    benchmark's tasks to its TaskType (get it from `leaderboard_api.task_type()`);
    without it, or when fewer than 3 types would result, axes fall back to individual
    tasks — the natural case for a domain-narrow custom cohort like a single-language
    retrieval slice, which may only span Retrieval + Reranking.
    """
    models = list(roles)
    entries_by_name = {e.model: e for e in coh.pool}
    missing = [m for m in models if m not in entries_by_name]
    if missing:
        raise SystemExit(
            f"no results on {coh.benchmark} for radar series: {missing} — pass "
            "cohort() a benchmark/task list wide enough to cover every role model"
        )

    per_task = coh.per_task
    types_by_task = task_types or {}

    common_types = None
    for m in models:
        types = {types_by_task[t] for t in per_task.get(m, {}) if t in types_by_task}
        types -= exclude_task_types
        common_types = types if common_types is None else common_types & types
    common_types = common_types or set()

    use_per_task = len(common_types) < 3
    if use_per_task:
        common_axes = None
        for m in models:
            axes = set(per_task.get(m, {}))
            common_axes = axes if common_axes is None else common_axes & axes
        axes_names = sorted(common_axes or [])
        axis_counts = {a: 1 for a in axes_names}
        values_of = per_task
    else:
        counts: dict[str, int] = {}
        for tt in types_by_task.values():
            counts[tt] = counts.get(tt, 0) + 1
        axes_names = sorted(common_types, key=lambda t: -counts.get(t, 0))
        axis_counts = counts
        values_of = {
            m: {
                tt: sum(v for t, v in per_task.get(m, {}).items() if types_by_task.get(t) == tt)
                / max(1, sum(1 for t in per_task.get(m, {}) if types_by_task.get(t) == tt))
                for tt in axes_names
            }
            for m in models
        }

    series = []
    for model, role in roles.items():
        e = entries_by_name[model]
        series.append({
            "model": model,
            "role": role,
            "active": e.active_params,
            "total": e.total_params,
            "mean": e.score,
            "values": [values_of.get(model, {}).get(a, 0) for a in axes_names],
        })

    return {
        "benchmark": coh.benchmark,
        "n_tasks": sum(axis_counts.get(a, 0) for a in axes_names),
        "axes": [{"name": a, "n_tasks": axis_counts.get(a, 0)} for a in axes_names],
        "excluded_axes": sorted(exclude_task_types),
        "series": series,
    }


def bars_card_data(
    coh: Cohort,
    *,
    top_n: int = 10,
    prior: tuple[str, ...] = (),
    size_field: str = "active",
) -> dict:
    """Schema for templates/model-release/card-bars.html.

    `prior` names a same-lab earlier generation, tagged distinctly from an unrelated
    peer (colvec11-vidore's within-lab comparison). `size_field` picks which parameter
    count labels each row — "active" for text models (matches the pareto/radar cards'
    axis), "total" when active-parameter counts are less meaningful for the comparison
    (image/document-retrieval models, say, where total is what a reader means by size).
    """
    ranking = coh.all_comparable
    subj_names = {s.model for s in coh.subjects}
    top = ranking[:top_n]
    # Always include subjects/prior even if they fall outside top_n, so the post's own
    # models are never silently dropped from their own card.
    must_include = [e for e in ranking if e.model in subj_names or e.model in prior]
    for e in must_include:
        if e not in top:
            top.append(e)
    top.sort(key=lambda e: e.score, reverse=True)

    # The row's rank on the whole board, not its position in the card's row list. A
    # subject outside top_n is appended above, so counting rows would print rank 11 for
    # a model lying 21st — a wrong number on the image, stated with the same confidence
    # as a right one.
    rank_of = {e.model: i for i, e in enumerate(ranking, 1)}
    rows = []
    for e in top:
        size = e.active_params if size_field == "active" else e.total_params
        rows.append({
            "model": e.model, "score": e.score, "params": size, "rank": rank_of[e.model],
            **({"subject": True} if e.model in subj_names else {}),
            **({"prior": True} if e.model in prior else {}),
        })
    return {
        "benchmark": coh.benchmark,
        "n_tasks": coh.n_benchmark_tasks,
        "n_models": len(ranking),
        "rows": rows,
    }
