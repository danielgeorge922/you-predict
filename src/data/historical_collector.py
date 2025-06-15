"""
Historical data collection for model training.

This script collects 3-6 months of historical video data from registered channels.
Run this ONCE to build your training dataset.
"""

from datetime import datetime, timedelta
from typing import List, Dict
import time
import structlog
from sqlalchemy.orm import Session

from src.utils.database import get_db, Channel, Video
from src.data.collectors import YouTubeCollector
from src.data.channel_manager import TARGET_CHANNELS

logger = structlog.get_logger()


class HistoricalDataCollector:
    """Collects historical video data for model training."""
    
    def __init__(self):
        self.collector = YouTubeCollector()
        self.videos_collected = 0
        self.api_calls_used = 0
    
    def collect_all_historical_data(self, months_back: int = 6) -> Dict:
        """
        Collect historical data for all registered channels.
        
        Args:
            months_back: How many months of historical data to collect
            
        Returns:
            Dictionary with collection results
        """
        logger.info("Starting historical data collection", months_back=months_back)
        
        results = {
            'channels_processed': 0,
            'total_videos_collected': 0,
            'api_calls_used': 0,
            'channels_results': {}
        }
        
        db = next(get_db())
        registered_channels = db.query(Channel).all()
        db.close()
        
        for channel in registered_channels:
            try:
                logger.info("Collecting historical data", channel_name=channel.channel_name)
                
                channel_result = self.collect_channel_historical_data(
                    channel.channel_id, 
                    months_back
                )
                
                results['channels_results'][channel.channel_id] = channel_result
                results['total_videos_collected'] += channel_result['videos_collected']
                results['api_calls_used'] += channel_result['api_calls']
                results['channels_processed'] += 1
                
                # Rate limiting - pause between channels
                time.sleep(2)
                
            except Exception as e:
                logger.error(
                    "Historical data collection failed for channel",
                    channel_id=channel.channel_id,
                    error=str(e)
                )
                results['channels_results'][channel.channel_id] = {
                    'videos_collected': 0,
                    'api_calls': 0,
                    'error': str(e)
                }
        
        logger.info(
            "Historical data collection completed",
            channels_processed=results['channels_processed'],
            total_videos=results['total_videos_collected'],
            api_calls=results['api_calls_used']
        )
        
        return results
    
    def collect_channel_historical_data(self, channel_id: str, months_back: int) -> Dict:
        """
        Collect historical data for a single channel.
        
        Strategy:
        1. Get recent videos (last 50-100)
        2. Filter to last N months
        3. Store with feature engineering
        4. Calculate 24hr view counts (simulate time-series target)
        """
        try:
            # Get maximum videos allowed by API
            all_videos = self.collector.get_recent_videos(channel_id, max_results=50)
            api_calls = 2  # Channel info + video list
            
            if not all_videos:
                return {'videos_collected': 0, 'api_calls': api_calls, 'error': 'No videos found'}
            
            # Filter by date range
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            historical_videos = []
            
            for video in all_videos:
                published_at = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
                if published_at >= cutoff_date:
                    historical_videos.append(video)
            
            logger.info(
                "Filtered historical videos",
                channel_id=channel_id,
                total_videos=len(all_videos),
                historical_videos=len(historical_videos)
            )
            
            # Store videos in database
            videos_stored = 0
            db = next(get_db())
            
            for video_data in historical_videos:
                try:
                    # Check if video already exists
                    existing = db.query(Video).filter(Video.video_id == video_data['video_id']).first()
                    if existing:
                        continue
                    
                    # Create video record with feature engineering
                    video = self._create_video_record(video_data, channel_id)
                    db.add(video)
                    videos_stored += 1
                    
                except Exception as e:
                    logger.warning("Failed to store video", video_id=video_data['video_id'], error=str(e))
                    continue
            
            db.commit()
            db.close()
            
            return {
                'videos_collected': videos_stored,
                'api_calls': api_calls,
                'date_range_days': months_back * 30
            }
            
        except Exception as e:
            logger.error("Channel historical collection failed", channel_id=channel_id, error=str(e))
            return {'videos_collected': 0, 'api_calls': 0, 'error': str(e)}
    
    def _create_video_record(self, video_data: Dict, channel_id: str) -> Video:
        """Create a Video database record with feature engineering."""
        
        # Parse publish time
        published_at = datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00'))
        
        # Extract timing features
        upload_hour = published_at.hour
        upload_day_of_week = published_at.weekday()  # 0=Monday
        
        # Calculate basic features
        title_length = len(video_data['title'])
        description_length = len(video_data.get('description', ''))
        
        # Simulate feature engineering (simplified for historical data)
        urgency_score = self._calculate_urgency_score(video_data['title'])
        
        # For historical data, use current view count as "24hr target"
        # This is a simplification - in reality we'd need actual 24hr data
        actual_views_24h = video_data['view_count']
        
        video = Video(
            video_id=video_data['video_id'],
            channel_id=channel_id,
            
            # Basic metadata
            title=video_data['title'],
            description=video_data.get('description', ''),
            duration_seconds=video_data['duration_seconds'],
            category_id=video_data.get('category_id'),
            published_at=published_at,
            
            # Timing features
            upload_hour=upload_hour,
            upload_day_of_week=upload_day_of_week,
            days_since_last_upload=0,  # TODO: Calculate this
            
            # Text analysis features
            title_length=title_length,
            urgency_score=urgency_score,
            urgency_ratio=urgency_score / 0.3 if urgency_score > 0 else 1.0,
            urgency_ratio_normalized=min(urgency_score / 0.3, 1.0),
            content_novelty_score=0.5,  # TODO: Implement semantic analysis
            
            # Ratio features (simplified)
            duration_ratio=video_data['duration_seconds'] / 300.0,  # vs 5min baseline
            duration_ratio_normalized=min(video_data['duration_seconds'] / 600.0, 1.0),
            upload_timing_deviation=0.0,  # TODO: Calculate vs channel optimal time
            
            # Target variable (KEY FOR TRAINING)
            actual_views_24h=actual_views_24h,
            
            # Data quality
            data_quality_passed=True,
            api_collection_complete=True
        )
        
        return video
    
    def _calculate_urgency_score(self, title: str) -> float:
        """Simple urgency score calculation."""
        urgency_words = ['breaking', 'urgent', 'finally', 'revealed', 'exposed', 'shocking', 'unbelievable']
        title_lower = title.lower()
        
        score = 0.0
        for word in urgency_words:
            if word in title_lower:
                score += 0.1
        
        # Check for caps
        caps_ratio = sum(1 for c in title if c.isupper()) / len(title) if title else 0
        score += caps_ratio * 0.3
        
        # Check for numbers
        if any(c.isdigit() for c in title):
            score += 0.1
        
        return min(score, 1.0)


