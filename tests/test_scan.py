"""Stage 0: what counts as a candidate, and the two bugs that made it lose one.

The scanner is deliberately dumb — title conventions and substring overlap — so the tests
are about its known failure modes rather than its cleverness: a pairing that equality
would miss, a title that classifies as news when it is plumbing, and the date arithmetic
that used to crash the scheduled run.
"""

from __future__ import annotations

import pathlib

from mtebpost import scan


def pr(number: int, title: str, merged: str = "2026-08-01") -> dict:
    return {
        "number": number,
        "title": title,
        "mergedAt": f"{merged}T12:00:00Z",
        "author": {"login": "someone"},
        "url": f"https://github.com/embeddings-benchmark/mteb/pull/{number}",
    }


class TestClassify:
    def test_plumbing_is_skipped_before_the_broad_patterns(self):
        # Ordered "not news first": "add docs for models" must not read as a model.
        for title in ("ci: split workflow", "chore: bump ruff", "docs: add model guide",
                      "test: fixtures", "Bump actions/checkout from 4 to 5"):
            assert scan.classify(title) == "skip", title

    def test_model_titles(self):
        for title in ("model: add Bekko", "Add Bekko embedding models",
                      "Add ModelMeta for foo/bar", "Register new model baz"):
            assert scan.classify(title) == "model", title

    def test_dataset_and_benchmark_titles(self):
        assert scan.classify("[MOEB] add audio tasks") == "dataset"
        assert scan.classify("task: add CoREB") == "dataset"
        assert scan.classify("Add new benchmark BRIGHT-Pro") == "benchmark"

    def test_fixes_are_their_own_bucket(self):
        assert scan.classify("fix: aggregation with missing tasks") == "fix"
        assert scan.classify("Revert \"Add model\"") == "fix"

    def test_unknown_falls_through(self):
        assert scan.classify("Update citation") == "other"


class TestPairing:
    """The pairing that equality gets wrong: a model PR and a results PR name the model
    differently, and only a substring match finds the overlap."""

    def test_bekko_pairs_through_a_longer_token(self):
        results = [pr(798, "MTEB Evaluation Results: hotchpotch/bekko-embedding-v1-a8m")]
        found = scan.pair_results(pr(5741, "Add Bekko embedding models"), results)
        assert found is not None and found["number"] == 798

    def test_a_single_short_overlap_is_not_a_pairing(self):
        results = [pr(1, "Results for something else entirely")]
        assert scan.pair_results(pr(2, "Add model foo"), results) is None

    def test_no_results_at_all_is_no_pairing(self):
        assert scan.pair_results(pr(1, "Add model"), []) is None

    def test_stopwords_carry_no_identity(self):
        # Both titles are made only of boilerplate, so tokens() is empty and there is
        # nothing to pair on — better no candidate than an invented one.
        assert scan.tokens("Add model definitions") == set()
        assert scan.pair_results(pr(1, "Add model definitions"),
                                 [pr(2, "Add model definitions")]) is None


class TestSlug:
    def test_strips_type_prefix(self):
        assert scan.slug("model: Add Bekko embedding models") == "add-bekko-embedding-models"
        assert scan.slug("[MOEB] add audio tasks") == "add-audio-tasks"

    def test_truncates_to_five_words(self):
        assert scan.slug("add one two three four five six") == "one-two-three-four-five"

    def test_falls_back_rather_than_returning_empty(self):
        assert scan.slug("model:") == "candidate"


class TestExpiry:
    """`expires:` is trigger date + one month, and the months are not all 31 days.

    The old implementation was `date.replace(month=month % 12 + 1)`, which raises
    ValueError on 31 January (31 February) and silently keeps the year in December.
    """

    def test_plain_rollover(self):
        assert scan.expiry("2026-08-10") == "2026-09-10"

    def test_short_month_clamps_instead_of_raising(self):
        assert scan.expiry("2026-01-31") == "2026-02-28"

    def test_leap_year_is_not_a_special_case(self):
        assert scan.expiry("2028-01-31") == "2028-02-29"

    def test_december_rolls_the_year(self):
        assert scan.expiry("2026-12-15") == "2027-01-15"

    def test_end_of_december(self):
        assert scan.expiry("2026-12-31") == "2027-01-31"


class TestAlreadyTracked:
    def test_reads_every_stage(self, tmp_path: pathlib.Path):
        for stage, n in (("1-candidates", 1), ("2-drafting", 2), ("5-posted", 3)):
            d = tmp_path / stage / f"p{n}"
            d.mkdir(parents=True)
            (d / "post.md").write_text(
                f"---\ntrigger: mteb#{n}\nsources:\n"
                f"  - https://github.com/embeddings-benchmark/results/pull/{n + 10}\n---\n"
            )
        tracked = scan.already_tracked(tmp_path)
        assert tracked == {"mteb#1", "mteb#2", "mteb#3",
                           "results#11", "results#12", "results#13"}
