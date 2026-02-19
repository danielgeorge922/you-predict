# You Predict - Data Model

**Dataset:** `you_predict_warehouse` (US region)

See `CLAUDE.md` for repo structure, deployment architecture, and code conventions.

---

## Architecture Overview

```
GCS (Raw JSON blobs)                      →  BigQuery (everything else)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Raw Layer (bronze)                           Dim/Fact Layer (transformed from GCS)
├─ channel_metadata/                         ├─ dim_channel
├─ video_metadata/                           ├─ dim_video
├─ video_snapshot_stats/                     ├─ dim_category
├─ channel_snapshot_stats/                   ├─ dim_date
├─ video_comments/                           ├─ dim_video_transcript (optional)
└─ video_transcripts/                        ├─ tracked_channels (seeded)
                                             ├─ video_monitoring
                                             ├─ fact_video_snapshot
                                             ├─ fact_channel_snapshot
                                             └─ fact_comment

                                             Feature Layer (derived from dim/fact via SQL)
                                             ├─ ml_feature_video_performance
                                             ├─ ml_feature_video_content
                                             ├─ ml_feature_temporal
                                             ├─ ml_feature_channel
                                             └─ ml_feature_comment_aggregates

                                             Mart Layer (derived from features + facts via SQL)
                                             ├─ mart_video_summary
                                             └─ mart_channel_daily

                                             MLOps Layer (written by ML pipelines)
                                             ├─ ml_model_registry
                                             ├─ ml_prediction_log
                                             └─ ml_experiment_log

                                             Operational Layer (written by orchestrator/DQ)
                                             ├─ pipeline_run_log
                                             └─ data_quality_results
```

**Idempotency guarantee:** GCS raw blobs are the source of truth. Raw data is ALWAYS persisted to GCS before any downstream processing begins. Everything in BigQuery from dim/fact onward is recomputable by replaying the raw data. If a transform fails, the raw data is still safe.

**No SCD2.** Dimensions are current-state only (daily full refresh). If historical dimension state is ever needed, replay from GCS raw JSON snapshots.

---

## How Data Enters the System

Three mechanisms drive data into the GCS raw layer:

**1. PubSubHubbub Webhook (event-driven)**
YouTube pushes Atom XML notifications to our Cloud Run webhook when a tracked channel uploads a new video. On receiving a notification, we write to `video_monitoring` and enqueue Cloud Tasks for the snapshot fan-out schedule.

**2. Cloud Tasks Fan-out (delayed, event-driven)**
When a new video is discovered, Cloud Tasks are enqueued with staggered delivery times for each snapshot interval. Each task fetches data from the YouTube API and writes raw JSON to GCS before any transformation.

- Snapshot polls: 1, 2, 4, 6, 8, 12, 16, 20, 24, 36, 48, 72 hours after publish
- Comment pulls: 24, 72 hours after publish
- Transcript fetch: ~24 hours after publish

**3. Cloud Scheduler → Cloud Run pipeline endpoints (scheduled)**
Daily pipelines for channel refreshes, video metadata refreshes, feature computation, mart rollups, and data quality checks. Cloud Scheduler sends HTTP POST to Cloud Run on a cron. Each pipeline writes raw data to GCS first, then triggers transforms.

---

## Raw Layer (GCS)

**Bucket:** `gs://you-predict-raw/`

| Prefix | Contents | Naming Convention | Frequency |
|--------|----------|-------------------|-----------|
| `channel_metadata/{channel_id}/` | Full `channels.list` API JSON (snippet, brandingSettings, topicDetails, statistics) | `{channel_id}_{iso_timestamp}.json` | Daily via Cloud Scheduler pipeline (all tracked channels) |
| `video_metadata/{video_id}/` | Full `videos.list` API JSON (snippet, contentDetails, status, topicDetails) | `{video_id}_{iso_timestamp}.json` | Daily at 12:00 UTC via Cloud Scheduler pipeline (all active videos) |
| `video_snapshot_stats/{date}/` | `videos.list` statistics-only responses (snapshot polls) | `{video_id}_{iso_timestamp}.json` | Cloud Tasks fan-out: 1, 2, 4, 6, 8, 12, 16, 20, 24, 36, 48, 72 hours after publish |
| `channel_snapshot_stats/{date}/` | `channels.list` statistics-only responses | `{channel_id}_{iso_timestamp}.json` | Daily via Cloud Scheduler pipeline (same pass as channel_metadata/) |
| `video_comments/{video_id}/` | `commentThreads.list` API JSON | `{video_id}_{iso_timestamp}_{page}.json` | Cloud Tasks: 2 pulls per video at 24 and 72 hours after publish |
| `video_transcripts/{video_id}/` | Raw transcript text via `youtube-transcript-api` | `{video_id}_{language}.txt` | Cloud Tasks: once per video, ~24 hours after publish |

