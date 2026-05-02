"""
Intelligent Prompt System — replaces the old keyword-matching approach.

Works in two modes:
  1. Template mode (no AI API needed) — structured, deterministic
  2. AI-enhanced mode (Gemini/OpenRouter) — creative, personalized
"""

from __future__ import annotations

import random
from typing import Optional

from lofi_gen.core.types import ThemeInfo
from lofi_gen.core.logging import get_logger

log = get_logger("prompt_system")


# ── Theme templates ────────────────────────────────────────────────────

THEME_TEMPLATES: dict[str, dict] = {
    "default": {
        "bpm_range": (70, 90),
        "mood": "clean",
        "music_templates": [
            "instrumental lofi hip hop, chill beats, aesthetic vibes, high quality, no vocals",
            "ambient lofi music, relaxing atmosphere, smooth melodies, professional production",
        ],
        "video_style": "cozy lofi aesthetic, soft lighting, gentle motion",
        "advanced": {},
    },
    "study": {
        "bpm_range": (65, 80),
        "mood": "productive",
        "music_templates": [
            "focus music, study beats, lofi hip hop, concentration vibes, calm and steady",
            "productive study session music, gentle lofi beats, minimal distraction",
        ],
        "video_style": "study room, desk, books, warm lamp, focused atmosphere",
        "advanced": {},
    },
    "sleep": {
        "bpm_range": (40, 60),
        "mood": "dreamy",
        "music_templates": [
            "sleep music, ultra calm lofi, deep relaxation, very slow tempo, peaceful atmosphere",
            "bedtime lofi beats, gentle sounds for sleeping, tranquil instrumental",
        ],
        "video_style": "bedroom, night sky, stars, moonlight, peaceful sleeping atmosphere",
        "advanced": {"speed": 0.8},
    },
    "work": {
        "bpm_range": (85, 100),
        "mood": "productive",
        "music_templates": [
            "work productivity music, energetic lofi beats, motivational vibes, upbeat tempo",
            "creative workspace soundtrack, inspiring lofi hip hop, positive energy",
        ],
        "video_style": "modern office, laptop, coffee, productive workspace",
        "advanced": {},
    },
    "rain": {
        "bpm_range": (60, 75),
        "mood": "sad",
        "music_templates": [
            "rainy day lofi, cozy indoor vibes, gentle rain sounds, melancholic beauty",
            "rainfall lofi beats, wet weather mood, nostalgic atmosphere, comfort music",
        ],
        "video_style": "rain on window, cozy room, warm blanket, melancholic beauty",
        "advanced": {"evolving": True, "audio": ["vinyl"]},
    },
    "cafe": {
        "bpm_range": (75, 90),
        "mood": "cozy",
        "music_templates": [
            "coffee shop lofi, cafe atmosphere, warm and cozy, social ambience",
            "barista beats, coffee culture music, friendly cafe vibes, comfortable setting",
        ],
        "video_style": "coffee shop, warm lighting, steam from cup, cozy atmosphere",
        "advanced": {"evolving": True},
    },
    "space": {
        "bpm_range": (55, 70),
        "mood": "ethereal",
        "music_templates": [
            "cosmic lofi beats, space atmosphere, ethereal synths, galactic vibes",
            "astral lofi hip hop, otherworldly sounds, celestial melodies, deep space mood",
        ],
        "video_style": "space, stars, nebula, cosmic atmosphere, ethereal lighting",
        "advanced": {"evolving": True, "glitch": True, "speed": 0.8, "audio": ["reverb"]},
    },
    "ocean": {
        "bpm_range": (65, 80),
        "mood": "dreamy",
        "music_templates": [
            "ocean waves lofi, seaside atmosphere, aquatic vibes, flowing melodies",
            "coastal lofi beats, beach sunset mood, maritime sounds, relaxing tides",
        ],
        "video_style": "ocean waves, beach sunset, coastal atmosphere, peaceful tides",
        "advanced": {},
    },
    "city": {
        "bpm_range": (80, 95),
        "mood": "melancholy",
        "music_templates": [
            "urban lofi beats, city night vibes, neon aesthetics, metropolitan atmosphere",
            "cityscape soundtrack, late night lofi, downtown ambience, modern sounds",
        ],
        "video_style": "city lights, neon signs, rain-slicked streets, urban night",
        "advanced": {"evolving": True, "glitch": True},
    },
    "retro": {
        "bpm_range": (80, 100),
        "mood": "cozy",
        "music_templates": [
            "vintage lofi beats, 80s nostalgia, retro aesthetics, analog warmth",
            "throwback lofi hip hop, old school vibes, classic sounds, nostalgic melodies",
        ],
        "video_style": "retro room, CRT TV, cassette player, vintage aesthetic, warm tones",
        "advanced": {"glitch": True, "audio": ["vinyl"]},
    },
    "jazz": {
        "bpm_range": (70, 95),
        "mood": "melancholy",
        "music_templates": [
            "jazzy lofi hip hop, smooth jazz fusion, sophisticated vibes, classy atmosphere",
            "jazz-influenced lofi beats, improvised feel, elegant melodies, refined taste",
        ],
        "video_style": "jazz club, saxophone, dim lighting, elegant atmosphere",
        "advanced": {},
    },
    "anime": {
        "bpm_range": (75, 95),
        "mood": "dreamy",
        "music_templates": [
            "anime style lofi hip hop, studio ghibli inspired music, nostalgic anime vibes",
            "chill anime soundtrack, emotional anime lofi, peaceful animation atmosphere",
        ],
        "video_style": "anime style, 2D animation, cozy room, soft lighting, ghibli inspired",
        "advanced": {"evolving": True},
    },
    "nature": {
        "bpm_range": (60, 75),
        "mood": "cozy",
        "music_templates": [
            "nature-inspired lofi, organic sounds, peaceful atmosphere, earthy tones",
            "forest vibes lofi hip hop, nature sounds blend, serene melodies",
        ],
        "video_style": "forest, trees, sunlight through leaves, peaceful nature",
        "advanced": {},
    },
}

