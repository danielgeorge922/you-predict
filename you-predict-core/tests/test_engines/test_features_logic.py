"""Functional tests for feature computation logic.

Uses DuckDB as an in-memory SQL engine. Each test class:
  1. Seeds DuckDB with sample rows (what BigQuery tables would contain)
  2. Runs the equivalent transformation SQL (same logic as the .sql files,
     expressed in DuckDB-compatible syntax)
  3. Asserts computed column values match handwritten expected outputs

Jan 1 2026 = Thursday, Jan 3 = Saturday, Jan 4 = Sunday, Jan 5 = Monday,
Jan 10 = Saturday (used in temporal tests).
"""

import duckdb
import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _df(conn, sql: str):
    """Execute SQL and return a pandas DataFrame."""
    return conn.execute(sql).fetchdf()


# ---------------------------------------------------------------------------
# Video performance — pivoting, velocities, PERCENT_RANK
# ---------------------------------------------------------------------------


class TestVideoPerformanceLogic:
    """Verify pivot, velocity, and channel-relative percentile logic."""

    @pytest.fixture
    def conn(self):
        con = duckdb.connect()
        con.execute("""
            CREATE TABLE fact_video_snapshot (
                video_id      VARCHAR,
                channel_id    VARCHAR,
                snapshot_type VARCHAR,
                view_count    BIGINT,
                like_count    BIGINT,
                comment_count BIGINT
            )
        """)
        # vid1: moderate start (1k views @ 1h), accelerates to 24k by 24h
        # vid2: fast start (2k views @ 1h), tapers to 12k by 24h
        con.execute("""
            INSERT INTO fact_video_snapshot VALUES
            ('vid1', 'chan1', '1h',  1000,  50,   5),
            ('vid1', 'chan1', '2h',  3000,  150,  15),
            ('vid1', 'chan1', '24h', 24000, 1200, 120),
            ('vid2', 'chan1', '1h',  2000,  100,  10),
            ('vid2', 'chan1', '2h',  4000,  200,  20),
            ('vid2', 'chan1', '24h', 12000, 600,  60)
        """)
        yield con
        con.close()

    def _transform(self, conn):
        """Run the pivot + velocity + PERCENT_RANK transformation."""
        return _df(conn, """
            WITH pivoted AS (
                SELECT
                    video_id, channel_id,
                    MAX(CASE WHEN snapshot_type = '1h'  THEN view_count    END) AS views_1h,
                    MAX(CASE WHEN snapshot_type = '2h'  THEN view_count    END) AS views_2h,
                    MAX(CASE WHEN snapshot_type = '24h' THEN view_count    END) AS views_24h,
                    MAX(CASE WHEN snapshot_type = '1h'  THEN like_count    END) AS likes_1h,
                    MAX(CASE WHEN snapshot_type = '24h' THEN like_count    END) AS likes_24h,
                    MAX(CASE WHEN snapshot_type = '1h'  THEN comment_count END) AS comments_1h,
                    MAX(CASE WHEN snapshot_type = '24h' THEN comment_count END) AS comments_24h
                FROM fact_video_snapshot
                GROUP BY video_id, channel_id
            ),
            computed AS (
                SELECT
                    video_id, channel_id,
                    views_1h, views_2h, views_24h,
                    likes_1h, likes_24h,
                    comments_1h, comments_24h,

                    views_1h  / 1.0  AS view_velocity_1h,
                    views_2h  / 2.0  AS view_velocity_2h,
                    views_24h / 24.0 AS view_velocity_24h,

                    likes_1h    / 1.0 AS like_velocity_1h,
                    comments_1h / 1.0 AS comment_velocity_1h,

                    GREATEST(
                        COALESCE(views_1h  / 1.0,  0),
                        COALESCE(views_2h  / 2.0,  0),
                        COALESCE(views_24h / 24.0, 0)
                    ) AS peak_velocity,

                    (views_24h / 24.0 - views_1h / 1.0)
                        / NULLIF(views_1h / 1.0, 0) AS engagement_acceleration,

                    likes_24h    / NULLIF(views_24h::DOUBLE, 0) AS like_view_ratio,
                    comments_24h / NULLIF(views_24h::DOUBLE, 0) AS comment_view_ratio,

                    PERCENT_RANK() OVER (
                        PARTITION BY channel_id ORDER BY views_24h
                    ) AS performance_vs_channel_avg

                FROM pivoted
            )
            SELECT * FROM computed ORDER BY video_id
        """)

    def _row(self, conn, video_id: str):
        df = self._transform(conn)
        return df[df["video_id"] == video_id].iloc[0]

    def test_views_pivoted_from_snapshot_type_correctly(self, conn):
        vid1 = self._row(conn, "vid1")
        assert vid1["views_1h"] == 1000
        assert vid1["views_24h"] == 24000

    def test_likes_pivoted_correctly(self, conn):
        vid1 = self._row(conn, "vid1")
        assert vid1["likes_1h"] == 50
        assert vid1["likes_24h"] == 1200

    def test_comments_pivoted_correctly(self, conn):
        vid1 = self._row(conn, "vid1")
        assert vid1["comments_1h"] == 5
        assert vid1["comments_24h"] == 120

    def test_view_velocity_1h_equals_views_divided_by_1(self, conn):
        vid1 = self._row(conn, "vid1")
        vid2 = self._row(conn, "vid2")
        assert vid1["view_velocity_1h"] == pytest.approx(1000.0)
        assert vid2["view_velocity_1h"] == pytest.approx(2000.0)

    def test_view_velocity_24h_equals_views_divided_by_24(self, conn):
        vid1 = self._row(conn, "vid1")
        vid2 = self._row(conn, "vid2")
        assert vid1["view_velocity_24h"] == pytest.approx(24000 / 24.0)   # 1000.0
        assert vid2["view_velocity_24h"] == pytest.approx(12000 / 24.0)   # 500.0

    def test_view_velocity_2h_equals_views_divided_by_2(self, conn):
        vid1 = self._row(conn, "vid1")
        # views_2h=3000 / 2.0 = 1500
        assert vid1["view_velocity_2h"] == pytest.approx(1500.0)

    def test_peak_velocity_is_max_across_interval_velocities(self, conn):
        vid1 = self._row(conn, "vid1")
        vid2 = self._row(conn, "vid2")
        # vid1: max(1000, 1500, 1000) = 1500.0
        assert vid1["peak_velocity"] == pytest.approx(1500.0)
        # vid2: max(2000, 2000, 500) = 2000.0
        assert vid2["peak_velocity"] == pytest.approx(2000.0)

    def test_engagement_acceleration_flat_trajectory(self, conn):
        # vid1: velocity at 24h (1000) equals velocity at 1h (1000) → 0.0
        vid1 = self._row(conn, "vid1")
        assert vid1["engagement_acceleration"] == pytest.approx(0.0)

    def test_engagement_acceleration_declining_trajectory(self, conn):
        # vid2: velocity dropped from 2000 (1h) to 500 (24h) → (500-2000)/2000 = -0.75
        vid2 = self._row(conn, "vid2")
        assert vid2["engagement_acceleration"] == pytest.approx(-0.75)

    def test_like_view_ratio(self, conn):
        vid1 = self._row(conn, "vid1")
        # 1200 likes / 24000 views = 0.05
        assert vid1["like_view_ratio"] == pytest.approx(1200 / 24000)

    def test_comment_view_ratio(self, conn):
        vid1 = self._row(conn, "vid1")
        # 120 comments / 24000 views = 0.005
        assert vid1["comment_view_ratio"] == pytest.approx(120 / 24000)

    def test_performance_vs_channel_avg_highest_gets_1(self, conn):
        # vid1 has more 24h views than vid2 → PERCENT_RANK = 1.0
        vid1 = self._row(conn, "vid1")
        assert vid1["performance_vs_channel_avg"] == pytest.approx(1.0)

    def test_performance_vs_channel_avg_lowest_gets_0(self, conn):
        # vid2 has fewer 24h views → PERCENT_RANK = 0.0
        vid2 = self._row(conn, "vid2")
        assert vid2["performance_vs_channel_avg"] == pytest.approx(0.0)

    def test_percent_rank_single_video_is_zero(self, conn):
        """Single video in a channel always gets PERCENT_RANK = 0."""
        con = duckdb.connect()
        df = _df(con, """
            WITH pivoted AS (
                SELECT 'vid_only' AS video_id, 'chan_solo' AS channel_id, 5000 AS views_24h
            )
            SELECT PERCENT_RANK() OVER (PARTITION BY channel_id ORDER BY views_24h)
                AS performance_vs_channel_avg
            FROM pivoted
        """)
        assert df["performance_vs_channel_avg"].iloc[0] == pytest.approx(0.0)
        con.close()

    def test_percent_rank_is_partitioned_per_channel(self, conn):
        """Videos from different channels do not affect each other's PERCENT_RANK."""
        con = duckdb.connect()
        df = _df(con, """
            WITH pivoted AS (
                SELECT 'vid_a' AS video_id, 'chan_x' AS channel_id, 10000 AS views_24h
                UNION ALL
                SELECT 'vid_b', 'chan_y', 10000
                UNION ALL
                SELECT 'vid_c', 'chan_y', 5000
            )
            SELECT
                video_id,
                PERCENT_RANK() OVER (PARTITION BY channel_id ORDER BY views_24h)
                    AS performance_vs_channel_avg
            FROM pivoted
            ORDER BY video_id
        """)
        by_id = dict(zip(df["video_id"], df["performance_vs_channel_avg"]))
        # vid_a is alone in chan_x → 0.0
        assert by_id["vid_a"] == pytest.approx(0.0)
        # vid_b highest in chan_y → 1.0
        assert by_id["vid_b"] == pytest.approx(1.0)
        # vid_c lowest in chan_y → 0.0
        assert by_id["vid_c"] == pytest.approx(0.0)
        con.close()

    def test_missing_interval_snapshot_is_null(self, conn):
        """Intervals with no snapshot row produce NULL (not 0) via MAX(CASE WHEN)."""
        vid1 = self._row(conn, "vid1")
        # We only inserted 1h, 2h, 24h for vid1 — e.g. 4h was never inserted
        # (No 4h column in this minimal query, but the pattern must hold)
        # Verify via direct query
        df = _df(conn, """
            SELECT MAX(CASE WHEN snapshot_type = '4h' THEN view_count END) AS views_4h
            FROM fact_video_snapshot WHERE video_id = 'vid1'
        """)
        assert df["views_4h"].iloc[0] is None or df["views_4h"].isna().iloc[0]


