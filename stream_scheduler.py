import os
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

class StreamScheduler:
    """
    Handles scheduling and execution of YouTube Live streams using FFmpeg.
    """
    
    @staticmethod
    def wait_until(target_time: datetime):
        """Wait until the specified time."""
        now = datetime.now()
        if target_time > now:
            delay = (target_time - now).total_seconds()
            print(f"⏳ Waiting for {delay/60:.1f} minutes until start time: {target_time.strftime('%H:%M:%S')}")
            time.sleep(delay)
    
    @staticmethod
    def run_stream(video_path: str, rtmp_url: str, duration_hours: float):
        """
        Run FFmpeg stream for a specific duration.
        """
        print(f"🔴 Starting Stream: {video_path}")
        print(f"⏱️ Duration: {duration_hours} hours")
        
        # FFmpeg command for streaming a loop
        cmd = [
            'ffmpeg', '-y', '-re',
            '-stream_loop', '-1',
            '-i', video_path,
            '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '4500k',
            '-maxrate', '4500k', '-bufsize', '9000k',
            '-pix_fmt', 'yuv420p', '-g', '60',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
            '-f', 'flv',
            rtmp_url
        ]
        
        start_time = time.time()
        end_time_seconds = start_time + (duration_hours * 3600)
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        
        try:
            while time.time() < end_time_seconds:
                if process.poll() is not None:
                    print("❌ FFmpeg process exited unexpectedly.")
                    break
                
                # Check output occasionally to prevent buffer filling
                # line = process.stdout.readline()
                time.sleep(10) # Check every 10 seconds
                
                elapsed = (time.time() - start_time) / 3600
                remaining = duration_hours - elapsed
                print(f"📡 Streaming... {elapsed:.2f}h / {duration_hours}h (Remaining: {remaining:.2f}h)")
                
        except KeyboardInterrupt:
            print("🛑 Stream stopped by user.")
        finally:
            if process.poll() is None:
                process.terminate()
                print("✅ Stream process terminated.")
            
            print(f"🏁 Stream ended at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    # Example usage
    pass
