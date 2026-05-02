import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, Optional

# Import V3 components
from v3_automation_pipeline import LofiV3Pipeline
from acestep_bridge import generate_music
import config

class LofiV4LocalPipeline(LofiV3Pipeline):
    """
    V4 Pipeline: Adds support for local music generation via ACE-Step 1.5
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("🚀 LofiGen V4 Local Pipeline Initialized (ACE-Step Support Active)")

    def run(self, user_idea: str, image_path: Optional[str] = None, output_name: Optional[str] = None, music_engine: str = "ace-step"):
        """
        Full Pipeline: Idea -> Prompts -> Media (Local/Cloud) -> Video
        """
        if not self.ai_orchestrator.active_provider:
             print("❌ No AI provider configured. Please check your API keys.")
             return {"success": False, "error": "No AI Provider"}
             
        # Normalize paths if image provided
        if image_path and image_path != "N/A":
            image_path = str(Path(image_path).absolute())
            if not Path(image_path).exists():
                print(f"❌ Image file not found: {image_path}")
                return {"success": False, "error": "Image not found"}
        else:
            image_path = None

        # --- PHASE 1: ORCHESTRATION ---
        print("\n🧠 Phase 1: Orchestrating prompts...")
        orchestration = self.ai_orchestrator.run_orchestrator(user_idea, None)
        
        if not orchestration:
            print("❌ Failed to output orchestration.")
            return {"success": False, "error": "Orchestration Failed"}
            
        suno_final = orchestration.get("suno_prompt")
        veo_final = orchestration.get("veo_prompt")
        seo = orchestration.get("seo_metadata")
        
        # --- PHASE 2a: MUSIC GENERATION ---
        music_file = self.temp_dir / f"music_{int(time.time())}.mp3"
        
        if music_engine.lower() == "ace-step":
            print(f"\n🎵 Phase 2a: Generating Local Music (ACE-Step 1.5)...")
            # Build high-quality prompt for ACE-Step based on orchestrated idea
            acestep_prompt = f"Lofi hip hop, {suno_final}, chill, 80 BPM, high quality"
            success = generate_music(acestep_prompt, str(music_file), duration=180)
            
            if not success:
                print("⚠️ ACE-Step failed. Falling back to Suno (Kie AI)...")
                music_engine = "suno"
            else:
                music_url = str(music_file)
        
        if music_engine.lower() == "suno":
            print("\n🎵 Phase 2a: Generating Music (Suno AI via Kie)...")
            music_result = self.kie.generate_music(
                prompt=suno_final,
                make_instrumental=True,
                wait_for_completion=True
            )
            
            if isinstance(music_result, dict):
                if not music_result.get("success", False):
                    print(f"❌ Music generation failed: {music_result.get('error')}")
                    return {"success": False, "error": music_result.get("error")}
                music_url = music_result.get("audio_url")
            else:
                music_url = music_result
                
            if not music_url:
                print("❌ No music URL returned.")
                return {"success": False, "error": "No Music URL"}
                
            print(f"📥 Downloading audio from: {music_url[:50]}...")
            if not self.kie.download_audio(music_url, str(music_file)):
                print("❌ Failed to download music.")
                return {"success": False, "error": "Music Download Failed"}

        # --- PHASE 2b: VIDEO GENERATION (Same as V3 for now) ---
        print("\n🎬 Phase 2b: Generation Video (Veo 3.1)...")
        veo_image_url = image_path
        if image_path and not image_path.startswith("http"):
            public_url = self._upload_temp_image(image_path)
            veo_image_url = public_url if public_url else None
        
        video_result = self.kie.generate_video(
            prompt=veo_final + ", cinematic motion, moving camera, dynamic lighting, high quality loop, 4k",
            image_url=veo_image_url,
            wait_for_completion=True
        )
        
        video_clip_file = None
        if video_result['success']:
            video_clip_file = self.temp_dir / f"clip_{int(time.time())}.mp4"
            self.kie.download_video(video_result['video_url'], str(video_clip_file))
            print("✅ Animation complete.")
        else:
            print(f"⚠️ Video generation failed. Falling back to static image.")

        # --- PHASE 3: PRODUCTION ---
        print("\n⚙️ Phase 3: Final Production (FFmpeg)...")
        if not output_name:
            output_name = f"final_lofi_v4_{int(time.time())}.mp4"
        
        final_output = self.output_dir / output_name
        
        if video_clip_file and video_clip_file.exists():
            success = self.finalize_video_from_clip(str(video_clip_file), str(music_file), str(final_output))
        elif image_path and Path(image_path).exists():
            success = self.finalize_video_from_image(image_path, str(music_file), str(final_output))
        else:
            print("❌ No visual content available.")
            return {"success": False, "error": "No visual content"}
        
        if success:
            print(f"\n🎉 V4 SUCCESS! Video created: {final_output}")
            return {"success": True, "final_video": str(final_output)}
        else:
            return {"success": False, "error": "FFmpeg Failed"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lofi V4 Local Automation Pipeline")
    parser.add_argument("idea", help="The user's idea")
    parser.add_argument("image", help="Path or URL to the source image")
    parser.add_argument("--music-engine", default="ace-step", choices=["ace-step", "suno"], help="Music engine to use")
    parser.add_argument("--provider", default="auto", help="AI orchestrator provider")
    
    args = parser.parse_args()
    
    # Load keys
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    kie_api_key = os.getenv("KIE_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    pipeline = LofiV4LocalPipeline(
        gemini_key=gemini_api_key, 
        kie_key=kie_api_key,
        openrouter_key=openrouter_api_key,
        ai_provider=args.provider
    )
    pipeline.run(args.idea, args.image, music_engine=args.music_engine)
