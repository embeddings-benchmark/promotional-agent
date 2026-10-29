---
id: embeddinggemma-2
type: model_addition
trigger: mteb#5588 + results#793
trigger_date: 2026-10-18
expires: 2026-11-18
subject: google/embeddinggemma-2
verified: true
evidence: data.json
media: card-1-embeddinggemma-2.png
thread: 2
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5588
  - https://github.com/embeddings-benchmark/results/pull/793
  - https://huggingface.co/google/embeddinggemma-2
---

```
New on MTEB: google/embeddinggemma-2, an open-weights model that handles text, images and audio.

Only four models have complete results on all three general benchmarks (MTEB(Multilingual, v2), MIEB(lite), MAEB(v1)). Among them it leads on images and trails on text and audio.
```

```
MIEB(lite) 63.52 (5th of 51), MTEB(Multilingual, v2) 60.52 (33rd of 96), MAEB(v1) 49.31 (7th of 23). On text it sits below its predecessor google/embeddinggemma-300m, at 61.14.

Added to MTEB by schechterh; results submitted by KennethEnevoldsen.
```

## LinkedIn

The two parts of the thread joined, word for word, with no numbering to drop.

```linkedin
New on MTEB: google/embeddinggemma-2, an open-weights model that handles text, images and audio.

Only four models have complete results on all three general benchmarks (MTEB(Multilingual, v2), MIEB(lite), MAEB(v1)). Among them it leads on images and trails on text and audio.

MIEB(lite) 63.52 (5th of 51), MTEB(Multilingual, v2) 60.52 (33rd of 96), MAEB(v1) 49.31 (7th of 23). On text it sits below its predecessor google/embeddinggemma-300m, at 61.14.

Added to MTEB by schechterh; results submitted by KennethEnevoldsen.
```

## The claim

`google/embeddinggemma-2` is complete on all three of MTEB's general benchmarks at once —
`MTEB(Multilingual, v2)` (131 tasks), `MIEB(lite)` (51), `MAEB(v1)` (30) — and it is one
of only four models that are. That four-model cohort is the post's scope: they are the
only models for which a text, an image and an audio score all exist.

| model (total params) | Multilingual v2 | MIEB(lite) | MAEB(v1) |
|---|---:|---:|---:|
| `jinaai/jina-embeddings-v5-omni-small` (1.626B) | **67.00** (13/96) | 61.07 (6/51) | 50.41 (5/23) |
| `jinaai/jina-embeddings-v5-omni-nano` (0.986B) | 65.52 (17/96) | 49.38 (25/51) | 50.14 (6/23) |
| `BidirLM/BidirLM-Omni-2.5B-Embedding` (2.445B) | 63.50 (24/96) | 55.96 (10/51) | **52.36** (3/23) |
| `google/embeddinggemma-2` (0.271B) | 60.52 (33/96) | **63.52** (5/51) | 49.31 (7/23) |

Mean(Task) and rank among models with complete results on that board. Bold marks the best
of the four on each board.

**What that supports.** Within these four the subject is first on one board and last on
the other two: it leads on images and trails on both text and audio. That ordering is a
comparison *between the same four models* on each board. It is not a comparison of scores
across boards: the three means are not on a common scale, and a 63.52 on MIEB(lite) does
not mean "better at images than at text". `fetch.py` asserts the ordering (`order` in
`data.json`), so a change in the data fails the run rather than silently contradicting the
draft.

**On the board as a whole**, rather than within the four: 5th of 51 complete on
`MIEB(lite)`, 33rd of 96 on `MTEB(Multilingual, v2)`, 7th of 23 on `MAEB(v1)`. The board
ranks are in the post because they are the guard against reading "leads the four" as
"leads the image board" (see below).

**On text it is not an upgrade.** Its 60.52 sits below its predecessor
`google/embeddinggemma-300m` at 61.14 (rank 30 of 96), and on `MTEB(eng, v2)` 67.53
against 69.67 — recorded in `data.json` under `context_not_used_in_post`, since the post
does not use the English board. The predecessor is a text-only model with no complete
image or audio row, so it cannot appear in the four-model cohort at all.

## Scope: who is missing

**The four are four submissions, not four candidates.** They are the models that happened
to submit complete results on all three boards, which is a fact about who ran what.

- **The whole top of the multilingual board is absent.** Of the top 20 models on
  `MTEB(Multilingual, v2)`, 18 have no complete `MIEB(lite)` *and* no complete `MAEB(v1)`
  row; the top twelve have no result on either board at all —
  `microsoft/harrier-oss-v1-27b`, `Qwen/Qwen3-Embedding-8B`,
  `google/gemini-embedding-001` and the rest. Only `jinaai/jina-embeddings-v5-omni-small`
  and `jinaai/jina-embeddings-v5-omni-nano` (2 of 20) appear on both other boards.
- **And the top of the image board is absent from the four.** All four models above the
  subject on `MIEB(lite)` are outside the cohort because they are short of complete text
  results: `LCO-Embedding/LCO-Embedding-Omni-7B` (68.76, 1st, 21 of 131 multilingual
  tasks), `LCO-Embedding/LCO-Embedding-Omni-3B` (66.38, 2nd, 21/131),
  `Haon-Chen/e5-omni-7B` (65.21, 3rd, 21/131) and `dnotitia/DNA-VL-STEER-2B` (64.30, 4th,
  0/131). So **"leads the four on images" is not "best on images"** — it is 5th of 51, and
  every model ahead of it is missing from the comparison the post is making. Three of the
  four also sit above it on `MAEB(v1)`.
