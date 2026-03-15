"""
Pexels Video Integration
Automatically fetches relevant background videos from Pexels based on detected theme.
"""

import requests
import os
import random
import time
from typing import Optional, Dict, List
from typing import Optional, Dict, List
from pathlib import Path


class PexelsVideoFetcher:
    """Fetches background videos from Pexels API based on theme."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pexels video fetcher.
        
        Args:
            api_key: Pexels API key (or set PEXELS_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Pexels API key required. Set PEXELS_API_KEY env var or pass api_key parameter."
            )
        
        self.base_url = "https://api.pexels.com/videos"
        self.headers = {"Authorization": self.api_key}
        
    def search_videos(
        self, 
        query: str, 
        orientation: str = "landscape",
        size: str = "large",
        per_page: int = 15,
        max_retries: int = 3
    ) -> List[Dict]:
        """
        Search for videos on Pexels with retry logic for rate limiting.
        
        Args:
            query: Search query (e.g., "cafe", "rain", "study room")
            orientation: Video orientation (landscape/portrait/square)
            size: Video size (large/medium/small)
            per_page: Number of results per page
            max_retries: Maximum number of retries for rate limiting
            
        Returns:
            List of video dictionaries with metadata
        """
        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "orientation": orientation,
            "size": size,
            "per_page": per_page
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < max_retries - 1:
                        print(f"⏳ Pexels rate limit reached. Waiting {retry_after}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_after)
                        continue
                    else:
                        print(f"❌ Pexels rate limit: Max retries reached after {max_retries} attempts")
                        print("💡 Tip: Pexels free tier has 200 requests/hour limit")
                        return []
                
                # Check for other errors
                response.raise_for_status()
                data = response.json()
                return data.get("videos", [])
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    print(f"⏳ Pexels timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Pexels connection timeout after {max_retries} attempts")
                    return []
                    
            except requests.RequestException as e:
                if attempt < max_retries - 1 and attempt == 0:
                    # Only retry once for general errors
                    print(f"⏳ Pexels error: {e}. Retrying...")
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Error searching Pexels Videos: {e}")
                    return []
        
        return []

    def search_photos(
        self, 
        query: str, 
        orientation: str = "landscape",
        per_page: int = 15
    ) -> List[Dict]:
        """Search for photos on Pexels."""
        url = "https://api.pexels.com/v1/search"
        params = {
            "query": query,
            "orientation": orientation,
            "per_page": per_page
        }
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("photos", [])
        except requests.RequestException as e:
            print(f"❌ Error searching Pexels Photos: {e}")
            return []
    
    def get_best_video_url(self, video: Dict, quality: str = "hd") -> Optional[str]:
        """
        Extract the best video URL from video metadata.
        
        Args:
            video: Video metadata dictionary
            quality: Preferred quality (hd/sd/uhd)
            
        Returns:
            Video download URL or None
        """
        video_files = video.get("video_files", [])
        
        # Priority: HD (1920x1080) > SD > any available
        for vf in video_files:
            if vf.get("quality") == quality and vf.get("width") == 1920:
                return vf.get("link")
        
        # Fallback: any HD quality
        for vf in video_files:
            if vf.get("quality") == quality:
                return vf.get("link")
        
        # Last resort: first available
        if video_files:
            return video_files[0].get("link")
        
        return None
    
    def download_video(self, url: str, output_path: str) -> bool:
        """
        Download video from URL.
        
        Args:
            url: Video download URL
            output_path: Path to save video
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📥 Downloading video from Pexels...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Progress indicator
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📥 Download progress: {progress:.1f}%", end='')
            
            print(f"\n✅ Video downloaded: {output_path}")
            return True
            
        except requests.RequestException as e:
            print(f"❌ Error downloading video: {e}")
            return False

    def download_photo(self, url: str, output_path: str) -> bool:
        """Download photo from URL."""
        return self.download_video(url, output_path) # Same logic
        
    def search_video(self, query: str, quality: str = "hd") -> Optional[str]:
        """
        Helper: Search and return best video URL
        """
        videos = self.search_videos(query)
        if not videos:
            return None
        
        # Pick random form top 3 for variety
        top_videos = videos[:3]
        video = random.choice(top_videos)
        
        return self.get_best_video_url(video, quality)
    
    def fetch_theme_video(
        self, 
        theme: str, 
        output_dir: str = "temp",
        quality: str = "hd"
    ) -> Optional[str]:
        """
        Fetch the best video for a given theme.
        
        Args:
            theme: Theme name (cafe, study, rain, etc.)
            output_dir: Directory to save downloaded video
            quality: Video quality (hd/sd/uhd)
            
        Returns:
            Path to downloaded video or None
        """
        # Search for video URL first
        video_url = self.search_video(theme)
        
        if not video_url:
            print(f"❌ No video found for theme: {theme}")
            return None
            
        output_path = os.path.join(output_dir, f"pexels_{theme.replace(' ', '_')}_{int(time.time())}.mp4")

        # Download video
        if self.download_video(video_url, output_path):
            return output_path
        
        return None

    def fetch_theme_media(
        self, 
        theme: str, 
        media_type: str = "video",
        output_dir: str = "temp"
    ) -> Optional[str]:
        """Fetch either video or photo based on theme."""
        search_queries = {
            "cafe": "cozy cafe coffee shop aesthetic lofi",
            "study": "study room desk workspace library aesthetic",
            "rain": "rain window rainy day cozy",
            "sleep": "night stars peaceful bedroom",
            "work": "modern office workspace desk",
            "night": "night city lights aesthetic",
            "morning": "sunrise morning coffee peaceful",
            "space": "stars galaxy space nebula",
            "winter": "snow winter cozy fireplace",
            "summer": "beach ocean sunset summer",
            "chill": "peaceful nature aesthetic lofi",
            "travel": "travel journey adventure scenic",
            "anime": "anime style animation aesthetic lofi scenery studio ghibli"
        }
        query = search_queries.get(theme.lower(), f"{theme} lofi aesthetic")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if media_type == "photo":
            print(f"🔍 Searching Pexels for '{theme}' photos...")
            photos = self.search_photos(query)
            if not photos: return None
            photo = photos[0]
            url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("original")
            output_path = os.path.join(output_dir, f"pexels_img_{theme}_{photo.get('id')}.jpg")
            if url and self.download_photo(url, output_path):
                return output_path
        else:
            return self.fetch_theme_video(theme, output_dir)
        
        return None
    
    def get_video_metadata(self, video: Dict) -> Dict:
        """
        Extract useful metadata from video.
        
        Args:
            video: Video metadata dictionary
            
        Returns:
            Cleaned metadata
        """
        return {
            "id": video.get("id"),
            "duration": video.get("duration"),
            "width": video.get("width"),
            "height": video.get("height"),
            "url": video.get("url"),
            "photographer": video.get("user", {}).get("name"),
            "avg_color": video.get("avg_color")
        }


def fetch_video_for_theme(theme: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to fetch video for a theme.
    
    Args:
        theme: Theme name (cafe, study, rain, etc.)
        api_key: Pexels API key (optional if env var set)
        
    Returns:
        Path to downloaded video or None
    """
    try:
        fetcher = PexelsVideoFetcher(api_key)
        return fetcher.fetch_theme_video(theme)
    except Exception as e:
        print(f"❌ Error fetching video: {e}")
        return None


if __name__ == "__main__":
    # Test the integration
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pexels_integration.py <theme>")
        print("Example: python pexels_integration.py cafe")
        sys.exit(1)
    
    theme = sys.argv[1]
    
    # Get API key from environment variable
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("❌ Error: PEXELS_API_KEY environment variable not set")
        print("💡 Set it in .env file or run: export PEXELS_API_KEY=your_key")
        sys.exit(1)
    
    print(f"🎬 Fetching Pexels video for theme: {theme}")
    video_path = fetch_video_for_theme(theme, api_key)
    
    if video_path:
        print(f"✅ Success! Video saved: {video_path}")
    else:
        print(f"❌ Failed to fetch video")
