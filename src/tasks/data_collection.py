"""
Celery tasks for YouTube data collection.

These tasks handle:
- Discovering new videos from tracked channels
- Updating video statistics over time
- Refreshing channel metadata
"""

from datetime import datetime, timedelta
from typing import List
import structlog
from sqlalchemy.orm import Session

from src.tasks.celery_app import celery_app
from src.data.collectors import YouTubeCollector
from src.utils.database import get_db, Channel, Video
from src.config.settings import settings

logger = structlog.get_logger()

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def check_new_videos(self):
    """
    Check for new videos from all tracked channels.
    
    This task:
    1. Gets list of active channels
    2. Fetches recent videos from each channel
    3. Stores new videos in database
    4. Triggers prediction tasks for new videos
    """
    try:
        logger.info("Starting new video check")
        
        collector = YouTubeCollector()
        db = next(get_db())
        
        # Get all active channels
        active_channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        total_new_videos = 0
        
        for channel in active_channels:
            try:
                logger.info("Checking channel for new videos", channel_name=channel.channel_name)
                
                # Get recent videos (last 10)
                recent_videos = collector.get_recent_videos(channel.channel_id, max_results=10)
                
                for video_data in recent_videos:
                    # Check if video already exists
                    existing_video = db.query(Video).filter(
                        Video.video_id == video_data['video_id']
                    ).first()
                    
                    if not existing_video:
                        # Create new video record
                        video = Video(
                            video_id=video_data['video_id'],
                            channel_id=video_data['channel_id'],
                            title=video_data['title'],
                            description=video_data['description'],
                            duration_seconds=video_data['duration_seconds'],
                            published_at=datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00')),
                            view_count=video_data['view_count'],
                            like_count=video_data['like_count'],
                            comment_count=video_data['comment_count'],
                            category_id=video_data.get('category_id'),
                            default_language=video_data.get('default_language'),
                            tags=str(video_data.get('tags', [])),  # Store as string for now
                            thumbnail_url=video_data['thumbnail_url']
                        )
                        
                        db.add(video)
                        total_new_videos += 1
                        
                        logger.info(
                            "New video discovered",
                            video_id=video_data['video_id'],
                            title=video_data['title'][:50]
                        )
                        
                        # Queue prediction task for new video
                        make_prediction_for_video.delay(video_data['video_id'])
                
            except Exception as e:
                logger.error(
                    "Failed to check channel",
                    channel_id=channel.channel_id,
                    error=str(e)
                )
                continue
        
        # Commit all new videos
        db.commit()
        
        logger.info(
            "New video check completed",
            total_new_videos=total_new_videos,
            channels_checked=len(active_channels),
            quota_used=collector.quota_used
        )
        
        return {
            'new_videos_found': total_new_videos,
            'channels_checked': len(active_channels),
            'quota_used': collector.quota_used
        }
        
    except Exception as e:
        logger.error("New video check failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 30})
def update_recent_video_stats(self):
    """
    Update view counts for videos published in the last 48 hours.
    
    This tracks view progression over time for recent videos.
    """
    try:
        logger.info("Starting video stats update")
        
        collector = YouTubeCollector()
        db = next(get_db())
        
        # Get videos published in last 48 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=48)
        recent_videos = db.query(Video).filter(
            Video.published_at >= cutoff_time
        ).all()
        
        updated_count = 0
        
        for video in recent_videos:
            try:
                # Get updated video details
                video_details = collector.get_video_details(video.video_id)
                
                if video_details:
                    # Update video statistics
                    video.view_count = video_details['view_count']
                    video.like_count = video_details['like_count']
                    video.comment_count = video_details['comment_count']
                    video.updated_at = datetime.utcnow()
                    
                    updated_count += 1
                    
                    # Check if this video needs prediction evaluation
                    time_since_publish = datetime.utcnow() - video.published_at
                    if time_since_publish >= timedelta(hours=24):
                        # Queue prediction evaluation
                        evaluate_prediction_accuracy.delay(video.video_id)
                
            except Exception as e:
                logger.error(
                    "Failed to update video stats",
                    video_id=video.video_id,
                    error=str(e)
                )
                continue
        
        # Commit updates
        db.commit()
        
        logger.info(
            "Video stats update completed",
            videos_updated=updated_count,
            total_recent_videos=len(recent_videos),
            quota_used=collector.quota_used
        )
        
        return {
            'videos_updated': updated_count,
            'total_recent_videos': len(recent_videos),
            'quota_used': collector.quota_used
        }
        
    except Exception as e:
        logger.error("Video stats update failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 300})
def update_channel_stats(self):
    """
    Update channel statistics (subscriber count, etc.).
    
    Runs daily to keep channel metadata current.
    """
    try:
        logger.info("Starting channel stats update")
        
        collector = YouTubeCollector()
        db = next(get_db())
        
        # Get all active channels
        active_channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        updated_count = 0
        
        for channel in active_channels:
            try:
                # Get updated channel info
                channel_info = collector.get_channel_info(channel.channel_id)
                
                if channel_info:
                    # Update channel statistics
                    channel.subscriber_count = channel_info['subscriber_count']
                    channel.view_count = channel_info['view_count']
                    channel.video_count = channel_info['video_count']
                    channel.updated_at = datetime.utcnow()
                    
                    updated_count += 1
                    
                    logger.info(
                        "Channel stats updated",
                        channel_name=channel.channel_name,
                        subscribers=channel_info['subscriber_count']
                    )
                
            except Exception as e:
                logger.error(
                    "Failed to update channel stats",
                    channel_id=channel.channel_id,
                    error=str(e)
                )
                continue
        
        # Commit updates
        db.commit()
        
        logger.info(
            "Channel stats update completed",
            channels_updated=updated_count,
            quota_used=collector.quota_used
        )
        
        return {
            'channels_updated': updated_count,
            'quota_used': collector.quota_used
        }
        
    except Exception as e:
        logger.error("Channel stats update failed", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def make_prediction_for_video(self, video_id: str):
    """
    Generate prediction for a newly discovered video.
    
    This will be expanded when we build the ML models.
    """
    try:
        logger.info("Making prediction for new video", video_id=video_id)
        
        # TODO: Implement actual prediction logic
        # For now, just log that we would make a prediction
        
        logger.info("Prediction queued", video_id=video_id)
        
        return {'video_id': video_id, 'status': 'prediction_queued'}
        
    except Exception as e:
        logger.error("Prediction failed", video_id=video_id, error=str(e))
        raise


@celery_app.task(bind=True)
def evaluate_prediction_accuracy(self, video_id: str):
    """
    Evaluate prediction accuracy after 24 hours.
    
    This will be expanded when we build the ML models.
    """
    try:
        logger.info("Evaluating prediction accuracy", video_id=video_id)
        
        # TODO: Implement actual evaluation logic
        # Compare predicted vs actual 24hr view count
        
        logger.info("Prediction evaluation queued", video_id=video_id)
        
        return {'video_id': video_id, 'status': 'evaluation_queued'}
        
    except Exception as e:
        logger.error("Prediction evaluation failed", video_id=video_id, error=str(e))
        raise


# Test task
@celery_app.task
def test_data_collection():
    """Test task to verify data collection tasks work."""
    logger.info("Data collection test task executed successfully!")
    return "Data collection tasks are working!"