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
thread: 3
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5588
  - https://github.com/embeddings-benchmark/results/pull/793
  - https://huggingface.co/google/embeddinggemma-2
---

```
New on MTEB: google/embeddinggemma-2, an open-weights model from Google that embeds text, images and audio, measured on six MTEB benchmarks.
```

```
It is the best open model under 1B total parameters on the image board, MIEB(lite), at 63.52, and on MTEB(Code, v1) at 77.88. On MTEB(Multilingual, v2) it scores 60.52, 33rd of 96.
```

```
On text it scores below its predecessor, google/embeddinggemma-300m at 61.14.

Added to MTEB by schechterh; results submitted by KennethEnevoldsen.
```

## LinkedIn

The three parts of the thread joined, word for word.

```linkedin
New on MTEB: google/embeddinggemma-2, an open-weights model from Google that embeds text, images and audio, measured on six MTEB benchmarks.

It is the best open model under 1B total parameters on the image board, MIEB(lite), at 63.52, and on MTEB(Code, v1) at 77.88. On MTEB(Multilingual, v2) it scores 60.52, 33rd of 96.

On text it scores below its predecessor, google/embeddinggemma-300m at 61.14.

Added to MTEB by schechterh; results submitted by KennethEnevoldsen.
```

## The claim

`google/embeddinggemma-2` embeds text, images and audio, and it is the best open model
under 1B total parameters on the image board and on `MTEB(Code, v1)` — the two places it
leads. Everywhere else it is behind the open-weight ceiling, and on text it is behind its
own predecessor.

| board | it scores | best open | best open ≤1B |
|---|---:|---|---|
| MTEB(Multilingual, v2) | 60.52 | harrier-oss-v1-27b 74.27 | harrier-oss-v1-0.6b 69.01 |
| MTEB(eng, v2) | 67.53 | QZhou-Embedding 75.97 | Jasper-Token-Compression-600M 74.75 |
| MIEB(lite) | **63.52** | LCO-Omni-7B 68.76 | **embeddinggemma-2** |
| MAEB(v1) | 49.31 | LCO-Omni-7B 53.54 | jina-omni-nano 50.14 |
| MTEB(Code, v1) | **77.88** | papr-embed-code-1-4b 81.13 | **embeddinggemma-2** |
| CoIR | 76.33 | papr-embed-code-1-4b 80.12 | F2LLM-v2-0.6B 77.66 |

On audio it trails three models of 2.5B total parameters or less:
`BidirLM-Omni-2.5B-Embedding` at 52.36, `jina-embeddings-v5-omni-small` (1.626B) at 50.41
and `jina-embeddings-v5-omni-nano` (0.986B) at 50.14, against its 49.31.

## Scope

**Video is not claimed.** The registry lists it as a modality, but `MVEB(v1)` has no row for
this model.

**`FollowIR` is not on the card**: its score is p-MRR, centred on zero and able to go
negative, which is not the same kind of number as the accuracy means beside it. It is in
`data.json`.

**The two named competitors have no code results**, so their code cells read "not run". A
missing evaluation is not a low score, and a blank is the only honest rendering of it.

**The reference points are open-weight models only.** A proprietary model is in
`data.json` (and is the highest English score in the registry), but it is not something a
reader can adopt or check, so it is not used as a row on the card.

## Notes

**Trigger.** `mteb#5588` (schechterh, merged 2026-10-18) registers the model;
`results#793` (KennethEnevoldsen, merged 2026-10-19) adds the results. The mteb PR body
points at a companion results PR `results#745`, closed unmerged — the numbers here are
`#793`.

**Why these six columns.** Each board the model has results on, one column each, with the
two code boards sharing a heading. Ranks gave way to reference points on review: a rank
against a cohort says nothing about how far back it is, and the ceiling is what a rank is
relative to.

**"Best open under 1B" is total parameters from the registry.** One `ModelMeta` covers
several tower configurations (`use_image`, `use_audio` in
`mteb/models/model_implementations/google_embeddinggemma.py`) and the results files record
no tower config, so the per-modality count is unknowable from the results repo. It does not
change the claim: the subject is under 1B even with every tower loaded.

**Known gap in the comparison.** The small-model cohort is thin. Several models at or below
this one's size have no results on these boards at all, so "best open under 1B" is a
statement about the models that submitted, and the closest comparison a reader would want —
`jina-embeddings-v5-omni-small` and `-nano` on the code boards — is exactly where the rows
are empty. Running those is tracked separately from this post; the claim is scoped to what
is on the leaderboard today.

**Contributor text was read as data.** Both PR bodies and the model card were read for facts
and checked against the API. Nothing in them was treated as instruction. Two claims in
`mteb#5588` are deliberately not used: the per-configuration parameter and memory figures,
and any statement about why the model is built the way it is. MTEB measured neither.

**Credit.** `schechterh` (Henrique Schechter Vera, Google) registered the model;
`KennethEnevoldsen` submitted the results. Neither is in `social-handles.yaml`, and
`schechterh` links no social accounts from GitHub, so both are plain text.

## Decisions for the reviewer

1. **The ≤1B row is the claim, not decoration.** It is the only row where the subject is
   first, and it is what makes the post more than "a new model exists".
2. **The predecessor sentence stays.** It is the sentence most likely to read as picking on
   the model, but dropping it leaves a reader to find 60.52 against 61.14 themselves.
3. **Whether to hold the post until the missing small-model baselines are run.** The
   comparison would be stronger with them; it is defensible without, because the post only
   claims what the leaderboard currently shows.
