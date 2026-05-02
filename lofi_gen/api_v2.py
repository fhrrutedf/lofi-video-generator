"""
Enhanced FastAPI with database, auth, and Celery queue.

This is the production-ready API (v2).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig
from lofi_gen.core.logging import get_logger
from lofi_gen.db.connection import get_db, engine
from lofi_gen.db.models import Base, User, Job, JobStatus, UserTier
from lofi_gen.auth import get_current_user, check_quota
from lofi_gen.tasks import celery_app, generate_video_task, update_job_progress
from lofi_gen.ai.prompt_system import THEME_TEMPLATES

log = get_logger("api_v2")

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LofiGen API v2",
    description="Production API with auth, queue, and progress tracking",
    version="2.0.0",
)

# ── Request/Response Models ──────────────────────────────────────────

class GenerateRequest(BaseModel):
    theme: str = Field(default="default", description="Theme keyword or description")
    duration: float = Field(default=14400, ge=60, le=43200, description="Duration in seconds (max 12h)")
    fps: int = Field(default=30, ge=24, le=60)
    max_zoom: float = Field(default=1.15, ge=1.0, le=1.3)
    quality: str = Field(default="medium", pattern="^(ultrafast|superfast|veryfast|faster|fast|medium|slow)$")
    film_grain: bool = False
    vignette: bool = False
    audio_effects: list[str] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list, max_length=5)


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str
    queue_position: Optional[int] = None


class JobStatusResponse(BaseModel):
    id: str
    theme: str
    duration: int
    status: str
    progress: float
    current_step: Optional[str]
    output_url: Optional[str]
    created_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


class UserInfoResponse(BaseModel):
    id: str
    email: str
    tier: str
    videos_generated: int
    monthly_limit: int
    storage_used_mb: float


class CreateUserRequest(BaseModel):
    email: str
    tier: UserTier = UserTier.FREE


class CreateUserResponse(BaseModel):
    id: str
    email: str
    api_key: str
    tier: str


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """Health check with DB connectivity."""
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    
    # Check Celery
    try:
        inspector = celery_app.control.inspect()
        workers = inspector.active() or {}
        worker_count = len(workers)
    except:
        worker_count = 0
    
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "celery_workers": worker_count,
        "version": "2.0.0"
    }


@app.get("/themes")
def list_themes() -> dict:
    """List all available themes."""
    result = {}
    for name, data in THEME_TEMPLATES.items():
        result[name] = {
            "bpm_range": data["bpm_range"],
            "mood": data["mood"],
            "music_templates_count": len(data.get("music_templates", [])),
        }
    return result


@app.post("/generate", response_model=GenerateResponse)
def create_job(
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GenerateResponse:
    """
    Create a new video generation job.
    
    Requires API key authentication.
    """
    # Check quota
    check_quota(user, int(req.duration))
    
    # Build config
    config = GenerationConfig(
        theme=req.theme,
        duration=req.duration,
        video=VideoConfig(
            fps=req.fps,
            preset=req.quality,
            max_zoom=req.max_zoom,
            film_grain=req.film_grain,
            vignette=req.vignette,
        ),
        audio=AudioConfig(effects=req.audio_effects),
        ai=AIConfig(),  # Uses env vars
        quotes=req.quotes,
        output_dir="output",
    )
    
    # Create job in DB
    job = Job(
        user_id=user.id,
        theme=req.theme,
        duration=int(req.duration),
        config_json=config.__dict__,  # Simplified serialization
        status=JobStatus.QUEUED,
        progress=0.0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Queue Celery task
    task = generate_video_task.delay(
        job_id=job.id,
        config_dict={
            "theme": config.theme,
            "duration": config.duration,
            "video": config.video.__dict__,
            "audio": config.audio.__dict__,
            "ai": config.ai.__dict__,
            "quotes": config.quotes,
            "output_dir": config.output_dir,
        }
    )
    
    # Update job with Celery task ID
    job.celery_task_id = task.id
    db.commit()
    
    # Get queue position (approximate)
    try:
        inspector = celery_app.control.inspect()
        active = inspector.active() or {}
        scheduled = inspector.scheduled() or {}
        queue_position = sum(len(t) for t in active.values()) + sum(len(t) for t in scheduled.values())
    except:
        queue_position = None
    
    log.info("Job %s created for user %s (tier: %s)", job.id, user.email, user.tier.value)
    
    return GenerateResponse(
        job_id=job.id,
        status="queued",
        message="Job queued successfully",
        queue_position=queue_position
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> JobStatusResponse:
    """Get status of a specific job."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        id=job.id,
        theme=job.theme,
        duration=job.duration,
        status=job.status.value,
        progress=job.progress,
        current_step=job.current_step,
        output_url=f"/download/{job.id}" if job.status == JobStatus.COMPLETED else None,
        created_at=job.created_at.isoformat() if job.created_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error_message,
    )


@app.get("/jobs")
def list_user_jobs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
) -> list[JobStatusResponse]:
    """List user's jobs."""
    jobs = db.query(Job).filter(
        Job.user_id == user.id
    ).order_by(
        Job.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [JobStatusResponse(
        id=j.id,
        theme=j.theme,
        duration=j.duration,
        status=j.status.value,
        progress=j.progress,
        current_step=j.current_step,
        output_url=f"/download/{j.id}" if j.status == JobStatus.COMPLETED else None,
        created_at=j.created_at.isoformat() if j.created_at else None,
        completed_at=j.completed_at.isoformat() if j.completed_at else None,
        error=j.error_message,
    ) for j in jobs]


@app.get("/download/{job_id}")
def download_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download generated video."""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == user.id,
        Job.status == JobStatus.COMPLETED
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not completed")
    
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=job.output_path,
        media_type="video/mp4",
        filename=f"lofi_{job.theme}_{job.id[:8]}.mp4"
    )


@app.get("/me", response_model=UserInfoResponse)
def get_current_user_info(user: User = Depends(get_current_user)) -> UserInfoResponse:
    """Get current user's info and usage stats."""
    return UserInfoResponse(
        id=user.id,
        email=user.email,
        tier=user.tier.value,
        videos_generated=user.videos_generated,
        monthly_limit=user.monthly_limit,
        storage_used_mb=user.storage_used_mb,
    )


# ── Admin Endpoints (should add admin auth) ──────────────────────────

@app.post("/admin/users", response_model=CreateUserResponse)
def create_user(
    req: CreateUserRequest,
    db: Session = Depends(get_db)
) -> CreateUserResponse:
    """Create a new user (admin only - should add auth)."""
    # Generate API key
    api_key = f"lg_{uuid.uuid4().hex}"
    
    # Set limits by tier
    limits = {
        UserTier.FREE: (3, 3600),
        UserTier.HOBBY: (10, 14400),
        UserTier.PRO: (50, 14400),
        UserTier.AGENCY: (999999, 43200),
    }
    monthly_limit, max_duration = limits.get(req.tier, (3, 3600))
    
    user = User(
        email=req.email,
        api_key=api_key,
        tier=req.tier,
        monthly_limit=monthly_limit,
        max_duration=max_duration,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return CreateUserResponse(
        id=user.id,
        email=user.email,
        api_key=api_key,
        tier=user.tier.value,
    )
