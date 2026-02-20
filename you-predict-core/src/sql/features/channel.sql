-- Compute ml_feature_channel for all tracked active channels.
--
-- Sources: dim_channel, tracked_channels, video_monitoring, dim_video,
--          fact_channel_snapshot
-- Key:     channel_id
-- Runs:    daily, before video_performance.sql (no upstream dependencies)

MERGE `{project}.{dataset}.ml_feature_channel` AS T
USING (
  WITH

  -- Base: only currently active tracked channels
  base AS (
    SELECT dc.channel_id
    FROM `{project}.{dataset}.dim_channel` dc
    INNER JOIN `{project}.{dataset}.tracked_channels` tc
      ON dc.channel_id = tc.channel_id
    WHERE tc.is_active = TRUE
  ),

  -- Videos published in last 30 days per channel
  recent_videos AS (
    SELECT
      channel_id,
      view_count,
      like_count,
      comment_count,
      duration_seconds,
      published_at
    FROM `{project}.{dataset}.dim_video`
    WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  ),

  -- Upload counts per channel over 7 and 30 day windows
  upload_counts AS (
    SELECT
      channel_id,
      COUNTIF(published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))  AS uploads_7d,
      COUNTIF(published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)) AS uploads_30d
    FROM `{project}.{dataset}.video_monitoring`
    GROUP BY channel_id
  ),

  -- Subscriber count ~30 days ago from fact_channel_snapshot
  subs_30d_ago AS (
    SELECT DISTINCT
      channel_id,
      FIRST_VALUE(subscriber_count) OVER (
        PARTITION BY channel_id
        ORDER BY snapshot_date DESC
      ) AS sub_count
    FROM `{project}.{dataset}.fact_channel_snapshot`
    WHERE snapshot_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  ),

  -- 30-day video aggregates per channel
  video_agg AS (
    SELECT
      channel_id,
      AVG(view_count)                                                   AS avg_views_30d,
      AVG(SAFE_DIVIDE(like_count + comment_count, NULLIF(view_count, 0))) AS avg_engagement_rate_30d,
      STDDEV(view_count)                                                AS stddev_views_30d,
      AVG(duration_seconds)                                             AS avg_duration_30d
    FROM recent_videos
    GROUP BY channel_id
  )

  SELECT
    b.channel_id,
    CURRENT_TIMESTAMP()                          AS computed_at,
    DATE(CURRENT_TIMESTAMP())                    AS computed_date,

    -- Subscriber tier
    CASE
      WHEN dc.subscriber_count < 10000   THEN 'micro'
      WHEN dc.subscriber_count < 100000  THEN 'small'
      WHEN dc.subscriber_count < 1000000 THEN 'medium'
      ELSE 'large'
    END                                          AS subscriber_tier,

    -- Channel age
    DATE_DIFF(CURRENT_DATE(), DATE(dc.channel_created_at), DAY)
                                                 AS channel_age_days,

    -- Upload frequency
    SAFE_DIVIDE(uc.uploads_7d,  7.0)             AS upload_frequency_7d,
    SAFE_DIVIDE(uc.uploads_30d, 30.0)            AS upload_frequency_30d,

    -- View / engagement averages
    CAST(va.avg_views_30d AS INT64)              AS avg_views_per_video_30d,
    va.avg_engagement_rate_30d                   AS avg_engagement_rate_30d,

    -- Subscriber growth rate over 30 days
    SAFE_DIVIDE(
      dc.subscriber_count - s30.sub_count,
      NULLIF(s30.sub_count, 0)
    )                                            AS subscriber_growth_rate_30d,

    -- View consistency: 1 / (1 + CV) so higher = more consistent output
    SAFE_DIVIDE(
      1.0,
      1.0 + SAFE_DIVIDE(va.stddev_views_30d, NULLIF(va.avg_views_30d, 0))
    )                                            AS view_consistency_score,

    -- Avg video duration
    CAST(va.avg_duration_30d AS INT64)           AS avg_video_duration_30d,

    -- Composite scores — deferred until more data is available
    NULL                                         AS channel_momentum_score,
    NULL                                         AS avg_time_between_uploads_7d

  FROM base b
  INNER JOIN `{project}.{dataset}.dim_channel` dc ON b.channel_id = dc.channel_id
  LEFT  JOIN upload_counts  uc  ON b.channel_id = uc.channel_id
  LEFT  JOIN subs_30d_ago   s30 ON b.channel_id = s30.channel_id
  LEFT  JOIN video_agg      va  ON b.channel_id = va.channel_id
) AS S
ON T.channel_id = S.channel_id

WHEN MATCHED THEN UPDATE SET
  computed_at                 = S.computed_at,
  computed_date               = S.computed_date,
  subscriber_tier             = S.subscriber_tier,
  channel_age_days            = S.channel_age_days,
  upload_frequency_7d         = S.upload_frequency_7d,
  upload_frequency_30d        = S.upload_frequency_30d,
  avg_views_per_video_30d     = S.avg_views_per_video_30d,
  avg_engagement_rate_30d     = S.avg_engagement_rate_30d,
  subscriber_growth_rate_30d  = S.subscriber_growth_rate_30d,
  view_consistency_score      = S.view_consistency_score,
  avg_video_duration_30d      = S.avg_video_duration_30d,
  channel_momentum_score      = S.channel_momentum_score,
  avg_time_between_uploads_7d = S.avg_time_between_uploads_7d

WHEN NOT MATCHED THEN INSERT (
  channel_id,
  computed_at,
  computed_date,
  subscriber_tier,
  channel_age_days,
  upload_frequency_7d,
  upload_frequency_30d,
  avg_views_per_video_30d,
  avg_engagement_rate_30d,
  subscriber_growth_rate_30d,
  view_consistency_score,
  avg_video_duration_30d,
  channel_momentum_score,
  avg_time_between_uploads_7d
) VALUES (
  S.channel_id,
  S.computed_at,
  S.computed_date,
  S.subscriber_tier,
  S.channel_age_days,
  S.upload_frequency_7d,
  S.upload_frequency_30d,
  S.avg_views_per_video_30d,
  S.avg_engagement_rate_30d,
  S.subscriber_growth_rate_30d,
  S.view_consistency_score,
  S.avg_video_duration_30d,
  S.channel_momentum_score,
  S.avg_time_between_uploads_7d
);