# ---------------------------------------------------------------------------
# Channel features — subscriber tier, upload frequency, growth rate
# ---------------------------------------------------------------------------


class TestChannelFeatureLogic:
    """Verify subscriber tier bucketing, upload frequency, and growth rate."""

    @pytest.fixture
    def conn(self):
        con = duckdb.connect()
        yield con
        con.close()

    def _tier(self, conn, sub_count: int) -> str:
        row = conn.execute(f"""
            SELECT CASE
                WHEN {sub_count} < 10000   THEN 'micro'
                WHEN {sub_count} < 100000  THEN 'small'
                WHEN {sub_count} < 1000000 THEN 'medium'
                ELSE                            'large'
            END
        """).fetchone()
        return row[0]

    def test_subscriber_tier_micro(self, conn):
        assert self._tier(conn, 5_000) == "micro"

    def test_subscriber_tier_small(self, conn):
        assert self._tier(conn, 50_000) == "small"

    def test_subscriber_tier_medium(self, conn):
        assert self._tier(conn, 500_000) == "medium"

    def test_subscriber_tier_large(self, conn):
        assert self._tier(conn, 2_000_000) == "large"

    def test_subscriber_tier_boundary_10k_is_small_not_micro(self, conn):
        # 10000 is NOT < 10000, so it falls to 'small'
        assert self._tier(conn, 10_000) == "small"

    def test_subscriber_tier_boundary_1m_is_large_not_medium(self, conn):
        # 1_000_000 is NOT < 1_000_000, so it falls to 'large'
        assert self._tier(conn, 1_000_000) == "large"

    def test_upload_frequency_7d_one_per_day(self, conn):
        row = conn.execute("SELECT 7 / 7.0").fetchone()
        assert row[0] == pytest.approx(1.0)

    def test_upload_frequency_30d_half_per_day(self, conn):
        row = conn.execute("SELECT 15 / 30.0").fetchone()
        assert row[0] == pytest.approx(0.5)

    def test_subscriber_growth_rate_positive(self, conn):
        # subs went from 100k → 110k → growth = (110k - 100k) / 100k = 0.1
        row = conn.execute(
            "SELECT (110000 - 100000) / NULLIF(100000.0, 0)"
        ).fetchone()
        assert row[0] == pytest.approx(0.1)

    def test_subscriber_growth_rate_null_when_no_prior_snapshot(self, conn):
        # no snapshot 30 days ago → denominator is NULL → result is NULL
        row = conn.execute(
            "SELECT 110000 / NULLIF(NULL::DOUBLE, 0)"
        ).fetchone()
        assert row[0] is None

    def test_view_consistency_score_perfectly_consistent(self, conn):
        # stddev=0 → 1 / (1 + 0/avg) = 1.0
        row = conn.execute("SELECT 1.0 / (1.0 + 0.0 / NULLIF(1000.0, 0))").fetchone()
        assert row[0] == pytest.approx(1.0)

    def test_view_consistency_score_high_variance_reduces_score(self, conn):
        # avg=1000, stddev=500 → CV=0.5 → 1 / (1 + 0.5) = 0.667
        row = conn.execute("SELECT 1.0 / (1.0 + 500.0 / NULLIF(1000.0, 0))").fetchone()
        assert row[0] == pytest.approx(1.0 / 1.5)

    def test_avg_views_per_video_computed_across_30d(self, conn):
        df = _df(conn, """
            WITH recent_videos (channel_id, view_count) AS (
                VALUES ('chan1', 5000), ('chan1', 15000), ('chan1', 10000)
            )
            SELECT channel_id, CAST(AVG(view_count) AS BIGINT) AS avg_views_per_video_30d
            FROM recent_videos GROUP BY channel_id
        """)
        # (5000 + 15000 + 10000) / 3 = 10000
        assert df["avg_views_per_video_30d"].iloc[0] == 10000


