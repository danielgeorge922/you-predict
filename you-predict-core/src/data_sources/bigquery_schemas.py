"""BigQuery SchemaField definitions for all tables.

These are the source of truth for table creation (bootstrap_tables.py)
and must match the Pydantic models in src/models/.
"""

from google.cloud.bigquery import SchemaField

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

DIM_CHANNEL = [
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("channel_name", "STRING"),
    SchemaField("channel_description", "STRING"),
    SchemaField("custom_url", "STRING"),
    SchemaField("channel_thumbnail_url", "STRING"),
    SchemaField("channel_created_at", "TIMESTAMP"),
    SchemaField("made_for_kids", "BOOL"),
    SchemaField("hidden_subscriber_count", "BOOL"),
    SchemaField("channel_keywords", "STRING"),
    SchemaField("uploads_playlist_id", "STRING"),
    SchemaField("topics", "STRING", mode="REPEATED"),
    SchemaField("topic_ids", "STRING", mode="REPEATED"),
    SchemaField("view_count", "INT64"),
    SchemaField("subscriber_count", "INT64"),
    SchemaField("video_count", "INT64"),
    SchemaField("updated_at", "TIMESTAMP"),
]

DIM_VIDEO = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("title", "STRING"),
    SchemaField("description", "STRING"),
    SchemaField("published_at", "TIMESTAMP"),
    SchemaField("thumbnail_url", "STRING"),
    SchemaField("duration_seconds", "INT64"),
    SchemaField("category_id", "INT64"),
    SchemaField("is_livestream", "BOOL"),
    SchemaField("is_age_restricted", "BOOL"),
    SchemaField("made_for_kids", "BOOL"),
    SchemaField("has_custom_thumbnail", "BOOL"),
    SchemaField("definition", "STRING"),
    SchemaField("caption_available", "BOOL"),
    SchemaField("licensed_content", "BOOL"),
    SchemaField("has_paid_promotion", "BOOL"),
    SchemaField("tags", "STRING", mode="REPEATED"),
    SchemaField("topics", "STRING", mode="REPEATED"),
    SchemaField("view_count", "INT64"),
    SchemaField("like_count", "INT64"),
    SchemaField("comment_count", "INT64"),
    SchemaField("first_seen_at", "TIMESTAMP"),
    SchemaField("updated_at", "TIMESTAMP"),
]

DIM_CATEGORY = [
    SchemaField("category_id", "INT64", mode="REQUIRED"),
    SchemaField("category_name", "STRING"),
]

DIM_DATE = [
    SchemaField("date_key", "INT64", mode="REQUIRED"),
    SchemaField("full_date", "DATE"),
    SchemaField("year", "INT64"),
    SchemaField("quarter", "INT64"),
    SchemaField("month", "INT64"),
    SchemaField("month_name", "STRING"),
    SchemaField("week_of_year", "INT64"),
    SchemaField("day_of_month", "INT64"),
    SchemaField("day_of_week", "INT64"),
    SchemaField("day_name", "STRING"),
    SchemaField("is_weekend", "BOOL"),
    SchemaField("is_us_holiday", "BOOL"),
    SchemaField("season", "STRING"),
]

DIM_VIDEO_TRANSCRIPT = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("transcript_source", "STRING"),
    SchemaField("gcs_uri", "STRING"),
    SchemaField("word_count", "INT64"),
    SchemaField("fetched_at", "TIMESTAMP"),
    SchemaField("topic_keywords", "STRING", mode="REPEATED"),
    SchemaField("readability_score", "FLOAT64"),
    SchemaField("has_profanity", "BOOL"),
]

# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------

TRACKED_CHANNELS = [
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("added_at", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("is_active", "BOOL", mode="REQUIRED"),
    SchemaField("notes", "STRING"),
]

VIDEO_MONITORING = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("published_at", "TIMESTAMP"),
    SchemaField("discovered_at", "TIMESTAMP"),
    SchemaField("monitoring_until", "TIMESTAMP"),
    SchemaField("first_seen_at", "TIMESTAMP"),
    SchemaField("is_active", "BOOL"),
    SchemaField("inactive_reason", "STRING"),
]

# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------

