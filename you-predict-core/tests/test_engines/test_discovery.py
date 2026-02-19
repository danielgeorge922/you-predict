"""Tests for DiscoveryEngine — video_monitoring lifecycle."""

from datetime import UTC, datetime

from src.engines.discovery import DiscoveryEngine

_VIDEO_ID = "QJI0an6irrA"
_CHANNEL_ID = "UCX6OQ3DkcsbYNE6H8uQQuVA"
_PUBLISHED_AT = datetime(2026, 1, 7, 20, 0, 0, tzinfo=UTC)


class TestRegisterVideo:

    def test_returns_true_when_new_video(self, mock_bq):
        # run_merge returns 1 → new row inserted
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        is_new = engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        assert is_new is True

    def test_returns_false_when_already_registered(self, mock_bq):
        # run_merge returns 0 → WHEN NOT MATCHED didn't fire (already exists)
        mock_bq.run_merge.return_value = 0
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        is_new = engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        assert is_new is False

    def test_calls_run_merge_once(self, mock_bq):
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        mock_bq.run_merge.assert_called_once()

    def test_merge_sql_contains_video_monitoring_table(self, mock_bq):
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        sql = mock_bq.run_merge.call_args[0][0]
        assert "video_monitoring" in sql

    def test_merge_sql_contains_video_id(self, mock_bq):
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        sql = mock_bq.run_merge.call_args[0][0]
        assert _VIDEO_ID in sql

    def test_merge_sql_contains_channel_id(self, mock_bq):
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        sql = mock_bq.run_merge.call_args[0][0]
        assert _CHANNEL_ID in sql

    def test_merge_sql_is_insert_only(self, mock_bq):
        # Register should only INSERT, never UPDATE existing rows
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        sql = mock_bq.run_merge.call_args[0][0]
        assert "WHEN NOT MATCHED" in sql
        assert "WHEN MATCHED" not in sql

    def test_monitoring_until_is_72h_after_published(self, mock_bq):
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        sql = mock_bq.run_merge.call_args[0][0]
        # published_at = 2026-01-07T20:00:00 → monitoring_until = 2026-01-10T20:00:00
        assert "2026-01-10T20:00:00" in sql

    def test_is_active_set_true_on_insert(self, mock_bq):
        engine = DiscoveryEngine(mock_bq, monitoring_window_hours=72)
        engine.register_video(_VIDEO_ID, _CHANNEL_ID, _PUBLISHED_AT)
        sql = mock_bq.run_merge.call_args[0][0]
        assert "TRUE" in sql


class TestIsVideoRegistered:

    def test_returns_true_when_found(self, mock_bq):
        mock_bq.run_query.return_value = [{"1": 1}]
        engine = DiscoveryEngine(mock_bq)
        assert engine.is_video_registered(_VIDEO_ID) is True

    def test_returns_false_when_not_found(self, mock_bq):
        # mock_bq.run_query default returns []
        engine = DiscoveryEngine(mock_bq)
        assert engine.is_video_registered(_VIDEO_ID) is False

    def test_query_contains_video_id(self, mock_bq):
        engine = DiscoveryEngine(mock_bq)
        engine.is_video_registered(_VIDEO_ID)
        sql = mock_bq.run_query.call_args[0][0]
        assert _VIDEO_ID in sql


class TestExpireMonitoring:

    def test_returns_expired_count(self, mock_bq):
        mock_bq.run_merge.return_value = 3
        engine = DiscoveryEngine(mock_bq)
        expired = engine.expire_monitoring()
        assert expired == 3

    def test_calls_run_merge_once(self, mock_bq):
        engine = DiscoveryEngine(mock_bq)
        engine.expire_monitoring()
        mock_bq.run_merge.assert_called_once()

    def test_sql_sets_is_active_false(self, mock_bq):
        engine = DiscoveryEngine(mock_bq)
        engine.expire_monitoring()
        sql = mock_bq.run_merge.call_args[0][0]
        assert "is_active = FALSE" in sql

    def test_sql_checks_monitoring_until(self, mock_bq):
        engine = DiscoveryEngine(mock_bq)
        engine.expire_monitoring()
        sql = mock_bq.run_merge.call_args[0][0]
        assert "monitoring_until" in sql

    def test_sql_sets_inactive_reason(self, mock_bq):
        engine = DiscoveryEngine(mock_bq)
        engine.expire_monitoring()
        sql = mock_bq.run_merge.call_args[0][0]
        assert "monitoring_window_expired" in sql


class TestGetActiveVideoIds:

    def test_returns_video_ids(self, mock_bq):
        mock_bq.run_query.return_value = [
            {"video_id": "abc", "channel_id": "UCxyz", "is_active": True},
            {"video_id": "def", "channel_id": "UCxyz", "is_active": True},
        ]
        engine = DiscoveryEngine(mock_bq)
        ids = engine.get_active_video_ids()
        assert ids == ["abc", "def"]

    def test_returns_empty_when_none(self, mock_bq):
        engine = DiscoveryEngine(mock_bq)
        assert engine.get_active_video_ids() == []
