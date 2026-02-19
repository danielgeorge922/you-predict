"""Tests for src.models.dimensions."""

from datetime import UTC, date, datetime

from src.models.dimensions import DimCategory, DimChannel, DimDate, DimVideo, DimVideoTranscript


class TestDimChannel:
    def test_minimal(self):
        ch = DimChannel(channel_id="UC123")
        assert ch.channel_id == "UC123"
        assert ch.channel_name is None
        assert ch.topics == []
        assert ch.topic_ids == []

    def test_full(self):
        ch = DimChannel(
            channel_id="UC123",
            channel_name="Test Channel",
            channel_description="A test",
            custom_url="@test",
            channel_created_at=datetime(2020, 1, 1, tzinfo=UTC),
            made_for_kids=False,
            hidden_subscriber_count=False,
            channel_keywords="test keywords",
            uploads_playlist_id="UU123",
            topics=["Gaming", "Music"],
            topic_ids=["t1", "t2"],
            view_count=1000,
            subscriber_count=500,
            video_count=50,
            updated_at=datetime(2026, 2, 15, tzinfo=UTC),
        )
        assert ch.channel_name == "Test Channel"
        assert len(ch.topics) == 2
        assert ch.subscriber_count == 500

    def test_serialization_roundtrip(self):
        ch = DimChannel(channel_id="UC123", channel_name="Test")
        data = ch.model_dump(mode="json")
        ch2 = DimChannel.model_validate(data)
        assert ch == ch2


class TestDimVideo:
    def test_minimal(self):
        v = DimVideo(video_id="abc123", channel_id="UC123")
        assert v.video_id == "abc123"
        assert v.tags == []
        assert v.duration_seconds is None

    def test_full(self):
        v = DimVideo(
            video_id="abc123",
            channel_id="UC123",
            title="Test Video",
            published_at=datetime(2026, 2, 15, 8, 0, tzinfo=UTC),
            duration_seconds=600,
            category_id=24,
            is_livestream=False,
            has_custom_thumbnail=True,
            tags=["tag1", "tag2"],
            view_count=10000,
            like_count=500,
            comment_count=50,
        )
        assert v.title == "Test Video"
        assert v.duration_seconds == 600
        assert len(v.tags) == 2


class TestDimCategory:
    def test_creation(self):
        cat = DimCategory(category_id=24, category_name="Entertainment")
        assert cat.category_id == 24
        assert cat.category_name == "Entertainment"


class TestDimDate:
    def test_creation(self):
        d = DimDate(
            date_key=20260215,
            full_date=date(2026, 2, 15),
            year=2026,
            quarter=1,
            month=2,
            month_name="February",
            week_of_year=7,
            day_of_month=15,
            day_of_week=7,
            day_name="Sunday",
            is_weekend=True,
            is_us_holiday=False,
            season="winter",
        )
        assert d.date_key == 20260215
        assert d.is_weekend is True


class TestDimVideoTranscript:
    def test_minimal(self):
        t = DimVideoTranscript(video_id="abc123")
        assert t.video_id == "abc123"
        assert t.word_count is None
        assert t.topic_keywords == []

    def test_full(self):
        t = DimVideoTranscript(
            video_id="abc123",
            transcript_source="auto_generated",
            gcs_uri="gs://bucket/path.txt",
            word_count=1500,
            fetched_at=datetime(2026, 2, 15, tzinfo=UTC),
            readability_score=8.5,
            has_profanity=False,
        )
        assert t.word_count == 1500
        assert t.readability_score == 8.5
