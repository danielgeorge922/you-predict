"""Operational models — pipeline tracking and data quality."""

from datetime import date, datetime

from pydantic import BaseModel


class PipelineRunLog(BaseModel):
    run_id: str
    pipeline_name: str
    target_table: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    rows_affected: int | None = None
    error_message: str | None = None
    run_date: date


class DataQualityResult(BaseModel):
    check_id: str
    table_name: str
    check_name: str
    check_type: str
    passed: bool
    actual_value: float | None = None
    expected_value: float | None = None
    checked_at: datetime
    check_date: date
