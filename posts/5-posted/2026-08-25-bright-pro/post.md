---
id: 2026-08-25-bright-pro
type: benchmark_addition
trigger: mteb#4929 (benchmark registration); results#644 (day-one 19-model results)
trigger_date: 2026-08-10
scheduled_for: 2026-08-25T14:30:00+02:00
approved_by: kennethenevoldsen (explicit instruction, 2026-08-23)
expires: 2026-09-10
verified: true
subject: BRIGHT-Pro
evidence: data.json
media: card-1-bright-pro.png
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/4929
  - https://github.com/embeddings-benchmark/results/pull/644
posted_on: 2026-08-25
url: https://bsky.app/profile/mteb.org/post/3mtvuyiffet2x
---

```
New benchmark: BRIGHT-Pro, a new multi-aspect retrieval benchmark on real StackExchange questions across 7 domains, built for agentic search — scored on surfacing several reasoning aspects, not one passage.

AQ-MedAI/Diver-Retriever-4B-1020 leads at 55.88.

Contributed by yilunzhao.
```

## The claim

`mteb#4929` registers `BRIGHT-Pro`: 7 retrieval tasks, one per StackExchange domain
(biology, earth science, economics, psychology, robotics, stackoverflow, sustainable
living). It extends the original `BRIGHT` benchmark with per-query "aspect"
annotations — each query's gold answer cites passages that collectively cover several
distinct reasoning aspects, so a retriever is scored on surfacing an aspect-diverse
evidence set rather than a single relevant passage. Built for agentic search settings,
where an agent needs a spread of evidence to reason over, not just the one nearest
neighbor.

`results#644`, same author, same day, submits day-one results for 19 models — all 19
with complete 7-task coverage, unusually thorough for a benchmark's first results PR.
That completeness is why this is a leaderboard post rather than a bare announcement.

`mteb#5129`, a same-day duplicate re-registration of the same benchmark ("Readd it from
#4929"), is rejected separately — see `posts/rejected/bright-pro-benchmark`.

## What the leaderboard shows

`AQ-MedAI/Diver-Retriever` sweeps 4 of the top 5 spots (4B-1020, 4B, 0.6B, 1.7B — every
size in the family), ahead of `yale-nlp/RTriever-4B` (the benchmark authors' own
reference model, 5th at 46.88) and the general-purpose leaders `Qwen/Qwen3-Embedding-8B`
(6th, 41.75) and `Alibaba-NLP/gte-Qwen2-7B-instruct` (8th, 37.75). `ReasonIR/ReasonIR-8B`
— a model built specifically for reasoning-intensive retrieval — places 9th at 32.94,
behind several models with no reasoning-specific training at all. Worth noting, not
worth a claim: 19 models on day one is too thin a field to say anything about what kind
of training this benchmark rewards.

## Notes

**Post text and card subtitle reworked** to lead with what the benchmark measures
("a new multi-aspect retrieval benchmark on real StackExchange questions") rather than
the day-one model count — the "19 models" line was dropped from both. The axis label
("top 10 of 19 models with complete coverage") stays: that describes the scope of what
the chart plots, not an editorial claim about the benchmark.

**`trigger:` was `mteb#4929 + results#644`** — the exact "mteb#X + results#Y" notation
this account uses for a model registration paired with its results (bekko,
most-embed-de). Wrong pairing semantics here: mteb#4929 registers the *benchmark*,
results#644 is its first *community* results batch, not a model's own submission.
Reworded to name what each PR actually is. Also moved "Added by yilunzhao" (ambiguous
right after a sentence naming a different model, `AQ-MedAI/Diver-Retriever-4B-1020` —
could read as crediting *that* model) to "Benchmark by yilunzhao."

Credit: yilunzhao (mteb#4929 and results#644, same author). No Bluesky handle in
`social-handles.yaml`, so plain text, no @-mention.

Card shows top 10 of 19 rather than the full board — the bars template's row spacing is
tuned for ~10 rows on the 1200px canvas (see `card-1-bright-pro.html`'s own comment).
`data.json` keeps all 19, per CONTRIBUTING's "record every model that qualified."

First post drafted with `mtebpost/model_release.py`'s bars builder for a
`benchmark_addition` (no single "subject" model — `cohort([], "BRIGHT-Pro")` with an
empty subject list, same builder as `most-embed-de`, just no highlighted row). Found and
fixed a real bug in the process: `bars_card_data`/`pareto_card_data` read the task count
from `coh.subjects[0]`, which doesn't exist when there's no subject — silently printed
"0 tasks" until `Cohort.n_benchmark_tasks` was added to read it from any scored entry.
