# Lofi Video Generator - Usage Examples

## Basic Examples

### 1. Minimal Setup (Music + Video Only)
```bash
python lofi_video_generator.py --music my_track.mp3 --video background.mp4 --output lofi_video.mp4
```

### 2. Add Ambience
```bash
python lofi_video_generator.py --music jazz.mp3 --video city.mp4 --ambience rain.mp3 --output rainy_jazz.mp4
```

### 3. Add Channel Logo
```bash
python lofi_video_generator.py --music beats.mp3 --video anime.mp4 --logo my_logo.png --output branded_lofi.mp4
```

### 4. Full Featured
```bash
python lofi_video_generator.py \
  --music "lofi_track.mp3" \
  --video "background.mp4" \
  --ambience "rain_sounds.mp3" \
  --logo "channel_logo.png" \
  --film-grain \
  --output "premium_lofi.mp4"
```

---

## Content-Specific Examples

### Study/Focus Sessions
```bash
# Calm piano with library ambience
python lofi_video_generator.py \
  -m "piano_study.mp3" \
  -v "library_scene.mp4" \
  -a "page_turning.mp3" \
  -l "study_logo.png" \
  -o "study_focus_4hr.mp4"
```

### Rainy Day Vibes
```bash
# Lofi beats with rain
python lofi_video_generator.py \
  -m "chill_beats.mp3" \
  -v "rainy_window.mp4" \
  -a "heavy_rain.mp3" \
  -fg \
  -o "rainy_lofi.mp4"
```

### Cafe Atmosphere
```bash
# Jazz with cafe sounds
python lofi_video_generator.py \
  -m "cafe_jazz.mp3" \
  -v "coffee_shop.mp4" \
  -a "cafe_chatter.mp3" \
  -l "logo.png" \
  -o "cafe_vibes.mp4"
```

### Night City Aesthetic
```bash
# Synthwave with city ambience
python lofi_video_generator.py \
  -m "synthwave_track.mp3" \
  -v "night_city.mp4" \
  -a "traffic_distant.mp3" \
  -fg \
  -o "city_nights.mp4"
```

### Nature Sounds
```bash
# Acoustic guitar with forest sounds
python lofi_video_generator.py \
  -m "acoustic_peaceful.mp3" \
  -v "forest_scene.jpg" \
  -a "birds_stream.mp3" \
  -o "nature_peace.mp4"
```

---

## Using Static Images

### Anime Wallpaper
```bash
python lofi_video_generator.py \
  -m "lofi_beats.mp3" \
  -v "anime_wallpaper.jpg" \
  -a "vinyl_crackle.mp3" \
  -l "channel_logo.png" \
  -o "anime_lofi.mp4"
```

### Minimalist Design
```bash
python lofi_video_generator.py \
  -m "minimal_ambient.mp3" \
  -v "abstract_art.png" \
  -fg \
  -o "minimal_vibes.mp4"
```

---

## Testing & Development

### Quick Test (Just to verify it works)
```bash
# Before committing to 4-hour render, test your setup
python lofi_video_generator.py --music test.mp3 --video test.mp4 --output test_output.mp4
```

### Check FFMPEG Installation
```bash
ffmpeg -version
ffprobe -version
```

### Verify Output File Details
```bash
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,r_frame_rate output.mp4
```

---

## Advanced Usage

### Custom Ambience Volume
Edit `config.py`:
```python
AMBIENCE_VOLUME = 0.10  # Quieter ambience (default is 0.15)
```

### Change Logo Position
Edit `config.py`:
```python
LOGO_POSITION = "bottom-right"  # Options: top-right, top-left, bottom-right, bottom-left
```

### Higher Quality Output
Edit `config.py`:
```python
VIDEO_CRF = 18  # Lower = better quality (default is 23)
AUDIO_BITRATE = "256k"  # Higher audio quality (default is 192k)
```

### Faster Rendering (Lower Quality)
Edit `config.py`:
```python
VIDEO_PRESET = "fast"  # Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
VIDEO_CRF = 28  # Higher = smaller file, lower quality
```

---

## Batch Processing

Create multiple videos with different ambiences:

### Windows (PowerShell)
```powershell
# Create array of ambience files
$ambiences = @("rain.mp3", "cafe.mp3", "ocean.mp3")

foreach ($amb in $ambiences) {
    $name = [System.IO.Path]::GetFileNameWithoutExtension($amb)
    python lofi_video_generator.py `
      --music "main_track.mp3" `
      --video "background.mp4" `
      --ambience "ambience\$amb" `
      --logo "logo.png" `
      --output "output_$name.mp4"
}
```

### Linux/macOS (Bash)
```bash
# Loop through ambience files
for ambience in ambience/*.mp3; do
    name=$(basename "$ambience" .mp3)
    python lofi_video_generator.py \
      --music "main_track.mp3" \
      --video "background.mp4" \
      --ambience "$ambience" \
      --logo "logo.png" \
      --output "output_${name}.mp4"
done
```

---

## Troubleshooting Examples

### If render fails, try simpler command first
```bash
# Start with absolute basics
python lofi_video_generator.py -m music.mp3 -v video.mp4 -o test.mp4
```

### Check input file duration
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 your_music.mp3
```

### Test FFMPEG directly
```bash
ffmpeg -i music.mp3 -i video.mp4 -t 10 -c:v libx264 -c:a aac quick_test.mp4
```

---

## Expected Rendering Times

- **Fast preset**: 20-30 minutes
- **Medium preset** (default): 30-60 minutes  
- **Slow preset**: 60-120 minutes

Times vary based on CPU power and complexity of filters (logo, film grain, etc.)