**Properties:**
- Append-only — never overwrite, never delete
- Partitioned by date in path where applicable
- Full JSON preserved — if YouTube adds a field, it's already captured
- `channel_metadata/` and `channel_snapshot_stats/` come from the same API call; transform layer splits them
- Raw data is ALWAYS written to GCS before any downstream processing — this is the bronze layer and the basis for idempotent reprocessing

---

## Dim/Fact Layer

### `dim_channel`

Current-state channel metadata. Daily full refresh from `gs://you-predict-raw/channel_metadata/`.

| Column | Type | Notes |
|---|---|---|
| `channel_id` | `STRING NOT NULL` | YouTube channel ID (natural key) |
| `channel_name` | `STRING` | |
| `channel_description` | `STRING` | For NLP/topic modeling |
| `custom_url` | `STRING` | The @handle |
| `channel_thumbnail_url` | `STRING` | |
| `channel_created_at` | `TIMESTAMP` | Channel creation date (channel age feature) |
| `made_for_kids` | `BOOL` | |
| `hidden_subscriber_count` | `BOOL` | Channels hiding subs behave differently |
| `channel_keywords` | `STRING` | From brandingSettings |
| `uploads_playlist_id` | `STRING` | For efficient video listing via API |
| `topics` | `ARRAY<STRING>` | |
| `topic_ids` | `ARRAY<STRING>` | |
| `updated_at` | `TIMESTAMP` | When this row was last refreshed |

**Clustering:** `channel_id`
**Write pattern:** MERGE on `channel_id`. If matched, UPDATE all fields; if not matched, INSERT. Avoids the risk of an empty table if a DELETE+INSERT refresh fails partway through. Daily.

---

### `dim_video`

Current-state video metadata. Daily full refresh from `gs://you-predict-raw/video_metadata/`.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | YouTube video ID (natural key) |
| `channel_id` | `STRING NOT NULL` | Owning channel |
| `title` | `STRING` | |
| `description` | `STRING` | |
| `published_at` | `TIMESTAMP` | |
| `thumbnail_url` | `STRING` | |
| `duration_seconds` | `INT64` | |
| `category_id` | `INT64` | FK to `dim_category` |
| `is_livestream` | `BOOL` | |
| `is_age_restricted` | `BOOL` | |
| `made_for_kids` | `BOOL` | |
| `has_custom_thumbnail` | `BOOL` | Strong correlation with performance |
| `definition` | `STRING` | HD / SD |
| `caption_available` | `BOOL` | Accessibility + discoverability signal |
| `licensed_content` | `BOOL` | Music/media licensing flag |
| `has_paid_promotion` | `BOOL` | Sponsored content flag |
| `tags` | `ARRAY<STRING>` | |
| `topics` | `ARRAY<STRING>` | |
| `first_seen_at` | `TIMESTAMP` | |
| `updated_at` | `TIMESTAMP` | When this row was last refreshed |

**Clustering:** `channel_id`, `video_id`
**Write pattern:** MERGE on `video_id`. If matched, UPDATE all fields; if not matched, INSERT. Avoids the risk of an empty table if a DELETE+INSERT refresh fails partway through. Daily at 12:00 UTC.

---

### `dim_category`

YouTube's ~30 video categories. Seeded once, rarely changes.

| Column | Type | Notes |
|---|---|---|
| `category_id` | `INT64 NOT NULL` | YouTube category ID |
| `category_name` | `STRING` | e.g. "Entertainment", "Gaming" |

**Write pattern:** Seed once. Rare refresh.

---

### `dim_date`

Static date dimension pre-populated for 2026-2028.

