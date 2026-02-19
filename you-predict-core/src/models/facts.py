"""Fact table Pydantic models — historical event/metric records."""

from datetime import date, datetime

from pydantic import BaseModel


class FactChannelSnapshot(BaseModel):
    snapshot_date: date
    snapshot_ts: datetime
    channel_id: str
    view_count: int | None = None
    subscriber_count: int | None = None
    video_count: int | None = None
    views_delta: int | None = None
    subs_delta: int | None = None
    videos_delta: int | None = None


class FactVideoSnapshot(BaseModel):
    snapshot_date: date
    snapshot_ts: datetime
    actual_captured_at: datetime
    snapshot_type: str
    video_id: str
    channel_id: str
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    views_delta: int | None = None
    likes_delta: int | None = None
    comments_delta: int | None = None
    hours_since_publish: int | None = None
    actual_hours_since_publish: float | None = None
    days_since_publish: int | None = None


class FactComment(BaseModel):
    comment_id: str
    video_id: str
    channel_id: str
    parent_comment_id: str | None = None
    is_reply: bool = False
    commenter_channel_id: str | None = None
    commenter_name: str | None = None
    comment_text: str | None = None
    like_count: int | None = None
    reply_count: int | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    pulled_at: datetime | None = None
    pull_date: date | None = None
    sample_strategy: str | None = None
    sample_rank: int | None = None
    sentiment_positive: float | None = None
    sentiment_negative: float | None = None
    sentiment_neutral: float | None = None
    sentiment_compound: float | None = None
    toxicity_score: float | None = None
    severe_toxicity_score: float | None = None
    insult_score: float | None = None
    identity_attack_score: float | None = None
