import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Database Configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/youtube_predictor"
    
    # Redis Configuration  
    redis_url: str = "redis://localhost:6379/0"
    
    # YouTube API Configuration
    youtube_api_key: str
    youtube_api_quota_limit: int = 10000  # Daily quota limit
    
    # MLflow Configuration
    mlflow_tracking_uri: str = "http://localhost:5000"
    
    # Data Collection Settings
    data_collection_interval_hours: int = 6
    max_videos_per_channel: int = 100
    channels_to_track: int = 10
    
    # Model Configuration
    model_retrain_threshold: float = 0.15  # Retrain if error increases by 15%
    prediction_cache_ttl_seconds: int = 3600  # Cache predictions for 1 hour
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Monitoring Configuration
    enable_prometheus_metrics: bool = True
    metrics_port: int = 8001
    
    @validator('youtube_api_key')
    def validate_youtube_api_key(cls, v):
        """Ensure YouTube API key is provided."""
        if not v or v == "your_youtube_api_key_here":
            raise ValueError("YouTube API key must be provided")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator('model_retrain_threshold')
    def validate_retrain_threshold(cls, v):
        """Ensure retrain threshold is reasonable."""
        if not 0.05 <= v <= 0.5:
            raise ValueError("Retrain threshold must be between 0.05 and 0.5")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"  # Automatically load from .env file
        case_sensitive = False  # Allow case-insensitive env vars
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL with proper formatting."""
    return settings.database_url


def get_redis_url() -> str:
    """Get Redis URL with proper formatting."""
    return settings.redis_url


def is_development() -> bool:
    """Check if running in development mode."""
    return os.getenv("ENVIRONMENT", "development") == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return os.getenv("ENVIRONMENT") == "production"


# Example usage and testing
if __name__ == "__main__":
    print("Configuration loaded successfully!")
    print(f"API will run on: {settings.api_host}:{settings.api_port}")
    print(f"Database URL: {settings.database_url}")
    print(f"Log Level: {settings.log_level}")
    print(f"Development Mode: {is_development()}")