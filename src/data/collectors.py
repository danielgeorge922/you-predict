"""
YouTube API data collection.

This module handles all interactions with the YouTube Data API v3,
including fetching channel info, video metadata, and statistics.
"""

import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import structlog

from src.config.settings import settings

logger = structlog.get_logger()


class YouTubeCollector:
    """
    Handles YouTube API data collection.
    
    This class manages API quota, rate limiting, and data extraction
    from YouTube channels and videos.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube API client."""
        self.api_key = api_key or settings.youtube_api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.quota_used = 0
        self.daily_quota_limit = settings.youtube_api_quota_limit
        
        logger.info("YouTube API client initialized")
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get basic channel information.
        
        Args:
            channel_id: YouTube channel ID (starts with UC)
            
        Returns:
            Dictionary with channel metadata or None if error
        """
        try:
            logger.info("Fetching channel info", channel_id=channel_id)
            
            # API call costs 1 quota unit
            response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
            
            self.quota_used += 1
            
            if not response.get('items'):
                logger.warning("Channel not found", channel_id=channel_id)
                return None
            
            channel_data = response['items'][0]
            
            # Extract relevant information
            channel_info = {
                'channel_id': channel_id,
                'channel_name': channel_data['snippet']['title'],
                'description': channel_data['snippet'].get('description', ''),
                'subscriber_count': int(channel_data['statistics'].get('subscriberCount', 0)),
                'view_count': int(channel_data['statistics'].get('viewCount', 0)),
                'video_count': int(channel_data['statistics'].get('videoCount', 0)),
                'created_at': channel_data['snippet']['publishedAt'],
                'thumbnail_url': channel_data['snippet']['thumbnails']['default']['url'],
                'uploads_playlist_id': channel_data['contentDetails']['relatedPlaylists']['uploads']
            }
            
            logger.info(
                "Channel info retrieved",
                channel_name=channel_info['channel_name'],
                subscribers=channel_info['subscriber_count']
            )
            
            return channel_info
            
        except HttpError as e:
            logger.error("YouTube API error", error=str(e), channel_id=channel_id)
            return None
        except Exception as e:
            logger.error("Unexpected error", error=str(e), channel_id=channel_id)
            return None
    
    def get_recent_videos(self, channel_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent videos from a channel.
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch (max 50 per call)
            
        Returns:
            List of video dictionaries
        """
        try:
            # First, get the uploads playlist ID
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return []
            
            uploads_playlist_id = channel_info['uploads_playlist_id']
            
            logger.info(
                "Fetching recent videos",
                channel_id=channel_id,
                max_results=max_results
            )
            
            # Get videos from uploads playlist (costs 1 quota unit)
            playlist_response = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50)  # API limit is 50
            ).execute()
            
            self.quota_used += 1
            
            video_ids = []
            video_basic_info = {}
            
            for item in playlist_response.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
                
                # Store basic info from playlist
                video_basic_info[video_id] = {
                    'video_id': video_id,
                    'channel_id': channel_id,
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                }
            
            # Get detailed video statistics (costs 1 quota unit per 50 videos)
            if video_ids:
                videos_response = self.youtube.videos().list(
                    part='statistics,contentDetails,snippet',
                    id=','.join(video_ids)
                ).execute()
                
                self.quota_used += 1
                
                # Combine basic info with detailed stats
                videos = []
                for video_data in videos_response.get('items', []):
                    video_id = video_data['id']
                    basic_info = video_basic_info.get(video_id, {})
                    
                    # Parse duration (PT4M13S -> seconds)
                    duration_str = video_data['contentDetails']['duration']
                    duration_seconds = self._parse_duration(duration_str)
                    
                    video_info = {
                        **basic_info,
                        'view_count': int(video_data['statistics'].get('viewCount', 0)),
                        'like_count': int(video_data['statistics'].get('likeCount', 0)),
                        'comment_count': int(video_data['statistics'].get('commentCount', 0)),
                        'duration_seconds': duration_seconds,
                        'category_id': video_data['snippet'].get('categoryId'),
                        'default_language': video_data['snippet'].get('defaultLanguage'),
                        'tags': video_data['snippet'].get('tags', [])
                    }
                    
                    videos.append(video_info)
                
                logger.info(
                    "Videos retrieved",
                    channel_id=channel_id,
                    video_count=len(videos),
                    quota_used=self.quota_used
                )
                
                return videos
            
            return []
            
        except HttpError as e:
            logger.error("YouTube API error", error=str(e), channel_id=channel_id)
            return []
        except Exception as e:
            logger.error("Unexpected error", error=str(e), channel_id=channel_id)
            return []
    
    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a single video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video details or None if error
        """
        try:
            logger.info("Fetching video details", video_id=video_id)
            
            # API call costs 1 quota unit
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            self.quota_used += 1
            
            if not response.get('items'):
                logger.warning("Video not found", video_id=video_id)
                return None
            
            video_data = response['items'][0]
            
            # Parse duration
            duration_str = video_data['contentDetails']['duration']
            duration_seconds = self._parse_duration(duration_str)
            
            video_info = {
                'video_id': video_id,
                'channel_id': video_data['snippet']['channelId'],
                'title': video_data['snippet']['title'],
                'description': video_data['snippet'].get('description', ''),
                'published_at': video_data['snippet']['publishedAt'],
                'view_count': int(video_data['statistics'].get('viewCount', 0)),
                'like_count': int(video_data['statistics'].get('likeCount', 0)),
                'comment_count': int(video_data['statistics'].get('commentCount', 0)),
                'duration_seconds': duration_seconds,
                'category_id': video_data['snippet'].get('categoryId'),
                'default_language': video_data['snippet'].get('defaultLanguage'),
                'tags': video_data['snippet'].get('tags', []),
                'thumbnail_url': video_data['snippet']['thumbnails']['default']['url']
            }
            
            logger.info("Video details retrieved", video_id=video_id)
            return video_info
            
        except HttpError as e:
            logger.error("YouTube API error", error=str(e), video_id=video_id)
            return None
        except Exception as e:
            logger.error("Unexpected error", error=str(e), video_id=video_id)
            return None
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse YouTube duration format (PT4M13S) to seconds.
        
        Args:
            duration_str: Duration in ISO 8601 format (PT4M13S)
            
        Returns:
            Duration in seconds
        """
        import re
        
        # Remove PT prefix
        duration_str = duration_str.replace('PT', '')
        
        # Extract hours, minutes, seconds
        hours = 0
        minutes = 0
        seconds = 0
        
        # Match patterns like 1H, 30M, 45S
        hour_match = re.search(r'(\d+)H', duration_str)
        minute_match = re.search(r'(\d+)M', duration_str)
        second_match = re.search(r'(\d+)S', duration_str)
        
        if hour_match:
            hours = int(hour_match.group(1))
        if minute_match:
            minutes = int(minute_match.group(1))
        if second_match:
            seconds = int(second_match.group(1))
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    
    def check_quota_remaining(self) -> int:
        """Check how much API quota is remaining today."""
        remaining = self.daily_quota_limit - self.quota_used
        return max(0, remaining)
    
    def reset_quota_counter(self):
        """Reset quota counter (call this daily)."""
        self.quota_used = 0
        logger.info("API quota counter reset")


# Example usage and testing
if __name__ == "__main__":
    # Test the collector
    collector = YouTubeCollector()
    
    # Test with a popular channel (MrBeast)
    test_channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"
    
    print("Testing YouTube API collector...")
    
    # Get channel info
    channel_info = collector.get_channel_info(test_channel_id)
    if channel_info:
        print(f"✅ Channel: {channel_info['channel_name']}")
        print(f"✅ Subscribers: {channel_info['subscriber_count']:,}")
        
        # Get recent videos
        videos = collector.get_recent_videos(test_channel_id, max_results=5)
        print(f"✅ Retrieved {len(videos)} recent videos")
        
        if videos:
            latest_video = videos[0]
            print(f"✅ Latest video: {latest_video['title']}")
            print(f"✅ Views: {latest_video['view_count']:,}")
    else:
        print("❌ Failed to get channel info")
    
    print(f"📊 API quota used: {collector.quota_used}")