"""Tests for VideoTransformer using real YouTube API response data."""

from unittest.mock import MagicMock

from src.engines.transforms.base import TransformResult
from src.engines.transforms.videos import VideoTransformer
from src.models.raw import VideoListResponse


class TestBuildDimVideos:
    """Unit tests for _build_dim_videos — raw item → DimVideo dict."""

    def _build(self, video_item: dict, bq: MagicMock) -> dict:
        transformer = VideoTransformer(bq)
        response = VideoListResponse.model_validate({"items": [video_item]})
        rows = transformer._build_dim_videos(response.items)
        assert len(rows) == 1
        return rows[0]

    # --- Identity & ownership ---

    def test_video_id_celebrities(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["video_id"] == "QJI0an6irrA"

    def test_channel_id_celebrities(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["channel_id"] == "UCX6OQ3DkcsbYNE6H8uQQuVA"

    def test_title_celebrities(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["title"] == "30 Celebrities Fight For $1,000,000!"

    # --- Duration parsing (PT41M58S = 41*60 + 58 = 2518 seconds) ---

    def test_duration_celebrities(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["duration_seconds"] == 2518

    def test_duration_sky(self, video_item_sky, mock_bq):
        # PT37M26S = 37*60 + 26 = 2246 seconds
        row = self._build(video_item_sky, mock_bq)
        assert row["duration_seconds"] == 2246

    # --- Stats (parsed from API strings) ---

    def test_view_count(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["view_count"] == 82_949_853

    def test_like_count(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["like_count"] == 2_127_007

    def test_comment_count(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["comment_count"] == 95_277

    # --- Content metadata ---

    def test_caption_true_when_string_true(self, video_item_celebrities, mock_bq):
        # API returns caption as the string "true" or "false"
        row = self._build(video_item_celebrities, mock_bq)
        assert row["caption_available"] is True

    def test_not_livestream(self, video_item_celebrities, mock_bq):
        # liveBroadcastContent = "none"
        row = self._build(video_item_celebrities, mock_bq)
        assert row["is_livestream"] is False

    def test_category_id(self, video_item_celebrities, mock_bq):
        # categoryId is "24" in the API → cast to int 24
        row = self._build(video_item_celebrities, mock_bq)
        assert row["category_id"] == 24

    def test_licensed_content_true(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["licensed_content"] is True

    def test_definition_hd(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["definition"] == "hd"

    def test_made_for_kids_false(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["made_for_kids"] is False

    # --- Topics ---

    def test_topics_celebrities(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert "https://en.wikipedia.org/wiki/Entertainment" in row["topics"]
        assert "https://en.wikipedia.org/wiki/Television_program" in row["topics"]

    def test_topics_sky(self, video_item_sky, mock_bq):
        row = self._build(video_item_sky, mock_bq)
        assert "https://en.wikipedia.org/wiki/Lifestyle_(sociology)" in row["topics"]
        assert "https://en.wikipedia.org/wiki/Tourism" in row["topics"]

    # --- Thumbnails (maxres preferred) ---

    def test_thumbnail_maxres_preferred(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["thumbnail_url"] == "https://i.ytimg.com/vi/QJI0an6irrA/maxresdefault.jpg"

    # --- Published at ---

    def test_published_at_parsed(self, video_item_celebrities, mock_bq):
        row = self._build(video_item_celebrities, mock_bq)
        assert row["published_at"] is not None
        assert "2026-01-07" in str(row["published_at"])

    # --- Empty items ---

    def test_empty_items(self, mock_bq):
        transformer = VideoTransformer(mock_bq)
        rows = transformer._build_dim_videos([])
        assert rows == []


class TestVideoTransformerFull:
    """Integration-style tests for VideoTransformer.transform()."""

    def test_transform_returns_single_result(self, video_item_celebrities, mock_bq):
        transformer = VideoTransformer(mock_bq)
        result = transformer.transform([video_item_celebrities])
        assert isinstance(result, TransformResult)
        assert result.table_name == "dim_video"
        assert result.write_method == "merge"

    def test_transform_calls_run_merge_once(self, video_item_celebrities, mock_bq):
        transformer = VideoTransformer(mock_bq)
        transformer.transform([video_item_celebrities])
        mock_bq.run_merge.assert_called_once()

    def test_transform_merge_sql_contains_video_id(self, video_item_celebrities, mock_bq):
        transformer = VideoTransformer(mock_bq)
        transformer.transform([video_item_celebrities])
        sql = mock_bq.run_merge.call_args[0][0]
        assert "QJI0an6irrA" in sql

    def test_transform_merge_sql_contains_duration(self, video_item_celebrities, mock_bq):
        transformer = VideoTransformer(mock_bq)
        transformer.transform([video_item_celebrities])
        sql = mock_bq.run_merge.call_args[0][0]
        assert "2518" in sql

    def test_transform_empty_returns_zero(self, mock_bq):
        transformer = VideoTransformer(mock_bq)
        result = transformer.transform([])
        assert result.rows_written == 0
        mock_bq.run_merge.assert_not_called()

    def test_transform_two_videos(
        self, video_item_celebrities, video_item_sky, mock_bq
    ):
        transformer = VideoTransformer(mock_bq)
        result = transformer.transform([video_item_celebrities, video_item_sky])
        assert result.table_name == "dim_video"
        sql = mock_bq.run_merge.call_args[0][0]
        assert "QJI0an6irrA" in sql
        assert "ZFoNBxpXen4" in sql