FACT_CHANNEL_SNAPSHOT = [
    SchemaField("snapshot_date", "DATE", mode="REQUIRED"),
    SchemaField("snapshot_ts", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("view_count", "INT64"),
    SchemaField("subscriber_count", "INT64"),
    SchemaField("video_count", "INT64"),
    SchemaField("views_delta", "INT64"),
    SchemaField("subs_delta", "INT64"),
    SchemaField("videos_delta", "INT64"),
]

FACT_VIDEO_SNAPSHOT = [
    SchemaField("snapshot_date", "DATE", mode="REQUIRED"),
    SchemaField("snapshot_ts", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("actual_captured_at", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("snapshot_type", "STRING"),
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("view_count", "INT64"),
    SchemaField("like_count", "INT64"),
    SchemaField("comment_count", "INT64"),
    SchemaField("views_delta", "INT64"),
    SchemaField("likes_delta", "INT64"),
    SchemaField("comments_delta", "INT64"),
    SchemaField("hours_since_publish", "INT64"),
    SchemaField("actual_hours_since_publish", "FLOAT64"),
    SchemaField("days_since_publish", "INT64"),
]

FACT_COMMENT = [
    SchemaField("comment_id", "STRING", mode="REQUIRED"),
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("parent_comment_id", "STRING"),
    SchemaField("is_reply", "BOOL"),
    SchemaField("commenter_channel_id", "STRING"),
    SchemaField("commenter_name", "STRING"),
    SchemaField("comment_text", "STRING"),
    SchemaField("like_count", "INT64"),
    SchemaField("reply_count", "INT64"),
    SchemaField("published_at", "TIMESTAMP"),
    SchemaField("updated_at", "TIMESTAMP"),
    SchemaField("pulled_at", "TIMESTAMP"),
    SchemaField("pull_date", "DATE"),
    SchemaField("sample_strategy", "STRING"),
    SchemaField("sample_rank", "INT64"),
    SchemaField("sentiment_positive", "FLOAT64"),
    SchemaField("sentiment_negative", "FLOAT64"),
    SchemaField("sentiment_neutral", "FLOAT64"),
    SchemaField("sentiment_compound", "FLOAT64"),
    SchemaField("toxicity_score", "FLOAT64"),
    SchemaField("severe_toxicity_score", "FLOAT64"),
    SchemaField("insult_score", "FLOAT64"),
    SchemaField("identity_attack_score", "FLOAT64"),
]

# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

ML_FEATURE_VIDEO_PERFORMANCE = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("computed_at", "TIMESTAMP"),
    SchemaField("computed_date", "DATE"),
    # View counts — one column per snapshot interval (mirrors FanoutSchedule)
    SchemaField("views_1h", "INT64"),
    SchemaField("views_2h", "INT64"),
    SchemaField("views_3h", "INT64"),
    SchemaField("views_4h", "INT64"),
    SchemaField("views_6h", "INT64"),
    SchemaField("views_8h", "INT64"),
    SchemaField("views_10h", "INT64"),
    SchemaField("views_12h", "INT64"),
    SchemaField("views_14h", "INT64"),
    SchemaField("views_16h", "INT64"),
    SchemaField("views_18h", "INT64"),
    SchemaField("views_20h", "INT64"),
    SchemaField("views_22h", "INT64"),
    SchemaField("views_24h", "INT64"),
    SchemaField("views_36h", "INT64"),
    SchemaField("views_48h", "INT64"),
    SchemaField("views_72h", "INT64"),
    # Like counts — same intervals as views
    SchemaField("likes_1h", "INT64"),
    SchemaField("likes_2h", "INT64"),
    SchemaField("likes_3h", "INT64"),
    SchemaField("likes_4h", "INT64"),
    SchemaField("likes_6h", "INT64"),
    SchemaField("likes_8h", "INT64"),
    SchemaField("likes_10h", "INT64"),
    SchemaField("likes_12h", "INT64"),
    SchemaField("likes_14h", "INT64"),
    SchemaField("likes_16h", "INT64"),
    SchemaField("likes_18h", "INT64"),
    SchemaField("likes_20h", "INT64"),
    SchemaField("likes_22h", "INT64"),
    SchemaField("likes_24h", "INT64"),
    SchemaField("likes_36h", "INT64"),
    SchemaField("likes_48h", "INT64"),
    SchemaField("likes_72h", "INT64"),
    # Comment counts — same intervals as views and likes
    SchemaField("comments_1h", "INT64"),
    SchemaField("comments_2h", "INT64"),
    SchemaField("comments_3h", "INT64"),
    SchemaField("comments_4h", "INT64"),
    SchemaField("comments_6h", "INT64"),
    SchemaField("comments_8h", "INT64"),
    SchemaField("comments_10h", "INT64"),
    SchemaField("comments_12h", "INT64"),
    SchemaField("comments_14h", "INT64"),
    SchemaField("comments_16h", "INT64"),
    SchemaField("comments_18h", "INT64"),
    SchemaField("comments_20h", "INT64"),
    SchemaField("comments_22h", "INT64"),
    SchemaField("comments_24h", "INT64"),
    SchemaField("comments_36h", "INT64"),
    SchemaField("comments_48h", "INT64"),
    SchemaField("comments_72h", "INT64"),
    # View velocity (views/hour) — one per interval
    SchemaField("view_velocity_1h", "FLOAT64"),
    SchemaField("view_velocity_2h", "FLOAT64"),
    SchemaField("view_velocity_3h", "FLOAT64"),
    SchemaField("view_velocity_4h", "FLOAT64"),
    SchemaField("view_velocity_6h", "FLOAT64"),
    SchemaField("view_velocity_8h", "FLOAT64"),
    SchemaField("view_velocity_10h", "FLOAT64"),
    SchemaField("view_velocity_12h", "FLOAT64"),
    SchemaField("view_velocity_14h", "FLOAT64"),
    SchemaField("view_velocity_16h", "FLOAT64"),
    SchemaField("view_velocity_18h", "FLOAT64"),
    SchemaField("view_velocity_20h", "FLOAT64"),
    SchemaField("view_velocity_22h", "FLOAT64"),
    SchemaField("view_velocity_24h", "FLOAT64"),
    SchemaField("view_velocity_36h", "FLOAT64"),
    SchemaField("view_velocity_48h", "FLOAT64"),
    SchemaField("view_velocity_72h", "FLOAT64"),
    # Engagement velocities and derived metrics
    SchemaField("like_velocity_1h", "FLOAT64"),
    SchemaField("comment_velocity_1h", "FLOAT64"),
    SchemaField("peak_velocity", "FLOAT64"),
    SchemaField("engagement_acceleration", "FLOAT64"),
    SchemaField("like_view_ratio", "FLOAT64"),
    SchemaField("comment_view_ratio", "FLOAT64"),
    SchemaField("performance_vs_channel_avg", "FLOAT64"),
]

ML_FEATURE_VIDEO_CONTENT = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("computed_at", "TIMESTAMP"),
    SchemaField("computed_date", "DATE"),
    SchemaField("title_length", "INT64"),
    SchemaField("title_word_count", "INT64"),
    SchemaField("title_has_emoji", "BOOL"),
    SchemaField("title_has_number", "BOOL"),
    SchemaField("title_has_question", "BOOL"),
    SchemaField("title_has_brackets", "BOOL"),
    SchemaField("title_caps_ratio", "FLOAT64"),
    SchemaField("title_power_word_count", "INT64"),
    SchemaField("title_sentiment", "FLOAT64"),
    SchemaField("title_clickbait_score", "FLOAT64"),
    SchemaField("description_length", "INT64"),
    SchemaField("description_link_count", "INT64"),
    SchemaField("tag_count", "INT64"),
    SchemaField("topic_count", "INT64"),
    SchemaField("duration_bucket", "STRING"),
]

ML_FEATURE_TEMPORAL = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("computed_at", "TIMESTAMP"),
    SchemaField("hour_of_day_published", "INT64"),
    SchemaField("day_of_week_published", "INT64"),
    SchemaField("is_weekend_publish", "BOOL"),
    SchemaField("is_holiday_publish", "BOOL"),
    SchemaField("days_since_last_upload", "INT64"),
    SchemaField("videos_published_same_day_channel", "INT64"),
]

