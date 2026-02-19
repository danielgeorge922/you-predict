"""Tests for src.models.operational and src.models.ml."""

from datetime import UTC, date, datetime

from src.models.ml import ExperimentLog, ModelRegistry, PredictionLog
from src.models.operational import DataQualityResult, PipelineRunLog


class TestPipelineRunLog:
    def test_creation(self):
        log = PipelineRunLog(
            run_id="run-001",
            pipeline_name="daily_channel_refresh",
            target_table="dim_channel",
            started_at=datetime(2026, 2, 15, 0, 0, tzinfo=UTC),
            status="success",
            rows_affected=25,
            run_date=date(2026, 2, 15),
        )
        assert log.pipeline_name == "daily_channel_refresh"
        assert log.finished_at is None
        assert log.error_message is None

    def test_failed_run(self):
        log = PipelineRunLog(
            run_id="run-002",
            pipeline_name="compute_features",
            started_at=datetime(2026, 2, 15, 13, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 15, 13, 5, tzinfo=UTC),
            status="failed",
            error_message="BigQuery timeout",
            run_date=date(2026, 2, 15),
        )
        assert log.status == "failed"
        assert log.error_message == "BigQuery timeout"


class TestDataQualityResult:
    def test_passing_check(self):
        result = DataQualityResult(
            check_id="chk-001",
            table_name="dim_channel",
            check_name="freshness",
            check_type="freshness",
            passed=True,
            actual_value=2.0,
            expected_value=24.0,
            checked_at=datetime(2026, 2, 15, 14, 0, tzinfo=UTC),
            check_date=date(2026, 2, 15),
        )
        assert result.passed is True

    def test_failing_check(self):
        result = DataQualityResult(
            check_id="chk-002",
            table_name="fact_video_snapshot",
            check_name="null_rate_view_count",
            check_type="null_rate",
            passed=False,
            actual_value=0.15,
            expected_value=0.05,
            checked_at=datetime(2026, 2, 15, 14, 0, tzinfo=UTC),
            check_date=date(2026, 2, 15),
        )
        assert result.passed is False


class TestModelRegistry:
    def test_creation(self):
        model = ModelRegistry(
            model_id="model-001",
            model_name="virality_classifier_v1",
            model_version=1,
            framework="xgboost",
            artifact_gcs_uri="gs://you-predict-models/v1.pkl",
            feature_set=["views_1h", "like_view_ratio"],
            metrics={"accuracy": 0.85, "f1": 0.82},
        )
        assert model.status == "staging"
        assert model.promoted_at is None
        assert len(model.feature_set) == 2


class TestPredictionLog:
    def test_creation(self):
        pred = PredictionLog(
            prediction_id="pred-001",
            model_id="model-001",
            video_id="abc123",
            predicted_at=datetime(2026, 2, 15, 10, 0, tzinfo=UTC),
            prediction_date=date(2026, 2, 15),
            prediction_type="virality_class",
            predicted_class="viral",
            prediction_confidence=0.92,
        )
        assert pred.actual_value is None
        assert pred.absolute_error is None


class TestExperimentLog:
    def test_creation(self):
        exp = ExperimentLog(
            experiment_id="exp-001",
            experiment_name="xgboost_vs_lightgbm",
            hypothesis="XGBoost outperforms LightGBM on this dataset",
            model_a_id="model-001",
            model_b_id="model-002",
        )
        assert exp.winner is None
        assert exp.sample_size is None
