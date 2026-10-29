#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["mtebpost"]
#
# [tool.uv.sources]
# mtebpost = { path = "../../..", editable = true }
# ///
"""Evidence for the LanguageBind post. Run from the repo root:

    uv run posts/3-review/languagebind-omni/fetch.py

mteb#4557 (myang333) adds wrappers for LanguageBind's video, audio and image encoders,
plus `LanguageBind/LanguageBind_Omni` — a composite with no checkpoint of its own, which
dispatches each input to the sub-model for its modality and shares the OpenCLIP text
tower across all three. results#683 (isaac-chung) submits its results.

LanguageBind is from October 2023 (arXiv:2310.01852, ICLR 2024). Everything else on
MTEB's audio-video board was released in 2025 or later, so this is the first entry on it
that predates the current generation — which is the post: a board with no starting point
cannot show how far it has come.

**Scope, and why this post is currently blocked on it.** `LanguageBind_Omni` has 18 of
`MVEB(beta)`'s 23 tasks, so there is no registered benchmark it completes and the cohort
has to be those 18 tasks plus every model complete on all of them. That much follows the
most-embed-de precedent. What does not is the reason for the gap: **every other model on
this board has run all 23**, so the slice is defined by this one submission's omissions
rather than by what anyone has evaluated — and the check at the bottom of this script
shows the slice is not neutral. Dropping those five tasks raises every peer's score by
3.06 points on average (max 5.43) and swaps two pairs of ranks, so a number computed on
it cannot be set beside the board's published numbers.

The honest fix is more results, not a better caption. Left as `blocked_on:` until the
remaining five tasks are submitted, at which point this becomes a full-board post and
this script's slice logic can go.
"""

import json
import pathlib
from datetime import date

from mtebpost.cards import write_card_data
from mtebpost.leaderboard_api import benchmark_task_scores
from mtebpost.model_release import bars_card_data, cohort, recommend_chart

BENCHMARK = "MVEB(beta)"
SUBJECT = "LanguageBind/LanguageBind_Omni"
HERE = pathlib.Path(__file__).parent


def main() -> None:
    all_tasks, per_model = benchmark_task_scores(BENCHMARK)
    ran = sorted(per_model[SUBJECT])
    print(f"{SUBJECT} ran {len(ran)} of {BENCHMARK}'s {len(all_tasks)} tasks")
    print(f"  not run: {sorted(set(all_tasks) - set(ran))}\n")

    # text_only=False: this is an audio-video board and its entrants are multimodal
    # encoders. The text filter exists to keep English-only text models off a
    # multilingual text board; here it would only remove intended competition.
    coh = cohort([SUBJECT], ran, name=f"{BENCHMARK}, audio-video", text_only=False)
    ranking = coh.all_comparable
    subject = coh.subjects[0]
    rank = ranking.index(subject) + 1

    rec = recommend_chart(coh)
    print(f"recommend_chart: {rec.chart} — {rec.reason}\n")

    for i, e in enumerate(ranking, 1):
        mark = "  <<< subject" if e.model == SUBJECT else ""
        print(f"  {i:>2}  {e.score:>6}  {e.release_date}  {(e.total_params or 0)/1e9:>5.2f}B  {e.model}{mark}")

    older = [e for e in ranking if e.release_date and e.release_date < subject.release_date]
    best = ranking[0]
    print(f"\nsubject: rank {rank} of {len(ranking)}, {subject.score}, released {subject.release_date}")
    print(f"best on the slice: {best.model}, {best.score}, released {best.release_date}")
    print(f"models on this board older than the subject: {[e.model for e in older]}")
    print(f"models below the subject: {[e.model for e in ranking[rank:]]}")

    # The claim the post leads with: nothing else here predates the subject, and the
    # 2025-onward field tops out 14 points above it. Both are assertions, not readings.
    assert not older, older
    assert all(e.release_date >= "2025-01-01" for e in ranking if e.model != SUBJECT)

    # Is the slice neutral? Recompute the peers both ways — on all 23 tasks, and on the
    # 18 the subject ran. If dropping five tasks moves everyone, the subject's score is
    # not on the same scale as the board's published numbers, whatever the cohort says.
    complete_23 = [m for m, sc in per_model.items() if len(sc) == len(all_tasks)]
    full_view = {m: sum(per_model[m].values()) / len(all_tasks) for m in complete_23}
    slice_view = {m: sum(per_model[m][t] for t in ran) / len(ran) for m in complete_23}
    deltas = [slice_view[m] - full_view[m] for m in complete_23]
    order_full = sorted(complete_23, key=lambda m: -full_view[m])
    order_slice = sorted(complete_23, key=lambda m: -slice_view[m])
    mean_shift = sum(deltas) / len(deltas)
    print(f"\nmodels complete on all {len(all_tasks)} tasks: {len(complete_23)} "
          f"(of {len(ranking)} in the cohort — the subject is the only incomplete one)")
    print(f"dropping the 5 tasks it did not run shifts peers by {mean_shift:+.2f} on "
          f"average (max {max(abs(d) for d in deltas):.2f})")
    print(f"peer order preserved by the slice: {order_full == order_slice}")

    evidence = {
        "generated": date.today().isoformat(),
        "slice_is_not_neutral": {
            "n_models_complete_on_full_benchmark": len(complete_23),
            "subject_is_only_incomplete_model": len(complete_23) == len(ranking) - 1,
            "mean_shift_from_dropping_5_tasks": round(mean_shift, 2),
            "max_shift": round(max(abs(d) for d in deltas), 2),
            "peer_order_preserved": order_full == order_slice,
        },
        "benchmark": BENCHMARK,
        "scope": {
            "why": f"{SUBJECT} has {len(ran)} of {BENCHMARK}'s {len(all_tasks)} tasks; "
                   "no registered benchmark it completes",
            "tasks": ran,
            "not_run": sorted(set(all_tasks) - set(ran)),
        },
        "n_models": len(ranking),
        "subject": SUBJECT,
        "subject_rank": rank,
        "subject_score": subject.score,
        "subject_release_date": subject.release_date,
        "best": {"model": best.model, "score": best.score, "release_date": best.release_date},
        "gap_to_best": round(best.score - subject.score, 2),
        "per_task": {t: s for t, s in sorted(coh.per_task[SUBJECT].items())},
        "ranking": [e.as_dict() for e in ranking],
    }
    (HERE / "data.json").write_text(json.dumps(evidence, indent=2) + "\n")

    # Release date on every row: the claim is about when these models are from, so the
    # date has to be on the image making it, not only in the post text.
    by_name = {e.model: e for e in ranking}
    data = bars_card_data(coh, top_n=10, size_field="total")
    for row in data["rows"]:
        row["released"] = (by_name[row["model"]].release_date or "")[:4]
    write_card_data(HERE / "card-1-languagebind-omni.html", data)
    print(f"\nwrote data.json ({len(ranking)} rows) and card data (top 10 + subject)")


if __name__ == "__main__":
    main()
