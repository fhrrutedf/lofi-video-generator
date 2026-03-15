#!/usr/bin/env python3
"""
Professional Lofi YouTube Video Generator

This script generates 4-hour Lofi YouTube videos by looping audio and video assets,
applying professional audio engineering and visual enhancements.

Author: Antigravity AI Assistant
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional
import time
import threading

import config
import ffmpeg_utils


class ProgressTracker:
    """Tracks and displays FFMPEG rendering progress"""
    
    def __init__(self, target_duration: float):
        self.target_duration = target_duration
        self.current_time = 0.0
        self.start_time = time.time()
        self.running = True
        
    def update(self, current_time: float):
        """Update current progress"""
        self.current_time = current_time
        self.display()
    
    def display(self):
        """Display progress bar and stats"""
        if self.target_duration <= 0:
            return
        
        percentage = min(100, (self.current_time / self.target_duration) * 100)
        elapsed = time.time() - self.start_time
        
        # Calculate ETA
        if self.current_time > 0:
            rate = elapsed / self.current_time
            remaining = (self.target_duration - self.current_time) * rate
            eta_str = ffmpeg_utils.format_time(remaining)
        else:
            eta_str = "calculating..."
        
        # Progress bar
        bar_length = 40
        filled = int(bar_length * percentage / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Display
        time_str = ffmpeg_utils.format_time(self.current_time)
        target_str = ffmpeg_utils.format_time(self.target_duration)
        
        print(f"\r[{bar}] {percentage:6.2f}% | {time_str} / {target_str} | ETA: {eta_str}", 
              end='', flush=True)
    
    def finish(self):
        """Mark progress as complete"""
        self.current_time = self.target_duration
        self.display()
        print()  # New line after completion


def validate_inputs(args) -> bool:
    """Validate all input files exist and are readable"""
    
    # Check music file
    if not Path(args.music).exists():
        print(f"❌ Error: Music file not found: {args.music}")
        return False
    
    # Check video/image file
    if not Path(args.video).exists():
        print(f"❌ Error: Video/image file not found: {args.video}")
        return False
    
    # Check ambience file if provided
    if args.ambience and not Path(args.ambience).exists():
        print(f"❌ Error: Ambience file not found: {args.ambience}")
        return False
    
    # Check logo file if provided
    if args.logo and not Path(args.logo).exists():
        print(f"❌ Error: Logo file not found: {args.logo}")
        return False
    
    return True


def build_ffmpeg_command(args, is_image_override: bool = False) -> list:
    """Build the complete FFMPEG command"""
    
    print("🔍 Analyzing input files...")
    
    # Get durations
    music_duration = ffmpeg_utils.get_media_duration(args.music)
    video_duration = ffmpeg_utils.get_media_duration(args.video)
    
    print(f"   Music duration: {ffmpeg_utils.format_time(music_duration)}")
    print(f"   Video duration: {ffmpeg_utils.format_time(video_duration)}")
    
    ambience_duration = None
    if args.ambience:
        ambience_duration = ffmpeg_utils.get_media_duration(args.ambience)
        print(f"   Ambience duration: {ffmpeg_utils.format_time(ambience_duration)}")
    
    # Calculate loop counts
    music_loops = ffmpeg_utils.calculate_loop_count(music_duration, config.OUTPUT_DURATION)
    video_loops = ffmpeg_utils.calculate_loop_count(video_duration, config.OUTPUT_DURATION)
    
    print(f"\n📊 Loop calculations:")
    print(f"   Music will loop: {music_loops + 1} times")
    print(f"   Video will loop: {video_loops + 1} times")
    
    ambience_loops = 0
    if args.ambience:
        ambience_loops = ffmpeg_utils.calculate_loop_count(ambience_duration, config.OUTPUT_DURATION)
        print(f"   Ambience will loop: {ambience_loops + 1} times")
    
    # Build actual command strings
    cmd = ["ffmpeg", "-y"]
    
    # Input 0: Music (with loop)
    cmd.extend(["-stream_loop", str(music_loops), "-i", args.music])
    
    # Input 1: Ambience (if provided)
    ambience_input_index = None
    if args.ambience:
        ambience_input_index = 1
        cmd.extend(["-stream_loop", str(ambience_loops), "-i", args.ambience])
    
    # Input 2/1: Video (with loop)
    # Determine video index based on ambience presence
    video_input_index = 1 if not args.ambience else 2
    cmd.extend(["-stream_loop", str(video_loops), "-i", args.video])
    
    # Input 3/2: Logo (if provided)
    logo_input_index = None
    if args.logo:
        logo_input_index = video_input_index + 1
        cmd.extend(["-i", args.logo])
    
    # Build filter complex
    print("\n🎨 Building filter chains...")
    
    effects_list = args.audio_effects.split(',') if args.audio_effects else []
    
    audio_filter = ffmpeg_utils.build_audio_filter(
        music_duration,
        has_ambience=bool(args.ambience),
        ambience_duration=ambience_duration,
        effects=effects_list
    )
    
    # Detect if background is an image
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.svg']
    is_image = is_image_override or (Path(args.video).suffix.lower() in image_extensions)
    
    # If a background image is provided via --bg-image, override video source (for safety)
    if getattr(args, 'bg_image', None):
        args.video = args.bg_image
        is_image = True
        
    video_filter = ffmpeg_utils.build_video_filter(
        video_index=video_input_index,
        has_logo=bool(args.logo),
        logo_index=logo_input_index,
        has_film_grain=args.film_grain,
        mood=getattr(args, 'mood', 'clean'),
        has_pomodoro=getattr(args, 'pomodoro', False),
        evolving=getattr(args, 'evolving', False),
        glitch=getattr(args, 'glitch', False),
        speed=getattr(args, 'speed', 1.0),
        is_image=is_image,
        has_rain=getattr(args, 'rain', False),
        has_fog=getattr(args, 'fog', False),
        has_particles=getattr(args, 'particles', False),
        has_breathing=getattr(args, 'breathing', False),
        has_vignette=getattr(args, 'vignette', False),
        has_letterbox=getattr(args, 'letterbox', False),
        has_blur_bg=getattr(args, 'blur_bg', False),
        has_camera_shake=getattr(args, 'camera_shake', False)
    )
    
    # Combine filters
    if audio_filter and video_filter:
        filter_complex = f"{audio_filter};{video_filter}"
    elif audio_filter:
        filter_complex = audio_filter
    else:
        filter_complex = video_filter
    
    if filter_complex:
        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-map", "[vout]", "-map", "[aout]"])
    
    # Video encoding settings
    cmd.extend([
        "-c:v", config.VIDEO_CODEC,
        "-crf", str(config.VIDEO_CRF),
        "-preset", config.VIDEO_PRESET,
        "-pix_fmt", config.PIXEL_FORMAT,
        "-r", str(config.OUTPUT_FPS),
    ])
    
    # Audio encoding settings
    cmd.extend([
        "-c:a", config.AUDIO_CODEC,
        "-b:a", config.AUDIO_BITRATE,
        "-ar", str(config.AUDIO_SAMPLE_RATE),
    ])
    
    # Duration and output
    cmd.extend([
        "-t", str(config.OUTPUT_DURATION),
        "-movflags", "+faststart",
    ])
    
    if args.live:
        # Determine RTMP URL for YouTube Live
        if args.stream_key:
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{args.stream_key}"
        elif args.youtube_key:
            from youtube_live import get_rtmp_url
            rtmp_url = get_rtmp_url(args.youtube_key)
        else:
            raise ValueError("Live mode requires either --stream-key or --youtube-key")
        cmd.extend(["-f", "flv", rtmp_url])
    else:
        cmd.append(args.output)
    
    return cmd


def run_ffmpeg(cmd: list):
    """Run FFMPEG command with progress tracking"""
    
    print("\n🎬 Starting video generation...")
    print(f"   Target duration: {ffmpeg_utils.format_time(config.OUTPUT_DURATION)} (4 hours)")
    print(f"   Output: {cmd[-1]}")
    print("\n" + "="*80)
    
    # Create progress tracker
    tracker = ProgressTracker(config.OUTPUT_DURATION)
    
    # Run FFMPEG
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    
    # Monitor output
    try:
        for line in process.stdout:
            # Parse progress
            current_time = ffmpeg_utils.parse_progress(line)
            if current_time:
                tracker.update(current_time)
            
            # Print errors
            if "error" in line.lower() or "warning" in line.lower():
                print(f"\n⚠️  {line.strip()}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Terminating FFMPEG...")
        process.terminate()
        process.wait()
        print("❌ Render cancelled.")
        return False
    
    # Wait for completion
    process.wait()
    
    if process.returncode == 0:
        tracker.finish()
        print("\n" + "="*80)
        print("✅ Video generation complete!")
        return True
    else:
        print("\n" + "="*80)
        print(f"❌ FFMPEG failed with return code: {process.returncode}")
        return False


def main():
    """Main entry point"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Professional Lofi YouTube Video Generator - Create 4-hour videos from loops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with music and video
  python lofi_video_generator.py --music track.mp3 --video background.mp4 --output lofi_4hr.mp4
  
  # Full featured with ambience, logo, and film grain
  python lofi_video_generator.py --music track.mp3 --video bg.mp4 --ambience rain.mp3 --logo logo.png --film-grain --output final.mp4
  
  # Using an image as background
  python lofi_video_generator.py --music track.mp3 --video wallpaper.jpg --ambience cafe.mp3 --output chill_vibes.mp4
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--music", "-m",
        required=True,
        help="Path to 3-minute music track (MP3, WAV, etc.)"
    )
    
    parser.add_argument(
        "--video", "-v",
        required=True,
        help="Path to video loop or image (MP4, JPG, PNG, etc.)"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path for output video file (MP4)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--ambience", "-a",
        help="Path to ambience track (rain, cafe sounds, etc.)"
    )
    
    parser.add_argument(
        "--logo", "-l",
        help="Path to channel logo PNG (transparent background recommended)"
    )
    
    parser.add_argument(
        "--film-grain", "-fg",
        action="store_true",
        help="Add subtle film grain/dust overlay for Lofi aesthetic"
    )
    
    parser.add_argument(
        "--mood", "-mo",
        choices=["cozy", "sad", "melancholy", "dreamy", "ethereal", "clean", "productive"],
        help="Apply specific color grading mood to the video"
    )
    # Live streaming options
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live streaming to YouTube (RTMP)"
    )
    parser.add_argument(
        "--youtube-key",
        type=str,
        help="Path to JSON file containing YouTube OAuth 2.0 access token"
    )
    parser.add_argument(
        "--stream-key",
        type=str,
        help="YouTube RTMP stream key (optional if token is provided)"
    )

    parser.add_argument(
        "--pomodoro", "-pmo",
        action="store_true",
        help="Overlay a 25/5 Pomodoro study timer"
    )
    
    parser.add_argument("--evolving", action="store_true", help="Enable day-to-night color transition")
    parser.add_argument("--glitch", action="store_true", help="Enable subtle periodic glitch effects")
    parser.add_argument("--speed", type=float, default=1.0, help="Adjust video playback speed")
    parser.add_argument("--audio-effects", help="Comma-separated audio effects (reverb, vinyl)")
    parser.add_argument("--rain", action="store_true", help="Add visual rain effect")
    parser.add_argument("--fog", action="store_true", help="Add moving fog/mist effect")
    parser.add_argument("--particles", action="store_true", help="Add floating particles (dust/snow)")
    parser.add_argument("--breathing", action="store_true", help="Add subtle breathing/pulsing animation")
    parser.add_argument("--vignette", action="store_true", help="Add cinematic vignette effect")
    parser.add_argument("--letterbox", action="store_true", help="Add cinematic black bars")
    parser.add_argument("--blur-bg", action="store_true", help="Replace black bars with blurred background")
    parser.add_argument("--camera-shake", action="store_true", help="Add subtle camera shake movement")
    parser.add_argument("--motion-bg", action="store_true", help="Force background animation (Zoom/Pan)")
    
    args = parser.parse_args()
    
    # Print header
    print("="*80)
    print(" "*20 + "LOFI YOUTUBE VIDEO GENERATOR")
    print(" "*25 + "Professional 4-Hour Render")
    print("="*80 + "\n")
    
    # Check FFMPEG installation
    print("🔧 Checking FFMPEG installation...")
    if not ffmpeg_utils.check_ffmpeg_installed():
        print("❌ Error: FFMPEG is not installed or not in PATH")
        print("\nPlease install FFMPEG:")
        print("  Windows: choco install ffmpeg  OR  download from ffmpeg.org")
        print("  Linux:   sudo apt install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        print("\nFor detailed instructions, see INSTALLATION.md")
        sys.exit(1)
    print("✅ FFMPEG found\n")
    
    # Validate inputs
    print("📂 Validating input files...")
    if not validate_inputs(args):
        sys.exit(1)
    print("✅ All input files found\n")
    
    # Build and run FFMPEG command
    try:
        # Detect if background is an image
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.svg']
        is_image = Path(args.video).suffix.lower() in image_extensions
        
        # If a background image is provided via --bg-image, override video source (for safety)
        if getattr(args, 'bg_image', None):
            args.video = args.bg_image
            is_image = True

        # Force image mode if motion-bg is requested (enables zoompan)
        if args.motion_bg:
            is_image = True

        cmd = build_ffmpeg_command(args, is_image_override=is_image)
        success = run_ffmpeg(cmd)
        
        if success:
            # Display file info
            output_path = Path(args.output)
            file_size = output_path.stat().st_size / (1024**3)  # GB
            print(f"\n📦 Output file: {args.output}")
            print(f"   Size: {file_size:.2f} GB")
            print("\n🎉 Your 4-hour Lofi video is ready for upload!")
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
