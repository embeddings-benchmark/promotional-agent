# promotional-agent

An experiment in having an agent write MTEB's social posts — new models, results,
datasets, benchmarks and features — without it saying anything MTEB would have to take
back.

It publishes. Twenty posts went out between 2026-08-03 and 2026-10-26 to
[@mteb.org](https://bsky.app/profile/mteb.org) on Bluesky, each one drafted, verified and
approved as a folder in `posts/` before a timer sent it. `posts/` is still the publishing
target: the drafting, the numbers and the review are files in git, and the Bluesky client
(`mteb-publish`) reads them rather than anything retyped.

MTEB spans three repositories — `mteb` (the evaluation package, plus dataset and model
implementations), `results` (evaluation results) and the leaderboard. Posts are triggered
by what merges in the first two.

## Automation tier: **Supervised**

| tier | what runs itself | what a human does |
|---|---|---|
| Handheld | nothing | invokes every step, reviews every post, publishes by hand |
| **Supervised** ← *we are here* | scanning, drafting, verifying, **publishing on a timer** | approves each post before it goes out |
| Autonomous | the whole loop, including what to say | audits after the fact, inside guardrails |

What is automated is the **trigger**, not the judgement. `.github/workflows/publish.yml`
runs hourly and sends the one post whose `scheduled_for` has passed. Every post it sends
was written, checked and approved by a named person first, and `mteb-publish` refuses to
send one that was not.

The account carries the **`bot` self-label** accordingly. Bluesky recommends it for
accounts that publish automatically, and it went on in the same change that added the
timer — the failure that matters is publishing on a schedule while presenting as a person
typing. It is a field on our own profile record and can be removed if the tier changes
back.

Three guardrails make unattended publishing safe enough to leave alone:

- **The rest of the scheduled day.** A run delayed by GitHub still publishes — cron is
  best-effort and skips under load, and a 09:00 post going out at 11:00 is on time in
  every sense a reader cares about. Once the local day is over it refuses, because a queue
  that has been stuck for days would otherwise flush itself, and those posts are answers
  to a question nobody is still asking.
- **A duplicate check.** Publishing and recording the post are separate steps and CI is
  not transactional, so the publisher asks the timeline what is already there before
  sending rather than trusting the repo to be up to date.
- **One at a time.** A backlog drains one post per run, never as a burst.

Reaching Autonomous would mean the agent choosing what to say without a person in the
loop. That needs an answer to the question this repo exists to ask — whether the numbers
can be trusted without a person checking them. The evidence is the published archive and
its `fetch.py` files: every number a reader saw can be recomputed from the folder it came
from.

## How you are meant to use it

**Drive it with an agent harness, not by hand.** Point one at the repo; it reads
`AGENTS.md` for the rules, `CONTRIBUTING.md` for the procedure, and runs the commands
below itself. Ask it for what you want — *"scan the last week"*, *"take the Bekko
candidate to review"*, *"reject this one, no results coming"*.

The commands exist so an agent has something reliable to call. Running them yourself
works and is sometimes the fastest way to check something, but the ergonomics are not
designed for it — a `fetch.py` takes four minutes and prints a cohort table, which is
useful to an agent deciding what to write and tedious to a person.

Your side of the loop is reading `post.md` files and moving folders between stages. That
is the review, and it is the part deliberately left to a human.

## How it works

A post moves through stages, and **the directory is its stage**. There is no `status:`
field — a folder and a field would drift the moment one changed without the other.

```
        mteb-scan
            │
            ▼
    1-candidates ──► 2-drafting ──► 3-review ──► 4-scheduled ──► 5-posted
```

A candidate that is not going to become a post is deleted, with a line in the PR or
commit saying why. Git keeps it; the pipeline does not.

| stage | what it means | frontmatter it adds |
|---|---|---|
| `1-candidates` | something happened; a guess at why it matters. No numbers yet. | — |
| `2-drafting` | being built, or stuck | `todo:` (our work) / `blocked_on:` (waiting on someone else) |
| `3-review` | everything checkable has been checked; awaiting the editorial call | `verified:` `evidence:` `media:` |
| `4-scheduled` | approved, with a date | `scheduled_for:` `approved_by:` |
| `5-posted` | archive of what went out | `posted_on:` `url:` |

Folders carry **no date until they are scheduled**. A candidate is just `dinghy-law-family`;
at stage 4 it becomes `2026-08-06-dinghy-law-family`. A date in a folder name therefore
means exactly one thing — when the post goes out — and it appears at the moment it stops
being a guess. When the thing *happened* is `trigger_date:` in the frontmatter, which is
a different fact and belongs there.

Everything behind a post lives in its folder, so any number can be traced without
leaving the folder it was published from:

```
posts/5-posted/2026-08-03-bekko-thread/
  post.md              the text (Bluesky and LinkedIn), frontmatter and editorial notes
  fetch.py             the exact query that produced the numbers
  fetch_tasks.py       a second query, for the thread's second card
  data.json            its output — the full cohort, not just the flattering rows
  card-1-frontier.html the card: its data, its copy, the markup that draws it, its alt text
  card-1-frontier.png  the rendered image
  card-2-tasks.html    the second part's card
  card-2-tasks.png
```

Cards are always numbered — `card-1-<slug>.html`/`.png`, even for a single-part post — so
`mteb-publish` can match each post part to its own card by filename alone. A thread adds
`card-2-<slug>.*`, `card-3-<slug>.*` and so on; a part with no numbered card of its own is
just text-only. `mteb-validate` rejects a bare `card.html`/`card.png`.

A candidate has only `post.md`. The rest appear as it earns them, so the stage is visible
from the file list alone.

## Running it

Everything runs through `uv`; there is no environment to set up.

```bash
# stage 0 — find things that might be worth posting
uv run mteb-scan --since 2026-07-24            # dry run: prints what it found
uv run mteb-scan --since 2026-07-24 --write    # create folders in posts/1-candidates/

# recompute a post's numbers from the results repo (~4 min; ~15 for a whole-registry post)
uv run posts/5-posted/2026-08-03-bekko-thread/fetch.py

# check every post against the mechanical rules (instant), and print the pipeline's shape
uv run mteb-validate
uv run mteb-validate --stage 3-review          # one stage
uv run mteb-validate --strict                  # warnings become failures

# render a card (~3 s)
uv run mteb-render --card posts/5-posted/2026-10-26-splade-code/card-1-splade-code.html \
                   --out posts/5-posted/2026-10-26-splade-code/card-1-splade-code.png

# what is due, without sending anything; --send publishes and files the post
uv run mteb-publish --due
uv run mteb-publish --all
```

`mteb-scan` is safe to re-run: any PR already referenced anywhere in the pipeline —
whether written as `mteb#5043` or as a GitHub URL — is skipped. A deleted candidate is not
remembered, so it can return in a later scan window; the window is about eight days, so
that is one extra proposal rather than a standing loop.

Each post's `fetch.py` is a standalone [PEP 723](https://peps.python.org/pep-0723/)
script declaring its own pinned dependencies. That is deliberate: a post's provenance
should not depend on the state of a shared environment.

## Checks

```bash
uv run --extra dev pytest      # the tooling's test suite (~0.2 s, no network)
uv run --extra dev ruff check  # lint
uv run mteb-validate           # the posts themselves
```

`.github/workflows/ci.yml` runs all three on every push and PR. `mteb-validate` covers the
rules a machine can check on a *post*; `pytest` covers the rules a machine can check on
the *tooling* — the date arithmetic, the cohort builders, and every publish-time refusal. Neither can tell you whether a post is worth publishing;
that is `CONTRIBUTING.md` and a person.

## Layout

```
README.md            this file — what it is, how it runs
CONTRIBUTING.md      how to take a candidate to a scheduled post, and the editorial rules
AGENTS.md            the non-negotiables, for whatever agent is driving
profile.md           account identity, voice, and the bio text
social-handles.yaml  GitHub -> social handle map, with sources; drives tagging
docs/
  card-design.md     how the charts are built, and why
  mteb-data.md       working with the MTEB API — the parts that surprise
  standards/         readable copies of the editorial standards CONTRIBUTING.md cites
src/mtebpost/
  scan.py            stage 0: candidate detection from merged PRs
  validate.py        the rules a machine can check, and the queue summary
  publish.py         the Bluesky client: due-post selection, guardrails, threading
  render.py          card.html -> png + alt text
  cards.py           writes query results into a card's #card-data block
  leaderboard_api.py live leaderboard-backend queries — the data path everything uses
  model_release.py   cohort selection, Pareto/radar/bars advice, card-data builders
  scoreboard.py      the local-`mteb` path; legacy, needs the `leaderboard` extra
templates/model-release/  the three card shapes (bars, pareto, radar)
posts/               the pipeline (above)
tests/               the suite ci.yml runs
assets/, brand/      logo, avatar and banner source
.github/workflows/   scan (weekly), publish (hourly), ci (every change)
```

`mteb` is heavy — torch, transformers, sentence-transformers, roughly 2 GB — and only
`scoreboard` needs it, so it sits behind the `leaderboard` extra. Nothing else does:
`model_release` and every `fetch.py` written since 2026-09 talk to the leaderboard API over
HTTP, which is both faster and current enough to know about a model registered last week.
Rendering a card does not pull a deep-learning stack either.
