"""Tests for SnapshotTransformer using real YouTube statistics-only response."""

from datetime import UTC, datetime

from src.engines.transforms.base import TransformResult
from src.engines.transforms.snapshots import SnapshotTransformer

# Fixed timestamps for deterministic delta/hours assertions (midnight base → clean arithmetic)
_PUBLISHED_AT = datetime(2026, 1, 7, 0, 0, 0, tzinfo=UTC)
_CAPTURED_4H = datetime(2026, 1, 7, 4, 0, 0, tzinfo=UTC)    # exactly 4h later
_CAPTURED_24H = datetime(2026, 1, 8, 0, 0, 0, tzinfo=UTC)   # exactly 24h later
_VIDEO_ID = "QJI0an6irrA"
_CHANNEL_ID = "UCX6OQ3DkcsbYNE6H8uQQuVA"


class TestSnapshotTransform:
    """Tests for SnapshotTransformer.transform()."""

    def test_returns_fact_video_snapshot_result(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        result = transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        assert isinstance(result, TransformResult)
        assert result.table_name == "fact_video_snapshot"
        assert result.write_method == "merge"

    def test_snapshot_type_label(self, video_stats_only, mock_bq):
        # interval 4 → snapshot_type "4h"
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "'4h'" in sql

    def test_snapshot_type_label_24h(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=24,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_24H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "'24h'" in sql

    def test_view_count_in_sql(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "82949853" in sql

    def test_like_count_in_sql(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "2127007" in sql

    def test_comment_count_in_sql(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "95277" in sql

    def test_hours_since_publish_nominal(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        # hours_since_publish = interval_hours = 4
        assert "4 AS hours_since_publish" in sql

    def test_actual_hours_since_publish_exact(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        # captured exactly 4h later → actual_hours_since_publish = 4.0
        assert "4.0" in sql

    def test_days_since_publish_zero_within_same_day(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "0 AS days_since_publish" in sql

    def test_days_since_publish_one_after_24h(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=24,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_24H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "1 AS days_since_publish" in sql

    def test_deltas_null_when_no_previous(self, video_stats_only, mock_bq):
        # mock_bq.run_query returns [] → no previous snapshot
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "NULL AS views_delta" in sql
        assert "NULL AS likes_delta" in sql
        assert "NULL AS comments_delta" in sql

    def test_deltas_computed_when_previous_exists(
        self, video_stats_only, mock_bq_with_prev_snapshot
    ):
        transformer = SnapshotTransformer(mock_bq_with_prev_snapshot)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq_with_prev_snapshot.run_merge.call_args[0][0]
        # 82_949_853 - 80_000_000 = 2_949_853
        assert "2949853" in sql
        # 2_127_007 - 2_100_000 = 27_007
        assert "27007" in sql
        # 95_277 - 90_000 = 5_277
        assert "5277" in sql

    def test_video_id_in_sql(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert _VIDEO_ID in sql
        assert _CHANNEL_ID in sql

    def test_merge_on_video_id_and_snapshot_type(self, video_stats_only, mock_bq):
        transformer = SnapshotTransformer(mock_bq)
        transformer.transform(
            raw_item=video_stats_only,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            interval_hours=4,
            published_at=_PUBLISHED_AT,
            captured_at=_CAPTURED_4H,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "T.video_id = S.video_id" in sql
        assert "T.snapshot_type = S.snapshot_type" in sql
