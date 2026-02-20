"""Tests for ChannelTransformer using real MrBeast API response data."""

import copy
from unittest.mock import MagicMock

from src.engines.transforms.base import TransformResult
from src.engines.transforms.channels import ChannelTransformer
from src.models.raw import ChannelListResponse


class TestBuildDimChannels:
    """Unit tests for _build_dim_channels — raw item → DimChannel dict."""

    def _build(self, channel_item: dict, bq: MagicMock) -> dict:
        transformer = ChannelTransformer(bq)
        response = ChannelListResponse.model_validate({"items": [channel_item]})
        rows = transformer._build_dim_channels(response.items)
        assert len(rows) == 1
        return rows[0]

    def test_channel_id(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["channel_id"] == "UCX6OQ3DkcsbYNE6H8uQQuVA"

    def test_channel_name(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["channel_name"] == "MrBeast"

    def test_custom_url(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["custom_url"] == "@mrbeast"

    def test_subscriber_count_parsed_from_string(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["subscriber_count"] == 461_000_000

    def test_view_count_parsed_from_string(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["view_count"] == 107_687_060_592

    def test_video_count_parsed_from_string(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["video_count"] == 938

    def test_uploads_playlist_id(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["uploads_playlist_id"] == "UUX6OQ3DkcsbYNE6H8uQQuVA"

    def test_made_for_kids_false(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["made_for_kids"] is False

    def test_hidden_subscriber_count_false(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["hidden_subscriber_count"] is False

    def test_channel_keywords(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["channel_keywords"] == "mrbeast6000 beast mrbeast Mr.Beast mr"

    def test_topic_categories(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert "https://en.wikipedia.org/wiki/Entertainment" in row["topics"]
        assert "https://en.wikipedia.org/wiki/Lifestyle_(sociology)" in row["topics"]

    def test_topic_ids(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert "/m/02jjt" in row["topic_ids"]
        assert "/m/019_rr" in row["topic_ids"]

    def test_thumbnail_picks_highest_res(self, channel_item, mock_bq):
        # high (800px) is highest available — maxres/standard not present
        row = self._build(channel_item, mock_bq)
        assert "s800" in (row["channel_thumbnail_url"] or "")

    def test_channel_created_at_parsed(self, channel_item, mock_bq):
        row = self._build(channel_item, mock_bq)
        assert row["channel_created_at"] is not None
        assert "2012-02-20" in str(row["channel_created_at"])

    def test_empty_items_returns_empty(self, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        rows = transformer._build_dim_channels([])
        assert rows == []


class TestBuildChannelSnapshots:
    """Unit tests for _build_channel_snapshots — raw item → FactChannelSnapshot dict."""

    def _build_snap(self, channel_item: dict, bq: MagicMock) -> dict:
        transformer = ChannelTransformer(bq)
        response = ChannelListResponse.model_validate({"items": [channel_item]})
        rows = transformer._build_channel_snapshots(response.items)
        assert len(rows) == 1
        return rows[0]

    def test_channel_id(self, channel_item, mock_bq):
        row = self._build_snap(channel_item, mock_bq)
        assert row["channel_id"] == "UCX6OQ3DkcsbYNE6H8uQQuVA"

    def test_view_count(self, channel_item, mock_bq):
        row = self._build_snap(channel_item, mock_bq)
        assert row["view_count"] == 107_687_060_592

    def test_subscriber_count(self, channel_item, mock_bq):
        row = self._build_snap(channel_item, mock_bq)
        assert row["subscriber_count"] == 461_000_000

    def test_video_count(self, channel_item, mock_bq):
        row = self._build_snap(channel_item, mock_bq)
        assert row["video_count"] == 938

    def test_deltas_none_when_no_previous(self, channel_item, mock_bq):
        # mock_bq.run_query returns [] → no previous snapshot
        row = self._build_snap(channel_item, mock_bq)
        assert row["views_delta"] is None
        assert row["subs_delta"] is None
        assert row["videos_delta"] is None

    def test_deltas_computed_when_previous_exists(
        self, channel_item, mock_bq_with_prev_channel_snapshot
    ):
        row = self._build_snap(channel_item, mock_bq_with_prev_channel_snapshot)
        # 107_687_060_592 - 107_000_000_000 = 687_060_592
        assert row["views_delta"] == 687_060_592
        # 461_000_000 - 460_000_000 = 1_000_000
        assert row["subs_delta"] == 1_000_000
        # 938 - 935 = 3
        assert row["videos_delta"] == 3


class TestChannelTransformerFull:
    """Integration-style tests for ChannelTransformer.transform()."""

    def test_transform_returns_two_results(self, channel_item, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        results = transformer.transform([channel_item])
        assert len(results) == 2

    def test_transform_dim_channel_result(self, channel_item, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        results = transformer.transform([channel_item])
        dim_result = next(r for r in results if r.table_name == "dim_channel")
        assert isinstance(dim_result, TransformResult)
        assert dim_result.write_method == "merge"

    def test_transform_snapshot_result(self, channel_item, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        results = transformer.transform([channel_item])
        snap_result = next(r for r in results if r.table_name == "fact_channel_snapshot")
        assert isinstance(snap_result, TransformResult)
        assert snap_result.write_method == "merge"

    def test_transform_calls_run_merge_twice(self, channel_item, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        transformer.transform([channel_item])
        assert mock_bq.run_merge.call_count == 2

    def test_transform_merge_sql_contains_channel_id(self, channel_item, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        transformer.transform([channel_item])
        all_sql = " ".join(str(c) for c in mock_bq.run_merge.call_args_list)
        assert "UCX6OQ3DkcsbYNE6H8uQQuVA" in all_sql

    def test_transform_merge_sql_contains_subscriber_count(self, channel_item, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        transformer.transform([channel_item])
        all_sql = " ".join(str(c) for c in mock_bq.run_merge.call_args_list)
        assert "461000000" in all_sql

    def test_transform_empty_list_returns_empty(self, mock_bq):
        transformer = ChannelTransformer(mock_bq)
        results = transformer.transform([])
        assert results == []
        mock_bq.run_merge.assert_not_called()


class TestChannelSqlEscaping:
    """SQL escaping edge cases — newlines, quotes, backslashes in channel text fields.

    These verify the bug fix for 'Unclosed string literal' BigQuery errors
    caused by literal newlines and other special characters in channel descriptions
    being embedded unescaped into MERGE SQL strings.
    """

    def _sql_for_dim_channel(self, channel_item: dict, mock_bq: MagicMock) -> str:
        """Transform and return the dim_channel MERGE SQL (first run_merge call)."""
        transformer = ChannelTransformer(mock_bq)
        transformer.transform([channel_item])
        # First call = _merge_dim_channels
        return mock_bq.run_merge.call_args_list[0][0][0]

    def test_newline_in_description_is_escaped(self, channel_item, mock_bq):
        item = copy.deepcopy(channel_item)
        item["snippet"]["description"] = "Line one\nLine two"
        sql = self._sql_for_dim_channel(item, mock_bq)
        assert "Line one\\nLine two" in sql
        assert "Line one\nLine two" not in sql  # raw newline must not appear

    def test_carriage_return_in_description_is_escaped(self, channel_item, mock_bq):
        item = copy.deepcopy(channel_item)
        item["snippet"]["description"] = "Windows\r\nStyle"
        sql = self._sql_for_dim_channel(item, mock_bq)
        assert "Windows\\r\\nStyle" in sql
        assert "Windows\r\nStyle" not in sql

    def test_single_quote_in_channel_name_is_escaped(self, channel_item, mock_bq):
        item = copy.deepcopy(channel_item)
        item["snippet"]["title"] = "Daniel's Channel"
        sql = self._sql_for_dim_channel(item, mock_bq)
        assert "Daniel\\'s Channel" in sql

    def test_backslash_in_channel_keywords_is_escaped(self, channel_item, mock_bq):
        item = copy.deepcopy(channel_item)
        item["brandingSettings"]["channel"]["keywords"] = "tech\\gear"
        sql = self._sql_for_dim_channel(item, mock_bq)
        assert "tech\\\\gear" in sql

    def test_combination_of_special_chars_in_description(self, channel_item, mock_bq):
        # Realistic description: apostrophe + newline + backslash
        item = copy.deepcopy(channel_item)
        item["snippet"]["description"] = "Jimmy's channel\nCheck out C:\\stuff"
        sql = self._sql_for_dim_channel(item, mock_bq)
        assert "Jimmy\\'s channel\\nCheck out C:\\\\stuff" in sql
