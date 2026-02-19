"""GCS path builder for the raw layer naming conventions."""

from datetime import date, datetime


class GCSPathBuilder:
    """Builds blob paths for each raw data prefix.

    All paths follow: {prefix}/{id_or_date}/{filename}
    """

    def channel_metadata(self, channel_id: str, ts: datetime) -> str:
        return f"channel_metadata/{channel_id}/{channel_id}_{ts.isoformat()}.json"

    def video_metadata(self, video_id: str, ts: datetime) -> str:
        return f"video_metadata/{video_id}/{video_id}_{ts.isoformat()}.json"

    def video_snapshot(
        self, video_id: str, ts: datetime, snapshot_date: date | None = None,
    ) -> str:
        d = (snapshot_date or ts.date()).isoformat()
        return f"video_snapshot_stats/{d}/{video_id}_{ts.isoformat()}.json"

    def channel_snapshot(
        self, channel_id: str, ts: datetime, snapshot_date: date | None = None
    ) -> str:
        d = (snapshot_date or ts.date()).isoformat()
        return f"channel_snapshot_stats/{d}/{channel_id}_{ts.isoformat()}.json"

    def video_comments(self, video_id: str, ts: datetime, page: int = 1) -> str:
        return f"video_comments/{video_id}/{video_id}_{ts.isoformat()}_{page}.json"

    def video_transcript(self, video_id: str, language: str = "en") -> str:
        return f"video_transcripts/{video_id}/{video_id}_{language}.txt"
