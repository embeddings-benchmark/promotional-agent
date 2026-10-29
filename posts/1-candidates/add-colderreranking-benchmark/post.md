---
id: add-colderreranking-benchmark
type: benchmark_addition
trigger: mteb#5409
trigger_date: 2026-09-13
expires: 2026-12-13
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5409
---

## Why this might be a post

A benchmark that measures a failure mode rather than a capability: `ColDeRReranking`, from
ColDeR (*Collapse of Dense Retrievers: Short, Early, and Literal Biases Outranking Factual
Evidence*, ACL 2025). Seven subsets, each a binary choice between a document carrying the
evidence and a foil that is shorter, earlier, more literal or more repetitive.

The ACL Anthology link is not recorded here: the PR body cites the paper by title and
finding, and an anthology id guessed from the title would be a broken link in a post whose
whole argument is that claims must be checkable. Find it before drafting.

The number that makes it a story: on the default `foil` subset,
`sentence-transformers/all-MiniLM-L6-v2` scores **0.40%**, where the random baseline scores
46%. That is not a weak retriever being weak — it is a retriever reliably choosing the
biased foil over the evidence, which is the paper's finding (Table 4) reproduced as an MTEB
task.

Angle worth drafting: "a new MTEB task where getting it wrong is the normal result" — a
well-known model gets 0.4% because the benchmark rewards resisting brevity, recency and
literal-match heuristics. Check the cohort before drafting: if every model scores near
zero, the post is about the *measurement*, not a ranking, and must say so (CONTRIBUTING,
"One post, one claim" and "Ask who is missing" — a board where everyone fails is not a
leaderboard).

## Before it can move to 2-drafting

- [x] confirm the pairing: single PR, `mteb#5409` by RishabhPatil, merged 2026-09-13
- [ ] check how many models have complete results on ColDeRReranking, and whether the
      spread is wide enough for a post that names any model
- [ ] decide whether the story is "MTEB can now measure retriever collapse" (benchmark
      announcement, no ranking) or a comparison — they are different posts
- [ ] decide the expiry: kept at 2026-12-13 rather than the usual month

## Notes

**Kept when the expired queue was triaged on 2026-10-29.** Its `expires:` date had passed
(2026-10-13) and 32 sibling candidates were rejected as stale. This one survived because a
benchmark addition is not date-bound the way a model announcement is: "MTEB can now measure
a retriever failure mode" does not stop being true, and it is the only candidate in the
queue that is a *benchmark* rather than another model ranking. The expiry is re-dated two
months rather than one, since the trigger is already seven weeks old.
