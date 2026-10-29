#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["mtebpost"]
#
# [tool.uv.sources]
# mtebpost = { path = "../../..", editable = true }
# ///
"""Evidence for the embeddinggemma-2 post. Run from the repo root:

    uv run posts/3-review/embeddinggemma-2/fetch.py

mteb#5588 (schechterh, merged 2026-10-18) registers `google/embeddinggemma-2`;
results#793 (KennethEnevoldsen, merged 2026-10-19) submits its results. An earlier
companion results PR in the mteb body (results#745) was closed unmerged, so the numbers in
the post come from #793.

The first draft compared four models that happened to be complete on three benchmarks.
Review killed that for the right reason: the intersection of complete submissions is a fact
about who submitted, and most models never run every board. So this script asks the
question per board instead — for every benchmark the model has results on, where does it
sit among the models that completed *that* board.

That makes the table a transposition: benchmarks are the rows, each with its own cohort.
Boards where the model ran only part of the tasks are recorded with their coverage and no
rank rather than dropped, because "ran 66 of 73 tasks" is a fact a reader can use and
hiding it would make the row look like a full result.

`BENCHMARK_GROUPS` is presentation only — it decides which column of the card a board lands
in. Every number in `data.json` comes from the API.
"""

from __future__ import annotations

import json
import pathlib
import urllib.parse
from datetime import date

from mtebpost.cards import write_card_data
from mtebpost.leaderboard_api import _get

SUBJECT = "google/embeddinggemma-2"
PREDECESSOR = "google/embeddinggemma-300m"
HERE = pathlib.Path(__file__).parent
CARD = HERE / "card-1-embeddinggemma-2.html"

MULTILINGUAL_V2 = "MTEB(Multilingual, v2)"

# Which column a board belongs in, and the order it is listed in. Presentation grouping,
# not data: a board with no entry here still lands in `data.json` under "Other", so a new
# benchmark in the registry is recorded and simply not drawn.
BENCHMARK_GROUPS: dict[str, list[str]] = {
    "Multilingual": [MULTILINGUAL_V2, "MTEB(eng, v2)", "MTEB(Europe, v1)", "MTEB(Indic, v1)"],
    "Image": ["MIEB(lite)", "MIEB(eng)", "MIEB(Multilingual)", "MIEB(Img)", "ViDoRe(v1&v2)"],
    "Audio": ["MAEB(v1)", "MAEB(v1, audio-only)", "MVEB(v1)"],
    "Code": ["MTEB(Code, v1)", "CoIR"],
    "Other": ["FollowIR", "BEIR", "LongEmbed", "MTEB(Law, v1)", "MTEB(Medical, v1)"],
}
GROUP_OF = {b: g for g, boards in BENCHMARK_GROUPS.items() for b in boards}
CARD_GROUPS = ("Multilingual", "Image", "Audio", "Code")


def benchmark_names() -> list[str]:
    """Every benchmark the scores endpoint serves.

    `/v1/benchmarks` is not the full list: `MTEB(Multilingual, v2)`, `MTEB(eng, v2)`, MIEB
    and MAEB all resolve when requested directly while the listing omits them. Ask both.
    """
    listed = [b["name"] for b in _get("/v1/benchmarks")]
    return list(dict.fromkeys([*listed, MULTILINGUAL_V2, "MTEB(eng, v2)"]))


def complete_rows(payload: dict) -> list[dict]:
    """Every model that ran *all* of a board's tasks, best first.

    Partial coverage is excluded from the ranking, not averaged in: a mean over a subset of
    tasks is not comparable to a mean over all of them, which is the mistake MTEB will make
    for you if you let it.
    """
    tasks = set(payload["tasks"])
    rows = []
    for r in payload["rows"]:
        if len(tasks.intersection(r["scoresByTask"])) != len(tasks):
            continue
        if r.get("meanTask") is None:
            continue
        rows.append({
            "model": r["model"]["name"],
            "short": r["model"]["name"].split("/")[-1],
            "score": round(r["meanTask"] * 100, 2),
            "active_params_b": r["model"].get("activeParamsB"),
            "total_params_b": r["model"].get("totalParamsB"),
            "open_weights": bool(r["model"].get("openWeights")),
        })
    return sorted(rows, key=lambda r: -r["score"])


