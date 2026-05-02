"""
LofiGen — Professional Lofi Video Generator
============================================

Turn a simple keyword into a complete lofi video with AI music,
visual effects, and seamless looping.

Usage:
    from lofi_gen import LofiPipeline, GenerationConfig

    config = GenerationConfig(theme="rain", duration=7200)
    pipeline = LofiPipeline(config)
    result = pipeline.run()
"""

__version__ = "1.0.0"
__author__ = "Antigravity AI"

from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig
from lofi_gen.core.types import GenerationResult, ThemeInfo, JobStatus
from lofi_gen.pipeline import LofiPipeline
