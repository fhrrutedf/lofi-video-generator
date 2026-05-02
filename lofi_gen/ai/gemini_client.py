"""
Gemini REST client — cleaned up from the original.

Fixes:
  - API key in URL → still required by Gemini REST API (documented limitation)
  - Proper retry with exponential backoff
  - No bare except
  - Structured logging
"""

from __future__ import annotations

import json
import time
from typing import Optional

import requests

from lofi_gen.core.logging import get_logger

log = get_logger("gemini")

MODELS_PRIORITY = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]


class GeminiClient:
    """Google Gemini API client via REST."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._working_model: Optional[str] = None

    def _call(self, prompt: str, max_retries: int = 3) -> str:
        if not self.api_key:
            return ""

        models = [self._working_model] if self._working_model else MODELS_PRIORITY
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        for model in models:
            for version in ("v1beta", "v1"):
                url = (
                    f"https://generativelanguage.googleapis.com/{version}"
                    f"/models/{model}:generateContent?key={self.api_key}"
                )

                for attempt in range(max_retries):
                    try:
                        resp = requests.post(url, headers=headers, json=payload, timeout=30)

                        if resp.status_code == 200:
                            self._working_model = model
                            data = resp.json()
                            return data["candidates"][0]["content"]["parts"][0]["text"]

                        if resp.status_code == 429:
                            wait = (2 ** attempt) * 5
                            log.warning("Quota exhausted (429) for %s, retry in %ds", model, wait)
                            time.sleep(wait)
                            continue

                        if resp.status_code == 404:
                            break  # try next model

                        log.error("Gemini error %d for %s: %s", resp.status_code, model, resp.text[:200])
                        break

                    except requests.exceptions.Timeout:
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        log.error("Timeout for %s after %d attempts", model, max_retries)

                    except requests.exceptions.ConnectionError:
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        log.error("Connection failed for %s", model)

        return ""

    def run_orchestrator(self, title: str, image_url: Optional[str] = None) -> dict:
        """
        Generate structured prompts for music, video, and SEO.
        Returns a dict with keys: suno_prompt, veo_prompt, seo_metadata
        """
        prompt = f"""You are a YouTube Lofi content expert. Convert the following idea into JSON.

Input: "{title}"
Image: {image_url or "N/A"}

RULES:
1. In 'suno_prompt', describe STYLE and INSTRUMENTS only (no artist names).
2. Use generic terms: "lofi hip hop", "chill beats", "relaxing".
3. In 'veo_prompt', describe a cinematic looping scene for video generation.
4. Return ONLY valid JSON with keys: suno_prompt, veo_prompt, seo_metadata

JSON format:
{{
  "suno_prompt": "music generation prompt",
  "veo_prompt": "video animation prompt",
  "seo_metadata": {{
    "title": "YouTube title",
    "description": "Full description with hashtags",
    "tags": "tag1, tag2, tag3"
  }}
}}"""

        raw = self._call(prompt).strip()
        if not raw:
            return {"error": "EMPTY_RESPONSE"}

        # Clean markdown fences
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            log.error("JSON parse failed: %s", e)
            return {"error": "JSON_PARSE_FAILED", "raw": raw[:200]}

    def generate_seo_metadata(self, user_input: str, mood: str) -> Optional[dict]:
        """Generate SEO metadata via Gemini."""
        prompt = f"""Generate YouTube SEO metadata for a lofi video.
Theme: {user_input}, Mood: {mood}
Return ONLY JSON: {{"title": "...", "description": "...", "tags": "..."}}"""
        raw = self._call(prompt).strip()
        if not raw:
            return None
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            return None
