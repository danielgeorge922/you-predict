"""Dimension table Pydantic models — current-state entities."""

from datetime import date, datetime

from pydantic import BaseModel


class DimChannel(BaseModel):
    channel_id: str
    channel_name: str | None = None
    channel_description: str | None = None
    custom_url: str | None = None
    channel_thumbnail_url: str | None = None
    channel_created_at: datetime | None = None
    made_for_kids: bool | None = None
    hidden_subscriber_count: bool | None = None
    channel_keywords: str | None = None
    uploads_playlist_id: str | None = None
    topics: list[str] = []
    topic_ids: list[str] = []
    # Current stats (overwritten on each daily MERGE refresh)
    view_count: int | None = None
    subscriber_count: int | None = None
    video_count: int | None = None
    updated_at: datetime | None = None


class DimVideo(BaseModel):
    video_id: str
    channel_id: str
    title: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    category_id: int | None = None
    is_livestream: bool | None = None
    is_age_restricted: bool | None = None
    made_for_kids: bool | None = None
    has_custom_thumbnail: bool | None = None
    definition: str | None = None
    caption_available: bool | None = None
    licensed_content: bool | None = None
    has_paid_promotion: bool | None = None
    tags: list[str] = []
    topics: list[str] = []
    # Current stats (overwritten on each daily MERGE refresh)
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    first_seen_at: datetime | None = None
    updated_at: datetime | None = None


class DimCategory(BaseModel):
    category_id: int
    category_name: str


class DimDate(BaseModel):
    date_key: int
    full_date: date
    year: int
    quarter: int
    month: int
    month_name: str
    week_of_year: int
    day_of_month: int
    day_of_week: int
    day_name: str
    is_weekend: bool
    is_us_holiday: bool = False
    season: str = ""


class DimVideoTranscript(BaseModel):
    video_id: str
    transcript_source: str | None = None
    gcs_uri: str | None = None
    word_count: int | None = None
    fetched_at: datetime | None = None
    topic_keywords: list[str] = []
    readability_score: float | None = None
    has_profanity: bool | None = None