| Column | Type | Notes |
|---|---|---|
| `date_key` | `INT64` | `YYYYMMDD` integer key |
| `full_date` | `DATE` | |
| `year` | `INT64` | |
| `quarter` | `INT64` | |
| `month` | `INT64` | |
| `month_name` | `STRING` | e.g. "January" |
| `week_of_year` | `INT64` | |
| `day_of_month` | `INT64` | |
| `day_of_week` | `INT64` | 1 = Sunday, 7 = Saturday |
| `day_name` | `STRING` | e.g. "Monday" |
| `is_weekend` | `BOOL` | |
| `is_us_holiday` | `BOOL` | YouTube traffic is heavily seasonal |
| `season` | `STRING` | e.g. "winter_break", "summer", "back_to_school" |

**Write pattern:** Seed once.

---

### `dim_video_transcript` (optional enrichment)

Derived transcript features. Raw text lives in GCS. App works without this table.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `transcript_source` | `STRING` | "auto_generated" / "manual" / "community" |
| `gcs_uri` | `STRING` | Pointer to raw text in GCS |
| `word_count` | `INT64` | Derived |
| `fetched_at` | `TIMESTAMP` | |
| `topic_keywords` | `ARRAY<STRING>` | Extracted via NLP |
| `readability_score` | `FLOAT64` | Flesch-Kincaid or similar |
| `has_profanity` | `BOOL` | |

**Write pattern:** MERGE on `video_id`. Handles Cloud Tasks redelivery. Uses `youtube-transcript-api` (no API quota cost). All downstream features gate on availability.

---

## Tracking

### `tracked_channels`

Authoritative list of channels the system monitors. Seeded once via `seed_tracked_channels.py`. Read by `daily-channel-refresh` and `subscribe_channels.py`.

| Column | Type | Notes |
|---|---|---|
| `channel_id` | `STRING NOT NULL` | YouTube channel ID |
| `added_at` | `TIMESTAMP NOT NULL` | When we started tracking |
| `is_active` | `BOOL NOT NULL` | Set to FALSE to stop tracking without deleting |
| `notes` | `STRING` | Optional label (e.g. "tech news", "gaming") |

**Clustering:** `channel_id`
**Write pattern:** MERGE on `channel_id`. Seed once; re-run to add channels or toggle `is_active`.

---

### `video_monitoring`

Tracks which videos are actively being polled for snapshots.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `channel_id` | `STRING NOT NULL` | |
| `published_at` | `TIMESTAMP` | |
| `discovered_at` | `TIMESTAMP` | |
| `monitoring_until` | `TIMESTAMP` | |
| `first_seen_at` | `TIMESTAMP` | |
| `is_active` | `BOOL` | |
| `inactive_reason` | `STRING` | Values: "monitoring_window_expired", "video_deleted", "video_privated", "manual_stop" |

**Clustering:** `channel_id`, `is_active`
**Write pattern:** UPSERT. Written by ingestion pipeline on video discovery, updated when monitoring ends.

---

## Facts

### `fact_channel_snapshot`

Daily channel-level metrics with deltas. Transformed from `gs://you-predict-raw/channel_snapshot_stats/`.

| Column | Type | Notes |
|---|---|---|
| `snapshot_id` | `INT64 NOT NULL` | Auto-increment |
| `snapshot_date` | `DATE NOT NULL` | Partition key |
| `snapshot_ts` | `TIMESTAMP NOT NULL` | Exact snapshot time |
| `channel_id` | `STRING NOT NULL` | |
| `view_count` | `INT64` | Total channel views |
| `subscriber_count` | `INT64` | |
| `video_count` | `INT64` | |
| `views_delta` | `INT64` | Change since last snapshot |
| `subs_delta` | `INT64` | Change since last snapshot |
| `videos_delta` | `INT64` | Change since last snapshot |

**Partitioned by:** `snapshot_date`
**Clustering:** `channel_id`
**Write pattern:** INSERT (append-only). Daily.

---

### `fact_video_snapshot`

Video-level metric snapshots with deltas and age tracking. Transformed from `gs://you-predict-raw/video_snapshot_stats/`.

