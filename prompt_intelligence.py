"""
Intelligent Prompt Generation System
Converts simple user input into professional music generation prompts
"""

import random
from typing import Dict, List, Optional
from gemini_integration import GeminiClient


class PromptIntelligence:
    """
    Smart prompt generator that transforms simple keywords into
    professional, detailed prompts for music generation APIs
    """
    
    # Base templates for different moods/themes
    TEMPLATES = {
        "default": [
            "instrumental lofi hip hop, chill beats, aesthetic vibes, high quality, no vocals",
            "ambient lofi music, relaxing atmosphere, smooth melodies, professional production",
            "chillhop instrumental, laid-back groove, atmospheric sounds, no singing"
        ],
        "study": [
            "focus music, study beats, lofi hip hop, concentration vibes, calm and steady",
            "productive study session music, gentle lofi beats, minimal distraction",
            "academic focus soundtrack, soft lofi instrumental, brain-friendly rhythms"
        ],
        "sleep": [
            "sleep music, ultra calm lofi, deep relaxation, very slow tempo, peaceful atmosphere",
            "bedtime lofi beats, gentle sounds for sleeping, tranquil instrumental",
            "nighttime ambient lofi, sleepy vibes, soft textures, dream-like quality"
        ],
        "work": [
            "work productivity music, energetic lofi beats, motivational vibes, upbeat tempo",
            "creative workspace soundtrack, inspiring lofi hip hop, positive energy",
            "professional background music, lofi beats for working, focused momentum"
        ],
        "nature": [
            "nature-inspired lofi, organic sounds, peaceful atmosphere, earthy tones",
            "natural ambient lofi, environmental textures, calming instrumental",
            "forest vibes lofi hip hop, nature sounds blend, serene melodies"
        ],
        "city": [
            "urban lofi beats, city night vibes, neon aesthetics, metropolitan atmosphere",
            "cityscape soundtrack, late night lofi, downtown ambience, modern sounds",
            "street life lofi hip hop, urban exploration music, contemporary beats"
        ],
        "space": [
            "cosmic lofi beats, space atmosphere, ethereal synths, galactic vibes",
            "astral lofi hip hop, otherworldly sounds, celestial melodies, deep space mood",
            "interstellar ambient lofi, sci-fi textures, astronomical inspiration"
        ],
        "ocean": [
            "ocean waves lofi, seaside atmosphere, aquatic vibes, flowing melodies",
            "coastal lofi beats, beach sunset mood, maritime sounds, relaxing tides",
            "underwater ambient lofi, deep sea inspiration, liquid textures"
        ],
        "rain": [
            "rainy day lofi, cozy indoor vibes, gentle rain sounds, melancholic beauty",
            "rainfall lofi beats, wet weather mood, nostalgic atmosphere, comfort music",
            "storm ambient lofi, rain-inspired melodies, cloudy day soundtrack"
        ],
        "cafe": [
            "coffee shop lofi, cafe atmosphere, warm and cozy, social ambience",
            "barista beats, coffee culture music, friendly cafe vibes, comfortable setting",
            "espresso lofi hip hop, morning cafe mood, aromatic soundscape"
        ],
        "retro": [
            "vintage lofi beats, 80s nostalgia, retro aesthetics, analog warmth",
            "throwback lofi hip hop, old school vibes, classic sounds, nostalgic melodies",
            "retro-wave lofi, vintage synthesizers, time machine music, past memories"
        ],
        "jazz": [
            "jazzy lofi hip hop, smooth jazz fusion, sophisticated vibes, classy atmosphere",
            "jazz-influenced lofi beats, improvised feel, elegant melodies, refined taste",
            "neo-jazz lofi, contemporary jazz elements, artistic expression, cultured sound"
        ],
        "anime": [
            "anime style lofi hip hop, studio ghibli inspired music, nostalgic anime vibes",
            "chill anime soundtrack, emotional anime lofi, peaceful animation atmosphere",
            "aesthetic anime beats, japanese classroom vibes, summer festival anime lofi"
        ]
    }
    
    # BPM ranges for different moods
    BPM_RANGES = {
        "default": (70, 90),
        "study": (65, 80),
        "sleep": (40, 60),
        "work": (85, 100),
        "nature": (60, 75),
        "city": (80, 95),
        "space": (55, 70),
        "ocean": (65, 80),
        "rain": (60, 75),
        "cafe": (75, 90),
        "retro": (80, 100),
        "jazz": (70, 95),
        "anime": (75, 95)
    }
    
    # Visual Mood mapping for FFmpeg color grading
    MOOD_MAP = {
        "default": "clean",
        "study": "productive",
        "sleep": "dreamy",
        "work": "productive",
        "nature": "cozy",
        "city": "melancholy",
        "space": "ethereal",
        "ocean": "dreamy",
        "rain": "sad",
        "cafe": "cozy",
        "retro": "cozy",
        "jazz": "melancholy",
        "anime": "dreamy"
    }

    # High-End Cinematic Effects Mapping
    ADVANCED_SYNC_MAP = {
        "space": {"evolving": True, "glitch": True, "speed": 0.8, "audio": ["reverb"]},
        "city": {"evolving": True, "glitch": True, "speed": 1.0, "audio": []},
        "rain": {"evolving": True, "glitch": False, "speed": 0.9, "audio": ["vinyl"]},
        "retro": {"evolving": False, "glitch": True, "speed": 1.0, "audio": ["vinyl"]},
        "cafe": {"evolving": True, "glitch": False, "speed": 1.0, "audio": []},
        "anime": {"evolving": True, "glitch": False, "speed": 1.0, "audio": []},
        "default": {"evolving": False, "glitch": False, "speed": 1.0, "audio": []}
    }
    
    # Mood/theme keywords mapping
    KEYWORD_MAP = {
        # Arabic keywords
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
        "جاز": "jazz", "موسيقى راقية": "jazz",
        
        # English keywords
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
        "anime": "anime", "anim": "anime", "انمي": "anime", "أنمي": "anime"
    }
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize the prompt intelligence system.
        Args:
            gemini_api_key: Optional API key for Google Gemini dynamic generation
        """
        self.gemini_client = GeminiClient(api_key=gemini_api_key) if gemini_api_key else None
        if self.gemini_client and self.gemini_client.api_key:
            print("✨ Gemini Intelligence Enabled")
    
    def detect_theme(self, user_input: str) -> str:
        """
        Detect the theme/mood from user input
        Returns the best matching theme or 'default'
        """
        user_input_lower = user_input.lower().strip()
        
        # Check for keyword matches
        for keyword, theme in self.KEYWORD_MAP.items():
            if keyword in user_input_lower:
                return theme
        
        # Default theme
        return "default"
    
    def generate_prompt(self, user_input: str, custom_settings: Dict = None) -> Dict:
        """
        Generate a professional prompt from simple user input
        
        Args:
            user_input: Simple keyword or phrase from user
            custom_settings: Optional custom settings to override defaults
            
        Returns:
            Dictionary with full prompt, BPM, and metadata
        """
        # Detect theme
        theme = self.detect_theme(user_input)
        
        # Get base template
        templates = self.TEMPLATES.get(theme, self.TEMPLATES["default"])
        base_template = random.choice(templates)
        
        # Get BPM range
        bpm_min, bpm_max = self.BPM_RANGES.get(theme, self.BPM_RANGES["default"])
        bpm = random.randint(bpm_min, bpm_max)
        
        # Build full prompt (initially template-based)
        full_prompt = f"{user_input} themed, {base_template}, approximately {bpm} BPM"
        
        # Use Gemini if available
        if self.gemini_client and self.gemini_client.api_key:
            try:
                print("🧠 Generating dynamic prompt with Gemini...")
                mood = self.MOOD_MAP.get(theme, "chill")
                dynamic_prompt = self.gemini_client.generate_music_prompt(user_input, mood)
                if dynamic_prompt:
                    full_prompt = dynamic_prompt
                    print("✅ Gemini prompt generated")
            except Exception as e:
                print(f"⚠️ Gemini prompt generation failed, falling back to templates: {e}")

        # Apply custom settings if provided
        if custom_settings:
            if "bpm" in custom_settings:
                bpm = custom_settings["bpm"]
                if not (self.gemini_client and self.gemini_client.api_key):
                     # Only append BPM if using template, Gemini usually includes it if prompted well
                     full_prompt = f"{user_input} themed, {base_template}, {bpm} BPM"
                else:
                     full_prompt += f", {bpm} BPM"
            
            if "extra_keywords" in custom_settings:
                full_prompt += f", {custom_settings['extra_keywords']}"
        
        return {
            "prompt": full_prompt,
            "theme": theme,
            "bpm": bpm,
            "user_input": user_input,
            "base_template": base_template,
            "suggested_mood": self.MOOD_MAP.get(theme, self.MOOD_MAP["default"]),
            "advanced": self.ADVANCED_SYNC_MAP.get(theme, self.ADVANCED_SYNC_MAP["default"])
        }
    
    def batch_generate(self, user_input: str, count: int = 3) -> List[Dict]:
        """
        Generate multiple prompt variations for the same input
        Useful for giving users options
        """
        theme = self.detect_theme(user_input)
        results = []
        
        for _ in range(count):
            result = self.generate_prompt(user_input)
            results.append(result)
        
        return results
    
    def get_theme_info(self, theme: str) -> Dict:
        """Get information about a specific theme"""
        return {
            "theme": theme,
            "templates": self.TEMPLATES.get(theme, []),
            "bpm_range": self.BPM_RANGES.get(theme, (70, 90)),
            "keywords": [k for k, v in self.KEYWORD_MAP.items() if v == theme]
        }

    def generate_youtube_metadata(self, theme: str, user_input: str, duration_sec: int = 14400) -> Dict:
        """
        Generates SEO-optimized YouTube Title, Description, and Tags
        """
        mood = self.MOOD_MAP.get(theme, "clean")
        
        # Use Gemini for SEO if available
        if self.gemini_client and self.gemini_client.api_key:
            try:
                print("🧠 Generating specialized SEO metadata with Gemini...")
                seo_data = self.gemini_client.generate_seo_metadata(user_input, mood)
                if seo_data and seo_data.get("title") and seo_data.get("description"):
                    return seo_data
            except Exception as e:
                 print(f"⚠️ Gemini SEO generation failed, falling back to templates: {e}")
        
        # Fallback to templates
        
        # 1. Generate Titles (Clickbait but professional)
        title_options = [
            f"Lofi Hip Hop Radio ☕ - {user_input} Beats to {theme if theme != 'default' else 'relax'}/study to",
            f"Slow it down in {user_input} 🌿 ~ Lofi Hip Hop Mix [4K]",
            f"a {mood} {theme} lofi mix to help you focus / study / sleep 🚀",
            f"pov: you are at a {user_input} cafe [lofi / chill / study beats]"
        ]
        title = random.choice(title_options)
        
        # 2. Generate Timestamps for Pomodoro (if 4 hours)
        timestamps = []
        if duration_sec >= 1800: # At least one cycle
            cycles = duration_sec // 1800
            for i in range(cycles):
                start_time = i * 30
                timestamps.append(f"{start_time:02d}:00 - Session {i+1} (Focus 🎯)")
                timestamps.append(f"{(start_time + 25):02d}:00 - Break {i+1} (Coffee ☕)")

        # 3. Build Description
        description = f"""✨ Experience the ultimate {mood} vibes with this {user_input} themed lofi mix. 
