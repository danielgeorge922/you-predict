"""Statistics-only response → fact_video_snapshot.

Input: Single VideoItem dict (statistics-only) + context from Cloud Tasks.
Output: fact_video_snapshot (MERGE on video_id + snapshot_type).

Called by: POST /tasks/snapshot/{video_id}
"""

import logging
from datetime import datetime
from typing import Any

from src.config.constants import FANOUT_SCHEDULE
from src.data_sources.bigquery import BigQueryService
from src.engines.transforms.base import TransformResult, safe_int
from src.models.facts import FactVideoSnapshot
from src.models.raw import VideoItem
from src.utils.timestamps import days_since, hours_since

logger = logging.getLogger(__name__)


class SnapshotTransformer:
    """Transforms a statistics-only API response into fact_video_snapshot."""

    def __init__(self, bq: BigQueryService) -> None:
        self._bq = bq

    def transform(
        self,
        raw_item: dict[str, Any],
        video_id: str,
        channel_id: str,
        interval_hours: int,
        published_at: datetime,
        captured_at: datetime,
    ) -> TransformResult:
        """Transform a single snapshot into a fact_video_snapshot row.

        Args:
            raw_item: Raw video item dict (statistics-only).
            video_id: YouTube video ID.
            channel_id: Owning channel ID.
            interval_hours: Nominal snapshot interval (1, 2, 4, ..., 72).
            published_at: When the video was published.
            captured_at: When the API was actually called.
        """
        item = VideoItem.model_validate(raw_item)
        stats = item.statistics

        view_count = safe_int(stats.viewCount) if stats else None
        like_count = safe_int(stats.likeCount) if stats else None
        comment_count = safe_int(stats.commentCount) if stats else None

        snapshot_type = FANOUT_SCHEDULE.interval_to_snapshot_type(
            interval_hours
        )

        # Delta computation: query previous snapshot
        prev = self._get_previous_snapshot(video_id)
        views_delta = None
        likes_delta = None
        comments_delta = None
        if prev:
            if view_count is not None and prev.get("view_count") is not None:
                views_delta = view_count - prev["view_count"]
            if like_count is not None and prev.get("like_count") is not None:
                likes_delta = like_count - prev["like_count"]
            if (
                comment_count is not None
                and prev.get("comment_count") is not None
            ):
                comments_delta = comment_count - prev["comment_count"]

        snap = FactVideoSnapshot(
            snapshot_date=captured_at.date(),
            snapshot_ts=captured_at,
            actual_captured_at=captured_at,
            snapshot_type=snapshot_type,
            video_id=video_id,
            channel_id=channel_id,
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            views_delta=views_delta,
            likes_delta=likes_delta,
            comments_delta=comments_delta,
            hours_since_publish=interval_hours,
            actual_hours_since_publish=round(
                hours_since(published_at, captured_at), 2
            ),
            days_since_publish=days_since(published_at, captured_at),
        )
        row = snap.model_dump(mode="json")

        affected = self._merge_snapshot(row)
        return TransformResult("fact_video_snapshot", affected, "merge")

    def _get_previous_snapshot(self, video_id: str) -> dict[str, Any] | None:
        """Get the most recent snapshot for delta computation."""
        sql = f"""
        SELECT view_count, like_count, comment_count
        FROM `{{project}}.{{dataset}}.fact_video_snapshot`
        WHERE video_id = '{video_id}'
        ORDER BY actual_captured_at DESC
        LIMIT 1
        """
        rows = self._bq.run_query(sql)
        return rows[0] if rows else None

    def _merge_snapshot(self, row: dict[str, Any]) -> int:
        """MERGE fact_video_snapshot on (video_id, snapshot_type)."""
        sql = f"""
        MERGE `{{project}}.{{dataset}}.fact_video_snapshot` T
        USING (
            SELECT
                DATE '{row["snapshot_date"]}' AS snapshot_date,
                TIMESTAMP '{row["snapshot_ts"]}' AS snapshot_ts,
                TIMESTAMP '{row["actual_captured_at"]}' AS actual_captured_at,
                '{row["snapshot_type"]}' AS snapshot_type,
                '{row["video_id"]}' AS video_id,
                '{row["channel_id"]}' AS channel_id,
                {_sql_int(row.get("view_count"))} AS view_count,
                {_sql_int(row.get("like_count"))} AS like_count,
                {_sql_int(row.get("comment_count"))} AS comment_count,
                {_sql_int(row.get("views_delta"))} AS views_delta,
                {_sql_int(row.get("likes_delta"))} AS likes_delta,
                {_sql_int(row.get("comments_delta"))} AS comments_delta,
                {_sql_int(row.get("hours_since_publish"))} AS hours_since_publish,
                {row.get("actual_hours_since_publish")} AS actual_hours_since_publish,
                {_sql_int(row.get("days_since_publish"))} AS days_since_publish
        ) S
        ON T.video_id = S.video_id AND T.snapshot_type = S.snapshot_type
        WHEN MATCHED THEN UPDATE SET
            snapshot_date = S.snapshot_date,
            snapshot_ts = S.snapshot_ts,
            actual_captured_at = S.actual_captured_at,
            channel_id = S.channel_id,
            view_count = S.view_count,
            like_count = S.like_count,
            comment_count = S.comment_count,
            views_delta = S.views_delta,
            likes_delta = S.likes_delta,
            comments_delta = S.comments_delta,
            hours_since_publish = S.hours_since_publish,
            actual_hours_since_publish = S.actual_hours_since_publish,
            days_since_publish = S.days_since_publish
        WHEN NOT MATCHED THEN INSERT (
            snapshot_date, snapshot_ts, actual_captured_at, snapshot_type,
            video_id, channel_id, view_count, like_count, comment_count,
            views_delta, likes_delta, comments_delta,
            hours_since_publish, actual_hours_since_publish, days_since_publish
        ) VALUES (
            S.snapshot_date, S.snapshot_ts, S.actual_captured_at, S.snapshot_type,
            S.video_id, S.channel_id, S.view_count, S.like_count, S.comment_count,
            S.views_delta, S.likes_delta, S.comments_delta,
            S.hours_since_publish, S.actual_hours_since_publish, S.days_since_publish
        )
        """
        return self._bq.run_merge(sql)


def _sql_int(value: int | None) -> str:
    return str(value) if value is not None else "NULL"
