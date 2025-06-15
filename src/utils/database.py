"""
Database models based on the complete MLOps specification.

This implements the full schema with proper constraints,
data quality validation, and feature engineering support.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, 
    Text, BigInteger, ForeignKey, Index, create_engine,
    CheckConstraint, UniqueConstraint, ARRAY, text  # Add text import
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from src.config.settings import get_database_url

# Base class for all database models
Base = declarative_base()


class Channel(Base):
    """
    YouTube channel information with enhanced baseline calculations.
    """
    __tablename__ = "channels"
    
    channel_id = Column(String(50), primary_key=True)
    channel_name = Column(String(255), nullable=False)
    subscriber_count = Column(BigInteger, CheckConstraint('subscriber_count > 0'), nullable=False)

    
    # Baseline calculations (updated weekly)
    avg_views_last_30_days = Column(BigInteger, 
                                  CheckConstraint('avg_views_last_30_days >= 0'))
    avg_views_last_30_days_nonviral = Column(BigInteger,
                                           CheckConstraint('avg_views_last_30_days_nonviral >= 0'))
    avg_duration_last_30_days = Column(Integer,
                                     CheckConstraint('avg_duration_last_30_days > 0'))
    avg_urgency_score_last_30_days = Column(Float,
                                          CheckConstraint('avg_urgency_score_last_30_days BETWEEN 0 AND 1'))
    avg_velocity_last_30_days = Column(Float,
                                     CheckConstraint('avg_velocity_last_30_days >= 0'))
    upload_frequency_per_week = Column(Float,
                                     CheckConstraint('upload_frequency_per_week > 0'))
    optimal_upload_hour = Column(Integer,
                               CheckConstraint('optimal_upload_hour BETWEEN 0 AND 23'))
    
    # Enhanced trend calculations
    growth_trend_7d = Column(Float)
    growth_trend_30d = Column(Float)
    days_since_last_viral_video = Column(Integer)
    last_video_id = Column(String(50))
    
    # Data quality metadata
    baseline_last_updated = Column(DateTime, nullable=False)
    data_quality_score = Column(Float,
                              CheckConstraint('data_quality_score BETWEEN 0 AND 1'))
    api_errors_last_24h = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = relationship("Video", back_populates="channel")
    
    def __repr__(self):
        return f"<Channel(id={self.channel_id}, name={self.channel_name})>"


class Video(Base):
    """
    Individual YouTube video data with comprehensive feature engineering.
    """
    __tablename__ = "videos"
    
    video_id = Column(String(50), primary_key=True)
    channel_id = Column(String(50), ForeignKey("channels.channel_id"), nullable=False)
    
    # Basic metadata with validation
    title = Column(Text, CheckConstraint(sqltext='LENGTH(title) > 0'), nullable=False)
    description = Column(Text)
    duration_seconds = Column(Integer, CheckConstraint('duration_seconds > 0'))
    category_id = Column(String(10))
    published_at = Column(DateTime, nullable=False)
    
    # Derived timing features
    upload_hour = Column(Integer, CheckConstraint('upload_hour BETWEEN 0 AND 23'))
    upload_day_of_week = Column(Integer, CheckConstraint('upload_day_of_week BETWEEN 0 AND 6'))
    days_since_last_upload = Column(Integer, CheckConstraint('days_since_last_upload >= 0'))
    
    # Enhanced text analysis features
    title_length = Column(Integer, CheckConstraint('title_length > 0'))
    urgency_score = Column(Float, CheckConstraint('urgency_score BETWEEN 0 AND 1'))
    urgency_ratio = Column(Float, CheckConstraint('urgency_ratio > 0'))
    urgency_ratio_normalized = Column(Float, CheckConstraint('urgency_ratio_normalized BETWEEN 0 AND 1'))
    content_novelty_score = Column(Float, CheckConstraint('content_novelty_score BETWEEN 0 AND 1'))
    
    # Enhanced ratio-based features (sigmoid normalized)
    duration_ratio = Column(Float, CheckConstraint('duration_ratio > 0'))
    duration_ratio_normalized = Column(Float, CheckConstraint('duration_ratio_normalized BETWEEN 0 AND 1'))
    upload_timing_deviation = Column(Float)
    
    # Velocity features (for virality detection)
    expected_velocity_1hr = Column(Float)
    expected_velocity_4hr = Column(Float)
    
    # Predictions and results (THE CORE PREDICTION TARGET)
    baseline_prediction = Column(BigInteger, CheckConstraint('baseline_prediction >= 0'))
    adjusted_prediction = Column(BigInteger, CheckConstraint('adjusted_prediction >= 0'))
    final_prediction = Column(BigInteger, CheckConstraint('final_prediction >= 0'))
    actual_views_24h = Column(BigInteger, CheckConstraint('actual_views_24h >= 0'))
    
    # Enhanced classification and quality
    is_viral = Column(Boolean)
    prediction_accuracy = Column(Float)
    virality_multiplier = Column(Float, CheckConstraint('virality_multiplier > 0'))
    
    # Data quality tracking
    data_quality_passed = Column(Boolean, default=False)
    data_quality_issues = Column(ARRAY(Text))
    api_collection_complete = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channel = relationship("Channel", back_populates="videos")
    predictions = relationship("Prediction", back_populates="video")
    snapshots = relationship("VideoSnapshot", back_populates="video")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_videos_channel_published', 'channel_id', 'published_at'),
        Index('idx_videos_published_viral', 'published_at', 'is_viral'),
        Index('idx_videos_actual_views', 'actual_views_24h'),
    )
    
    def __repr__(self):
        return f"<Video(id={self.video_id}, title={self.title[:30]}...)>"


class VideoSnapshot(Base):
    """
    Time-series data for video view progression with comprehensive metrics.
    """
    __tablename__ = "video_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(50), ForeignKey("videos.video_id"), nullable=False)
    hours_after_publish = Column(Integer, CheckConstraint('hours_after_publish > 0'), nullable=False)

    # Raw engagement data with validation
    view_count = Column(BigInteger, CheckConstraint('view_count >= 0'), nullable=False)
    like_count = Column(Integer, CheckConstraint('like_count >= 0'), nullable=False)
    comment_count = Column(Integer, CheckConstraint('comment_count >= 0'), nullable=False)

    # Enhanced calculated features
    views_per_hour = Column(Float, CheckConstraint('views_per_hour >= 0'))
    engagement_rate = Column(Float, CheckConstraint('engagement_rate >= 0'))
    expected_views_at_hour = Column(BigInteger, CheckConstraint('expected_views_at_hour >= 0'))
    performance_ratio = Column(Float, CheckConstraint('performance_ratio >= 0'))
    performance_ratio_normalized = Column(Float, CheckConstraint('performance_ratio_normalized BETWEEN 0 AND 1'))
    
    # Velocity and acceleration features
    view_velocity = Column(Float)
    view_acceleration = Column(Float)
    like_velocity = Column(Float)
    comment_velocity = Column(Float)
    engagement_velocity = Column(Float)
    
    # Relative velocity (key for virality detection)
    velocity_vs_baseline = Column(Float)
    velocity_vs_baseline_normalized = Column(Float, CheckConstraint('velocity_vs_baseline_normalized BETWEEN 0 AND 1'))
    
    # Data quality
    data_quality_passed = Column(Boolean, default=False)
    monotonic_check_passed = Column(Boolean)
    
    recorded_at = Column(DateTime, nullable=False)
    
    # Relationships
    video = relationship("Video", back_populates="snapshots")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('video_id', 'hours_after_publish'),
        CheckConstraint('view_count >= 0 AND like_count <= view_count AND comment_count >= 0'),
        Index('idx_snapshots_video_hours', 'video_id', 'hours_after_publish'),
        Index('idx_snapshots_recorded', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<VideoSnapshot(video_id={self.video_id}, hours={self.hours_after_publish})>"


class Prediction(Base):
    """
    Model predictions for different phases (baseline, adjusted).
    """
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(50), ForeignKey("videos.video_id"), nullable=False)
    
    prediction_phase = Column(String(20), nullable=False)  # 'baseline', 'adjusted_1hr', etc.
    predicted_views_24h = Column(BigInteger, CheckConstraint('predicted_views_24h >= 0'), nullable=False)
    virality_score = Column(Float, CheckConstraint('virality_score BETWEEN 0 AND 1'))
    virality_multiplier = Column(Float, CheckConstraint('virality_multiplier > 0'))
    
    model_version = Column(String(50))
    features_used = Column(JSONB)
    prediction_error = Column(Float)
    
    predicted_at = Column(DateTime, nullable=False)
    evaluated_at = Column(DateTime)
    
    # Relationship
    video = relationship("Video", back_populates="predictions")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('video_id', 'prediction_phase'),
        Index('idx_predictions_video_phase', 'video_id', 'prediction_phase'),
        Index('idx_predictions_evaluation', 'evaluated_at'),
    )
    
    def __repr__(self):
        return f"<Prediction(video_id={self.video_id}, phase={self.prediction_phase})>"


class DataQualityLog(Base):
    """
    Comprehensive data quality tracking and issue logging.
    """
    __tablename__ = "data_quality_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(50), ForeignKey("videos.video_id"))
    channel_id = Column(String(50), ForeignKey("channels.channel_id"))
    
    check_type = Column(String(50), nullable=False)  # 'schema', 'range', 'consistency', 'monotonic'
    check_name = Column(String(100), nullable=False)
    check_result = Column(Boolean, nullable=False)
    error_message = Column(Text)
    data_snapshot = Column(JSONB)
    
    severity = Column(String(20), CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')"))
    resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_log_video', 'video_id', 'created_at'),
        Index('idx_quality_log_severity', 'severity', 'resolved'),
    )
    
    def __repr__(self):
        return f"<DataQualityLog(type={self.check_type}, result={self.check_result})>"


class ModelPerformance(Base):
    """
    Track model performance metrics over time.
    """
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(50), nullable=False)
    
    # Performance metrics
    mae = Column(Float)  # Mean Absolute Error
    mape = Column(Float)  # Mean Absolute Percentage Error
    rmse = Column(Float)  # Root Mean Square Error
    viral_precision = Column(Float)
    viral_recall = Column(Float)
    
    # Data details
    evaluation_period_start = Column(DateTime)
    evaluation_period_end = Column(DateTime)
    total_predictions = Column(Integer)
    viral_predictions = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelPerformance(version={self.model_version}, mape={self.mape})>"


# Database connection and session management
class DatabaseManager:
    """Enhanced database manager with comprehensive table creation."""
    
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
        """Create all database tables with proper constraints."""
        Base.metadata.create_all(bind=self.engine)
        print("✅ All database tables created successfully!")
        
        # List created tables
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Created {len(tables)} tables: {', '.join(tables)}")
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return False
        
    def get_table_counts(self) -> dict:
        table_counts = {}
        try:
            with self.engine.connect() as conn:
                # Get all table names
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                
                # Count rows in each table
                for table in tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    table_counts[table] = count
                    
            return table_counts
        except Exception as e:
            print(f"❌ Failed to get table counts: {e}")
            return {}


# Global database manager
db_manager = DatabaseManager(get_database_url())


# FastAPI dependency for getting database sessions
def get_db():
    """FastAPI dependency to get database session."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


# Utility functions
def check_database_health() -> bool:
    """Standalone function to check database health."""
    return db_manager.health_check()

def init_database():
    """Initialize database with complete schema."""
    print("🔧 Initializing YouTube Predictor database...")
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