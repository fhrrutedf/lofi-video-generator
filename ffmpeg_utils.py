"""
FFMPEG utility functions for video processing
"""

import re
import subprocess
import math
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
import config


def check_ffmpeg_installed() -> bool:
    """Check if FFMPEG is installed and accessible"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_media_duration(file_path: str) -> float:
    """Get duration of media file in seconds using ffprobe"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise RuntimeError(f"Failed to get duration of {file_path}: {e}")


def calculate_loop_count(source_duration: float, target_duration: float) -> int:
    """Calculate how many times to loop a source to reach target duration"""
    # -stream_loop N means loop N+1 times total, so we need loops-1
    loops_needed = math.ceil(target_duration / source_duration)
    return loops_needed - 1


def build_audio_filter(
    music_duration: float,
    has_ambience: bool = False,
    ambience_duration: Optional[float] = None,
    effects: Optional[list] = None
) -> str:
    """
    Build audio filter chain with optional cinematic effects (reverb, vinyl, etc.)
    """
    target_duration = config.OUTPUT_DURATION
    fade_out_start = target_duration - config.FADE_OUT_DURATION
    
    filters = []
    
    # Base Music processing (Input 0)
    music_filter = f"[0:a]afade=t=in:st=0:d={config.FADE_IN_DURATION},"
    
    # Add Space Reverb if needed
    if effects and "reverb" in effects:
        music_filter += "aecho=0.8:0.88:60:0.4,"
    
    # Add Vintage Vinyl Cracks if needed
    if effects and "vinyl" in effects:
        music_filter += "highpass=f=200,lowpass=f=3500,"
        
    music_filter += f"afade=t=out:st={fade_out_start}:d={config.FADE_OUT_DURATION}[music_faded]"
    filters.append(music_filter)
    
    # Combine sources
    if has_ambience:
        # Ambience track (Input 1)
        ambience_filter = f"[1:a]volume={config.AMBIENCE_VOLUME}[ambience]"
        filters.append(ambience_filter)
        
        # Mix both audio streams
        mix_filter = f"[music_faded][ambience]amix=inputs=2:duration=first[mixed]"
        filters.append(mix_filter)
        current_audio = "[mixed]"
    else:
        current_audio = "[music_faded]"
    
    # --- PROFESSIONAL AUDIO MASTERING ---
    # Add a limiter and compressor to ensure professional loudness and prevent clipping
    # 'alimiter' ensures peaks do not exceed -0.1dB
    # 'acompressor' adds subtle punch
    mastering_filter = f"{current_audio}acompressor=threshold=-12dB:ratio=2:attack=5:release=50,alimiter=limit=0.95[aout]"
    filters.append(mastering_filter)
    
    return ";".join(filters)


