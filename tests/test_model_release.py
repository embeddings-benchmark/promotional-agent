"""Chart-data builders: the numbers a card draws, checked without a browser.

`model_release` decides who counts as a fair peer and which chart shape fits. Getting the
peer set wrong is the failure CONTRIBUTING.md spends the most words on, and getting a rank
wrong puts a confidently-stated untruth on an image. Both are pure functions over `Entry`
lists, so both are testable here. Network-backed construction (`cohort()`) is not tested —
it is a thin wrapper over the leaderboard API, and a test against a live endpoint fails for
reasons that have nothing to do with this code.
"""

from __future__ import annotations

from mtebpost import model_release as M
from mtebpost.leaderboard_api import Entry


def E(model: str, score: float, active: int | None = 7_000_000, total: int | None = None,
      langs: tuple[str, ...] = ("en",), mods: tuple[str, ...] = ("text",),
      n: int = 131, n_bench: int = 131) -> Entry:
    return Entry(
        model=model, score=score, active_params=active,
        total_params=total if total is not None else active,
        n_tasks=n, n_benchmark_tasks=n_bench, languages=langs, modalities=mods,
    )


def cohort(subjects: list[Entry], peers: list[Entry], *, tasks: tuple[str, ...] = (),
           per_task: dict | None = None, max_active: float | None = None) -> M.Cohort:
    return M.Cohort(
        benchmark="MTEB(Multilingual, v2)", subjects=subjects, peers=peers,
        excluded=[], pool=subjects + peers, per_task=per_task or {}, tasks=tasks,
        max_active=max_active,
    )


class TestPareto:
    def test_frontier_is_the_staircase(self):
        entries = [E("a", 50, 1_000_000), E("b", 60, 2_000_000),
                   E("c", 55, 3_000_000), E("d", 70, 5_000_000)]
        assert [e.model for e in M.pareto_frontier(entries)] == ["a", "b", "d"]

    def test_sizeless_entries_are_not_on_a_size_axis(self):
        entries = [E("a", 50, 1_000_000), E("api", 99, None)]
        assert [e.model for e in M.pareto_frontier(entries)] == ["a"]

    def test_ties_do_not_duplicate_the_frontier(self):
        entries = [E("a", 60, 1_000_000), E("b", 60, 2_000_000)]
        assert [e.model for e in M.pareto_frontier(entries)] == ["a"]

    def test_domination_needs_both_smaller_and_better(self):
        subject = E("subject", 60, 5_000_000)
        assert M.is_pareto(subject, [E("smaller", 61, 1_000_000)]) is False
        assert M.is_pareto(subject, [E("larger", 61, 9_000_000)]) is True
        assert M.is_pareto(subject, [E("smaller-but-worse", 59, 1_000_000)]) is True

    def test_an_unknown_size_cannot_make_a_pareto_claim(self):
        assert M.is_pareto(E("subject", 60, None), []) is False


class TestNearestRival:
    def test_picks_the_closest_larger_model_within_the_gap(self):
        subject = E("subject", 60, 1_000_000)
        rival = M.nearest_rival(subject, [E("far", 70, 9_000_000),
                                          E("near", 61, 8_000_000)])
        assert rival.model == "near"

    def test_only_larger_models_are_candidates(self):
        """A smaller model scoring more is a Pareto finding, not a head-to-head."""
        subject = E("subject", 60, 5_000_000)
        assert M.nearest_rival(subject, [E("smaller", 60.5, 1_000_000)]) is None

    def test_nothing_within_the_gap_is_not_a_story(self):
        subject = E("subject", 60, 1_000_000)
        assert M.nearest_rival(subject, [E("x", 70, 9_000_000)], max_gap=2.0) is None


class TestRecommendChart:
    def test_pareto_wins_when_a_subject_is_non_dominated(self):
        coh = cohort([E("subject", 65, 7_000_000)], [E("peer", 60, 9_000_000)])
        rec = M.recommend_chart(coh)
        assert rec.chart == "pareto"
        assert "non-dominated" in rec.reason

    def test_radar_when_one_rival_is_close_and_larger(self):
        coh = cohort([E("subject", 60, 7_000_000)],
                     [E("dominates", 66, 6_000_000), E("rival", 61, 8_000_000)])
        rec = M.recommend_chart(coh)
        assert rec.chart == "radar"
        assert "rival" in rec.reason

    def test_bars_is_the_default_when_no_story_exists(self):
        coh = cohort([E("subject", 40, 7_000_000)],
                     [E("dominates", 66, 6_000_000), E("far", 70, 8_000_000)])
        rec = M.recommend_chart(coh)
        assert rec.chart == "bars"