def board(name: str) -> dict:
    """One benchmark: the subject's position among the models that completed it."""
    try:
        payload = _get(f"/v1/benchmarks/{urllib.parse.quote(name)}/scores")
    except SystemExit:
        return {"name": name, "found": False}

    tasks = set(payload["tasks"])
    subject = next((r for r in payload["rows"] if r["model"]["name"] == SUBJECT), None)
    if subject is None:
        return {"name": name, "found": False}

    complete = complete_rows(payload)
    rank = next((i for i, r in enumerate(complete, 1) if r["model"] == SUBJECT), None)
    covered = len(tasks.intersection(subject["scoresByTask"]))
    mean = subject.get("meanTask")

    return {
        "name": name,
        "found": True,
        "group": GROUP_OF.get(name, "Other"),
        "n_tasks": len(tasks),
        "n_models_any_result": len(payload["rows"]),
        "n_models_complete": len(complete),
        "subject_tasks_run": covered,
        "subject_complete": covered == len(tasks),
        "subject_score": None if mean is None else round(mean * 100, 2),
        "subject_rank": rank,
        # Named so a rank is checkable from the folder without calling the API again.
        "above": complete[: rank - 1] if rank else [],
        "complete": complete,
    }


def predecessor_context() -> dict:
    """The previous generation, on the one board both are complete on."""
    payload = _get(f"/v1/benchmarks/{urllib.parse.quote(MULTILINGUAL_V2)}/scores")
    complete = {r["model"]: r["score"] for r in complete_rows(payload)}
    return {
        "benchmark": MULTILINGUAL_V2,
        "scores": {m: complete[m] for m in (SUBJECT, PREDECESSOR) if m in complete},
    }


# One column per benchmark, under a joint heading where two boards measure the same
# thing. Partial boards are not here at all: review was right that a row without a
# comparable mean does not belong in a comparison table.
COLUMNS: list[tuple[str, list[str]]] = [
    ("Multilingual", ["MTEB(Multilingual, v2)"]),
    ("English", ["MTEB(eng, v2)"]),
    ("Image", ["MIEB(lite)"]),
    ("Audio", ["MAEB(v1)"]),
    ("Code", ["MTEB(Code, v1)", "CoIR"]),
]

# Named competitors. Both are multimodal and small, which is the comparison the post is
# making; neither has code results, and a missing result is shown as missing.
NAMED = ["jinaai/jina-embeddings-v5-omni-small", "BidirLM/BidirLM-Omni-2.5B-Embedding"]

# "Under 1B" is total parameters, from the registry. The subject is under 1B on any of its
# tower configurations (271M text-only, 744M with every tower), so the claim does not
# depend on which configuration a run loaded.
SMALL_TOTAL_B = 1.0


def _pick(complete: list[dict], *, open_required: bool = False,
          max_total: float | None = None) -> dict | None:
    for r in complete:
        if open_required and not r["open_weights"]:
            continue
        if max_total is not None and (r["total_params_b"] or 99) > max_total:
            continue
        return r
    return None


