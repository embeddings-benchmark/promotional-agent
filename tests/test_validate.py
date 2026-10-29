"""The mechanical rules, one test per rule.

`mteb-validate` exists because a written-down rule that nothing runs is a rule that has
already been broken. The same argument applies to the validator itself: these are the
checks the publisher and the CI rely on, and each one is stated in CONTRIBUTING.md or
AGENTS.md, so a regression here silently re-opens a hole the repo believes is closed.
"""

from __future__ import annotations

from mtebpost import validate


def rep() -> validate.Report:
    return validate.Report()


def test_valid_three_review_post_passes(post):
    r = rep()
    validate.check_post(post("3-review"), "3-review", r)
    assert r.errors == []


def test_missing_frontmatter_is_named(post):
    r = rep()
    p = post("3-review", frontmatter="id: some-post\ntype: model_addition\n")
    validate.check_post(p, "3-review", r)
    missing = " ".join(r.errors)
    assert "trigger" in missing and "verified" in missing and "media" in missing


def test_id_must_match_folder(post):
    r = rep()
    p = post("3-review", frontmatter=(
        "id: something-else\ntype: model_addition\ntrigger: mteb#1\n"
        "trigger_date: 2026-08-01\nverified: true\nmedia: none\n"
    ))
    validate.check_post(p, "3-review", r)
    assert any("does not match folder name" in e for e in r.errors)


def test_character_limit_is_exact(post):
    """299 passes, 301 fails — the boundary is the platform's, not ours."""
    for n, ok in ((299, True), (301, False)):
        r = rep()
        p = post("3-review", name=f"post-{n}", blocks=["x" * n])
        validate.check_post(p, "3-review", r)
        over = [e for e in r.errors if "chars" in e]
        assert bool(over) is not ok, (n, r.errors)


def test_dated_folder_only_once_scheduled(post):
    r = rep()
    p = post("3-review", name="2026-08-06-dinghy-law-family")
    validate.check_post(p, "3-review", r)
    assert any("only scheduled/posted folders carry a date" in e for e in r.errors)


def test_scheduled_requires_dated_folder(post):
    r = rep()
    p = post("4-scheduled", name="dinghy-law-family", frontmatter=(
        "id: dinghy-law-family\ntype: model_addition\ntrigger: mteb#1\n"
        "trigger_date: 2026-08-01\nverified: true\nmedia: none\n"
        "scheduled_for: 2026-08-06T14:30:00+02:00\napproved_by: kennethenevoldsen\n"
    ))
    validate.check_post(p, "4-scheduled", r)
    assert any("must be named <date>-<slug>" in e for e in r.errors)


def test_scheduled_for_needs_a_timezone(post):
    """A naive timestamp is a different instant on a UTC runner than where it was written."""
    r = rep()
    p = post("4-scheduled", name="2026-08-06-dinghy-law-family", frontmatter=(
        "id: 2026-08-06-dinghy-law-family\ntype: model_addition\ntrigger: mteb#1\n"
        "trigger_date: 2026-08-01\nverified: true\nmedia: none\n"
        "scheduled_for: 2026-08-06T09:00:00\napproved_by: kennethenevoldsen\n"
    ))
    validate.check_post(p, "4-scheduled", r)
    assert any("no timezone offset" in e for e in r.errors)


def test_folder_date_must_match_scheduled_for(post):
    r = rep()
    p = post("4-scheduled", name="2026-08-06-dinghy-law-family", frontmatter=(
        "id: 2026-08-06-dinghy-law-family\ntype: model_addition\ntrigger: mteb#1\n"
        "trigger_date: 2026-08-01\nverified: true\nmedia: none\n"
        "scheduled_for: 2026-08-07T14:30:00+02:00\napproved_by: kennethenevoldsen\n"
    ))
    validate.check_post(p, "4-scheduled", r)
    assert any("!= scheduled_for date" in e for e in r.errors)


def test_no_approver_names_reject_the_agent(post):
    """The one field that distinguishes "a person approved" from "a folder got moved"."""
    for who in ("", "agent", "auto", "self"):
        r = rep()
        name = "2026-08-06-dinghy-law-family"
        p = post("4-scheduled", name=name, frontmatter=(
            f"id: {name}\ntype: model_addition\ntrigger: mteb#1\n"
            "trigger_date: 2026-08-01\nverified: true\nmedia: none\n"
            f"scheduled_for: 2026-08-06T14:30:00+02:00\napproved_by: {who}\n"
        ))
        validate.check_post(p, "4-scheduled", r)
        assert any("named human approver" in e for e in r.errors), who


def test_thread_count_must_match_blocks(post):
    r = rep()
    p = post("3-review", frontmatter=(
        "id: some-post\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-08-01\n"
        "verified: true\nmedia: none\nthread: 2\n"
    ))
    validate.check_post(p, "3-review", r)
    assert any("thread: 2 but 1 post blocks" in e for e in r.errors)


def test_bare_card_name_is_rejected(post):
    """publish.py only matches card-N-*, so a bare card.html is invisible to it."""
    r = rep()
    p = post("3-review", card_name="card")
    validate.check_post(p, "3-review", r)
    assert any("is not numbered" in e for e in r.errors)


def test_card_number_beyond_part_count_is_rejected(post):
    r = rep()
    p = post("3-review", extra_files={"card-2-second.html": "<html></html>"})
    validate.check_post(p, "3-review", r)
    assert any("numbered 2 but this post has 1 part" in e for e in r.errors)


def test_card_without_alt_text_is_rejected(post):
    r = rep()
    p = post("3-review", extra_files={"card-1-some-post.html": (
        '<script type="application/json" id="card-data">{}</script>'
    )})
    validate.check_post(p, "3-review", r)
    assert any("no alt text" in e for e in r.errors)