class TestBarsCardData:
    def test_subject_outside_top_n_is_kept_with_its_true_rank(self):
        """The card's rank is the model's rank on the board, not its row number.

        Counting rows would print rank 3 for a model lying 21st — a wrong number stated
        with exactly the confidence of a right one.
        """
        peers = [E(f"peer{i:02d}", 90 - i, 7_000_000) for i in range(20)]
        subject = E("subject", 10, 7_000_000)
        data = M.bars_card_data(cohort([subject], peers), top_n=3)
        row = next(r for r in data["rows"] if r["model"] == "subject")
        assert row["rank"] == 21
        assert row["subject"] is True
        assert data["n_models"] == 21

    def test_size_field_switches_the_labelled_count(self):
        subject = E("subject", 60, 7_000_000, total=106_000_000)
        data = M.bars_card_data(cohort([subject], []), size_field="total")
        assert data["rows"][0]["params"] == 106_000_000

    def test_prior_generation_is_tagged_distinctly(self):
        coh = cohort([E("new", 61, 7_000_000)], [E("old", 58, 7_000_000)])
        data = M.bars_card_data(coh, prior=("old",))
        prior = next(r for r in data["rows"] if r["model"] == "old")
        assert prior["prior"] is True
        assert "subject" not in prior


class TestRadarCardData:
    def test_axes_fall_back_to_tasks_when_too_few_types(self):
        coh = cohort(
            [E("a", 60, 1_000_000), E("b", 58, 2_000_000)], [],
            per_task={"a": {"T1": 60.0, "T2": 55.0}, "b": {"T1": 58.0, "T2": 54.0}},
        )
        data = M.radar_card_data(coh, {"a": "subject", "b": "highlight"},
                                 task_types={"T1": "Retrieval", "T2": "Retrieval"})
        assert [ax["name"] for ax in data["axes"]] == ["T1", "T2"]

    def test_axes_become_task_types_when_enough_of_them(self):
        tasks = {"T1": "Retrieval", "T2": "Classification", "T3": "Clustering"}
        coh = cohort(
            [E("a", 60, 1_000_000), E("b", 58, 2_000_000)], [],
            per_task={"a": {"T1": 60.0, "T2": 50.0, "T3": 70.0},
                      "b": {"T1": 58.0, "T2": 48.0, "T3": 68.0}},
        )
        data = M.radar_card_data(coh, {"a": "subject", "b": "highlight"},
                                 task_types=tasks)
        assert {ax["name"] for ax in data["axes"]} == set(tasks.values())

    def test_negative_metric_types_are_excluded_rather_than_clamped(self):
        """A radial axis starts at zero; a p-MRR score has no honest position on it."""
        coh = cohort(
            [E("a", 60, 1_000_000), E("b", 58, 2_000_000)], [],
            per_task={"a": {"T1": 60.0, "T2": -5.0, "T3": 70.0, "T4": 50.0},
                      "b": {"T1": 58.0, "T2": -6.0, "T3": 68.0, "T4": 48.0}},
        )
        data = M.radar_card_data(
            coh, {"a": "subject", "b": "highlight"},
            task_types={"T1": "Retrieval", "T2": "InstructionRetrieval",
                        "T3": "Clustering", "T4": "Classification"},
        )
        assert "InstructionRetrieval" in data["excluded_axes"]
        assert "InstructionRetrieval" not in {ax["name"] for ax in data["axes"]}

    def test_a_role_model_missing_from_the_cohort_is_an_error_not_a_zero(self):
        coh = cohort([E("a", 60, 1_000_000)], [])
        try:
            M.radar_card_data(coh, {"a": "subject", "ghost": "highlight"})
        except SystemExit as e:
            assert "ghost" in str(e)
        else:
            raise AssertionError("a missing series should not silently plot at zero")


class TestParetoCardData:
    def test_sizeless_points_are_dropped_from_a_scatter(self):
        coh = cohort([E("subject", 60, 7_000_000)],
                     [E("peer", 58, None), E("other", 55, 9_000_000)],
                     max_active=10_000_000)
        data = M.pareto_card_data(coh)
        assert {p["model"] for p in data["points"]} == {"subject", "other"}
        assert data["max_active_params"] == 10_000_000

    def test_reference_point_is_marked_not_peered(self):
        coh = cohort([E("subject", 60, 7_000_000)], [])
        data = M.pareto_card_data(coh, reference=E("giant", 70, 8_000_000_000))
        ref = next(p for p in data["points"] if p["model"] == "giant")
        assert ref["reference"] is True
        assert "subject" not in ref


class TestCohortProperties:
    def test_n_benchmark_tasks_survives_a_benchmark_post_with_no_subject(self):
        coh = cohort([], [E("peer", 58)])
        assert coh.n_benchmark_tasks == 131

    def test_ranking_merges_subjects_and_peers(self):
        coh = cohort([E("subject", 60)], [E("peer", 62)])
        assert [e.model for e in coh.all_comparable] == ["peer", "subject"]