# ── Keyword → theme mapping (Arabic + English) ────────────────────────

KEYWORD_MAP: dict[str, str] = {
    # Arabic
    "دراسة": "study", "تركيز": "study", "مذاكرة": "study",
    "نوم": "sleep", "استرخاء": "sleep", "راحة": "sleep",
    "عمل": "work", "إنتاجية": "work", "تحفيز": "work",
    "طبيعة": "nature", "غابة": "nature", "جبال": "nature",
    "مدينة": "city", "شارع": "city", "حضري": "city",
    "فضاء": "space", "كواكب": "space", "نجوم": "space",
    "بحر": "ocean", "محيط": "ocean", "موج": "ocean",
    "مطر": "rain", "أمطار": "rain", "غيوم": "rain",
    "قهوة": "cafe", "كافيه": "cafe", "مقهى": "cafe",
    "كلاسيكي": "retro", "قديم": "retro", "نوستالجيا": "retro",
    "جاز": "jazz", "انمي": "anime", "أنمي": "anime",
    # English
    "study": "study", "focus": "study", "concentration": "study",
    "sleep": "sleep", "relax": "sleep", "calm": "sleep",
    "work": "work", "productivity": "work", "creative": "work",
    "nature": "nature", "forest": "nature", "mountain": "nature",
    "city": "city", "urban": "city", "street": "city",
    "space": "space", "cosmic": "space", "galaxy": "space",
    "ocean": "ocean", "sea": "ocean", "beach": "ocean",
    "rain": "rain", "rainy": "rain", "storm": "rain",
    "cafe": "cafe", "coffee": "cafe", "espresso": "cafe",
    "retro": "retro", "vintage": "retro", "80s": "retro",
    "jazz": "jazz", "jazzy": "jazz", "smooth": "jazz",
    "anime": "anime",
}