| Column | Type | Notes |
|---|---|---|
| `snapshot_id` | `INT64 NOT NULL` | Auto-increment |
| `snapshot_date` | `DATE NOT NULL` | Partition key |
| `snapshot_ts` | `TIMESTAMP NOT NULL` | Scheduled snapshot time |
| `actual_captured_at` | `TIMESTAMP NOT NULL` | When the YouTube API was actually called (Cloud Tasks delivery may drift from schedule) |
| `snapshot_type` | `STRING` | e.g. "1h", "2h", "4h", "24h" |
| `video_id` | `STRING NOT NULL` | |
| `channel_id` | `STRING NOT NULL` | |
| `view_count` | `INT64` | |
| `like_count` | `INT64` | |
| `comment_count` | `INT64` | |
| `views_delta` | `INT64` | Change since last snapshot |
| `likes_delta` | `INT64` | Change since last snapshot |
| `comments_delta` | `INT64` | Change since last snapshot |
| `hours_since_publish` | `INT64` | Nominal video age at snapshot (from snapshot_type) |
| `actual_hours_since_publish` | `FLOAT64` | Actual video age based on `actual_captured_at - published_at`. Use this for ML features — more accurate than nominal interval. |
| `days_since_publish` | `INT64` | Video age at snapshot |

**Partitioned by:** `snapshot_date`
**Clustering:** `video_id`, `channel_id`
**Write pattern:** MERGE on `(video_id, snapshot_type)`. Handles Cloud Tasks at-least-once delivery — if the same snapshot fires twice, the row is updated instead of duplicated. 12 snapshots per video lifecycle (1h, 2h, 4h, 6h, 8h, 12h, 16h, 20h, 24h, 36h, 48h, 72h).

---

### `fact_comment`

Individual comments with sentiment and toxicity analysis. Transformed from `gs://you-predict-raw/video_comments/`.

`channel_id` is an intentional denormalization (derivable via dim_video) kept for BigQuery scan reduction.

| Column | Type | Notes |
|---|---|---|
| `comment_id` | `STRING NOT NULL` | Dedup key |
| `video_id` | `STRING NOT NULL` | |
| `channel_id` | `STRING NOT NULL` | Video's channel (intentional denorm) |
| `parent_comment_id` | `STRING` | NULL for top-level comments |
| `is_reply` | `BOOL` | Top-level vs reply distinction |
| `commenter_channel_id` | `STRING` | Who commented |
| `commenter_name` | `STRING` | |
| `comment_text` | `STRING` | |
| `like_count` | `INT64` | Comment likes |
| `reply_count` | `INT64` | |
| `published_at` | `TIMESTAMP` | |
| `updated_at` | `TIMESTAMP` | Edited comments signal controversy |
| `pulled_at` | `TIMESTAMP` | When we fetched it |
| `pull_date` | `DATE` | Partition key |
| `sample_strategy` | `STRING` | Sampling method used |
| `sample_rank` | `INT64` | Rank within sample |
| `sentiment_positive` | `FLOAT64` | |
| `sentiment_negative` | `FLOAT64` | |
| `sentiment_neutral` | `FLOAT64` | |
| `sentiment_compound` | `FLOAT64` | |
| `toxicity_score` | `FLOAT64` | |
| `severe_toxicity_score` | `FLOAT64` | |
| `insult_score` | `FLOAT64` | |
| `identity_attack_score` | `FLOAT64` | |

**Partitioned by:** `pull_date`
**Clustering:** `video_id`, `channel_id`
**Write pattern:** MERGE on `comment_id`. Handles duplicate pulls and Cloud Tasks redelivery — if the same comment is pulled twice, the row is updated with latest data. 2 pulls per video (24h, 72h).

---

## Feature Layer

All feature tables are **derived from dim/fact tables via SQL**. No external data ingestion.

### `ml_feature_video_performance`

