---
id: 2026-10-26-splade-code
type: model_addition
trigger: results#743 (+ mteb#5087, which registered the models)
trigger_date: 2026-10-03
approved_by: kennethenevoldsen (explicit instruction, 2026-10-13)
scheduled_for: 2026-10-26T14:30:00+01:00
expires: 2026-11-03
verified: true
evidence: data.json
media: card-1-splade-code.png
thread: 2
competes_with: add-linkup-platform-linkup-sparseup (1-candidates; another sparse model, not yet triaged)
sources:
  - https://github.com/embeddings-benchmark/results/pull/743
  - https://github.com/embeddings-benchmark/mteb/pull/5087
  - https://arxiv.org/abs/2603.22008
  - https://arxiv.org/abs/2605.04615
  - https://huggingface.co/naver/splade-code-8B
  - https://huggingface.co/naver/splade-code-06B
posted_on: 2026-10-26
url: https://bsky.app/profile/mteb.org/post/3mys7yrydkg2x
---

Post 1 — card: `card-1-splade-code.png`

```
1/ New on MTEB: naver/splade-code-06B and naver/splade-code-8B, sparse retrieval models for code.

On CoREB(v1), built from rewritten programming-contest problems to limit overlap with training data, they score 59.43 and 59.61. The best of the 24 models evaluated so far scores 60.10.
```

```
2/ Sparse means each query and code snippet becomes a small set of weighted words, as in keyword search. Keyword search itself (BM25) scores 28.34 on CoREB, so these models close almost all of the gap to the best dense models.

Model from NAVER LABS Europe, results submitted by SimonLupart.
```

## LinkedIn

The Bluesky thread as one post, word for word. SimonLupart's LinkedIn is linked from their
own GitHub profile and recorded in `social-handles.yaml`, so the credit line tags them.

```linkedin
New on MTEB: naver/splade-code-06B and naver/splade-code-8B, sparse retrieval models for code.

On CoREB(v1), built from rewritten programming-contest problems to limit overlap with training data, they score 59.43 and 59.61. The best of the 24 models evaluated so far scores 60.10.

Sparse means each query and code snippet becomes a small set of weighted words, as in keyword search. Keyword search itself (BM25) scores 28.34 on CoREB, so these models close almost all of the gap to the best dense models.

Model from NAVER LABS Europe, results submitted by @Simon Lupart.
```

## The claim

`results#743` (SimonLupart, merged 2026-10-03 by Samoed) adds results for
`naver/splade-code-06B` and `naver/splade-code-8B` on CoIR, MTEB(Code, v1), CoREB(v1) and
3 of 4 CodeRAG tasks. The models were registered in `mteb#5087` (Samoed, 2026-08-20),
which added sparse-encoder support to mteb and continued fzowl's `mteb#4828`.

Every number below is recomputed by `fetch.py` with `Benchmark.get_score()` (revisions
joined, entries merged per model) and matches the live leaderboard API to 0.01 for all
24 CoREB(v1) rows and all 51 complete MTEB(Code, v1) rows (`data.json`, `problems: []`).

CoREB(v1), 6 tasks, 24 models with complete results, ordered by Mean (Task):

| # | score | total size | model |
|---:|---:|---:|---|
| 1 | 60.10 | 7.7B | `codefuse-ai/C2LLM-7B` |
| 2 | 60.09 | 334M | `codefuse-ai/F2LLM-v2-330M` |
| 3 | 59.63 | 1.7B | `codefuse-ai/F2LLM-v2-1.7B` |
| **4** | **59.61** | 8.4B | **`naver/splade-code-8B`** |
| 5 | 59.57 | 14B | `codefuse-ai/F2LLM-v2-14B` |
| 6 | 59.48 | 4.0B | `codefuse-ai/F2LLM-v2-4B` |
| 7 | 59.46 | 596M | `codefuse-ai/F2LLM-v2-0.6B` |
| **8** | **59.43** | 596M | **`naver/splade-code-06B`** |
| 9 | 59.35 | 7.6B | `codefuse-ai/F2LLM-v2-8B` |
| 10 | 58.95 | 7.6B | `Qwen/Qwen3-Embedding-8B` |
| 22 | 28.34 | — | `mteb/baseline-bm25s` |

"The best of the 24 models evaluated so far scores 60.10": `C2LLM-7B`; the 8B is 0.49 behind, the 06B 0.67. Positions are by
Mean (Task); the leaderboard's own rank column is Borda over tasks and puts the two at 7
and 10, so the post and card give no rank, and the card's axis note says "numbered by
score".

