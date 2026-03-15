"""
Configuration settings for Lofi YouTube Video Generator
"""

import os

# API Keys (loaded from environment variables for security)
# Set these in your .env file or as environment variables
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")  # Pexels video search
KIE_API_KEY = os.getenv("KIE_API_KEY", "")  # Kie.ai for music/video generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Google Gemini AI

# Output Video Settings
OUTPUT_DURATION = 36000  # 10 hours (originally 120)
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
OUTPUT_FPS = 30

# Video Encoding Settings
VIDEO_CODEC = "libx264"
VIDEO_CRF = 23  # Constant Rate Factor (0-51, lower = better quality, 23 is good balance)
VIDEO_PRESET = "superfast"  # Fast for testing (originally medium)
PIXEL_FORMAT = "yuv420p"  # Maximum compatibility

# Audio Encoding Settings
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
AUDIO_SAMPLE_RATE = 48000

# Audio Effects Settings
FADE_IN_DURATION = 3  # seconds
FADE_OUT_DURATION = 3  # seconds
AMBIENCE_VOLUME = 0.15  # 0.0 to 1.0

# Visual Overlay Settings
LOGO_POSITION = "top-right"  # top-right, top-left, bottom-right, bottom-left
LOGO_MARGIN = 20  # pixels from edge
LOGO_OPACITY = 1.0  # 0.0 to 1.0

# Film Grain/Dust Settings
FILM_GRAIN_STRENGTH = 5  # 0-100, subtle effect
FILM_GRAIN_TYPE = "all"  # all, temporal, uniform

# Progress Display Settings
PROGRESS_UPDATE_INTERVAL = 1.0  # seconds

# FFMPEG Settings
FFMPEG_LOGLEVEL = "info"  # quiet, panic, fatal, error, warning, info, verbose, debug
OVERWRITE_OUTPUT = True  # Automatically overwrite output file if exists
