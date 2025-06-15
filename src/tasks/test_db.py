"""
Test database setup and create tables.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.database import db_manager, init_database

def test_database_setup():
    """Test database connection and create all tables."""
    print("🧪 Testing database setup...")
    print("=" * 50)
    
    # Test connection
    if db_manager.health_check():
        print("✅ Database connection successful!")
        
        # Create tables
        print("📋 Creating database tables...")
        if init_database():
            print("✅ All tables created successfully!")
            
            # Verify tables exist
            try:
                with db_manager.engine.connect() as conn:
                    result = conn.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    tables = [row[0] for row in result.fetchall()]
                    
                    print(f"✅ Found {len(tables)} tables:")
                    for table in tables:
                        print(f"   - {table}")
                    
                    expected_tables = ['channels', 'videos', 'predictions', 'video_snapshots']
                    missing_tables = [t for t in expected_tables if t not in tables]
                    
                    if missing_tables:
                        print(f"⚠️  Missing tables: {missing_tables}")
                    else:
                        print("🎉 All expected tables present!")
                    
                    return True
                    
            except Exception as e:
                print(f"❌ Error checking tables: {e}")
                return False
        else:
            return False
    else:
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running: docker-compose up -d db")
        return False

if __name__ == "__main__":
    success = test_database_setup()
    
    print("=" * 50)
    if success:
        print("🎉 Database setup complete!")
        print("\n🚀 Next steps:")
        print("1. Test Celery: python test_celery.py") 
        print("2. Start collecting data from YouTube API")
        print("3. Build ML models")
    else:
        print("❌ Database setup failed. Check errors above.")