# LofiGen 🎵

**Professional Lofi Video Generator** — CLI + API + Python SDK

Turn a simple keyword into a complete lofi video with AI music, visual effects, and seamless looping.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

- **Seamless Looping** — Cosine-based ping-pong zoom (no glitch at loop point)
- **Multi-Scene** — Crossfade transitions between scenes
- **AI Music** — Suno via Kie.ai, with free fallback
- **AI Prompts** — Gemini / OpenRouter enhancement (optional)
- **Stock Media** — Auto-fetch from Pexels API
- **Audio Processing** — Seamless looping, normalization, effects (reverb, vinyl)
- **Text Overlays** — Quotes with fade in/out
- **YouTube Ready** — SEO metadata, thumbnail generation, upload support

---

## 🚀 Quick Start

### Install

```bash
pip install lofi-gen
```

### CLI Usage

```bash
# Generate from a theme keyword (auto-fetches media)
lofi-gen generate --theme "rain" --duration 2h

# Generate with your own image + music
lofi-gen generate --theme "cafe" --image cafe.jpg --music track.mp3 --duration 4h

# Batch generation from JSON
lofi-gen batch config.json

# List available themes
lofi-gen themes
```

### Python SDK

```python
from lofi_gen import LofiPipeline, GenerationConfig

config = GenerationConfig(
    theme="rain",
    duration=7200,  # 2 hours
    image_paths=["rain_window.jpg"],
    music_path="lofi_track.mp3",
    quotes=["Focus and relax", "Rainy day vibes"],
)

pipeline = LofiPipeline(config)
result = pipeline.run()

if result.success:
    print(f"Video: {result.output_path}")
    print(f"Size: {result.file_size_mb:.1f} MB")
```

### API Server

```bash
pip install lofi-gen[api]
uvicorn lofi_gen.api:app --host 0.0.0.0 --port 8000
```

```bash
# Start generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"theme": "rain", "duration": 7200}'

# Check status
curl http://localhost:8000/status/{job_id}

# Download result
curl -O http://localhost:8000/download/{job_id}
```

---

## 📁 Project Structure

```
lofi_gen/
├── __init__.py          # Package entry + version
├── core/
│   ├── config.py        # Dataclass configs (replaces 25-param functions)
│   ├── types.py         # Shared types (GenerationResult, JobStatus)
│   └── logging.py       # Structured logging
├── ai/
│   ├── prompt_system.py # Theme detection + prompt generation
│   ├── orchestrator.py  # Gemini ↔ OpenRouter router
│   ├── gemini_client.py # Gemini REST client
│   └── openrouter_client.py
├── media/
│   ├── video_engine.py  # FFMPEG ping-pong zoom + crossfade
│   ├── audio_engine.py  # Seamless audio looping + effects
│   ├── pexels_client.py # Stock media fetcher
│   ├── kie_client.py    # Suno music + Veo video API
│   └── free_music.py    # Fallback music provider
├── pipeline/
│   └── pipeline.py      # The ONE canonical pipeline
├── cli/
│   └── __init__.py      # Typer CLI (lofi-gen command)
└── api/
    └── __init__.py      # FastAPI backend
```

---

## ⚙️ Configuration

Set API keys via environment variables or `.env` file:

```bash
# Required for AI music generation
KIE_API_KEY=your_kie_key

# Optional: AI prompt enhancement
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional: Auto-fetch stock media
PEXELS_API_KEY=your_pexels_key
```

Works **without any API keys** — uses templates + free music fallback.

---

## 🎨 Available Themes

| Theme | BPM | Mood | Keywords |
|-------|-----|------|----------|
| rain | 60-75 | sad | مطر, rain, storm |
| cafe | 75-90 | cozy | قهوة, cafe, coffee |
| study | 65-80 | productive | دراسة, study, focus |
| sleep | 40-60 | dreamy | نوم, sleep, relax |
| space | 55-70 | ethereal | فضاء, space, galaxy |
| city | 80-95 | melancholy | مدينة, city, urban |
| ocean | 65-80 | dreamy | بحر, ocean, beach |
| retro | 80-100 | cozy | كلاسيكي, retro, vintage |
| anime | 75-95 | dreamy | انمي, anime |
| jazz | 70-95 | melancholy | جاز, jazz |
| nature | 60-75 | cozy | طبيعة, nature, forest |
| work | 85-100 | productive | عمل, work, productivity |

---

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check lofi_gen/

# Type check
mypy lofi_gen/
```

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

Please run `ruff check` and `pytest` before submitting.
