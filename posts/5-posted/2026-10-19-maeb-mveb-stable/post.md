---
id: 2026-10-19-maeb-mveb-stable
type: benchmark_addition
trigger: mteb#5640 (benchmarks: promote MAEB and MVEB to v1), merge 50631ac4
trigger_date: 2026-10-12
approved_by: kennethenevoldsen (explicit instruction, 2026-10-12)
scheduled_for: 2026-10-19T14:30:00+02:00
expires: 2026-11-09
verified: true
media: none
thread: 2
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5640
  - https://github.com/embeddings-benchmark/mteb/issues/5292
  - https://arxiv.org/abs/2602.16008
  - https://arxiv.org/abs/2606.14958
  - https://github.com/embeddings-benchmark/mteb/pull/5454
posted_on: 2026-10-19
url: https://bsky.app/profile/mteb.org/post/3mya6a2o6ex2j
---

```
1/ MAEB and MVEB are out of beta. Their papers have been accepted, MAEB at NeurIPS and MVEB at EMNLP Findings, so the task lists are now fixed as v1. The tasks are the same as in beta.
```

```
2/ MAEB is our benchmark for audio embeddings: 30 tasks covering speech in 100+ languages, music and environmental sound. MVEB covers video: 23 tasks, including retrieval, classification and question answering.

Read more:
arxiv.org/abs/2602.16008
arxiv.org/abs/2606.14958
```

## LinkedIn

The Bluesky thread as one post, word for word.

```linkedin
MAEB and MVEB are out of beta. Their papers have been accepted, MAEB at NeurIPS and MVEB at EMNLP Findings, so the task lists are now fixed as v1. The tasks are the same as in beta.

MAEB is our benchmark for audio embeddings: 30 tasks covering speech in 100+ languages, music and environmental sound. MVEB covers video: 23 tasks, including retrieval, classification and question answering.

Read more:
arxiv.org/abs/2602.16008
arxiv.org/abs/2606.14958
```

## The claim

That MAEB and MVEB moved from beta to v1, what that changes for a user, and why now. No
scores: see "Why no scores" below.

Every statement in the text, and where it was checked (2026-10-12):

| statement | checked against |
|---|---|
| MAEB has 30 tasks, MVEB 23 | task lists in `mteb/benchmarks/benchmarks/benchmarks.py` at `50631ac4`, counted by hand, and cross-checked against the live leaderboard API (`/v1/benchmarks/{name}/scores` → `tasks`): MAEB(v1) 30, MAEB(v1, audio-only) 19, MVEB(v1) 23, MVEB(text, video, v1) 19, MVEB(video, v1) 9. Also matches both abstracts (30 / 23). |
| MAEB: speech in 100+ languages, music, environmental sound | MAEB abstract (arXiv:2602.16008). The 100+ comes from `SIBFLEURS` and `FleursT2ARetrieval`, both 102 language codes in `eval_langs` at `50631ac4`. Music: `GTZANGenre`, `BeijingOpera`, `MridinghamTonic`, `JamAlt*`; environmental: `UrbanSound8KT2ARetrieval`, `ClothoT2ARetrieval`, `VehicleSoundClustering`, `FSD2019Kaggle`. |
| MVEB: video with its soundtrack; retrieval, classification, QA | MVEB description at `50631ac4`: "Audio-visual video embedding quality … tasks selected to maximize coverage of audio-video joint modality inputs". Task types: Any2AnyRetrieval (10), VideoClassification (6), VideoCentricQA (1), plus clustering, pair classification, zero-shot. |
| out of beta, as v1 | Diff: every benchmark renamed `(beta)` → `(v1)`; `is_beta=True` removed 46 times across the task files. |
| "Beta meant the task lists could still change" | The removed `is_beta` warning in `abstask.py`: "still being tested and may be subject to changes … scores … liable to change". The removed MAEB description text: "Currently in beta pending peer review." |
| "kept in beta until their papers had passed peer review … accepted at NeurIPS and EMNLP Findings" | kennethenevoldsen (maintainer), 2026-10-12: leaving beta was tied to paper acceptance, MAEB at NeurIPS and MVEB at EMNLP. Findings track for MVEB from issue #5292 ("accepted into EMNLP findings") and the first author's own site (adnanelassadi.github.io: "Findings of EMNLP 2026"; MAEB listed as NeurIPS 2026). The removed MAEB description also read "pending peer review". |
| tasks are the same as in beta | The diff changes names, aliases, descriptions and citations only. No task list changed. |
| old names still work | `aliases=["MAEB(beta)", "MAEB"]` etc. on all five benchmarks at `50631ac4`. (This is true in the Python package. The leaderboard **API** returns 404 for `MAEB(beta)`/`MVEB(beta)`, so any external link or script using the old name against the API is broken. The post makes no claim about the API.) |
| no credit line | Deliberate; see Notes, "Credit". |

The leaderboard already serves the v1 names: `MAEB(v1)`, `MAEB(v1, audio-only)`,
`MVEB(v1)`, `MVEB(text, video, v1)`, `MVEB(video, v1)` from `/v1/benchmarks`.

### What "out of beta" concretely changed (mteb#5640)

- **Names.** `MAEB(beta)` → `MAEB(v1)`, `MAEB(beta, audio-only)` → `MAEB(v1, audio-only)`,
  `MVEB(beta)` → `MVEB(v1)`, `MVEB(video, beta)` → `MVEB(video, v1)`,
  `MVEB(text, video, beta)` → `MVEB(text, video, v1)`. Old names kept as aliases.