Pre-computed performance features for ML. Derived from `fact_video_snapshot` + `ml_feature_channel`.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `computed_at` | `TIMESTAMP` | |
| `computed_date` | `DATE` | Partition key |
| `views_1h` | `INT64` | Views at 1 hour |
| `views_2h` | `INT64` | Views at 2 hours |
| `views_4h` | `INT64` | Views at 4 hours |
| `views_6h` | `INT64` | Views at 6 hours |
| `views_8h` | `INT64` | Views at 8 hours |
| `views_12h` | `INT64` | Views at 12 hours |
| `views_16h` | `INT64` | Views at 16 hours |
| `views_20h` | `INT64` | Views at 20 hours |
| `views_24h` | `INT64` | Views at 24 hours |
| `views_36h` | `INT64` | Views at 36 hours |
| `views_48h` | `INT64` | Views at 48 hours |
| `views_72h` | `INT64` | Views at 72 hours |
| `likes_1h` | `INT64` | Likes at 1 hour |
| `likes_24h` | `INT64` | Likes at 24 hours |
| `comments_1h` | `INT64` | Comments at 1 hour |
| `comments_24h` | `INT64` | Comments at 24 hours |
| `view_velocity_1h` | `FLOAT64` | Views per hour (first hour) |
| `view_velocity_24h` | `FLOAT64` | Views per hour (first 24h) |
| `like_velocity_1h` | `FLOAT64` | Likes per hour (first hour) |
| `comment_velocity_1h` | `FLOAT64` | Comments per hour (first hour) |
| `peak_velocity` | `FLOAT64` | Max views per hour across all intervals |
| `engagement_acceleration` | `FLOAT64` | Is velocity increasing or decreasing (2nd derivative) |
| `hours_to_10k_views` | `INT64` | |
| `like_view_ratio` | `FLOAT64` | |
| `comment_view_ratio` | `FLOAT64` | |
| `performance_vs_channel_avg` | `FLOAT64` | Ratio vs channel avg (from ml_feature_channel) |

**Partitioned by:** `computed_date`
**Clustering:** `video_id`
**Write pattern:** MERGE. Recomputed as new snapshots arrive.

---

### `ml_feature_video_content`

Pre-computed content/metadata features. Derived from `dim_video`.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `computed_at` | `TIMESTAMP` | |
| `computed_date` | `DATE` | Partition key |
| `title_length` | `INT64` | Character count |
| `title_word_count` | `INT64` | |
| `title_has_emoji` | `BOOL` | |
| `title_has_number` | `BOOL` | |
| `title_has_question` | `BOOL` | "?" drives curiosity clicks |
| `title_has_brackets` | `BOOL` | "[GONE WRONG]" pattern |
| `title_caps_ratio` | `FLOAT64` | Clickbait signal |
| `title_power_word_count` | `INT64` | Words like "INSANE", "SECRET" |
| `title_sentiment` | `FLOAT64` | |
| `title_clickbait_score` | `FLOAT64` | Trained classifier output |
| `description_length` | `INT64` | Character count |
| `description_link_count` | `INT64` | |
| `tag_count` | `INT64` | |
| `topic_count` | `INT64` | |
| `duration_bucket` | `STRING` | e.g. "short", "medium", "long" |

**Partitioned by:** `computed_date`
**Clustering:** `video_id`
**Write pattern:** INSERT once per video. Recompute if dim_video changes.

---

### `ml_feature_temporal`

Publishing time features per video. Derived from `dim_video` + `dim_date` + channel upload history.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `computed_at` | `TIMESTAMP` | |
| `hour_of_day_published` | `INT64` | 0-23 UTC |
| `day_of_week_published` | `INT64` | 1=Sun, 7=Sat |
| `is_weekend_publish` | `BOOL` | |
| `is_holiday_publish` | `BOOL` | |
| `days_since_last_upload` | `INT64` | Channel cadence signal |
| `videos_published_same_day_channel` | `INT64` | Multi-upload detection |

**Clustering:** `video_id`
**Write pattern:** INSERT once at video discovery.

---

### `ml_feature_channel`

Channel-level features for ML. Derived from `dim_channel` + `fact_channel_snapshot` + `fact_video_snapshot`.

| Column | Type | Notes |
|---|---|---|
| `channel_id` | `STRING NOT NULL` | |
| `computed_at` | `TIMESTAMP` | |
| `computed_date` | `DATE` | Partition key |
| `subscriber_tier` | `STRING` | "micro" (<10K), "small" (<100K), "medium" (<1M), "large" (1M+) |
| `channel_age_days` | `INT64` | |
| `upload_frequency_7d` | `FLOAT64` | Videos per week |
| `upload_frequency_30d` | `FLOAT64` | Videos per month |
| `avg_views_per_video_30d` | `INT64` | Channel baseline |
| `avg_engagement_rate_30d` | `FLOAT64` | (likes+comments)/views |
| `subscriber_growth_rate_30d` | `FLOAT64` | % change |
| `view_consistency_score` | `FLOAT64` | stddev/mean of recent video views |
| `avg_video_duration_30d` | `INT64` | Seconds |
| `channel_momentum_score` | `FLOAT64` | Are recent videos trending up or down |
| `avg_time_between_uploads_7d` | `FLOAT64` | Cadence regularity |

