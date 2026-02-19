"""Pydantic models for YouTube Data API v3 responses.

These models validate the raw JSON from YouTube before any transformation.
They're intentionally loose (most fields Optional) since YouTube can omit fields.
"""

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Shared sub-objects
# ---------------------------------------------------------------------------


class Thumbnail(BaseModel):
    url: str
    width: int | None = None
    height: int | None = None


class ThumbnailSet(BaseModel):
    default: Thumbnail | None = None
    medium: Thumbnail | None = None
    high: Thumbnail | None = None
    standard: Thumbnail | None = None
    maxres: Thumbnail | None = None


class PageInfo(BaseModel):
    totalResults: int | None = None
    resultsPerPage: int | None = None


# ---------------------------------------------------------------------------
# Channel responses
# ---------------------------------------------------------------------------


class ChannelSnippet(BaseModel):
    title: str | None = None
    description: str | None = None
    customUrl: str | None = None
    publishedAt: str | None = None
    thumbnails: ThumbnailSet | None = None
    country: str | None = None


class ChannelStatistics(BaseModel):
    viewCount: str | None = None
    subscriberCount: str | None = None
    hiddenSubscriberCount: bool | None = None
    videoCount: str | None = None


class ChannelBrandingSettings(BaseModel):
    class Channel(BaseModel):
        keywords: str | None = None

    channel: Channel | None = None


class ChannelContentDetails(BaseModel):
    class RelatedPlaylists(BaseModel):
        likes: str | None = None
        uploads: str | None = None

    relatedPlaylists: RelatedPlaylists | None = None


class ChannelTopicDetails(BaseModel):
    topicIds: list[str] | None = None
    topicCategories: list[str] | None = None


class ChannelStatus(BaseModel):
    privacyStatus: str | None = None
    isLinked: bool | None = None
    madeForKids: bool | None = None


class ChannelItem(BaseModel):
    id: str
    snippet: ChannelSnippet | None = None
    statistics: ChannelStatistics | None = None
    brandingSettings: ChannelBrandingSettings | None = None
    contentDetails: ChannelContentDetails | None = None
    topicDetails: ChannelTopicDetails | None = None
    status: ChannelStatus | None = None


class ChannelListResponse(BaseModel):
    items: list[ChannelItem] = []
    pageInfo: PageInfo | None = None


# ---------------------------------------------------------------------------
# Video responses
# ---------------------------------------------------------------------------


class VideoSnippet(BaseModel):
    publishedAt: str | None = None
    channelId: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnails: ThumbnailSet | None = None
    channelTitle: str | None = None
    tags: list[str] | None = None
    categoryId: str | None = None
    liveBroadcastContent: str | None = None


class VideoStatistics(BaseModel):
    viewCount: str | None = None
    likeCount: str | None = None
    favoriteCount: str | None = None
    commentCount: str | None = None


class VideoContentDetails(BaseModel):
    duration: str | None = None
    dimension: str | None = None
    definition: str | None = None
    caption: str | None = None
    licensedContent: bool | None = None
    hasCustomThumbnail: bool | None = None


class VideoStatus(BaseModel):
    uploadStatus: str | None = None
    privacyStatus: str | None = None
    license: str | None = None
    embeddable: bool | None = None
    publicStatsViewable: bool | None = None
    madeForKids: bool | None = None
    selfDeclaredMadeForKids: bool | None = None


class VideoTopicDetails(BaseModel):
    topicIds: list[str] | None = None
    topicCategories: list[str] | None = None


class VideoPaidProductPlacement(BaseModel):
    hasPaidProductPlacement: bool | None = None


class VideoItem(BaseModel):
    id: str
    snippet: VideoSnippet | None = None
    statistics: VideoStatistics | None = None
    contentDetails: VideoContentDetails | None = None
    status: VideoStatus | None = None
    topicDetails: VideoTopicDetails | None = None
    paidProductPlacementDetails: VideoPaidProductPlacement | None = None


class VideoListResponse(BaseModel):
    items: list[VideoItem] = []
    pageInfo: PageInfo | None = None


# ---------------------------------------------------------------------------
# Comment responses
# ---------------------------------------------------------------------------


class CommentSnippet(BaseModel):
    authorDisplayName: str | None = None
    authorProfileImageUrl: str | None = None
    authorChannelId: dict[str, str] | None = None
    textDisplay: str | None = None
    textOriginal: str | None = None
    likeCount: int | None = None
    publishedAt: str | None = None
    updatedAt: str | None = None


class Comment(BaseModel):
    id: str
    snippet: CommentSnippet | None = None


class CommentThreadSnippet(BaseModel):
    channelId: str | None = None
    videoId: str | None = None
    topLevelComment: Comment | None = None
    canReply: bool | None = None
    totalReplyCount: int | None = None
    isPublic: bool | None = None


class CommentThread(BaseModel):
    id: str
    snippet: CommentThreadSnippet | None = None
    replies: dict[str, list[Comment]] | None = None


class CommentThreadListResponse(BaseModel):
    items: list[CommentThread] = []
    nextPageToken: str | None = None
    pageInfo: PageInfo | None = None
