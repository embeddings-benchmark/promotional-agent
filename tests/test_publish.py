"""The publisher's guardrails, minus the network.

`send()` is the one function here that talks to Bluesky and it is not tested — everything
it relies on is, because the failures that matter are the ones that let it send something
it should have refused: a post that is not due, one that missed its day, a naive
timestamp read as UTC, or an image attached to the wrong part of a thread.
"""

from __future__ import annotations

import datetime as dt
import pathlib

import pytest

from mtebpost import publish


class TestParseWhen:
    def test_aware_timestamp_is_kept_in_the_writer_s_timezone(self):
        when = publish.parse_when("2026-08-05T09:00:00+02:00")
        assert when is not None
        assert when.hour == 9  # not converted to UTC: lateness is a local-calendar question
        assert when.utcoffset() == dt.timedelta(hours=2)

    def test_naive_timestamp_is_unusable(self):
        assert publish.parse_when("2026-08-05T09:00") is None

    def test_garbage_is_unusable(self):
        assert publish.parse_when("next tuesday") is None
        assert publish.parse_when("") is None


class TestTooLate:
    def test_later_the_same_local_day_still_publishes(self):
        """Cron is best-effort; 09:00 arriving at 11:00 is on time to a reader."""
        when = dt.datetime(2026, 8, 5, 9, 0, tzinfo=dt.timezone(dt.timedelta(hours=2)))
        now = dt.datetime(2026, 8, 5, 11, 0, tzinfo=dt.timezone(dt.timedelta(hours=2)))
        assert publish.too_late(when, now) is False

    def test_the_next_local_day_is_too_late(self):
        when = dt.datetime(2026, 8, 5, 9, 0, tzinfo=dt.timezone(dt.timedelta(hours=2)))
        now = dt.datetime(2026, 8, 6, 0, 30, tzinfo=dt.timezone(dt.timedelta(hours=2)))
        assert publish.too_late(when, now) is True

    def test_the_day_boundary_is_judged_in_the_post_s_timezone(self):
        """23:00 UTC is already the 26th in Copenhagen, and 23:00 the 25th in São Paulo.

        Same instant, two different verdicts — which is why the offset is mandatory.
        """
        instant = dt.datetime(2026, 8, 25, 23, 0, tzinfo=dt.UTC)
        copenhagen = dt.datetime(2026, 8, 25, 9, 0,
                                 tzinfo=dt.timezone(dt.timedelta(hours=2)))
        sao_paulo = dt.datetime(2026, 8, 25, 9, 0,
                                tzinfo=dt.timezone(dt.timedelta(hours=-3)))
        assert publish.too_late(copenhagen, instant) is True   # 26th vs the 25th
        assert publish.too_late(sao_paulo, instant) is False   # 25th vs the 25th


class TestCardFor:
    def test_single_part_post_finds_its_numbered_card(self, tmp_path: pathlib.Path):
        (tmp_path / "card-1-frontier.png").write_bytes(b"x")
        assert publish.card_for(tmp_path, 1).name == "card-1-frontier.png"

    def test_thread_part_without_a_card_is_text_only(self, tmp_path: pathlib.Path):
        (tmp_path / "card-1-frontier.png").write_bytes(b"x")
        assert publish.card_for(tmp_path, 2) is None

    def test_a_thread_part_gets_its_own_card(self, tmp_path: pathlib.Path):
        (tmp_path / "card-1-frontier.png").write_bytes(b"x")
        (tmp_path / "card-2-tasks.png").write_bytes(b"x")
        assert publish.card_for(tmp_path, 2).name == "card-2-tasks.png"

    def test_bare_card_is_invisible(self, tmp_path: pathlib.Path):
        """Which is the whole reason validate.py rejects the name."""
        (tmp_path / "card.png").write_bytes(b"x")
        assert publish.card_for(tmp_path, 1) is None


def test_wrap_keeps_words_whole():
    assert publish._wrap("one two three four", 9) == ["one two", "three", "four"]


def test_png_size_reads_the_ihdr_chunk(tmp_path: pathlib.Path):
    import struct

    p = tmp_path / "x.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
                  + struct.pack(">II", 2400, 1200) + b"\0" * 8)
    assert publish.png_size(p) == (2400, 1200)


class TestRecordPosted:
    def test_stamps_and_moves_the_folder(self, tmp_path: pathlib.Path):
        d = tmp_path / "posts" / "4-scheduled" / "2026-08-06-some-post"
        d.mkdir(parents=True)
        post = d / "post.md"
        post.write_text("---\nid: x\nscheduled_for: 2026-08-06T14:30:00+02:00\n---\nbody\n")

        publish._record_posted(post, "https://bsky.app/profile/mteb.org/post/abc")

        moved = tmp_path / "posts" / "5-posted" / "2026-08-06-some-post" / "post.md"
        text = moved.read_text()
        assert "url: https://bsky.app/profile/mteb.org/post/abc" in text
        assert "posted_on:" in text
        assert not d.exists()

    def test_posted_on_uses_the_post_s_local_day(self):
        """A 23:30 post at UTC-3 belongs to that day, not the runner's next one."""
        sao_paulo = dt.timezone(dt.timedelta(hours=-3))
        when = dt.datetime(2026, 8, 6, 23, 30, tzinfo=sao_paulo)
        # 02:30 UTC on the 7th is still the 6th where the post was scheduled.
        now = dt.datetime(2026, 8, 7, 2, 30, tzinfo=dt.UTC)
        assert publish.local_day(when, now) == dt.date(2026, 8, 6)
        assert publish.local_day(when, now).isoformat() == when.date().isoformat()

    def test_local_day_falls_back_to_utc_without_a_timezone(self):
        now = dt.datetime(2026, 8, 7, 2, 30, tzinfo=dt.UTC)
        assert publish.local_day(None, now) == dt.date(2026, 8, 7)


def test_send_refuses_a_folder_outside_4_scheduled(tmp_path: pathlib.Path):
    d = tmp_path / "posts" / "3-review" / "some-post"
    d.mkdir(parents=True)
    post = d / "post.md"
    post.write_text("---\nid: x\napproved_by: someone\n---\n```\nhello\n```\n")
    with pytest.raises(SystemExit, match="not 4-scheduled"):
        publish.send(post, "mteb.org")


class TestMain:
    """An empty queue is the normal state, and must not fail the hourly workflow."""

    def test_empty_queue_exits_zero(self, tmp_path: pathlib.Path, monkeypatch, capsys):
        (tmp_path / "4-scheduled").mkdir()
        monkeypatch.setattr("sys.argv", ["mteb-publish", "--due", "--posts", str(tmp_path)])
        publish.main()  # no SystemExit
        assert "nothing scheduled" in capsys.readouterr().out

    def test_missing_pipeline_is_still_an_error(self, tmp_path: pathlib.Path, monkeypatch):
        monkeypatch.setattr("sys.argv", ["mteb-publish", "--due", "--posts", str(tmp_path)])
        with pytest.raises(SystemExit, match="run this from the repo root"):
            publish.main()
