#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["mtebpost"]
#
# [tool.uv.sources]
# mtebpost = { path = "../../..", editable = true }
# ///
"""Evidence for the embeddinggemma-2 post. Run from the repo root:

    uv run posts/2-drafting/embeddinggemma-2/fetch.py

mteb#5588 (schechterh, merged 2026-10-18) registers `google/embeddinggemma-2`;
results#793 (KennethEnevoldsen, merged 2026-10-19) submits its results. An earlier
companion results PR in the mteb body (results#745, schechterh) was closed unmerged,
so the pairing the candidate note guessed from title overlap is real but the numbers
in the post come from #793.

The claim is about *breadth*, and breadth is the one thing a rank on a single board
cannot show. So the script asks the same question three times — who has complete
results on MTEB(Multilingual, v2), on MIEB(lite), on MAEB(v1) — and then asks the
question that only exists at the intersection: how many models can be compared across
all three at once. Four can. That cohort is the post's scope, and `data.json` keeps
every complete row on every board, not just the ones that flatter the subject.

Two things this script records rather than asserts:

* **MIEB(lite)'s `meanTask` is not an unweighted mean of its tasks.** On the other two
  boards the API's aggregate reproduces task-by-task averaging to 0.005; on MIEB it
  does not (worst case 6.06 points). The leaderboard's own aggregation is therefore
  what the post quotes, and the per-model delta is written to `data.json` so nobody
  later "fixes" the number by averaging the tasks themselves.
* **Parameter counts on a multi-tower model are per-experiment.** The registry row
  reports one count for the model name, and the results files do not record which
  towers a run loaded, so a size claim about the image or audio scores is not
  measurable from the results repo. The post therefore makes no size claim; the
  caveat lives here and in `post.md`.
"""

from __future__ import annotations

import json
import pathlib
from datetime import date

from mtebpost.cards import write_card_data
from mtebpost.leaderboard_api import benchmark_scores, benchmark_task_scores

SUBJECT = "google/embeddinggemma-2"
PREDECESSOR = "google/embeddinggemma-300m"
BENCHMARKS = ["MTEB(Multilingual, v2)", "MIEB(lite)", "MAEB(v1)"]
HERE = pathlib.Path(__file__).parent


def billions(n: int | None) -> float | None:
    return round(n / 1e9, 4) if n is not None else None


def board(name: str) -> dict:
    """Everything the post needs about one benchmark, plus every complete row on it."""
    tasks, per_model = benchmark_task_scores(name)
    entries, _ = benchmark_scores(name)
    by_model = {e.model: e for e in entries}

    complete = [m for m in per_model if len(per_model[m]) == len(tasks)]
    # A complete task set and a missing meanTask would mean the API does not consider
    # the row aggregable — that would silently change every rank below it.
    missing_aggregate = sorted(m for m in complete if m not in by_model)
    if missing_aggregate:
        raise SystemExit(f"{name}: complete but no meanTask: {missing_aggregate}")

    ranking = sorted(complete, key=lambda m: by_model[m].score, reverse=True)
    if SUBJECT not in ranking:
        raise SystemExit(f"{SUBJECT} has no complete {name} row ({len(per_model[SUBJECT])} "
                         f"of {len(tasks)} tasks) — the post's premise is gone")

    rank = ranking.index(SUBJECT) + 1
    subj = by_model[SUBJECT]

    # How far the API's meanTask sits from a plain average of the same tasks, per model.
    deltas = {
        m: round(sum(per_model[m][t] for t in tasks) / len(tasks) - by_model[m].score, 3)
        for m in ranking
    }

    return {
        "benchmark": name,
        "n_tasks": len(tasks),
        "n_models_with_any_result": len(per_model),
        "n_models_complete": len(ranking),
        "n_models_partial": len(per_model) - len(ranking),
        "n_rows_with_meanTask": len(entries),
        "subject": {
            "model": SUBJECT,
            "mean_task": subj.score,
            "rank": rank,
            "n_tasks": subj.n_tasks,
            "unweighted_task_mean": round(sum(per_model[SUBJECT].values()) / len(tasks), 2),
            "mean_task_minus_unweighted": deltas[SUBJECT],
        },
        "mean_task_vs_unweighted": {
            "max_abs_delta": max(abs(d) for d in deltas.values()),
            "note": ("meanTask reproduces an unweighted task mean on this board"
                     if max(abs(d) for d in deltas.values()) <= 0.01 else
                     "meanTask is a weighted/structured aggregate on this board; the API "
                     "value is quoted as-is and is NOT the plain average of its tasks"),
        },
        "models_above_subject": [
            {
                "model": m,
                "mean_task": by_model[m].score,
                "gap_to_subject": round(by_model[m].score - subj.score, 2),
                "total_params_b": billions(by_model[m].total_params),
                "active_params_b": billions(by_model[m].active_params),
                "release_date": by_model[m].release_date,
                "modalities": list(by_model[m].modalities),
            }
            for m in ranking[: rank - 1]
        ],
        "ranking": [
            {
                "rank": i,
                "model": m,
                "mean_task": by_model[m].score,
                "total_params_b": billions(by_model[m].total_params),
                "active_params_b": billions(by_model[m].active_params),
                "release_date": by_model[m].release_date,
                "modalities": list(by_model[m].modalities),
                "complete": True,
            }
            for i, m in enumerate(ranking, 1)
        ],
    }