def run_historical_collection(months_back: int = 6):
    """
    Main function to run historical data collection.
    
    This gives you the training dataset you need for your XGBoost model.
    """
    print("🚀 YouTube Historical Data Collection")
    print("=" * 50)
    print(f"📅 Collecting {months_back} months of historical data")
    print("⏱️  This will take 10-15 minutes...")
    print()
    
    collector = HistoricalDataCollector()
    results = collector.collect_all_historical_data(months_back)
    
    print("📊 COLLECTION RESULTS:")
    print(f"✅ Channels processed: {results['channels_processed']}")
    print(f"✅ Total videos collected: {results['total_videos_collected']}")
    print(f"✅ API calls used: {results['api_calls_used']}")
    print()
    
    print("📋 Per-channel results:")
    for channel_id, result in results['channels_results'].items():
        channel_name = TARGET_CHANNELS.get(channel_id, channel_id)
        if 'error' in result:
            print(f"   ❌ {channel_name}: {result['error']}")
        else:
            print(f"   ✅ {channel_name}: {result['videos_collected']} videos")
    
    print()
    if results['total_videos_collected'] > 100:
        print("🎉 SUCCESS! You now have a training dataset ready.")
        print("🚀 Next step: Train your XGBoost model")
    else:
        print("⚠️  Low video count. Consider:")
        print("   - Checking YouTube API key")
        print("   - Increasing months_back parameter")
        print("   - Verifying channel registration")
    
    return results


if __name__ == "__main__":
    # Run historical data collection
    run_historical_collection(months_back=6)