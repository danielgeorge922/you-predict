"""
Channel management API routes.

These endpoints handle YouTube channel operations:
- Adding channels to track
- Fetching channel information
- Managing channel data collection
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import structlog

from src.data.collectors import YouTubeCollector

logger = structlog.get_logger()

# Create router for channel endpoints
router = APIRouter()


class ChannelRequest(BaseModel):
    """Request to add a new channel."""
    channel_id: str
    channel_name: Optional[str] = None

class ChannelResponse(BaseModel):
    """Channel information response."""
    channel_id: str
    channel_name: str
    subscriber_count: int
    view_count: int
    video_count: int
    

@router.get("/test-api")
async def test_youtube_api():
    """
    Test YouTube API connectivity.
    
    This is a simple endpoint to verify our YouTube API
    integration is working correctly.
    """
    try:
        collector = YouTubeCollector()
        
        # Test with MrBeast's channel (very popular, should always exist)
        test_channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"
        
        logger.info("Testing YouTube API", channel_id=test_channel_id)
        
        channel_info = collector.get_channel_info(test_channel_id)
        
        if channel_info:
            return {
                "status": "success",
                "message": "YouTube API working correctly",
                "test_channel": {
                    "name": channel_info['channel_name'],
                    "subscribers": channel_info['subscriber_count'],
                    "videos": channel_info['video_count']
                },
                "quota_used": collector.quota_used
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch channel data"
            )
            
    except Exception as e:
        logger.error("YouTube API test failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"YouTube API test failed: {str(e)}"
        )


@router.get("/info/{channel_id}")
async def get_channel_info(channel_id: str):
    """
    Get information about a YouTube channel.
    
    Args:
        channel_id: YouTube channel ID (starts with UC)
        
    Returns:
        Channel metadata including subscriber count, video count, etc.
    """
    try:
        collector = YouTubeCollector()
        
        logger.info("Fetching channel info", channel_id=channel_id)
        
        channel_info = collector.get_channel_info(channel_id)
        
        if channel_info:
            return {
                "channel_id": channel_info['channel_id'],
                "channel_name": channel_info['channel_name'],
                "subscriber_count": channel_info['subscriber_count'],
                "view_count": channel_info['view_count'],
                "video_count": channel_info['video_count'],
                "created_at": channel_info['created_at'],
                "thumbnail_url": channel_info['thumbnail_url']
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Channel {channel_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get channel info", error=str(e), channel_id=channel_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch channel information: {str(e)}"
        )


@router.get("/videos/{channel_id}")
async def get_channel_videos(channel_id: str, limit: int = 10):
    """
    Get recent videos from a YouTube channel.
    
    Args:
        channel_id: YouTube channel ID
        limit: Maximum number of videos to return (max 50)
        
    Returns:
        List of recent videos with metadata
    """
    if limit > 50:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 50"
        )
    
    try:
        collector = YouTubeCollector()
        
        logger.info("Fetching channel videos", channel_id=channel_id, limit=limit)
        
        videos = collector.get_recent_videos(channel_id, max_results=limit)
        
        # Format response
        formatted_videos = []
        for video in videos:
            formatted_videos.append({
                "video_id": video['video_id'],
                "title": video['title'],
                "published_at": video['published_at'],
                "view_count": video['view_count'],
                "like_count": video['like_count'],
                "comment_count": video['comment_count'],
                "duration_seconds": video['duration_seconds'],
                "thumbnail_url": video['thumbnail_url']
            })
        
        return {
            "channel_id": channel_id,
            "videos": formatted_videos,
            "total_count": len(formatted_videos),
            "quota_used": collector.quota_used
        }
        
    except Exception as e:
        logger.error("Failed to get channel videos", error=str(e), channel_id=channel_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch channel videos: {str(e)}"
        )


@router.get("/video/{video_id}")
async def get_video_details(video_id: str):
    """
    Get detailed information about a specific video.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Detailed video metadata
    """
    try:
        collector = YouTubeCollector()
        
        logger.info("Fetching video details", video_id=video_id)
        
        video_info = collector.get_video_details(video_id)
        
        if video_info:
            return {
                "video_id": video_info['video_id'],
                "channel_id": video_info['channel_id'],
                "title": video_info['title'],
                "description": video_info['description'][:500] + "..." if len(video_info['description']) > 500 else video_info['description'],
                "published_at": video_info['published_at'],
                "view_count": video_info['view_count'],
                "like_count": video_info['like_count'],
                "comment_count": video_info['comment_count'],
                "duration_seconds": video_info['duration_seconds'],
                "category_id": video_info['category_id'],
                "tags": video_info['tags'][:10],  # Limit tags for response size
                "thumbnail_url": video_info['thumbnail_url']
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Video {video_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get video details", error=str(e), video_id=video_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch video details: {str(e)}"
        )


@router.get("/quota")
async def get_api_quota_status():
    """
    Check YouTube API quota usage.
    
    Returns current quota usage and remaining quota.
    Useful for monitoring API consumption.
    """
    try:
        collector = YouTubeCollector()
        
        return {
            "quota_used_today": collector.quota_used,
            "daily_quota_limit": collector.daily_quota_limit,
            "quota_remaining": collector.check_quota_remaining(),
            "quota_percentage_used": round((collector.quota_used / collector.daily_quota_limit) * 100, 2)
        }
        
    except Exception as e:
        logger.error("Failed to get quota status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quota status: {str(e)}"
        )