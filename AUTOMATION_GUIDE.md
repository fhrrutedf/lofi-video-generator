# 🤖 Lofi Video Automation - Complete Guide

## 🎯 Three Ways to Use This Tool

### 4️⃣ **YouTube Live Streaming 🔴 & Motion Backgrounds**
Broadcast directly to YouTube or animate static images.

**Live Streaming:**
```bash
# Stream with key
python lofi_video_generator.py --music track.mp3 --video loop.mp4 --live --stream-key "YOUR_KEY"
```

**Background Image & Motion:**
```bash
# Animate a static image
python lofi_video_generator.py --music track.mp3 --bg-image art.jpg --motion-bg
```

---

### 1️⃣ **Web Interface** (Easiest - Google-like)
Simple, beautiful interface - just type and generate!

```bash
streamlit run web_interface.py
```

**Perfect for:**
- Non-technical users
- Quick experimentation
- Visual feedback
- Easy file uploads

---

### 2️⃣ **Automation Pipeline** (Smart - Full AI)
Command-line automation with AI music generation

```bash
# Full automation: Text → AI Music → Video
python automation_pipeline.py "قهوة الصباح" --video cafe.mp4 --ambience rain.mp3 --logo logo.png

# Using existing music
python automation_pipeline.py "study vibes" --video library.mp4 --existing-music track.mp3 --skip-music
```

**Perfect for:**
- Batch processing
- Scripting/automation
- CI/CD pipelines
- Advanced users

---

### 3️⃣ **Manual FFMPEG Tool** (Classic - Direct Control)
Original tool with full control

```bash
python lofi_video_generator.py --music track.mp3 --video bg.mp4 --output video.mp4
```

**Perfect for:**
- When you already have music
- Maximum control
- Custom workflows
- No API needed

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install FFMPEG (see INSTALLATION.md for detailed instructions)
# Windows:
choco install ffmpeg

# macOS:
brew install ffmpeg

# Linux:
sudo apt install ffmpeg
```

### Step 2: Get Kie.ai API Key (Optional)

Only needed if you want AI music generation:

1. Go to [Kie.ai](https://kie.ai)
2. Sign up and get your API key
3. Set environment variable:

```bash
# Windows (PowerShell)
$env:KIE_API_KEY="your_key_here"

# Linux/macOS
export KIE_API_KEY="your_key_here"
```

### Step 3: Run!

**Web Interface:**
```bash
streamlit run web_interface.py
```

**Automation Pipeline:**
```bash
python automation_pipeline.py "your theme" --video background.mp4
```

---

## 📚 Detailed Examples

### Example 1: Complete Automation (Arabic Input)

```bash
python automation_pipeline.py "قهوة الصباح" \
  --video "cafe_scene.mp4" \
  --ambience "cafe_sounds.mp3" \
  --logo "channel_logo.png" \
  --film-grain
```

**What happens:**
1. ✨ System detects "قهوة" → "cafe" theme
2. 🎵 Generates prompt: "قهوة الصباح themed, coffee shop lofi, cafe atmosphere..."
3. 🤖 AI generates 3-minute cafe-themed music
4. 🎬 Creates 4-hour video with all effects

---

### Example 2: Study Music with Existing Track

```bash
python automation_pipeline.py "دراسة مكثفة" \
  --video "library.mp4" \
  --existing-music "my_study_track.mp3" \
  --skip-music \
  --logo "edu_logo.png"
