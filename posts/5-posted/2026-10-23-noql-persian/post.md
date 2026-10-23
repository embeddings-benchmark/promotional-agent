---
id: 2026-10-23-noql-persian
type: model_addition
trigger: mteb#5512 + results#724
trigger_date: 2026-09-22
approved_by: kennethenevoldsen (explicit instruction, 2026-10-13)
scheduled_for: 2026-10-23T14:30:00+02:00
expires: 2026-10-31
subject: shekar-ai/Noql
verified: true
evidence: data.json
media: card-1-noql-persian.png
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5512
  - https://github.com/embeddings-benchmark/results/pull/724
  - https://huggingface.co/shekar-ai/Noql/tree/fcdec3f8c64107a4a552b1877156d561fa1b6eb9
  - https://github.com/embeddings-benchmark/mteb/pull/5522
posted_on: 2026-10-23
url: https://bsky.app/profile/mteb.org/post/3mykbdfsp2r2u
---

```
New on MTEB: shekar-ai/Noql, a 12M-parameter Persian embedding model. Of the models with a published size and results on all 52 tasks of MTEB(fas, v2), it is the smallest. It averages 58.20; the next-smallest, MCINext/Hakim-small (39M), averages 68.55.

Results submitted by amirivojdan.
```

## LinkedIn

The Bluesky post, word for word. amirivojdan's LinkedIn is linked from their
own GitHub profile and is recorded in `social-handles.yaml`, so the credit line tags them.

```linkedin
New on MTEB: shekar-ai/Noql, a 12M-parameter Persian embedding model. Of the models with a published size and results on all 52 tasks of MTEB(fas, v2), it is the smallest. It averages 58.20; the next-smallest, MCINext/Hakim-small (39M), averages 68.55.

Results submitted by @Ahmad Amirivojdan.
```

## The claim

