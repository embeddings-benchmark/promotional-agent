---
id: languagebind-omni
type: model_addition
trigger: mteb#4557 + results#683
trigger_date: 2026-08-22
expires: 2026-09-22
subject: LanguageBind/LanguageBind_Omni
verified: true
evidence: data.json
media: card-1-languagebind-omni.png
blocked_on: >-
  results#683 covers 18 of MVEB(beta)'s 23 tasks. Every other model on that board has run
  all 23, so the 18-task cohort is defined by this submission's gaps rather than by what
  the field has evaluated — and it is not neutral: dropping those five tasks lifts every
  peer by 2.63 points on average. Ships as a full-board post once the remaining five land.
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/4557
  - https://github.com/embeddings-benchmark/results/pull/683
  - https://arxiv.org/abs/2310.01852
  - https://github.com/PKU-YuanGroup/LanguageBind
reason: >
  stale and off-thesis: a model from October 2023, newly integrated, scoring 47.14 on 18
  MVEB(beta) tasks where the best model reaches 61.30. Three years old is not a release,
  and 'an old model scores low on a new board' is not news. Expired 2026-09-22.

---

```
New on MTEB: LanguageBind/LanguageBind_Omni — video, audio, image and text in one space, from October 2023.

It scores 47.14 on 18 MVEB(beta) tasks. Every other model on that board was released in 2025 or later, and the best reaches 61.30.

Integration by myang333, results submitted by isaac-chung.
```

## LinkedIn

The Bluesky text plus what the composite actually is — three encoders behind one name is
the kind of detail that changes how a reader reads the number, and it does not fit.

```linkedin
New on MTEB: LanguageBind/LanguageBind_Omni — video, audio, image and text in one embedding space, from October 2023 (arXiv:2310.01852, ICLR 2024).

It is a composite with no checkpoint of its own: mteb's wrapper dispatches each input to LanguageBind's video, audio or image encoder, all three of which share the same frozen text tower, and sums per-modality embeddings for inputs that span several.

It scores 47.14 on the 18 MVEB(beta) tasks it has run, 13th of the 17 models with complete coverage of those tasks. Every other model on that board was released in 2025 or later, and the best of them reaches 61.30 — the audio-video board now has a point of comparison from before the current generation, which is what makes a gap measurable at all.

Integration by myang333, results submitted by isaac-chung.
```

## The claim

`mteb#4557` adds wrappers for LanguageBind's video, audio and image encoders, plus
`LanguageBind/LanguageBind_Omni` — a composite with **no checkpoint of its own**. It
dispatches each input to the sub-model for its modality, shares the OpenCLIP text tower
across all three, and sums per-modality embeddings for an input that spans more than one.
Its parameter count (1.2B) is the three encoders added together, which is why it is
listed as larger than any single LanguageBind checkpoint.

`results#683` submits its results. **Scope: the 18 of `MVEB(beta)`'s 23 tasks it ran** —
there is no registered benchmark it completes, so the cohort is those 18 tasks and the 17
models with a complete result on all of them. The five it did not run are in
`data.json`. **This is the reason the post is blocked** — see below.

| rank | score | released | model |
|---:|---:|---|---|
| 1 | 61.30 | 2025-10 | `LCO-Embedding/LCO-Embedding-Omni-7B` |
| 2 | 60.89 | 2025-11 | `encord-team/ebind-audio-vision` |
| 3 | 60.89 | 2025-11 | `encord-team/ebind-full` |
| **13** | **47.14** | **2023-10** | **`LanguageBind/LanguageBind_Omni`** |

`fetch.py` asserts the two facts the post rests on: no model on this board is older than
the subject, and every other entrant was released in 2025 or later.

## Why this is blocked rather than in review

The 18-task cohort is arithmetically fair — every model in it is scored on exactly the
same tasks — but the scope is not the same shape as `most-embed-de`'s, which is the
precedent it would lean on. There, six tasks were what *anyone* had run for German
retrieval. Here, **16 of the 17 models on the board have run all 23 tasks; the subject is
the only one that has not**, so the slice is drawn around one submission's gaps.

That would be tolerable if the slice were neutral. It is not. `fetch.py` recomputes every
complete model both ways:

- dropping the five tasks lifts peer scores by **+2.63 on average**, up to **5.43**
- two pairs of peers swap places between the two views

So 47.14 is not on the same scale as the MVEB numbers published anywhere else, and the
"best reaches 61.30" in the draft text is a slice figure too — the same model scores
57.58 on the full board. Both numbers are correct and neither is comparable to what a
reader will find on the leaderboard, which is the kind of gap this account exists not to
create.

The five missing tasks (`RAVDESSAVClassification`, `MELDEmotionAudioVideoClustering`,
`Kinetics700VA`, `HumanAnimalCartoonVAPairClassification`,
`MusicAVQACLSAudioVideoClustering`) are classification and clustering, and all 16 other
models have them, so this needs one more results submission and not a rewrite. When they
land, the post is simply the full 23-task board and everything below still holds.

## Why this is a post and not a rank

The rank is not the story and the post does not lead with it. What is new is that a board
made entirely of 2025-and-later models now has an entry from before that wave — the paper
that aligned video, audio and text through language, and the reason a lot of what sits
above it exists. A benchmark with no older entrant can show which model is ahead but not
how far the field has come; this one now can, and the distance is about 14 points on the
same 18 tasks.

That is also why the card puts a release year on every row. The claim is chronological,
so the years have to be on the image making it.

## What is not claimed

- **Not that the model is weak.** Four models on the board score below it, two of them
  released this year. The post does not name them; ranking a 2023 model against a 2026
  one is only interesting in the direction that is fair to the older model.
- **Not a general audio-video capability claim.** 18 tasks selected by what one model
  has run is a cohort, not a benchmark, and the post says which tasks and how many
  models throughout.
- **Nothing about the other three LanguageBind entries.** `LanguageBind_Video_FT`,
  `LanguageBind_Audio_FT` and `LanguageBind_Image` are registered by the same PR;
  `Audio_FT` has one task of MAEB and `Video_FT` has no merged results at all. Only the
  composite is scorable today.

## Notes

Credit is split because the work was: myang333 wrote the wrappers (`mteb#4557`),
isaac-chung ran and submitted the results (`results#683`). Neither is in
`social-handles.yaml`, so both are plain text. The model itself is Zhu et al.'s
(PKU-YuanGroup) — named through the arXiv reference on the card rather than as a handle,
since "contributed by" here means contributed to MTEB.

Breadth (`AGENTS.md` #7): the audio and video *tasks* were covered on 2026-08-18 as a
roundup, but no audio-video *model* has ever been posted. `MVEB(beta)` is a board this
account has never cited.

**No proposed date while blocked.** It was drafted for 2026-09-08; if the missing
results land before `expires: 2026-09-22`, that slot still works.