- **`MIEB(lite)` is the 51-task lite set**, not the full MIEB, and `MAEB(v1)` is v1. A
  complete row on either is complete for the benchmark named, nothing more.
- **Partial rows are excluded rather than averaged**, on all three boards: 51 of the 106
  models with any `MIEB(lite)` result are complete, 23 of 70 on `MAEB(v1)`, 96 of 483 on
  `MTEB(Multilingual, v2)`. Six models — `LCO-Embedding-Omni-7B`, `-3B`,
  `Haon-Chen/e5-omni-7B`, `-3B`, `Tevatron/OmniEmbed-v0.1`, `encord-team/ebind-full` — are
  complete on two of the three and miss only the multilingual board.

The claim that survives all of this is the narrow one the post makes: among the four
models that can be compared across the three, this one is the image-leaning one. Nothing
here supports a statement about which model is best at images, audio or text overall.

## Notes

**Trigger.** `mteb#5588` (schechterh, merged 2026-10-18) registers the model;
`results#793` (KennethEnevoldsen, merged 2026-10-19) adds the results. The mteb PR body
points at a companion results PR `results#745`, which was closed unmerged — the merged
numbers are `#793`. The results files sit at revision `914f7f89…`, the revision in the
`ModelMeta`.

**Contributor text was read as data.** Both PR bodies and the model card were read for
facts and checked against the API and the results repo. Nothing in them was treated as an
instruction. Two claims in `mteb#5588` are deliberately *not* used: the per-configuration
parameter and memory figures, and any statement about why the model is built the way it
is. MTEB did not measure either.

**The post says "text, images and audio", not "video".** The registry row also lists
video, but none of the three boards measures it, so the post names only the modalities
MTEB has scored.

**No size claim, on purpose.** `google/embeddinggemma-2` is one `ModelMeta` covering
several tower configurations (`use_image`, `use_audio` in
`mteb/models/model_implementations/google_embeddinggemma.py`); the wrapper reports the
parameter count of the towers a run actually loaded, but the results files record no tower
configuration, so which count belongs to the image and audio scores is not measurable from
the results repo. The leaderboard row says 0.271B, which is the text-tower default. The
post therefore makes no size claim, and the table's size column is labelled "total
params" — it is not "the size of the model that produced these scores".

**`MIEB(lite)`'s `meanTask` is not a plain task average.** On `MTEB(Multilingual, v2)` and
`MAEB(v1)` the API's aggregate reproduces the unweighted mean to within 0.01; on
`MIEB(lite)` it does not (worst case 6.06 points across the board, 63.52 against 57.94 for
the subject). The post quotes the leaderboard's own aggregate, as the registered-benchmark
path in `leaderboard_api.py` is documented to. Do not "correct" it by averaging the 51
tasks — that produces a number nobody else can reproduce.

**The card is a table, not a chart.** The claim is a comparison across three boards, which
none of `templates/model-release/`'s three shapes can express — a bars card would have to
pick one board and drop the argument. So the card is bespoke, per `docs/card-design.md`
("other post types stay bespoke until they converge"), and inherits only the palette from
`card-bars.html` so the brand cannot drift. `fetch.py` writes its values into `#card-data`
from the same `cohort` that the prose quotes; every sentence is in the card's `COPY`.

**Two things the card says that the thread does not.** It enumerates each column's
"best of the four", so the subject's image lead is not shown in isolation from losing the
other two columns — a reader who sees only the image will still see 60.52 and 49.31 beside
it. And its footnote carries the tower-configuration caveat, because a screenshot travels
without "## Notes".

**Credit.** `schechterh` (Henrique Schechter Vera, Google) registered the model;
`KennethEnevoldsen` submitted the results. Neither has an entry in `social-handles.yaml`,
and `schechterh` links no social accounts from his GitHub profile, so both are plain text.

**The count is live.** "Only four models" is true of the leaderboard on 2026-10-29 and
will change as results merge; `expires: 2026-11-18`.

## Decisions for the reviewer

1. **Post it, or reject it?** This is a successor model that does not beat its own
   predecessor on text (60.52 vs 61.14 multilingual; 67.53 vs 69.67 English). My
   recommendation is to post: the coverage fact is rare and useful, the model's text
   position is stated in the post, and a reader choosing between the two generations is
   better off knowing it. The counter-argument is the `sante-embed` precedent — this
   account has declined before to post a model that scored below the model it was built
   from. The difference is that there the whole claim collapsed; here the coverage claim
   stands on its own.
2. **The predecessor sentence in part 2.** `On text its 60.52 sits below its predecessor
   google/embeddinggemma-300m at 61.14.` It is the sentence most likely to be read as this
   account picking on a model, and part 2 fits without it. I would keep it: dropping it
   leaves a post announcing a successor whose text score a reader will check against the
   board anyway.
3. **The card.** None exists. Someone has to write `card-1-embeddinggemma-2.html` and run
   `mteb-render`, otherwise the post cannot reach `3-review` (`media:` will not resolve).
   Suggested content: the four rows across three boards, subject highlighted — the table
   in "The claim" is the whole argument, and the thread carries its numbers only because
   the card does not exist yet.
4. **Tagging.** None proposed. `KennethEnevoldsen` has a Bluesky handle in
   `social-handles.yaml`, but he is the account's maintainer and the post is about
   Google's model, so tagging him would read as tagging ourselves.
5. **Timing.** `expires: 2026-11-18`, one month from the trigger. The "only four models"
   count is the part that goes stale first — a fifth complete submission makes the first
   sentence wrong rather than old.
