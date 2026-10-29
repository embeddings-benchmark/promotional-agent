"""Shared fixtures.

Posts are written to disk rather than mocked: every rule `mteb-validate` enforces is a
rule about a *folder* — its name, the files beside `post.md`, the date in the directory
— so a test that does not create the folder is not testing the rule.
"""

from __future__ import annotations

import pathlib

import pytest

CARD_HTML = """<!doctype html>
<html><body>
<script type="application/json" id="card-data">
{"benchmark": "MTEB(Multilingual, v2)", "n_tasks": 131}
</script>
<script type="text/plain" id="alt-text">
Bar chart. model-a scores 61.2, model-b 58.0.
</script>
</body></html>
"""

CARD_HTML_NO_ALT = """<!doctype html>
<html><body>
<script type="application/json" id="card-data">
{"benchmark": "MTEB(Multilingual, v2)", "n_tasks": 131}
</script>
</body></html>
"""


@pytest.fixture
def post(tmp_path: pathlib.Path):
    """Write a post folder and return its `post.md` path.

    Defaults are a *valid* `3-review` post so that each test varies exactly one thing
    and a failure names the rule that broke rather than a pile of missing fields.
    """

    def _make(
        stage: str = "3-review",
        name: str = "some-post",
        frontmatter: str | None = None,
        body: str = "A post about a model.\n",
        blocks: list[str] | None = None,
        card: bool = True,
        card_name: str = "card-1-some-post",
        png: bool = True,
        extra_files: dict[str, str] | None = None,
    ) -> pathlib.Path:
        d = tmp_path / "posts" / stage / name
        d.mkdir(parents=True, exist_ok=True)

        if frontmatter is None:
            frontmatter = (
                f"id: {name}\n"
                "type: model_addition\n"
                "trigger: mteb#1234 + results#5678\n"
                "trigger_date: 2026-08-01\n"
                "verified: true\n"
                f"media: {card_name}.png\n"
            )
            if stage in ("4-scheduled", "5-posted"):
                day = name[:10]
                frontmatter += (
                    f"scheduled_for: {day}T14:30:00+02:00\n"
                    "approved_by: kennethenevoldsen\n"
                )
            if stage == "5-posted":
                frontmatter += "posted_on: 2026-08-06\nurl: https://bsky.app/x\n"

        if blocks is None:
            blocks = ["A post about a model.\n"]
        text = f"---\n{frontmatter}---\n\n{body}\n"
        text += "\n".join(f"```\n{b}\n```\n" for b in blocks)
        (d / "post.md").write_text(text)

        if card:
            (d / f"{card_name}.html").write_text(CARD_HTML)
        if card and png:
            (d / f"{card_name}.png").write_bytes(b"\x89PNG" + b"\0" * 32)
        for fname, content in (extra_files or {}).items():
            (d / fname).write_text(content)
        return d / "post.md"

    return _make
