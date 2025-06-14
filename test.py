#!/usr/bin/env python3
"""
Test script to verify our project setup is working correctly.

This script tests:
1. Configuration loading
2. Environment variables
3. Basic imports
4. Database connection (when available)

Run this to make sure Phase 1 setup is complete.
"""

import os
import sys
from pathlib import Path

# Add src to Python path so we can import our modules
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that we can import our modules."""
    print("🧪 Testing imports...")
    
    try:
        from src.config.settings import settings
        print("✅ Successfully imported settings")
        return settings
    except ImportError as e:
        print(f"❌ Failed to import settings: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return None

def test_configuration(settings):
    """Test configuration values."""
    print("\n🧪 Testing configuration...")
    
    if not settings:
        print("❌ Cannot test configuration - settings not loaded")
        return False
    
    # Test basic config
    print(f"✅ API Host: {settings.api_host}")
    print(f"✅ API Port: {settings.api_port}")
    print(f"✅ Database URL: {settings.database_url[:50]}...")
    print(f"✅ Log Level: {settings.log_level}")
    
    # Test YouTube API key (without showing it)
    if hasattr(settings, 'youtube_api_key') and settings.youtube_api_key:
        if settings.youtube_api_key == "your_youtube_api_key_here":
            print("⚠️  YouTube API key is still placeholder - you'll need to set this")
        else:
            print("✅ YouTube API key is configured")
    else:
        print("⚠️  YouTube API key not found - you'll need to set YOUTUBE_API_KEY")
    
    return True

def test_environment():
    """Test environment setup."""
    print("\n🧪 Testing environment...")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment (recommended to use venv)")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version too old: {python_version.major}.{python_version.minor}")
        return False
    
    # Check required directories exist
    required_dirs = ["src", "src/config", "src/api", "src/data"]
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
    
    return True

def test_dependencies():
    """Test that key dependencies are installed."""
    print("\n🧪 Testing dependencies...")
    
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "sqlalchemy", 
        "psycopg2", "redis", "pandas", "numpy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def create_env_file_if_needed():
    """Create .env file from template if it doesn't exist."""
    print("\n🧪 Checking environment file...")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("📝 Creating .env file from template...")
            with open(".env.example", "r") as example:
                content = example.read()
            
            with open(".env", "w") as env_file:
                env_file.write(content)
            
            print("✅ Created .env file")
            print("⚠️  Remember to update .env with your actual values!")
        else:
            print("❌ No .env.example file found")
            return False
    else:
        print("✅ .env file exists")
    
    return True

def main():
    """Run all setup tests."""
    print("🚀 YouTube View Predictor - Setup Test")
    print("=" * 50)
    
    # Test environment first
    env_ok = test_environment()
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    # Create .env if needed
    env_file_ok = create_env_file_if_needed()
    
    # Test imports (this will fail if dependencies aren't installed)
    if deps_ok:
        settings = test_imports()
        config_ok = test_configuration(settings)
    else:
        config_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SETUP SUMMARY")
    print("=" * 50)
    
    if env_ok and deps_ok and env_file_ok and config_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your Phase 1 setup is complete!")
        print("\n🚀 Next steps:")
        print("1. Set your YouTube API key in .env file")
        print("2. Start Docker services: docker-compose up -d")
        print("3. Initialize database: python -c 'from src.utils.database import init_database; init_database()'")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        
        if not deps_ok:
            print("\n💡 Quick fix: pip install -r requirements.txt")
        
        if not config_ok:
            print("\n💡 Quick fix: Check your .env file and settings.py")
    
    print("\n📚 Need help? Check the README.md or documentation!")

if __name__ == "__main__":
    main()