# ---------------------------------------------------------------------------
# Video content — title signals and duration buckets
# ---------------------------------------------------------------------------


class TestVideoContentLogic:
    """Verify title feature extraction and duration bucketing."""

    @pytest.fixture
    def conn(self):
        con = duckdb.connect()
        yield con
        con.close()

    def test_title_length(self, conn):
        row = conn.execute("SELECT LENGTH('Hello World')").fetchone()
        assert row[0] == 11

    def test_title_word_count_two_words(self, conn):
        row = conn.execute(
            "SELECT array_length(string_split(trim('Hello World'), ' '))"
        ).fetchone()
        assert row[0] == 2

    def test_title_word_count_leading_trailing_spaces_trimmed(self, conn):
        row = conn.execute(
            "SELECT array_length(string_split(trim('  Hello World  '), ' '))"
        ).fetchone()
        assert row[0] == 2

    def test_title_has_number_true(self, conn):
        row = conn.execute(r"SELECT regexp_matches('Top 10 Videos', '\d')").fetchone()
        assert row[0] is True

    def test_title_has_number_false(self, conn):
        row = conn.execute(r"SELECT regexp_matches('Hello World', '\d')").fetchone()
        assert row[0] is False

    def test_title_has_question_true(self, conn):
        row = conn.execute("SELECT strpos('Is this real?', '?') > 0").fetchone()
        assert row[0] is True

    def test_title_has_question_false(self, conn):
        row = conn.execute("SELECT strpos('Hello World', '?') > 0").fetchone()
        assert row[0] is False

    def test_title_has_brackets_square_bracket(self, conn):
        row = conn.execute(
            r"SELECT regexp_matches('[Official] Video', '\[|\(')"
        ).fetchone()
        assert row[0] is True

    def test_title_has_brackets_round_bracket(self, conn):
        row = conn.execute(
            r"SELECT regexp_matches('Song (Live)', '\[|\(')"
        ).fetchone()
        assert row[0] is True

    def test_title_has_brackets_false(self, conn):
        row = conn.execute(
            r"SELECT regexp_matches('Hello World', '\[|\(')"
        ).fetchone()
        assert row[0] is False

    def test_title_caps_ratio_half_uppercase(self, conn):
        # "HELLO world": uppercase=H,E,L,L,O (5), total letters=10 → 0.5
        row = conn.execute(r"""
            SELECT
                LENGTH(regexp_replace('HELLO world', '[^A-Z]', '', 'g'))::DOUBLE
                / NULLIF(LENGTH(regexp_replace('HELLO world', '[^a-zA-Z]', '', 'g')), 0)
        """).fetchone()
        assert row[0] == pytest.approx(0.5)

    def test_title_caps_ratio_all_lowercase(self, conn):
        row = conn.execute(r"""
            SELECT
                LENGTH(regexp_replace('hello world', '[^A-Z]', '', 'g'))::DOUBLE
                / NULLIF(LENGTH(regexp_replace('hello world', '[^a-zA-Z]', '', 'g')), 0)
        """).fetchone()
        assert row[0] == pytest.approx(0.0)

    def test_title_caps_ratio_all_uppercase(self, conn):
        row = conn.execute(r"""
            SELECT
                LENGTH(regexp_replace('HELLO', '[^A-Z]', '', 'g'))::DOUBLE
                / NULLIF(LENGTH(regexp_replace('HELLO', '[^a-zA-Z]', '', 'g')), 0)
        """).fetchone()
        assert row[0] == pytest.approx(1.0)

    def _power_word_count(self, conn, title: str) -> int:
        row = conn.execute(f"""
            SELECT (
                CASE WHEN regexp_matches(lower('{title}'), 'insane|secret|shocking|unbelievable|incredible|amazing')    THEN 1 ELSE 0 END
              + CASE WHEN regexp_matches(lower('{title}'), 'ultimate|exposed|revealed|banned|warning|urgent')           THEN 1 ELSE 0 END
              + CASE WHEN regexp_matches(lower('{title}'), 'breaking|exclusive|epic|crazy|huge|massive')                THEN 1 ELSE 0 END
              + CASE WHEN regexp_matches(lower('{title}'), 'destroyed|ruined|worst|best|perfect|impossible')            THEN 1 ELSE 0 END
              + CASE WHEN regexp_matches(lower('{title}'), 'never|always|finally|gone wrong|not clickbait')             THEN 1 ELSE 0 END
            )
        """).fetchone()
        return row[0]

    def test_power_word_count_zero_for_neutral_title(self, conn):
        assert self._power_word_count(conn, "My First Video") == 0

    def test_power_word_count_one_match(self, conn):
        assert self._power_word_count(conn, "This is Amazing!") == 1

    def test_power_word_count_two_matches_different_groups(self, conn):
        # "amazing" (group 1) + "exposed" (group 2) → 2
        assert self._power_word_count(conn, "Amazing Exposed Content") == 2

    def test_duration_bucket_short_under_60s(self, conn):
        row = conn.execute("""
            SELECT CASE WHEN 30 < 60 THEN 'short' WHEN 30 < 600 THEN 'medium'
                        WHEN 30 < 1800 THEN 'long' ELSE 'very_long' END
        """).fetchone()
        assert row[0] == "short"

    def test_duration_bucket_medium_60_to_600s(self, conn):
        row = conn.execute("""
            SELECT CASE WHEN 300 < 60 THEN 'short' WHEN 300 < 600 THEN 'medium'
                        WHEN 300 < 1800 THEN 'long' ELSE 'very_long' END
        """).fetchone()
        assert row[0] == "medium"

    def test_duration_bucket_long_600_to_1800s(self, conn):
        row = conn.execute("""
            SELECT CASE WHEN 900 < 60 THEN 'short' WHEN 900 < 600 THEN 'medium'
                        WHEN 900 < 1800 THEN 'long' ELSE 'very_long' END
        """).fetchone()
        assert row[0] == "long"

    def test_duration_bucket_very_long_above_1800s(self, conn):
        row = conn.execute("""
            SELECT CASE WHEN 3600 < 60 THEN 'short' WHEN 3600 < 600 THEN 'medium'
                        WHEN 3600 < 1800 THEN 'long' ELSE 'very_long' END
        """).fetchone()
        assert row[0] == "very_long"

    def test_duration_bucket_boundary_exactly_60s_is_medium(self, conn):
        # 60 is NOT < 60, falls through to 'medium'
        row = conn.execute("""
            SELECT CASE WHEN 60 < 60 THEN 'short' WHEN 60 < 600 THEN 'medium'
                        WHEN 60 < 1800 THEN 'long' ELSE 'very_long' END
        """).fetchone()
        assert row[0] == "medium"

    def test_description_link_count_two_urls(self, conn):
        row = conn.execute(r"""
            SELECT array_length(regexp_extract_all(
                'See https://youtube.com and http://twitter.com for more',
                'https?://[^\s]+'
            ))
        """).fetchone()
        assert row[0] == 2

    def test_description_link_count_zero_when_no_urls(self, conn):
        row = conn.execute(r"""
            SELECT array_length(regexp_extract_all('No links here at all', 'https?://[^\s]+'))
        """).fetchone()
        assert row[0] == 0


