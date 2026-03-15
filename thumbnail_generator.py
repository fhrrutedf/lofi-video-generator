"""
Thumbnail Generator for Lofi Videos
Creates high-quality 1280x720 thumbnails with stylized text
"""

import subprocess
import os
from pathlib import Path
from typing import Optional
import config

class ThumbnailGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, 
                 source_path: str, 
                 theme_text: str, 
                 subtitle: str = "lofi beats to study / relax to",
                 logo_path: Optional[str] = None,
                 output_name: Optional[str] = None) -> str:
        """
        Generate a thumbnail from a video frame or image
        """
        if not output_name:
            import time
            timestamp = int(time.time())
            output_name = f"thumb_{timestamp}.jpg"
        
        output_path = self.output_dir / output_name
        
        # 1. Extract frame or use image
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        is_image = Path(source_path).suffix.lower() in image_extensions
        
        # Build FFmpeg command for thumbnail
        # We use a complex filter to scale, darken, and add text
        
        # Scale to 1280x720 (YouTube standard)
        filters = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720"
        
        # Add a dark overlay for better text readability
        filters += ",drawbox=y=0:color=black@0.4:width=iw:height=ih:t=fill"
        
        # Add theme text (centered, large)
        # Using a generic font that works on most systems
        clean_theme = theme_text.upper().replace("'", "")
        filters += f",drawtext=text='{clean_theme}':fontcolor=white:fontsize=100:x=(w-text_w)/2:y=(h-text_h)/2-40:shadowcolor=black:shadowx=5:shadowy=5"
        
        # Add subtitle (centered, smaller, below theme)
        clean_subtitle = subtitle.upper().replace("'", "")
        filters += f",drawtext=text='{clean_subtitle}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+60:shadowcolor=black:shadowx=3:shadowy=3"
        
        # Add a "LIVE" or "4HR" badge (optional, let's add 4HR)
        filters += ",drawtext=text='4 HOURS':fontcolor=white:fontsize=30:x=w-text_w-20:y=20:box=1:boxcolor=red@0.8:boxborderw=10"

        cmd = ["ffmpeg", "-y"]
        
        if is_image:
            cmd.extend(["-i", source_path])
        else:
            # Extract frame at 1 second to avoid potential black frames at start
            cmd.extend(["-ss", "00:00:01", "-i", source_path])
            
        cmd.extend([
            "-frames:v", "1",
            "-vf", filters,
            str(output_path)
        ])
        
        try:
            print(f"🎬 Generating thumbnail: {output_path.name}")
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"❌ Thumbnail generation failed: {e.stderr.decode(errors='replace')}")
            return ""

if __name__ == "__main__":
    # Test
    gen = ThumbnailGenerator()
    # Simple test if you have a file
    # gen.generate("background.mp4", "Coffee Vibes")
