"""
Direct database connection test to debug URL issues.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_database_urls():
    """Test different database URL configurations."""
    
    database_urls = [
        "postgresql://postgres:postgres@localhost:5432/youtube_predictor",
        "postgresql://postgres:postgres@127.0.0.1:5432/youtube_predictor",
        "postgresql://postgres:postgres@host.docker.internal:5432/youtube_predictor",
    ]
    
    for url in database_urls:
        try:
            print(f"Testing: {url}")
            
            # Test with psycopg2 directly
            import psycopg2
            conn = psycopg2.connect(url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            print(f"✅ SUCCESS: {url}")
            print(f"✅ Query result: {result}")
            return url
            
        except Exception as e:
            print(f"❌ FAILED: {url} - {e}")
    
    return None

def test_settings_import():
    """Test importing settings and check current URL."""
    try:
        from src.config.settings import settings
        print(f"Current database URL from settings: {settings.database_url}")
        return settings.database_url
    except Exception as e:
        print(f"Failed to import settings: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing database connections...")
    print("=" * 60)
    
    # Check current settings
    current_url = test_settings_import()
    
    print("\n🔍 Testing different URLs...")
    working_url = test_database_urls()
    
    print("=" * 60)
    if working_url:
        print(f"🎉 Database is working with: {working_url}")
        if current_url != working_url:
            print(f"⚠️  Your settings.py has: {current_url}")
            print(f"💡 Update settings.py to use: {working_url}")
    else:
        print("❌ No database connection worked")
        print("\n🔍 Troubleshooting:")
        print("1. Check if PostgreSQL container is running: docker ps")
        print("2. Check container logs: docker-compose logs db")
        print("3. Try restarting: docker-compose restart db")