```

**What happens:**
1. ✨ Uses your existing music
2. 📝 Still generates intelligent prompt metadata
3. 🎬 Creates 4-hour video

---

### Example 3: Web Interface Workflow

1. Open browser: `streamlit run web_interface.py`
2. Type: "rainy night"
3. Upload background video
4. Upload rain ambience (optional)
5. Click "Generate Video"  
6. ☕ Wait 30-90 minutes
7. ✅ Done!

---

## 🧠 How the Intelligence Works

### Prompt Intelligence System

When you type **"قهوة الصباح"** (morning coffee):

```python
# Behind the scenes:
{
  "user_input": "قهوة الصباح",
  "detected_theme": "cafe",
  "bpm": 82,
  "prompt": "قهوة الصباح themed, coffee shop lofi, cafe atmosphere, warm and cozy, social ambience, instrumental lofi hip hop, high quality, no vocals, 82 BPM"
}
```

### Supported Themes

| Arabic | English | BPM Range | Vibe |
|--------|---------|-----------|------|
| دراسة | study | 65-80 | Focus, concentration |
| نوم | sleep | 40-60 | Ultra calm, peaceful |
| عمل | work | 85-100 | Productive, energetic |
| قهوة | cafe | 75-90 | Cozy, social |
| مطر | rain | 60-75 | Melancholic, cozy |
| فضاء | space | 55-70 | Cosmic, ethereal |
| بحر | ocean | 65-80 | Flowing, aquatic |
| مدينة | city | 80-95 | Urban, metropolitan |

---

## ⚙️ Configuration

### Default Settings (config.py)

```python
# Output
OUTPUT_DURATION = 14400  # 4 hours
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
OUTPUT_FPS = 30

# Quality
VIDEO_CRF = 23  # Lower = better (18 for high quality)
VIDEO_PRESET = "medium"  # faster, fast, medium, slow, slower

# Audio
FADE_IN_DURATION = 3
FADE_OUT_DURATION = 3
AMBIENCE_VOLUME = 0.15

# Visual
LOGO_POSITION = "top-right"
FILM_GRAIN_STRENGTH = 5
```

### Customization

**Higher Quality:**
```python
VIDEO_CRF = 18
AUDIO_BITRATE = "256k"
VIDEO_PRESET = "slow"
```

**Faster Rendering:**
```python
VIDEO_CRF = 28
VIDEO_PRESET = "fast"
```

**Different Duration:**
```python
OUTPUT_DURATION = 7200  # 2 hours
OUTPUT_DURATION = 21600  # 6 hours
```

---

## 🔄 Complete Workflow Diagram

```
User Input: "قهوة الصباح"
       ↓
┌──────────────────────────────────┐
│  Prompt Intelligence             │
│  - Detect theme: "cafe"          │
│  - Generate professional prompt  │
│  - Select BPM: 82                │
└──────────────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  Kie.ai Music Generation         │
│  - Send prompt to Suno API       │
│  - Wait for generation (1-2 min) │
│  - Download MP3                  │
└──────────────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  FFMPEG Video Processing         │
│  - Loop audio (3min → 4hr)       │
│  - Apply fades (in/out)          │
│  - Mix ambience                  │
│  - Loop video background         │
│  - Add logo overlay              │
│  - Add film grain (optional)     │
│  - Encode to MP4                 │
│  - Progress tracking             │
└──────────────────────────────────┘
       ↓
    4-Hour Lofi Video Ready! 🎉
```

---

## 📊 Performance & Timing

### Music Generation (Kie.ai)
- **Time**: 1-3 minutes
- **Output**: 3-minute MP3 track
- **Quality**: Professional AI-generated music

### Video Rendering (FFMPEG)
- **Time**: 30-90 minutes (depends on CPU)
- **Output**: 4-hour 1080p MP4
- **Size**: ~5-10 GB

### Total Pipeline
- **Minimum**: ~35 minutes (fast CPU + quick API)
- **Average**: ~60 minutes
- **Maximum**: ~120 minutes (slow CPU)

---

## 🛠️ Troubleshooting

### "FFMPEG not found"
```bash
# Verify installation
ffmpeg -version

# If not found, install:
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

### "No API key for music generation"
```bash
# Set environment variable
export KIE_API_KEY="your_key_here"

# Or use existing music
python automation_pipeline.py "theme" --video bg.mp4 --existing-music music.mp3 --skip-music
```

