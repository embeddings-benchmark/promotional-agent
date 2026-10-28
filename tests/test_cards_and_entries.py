"""Writing numbers into a card, and the entry contract both data sources share.

`leaderboard_api.Entry` and `scoreboard.Entry` are deliberately interchangeable: a card
builder must not care which module produced its rows. The property that matters is
`complete` — MTEB will aggregate a model that ran a subset of tasks and produce a mean
that looks comparable to one over all of them, and that is the mistake every cohort rule
in CONTRIBUTING.md exists to prevent.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from mtebpost import cards
from mtebpost import leaderboard_api as api

CARD = """<html>
<script type="application/json" id="card-data">
{"benchmark": "placeholder"}
</script>
<script type="text/plain" id="alt-text">
old alt
</script>
</html>
"""


def test_write_card_data_replaces_the_block_in_place(tmp_path: pathlib.Path):
    card = tmp_path / "card-1-x.html"
    card.write_text(CARD)
    cards.write_card_data(card, {"benchmark": "MTEB(eng, v2)", "n_tasks": 41})

    text = card.read_text()
    data = json.loads(text.split('id="card-data">', 1)[1].split("</script>", 1)[0])
    assert data == {"benchmark": "MTEB(eng, v2)", "n_tasks": 41}
    assert "old alt" in text  # the alt text is not clobbered by a data write


def test_write_card_data_refuses_a_card_with_no_data_block(tmp_path: pathlib.Path):
    card = tmp_path / "card-1-x.html"
    card.write_text("<html><body>no block</body></html>")
    with pytest.raises(SystemExit, match="no #card-data block"):
        cards.write_card_data(card, {"x": 1})


class TestEntry:
    def test_complete_is_coverage_not_score(self):
        full = api.Entry("m", 60.0, 1, 1, n_tasks=131, n_benchmark_tasks=131)
        part = api.Entry("m", 60.0, 1, 1, n_tasks=130, n_benchmark_tasks=131)
        assert full.complete is True
        assert part.complete is False

    def test_plottable_needs_both_a_score_and_a_size(self):
        assert api.Entry("m", 60.0, None, None, 131, 131).plottable is False
        # zero active params is a static model, not a missing size
        assert api.Entry("m", 60.0, 0, 106, 131, 131).plottable is True

    def test_static_models_are_identified_by_zero_not_none(self):
        assert api.Entry("m", 60.0, 0, 106, 131, 131).is_static is True
        assert api.Entry("m", 60.0, None, 106, 131, 131).is_static is False

    def test_as_dict_lists_are_plain_lists(self):
        d = api.Entry("m", 60.0, 1, 1, 131, 131, languages=("en",)).as_dict()
        assert d["languages"] == ["en"]
        assert json.dumps(d)  # serialisable, so it can go straight into card data


class TestScaling:
    def test_scores_are_fractions_in_the_api_and_0_100_here(self):
        assert api._score100(0.6123) == 61.23
        assert api._score100(61.23) == 61.23

    def test_params_come_back_as_raw_counts_not_billions(self):
        assert api._params({"activeParamsB": 0.0077, "totalParamsB": 0.106}) == (
            7_700_000, 106_000_000,
        )

    def test_unknown_params_stay_unknown(self):
        assert api._params({}) == (None, None)
