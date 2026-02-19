"""Raw channel JSON → dim_channel + fact_channel_snapshot.

Input: Raw ChannelItem dicts from channels.list API response (via GCS).
Output: Two tables — dim_channel (MERGE on channel_id) and
        fact_channel_snapshot (MERGE on snapshot_date + channel_id).

Called by: POST /pipelines/daily-channel-refresh
"""

import logging
from typing import Any

from src.data_sources.bigquery import BigQueryService
from src.engines.transforms.base import TransformResult, best_thumbnail, safe_int
from src.models.dimensions import DimChannel
from src.models.facts import FactChannelSnapshot
from src.models.raw import ChannelItem, ChannelListResponse
from src.utils.timestamps import parse_iso, utcnow

logger = logging.getLogger(__name__)


class ChannelTransformer:
    """Transforms raw channel API data into dim_channel + fact_channel_snapshot."""

    def __init__(self, bq: BigQueryService) -> None:
        self._bq = bq

    def transform(self, raw_items: list[dict[str, Any]]) -> list[TransformResult]:
        """Run the full channel transform pipeline.

        Args:
            raw_items: List of raw channel item dicts from the YouTube API.

        Returns:
            List of TransformResults (one per table written).
        """
        response = ChannelListResponse.model_validate({"items": raw_items})
        if not response.items:
            logger.warning("No channel items to transform")
            return []

        results = []

        # dim_channel — MERGE on channel_id
        dim_rows = self._build_dim_channels(response.items)
        if dim_rows:
            affected = self._merge_dim_channels(dim_rows)
            results.append(TransformResult("dim_channel", affected, "merge"))

        # fact_channel_snapshot — MERGE on (snapshot_date, channel_id)
        snap_rows = self._build_channel_snapshots(response.items)
        if snap_rows:
            affected = self._merge_channel_snapshots(snap_rows)
            results.append(TransformResult("fact_channel_snapshot", affected, "merge"))

        return results

    def _build_dim_channels(self, items: list[ChannelItem]) -> list[dict[str, Any]]:
        """Map ChannelItems to DimChannel dicts."""
        now = utcnow()
        rows = []

        for item in items:
            snippet = item.snippet
            stats = item.statistics
            branding = item.brandingSettings
            content = item.contentDetails
            topic = item.topicDetails
            status = item.status

            dim = DimChannel(
                channel_id=item.id,
                channel_name=snippet.title if snippet else None,
                channel_description=snippet.description if snippet else None,
                custom_url=snippet.customUrl if snippet else None,
                channel_thumbnail_url=best_thumbnail(snippet.thumbnails) if snippet else None,
                channel_created_at=(
                    parse_iso(snippet.publishedAt)
                    if snippet and snippet.publishedAt
                    else None
                ),
                made_for_kids=status.madeForKids if status else None,
                hidden_subscriber_count=(
                    stats.hiddenSubscriberCount if stats else None
                ),
                channel_keywords=(
                    branding.channel.keywords
                    if branding and branding.channel
                    else None
                ),
                uploads_playlist_id=(
                    content.relatedPlaylists.uploads
                    if content and content.relatedPlaylists
                    else None
                ),
                topics=topic.topicCategories or [] if topic else [],
                topic_ids=topic.topicIds or [] if topic else [],
                view_count=safe_int(stats.viewCount) if stats else None,
                subscriber_count=safe_int(stats.subscriberCount) if stats else None,
                video_count=safe_int(stats.videoCount) if stats else None,
                updated_at=now,
            )
            rows.append(dim.model_dump(mode="json"))

        return rows

    def _build_channel_snapshots(self, items: list[ChannelItem]) -> list[dict[str, Any]]:
        """Build fact_channel_snapshot rows with delta computation."""
        now = utcnow()
        today = now.date()
        rows = []

        for item in items:
            stats = item.statistics
            if not stats:
                continue

            view_count = safe_int(stats.viewCount)
            subscriber_count = safe_int(stats.subscriberCount)
            video_count = safe_int(stats.videoCount)

            # Query previous snapshot for delta computation
            prev = self._get_previous_channel_snapshot(item.id)

            views_delta = None
            subs_delta = None
            videos_delta = None
            if prev and view_count is not None:
                prev_views = prev.get("view_count")
                prev_subs = prev.get("subscriber_count")
                prev_videos = prev.get("video_count")
                if prev_views is not None:
                    views_delta = view_count - prev_views
                if prev_subs is not None and subscriber_count is not None:
                    subs_delta = subscriber_count - prev_subs
                if prev_videos is not None and video_count is not None:
                    videos_delta = video_count - prev_videos

            snap = FactChannelSnapshot(
                snapshot_date=today,
                snapshot_ts=now,
                channel_id=item.id,
                view_count=view_count,
                subscriber_count=subscriber_count,
                video_count=video_count,
                views_delta=views_delta,
                subs_delta=subs_delta,
                videos_delta=videos_delta,
            )
            rows.append(snap.model_dump(mode="json"))

        return rows

    def _get_previous_channel_snapshot(self, channel_id: str) -> dict[str, Any] | None:
        """Get the most recent channel snapshot for delta computation."""
        sql = f"""
        SELECT view_count, subscriber_count, video_count
        FROM `{{project}}.{{dataset}}.fact_channel_snapshot`
        WHERE channel_id = '{channel_id}'
        ORDER BY snapshot_ts DESC
        LIMIT 1
        """

        rows = self._bq.run_query(sql)
        return rows[0] if rows else None

    def _merge_dim_channels(self, rows: list[dict[str, Any]]) -> int:
        """MERGE dim_channel rows on channel_id."""
        selects = []
        for row in rows:
            topics = ", ".join(f"'{t}'" for t in (row.get("topics") or []))
            topic_ids = ", ".join(f"'{t}'" for t in (row.get("topic_ids") or []))
            selects.append(
                f"SELECT "
                f"'{row['channel_id']}' AS channel_id, "
                f"{_sql_str(row.get('channel_name'))} AS channel_name, "
                f"{_sql_str(row.get('channel_description'))} AS channel_description, "
                f"{_sql_str(row.get('custom_url'))} AS custom_url, "
                f"{_sql_str(row.get('channel_thumbnail_url'))} AS channel_thumbnail_url, "
                f"{_sql_ts(row.get('channel_created_at'))} AS channel_created_at, "
                f"{_sql_bool(row.get('made_for_kids'))} AS made_for_kids, "
                f"{_sql_bool(row.get('hidden_subscriber_count'))} AS hidden_subscriber_count, "
                f"{_sql_str(row.get('channel_keywords'))} AS channel_keywords, "
                f"{_sql_str(row.get('uploads_playlist_id'))} AS uploads_playlist_id, "
                f"[{topics}] AS topics, "
                f"[{topic_ids}] AS topic_ids, "
                f"{_sql_int(row.get('view_count'))} AS view_count, "
                f"{_sql_int(row.get('subscriber_count'))} AS subscriber_count, "
                f"{_sql_int(row.get('video_count'))} AS video_count, "
                f"CURRENT_TIMESTAMP() AS updated_at"
            )

        source = " UNION ALL ".join(selects)

        sql = f"""
        MERGE `{{project}}.{{dataset}}.dim_channel` T
        USING ({source}) S
        ON T.channel_id = S.channel_id
        WHEN MATCHED THEN UPDATE SET
            channel_name = S.channel_name,
            channel_description = S.channel_description,
            custom_url = S.custom_url,
            channel_thumbnail_url = S.channel_thumbnail_url,
            channel_created_at = S.channel_created_at,
            made_for_kids = S.made_for_kids,
            hidden_subscriber_count = S.hidden_subscriber_count,
            channel_keywords = S.channel_keywords,
            uploads_playlist_id = S.uploads_playlist_id,
            topics = S.topics,
            topic_ids = S.topic_ids,
            view_count = S.view_count,
            subscriber_count = S.subscriber_count,
            video_count = S.video_count,
            updated_at = S.updated_at
        WHEN NOT MATCHED THEN INSERT (
            channel_id, channel_name, channel_description, custom_url,
            channel_thumbnail_url, channel_created_at, made_for_kids,
            hidden_subscriber_count, channel_keywords, uploads_playlist_id,
            topics, topic_ids, view_count, subscriber_count, video_count, updated_at
        ) VALUES (
            S.channel_id, S.channel_name, S.channel_description, S.custom_url,
            S.channel_thumbnail_url, S.channel_created_at, S.made_for_kids,
            S.hidden_subscriber_count, S.channel_keywords, S.uploads_playlist_id,
            S.topics, S.topic_ids, S.view_count, S.subscriber_count, S.video_count,
            S.updated_at
        )
        """
        return self._bq.run_merge(sql)

    def _merge_channel_snapshots(self, rows: list[dict[str, Any]]) -> int:
        """MERGE fact_channel_snapshot on (snapshot_date, channel_id)."""
        selects = []
        for row in rows:
            selects.append(
                f"SELECT "
                f"DATE '{row['snapshot_date']}' AS snapshot_date, "
                f"TIMESTAMP '{row['snapshot_ts']}' AS snapshot_ts, "
                f"'{row['channel_id']}' AS channel_id, "
                f"{_sql_int(row.get('view_count'))} AS view_count, "
                f"{_sql_int(row.get('subscriber_count'))} AS subscriber_count, "
                f"{_sql_int(row.get('video_count'))} AS video_count, "
                f"{_sql_int(row.get('views_delta'))} AS views_delta, "
                f"{_sql_int(row.get('subs_delta'))} AS subs_delta, "
                f"{_sql_int(row.get('videos_delta'))} AS videos_delta"
            )

        source = " UNION ALL ".join(selects)

        sql = f"""
        MERGE `{{project}}.{{dataset}}.fact_channel_snapshot` T
        USING ({source}) S
        ON T.snapshot_date = S.snapshot_date AND T.channel_id = S.channel_id
        WHEN MATCHED THEN UPDATE SET
            snapshot_ts = S.snapshot_ts,
            view_count = S.view_count,
            subscriber_count = S.subscriber_count,
            video_count = S.video_count,
            views_delta = S.views_delta,
            subs_delta = S.subs_delta,
            videos_delta = S.videos_delta
        WHEN NOT MATCHED THEN INSERT (
            snapshot_date, snapshot_ts, channel_id,
            view_count, subscriber_count, video_count,
            views_delta, subs_delta, videos_delta
        ) VALUES (
            S.snapshot_date, S.snapshot_ts, S.channel_id,
            S.view_count, S.subscriber_count, S.video_count,
            S.views_delta, S.subs_delta, S.videos_delta
        )
        """
        return self._bq.run_merge(sql)


# ---------------------------------------------------------------------------
# SQL literal helpers
# ---------------------------------------------------------------------------


def _sql_str(value: str | None) -> str:
    if value is None:
        return "NULL"
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _sql_int(value: int | None) -> str:
    return str(value) if value is not None else "NULL"


def _sql_bool(value: bool | None) -> str:
    if value is None:
        return "NULL"
    return "TRUE" if value else "FALSE"


def _sql_ts(value: str | None) -> str:
    if value is None:
        return "CAST(NULL AS TIMESTAMP)"
    return f"TIMESTAMP '{value}'"
