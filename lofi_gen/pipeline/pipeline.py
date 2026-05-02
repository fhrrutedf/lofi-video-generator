"""
LofiGen Pipeline — the ONE canonical pipeline.

Replaces the 3 duplicate pipelines (automation_pipeline.py,
v3_automation_pipeline.py, v4_local_pipeline.py).

Flow:
  1. Analyze theme → ThemeInfo
  2. Obtain music (AI / local / free)
  3. Obtain visuals (images / video / Pexels)
  4. Render video (FFMPEG ping-pong + crossfade)
  5. Process audio (loop + normalize + effects)
  6. Merge audio + video
  7. Optional: text overlay, thumbnail, YouTube upload
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional

from lofi_gen.core.config import GenerationConfig
from lofi_gen.core.types import GenerationResult, ThemeInfo
from lofi_gen.core.logging import get_logger
from lofi_gen.ai.prompt_system import PromptSystem
from lofi_gen.ai.orchestrator import AIOrchestrator
from lofi_gen.media.video_engine import VideoEngine
from lofi_gen.media.audio_engine import AudioEngine
from lofi_gen.media.pexels_client import PexelsClient
from lofi_gen.media.kie_client import KieClient
from lofi_gen.media.free_music import FreeMusicProvider

log = get_logger("pipeline")


class LofiPipeline:
    """
    Single, unified pipeline for lofi video generation.

    Usage:
        config = GenerationConfig(theme="rain", duration=7200)
        pipeline = LofiPipeline(config)
        result = pipeline.run()
    """

    def __init__(self, config: GenerationConfig):
        self.config = config
        self._setup_dirs()

        self.orchestrator = AIOrchestrator(config.ai)
        self.prompt_system = PromptSystem(ai_enhancer=self.orchestrator)
        self.video_engine = VideoEngine(config.video)
        self.audio_engine = AudioEngine(config.audio)
        self.pexels = PexelsClient(config.ai.pexels_api_key)
        self.kie = KieClient(config.ai.kie_api_key)
        self.free_music = FreeMusicProvider(temp_dir=str(self._temp_dir / "music"))

    def run(self) -> GenerationResult:
        """Execute the full pipeline."""
        start_time = time.time()
        log.info("=" * 60)
        log.info("LofiGen Pipeline started: theme=%s, duration=%.0fs", self.config.theme, self.config.duration)

        try:
            theme_info = self._step_analyze_theme()
            log.info("Theme: %s (bpm=%d, mood=%s)", theme_info.name, theme_info.bpm, theme_info.mood)

            music_path = self._step_obtain_music(theme_info)
            if not music_path:
                return GenerationResult(success=False, error="Failed to obtain music")

            visual_paths = self._step_obtain_visuals(theme_info)
            if not visual_paths:
                return GenerationResult(success=False, error="Failed to obtain visuals")

            video_path = self._step_render_video(visual_paths)
            processed_audio = self._step_process_audio(music_path)
            final_path = self._step_merge(video_path, processed_audio)
            final_path = self._step_text_overlay(final_path)

            thumb_path = self._step_thumbnail(final_path, theme_info)
            meta_path = self._step_metadata(theme_info)

            elapsed = time.time() - start_time
            file_size = Path(final_path).stat().st_size / (1024 * 1024) if Path(final_path).exists() else 0

            log.info("Pipeline complete in %.0fs: %s (%.1f MB)", elapsed, final_path, file_size)

            return GenerationResult(
                success=True,
                output_path=final_path,
                music_path=processed_audio,
                video_clip_path=video_path,
                thumbnail_path=thumb_path,
                metadata_path=meta_path,
                duration_seconds=elapsed,
                file_size_mb=file_size,
                theme_info=theme_info,
            )

        except Exception as e:
            log.error("Pipeline failed: %s", e)
            return GenerationResult(success=False, error=str(e))

    # ── Pipeline Steps ──────────────────────────────────────────────────

    def _step_analyze_theme(self) -> ThemeInfo:
        log.info("[Step 1/7] Analyzing theme: %s", self.config.theme)
        return self.prompt_system.generate(self.config.theme)

    def _step_obtain_music(self, theme_info: ThemeInfo) -> Optional[str]:
        log.info("[Step 2/7] Obtaining music")
        if self.config.music_path and Path(self.config.music_path).exists():
            log.info("Using provided music: %s", self.config.music_path)
            return self.config.music_path

        if self.kie.api_key:
            result = self.kie.generate_music(prompt=theme_info.music_prompt, duration=180)
            if result.get("success") and result.get("audio_url"):
                out = str(self._temp_dir / "music" / f"suno_{int(time.time())}.mp3")
                if self.kie.download(result["audio_url"], out):
                    return out

        free = self.free_music.fetch_music(theme_info.name)
        if free:
            return free

        log.error("No music source available")
        return None

    def _step_obtain_visuals(self, theme_info: ThemeInfo) -> list[str]:
        log.info("[Step 3/7] Obtaining visuals")
        if self.config.image_paths:
            valid = [p for p in self.config.image_paths if Path(p).exists()]
            if valid:
                return valid

        if self.config.video_path and Path(self.config.video_path).exists():
            return [self.config.video_path]

        if self.pexels.api_key:
            photo = self.pexels.fetch_photo(theme_info.name, str(self._temp_dir))
            if photo:
                return [photo]
            video = self.pexels.fetch_video(theme_info.name, str(self._temp_dir))
            if video:
                return [video]

        log.error("No visual content available")
        return []

    def _step_render_video(self, visual_paths: list[str]) -> str:
        log.info("[Step 4/7] Rendering video")
        output = str(self._temp_dir / "video.mp4")
        image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        all_images = all(Path(p).suffix.lower() in image_exts for p in visual_paths)

        if all_images and len(visual_paths) > 1:
            duration_per_scene = self.config.duration / len(visual_paths)
            return self.video_engine.create_multi_scene_video(visual_paths, duration_per_scene, output)
        elif all_images:
            return self.video_engine.create_ping_pong_video(visual_paths[0], self.config.duration, output)
        else:
            return self._loop_video_file(visual_paths[0], output)

    def _step_process_audio(self, music_path: str) -> str:
        log.info("[Step 5/7] Processing audio")
        output = str(self._temp_dir / "audio_processed.mp3")

        src_duration = self.audio_engine._get_duration(music_path)
        if src_duration < self.config.duration:
            looped = str(self._temp_dir / "audio_looped.mp3")
            self.audio_engine.loop_audio(music_path, self.config.duration, looped)
            current = looped
        else:
            current = music_path

        if self.config.audio.effects:
            effected = str(self._temp_dir / "audio_effected.mp3")
            self.audio_engine.apply_effects(current, self.config.audio.effects, effected)
            current = effected

        if self.config.ambience_path and Path(self.config.ambience_path).exists():
            mixed = str(self._temp_dir / "audio_mixed.mp3")
            self.audio_engine.mix_ambience(current, self.config.ambience_path, mixed)
            current = mixed

        self.audio_engine.normalize(current, output)
        return output

    def _step_merge(self, video_path: str, audio_path: str) -> str:
        log.info("[Step 6/7] Merging video + audio")
        output = str(self._output_dir / self._output_name)
        return self.video_engine.merge_audio(video_path, audio_path, output)

    def _step_text_overlay(self, video_path: str) -> str:
        if not self.config.quotes:
            return video_path
        log.info("[Step 7/7] Adding text overlay")
        output = video_path.replace(".mp4", "_text.mp4")
        return self.video_engine.add_text_overlay(video_path, self.config.quotes, output_path=output)

    def _step_thumbnail(self, video_path: str, theme_info: ThemeInfo) -> Optional[str]:
        try:
            output = str(self._output_dir / self._output_name.replace(".mp4", "_thumb.jpg"))
            cmd = [
                "ffmpeg", "-y", "-ss", "5", "-i", video_path,
                "-frames:v", "1",
                "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                output,
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output
        except Exception as e:
            log.warning("Thumbnail generation failed: %s", e)
            return None

    def _step_metadata(self, theme_info: ThemeInfo) -> Optional[str]:
        try:
            seo = self.prompt_system.generate_seo_metadata(theme_info, self.config.theme, self.config.duration / 3600)
            if self.orchestrator.active:
                ai_seo = self.orchestrator.generate_seo(self.config.theme, theme_info.mood)
                if ai_seo and ai_seo.get("title"):
                    seo = ai_seo

            output = str(self._output_dir / self._output_name.replace(".mp4", "_meta.txt"))
            with open(output, "w", encoding="utf-8") as f:
                f.write(f"TITLE:\n{seo.get('title', '')}\n\n")
                f.write(f"DESCRIPTION:\n{seo.get('description', '')}\n\n")
                f.write(f"TAGS:\n{seo.get('tags', '')}\n")
            return output
        except Exception as e:
            log.warning("Metadata generation failed: %s", e)
            return None

    # ── Helpers ────────────────────────────────────────────────────────

    def _loop_video_file(self, video_path: str, output_path: str) -> str:
        cmd = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", video_path,
            "-t", str(self.config.duration),
            "-c:v", self.config.video.codec, "-preset", self.config.video.preset,
            "-crf", str(self.config.video.crf), "-pix_fmt", self.config.video.pixel_format,
            "-an", output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Video loop failed: {result.stderr[-300:]}")
        return output_path

    def _setup_dirs(self) -> None:
        self._output_dir = Path(self.config.output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._temp_dir = Path("temp") / f"job_{int(time.time())}"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _output_name(self) -> str:
        if self.config.output_name:
            return self.config.output_name
        safe = "".join(c if c.isalnum() else "_" for c in self.config.theme[:30])
        return f"{safe}_{int(time.time())}.mp4"
