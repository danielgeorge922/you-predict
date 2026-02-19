"""Tests for src.data_sources.gcs_paths."""

from datetime import UTC, date, datetime

from src.data_sources.gcs_paths import GCSPathBuilder


class TestGCSPathBuilder:
    def setup_method(self):
        self.paths = GCSPathBuilder()
        self.ts = datetime(2026, 2, 15, 8, 30, 0, tzinfo=UTC)

    def test_channel_metadata(self):
        path = self.paths.channel_metadata("UC123", self.ts)
        assert path.startswith("channel_metadata/UC123/")
        assert "UC123_" in path
        assert path.endswith(".json")

    def test_video_metadata(self):
        path = self.paths.video_metadata("abc123", self.ts)
        assert path.startswith("video_metadata/abc123/")
        assert "abc123_" in path
        assert path.endswith(".json")

    def test_video_snapshot_default_date(self):
        path = self.paths.video_snapshot("abc123", self.ts)
        assert path.startswith("video_snapshot_stats/2026-02-15/")
        assert path.endswith(".json")

    def test_video_snapshot_explicit_date(self):
        path = self.paths.video_snapshot("abc123", self.ts, snapshot_date=date(2026, 2, 14))
        assert "2026-02-14" in path

    def test_channel_snapshot_default_date(self):
        path = self.paths.channel_snapshot("UC123", self.ts)
        assert path.startswith("channel_snapshot_stats/2026-02-15/")

    def test_channel_snapshot_explicit_date(self):
        path = self.paths.channel_snapshot("UC123", self.ts, snapshot_date=date(2026, 2, 14))
        assert "2026-02-14" in path

    def test_video_comments(self):
        path = self.paths.video_comments("abc123", self.ts, page=3)
        assert path.startswith("video_comments/abc123/")
        assert path.endswith("_3.json")

    def test_video_comments_default_page(self):
        path = self.paths.video_comments("abc123", self.ts)
        assert path.endswith("_1.json")

    def test_video_transcript(self):
        path = self.paths.video_transcript("abc123", language="en")
        assert path == "video_transcripts/abc123/abc123_en.txt"

    def test_video_transcript_default_language(self):
        path = self.paths.video_transcript("abc123")
        assert path.endswith("_en.txt")
