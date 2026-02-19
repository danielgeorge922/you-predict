"""MLOps models — model registry, predictions, experiments."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class ModelRegistry(BaseModel):
    model_id: str
    model_name: str
    model_version: int
    framework: str
    artifact_gcs_uri: str
    feature_set: list[str] = []
    training_date: datetime | None = None
    training_rows: int | None = None
    metrics: dict[str, Any] = {}
    status: str = "staging"
    promoted_at: datetime | None = None


class PredictionLog(BaseModel):
    prediction_id: str
    model_id: str
    video_id: str
    predicted_at: datetime
    prediction_date: date
    prediction_type: str
    predicted_value: float | None = None
    predicted_class: str | None = None
    prediction_confidence: float | None = None
    features_snapshot: dict[str, Any] = {}
    actual_value: float | None = None
    absolute_error: float | None = None


class ExperimentLog(BaseModel):
    experiment_id: str
    experiment_name: str
    hypothesis: str | None = None
    model_a_id: str | None = None
    model_b_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sample_size: int | None = None
    result_summary: dict[str, Any] = {}
    winner: str | None = None
