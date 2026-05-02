"""
Kie.ai client — cleaned up from the original.

Fixes:
  - Fixed the broken retry (undefined variables tags, mv, title)
  - Proper error handling
  - Structured logging
  - No dummy callback URLs
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import requests

from lofi_gen.core.logging import get_logger

log = get_logger("kie")

ERROR_MESSAGES: dict[int, str] = {
    400: "Invalid request parameters",
    401: "Invalid API key",
    402: "Credits exhausted — top up your account",
    403: "Access forbidden",
    429: "Rate limit exceeded — wait and retry",
    500: "Kie.ai server error",
    502: "Bad gateway — temporary issue",
    503: "Service unavailable",
}


class KieClient:
    """Client for Kie.ai API (Suno music + Veo video generation)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KIE_API_KEY", "")
        if not self.api_key:
            log.warning("Kie.ai API key not set — AI music/video disabled")
        self.base_url = "https://api.kie.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_music(
        self,
        prompt: str,
        duration: int = 180,
        model: str = "V3_5",
        instrumental: bool = True,
        max_wait: int = 300,
    ) -> dict:
        """Generate music using Suno via Kie.ai."""
        if not self.api_key:
            return {"success": False, "error": "No Kie.ai API key"}

        log.info("Generating music: %s...", prompt[:80])
        payload = {
            "prompt": prompt,
            "instrumental": instrumental,
            "model": model,
            "title": "Lofi Track",
            "style": "lofi hip hop",
            "customMode": False,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=self.headers,
                timeout=30,
            )

            if resp.status_code != 200:
                msg = ERROR_MESSAGES.get(resp.status_code, f"HTTP {resp.status_code}")
                log.error("Music generation failed: %s", msg)
                return {"success": False, "error": msg, "status_code": resp.status_code}

            data = resp.json()
            task_id = data.get("data", {}).get("taskId") or data.get("taskId")

            if not task_id:
                return {"success": False, "error": "No taskId in response"}

            # Poll for completion
            result = self._poll_music(task_id, max_wait)

            # Content filter retry with safe prompt
            if not result.get("success"):
                err = str(result.get("error", "")).lower()
                if any(kw in err for kw in ("artist", "sensitive", "policy", "contain")):
                    log.warning("Content filter triggered, retrying with safe prompt")
                    safe_prompt = "lofi study beats, relaxing piano, ambient atmosphere, instrumental, no lyrics"
                    return self.generate_music(
                        prompt=safe_prompt,
                        duration=duration,
                        model=model,
                        instrumental=True,
                        max_wait=max_wait,
                    )

            return result

        except requests.RequestException as e:
            log.error("Music generation request failed: %s", e)
            return {"success": False, "error": str(e)}

    def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        model: str = "veo3",
        max_wait: int = 600,
    ) -> dict:
        """Generate video animation using Veo via Kie.ai."""
        if not self.api_key:
            return {"success": False, "error": "No Kie.ai API key"}

        log.info("Generating video: %s...", prompt[:80])
        payload = {
            "prompt": prompt,
            "model": model,
            "aspectRatio": "16:9",
            "enableTranslation": True,
        }

        if image_url:
            payload["imageUrls"] = [image_url]
            payload["generationType"] = "FIRST_AND_LAST_FRAMES_2_VIDEO"
        else:
            payload["generationType"] = "TEXT_2_VIDEO"

        try:
            resp = requests.post(
                f"{self.base_url}/veo/generate",
                json=payload,
                headers=self.headers,
                timeout=30,
            )

            if resp.status_code != 200:
                return {"success": False, "error": f"HTTP {resp.status_code}"}

            data = resp.json()
            task_id = data.get("data", {}).get("taskId")
            if not task_id:
                return {"success": False, "error": "No taskId in video response"}

            return self._poll_video(task_id, max_wait)

        except requests.RequestException as e:
            log.error("Video generation failed: %s", e)
            return {"success": False, "error": str(e)}

    def download(self, url: str, output_path: str) -> bool:
        """Download file from URL."""
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            log.info("Downloaded: %s (%.1f MB)", output_path, size_mb)
            return True
        except requests.RequestException as e:
            log.error("Download failed: %s", e)
            return False

    def _poll_music(self, task_id: str, max_wait: int) -> dict:
        """Poll for music generation status."""
        start = time.time()
        while (time.time() - start) < max_wait:
            try:
                resp = requests.get(
                    f"{self.base_url}/generate/record-info",
                    params={"taskId": task_id},
                    headers=self.headers,
                    timeout=30,
                )
                data = resp.json().get("data", {})
                status = data.get("status", "unknown")

                if status == "SUCCESS":
                    tracks = data.get("response", {}).get("sunoData", [])
                    if tracks:
                        return {
                            "success": True,
                            "audio_url": tracks[0].get("audioUrl"),
                            "title": tracks[0].get("title", "Generated Track"),
                        }
                    return {"success": False, "error": "No audio data in response"}

                if status in ("CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "SENSITIVE_WORD_ERROR"):
                    return {"success": False, "error": data.get("errorMessage", status)}

                elapsed = int(time.time() - start)
                log.debug("Music status: %s (%ds elapsed)", status, elapsed)
                time.sleep(10)

            except requests.RequestException as e:
                log.warning("Polling error: %s", e)
                time.sleep(10)

        return {"success": False, "error": "Timeout waiting for music generation"}

    def _poll_video(self, task_id: str, max_wait: int) -> dict:
        """Poll for video generation status."""
        start = time.time()
        while (time.time() - start) < max_wait:
            try:
                resp = requests.get(
                    f"{self.base_url}/veo/record-info",
                    params={"taskId": task_id},
                    headers=self.headers,
                    timeout=30,
                )
                data = resp.json().get("data", {})
                status = data.get("status", "unknown")

                if status == "SUCCESS":
                    video_url = data.get("response", {}).get("videoUrl")
                    if video_url:
                        return {"success": True, "video_url": video_url}
                    return {"success": False, "error": "No video URL in response"}

                if status in ("FAILED", "TASK_ERROR"):
                    return {"success": False, "error": "Video generation failed"}

                elapsed = int(time.time() - start)
                log.debug("Video status: %s (%ds elapsed)", status, elapsed)
                time.sleep(20)

            except requests.RequestException as e:
                log.warning("Video polling error: %s", e)
                time.sleep(20)

        return {"success": False, "error": "Timeout waiting for video generation"}
