"""Raw video JSON → dim_video.

Input: Raw VideoItem dicts from videos.list API response (via GCS).
Output: dim_video (MERGE on video_id, preserves first_seen_at on UPDATE).

Called by: POST /pipelines/daily-video-refresh
"""

import logging
from typing import Any

from src.data_sources.bigquery import BigQueryService
from src.engines.transforms.base import TransformResult, best_thumbnail, safe_int
from src.models.dimensions import DimVideo
from src.models.raw import VideoItem, VideoListResponse
from src.utils.timestamps import parse_iso, parse_iso8601_duration, utcnow

logger = logging.getLogger(__name__)


class VideoTransformer:
    """Transforms raw video API data into dim_video."""

    def __init__(self, bq: BigQueryService) -> None:
        self._bq = bq

    def transform(self, raw_items: list[dict[str, Any]]) -> TransformResult:
        """Run the video transform pipeline.

        Args:
            raw_items: List of raw video item dicts from the YouTube API.
        """
        response = VideoListResponse.model_validate({"items": raw_items})
        if not response.items:
            logger.warning("No video items to transform")
            return TransformResult("dim_video", 0, "merge")

        rows = self._build_dim_videos(response.items)
        affected = self._merge_dim_videos(rows)
        return TransformResult("dim_video", affected, "merge")

    def _build_dim_videos(self, items: list[VideoItem]) -> list[dict[str, Any]]:
        """Map VideoItems to DimVideo dicts."""
        now = utcnow()
        rows = []

        for item in items:
            snippet = item.snippet
            content = item.contentDetails
            status = item.status
            topic = item.topicDetails
            stats = item.statistics
            paid = item.paidProductPlacementDetails

            dim = DimVideo(
                video_id=item.id,
                channel_id=snippet.channelId or "" if snippet else "",
                title=snippet.title if snippet else None,
                description=snippet.description if snippet else None,
                published_at=(
                    parse_iso(snippet.publishedAt)
                    if snippet and snippet.publishedAt
                    else None
                ),
                thumbnail_url=(
                    best_thumbnail(snippet.thumbnails)
                    if snippet
                    else None
                ),
                duration_seconds=(
                    parse_iso8601_duration(content.duration)
                    if content and content.duration
                    else None
                ),
                category_id=(
                    int(snippet.categoryId)
                    if snippet and snippet.categoryId
                    else None
                ),
                is_livestream=(
                    snippet.liveBroadcastContent in ("live", "upcoming")
                    if snippet and snippet.liveBroadcastContent
                    else False
                ),
                is_age_restricted=None,  # contentRating not parsed yet
                made_for_kids=(
                    status.madeForKids if status else None
                ),
                has_custom_thumbnail=(
                    content.hasCustomThumbnail if content else None
                ),
                definition=content.definition if content else None,
                caption_available=(
                    content.caption == "true"
                    if content and content.caption
                    else None
                ),
                licensed_content=(
                    content.licensedContent if content else None
                ),
                has_paid_promotion=(
                    paid.hasPaidProductPlacement if paid else None
                ),
                tags=snippet.tags or [] if snippet else [],
                topics=(
                    topic.topicCategories or [] if topic else []
                ),
                view_count=safe_int(stats.viewCount) if stats else None,
                like_count=safe_int(stats.likeCount) if stats else None,
                comment_count=(
                    safe_int(stats.commentCount) if stats else None
                ),
                first_seen_at=now,  # Preserved on UPDATE via MERGE SQL
                updated_at=now,
            )
            rows.append(dim.model_dump(mode="json"))

        return rows

    def _merge_dim_videos(self, rows: list[dict[str, Any]]) -> int:
        """MERGE dim_video rows on video_id.

        Preserves first_seen_at on UPDATE (keeps the original value).
        """
        if not rows:
            return 0

        selects = []
        for row in rows:
            tags = ", ".join(
                f"'{_esc(t)}'" for t in (row.get("tags") or [])
            )
            topics = ", ".join(
                f"'{_esc(t)}'" for t in (row.get("topics") or [])
            )
            selects.append(
                f"SELECT "
                f"'{row['video_id']}' AS video_id, "
                f"'{row['channel_id']}' AS channel_id, "
                f"{_sql_str(row.get('title'))} AS title, "
                f"{_sql_str(row.get('description'))} AS description, "
                f"{_sql_ts(row.get('published_at'))} AS published_at, "
                f"{_sql_str(row.get('thumbnail_url'))} AS thumbnail_url, "
                f"{_sql_int(row.get('duration_seconds'))} AS duration_seconds, "
                f"{_sql_int(row.get('category_id'))} AS category_id, "
                f"{_sql_bool(row.get('is_livestream'))} AS is_livestream, "
                f"{_sql_bool(row.get('is_age_restricted'))} AS is_age_restricted, "
                f"{_sql_bool(row.get('made_for_kids'))} AS made_for_kids, "
                f"{_sql_bool(row.get('has_custom_thumbnail'))} AS has_custom_thumbnail, "
                f"{_sql_str(row.get('definition'))} AS definition, "
                f"{_sql_bool(row.get('caption_available'))} AS caption_available, "
                f"{_sql_bool(row.get('licensed_content'))} AS licensed_content, "
                f"{_sql_bool(row.get('has_paid_promotion'))} AS has_paid_promotion, "
                f"[{tags}] AS tags, "
                f"[{topics}] AS topics, "
                f"{_sql_int(row.get('view_count'))} AS view_count, "
                f"{_sql_int(row.get('like_count'))} AS like_count, "
                f"{_sql_int(row.get('comment_count'))} AS comment_count, "
                f"CURRENT_TIMESTAMP() AS first_seen_at, "
                f"CURRENT_TIMESTAMP() AS updated_at"
            )

        source = " UNION ALL ".join(selects)

        sql = f"""
        MERGE `{{project}}.{{dataset}}.dim_video` T
        USING ({source}) S
        ON T.video_id = S.video_id
        WHEN MATCHED THEN UPDATE SET
            channel_id = S.channel_id,
            title = S.title,
            description = S.description,
            published_at = S.published_at,
            thumbnail_url = S.thumbnail_url,
            duration_seconds = S.duration_seconds,
            category_id = S.category_id,
            is_livestream = S.is_livestream,
            is_age_restricted = S.is_age_restricted,
            made_for_kids = S.made_for_kids,
            has_custom_thumbnail = S.has_custom_thumbnail,
            definition = S.definition,
            caption_available = S.caption_available,
            licensed_content = S.licensed_content,
            has_paid_promotion = S.has_paid_promotion,
            tags = S.tags,
            topics = S.topics,
            view_count = S.view_count,
            like_count = S.like_count,
            comment_count = S.comment_count,
            updated_at = S.updated_at
        WHEN NOT MATCHED THEN INSERT (
            video_id, channel_id, title, description, published_at,
            thumbnail_url, duration_seconds, category_id, is_livestream,
            is_age_restricted, made_for_kids, has_custom_thumbnail,
            definition, caption_available, licensed_content,
            has_paid_promotion, tags, topics,
            view_count, like_count, comment_count,
            first_seen_at, updated_at
        ) VALUES (
            S.video_id, S.channel_id, S.title, S.description, S.published_at,
            S.thumbnail_url, S.duration_seconds, S.category_id, S.is_livestream,
            S.is_age_restricted, S.made_for_kids, S.has_custom_thumbnail,
            S.definition, S.caption_available, S.licensed_content,
            S.has_paid_promotion, S.tags, S.topics,
            S.view_count, S.like_count, S.comment_count,
            S.first_seen_at, S.updated_at
        )
        """
        return self._bq.run_merge(sql)


# ---------------------------------------------------------------------------
# SQL literal helpers
# ---------------------------------------------------------------------------


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _sql_str(value: str | None) -> str:
    if value is None:
        return "NULL"
    return f"'{_esc(value)}'"


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