# ---------------------------------------------------------------------------
# Temporal — publish time features and window functions
# ---------------------------------------------------------------------------


class TestTemporalLogic:
    """Verify hour/day extraction, weekend flag, LAG, and COUNT OVER."""

    # Jan 1 2026 = Thursday, Jan 3 = Saturday, Jan 4 = Sunday, Jan 5 = Monday
    _THURSDAY  = "'2026-01-01 09:00:00'::TIMESTAMP"
    _SATURDAY  = "'2026-01-03 14:00:00'::TIMESTAMP"
    _SUNDAY    = "'2026-01-04 20:00:00'::TIMESTAMP"
    _MONDAY    = "'2026-01-05 08:00:00'::TIMESTAMP"

    @pytest.fixture
    def conn(self):
        con = duckdb.connect()
        # Three videos: vid1 and vid3 on same day (Jan 1), vid2 on Jan 3
        con.execute("""
            CREATE TABLE video_monitoring (
                video_id    VARCHAR,
                channel_id  VARCHAR,
                published_at TIMESTAMP
            )
        """)
        con.execute("""
            INSERT INTO video_monitoring VALUES
            ('vid1', 'chan1', '2026-01-01 09:00:00'),
            ('vid3', 'chan1', '2026-01-01 18:00:00'),
            ('vid2', 'chan1', '2026-01-03 14:00:00')
        """)
        yield con
        con.close()

    def test_hour_of_day_extracted_correctly(self, conn):
        row = conn.execute(
            f"SELECT EXTRACT(HOUR FROM {self._SATURDAY})"
        ).fetchone()
        assert row[0] == 14

    def test_day_of_week_sunday_maps_to_1(self, conn):
        # DuckDB DOW: Sun=0; BigQuery DAYOFWEEK: Sun=1; conversion: DOW+1
        row = conn.execute(
            f"SELECT EXTRACT(DOW FROM {self._SUNDAY}) + 1"
        ).fetchone()
        assert row[0] == 1  # Sunday

    def test_day_of_week_monday_maps_to_2(self, conn):
        row = conn.execute(
            f"SELECT EXTRACT(DOW FROM {self._MONDAY}) + 1"
        ).fetchone()
        assert row[0] == 2  # Monday

    def test_day_of_week_saturday_maps_to_7(self, conn):
        row = conn.execute(
            f"SELECT EXTRACT(DOW FROM {self._SATURDAY}) + 1"
        ).fetchone()
        assert row[0] == 7  # Saturday

    def test_is_weekend_publish_sunday_is_true(self, conn):
        row = conn.execute(
            f"SELECT (EXTRACT(DOW FROM {self._SUNDAY}) + 1) IN (1, 7)"
        ).fetchone()
        assert row[0] is True

    def test_is_weekend_publish_saturday_is_true(self, conn):
        row = conn.execute(
            f"SELECT (EXTRACT(DOW FROM {self._SATURDAY}) + 1) IN (1, 7)"
        ).fetchone()
        assert row[0] is True

    def test_is_weekend_publish_monday_is_false(self, conn):
        row = conn.execute(
            f"SELECT (EXTRACT(DOW FROM {self._MONDAY}) + 1) IN (1, 7)"
        ).fetchone()
        assert row[0] is False

    def test_is_weekend_publish_thursday_is_false(self, conn):
        row = conn.execute(
            f"SELECT (EXTRACT(DOW FROM {self._THURSDAY}) + 1) IN (1, 7)"
        ).fetchone()
        assert row[0] is False

    def _lag_df(self, conn):
        """Shared helper: compute days_since_last_upload for all videos."""
        return _df(conn, """
            WITH windowed AS (
                SELECT
                    video_id,
                    published_at,
                    DATEDIFF('day',
                        LAG(published_at::DATE) OVER (PARTITION BY channel_id ORDER BY published_at),
                        published_at::DATE
                    ) AS days_since_last_upload
                FROM video_monitoring
            )
            SELECT video_id, days_since_last_upload FROM windowed ORDER BY published_at
        """)

    def test_days_since_last_upload_first_upload_is_null(self, conn):
        """First upload for a channel has no prior — LAG returns NULL → NULL gap."""
        import pandas as pd
        df = self._lag_df(conn)
        by_id = dict(zip(df["video_id"], df["days_since_last_upload"]))
        assert pd.isna(by_id["vid1"])

    def test_days_since_last_upload_same_day_is_zero(self, conn):
        """Two uploads on the same calendar day → gap = 0."""
        df = self._lag_df(conn)
        by_id = dict(zip(df["video_id"], df["days_since_last_upload"]))
        # vid3 published Jan 1 18:00, prior upload vid1 was Jan 1 09:00 → same calendar day
        assert by_id["vid3"] == 0

    def test_days_since_last_upload_two_day_gap(self, conn):
        """Upload on Jan 3 with prior on Jan 1 → gap = 2 days."""
        df = self._lag_df(conn)
        by_id = dict(zip(df["video_id"], df["days_since_last_upload"]))
        assert by_id["vid2"] == 2

    def test_videos_published_same_day_channel_counts_same_day_videos(self, conn):
        """vid1 and vid3 both published Jan 1 on chan1 → each gets count 2."""
        df = _df(conn, """
            SELECT video_id,
                COUNT(*) OVER (
                    PARTITION BY channel_id, published_at::DATE
                ) AS videos_published_same_day_channel
            FROM video_monitoring
        """)
        by_id = dict(zip(df["video_id"], df["videos_published_same_day_channel"]))
        assert by_id["vid1"] == 2
        assert by_id["vid3"] == 2

    def test_videos_published_same_day_channel_solo_upload_is_one(self, conn):
        """vid2 is the only upload on Jan 3 → count = 1."""
        df = _df(conn, """
            SELECT video_id,
                COUNT(*) OVER (
                    PARTITION BY channel_id, published_at::DATE
                ) AS videos_published_same_day_channel
            FROM video_monitoring
        """)
        by_id = dict(zip(df["video_id"], df["videos_published_same_day_channel"]))
        assert by_id["vid2"] == 1


