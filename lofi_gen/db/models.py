"""
Database models for LofiGen SaaS.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserTier(str, enum.Enum):
    FREE = "free"
    HOBBY = "hobby"
    PRO = "pro"
    AGENCY = "agency"


class User(Base):
    """User account for SaaS."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    tier = Column(Enum(UserTier), default=UserTier.FREE)
    
    # Usage tracking
    videos_generated = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0.0)
    
    # Limits by tier
    monthly_limit = Column(Integer, default=3)  # videos per month
    max_duration = Column(Integer, default=3600)  # seconds
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """Video generation job."""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Input
    theme = Column(String(255), nullable=False)
    duration = Column(Integer, nullable=False)  # seconds
    config_json = Column(Text)  # JSON string of GenerationConfig
    
    # Status
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(100))  # e.g., "rendering_video"
    
    # Results
    output_path = Column(String(500))
    thumbnail_path = Column(String(500))
    metadata_path = Column(String(500))
    file_size_mb = Column(Float)
    
    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Celery
    celery_task_id = Column(String(100), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relations
    user = relationship("User", back_populates="jobs")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "theme": self.theme,
            "duration": self.duration,
            "status": self.status.value,
            "progress": round(self.progress, 2),
            "current_step": self.current_step,
            "output_url": f"/download/{self.id}" if self.output_path else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error_message,
        }
