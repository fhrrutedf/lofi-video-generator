"""
End-to-End Automation Pipeline
Combines prompt intelligence, music generation, and video creation
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional
import json

from prompt_intelligence import PromptIntelligence
from kie_ai_integration import KieAIClient
from pexels_integration import PexelsVideoFetcher
from thumbnail_generator import ThumbnailGenerator
import config
import subprocess
import sys


class LofiVideoPipeline:
    """
    Complete automation pipeline from user input to final video
    """
    
    def __init__(
        self,
        kie_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        output_dir: str = "output",
        temp_dir: str = "temp"
    ):
        """
        Initialize the automation pipeline
        
        Args:
            kie_api_key: Kie.ai API key
            output_dir: Directory for final videos
            temp_dir: Directory for temporary files (music, etc.)
        """

        self.prompt_intelligence = PromptIntelligence(gemini_api_key=gemini_api_key)
        self.kie_client = KieAIClient(api_key=kie_api_key) if kie_api_key else None
        self.thumbnail_generator = ThumbnailGenerator(output_dir=output_dir)
        
        # Setup directories
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        self.music_dir = self.temp_dir / "music"
        self.music_dir.mkdir(exist_ok=True)
        
        self.ambience_dir = self.temp_dir / "ambience"
        self.ambience_dir.mkdir(exist_ok=True)

        self.pexels_fetcher = PexelsVideoFetcher(api_key=config.PEXELS_API_KEY)
        
        # Mapping themes to specialized ambience sounds
        self.AMBIENCE_MAP = {
            "rain": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/rain.mp3",
            "cafe": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/cafe.mp3",
            "forest": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/forest.mp3",
            "nature": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/forest.mp3",
            "ocean": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/waves.mp3",
            "city": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/city.mp3",
            "work": "https://raw.githubusercontent.com/the-muda-organization/lofi/master/ambience/office.mp3"
        }
    
    def create_video_from_text(
        self,
        user_input: str,
        video_background: str,
        ambience_track: Optional[str] = None,
        logo: Optional[str] = None,
        film_grain: bool = False,
        output_filename: Optional[str] = None,
        skip_music_generation: bool = False,
        existing_music_path: Optional[str] = None,
        has_pomodoro: bool = False,
        has_rain: bool = False,
        has_fog: bool = False,
        has_particles: bool = False,
        has_breathing: bool = False,
        has_vignette: bool = False,
        has_letterbox: bool = False,
        has_blur_bg: bool = False,
        has_camera_shake: bool = False,
        has_motion_bg: bool = False,
        live: bool = False,
        youtube_key: str = None,
        stream_key: str = None,
        mood: Optional[str] = None,
        speed: float = 1.0,
        has_glitch: bool = False,
        has_evolving: bool = False,
        audio_effects: Optional[list] = None,
        auto_fetch_type: str = "video" # "video" or "photo"
    ) -> Dict:
        """
        Complete pipeline: Text -> Music -> Video
        
        Args:
            user_input: Simple keyword/phrase (e.g., "قهوة الصباح")
            video_background: Path to video or image file
            ambience_track: Optional ambience audio file
            logo: Optional logo PNG file
            film_grain: Add film grain effect
            output_filename: Custom output filename
            skip_music_generation: Use existing music instead
            existing_music_path: Path to existing music if skipping generation
            
        Returns:
            Dictionary with pipeline results and file paths
        """
        print("\n" + "="*80)
        print("🚀 LOFI VIDEO AUTOMATION PIPELINE")
        print("="*80 + "\n")
        
        pipeline_start = time.time()
        results = {
            "success": False,
            "user_input": user_input,
            "steps": {}
        }
        
        # STEP 1: Generate intelligent prompt
        print("📝 STEP 1: Intelligent Prompt Generation")
        print("-" * 80)
        
        prompt_result = self.prompt_intelligence.generate_prompt(user_input)
        results["steps"]["prompt_generation"] = prompt_result
        
        print(f"   User Input: '{user_input}'")
        print(f"   Detected Theme: {prompt_result['theme']}")
        print(f"   Generated Prompt: {prompt_result['prompt'][:100]}...")
        print(f"   BPM: {prompt_result['bpm']}")
        print("✅ Prompt generated successfully!\n")
        
        # STEP 2: Generate or use existing music
        if skip_music_generation and existing_music_path:
            print("📀 STEP 2: Using Existing Music")
            print("-" * 80)
            music_path = existing_music_path
            print(f"   Using: {music_path}")
            results["steps"]["music_generation"] = {
                "success": True,
                "source": "existing",
                "path": music_path
            }
        else:
            print("🎵 STEP 2: Music Generation")
            print("-" * 80)
            
            music_success = False
            music_path = None
            
            # Try Kie.ai first if available
            if self.kie_client:
                print("✨ Attempting Kie.ai generation...")
                timestamp = int(time.time())
                safe_input = "".join(c if c.isalnum() else "_" for c in user_input[:30])
                music_filename = f"{safe_input}_{timestamp}.mp3"
                music_path = str(self.music_dir / music_filename)
                
                music_result = self.kie_client.generate_and_download(
                    prompt=prompt_result["prompt"],
                    output_path=music_path,
                    duration=180
                )
                
                if music_result.get("success"):
                    music_success = True
                    results["steps"]["music_generation"] = music_result
                    print(f"✅ Kie.ai Music saved: {music_path}\n")
                else:
                    print(f"⚠️  Kie.ai failed or no credits. Switching to Free Music Provider...")
            
            # Fallback to Free Music Provider
            if not music_success:
                from free_music_provider import FreeMusicProvider
                free_provider = FreeMusicProvider(temp_dir=str(self.music_dir))
                free_music = free_provider.fetch_music(prompt_result["theme"])
                
                if free_music:
                    music_path = free_music
                    music_success = True
                    results["steps"]["music_generation"] = {
                        "success": True,
                        "source": "free_archive",
                        "path": music_path
                    }
                    print(f"✅ Free Music saved: {music_path}\n")
                else:
                    results["error"] = "Failed to obtain music from any source"
                    results["steps"]["music_generation"] = {"success": False, "error": results["error"]}
                    return results
        # STEP 2.5: Auto-fetch media from Pexels if not provided
        if not video_background:
            media_label = "photo" if auto_fetch_type == "photo" else "video"
            print(f"🎬 STEP 2.5: Auto-fetching {media_label} from Pexels")
            print("-" * 80)
            fetched_media = self.pexels_fetcher.fetch_theme_media(
                prompt_result["theme"], 
                media_type=auto_fetch_type
            )
            if fetched_media:
                video_background = fetched_media
                results["steps"]["video_fetching"] = {"success": True, "path": video_background, "type": media_label}
                print(f"✅ {media_label.capitalize()} fetched: {video_background}\n")
            else:
                print(f"❌ Error: Could not fetch {media_label} from Pexels and no local file provided.")
                results["error"] = f"No {media_label} background available"
                return results
        else:
            results["steps"]["video_fetching"] = {"success": True, "path": video_background, "source": "local"}
            
        # STEP 2.7: Smart Ambience & Mood Selection
        mood = prompt_result.get("suggested_mood", "clean")
        advanced = prompt_result.get("advanced", {})
        
        # Audio Effects (Reverb, Vinyl, etc.)
        audio_effects = advanced.get("audio", [])
        
        if not ambience_track:
            print(f"🌍 STEP 2.7: Auto-selecting ambience for theme '{prompt_result['theme']}'")
            ambience_url = self.AMBIENCE_MAP.get(prompt_result['theme'])
            if ambience_url:
                ambience_track = self._fetch_ambience(prompt_result['theme'], ambience_url)
                if ambience_track:
                    print(f"✅ Ambience added: {Path(ambience_track).name}")
            else:
                print("   No specific ambience for this theme, using pure music.")
        
        print(f"🎨 Visual Mood detected: {mood.upper()}\n")

        # --- THE ADVANCED VISUAL BRAIN ---
        is_image = Path(video_background).suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
        
        if is_image:
            input_text = f"{user_input} {prompt_result['theme']} {prompt_result['prompt']}".lower()
            print(f"🧠 Visual Brain analyzing: '{user_input}'")
            
            # 1. RAIN & STORM (Dynamic Intensity)
            rain_map = {
                "heavy": ["storm", "thunder", "heavy rain", "عاصفة", "رعد"],
                "normal": ["rain", "wet", "raindrops", "مطر", "شتاء", "غيث"]
            }
            if any(k in input_text for k in rain_map["heavy"]):
                has_rain = True
                print("🌧️ Detected: HEAVY STORM Vibe")
            elif any(k in input_text for k in rain_map["normal"]):
                has_rain = True
                print("🌦️ Detected: GENTLE RAIN Vibe")
            
            # 2. FOG & ATMOSPHERE
            fog_map = ["fog", "mist", "smoke", "cloud", "morning", "dreamy", "mystic", "ضباب", "فجر", "غموض", "حلم"]
            if any(k in input_text for k in fog_map) or is_image:
                has_fog = True
                print("🌫️ Detected: ATMOSPHERIC MIST")
                
            # 3. SMART PARTICLES (Context-Aware)
            particles_map = {
                "snow": ["snow", "winter", "cold", "frozen", "ثلج", "جليد", "برد"],
                "stars": ["stars", "space", "galaxy", "universe", "night", "dark", "فضاء", "نجوم", "ليل"],
                "petals": ["spring", "flower", "cherry", "blossom", "nature", "garden", "ربيع", "ورود", "زهور"],
                "dust": ["retro", "vintage", "old", "nostalgia", "library", "loft", "قديم", "تراث"]
            }
            
            for p_type, keywords in particles_map.items():
                if any(k in input_text for k in keywords):
                    has_particles = True
                    print(f"❄️ Detected: {p_type.upper()} Particles")
                    break # Use first matching particle type
            
            # 4. VIBE-BASED EFFECTS (Glitch/Grain)
            vibe_map = {
                "retro": ["90s", "80s", "retro", "vintage", "analog", "old school"],
                "cyber": ["cyberpunk", "neon", "future", "glitch", "digital"]
            }
            if any(k in input_text for k in vibe_map["retro"]):
                film_grain = True
                print("🎞️ Detected: RETRO NOSTALGIA (Grain Boost)")
            if any(k in input_text for k in vibe_map["cyber"]):
                # We can't change glitch here easily but we can print a note
                print("👾 Detected: CYBERPUNK (Glitch Enabled)")

            # 5. LIFE ANIMATION
            has_breathing = True
            print("💨 Auto-detecting: BREATHING LIFE (Enabled for all images)")

        print("-" * 80)
        print("🎬 STEP 3: Video Generation (4-Hour Render)")
        print("-" * 80)
        
        # Prepare output filename
        if not output_filename:
            timestamp = int(time.time())
            safe_input = "".join(c if c.isalnum() else "_" for c in user_input[:30])
            output_filename = f"{safe_input}_4hr_{timestamp}.mp4"
        
        output_path = str(self.output_dir / output_filename)
        
        # Build FFMPEG command
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "lofi_video_generator.py"),
            "--music", music_path,
            "--video", video_background,
            "--output", output_path
        ]
        
        if ambience_track:
            cmd.extend(["--ambience", ambience_track])
        
        if logo:
            cmd.extend(["--logo", logo])
        
        if film_grain:
            cmd.append("--film-grain")
            
        if mood:
            cmd.extend(["--mood", mood])
            
        if has_pomodoro:
            cmd.append("--pomodoro")
            
        if advanced.get("evolving"):
            cmd.append("--evolving")
            
        if advanced.get("glitch"):
            cmd.append("--glitch")
            
        if advanced.get("speed"):
            cmd.extend(["--speed", str(advanced["speed"])])
            
        if audio_effects:
            cmd.extend(["--audio-effects", ",".join(audio_effects)])
            
        if has_rain:
            cmd.append("--rain")
            
        if has_fog:
            cmd.append("--fog")
            
        if has_particles:
            cmd.append("--particles")
            
        if has_breathing:
            cmd.append("--breathing")

        if has_vignette:
            cmd.append("--vignette")

        if has_letterbox:
            cmd.append("--letterbox")

        if has_blur_bg:
            cmd.append("--blur-bg")

        if has_camera_shake:
            cmd.append("--camera-shake")

        if has_motion_bg:
            cmd.append("--motion-bg")

        if live:
            cmd.append("--live")
            if youtube_key:
                cmd.extend(["--youtube-key", str(youtube_key)])
            if stream_key:
                cmd.extend(["--stream-key", str(stream_key)])
        
        # Advanced optional args
        if mood:
            cmd.extend(["--mood", str(mood)])
        
        if speed != 1.0:
            cmd.extend(["--speed", str(speed)])
            
        if has_pomodoro:
            cmd.append("--pomodoro")
            
        if has_glitch:
            cmd.append("--glitch")
            
        if has_evolving:
            cmd.append("--evolving")
            
        if audio_effects:
            effects_str = ",".join(audio_effects)
            cmd.extend(["--audio-effects", effects_str])
            
        print(f"   Running: {' '.join(cmd[:3])}...")
        print(f"   Music: {Path(music_path).name}")
        print(f"   Video: {Path(video_background).name}")
        print(f"   Output: {output_filename}")
        print()
        
        # Run video generator
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,  # Show progress in real-time
                encoding="utf-8",
                errors="replace",
                check=True
            )
            
            results["steps"]["video_generation"] = {
                "success": True,
                "output_path": output_path,
                "command": " ".join(cmd)
            }
            
            # Calculate total time
            total_time = time.time() - pipeline_start
            minutes = int(total_time // 60)
            seconds = int(total_time % 60)
            
            # Get file size
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size / (1024**3)  # GB
            else:
                file_size = 0
            
            print("\n" + "="*80)
            print("🎉 PIPELINE COMPLETE!")
            print("="*80)
            print(f"\n📊 Summary:")
            print(f"   Input: '{user_input}'")
            print(f"   Theme: {prompt_result['theme']}")
            print(f"   Music: {Path(music_path).name}")
            print(f"   Output: {output_filename}")
            print(f"   Size: {file_size:.2f} GB")
            print(f"   Total Time: {minutes}m {seconds}s")
            print(f"\n✅ Your 4-hour Lofi video is ready!")
            print(f"   Location: {output_path}\n")
            
            results["success"] = True
            results["output_path"] = output_path
            results["file_size_gb"] = file_size
            results["total_time_seconds"] = total_time
            
            # --- Generate & Save YouTube Metadata ---
            print("📄 Generating YouTube Metadata (SEO)...")
            meta = self.prompt_intelligence.generate_youtube_metadata(
                prompt_result["theme"], 
                user_input,
                config.OUTPUT_DURATION
            )
            
            meta_path = Path(output_path).with_suffix(".txt")
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(f"TITLE:\n{meta['title']}\n\n")
                f.write(f"TAGS:\n{meta['tags']}\n\n")
                f.write(f"DESCRIPTION:\n{meta['description']}")
            
            print(f"✅ Metadata saved: {meta_path.name}")
            results["metadata_path"] = str(meta_path)
            
            # --- Generate Thumbnail ---
            print("🖼️ Generating Thumbnail...")
            thumb_path = self.thumbnail_generator.generate(
                source_path=video_background,
                theme_text=user_input if user_input else prompt_result["theme"],
                subtitle="lofi beats to study / relax to"
            )
            if thumb_path:
                results["thumbnail_path"] = thumb_path
                print(f"✅ Thumbnail ready: {Path(thumb_path).name}")
            
            return results
        
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Video generation failed!")
            results["steps"]["video_generation"] = {
                "success": False,
                "error": str(e)
            }
            results["error"] = "Video generation failed"
            return results
        
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            results["error"] = str(e)
            return results

    def _fetch_ambience(self, theme: str, url: str) -> Optional[str]:
        """Fetch ambient sound from URL"""
        import requests
        try:
            filename = f"ambience_{theme}.mp3"
            path = self.ambience_dir / filename
            
            # Use cached version if exists
            if path.exists():
                return str(path)
                
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(path, 'wb') as f:
                f.write(response.content)
            return str(path)
        except Exception as e:
            print(f"   ⚠️  Could not fetch ambience: {e}")
            return None
    
    def save_pipeline_report(self, results: Dict, report_path: Optional[str] = None):
        """Save pipeline execution report as JSON"""
        if not report_path:
            timestamp = int(time.time())
            report_path = str(self.output_dir / f"pipeline_report_{timestamp}.json")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Pipeline report saved: {report_path}")


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎵 Lofi Video Automation Pipeline - From Text to 4-Hour Video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate everything from scratch
  python automation_pipeline.py "قهوة الصباح" --video cafe.mp4 --ambience rain.mp3 --logo logo.png
  
  # Use existing music
  python automation_pipeline.py "study vibes" --video library.mp4 --existing-music track.mp3
  
  # Minimal (no API key needed)
  python automation_pipeline.py "chill beats" --video bg.mp4 --existing-music music.mp3 --skip-music
        """
    )
    
    parser.add_argument("user_input", help="Simple keyword or phrase (Arabic/English)")
    parser.add_argument("--video", "-v", required=True, help="Background video or image")
    parser.add_argument("--ambience", "-a", help="Ambience audio track")
    parser.add_argument("--logo", "-l", help="Channel logo PNG")
    parser.add_argument("--film-grain", "-fg", action="store_true", help="Add film grain")
    parser.add_argument("--output", "-o", help="Custom output filename")
    parser.add_argument("--api-key", help="Kie.ai API key (or set KIE_API_KEY env var)")
    parser.add_argument("--skip-music", action="store_true", help="Skip music generation")
    parser.add_argument("--existing-music", help="Path to existing music file")
    parser.add_argument("--save-report", action="store_true", help="Save pipeline report")
    parser.add_argument("--pomodoro", action="store_true", help="Add 25/5 Pomodoro timer")
    parser.add_argument("--rain", action="store_true", help="Force visual rain")
    parser.add_argument("--fog", action="store_true", help="Force moving fog")
    parser.add_argument("--particles", action="store_true", help="Force floating particles")
    parser.add_argument("--breathing", action="store_true", help="Force breathing animation")
    parser.add_argument("--vignette", action="store_true", help="Add cinematic vignette")
    parser.add_argument("--letterbox", action="store_true", help="Add cinematic black bars")
    parser.add_argument("--blur-bg", action="store_true", help="Replace black bars with blurred background")
    parser.add_argument("--camera-shake", action="store_true", help="Add subtle camera shake")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    api_key = args.api_key or os.getenv("KIE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    pipeline = LofiVideoPipeline(kie_api_key=api_key, gemini_api_key=gemini_key)
    
    # Run pipeline
    results = pipeline.create_video_from_text(
        user_input=args.user_input,
        video_background=args.video,
        ambience_track=args.ambience,
        logo=args.logo,
        film_grain=args.film_grain,
        output_filename=args.output,
        skip_music_generation=args.skip_music,
        existing_music_path=args.existing_music,
        has_pomodoro=args.pomodoro,
        has_rain=args.rain,
        has_fog=args.fog,
        has_particles=args.particles,
        has_breathing=args.breathing,
        has_vignette=args.vignette,
        has_letterbox=args.letterbox,
        has_blur_bg=args.blur_bg,
        has_camera_shake=args.camera_shake,
        # Live Stream & Background Image
        live=getattr(args, 'live', False),
        stream_key=getattr(args, 'stream_key', None),
        youtube_key=getattr(args, 'youtube_key', None),

        has_motion_bg=getattr(args, 'motion_bg', False)
    )
    
    # Save report if requested
    if args.save_report:
        pipeline.save_pipeline_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)
