#!/usr/bin/env python3
"""Render a post's card HTML to PNG.

    uv run mteb-render --card posts/<id>/card-1-<slug>.html --out posts/<id>/card-1-<slug>.png
    uv run mteb-render --card posts/<id>/card-1-<slug>.html --mode dark --out /tmp/preview.png

The card is self-contained: `fetch.py` writes its numbers into the `#card-data` block,
and the copy lives in a `COPY` object beside it. So opening `card.html` in a browser
shows exactly what this produces — there is no separate data file that can drift from
the checked-in markup.

The only thing injected at render time is `mode`, merged into the existing card data
rather than replacing it, so dark and light come from one file.

Alt text is read back out of the rendered page (`window.__altText`) and written into the
card itself as `<script type="text/plain" id="alt-text">`. So it stays generated from the
same data that drew the image — it cannot disagree with the picture — while remaining
readable by anything that can parse HTML, with no browser required at publish time.

There is deliberately no `.txt` sidecar. A derived file next to a source file is a file
that drifts; the card already carries its own data and copy, and the alt text belongs
there for the same reason.

`--mode dark` is for previewing: only one image can be posted, so the light render is
the artifact and a dark PNG would just be a second copy of the same numbers.

Uses the locally installed Chrome via Playwright's `channel="chrome"`, so there is no
browser download. Chrome's `--screenshot` CLI flag is deliberately not used: it hangs
on macOS in both the old and new headless modes.
"""

import argparse
import json
import pathlib
import re
import sys
import tempfile

from playwright.sync_api import sync_playwright

CARD_W, CARD_H = 1200, 1200  # square: social feeds crop wide images, and a
                             # square (or taller) card keeps its full height in-feed
SCALE = 2  # retina; produces a 2400x2400 png

# Account art is not a card and does not share its geometry: a Bluesky banner is 3:1
# and is cropped and scaled by the client, so it gets its own size rather than a card
# squeezed into a letterbox. Everything else — the palette, the logo, the alt-text
# contract — is deliberately the same, because the brand should not fork by surface.
PRESETS = {"card": (1200, 1200), "banner": (1500, 500), "avatar": (1000, 1000)}

BLOCK = re.compile(
    r'(<script type="application/json" id="card-data">)(.*?)(</script>)', re.S
)


def build_page(card: pathlib.Path, mode: str) -> str:
    """Return the card's HTML with `mode` merged into its data block."""
    html = card.read_text()
    m = BLOCK.search(html)
    if not m:
        sys.exit(f"{card}: no #card-data block found")
    data = json.loads(m.group(2))
    blob = json.dumps({**data, "mode": mode}, indent=2, ensure_ascii=False)
    return html[: m.start(2)] + "\n" + blob + "\n" + html[m.end(2) :]


ALT_BLOCK = re.compile(
    r'<script type="text/plain" id="alt-text">.*?</script>\n?', re.S
)


def write_alt(card: pathlib.Path, alt: str) -> None:
    """Store the generated alt text in the card, replacing any previous copy.

    Kept as `type="text/plain"` so the browser neither executes nor renders it; it is
    inert payload that a publisher can lift out with a regex.
    """
    html = card.read_text()
    block = f'<script type="text/plain" id="alt-text">\n{alt}\n</script>\n'
    html = ALT_BLOCK.sub("", html)
    # sits directly after the card data, where anything generated lives
    marker = "</script>\n"
    i = html.index(marker) + len(marker)
    card.write_text(html[:i] + block + html[i:])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, help="path to the post's card.html")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=("light", "dark"), default="light")
    ap.add_argument("--size", choices=tuple(PRESETS), default="card")
    # Chrome is the default because a system Chrome renders the fonts a card is designed
    # around, and GitHub's runners ship it. A machine without Chrome — a fresh Linux box,
    # a container — can use Playwright's own chromium instead of failing outright:
    #     uv run playwright install chromium && uv run mteb-render --channel chromium ...
    ap.add_argument("--channel", default="chrome",
                    help="Playwright browser channel: chrome (default) or chromium")
    args = ap.parse_args()

    width, height = PRESETS[args.size]

    page_html = build_page(pathlib.Path(args.card), args.mode)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "card.html"
        src.write_text(page_html)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=args.channel)
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=SCALE,
            )
            page.goto(src.as_uri())
            page.wait_for_function("window.__altText !== undefined")
            page.screenshot(path=str(out))
            alt = page.evaluate("window.__altText")
            browser.close()

    write_alt(pathlib.Path(args.card), alt)
    print(f"{out}  ({out.stat().st_size // 1024} KB)")
    print(f"alt text -> {args.card} (#alt-text)")


if __name__ == "__main__":
    main()
