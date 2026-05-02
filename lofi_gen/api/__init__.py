"""
LofiGen API — FastAPI backend for SaaS deployment.

Endpoints:
  POST /generate   — Start a generation job
  GET  /status/{id} — Check job status
  GET  /download/{id} — Download result
  GET  /themes     — List available themes
  GET  /health     — Health check
"""

from __future__ import annotations

import uuid
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig
from lofi_gen.core.types import GenerationResult, JobStatus, JobState
from lofi_gen.pipeline import LofiPipeline
from lofi_gen.ai.prompt_system import THEME_TEMPLATES
from lofi_gen.core.logging import get_logger

log = get_logger("api")

app = FastAPI(
    title="LofiGen API",
    description="Professional Lofi Video Generator API",
    version="1.0.0",
)

# In-memory job store (replace with Redis/DB for production)
_jobs: dict[str, JobStatus] = {}


# ── Request Models ─────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """Request body for /generate endpoint."""
    theme: str = "default"
    duration: float = 14400.0  # seconds
    image_paths: list[str] = []
    video_path: Optional[str] = None
    music_path: Optional[str] = None
    ambience_path: Optional[str] = None
    quotes: list[str] = []
    fps: int = 30
    max_zoom: float = 1.15
    crossfade: float = 2.0
    film_grain: bool = False
    vignette: bool = False
    audio_effects: list[str] = []
    output_name: Optional[str] = None


class GenerateResponse(BaseModel):
    job_id: str
    message: str


class StatusResponse(BaseModel):
    job_id: str
    state: str
    progress: float
    message: str
    output_path: Optional[str] = None
    error: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0"}


@app.get("/themes")
def list_themes() -> dict:
    """List all available themes with their BPM ranges and moods."""
    result = {}
    for name, data in THEME_TEMPLATES.items():
        result[name] = {
            "bpm_range": data["bpm_range"],
            "mood": data["mood"],
        }
    return result


@app.post("/generate", response_model=GenerateResponse)
def start_generation(req: GenerateRequest) -> GenerateResponse:
    """Start a video generation job in the background."""
    job_id = str(uuid.uuid4())[:8]

    config = GenerationConfig(
        theme=req.theme,
        duration=req.duration,
        video=VideoConfig(
            fps=req.fps,
            max_zoom=req.max_zoom,
            crossfade_duration=req.crossfade,
            film_grain=req.film_grain,
            vignette=req.vignette,
        ),
        audio=AudioConfig(effects=req.audio_effects),
        ai=AIConfig(),
        image_paths=req.image_paths,
        video_path=req.video_path,
        music_path=req.music_path,
        ambience_path=req.ambience_path,
        quotes=req.quotes,
        output_name=req.output_name,
    )

    # Store job
    _jobs[job_id] = JobStatus(job_id=job_id, state=JobState.PENDING, message="Queued")

    # Run in background thread (use Celery for production)
    thread = threading.Thread(target=_run_job, args=(job_id, config), daemon=True)
    thread.start()

    return GenerateResponse(job_id=job_id, message="Generation started")


@app.get("/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: str) -> StatusResponse:
    """Check the status of a generation job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]
    return StatusResponse(
        job_id=job.job_id,
        state=job.state.value,
        progress=job.progress,
        message=job.message,
        output_path=job.result.output_path if job.result and job.result.success else None,
        error=job.result.error if job.result and not job.result.success else None,
    )


@app.get("/download/{job_id}")
def download_result(job_id: str):
    """Download the generated video file."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]
    if job.state != JobState.COMPLETED or not job.result or not job.result.output_path:
        raise HTTPException(status_code=400, detail="Video not ready yet")

    path = Path(job.result.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=path,
        media_type="video/mp4",
        filename=path.name,
    )


# ── Background Worker ──────────────────────────────────────────────────

def _run_job(job_id: str, config: GenerationConfig) -> None:
    """Execute pipeline in background thread."""
    job = _jobs[job_id]
    job.state = JobState.RUNNING
    job.message = "Generating..."

    try:
        pipeline = LofiPipeline(config)
        result = pipeline.run()

        job.result = result
        if result.success:
            job.state = JobState.COMPLETED
            job.progress = 1.0
            job.message = "Complete"
        else:
            job.state = JobState.FAILED
            job.message = result.error or "Unknown error"

    except Exception as e:
        job.state = JobState.FAILED
        job.message = str(e)
        log.error("Job %s failed: %s", job_id, e)
