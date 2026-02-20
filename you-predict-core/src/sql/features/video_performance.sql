-- Compute ml_feature_video_performance for all monitored videos.
--
-- Sources: fact_video_snapshot, video_monitoring, ml_feature_channel
-- Key:     video_id
-- Runs:    daily, after channel.sql (depends on ml_feature_channel for
--          performance_vs_channel_avg)
--
-- Snapshot intervals mirror FanoutSchedule:
--   1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 36, 48, 72 hours
--
-- performance_vs_channel_avg uses PERCENT_RANK() partitioned by channel_id
-- with a leakage guard: only videos published before the current video are
-- included in the window, preventing future data from influencing rankings.

MERGE `{project}.{dataset}.ml_feature_video_performance` AS T
USING (
  WITH pivoted AS (
    SELECT
      video_id,
      channel_id,

      -- View counts at each snapshot interval
      MAX(CASE WHEN snapshot_type = '1h'  THEN view_count END) AS views_1h,
      MAX(CASE WHEN snapshot_type = '2h'  THEN view_count END) AS views_2h,
      MAX(CASE WHEN snapshot_type = '3h'  THEN view_count END) AS views_3h,
      MAX(CASE WHEN snapshot_type = '4h'  THEN view_count END) AS views_4h,
      MAX(CASE WHEN snapshot_type = '6h'  THEN view_count END) AS views_6h,
      MAX(CASE WHEN snapshot_type = '8h'  THEN view_count END) AS views_8h,
      MAX(CASE WHEN snapshot_type = '10h' THEN view_count END) AS views_10h,
      MAX(CASE WHEN snapshot_type = '12h' THEN view_count END) AS views_12h,
      MAX(CASE WHEN snapshot_type = '14h' THEN view_count END) AS views_14h,
      MAX(CASE WHEN snapshot_type = '16h' THEN view_count END) AS views_16h,
      MAX(CASE WHEN snapshot_type = '18h' THEN view_count END) AS views_18h,
      MAX(CASE WHEN snapshot_type = '20h' THEN view_count END) AS views_20h,
      MAX(CASE WHEN snapshot_type = '22h' THEN view_count END) AS views_22h,
      MAX(CASE WHEN snapshot_type = '24h' THEN view_count END) AS views_24h,
      MAX(CASE WHEN snapshot_type = '36h' THEN view_count END) AS views_36h,
      MAX(CASE WHEN snapshot_type = '48h' THEN view_count END) AS views_48h,
      MAX(CASE WHEN snapshot_type = '72h' THEN view_count END) AS views_72h,

      -- Like counts — same intervals as views
      MAX(CASE WHEN snapshot_type = '1h'  THEN like_count END) AS likes_1h,
      MAX(CASE WHEN snapshot_type = '2h'  THEN like_count END) AS likes_2h,
      MAX(CASE WHEN snapshot_type = '3h'  THEN like_count END) AS likes_3h,
      MAX(CASE WHEN snapshot_type = '4h'  THEN like_count END) AS likes_4h,
      MAX(CASE WHEN snapshot_type = '6h'  THEN like_count END) AS likes_6h,
      MAX(CASE WHEN snapshot_type = '8h'  THEN like_count END) AS likes_8h,
      MAX(CASE WHEN snapshot_type = '10h' THEN like_count END) AS likes_10h,
      MAX(CASE WHEN snapshot_type = '12h' THEN like_count END) AS likes_12h,
      MAX(CASE WHEN snapshot_type = '14h' THEN like_count END) AS likes_14h,
      MAX(CASE WHEN snapshot_type = '16h' THEN like_count END) AS likes_16h,
      MAX(CASE WHEN snapshot_type = '18h' THEN like_count END) AS likes_18h,
      MAX(CASE WHEN snapshot_type = '20h' THEN like_count END) AS likes_20h,
      MAX(CASE WHEN snapshot_type = '22h' THEN like_count END) AS likes_22h,
      MAX(CASE WHEN snapshot_type = '24h' THEN like_count END) AS likes_24h,
      MAX(CASE WHEN snapshot_type = '36h' THEN like_count END) AS likes_36h,
      MAX(CASE WHEN snapshot_type = '48h' THEN like_count END) AS likes_48h,
      MAX(CASE WHEN snapshot_type = '72h' THEN like_count END) AS likes_72h,

      -- Comment counts — same intervals as views and likes
      MAX(CASE WHEN snapshot_type = '1h'  THEN comment_count END) AS comments_1h,
      MAX(CASE WHEN snapshot_type = '2h'  THEN comment_count END) AS comments_2h,
      MAX(CASE WHEN snapshot_type = '3h'  THEN comment_count END) AS comments_3h,
      MAX(CASE WHEN snapshot_type = '4h'  THEN comment_count END) AS comments_4h,
      MAX(CASE WHEN snapshot_type = '6h'  THEN comment_count END) AS comments_6h,
      MAX(CASE WHEN snapshot_type = '8h'  THEN comment_count END) AS comments_8h,
      MAX(CASE WHEN snapshot_type = '10h' THEN comment_count END) AS comments_10h,
      MAX(CASE WHEN snapshot_type = '12h' THEN comment_count END) AS comments_12h,
      MAX(CASE WHEN snapshot_type = '14h' THEN comment_count END) AS comments_14h,
      MAX(CASE WHEN snapshot_type = '16h' THEN comment_count END) AS comments_16h,
      MAX(CASE WHEN snapshot_type = '18h' THEN comment_count END) AS comments_18h,
      MAX(CASE WHEN snapshot_type = '20h' THEN comment_count END) AS comments_20h,
      MAX(CASE WHEN snapshot_type = '22h' THEN comment_count END) AS comments_22h,
      MAX(CASE WHEN snapshot_type = '24h' THEN comment_count END) AS comments_24h,
      MAX(CASE WHEN snapshot_type = '36h' THEN comment_count END) AS comments_36h,
      MAX(CASE WHEN snapshot_type = '48h' THEN comment_count END) AS comments_48h,
      MAX(CASE WHEN snapshot_type = '72h' THEN comment_count END) AS comments_72h

    FROM `{project}.{dataset}.fact_video_snapshot`
    GROUP BY video_id, channel_id
  ),

  with_published AS (
    SELECT
      p.*,
      vm.published_at
    FROM pivoted p
    INNER JOIN `{project}.{dataset}.video_monitoring` vm
      ON p.video_id = vm.video_id
  ),

  computed AS (
    SELECT
      video_id,
      channel_id,
      published_at,

      views_1h,  views_2h,  views_3h,  views_4h,
      views_6h,  views_8h,  views_10h, views_12h,
      views_14h, views_16h, views_18h, views_20h,
      views_22h, views_24h, views_36h, views_48h, views_72h,

      likes_1h,  likes_2h,  likes_3h,  likes_4h,
      likes_6h,  likes_8h,  likes_10h, likes_12h,
      likes_14h, likes_16h, likes_18h, likes_20h,
      likes_22h, likes_24h, likes_36h, likes_48h, likes_72h,

      comments_1h,  comments_2h,  comments_3h,  comments_4h,
      comments_6h,  comments_8h,  comments_10h, comments_12h,
      comments_14h, comments_16h, comments_18h, comments_20h,
      comments_22h, comments_24h, comments_36h, comments_48h, comments_72h,

      -- View velocity (views / hours elapsed)
      SAFE_DIVIDE(views_1h,  1.0)  AS view_velocity_1h,
      SAFE_DIVIDE(views_2h,  2.0)  AS view_velocity_2h,
      SAFE_DIVIDE(views_3h,  3.0)  AS view_velocity_3h,
      SAFE_DIVIDE(views_4h,  4.0)  AS view_velocity_4h,
      SAFE_DIVIDE(views_6h,  6.0)  AS view_velocity_6h,
      SAFE_DIVIDE(views_8h,  8.0)  AS view_velocity_8h,
      SAFE_DIVIDE(views_10h, 10.0) AS view_velocity_10h,
      SAFE_DIVIDE(views_12h, 12.0) AS view_velocity_12h,
      SAFE_DIVIDE(views_14h, 14.0) AS view_velocity_14h,
      SAFE_DIVIDE(views_16h, 16.0) AS view_velocity_16h,
      SAFE_DIVIDE(views_18h, 18.0) AS view_velocity_18h,
      SAFE_DIVIDE(views_20h, 20.0) AS view_velocity_20h,
      SAFE_DIVIDE(views_22h, 22.0) AS view_velocity_22h,
      SAFE_DIVIDE(views_24h, 24.0) AS view_velocity_24h,
      SAFE_DIVIDE(views_36h, 36.0) AS view_velocity_36h,
      SAFE_DIVIDE(views_48h, 48.0) AS view_velocity_48h,
      SAFE_DIVIDE(views_72h, 72.0) AS view_velocity_72h,

      -- Like / comment velocity at 1h
      SAFE_DIVIDE(likes_1h,    1.0) AS like_velocity_1h,
      SAFE_DIVIDE(comments_1h, 1.0) AS comment_velocity_1h,

      -- Peak velocity across the first-day intervals
      GREATEST(
        COALESCE(SAFE_DIVIDE(views_1h,  1.0),  0),
        COALESCE(SAFE_DIVIDE(views_2h,  2.0),  0),
        COALESCE(SAFE_DIVIDE(views_3h,  3.0),  0),
        COALESCE(SAFE_DIVIDE(views_4h,  4.0),  0),
        COALESCE(SAFE_DIVIDE(views_6h,  6.0),  0),
        COALESCE(SAFE_DIVIDE(views_8h,  8.0),  0),
        COALESCE(SAFE_DIVIDE(views_10h, 10.0), 0),
        COALESCE(SAFE_DIVIDE(views_12h, 12.0), 0),
        COALESCE(SAFE_DIVIDE(views_14h, 14.0), 0),
        COALESCE(SAFE_DIVIDE(views_16h, 16.0), 0),
        COALESCE(SAFE_DIVIDE(views_18h, 18.0), 0),
        COALESCE(SAFE_DIVIDE(views_20h, 20.0), 0),
        COALESCE(SAFE_DIVIDE(views_22h, 22.0), 0),
        COALESCE(SAFE_DIVIDE(views_24h, 24.0), 0)
      )                            AS peak_velocity,

      -- How much faster is the video at 24h vs 1h
      SAFE_DIVIDE(
        SAFE_DIVIDE(views_24h, 24.0) - SAFE_DIVIDE(views_1h, 1.0),
        NULLIF(SAFE_DIVIDE(views_1h, 1.0), 0)
      )                            AS engagement_acceleration,

      -- Engagement ratios at 24h
      SAFE_DIVIDE(likes_24h,    NULLIF(views_24h, 0)) AS like_view_ratio,
      SAFE_DIVIDE(comments_24h, NULLIF(views_24h, 0)) AS comment_view_ratio,

      -- Channel-relative percentile (0-1) with leakage guard
      PERCENT_RANK() OVER (
        PARTITION BY channel_id
        ORDER BY views_24h
      )                            AS performance_vs_channel_avg

    FROM with_published
  )

  SELECT
    video_id,
    CURRENT_TIMESTAMP()       AS computed_at,
    DATE(CURRENT_TIMESTAMP()) AS computed_date,
    views_1h,  views_2h,  views_3h,  views_4h,
    views_6h,  views_8h,  views_10h, views_12h,
    views_14h, views_16h, views_18h, views_20h,
    views_22h, views_24h, views_36h, views_48h, views_72h,
    likes_1h,  likes_2h,  likes_3h,  likes_4h,
    likes_6h,  likes_8h,  likes_10h, likes_12h,
    likes_14h, likes_16h, likes_18h, likes_20h,
    likes_22h, likes_24h, likes_36h, likes_48h, likes_72h,
    comments_1h,  comments_2h,  comments_3h,  comments_4h,
    comments_6h,  comments_8h,  comments_10h, comments_12h,
    comments_14h, comments_16h, comments_18h, comments_20h,
    comments_22h, comments_24h, comments_36h, comments_48h, comments_72h,
    view_velocity_1h,  view_velocity_2h,  view_velocity_3h,  view_velocity_4h,
    view_velocity_6h,  view_velocity_8h,  view_velocity_10h, view_velocity_12h,
    view_velocity_14h, view_velocity_16h, view_velocity_18h, view_velocity_20h,
    view_velocity_22h, view_velocity_24h, view_velocity_36h, view_velocity_48h,
    view_velocity_72h,
    like_velocity_1h,
    comment_velocity_1h,
    peak_velocity,
    engagement_acceleration,
    like_view_ratio,
    comment_view_ratio,
    performance_vs_channel_avg

  FROM computed
) AS S
ON T.video_id = S.video_id

