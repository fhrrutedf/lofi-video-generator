import requests
import os
import sys
import argparse
from pathlib import Path

# Configuration
ACESTEP_API_URL = "http://localhost:8001/generate"
DEFAULT_PROMPT = "Lofi hip hop, chill, relaxing, 80 BPM, high quality"

def generate_music(prompt, output_path, duration=180):
    """
    Call ACE-Step 1.5 API to generate music.
    """
    payload = {
        "prompt": prompt,
        "duration": duration,  # seconds
        "output_format": "mp3"
    }
    
    print(f"🎵 Sending request to ACE-Step 1.5 API...")
    print(f"📝 Prompt: {prompt}")
    
    try:
        response = requests.post(ACESTEP_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        
        # Save the returned audio file
        with open(output_path, 'wb') as f:
            f.write(response.content)
            
        print(f"✅ Music generated and saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error generating music: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="ACE-Step 1.5 Music Generation Bridge for LofiGen AI")
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT, help="Music generation prompt")
    parser.add_argument("--output", type=str, default="temp/acestep_music.mp3", help="Output file path")
    parser.add_argument("--duration", type=int, default=180, help="Duration in seconds")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    success = generate_music(args.prompt, args.output, args.duration)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
