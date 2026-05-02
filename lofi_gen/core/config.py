"""
Configuration dataclasses — replaces the old config.py globals
and the 25+ parameter functions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoConfig:
    """Video rendering settings."""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "libx264"
    crf: int = 23
    preset: str = "medium"
    pixel_format: str = "yuv420p"
    max_zoom: float = 1.15
    crossfade_duration: float = 2.0
    fade_in: float = 3.0
    fade_out: float = 3.0
    film_grain: bool = False
    grain_strength: int = 5
    mood: Optional[str] = None
    vignette: bool = False
    letterbox: bool = False


@dataclass
class AudioConfig:
    """Audio rendering settings."""
    codec: str = "aac"
    bitrate: str = "192k"
    sample_rate: int = 48000
    crossfade_duration: float = 3.0
    ambience_volume: float = 0.15
    effects: list[str] = field(default_factory=list)


@dataclass
class AIConfig:
    """AI provider configuration."""
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    kie_api_key: str = field(default_factory=lambda: os.getenv("KIE_API_KEY", ""))
    pexels_api_key: str = field(default_factory=lambda: os.getenv("PEXELS_API_KEY", ""))
    provider: str = "auto"  # "gemini" | "openrouter" | "auto"

    @property
    def has_ai(self) -> bool:
        return bool(self.gemini_api_key or self.openrouter_api_key)

    @property
    def has_music(self) -> bool:
        return bool(self.kie_api_key)


@dataclass
class GenerationConfig:
    """Top-level configuration for a single generation job."""
    theme: str = "default"
    duration: float = 14400.0  # 4 hours in seconds
    video: VideoConfig = field(default_factory=VideoConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    ai: AIConfig = field(default_factory=AIConfig)

    # Input sources (at least one visual + one audio required)
    image_paths: list[str] = field(default_factory=list)
    video_path: Optional[str] = None
    music_path: Optional[str] = None
    ambience_path: Optional[str] = None
    logo_path: Optional[str] = None

    # Text overlays
    quotes: list[str] = field(default_factory=list)

    # Output
    output_dir: str = "output"
    output_name: Optional[str] = None

    # YouTube
    upload_to_youtube: bool = False
    youtube_secrets_file: str = "client_secrets.json"
    youtube_privacy: str = "private"

    # Live stream
    live_stream: bool = False
    stream_key: Optional[str] = None

    @property
    def has_visual(self) -> bool:
        return bool(self.image_paths or self.video_path)

    @property
    def has_audio(self) -> bool:
        return bool(self.music_path or self.ai.has_music)