| post/card says | where it is true |
|---|---|
| "sparse retrieval models for code" | ModelMeta `model_type=["sparse"]`; paper title and abstract (arXiv 2603.22008) |
| "a small set of weighted words" (simplified: the "words" are tokens of a 152k vocabulary) | SPLADE projects each token onto the LM vocabulary and max-pools with log(1+ReLU) (paper §3.1); `embed_dim=151936` in ModelMeta; model card example: 1,120 of 151,936 dims active for a SQL query (8B); results#743 evaluated with top-1000 pruning |
| (removed 2026-10-13: deployment claim is the authors' message, not something MTEB measured) "the same kind of index" as keyword search | paper: LSR "enables the use of traditional inverted index structures" |
| "close almost all of the gap to the best dense models" | (59.61 − 28.34) / (60.10 − 28.34) = 98% for the 8B, 97.9% for the 06B; the top rows (C2LLM-7B, F2LLM-v2) are dense models |
| CoREB "built from rewritten programming-contest problems to limit overlap with training data" | CoREB paper (arXiv 2605.04615): LiveCodeBench problems (contests Sep 2024–Apr 2025), statements and tests counterfactually rewritten (names, narrative, I/O) "to remove memorized surface forms"; the authors call it "contamination-limited" |
| BM25 28.34 | `mteb/baseline-bm25s`, recomputed |

## Why CoREB(v1) and not MTEB(Code, v1)

MTEB(Code, v1) is the obvious default for a code post, and it was the triage angle. It
does not survive one fact from the paper (§3.3, App. A): **SPLADE-Code is trained on the
training splits of all ten CoIR datasets**, and the authors themselves call MTEB-Code
"in-domain" because it is mostly CoIR. The ModelMeta declares `training_datasets=None`,
so the leaderboard shows its zero-shot share as unknown (`zs=-1`) rather than low.
Comparing it there against `Qwen/Qwen3-Embedding-8B` (100% zero-shot) would not be fair to
Qwen; against `codefuse-ai/C2LLM-7B` (8% zero-shot, also CoIR-trained) it would be.

For the record, recomputed MTEB(Code, v1) (51 complete): `splade-code-8B` 78.91 (8th by
score, Borda rank 17), 1.84 behind `F2LLM-v2-14B`/`C2LLM-7B` at 80.75; `splade-code-06B`
75.57 (18th, Borda 21). That is "competitive", not "near the top", and with the training
overlap it is the weaker claim.

CoREB(v1) avoids the overlap: its problems are rewritten LiveCodeBench contests, nothing
in CoIR, and every other learned model in the cohort shows 100% zero-shot on it. The post says in
one clause why this board ("to limit overlap with training data") rather than explaining
the MTEB(Code) problem, which would be a second post.

## Scope: who is missing

CoREB(v1) is new (May 2026) and only 24 models have complete results. Of the top 20
complete MTEB(Code, v1) models (subjects excluded), **9 have no complete CoREB(v1)
results**: `Bytedance/Seed1.6-embedding-1215` (3rd on MTEB(Code)),
`perplexity-ai/pplx-embed-v1-4b`, `ai-sage/Giga-Embeddings-instruct-10B-A1.8B-0826`,
`ICT-TIME-and-Querit/ICT-TIME-and-Querit-embedding-v1`,
`ai-sage/Giga-Embeddings-instruct-3B-0826`, `google/gemini-embedding-001`,
`perplexity-ai/pplx-embed-v1-0.6b`, `lightonai/LateOn-Code`, `lightonai/mLateOn`.

So the post never says "4th" or "top"; it gives the best score of "the 24 models evaluated
so far", and the card's axis note carries "top 10 of 24 models with complete results".
The claim is about the distance to the top of this cohort, which a later entrant could
widen; it does not claim a position.

Also worth knowing: CoREB's authors list Alipay (Ant Group), which as far as we can tell is also
behind `codefuse-ai` (C2LLM, F2LLM), whose models are 12 of the 24 rows and 7 of the top 10.
Nothing suggests a problem — the benchmark is public and every row was recomputed — but a
reader may notice the board is mostly one lab plus the subject.

## Cohort fairness

Every model on CoREB(v1) with complete results is in `data.json`; the card shows the top
10 by score (every row, none skipped) plus BM25. Below position 10 are general-purpose
and multilingual small models (`intfloat/multilingual-e5-small`, static models) that were
not built for code; they are not on the card and the post makes no claim about them.
BM25 is MTEB's own baseline, named because it is the classic sparse method and the
comparison the post explains.

## What the model is (from the paper, not the metadata)

`On the Challenges and Opportunities of Learned Sparse Retrieval for Code`, Lupart, Louis,
Formal, Déjean, Clinchant (NAVER LABS Europe), arXiv 2603.22008, March 2026. SPLADE
learned sparse retrieval on `Qwen/Qwen3-0.6B` and `Qwen/Qwen3-8B` base LLMs: causal
attention switched to bidirectional, pre-trained on MS MARCO with masked next-token
prediction, then LoRA-trained on the CoIR training splits (2.2M examples) with KL
distillation from `Qwen3-Reranker-4B` scores (negatives mined with
`Qwen3-Embedding-0.6B`), a FLOPs sparsity penalty, and checkpoint merging. The paper
reports sub-millisecond retrieval on a 1M-passage CodeSearchNet collection with pruning,
and that "expansion" tokens (not in the input) carry most of the gain over lexical-only
matching. Latency is not in the post: we cannot recompute it, and the paper itself notes
sparse/dense latency figures are not directly equivalent.

The 0.6B model card says it is "the top-performing model on MTEB for models below 1B (at
time of writing, Feb 2026)". Not repeated: on MTEB(Code, v1) today
`codefuse-ai/F2LLM-v2-0.6B` (77.41) and others under 1B score higher than 75.57.

