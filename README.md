# 🎵 Lofi YouTube Video Generator - Complete Automation System

**Professional Python tool that transforms simple text into 4-hour Lofi YouTube videos**

Transform a single keyword like "قهوة الصباح" into a complete 4-hour professional Lofi video with AI-generated music, visual effects, and perfect looping.

---

## ✨ What's New: Full Automation!

### 🤖 Intelligent System
- **Smart Prompt Generation**: Type "قهوة" → AI understands "cafe theme"
- **Auto Music Creation**: Generates professional 3-minute tracks via Kie.ai
- **Complete Pipeline**: One command from text to finished 4-hour video

### 🎨 Three Ways to Use

1. **🌐 Web Interface** - Beautiful Google-like UI
2. **⚡ Automation Pipeline** - Smart CLI with AI music
3. **🎬 Manual FFMPEG Tool** - Classic precision control

---

## 🚀 Quick Start

### Install
```bash
pip install -r requirements.txt
# Install FFMPEG - see INSTALLATION.md
```

### Web Interface (Easiest!)
```bash
streamlit run web_interface.py
```

### Automation Pipeline
```bash
# With AI music generation
python automation_pipeline.py "قهوة الصباح" --video cafe.mp4

# With existing music  
python automation_pipeline.py "study vibes" --video library.mp4 --existing-music track.mp3 --skip-music
```

### Classic Tool
```bash
python lofi_video_generator.py --music track.mp3 --video bg.mp4 --output lofi_4hr.mp4
```

---

## 📚 Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Setup guide (Windows/Linux/macOS)
- **[AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)** - Complete automation system guide ⭐ NEW
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- **[examples/USAGE_EXAMPLES.md](examples/USAGE_EXAMPLES.md)** - Detailed examples

---

## 🎯 Features

### Core Features
- ✅ 4-hour video generation (14,400 seconds exactly)
- ✅ 1080p quality at 30 FPS
- ✅ Professional audio fades (in/out)
- ✅ Ambience track mixing
- ✅ Logo overlay
- ✅ Film grain effect
- ✅ Memory-efficient rendering

### 🆕 Automation Features
- ✅ **Smart Prompt Generation** (Arabic + English keywords)
- ✅ **AI Music Generation** (Kie.ai/Suno integration)
- ✅ **12+ Theme Detection** (study, cafe, rain, space, etc.)
- ✅ **Web Interface** (Google-like design)
- ✅ **End-to-End Pipeline** (text → music → video)
- ✅ **Batch Processing** ready

---

## 🧠 How It Works

```
"قهوة الصباح" (User Input)
    ↓
🤖 AI detects: "cafe" theme, 82 BPM
    ↓
🎵 Generates: Professional cafe lofi music (3 min)
    ↓
🎬 Creates: 4-hour video with loops, fades, effects
    ↓
✅ Result: Upload-ready MP4 (~5-10 GB)
```

---

## 📊 Supported Themes

| Arabic | English | Vibe |
|--------|---------|------|
| دراسة | study | Focus beats |
| قهوة | cafe | Cozy vibes |
| مطر | rain | Melancholic |
| فضاء | space | Cosmic |
| نوم | sleep | Ultra calm |
| عمل | work | Productive |
| +6 more themes... | | |

---

## 💡 Examples

### Web Interface
1. Open: `streamlit run web_interface.py`
2. Type: "rainy night"
3. Upload video
4. Click "Generate"
5. Wait ~60 min
6. Done! ✨

### Automation
```bash
# Arabic input with full features
python automation_pipeline.py "قهوة الصباح" \
  --video cafe.mp4 \
  --ambience cafe_sounds.mp3 \
  --logo logo.png \
  --film-grain

# Batch processing
for theme in "study" "sleep" "rain"; do
  python automation_pipeline.py "$theme" --video "bg_${theme}.mp4"
done
```

---

## 🎛️ Configuration

Edit `config.py` for customization:

```python
OUTPUT_DURATION = 14400  # 4 hours (or custom)
VIDEO_CRF = 23          # Quality (lower = better)
AMBIENCE_VOLUME = 0.15  # Ambience mix level
LOGO_POSITION = "top-right"
```

---

## 📦 What You Get

### Project Files
```
d:/viideo/
├── 🎬 Core Tools
│   ├── lofi_video_generator.py
│   ├── config.py
│   └── ffmpeg_utils.py
├── 🤖 Automation
│   ├── prompt_intelligence.py
│   ├── kie_ai_integration.py
│   ├── automation_pipeline.py
│   └── web_interface.py
├── 📚 Documentation
│   ├── README.md
│   ├── INSTALLATION.md
│   ├── AUTOMATION_GUIDE.md ⭐
│   └── QUICK_REFERENCE.md
└── 📁 Output
    ├── temp/ (generated music)
    └── output/ (final videos)
```

---

## ⚡ Performance

- **Music Generation**: 1-3 minutes (Kie.ai)
- **Video Rendering**: 30-90 minutes (CPU dependent)
- **Total**: ~35-120 minutes per video
- **Output Size**: 5-10 GB (1080p, 4 hours)

---

## 🔧 Requirements

- **Python 3.7+**
- **FFMPEG** (video processing)
- **Kie.ai API Key** (optional, for music generation)
- **8GB+ RAM** (recommended)
- **10+ GB** free disk space

---

## 🆘 Troubleshooting

### FFMPEG not found
```bash
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg  
# Linux: sudo apt install ffmpeg
```

### No API key
```bash
export KIE_API_KEY="your_key"
# Or use existing music with --skip-music flag
```

### More help
See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) for detailed troubleshooting.

---

## 🌟 Why Use This?

### For Content Creators
- ✅ Generate multiple videos efficiently
- ✅ Consistent professional quality
- ✅ Automated workflow
- ✅ YouTube-ready format

### For Developers
- ✅ Clean, modular code
- ✅ Easy to extend
- ✅ Well-documented
- ✅ Production-ready

### For Everyone
- ✅ Simple text input
- ✅ Beautiful results
- ✅ Multiple usage modes
- ✅ Free and open

---

## 📈 What's Next?

The tool is **production-ready**! Possible future enhancements:
- YouTube auto-upload integration
- More theme templates
- Mobile app
- Cloud deployment
- Multi-language support

---

## 🙏 Credits

Built with:
- **FFMPEG** - Video processing engine
- **Python 3** - Automation backbone
- **Streamlit** - Web interface
- **Kie.ai** - Music generation API

**Made with ❤️ by Antigravity AI**

---

## 📝 License

Open source - Use freely for personal or commercial projects.

---

**🎉 Start creating amazing Lofi videos today!**

```bash
streamlit run web_interface.py
```