ML_FEATURE_CHANNEL = [
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("computed_at", "TIMESTAMP"),
    SchemaField("computed_date", "DATE"),
    SchemaField("subscriber_tier", "STRING"),
    SchemaField("channel_age_days", "INT64"),
    SchemaField("upload_frequency_7d", "FLOAT64"),
    SchemaField("upload_frequency_30d", "FLOAT64"),
    SchemaField("avg_views_per_video_30d", "INT64"),
    SchemaField("avg_engagement_rate_30d", "FLOAT64"),
    SchemaField("subscriber_growth_rate_30d", "FLOAT64"),
    SchemaField("view_consistency_score", "FLOAT64"),
    SchemaField("avg_video_duration_30d", "INT64"),
    SchemaField("channel_momentum_score", "FLOAT64"),
    SchemaField("avg_time_between_uploads_7d", "FLOAT64"),
]

ML_FEATURE_COMMENT_AGGREGATES = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("computed_at", "TIMESTAMP"),
    SchemaField("computed_date", "DATE"),
    SchemaField("sample_strategy", "STRING"),
    SchemaField("comments_sampled", "INT64"),
    SchemaField("avg_sentiment_compound", "FLOAT64"),
    SchemaField("positive_ratio", "FLOAT64"),
    SchemaField("negative_ratio", "FLOAT64"),
    SchemaField("avg_toxicity", "FLOAT64"),
    SchemaField("avg_severe_toxicity", "FLOAT64"),
    SchemaField("avg_insult", "FLOAT64"),
    SchemaField("avg_identity_attack", "FLOAT64"),
    SchemaField("toxic_ratio", "FLOAT64"),
    SchemaField("severe_toxic_ratio", "FLOAT64"),
    SchemaField("insult_ratio", "FLOAT64"),
    SchemaField("identity_attack_ratio", "FLOAT64"),
    SchemaField("max_toxicity", "FLOAT64"),
    SchemaField("max_identity_attack", "FLOAT64"),
    SchemaField("avg_comment_likes", "FLOAT64"),
    SchemaField("max_comment_likes", "INT64"),
    SchemaField("avg_reply_count", "FLOAT64"),
    SchemaField("comment_language_entropy", "FLOAT64"),
    SchemaField("unique_commenter_ratio", "FLOAT64"),
    SchemaField("avg_comment_length", "FLOAT64"),
    SchemaField("question_comment_ratio", "FLOAT64"),
    SchemaField("creator_reply_count", "INT64"),
]

