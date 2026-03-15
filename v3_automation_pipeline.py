import os
import sys
import json
import time
import requests  # Added for file upload
import subprocess
from pathlib import Path
from typing import Dict, Optional

from ai_orchestrator import AIOrchestrator  # Updated to use universal orchestrator
from kie_ai_integration import KieAIClient
import config

class LofiV3Pipeline:
    """
    Implementation of the V3 Lofi Generation Pipeline
    Uses Gemini for Orchestration and Kie.ai for Suno (Music) and Veo (Video)
    """
    
    def __init__(
        self, 
        gemini_key: Optional[str] = None, 
        kie_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        ai_provider: str = "auto"
    ):
        # Initialize AI orchestrator (supports Gemini, OpenRouter, or both)
        self.ai_orchestrator = AIOrchestrator(
            provider=ai_provider,
            gemini_key=gemini_key,
            openrouter_key=openrouter_key
        )
        self.kie = KieAIClient(api_key=kie_key)
        
        self.output_dir = Path("output")
        self.temp_dir = Path("temp")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

    def _upload_temp_image(self, image_path: str) -> Optional[str]:
        """
        Uploads local image to temporary hosting to get a public URL for Veo API.
        Tries Litterbox first, then file.io as fallback.
        """
        file_content = None
        try:
            with open(image_path, "rb") as f:
                file_content = f.read()
        except Exception as e:
            print(f"❌ Error reading image file: {e}")
            return None


        # Common headers to avoid blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # 1. Try Litterbox
        try:
            print(f"📤 Uploading image to temporary storage (Litterbox)...")
            url = "https://litterbox.catbox.moe/resources/internals/api.php"
            
            payload = {
                "reqtype": "fileupload",
                "time": "1h"
            }
            files = {
                "fileToUpload": ("image.png", file_content, "image/png")
            }
            
            response = requests.post(url, data=payload, files=files, headers=headers, timeout=30)
            
            if response.status_code == 200 and response.text.startswith("http"):
                public_url = response.text.strip()
                print(f"✅ Image allocated: {public_url}")
                return public_url
            else:
                print(f"⚠️ Litterbox upload response: {response.text[:100]}")
        except Exception as e:
            print(f"⚠️ Litterbox upload failed: {e}")

        # 2. Fallback to file.io
        try:
            print(f"🔄 Retrying with fallback storage (file.io)...")
            url = "https://file.io/"
            
            files = {
                "file": ("image.png", file_content, "image/png")
            }
            payload = {"expires": "1d"}
            
            response = requests.post(url, data=payload, files=files, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                public_url = data.get("link")
                if public_url:
                    print(f"✅ Image allocated (fallback): {public_url}")
                    return public_url
        except Exception as e:
            print(f"⚠️ Fallback upload failed: {e}")

        # 3. Fallback to tmpfiles.org
        try:
            print(f"🔄 Retrying with fallback storage (tmpfiles.org)...")
            url = "https://tmpfiles.org/api/v1/upload"
            
            files = {
                "file": ("image.png", file_content, "image/png")
            }
            
            response = requests.post(url, files=files, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                raw_url = data.get("data", {}).get("url")
                if raw_url:
                    # Convert to direct link: https://tmpfiles.org/12345/image.png -> https://tmpfiles.org/dl/12345/image.png
                    public_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    print(f"✅ Image allocated (fallback 2): {public_url}")
                    return public_url
        except Exception as e:
            print(f"⚠️ Fallback 2 upload failed: {e}")
            
        return None

    def run(self, user_idea: str, image_path: Optional[str] = None, output_name: Optional[str] = None):
        """
        Full Pipeline: Idea -> Prompts -> Media -> Video
        """
        if not self.ai_orchestrator.active_provider:
             print("❌ No AI provider configured. Please check your API keys.")
             return {"success": False, "error": "No AI Provider"}
             
        # Normalize paths if image provided
        if image_path and image_path != "N/A":
            image_path = str(Path(image_path).absolute())
            # Check image
            if not Path(image_path).exists():
                print(f"❌ Image file not found: {image_path}")
                return {"success": False, "error": "Image not found"}
        else:
            image_path = None

        # --- PHASE 1: ORCHESTRATION ---
        # (Using local path for Gemini/OpenRouter to describe it textually is fine if they don't see it, 
        # but for Veo we need URL)
        
        # If it's a local file, we might pass a placeholder URL to orchestrator or handle it.
        # But let's first get the orchestration tags/prompts.
        
        print("\n🧠 Phase 1: Orchestrating prompts...")
        # Note: Orchestrator currently takes URL. If local, it might not analyze the image content visually 
        # unless we upload it or use a model that supports local bytes.
        # For now, we rely on the text idea mainly.
        orchestration = self.ai_orchestrator.run_orchestrator(user_idea, None)
        
        if not orchestration:
            print("❌ Failed to output orchestration.")
            return {"success": False, "error": "Orchestration Failed"}
            
        # Extract keys
        suno_final = orchestration.get("suno_prompt")
        veo_final = orchestration.get("veo_prompt")
        seo = orchestration.get("seo_metadata")
        
        print(f"✅ Music Prompt (Final): {suno_final[:80]}...")
        
        # --- PHASE 2a: MUSIC GENERATION ---
        print("\n🎵 Phase 2a: Generating Music (Suno AI)...")
        # Ensure instrumental
        music_result = self.kie.generate_music(
            prompt=suno_final,
            make_instrumental=True,
            wait_for_completion=True
        )
        
        # Check result type and extract URL
        if isinstance(music_result, dict):
            if not music_result.get("success", False):
                print(f"❌ Music generation failed: {music_result.get('error')}")
                return {"success": False, "error": music_result.get("error")}
            music_url = music_result.get("audio_url")
        else:
            # Assume it's a string (old behavior)
            music_url = music_result
            
        if not music_url:
            print("❌ No music URL returned.")
            return {"success": False, "error": "No Music URL"}
            
        # Download Music
        print(f"📥 Downloading audio from: {music_url[:50]}...")
        music_file = self.temp_dir / f"music_{int(time.time())}.mp3"
        if not self.kie.download_audio(music_url, str(music_file)):
            print("❌ Failed to download music.")
            return {"success": False, "error": "Music Download Failed"}
        
        # --- PHASE 2b: VIDEO GENERATION ---
        print("\n🎬 Phase 2b: Generation Video (Veo 3.1)...")
        
        # 1. Decide on Image URL for Veo
        veo_image_url = image_path
        
        if image_path:
            is_local = not image_path.startswith("http")
            if is_local:
                # Upload to temp storage to get public URL
                public_url = self._upload_temp_image(image_path)
                if public_url:
                    veo_image_url = public_url
                    print("ℹ️ Using public URL for animation.")
                else:
                    print("⚠️ Failed to generate public URL. Falling back to Text-to-Video.")
                    veo_image_url = None # Fallback to Text-to-Video
        else:
            print("ℹ️ No image provided. Using Text-to-Video mode.")
            veo_image_url = None
        
        # 2. Call Veo
        video_result = self.kie.generate_video(
            prompt=veo_final + ", cinematic motion, moving camera, dynamic lighting, high quality loop, 4k",
            image_url=veo_image_url, # Now this is a Public URL or None
            wait_for_completion=True
        )
        
        if video_result['success']:
            video_clip_file = self.temp_dir / f"clip_{int(time.time())}.mp4"
            self.kie.download_video(video_result['video_url'], str(video_clip_file))
            print("✅ Animation complete.")
        else:
            print(f"⚠️ Video generation failed: {video_result.get('error')}. Falling back to static image.")
            video_clip_file = None

        # --- PHASE 3: PRODUCTION ---
        print("\n⚙️ Phase 3: Final Production (FFmpeg)...")
        if not output_name:
            output_name = f"final_lofi_{int(time.time())}.mp4"
        
        final_output = self.output_dir / output_name
        
        # If we have an animated clip, loop it. Otherwise, use the static image (if available).
        if video_clip_file and video_clip_file.exists():
            success = self.finalize_video_from_clip(
                video_path=str(video_clip_file),
                audio_path=str(music_file),
                output_path=str(final_output)
            )
        elif image_path and Path(image_path).exists():
            print("⚠️ Using fallback: Static image with music.")
            success = self.finalize_video_from_image(
                image_path=image_path,  # Use local path
                audio_path=str(music_file),
                output_path=str(final_output)
            )
        else:
            print("❌ No visual content generated (Veo failed and no source image).")
            return {"success": False, "error": "No visual content available"}
        
        if success:
            print(f"\n🎉 SUCCESS! Video created: {final_output}")
            seo_file = final_output.with_suffix(".txt")
            with open(seo_file, "w", encoding="utf-8") as f:
                if isinstance(seo, dict):
                    f.write(f"TITLE: {seo.get('title')}\n\n")
                    f.write(f"DESCRIPTION:\n{seo.get('description')}")
                else:
                    f.write(str(seo))
            
            return {
                "success": True,
                "music_file": str(music_file),
                "video_clip": str(video_clip_file) if video_clip_file else None,
                "final_video": str(final_output)
            }
        else:
            print("❌ Final production failed.")
            return {"success": False, "error": "FFmpeg Failed"}

    def finalize_video_from_clip(self, video_path: str, audio_path: str, output_path: str):
        """Standard looping logic using FFmpeg."""
        print(f"🎞️ Merging animated clip...")
        cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1',
            '-i', video_path,
            '-i', audio_path,
            '-shortest',
            '-fflags', '+shortest',
            '-c:v', 'copy',
            '-c:a', 'aac',
            output_path
        ]
        try:
            subprocess.run(cmd, check=True)
            return True
        except:
            # Re-encode fallback
            cmd_fallback = [
                'ffmpeg', '-y', '-stream_loop', '-1', '-i', video_path, '-i', audio_path,
                '-shortest', '-fflags', '+shortest',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', output_path
            ]
            subprocess.run(cmd_fallback, check=True)
            return True

    def finalize_video_from_image(self, image_path: str, audio_path: str, output_path: str):
        """Creates a video from a static image and audio."""
        if not Path(image_path).exists():
            print(f"❌ Image not found: {image_path}")
            return False

        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path
        ]
        try:
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            print(f"❌ Static render error: {e}")
            return False

