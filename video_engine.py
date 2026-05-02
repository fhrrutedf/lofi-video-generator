"""
Lofi Video Processing Engine
============================
MoviePy-based processing engine that solves 4 core technical problems
in lofi video generation:

  1. Visual Loop Glitch  — ping-pong sine-wave zoom (seamless loop)
  2. YouTube Reused Content — multi-scene with crossfade transitions
  3. Static Text          — dynamic quote overlay with fade in/out
  4. Audio Loop Clicks    — seamless audio looping with crossfade

All functions are stateless and designed to be called from any
backend / web interface.  No Flask / FastAPI / GUI code here.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip,
    CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, concatenate_audioclips,
)

# ─── Engine-wide constants ────────────────────────────────────────────
TARGET_WIDTH  = 1920
TARGET_HEIGHT = 1080
TARGET_FPS    = 30

CROSSFADE_DURATION      = 2   # seconds between video scenes
QUOTE_DISPLAY_DURATION  = 10  # seconds each quote is visible
QUOTE_FADE_DURATION     = 1   # seconds for text crossfade in/out
AUDIO_CROSSFADE         = 3   # seconds for audio loop crossfade
MAX_ZOOM                = 1.15  # peak zoom factor (15 % zoom-in)


# ═══════════════════════════════════════════════════════════════════════
# PROBLEM 1: Visual Loop Glitch — Ping-Pong Zoom
# ═══════════════════════════════════════════════════════════════════════

def create_ping_pong_loop(image_path: str,
                          duration: float,
                          fps: int = TARGET_FPS,
                          max_zoom: float = MAX_ZOOM) -> VideoClip:
    """
    Create a seamlessly looping video from a static image using a
    smooth cosine-wave zoom-in / zoom-out (ping-pong) effect.

    The cosine curve guarantees that at t=0 **and** t=duration the
    zoom factor is exactly 1.0, so the first and last frames are
    pixel-identical — no visible glitch when the video loops.

    How it works
    ------------
    1. Pre-render the image at ``target * max_zoom`` resolution so
       that even at peak zoom the crop equals the target size.
       This means we only ever *down-scale*, which is fast and
       high-quality.
    2. For each frame, compute ``zoom = 1 + (max_zoom-1) * 0.5 * (1 - cos(2πt/T))``
       which smoothly goes 1 → max_zoom → 1.
    3. Crop a centered rectangle of size ``target / zoom`` from the
       pre-rendered image, then resize to target dimensions.

    Parameters
    ----------
    image_path : str   — Path to the source image.
    duration   : float — Total clip duration in seconds.
    fps        : int   — Frames per second (default 30).
    max_zoom   : float — Peak zoom factor (default 1.15).

    Returns
    -------
    VideoClip — MoviePy clip with the ping-pong zoom effect.
    """

    # ── 1. Load & pre-render at high resolution ────────────────────
    img = Image.open(image_path).convert("RGB")

    # We need the source to cover target * max_zoom in both axes
    # so that at max zoom the crop is exactly target-sized.
    pre_w = int(TARGET_WIDTH  * max_zoom)
    pre_h = int(TARGET_HEIGHT * max_zoom)

    # Resize to cover the pre-render area (maintain aspect ratio)
    img_ratio     = img.width / img.height
    target_ratio  = pre_w / pre_h

    if img_ratio > target_ratio:
        # Image is wider → fit by height, crop sides
        new_h = pre_h
        new_w = int(pre_h * img_ratio)
    else:
        # Image is taller → fit by width, crop top/bottom
        new_w = pre_w
        new_h = int(pre_w / img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    img_array = np.array(img)  # shape: (new_h, new_w, 3)

    # Center offset for cropping inside the pre-rendered image
    offset_x = (new_w - pre_w) // 2
    offset_y = (new_h - pre_h) // 2

    # ── 2. Frame generator ─────────────────────────────────────────
    def _make_frame(t: float) -> np.ndarray:
        # Cosine ping-pong:  cos(0)=1 → zoom=1
        #                     cos(π)=-1 → zoom=max_zoom
        #                     cos(2π)=1 → zoom=1  (seamless!)
        phase = 2.0 * np.pi * t / duration
        zoom  = 1.0 + (max_zoom - 1.0) * 0.5 * (1.0 - np.cos(phase))

        # Crop region (centered) — at zoom=1 this is the full
        # pre-rendered area; at max_zoom it shrinks to target size.
        crop_w = int(TARGET_WIDTH  / zoom)
        crop_h = int(TARGET_HEIGHT / zoom)

        cx = new_w // 2
        cy = new_h // 2

        x1 = max(0, cx - crop_w // 2)
        y1 = max(0, cy - crop_h // 2)
        x2 = min(new_w, x1 + crop_w)
        y2 = min(new_h, y1 + crop_h)

        cropped = img_array[y1:y2, x1:x2]

        # Resize to exact target dimensions (always down-scale → fast)
        pil_crop  = Image.fromarray(cropped)
        pil_final = pil_crop.resize((TARGET_WIDTH, TARGET_HEIGHT),
                                    Image.LANCZOS)
        return np.array(pil_final)

    clip = VideoClip(make_frame=_make_frame, duration=duration)
    clip = clip.set_fps(fps)
    return clip


# ═══════════════════════════════════════════════════════════════════════
# PROBLEM 2: YouTube Reused Content — Multi-Scene with Crossfade
# ═══════════════════════════════════════════════════════════════════════

def build_multi_scene_video(image_paths_list: list,
                            duration_per_scene: float,
                            fps: int = TARGET_FPS) -> VideoClip:
    """
    Build a multi-scene video from a list of images, applying the
    ping-pong zoom to each scene and blending them with a
    2-second crossfade transition.

    The crossfade makes each scene visually distinct, which helps
    bypass YouTube's "reused content" detection algorithm.

    Total duration
    --------------
    With *n* images the output duration is::

        n * duration_per_scene  -  (n-1) * CROSSFADE_DURATION

    because each overlap removes CROSSFADE_DURATION seconds.

    Parameters
    ----------
    image_paths_list  : list  — List of image file paths.
    duration_per_scene: float — Duration of each scene in seconds.
    fps               : int   — Frames per second (default 30).

    Returns
    -------
    VideoClip — Single concatenated clip with crossfade transitions.
    """

    if not image_paths_list:
        raise ValueError("image_paths_list must contain at least one image")

    scene_clips = []
    for path in image_paths_list:
        # Apply ping-pong zoom to each image
        clip = create_ping_pong_loop(path, duration_per_scene, fps=fps)

        # Crossfade in/out so the tail of scene N blends with
        # the head of scene N+1 when they overlap.
        clip = clip.crossfadein(CROSSFADE_DURATION)
        clip = clip.crossfadeout(CROSSFADE_DURATION)
        scene_clips.append(clip)

    # Negative padding → clips overlap by CROSSFADE_DURATION seconds.
    # method="compose" uses CompositeVideoClip internally so the
    # crossfade effects blend the overlapping regions smoothly.
    final = concatenate_videoclips(
        scene_clips,
        method="compose",
        padding=-CROSSFADE_DURATION,
    )
    final = final.set_fps(fps)
    return final


# ═══════════════════════════════════════════════════════════════════════
# PROBLEM 3: Static Text — Dynamic Quote Overlay
# ═══════════════════════════════════════════════════════════════════════

def _render_quote_frame(quote: str,
                        width: int,
                        height: int,
                        font_size: int = 40) -> np.ndarray:
    """
    Render a single RGBA frame containing the quote text centered
    over a semi-transparent black box, using PIL (no ImageMagick).

    Returns
    -------
    np.ndarray — RGBA image of shape (height, width, 4).
    """
    img  = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load font — try common paths, fall back to default bitmap font
    font = None
    for font_path in ("arial.ttf",
                      "C:/Windows/Fonts/arial.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                      "/System/Library/Fonts/Helvetica.ttc"):
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    # ── Word-wrap to 80 % of frame width ──────────────────────────
    max_text_w = int(width * 0.8)
    words   = quote.split()
    lines   = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_text_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    # ── Measure every line ─────────────────────────────────────────
    line_sizes = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_sizes.append((bbox[2] - bbox[0], bbox[3] - bbox[1]))

    line_spacing   = 12
    total_text_h   = sum(s[1] for s in line_sizes) + line_spacing * (len(lines) - 1)
    max_line_w     = max(s[0] for s in line_sizes)

    # ── Semi-transparent background box ────────────────────────────
    pad    = 24
    box_x1 = (width  - max_line_w)  // 2 - pad
    box_y1 = (height - total_text_h) // 2 - pad
    box_x2 = (width  + max_line_w)  // 2 + pad
    box_y2 = (height + total_text_h) // 2 + pad
    draw.rectangle([box_x1, box_y1, box_x2, box_y2],
                   fill=(0, 0, 0, 140))  # ~55 % opacity

    # ── Draw each line of text ─────────────────────────────────────
    text_y = box_y1 + pad
    for i, line in enumerate(lines):
        lw     = line_sizes[i][0]
        text_x = (width - lw) // 2
        draw.text((text_x, text_y), line,
                  fill=(255, 255, 255, 255), font=font)
        text_y += line_sizes[i][1] + line_spacing

    return np.array(img)


def overlay_dynamic_text(video_clip: VideoClip,
                         quotes_list: list) -> CompositeVideoClip:
    """
    Overlay a list of quotes onto a video clip.  Each quote is shown
    for 10 seconds with 1-second crossfade in/out so text never
    appears or disappears abruptly.

    Text is rendered with PIL (no ImageMagick dependency) and placed
    at the center of the frame over a semi-transparent black box for
    readability on any background.

    Parameters
    ----------
    video_clip  : VideoClip — Base video (e.g. from build_multi_scene_video).
    quotes_list : list      — List of quote strings.

    Returns
    -------
    CompositeVideoClip — Video with text overlays composited on top.
    """

    w, h = video_clip.size
    text_clips = []

    for i, quote in enumerate(quotes_list):
        start_t = i * QUOTE_DISPLAY_DURATION

        # Don't add quotes that would start after the video ends
        if start_t >= video_clip.duration:
            break

        # Render the quote as an RGBA image via PIL
        rgba = _render_quote_frame(quote, w, h)

        # ImageClip auto-detects the alpha channel from the RGBA array
        # and creates a mask, so compositing works out of the box.
        txt_clip = (ImageClip(rgba)
                    .set_duration(QUOTE_DISPLAY_DURATION)
                    .set_start(start_t)
                    .set_position("center")
                    .crossfadein(QUOTE_FADE_DURATION)
                    .crossfadeout(QUOTE_FADE_DURATION))

        text_clips.append(txt_clip)

    return CompositeVideoClip([video_clip] + text_clips, size=(w, h))


# ═══════════════════════════════════════════════════════════════════════
# PROBLEM 4: Audio Loop Clicks — Seamless Audio Looping
# ═══════════════════════════════════════════════════════════════════════

def loop_audio_seamlessly(audio_path: str,
                          target_duration: float) -> AudioFileClip:
    """
    Loop an audio file to fill the target duration with seamless
    crossfades at every loop junction so there are no audible clicks
    or pops.

    Strategy
    --------
    At each junction the tail of the outgoing clip fades out over
    3 seconds while the head of the incoming clip fades in over the
    same period.  The clips are concatenated with **negative padding**
    equal to the crossfade duration so the fade-out and fade-in
    overlap perfectly, producing a smooth crossfade.

    Parameters
    ----------
    audio_path      : str   — Path to the source audio file.
    target_duration : float — Desired total audio length in seconds.

    Returns
    -------
    AudioClip — Looped audio trimmed to exactly ``target_duration``.
    """

    original = AudioFileClip(audio_path)
    src_dur  = original.duration

    if src_dur <= 0:
        raise ValueError(f"Audio file has invalid duration: {src_dur}")

    # Close the probe clip — we'll re-read from disk for each loop
    # to avoid shared-object issues inside MoviePy.
    original.close()

    # How many full copies we need (ceiling to guarantee coverage)
    num_loops = math.ceil(target_duration / src_dur)

    # Build individual loop copies with crossfade at junctions
    audio_clips = []
    for i in range(num_loops):
        # Re-read from disk each time to avoid shared-state bugs
        clip = AudioFileClip(audio_path)

        # Every clip fades out at its tail …
        clip = clip.audio_fadeout(AUDIO_CROSSFADE)

        # … and every clip *after the first* fades in at its head
        if i > 0:
            clip = clip.audio_fadein(AUDIO_CROSSFADE)

        audio_clips.append(clip)

    # Negative padding = overlap by AUDIO_CROSSFADE seconds.
    # The fade-out of clip N overlaps with the fade-in of clip N+1,
    # producing a smooth crossfade instead of a hard cut / click.
    looped = concatenate_audioclips(audio_clips,
                                    padding=-AUDIO_CROSSFADE)

    # Trim to exact target duration
    if looped.duration > target_duration:
        looped = looped.subclip(0, target_duration)

    return looped
