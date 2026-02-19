"""Tests for src.models.monitoring."""

from datetime import UTC, datetime

from src.models.monitoring import VideoMonitoring


class TestVideoMonitoring:
    def test_creation(self):
        now = datetime(2026, 2, 15, 8, 0, tzinfo=UTC)
        vm = VideoMonitoring(
            video_id="abc123",
            channel_id="UC123",
            published_at=now,
            discovered_at=now,
            monitoring_until=datetime(2026, 2, 18, 8, 0, tzinfo=UTC),
            first_seen_at=now,
        )
        assert vm.video_id == "abc123"
        assert vm.is_active is True
        assert vm.inactive_reason is None

    def test_inactive(self):
        now = datetime(2026, 2, 15, 8, 0, tzinfo=UTC)
        vm = VideoMonitoring(
            video_id="abc123",
            channel_id="UC123",
            published_at=now,
            discovered_at=now,
            monitoring_until=now,
            first_seen_at=now,
            is_active=False,
            inactive_reason="monitoring_window_expired",
        )
        assert vm.is_active is False
        assert vm.inactive_reason == "monitoring_window_expired"
