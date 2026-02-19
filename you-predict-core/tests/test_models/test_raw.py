"""Tests for src.models.raw — YouTube API response parsing."""

from src.models.raw import (
    ChannelListResponse,
    CommentThreadListResponse,
    VideoListResponse,
)


class TestChannelListResponse:
    def test_parse_minimal(self):
        data = {"items": [{"id": "UC123"}]}
        resp = ChannelListResponse.model_validate(data)
        assert len(resp.items) == 1
        assert resp.items[0].id == "UC123"

    def test_parse_empty(self):
        resp = ChannelListResponse.model_validate({"items": []})
        assert resp.items == []

    def test_parse_with_snippet(self):
        data = {
            "items": [{
                "id": "UC123",
                "snippet": {
                    "title": "Test Channel",
                    "description": "A test channel",
                    "customUrl": "@test",
                    "publishedAt": "2020-01-01T00:00:00Z",
                },
                "statistics": {
                    "viewCount": "100000",
                    "subscriberCount": "5000",
                    "videoCount": "200",
                },
            }]
        }
        resp = ChannelListResponse.model_validate(data)
        item = resp.items[0]
        assert item.snippet is not None
        assert item.snippet.title == "Test Channel"
        assert item.statistics is not None
        assert item.statistics.viewCount == "100000"

    def test_parse_with_topic_details(self):
        data = {
            "items": [{
                "id": "UC123",
                "topicDetails": {
                    "topicCategories": ["https://en.wikipedia.org/wiki/Gaming"],
                },
            }]
        }
        resp = ChannelListResponse.model_validate(data)
        td = resp.items[0].topicDetails
        assert td is not None
        assert td.topicCategories == ["https://en.wikipedia.org/wiki/Gaming"]


class TestVideoListResponse:
    def test_parse_minimal(self):
        data = {"items": [{"id": "abc123"}]}
        resp = VideoListResponse.model_validate(data)
        assert resp.items[0].id == "abc123"

    def test_parse_with_all_parts(self):
        data = {
            "items": [{
                "id": "abc123",
                "snippet": {
                    "publishedAt": "2026-02-15T08:00:00Z",
                    "channelId": "UC123",
                    "title": "Test Video",
                    "tags": ["tag1", "tag2"],
                    "categoryId": "24",
                },
                "statistics": {
                    "viewCount": "10000",
                    "likeCount": "500",
                    "commentCount": "50",
                },
                "contentDetails": {
                    "duration": "PT10M30S",
                    "definition": "hd",
                    "caption": "true",
                    "licensedContent": True,
                    "hasCustomThumbnail": True,
                },
                "status": {
                    "privacyStatus": "public",
                    "madeForKids": False,
                },
            }]
        }
        resp = VideoListResponse.model_validate(data)
        item = resp.items[0]
        assert item.snippet is not None
        assert item.snippet.tags == ["tag1", "tag2"]
        assert item.contentDetails is not None
        assert item.contentDetails.duration == "PT10M30S"
        assert item.status is not None
        assert item.status.madeForKids is False

    def test_statistics_only_response(self):
        """This is what snapshot polls return — statistics part only."""
        data = {
            "items": [{
                "id": "abc123",
                "statistics": {
                    "viewCount": "5000",
                    "likeCount": "200",
                    "commentCount": "30",
                },
            }]
        }
        resp = VideoListResponse.model_validate(data)
        item = resp.items[0]
        assert item.snippet is None
        assert item.statistics is not None
        assert item.statistics.viewCount == "5000"


class TestCommentThreadListResponse:
    def test_parse_minimal(self):
        data = {"items": [{"id": "thread_1"}]}
        resp = CommentThreadListResponse.model_validate(data)
        assert len(resp.items) == 1

    def test_parse_with_comments(self):
        data = {
            "items": [{
                "id": "thread_1",
                "snippet": {
                    "videoId": "abc123",
                    "topLevelComment": {
                        "id": "cmt_1",
                        "snippet": {
                            "authorDisplayName": "User1",
                            "textOriginal": "Great video!",
                            "likeCount": 5,
                            "publishedAt": "2026-02-15T10:00:00Z",
                        },
                    },
                    "totalReplyCount": 2,
                },
            }]
        }
        resp = CommentThreadListResponse.model_validate(data)
        thread = resp.items[0]
        assert thread.snippet is not None
        assert thread.snippet.videoId == "abc123"
        tlc = thread.snippet.topLevelComment
        assert tlc is not None
        assert tlc.snippet is not None
        assert tlc.snippet.textOriginal == "Great video!"

    def test_pagination_token(self):
        data = {
            "items": [{"id": "t1"}],
            "nextPageToken": "CDIQAA",
        }
        resp = CommentThreadListResponse.model_validate(data)
        assert resp.nextPageToken == "CDIQAA"
