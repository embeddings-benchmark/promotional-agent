#!/usr/bin/env python3
"""Stage 1 of the pipeline: find things that *might* be worth posting.

    uv run mteb-scan --since 2026-07-20
    uv run mteb-scan --since 2026-07-20 --write     # create candidate folders

Reads merged PRs from the mteb and results repos via `gh`, classifies them by title
convention, and pairs each model addition with its results PR. Output is a list of
candidates — *not* drafts. A candidate is a claim that something happened and a guess at
why it might matter; deciding whether it is postable is the next stage's job.

Two things this deliberately does not do:

* **It does not judge.** Everything merged in the window shows up, including the bug
  fixes and refactors that will obviously be rejected. Filtering here would hide the
  denominator — you could no longer see what the pipeline chose not to say.
* **It does not trust labels.** Roughly half the genuine model additions carry no label
  at all, and `jina-reranker-v3.5` carried `new model` while being pure plumbing.
  Classification keys off the title conventions the repos actually use
  (`model:`, `task:`, `[MOEB]`, `fix:`, `ci:`), which are far more consistent.

The pairing heuristic is crude: it looks for distinctive words from the model PR title
appearing inside the results PR title. It will miss pairs and occasionally invent one,
which is why every candidate records both PR numbers for a human to check rather than
asserting the pairing as fact.

Running it twice is safe: anything whose trigger PR already appears in the pipeline is
skipped. Dropping a candidate deletes its folder, so a dropped PR *can* be proposed again
if it falls inside a later scan window — the window is about eight days, so that is one
extra proposal rather than a standing loop, and the second look is cheap.
"""

import argparse
import calendar
import dataclasses
import json
import pathlib
import re
import subprocess
import sys
from datetime import date


@dataclasses.dataclass
class Candidate:
    pr: dict
    results_pr: dict | None
    type: str
    hypothesis: str
    # Which PR is the *event*. Usually the mteb one, but when results land for a model
    # registered in an earlier window the results PR is the trigger and the mteb PR is
    # not in this scan's range at all.
    trigger: str = ""
    sources: tuple[str, ...] = ()


MTEB = "embeddings-benchmark/mteb"
RESULTS = "embeddings-benchmark/results"

# Ordered: first match wins, so the "not news" patterns must come before the broad ones.
KINDS = [
    ("skip",             r"^(ci|chore|build|docs|test|refactor|style)[:(]|^bump |dependabot"),
    ("fix",              r"^fix[:(]|^hotfix|fix:|^revert"),
    ("dataset",          r"^\[moeb\]|^task:|add .*(dataset|task)\b"),
    ("benchmark",        r"benchmark|^\[.*\] add .*bench"),
    ("model",            r"^model:|add .*model|modelmeta|register .*model"),
]


def gh_json(args: list[str]) -> list[dict]:
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"gh failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


def merged_prs(repo: str, since: str) -> list[dict]:
    return gh_json([
        "pr", "list", "--repo", repo, "--state", "merged",
        "--search", f"merged:>={since}", "--limit", "200",
        "--json", "number,title,mergedAt,author,url",
    ])


def classify(title: str) -> str:
    low = title.lower()
    for kind, pattern in KINDS:
        if re.search(pattern, low):
            return kind
    return "other"


# Words that appear in almost every PR title on both sides and so carry no signal.
STOP = {
    "add", "adds", "added", "model", "models", "modelmeta", "meta", "metadata",
    "embedding", "embeddings", "results", "result", "evaluation", "mteb", "eval",
    "definitions", "definition", "implementation", "with", "and", "the", "for",
    "new", "update", "updates", "expand", "register", "support", "from",
}


def tokens(title: str) -> set[str]:
    """Distinctive words in a title — long enough to identify a model, minus boilerplate."""
    return {
        w for w in (
            x.strip(".,()[]:").lower() for x in re.split(r"[\s/]+", title)
        )
        if len(w) >= 4 and w not in STOP
    }


