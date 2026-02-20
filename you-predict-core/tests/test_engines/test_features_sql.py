"""SQL structure tests for feature MERGE files.

Each test class reads the actual .sql file from disk and asserts that the
right table, MERGE key, columns, and SQL patterns are present. No BigQuery
connection is required — these are static analysis tests.
"""

from pathlib import Path

import pytest

_SQL_DIR = Path(__file__).parent.parent.parent / "src" / "sql" / "features"

# Canonical snapshot intervals from FanoutSchedule
_ALL_INTERVALS = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 36, 48, 72]


# ---------------------------------------------------------------------------
# channel.sql
# ---------------------------------------------------------------------------


class TestChannelSql:
    @pytest.fixture(scope="class")
    def sql(self) -> str:
        return (_SQL_DIR / "channel.sql").read_text(encoding="utf-8")

    def test_merges_correct_table(self, sql):
        assert "ml_feature_channel" in sql

    def test_merge_key_is_channel_id(self, sql):
        assert "T.channel_id = S.channel_id" in sql

    def test_project_dataset_placeholders_present(self, sql):
        assert "{project}" in sql
        assert "{dataset}" in sql

    def test_subscriber_tier_present(self, sql):
        assert "subscriber_tier" in sql

    def test_subscriber_tier_has_all_four_tiers(self, sql):
        for tier in ("'micro'", "'small'", "'medium'", "'large'"):
            assert tier in sql

    def test_channel_age_days_present(self, sql):
        assert "channel_age_days" in sql
        assert "DATE_DIFF" in sql

    def test_upload_frequency_7d_present(self, sql):
        assert "upload_frequency_7d" in sql

    def test_upload_frequency_30d_present(self, sql):
        assert "upload_frequency_30d" in sql

    def test_avg_views_per_video_30d_present(self, sql):
        assert "avg_views_per_video_30d" in sql

    def test_avg_engagement_rate_30d_present(self, sql):
        assert "avg_engagement_rate_30d" in sql

    def test_subscriber_growth_rate_30d_present(self, sql):
        assert "subscriber_growth_rate_30d" in sql

    def test_view_consistency_score_present(self, sql):
        assert "view_consistency_score" in sql

    def test_avg_video_duration_30d_present(self, sql):
        assert "avg_video_duration_30d" in sql

    def test_deferred_fields_present(self, sql):
        # These are written as NULL pending future implementation
        assert "channel_momentum_score" in sql
        assert "avg_time_between_uploads_7d" in sql

    def test_safe_divide_used_for_ratios(self, sql):
        assert "SAFE_DIVIDE" in sql

    def test_only_active_channels_included(self, sql):
        assert "is_active" in sql

    def test_joins_fact_channel_snapshot_for_30d_subs(self, sql):
        assert "fact_channel_snapshot" in sql


# ---------------------------------------------------------------------------
# video_performance.sql
# ---------------------------------------------------------------------------


class TestVideoPerformanceSql:
    @pytest.fixture(scope="class")
    def sql(self) -> str:
        return (_SQL_DIR / "video_performance.sql").read_text(encoding="utf-8")

    def test_merges_correct_table(self, sql):
        assert "ml_feature_video_performance" in sql

    def test_merge_key_is_video_id(self, sql):
        assert "T.video_id = S.video_id" in sql

    def test_project_dataset_placeholders_present(self, sql):
        assert "{project}" in sql
        assert "{dataset}" in sql

    @pytest.mark.parametrize("interval", _ALL_INTERVALS)
    def test_views_column_for_interval(self, sql, interval):
        assert f"views_{interval}h" in sql

    @pytest.mark.parametrize("interval", _ALL_INTERVALS)
    def test_likes_column_for_interval(self, sql, interval):
        assert f"likes_{interval}h" in sql

    @pytest.mark.parametrize("interval", _ALL_INTERVALS)
    def test_comments_column_for_interval(self, sql, interval):
        assert f"comments_{interval}h" in sql

    @pytest.mark.parametrize("interval", _ALL_INTERVALS)
    def test_view_velocity_for_interval(self, sql, interval):
        assert f"view_velocity_{interval}h" in sql

    def test_like_velocity_1h_present(self, sql):
        assert "like_velocity_1h" in sql

    def test_comment_velocity_1h_present(self, sql):
        assert "comment_velocity_1h" in sql

    def test_peak_velocity_present(self, sql):
        assert "peak_velocity" in sql
        assert "GREATEST" in sql

    def test_engagement_acceleration_present(self, sql):
        assert "engagement_acceleration" in sql

    def test_like_view_ratio_present(self, sql):
        assert "like_view_ratio" in sql

    def test_comment_view_ratio_present(self, sql):
        assert "comment_view_ratio" in sql

    def test_performance_vs_channel_avg_uses_percent_rank(self, sql):
        assert "performance_vs_channel_avg" in sql
        assert "PERCENT_RANK()" in sql

    def test_percent_rank_partitioned_by_channel_id(self, sql):
        assert "PARTITION BY channel_id" in sql

    def test_hours_to_10k_views_removed(self, sql):
        # Explicitly dropped — verify it is not present
        assert "hours_to_10k_views" not in sql

    def test_safe_divide_used_for_velocity(self, sql):
        assert "SAFE_DIVIDE" in sql

    def test_sources_from_fact_video_snapshot(self, sql):
        assert "fact_video_snapshot" in sql

    def test_joins_video_monitoring(self, sql):
        assert "video_monitoring" in sql


