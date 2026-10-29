# Account profile

Account-level copy: the handle, display name and bio. Not a post — this is the standing
description, and it changes rarely.

## The split

The bio answers **"should I follow this?"**. Posts carry **news**. Anything that is true
of every post belongs in the bio, not repeated in the feed.

That distinction is why there is no pinned introduction post. An explainer would mostly
restate the bio, and a first post is better spent on something that happened. One was
drafted and dropped; the reasoning is in the commit that removed it, and the condition
that would bring it back is a change to what the bio can carry.

## Identity

**The account is MTEB**, not a companion or a named bot. The org is speaking, and the org
is accountable for what goes out — an agent drafts, people review, and the byline belongs
to the people either way.

So: **`mteb`**, not "MTEB Agent" or "MTEB Bot". Naming the tooling in the handle would
make the tool the subject, invite people to address it, and imply an autonomy it does not
have.

**Voice is "we", meaning the MTEB team.** Not first-person-singular — the agent is not a
character and should never be given one, because a character invites replies and this
account does not reply. "We" is for accountability, not warmth: if a number is wrong, we
got it wrong. It is not a licence for "we're excited to share".

## Bluesky

**Handle:** `@mteb.org` — verified by a `_atproto.mteb.org` TXT record, so the handle is
its own proof of identity. No blue check is involved and nothing is impersonable without
DNS control.

**DID:** `did:plc:hf5dicjnj24ropzmc4ejdvgu` — this, not the handle, is the account's real
identity. Handles are rented and can change; the DID does not, which is why the TXT record
contains it (`did=did:plc:…`) and why it is the thing to check when confirming an account
is ours.

Account created 2026-08-03 under the placeholder `mteb-leaderboard.bsky.social`, pending
the DNS switch.

`mteb.bsky.social` is taken by an unrelated dormant personal account (bio: "art guy",
12 posts, since 2023). Not an impersonation, so there is nothing to report and no reason
to contact them. It does not matter: the `.bsky.social` handle is only a placeholder
during signup and is released once the domain handle is set.

**Display name:** `MTEB`

**Bio** (Bluesky allows 256 characters):

```
News from the Massive Text Embedding Benchmark: new features, models, results, datasets and benchmarks.

Every number is recomputed from public results — check them yourself at leaderboard.mteb.org.

We don't reply here. Issues and PRs on GitHub.
```

**Link:** `https://leaderboard.mteb.org`

## Account art

Both live in `brand/`, built by the same renderer as the post cards so the account and
the feed share one palette:

```
uv run mteb-render --card brand/avatar-light.html    --out brand/avatar-light.png    --size avatar
uv run mteb-render --card brand/banner.html          --out brand/banner.png          --size banner
uv run mteb-render --card brand/banner-wordmark.html --out brand/banner-wordmark.png --size banner
```

**Avatar** (1000×1000) — the MTEB mark, measured off `assets/avatar.png` rather than
redrawn, so it is the same mark and not an imitation. Scaled to 0.885 about the centre
because **clients mask avatars to a circle**: at full size the outermost dots reached
531px against a 500px radius, so the corner dots were being clipped. They now reach 469px.

**Banner** (1500×500) — every model scored on MTEB(Multilingual, v2), placed by size and
score, with the Pareto frontier stepped through it.

Three things make it read as MTEB rather than as a generic chart:

- **The dots carry the mark's own gradient.** The logo is blue dots shading deep blue to
  light; the plot uses that same ramp across its width, so the banner speaks the mark's
  visual language instead of sitting next to it.
- **The frontier is drawn as a staircase**, because that is what the data does. A smoothed
  curve would invent models between the real ones, and the flat runs — a size where
  nothing better exists yet — are the interesting part.
- **The band is shallow**, 208px of the 500px frame. A full-height scatter reads as a
  figure someone forgot to label; a stripe reads as texture with direction.

The frontier line is shape, not a claim. It says *smaller models keep catching up*, which
is the standing fact about this field rather than a result that expires.

Two variants:

- `banner.html` — **plain, and the one to use on Bluesky.** The client already prints the
  display name and handle under the avatar, so a wordmark up here says the same thing
  twice. A logo on a white field is also the *anonymous* part; the plot is the thing no
  other account could put there.
- `banner-wordmark.html` — the same image with the mark bottom-right, for anywhere the
  banner appears without profile chrome around it (a slide, a README header, LinkedIn).
  Bottom-right because that corner is empty as a property of the data — no large model
  scores low — and is diagonally clear of the avatar.

Off-frontier models are 2.5px at 42% — they are the field the frontier is measured
against, so they recede. Frontier models are 4.5px and fully opaque.

**The rule that shapes the banner: no numbers, no names, no axes.** A banner is set once
and then never looked at again, while every score on it keeps ageing — a leaderboard
snapshot would be quietly wrong within weeks, on the one surface nobody re-checks. So the
data is used as texture: real, but asserting nothing that could need retracting. It can be
re-fetched at any time and nothing downstream depends on which models are in it.

The cloud rises left to right because small models score low and large ones score high,
which leaves the top-left empty as a property of the data — the wordmark sits in space the
plot was never going to occupy, so no backdrop is needed behind it.

Three things that line does, in order of importance to someone deciding:

1. **What lands in the feed** — the concrete list, so the value is obvious without
   scrolling.
2. **That the numbers are checkable, and where.** This is the part worth spending
   characters on. Anyone can claim accuracy; pointing at the leaderboard invites the
   check, which is a different and stronger thing.
3. **That it does not converse** — stated plainly so silence reads as policy rather than
   as being ignored, and so nobody wastes a question here.

## What deliberately is not in the bio

- **"Drafted by an agent."** Currently the drafting is human-led with tooling, so the
  claim would overstate what happens. Revisit if that changes — it should be disclosed
  rather than discovered.
- **Cadence promises.** "Daily" or "weekly" is a commitment that will be broken in a
  quiet week and is not what anyone is deciding on.
- **Hashtags, emoji, follow-for-follow.** The account informs; it does not farm.

## The `bot` self-label — tied to the automation tier

Bluesky recommends automated accounts self-label as `bot` so users and moderation tools
can recognise them. Whether that applies here depends on the tier, not on whether an API
is involved:

| tier | posts automatically? | `bot` label |
|---|---|---|
| Handheld | no — a person publishes each post | no |
| **Supervised** (now) | yes, on a timer, after per-post human approval | **yes** — applied 2026-08-03 |
| Autonomous | yes, and chooses what to say | yes, and prominently |

**The label is on.** It went up in the same change that added
`.github/workflows/publish.yml`, because the failure that matters is publishing on a
schedule while presenting as a person typing — worse for a benchmark's account than for
almost anyone else's.

It is worth being precise about what it does and does not claim here. The label tells a
reader the account publishes automatically. It does not mean nobody is accountable: every
post is written, checked and approved by a named person before it enters the queue, and
the workflow only decides *when*. Some clients let users mute `bot`-labelled accounts, so
this costs some reach — accepted, because being quietly wrong about it would cost more.

The label is a self-label on our own `app.bsky.actor.profile` record, so it is ours to
remove if the tier ever moves back.

Two of Bluesky's bot norms already hold regardless: interactions must be opt-in (we never
reply at all — `AGENTS.md`, "This account publishes; it does not converse"), and rate limits must be respected (at most one post
a day, far below any limit).

## LinkedIn

Same identity and voice. The bio can be longer, but it must say the same things — the
failure mode is two formats drifting into two personalities.

Per-post LinkedIn text lives in that post's `post.md` under a ` ```linkedin ` block, not in
a separate file. See `CONTRIBUTING.md`.
