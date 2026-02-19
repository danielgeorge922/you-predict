"""Tests for CommentTransformer using real YouTube comment thread data."""

from datetime import UTC, datetime

from src.engines.transforms.base import TransformResult
from src.engines.transforms.comments import CommentTransformer
from src.models.raw import CommentThreadListResponse

_VIDEO_ID = "QJI0an6irrA"
_CHANNEL_ID = "UCX6OQ3DkcsbYNE6H8uQQuVA"
_PULLED_AT = datetime(2026, 1, 8, 12, 0, 0, tzinfo=UTC)


class TestFlattenThreads:
    """Unit tests for _flatten_threads — thread list → flat row list."""

    def _flatten(self, comment_threads: list[dict], bq) -> list[dict]:
        transformer = CommentTransformer(bq)
        response = CommentThreadListResponse.model_validate({"items": comment_threads})
        return transformer._flatten_threads(
            response.items, _VIDEO_ID, _CHANNEL_ID, _PULLED_AT, "relevance"
        )

    def test_top_level_comment_count(self, comment_threads, mock_bq):
        # 2 threads → at least 2 rows (top-level), plus 1 reply
        rows = self._flatten(comment_threads, mock_bq)
        assert len(rows) == 3  # 2 top-level + 1 reply

    def test_first_comment_id(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        top_level = [r for r in rows if not r["is_reply"]]
        ids = {r["comment_id"] for r in top_level}
        assert "comment_001" in ids
        assert "comment_003" in ids

    def test_top_level_is_not_reply(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        top_level = [r for r in rows if r["comment_id"] == "comment_001"]
        assert len(top_level) == 1
        assert top_level[0]["is_reply"] is False
        assert top_level[0]["parent_comment_id"] is None

    def test_top_level_comment_text(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        row = next(r for r in rows if r["comment_id"] == "comment_001")
        assert "insane" in row["comment_text"]

    def test_top_level_like_count(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        row = next(r for r in rows if r["comment_id"] == "comment_001")
        assert row["like_count"] == 342

    def test_top_level_commenter_name(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        row = next(r for r in rows if r["comment_id"] == "comment_001")
        assert row["commenter_name"] == "TopFan123"

    def test_top_level_commenter_channel_id(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        row = next(r for r in rows if r["comment_id"] == "comment_001")
        assert row["commenter_channel_id"] == "UCfan_channel_001"

    def test_reply_is_flagged(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        reply = next(r for r in rows if r["comment_id"] == "comment_002")
        assert reply["is_reply"] is True

    def test_reply_parent_id(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        reply = next(r for r in rows if r["comment_id"] == "comment_002")
        assert reply["parent_comment_id"] == "comment_001"

    def test_reply_text(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        reply = next(r for r in rows if r["comment_id"] == "comment_002")
        assert "Agreed" in reply["comment_text"]

    def test_reply_has_no_sample_rank(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        reply = next(r for r in rows if r["comment_id"] == "comment_002")
        assert reply["sample_rank"] is None

    def test_top_level_sample_rank_sequential(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        top_level = sorted(
            [r for r in rows if not r["is_reply"]],
            key=lambda r: r["sample_rank"] or 999,
        )
        assert top_level[0]["sample_rank"] == 1
        assert top_level[1]["sample_rank"] == 2

    def test_video_id_and_channel_id_denormalized(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        for row in rows:
            assert row["video_id"] == _VIDEO_ID
            assert row["channel_id"] == _CHANNEL_ID

    def test_sample_strategy(self, comment_threads, mock_bq):
        rows = self._flatten(comment_threads, mock_bq)
        top_level = [r for r in rows if not r["is_reply"]]
        for row in top_level:
            assert row["sample_strategy"] == "relevance"

    def test_thread_with_null_replies_skipped(self, comment_threads, mock_bq):
        # thread_002 has replies=null — should still get its top-level comment
        rows = self._flatten(comment_threads, mock_bq)
        thread2 = [r for r in rows if r["comment_id"] == "comment_003"]
        assert len(thread2) == 1


class TestCommentTransformerFull:
    """Integration tests for CommentTransformer.transform()."""

    def test_returns_fact_comment_result(self, comment_threads, mock_bq):
        transformer = CommentTransformer(mock_bq)
        result = transformer.transform(
            raw_items=comment_threads,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            pulled_at=_PULLED_AT,
        )
        assert isinstance(result, TransformResult)
        assert result.table_name == "fact_comment"
        assert result.write_method == "merge"

    def test_merge_called_once(self, comment_threads, mock_bq):
        transformer = CommentTransformer(mock_bq)
        transformer.transform(
            raw_items=comment_threads,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            pulled_at=_PULLED_AT,
        )
        mock_bq.run_merge.assert_called_once()

    def test_merge_sql_contains_comment_ids(self, comment_threads, mock_bq):
        transformer = CommentTransformer(mock_bq)
        transformer.transform(
            raw_items=comment_threads,
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            pulled_at=_PULLED_AT,
        )
        sql = mock_bq.run_merge.call_args[0][0]
        assert "comment_001" in sql
        assert "comment_002" in sql
        assert "comment_003" in sql

    def test_empty_items_returns_zero(self, mock_bq):
        transformer = CommentTransformer(mock_bq)
        result = transformer.transform(
            raw_items=[],
            video_id=_VIDEO_ID,
            channel_id=_CHANNEL_ID,
            pulled_at=_PULLED_AT,
        )
        assert result.rows_written == 0
        mock_bq.run_merge.assert_not_called()
