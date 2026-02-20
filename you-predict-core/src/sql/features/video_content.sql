-- Compute ml_feature_video_content for all monitored videos.
--
-- Sources: dim_video, video_monitoring
-- Key:     video_id
-- Runs:    daily, independent (no upstream feature dependencies)
--
-- NLP-derived fields (title_sentiment, title_clickbait_score) are written as
-- NULL — these require Python text processing and are deferred to a future
-- enrichment step that will read from this table and backfill those columns.

MERGE `{project}.{dataset}.ml_feature_video_content` AS T
USING (
  SELECT
    dv.video_id,
    CURRENT_TIMESTAMP()  AS computed_at,
    DATE(CURRENT_TIMESTAMP()) AS computed_date,

    -- Title structural features
    LENGTH(dv.title)                                     AS title_length,
    ARRAY_LENGTH(SPLIT(TRIM(dv.title), ' '))             AS title_word_count,

    -- Title signal features (regex-based, no NLP required)
    REGEXP_CONTAINS(
      dv.title,
      r'[\x{1F600}-\x{1F64F}\x{1F300}-\x{1F5FF}\x{1F680}-\x{1F6FF}'
      r'\x{1F1E0}-\x{1F1FF}\x{2702}-\x{27B0}\x{24C2}-\x{1F251}]'
    )                                                    AS title_has_emoji,

    REGEXP_CONTAINS(dv.title, r'\d')                     AS title_has_number,
    STRPOS(dv.title, '?') > 0                            AS title_has_question,
    REGEXP_CONTAINS(dv.title, r'\[|\(')                  AS title_has_brackets,

    -- Caps ratio: uppercase letters / total letters
    SAFE_DIVIDE(
      LENGTH(REGEXP_REPLACE(dv.title, r'[^A-Z]', '')),
      NULLIF(LENGTH(REGEXP_REPLACE(dv.title, r'[^a-zA-Z]', '')), 0)
    )                                                    AS title_caps_ratio,

    -- Power word count: matches from known clickbait vocabulary
    (
      CASE WHEN REGEXP_CONTAINS(LOWER(dv.title), r'insane|secret|shocking|unbelievable|incredible|amazing')    THEN 1 ELSE 0 END
    + CASE WHEN REGEXP_CONTAINS(LOWER(dv.title), r'ultimate|exposed|revealed|banned|warning|urgent')           THEN 1 ELSE 0 END
    + CASE WHEN REGEXP_CONTAINS(LOWER(dv.title), r'breaking|exclusive|epic|crazy|huge|massive')                THEN 1 ELSE 0 END
    + CASE WHEN REGEXP_CONTAINS(LOWER(dv.title), r'destroyed|ruined|worst|best|perfect|impossible')            THEN 1 ELSE 0 END
    + CASE WHEN REGEXP_CONTAINS(LOWER(dv.title), r'never|always|finally|gone wrong|not clickbait')             THEN 1 ELSE 0 END
    )                                                    AS title_power_word_count,

    -- NLP fields — deferred, filled by future Python enrichment step
    NULL                                                 AS title_sentiment,
    NULL                                                 AS title_clickbait_score,

    -- Description features
    LENGTH(dv.description)                               AS description_length,
    ARRAY_LENGTH(
      REGEXP_EXTRACT_ALL(dv.description, r'https?://[^\s]+')
    )                                                    AS description_link_count,

    -- Metadata counts
    ARRAY_LENGTH(dv.tags)                                AS tag_count,
    ARRAY_LENGTH(dv.topics)                              AS topic_count,

    -- Duration bucket
    CASE
      WHEN dv.duration_seconds < 60   THEN 'short'
      WHEN dv.duration_seconds < 600  THEN 'medium'
      WHEN dv.duration_seconds < 1800 THEN 'long'
      ELSE 'very_long'
    END                                                  AS duration_bucket

  FROM `{project}.{dataset}.dim_video` dv
  INNER JOIN `{project}.{dataset}.video_monitoring` vm
    ON dv.video_id = vm.video_id
) AS S
ON T.video_id = S.video_id

WHEN MATCHED THEN UPDATE SET
  computed_at             = S.computed_at,
  computed_date           = S.computed_date,
  title_length            = S.title_length,
  title_word_count        = S.title_word_count,
  title_has_emoji         = S.title_has_emoji,
  title_has_number        = S.title_has_number,
  title_has_question      = S.title_has_question,
  title_has_brackets      = S.title_has_brackets,
  title_caps_ratio        = S.title_caps_ratio,
  title_power_word_count  = S.title_power_word_count,
  title_sentiment         = S.title_sentiment,
  title_clickbait_score   = S.title_clickbait_score,
  description_length      = S.description_length,
  description_link_count  = S.description_link_count,
  tag_count               = S.tag_count,
  topic_count             = S.topic_count,
  duration_bucket         = S.duration_bucket

WHEN NOT MATCHED THEN INSERT (
  video_id,
  computed_at,
  computed_date,
  title_length,
  title_word_count,
  title_has_emoji,
  title_has_number,
  title_has_question,
  title_has_brackets,
  title_caps_ratio,
  title_power_word_count,
  title_sentiment,
  title_clickbait_score,
  description_length,
  description_link_count,
  tag_count,
  topic_count,
  duration_bucket
) VALUES (
  S.video_id,
  S.computed_at,
  S.computed_date,
  S.title_length,
  S.title_word_count,
  S.title_has_emoji,
  S.title_has_number,
  S.title_has_question,
  S.title_has_brackets,
  S.title_caps_ratio,
  S.title_power_word_count,
  S.title_sentiment,
  S.title_clickbait_score,
  S.description_length,
  S.description_link_count,
  S.tag_count,
  S.topic_count,
  S.duration_bucket
);
