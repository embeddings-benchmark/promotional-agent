---
id: sante-embed-medical
type: model_addition
trigger: mteb#5466 + results#716
trigger_date: 2026-09-15
expires: 2026-10-15
subject: Singaraj/sante-embed
verified: true
evidence: data.json
reason: the fine-tune scores below its own base model on the benchmark it was built for (63.61 vs 65.04 on MTEB(Medical, v1)); its rank (9th of 135) is the only positive number, and that rank is measured on a board that 16 of the top 20 MTEB(Multilingual, v2) models never entered. No claim survives that is both true and worth amplifying — every honest version had to lead with the base model beating the fine-tune, which is not a story the account can tell on the authors' behalf.
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5466
  - https://github.com/embeddings-benchmark/results/pull/716
  - https://huggingface.co/Singaraj/sante-embed
---

**Recommendation: do not post. Reject with the `reason:` above, or leave it to expire on
2026-10-15.** It stays in `2-drafting` so you make that call, not me. There is no draft
text: every honest version I could write leads with the base model beating the fine-tune.

## What it is

`mteb#5466` (merged 2026-09-15) registers `Singaraj/sante-embed`: open weights,
apache-2.0, 1.54B parameters (1.31B active), a LoRA fine-tune of
`Alibaba-NLP/gte-Qwen2-1.5B-instruct` merged back into the weights, capped at 512 tokens.
`results#716` (merged 2026-09-16, same author) adds all 12 `MTEB(Medical, v1)` tasks, run
with mteb 2.20.11. The pairing is real: same author, same model id, same revision
(`9343a6f8…`), and the HF repo is public at that sha.

## What the numbers say (recomputed, `fetch.py` → `data.json`)

| | MTEB(Medical, v1) Mean(Task) | rank by mean, of 135 complete | site rank (Borda) | zero-shot |
|---|---:|---:|---:|---:|
| `Alibaba-NLP/gte-Qwen2-1.5B-instruct` (base) | **65.04** | 3 | 5 | unknown |
| `Singaraj/sante-embed` | 63.61 | 11 | 9 | 75% |

Both recomputed with `Benchmark.get_score()` after `join_revisions()` and merging each
model's entries, and both match the live leaderboard API to 0.01.

**The triage note was wrong about the base, and it is the whole story.** The base has
5 Medical tasks in its main revision folder and the other 7 in `external`. Read one
folder at a time it looks like 5/12; the leaderboard joins them into a complete 12/12
row, and so does `fetch.py`. That is exactly the revision-split trap in the brief. With
the base complete, the comparison the triage told me to avoid making is the one the
leaderboard already shows every reader: the base sits 4 places above the fine-tune.

Per task (fine-tune minus base, points): gains on MedicalQARetrieval (+5.2),
PublicHealthQA (+2.6), NFCorpus (+1.1); losses on TRECCOVID-PL (−11.5), CUREv1 (−6.3),
TRECCOVID (−4.3), SciFact (−2.2), CmedqaRetrieval (−1.6). Full table in `data.json`.
It is lower on SciFact, one of its two declared training sets.

**The base/fine-tune comparison is not controlled.** The base's `external` results are
author-reported imports (no mteb version recorded, `max_tokens` 131072); its main-revision
results were run on mteb 1.18.0. The fine-tune was run on 2.20.11 truncated at 512 tokens,
which plausibly costs it on CUREv1 and the TRECCOVID pair. So "fine-tuning made it worse"
is not established either. But a post cannot say the opposite, and the leaderboard shows
the base ahead regardless.

## Checks on the triage notes

- **Languages.** `ModelMeta.languages` lists 9 (eng, zho, ara, spa, fra, kor, pol, rus,
  vie). The benchmark measures only 5 of them: English, Chinese (CMedQAv2, Cmedqa),
  Polish (SciFact-PL, TRECCOVID-PL), Spanish and French (CUREv1). Arabic, Korean, Russian
  and Vietnamese are a model-card claim with no MTEB result behind it.
- **Zero-shot 75%.** Confirmed: `training_datasets = {NFCorpus, SciFact}`, which MTEB
  resolves to NFCorpus, SciFact and SciFact-PL — 3 of 12 tasks, 75% zero-shot (site
  `zeroShotPct: 75`, `trainedOnTasks` lists the three).
- **CUREv1 "evaluated per language subset and merged into one file"** (results#716 body).
  Checked: the file holds all 11 splits × 3 languages (en/es/fr) and the API's score
  matches our recompute, so the merge did not drop anything.
- **Who is missing.** 16 of the top 20 `MTEB(Multilingual, v2)` models and 15 of the top
  20 `MTEB(eng, v2)` models have no complete Medical results (Qwen3-Embedding 0.6B/4B/8B,
  gemini-embedding-001, harrier-oss, jina-v5, …). The board's #1 is a 2024 model,
  `Alibaba-NLP/gte-Qwen2-7B-instruct`. Any rank here is a rank among who entered.
- **Other benchmarks.** The model has 2/131 tasks on Multilingual v2 and 3/41 on eng v2,
  so there is no within-model comparison to fall back on.

## Angles considered

1. *"Open 1.5B medical retriever, 9th of 135 on MTEB(Medical, v1)."* True, but it
   implies the medical fine-tune is what puts it there, while the general model it was
   built from ranks higher on the same board. Misleading by omission. Rejected.
2. *Say it straight: fine-tune 63.61, base 65.04.* Honest, but it singles out a
   community contributor's first model to report that it did not beat its base, on a
   comparison that is not controlled (see above). That is not what this account is for,
   and it is not news a reader can use.
3. *Medical breadth / state of the Medical board.* Medical has never been covered by the
   account, and that is worth fixing. But that is a different post (`state_of_field`)
   with no credit line, not this one. The who-is-missing count above, plus "a 2024 model
   still leads", is a starting point for it.

## Notes

**Contributor text treated as data.** Both PR bodies and the ModelMeta were read for
facts and checked against the results files and the API. The "75% zero-shot" and
CUREv1-merge claims both held. Nothing in them was treated as instruction.

**Credit, if it ever runs:** GitHub `LK-maker-007` (Singaraj B), author of both PRs. No
social accounts on GitHub, no homepage, and no entry in `social-handles.yaml`. The same
author has two more candidates in `1-candidates`
(`add-singaraj-morisien-embed-mauritian`, `mteb-evaluation-results-for-singaraj`). A
Mauritian Creole model would broaden coverage more than this one would, so it may be the
better way to credit this contributor.

## Decisions for the reviewer

1. **Reject or not.** Recommended: reject, with the `reason:` in the frontmatter. If you
   agree, move the folder to `rejected/` and add `rejected_on:`.
2. **Timing, if you overrule.** `expires: 2026-10-15`. You review on 2026-10-13, and
   2026-10-14 is a free slot (13th, 15th and 19th are taken), so it can still go out in
   its window. It would need text and a card first. Angle 2 is the only version I would
   defend, and it should name the base model's score.
3. **A Medical state-of-field post** (angle 3) is probably the better way to put
   medical on the feed. Want it drafted?
