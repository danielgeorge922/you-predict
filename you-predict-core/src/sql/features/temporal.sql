-- Compute ml_feature_temporal for all monitored videos.
--
-- Sources: video_monitoring, dim_date
-- Key:     video_id
-- Runs:    daily, independent (no upstream feature dependencies)
--
-- days_since_last_upload and videos_published_same_day_channel use window
-- functions over video_monitoring so no join to dim_video is needed.

MERGE `{project}.{dataset}.ml_feature_temporal` AS T
USING (
  WITH

  -- All monitored videos with their publish timestamps
  all_videos AS (
    SELECT
      video_id,
      channel_id,
      published_at
    FROM `{project}.{dataset}.video_monitoring`
  ),

  -- Window functions require a separate CTE — BigQuery does not allow
  -- window functions directly in a MERGE source subquery in all contexts
  windowed AS (
    SELECT
      video_id,
      channel_id,
      published_at,

      -- How many days since this channel's previous upload
      DATE_DIFF(
        DATE(published_at),
        DATE(LAG(published_at) OVER (
          PARTITION BY channel_id
          ORDER BY published_at
        )),
        DAY
      ) AS days_since_last_upload,

      -- How many videos this channel published on the same calendar day
      COUNT(*) OVER (
        PARTITION BY channel_id, DATE(published_at)
      ) AS videos_published_same_day_channel

    FROM all_videos
  )

  SELECT
    w.video_id,
    CURRENT_TIMESTAMP()                               AS computed_at,

    EXTRACT(HOUR       FROM w.published_at)           AS hour_of_day_published,
    EXTRACT(DAYOFWEEK  FROM w.published_at)           AS day_of_week_published,
    EXTRACT(DAYOFWEEK  FROM w.published_at) IN (1, 7) AS is_weekend_publish,

    -- is_holiday_publish from dim_date (US holidays only)
    COALESCE(dd.is_us_holiday, FALSE)                 AS is_holiday_publish,

    w.days_since_last_upload,
    w.videos_published_same_day_channel

  FROM windowed w
  LEFT JOIN `{project}.{dataset}.dim_date` dd
    ON dd.full_date = DATE(w.published_at)
) AS S
ON T.video_id = S.video_id

WHEN MATCHED THEN UPDATE SET
  computed_at                        = S.computed_at,
  hour_of_day_published              = S.hour_of_day_published,
  day_of_week_published              = S.day_of_week_published,
  is_weekend_publish                 = S.is_weekend_publish,
  is_holiday_publish                 = S.is_holiday_publish,
  days_since_last_upload             = S.days_since_last_upload,
  videos_published_same_day_channel  = S.videos_published_same_day_channel

WHEN NOT MATCHED THEN INSERT (
  video_id,
  computed_at,
  hour_of_day_published,
  day_of_week_published,
  is_weekend_publish,
  is_holiday_publish,
  days_since_last_upload,
  videos_published_same_day_channel
) VALUES (
  S.video_id,
  S.computed_at,
  S.hour_of_day_published,
  S.day_of_week_published,
  S.is_weekend_publish,
  S.is_holiday_publish,
  S.days_since_last_upload,
  S.videos_published_same_day_channel
);
