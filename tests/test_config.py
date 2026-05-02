"""Tests for configuration system."""

import pytest
from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig


def test_generation_config_defaults():
    """Test default configuration values."""
    config = GenerationConfig()
    
    assert config.theme == "default"
    assert config.duration == 14400.0  # 4 hours
    assert config.video.width == 1920
    assert config.video.height == 1080
    assert config.video.fps == 30


def test_video_config():
    """Test video configuration."""
    video = VideoConfig(
        fps=60,
        max_zoom=1.2,
        film_grain=True,
        vignette=True,
    )
    
    assert video.fps == 60
    assert video.max_zoom == 1.2
    assert video.film_grain is True
    assert video.vignette is True


def test_ai_config_has_keys():
    """Test AI config detects API keys."""
    # Without keys
    ai_empty = AIConfig()
    assert ai_empty.has_ai is False
    assert ai_empty.has_music is False
    
    # With keys
    ai_with_keys = AIConfig(
        gemini_api_key="test_key",
        kie_api_key="test_key"
    )
    assert ai_with_keys.has_ai is True
    assert ai_with_keys.has_music is True


def test_config_has_visual():
    """Test has_visual property."""
    config_no_visual = GenerationConfig()
    assert config_no_visual.has_visual is False
    
    config_with_image = GenerationConfig(image_paths=["test.jpg"])
    assert config_with_image.has_visual is True
    
    config_with_video = GenerationConfig(video_path="test.mp4")
    assert config_with_video.has_visual is True


def test_config_has_audio():
    """Test has_audio property."""
    config_no_audio = GenerationConfig()
    assert config_no_audio.has_audio is False
    
    config_with_music = GenerationConfig(music_path="test.mp3")
    assert config_with_music.has_audio is True
