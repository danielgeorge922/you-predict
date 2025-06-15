"""
Database models and connection management.

This module defines the database schema using SQLAlchemy ORM,
optimized for YouTube video prediction and time-series data collection.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, 
    Text, BigInteger, ForeignKey, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.config.settings import get_database_url

# Base class for all database models
Base = declarative_base()


class Channel(Base):
    """
    YouTube channel information and statistics.
    """
    __tablename__ = "channels"
    
    channel_id = Column(String(50), primary_key=True)  # YouTube channel ID
    channel_name = Column(String(255), nullable=False)
    subscriber_count = Column(BigInteger, default=0)
    avg_views_last_30_days = Column(BigInteger, default=0)  # Calculated field
    upload_frequency_per_week = Column(Float, default=0.0)  # Calculated field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to videos
    videos = relationship("Video", back_populates="channel")
    
    def __repr__(self):
        return f"<Channel(id={self.channel_id}, name={self.channel_name})>"


class Video(Base):
    """
    Individual YouTube video data and metadata.
    """
    __tablename__ = "videos"
    
    video_id = Column(String(50), primary_key=True)  # YouTube video ID
    channel_id = Column(String(50), ForeignKey("channels.channel_id"), nullable=False)
    
    # Video metadata
    title = Column(Text, nullable=False)
    description = Column(Text)
    duration_seconds = Column(Integer)
    published_at = Column(DateTime, nullable=False)
    
    # Video statistics
    view_count = Column(BigInteger, default=0)
    like_count = Column(Integer, default=0)
    
    # Extracted features
    upload_hour = Column(Integer)  # 0-23
    upload_day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    category_id = Column(String(10))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channel = relationship("Channel", back_populates="videos")
    predictions = relationship("Prediction", back_populates="video")
    snapshots = relationship("VideoSnapshot", back_populates="video")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_video_published_at', 'published_at'),
        Index('idx_video_channel_published', 'channel_id', 'published_at'),
    )
    
    def __repr__(self):
        return f"<Video(id={self.video_id}, title={self.title[:30]}...)>"


class Prediction(Base):
    """
    Model predictions and results for videos.
    """
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(50), ForeignKey("videos.video_id"), nullable=False)
    
    # Prediction values
    predicted_views_24h = Column(BigInteger, nullable=False)
    actual_views_24h = Column(BigInteger)  # Filled after 24 hours
    baseline_prediction = Column(BigInteger)  # XGBoost output
    virality_score = Column(Float)  # 0-1 from virality classifier
    model_version = Column(String(50), nullable=False)
    
    # Timestamps
    predicted_at = Column(DateTime, default=datetime.utcnow)
    evaluated_at = Column(DateTime)  # When actual views were recorded
    
    # Relationship
    video = relationship("Video", back_populates="predictions")
    
    # Indexes
    __table_args__ = (
        Index('idx_prediction_video', 'video_id'),
        Index('idx_prediction_model', 'model_version', 'predicted_at'),
    )
    
    @property
    def accuracy_error(self) -> Optional[float]:
        """Calculate prediction accuracy error."""
        if self.actual_views_24h is not None and self.actual_views_24h > 0:
            return abs(self.predicted_views_24h - self.actual_views_24h) / self.actual_views_24h
        return None
    
    def __repr__(self):
        return f"<Prediction(video_id={self.video_id}, predicted={self.predicted_views_24h})>"


class VideoSnapshot(Base):
    """
    Time-series data for video view progression (Phase 2).
    """
    __tablename__ = "video_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(50), ForeignKey("videos.video_id"), nullable=False)
    
    # Time-series data
    hours_after_publish = Column(Integer, nullable=False)  # 1, 2, 4, 6, 12, 24, etc.
    view_count = Column(BigInteger, nullable=False)
    like_count = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    video = relationship("Video", back_populates="snapshots")
    
    # Indexes
    __table_args__ = (
        Index('idx_snapshot_video_hours', 'video_id', 'hours_after_publish'),
        Index('idx_snapshot_recorded', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<VideoSnapshot(video_id={self.video_id}, hours={self.hours_after_publish})>"


# Database connection and session management
class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully!")
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return False


# Global database manager
db_manager = DatabaseManager(get_database_url())


# FastAPI dependency for getting database sessions
def get_db():
    """
    FastAPI dependency to get database session.
    Ensures sessions are properly closed after each request.
    """
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


# Utility functions
def init_database():
    """Initialize database with tables."""
    print("🔧 Initializing database...")
    try:
        db_manager.create_tables()
        print("✅ Database initialization complete!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Test database setup
    print("🧪 Testing database setup...")
    if db_manager.health_check():
        print("✅ Database connection successful!")
        init_database()
    else:
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running: docker-compose up -d db")