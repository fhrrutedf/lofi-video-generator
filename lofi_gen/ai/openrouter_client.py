"""
OpenRouter client — cleaned up from the original.

Fixes:
  - Proper retry logic
  - No bare except
  - Structured logging
"""

from __future__ import annotations

import json
import time
from typing import Optional

import requests

from lofi_gen.core.logging import get_logger

log = get_logger("openrouter")

FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openrouter/auto",
]


class OpenRouterClient:
    """OpenRouter API client with free model support."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._working_model: Optional[str] = None

    def _call(self, prompt: str, max_retries: int = 3) -> str:
        if not self.api_key:
            return ""

        models = [self._working_model] if self._working_model else FREE_MODELS
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lofi-gen/lofi-gen",
            "X-Title": "LofiGen",
        }

        for model in models:
            for attempt in range(max_retries):
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.7,
                }
                try:
                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        self._working_model = model
                        return resp.json()["choices"][0]["message"]["content"]

                    if resp.status_code == 429:
                        wait = (2 ** attempt) * 5
                        log.warning("Rate limited for %s, retry in %ds", model, wait)
                        time.sleep(wait)
                        continue

                    if resp.status_code in (401, 402):
                        log.error("Auth/billing error %d for %s", resp.status_code, model)
                        break

                    log.error("OpenRouter error %d: %s", resp.status_code, resp.text[:200])
                    break

                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                except Exception as e:
                    log.error("Unexpected error: %s", e)
                    break

        return ""

    def run_orchestrator(self, title: str, image_url: Optional[str] = None) -> dict:
        """Generate structured prompts (same format as Gemini)."""
        prompt = f"""You are a YouTube Lofi content expert. Convert the following idea into JSON.

Input: "{title}"
Image: {image_url or "N/A"}

RULES:
1. In 'suno_prompt', describe STYLE and INSTRUMENTS only (no artist names).
2. Use generic terms: "lofi hip hop", "chill beats".
3. In 'veo_prompt', describe a cinematic looping scene.
4. Return ONLY valid JSON with keys: suno_prompt, veo_prompt, seo_metadata

JSON:
{{
  "suno_prompt": "music generation prompt",
  "veo_prompt": "video animation prompt",
  "seo_metadata": {{"title": "...", "description": "...", "tags": "..."}}
}}"""

        raw = self._call(prompt).strip()
        if not raw:
            return {}

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            log.error("JSON parse failed: %s", e)
            return {"error": "JSON_PARSE_FAILED", "raw": raw[:200]}
