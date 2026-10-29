# Scheduling a post

How a post gets on the account. Written for someone who has something worth posting and
wants it to go out — a new model, a benchmark, a result that reads wrong, a change to the
package.

You do not need write access, and you do not need the agent. The path is a pull request,
and a maintainer does the part that publishes.

## What you need first

A post is two things: **a text** and **the evidence for every number in it**. If you cannot
recompute a number from the results repository or the leaderboard API, it does not go in
the post — contributor score tables are claims, not facts, and this account does not
launder them.

Before you write anything, check the two editorial criteria in
[CONTRIBUTING.md](../CONTRIBUTING.md): is it **news** to someone who follows MTEB, and is
it **hard to misread** by someone who sees only the first sentence or only the image? Most
candidates fail the first one. A quiet week costs nothing; a dull post costs followers.

## The folder

One folder per post, under `posts/3-review/` — that is the stage for "everything checkable
has been checked, waiting for the editorial call". Name it after the post, with no date:

```
posts/3-review/embeddinggemma-2/
  post.md                    required — the text, the frontmatter, your notes
  fetch.py                   required — the query that produced every number
  data.json                  required — its output, every row, not just the good ones
  card-1-embeddinggemma-2.html   optional — the image, as HTML
  card-1-embeddinggemma-2.png    required if the html exists — the rendered result
```

A date never appears in a folder name until the post is scheduled; the maintainer adds it
when they set the date, and that is the only moment it means anything.

If you are only proposing an idea — "something happened here, someone should look" — put
it in `posts/1-candidates/` with just a `post.md` and a sentence of why. Run
`uv run mteb-scan --since <date>` to see what the scanner would generate; it is the same
shape.

## `post.md`

The fenced blocks are the *only* thing that gets posted. Everything outside them is for the
reviewer.

````markdown
---
id: embeddinggemma-2                     # must equal the folder name
type: model_addition                     # model_addition | results_addition |
                                         # benchmark_addition | dataset_roundup |
                                         # state_of_field | feature_release
trigger: mteb#5588 + results#793         # the PRs this came from
trigger_date: 2026-10-18                 # when it happened, not when it goes out
expires: 2026-11-18                      # past this, it is not news any more
subject: google/embeddinggemma-2
verified: true                           # you checked every number yourself
evidence: data.json
media: card-1-embeddinggemma-2.png       # or `none` — see below
thread: 2                                # omit for a single post
sources:
  - https://github.com/embeddings-benchmark/mteb/pull/5588
  - https://github.com/embeddings-benchmark/results/pull/793
---

```
New on MTEB: google/embeddinggemma-2, an open-weights model that handles text, images and audio.
```

```
MIEB(lite) 63.52 (5th of 51), MTEB(Multilingual, v2) 60.52 (33rd of 96), MAEB(v1) 49.31 (7th of 23).

Added to MTEB by schechterh; results submitted by KennethEnevoldsen.
```

## LinkedIn

The thread joined into one post, word for word, with the numbering dropped.

```linkedin
New on MTEB: …
```

## The claim

One paragraph: what this says, and what bounds it.

## Scope: who is missing

Who did not submit, and whether their absence would test the claim.

## Notes

Anything the reviewer should know: why this angle, what you left out and why.
````

Rules that will bite you:

- **300 characters per fenced block.** That is the dominant constraint, and the validator
  measures it exactly. A thread is several blocks; `thread:` must equal their count.
- **Bare fences only** — ```` ``` ```` with nothing after it. A block tagged ```` ```text ````
  is not counted, and will not be posted.
- **The LinkedIn block must be the Bluesky thread joined verbatim** — same words, no
  added caveats, no links. The only permitted difference is the credit line, which may
  `@Name` someone who has a `linkedin:` entry in `social-handles.yaml`.
- **Name models by full Hugging Face id** (`hotchpotch/bekko-embedding-v1-a8m`, not
  `bekko`). An abbreviation is harder to check against the leaderboard.
- **Credit the people, don't guess handles.** `results submitted by X` / `added to MTEB by
  X` in plain text. Tagging needs a handle recorded in `social-handles.yaml` with a source,
  and a handle the person publishes on their own GitHub profile is the only automatic way
  to justify one.
- **`media: none` is a real choice**, for a post with no measurement to show. Everything
  else needs a card.

## The card

One image, 1200×1200, with the numbers and its own alt text. `docs/card-design.md` explains
the rules (bars start at zero, missing results are never plotted as zero, colour encodes
the claim). For a `model_addition` post, copy a starting point from
`templates/model-release/` and fill its `COPY` object; anything else is bespoke.

```
uv run mteb-render --card posts/3-review/<id>/card-1-<slug>.html \
                   --out posts/3-review/<id>/card-1-<slug>.png
```

That writes the alt text back into the HTML, where the publisher reads it — never paste an
alt text in by hand, and never commit a card without one.

## Check it, then open the PR

```bash
uv run mteb-validate --stage 3-review
uv run mteb-validate                       # the whole pipeline, plus the queue summary
```

Zero errors is the floor, not the bar. Then open a PR. What a reviewer is looking at:

1. **Is it news**, by the criteria in `CONTRIBUTING.md` — and would they have posted it.
2. **Is every number recomputable** from `fetch.py`, and does `data.json` hold the rows that
   beat the subject, not only the flattering ones.
3. **Is the claim scoped** — does the ranking say how many models were compared, and is the
   cohort one the named models' authors would accept (complete task coverage, peers built
   for that benchmark).
4. **Would the first sentence alone mislead?** And the card title alone?

Expect a rewrite of the first sentence. That is the normal amount of review here, not a
rejection.

## Who sets the date

**A maintainer.** Scheduling is publishing: a folder in `posts/4-scheduled/` goes out on a
timer, unattended, and cannot be taken back. So the maintainer, on your PR, before merging:

1. renames the folder to `YYYY-MM-DD-<slug>`,
2. adds `scheduled_for:` with a full timestamp **and a timezone offset**,
3. adds `approved_by:` with their name,
4. moves the folder to `posts/4-scheduled/`.

Doing it on the branch rather than after the merge is deliberate: the reviewed state and
the published state are the same commit.

Timing conventions, not rules of physics:

- **One post a day, maximum.** A backlog spreads wider; it never batches.
- **Default `14:30:00+02:00`.** The account's followers peak at 16:00 CEST with a second
  peak at 13:00; 14:30 sits in the plateau between them rather than over-fitting to a
  small sample.
- **A naive timestamp is rejected.** `2026-11-03T14:30:00` means a different instant on a
  UTC runner than it does to you, and the difference is exactly the hour nobody is looking.

## What the publisher will and will not do

`mteb-publish --due` selects the single post whose time has passed and, with `--send`,
publishes it. It refuses to send a post that:

- is not in `posts/4-scheduled/`,
- has no named `approved_by:`,
- is not due yet,
- was due on an earlier day — a delayed run still publishes later the same day, but a queue
  that has been stuck for days is not flushed into a feed where nobody is asking,
- is already on the timeline (it checks before sending, because publishing and recording
  the post are separate steps and CI is not transactional),
- exceeds 300 characters.

After sending it stamps `posted_on:` and `url:` and moves the folder to `posts/5-posted/`,
which is the archive — every number in it recomputable from the `fetch.py` beside it.

## If you do not have write access

Fork the repo, add your folder on a branch, and open the PR from the fork. Nothing about
the process changes: a maintainer reviews it, schedules it on the branch, and merges.
