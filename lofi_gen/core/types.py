"""
Shared types and data structures used across the package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class JobState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ThemeInfo:
    """Detected theme metadata."""
    name: str
    bpm: int = 80
    mood: str = "clean"
    music_prompt: str = ""
    video_prompt: str = ""
    advanced: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of a generation job."""
    success: bool
    output_path: Optional[str] = None
    music_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    metadata_path: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    file_size_mb: float = 0.0
    theme_info: Optional[ThemeInfo] = None


@dataclass
class JobStatus:
    """Status of an async generation job."""
    job_id: str
    state: JobState = JobState.PENDING
    progress: float = 0.0  # 0.0 → 1.0
    message: str = ""
    result: Optional[GenerationResult] = None
