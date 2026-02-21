"""Video monitoring lifecycle — manages the video_monitoring table.

This is NOT a transform (it doesn't read from GCS). It's the engine that
tracks which videos are actively being polled for snapshots.

Called by: webhook handler, pipeline endpoints (Phase 5)
"""

import logging
from datetime import datetime
from typing import Any

from src.config.constants import InactiveReason
from src.data_sources.bigquery import BigQueryService
from src.utils.timestamps import add_hours, utcnow

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Manages the video_monitoring table lifecycle.

    Usage:
        engine = DiscoveryEngine(bq=bq_service, monitoring_window_hours=72)
        is_new = engine.register_video("abc123", "UCxyz", published_at)
        engine.expire_monitoring()
    """

    def __init__(self, bq: BigQueryService, monitoring_window_hours: int = 72) -> None:
        self._bq = bq
        self._monitoring_window_hours = monitoring_window_hours

    def register_video(
        self,
        video_id: str,
        channel_id: str,
        published_at: datetime,
    ) -> bool:
        """Register a new video for monitoring. Idempotent.

        MERGE on video_id: inserts if new, skips if already exists.
        Returns True if this was a new video, False if already registered.
        """
        now = utcnow()
        monitoring_until = add_hours(published_at, self._monitoring_window_hours)

        sql = """
        MERGE `{project}.{dataset}.video_monitoring` T
        USING (
            SELECT
                '{video_id}' AS video_id,
                '{channel_id}' AS channel_id,
                TIMESTAMP '{published_at}' AS published_at,
                TIMESTAMP '{discovered_at}' AS discovered_at,
                TIMESTAMP '{monitoring_until}' AS monitoring_until,
                TIMESTAMP '{first_seen_at}' AS first_seen_at,
                TRUE AS is_active
        ) S
        ON T.video_id = S.video_id
        WHEN NOT MATCHED THEN
            INSERT (video_id, channel_id, published_at, discovered_at,
                    monitoring_until, first_seen_at, is_active)
            VALUES (S.video_id, S.channel_id, S.published_at, S.discovered_at,
                    S.monitoring_until, S.first_seen_at, S.is_active)
        """.format(
            project="{project}",
            dataset="{dataset}",
            video_id=video_id,
            channel_id=channel_id,
            published_at=published_at.isoformat(),
            discovered_at=now.isoformat(),
            monitoring_until=monitoring_until.isoformat(),
            first_seen_at=now.isoformat(),
        )

        affected = self._bq.run_merge(sql)
        is_new = affected > 0
        if is_new:
            logger.info("Registered new video %s for monitoring", video_id)
        else:
            logger.info("Video %s already registered, skipping", video_id)
        return is_new

    def is_video_registered(self, video_id: str) -> bool:
        """Check if a video is already in video_monitoring."""
        sql = f"""
        SELECT 1 FROM `{{project}}.{{dataset}}.video_monitoring`
        WHERE video_id = '{video_id}'
        LIMIT 1
        """
        rows = self._bq.run_query(sql)
        return len(rows) > 0

    def get_active_videos(self) -> list[dict[str, Any]]:
        """Get all actively monitored videos."""
        sql = """
        SELECT * FROM `{project}.{dataset}.video_monitoring`
        WHERE is_active = TRUE
        """
        return self._bq.run_query(sql)

    def get_active_video_ids(self) -> list[str]:
        """Get deduplicated video IDs of actively monitored videos.

        Uses DISTINCT to guard against duplicate rows in video_monitoring
        (which can occur from concurrent webhook deliveries hitting the same
        video before the MERGE completes).
        """
        sql = """
        SELECT DISTINCT video_id FROM `{project}.{dataset}.video_monitoring`
        WHERE is_active = TRUE
        """
        rows = self._bq.run_query(sql)
        return [row["video_id"] for row in rows]

    def get_tracked_channel_ids(self) -> list[str]:
        """Get all active channel IDs from tracked_channels."""
        sql = """
        SELECT channel_id FROM `{project}.{dataset}.tracked_channels`
        WHERE is_active = TRUE
        """
        rows = self._bq.run_query(sql)
        return [row["channel_id"] for row in rows]

    def expire_monitoring(self) -> int:
        """Deactivate videos past their monitoring window.

        Sets is_active=False and inactive_reason='monitoring_window_expired'
        for all videos where monitoring_until < CURRENT_TIMESTAMP().
        Returns the number of rows updated.
        """
        sql = """
        UPDATE `{project}.{dataset}.video_monitoring`
        SET is_active = FALSE,
            inactive_reason = 'monitoring_window_expired'
        WHERE is_active = TRUE
          AND monitoring_until < CURRENT_TIMESTAMP()
        """
        rows = self._bq.run_merge(sql)  # run_merge works for UPDATE too
        logger.info("Expired monitoring for %d videos", rows)
        return rows

    def deactivate_video(self, video_id: str, reason: InactiveReason) -> int:
        """Manually deactivate a video with a reason.

        Returns 1 if the video was deactivated, 0 if not found/already inactive.
        """
        sql = f"""
        UPDATE `{{project}}.{{dataset}}.video_monitoring`
        SET is_active = FALSE,
            inactive_reason = '{reason.value}'
        WHERE video_id = '{video_id}'
          AND is_active = TRUE
        """
        affected = self._bq.run_merge(sql)
        logger.info("Deactivated video %s (reason: %s)", video_id, reason.value)
        return affected