if __name__ == "__main__":
    # Quick CLI
    import argparse
    parser = argparse.ArgumentParser(description="Lofi V3 Automation Pipeline")
    parser.add_argument("idea", help="The user's idea (e.g. 'Sunny Room')")
    parser.add_argument("image_url", help="URL of the image to animate")
    parser.add_argument("--output", help="Optional output filename")
    parser.add_argument("--provider", default="auto", 
                       help="AI provider: 'gemini', 'openrouter', or 'auto' (default: auto)")
    
    args = parser.parse_args()
    
    # Load keys from environment or config
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    kie_api_key = os.getenv("KIE_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", args.provider)
    
    if not kie_api_key:
        print("❌ Error: KIE_API_KEY environment variable is required.")
        sys.exit(1)
    
    if not gemini_api_key and not openrouter_api_key:
        print("❌ Error: Either GEMINI_API_KEY or OPENROUTER_API_KEY is required.")
        print("   Get Gemini key: https://aistudio.google.com/app/apikey")
        print("   Get OpenRouter key: https://openrouter.ai/keys")
        sys.exit(1)
        
    pipeline = LofiV3Pipeline(
        gemini_key=gemini_api_key, 
        kie_key=kie_api_key,
        openrouter_key=openrouter_api_key,
        ai_provider=ai_provider
    )
    pipeline.run(args.idea, args.image_url, args.output)

