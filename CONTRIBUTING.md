# Working on posts

How a candidate becomes a scheduled post, and the editorial rules that decide what gets
said. `README.md` has the pipeline shape; `AGENTS.md` has the rules in one-line form.
This file is the reasoning behind them, which is what you need while actually drafting.

Written as instructions because that is what an agent needs, and read as documentation
because that is what a person auditing it needs. Same text either way.

Two criteria run through every stage: a post must be **newsworthy**, and it must be **easy
to read and hard to misread**. Both are judgement calls that `mteb-validate` cannot make,
and a post that fails either is rejected however correct its numbers are. Neither is
new; each borrows from standards that journalism and science communication already use
(see [References](#references); readable copies are in `docs/standards/`).

---

## 1 → 2: is this worth working up?

A candidate is a PR and a guess. Most die here, and that is the point — the repos merge
3-4 PRs a day, so the bottleneck is not finding things to post but choosing the one or
two a week worth saying.

**Is it news?** Someone who follows MTEB should be glad this showed up in their feed.
Every post spends the attention of people who chose to follow us. A feed that posts every
merge teaches them to scroll past, and then the posts that matter get scrolled past too.
Journalism calls the properties that make something worth reporting *news values*. Four
from Harcup and O'Neill's list [1] fit this account:

- **Relevance:** it matters to people who build or choose embedding models, not mainly to
  the people who made the change.
- **Magnitude:** it is big enough to change what someone would do: a new benchmark to
  evaluate on, a model that leads its class, a change that moves scores.
- **Surprise:** the result is not what a reader would have guessed.
- **Follow-up:** it moves a story we have already told, such as rerun results after a
  settings change.

When in doubt, don't post. A quiet week costs nothing, but a dull post costs followers.
The rules below are this criterion applied to the cases that come up most often.

**A model addition is postable only once results are merged.** A `ModelMeta`
registration with no scores is plumbing, not news. The pairing — a PR in `mteb` plus its
partner in `results` — is the single most reliable trigger there is.

If the results are not there yet, that is `blocked_on:`, not a rejection. If they are
never coming (metadata-only, a revision bump, a wrapper fix), reject it with that as the
reason.

**Do not trust labels.** Roughly half of genuine model additions carry no label at all,
and `jina-reranker-v3.5` carried `new model` while being pure plumbing. Title
conventions (`model:`, `task:`, `[MOEB]`, `fix:`, `ci:`) are far more consistent, which
is what `mteb-scan` keys off.

**Patch releases are not features.** The package shipped 8 releases in 12 days. Only
minor/major versions, or a specifically notable capability, qualify.

**Two categories are almost never worth a post:**

- *Minor corrections and bug fixes.* The exception is a fix with a result a reader would
  find surprising — a large speed-up, say — where the number is the story.
- *Plumbing for a larger research project.* Scaffolding for work that has not landed yet
  has nothing to announce. This one is contextual: if the project itself is the news and
  it is public, that is a different post.

**Results added for an existing model** are a real category and easy to miss, since the
model itself was announced long ago. Worth a post only when the new numbers change
something — a new benchmark, a size class nobody had covered, a surprising result.

**Clusters can be grouped or spread.** 18 audio/video tasks landed in one month. Group
them into one roundup when no individual item carries its own story; spread them across
days when they do.

---

## 2 → 3: making it checkable

This is the stage that earns the account its credibility. Everything a reader could
verify must be verified before the post reaches review.

### Recompute every number

Contributor-supplied score tables are *claims*. MTEB's account restating them verbatim
lends the benchmark's credibility to numbers nobody checked. Pull them from the results
repo through `Benchmark.get_score()` — the same aggregation the leaderboard uses — and
compare. If recomputation disagrees with the PR, the post does not run.

`docs/mteb-data.md` covers the API and the several ways this goes silently wrong.

### Say what MTEB measured, not what the authors claim

A post reports what MTEB measured: scores, and the model facts MTEB records and shows on
the leaderboard, such as active parameters. It does not pass on the authors' account of
their own model, such as why it is small, how fast it runs, what it costs to serve, or
what its architecture makes possible. Even when such a claim is true, MTEB did not
measure it. Repeating it lends the benchmark's credibility to a message the authors are
better placed to make themselves, and it reads as promotion.

The test for each sentence: could a reader check it on the leaderboard or in the results
repo? If not, cut it. Explaining a term the reader needs (what a sparse model is, what a
benchmark measures) is fine. Claims about a model's speed or efficiency are not, unless
MTEB measured them.

### Default to MTEB(Multilingual, v2)

Unless the post is specifically about English, or about a domain or modality that has its
own benchmark, **`MTEB(Multilingual, v2)` is the general-purpose benchmark**. It is newer,
less exposed to overfitting than the English set, and it describes performance for far
more people. `MTEB(eng, v2)` answers a narrower question and should be chosen on purpose,
not by default.

This is worth stating because the default slipped once already. Two state-of-the-field
posts were built on `eng v2` for a purely mechanical reason — 41 tasks loaded faster than
131 — which stopped being true once load cost turned out to scale with model count rather
than task count, and stopped mattering entirely once the leaderboard API made either
about a second. A performance workaround outlived its cause and quietly narrowed the
claims to English.

If you use `eng v2`, say in the post why English is the right scope for that claim.

### Curate for breadth

This account exists to encourage embedding models that work broadly — across languages,
domains and modalities. What it chooses to cover is itself a signal about what counts as
progress, so the *mix* of posts is an editorial object, not just the individual posts.

Check the mix at scheduling, over roughly the last ten posts:

- **Languages.** English-only results are a narrow slice. If several posts running have
  been English, prefer a multilingual or non-English one.
- **Modalities.** Text dominates by volume. Audio, image and video work is
  under-represented relative to how much of it is landing — the MOEB cluster added 18
  audio and video tasks in a month and none of it has been posted.
- **Domains.** Legal, code, medical and finance benchmarks exist and get far less
  attention than the general leaderboards.
- **Kinds of post.** Model announcements are the easiest to produce and will crowd out
  dataset, benchmark and feature posts if nothing pushes back.

When two candidates are otherwise close, **prefer the one that broadens coverage**. When
a whole area has gone quiet in the feed but not in the repos, that is a reason to go
looking rather than to wait.

This is a bias correction, not a quota. A genuinely important English text model should
still be posted; the rule is to notice when a run of posts has narrowed, and to reach for
breadth when the choice is otherwise a toss-up.

### Ask who is missing before believing a ranking

A leaderboard rank is a fact about **who submitted**, not about who is best. On the big
general benchmarks the two are close enough to ignore. On a domain benchmark they are
not: a domain model has every incentive to submit domain results, and a frontier
generalist has none.

This is measurable, so measure it. Take the top ~20 models on a broad benchmark and check
how many appear in the cohort you are about to rank. For `MTEB(Law, v1)`: **14 of the top
20 `MTEB(eng, v2)` models had no complete Law results**, including the top four overall.
A post concluding "specialists beat generalists" from that ranking would have been
measuring submission behaviour and calling it capability.

Two ways out, in order of preference:

1. **Find the claim that survives.** A *within-model* comparison — the same model on two
   benchmarks — is untouched by who else submitted. `Jasper-Token-Compression-600M` is
   5th on English and 29th on legal; that holds no matter who is absent, and it turned
   out to be the more interesting finding anyway.
2. **Scope the claim to the cohort.** "Of models evaluated on X" is honest and often
   enough. Say it in the post, not only in the notes.

Never state or imply the unscoped version. The absent models are usually absent precisely
because they are the ones that would test the claim.

### One post, one claim

A model announcement and a claim about the field are different posts even when they use
the same query and the same chart. `dinghy-law-family` says "this model is first";
`legal-specialisation` says "specialists beat generalists here". Same eight rows, but the
subject differs and so does the risk: an announcement is wrong only if a number is wrong,
while a field claim is wrong if a *category* is wrong.

The tell is in the card. An early dinghy-law card coloured every legal-domain model,
which encoded the field claim on a post that was announcing a model — and left a reader
asking what the colour meant, because nothing on the card was making that argument.

**Colour may only encode the claim the post is actually making.** If a distinction is
worth colouring, it is worth a sentence; if it does not get a sentence, it should be
context grey.

When two posts do overlap, mark it (`competes_with:` in the frontmatter) and choose
between them rather than running both in a week. Merging is sometimes the better answer,
but a merged post is a third thing that needs its own draft, not either original with a
paragraph bolted on.

### Choose the cohort, and record it

Any comparison names *other people's models*, so the cohort has to be one those authors
would accept. This is the one editorial judgement a reader cannot check against the
leaderboard, which is why it lives in `fetch.py` as code rather than in prose.

Two filters that turned out to matter more than they look:

- **Peers must be built for the benchmark being cited.** Bekko's first cohort swept in
  `e5-small-v2`, `bge-small-en-v1.5` and `all-MiniLM-L6-v2` — English-only models
  scoring 41-45 on a *multilingual* benchmark. They score low because they were never
  built for it. Keeping them would have inflated Bekko's margin **and** implied three
  well-regarded models were worse than they are.
- **Complete task coverage only.** MTEB aggregates partial results without complaining.
  A mean over a subset of tasks is not comparable to a mean over all of them.

The general form: a comparison flattered by models that were never in the race is the
fastest way for this account to lose the trust it exists to protect.

`data.json` records every model that qualified, including any that beat the subject.
Filtering it to the flattering rows would make it useless as evidence.

### Write the post

**300 characters.** This is the dominant constraint. LMArena's LinkedIn page is the
tonal reference, but it transfers as tone and cadence only — those posts run 5-10x too
long structurally.

House style: factual, specific, understated. Lead with the concrete thing. No hype
adjectives, no emoji strings, no hashtag stuffing.

**Easy to read.** The plain-language standard ISO 24495-1 [2] calls a text plain when its
readers can easily find what they need, understand what they find, and use it. In 300
characters:

- **Find:** the point comes first, and the card title states it.
- **Understand:** no jargon that a reader would need the PR to decode, and no exact
  numbers that don't carry the point.
- **Use:** the post ends with what it means for the reader.

**Hard to misread.** The SPJ Code of Ethics [3] asks journalists to "take special care not
to misrepresent or oversimplify in promoting, previewing or summarizing a story", and
reminds them that "neither speed nor format excuses inaccuracy". A 300-character post is
exactly such a summary, and its format is no excuse. Sumner et al. [4] found that most
exaggeration in science news was already in the press release: advice the study did not
support, causation claimed from correlation, and conclusions about people drawn from
animal studies. They also found that exaggeration did not win more coverage, and caveats
did not cost any. We are the press release here. Our equivalents:

- A ranking within a cohort read as a ranking of all models (see *Ask who is missing*).
- A score on one benchmark read as general quality.
- "Smallest", "first" or "best" without its scope.
- Numbers that look comparable but aren't (different benchmark versions or settings).

To check, ask what someone who reads only the first sentence, or only the card title,
would now believe. If that is wrong or overstated, rewrite it. Put the scope in the same
sentence as the claim, not in a later part of the thread.

**Explain, don't list changes.** Write for a reader who has never seen the PR. A post
about a change answers, in order: what the situation was and why it was that way, what
changed and why, and what it means for the reader (what to do). A list of what changed
(clip length, sampling rate, frame count) reads like a diff and tells the reader nothing.
One concrete example ("models were only scored on the start of each recording") beats an
enumeration. Plain sentences, too: if a line sounds clever but you could not say what it
means ("part of what the leaderboard measured was our setting"), cut it. Both failures
are in the history of `audio-video-input-config` (2026-10-12).

**Voice is "we", meaning the MTEB team** — the org is accountable for what goes out
whoever drafted it. Never first-person-singular: the tooling is not a character, and a
character invites the replies this account does not make. "We" is for accountability, not
warmth. `profile.md` has the account-level identity.

**Anything true of every post belongs in the bio, not the feed.** If a draft is mostly
explaining what the account is, it is competing with `profile.md` and will lose.

**Internal reasoning never reaches the reader.** `## Notes`, `todo:`, and code comments
exist to tell the human reviewer why a post was built the way it was — not to tell the
audience. A line like "no single one of these is an announcement, but together they are a
real story" is honest and useful in `## Notes`; in a headline it describes this pipeline's
own editorial process to a reader who never asked and doesn't care, and it reads as an
apology for the post instead of a claim about MTEB. It has leaked before: a Notes sentence
copied wholesale into a card's `COPY.subtitle`. Before finalizing a post, read every
string a reader will actually see — the fenced text blocks, and every value in the card's
`COPY` object — and check none of it is really addressed to a reviewer.

**Name models by their full Hugging Face id** — `hotchpotch/bekko-embedding-v1-a8m`, not
`bekko`. It costs characters, but an abbreviation is harder to check against the
leaderboard and two models can abbreviate to the same string.

Post shapes that have worked:

| type | shape |
|---|---|
| `model_addition` | what it is · the number that makes it interesting · the benchmark it is on |
| `dataset_roundup` | a cluster's shared theme, then the task names with a one-word gloss each |
| `benchmark_addition` | what it measures and why it did not exist before |
| `state_of_field` | a claim about the whole registry, with the cohort stated |
| `feature_release` | minor/major versions only; the one thing that matters to users |

**A card buys back character budget.** Once a draft carries two model names, two scores,
a benchmark name and a credit line it is already at ~290 characters with nothing left to
say why anyone should care. Moving the numbers into the image frees the text to make the
argument. See `docs/card-design.md`.

### The LinkedIn version

**The LinkedIn post is the Bluesky text.** Join the thread's parts into one post, drop the
`1/ 2/` numbering, and change nothing else. The only permitted difference is the credit
line, which may @-mention someone who has a `linkedin:` entry in `social-handles.yaml`.

Do not add detail, caveats, links or instructions to the LinkedIn version, even though it
has room. If something is missing that a reader genuinely needs, it belongs in the Bluesky
text, or the post needs a rethink. An expanded LinkedIn version was rejected on
2026-10-12 for exactly this, and the earlier rule allowing a separate version for a
forced-out caveat is withdrawn.

It goes in `post.md` under a `## LinkedIn` heading inside a ```` ```linkedin ```` block —
same file, and the fence keeps it out of the 300-character check, which only scans bare
``` blocks. Because it is the same text, the two can never disagree on a number; if they
do, that is a bug.

### Credit

Every post names the people whose work it describes. This is a community project and the
posts should read like it.

Credit and tagging are separate. Credit is unconditional and uses the GitHub handle as
plain text. Say what each person did, in MTEB's terms: "results submitted by X" for
whoever opened the results PR, "added to MTEB by X" for a task or model integration, and
"Work by X" for a change to MTEB itself. Credit the model or dataset authors by
organisation or paper ("Model from NAVER LABS Europe", "Dataset by Dalla Noce et al."),
not by a handle that only looks like theirs. Tagging uses a handle recorded in `social-handles.yaml`, with `via:` saying
where it came from.

**A handle the person links from their own GitHub profile can be used.** Check
`gh api users/<handle>/social_accounts` and the profile's website and bio. If they link a
Bluesky or LinkedIn account there, they have published it themselves, so add it to
`social-handles.yaml` with `via:` naming the source and date (for example, "linked from
GitHub profile, checked 2026-10-13") and tag them. The same goes for a handle the person
or a maintainer has given us directly.

Never infer a handle any other way: not by searching Bluesky or LinkedIn for the
person's name, and not from a profile that only looks like the right person. A
wrong-person mention is precisely the spammy, follower-farming behaviour this account
exists to avoid.

On LinkedIn, write the mention as `@Full Name` in the ```` ```linkedin ```` block. LinkedIn text is pasted by hand, and the
person posting must pick the name from LinkedIn's mention dropdown, or it stays plain text.

State-of-the-field posts describe no single person's submission and carry no credit line.
That is a deliberate signal, not an oversight.

The same goes for work that is a large group effort, such as an MTEB benchmark with a
many-author paper (MAEB, MVEB). Naming one or two people misrepresents a group effort,
and naming everyone does not fit, so these posts carry no credit line. The paper links do
the crediting.

---

## 3 → 4: scheduling

Floor is one post a week, ceiling is **one a day**. With 3-4 PRs merging daily the
ceiling binds, not the floor — the job is spreading material evenly, not hunting for it.

Never post twice in a day to clear a backlog. A long queue means spread wider, not batch.
A thin week is not a reason to promote something that failed the rules above; that is
what the roundup shape exists for.

Check `expires:` before scheduling. News older than about a month is not news, and a
post that sat in review past its window should be rejected rather than shipped stale.

Read the post once more as a follower would, against both criteria: is it still news on
the day it goes out, and does the first sentence or the card title alone leave a true
impression? Drafting makes a post feel finished; this is the check that it is worth
sending.

**This move is the human's, and only the human's.** `3-review` means "a person has not
looked yet". An agent that drafts a post and then schedules it has removed the only step
that makes any of the rest trustworthy — and it is an easy mistake, because the work
feels finished. Record who decided in `approved_by:`; `mteb-validate` refuses a scheduled
post without a named approver.

**Add the date to the folder name when you move it here** — `dinghy-law-family` becomes
`2026-08-06-dinghy-law-family` — and set `scheduled_for:` to match. That is the only
point in the pipeline where a folder gets a date, which is what keeps the date
meaningful.

**Default to `14:30:00+02:00`** unless a post has a reason to go out elsewhere. The
account's own followers were sampled on 2026-08-07 — 978 posts from 28 of 30 — and their
activity peaks at 16:00 CEST (10:00 ET) with a second peak at 13:00 CEST. The earlier
09:00 default was worse on both counts: it is 03:00 US Eastern, and it is not the European
peak either. 14:30 sits inside the plateau between the two peaks rather than over-fitting
to thirty people. Re-measure when the follower count is large enough for the sample to
mean something; the method is in the git history of this line.

---

## Validate before moving a post forward

```bash
uv run mteb-validate                    # whole pipeline
uv run mteb-validate --stage 3-review   # one stage
```

It checks what a machine can: the 300-character limit, required frontmatter per stage,
that `media:` points at a file that exists, that a thread declares as many
posts as it contains, that every card carries alt text and has been rendered, that folder dates
appear only once scheduled and match `scheduled_for:`, that no two posts share a day, and
that a scheduled post is not already past its `expires:` date.

It also prints the pipeline's shape — how many posts sit in each stage, and how many
candidates and drafts are past their expiry. That count is not a warning, because
rejecting a stale candidate is a judgement someone has to make; it is there so the backlog
is visible before it gets to be a third of the queue.

**A clean run means nothing is obviously broken. It does not mean the post is good.**
Whether a cohort is fair, whether a claim is scoped to its evidence, whether the subject
is worth anyone's attention — none of that is checkable, and all of it is in this file.
Treat the validator as the floor, never the bar.

So check by hand, every time a post moves forward:

- **Newsworthy:** would a follower be glad to see it? (*Is it news?*, under 1 → 2)
- **Easy to read:** is the point first, free of PR jargon, and does it say what it means
  for the reader? (*Write the post*)
- **Hard to misread:** what would someone who reads only the first sentence, or only the
  card title, believe? Is that true? (*Write the post*)

Record anything borderline in `## Notes` so the reviewer sees the call you made.

## Rejecting

Every rejection needs a `reason:`. `rejected/` is the most auditable thing in the repo —
it is the record of what the pipeline chose *not* to say, and the first place to look if
the account's judgement is ever questioned.

Rejections stick: `mteb-scan` skips any PR already referenced anywhere in the pipeline,
so a rejected candidate does not reappear the next morning. If circumstances change
(results finally land), move the folder back to `1-candidates/` by hand.

## References

Readable copies, with licence notes and a record of what was changed, are in
`docs/standards/`. The full text is included where the licence allows it; otherwise there
is a summary with the relevant clauses quoted.

1. Harcup, T. & O'Neill, D. (2017). What is news? News values revisited (again).
   *Journalism Studies* 18(12), 1470–1488.
   [doi:10.1080/1461670X.2016.1150193](https://doi.org/10.1080/1461670X.2016.1150193).
   CC BY 4.0. Full text: `docs/standards/harcup-oneill-2017-what-is-news.md`.
2. ISO 24495-1:2023. *Plain language — Part 1: Governing principles and guidelines.*
   International Organization for Standardization. Paywalled; summary only:
   `docs/standards/iso-24495-1-plain-language.md`.
3. Society of Professional Journalists (2014). *SPJ Code of Ethics*, revised 6 September
   2014. <https://www.spj.org/ethicscode.asp>. All rights reserved; relevant clauses quoted
   in `docs/standards/spj-code-of-ethics.md`.
4. Sumner, P., Vivian-Griffiths, S., Boivin, J., Williams, A., Venetis, C. A., Davies, A.,
   Ogden, J., Whelan, L., Hughes, B., Dalton, B., Boy, F. & Chambers, C. D. (2014). The
   association between exaggeration in health related science news and academic press
   releases: retrospective observational study. *BMJ* 349, g7015.
   [doi:10.1136/bmj.g7015](https://doi.org/10.1136/bmj.g7015). CC BY 4.0. Full text:
   `docs/standards/sumner-2014-exaggeration-press-releases.md`.