def test_card_never_rendered_is_rejected(post):
    r = rep()
    p = post("3-review", png=False)
    validate.check_post(p, "3-review", r)
    assert any("never been rendered" in e for e in r.errors)


def test_media_pointing_nowhere_is_rejected(post):
    r = rep()
    p = post("3-review", frontmatter=(
        "id: some-post\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-08-01\n"
        "verified: true\nmedia: card-9-missing.png\n"
    ))
    validate.check_post(p, "3-review", r)
    assert any("does not exist" in e for e in r.errors)


def test_media_none_is_a_choice_not_an_error(post):
    """The pinned intro post has no measurement to show; a chart would undercut it."""
    r = rep()
    p = post("3-review", card=False, frontmatter=(
        "id: some-post\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-08-01\n"
        "verified: true\nmedia: none\n"
    ))
    validate.check_post(p, "3-review", r)
    assert r.errors == []


def test_verified_false_cannot_reach_review(post):
    r = rep()
    p = post("3-review", frontmatter=(
        "id: some-post\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-08-01\n"
        "verified: false\nmedia: none\n"
    ))
    validate.check_post(p, "3-review", r)
    assert any("verified: false" in e for e in r.errors)


def test_expires_before_scheduled_date_is_an_error(post):
    r = rep()
    name = "2026-08-06-dinghy-law-family"
    p = post("4-scheduled", name=name, frontmatter=(
        f"id: {name}\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-08-01\n"
        "verified: true\nmedia: none\nexpires: 2026-08-05\n"
        "scheduled_for: 2026-08-06T14:30:00+02:00\napproved_by: kennethenevoldsen\n"
    ))
    validate.check_post(p, "4-scheduled", r)
    assert any("already stale" in e for e in r.errors)


def test_empty_linkedin_block_is_an_error(post):
    r = rep()
    p = post("3-review", body="## LinkedIn\n\n```linkedin\n\n```\n")
    validate.check_post(p, "3-review", r)
    assert any("empty linkedin block" in e for e in r.errors)


def test_linkedin_block_is_not_held_to_300_chars(post):
    """The fence keeps it out of the limit on purpose — it is pasted by hand."""
    r = rep()
    p = post("3-review", body="```linkedin\n" + "x" * 900 + "\n```\n")
    validate.check_post(p, "3-review", r)
    assert r.errors == []


def test_night_time_schedule_warns_but_passes(post):
    """Intentional 03:00 posts exist; a wrong offset looks exactly like one."""
    r = rep()
    name = "2026-08-06-dinghy-law-family"
    p = post("4-scheduled", name=name, frontmatter=(
        f"id: {name}\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-08-01\n"
        "verified: true\nmedia: none\n"
        "scheduled_for: 2026-08-06T03:00:00+02:00\napproved_by: kennethenevoldsen\n"
    ))
    validate.check_post(p, "4-scheduled", r)
    assert r.errors == []
    assert any("check the offset" in w for w in r.warnings)


def test_two_posts_on_one_day_fail(post):
    """One post a day is the cadence ceiling, and a backlog spreads rather than batches."""
    r = rep()
    post("4-scheduled", name="2026-08-06-a", card_name="card-1-a")
    post("4-scheduled", name="2026-08-06-b", card_name="card-1-b")
    validate.check_schedule(post("4-scheduled").parent.parent.parent, r)
    assert any("2026-08-06 has 2 posts" in e for e in r.errors)


def test_frontmatter_parser_ignores_nested_list_items():
    fm = validate.frontmatter(
        "---\nid: x\ntrigger: mteb#1\nsources:\n  - https://example.com\n---\nbody\n"
    )
    assert fm == {"id": "x", "trigger": "mteb#1", "sources": ""}


def test_frontmatter_absent_is_empty():
    assert validate.frontmatter("no frontmatter here") == {}


def test_queue_stats_counts_each_stage_and_its_expired_head(post):
    """The summary exists because a third of the queue sat expired and nothing said so."""
    post("1-candidates", name="fresh", frontmatter=(
        "id: fresh\ntype: model_addition\ntrigger: mteb#1\ntrigger_date: 2026-10-01\n"
        "expires: 2099-01-01\n"
    ))
    post("1-candidates", name="stale", frontmatter=(
        "id: stale\ntype: model_addition\ntrigger: mteb#2\ntrigger_date: 2020-01-01\n"
        "expires: 2020-02-01\n"
    ))
    p = post("1-candidates", name="undated", frontmatter=(
        "id: undated\ntype: model_addition\ntrigger: mteb#3\ntrigger_date: 2026-10-01\n"
    ))
    stats = {stage: (total, expired) for stage, total, expired
             in validate.queue_stats(p.parent.parent.parent)}
    assert stats["1-candidates"] == (3, 1)


def test_queue_stats_does_not_report_expiry_on_the_archive(post):
    """An old `expires:` on a published post is history, not something to act on."""
    p = post("5-posted", name="2020-01-01-old", frontmatter=(
        "id: 2020-01-01-old\ntype: model_addition\ntrigger: mteb#1\n"
        "trigger_date: 2019-12-01\nexpires: 2020-01-01\nverified: true\nmedia: none\n"
        "scheduled_for: 2020-01-01T14:30:00+01:00\napproved_by: kennethenevoldsen\n"
        "posted_on: 2020-01-01\nurl: https://example.com\n"
    ))
    stats = {stage: (total, expired) for stage, total, expired
             in validate.queue_stats(p.parent.parent.parent)}
    assert stats["5-posted"] == (1, 0)
