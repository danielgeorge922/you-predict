"""
Test script for Celery setup.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_celery_import():
    """Test that we can import Celery components."""
    try:
        from src.tasks.celery_app import celery_app
        print("✅ Celery app imported successfully")
        
        from src.tasks.data_collection import test_data_collection
        print("✅ Data collection tasks imported successfully")
        
        # Test task registration
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✅ {len(registered_tasks)} tasks registered")
        
        for task in registered_tasks[:5]:  # Show first 5 tasks
            print(f"   - {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery import failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection."""
    try:
        import redis
        from src.config.settings import settings
        
        r = redis.from_url(settings.redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis is running: docker-compose up -d redis")
        return False

if __name__ == "__main__":
    print("🧪 Testing Celery + Redis setup...")
    print("=" * 50)
    
    redis_ok = test_redis_connection()
    celery_ok = test_celery_import()
    
    print("=" * 50)
    if redis_ok and celery_ok:
        print("🎉 Celery setup looks good!")
        print("\n🚀 Next steps:")
        print("1. Start Redis: docker-compose up -d redis")
        print("2. Start Celery worker: celery -A src.tasks.celery_app worker --loglevel=info")
        print("3. Start Celery beat: celery -A src.tasks.celery_app beat --loglevel=info")
    else:
        print("❌ Setup incomplete. Fix the issues above.")