### "Music generation failed"
- Check API key is valid
- Check internet connection
- Verify Kie.ai service status
- Use `--skip-music` with existing track as backup

### Video rendering too slow
```python
# In config.py, use faster preset:
VIDEO_PRESET = "fast"  # or "veryfast"
VIDEO_CRF = 28  # Lower quality, faster render
```

### Out of disk space
- 4-hour video needs ~10-15 GB free space
- Clean temp files: `rm -rf temp/`
- Use external drive for output

---

## 💡 Pro Tips

### Batch Processing

Create multiple videos automatically:

**Windows (PowerShell):**
```powershell
$themes = @("دراسة", "نوم", "قهوة", "مطر")
foreach ($theme in $themes) {
    python automation_pipeline.py $theme `
      --video "backgrounds/$theme.mp4" `
      --logo "logo.png"
}
```

**Linux/macOS (Bash):**
```bash
themes=("study" "sleep" "cafe" "rain")
for theme in "${themes[@]}"; do
    python automation_pipeline.py "$theme" \
      --video "backgrounds/${theme}.mp4" \
      --logo "logo.png"
done
```

### Scheduled Generation

Use cron (Linux/macOS) or Task Scheduler (Windows) to generate videos automatically.

### Notification on Completion

Add to automation_pipeline.py:
```python
# At the end of successful generation
import os
os.system('echo "Video ready!" | mail -s "Lofi Video Complete" you@email.com')
```

---

## 📁 Project Structure

```
d:/viideo/
├── lofi_video_generator.py      # Core FFMPEG tool
├── config.py                     # Settings
├── ffmpeg_utils.py               # FFMPEG utilities
├── prompt_intelligence.py        # Smart prompt generation
├── kie_ai_integration.py         # Kie.ai API client
├── automation_pipeline.py        # End-to-end automation
├── web_interface.py              # Streamlit web UI
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── INSTALLATION.md               # Setup guide
├── AUTOMATION_GUIDE.md           # This file
├── QUICK_REFERENCE.md            # Quick commands
├── examples/
│   ├── USAGE_EXAMPLES.md
│   └── example_config.json
├── temp/                         # Temporary files
│   └── music/                    # Generated music
└── output/                       # Final videos
```

---

## 🌟 What Makes This Special

### 1. **Intelligent Theme Detection**
- Supports Arabic and English
- 12+ predefined themes
- Automatic BPM selection
- Professional prompt engineering

### 2. **Seamless Integration**
- One command from text to video
- Automatic error handling
- Progress tracking
- Report generation

### 3. **Flexible Usage**
- Web interface for beginners
- CLI for developers
- Manual mode for advanced users
- Batch processing support

### 4. **Production Ready**
- Memory efficient
- Handles long renders
- Professional quality output
- YouTube-ready format

---

## 🎓 Learning Path

### Beginner
1. Start with **web interface**
2. Use existing music files
3. Try simple themes ("study", "rain")
4. Experiment with settings

### Intermediate
1. Use **automation pipeline**
2. Get Kie.ai API key
3. Try Arabic keywords
4. Customize config.py

### Advanced
1. Modify prompt templates
2. Add custom themes
3. Batch process multiple videos
4. Integrate with CI/CD
5. Deploy as web service

---

## 🤝 Contributing Ideas

Want to extend the system?

- Add more themes and templates
- Support other music generation APIs
- Add video generation APIs (background videos)
- Create mobile app interface
- Add YouTube auto-upload
- Implement job queue system
- Add email notifications
- Support custom ambience mixing

---

## 📞 Getting Help

1. Check [INSTALLATION.md](INSTALLATION.md) for setup issues
2. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands
3. Check [examples/USAGE_EXAMPLES.md](examples/USAGE_EXAMPLES.md) for examples
4. Review this guide for automation workflows

---

**Made with ❤️ for Lofi creators**

Happy generating! 🎵✨
