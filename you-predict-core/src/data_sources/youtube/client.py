"""YouTube Data API v3 client with quota tracking.

Consolidates all YouTube API interactions into a single class.
Consistent with GCSService/BigQueryService dependency injection pattern.
"""

import logging
from typing import Any

from googleapiclient.discovery import build
from youtube_transcript_api import (
    YouTubeTranscriptApi,  # pyright: ignore[reportMissingModuleSource]
)

from src.models.raw import (
    ChannelListResponse,
    CommentThreadListResponse,
    VideoListResponse,
)

logger = logging.getLogger(__name__)

_CHANNEL_PARTS = "snippet,statistics,brandingSettings,contentDetails,topicDetails,status"
_VIDEO_PARTS = "snippet,contentDetails,status,topicDetails,statistics,paidProductPlacementDetails"


class YouTubeClient:
    """YouTube Data API v3 client with quota tracking.

    Wraps all YouTube API interactions. Tracks quota usage per instance.
    YouTube free tier = 10,000 units/day. All list operations cost 1 unit
    per API call (regardless of batch size up to 50 IDs). Transcripts use
    a separate library (youtube-transcript-api) with zero quota cost.

    Usage:
        client = YouTubeClient(api_key="...")
        channels = client.fetch_channels(["UCX6OQ3DkcsbYNE6H8uQQuVA"])
        print(client.quota_used)  # 1
    """

    def __init__(self, api_key: str, quota_limit: int = 10_000) -> None:
        self._service = build("youtube", "v3", developerKey=api_key)
        self._quota_used = 0
        self._quota_limit = quota_limit

    # -----------------------------------------------------------------
    # Quota tracking
    # -----------------------------------------------------------------

    @property
    def quota_used(self) -> int:
        """Total quota units consumed since this client was created."""
        return self._quota_used

    @property
    def quota_remaining(self) -> int:
        """Estimated quota units remaining (based on configured limit)."""
        return self._quota_limit - self._quota_used

    def _track_quota(self, units: int = 1) -> None:
        """Record quota usage and warn if running low."""
        self._quota_used += units
        if self.quota_remaining < 1000:
            logger.warning(
                "YouTube API quota low: %d/%d used (%d remaining)",
                self._quota_used,
                self._quota_limit,
                self.quota_remaining,
            )

    # -----------------------------------------------------------------
    # Pagination helper
    # -----------------------------------------------------------------

    def _fetch_all_pages(
        self,
        request: Any,
        max_pages: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch all pages from a YouTube API list endpoint.

        Tracks 1 quota unit per page fetched.

        Args:
            request: Initial API request (from .list()).
            max_pages: Safety cap on number of pages to fetch.

        Returns:
            All items concatenated across pages.
        """
        all_items: list[dict[str, Any]] = []
        pages_fetched = 0

        for _ in range(max_pages):
            response: dict[str, Any] = request.execute()
            self._track_quota(1)
            pages_fetched += 1

            items = response.get("items", [])
            all_items.extend(items)

            next_page = response.get("nextPageToken")
            if not next_page:
                break

            request = request.next(response)
            if request is None:
                break

        logger.info("Fetched %d items across %d page(s)", len(all_items), pages_fetched)
        return all_items

    # -----------------------------------------------------------------
    # Channel endpoints
    # -----------------------------------------------------------------

    def fetch_channels(self, channel_ids: list[str]) -> ChannelListResponse:
        """Fetch full channel metadata for up to 50 channel IDs.

        Parts: snippet, statistics, brandingSettings, contentDetails, topicDetails, status
        Quota cost: 1 unit per call (regardless of batch size, max 50).
        """
        response: dict[str, Any] = (
            self._service.channels()
            .list(part=_CHANNEL_PARTS, id=",".join(channel_ids[:50]))
            .execute()
        )
        self._track_quota(1)
        return ChannelListResponse.model_validate(response)

    def fetch_channels_batched(
        self, channel_ids: list[str], batch_size: int = 50
    ) -> ChannelListResponse:
        """Fetch channels in batches of 50 (YouTube API limit)."""
        all_items = []
        for i in range(0, len(channel_ids), batch_size):
            batch = channel_ids[i : i + batch_size]
            result = self.fetch_channels(batch)
            all_items.extend(result.items)
            logger.info(
                "Fetched channel batch %d-%d (%d channels)",
                i,
                i + len(batch),
                len(result.items),
            )
        return ChannelListResponse(items=all_items)

    # -----------------------------------------------------------------
    # Video endpoints (full metadata)
    # -----------------------------------------------------------------

    def fetch_videos(self, video_ids: list[str]) -> VideoListResponse:
        """Fetch full video metadata for up to 50 video IDs.

        Parts: snippet, contentDetails, status, topicDetails, statistics,
               paidProductPlacementDetails
        Quota cost: 1 unit per call.
        """
        response: dict[str, Any] = (
            self._service.videos().list(part=_VIDEO_PARTS, id=",".join(video_ids[:50])).execute()
        )
        self._track_quota(1)
        return VideoListResponse.model_validate(response)

    def fetch_videos_batched(
        self, video_ids: list[str], batch_size: int = 50
    ) -> VideoListResponse:
        """Fetch videos in batches of 50."""
        all_items = []
        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i : i + batch_size]
            result = self.fetch_videos(batch)
            all_items.extend(result.items)
            logger.info(
                "Fetched video batch %d-%d (%d videos)",
                i,
                i + len(batch),
                len(result.items),
            )
        return VideoListResponse(items=all_items)

    # -----------------------------------------------------------------
    # Video snapshot endpoint (statistics-only, lightweight)
    # -----------------------------------------------------------------

    def fetch_video_stats(self, video_ids: list[str]) -> VideoListResponse:
        """Fetch statistics-only for up to 50 video IDs.

        This is the lightweight call used by Cloud Tasks snapshot polling.
        Only requests the 'statistics' part to minimize response size.
        Quota cost: 1 unit per call.
        """
        response: dict[str, Any] = (
            self._service.videos().list(part="statistics", id=",".join(video_ids[:50])).execute()
        )
        self._track_quota(1)
        return VideoListResponse.model_validate(response)

    # -----------------------------------------------------------------
    # Comment endpoint (paginated)
    # -----------------------------------------------------------------

    def fetch_comment_threads(
        self,
        video_id: str,
        max_results: int = 100,
        max_pages: int = 5,
        order: str = "relevance",
    ) -> CommentThreadListResponse:
        """Fetch comment threads for a video.

        Parts: snippet, replies
        Quota cost: 1 unit per page fetched.

        Args:
            video_id: YouTube video ID.
            max_results: Results per page (max 100).
            max_pages: Max pages to fetch (safety cap).
            order: 'relevance' or 'time'.
        """
        request = self._service.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=min(max_results, 100),
            order=order,
        )

        all_items: list[dict[str, Any]] = []
        for _ in range(max_pages):
            response: dict[str, Any] = request.execute()
            self._track_quota(1)

            items = response.get("items", [])
            all_items.extend(items)

            next_page = response.get("nextPageToken")
            if not next_page:
                break

            request = self._service.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=min(max_results, 100),
                order=order,
                pageToken=next_page,
            )

        logger.info("Fetched %d comment threads for video %s", len(all_items), video_id)
        return CommentThreadListResponse.model_validate({"items": all_items})

    # -----------------------------------------------------------------
    # Transcript (zero quota cost — uses youtube-transcript-api)
    # -----------------------------------------------------------------

    def fetch_transcript(self, video_id: str, languages: list[str] | None = None) -> str | None:
        """Fetch transcript text for a video.

        Uses youtube-transcript-api (not the Data API), so this costs
        zero quota units.

        Args:
            video_id: YouTube video ID.
            languages: Preferred languages in order. Defaults to English.

        Returns:
            Full transcript as a single string, or None if unavailable.
        """
        if languages is None:
            languages = ["en"]

        try:
            transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
            full_text = " ".join(snippet.text for snippet in transcript)
            logger.info("Fetched transcript for %s (%d chars)", video_id, len(full_text))
            return full_text
        except Exception as exc:
            logger.warning("No transcript available for %s (%s: %s)", video_id, type(exc).__name__, exc)
            return None
