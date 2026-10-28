#!/usr/bin/env python3
"""Check posts against the rules a machine can check.

    uv run mteb-validate                    # whole pipeline
    uv run mteb-validate --stage 3-review   # one stage
    uv run mteb-validate --strict           # warnings become failures

This covers the mechanical rules only — 300 characters, required fields per stage, files
that must exist, dates that must be consistent. It cannot tell you whether a post is
worth publishing, whether a cohort is fair, or whether a claim is scoped correctly. Those
are in CONTRIBUTING.md and they need a person.

The split matters: a check that runs is worth more than a rule that is merely written
down, but a passing run says only that nothing obvious is broken.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

BLUESKY_LIMIT = 300

STAGES = ("1-candidates", "2-drafting", "3-review", "4-scheduled", "5-posted", "rejected")

# Fields each stage requires beyond the common set. A stage inherits nothing: what is
# listed here is what that stage must have, because the point is to catch a folder that
# was moved without the work that move implies.
REQUIRED = {
    "1-candidates": {"id", "type", "trigger", "trigger_date"},
    "2-drafting": {"id", "type", "trigger", "trigger_date"},
    "3-review": {"id", "type", "trigger", "trigger_date", "verified", "media"},
    "4-scheduled": {"id", "type", "trigger", "trigger_date", "verified", "media",
                    "scheduled_for", "approved_by"},
    "5-posted": {"id", "type", "trigger", "trigger_date", "verified", "media",
                 "scheduled_for", "posted_on", "approved_by"},
    "rejected": {"id", "type", "trigger", "trigger_date", "reason"},
}

# Stages that must have a rendered card. Which *files* those are comes from the
# frontmatter rather than a fixed list: a post has card-1-*.png, card-2-*.png, and so on
# — always numbered, even when it is not a thread — and hardcoding names would fail
# every post.
NEEDS_CARD = ("3-review", "4-scheduled", "5-posted")

DATED_STAGES = ("4-scheduled", "5-posted")
DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
ALT_IN_CARD = re.compile(r'id="alt-text"')

# card-1-<slug>.html / card-1-<slug>.png — never bare card.html / card.png. publish.py's
# card_for() only ever looks for the numbered form, so a bare name is invisible to it:
# `mteb-publish --due` would report "expected a card for this part and found none" even
# though the file is sitting right there.
CARD_NAME = re.compile(r"^card-(\d+)-[\w-]+\.(html|png)$")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if line.startswith((" ", "-")) or ":" not in line:
            continue  # nested list items belong to the key above
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def post_blocks(text: str) -> list[str]:
    """Fenced blocks are the text that actually gets posted."""
    return re.findall(r"```\n(.*?)\n```", text, re.S)


def check_post(path: pathlib.Path, stage: str, rep: Report) -> None:
    where = f"{stage}/{path.parent.name}"
    text = path.read_text()
    fm = frontmatter(text)

    missing = REQUIRED[stage] - set(fm)
    if missing:
        rep.error(where, f"missing frontmatter: {', '.join(sorted(missing))}")

    if fm.get("id") and fm["id"] != path.parent.name:
        rep.error(where, f"id '{fm['id']}' does not match folder name")

    # The date rule: it means "when this goes out", so it exists only once scheduled.
    m = DATE_PREFIX.match(path.parent.name)
    if stage in DATED_STAGES and not m:
        rep.error(where, "scheduled/posted folders must be named <date>-<slug>")
    if stage not in DATED_STAGES and m:
        rep.error(where, "only scheduled/posted folders carry a date in the name")

    # `scheduled_for` is an instant, not a day: a workflow runs in UTC and a person
    # thinks in local time, so a naive timestamp would publish at the wrong hour and the
    # mistake would only be visible after the fact. The folder keeps the date alone —
    # a time in a directory name is noise no one reads.
    when = None
    if fm.get("scheduled_for"):
        try:
            when = dt.datetime.fromisoformat(fm["scheduled_for"].strip())
        except ValueError:
            rep.error(where, f"unparseable scheduled_for: {fm['scheduled_for']!r} "
                             "(expected e.g. 2026-08-05T09:00:00+02:00)")
        else:
            if when.tzinfo is None:
                rep.error(where, f"scheduled_for {fm['scheduled_for']!r} has no timezone "
                                 "offset — it would mean a different instant on a runner")
            elif m and m.group(1) != when.date().isoformat():
                rep.error(where, f"folder date {m.group(1)} != "
                                 f"scheduled_for date {when.date().isoformat()}")
            # Not an error — an intentional 03:00 post is possible — but almost always a
            # timezone that was worked out wrongly rather than an audience that is awake.
            if when.tzinfo is not None and not (6 <= when.hour < 22):
                rep.warn(where, f"scheduled for {when.strftime('%H:%M')} local; check the "
                                "offset is right before letting it fire unattended")

    blocks = post_blocks(text)
    if stage in NEEDS_CARD and not blocks:
        rep.error(where, "no post text (expected a fenced block)")
    for i, b in enumerate(blocks, 1):
        if len(b) > BLUESKY_LIMIT:
            rep.error(where, f"post text block {i} is {len(b)} chars (limit {BLUESKY_LIMIT})")

    # "media: none" is a deliberate choice, not a missing file — the pinned meta post
    # has no measurement to show, and inventing a chart would undercut its own point.
    has_card = fm.get("media", "none") != "none"
    if stage in NEEDS_CARD and has_card:
        named = fm.get("media")
        if named and not (path.parent / named).exists():
            rep.error(where, f"media: {named} does not exist")
        if not list(path.parent.glob("card*.html")):
            rep.error(where, "no card markup (expected card-1-<slug>.html)")

    # A thread declares how many posts it is; check that many fenced blocks exist.
    n_parts = len(blocks) or 1
    if fm.get("thread") and fm["thread"] != "none":
        try:
            want = int(fm["thread"])
            if len(blocks) != want:
                rep.error(where, f"thread: {want} but {len(blocks)} post blocks found")
            n_parts = want
        except ValueError:
            rep.error(where, f"unparseable thread: {fm['thread']!r}")

    # Every card is numbered — card-1-<slug>.{html,png}, even for a single-part post —
    # so publish.py's card_for() can match it to its post by filename alone. A bare
    # card.html/card.png is the pre-thread convention and is no longer accepted: it is
    # invisible to card_for(), which silently treats the part as text-only instead of
    # erroring, so this is the only place the mistake gets caught.
    for card in sorted(path.parent.glob("card*.html")) + sorted(path.parent.glob("card*.png")):
        m = CARD_NAME.match(card.name)
        if not m:
            rep.error(where, f"{card.name} is not numbered — rename to "
                              f"card-1-<slug>{card.suffix} (or card-N-<slug>{card.suffix} "
                              "for post part N)")
        elif not (1 <= int(m.group(1)) <= n_parts):
            rep.error(where, f"{card.name} is numbered {m.group(1)} but this post has "
                              f"{n_parts} part(s)")

    # Alt text lives inside the card, written there by render.py from the same data that
    # drew the image. A card without it ships an image-only payload, which is unreadable
    # to screen readers and to anyone whose client fails to load it.
    for card in path.parent.glob("card*.html"):
        if not ALT_IN_CARD.search(card.read_text()):
            rep.error(where, f"{card.name} has no alt text — re-run mteb-render")
        if not card.with_suffix(".png").exists():
            rep.error(where, f"{card.name} has never been rendered")

    if fm.get("verified") == "false" and stage in ("3-review", "4-scheduled", "5-posted"):
        rep.error(where, "reached review with verified: false")

    if stage == "rejected" and not fm.get("reason"):
        rep.error(where, "rejection without a reason")

    # The whole pipeline rests on a human deciding what goes out. Until this field
    # exists, nothing distinguishes "someone approved it" from "a folder got moved".
    if stage in ("4-scheduled", "5-posted"):
        who = fm.get("approved_by", "")
        if not who or who.lower() in ("agent", "none", "auto", "self"):
            rep.error(where, "scheduled without a named human approver")

    # An expired post should be rejected rather than quietly shipped stale.
    exp = fm.get("expires")
    if exp and stage in ("3-review", "4-scheduled"):
        try:
            expires = dt.date.fromisoformat(exp)
        except ValueError:
            rep.error(where, f"unparseable expires: {exp!r}")
        else:
            # The scheduled-after-expiry check comes first because it is the stronger
            # finding: a post whose date has already passed AND is scheduled past its
            # expiry is about to go out stale, which is an error, not a nudge. Checking
            # "already expired" first would shadow it for every post in a queue that is
            # more than a few weeks old — exactly the queue this check is for.
            if when and expires < when.date():
                rep.error(where, f"scheduled for {when.date()} but expires {exp} — "
                                 "it would go out already stale")
            elif expires < dt.date.today():
                rep.warn(where, f"expired on {exp}; reject rather than post stale")

    # Publishing is unattended now, so a post whose day has passed must be caught here
    # rather than discovered when the workflow refuses it. The window is the rest of the
    # scheduled local day: a run delayed by GitHub still publishes, a queue stuck for
    # days does not.
    if stage == "4-scheduled" and when and when.tzinfo:
        now_local = dt.datetime.now(dt.UTC).astimezone(when.tzinfo)
        if now_local.date() > when.date():
            rep.warn(where, f"was due {when.date()} and will no longer publish; "
                            "re-date it or reject it")

    # The LinkedIn version lives in post.md under ```linkedin — one file per post, and
    # the bare-``` scan above deliberately does not pick it up, so the 300-character
    # limit is not applied to it.
    for i, b in enumerate(re.findall(r"```linkedin\n(.*?)\n```", text, re.S), 1):
        if not b.strip():
            rep.error(where, f"empty linkedin block {i}")

    for field in ("todo", "blocked_on"):
        if stage in ("3-review", "4-scheduled") and field in fm and fm[field] not in ("", "null"):
            rep.warn(where, f"still carries {field}: while in {stage}")


def check_schedule(posts: pathlib.Path, rep: Report) -> None:
    """One post a day, maximum — a queue that is long should spread, never batch."""
    seen: dict[str, list[str]] = {}
    for stage in ("4-scheduled", "5-posted"):
        for d in sorted((posts / stage).glob("*/")):
            m = DATE_PREFIX.match(d.name)
            if m:
                seen.setdefault(m.group(1), []).append(f"{stage}/{d.name}")
    for day, items in sorted(seen.items()):
        if len(items) > 1:
            rep.error("schedule", f"{day} has {len(items)} posts: {', '.join(items)}")


def queue_stats(posts: pathlib.Path) -> list[tuple[str, int, int]]:
    """(stage, total, expired) per stage — the pipeline at a glance.

    Expiry is counted rather than raised as a warning on purpose: an expired candidate is
    a decision someone has to make, and `mteb-validate` failing every week until an
    editorial backlog is cleared would train everyone to ignore it. Silence is worse,
    though — a third of the candidate queue once sat past its expiry with nothing anywhere
    saying so, and a queue nobody can see the shape of is a queue nobody triages.
    """
    today = dt.date.today()
    out = []
    for stage in STAGES:
        d = posts / stage
        if not d.is_dir():
            continue
        total = expired = 0
        for post in d.glob("*/post.md"):
            total += 1
            # Only the live end of the pipeline: an `expires:` date on a published post
            # or a rejection is a record of when it was current, not a task.
            if stage not in ("1-candidates", "2-drafting", "3-review", "4-scheduled"):
                continue
            exp = frontmatter(post.read_text()).get("expires")
            if not exp:
                continue
            try:
                if dt.date.fromisoformat(exp) < today:
                    expired += 1
            except ValueError:
                pass
        out.append((stage, total, expired))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", default="posts", type=pathlib.Path)
    ap.add_argument("--stage", help="check only this stage")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    rep = Report()
    stages = (args.stage,) if args.stage else STAGES
    n = 0
    for stage in stages:
        d = args.posts / stage
        if not d.is_dir():
            continue
        for post in sorted(d.glob("*/post.md")):
            check_post(post, stage, rep)
            n += 1
    if not args.stage:
        check_schedule(args.posts, rep)

    for w in rep.warnings:
        print(f"  warn   {w}")
    for e in rep.errors:
        print(f"  ERROR  {e}")

    if not args.stage:
        print()
        for stage, total, expired in queue_stats(args.posts):
            note = f"   ({expired} past expires)" if expired else ""
            print(f"  {stage:<14} {total:>3}{note}")

    bad = rep.errors or (rep.warnings and args.strict)
    print(f"\n{n} posts checked — {len(rep.errors)} errors, {len(rep.warnings)} warnings")
    if not bad:
        print("Mechanical checks pass. They say nothing about whether a post is worth "
              "publishing — see CONTRIBUTING.md.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