# ---------------------------------------------------------------------------
# Comment aggregates — sentiment, toxicity, diversity, engagement
# ---------------------------------------------------------------------------


class TestCommentAggregatesLogic:
    """Verify aggregation logic for comment-level features."""

    @pytest.fixture
    def conn(self):
        con = duckdb.connect()
        con.execute("""
            CREATE TABLE fact_comment (
                video_id              VARCHAR,
                channel_id            VARCHAR,
                comment_id            VARCHAR,
                comment_text          VARCHAR,
                sentiment_compound    DOUBLE,
                toxicity_score        DOUBLE,
                severe_toxicity_score DOUBLE,
                insult_score          DOUBLE,
                identity_attack_score DOUBLE,
                like_count            INTEGER,
                reply_count           INTEGER,
                commenter_channel_id  VARCHAR,
                sample_strategy       VARCHAR
            )
        """)
        # c1: positive, low toxicity, 10 likes, from user1
        # c2: negative, high toxicity, 0 likes, from user2
        # c3: neutral, low toxicity, 5 likes, commenter = channel owner (creator reply)
        con.execute("""
            INSERT INTO fact_comment VALUES
            ('vid1','chan1','c1','Great video!',  0.8, 0.10, 0.05, 0.10, 0.05, 10, 2, 'user1', 'top'),
            ('vid1','chan1','c2','I hate this',  -0.7, 0.70, 0.40, 0.80, 0.60,  0, 0, 'user2', 'top'),
            ('vid1','chan1','c3','ok I guess',    0.0, 0.20, 0.10, 0.10, 0.10,  5, 1, 'chan1', 'top')
        """)
        yield con
        con.close()

    def _agg(self, conn, video_id: str = "vid1"):
        return _df(conn, f"""
            SELECT
                video_id,
                COUNT(*)                                              AS comments_sampled,
                AVG(sentiment_compound)                               AS avg_sentiment_compound,
                COUNT(*) FILTER (WHERE sentiment_compound >  0.05)
                    / COUNT(*)::DOUBLE                                AS positive_ratio,
                COUNT(*) FILTER (WHERE sentiment_compound < -0.05)
                    / COUNT(*)::DOUBLE                                AS negative_ratio,
                AVG(toxicity_score)                                   AS avg_toxicity,
                COUNT(*) FILTER (WHERE toxicity_score        > 0.5)
                    / COUNT(*)::DOUBLE                                AS toxic_ratio,
                COUNT(*) FILTER (WHERE severe_toxicity_score > 0.5)
                    / COUNT(*)::DOUBLE                                AS severe_toxic_ratio,
                MAX(toxicity_score)                                   AS max_toxicity,
                MAX(identity_attack_score)                            AS max_identity_attack,
                AVG(like_count::DOUBLE)                               AS avg_comment_likes,
                MAX(like_count)                                       AS max_comment_likes,
                AVG(reply_count::DOUBLE)                              AS avg_reply_count,
                COUNT(DISTINCT commenter_channel_id)
                    / COUNT(*)::DOUBLE                                AS unique_commenter_ratio,
                AVG(LENGTH(comment_text))                             AS avg_comment_length,
                COUNT(*) FILTER (WHERE ends_with(trim(comment_text), '?'))
                    / COUNT(*)::DOUBLE                                AS question_comment_ratio,
                COUNT(*) FILTER (WHERE commenter_channel_id = channel_id)
                                                                      AS creator_reply_count
            FROM fact_comment
            WHERE video_id = '{video_id}'
            GROUP BY video_id
        """).iloc[0]

    def test_comments_sampled_count(self, conn):
        row = self._agg(conn)
        assert row["comments_sampled"] == 3

    def test_avg_sentiment_compound(self, conn):
        row = self._agg(conn)
        # (0.8 + -0.7 + 0.0) / 3 = 0.1 / 3
        assert row["avg_sentiment_compound"] == pytest.approx(0.1 / 3)

    def test_positive_ratio_one_of_three(self, conn):
        row = self._agg(conn)
        # c1 (0.8 > 0.05) → 1/3
        assert row["positive_ratio"] == pytest.approx(1 / 3)

    def test_negative_ratio_one_of_three(self, conn):
        row = self._agg(conn)
        # c2 (-0.7 < -0.05) → 1/3
        assert row["negative_ratio"] == pytest.approx(1 / 3)

    def test_avg_toxicity(self, conn):
        row = self._agg(conn)
        # (0.10 + 0.70 + 0.20) / 3 = 1.0 / 3
        assert row["avg_toxicity"] == pytest.approx(1.0 / 3)

    def test_toxic_ratio_threshold_05(self, conn):
        row = self._agg(conn)
        # c2 (0.70 > 0.5) → 1/3
        assert row["toxic_ratio"] == pytest.approx(1 / 3)

    def test_severe_toxic_ratio_none_exceed_threshold(self, conn):
        row = self._agg(conn)
        # max severe_toxicity_score is 0.40, below 0.5 threshold
        assert row["severe_toxic_ratio"] == pytest.approx(0.0)

    def test_max_toxicity(self, conn):
        row = self._agg(conn)
        assert row["max_toxicity"] == pytest.approx(0.70)

    def test_max_identity_attack(self, conn):
        row = self._agg(conn)
        assert row["max_identity_attack"] == pytest.approx(0.60)

    def test_avg_comment_likes(self, conn):
        row = self._agg(conn)
        # (10 + 0 + 5) / 3 = 5.0
        assert row["avg_comment_likes"] == pytest.approx(5.0)

    def test_max_comment_likes(self, conn):
        row = self._agg(conn)
        assert row["max_comment_likes"] == 10

    def test_avg_reply_count(self, conn):
        row = self._agg(conn)
        # (2 + 0 + 1) / 3 = 1.0
        assert row["avg_reply_count"] == pytest.approx(1.0)

    def test_unique_commenter_ratio_all_different(self, conn):
        row = self._agg(conn)
        # user1, user2, chan1 — all distinct → 3/3 = 1.0
        assert row["unique_commenter_ratio"] == pytest.approx(1.0)

    def test_unique_commenter_ratio_with_duplicate_commenter(self, conn):
        conn.execute("""
            INSERT INTO fact_comment VALUES
            ('vid2','chan1','c4','Again',  0.5, 0.1, 0.0, 0.0, 0.0, 0, 0, 'user1', 'top'),
            ('vid2','chan1','c5','More',   0.5, 0.1, 0.0, 0.0, 0.0, 0, 0, 'user1', 'top'),
            ('vid2','chan1','c6','Other',  0.5, 0.1, 0.0, 0.0, 0.0, 0, 0, 'user2', 'top')
        """)
        row = self._agg(conn, "vid2")
        # 2 distinct (user1, user2) / 3 total = 0.667
        assert row["unique_commenter_ratio"] == pytest.approx(2 / 3)

    def test_avg_comment_length(self, conn):
        row = self._agg(conn)
        # "Great video!"=12, "I hate this"=11, "ok I guess"=10 → (12+11+10)/3=11
        assert row["avg_comment_length"] == pytest.approx(11.0)

    def test_question_comment_ratio_zero_when_no_questions(self, conn):
        row = self._agg(conn)
        # none of the 3 comments end with '?'
        assert row["question_comment_ratio"] == pytest.approx(0.0)

    def test_question_comment_ratio_half_when_one_of_two(self, conn):
        conn.execute("""
            INSERT INTO fact_comment VALUES
            ('vid3','chan1','c7','Is this good?', 0.5, 0.1, 0.0, 0.0, 0.0, 0, 0, 'user1', 'top'),
            ('vid3','chan1','c8','Not a question', 0.0, 0.1, 0.0, 0.0, 0.0, 0, 0, 'user2', 'top')
        """)
        row = self._agg(conn, "vid3")
        assert row["question_comment_ratio"] == pytest.approx(0.5)

    def test_creator_reply_count(self, conn):
        row = self._agg(conn)
        # c3: commenter_channel_id='chan1' = channel_id='chan1' → count = 1
        assert row["creator_reply_count"] == 1

    def test_creator_reply_count_zero_when_no_creator_comments(self, conn):
        conn.execute("""
            INSERT INTO fact_comment VALUES
            ('vid4','chan1','c9','Hello', 0.5, 0.1, 0.0, 0.0, 0.0, 0, 0, 'user_x', 'top')
        """)
        row = self._agg(conn, "vid4")
        assert row["creator_reply_count"] == 0
