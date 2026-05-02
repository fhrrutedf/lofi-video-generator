"""
AI Orchestrator — routes between Gemini and OpenRouter.

Clean implementation with:
  - Proper fallback chain
  - No dead code
  - Structured logging
  - Graceful degradation when APIs are unavailable
"""

from __future__ import annotations

import json
from typing import Optional

from lofi_gen.core.config import AIConfig
from lofi_gen.core.logging import get_logger

log = get_logger("orchestrator")


class AIOrchestrator:
    """
    Routes AI requests between Gemini and OpenRouter.

    Modes:
      - "gemini": Use only Gemini
      - "openrouter": Use only OpenRouter
      - "auto": Try Gemini first, fall back to OpenRouter
    """

    def __init__(self, config: AIConfig):
        self.config = config
        self._gemini = None
        self._openrouter = None

        if config.provider in ("gemini", "auto") and config.gemini_api_key:
            from lofi_gen.ai.gemini_client import GeminiClient
            self._gemini = GeminiClient(config.gemini_api_key)
            log.info("Gemini client initialized")

        if config.provider in ("openrouter", "auto") and config.openrouter_api_key:
            from lofi_gen.ai.openrouter_client import OpenRouterClient
            self._openrouter = OpenRouterClient(config.openrouter_api_key)
            log.info("OpenRouter client initialized")

        # Determine active provider
        if config.provider == "auto":
            self.active = "gemini" if self._gemini else "openrouter" if self._openrouter else None
        else:
            self.active = config.provider

        if self.active:
            log.info("Active AI provider: %s", self.active)
        else:
            log.warning("No AI provider available — template mode only")

    def enhance_prompt(
        self, theme: str, base_music: str, base_video: str
    ) -> Optional[dict[str, str]]:
        """
        Use AI to enhance music and video prompts.

        Returns dict with 'music_prompt' and 'video_prompt', or None on failure.
        """
        if not self.active:
            return None

        # Try primary provider
        if self.active == "gemini" or (self.config.provider == "auto" and self._gemini):
            result = self._try_gemini(theme, base_music, base_video)
            if result:
                return result

        # Fallback to OpenRouter
        if self._openrouter:
            result = self._try_openrouter(theme, base_music, base_video)
            if result:
                return result

        log.warning("All AI providers failed")
        return None

    def generate_seo(self, user_input: str, mood: str) -> Optional[dict]:
        """Use AI to generate SEO-optimized metadata."""
        if self._gemini:
            try:
                return self._gemini.generate_seo_metadata(user_input, mood)
            except Exception as e:
                log.warning("Gemini SEO failed: %s", e)
        return None

    def _try_gemini(self, theme: str, music: str, video: str) -> Optional[dict]:
        if not self._gemini:
            return None
        try:
            result = self._gemini.run_orchestrator(theme)
            if result and "error" not in result:
                return {
                    "music_prompt": result.get("suno_prompt", music),
                    "video_prompt": result.get("veo_prompt", video),
                }
        except Exception as e:
            log.warning("Gemini failed: %s", e)
        return None

    def _try_openrouter(self, theme: str, music: str, video: str) -> Optional[dict]:
        if not self._openrouter:
            return None
        try:
            result = self._openrouter.run_orchestrator(theme)
            if result and "error" not in result:
                return {
                    "music_prompt": result.get("suno_prompt", music),
                    "video_prompt": result.get("veo_prompt", video),
                }
        except Exception as e:
            log.warning("OpenRouter failed: %s", e)
        return None
