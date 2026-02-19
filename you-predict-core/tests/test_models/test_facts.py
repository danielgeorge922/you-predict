"""Tests for src.models.facts."""

from datetime import UTC, date, datetime

from src.models.facts import FactChannelSnapshot, FactComment, FactVideoSnapshot


class TestFactChannelSnapshot:
    def test_minimal(self):
        snap = FactChannelSnapshot(
            snapshot_date=date(2026, 2, 15),
            snapshot_ts=datetime(2026, 2, 15, 0, 0, tzinfo=UTC),
            channel_id="UC123",
        )
        assert snap.channel_id == "UC123"
        assert snap.views_delta is None

    def test_with_deltas(self):
        snap = FactChannelSnapshot(
            snapshot_date=date(2026, 2, 15),
            snapshot_ts=datetime(2026, 2, 15, 0, 0, tzinfo=UTC),
            channel_id="UC123",
            view_count=100000,
            subscriber_count=5000,
            video_count=200,
            views_delta=1500,
            subs_delta=10,
            videos_delta=1,
        )
        assert snap.views_delta == 1500
        assert snap.subs_delta == 10


class TestFactVideoSnapshot:
    def test_minimal(self):
        snap = FactVideoSnapshot(
            snapshot_date=date(2026, 2, 15),
            snapshot_ts=datetime(2026, 2, 15, 1, 0, tzinfo=UTC),
            actual_captured_at=datetime(2026, 2, 15, 1, 3, tzinfo=UTC),
            snapshot_type="1h",
            video_id="abc123",
            channel_id="UC123",
        )
        assert snap.snapshot_type == "1h"
        assert snap.view_count is None

    def test_full_snapshot(self):
        snap = FactVideoSnapshot(
            snapshot_date=date(2026, 2, 15),
            snapshot_ts=datetime(2026, 2, 15, 4, 0, tzinfo=UTC),
            actual_captured_at=datetime(2026, 2, 15, 4, 2, tzinfo=UTC),
            snapshot_type="4h",
            video_id="abc123",
            channel_id="UC123",
            view_count=5000,
            like_count=200,
            comment_count=30,
            views_delta=3000,
            likes_delta=150,
            comments_delta=20,
            hours_since_publish=4,
            actual_hours_since_publish=4.03,
            days_since_publish=0,
        )
        assert snap.views_delta == 3000
        assert snap.actual_hours_since_publish == 4.03


class TestFactComment:
    def test_minimal(self):
        c = FactComment(
            comment_id="cmt_1",
            video_id="abc123",
            channel_id="UC123",
        )
        assert c.comment_id == "cmt_1"
        assert c.is_reply is False
        assert c.parent_comment_id is None

    def test_reply(self):
        c = FactComment(
            comment_id="cmt_2",
            video_id="abc123",
            channel_id="UC123",
            parent_comment_id="cmt_1",
            is_reply=True,
            commenter_name="User1",
            comment_text="Great video!",
            like_count=5,
        )
        assert c.is_reply is True
        assert c.parent_comment_id == "cmt_1"

    def test_with_sentiment(self):
        c = FactComment(
            comment_id="cmt_3",
            video_id="abc123",
            channel_id="UC123",
            sentiment_compound=0.85,
            toxicity_score=0.02,
        )
        assert c.sentiment_compound == 0.85
        assert c.toxicity_score == 0.02
