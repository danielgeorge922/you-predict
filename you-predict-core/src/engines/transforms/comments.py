"""Comment threads → fact_comment (flattened).

Input: Raw CommentThread dicts from commentThreads.list API response.
Output: fact_comment (MERGE on comment_id).

Called by: POST /tasks/comments/{video_id}
"""

import logging
from datetime import datetime
from typing import Any

from src.data_sources.bigquery import BigQueryService
from src.engines.transforms.base import TransformResult
from src.models.facts import FactComment
from src.models.raw import CommentThread, CommentThreadListResponse
from src.utils.timestamps import parse_iso

logger = logging.getLogger(__name__)


class CommentTransformer:
    """Flattens comment threads into individual fact_comment rows."""

    def __init__(self, bq: BigQueryService) -> None:
        self._bq = bq

    def transform(
        self,
        raw_items: list[dict[str, Any]],
        video_id: str,
        channel_id: str,
        pulled_at: datetime,
        sample_strategy: str = "relevance",
    ) -> TransformResult:
        """Flatten and merge comment threads into fact_comment.

        Args:
            raw_items: Raw comment thread dicts from the API.
            video_id: YouTube video ID.
            channel_id: Video's channel ID (denormalized).
            pulled_at: When the comments were fetched.
            sample_strategy: Sampling method (e.g. "relevance", "time").
        """
        response = CommentThreadListResponse.model_validate(
            {"items": raw_items}
        )
        if not response.items:
            logger.warning("No comment threads to transform for %s", video_id)
            return TransformResult("fact_comment", 0, "merge")

        rows = self._flatten_threads(
            response.items, video_id, channel_id, pulled_at, sample_strategy
        )

        if not rows:
            return TransformResult("fact_comment", 0, "merge")

        affected = self._merge_comments(rows)
        return TransformResult("fact_comment", affected, "merge")

    def _flatten_threads(
        self,
        threads: list[CommentThread],
        video_id: str,
        channel_id: str,
        pulled_at: datetime,
        sample_strategy: str,
    ) -> list[dict[str, Any]]:
        """Flatten nested comment threads into individual rows."""
        rows = []
        pull_date = pulled_at.date()

        for rank, thread in enumerate(threads, start=1):
            if not thread.snippet or not thread.snippet.topLevelComment:
                continue

            top_comment = thread.snippet.topLevelComment
            top_snippet = top_comment.snippet
            if not top_snippet:
                continue

            # Top-level comment
            commenter_channel_id = None
            if top_snippet.authorChannelId:
                commenter_channel_id = top_snippet.authorChannelId.get(
                    "value"
                )

            fact = FactComment(
                comment_id=top_comment.id,
                video_id=video_id,
                channel_id=channel_id,
                parent_comment_id=None,
                is_reply=False,
                commenter_channel_id=commenter_channel_id,
                commenter_name=top_snippet.authorDisplayName,
                comment_text=top_snippet.textDisplay,
                like_count=top_snippet.likeCount,
                reply_count=thread.snippet.totalReplyCount,
                published_at=(
                    parse_iso(top_snippet.publishedAt)
                    if top_snippet.publishedAt
                    else None
                ),
                updated_at=(
                    parse_iso(top_snippet.updatedAt)
                    if top_snippet.updatedAt
                    else None
                ),
                pulled_at=pulled_at,
                pull_date=pull_date,
                sample_strategy=sample_strategy,
                sample_rank=rank,
            )
            rows.append(fact.model_dump(mode="json"))

            # Replies (if present)
            if thread.replies and "comments" in thread.replies:
                for reply_comment in thread.replies["comments"]:
                    reply_snippet = reply_comment.snippet
                    if not reply_snippet:
                        continue

                    reply_commenter_id = None
                    if reply_snippet.authorChannelId:
                        reply_commenter_id = (
                            reply_snippet.authorChannelId.get("value")
                        )

                    reply_fact = FactComment(
                        comment_id=reply_comment.id,
                        video_id=video_id,
                        channel_id=channel_id,
                        parent_comment_id=top_comment.id,
                        is_reply=True,
                        commenter_channel_id=reply_commenter_id,
                        commenter_name=reply_snippet.authorDisplayName,
                        comment_text=reply_snippet.textDisplay,
                        like_count=reply_snippet.likeCount,
                        reply_count=0,
                        published_at=(
                            parse_iso(reply_snippet.publishedAt)
                            if reply_snippet.publishedAt
                            else None
                        ),
                        updated_at=(
                            parse_iso(reply_snippet.updatedAt)
                            if reply_snippet.updatedAt
                            else None
                        ),
                        pulled_at=pulled_at,
                        pull_date=pull_date,
                        sample_strategy=sample_strategy,
                        sample_rank=None,
                    )
                    rows.append(reply_fact.model_dump(mode="json"))

        return rows

    def _merge_comments(self, rows: list[dict[str, Any]]) -> int:
        """MERGE fact_comment rows on comment_id."""
        selects = []
        for row in rows:
            selects.append(
                f"SELECT "
                f"'{_esc(row['comment_id'])}' AS comment_id, "
                f"'{row['video_id']}' AS video_id, "
                f"'{row['channel_id']}' AS channel_id, "
                f"{_sql_str(row.get('parent_comment_id'))} AS parent_comment_id, "
                f"{_sql_bool(row.get('is_reply'))} AS is_reply, "
                f"{_sql_str(row.get('commenter_channel_id'))} AS commenter_channel_id, "
                f"{_sql_str(row.get('commenter_name'))} AS commenter_name, "
                f"{_sql_str(row.get('comment_text'))} AS comment_text, "
                f"{_sql_int(row.get('like_count'))} AS like_count, "
                f"{_sql_int(row.get('reply_count'))} AS reply_count, "
                f"{_sql_ts(row.get('published_at'))} AS published_at, "
                f"{_sql_ts(row.get('updated_at'))} AS updated_at, "
                f"{_sql_ts(row.get('pulled_at'))} AS pulled_at, "
                f"DATE '{row['pull_date']}' AS pull_date, "
                f"{_sql_str(row.get('sample_strategy'))} AS sample_strategy, "
                f"{_sql_int(row.get('sample_rank'))} AS sample_rank"
            )

        source = " UNION ALL ".join(selects)

        sql = f"""
        MERGE `{{project}}.{{dataset}}.fact_comment` T
        USING ({source}) S
        ON T.comment_id = S.comment_id
        WHEN MATCHED THEN UPDATE SET
            like_count = S.like_count,
            reply_count = S.reply_count,
            updated_at = S.updated_at,
            pulled_at = S.pulled_at,
            pull_date = S.pull_date,
            comment_text = S.comment_text
        WHEN NOT MATCHED THEN INSERT (
            comment_id, video_id, channel_id, parent_comment_id,
            is_reply, commenter_channel_id, commenter_name,
            comment_text, like_count, reply_count,
            published_at, updated_at, pulled_at, pull_date,
            sample_strategy, sample_rank
        ) VALUES (
            S.comment_id, S.video_id, S.channel_id, S.parent_comment_id,
            S.is_reply, S.commenter_channel_id, S.commenter_name,
            S.comment_text, S.like_count, S.reply_count,
            S.published_at, S.updated_at, S.pulled_at, S.pull_date,
            S.sample_strategy, S.sample_rank
        )
        """
        return self._bq.run_merge(sql)


# ---------------------------------------------------------------------------
# SQL literal helpers
# ---------------------------------------------------------------------------


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")


def _sql_str(value: str | None) -> str:
    if value is None:
        return "NULL"
    return f"'{_esc(value)}'"


def _sql_int(value: int | None) -> str:
    return str(value) if value is not None else "NULL"


def _sql_bool(value: bool | None) -> str:
    if value is None:
        return "CAST(NULL AS BOOL)"
    return "TRUE" if value else "FALSE"


def _sql_ts(value: str | None) -> str:
    if value is None:
        return "CAST(NULL AS TIMESTAMP)"
    return f"TIMESTAMP '{value}'"
