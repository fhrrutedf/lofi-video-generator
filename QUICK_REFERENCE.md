# Quick Reference - Lofi Video Generator

## Installation Check
```bash
ffmpeg -version  # Verify FFMPEG is installed
python --version # Verify Python 3.7+
```

## Basic Command Structure
```bash
python lofi_video_generator.py --music <audio> --video <video> --output <output.mp4>
```

## All Arguments

### Required
- `--music` / `-m` : Path to music track
- `--video` / `-v` : Path to video/image
- `--output` / `-o` : Output file path

### Optional
- `--ambience` / `-a` : Ambience audio track
- `--logo` / `-l` : Channel logo (PNG)
- `--film-grain` / `-fg` : Add film grain effect

## Common Commands

### Basic
```bash
python lofi_video_generator.py -m track.mp3 -v bg.mp4 -o output.mp4
```

### With Ambience
```bash
python lofi_video_generator.py -m track.mp3 -v bg.mp4 -a rain.mp3 -o output.mp4
```

### Full Featured
```bash
python lofi_video_generator.py -m track.mp3 -v bg.mp4 -a rain.mp3 -l logo.png -fg -o output.mp4
```

## Configuration Quickstart

Edit `config.py` to customize:

```python
# Duration (default: 4 hours)
OUTPUT_DURATION = 14400

# Quality (lower = better, default: 23)
VIDEO_CRF = 23

# Speed (options: fast, medium, slow)
VIDEO_PRESET = "medium"

# Ambience volume (0.0 - 1.0, default: 0.15)
AMBIENCE_VOLUME = 0.15

# Fade durations (seconds)
FADE_IN_DURATION = 3
FADE_OUT_DURATION = 3

# Logo position
LOGO_POSITION = "top-right"  # top-right, top-left, bottom-right, bottom-left
```

## Troubleshooting One-Liners

```bash
# Check FFMPEG
ffmpeg -version

# Check input duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 music.mp3

# Check output properties
ffprobe -v error -show_entries format=duration -show_entries stream=width,height,codec_name output.mp4

# Test FFMPEG works
ffmpeg -i music.mp3 -i video.mp4 -t 10 test.mp4
```

## Expected Results

- **Duration**: 4 hours (14,400 seconds)
- **Resolution**: 1920x1080
- **FPS**: 30
- **Size**: ~5-10 GB
- **Render Time**: 30-90 minutes (varies by CPU)