def text_context() -> dict:
    """The subject against its predecessor on the English board.

    Not used in the post text: the post's three boards are the general ones it can be
    compared across, and mixing a fourth board into a claim about cross-modal coverage
    would blur the scope. Recorded because the reviewer's first question about a
    *successor* model is whether it beats the model it replaces, and that answer should
    come out of this folder rather than out of a conversation.
    """
    name = "MTEB(eng, v2)"
    tasks, per_model = benchmark_task_scores(name)
    entries, _ = benchmark_scores(name)
    by_model = {e.model: e for e in entries}
    complete = [m for m in per_model
                if len(per_model[m]) == len(tasks) and m in by_model]
    ranking = sorted(complete, key=lambda m: by_model[m].score, reverse=True)
    return {
        "benchmark": name,
        "n_tasks": len(tasks),
        "n_models_complete": len(ranking),
        "used_in_post": False,
        "models": {
            m: ({"mean_task": by_model[m].score, "rank": ranking.index(m) + 1}
                if m in ranking else None)
            for m in (SUBJECT, PREDECESSOR)
        },
    }


def main() -> None:
    boards = {name: board(name) for name in BENCHMARKS}
    complete = {name: [r["model"] for r in b["ranking"]] for name, b in boards.items()}

    all_three = sorted(
        set.intersection(*(set(v) for v in complete.values())),
        key=lambda m: -{r["model"]: r["mean_task"] for r in boards[BENCHMARKS[0]]["ranking"]}[m],
    )
    two_of_three = {
        m: sorted(n for n, v in complete.items() if m in v)
        for m in set().union(*(set(v) for v in complete.values()))
        if 1 < sum(m in v for v in complete.values()) < 3
    }

    # The cohort the claim is scoped to: models complete on all three, with their row on
    # each board. Sizes are the registry's, which are per-model, not per-experiment.
    rows = {}
    for name in BENCHMARKS:
        rows[name] = {r["model"]: r for r in boards[name]["ranking"]}
    cohort = [
        {
            "model": m,
            "mean_task": {name: rows[name][m]["mean_task"] for name in BENCHMARKS},
            "rank": {name: rows[name][m]["rank"] for name in BENCHMARKS},
            "total_params_b": rows[BENCHMARKS[0]][m]["total_params_b"],
            "active_params_b": rows[BENCHMARKS[0]][m]["active_params_b"],
            "release_date": rows[BENCHMARKS[0]][m]["release_date"],
            "modalities": rows[BENCHMARKS[0]][m]["modalities"],
        }
        for m in all_three
    ]
    order = {name: [c["model"] for c in sorted(cohort, key=lambda c: -c["mean_task"][name])]
             for name in BENCHMARKS}

    # "Who is missing": the top of the board the default benchmark measures, checked
    # against the two boards that require image and audio runs. A rank on MIEB or MAEB
    # is a fact about who submitted there.
    top20 = [r["model"] for r in boards["MTEB(Multilingual, v2)"]["ranking"][:20]]
    top20_coverage = []
    for m in top20:
        entry = {"model": m}
        for name in BENCHMARKS[1:]:
            if m in rows[name]:
                entry[name] = "complete"
            else:
                entry[name] = "partial" if m in benchmark_task_scores(name)[1] else "none"
        top20_coverage.append(entry)

    # "Who is missing" cuts two ways, and the second way is the one that matters for this
    # post. The top of MIEB and MAEB is *not* in the four-model cohort: those models ran
    # only part of MTEB(Multilingual, v2), so they are absent from any cross-modal
    # comparison on complete rows. If the subject's image rank is quoted, the leader it
    # is missing has to be named.
    ml_per_model = benchmark_task_scores(BENCHMARKS[0])[1]

    def ml_coverage(model: str) -> dict:
        return {
            "benchmark": BENCHMARKS[0],
            "tasks_run": len(ml_per_model.get(model, {})),
            "n_tasks": boards[BENCHMARKS[0]]["n_tasks"],
        }

    excluded_leaders = {
        name: [
            {"model": r["model"], "mean_task": r["mean_task"], "rank": r["rank"],
             "multilingual_v2": ml_coverage(r["model"])}
            for r in boards[name]["ranking"][:5]
            if r["model"] not in all_three
        ]
        for name in BENCHMARKS[1:]
    }
    near_miss_detail = {
        m: {"complete_on": v, "multilingual_v2": ml_coverage(m)}
        for m, v in sorted(two_of_three.items())
    }

    evidence = {
        "generated": date.today().isoformat(),
        "subject": SUBJECT,
        "predecessor": PREDECESSOR,
        "source": {
            "registry": "https://github.com/embeddings-benchmark/mteb/pull/5588",
            "results": "https://github.com/embeddings-benchmark/results/pull/793",
            "api": "https://mteb-leaderboard-backend.hf.space/v1/benchmarks/<name>/scores",
            "module": "mtebpost.leaderboard_api.benchmark_scores / benchmark_task_scores",
        },
        "benchmarks": boards,
        "cohort_complete_on_all_three": {
            "n_models": len(all_three),
            "models": cohort,
            "order": order,
            "how_many_boards_each_top": {
                m: sum(order[name][0] == m for name in BENCHMARKS) for m in all_three
            },
        },
        "near_misses_complete_on_two": near_miss_detail,
        "board_leaders_excluded_from_cohort": excluded_leaders,
        "context_not_used_in_post": text_context(),
        "who_is_missing": {
            "question": ("coverage of the top 20 MTEB(Multilingual, v2) models on the "
                         "image and audio boards"),
            "top20_multilingual_v2_vs_mieb_and_maeb": top20_coverage,
            "n_top20_with_complete_mieb": sum(e["MIEB(lite)"] == "complete"
                                              for e in top20_coverage),
            "n_top20_with_complete_maeb": sum(e["MAEB(v1)"] == "complete"
                                              for e in top20_coverage),
            "n_top20_with_neither": sum(e["MIEB(lite)"] == "none" and e["MAEB(v1)"] == "none"
                                        for e in top20_coverage),
        },
        "caveats": {
            "parameter_counts": (
                "total_params_b/active_params_b are the registry row for the model name. "
                "`google/embeddinggemma-2` is registered under several tower "
                "configurations (use_image / use_audio in "
                "mteb/models/model_implementations/google_embeddinggemma.py) and the "
                "wrapper reports the loaded towers' count at run time, but the results "
                "files record no tower config. So no size is quoted for the image or "
                "audio scores, and the post makes no size claim."
            ),
            "predecessor": (
                f"{PREDECESSOR} is a text-only model and has no complete MIEB or MAEB "
                "row, so it belongs in a text comparison only."
            ),
            "cohort": (
                "the four-model cohort is who submitted complete results, not who can "
                "run all three; the big text models have no image or audio results at "
                "all (see who_is_missing)."
            ),
        },
    }
    (HERE / "data.json").write_text(json.dumps(evidence, indent=2) + "\n")

    # The card is a table of the four-model cohort, so its values are exactly `cohort`
    # and the per-board task counts — nothing the card draws is computed anywhere else.
    # Copy stays in the card's COPY object, per docs/card-design.md.
    card = HERE / "card-1-embeddinggemma-2.html"
    if card.exists():
        write_card_data(card, {
            "eyebrow": "NEW ON MTEB",
            "boards": [
                {"name": name, "n_tasks": boards[name]["n_tasks"],
                 "n_complete": boards[name]["n_models_complete"]}
                for name in BENCHMARKS
            ],
            "rows": [
                {"model": c["model"], "total_params_b": c["total_params_b"],
                 "subject": c["model"] == SUBJECT,
                 "scores": c["mean_task"], "ranks": c["rank"]}
                for c in cohort
            ],
        })
        print(f"card data -> {card.name}")

    # ---- report ---------------------------------------------------------------
    for name in BENCHMARKS:
        b = boards[name]
        s = b["subject"]
        print(f"{name}: {b['n_tasks']} tasks, {b['n_models_complete']} complete "
              f"(of {b['n_models_with_any_result']} with any result)")
        print(f"  subject {s['mean_task']}  rank {s['rank']}/{b['n_models_complete']}  "
              f"(unweighted task mean {s['unweighted_task_mean']}, "
              f"delta {s['mean_task_minus_unweighted']:+.2f}; board max "
              f"{b['mean_task_vs_unweighted']['max_abs_delta']:.2f})")
        print(f"  above: {[(m['model'], m['mean_task'], m['total_params_b']) for m in b['models_above_subject']]}")
        print()

    print(f"complete on all three: {len(all_three)}")
    for c in cohort:
        print(f"  {c['model']:<48} "
              + "  ".join(f"{n.split('(')[0][:9]!s} {c['mean_task'][n]:>6}" for n in BENCHMARKS)
              + f"  tot={c['total_params_b']}B  {c['release_date']}")
    print(f"  first on each board: { {n: order[n][0] for n in BENCHMARKS} }")
    print(f"  subject first on: {[n for n in BENCHMARKS if order[n][0] == SUBJECT]}")
    print(f"  subject last on:  {[n for n in BENCHMARKS if order[n][-1] == SUBJECT]}")

    wm = evidence["who_is_missing"]
    print(f"\ntop 20 MTEB(Multilingual, v2) models with complete MIEB(lite): "
          f"{wm['n_top20_with_complete_mieb']}, complete MAEB(v1): "
          f"{wm['n_top20_with_complete_maeb']}, neither: {wm['n_top20_with_neither']}")
    print(f"near misses (complete on two of three): {sorted(two_of_three)}")
    for name, rows_ in excluded_leaders.items():
        print(f"\ntop of {name} not in the cohort:")
        for r in rows_:
            print(f"  {r['rank']:>2} {r['mean_task']:>6}  {r['model']:<45} "
                  f"multilingual v2: {r['multilingual_v2']['tasks_run']}"
                  f"/{r['multilingual_v2']['n_tasks']} tasks")
    print(f"\nwrote data.json ({sum(b['n_models_complete'] for b in boards.values())} "
          f"complete rows across three boards)")

    # ---- the claims the post makes, as assertions ------------------------------
    # If any of these stops holding, the draft is wrong and this run should fail loudly
    # rather than leave a stale data.json that looks current.
    problems = []
    if len(all_three) != 4:
        problems.append(f"cohort is {len(all_three)}, not the 4 the post states")
    if order[BENCHMARKS[1]][0] != SUBJECT:
        problems.append(f"subject is not first on MIEB(lite): {order[BENCHMARKS[1]][0]}")
    for name in (BENCHMARKS[0], BENCHMARKS[2]):
        if order[name][-1] != SUBJECT:
            problems.append(f"subject is not last on {name}: {order[name][-1]}")
        if order[name][0] == SUBJECT:
            problems.append(f"subject is first on {name}, so 'last on text/audio' is moot")
    if problems:
        raise SystemExit("CLAIM NO LONGER HOLDS: " + "; ".join(problems))


if __name__ == "__main__":
    main()
