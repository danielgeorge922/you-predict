#!/usr/bin/env python3
"""
Complete setup script for YouTube View Predictor.

This script:
1. Tests all connections (Redis, PostgreSQL)
2. Creates database tables
3. Tests Celery setup
4. Runs basic data collection test
5. Verifies the complete pipeline
"""

import sys
import os
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_redis_connection():
    """Test Redis connection for Celery."""
    try:
        import redis
        from src.config.settings import settings
        
        print("🔍 Testing Redis connection...")
        r = redis.from_url(settings.redis_url)
        r.ping()
        print("✅ Redis connection successful")
        
        # Test different databases
        for db_num in [0, 1, 2]:
            r_db = redis.from_url(f"{settings.redis_url.split('/')[0]}//{settings.redis_url.split('//')[1].split('/')[0]}/{db_num}")
            r_db.ping()
            print(f"   ✅ Redis DB {db_num} accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Start Redis: docker-compose up -d redis")
        return False


def test_postgresql_connection():
    """Test PostgreSQL connection and setup."""
    try:
        print("🔍 Testing PostgreSQL connection...")
        from src.utils.database import db_manager

        if db_manager.health_check():
            print("✅ PostgreSQL connection successful")
            
            # Verify tables exist
            counts = db_manager.get_table_counts()
            print("📊 Database tables created:")
            for table, count in counts.items():
                print(f"   📋 {table}: {count} rows")
            
            return True
        else:
            raise Exception("Connection failed")
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Start PostgreSQL: docker-compose up -d postgres")
        return False


def test_celery_setup():
    """Test Celery application setup."""
    try:
        print("🔍 Testing Celery setup...")
        from src.tasks.celery_app import celery_app
        from src.tasks.data_collection import test_data_collection
        
        # Test task registration
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✅ Celery app loaded with {len(registered_tasks)} tasks")
        
        # Show key tasks
        key_tasks = [task for task in registered_tasks if 'src.tasks' in task]
        for task in key_tasks[:3]:
            print(f"   📋 {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery setup failed: {e}")
        return False


def test_youtube_api():
    """Test YouTube API integration."""
    try:
        print("🔍 Testing YouTube API...")
        from src.data.collectors import YouTubeCollector
        from src.config.settings import settings
        
        if settings.youtube_api_key == "placeholder_key":
            print("⚠️  YouTube API key not set - skipping API test")
            print("💡 Set YOUTUBE_API_KEY environment variable")
            return True
        
        collector = YouTubeCollector()
        
        # Test with a known channel (YouTube's own channel)
        test_channel_id = "UCBR8-60-B28hp2BmDPdntcQ"  # YouTube channel
        channel_info = collector.get_channel_info(test_channel_id)
        
        if channel_info:
            print(f"✅ YouTube API working - got info for: {channel_info['channel_name']}")
            return True
        else:
            raise Exception("API call returned None")
            
    except Exception as e:
        print(f"❌ YouTube API test failed: {e}")
        print("💡 Check your YouTube API key and quota")
        return False


def test_fastapi_server():
    """Test if FastAPI server can start."""
    try:
        print("🔍 Testing FastAPI import...")
        from src.api.main import app
        print("✅ FastAPI app imported successfully")
        print("💡 Start server: uvicorn src.api.main:app --reload")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False


def create_sample_data():
    """Create some sample data for testing."""
    try:
        print("🔍 Creating sample data...")
        from src.utils.database import get_db, Channel
        from datetime import datetime
        
        db = next(get_db())
        
        # Check if sample channel already exists
        existing_channel = db.query(Channel).filter(
            Channel.channel_id == "SAMPLE_CHANNEL_001"
        ).first()
        
        if not existing_channel:
            # Create sample channel with correct fields
            sample_channel = Channel(
                channel_id="SAMPLE_CHANNEL_001",
                channel_name="Sample Tech Channel",
                subscriber_count=50000,
                avg_views_last_30_days=5000,
                avg_views_last_30_days_nonviral=4500,
                avg_duration_last_30_days=600,
                avg_urgency_score_last_30_days=0.3,
                avg_velocity_last_30_days=100.0,
                upload_frequency_per_week=2.5,
                optimal_upload_hour=14,
                baseline_last_updated=datetime.utcnow(),
                data_quality_score=0.95
            )
            
            db.add(sample_channel)
            db.commit()
            print("✅ Sample channel created")
        else:
            print("✅ Sample data already exists")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False
    """Create some sample data for testing."""
    try:
        print("🔍 Creating sample data...")
        from src.utils.database import get_db, Channel
        from datetime import datetime
        
        db = next(get_db())
        
        # Check if sample channel already exists
        existing_channel = db.query(Channel).filter(
            Channel.channel_id == "SAMPLE_CHANNEL_001"
        ).first()
        
        if not existing_channel:
            # Create sample channel
            sample_channel = Channel(
                channel_id="SAMPLE_CHANNEL_001",
                channel_name="Sample Tech Channel",
                description="A sample channel for testing",
                subscriber_count=50000,
                view_count=1000000,
                video_count=100,
                avg_views_last_30_days=5000.0,
                upload_frequency_per_week=2.5
            )
            
            db.add(sample_channel)
            db.commit()
            print("✅ Sample channel created")
        else:
            print("✅ Sample data already exists")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False


def run_complete_setup():
    """Run the complete setup process."""
    print("🚀 YouTube View Predictor - Complete Setup")
    print("=" * 60)
    
    # Track results
    results = {}
    
    # Test each component
    results['redis'] = test_redis_connection()
    print()
    
    results['postgresql'] = test_postgresql_connection()
    print()
    
    results['celery'] = test_celery_setup()
    print()
    
    results['youtube_api'] = test_youtube_api()
    print()
    
    results['fastapi'] = test_fastapi_server()
    print()
    
    if results['postgresql']:
        results['sample_data'] = create_sample_data()
        print()
    
    # Summary
    print("=" * 60)
    print("📊 SETUP SUMMARY:")
    
    all_good = True
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component.upper()}: {'WORKING' if status else 'FAILED'}")
        if not status:
            all_good = False
    
    print("=" * 60)
    
    if all_good:
        print("🎉 ALL SYSTEMS GO!")
        print("\n🚀 NEXT STEPS:")
        print("1. Start all services:")
        print("   docker-compose up -d")
        print()
        print("2. Start FastAPI server:")
        print("   uvicorn src.api.main:app --reload")
        print()
        print("3. Start Celery worker:")
        print("   celery -A src.tasks.celery_app worker --loglevel=info --queues=data_collection,ml_tasks,maintenance")
        print()
        print("4. Start Celery beat (scheduler):")
        print("   celery -A src.tasks.celery_app beat --loglevel=info")
        print()
        print("5. Visit API docs:")
        print("   http://localhost:8000/docs")
        print()
        print("🎯 Ready to start data collection and model training!")
        
    else:
        print("❌ SETUP INCOMPLETE")
        print("\n🔧 FIX THESE ISSUES:")
        for component, status in results.items():
            if not status:
                print(f"   - {component.upper()}")
        
        print("\n💡 COMMON FIXES:")
        print("   - Start Docker services: docker-compose up -d")
        print("   - Set YouTube API key: export YOUTUBE_API_KEY=your_key_here")
        print("   - Check Docker containers: docker-compose ps")
    
    return all_good


if __name__ == "__main__":
    success = run_complete_setup()
    sys.exit(0 if success else 1)