def pair_results(model_pr: dict, result_prs: list[dict]) -> dict | None:
    """Match on substrings, not equal tokens.

    A model PR says "Add Bekko embedding models" while its results PR says
    "MTEB Evaluation Results: hotchpotch/bekko-embedding-v1-a8m". The shared identity is
    "bekko" *inside* a longer token, so equality never fires — which is exactly how an
    earlier version reported Bekko as having no results at all.
    """
    mt = tokens(model_pr["title"])
    if not mt:
        return None
    best, best_score = None, 0
    for r in result_prs:
        low = r["title"].lower()
        score = sum(len(w) for w in mt if w in low)
        if score > best_score:
            best, best_score = r, score
    # one short accidental overlap is not a pairing
    return best if best_score >= 5 else None


def slug(title: str) -> str:
    s = re.sub(r"^\[?\w+\]?:?\s*", "", title.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return "-".join(s.split("-")[:5]) or "candidate"


def expiry(merged: str, months: int = 1) -> str:
    """The candidate's shelf life: `months` after the trigger date, clamped to month end.

    News older than about a month is not news (CONTRIBUTING.md, "3 -> 4: scheduling"),
    so every candidate carries an `expires:` date. A bare `date.replace(month=...)`
    cannot express that: rolling 31 January forward asks for 31 February and raises
    ValueError, and rolling December forward keeps the year it started in. Both would
    crash a scan — one of the few things in this pipeline that fails silently, because
    the crash lands in a scheduled workflow nobody is watching.
    """
    d = date.fromisoformat(merged)
    years, month = divmod(d.month - 1 + months, 12)
    year = d.year + years
    day = min(d.day, calendar.monthrange(year, month + 1)[1])
    return date(year, month + 1, day).isoformat()


STUB = """---
id: {id}
type: {type}
trigger: {trigger}
trigger_date: {date}
expires: {expires}
sources:
{sources}
---

## Why this might be a post

{hypothesis}

## Before it can move to 2-drafting

- [ ] confirm the pairing above is real (the scanner guesses it from title overlap)
- [ ] check the results are merged and complete, not partial
- [ ] decide the angle, or reject with a reason
"""


# Two spellings of the same fact. `trigger:` writes a PR as `mteb#5043`; `sources:`
# writes it as a URL, the way it was copied out of GitHub. Reading only the first form
# means a PR that appears only in `sources:` is not tracked, and its results half gets
# proposed a second time.
PR_REF = re.compile(
    r"\b(mteb|results)#(\d+)\b"
    r"|github\.com/embeddings-benchmark/(mteb|results)/(?:pull|issues)/(\d+)"
)


def already_tracked(posts: pathlib.Path) -> set[str]:
    """PR references (`mteb#5043`) that already exist anywhere in the pipeline.

    Without this the scanner re-proposes everything already in the pipeline every morning,
    including candidates that are being drafted or are already scheduled.
    """
    seen = set()
    for post in posts.rglob("post.md"):
        for m in PR_REF.finditer(post.read_text()):
            repo = m.group(1) or m.group(3)
            number = m.group(2) or m.group(4)
            seen.add(f"{repo}#{number}")
    return seen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="ISO date, e.g. 2026-07-20")
    ap.add_argument("--posts", default="posts", type=pathlib.Path,
                    help="pipeline root (default: ./posts)")
    ap.add_argument("--write", action="store_true", help="create folders in 1-candidates/")
    args = ap.parse_args()

    mteb_prs = merged_prs(MTEB, args.since)
    result_prs = merged_prs(RESULTS, args.since)

    buckets: dict[str, list[dict]] = {}
    for pr in mteb_prs:
        buckets.setdefault(classify(pr["title"]), []).append(pr)

    print(f"merged since {args.since}: {len(mteb_prs)} in mteb, {len(result_prs)} in results\n")
    for kind in ("model", "dataset", "benchmark", "fix", "skip", "other"):
        rows = buckets.get(kind, [])
        note = "  <- candidates" if kind in ("model", "dataset", "benchmark") else ""
        print(f"{kind:<10} {len(rows):>3}{note}")

    tracked = already_tracked(args.posts)
    skipped = 0

    candidates: list[Candidate] = []
    paired: set[int] = set()
    plumbing = 0
    for pr in buckets.get("model", []):
        if f"mteb#{pr['number']}" in tracked:
            skipped += 1
            continue
        res = pair_results(pr, result_prs)
        if res is None:
            # A registration with no scores is plumbing, and a folder for it is a claim
            # that something might be a story when nothing can be said yet. It still gets
            # printed below, so the denominator stays visible — it just does not get a
            # folder. When its results land, the branch further down picks it up.
            plumbing += 1
            continue
        paired.add(res["number"])
        candidates.append(Candidate(
            pr=pr, results_pr=res, type="model_addition",
            trigger=f"mteb#{pr['number']} + results#{res['number']}",
            sources=(pr["url"], res["url"]),
            hypothesis=(
                "Model addition with a matching results PR — the most reliable trigger "
                "there is. Worth a post if the scores say something a reader could not "
                "guess from the model card."
            ),
        ))

    # Results landing for a model registered in an earlier window. This is the moment a
    # registration becomes postable, and without it that moment is invisible: candidates
    # were only ever built from mteb PRs *in the window*, so a model registered in July
    # whose scores merged in August never surfaced again. Nothing re-proposed it, because
    # nothing was watching the side the event happened on.
    for r in result_prs:
        if r["number"] in paired or f"results#{r['number']}" in tracked:
            continue
        # The results repo carries its own CI and housekeeping. A submission names what it
        # submitted — results, scores, or a benchmark; "Fix comment step" does not.
        if classify(r["title"]) in ("skip", "fix") or not re.search(
                r"result|score|[MRA]TEB|MIEB|MAEB|MVEB|ViDoRe|BEIR", r["title"], re.I):
            continue
        candidates.append(Candidate(
            pr=r, results_pr=r, type="results_addition",
            trigger=f"results#{r['number']}",
            sources=(r["url"],),
            hypothesis=(
                "Results merged for a model registered earlier — the registration is not "
                "in this window, so this is the first moment the model can be written "
                "about. Check what the scores actually say before drafting."
            ),
        ))
    for pr in buckets.get("benchmark", []):
        if f"mteb#{pr['number']}" in tracked:
            skipped += 1
            continue
        candidates.append(Candidate(
            pr=pr, results_pr=None, type="benchmark_addition",
            trigger=f"mteb#{pr['number']}", sources=(pr["url"],),
            hypothesis="New benchmark. Always worth announcing."))

    print(f"\n{len(candidates)} new candidates ({skipped} already in the pipeline)")
    print(f"  ({plumbing} registration(s) with no merged results — listed above, "
          f"no folder written; they return when their results merge)")
    for c in candidates:
        print(f"  {c.pr['mergedAt'][:10]}  {c.trigger:<28}  {c.pr['title'][:60]}")

    if not args.write:
        print("\n(dry run — pass --write to create candidate folders)")
        return

    out = args.posts / "1-candidates"
    out.mkdir(exist_ok=True)
    for c in candidates:
        pr, res = c.pr, c.results_pr
        merged = pr["mergedAt"][:10]
        # No date in the folder name: a date only means something once the post is
        # scheduled, and until then it reads as a promise the pipeline has not made.
        # `trigger_date` in the frontmatter keeps the "when did this happen" fact.
        name = slug(pr["title"])
        d = out / name
        # Slugs are derived from PR titles and collide: two different PRs titled "Add
        # Bekko embedding models" produce one name, and `already_tracked` has already
        # removed the ones that really are duplicates. So a name that is taken belongs
        # to a different candidate, and skipping it — which is what returning here used
        # to do — loses the story without saying so.
        n = 2
        while d.exists():
            name = f"{slug(pr['title'])}-{n}"
            d = out / name
            n += 1
        d.mkdir()
        srcs = [f"  - {u}" for u in c.sources]
        (d / "post.md").write_text(STUB.format(
            id=name, type=c.type, date=merged, expires=expiry(merged),
            trigger=c.trigger,
            sources="\n".join(srcs), hypothesis=c.hypothesis,
        ))
        print(f"  wrote {d}")


if __name__ == "__main__":
    main()