def card_data(found: dict) -> dict:
    """One column per benchmark: the ceiling, the open-weight ceiling, the ceiling under
    1B parameters, the two named competitors, and the subject.

    Rows 1-3 name a different model in every column, so each cell carries its own org and
    model name. The rows below are one model across the whole table, so the label names it
    once and the cells carry only the score.
    """
    columns = []
    for group, names in COLUMNS:
        for name in names:
            b = found.get(name)
            if not b or not b.get("found") or not b["subject_complete"]:
                continue
            complete = b["complete"]
            rows = []

            def add(label: str, r: dict | None, *, fixed: bool = False, **extra) -> None:
                rows.append({
                    "label": label,
                    "model": r["model"] if r else None,
                    "score": r["score"] if r else None,
                    "params_b": r["total_params_b"] if r else None,
                    "fixed": fixed,
                    **extra,
                })

            add("Best open weights", _pick(complete, open_required=True), muted=True)
            add("Best open, ≤1B params",
                _pick(complete, open_required=True, max_total=SMALL_TOTAL_B))
            for model in NAMED:
                add(model, next((x for x in complete if x["model"] == model), None), fixed=True)
            add(SUBJECT, next((x for x in complete if x["model"] == SUBJECT), None),
                fixed=True, subject=True)

            columns.append({
                "group": group,
                "benchmark": name,
                "rows": rows,
            })
    return {"eyebrow": "NEW ON MTEB", "columns": columns}


def main() -> None:
    boards = {name: board(name) for name in benchmark_names()}
    found = {k: v for k, v in boards.items() if v["found"]}
    complete = {k: v for k, v in found.items() if v["subject_complete"]}

    evidence = {
        "generated": date.today().isoformat(),
        "subject": SUBJECT,
        "predecessor": PREDECESSOR,
        "source": {
            "registry": "https://github.com/embeddings-benchmark/mteb/pull/5588",
            "results": "https://github.com/embeddings-benchmark/results/pull/793",
            "api": "https://mteb-leaderboard-backend.hf.space/v1/benchmarks/<name>/scores",
            "module": "mtebpost.leaderboard_api._get",
        },
        "how_to_read": (
            "subject_rank is the position among models with complete results on that board "
            "only. Where subject_complete is false there is no comparable mean, so coverage "
            "is reported instead of a rank. `complete` holds every complete row on the "
            "board, so any rank can be re-derived and the models ahead are in `above`."
        ),
        "summary": {
            "n_benchmarks_served": len(boards),
            "n_with_any_result": len(found),
            "n_complete": len(complete),
            "complete_boards": sorted(complete),
        },
        "boards": found,
        "predecessor_context": predecessor_context(),
        "caveats": {
            "not_video": (
                "The registry lists video, but MVEB(v1) has no row for this model, so the "
                "post does not claim video."
            ),
            "partial_boards": (
                "MTEB(Europe), MTEB(Indic), MIEB(eng), MIEB(Multilingual), MIEB(Img) and "
                "ViDoRe are partial: the merged results cover some tasks and not others, so "
                "no mean is comparable. They appear with coverage and no rank."
            ),
            "parameter_counts": (
                "One ModelMeta covers several tower configurations (use_image / use_audio) "
                "and the results files record no tower config, so size is quoted once from "
                "the registry and never attached to a modality's score."
            ),
            "followir": (
                "FollowIR's main score is p-MRR: centred on zero, can be negative, and not "
                "comparable to an accuracy mean. It is why it is not in the card."
            ),
        },
    }
    (HERE / "data.json").write_text(json.dumps(evidence, indent=2) + "\n")

    if CARD.exists():
        write_card_data(CARD, card_data(found))
        print(f"card data -> {CARD.name}")

    print(f"{len(found)} boards with a result, {len(complete)} complete\n")
    for group in CARD_GROUPS:
        printed = False
        for name in BENCHMARK_GROUPS[group]:
            b = boards.get(name)
            if not b or not b.get("found") or b["subject_score"] is None:
                continue
            if not printed:
                print(f"{group}:")
                printed = True
            depth = (f"rank {b['subject_rank']} of {b['n_models_complete']}"
                     if b["subject_complete"]
                     else f"{b['subject_tasks_run']}/{b['n_tasks']} tasks, partial")
            print(f"  {name:<26} {b['subject_score']:>6.2f}   {depth}")
    print("\npredecessor:", evidence["predecessor_context"])
    print("complete on:", ", ".join(evidence["summary"]["complete_boards"]))


if __name__ == "__main__":
    main()