Perfect for studying, working, or just relaxing after a long day.

Track Features:
- 100% Royalty Free Lofi Music
- Immersive Ambient Sounds
- Professional {mood} Color Grading

⏰ Pomodoro Timestamps:
{chr(10).join(timestamps[:20])} # Show first 10 cycles

#lofi #chill #study #focus #work #{theme if theme != 'default' else 'beats'} #productivity
"""
        
        # 4. Tags
        tags = f"lofi, lofi hip hop, chill beats, study music, focus beats, {user_input}, {theme}, relaxing music, no copyright lofi"
        
        return {
            "title": title,
            "description": description,
            "tags": tags
        }


# Example usage and testing
if __name__ == "__main__":
    intelligence = PromptIntelligence()
    
    # Test various inputs
    test_inputs = [
        "قهوة الصباح",
        "دراسة",
        "فضاء",
        "study session",
        "rainy night",
        "coffee vibes"
    ]
    
    print("=== Prompt Intelligence System - Test Results ===\n")
    
    for user_input in test_inputs:
        result = intelligence.generate_prompt(user_input)
        print(f"User Input: '{user_input}'")
        print(f"Detected Theme: {result['theme']}")
        print(f"BPM: {result['bpm']}")
        print(f"Full Prompt: {result['prompt']}")
        print("-" * 80)
        print()