# ---------------------------------------------------------------------------
# video_content.sql
# ---------------------------------------------------------------------------


class TestVideoContentSql:
    @pytest.fixture(scope="class")
    def sql(self) -> str:
        return (_SQL_DIR / "video_content.sql").read_text(encoding="utf-8")

    def test_merges_correct_table(self, sql):
        assert "ml_feature_video_content" in sql

    def test_merge_key_is_video_id(self, sql):
        assert "T.video_id = S.video_id" in sql

    def test_project_dataset_placeholders_present(self, sql):
        assert "{project}" in sql
        assert "{dataset}" in sql

    def test_title_length_present(self, sql):
        assert "title_length" in sql

    def test_title_word_count_uses_split(self, sql):
        assert "title_word_count" in sql
        assert "SPLIT" in sql

    def test_title_has_emoji_uses_regexp_contains(self, sql):
        assert "title_has_emoji" in sql
        assert "REGEXP_CONTAINS" in sql

    def test_title_has_number_present(self, sql):
        assert "title_has_number" in sql

    def test_title_has_question_present(self, sql):
        assert "title_has_question" in sql

    def test_title_has_brackets_present(self, sql):
        assert "title_has_brackets" in sql

    def test_title_caps_ratio_uses_safe_divide(self, sql):
        assert "title_caps_ratio" in sql
        assert "SAFE_DIVIDE" in sql

    def test_title_power_word_count_present(self, sql):
        assert "title_power_word_count" in sql

    def test_nlp_fields_written_as_null(self, sql):
        # NLP deferred — must be present as columns but written as NULL
        assert "title_sentiment" in sql
        assert "title_clickbait_score" in sql

    def test_description_length_present(self, sql):
        assert "description_length" in sql

    def test_description_link_count_uses_regexp_extract_all(self, sql):
        assert "description_link_count" in sql
        assert "REGEXP_EXTRACT_ALL" in sql

    def test_tag_count_present(self, sql):
        assert "tag_count" in sql

    def test_topic_count_present(self, sql):
        assert "topic_count" in sql

    def test_duration_bucket_has_all_tiers(self, sql):
        assert "duration_bucket" in sql
        for tier in ("'short'", "'medium'", "'long'", "'very_long'"):
            assert tier in sql

    def test_sources_dim_video_and_video_monitoring(self, sql):
        assert "dim_video" in sql
        assert "video_monitoring" in sql


# ---------------------------------------------------------------------------
# temporal.sql
# ---------------------------------------------------------------------------


