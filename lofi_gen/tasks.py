"""
Celery tasks for background job processing.

This replaces the threading-based approach with proper queue workers.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm import Session

from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig
from lofi_gen.core.logging import get_logger
from lofi_gen.db.connection import SessionLocal
from lofi_gen.db.models import Job, JobStatus
from lofi_gen.pipeline import LofiPipeline

log = get_logger("tasks")

# Celery app configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "lofi_gen",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["lofi_gen.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,  # 2 hours max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


def update_job_progress(
    job_id: str,
    progress: float,
    step: str,
    db: Optional[Session] = None
) -> None:
    """Update job progress in database."""
    should_close = db is None
    if db is None:
        db = SessionLocal()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.progress = progress
            job.current_step = step
            db.commit()
    finally:
        if should_close:
            db.close()


@celery_app.task(bind=True, max_retries=3)
def generate_video_task(self, job_id: str, config_dict: dict) -> dict:
    """
    Celery task for video generation.
    
    Args:
        job_id: Database job ID
        config_dict: GenerationConfig as dictionary
    """
    db = SessionLocal()
    
    try:
        # Get job from DB
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            log.error("Job not found: %s", job_id)
            return {"success": False, "error": "Job not found"}
        
        # Update status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.celery_task_id = self.request.id
        db.commit()
        
        # Reconstruct config
        config = GenerationConfig(
            theme=config_dict.get("theme", "default"),
            duration=config_dict.get("duration", 14400),
            video=VideoConfig(**config_dict.get("video", {})),
            audio=AudioConfig(**config_dict.get("audio", {})),
            ai=AIConfig(**config_dict.get("ai", {})),
            image_paths=config_dict.get("image_paths", []),
            video_path=config_dict.get("video_path"),
            music_path=config_dict.get("music_path"),
            ambience_path=config_dict.get("ambience_path"),
            quotes=config_dict.get("quotes", []),
            output_dir=config_dict.get("output_dir", "output"),
        )
        
        # Custom progress callback
        def progress_callback(step: str, percent: float):
            update_job_progress(job_id, percent / 100, step, db)
            self.update_state(
                state="PROGRESS",
                meta={"step": step, "percent": percent}
            )
        
        # Run pipeline with progress updates
        log.info("Starting pipeline for job %s", job_id)
        
        pipeline = LofiPipeline(config)
        
        # Manual progress steps
        progress_callback("analyzing_theme", 5)
        result = pipeline.run()
        
        # Update job with results
        if result.success:
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.output_path = result.output_path
            job.thumbnail_path = result.thumbnail_path
            job.metadata_path = result.metadata_path
            job.file_size_mb = result.file_size_mb
            job.completed_at = datetime.utcnow()
            
            # Update user stats
            user = job.user
            user.videos_generated += 1
            user.total_duration_seconds += int(config.duration)
            user.storage_used_mb += result.file_size_mb or 0
            
            db.commit()
            log.info("Job %s completed successfully", job_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "output_path": result.output_path,
                "file_size_mb": result.file_size_mb,
            }
        else:
            job.status = JobStatus.FAILED
            job.error_message = result.error
            db.commit()
            log.error("Job %s failed: %s", job_id, result.error)
            
            # Retry on certain errors
            if result.error and any(e in result.error.lower() for e in ["timeout", "connection", "rate limit"]):
                try:
                    raise self.retry(countdown=60)
                except MaxRetriesExceededError:
                    pass
            
            return {"success": False, "error": result.error}
    
    except Exception as e:
        log.exception("Exception in job %s", job_id)
        
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                db.commit()
        except:
            pass
        
        # Retry on exception
        try:
            raise self.retry(countdown=120)
        except MaxRetriesExceededError:
            return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_jobs(days: int = 7) -> int:
    """Cleanup old completed/failed jobs and their files."""
    db = SessionLocal()
    
    try:
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        old_jobs = db.query(Job).filter(
            Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
            Job.completed_at < cutoff
        ).all()
        
        deleted = 0
        for job in old_jobs:
            # Delete files
            for path_attr in ["output_path", "thumbnail_path", "metadata_path"]:
                path = getattr(job, path_attr)
                if path:
                    try:
                        os.remove(path)
                    except:
                        pass
            
            db.delete(job)
            deleted += 1
        
        db.commit()
        log.info("Cleaned up %d old jobs", deleted)
        return deleted
    
    finally:
        db.close()
