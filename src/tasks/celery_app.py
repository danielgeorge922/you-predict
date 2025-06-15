"""
Celery application configuration for background tasks.

This module sets up Celery for handling:
- YouTube API data collection
- Model training and inference
- Periodic maintenance tasks
"""

from celery import Celery
from celery.schedules import crontab
import structlog

from src.config.settings import settings

logger = structlog.get_logger()

# Create Celery application
celery_app = Celery(
    'youtube_predictor',
    broker=settings.redis_url,  # Task queue
    backend=settings.redis_url,  # Result storage
    include=[
        'src.tasks.data_collection',
        'src.tasks.model_tasks',
        'src.tasks.maintenance'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'src.tasks.data_collection.*': {'queue': 'data_collection'},
        'src.tasks.model_tasks.*': {'queue': 'ml_tasks'},
        'src.tasks.maintenance.*': {'queue': 'maintenance'},
    },
    
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Check for new videos every 6 hours
        'check-new-videos': {
            'task': 'src.tasks.data_collection.check_new_videos',
            'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        },
        
        # Update video stats every hour
        'update-video-stats': {
            'task': 'src.tasks.data_collection.update_recent_video_stats',
            'schedule': crontab(minute=0),  # Every hour
        },
        
        # Update channel stats daily
        'update-channel-stats': {
            'task': 'src.tasks.data_collection.update_channel_stats',
            'schedule': crontab(minute=0, hour=2),  # 2 AM daily
        },
        
        # Check prediction accuracy daily
        'evaluate-predictions': {
            'task': 'src.tasks.model_tasks.evaluate_recent_predictions',
            'schedule': crontab(minute=30, hour=3),  # 3:30 AM daily
        },
        
        # Check for model drift weekly
        'check-model-drift': {
            'task': 'src.tasks.model_tasks.check_model_drift',
            'schedule': crontab(minute=0, hour=4, day_of_week=1),  # Monday 4 AM
        },
        
        # Clean up old data monthly
        'cleanup-old-data': {
            'task': 'src.tasks.maintenance.cleanup_old_data',
            'schedule': crontab(minute=0, hour=5, day_of_month=1),  # Changed from 'day' to 'day_of_month'
        },
    },
)

# Configure logging
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up any additional periodic tasks."""
    logger.info("Celery periodic tasks configured")

# Task failure handler
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"

# Error handling
@celery_app.task(bind=True)
def handle_task_failure(self, exc, task_id, args, kwargs, traceback):
    """Handle task failures."""
    logger.error(
        "Task failed",
        task_id=task_id,
        exception=str(exc),
        args=args,
        kwargs=kwargs
    )

if __name__ == '__main__':
    celery_app.start()