| post says | where it is true |
|---|---|
| "12M parameters" | `ModelMeta.n_parameters` = 11,940,096 (mteb#5512); safetensors at the scored revision 12,709,632; leaderboard `totalParamsB` 0.012. Both round to 12M |
| "Persian embedding model" | `languages=["fas-Arab"]`; model card: Persian only |
| "smallest … with a published size and results on all 52 tasks" | 33 rows on the live API have a non-null Mean (Task) (= full coverage); 32 have a size. Noql 12M, next MCINext/Hakim-small 39M, then codefuse-ai/F2LLM-v2-80M. The 33rd, openai/text-embedding-3-small, publishes no size — hence the qualifier |
| "averages 58.20" | `Benchmark.get_score()` recomputed 58.20 from results#724 (revision `fcdec3f8`, 52/52 tasks); live API 58.20; PR body 58.20 |
| "MCINext/Hakim-small, has 39M and averages 68.55" | recomputed 68.55, API 68.55; `totalParamsB` 0.039 |
| (removed 2026-10-13: architecture is the authors' message, not something MTEB measured) "12 layers share one set of weights" | `config.json` at `fcdec3f8`: `model_type: albert`, `num_hidden_layers: 12`, `num_hidden_groups: 1`, `inner_group_num: 1` |
| "about as much computation as a BERT-base model" | hidden 768, 12 layers, 12 heads, FFN 3072 — the same per-layer shape as BERT-base, run 12 times. ALBERT adds a 128→768 embedding projection and saves on the embedding lookup; neither changes the order of compute |

All 33 full-coverage scores recomputed and agree with the live leaderboard to 0.01
(`data.json`, `problems: []`). Run 2026-10-12, mteb 2.24.10.

## Notes

**Pairing is genuine.** results#724 names mteb#5512 and the exact revision
(`fcdec3f8…`) that `ModelMeta.revision` pins; same author (amirivojdan); both merged by
Samoed on 2026-09-22. 62 task result files + model_meta.json; the 52 MTEB(fas, v2) tasks are all
present (the rest are other tasks, not used).

**Architecture read from the config, not guessed.** ALBERT-base with a factorized 128-dim
embedding (32,004 × 128 = 4,096,512 = `n_embedding_parameters` exactly) and one
transformer layer reused 12 times. MTEB's active count is 7.84M (`n_parameters −
n_embedding_parameters`). Neither number describes compute: sharing weights saves storage,
not arithmetic. This is why part 2 exists — "12M" next to "efficient" would otherwise
read as "fast", which is false. Not MoE; `n_active_parameters_override` unused.

**Why total, not active, parameters on the card.** (1) The size claim is about storage,
which is what total parameters measures. (2) The Hakim models publish no active count, so
an active-parameter chart would silently drop MCINext/Hakim-small — the strongest small
Persian model — and flatter Noql. (3) On the leaderboard's own active-parameter axis Noql
is *not* Pareto-tagged: hotchpotch/bekko-embedding-v1-a8m has 7.7M active (vs 7.8M) and
scores 62.17. So the card draws no frontier and the post makes no Pareto claim.

**Cohort.** Every model with complete MTEB(fas, v2) results — 33 rows, no English-only
models among them (all are multilingual or Persian-specific; e5-mistral and gte-Qwen2 are
the least Persian-oriented and sit far right on the chart, irrelevant to the claim). No
filtering was applied, so nothing flatters the subject: the card shows Noql at rank 24 of
33 by its plain score. Smaller models in the registry (potion-base-2M/4M/8M, rubert-tiny,
the Mihaiii gte-micro family) have at most 6 of the 52 tasks and are English or Russian
models, so they are rightly outside the "all 52 tasks" scope.

**Who is missing.** Small multilingual models without Persian results (e.g.
intfloat/multilingual-e5-small, 118M total; static multilingual models such as
minishlab/potion-multilingual-128M) — all larger than 12M total, so the "smallest" claim
survives their absence. Claim is scoped to the cohort in the text.

**Comparison fairness to Hakim-small.** It is closed-weight (API) and declares training
data overlapping 58% of the benchmark's tasks (zero-shot 42%). Noql declares
`training_datasets=set()`, which reads as 100% zero-shot, but its training set
(shekar-ai/Shiraz) was not audited for overlap with FaMTEB train splits — "nothing
declared" is not the same as "verified none". Neither point is in the post: naming the
next-smallest model with its higher score is fair to it, and adding "but it trained on
the tasks" would be an unchecked insinuation about one and an unchecked vouching for the
other.

**Matryoshka numbers not used.** The model card reports 768→64-dim truncation results;
only the 768-dim run is in the results repo, so those are unverifiable claims (rule 1).
The card's specs line mentions truncation as a property, without numbers.

**#5522 not used.** Same contributor renamed the leaderboard label "Farsi" → "Persian".
The post says "Persian" throughout, consistent with that; a clause about the rename
would be account-internal news and cost ~60 characters.

**Contributor text handled as data.** PR bodies and the model card were read for claims,
each checked against config/results; nothing in them was treated as instruction.

**Handles.** GitHub amirivojdan = Ahmad Amirivojdan (PhD student, University of
Tennessee). GitHub social accounts and homepage amirivojdan.com list LinkedIn
https://www.linkedin.com/in/amirivojdan/ only; no Bluesky found. Not in
`social-handles.yaml`, so no tag.

## Decisions for the reviewer

**Scheduled 2026-10-23 by kennethenevoldsen (2026-10-13)**, who judged it worth posting. Expiry extended from 2026-10-22 to cover the date. Now a single post: part 2 had shrunk to the credit line once the architecture claim was removed.

1. **The default download is no longer the scored model.** On 2026-09-30 the author
   replaced the weights on `main` ("Replace Noql with stage 2 round 2 checkpoint 1500
   and matching ZWNJ tokenizer"; vocab 32,004 → 38,016) and updated the card to claim
   58.40. MTEB's 58.20 is for revision `fcdec3f8`, which `ModelMeta` pins, so
   `mteb.get_model("shekar-ai/Noql")` loads the scored model — but
   `SentenceTransformer("shekar-ai/Noql")` loads an unscored one. Options: (a) post as
   is (the leaderboard number is correct for the registered revision); (b) hold
   (`blocked_on:`) until results for the new revision are submitted; (c) mention the
   revision in part 2. My lean is (a) or (b); the post never describes the new
   checkpoint, but a reader who downloads it will not get exactly what we scored.
2. **Is a modest score worth a post?** Noql is 24th of 33 and 10 points behind the
   next-smallest model. The case for posting is breadth (no post in 5-posted or 4-scheduled covers Persian; the only
   non-European language benchmark so far is mteb-kor-v2) and that the post is straightforwardly honest about it. If that
   reads as damning with faint praise, part 1 could drop the Hakim-small sentence — but
   then the card's purple dot needs to go grey, and "smallest" would stand without the
   context that makes it fair.
3. **Thread vs single post.** Part 2 (weights shared, not faster) is the "what it means
   for you" part and prevents the obvious misreading of 12M. Dropping it saves a part
   but leaves an efficiency implication the post cannot back.
4. **Expiry.** Trigger 2026-09-22, expires 2026-10-22; the queue already has posts on
   10-13, 10-15 and 10-19, so the window is roughly a week.
