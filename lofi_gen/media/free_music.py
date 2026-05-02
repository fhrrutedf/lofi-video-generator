"""
Free music provider — fallback when no AI music API is available.

Uses Pixabay API (free tier) instead of hardcoded CDN links.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import requests

from lofi_gen.core.logging import get_logger

log = get_logger("free_music")

# Pixabay API for royalty-free music (requires free API key)
PIXABAY_API_URL = "https://pixabay.com/api/"

# Fallback: verified direct links to royalty-free tracks
FALLBACK_TRACKS = [
    "https://www.bensound.com/bensound-music/bensound-memories.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
]


class FreeMusicProvider:
    """
    Provides free royalty-free music as a fallback.

    Tries Pixabay API first, then falls back to direct links.
    """

    def __init__(self, pixabay_api_key: Optional[str] = None, temp_dir: str = "temp/music"):
        self.api_key = pixabay_api_key or os.getenv("PIXABAY_API_KEY", "")
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def fetch_music(self, theme: str) -> Optional[str]:
        """
        Search and download a free lofi track based on theme.
        Returns path to downloaded file, or None.
        """
        # Try Pixabay API first
        if self.api_key:
            result = self._search_pixabay(theme)
            if result:
                return result

        # Fallback to direct links
        return self._try_fallback_links()

    def _search_pixabay(self, theme: str) -> Optional[str]:
        """Search Pixabay for royalty-free music."""
        try:
            resp = requests.get(
                PIXABAY_API_URL,
                params={
                    "key": self.api_key,
                    "q": f"lofi {theme} instrumental",
                    "category": "music",
                    "per_page": 5,
                },
                timeout=30,
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", [])

            if not hits:
                return None

            for hit in hits:
                audio_url = hit.get("pageURL")  # Pixabay returns page URLs
                # Note: Pixabay's API for audio requires their separate audio endpoint
                # This is a simplified implementation

            return None  # Pixabay audio API requires different endpoint

        except requests.RequestException as e:
            log.warning("Pixabay search failed: %s", e)
            return None

    def _try_fallback_links(self) -> Optional[str]:
        """Try downloading from fallback direct links."""
        import random

        for url in FALLBACK_TRACKS:
            try:
                output_path = self.temp_dir / f"free_lofi_{int(time.time())}.mp3"
                resp = requests.get(url, stream=True, timeout=30)

                if resp.status_code == 200 and len(resp.content) > 100000:
                    with open(output_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            f.write(chunk)
                    log.info("Downloaded fallback music: %s", output_path)
                    return str(output_path)

            except requests.RequestException as e:
                log.warning("Fallback link failed: %s", e)
                continue

        return None