**Partitioned by:** `computed_date`
**Clustering:** `channel_id`
**Write pattern:** MERGE. Recomputed daily.

---

### `ml_feature_comment_aggregates`

Aggregated comment sentiment/toxicity per video. Derived from `fact_comment`.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `computed_at` | `TIMESTAMP` | |
| `computed_date` | `DATE` | Partition key |
| `sample_strategy` | `STRING` | |
| `comments_sampled` | `INT64` | |
| `avg_sentiment_compound` | `FLOAT64` | |
| `positive_ratio` | `FLOAT64` | |
| `negative_ratio` | `FLOAT64` | |
| `avg_toxicity` | `FLOAT64` | |
| `avg_severe_toxicity` | `FLOAT64` | |
| `avg_insult` | `FLOAT64` | |
| `avg_identity_attack` | `FLOAT64` | |
| `toxic_ratio` | `FLOAT64` | Fraction above toxicity threshold |
| `severe_toxic_ratio` | `FLOAT64` | |
| `insult_ratio` | `FLOAT64` | |
| `identity_attack_ratio` | `FLOAT64` | |
| `max_toxicity` | `FLOAT64` | |
| `max_identity_attack` | `FLOAT64` | |
| `avg_comment_likes` | `FLOAT64` | |
| `max_comment_likes` | `INT64` | |
| `avg_reply_count` | `FLOAT64` | |
| `comment_language_entropy` | `FLOAT64` | Language diversity = international reach |
| `unique_commenter_ratio` | `FLOAT64` | Unique commenters / total (bot detection) |
| `avg_comment_length` | `FLOAT64` | Engagement depth |
| `question_comment_ratio` | `FLOAT64` | Audience curiosity signal |
| `creator_reply_count` | `INT64` | Creator engagement |

**Partitioned by:** `computed_date`
**Clustering:** `video_id`
**Write pattern:** MERGE. Recomputed as new comment pulls arrive.

---

## Mart Layer

All marts are **derived from feature + fact tables via SQL**. No external data ingestion.

### `mart_video_summary`

One row per video with final/latest stats. Powers DS analysis.

| Column | Type | Notes |
|---|---|---|
| `video_id` | `STRING NOT NULL` | |
| `channel_id` | `STRING NOT NULL` | |
| `published_at` | `TIMESTAMP` | |
| `category_id` | `INT64` | |
| `final_view_count` | `INT64` | Latest snapshot |
| `final_like_count` | `INT64` | |
| `final_comment_count` | `INT64` | |
| `peak_view_velocity` | `FLOAT64` | Max views/hour |
| `hours_to_50pct_views` | `INT64` | How fast it plateaus |
| `engagement_rate` | `FLOAT64` | (likes+comments)/views |
| `virality_label` | `STRING` | "viral" / "above_avg" / "normal" / "below_avg" |
| `avg_sentiment_compound` | `FLOAT64` | From comment aggregates |
| `avg_toxicity` | `FLOAT64` | |
| `last_updated_at` | `TIMESTAMP` | |

**Clustering:** `video_id`, `channel_id`
**Write pattern:** MERGE. Recomputed as snapshots accumulate.

---

### `mart_channel_daily`

Daily channel rollup. Powers dashboard.

| Column | Type | Notes |
|---|---|---|
| `channel_id` | `STRING NOT NULL` | |
| `snapshot_date` | `DATE NOT NULL` | Partition key |
| `subscriber_count` | `INT64` | |
| `subscriber_change` | `INT64` | |
| `total_views_today` | `INT64` | Sum of views_delta across channel's videos |
| `videos_published_today` | `INT64` | |
| `avg_engagement_rate` | `FLOAT64` | |
| `top_video_id` | `STRING` | Best performing video of the day |