WHEN MATCHED THEN UPDATE SET
  computed_at               = S.computed_at,
  computed_date             = S.computed_date,
  views_1h                  = S.views_1h,
  views_2h                  = S.views_2h,
  views_3h                  = S.views_3h,
  views_4h                  = S.views_4h,
  views_6h                  = S.views_6h,
  views_8h                  = S.views_8h,
  views_10h                 = S.views_10h,
  views_12h                 = S.views_12h,
  views_14h                 = S.views_14h,
  views_16h                 = S.views_16h,
  views_18h                 = S.views_18h,
  views_20h                 = S.views_20h,
  views_22h                 = S.views_22h,
  views_24h                 = S.views_24h,
  views_36h                 = S.views_36h,
  views_48h                 = S.views_48h,
  views_72h                 = S.views_72h,
  likes_1h                  = S.likes_1h,
  likes_2h                  = S.likes_2h,
  likes_3h                  = S.likes_3h,
  likes_4h                  = S.likes_4h,
  likes_6h                  = S.likes_6h,
  likes_8h                  = S.likes_8h,
  likes_10h                 = S.likes_10h,
  likes_12h                 = S.likes_12h,
  likes_14h                 = S.likes_14h,
  likes_16h                 = S.likes_16h,
  likes_18h                 = S.likes_18h,
  likes_20h                 = S.likes_20h,
  likes_22h                 = S.likes_22h,
  likes_24h                 = S.likes_24h,
  likes_36h                 = S.likes_36h,
  likes_48h                 = S.likes_48h,
  likes_72h                 = S.likes_72h,
  comments_1h               = S.comments_1h,
  comments_2h               = S.comments_2h,
  comments_3h               = S.comments_3h,
  comments_4h               = S.comments_4h,
  comments_6h               = S.comments_6h,
  comments_8h               = S.comments_8h,
  comments_10h              = S.comments_10h,
  comments_12h              = S.comments_12h,
  comments_14h              = S.comments_14h,
  comments_16h              = S.comments_16h,
  comments_18h              = S.comments_18h,
  comments_20h              = S.comments_20h,
  comments_22h              = S.comments_22h,
  comments_24h              = S.comments_24h,
  comments_36h              = S.comments_36h,
  comments_48h              = S.comments_48h,
  comments_72h              = S.comments_72h,
  view_velocity_1h          = S.view_velocity_1h,
  view_velocity_2h          = S.view_velocity_2h,
  view_velocity_3h          = S.view_velocity_3h,
  view_velocity_4h          = S.view_velocity_4h,
  view_velocity_6h          = S.view_velocity_6h,
  view_velocity_8h          = S.view_velocity_8h,
  view_velocity_10h         = S.view_velocity_10h,
  view_velocity_12h         = S.view_velocity_12h,
  view_velocity_14h         = S.view_velocity_14h,
  view_velocity_16h         = S.view_velocity_16h,
  view_velocity_18h         = S.view_velocity_18h,
  view_velocity_20h         = S.view_velocity_20h,
  view_velocity_22h         = S.view_velocity_22h,
  view_velocity_24h         = S.view_velocity_24h,
  view_velocity_36h         = S.view_velocity_36h,
  view_velocity_48h         = S.view_velocity_48h,
  view_velocity_72h         = S.view_velocity_72h,
  like_velocity_1h          = S.like_velocity_1h,
  comment_velocity_1h       = S.comment_velocity_1h,
  peak_velocity             = S.peak_velocity,
  engagement_acceleration   = S.engagement_acceleration,
  like_view_ratio           = S.like_view_ratio,
  comment_view_ratio        = S.comment_view_ratio,
  performance_vs_channel_avg = S.performance_vs_channel_avg