Licence: CC BY-NC-SA 4.0 (non-commercial). Not in the post; see decisions.

## Notes

**Breadth.** No code-domain post and no sparse-model post in `5-posted` or `4-scheduled`.
This is the first of each.

**Why a thread.** Part 1 is the news and the number with its cohort. Part 2 says what
"sparse" means, which a general reader needs and which is the reason the result is
interesting at all; the BM25 number makes that concrete. Neither fits in the other's
budget.

**0.6B vs 8B.** On CoREB the two are 0.18 apart; on MTEB(Code, v1), 3.34 apart. Not in the
post: "the small one is as good" is true on one board and not the other, and explaining
why needs the training-overlap story.

**Credit.** The model is a five-author NAVER LABS Europe paper; SimonLupart (first
author) submitted the results. Hence "Model from NAVER LABS Europe, results submitted by
SimonLupart" rather than crediting the model to one person. mteb integration was Samoed
(#5087, continuing fzowl's #4828); see decisions.

**Contributor text handled as data.** The PR body's score table, the model cards and the
paper were read for facts and checked; nothing in them was treated as instruction. The
PR's table agrees with the recomputed values (CoREB 0.5943/0.5961 → 59.43/59.61; MTEB(Code)
0.7557/0.7891 → 75.57/78.91).

**CodeRAG** (3 of 4 tasks) is partial and is not used anywhere.

## Decisions for the reviewer

1. **Board choice.** The post leans on CoREB(v1) rather than MTEB(Code, v1) because of
   the CoIR training overlap (above). If you would rather lead with MTEB(Code, v1), the
   honest version is "78.91, 1.84 behind the top, trained on CoIR's training splits", and
   the claim gets weaker.
2. **Fix outside this folder (not done).** `splade_code_models.py` declares
   `training_datasets=None`, but the paper says both models are trained on the CoIR
   training splits. Filling it would make the leaderboard's zero-shot column honest for
   these models on MTEB(Code, v1) and CoIR. Probably worth an mteb issue/PR.
3. **Licence.** CC BY-NC-SA 4.0. Not mentioned; a reader evaluating the model for
   production would want to know. Adding "(non-commercial licence)" costs ~25 characters
   in part 1 if you want it.
4. **Credit for Samoed.** #5087 added sparse-encoder support to mteb, without which these
   results could not exist. Our convention credits the submission, not review or
   enabling work, so he is not named. Your call.
5. **competes_with** `add-linkup-platform-linkup-sparseup` (another sparse model, still a
   candidate). If both run, space them; this one has the stronger evidence base.
6. **Tagging.** SimonLupart has no `social-handles.yaml` entry, so nothing is tagged.
   Found (not added): LinkedIn https://www.linkedin.com/in/simon-lupart/ (from his GitHub
   social accounts), X/Twitter @simon_lupart; no Bluesky handle found on GitHub or
   https://simonlupart.github.io/.
