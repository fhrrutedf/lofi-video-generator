"""
Kie.ai API Integration for Suno Music Generation
Handles communication with Kie.ai to generate music from prompts
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, Optional
import os


# User-friendly error messages for common API errors
API_ERROR_MESSAGES = {
    400: "طلب غير صالح - تحقق من المعاملات (Invalid request parameters)",
    401: "مفتاح API غير صحيح - تحقق من KIE_API_KEY (Invalid API key)",
    402: "نفذ رصيدك - يجب شحن الحساب (Payment required - Credits exhausted)",
    403: "الوصول محظور - تحقق من صلاحيات الحساب (Access forbidden)",
    429: "تجاوزت حد الطلبات - انتظر قليلاً (Rate limit exceeded)",
    500: "خطأ في خادم Kie.ai - حاول لاحقاً (Server error)",
    502: "بوابة غير صالحة - مشكلة مؤقتة (Bad gateway)",
    503: "الخدمة غير متاحة مؤقتاً (Service unavailable)",
    504: "انتهت مهلة البوابة (Gateway timeout)"
}

# Helpful links for error resolution
ERROR_HELP_LINKS = {
    401: "https://kie.ai/dashboard/api-keys",
    402: "https://kie.ai/billing",
    429: "https://kie.ai/docs/rate-limits"
}


class KieAIClient:
    """
    Client for Kie.ai API (Suno music generation)
    Handles authentication, music generation, and download
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Kie.ai client
        
        Args:
            api_key: Your Kie.ai API key (or set KIE_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv("KIE_API_KEY")
        self.base_url = "https://api.kie.ai/api/v1"
        
        if not self.api_key:
            raise ValueError(
                "API key required! Set KIE_API_KEY environment variable or pass api_key parameter"
            )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_music(
        self,
        prompt: str,
        duration: int = 180,  # 3 minutes in seconds
        model: str = "V3_5",
        make_instrumental: bool = True,
        wait_for_completion: bool = True,
        max_wait_time: int = 300  # 5 minutes max
    ) -> Dict:
        """
        Generate music using Suno via Kie.ai
        
        Args:
            prompt: Text description of the music to generate
            duration: Desired length in seconds (default: 180 = 3 minutes)
            model: Suno model version (default: v3.5)
            make_instrumental: Generate instrumental only (default: True)
            wait_for_completion: Wait for generation to complete (default: True)
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            Dictionary with generation results including audio_url
        """
        print(f"🎵 Generating music with Kie.ai...")
        print(f"   Prompt: {prompt[:100]}...")
        
        # Prepare request payload
        # Some versions of the API require callBackUrl, style, and title
        payload = {
            "prompt": prompt,
            "instrumental": make_instrumental,
            "model": model,
            "title": "Lofi Track",
            "style": "lofi hip hop",
            "customMode": False, # Required by the latest API
            "callBackUrl": "https://example.com/callback" # Dummy callback
        }
        
        try:
            # Send generation request
            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # Check if response is successful
            if response.status_code != 200:
                # Get user-friendly error message
                user_msg = API_ERROR_MESSAGES.get(
                    response.status_code,
                    f"خطأ غير معروف (Unknown error {response.status_code})"
                )
                
                print(f"❌ {user_msg}")
                
                # Add helpful link if available
                help_link = ERROR_HELP_LINKS.get(response.status_code)
                if help_link:
                    print(f"💡 للمساعدة: {help_link}")
                
                # Technical details for debugging
                print(f"   Technical: {response.text[:200]}")
                
                return {
                    "success": False,
                    "error": user_msg,
                    "status_code": response.status_code,
                    "details": response.text[:200],
                    "help_link": help_link
                }

            res_json = response.json()
            
            # The API might use "code" or might just rely on HTTP status
            if "code" in res_json and res_json.get("code") != 200:
                return {
                    "success": False,
                    "error": f"API returned code {res_json.get('code')}: {res_json.get('message', 'No message')}. Full response: {json.dumps(res_json)[:200]}"
                }
            
            data = res_json.get("data", {})
            task_id = data.get("taskId")
            
            if not task_id:
                # If taskId is missing, check if it's under a different key
                task_id = res_json.get("taskId") or data.get("id")
                
            if not task_id:
                return {
                    "success": False,
                    "error": f"No taskId found in response. Response: {json.dumps(res_json)[:200]}"
                }
            
            if wait_for_completion:
                result = self._poll_generation_status(task_id, max_wait_time)
                
                # --- SMART RETRY logic for Content Filters ---
                if not result.get("success"):
                     err = str(result.get("error", "")).lower()
                     if "artist" in err or "sensitive" in err or "policy" in err or "contain" in err:
                         if "SAFE_MODE" not in prompt: # Prevent infinite loop
                             print("⚠️  Content Filter triggered (Artist Name/Policy). Retrying with SAFE PROMPT...")
                             safe_prompt = "lofi study beats, relaxing piano, ambient atmosphere, instrumental, no lyrics -- SAFE_MODE"
                             return self.generate_music(
                                 prompt=safe_prompt,
                                 tags="lofi, chill",
                                 mv=mv,
                                 title="Safe Lofi Track",
                                 make_instrumental=True,
                                 wait_for_completion=True
                             )
                return result
            else:
                return {
                    "success": True,
                    "job_id": task_id,
                    "status": "pending"
                }
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error generating music: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        model: str = "veo3",
        aspect_ratio: str = "16:9",
        wait_for_completion: bool = True,
        max_wait_time: int = 600  # Video takes longer
    ) -> Dict:
        """
        Generate video animation using Veo 3.1 via Kie.ai
        """
        print(f"🎬 Generating video with Veo 3.1...")
        print(f"   Prompt: {prompt[:100]}...")
        
        payload = {
            "prompt": prompt,
            "model": model,
            "aspectRatio": aspect_ratio,
            "enableTranslation": True
        }
        
        if image_url:
            payload["imageUrls"] = [image_url]
            payload["generationType"] = "FIRST_AND_LAST_FRAMES_2_VIDEO"
            print("   Mode: Image-to-Video")
        else:
            payload["generationType"] = "TEXT_2_VIDEO"
            print("   Mode: Text-to-Video")
        
        try:
            response = requests.post(
                f"{self.base_url}/veo/generate",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Video API Error: {response.text}")
                return {"success": False, "error": response.text}

            res_json = response.json()
            if res_json.get("code") != 200:
                return {"success": False, "error": res_json.get("message")}
                
            task_id = res_json.get("data", {}).get("taskId")
            if not task_id:
                return {"success": False, "error": "No taskId in video response"}
                
            if wait_for_completion:
                return self._poll_video_status(task_id, max_wait_time)
            else:
                return {"success": True, "job_id": task_id}
                
        except Exception as e:
            print(f"❌ Error during video generation: {e}")
            return {"success": False, "error": str(e)}

    def _poll_video_status(self, job_id: str, max_wait_time: int) -> Dict:
        """Poll the API for video generation status"""
        print("⏳ Waiting for video generation (Veo) to complete...")
        start_time = time.time()
        poll_interval = 20 # Video generation is slow
        
        while (time.time() - start_time) < max_wait_time:
            try:
                response = requests.get(
                    f"{self.base_url}/veo/record-info",
                    params={"taskId": job_id},
                    headers=self.headers,
                    timeout=30
                )
                
                res_json = response.json()
                if res_json.get("code") != 200:
                    time.sleep(poll_interval)
                    continue
                    
                data = res_json.get("data", {})
                status = data.get("status")
                
                if status == "SUCCESS":
                    video_url = data.get("response", {}).get("videoUrl")
                    if video_url:
                        print("✅ Video generated successfully!")
                        return {
                            "success": True,
                            "video_url": video_url,
                            "job_id": job_id
                        }
                
                elif status in ["FAILED", "TASK_ERROR"]:
                    return {"success": False, "error": "Video generation failed"}
                
                elapsed = int(time.time() - start_time)
                print(f"   Video Status: {status} ({elapsed}s elapsed)...")
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f"⚠️ Video polling error: {e}")
                time.sleep(poll_interval)
                
        return {"success": False, "error": "Timeout waiting for video"}

    def download_video(self, video_url: str, output_path: str) -> bool:
        """Download generated video file"""
        return self.download_audio(video_url, output_path)  # Re-use logic
    
    def _poll_generation_status(self, job_id: str, max_wait_time: int) -> Dict:
        """
        Poll the API to check generation status using record-info
        """
        print("⏳ Waiting for music generation to complete...")
        
        start_time = time.time()
        poll_interval = 10  # Check every 10 seconds
        
        while (time.time() - start_time) < max_wait_time:
            try:
                # GET request with taskId as query parameter
                response = requests.get(
                    f"{self.base_url}/generate/record-info",
                    params={"taskId": job_id},
                    headers=self.headers,
                    timeout=30
                )
                
                response.raise_for_status()
                res_json = response.json()
                
                if res_json.get("code") != 200:
                    print(f"⚠️  API Error during polling: {res_json.get('message')}")
                    time.sleep(poll_interval)
                    continue
                
                data = res_json.get("data", {})
                status = data.get("status", "unknown")
                
                # Check for success
                if status == "SUCCESS":
                    suno_data = data.get("response", {}).get("sunoData", [])
                    if suno_data and len(suno_data) > 0:
                        # Pick the first one (Suno usually generates two)
                        track = suno_data[0]
                        print("✅ Music generated successfully!")
                        return {
                            "success": True,
                            "audio_url": track.get("audioUrl"),
                            "audio_id": job_id,
                            "title": track.get("title", "Generated Track"),
                            "duration": track.get("duration"),
                            "metadata": track
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Generation succeeded but no audio data found"
                        }
                
                # Check for failure
                elif status in ["CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "SENSITIVE_WORD_ERROR"]:
                    error_msg = data.get("errorMessage") or f"Generation failed with status: {status}"
                    return {
                        "success": False,
                        "error": error_msg
                    }
                
                # Still processing
                elapsed = int(time.time() - start_time)
                print(f"   Status: {status} ({elapsed}s elapsed)...")
                time.sleep(poll_interval)
            
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Polling error: {e}")
                time.sleep(poll_interval)
        
        return {
            "success": False,
            "error": "Timeout waiting for generation"
        }
    
    def download_audio(self, audio_url: str, output_path: str) -> bool:
        """
        Download generated audio file
        
        Args:
            audio_url: URL to the generated audio
            output_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        print(f"📥 Downloading audio...")
        
        try:
            response = requests.get(audio_url, stream=True, timeout=60)
            response.raise_for_status()
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Audio downloaded: {output_path} ({file_size:.2f} MB)")
            return True
        
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def generate_and_download(
        self,
        prompt: str,
        output_path: str,
        duration: int = 180,
        **kwargs
    ) -> Dict:
        """
        Complete workflow: generate music and download it
        
        Returns:
            Dictionary with success status and file path
        """
        # Generate music
        result = self.generate_music(prompt, duration=duration, **kwargs)
        
        if not result["success"]:
            return result
        
        # Download audio
        download_success = self.download_audio(
            result["audio_url"],
            output_path
        )
        
        if download_success:
            return {
                "success": True,
                "audio_path": output_path,
                "audio_url": result["audio_url"],
                "metadata": result["metadata"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to download audio",
                "audio_url": result["audio_url"]  # User can try manual download
            }


# Testing and example usage
if __name__ == "__main__":
    # Example usage (requires valid API key)
    
    print("=== Kie.ai Music Generation Test ===\n")
    print("Note: Set your KIE_API_KEY environment variable to test\n")
    
    # Check if API key is available
    if not os.getenv("KIE_API_KEY"):
        print("⚠️  No API key found. Set KIE_API_KEY environment variable to test.")
        print("\nExample usage:")
        print("```python")
        print("from kie_ai_integration import KieAIClient")
        print("")
        print("client = KieAIClient(api_key='your_key_here')")
        print("result = client.generate_and_download(")
        print("    prompt='lofi hip hop beats, chill vibes, study music',")
        print("    output_path='generated_music.mp3'")
        print(")")
        print("```")
    else:
        try:
            client = KieAIClient()
            
            test_prompt = "instrumental lofi hip hop, chill beats, aesthetic vibes, 80 BPM"
            output_file = "test_generated_music.mp3"
            
            result = client.generate_and_download(
                prompt=test_prompt,
                output_path=output_file,
                duration=180
            )
            
            if result["success"]:
                print(f"\n🎉 Success! Audio saved to: {result['audio_path']}")
            else:
                print(f"\n❌ Failed: {result.get('error')}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