class PromptSystem:
    """
    Structured prompt generation with optional AI enhancement.

    Works without any API keys (template mode).
    When AI is available, it enhances the prompts creatively.
    """

    def __init__(self, ai_enhancer: Optional[object] = None):
        """
        Args:
            ai_enhancer: Optional object with .enhance_prompt(theme, base_prompt) -> str
                         (e.g. AIOrchestrator instance)
        """
        self.ai_enhancer = ai_enhancer

    def detect_theme(self, user_input: str) -> str:
        """
        Detect theme from user input using keyword matching.
        Uses word-boundary matching to avoid false positives
        (e.g. "space" won't match "workspace").
        """
        text = user_input.lower().strip()

        # Try exact word matches first (avoid "space" matching "workspace")
        for keyword, theme in KEYWORD_MAP.items():
            # Check if keyword appears as a standalone word
            if f" {keyword} " in f" {text} " or text.startswith(keyword) or text.endswith(keyword):
                return theme

        return "default"

    def generate(self, user_input: str) -> ThemeInfo:
        """
        Generate a complete ThemeInfo from user input.

        Always works in template mode. If AI enhancer is available,
        it will be used to improve the music/video prompts.
        """
        theme_name = self.detect_theme(user_input)
        template = THEME_TEMPLATES.get(theme_name, THEME_TEMPLATES["default"])

        bpm_min, bpm_max = template["bpm_range"]
        bpm = random.randint(bpm_min, bpm_max)
        music_prompt = random.choice(template["music_templates"])
        video_prompt = template["video_style"]
        mood = template["mood"]
        advanced = template.get("advanced", {})

        # Build full music prompt with theme context
        full_music = f"{user_input} themed, {music_prompt}, approximately {bpm} BPM"

        # Build video prompt
        full_video = f"{video_prompt}, {user_input} atmosphere, cinematic lighting, looping animation, 4k"

        # AI enhancement (optional)
        if self.ai_enhancer and hasattr(self.ai_enhancer, "enhance_prompt"):
            try:
                enhanced = self.ai_enhancer.enhance_prompt(theme_name, full_music, full_video)
                if enhanced:
                    full_music = enhanced.get("music_prompt", full_music)
                    full_video = enhanced.get("video_prompt", full_video)
                    log.info("AI-enhanced prompts generated")
            except Exception as e:
                log.warning("AI enhancement failed, using templates: %s", e)

        return ThemeInfo(
            name=theme_name,
            bpm=bpm,
            mood=mood,
            music_prompt=full_music,
            video_prompt=full_video,
            advanced=advanced,
        )

    def generate_seo_metadata(
        self,
        theme_info: ThemeInfo,
        user_input: str,
        duration_hours: float = 4.0,
    ) -> dict[str, str]:
        """Generate YouTube SEO metadata (title, description, tags)."""
        theme = theme_info.name
        mood = theme_info.mood

        title_options = [
            f"Lofi Hip Hop Radio ☕ - {user_input} Beats to {theme if theme != 'default' else 'relax'}/study to",
            f"Slow it down in {user_input} 🌿 ~ Lofi Hip Hop Mix [4K]",
            f"a {mood} {theme} lofi mix to help you focus / study / sleep 🚀",
        ]
        title = random.choice(title_options)

        tags = (
            f"lofi, lofi hip hop, chill beats, study music, focus beats, "
            f"{user_input}, {theme}, relaxing music, no copyright lofi"
        )

        description = (
            f"✨ Experience the ultimate {mood} vibes with this {user_input} themed lofi mix.\n"
            f"Perfect for studying, working, or just relaxing.\n\n"
            f"🎵 100% Royalty Free Lofi Music\n"
            f"🎬 Immersive Ambient Sounds\n"
            f"🎨 Professional {mood} Color Grading\n\n"
            f"#{theme} #lofi #chill #study #focus #productivity"
        )

        return {"title": title, "description": description, "tags": tags}
