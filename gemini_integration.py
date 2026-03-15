"""
Gemini API Integration for Dynamic Content Generation
Handles communication with Google's Gemini API for prompts, lyrics, and SEO
"""

import os
import json
import requests
import time
from typing import Dict, Optional

class GeminiClient:
    """
    Client for Google Gemini API via REST
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ Gemini API Key not provided. AI features will be disabled.")
        
        # القائمة مرتبة: مجاني → رخيص → غالي
        # النماذج المجانية أولاً (Free Tier)
        self.models_to_try = [
            "gemini-2.0-flash-exp",           # ⭐ مجاني تماماً - 1500 طلب/يوم
            "gemini-1.5-flash-8b",            # ⭐ مجاني - 4000 طلب/يوم (أسرع)
            "gemini-1.5-flash",               # مجاني - 1500 طلب/يوم
            "gemini-1.5-flash-latest",        # نفس 1.5-flash
            "gemini-2.0-flash-lite",          # رخيص: $0.075/$0.30
            "gemini-2.0-flash",               # رخيص: $0.10/$0.40
            "gemini-pro"                      # احتياطي
        ]
        self.working_model = None
        
        print(f"🤖 Gemini Models Priority: Free → Cheap → Expensive")
        print(f"   Will try: {self.models_to_try[0]} first (Free Tier)")
    
    def _call_gemini(self, prompt: str, max_retries: int = 3) -> str:
        """Helper to make the API call with fallback and quota handling with retry logic"""
        if not self.api_key:
            return ""
            
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        models = [self.working_model] if self.working_model else self.models_to_try
        
        for model in models:
            for version in ["v1beta", "v1"]:
                url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={self.api_key}"
                
                # Retry logic with exponential backoff
                for attempt in range(max_retries):
                    try:
                        response = requests.post(url, headers=headers, json=payload, timeout=30)
                        
                        if response.status_code == 200:
                            self.working_model = model
                            data = response.json()
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        elif response.status_code == 429:
                            if attempt < max_retries - 1:
                                # Exponential backoff: 5s, 10s, 20s
                                wait_time = (2 ** attempt) * 5
                                print(f"⏳ Quota Exhausted (429) for {model}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                            else:
                                print(f"🛑 Quota Exhausted (429) for {model}. Max retries reached.")
                                return "ERR_QUOTA_EXHAUSTED"
                            
                        elif response.status_code == 404:
                            break  # Try next model/version
                            
                        elif response.status_code == 400:
                            print(f"❌ Bad Request (400) for {model}: Invalid prompt or parameters")
                            return ""
                            
                        elif response.status_code == 401:
                            print(f"❌ Unauthorized (401): Invalid GEMINI_API_KEY")
                            return ""
                            
                        else:
                            print(f"❌ Gemini API Error ({model} {version}): {response.status_code} - {response.text[:200]}")
                            break
                            
                    except requests.exceptions.Timeout:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"⏳ Request timeout. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Connection timeout after {max_retries} attempts")
                            return ""
                            
                    except requests.exceptions.ConnectionError:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"⏳ Connection error. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Connection failed after {max_retries} attempts")
                            return ""
                            
                    except Exception as e:
                        print(f"❌ Unexpected error ({model}): {e}")
                        break
        
        return ""

    def run_orchestrator(self, title: str, image_url: Optional[str] = None) -> Dict:
        """
        The Orchestrator Prompt: Converts simple user input into technical data for music, video and SEO.
        """
        prompt = f"""
أنت خبير محتوى YouTube Lofi. وظيفتك استلام (عنوان أو فكرة) وتحويلها إلى مخرجات JSON تقنية بالمفاتيح التالية:
suno_prompt, veo_prompt, seo_metadata

المدخلات:
العنوان: {title}
الصورة: {image_url if image_url else "N/A"}

IMPORTANT RULES:
1. In 'suno_prompt', describe the STYLE and INSTRUMENTS only.
2. DO NOT use specific artist names (e.g., NO "Chillhop", "Lofi Girl").
3. Use generic terms like "lofi hip hop", "chill beats".

Important: Return ONLY valid JSON block with these exact keys:     """
        
        raw_response = self._call_gemini(prompt).strip()
        
        if raw_response == "ERR_QUOTA_EXHAUSTED":
            return {"error": "QUOTA_EXHAUSTED"}
            
        if not raw_response:
            return {}

        # Clean up JSON formatting
        result = raw_response
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
            
        result = result.strip()
        
        try:
            parsed = json.loads(result)
            
            # Validate required keys
            required_keys = ["suno_prompt", "veo_prompt", "seo_metadata"]
            missing_keys = [k for k in required_keys if k not in parsed]
            
            if missing_keys:
                print(f"⚠️  Gemini response missing keys: {missing_keys}")
                print(f"📄 Partial response received. Available keys: {list(parsed.keys())}")
                # Return partial data anyway - better than nothing
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gemini JSON response: {e}")
            print(f"📄 Raw response (first 500 chars):")
            print(result[:500] + "..." if len(result) > 500 else result)
            print("\n💡 Tip: Gemini may need clearer instructions. Try simplifying your input.")
            return {
                "error": "JSON_PARSE_FAILED",
                "raw_response": result[:200]
            }

if __name__ == "__main__":
    client = GeminiClient()
    if client.api_key:
        print(client.run_orchestrator("Rainy Cafe"))
