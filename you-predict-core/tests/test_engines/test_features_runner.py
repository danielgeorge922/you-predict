"""Tests for FeatureRunner and FEATURE_EXECUTION_ORDER registry."""

import pytest

from src.engines.features.registry import FEATURE_EXECUTION_ORDER
from src.engines.features.runner import FeatureRunner

_ALL_FEATURES = {"channel", "video_performance", "video_content", "temporal", "comment_aggregates"}


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestFeatureExecutionOrder:
    def test_contains_all_five_features(self):
        assert set(FEATURE_EXECUTION_ORDER) == _ALL_FEATURES

    def test_exactly_five_features_no_duplicates(self):
        assert len(FEATURE_EXECUTION_ORDER) == 5

    def test_channel_runs_before_video_performance(self):
        # video_performance.sql joins ml_feature_channel — channel must be first
        assert FEATURE_EXECUTION_ORDER.index("channel") < FEATURE_EXECUTION_ORDER.index(
            "video_performance"
        )

    def test_channel_is_first(self):
        assert FEATURE_EXECUTION_ORDER[0] == "channel"


# ---------------------------------------------------------------------------
# FeatureRunner tests
# ---------------------------------------------------------------------------


class TestFeatureRunner:
    def test_run_calls_bq_run_merge(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("channel")
        assert mock_bq.run_merge.called

    def test_run_returns_rows_affected(self, mock_bq):
        mock_bq.run_merge.return_value = 42
        runner = FeatureRunner(mock_bq)
        result = runner.run("channel")
        assert result == 42

    def test_run_passes_sql_string_to_bq(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("channel")
        sql = mock_bq.run_merge.call_args[0][0]
        assert isinstance(sql, str)
        assert len(sql) > 0

    def test_run_channel_sql_targets_correct_table(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("channel")
        sql = mock_bq.run_merge.call_args[0][0]
        assert "ml_feature_channel" in sql

    def test_run_video_performance_sql_targets_correct_table(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("video_performance")
        sql = mock_bq.run_merge.call_args[0][0]
        assert "ml_feature_video_performance" in sql

    def test_run_video_content_sql_targets_correct_table(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("video_content")
        sql = mock_bq.run_merge.call_args[0][0]
        assert "ml_feature_video_content" in sql

    def test_run_temporal_sql_targets_correct_table(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("temporal")
        sql = mock_bq.run_merge.call_args[0][0]
        assert "ml_feature_temporal" in sql

    def test_run_comment_aggregates_sql_targets_correct_table(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("comment_aggregates")
        sql = mock_bq.run_merge.call_args[0][0]
        assert "ml_feature_comment_aggregates" in sql

    def test_run_unknown_feature_raises_file_not_found(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        with pytest.raises(FileNotFoundError):
            runner.run("nonexistent_feature")

    def test_run_all_features_in_order_calls_bq_five_times(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        for name in FEATURE_EXECUTION_ORDER:
            runner.run(name)
        assert mock_bq.run_merge.call_count == 5

    def test_sql_contains_project_placeholder(self, mock_bq):
        runner = FeatureRunner(mock_bq)
        runner.run("channel")
        sql = mock_bq.run_merge.call_args[0][0]
        # Placeholders must be present — BigQueryService._format_sql() substitutes them
        assert "{project}" in sql
        assert "{dataset}" in sql
