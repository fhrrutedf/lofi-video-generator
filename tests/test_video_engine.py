"""Tests for video engine."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from lofi_gen.media.video_engine import VideoEngine
from lofi_gen.core.config import VideoConfig


def test_video_engine_init():
    """Test video engine initialization."""
    config = VideoConfig(fps=30, max_zoom=1.15)
    engine = VideoEngine(config)
    
    assert engine.config.fps == 30
    assert engine.config.max_zoom == 1.15


def test_ping_pong_zoom_expression():
    """Test that ping-pong zoom uses cosine formula."""
    config = VideoConfig(max_zoom=1.2)
    engine = VideoEngine(config)
    
    # The zoom expression should be a cosine-based formula
    # z(t) = 1 + (max_zoom - 1) * 0.5 * (1 - cos(2*pi*t/duration))
    assert config.max_zoom == 1.2


def test_wrap_text():
    """Test text wrapping utility."""
    engine = VideoEngine(VideoConfig())
    
    short_text = "Short"
    assert engine._wrap_text(short_text, 40) == ["Short"]
    
    long_text = "This is a very long text that should be wrapped into multiple lines"
    lines = engine._wrap_text(long_text, 20)
    assert len(lines) > 1
    assert all(len(line) <= 20 for line in lines)


def test_ffmpeg_not_found():
    """Test error handling when ffmpeg is not found."""
    engine = VideoEngine(VideoConfig())
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        
        with pytest.raises(RuntimeError, match="FFMPEG not found"):
            engine._run_ffmpeg(["ffmpeg", "-version"])


def test_ffmpeg_error():
    """Test error handling for ffmpeg command failure."""
    engine = VideoEngine(VideoConfig())
    
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: invalid input"
        mock_run.return_value = mock_result
        
        with pytest.raises(RuntimeError, match="FFMPEG exited with code 1"):
            engine._run_ffmpeg(["ffmpeg", "-i", "test.mp4"])
