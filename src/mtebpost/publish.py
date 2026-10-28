#!/usr/bin/env python3
"""Show, and optionally send, a scheduled post.

    uv run mteb-publish                       # show anything due today
    uv run mteb-publish --date 2026-08-03     # a specific day
    uv run mteb-publish --all                 # the whole queue
    uv run mteb-publish --send                # actually post it to Bluesky

Without --send this only prints, and needs no credentials.

WHY A SCRIPT AND NOT A BROWSER. The text and the alt come straight out of post.md, so
what is published is byte-for-byte what was reviewed — there is no retyping step for a
number to change in. It is also the same path a scheduler would use, so a manual run
today exercises tomorrow's automation instead of being a throwaway.

CREDENTIALS. --send reads BLUESKY_APP_PASSWORD from the environment and nothing else.
Use a Bluesky *app password* (Settings -> Privacy and Security -> App Passwords), never
the account password: app passwords are revocable and cannot change account settings or
delete the account. It is never written to disk or logged by this script.

WHAT --send REFUSES TO DO. It will not post something that is not in 4-scheduled, not
approved by a named human, or not dated today. Those are the pipeline's guarantees, and
a publish path that can bypass them is a publish path that eventually does.

DISCLOSURE. Running this by hand keeps the account at the Handheld tier: a person still
decides that a post goes out now. Automating the *trigger* — cron, a scheduler — is the
change that needs the `bot` self-label reconsidered, and profile.md holds that reasoning.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import struct
import sys
import urllib.error
import urllib.request

BLUESKY_LIMIT = 300
ALT_IN_CARD = re.compile(
    r'<script type="text/plain" id="alt-text">\n(.*?)\n</script>', re.S
)


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if line.startswith((" ", "-")) or ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def card_for(post_dir: pathlib.Path, index: int) -> pathlib.Path | None:
    """Match the Nth post part to its card, if it has one.

    Cards are always numbered — card-1-*.png, card-2-*.png, etc. — even for a single-part
    post, so a post's own card and a stray leftover from an edit can never collide under
    the same bare name. The numbering is the contract for whichever parts do carry an
    image — a mismatch there attaches the wrong picture to the right words, which is
    worse than attaching none. Not every part needs a card, though: returning None here
    for index i just means part i is text-only, same as `media: none` for a whole post.
    """
    matches = sorted(post_dir.glob(f"card-{index}-*.png"))
    return matches[0] if matches else None


def show(post: pathlib.Path) -> int:
    text = post.read_text()
    fm = frontmatter(text)
    d = post.parent
    problems = 0

    print("=" * 78)
    print(f"  {fm.get('scheduled_for', '?')}   {d.name}")
    print(f"  approved by: {fm.get('approved_by', '— NOT APPROVED —')}")
    print("=" * 78)

    parts = re.findall(r"```\n(.*?)\n```", text, re.S)
    for i, body in enumerate(parts, 1):
        label = f"POST {i} of {len(parts)}" if len(parts) > 1 else "POST"
        n = len(body)
        flag = "" if n <= BLUESKY_LIMIT else f"  *** {n - BLUESKY_LIMIT} OVER LIMIT ***"
        if n > BLUESKY_LIMIT:
            problems += 1
        print(f"\n--- {label}   [{n}/{BLUESKY_LIMIT} chars]{flag} ---\n")
        print(body)

        card = card_for(d, i)
        if card:
            print(f"\n  attach: {card}")
            alt = ALT_IN_CARD.search(card.with_suffix(".html").read_text()) \
                if card.with_suffix(".html").exists() else None
            if alt:
                print(f"  alt text ({len(alt.group(1))} chars) — paste into Bluesky's ALT field:\n")
                for line in _wrap(alt.group(1), 74):
                    print(f"    {line}")
            else:
                print("  !! no alt text found in the card — run mteb-render")
                problems += 1
        elif len(parts) == 1 and fm.get("media", "none") != "none":
            print("\n  !! expected a card for this part and found none")
            problems += 1
        else:
            print("\n  (no image — deliberate for this post)")

    li = re.findall(r"```linkedin\n(.*?)\n```", text, re.S)
    if li:
        print(f"\n--- LINKEDIN   [{len(li[0].split())} words] ---\n")
        print(li[0])

    print(f"\n{'-' * 78}")
    print("After posting: move the folder to posts/5-posted/ and add posted_on: and url:")
    return problems


PDS = "https://bsky.social"
APPVIEW = "https://public.api.bsky.app"

def parse_when(s: str) -> dt.datetime | None:
    """Parse `scheduled_for` into an aware datetime, or None if it is unusable.

    Returned in the offset it was written in, not converted to UTC: lateness is judged
    against the local calendar day the post was scheduled for, so that frame has to
    survive parsing.

    A timezone is required, not optional. "2026-08-05T09:00" means different instants in
    Copenhagen and on a GitHub runner (which is UTC), and the difference is exactly the
    two hours in which someone notices the post went out at the wrong time.
    """
    try:
        d = dt.datetime.fromisoformat(s.strip())
    except ValueError:
        return None
    return None if d.tzinfo is None else d


def too_late(when: dt.datetime, now: dt.datetime) -> bool:
    """Has the post missed its day?

    The window is the rest of the scheduled local day, not a fixed number of hours. A run
    delayed by GitHub — cron is best-effort and skips under load — should still publish:
    a post meant for 09:00 that goes out at 11:00 is on time in every sense a reader
    cares about. What must not happen is a queue that has been stuck for days flushing
    itself, because those posts are answers to a question nobody is still asking.

    Judged in the post's own timezone, since that is the day it was written for.
    """
    return now.astimezone(when.tzinfo).date() != when.date()

# Checked in this order. The env var suits an interactive run; the file suits anything
# non-interactive (a scheduler, another shell) where an export does not survive. It is
# gitignored, and the mode check below is not decoration: a world-readable credential in
# a repo directory is the kind of mistake that is invisible until it is not.
PW_ENV = "BLUESKY_APP_PASSWORD"
PW_FILE = pathlib.Path(".bluesky-app-password")


def _app_password() -> str:
    pw = os.environ.get(PW_ENV)
    if pw:
        return pw.strip()
    if PW_FILE.exists():
        if PW_FILE.stat().st_mode & 0o077:
            sys.exit(f"{PW_FILE} is readable by others — chmod 600 {PW_FILE}")
        return PW_FILE.read_text().strip()
    sys.exit(
        f"No app password found. Either export {PW_ENV}, or:\n"
        f"    printf %s 'xxxx-xxxx-xxxx-xxxx' > {PW_FILE} && chmod 600 {PW_FILE}\n"
        "Use a Bluesky app password (Settings -> Privacy and Security -> App Passwords), "
        "never the account password."
    )


def _api(path: str, body, token: str | None = None, ctype: str = "application/json"):
    data = body if isinstance(body, bytes) else json.dumps(body).encode()
    req = urllib.request.Request(f"{PDS}/xrpc/{path}", data=data, method="POST")
    req.add_header("Content-Type", ctype)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"{path} failed: {e.code} {detail}")


def _already_posted(handle: str, text: str) -> bool:
    """Is this exact text already on the account's timeline?

    Compares the first post of the thread, which is enough: a partially-sent thread is
    caught too, and refusing is the right answer there as well — the repair is a person
    looking at what landed, not a second attempt.
    """
    url = (f"{APPVIEW}/xrpc/app.bsky.feed.getAuthorFeed"
           f"?actor={handle}&limit=50&filter=posts_no_replies")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            feed = json.loads(r.read()).get("feed", [])
    except urllib.error.URLError:
        # Fail closed: if the timeline cannot be read, we cannot rule out a duplicate.
        sys.exit("could not read the account timeline to check for a duplicate")
    return any(item["post"]["record"].get("text") == text for item in feed)


def png_size(p: pathlib.Path) -> tuple[int, int]:
    """Width and height from the IHDR chunk.

    Bluesky uses the declared aspect ratio to lay the image out before it loads; getting
    it wrong makes the post reflow when the picture arrives.
    """
    w, h = struct.unpack(">II", p.read_bytes()[16:24])
    return w, h


def send(post: pathlib.Path, handle: str) -> None:
    text = post.read_text()
    fm = frontmatter(text)
    d = post.parent

    # Guardrails. Every one of these corresponds to a promise the pipeline makes, and a
    # send path that can skip them is how the promise quietly stops holding.
    if d.parent.name != "4-scheduled":
        sys.exit(f"{d.name} is in {d.parent.name}, not 4-scheduled")
    who = fm.get("approved_by", "")
    if not who or who.lower() in ("agent", "none", "auto", "self"):
        sys.exit(f"{d.name} has no named human approver — see AGENTS.md rule 13")

    when = parse_when(fm.get("scheduled_for", ""))
    if when is None:
        sys.exit(f"{d.name}: unparseable or naive scheduled_for "
                 f"{fm.get('scheduled_for')!r} — needs a timezone offset")
    now = dt.datetime.now(dt.UTC)
    if when > now:
        sys.exit(f"{d.name} is not due until {when.isoformat()}")
    if too_late(when, now):
        sys.exit(f"{d.name} was due {when.date()} and it is now "
                 f"{now.astimezone(when.tzinfo).date()}. Re-date it deliberately or "
                 "reject it — news that missed its day should not go out as though it "
                 "had not.")

    pw = _app_password()

    parts = re.findall(r"```\n(.*?)\n```", text, re.S)
    if not parts:
        sys.exit(f"{d.name} has no post text (expected a fenced block)")
    over = [i for i, b in enumerate(parts, 1) if len(b) > BLUESKY_LIMIT]
    if over:
        sys.exit(f"post block(s) {over} exceed {BLUESKY_LIMIT} characters")

    ses = _api("com.atproto.server.createSession",
               {"identifier": handle, "password": pw})
    token, did = ses["accessJwt"], ses["did"]
    if ses.get("handle") != handle:
        sys.exit(f"logged in as {ses.get('handle')}, expected {handle}")
    print(f"authenticated as {ses['handle']} ({did})\n")

    # Posting and recording the post are two steps and CI is not transactional: a run
    # that publishes and then fails to commit the move would leave the post in
    # 4-scheduled, and the next hourly run would publish it again. Ask the timeline what
    # is already there instead of trusting local state to be accurate.
    if _already_posted(handle, parts[0]):
        sys.exit(f"{d.name} appears to be on the timeline already — refusing to repost. "
                 "If that is wrong, move the folder to 5-posted by hand.")

    root = parent = None
    for i, body in enumerate(parts, 1):
        record = {
            "$type": "app.bsky.feed.post",
            "text": body,
            "createdAt": dt.datetime.now(dt.UTC)
                           .isoformat(timespec="seconds").replace("+00:00", "Z"),
            "langs": ["en"],
        }

        card = card_for(d, i)
        if card:
            alt_m = ALT_IN_CARD.search(card.with_suffix(".html").read_text())
            if not alt_m:
                sys.exit(f"{card.name} has no alt text — run mteb-render")
            blob = _api("com.atproto.repo.uploadBlob", card.read_bytes(),
                        token, "image/png")["blob"]
            w, h = png_size(card)
            record["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{"alt": alt_m.group(1), "image": blob,
                            "aspectRatio": {"width": w, "height": h}}],
            }

        # A thread is a reply chain: every part after the first points at the first as
        # root and at its immediate predecessor as parent.
        if parent:
            record["reply"] = {"root": root, "parent": parent}

        res = _api("com.atproto.repo.createRecord",
                   {"repo": did, "collection": "app.bsky.feed.post", "record": record},
                   token)
        ref = {"uri": res["uri"], "cid": res["cid"]}
        root = root or ref
        parent = ref
        print(f"posted {i}/{len(parts)}  https://bsky.app/profile/{handle}/post/"
              f"{res['uri'].rsplit('/', 1)[1]}")

    url = f"https://bsky.app/profile/{handle}/post/{root['uri'].rsplit('/', 1)[1]}"
    _record_posted(post, url)
    print(f"\nthread: {url}")


def local_day(when: dt.datetime | None, now: dt.datetime | None = None) -> dt.date:
    """The date a post went out, in the post's own timezone.

    A 23:30 post at UTC-3 goes out on the 26th where its audience is; stamping `posted_on`
    from the runner's UTC clock files it under the 27th, and the archive then disagrees
    with the folder name it sits in.
    """
    now = now or dt.datetime.now(dt.UTC)
    return now.astimezone(when.tzinfo).date() if when else now.date()


def _record_posted(post: pathlib.Path, url: str) -> None:
    """Move the folder to 5-posted and stamp it.

    Done here rather than by hand because the pipeline's state lives in the directory
    layout: a post that went out but still sits in 4-scheduled will be offered again.
    """
    text = post.read_text()
    today = local_day(parse_when(frontmatter(text).get("scheduled_for", ""))).isoformat()
    end = text.find("\n---", 3)
    text = text[:end] + f"\nposted_on: {today}\nurl: {url}" + text[end:]
    post.write_text(text)

    dest = post.parent.parent.parent / "5-posted" / post.parent.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    post.parent.rename(dest)
    print(f"moved -> {dest}")


def _wrap(s: str, width: int) -> list[str]:
    out, line = [], ""
    for word in s.split():
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", default="posts", type=pathlib.Path)
    ap.add_argument("--date", help="ISO date; defaults to today")
    ap.add_argument("--all", action="store_true", help="show the whole scheduled queue")
    ap.add_argument("--due", action="store_true",
                    help="select the one post whose scheduled time has passed")
    ap.add_argument("--send", action="store_true",
                    help="actually post to Bluesky (needs BLUESKY_APP_PASSWORD)")
    ap.add_argument("--handle", default="mteb.org")
    args = ap.parse_args()

    scheduled = sorted((args.posts / "4-scheduled").glob("*/post.md"))
    if not scheduled:
        sys.exit("nothing scheduled")

    if args.all:
        due = scheduled
    elif args.due:
        # Everything whose moment has arrived, earliest first — then at most one, because
        # the cadence ceiling is one post a day (AGENTS.md rule 4) and a backlog must
        # drain one at a time rather than arrive as a burst.
        now = dt.datetime.now(dt.UTC)
        ready = sorted(
            ((parse_when(frontmatter(p.read_text()).get("scheduled_for", "")), p)
             for p in scheduled),
            key=lambda t: (t[0] is None, t[0]),
        )
        due = [p for when, p in ready if when is not None and when <= now][:1]
        if not due:
            nxt = next((w for w, _ in ready if w is not None and w > now), None)
            print(f"nothing due. Next: {nxt.isoformat() if nxt else 'nothing scheduled'}")
            return
    else:
        want = args.date or dt.date.today().isoformat()
        due = [p for p in scheduled if p.parent.name.startswith(want)]
        if not due:
            print(f"nothing scheduled for {want}. The queue:")
            for p in scheduled:
                print(f"  {p.parent.name}")
            return

    problems = sum(show(p) for p in due)
    if problems:
        sys.exit(f"\n{problems} problem(s) — fix before posting")

    if args.send:
        if len(due) != 1:
            sys.exit("--send takes exactly one post; narrow it with --date")
        print()
        send(due[0], args.handle)


if __name__ == "__main__":
    main()
