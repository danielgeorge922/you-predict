"""ML feature vector models — one model per feature table."""

from datetime import date, datetime

from pydantic import BaseModel


class FeatureVideoPerformance(BaseModel):
    video_id: str
    computed_at: datetime | None = None
    computed_date: date | None = None
    # View counts — one field per snapshot interval (mirrors FanoutSchedule)
    views_1h: int | None = None
    views_2h: int | None = None
    views_3h: int | None = None
    views_4h: int | None = None
    views_6h: int | None = None
    views_8h: int | None = None
    views_10h: int | None = None
    views_12h: int | None = None
    views_14h: int | None = None
    views_16h: int | None = None
    views_18h: int | None = None
    views_20h: int | None = None
    views_22h: int | None = None
    views_24h: int | None = None
    views_36h: int | None = None
    views_48h: int | None = None
    views_72h: int | None = None
    # Like counts — same intervals as views
    likes_1h: int | None = None
    likes_2h: int | None = None
    likes_3h: int | None = None
    likes_4h: int | None = None
    likes_6h: int | None = None
    likes_8h: int | None = None
    likes_10h: int | None = None
    likes_12h: int | None = None
    likes_14h: int | None = None
    likes_16h: int | None = None
    likes_18h: int | None = None
    likes_20h: int | None = None
    likes_22h: int | None = None
    likes_24h: int | None = None
    likes_36h: int | None = None
    likes_48h: int | None = None
    likes_72h: int | None = None
    # Comment counts — same intervals as views and likes
    comments_1h: int | None = None
    comments_2h: int | None = None
    comments_3h: int | None = None
    comments_4h: int | None = None
    comments_6h: int | None = None
    comments_8h: int | None = None
    comments_10h: int | None = None
    comments_12h: int | None = None
    comments_14h: int | None = None
    comments_16h: int | None = None
    comments_18h: int | None = None
    comments_20h: int | None = None
    comments_22h: int | None = None
    comments_24h: int | None = None
    comments_36h: int | None = None
    comments_48h: int | None = None
    comments_72h: int | None = None
    # View velocity (views/hour) — one per interval
    view_velocity_1h: float | None = None
    view_velocity_2h: float | None = None
    view_velocity_3h: float | None = None
    view_velocity_4h: float | None = None
    view_velocity_6h: float | None = None
    view_velocity_8h: float | None = None
    view_velocity_10h: float | None = None
    view_velocity_12h: float | None = None
    view_velocity_14h: float | None = None
    view_velocity_16h: float | None = None
    view_velocity_18h: float | None = None
    view_velocity_20h: float | None = None
    view_velocity_22h: float | None = None
    view_velocity_24h: float | None = None
    view_velocity_36h: float | None = None
    view_velocity_48h: float | None = None
    view_velocity_72h: float | None = None
    # Engagement velocities and derived metrics
    like_velocity_1h: float | None = None
    comment_velocity_1h: float | None = None
    peak_velocity: float | None = None
    engagement_acceleration: float | None = None
    like_view_ratio: float | None = None
    comment_view_ratio: float | None = None
    performance_vs_channel_avg: float | None = None


class FeatureVideoContent(BaseModel):
    video_id: str
    computed_at: datetime | None = None
    computed_date: date | None = None
    title_length: int | None = None
    title_word_count: int | None = None
    title_has_emoji: bool | None = None
    title_has_number: bool | None = None
    title_has_question: bool | None = None
    title_has_brackets: bool | None = None
    title_caps_ratio: float | None = None
    title_power_word_count: int | None = None
    title_sentiment: float | None = None
    title_clickbait_score: float | None = None
    description_length: int | None = None
    description_link_count: int | None = None
    tag_count: int | None = None
    topic_count: int | None = None
    duration_bucket: str | None = None


class FeatureTemporal(BaseModel):
    video_id: str
    computed_at: datetime | None = None
    hour_of_day_published: int | None = None
    day_of_week_published: int | None = None
    is_weekend_publish: bool | None = None
    is_holiday_publish: bool | None = None
    days_since_last_upload: int | None = None
    videos_published_same_day_channel: int | None = None


class FeatureChannel(BaseModel):
    channel_id: str
    computed_at: datetime | None = None
    computed_date: date | None = None
    subscriber_tier: str | None = None
    channel_age_days: int | None = None
    upload_frequency_7d: float | None = None
    upload_frequency_30d: float | None = None
    avg_views_per_video_30d: int | None = None
    avg_engagement_rate_30d: float | None = None
    subscriber_growth_rate_30d: float | None = None
    view_consistency_score: float | None = None
    avg_video_duration_30d: int | None = None
    channel_momentum_score: float | None = None
    avg_time_between_uploads_7d: float | None = None


class FeatureCommentAggregates(BaseModel):
    video_id: str
    computed_at: datetime | None = None
    computed_date: date | None = None
    sample_strategy: str | None = None
    comments_sampled: int | None = None
    avg_sentiment_compound: float | None = None
    positive_ratio: float | None = None
    negative_ratio: float | None = None
    avg_toxicity: float | None = None
    avg_severe_toxicity: float | None = None
    avg_insult: float | None = None
    avg_identity_attack: float | None = None
    toxic_ratio: float | None = None
    severe_toxic_ratio: float | None = None
    insult_ratio: float | None = None
    identity_attack_ratio: float | None = None
    max_toxicity: float | None = None
    max_identity_attack: float | None = None
    avg_comment_likes: float | None = None
    max_comment_likes: int | None = None
    avg_reply_count: float | None = None
    comment_language_entropy: float | None = None
    unique_commenter_ratio: float | None = None
    avg_comment_length: float | None = None
    question_comment_ratio: float | None = None
    creator_reply_count: int | None = None
