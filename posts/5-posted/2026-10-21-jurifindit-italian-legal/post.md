---
id: 2026-10-21-jurifindit-italian-legal
type: dataset_addition
trigger: mteb#5464 (task, merged 2026-09-16) + results#719 (first results, merged 2026-09-16); results#722 (merged 2026-09-20)
trigger_date: 2026-09-16
approved_by: kennethenevoldsen (explicit instruction, 2026-10-13)
scheduled_for: 2026-10-21T14:30:00+02:00
expires: 2026-10-31
subject: JuriFindITRetrieval
verified: true
evidence: data.json
media: card-1-jurifindit.png
thread: 2
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5464
  - https://github.com/embeddings-benchmark/results/pull/719
  - https://github.com/embeddings-benchmark/results/pull/722
  - https://aclanthology.org/2026.findings-eacl.221/
  - https://huggingface.co/datasets/jurifindit/JuriFindIT
posted_on: 2026-10-21
url: https://bsky.app/profile/mteb.org/post/3myfbnfucal2p
---

```
1/ New on MTEB: JuriFindIT, 895 questions on Italian law written by four legal professionals, each linked to the statutory articles that answer it.

Until now, MTEB's only Italian legal retrieval data was 200 machine-generated questions about EU law.
```

```
2/ Eight models have results so far, led by Snowflake/snowflake-arctic-embed-m-v2.0 at 62.92 nDCG@10. Widely used multilingual models such as BAAI/bge-m3 and Qwen/Qwen3-Embedding-8B have not been run on it yet.

Dataset by Dalla Noce et al., added to MTEB by albertobarnabo.
```

## LinkedIn

The Bluesky thread as one post, word for word. No one in this post has a `linkedin:` entry
in `social-handles.yaml`, so the credit line is plain text here too.

```linkedin
New on MTEB: JuriFindIT, 895 questions on Italian law written by four legal professionals, each linked to the statutory articles that answer it.

Until now, MTEB's only Italian legal retrieval data was 200 machine-generated questions about EU law.

Eight models have results so far, led by Snowflake/snowflake-arctic-embed-m-v2.0 at 62.92 nDCG@10. Widely used multilingual models such as BAAI/bge-m3 and Qwen/Qwen3-Embedding-8B have not been run on it yet.

Dataset by Dalla Noce et al., added to MTEB by albertobarnabo.
```

## The claim

`mteb#5464` (merged 2026-09-16) adds `JuriFindITRetrieval`, MTEB's task for **JuriFindIT**
(Dalla Noce, Colla, Farhang Doust, De Mattei, Bacciu; Findings of EACL 2026; dataset
`jurifindit/JuriFindIT`, CC BY-NC-SA 4.0). `results#719` (same day) and `results#722`
(2026-09-20) give it its first results. All three PRs are by albertobarnabo, who is not
an author of the paper.

| post says | where it is true |
|---|---|
| "895 legal questions" | task metadata and `descriptive_stats` (`num_queries: 895`), printed by `fetch.py` |
| "written in Italian by four legal professionals" | task description: "895 legal questions written by four Italian legal professionals (one per macro-area)"; paper abstract: "895 expert-authored questions"; `eval_langs: ita-Latn`, `annotations_creators: expert-annotated`, `sample_creation: created` |
| "each linked to the statutory articles that answer it" | qrels: 4.48 relevant articles per question on average, 23,113 articles in the corpus (card) |
| "civil and criminal law, anti-money laundering and data protection" | the four macro-areas in the task description and the paper ("privacy" in the paper, "data protection" in the task) |
| "Until now, MTEB's only Italian legal retrieval data was 200 machine-generated questions about EU law" | `mteb.get_tasks(languages=["ita"], domains=["Legal"], task_types=["Retrieval"])` returns exactly two tasks: this one and `MuPLeR-retrieval` (`annotations_creators: LM-generated and reviewed`; "200 parallel queries (synthetic)" over DGT-Acquis EU legislation in 14 languages). "Machine-generated" simplifies "LM-generated and reviewed": the queries were generated, then checked by people. Recorded in `data.json` |
| "Eight models have results so far" | 10 rows on disk and on the leaderboard's task endpoint, two of them `mteb/baseline-*` |
| "led by Snowflake/snowflake-arctic-embed-m-v2.0 at 62.92 nDCG@10" | recomputed (below) |
| "Widely used multilingual models such as BAAI/bge-m3 and Qwen/Qwen3-Embedding-8B have not been run on it yet" | neither has a `JuriFindITRetrieval.json` in any revision folder (checked in `fetch.py` for bge-m3; on disk for both) |

