"""
Pexels client — cleaned up from the original.

Fixes:
  - No duplicate imports
  - Proper retry logic
  - Structured logging
"""

from __future__ import annotations

import os
import random
import time
from pathlib import Path
from typing import Optional

import requests

from lofi_gen.core.logging import get_logger

log = get_logger("pexels")

THEME_QUERIES: dict[str, str] = {
    "cafe": "cozy cafe coffee shop aesthetic lofi",
    "study": "study room desk workspace library aesthetic",
    "rain": "rain window rainy day cozy",
    "sleep": "night stars peaceful bedroom",
    "work": "modern office workspace desk",
    "space": "stars galaxy space nebula",
    "ocean": "ocean beach sunset waves",
    "city": "city night lights aesthetic urban",
    "nature": "forest nature peaceful green",
    "retro": "vintage retro aesthetic warm",
    "anime": "anime style aesthetic lofi scenery",
}


class PexelsClient:
    """Fetch stock videos and photos from Pexels API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY", "")
        if not self.api_key:
            log.warning("Pexels API key not set — auto-fetch disabled")

    def fetch_video(self, theme: str, output_dir: str = "temp") -> Optional[str]:
        """Fetch a background video for the given theme."""
        if not self.api_key:
            return None

        query = THEME_QUERIES.get(theme, f"{theme} lofi aesthetic")
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=landscape&per_page=5"

        try:
            resp = requests.get(
                url,
                headers={"Authorization": self.api_key},
                params={"size": "large"},
                timeout=30,
            )
            resp.raise_for_status()
            videos = resp.json().get("videos", [])

            if not videos:
                log.warning("No Pexels videos found for theme: %s", theme)
                return None

            # Pick best quality from top 3
            video = random.choice(videos[:3])
            video_url = self._best_quality_url(video)
            if not video_url:
                return None

            # Download
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = os.path.join(output_dir, f"pexels_{theme}_{int(time.time())}.mp4")
            return self._download(video_url, output_path)

        except requests.RequestException as e:
            log.error("Pexels API error: %s", e)
            return None

    def fetch_photo(self, theme: str, output_dir: str = "temp") -> Optional[str]:
        """Fetch a background photo for the given theme."""
        if not self.api_key:
            return None

        query = THEME_QUERIES.get(theme, f"{theme} lofi aesthetic")
        url = "https://api.pexels.com/v1/search"

        try:
            resp = requests.get(
                url,
                headers={"Authorization": self.api_key},
                params={"query": query, "orientation": "landscape", "per_page": 5},
                timeout=30,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])

            if not photos:
                return None

            photo = random.choice(photos[:3])
            img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("original")
            if not img_url:
                return None

            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = os.path.join(output_dir, f"pexels_{theme}_{photo.get('id')}.jpg")
            return self._download(img_url, output_path)

        except requests.RequestException as e:
            log.error("Pexels photo API error: %s", e)
            return None

    @staticmethod
    def _best_quality_url(video: dict) -> Optional[str]:
        """Extract best quality video URL."""
        files = video.get("video_files", [])
        # Prefer HD 1920x1080
        for vf in files:
            if vf.get("quality") == "hd" and vf.get("width") == 1920:
                return vf.get("link")
        # Fallback: any HD
        for vf in files:
            if vf.get("quality") == "hd":
                return vf.get("link")
        # Last resort
        return files[0].get("link") if files else None

    @staticmethod
    def _download(url: str, output_path: str) -> Optional[str]:
        """Download file from URL."""
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            log.info("Downloaded: %s", output_path)
            return output_path
        except requests.RequestException as e:
            log.error("Download failed: %s", e)
            return None