- **Task flags.** 46 `is_beta=True` lines removed. These are all video/audio-visual task
  files (the MVEB side); MAEB's tasks were not flagged at task level. Two consequences:
  mteb no longer warns "currently in beta" when those tasks load, and they now appear in
  `mteb.get_tasks()` by default (`exclude_beta=True` is the default there).
- **Descriptions.** "Currently in beta pending peer review" dropped from MAEB's.
- **Citation.** MVEB had `citation=""`; now has a BibTeX entry (EMNLP 2026, OpenReview).
- **Leaderboard menu.** The Audio and Video menu entries point at the v1 names.
- **Not changed.** Task lists, task contents, aggregation. A result on a beta task counts
  toward v1 without rerunning, as far as task definitions go. Model run settings are a
  separate matter (#5454).

## Why no scores

Considered and rejected for this post:

- **Every audio and video result on the board predates mteb 2.24.4** (#5454), which
  changed per-model clip length, sampling rate and frame sampling. MTEB's own release
  note says earlier results are not comparable with new ones. A "who leads MAEB v1"
  line would rank old-config numbers on the day the benchmark is declared stable, and
  could be overturned by the reruns within weeks.
- **Coverage is thin.** From the live API: MAEB(v1) has 22 of 69 models with all 30
  tasks; MVEB(v1) has 16 of 36 with all 23. kennethenevoldsen's approval of the PR noted
  "we are missing some reference model coverage". A ranking would also be a statement
  about who submitted.
- **One post, one claim.** The claim here is the benchmark's status. Its results deserve
  their own post once rerun on ≥ 2.24.4, and that post has a better story: the papers'
  "no single model dominates" finding (audio-text contrastive models near random on
  multilingual speech, speech models the reverse), re-checked under the new configs.

So no `fetch.py`. Nothing in the text is a score, and every count was checked from the
code at the merge commit or the live API, as listed above.

## What must not be claimed

- **Not "accepted at EMNLP" without "Findings".** MVEB is in Findings of EMNLP 2026
  (issue #5292 and the first author's site). The BibTeX added in mteb#5640 gives the main
  proceedings as booktitle; worth a fix upstream, and the post follows the two sources
  that agree.

- **Not "a MAEB(v1) score means the same everywhere".** An earlier draft said this. It
  is false while pre- and post-2.24.4 runs are mixed. Same task set ≠ same score.
- **Not that future changes "will come as v2".** That is MTEB's naming convention
  (`MTEB(eng, v2)`), but nothing in this PR commits to it.

## Notes

**Release check before 2026-10-19 14:30.** Scheduled on 2026-10-12 while no mteb release
contained 50631ac4 (latest 2.24.10, "ahead"). The post gives no code, so it is not wrong
without a release, but `pip install mteb` users would still see the `(beta)` names. If no
release containing 50631ac4 exists by the morning of the 19th, move the date.


**Written for a reader who has never heard of either benchmark.** Part 1 says what they
measure and that they are now stable. Part 2 says what beta vs v1 means and why now.
Part 3 says what to do, plus the one caveat that changes how to read the leaderboard.
The rename list, `is_beta` and the citation are kept out of the text: they are the diff,
not the meaning.

**Credit.** No credit line, on kennethenevoldsen's instruction (2026-10-12). Both
benchmarks are a group effort (18 authors on MAEB, 10 on MVEB), and naming one or two
people would misrepresent that, while naming everyone does not fit. See CONTRIBUTING.md,
"Credit".

**Type.** `benchmark_addition` is the closest listed shape ("what it measures and why it
did not exist before"). Strictly this is a status change, not an addition. For most of
this account's followers, though, it is the first time either benchmark has been
introduced. The 2026-08-18 MOEB roundup covered individual audio/video tasks and never
named MAEB or MVEB.

**Breadth.** Of the last ten posted, one (2026-08-18) is audio/video. This post broadens
coverage, and MAEB's multilingual speech side is unusually broad.

**Side effect elsewhere (not touched).** `2-drafting/languagebind-omni` uses the name
`MVEB(beta)` in its text. That name now resolves in mteb but returns 404 on the
leaderboard API, so its fetch path may need the v1 name.

## Decisions for the reviewer

1. **Sequencing with `4-scheduled/2026-10-13-audio-video-input-config` (#5454).** Recommend #5454
   **first**. It is actionable today for anyone holding audio/video results, and this post's
   part 3 leans on it. This post goes out after, on a different day, once a release
   contains #5640 (see `blocked_on`). If #5454 has gone out by then, part 3's middle
   paragraph can shrink to a pointer ("see our 2.24.4 post"), which frees about 120
   characters. Merging the two into one thread is possible, but would be a third post
   with two claims. Not recommended.
2. **Post before or after the reruns?** Posting before means announcing "stable" next to
   a board we are telling people not to trust. Part 3 handles that honestly, but it is
   a strange pair of messages. Waiting until the reference models are rerun on ≥ 2.24.4
   gives a cleaner post, and possibly a later results post. The cost is that "out of
   beta" ages; expiry is set to 2026-11-09. Is there a rerun date?
3. **Venue wording.** Resolved: acceptance is the reason for leaving beta (owner, 2026-10-12).
   The post says "EMNLP Findings" rather than "EMNLP" because both sources say Findings;
   change it if you know otherwise.
4. **`AdnanElAssadi56` in `contacts=`** is not a GitHub account. Worth a one-line fix
   upstream. It does not affect this post.
5. **Card.** Text-only as drafted. One option is a two-column card listing the task
   types per benchmark plus the three MVEB / two MAEB variants (e.g. video-only for
   encoders with no text tower). That would be verifiable from the code and would carry no
   scores. Worth it only if you want the "what they measure" part to land at a glance.
