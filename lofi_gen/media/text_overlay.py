"""
Text overlay with RTL/Arabic support.

Uses PIL/Pillow for proper text rendering with Arabic reshaping.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

from lofi_gen.core.logging import get_logger

log = get_logger("text_overlay")


def reshape_arabic(text: str) -> str:
    """Reshape Arabic text for proper display."""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def is_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return any("\u0600" <= c <= "\u06FF" or "\u0750" <= c <= "\u077F" for c in text)


def create_text_frame(
    width: int,
    height: int,
    text: str,
    font_size: int = 48,
    text_color: tuple = (255, 255, 255),
    bg_opacity: int = 128,
) -> Image.Image:
    """
    Create a transparent PNG with text overlay.
    
    Supports Arabic text with proper reshaping.
    """
    # Create transparent image
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Prepare text
    if is_arabic(text):
        display_text = reshape_arabic(text)
    else:
        display_text = text
    
    # Try to find a suitable font
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arial.ttf",  # Windows
        "C:/Windows/Fonts/segoeui.ttf",  # Windows alternative
    ]
    
    font = None
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # Calculate text size
    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center position
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw background box
    padding = 20
    box_coords = [
        x - padding,
        y - padding,
        x + text_width + padding,
        y + text_height + padding
    ]
    draw.rectangle(box_coords, fill=(0, 0, 0, bg_opacity))
    
    # Draw text with shadow
    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), display_text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), display_text, font=font, fill=text_color)
    
    return img


def add_text_overlay_pillow(
    video_path: str,
    text: str,
    output_path: str,
    start_time: float = 0,
    duration: float = 10,
    fps: int = 30,
) -> str:
    """
    Add text overlay to video using PIL for text generation + FFmpeg overlay.
    
    This supports Arabic/RTL text properly.
    """
    # Get video dimensions
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path
    ]
    
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        width, height = map(int, result.stdout.strip().split("x"))
    except:
        width, height = 1920, 1080
    
    # Create text frame
    text_img = create_text_frame(width, height, text)
    
    # Save temporary overlay
    temp_dir = Path(output_path).parent
    overlay_path = str(temp_dir / f"overlay_{hash(text)}.png")
    text_img.save(overlay_path)
    
    # Build FFmpeg command with overlay
    # Enable overlay at start_time for duration
    enable_expr = f"between(t,{start_time},{start_time + duration})"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", overlay_path,
        "-filter_complex",
        f"[1:v]format=rgba[ovr];[0:v][ovr]overlay=0:0:enable='{enable_expr}'[v]",
        "-map", "[v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Cleanup temp overlay
        Path(overlay_path).unlink(missing_ok=True)
        return output_path
    except subprocess.CalledProcessError as e:
        log.error("Text overlay failed: %s", e.stderr[-300:])
        raise RuntimeError(f"Text overlay failed: {e.stderr[-200:]}")


def wrap_text_arabic(text: str, max_chars: int = 30) -> list[str]:
    """Wrap Arabic/English text into lines."""
    words = text.split()
    lines = []
    current = ""
    
    for word in words:
        test = f"{current} {word}".strip()
        if len(test) <= max_chars:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    
    if current:
        lines.append(current)
    
    return lines