**Partitioned by:** `snapshot_date`
**Clustering:** `channel_id`
**Write pattern:** INSERT daily.

---

## MLOps Layer

Written by ML training/serving pipelines, not derived from other BQ tables.

### `ml_model_registry`

Model versioning and metadata.

| Column | Type | Notes |
|---|---|---|
| `model_id` | `STRING NOT NULL` | UUID |
| `model_name` | `STRING` | e.g. "virality_classifier_v1" |
| `model_version` | `INT64` | Auto-increment per model_name |
| `framework` | `STRING` | "xgboost", "lightgbm", "sklearn", etc. |
| `artifact_gcs_uri` | `STRING` | GCS path to model artifact |
| `feature_set` | `ARRAY<STRING>` | Which features were used |
| `training_date` | `TIMESTAMP` | |
| `training_rows` | `INT64` | |
| `metrics` | `JSON` | {"accuracy": 0.85, "rmse": 1234, ...} |
| `status` | `STRING` | "staging" / "production" / "archived" |
| `promoted_at` | `TIMESTAMP` | When moved to production |

**Write pattern:** INSERT on train, UPDATE on promote/archive.

---

### `ml_prediction_log`

Every prediction stored. Backbone of model monitoring.

| Column | Type | Notes |
|---|---|---|
| `prediction_id` | `STRING NOT NULL` | UUID |
| `model_id` | `STRING NOT NULL` | FK to ml_model_registry |
| `video_id` | `STRING NOT NULL` | |
| `predicted_at` | `TIMESTAMP` | |
| `prediction_date` | `DATE` | Partition key |
| `prediction_type` | `STRING` | "views_24h", "virality_class", etc. |
| `predicted_value` | `FLOAT64` | |
| `predicted_class` | `STRING` | For classifiers |
| `prediction_confidence` | `FLOAT64` | |
| `features_snapshot` | `JSON` | Input features at prediction time |
| `actual_value` | `FLOAT64` | Backfilled once known |
| `absolute_error` | `FLOAT64` | Backfilled |

**Partitioned by:** `prediction_date`
**Clustering:** `video_id`, `model_id`
**Write pattern:** INSERT on predict, UPDATE to backfill actuals.

---

### `ml_experiment_log`

A/B test and experiment tracking.

| Column | Type | Notes |
|---|---|---|
| `experiment_id` | `STRING NOT NULL` | |
| `experiment_name` | `STRING` | |
| `hypothesis` | `STRING` | |
| `model_a_id` | `STRING` | Challenger |
| `model_b_id` | `STRING` | Champion |
| `start_date` | `DATE` | |
| `end_date` | `DATE` | |
| `sample_size` | `INT64` | |
| `result_summary` | `JSON` | |
| `winner` | `STRING` | model_a / model_b / inconclusive |

**Write pattern:** INSERT on start, UPDATE on completion.

---

## Operational Layer

Written by orchestrator and data quality framework.

### `pipeline_run_log`

Every pipeline execution tracked.

| Column | Type | Notes |
|---|---|---|
| `run_id` | `STRING NOT NULL` | UUID |
| `pipeline_name` | `STRING` | e.g. "video_snapshot", "comment_pull" |
| `target_table` | `STRING` | |
| `started_at` | `TIMESTAMP` | |
| `finished_at` | `TIMESTAMP` | |
| `status` | `STRING` | success / failed / timeout |
| `rows_affected` | `INT64` | |
| `error_message` | `STRING` | |
| `run_date` | `DATE` | Partition key |

**Partitioned by:** `run_date`
**Write pattern:** INSERT per run.

---

### `data_quality_results`

Automated validation results.

| Column | Type | Notes |
|---|---|---|
| `check_id` | `STRING NOT NULL` | UUID |
| `table_name` | `STRING` | |
| `check_name` | `STRING` | e.g. "freshness", "null_rate_video_id" |
| `check_type` | `STRING` | freshness / row_count / null_rate / custom |
| `passed` | `BOOL` | |
| `actual_value` | `FLOAT64` | |
| `expected_value` | `FLOAT64` | |
| `checked_at` | `TIMESTAMP` | |
| `check_date` | `DATE` | Partition key |

**Partitioned by:** `check_date`
**Write pattern:** INSERT per check.