# ---------------------------------------------------------------------------
# Marts
# ---------------------------------------------------------------------------

MART_VIDEO_SUMMARY = [
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("published_at", "TIMESTAMP"),
    SchemaField("category_id", "INT64"),
    SchemaField("final_view_count", "INT64"),
    SchemaField("final_like_count", "INT64"),
    SchemaField("final_comment_count", "INT64"),
    SchemaField("peak_view_velocity", "FLOAT64"),
    SchemaField("hours_to_50pct_views", "INT64"),
    SchemaField("engagement_rate", "FLOAT64"),
    SchemaField("virality_label", "STRING"),
    SchemaField("avg_sentiment_compound", "FLOAT64"),
    SchemaField("avg_toxicity", "FLOAT64"),
    SchemaField("last_updated_at", "TIMESTAMP"),
]

MART_CHANNEL_DAILY = [
    SchemaField("channel_id", "STRING", mode="REQUIRED"),
    SchemaField("snapshot_date", "DATE", mode="REQUIRED"),
    SchemaField("subscriber_count", "INT64"),
    SchemaField("subscriber_change", "INT64"),
    SchemaField("total_views_today", "INT64"),
    SchemaField("videos_published_today", "INT64"),
    SchemaField("avg_engagement_rate", "FLOAT64"),
    SchemaField("top_video_id", "STRING"),
]

# ---------------------------------------------------------------------------
# MLOps
# ---------------------------------------------------------------------------

ML_MODEL_REGISTRY = [
    SchemaField("model_id", "STRING", mode="REQUIRED"),
    SchemaField("model_name", "STRING"),
    SchemaField("model_version", "INT64"),
    SchemaField("framework", "STRING"),
    SchemaField("artifact_gcs_uri", "STRING"),
    SchemaField("feature_set", "STRING", mode="REPEATED"),
    SchemaField("training_date", "TIMESTAMP"),
    SchemaField("training_rows", "INT64"),
    SchemaField("metrics", "JSON"),
    SchemaField("status", "STRING"),
    SchemaField("promoted_at", "TIMESTAMP"),
]

ML_PREDICTION_LOG = [
    SchemaField("prediction_id", "STRING", mode="REQUIRED"),
    SchemaField("model_id", "STRING", mode="REQUIRED"),
    SchemaField("video_id", "STRING", mode="REQUIRED"),
    SchemaField("predicted_at", "TIMESTAMP"),
    SchemaField("prediction_date", "DATE"),
    SchemaField("prediction_type", "STRING"),
    SchemaField("predicted_value", "FLOAT64"),
    SchemaField("predicted_class", "STRING"),
    SchemaField("prediction_confidence", "FLOAT64"),
    SchemaField("features_snapshot", "JSON"),
    SchemaField("actual_value", "FLOAT64"),
    SchemaField("absolute_error", "FLOAT64"),
]