**Scores.** `fetch.py` wraps the single task in `mteb.Benchmark(tasks=[task])` and calls
`get_score()` after `join_revisions()` and per-model merging (the pareto-tag pattern), so
`Mean(Task)` is the task's main score, nDCG@10. It asserts this equals
`TaskResult.get_score()` and the live leaderboard's `/v1/tasks/JuriFindITRetrieval/scores`
within 0.01 for every model, and that the on-disk cohort equals the API's. See
`data.json`. One rounding difference: the arctic result file holds exactly 0.62915, which
we round half-up to 62.92; the leaderboard API's display rounds it to 62.91. Both are the same
stored number, and the post uses ours.

**Cohort fairness.** All eight models are multilingual models that declare Italian (checked
from `ModelMeta` in `fetch.py`); none declares JuriFindIT as training data. Every score is on
the same single task, so coverage is complete by construction. No leaderboard-style claim is
made beyond "leads among the eight", and part 2 says outright that the obvious larger models
have not been run.

**What is not claimed.**
- Not that "Italian national law" is the whole corpus: the task description says the
  articles come from Italian *and EU* legislative acts. The post says "statutory articles".
- Not "the first Italian legal retrieval dataset", though the paper's abstract says "the
  first SAR dataset for the Italian legal domain". That is the authors' claim about the
  literature; ours is only about MTEB, which we checked.
- No fine-tune-vs-base claim for `albertobarnabo/bge-m3-italian` (3rd, 61.73, fine-tuned on
  Italian mMARCO): `BAAI/bge-m3` has no JuriFindIT result in any revision, so the comparison
  the model exists to make cannot be made. That model is on the card but not in the text.
- Nothing about BM25. It is on the card as a hatched reference (47.79, between
  `intfloat/multilingual-e5-small` and `codefuse-ai/F2LLM-v2-80M`). A line like "keyword
  matching beats three models" would be true but would mostly be a remark about two static
  models and an 80M one, which is unfair to them and not the point of the post.
- No numbers from the paper's own tables, or from the PR bodies (e.g. the paper-reproduction
  table in mteb#5464): those are claims we have not recomputed.

## Notes

**Why lead with the dataset, not with law.** Two recent posts were legal
(`dinghy-law-family`, `octen-law-8b`) and `legal-specialisation` is in drafting. This one is a
`dataset_addition`, and what is new is the language and who wrote the questions, so the
post opens with that and law is the setting. It is not marked `competes_with:
legal-specialisation`: that post is an English/`MTEB(Law, v1)` field claim and shares no
data with this one.

**Breadth.** Non-English (Italian), a domain (legal) and a dataset rather than a model post.
Of the scheduled posts two are features and one is a benchmark-status post.

**Related candidates, not folded in, left in `1-candidates/` for the owner:**
- `add-albertobarnabo-bge-m3-italian` (mteb#5488 + results#722): the model appears on this
  card. As a post of its own it is weak: no base-model comparison is possible on JuriFindIT
  (above), and its 26 Italian tasks are not a registered benchmark. Suggest rejecting with
  "covered as context in jurifindit-italian-legal; no base-model comparison available".
- `reference-models-for-mteb-ita` (results#720): reference results for `MTEB(ita, v1)`,
  which was closed unmerged on 2026-09-20 (mteb#5479; maintainers declined a benchmark
  without a citation). Plumbing for a benchmark that did not land. Suggest rejecting with
  that reason.

**Credit.** Dataset: the paper's five authors. Not a large group effort, so there is a
credit line. `nikodallanoce` is the first author's GitHub account (name "Niko Dalla Noce",
University of Pisa, owns `nikodallanoce/JuriFindIT`). `dbacciu` (Davide Bacciu) is the last
author; the other three have no GitHub account that could be confirmed. The dataset is
credited by its paper ("Dalla Noce et al.", as on the card), since its authors did not
contribute to MTEB; albertobarnabo is credited by handle for the MTEB integration and all
results. None has an entry in `social-handles.yaml`; no social accounts on GitHub
(`gh api users/<h>/social_accounts` empty for albertobarnabo, nikodallanoce, dbacciu).

**Contributor text handled as data.** PR bodies and comments were read for what the task
is; every fact used was checked against the task code, metadata, paper abstract or results.

## Decisions for the reviewer

**Expiry extended** from 2026-10-16 to 2026-10-31 by kennethenevoldsen (2026-10-13): fine to post after the one-month mark.

1. **Expiry is 2026-10-16.** Free slots before it: 10-14 and 10-16. 10-14 would also put a
   dataset post between the two feature posts on 10-13 and 10-15, which the pareto-tag
   post's own reviewer note asks for. Suggest `2026-10-14T14:30:00+02:00`.
2. **Thread or single post.** Part 1 alone (295 chars) is the dataset post; part 2 adds
   the first results and the "who has not run it" scope. If you prefer one post, drop part
   2 and keep the card, but then the scope line lives only on the card.
3. **Credit wording.** "Dataset by nikodallanoce et al." names one of five authors by
   handle. Alternative: "Dataset by Dalla Noce et al. (EACL Findings 2026)", by name like the
   card footer.
4. **"legal professionals".** The source says "four Italian legal professionals"; not
   "lawyers", since their roles are not specified.