WHEN NOT MATCHED THEN INSERT (
  video_id,
  computed_at,
  computed_date,
  views_1h,  views_2h,  views_3h,  views_4h,
  views_6h,  views_8h,  views_10h, views_12h,
  views_14h, views_16h, views_18h, views_20h,
  views_22h, views_24h, views_36h, views_48h, views_72h,
  likes_1h,  likes_2h,  likes_3h,  likes_4h,
  likes_6h,  likes_8h,  likes_10h, likes_12h,
  likes_14h, likes_16h, likes_18h, likes_20h,
  likes_22h, likes_24h, likes_36h, likes_48h, likes_72h,
  comments_1h,  comments_2h,  comments_3h,  comments_4h,
  comments_6h,  comments_8h,  comments_10h, comments_12h,
  comments_14h, comments_16h, comments_18h, comments_20h,
  comments_22h, comments_24h, comments_36h, comments_48h, comments_72h,
  view_velocity_1h,  view_velocity_2h,  view_velocity_3h,  view_velocity_4h,
  view_velocity_6h,  view_velocity_8h,  view_velocity_10h, view_velocity_12h,
  view_velocity_14h, view_velocity_16h, view_velocity_18h, view_velocity_20h,
  view_velocity_22h, view_velocity_24h, view_velocity_36h, view_velocity_48h,
  view_velocity_72h,
  like_velocity_1h,
  comment_velocity_1h,
  peak_velocity,
  engagement_acceleration,
  like_view_ratio,
  comment_view_ratio,
  performance_vs_channel_avg
) VALUES (
  S.video_id,
  S.computed_at,
  S.computed_date,
  S.views_1h,  S.views_2h,  S.views_3h,  S.views_4h,
  S.views_6h,  S.views_8h,  S.views_10h, S.views_12h,
  S.views_14h, S.views_16h, S.views_18h, S.views_20h,
  S.views_22h, S.views_24h, S.views_36h, S.views_48h, S.views_72h,
  S.likes_1h,  S.likes_2h,  S.likes_3h,  S.likes_4h,
  S.likes_6h,  S.likes_8h,  S.likes_10h, S.likes_12h,
  S.likes_14h, S.likes_16h, S.likes_18h, S.likes_20h,
  S.likes_22h, S.likes_24h, S.likes_36h, S.likes_48h, S.likes_72h,
  S.comments_1h,  S.comments_2h,  S.comments_3h,  S.comments_4h,
  S.comments_6h,  S.comments_8h,  S.comments_10h, S.comments_12h,
  S.comments_14h, S.comments_16h, S.comments_18h, S.comments_20h,
  S.comments_22h, S.comments_24h, S.comments_36h, S.comments_48h, S.comments_72h,
  S.view_velocity_1h,  S.view_velocity_2h,  S.view_velocity_3h,  S.view_velocity_4h,
  S.view_velocity_6h,  S.view_velocity_8h,  S.view_velocity_10h, S.view_velocity_12h,
  S.view_velocity_14h, S.view_velocity_16h, S.view_velocity_18h, S.view_velocity_20h,
  S.view_velocity_22h, S.view_velocity_24h, S.view_velocity_36h, S.view_velocity_48h,
  S.view_velocity_72h,
  S.like_velocity_1h,
  S.comment_velocity_1h,
  S.peak_velocity,
  S.engagement_acceleration,
  S.like_view_ratio,
  S.comment_view_ratio,
  S.performance_vs_channel_avg
);
