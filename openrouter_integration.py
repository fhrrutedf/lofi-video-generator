"""
OpenRouter API Integration - Free Alternative to Gemini
Supports free models like openai/gpt-oss-120b:free
https://openrouter.ai/
"""

import os
import json
import requests
import time
from typing import Dict, Optional


class OpenRouterClient:
    """
    Client for OpenRouter API - supports free and paid models
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            print("⚠️ OpenRouter API Key not provided. This provider will be disabled.")
        
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Free models available on OpenRouter (Cleaned List - Jan 2026)
        # Removed models creating 404/400 errors
        self.free_models = [
            # 1. Google Gemini (Free Tier) - Best Quality
            "google/gemini-2.0-flash-exp:free",
            
            # 2. Meta Llama 3 (High Performance)
            "meta-llama/llama-3.3-70b-instruct:free",
            
            # 3. Mistral (Reliable Backup)
            "mistralai/mistral-7b-instruct:free",
            
            # 4. Extra Backups
            "sophosympatheia/midnight-rose-70b:free",
            "openrouter/auto"  # Tries to find best available free model automatically
        ]
        
        self.working_model = None
        
        print(f"🌐 OpenRouter Client initialized")
        print(f"   Will try: {self.free_models[0]} first (Free)")
    
    def _call_openrouter(self, prompt: str, model: Optional[str] = None, max_retries: int = 3) -> str:
        """Make API call to OpenRouter with retry logic"""
        if not self.api_key:
            return ""
        
        # Use specified model or try free models in order
        models_to_try = [model] if model else self.free_models
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lofi-video-generator",  # Required by OpenRouter
            "X-Title": "Lofi Video Generator"  # Optional but nice
        }
        
        for model_name in models_to_try:
            for attempt in range(max_retries):
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
                
                try:
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        self.working_model = model_name
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 5
                            print(f"⏳ Rate limited. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"🛑 Rate limit exceeded for {model_name}")
                            break  # Try next model
                    
                    elif response.status_code == 401:
                        print(f"❌ Invalid OpenRouter API Key")
                        return ""
                    
                    elif response.status_code == 402:
                        print(f"💰 Credits exhausted for {model_name}")
                        break  # Try next model
                    
                    elif response.status_code == 400:
                        print(f"❌ Bad request for {model_name}: {response.text[:200]}")
                        break
                    
                    else:
                        print(f"❌ OpenRouter Error ({model_name}): {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        break
                
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        print(f"⏳ Timeout. Retrying...")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        print(f"❌ Timeout after {max_retries} attempts")
                        break
                
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        print(f"⏳ Connection error. Retrying...")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        print(f"❌ Connection failed")
                        break
                
                except Exception as e:
                    print(f"❌ Unexpected error: {e}")
                    break
        
        return ""
    
    def run_orchestrator(self, title: str, image_url: Optional[str] = None) -> Dict:
        """
        The Orchestrator Prompt: Converts simple user input into technical data for music, video and SEO.
        Compatible with Gemini's format.
        """
        aesthetic_rules = ""
        if not image_url or image_url == "N/A":
            aesthetic_rules = """
4. CRITICAL: Since NO IMAGE is provided, the 'veo_prompt' MUST strictly describe a classic YouTube Lofi aesthetic scene for a Text-to-Video AI.
5. In 'veo_prompt', strictly include terms: "Anime style, 2D animation, cozy room, raining outside the window, soft neon lighting, lo-fi hip hop aesthetic, looping animation, 4k resolution." 
6. Adapt the scene to match the user's title while keeping the anime/lofi loop vibe prominent.
"""

        prompt = f"""
أنت خبير محتوى YouTube Lofi. وظيفتك استلام (عنوان أو فكرة) وتحويلها إلى مخرجات JSON تقنية بالمفاتيح التالية:
suno_prompt, veo_prompt, seo_metadata

المدخلات:
العنوان: {title}
الصورة: {image_url if image_url else "N/A"}

IMPORTANT RULES:
1. In 'suno_prompt', describe the STYLE and INSTRUMENTS only.
2. DO NOT use specific artist names, band names, or trademarks (e.g., do NOT use "Chillhop", "Lofi Girl", "Post Malone").
3. Use generic terms: "lofi hip hop", "chill beats", "relaxing", "study music".{aesthetic_rules}

Important: Return ONLY valid JSON block with these exact keys:
{{
  "suno_prompt": "music generation prompt in English",
  "veo_prompt": "video animation prompt in English", 
  "seo_metadata": {{
    "title": "YouTube video title",
    "description": "Full description with hashtags",
    "tags": "tag1, tag2, tag3"
  }}
}}

Return only the JSON, nothing else.
        """
        
        raw_response = self._call_openrouter(prompt).strip()
        
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
                print(f"⚠️  OpenRouter response missing keys: {missing_keys}")
                print(f"📄 Partial response received. Available keys: {list(parsed.keys())}")
            
            return parsed
        
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse OpenRouter JSON response: {e}")
            print(f"📄 Raw response (first 500 chars):")
            print(result[:500] + "..." if len(result) > 500 else result)
            return {
                "error": "JSON_PARSE_FAILED",
                "raw_response": result[:200]
            }


# Test function
if __name__ == "__main__":
    print("=== OpenRouter Test ===\n")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️  Set OPENROUTER_API_KEY environment variable to test")
        print("\nGet your free key from: https://openrouter.ai/keys")
        print("\nExample:")
        print('export OPENROUTER_API_KEY="sk-or-v1-..."')
    else:
        client = OpenRouterClient(api_key=api_key)
        
        # Test orchestrator
        result = client.run_orchestrator("Calm morning coffee", "https://example.com/image.jpg")
        
        if result:
            print("\n✅ Test successful!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n❌ Test failed")
