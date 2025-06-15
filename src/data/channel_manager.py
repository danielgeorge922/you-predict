"""
Channel management for YouTube data collection.

This module handles:
1. Registering channels to track
2. Initial channel baseline calculation
3. Channel health monitoring
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import structlog
from sqlalchemy.orm import Session

from src.utils.database import get_db, Channel
from src.data.collectors import YouTubeCollector

logger = structlog.get_logger()

# Target channels for data collection
TARGET_CHANNELS = {
    "UCBJycsmduvYEL83R_U4JriQ": "Marques Brownlee",  # Tech
    "UC6nSFpj9HTCZ5t-N3Rm3-HA": "Veritasium",         # Science 
    "UCX6OQ3DkcsbYNE6H8uQQuVA": "MrBeast",            # Entertainment
    "UC-lHJZR3Gqxm24_Vd_AJ5Yw": "PewDiePie",          # Gaming
    "UCJ5v_MCY6GNUBTO8-D3XoAg": "Good Mythical Morning", # Lifestyle
    "UC0v-tlzsn0QZwJnkiaUSJVQ": "Dude Perfect",       # Sports/Entertainment
    "UCsXVk37bltHxD1rDPwtNM8Q": "Kurzgesagt",         # Educational
    "UC7_gcs09iThXybpVgjHZ_7g": "PBS Space Time",     # Science
    "UCBR8-60-B28hp2BmDPdntcQ": "YouTube",            # Platform (control)
    "UCuAXFkgsw1L7xaCfnd5JJOw": "Real Engineering",   # Engineering
}


class ChannelManager:
    """Manages YouTube channel registration and baseline calculations."""
    
    def __init__(self):
        self.collector = YouTubeCollector()
    
    def register_all_target_channels(self) -> Dict[str, bool]:
        """Register all target channels for tracking."""
        results = {}
        
        logger.info("Starting bulk channel registration", total_channels=len(TARGET_CHANNELS))
        
        for channel_id, expected_name in TARGET_CHANNELS.items():
            try:
                success = self.register_channel(channel_id, expected_name)
                results[channel_id] = success
                
                if success:
                    logger.info("Channel registered", channel_id=channel_id, name=expected_name)
                else:
                    logger.error("Channel registration failed", channel_id=channel_id)
                    
            except Exception as e:
                logger.error("Channel registration error", channel_id=channel_id, error=str(e))
                results[channel_id] = False
        
        successful = sum(1 for success in results.values() if success)
        logger.info("Bulk registration completed", successful=successful, total=len(TARGET_CHANNELS))
        
        return results
    
    def register_channel(self, channel_id: str, expected_name: Optional[str] = None) -> bool:
        """
        Register a single channel for tracking.
        
        Args:
            channel_id: YouTube channel ID
            expected_name: Expected channel name for validation
            
        Returns:
            bool: True if registration successful
        """
        try:
            db = next(get_db())
            
            # Check if already registered
            existing_channel = db.query(Channel).filter(
                Channel.channel_id == channel_id
            ).first()
            
            if existing_channel:
                logger.info("Channel already registered", channel_id=channel_id)
                db.close()
                return True
            
            # Get channel info from YouTube API
            channel_info = self.collector.get_channel_info(channel_id)
            
            if not channel_info:
                logger.error("Failed to get channel info from API", channel_id=channel_id)
                db.close()
                return False
            
            # Validate expected name if provided
            if expected_name and channel_info['channel_name'] != expected_name:
                logger.warning(
                    "Channel name mismatch",
                    channel_id=channel_id,
                    expected=expected_name,
                    actual=channel_info['channel_name']
                )
            
            # Create channel record with initial baselines
            channel = Channel(
                channel_id=channel_id,
                channel_name=channel_info['channel_name'],
                subscriber_count=channel_info['subscriber_count'],
                
                # Initialize with placeholder values - will be calculated later
                avg_views_last_30_days=0,
                avg_views_last_30_days_nonviral=0,
                avg_duration_last_30_days=300,  # Default 5 minutes
                avg_urgency_score_last_30_days=0.3,
                avg_velocity_last_30_days=50.0,
                upload_frequency_per_week=2.0,
                optimal_upload_hour=14,  # Default 2 PM
                
                # Data quality tracking
                baseline_last_updated=datetime.utcnow(),
                data_quality_score=0.0,  # Will be calculated
                api_errors_last_24h=0,
                
                # Store latest video for efficient new upload detection
                last_video_id=None
            )
            
            db.add(channel)
            db.commit()
            
            logger.info(
                "Channel registered successfully",
                channel_id=channel_id,
                name=channel_info['channel_name'],
                subscribers=channel_info['subscriber_count']
            )
            
            db.close()
            return True
            
        except Exception as e:
            logger.error("Channel registration failed", channel_id=channel_id, error=str(e))
            if 'db' in locals():
                db.close()
            return False
    
    def calculate_channel_baselines(self, channel_id: str) -> bool:
        """
        Calculate baseline metrics for a channel using historical data.
        
        This is crucial for accurate predictions - we need to know each channel's
        typical performance patterns.
        """
        try:
            logger.info("Calculating channel baselines", channel_id=channel_id)
            
            # Get recent videos (last 30 days worth)
            recent_videos = self.collector.get_recent_videos(channel_id, max_results=50)
            
            if not recent_videos:
                logger.warning("No recent videos found for baseline calculation", channel_id=channel_id)
                return False
            
            # Calculate baseline metrics
            baselines = self._calculate_baseline_metrics(recent_videos)
            
            # Update channel record
            db = next(get_db())
            channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            
            if channel:
                # Update baseline values
                channel.avg_views_last_30_days = baselines['avg_views']
                channel.avg_views_last_30_days_nonviral = baselines['avg_views_nonviral']
                channel.avg_duration_last_30_days = baselines['avg_duration']
                channel.avg_urgency_score_last_30_days = baselines['avg_urgency_score']
                channel.avg_velocity_last_30_days = baselines['avg_velocity']
                channel.upload_frequency_per_week = baselines['upload_frequency']
                channel.optimal_upload_hour = baselines['optimal_upload_hour']
                
                # Update metadata
                channel.baseline_last_updated = datetime.utcnow()
                channel.data_quality_score = baselines['data_quality_score']
                
                # Store most recent video ID for new upload detection
                if recent_videos:
                    channel.last_video_id = recent_videos[0]['video_id']
                
                db.commit()
                
                logger.info(
                    "Channel baselines updated",
                    channel_id=channel_id,
                    avg_views=baselines['avg_views'],
                    video_count=len(recent_videos)
                )
            
            db.close()
            return True
            
        except Exception as e:
            logger.error("Baseline calculation failed", channel_id=channel_id, error=str(e))
            if 'db' in locals():
                db.close()
            return False
    
    def _calculate_baseline_metrics(self, videos: List[Dict]) -> Dict:
        """Calculate baseline metrics from video data."""
        if not videos:
            return self._default_baselines()
        
        # Filter out videos older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_videos = []
        
        for video in videos:
            published_at = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
            if published_at >= cutoff_date:
                recent_videos.append(video)
        
        if not recent_videos:
            return self._default_baselines()
        
        # Calculate basic averages
        view_counts = [video['view_count'] for video in recent_videos]
        durations = [video['duration_seconds'] for video in recent_videos if video['duration_seconds'] > 0]
        
        # Remove viral outliers (top 10%) for baseline calculation
        sorted_views = sorted(view_counts)
        viral_threshold = sorted_views[int(len(sorted_views) * 0.9)] if len(sorted_views) > 10 else max(sorted_views)
        nonviral_views = [v for v in view_counts if v <= viral_threshold]
        
        # Calculate metrics
        baselines = {
            'avg_views': int(sum(view_counts) / len(view_counts)),
            'avg_views_nonviral': int(sum(nonviral_views) / len(nonviral_views)) if nonviral_views else 0,
            'avg_duration': int(sum(durations) / len(durations)) if durations else 300,
            'avg_urgency_score': 0.3,  # TODO: Implement text analysis
            'avg_velocity': 50.0,  # TODO: Calculate from early engagement data
            'upload_frequency': len(recent_videos) * 7 / 30,  # Videos per week
            'optimal_upload_hour': 14,  # TODO: Analyze upload times
            'data_quality_score': 0.8  # TODO: Implement quality scoring
        }
        
        return baselines
    
    def _default_baselines(self) -> Dict:
        """Return default baseline values when no data available."""
        return {
            'avg_views': 10000,
            'avg_views_nonviral': 8000,
            'avg_duration': 300,
            'avg_urgency_score': 0.3,
            'avg_velocity': 50.0,
            'upload_frequency': 2.0,
            'optimal_upload_hour': 14,
            'data_quality_score': 0.5
        }
    
    def get_registered_channels(self) -> List[Dict]:
        """Get list of all registered channels."""
        try:
            db = next(get_db())
            channels = db.query(Channel).all()
            
            channel_list = []
            for channel in channels:
                channel_list.append({
                    'channel_id': channel.channel_id,
                    'channel_name': channel.channel_name,
                    'subscriber_count': channel.subscriber_count,
                    'baseline_last_updated': channel.baseline_last_updated,
                    'data_quality_score': channel.data_quality_score
                })
            
            db.close()
            return channel_list
            
        except Exception as e:
            logger.error("Failed to get registered channels", error=str(e))
            return []


# CLI functions for easy setup
def setup_all_channels():
    """Setup all target channels - run this once to initialize data collection."""
    manager = ChannelManager()
    
    print("🚀 Setting up YouTube data collection channels...")
    print(f"📊 Registering {len(TARGET_CHANNELS)} channels...")
    
    # Register all channels
    results = manager.register_all_target_channels()
    
    # Calculate baselines for successfully registered channels
    print("\n📈 Calculating channel baselines...")
    for channel_id, registered in results.items():
        if registered:
            print(f"   🔄 Calculating baselines for {TARGET_CHANNELS[channel_id]}...")
            success = manager.calculate_channel_baselines(channel_id)
            if success:
                print(f"   ✅ Baselines calculated for {TARGET_CHANNELS[channel_id]}")
            else:
                print(f"   ⚠️  Baseline calculation failed for {TARGET_CHANNELS[channel_id]}")
    
    # Summary
    successful = sum(1 for success in results.values() if success)
    print(f"\n🎉 Setup complete: {successful}/{len(TARGET_CHANNELS)} channels ready for data collection")
    
    return results


if __name__ == "__main__":
    # Run channel setup
    setup_all_channels()