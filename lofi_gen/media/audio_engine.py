"""
Audio Engine — seamless audio looping with crossfade.

Fixes the "click" problem at loop junctions by using
FFMPEG's acrossfade filter with proper overlap.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from lofi_gen.core.config import AudioConfig
from lofi_gen.core.logging import get_logger

log = get_logger("audio_engine")


class AudioEngine:
    """
    Audio processing engine using FFMPEG.

    Handles:
      - Seamless audio looping with crossfade
      - Audio normalization
      - Audio effects (reverb, vinyl, etc.)
      - Ambience mixing
    """

    def __init__(self, config: AudioConfig):
        self.config = config

    def loop_audio(
        self,
        audio_path: str,
        target_duration: float,
        output_path: str,
    ) -> str:
        """
        Loop audio to target duration with seamless crossfade at junctions.

        Strategy: Use FFMPEG's -stream_loop with a short crossfade
        at the loop boundary to eliminate clicks.
        """
        # Get source duration
        src_duration = self._get_duration(audio_path)
        if src_duration <= 0:
            raise ValueError(f"Cannot determine duration of {audio_path}")

        # If source is already long enough, just trim
        if src_duration >= target_duration:
            return self._trim(audio_path, target_duration, output_path)

        # Calculate how many loops we need
        loops_needed = int(target_duration / src_duration) + 1
        crossfade = min(self.config.crossfade_duration, src_duration / 4)

        # Build looped audio with crossfade at junctions
        # Use concat demuxer with crossfade for seamless looping
        temp_dir = Path(output_path).parent / "_audio_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Create fade-out version and fade-in version
        fade_out_path = str(temp_dir / "fade_out.mp3")
        fade_in_path = str(temp_dir / "fade_in.mp3")

        self._apply_fade(audio_path, fade_out_path, fade_out=crossfade)
        self._apply_fade(audio_path, fade_in_path, fade_in=crossfade)

        # Step 2: Concatenate with crossfade using acrossfade filter
        # Build the chain: fade_out + fade_in crossfaded, repeated
        current_path = fade_out_path
        accumulated_duration = src_duration

        while accumulated_duration < target_duration:
            next_path = str(temp_dir / f"loop_{accumulated_duration:.0f}.mp3")
            remaining = target_duration - accumulated_duration

            # Crossfade current with next segment
            self._crossfade(
                current_path,
                fade_in_path if remaining > src_duration else audio_path,
                next_path,
                crossfade,
            )
            current_path = next_path
            accumulated_duration += src_duration - crossfade

        # Step 3: Trim to exact target duration
        self._trim(current_path, target_duration, output_path)

        # Cleanup
        for f in temp_dir.iterdir():
            f.unlink(missing_ok=True)
        temp_dir.rmdir()

        log.info(
            "Looped audio: %.1fs → %.1fs (%d loops, %.1fs crossfade)",
            src_duration, target_duration, loops_needed, crossfade,
        )
        return output_path

    def mix_ambience(
        self,
        music_path: str,
        ambience_path: str,
        output_path: str,
        ambience_volume: Optional[float] = None,
    ) -> str:
        """Mix ambience sounds with music at specified volume."""
        vol = ambience_volume or self.config.ambience_volume

        cmd = [
            "ffmpeg", "-y",
            "-i", music_path,
            "-i", ambience_path,
            "-filter_complex",
            f"[1:a]volume={vol}[amb];[0:a][amb]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "[aout]",
            "-c:a", self.config.codec,
            "-b:a", self.config.bitrate,
            output_path,
        ]

        log.info("Mixing ambience at %.0f%% volume", vol * 100)
        self._run_ffmpeg(cmd)
        return output_path

    def apply_effects(
        self,
        audio_path: str,
        effects: list[str],
        output_path: str,
    ) -> str:
        """Apply audio effects (reverb, vinyl, etc.)."""
        if not effects:
            return audio_path

        filters = []
        for effect in effects:
            if effect == "reverb":
                filters.append("aecho=0.8:0.88:60:0.4")
            elif effect == "vinyl":
                filters.append("atempo=0.998,lowpass=f=8000,volume=0.95")
            elif effect == "bass_boost":
                filters.append("bass=g=5:f=100:t=q")

        if not filters:
            return audio_path

        af = ",".join(filters)
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-af", af,
            "-c:a", self.config.codec,
            "-b:a", self.config.bitrate,
            output_path,
        ]

        log.info("Applying audio effects: %s", effects)
        self._run_ffmpeg(cmd)
        return output_path

    def normalize(self, audio_path: str, output_path: str) -> str:
        """Normalize audio levels for YouTube (EBU R128)."""
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-af", "loudnorm=I=-14:TP=-2:LRA=11",
            "-c:a", self.config.codec,
            "-b:a", self.config.bitrate,
            output_path,
        ]

        log.info("Normalizing audio")
        self._run_ffmpeg(cmd)
        return output_path

    # ── Private helpers ─────────────────────────────────────────────────

    def _apply_fade(
        self,
        input_path: str,
        output_path: str,
        fade_in: float = 0,
        fade_out: float = 0,
    ) -> None:
        """Apply fade in/out to audio."""
        af_parts = []
        if fade_in > 0:
            af_parts.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            duration = self._get_duration(input_path)
            af_parts.append(f"afade=t=out:st={duration - fade_out}:d={fade_out}")

        if not af_parts:
            return

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", ",".join(af_parts),
            "-c:a", self.config.codec,
            "-b:a", self.config.bitrate,
            output_path,
        ]
        self._run_ffmpeg(cmd)

    def _crossfade(
        self,
        first_path: str,
        second_path: str,
        output_path: str,
        crossfade_duration: float,
    ) -> None:
        """Crossfade two audio files using acrossfade filter."""
        cmd = [
            "ffmpeg", "-y",
            "-i", first_path,
            "-i", second_path,
            "-filter_complex",
            f"[0:a][1:a]acrossfade=d={crossfade_duration}:c1=tri:c2=tri[aout]",
            "-map", "[aout]",
            "-c:a", self.config.codec,
            "-b:a", self.config.bitrate,
            output_path,
        ]
        self._run_ffmpeg(cmd)

    def _trim(self, input_path: str, duration: float, output_path: str) -> str:
        """Trim audio to exact duration."""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(duration),
            "-c:a", self.config.codec,
            "-b:a", self.config.bitrate,
            output_path,
        ]
        self._run_ffmpeg(cmd)
        return output_path

    @staticmethod
    def _get_duration(path: str) -> float:
        """Get audio/video duration using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return float(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError):
            return 0.0

    @staticmethod
    def _run_ffmpeg(cmd: list[str]) -> None:
        """Execute FFMPEG command with error handling."""
        log.debug("FFMPEG: %s", " ".join(cmd[:6]) + "...")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if result.returncode != 0:
                raise RuntimeError(f"FFMPEG error: {result.stderr[-300:]}")
        except FileNotFoundError:
            raise RuntimeError("FFMPEG not found. Install from https://ffmpeg.org")