ML_EXPERIMENT_LOG = [
    SchemaField("experiment_id", "STRING", mode="REQUIRED"),
    SchemaField("experiment_name", "STRING"),
    SchemaField("hypothesis", "STRING"),
    SchemaField("model_a_id", "STRING"),
    SchemaField("model_b_id", "STRING"),
    SchemaField("start_date", "DATE"),
    SchemaField("end_date", "DATE"),
    SchemaField("sample_size", "INT64"),
    SchemaField("result_summary", "JSON"),
    SchemaField("winner", "STRING"),
]

# ---------------------------------------------------------------------------
# Operational
# ---------------------------------------------------------------------------

PIPELINE_RUN_LOG = [
    SchemaField("run_id", "STRING", mode="REQUIRED"),
    SchemaField("pipeline_name", "STRING"),
    SchemaField("target_table", "STRING"),
    SchemaField("started_at", "TIMESTAMP"),
    SchemaField("finished_at", "TIMESTAMP"),
    SchemaField("status", "STRING"),
    SchemaField("rows_affected", "INT64"),
    SchemaField("error_message", "STRING"),
    SchemaField("run_date", "DATE"),
]

DATA_QUALITY_RESULTS = [
    SchemaField("check_id", "STRING", mode="REQUIRED"),
    SchemaField("table_name", "STRING"),
    SchemaField("check_name", "STRING"),
    SchemaField("check_type", "STRING"),
    SchemaField("passed", "BOOL"),
    SchemaField("actual_value", "FLOAT64"),
    SchemaField("expected_value", "FLOAT64"),
    SchemaField("checked_at", "TIMESTAMP"),
    SchemaField("check_date", "DATE"),
]

# ---------------------------------------------------------------------------
# Registry — maps table name -> (schema, partition_field, clustering_fields)
# Used by bootstrap_tables.py to create all tables idempotently.
# ---------------------------------------------------------------------------

TABLE_REGISTRY: dict[str, tuple[list[SchemaField], str | None, list[str] | None]] = {
    "tracked_channels": (TRACKED_CHANNELS, None, ["channel_id"]),
    "dim_channel": (DIM_CHANNEL, None, ["channel_id"]),
    "dim_video": (DIM_VIDEO, None, ["channel_id", "video_id"]),
    "dim_category": (DIM_CATEGORY, None, None),
    "dim_date": (DIM_DATE, None, None),
    "dim_video_transcript": (DIM_VIDEO_TRANSCRIPT, None, None),
    "video_monitoring": (VIDEO_MONITORING, None, ["channel_id"]),
    "fact_channel_snapshot": (FACT_CHANNEL_SNAPSHOT, "snapshot_date", ["channel_id"]),
    "fact_video_snapshot": (FACT_VIDEO_SNAPSHOT, "snapshot_date", ["video_id", "channel_id"]),
    "fact_comment": (FACT_COMMENT, "pull_date", ["video_id", "channel_id"]),
    "ml_feature_video_performance": (ML_FEATURE_VIDEO_PERFORMANCE, "computed_date", ["video_id"]),
    "ml_feature_video_content": (ML_FEATURE_VIDEO_CONTENT, "computed_date", ["video_id"]),
    "ml_feature_temporal": (ML_FEATURE_TEMPORAL, None, ["video_id"]),
    "ml_feature_channel": (ML_FEATURE_CHANNEL, "computed_date", ["channel_id"]),
    "ml_feature_comment_aggregates": (
        ML_FEATURE_COMMENT_AGGREGATES,
        "computed_date",
        ["video_id"],
    ),
    "mart_video_summary": (MART_VIDEO_SUMMARY, None, ["video_id", "channel_id"]),
    "mart_channel_daily": (MART_CHANNEL_DAILY, "snapshot_date", ["channel_id"]),
    "ml_model_registry": (ML_MODEL_REGISTRY, None, None),
    "ml_prediction_log": (ML_PREDICTION_LOG, "prediction_date", ["video_id", "model_id"]),
    "ml_experiment_log": (ML_EXPERIMENT_LOG, None, None),
    "pipeline_run_log": (PIPELINE_RUN_LOG, "run_date", None),
    "data_quality_results": (DATA_QUALITY_RESULTS, "check_date", None),
}