class TestTemporalSql:
    @pytest.fixture(scope="class")
    def sql(self) -> str:
        return (_SQL_DIR / "temporal.sql").read_text(encoding="utf-8")

    def test_merges_correct_table(self, sql):
        assert "ml_feature_temporal" in sql

    def test_merge_key_is_video_id(self, sql):
        assert "T.video_id = S.video_id" in sql

    def test_project_dataset_placeholders_present(self, sql):
        assert "{project}" in sql
        assert "{dataset}" in sql

    def test_hour_of_day_published_uses_extract_hour(self, sql):
        assert "hour_of_day_published" in sql
        assert "EXTRACT(HOUR" in sql

    def test_day_of_week_published_uses_extract_dayofweek(self, sql):
        assert "day_of_week_published" in sql
        assert "EXTRACT(DAYOFWEEK" in sql

    def test_is_weekend_publish_checks_sunday_and_saturday(self, sql):
        assert "is_weekend_publish" in sql
        assert "IN (1, 7)" in sql

    def test_is_holiday_publish_uses_dim_date_flag(self, sql):
        assert "is_holiday_publish" in sql
        assert "is_us_holiday" in sql
        assert "dim_date" in sql

    def test_days_since_last_upload_uses_lag_window(self, sql):
        assert "days_since_last_upload" in sql
        assert "LAG(" in sql

    def test_days_since_last_upload_partitioned_by_channel(self, sql):
        # LAG must be ordered per channel to get the previous upload of the same channel
        assert "PARTITION BY channel_id" in sql

    def test_videos_published_same_day_channel_uses_count_over(self, sql):
        assert "videos_published_same_day_channel" in sql
        assert "COUNT(*) OVER" in sql

    def test_source_is_video_monitoring(self, sql):
        assert "video_monitoring" in sql


# ---------------------------------------------------------------------------
# comment_aggregates.sql
# ---------------------------------------------------------------------------


class TestCommentAggregatesSql:
    @pytest.fixture(scope="class")
    def sql(self) -> str:
        return (_SQL_DIR / "comment_aggregates.sql").read_text(encoding="utf-8")

    def test_merges_correct_table(self, sql):
        assert "ml_feature_comment_aggregates" in sql

    def test_merge_key_is_video_id(self, sql):
        assert "T.video_id = S.video_id" in sql

    def test_project_dataset_placeholders_present(self, sql):
        assert "{project}" in sql
        assert "{dataset}" in sql

    def test_avg_sentiment_compound_present(self, sql):
        assert "avg_sentiment_compound" in sql

    def test_positive_ratio_present(self, sql):
        assert "positive_ratio" in sql

    def test_negative_ratio_present(self, sql):
        assert "negative_ratio" in sql

    def test_avg_toxicity_present(self, sql):
        assert "avg_toxicity" in sql

    def test_avg_severe_toxicity_present(self, sql):
        assert "avg_severe_toxicity" in sql

    def test_avg_insult_present(self, sql):
        assert "avg_insult" in sql

    def test_avg_identity_attack_present(self, sql):
        assert "avg_identity_attack" in sql

    def test_toxicity_ratios_use_threshold_of_05(self, sql):
        assert "toxic_ratio" in sql
        assert "> 0.5" in sql

    def test_max_toxicity_present(self, sql):
        assert "max_toxicity" in sql

    def test_max_identity_attack_present(self, sql):
        assert "max_identity_attack" in sql

    def test_avg_comment_likes_present(self, sql):
        assert "avg_comment_likes" in sql

    def test_max_comment_likes_present(self, sql):
        assert "max_comment_likes" in sql

    def test_avg_reply_count_present(self, sql):
        assert "avg_reply_count" in sql

    def test_comment_language_entropy_written_as_null(self, sql):
        # Deferred — frequency distribution requires Python, not SQL
        assert "comment_language_entropy" in sql

    def test_unique_commenter_ratio_uses_count_distinct(self, sql):
        assert "unique_commenter_ratio" in sql
        assert "COUNT(DISTINCT" in sql

    def test_avg_comment_length_measures_text_length(self, sql):
        assert "avg_comment_length" in sql
        assert "LENGTH(comment_text)" in sql

    def test_question_comment_ratio_uses_ends_with(self, sql):
        assert "question_comment_ratio" in sql
        assert "ENDS_WITH" in sql

    def test_creator_reply_count_matches_on_channel_id(self, sql):
        assert "creator_reply_count" in sql
        assert "commenter_channel_id = channel_id" in sql

    def test_source_is_fact_comment(self, sql):
        assert "fact_comment" in sql

    def test_grouped_by_video_id(self, sql):
        assert "GROUP BY video_id" in sql
