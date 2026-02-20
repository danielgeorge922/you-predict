-- Compute ml_feature_comment_aggregates for all videos that have comments.
--
-- Sources: fact_comment
-- Key:     video_id
-- Runs:    daily, independent (no upstream feature dependencies)
--
-- comment_language_entropy is written as NULL — it requires computing a
-- per-language frequency distribution which is not practical in pure SQL.
-- Only videos that have at least one comment row are included.

MERGE `{project}.{dataset}.ml_feature_comment_aggregates` AS T
USING (
  SELECT
    video_id,
    CURRENT_TIMESTAMP()                                      AS computed_at,
    DATE(CURRENT_TIMESTAMP())                                AS computed_date,

    -- Sample metadata
    MAX(sample_strategy)                                     AS sample_strategy,
    COUNT(*)                                                 AS comments_sampled,

    -- Sentiment aggregates
    AVG(sentiment_compound)                                  AS avg_sentiment_compound,
    SAFE_DIVIDE(
      COUNTIF(sentiment_compound > 0.05),
      COUNT(*)
    )                                                        AS positive_ratio,
    SAFE_DIVIDE(
      COUNTIF(sentiment_compound < -0.05),
      COUNT(*)
    )                                                        AS negative_ratio,

    -- Toxicity aggregates
    AVG(toxicity_score)                                      AS avg_toxicity,
    AVG(severe_toxicity_score)                               AS avg_severe_toxicity,
    AVG(insult_score)                                        AS avg_insult,
    AVG(identity_attack_score)                               AS avg_identity_attack,

    -- Toxicity ratios (threshold: 0.5)
    SAFE_DIVIDE(COUNTIF(toxicity_score        > 0.5), COUNT(*)) AS toxic_ratio,
    SAFE_DIVIDE(COUNTIF(severe_toxicity_score > 0.5), COUNT(*)) AS severe_toxic_ratio,
    SAFE_DIVIDE(COUNTIF(insult_score          > 0.5), COUNT(*)) AS insult_ratio,
    SAFE_DIVIDE(COUNTIF(identity_attack_score > 0.5), COUNT(*)) AS identity_attack_ratio,

    -- Toxicity extremes
    MAX(toxicity_score)                                      AS max_toxicity,
    MAX(identity_attack_score)                               AS max_identity_attack,

    -- Engagement stats
    AVG(CAST(like_count AS FLOAT64))                         AS avg_comment_likes,
    MAX(like_count)                                          AS max_comment_likes,
    AVG(CAST(reply_count AS FLOAT64))                        AS avg_reply_count,

    -- Language entropy — requires frequency distribution, deferred
    NULL                                                     AS comment_language_entropy,

    -- Commenter diversity
    SAFE_DIVIDE(
      COUNT(DISTINCT commenter_channel_id),
      COUNT(*)
    )                                                        AS unique_commenter_ratio,

    -- Comment text features
    AVG(LENGTH(comment_text))                                AS avg_comment_length,
    SAFE_DIVIDE(
      COUNTIF(ENDS_WITH(TRIM(comment_text), '?')),
      COUNT(*)
    )                                                        AS question_comment_ratio,

    -- Creator engagement: comments where the commenter is the channel owner
    COUNTIF(commenter_channel_id = channel_id)               AS creator_reply_count

  FROM `{project}.{dataset}.fact_comment`
  GROUP BY video_id
) AS S
ON T.video_id = S.video_id

WHEN MATCHED THEN UPDATE SET
  computed_at               = S.computed_at,
  computed_date             = S.computed_date,
  sample_strategy           = S.sample_strategy,
  comments_sampled          = S.comments_sampled,
  avg_sentiment_compound    = S.avg_sentiment_compound,
  positive_ratio            = S.positive_ratio,
  negative_ratio            = S.negative_ratio,
  avg_toxicity              = S.avg_toxicity,
  avg_severe_toxicity       = S.avg_severe_toxicity,
  avg_insult                = S.avg_insult,
  avg_identity_attack       = S.avg_identity_attack,
  toxic_ratio               = S.toxic_ratio,
  severe_toxic_ratio        = S.severe_toxic_ratio,
  insult_ratio              = S.insult_ratio,
  identity_attack_ratio     = S.identity_attack_ratio,
  max_toxicity              = S.max_toxicity,
  max_identity_attack       = S.max_identity_attack,
  avg_comment_likes         = S.avg_comment_likes,
  max_comment_likes         = S.max_comment_likes,
  avg_reply_count           = S.avg_reply_count,
  comment_language_entropy  = S.comment_language_entropy,
  unique_commenter_ratio    = S.unique_commenter_ratio,
  avg_comment_length        = S.avg_comment_length,
  question_comment_ratio    = S.question_comment_ratio,
  creator_reply_count       = S.creator_reply_count

WHEN NOT MATCHED THEN INSERT (
  video_id,
  computed_at,
  computed_date,
  sample_strategy,
  comments_sampled,
  avg_sentiment_compound,
  positive_ratio,
  negative_ratio,
  avg_toxicity,
  avg_severe_toxicity,
  avg_insult,
  avg_identity_attack,
  toxic_ratio,
  severe_toxic_ratio,
  insult_ratio,
  identity_attack_ratio,
  max_toxicity,
  max_identity_attack,
  avg_comment_likes,
  max_comment_likes,
  avg_reply_count,
  comment_language_entropy,
  unique_commenter_ratio,
  avg_comment_length,
  question_comment_ratio,
  creator_reply_count
) VALUES (
  S.video_id,
  S.computed_at,
  S.computed_date,
  S.sample_strategy,
  S.comments_sampled,
  S.avg_sentiment_compound,
  S.positive_ratio,
  S.negative_ratio,
  S.avg_toxicity,
  S.avg_severe_toxicity,
  S.avg_insult,
  S.avg_identity_attack,
  S.toxic_ratio,
  S.severe_toxic_ratio,
  S.insult_ratio,
  S.identity_attack_ratio,
  S.max_toxicity,
  S.max_identity_attack,
  S.avg_comment_likes,
  S.max_comment_likes,
  S.avg_reply_count,
  S.comment_language_entropy,
  S.unique_commenter_ratio,
  S.avg_comment_length,
  S.question_comment_ratio,
  S.creator_reply_count
);