def build_video_filter(
    video_index: int,
    has_logo: bool = False,
    logo_index: Optional[int] = None,
    has_film_grain: bool = False,
    mood: Optional[str] = None,
    has_pomodoro: bool = False,
    evolving: bool = False,
    glitch: bool = False,
    speed: float = 1.0,
    is_image: bool = False,
    has_rain: bool = False,
    has_fog: bool = False,
    has_particles: bool = False,
    has_breathing: bool = False,
    has_vignette: bool = False,
    has_letterbox: bool = False,
    has_blur_bg: bool = False,
    has_camera_shake: bool = False
) -> str:
    """
    Build video filter chain for scaling, logo overlay, film grain, and color grading
    
    Returns: Complex filter string for video processing
    """
    filters = []
    # current_label tracks the name of the last output label (without brackets)
    current_label = f"{video_index}:v"
    
    # 1. Image Animation (Ken Burns Effect) if input is image
    if is_image:
        zoom_filter = (
            "zoompan=z='min(zoom+0.0005,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=hd1080:fps=30"
        )
        filters.append(f"[{current_label}]{zoom_filter}[animated]")
        current_label = "animated"

    # 2. Speed, Scaling & Smart Background
    speed_filter = f"setpts={1.0/speed}*PTS"
    
    if has_blur_bg:
        blur_chain = (
            f"split[main][bg];"
            f"[bg]scale={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT},boxblur=20:10[blurred];"
            f"[main]scale={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease[foreground];"
            f"[blurred][foreground]overlay=(W-w)/2:(H-h)/2"
        )
        filters.append(f"[{current_label}]{speed_filter},{blur_chain}[scaled_v]")
    else:
        # Standard scaling with padding (black bars)
        scale_filter = f"[{current_label}]{speed_filter},scale={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,pad={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2[scaled_v]"
        filters.append(scale_filter)
    
    current_label = "scaled_v"
    
    # 🎥 PROFESSIONAL VIGNETTE
    if has_vignette:
        filters.append(f"[{current_label}]vignette=angle=0.3[vignetted]")
        current_label = "vignetted"

    # 🎬 LETTERBOX (Cinematic Bars)
    if has_letterbox:
        lb_h = config.OUTPUT_HEIGHT // 10
        filters.append(
            f"[{current_label}]drawbox=y=0:h={lb_h}:color=black:t=fill,"
            f"drawbox=y=ih-{lb_h}:h={lb_h}:color=black:t=fill[letterboxed]"
        )
        current_label = "letterboxed"

    if evolving:
        total_s = config.OUTPUT_DURATION
        evolve_expr = f"eq=brightness=-0.15*t/{total_s}:saturation=1.0-0.3*t/{total_s}:gamma=1.0-0.2*t/{total_s}"
        filters.append(f"[{current_label}]{evolve_expr}[evolved]")
        current_label = "evolved"

    # 👾 GENERATIVE GLITCH
    if glitch:
        glitch_expr = "rgbashift=rh='if(gt(sin(t*0.02),0.98),5,0)':bh='if(gt(sin(t*0.021),0.98),-5,0)'"
        filters.append(f"[{current_label}]{glitch_expr}[glitched]")
        current_label = "glitched"
    
    # 🎨 MOOD-BASED COLOR GRADING
    if mood:
        if mood == "cozy":
            grade = "colorbalance=rm=0.1:gm=0.05:bm=-0.05,eq=gamma=1.1:saturation=1.1"
        elif mood == "sad" or mood == "melancholy":
            grade = "colorbalance=bm=0.15:rm=-0.05:gm=-0.05,eq=saturation=0.8:brightness=-0.05"
        elif mood == "dreamy" or mood == "ethereal":
            grade = "eq=gamma=1.2:contrast=0.9,colorbalance=bm=0.05:rm=0.05"
        elif mood == "clean" or mood == "productive":
            grade = "eq=contrast=1.2:saturation=1.2"
        else:
            grade = "copy"
            
        filters.append(f"[{current_label}]{grade}[graded]")
        current_label = "graded"
    
    # Add film grain
    if has_film_grain:
        filters.append(f"[{current_label}]noise=alls={config.FILM_GRAIN_STRENGTH}:allf=t[grained]")
        current_label = "grained"
    
    # Add logo overlay
    if has_logo and logo_index is not None:
        if config.LOGO_POSITION == "top-right":
            position = f"W-w-{config.LOGO_MARGIN}:{config.LOGO_MARGIN}"
        elif config.LOGO_POSITION == "top-left":
            position = f"{config.LOGO_MARGIN}:{config.LOGO_MARGIN}"
        elif config.LOGO_POSITION == "bottom-right":
            position = f"W-w-{config.LOGO_MARGIN}:H-h-{config.LOGO_MARGIN}"
        elif config.LOGO_POSITION == "bottom-left":
            position = f"{config.LOGO_MARGIN}:H-h-{config.LOGO_MARGIN}"
        else:
            position = f"W-w-{config.LOGO_MARGIN}:{config.LOGO_MARGIN}"
        
        overlay_filter = f"[{current_label}][{logo_index}:v]format=rgba,colorchannelmixer=aa={config.LOGO_OPACITY}[logo_alpha];[logo_alpha]overlay={position}:format=auto[logo_out]"
        filters.append(overlay_filter)
        current_label = "logo_out"
        
    # 🌧️ VISUAL RAIN EFFECT
    if has_rain:
        filters.append(
            f"[{current_label}]split[v_orig][v_noise];"
            f"[v_noise]noise=c0s=80:c0f=t+u,hue=s=0,eq=brightness=-0.2:contrast=1.5,gblur=sigma=2:steps=1,scale=w=iw/10:h=ih,scale=w=1920:h=1080,"
            f"format=rgba,negate,colorkey=black:0.1:0.1,colorchannelmixer=aa=0.3[v_streaks_alpha];"
            f"[v_orig][v_streaks_alpha]overlay=0:0:format=auto[rained]"
        )
        current_label = "rained"

    # 🌫️ MOVING FOG/MIST EFFECT
    if has_fog:
        filters.append(
            f"[{current_label}]split[v_base][v_cloud];"
            f"[v_cloud]noise=c0s=50:c0f=t,gblur=sigma=10:steps=3,scale=w=iw:h=ih,format=rgba,colorkey=black:0.5:0.5,colorchannelmixer=aa=0.15[v_mist_alpha];"
            f"[v_base][v_mist_alpha]overlay='W*sin(t*0.1)':0:format=auto[foggy]"
        )
        current_label = "foggy"

    # ❄️ FLOATING PARTICLES
    if has_particles:
        filters.append(
            f"[{current_label}]split[v_pbase][v_pnoise];"
            f"[v_pnoise]noise=c0s=100:c0f=t+u,hue=s=0,eq=brightness=-0.3:contrast=2.0,gblur=sigma=1,"
            f"format=rgba,colorkey=black:0.2:0.2,colorchannelmixer=aa=0.4[v_pts_alpha];"
            f"[v_pbase][v_pts_alpha]overlay='100*sin(t*0.5)':'50*t':format=auto[particles]"
        )
        current_label = "particles"

    # 💨 BREATHING EFFECT
    if has_breathing:
        breath_expr = "zoompan=z='1.01+0.01*sin(t*0.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=hd1080:fps=30"
        filters.append(f"[{current_label}]{breath_expr}[breathing]")
        current_label = "breathing"

    # 📳 SUBTLE CAMERA SHAKE
    if has_camera_shake:
        shake_expr = (
            f"scale=1.05*iw:-1,"
            f"crop=iw/1.05:ih/1.05:"
            f"(iw-ow)/2+5*sin(t*0.7)+2*sin(t*1.3):"
            f"(ih-oh)/2+4*sin(t*0.8)+3*sin(t*1.1)"
        )
        filters.append(f"[{current_label}]{shake_expr}[shaken]")
        current_label = "shaken"
        
    # ⏱️ POMODORO TIMER OVERLAY
    if has_pomodoro:
        # Resolve absolute path for temp/arial.ttf to satisfy FFmpeg on Windows
        # Use simple forward slash path relative to current drive if possible
        os.makedirs("temp", exist_ok=True)
        local_font_abs = os.path.abspath("temp/arial.ttf")
        
        system_font = r"C:\Windows\Fonts\arial.ttf"
        
        # Try to copy font if it doesn't exist
        if not os.path.exists(local_font_abs):
            try:
                if os.path.exists(system_font):
                    shutil.copy(system_font, local_font_abs)
                else:
                    print(f"⚠️ System font not found at {system_font}")
            except Exception as e:
                print(f"⚠️ Failed to copy font: {e}")

        # Get safe path for FFMPEG
        if os.path.exists(local_font_abs):
             font_path = local_font_abs.replace("\\", "/")
        else:
             font_path = "C:/Windows/Fonts/arial.ttf"

        # Define text settings using the absolute font path
        # Note: 'fontfile' parameter avoids Fontconfig dependency
        # We also need to escape colon after drive letter if it happens to be interpreted oddly,
        # but inside single quotes it is usually fine.
        timer_settings = f"fontfile='{font_path}':fontcolor=white:fontsize=80:x=50:y=110:box=1:boxcolor=black@0.5:boxborderw=10"
        title_settings = f"fontfile='{font_path}':fontcolor=white:fontsize=40:x=50:y=50:box=1:boxcolor=black@0.5:boxborderw=10"
        
        # Timer Expressions
        focus_timer_text = "%{eif:floor((1500-mod(t,1800))/60):d:2}:%{eif:mod(1500-mod(t,1800),60):d:2}"
        break_timer_text = "%{eif:floor((1800-mod(t,1800))/60):d:2}:%{eif:mod(1800-mod(t,1800),60):d:2}"

        filters.append(
            f"[{current_label}]drawtext=text='FOCUS':enable='lt(mod(t,1800),1500)':{title_settings}[p1]"
        )
        filters.append(
            f"[p1]drawtext=text='{focus_timer_text}':enable='lt(mod(t,1800),1500)':{timer_settings}[p2]"
        )
        filters.append(
            f"[p2]drawtext=text='BREAK':enable='gte(mod(t,1800),1500)':{title_settings}[p3]"
        )
        filters.append(
            f"[p3]drawtext=text='{break_timer_text}':enable='gte(mod(t,1800),1500)':{timer_settings}[timed]"
        )
        current_label = "timed"
    
    # Final output
    filters.append(f"[{current_label}]copy[vout]")
    
    return ";".join(filters) if filters else ""


def parse_progress(line: str) -> Optional[float]:
    """
    Parse FFMPEG output line to extract current time position
    Returns time in seconds or None if not found
    """
    # FFMPEG outputs progress like: frame= 1234 fps= 30 time=00:01:23.45 ...
    time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
    if time_match:
        hours, minutes, seconds = time_match.groups()
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return total_seconds
    return None


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
