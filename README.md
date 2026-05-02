# LofiGen Pro 🎵

**Professional Lofi Video Generator** — CLI + API + SaaS-Ready

Turn a keyword like "قهوة الصباح" into a complete 4-hour lofi video with AI music, seamless looping, and YouTube-ready output.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker Ready](https://img.shields.io/badge/docker-ready-blue.svg)](docker-compose.yml)

---

## ✨ Features

- **🎬 Seamless Looping** — Cosine ping-pong zoom (no glitch at loop point)
- **🎵 AI Music** — Suno via Kie.ai, with free fallback
- **🤖 AI Prompts** — Gemini/OpenRouter enhancement (optional)
- **🖼️ Stock Media** — Auto-fetch from Pexels API
- **🔊 Audio Processing** — Looping, normalization, effects
- **🌐 Web Interface** — Streamlit UI with Arabic support
- **⚡ REST API** — FastAPI with auth + job queue
- **🐳 Docker Ready** — One-command deployment

---

## 📦 Installation

### Option 1: Docker (Recommended) ⭐

**Requirements:**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

**Steps:**

```bash
# 1. Clone repository
git clone https://github.com/yourname/lofigen-pro.git
cd lofigen-pro

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (see API Keys section below)

# 3. Start all services
docker-compose up -d

# 4. Create first user
docker-compose exec api python -c "
from lofi_gen.db.connection import engine
from lofi_gen.db.models import Base
Base.metadata.create_all(bind=engine)
print('Database initialized!')
"

# 5. Access services
API:   http://localhost:8000/docs
Web:   http://localhost:8501
```

---

### Option 2: Local Development (Without Docker)

**Requirements:**
- Python 3.10+
- FFMPEG 4.4+ (with libx264)
- PostgreSQL 14+ (optional, can use SQLite)
- Redis 7+ (optional, for queue)

**Step 1: Install FFMPEG**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg -y
ffmpeg -version  # Verify
```

**macOS:**
```bash
brew install ffmpeg
ffmpeg -version  # Verify
```

**Windows:**
```powershell
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH
```

**Step 2: Install Python Dependencies**

```bash
# Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install package
pip install -e ".[api,all]"
```

**Step 3: Configure Database (Optional)**

```bash
# Option A: SQLite (simplest, no setup)
# No action needed — used by default

# Option B: PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu
brew install postgresql  # macOS

# Create database
sudo -u postgres psql -c "CREATE DATABASE lofidb;"
sudo -u postgres psql -c "CREATE USER lofi WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lofidb TO lofi;"

# Set environment variable
export DATABASE_URL="postgresql://lofi:yourpassword@localhost:5432/lofidb"
```

**Step 4: Configure Redis (Optional)**

```bash
# Ubuntu/macOS
sudo apt install redis-server  # Ubuntu
brew install redis  # macOS

# Start Redis
redis-server

# Set environment variable
export REDIS_URL="redis://localhost:6379/0"
```

**Step 5: Configure API Keys**

```bash
cp .env.example .env
# Edit .env with your keys (see API Keys section)
```

---

## 🚀 Usage

### CLI (Command Line)

```bash
# Generate with theme only (auto-fetches media)
python -m lofi_gen.cli generate --theme "rain" --duration 2h

# With custom image + music
python -m lofi_gen.cli generate \
  --theme "cafe" \
  --image rain_window.jpg \
  --music lofi_track.mp3 \
  --duration 4h

# Batch generation from JSON
python -m lofi_gen.cli batch config.json

# List available themes
python -m lofi_gen.cli themes
```

### Web Interface

```bash
# Local
python -m lofi_gen.web

# Or with Streamlit directly
streamlit run lofi_gen/web/__init__.py
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

### API (REST)

```bash
# Start API server
python -m lofi_gen.api

# Or with uvicorn
uvicorn lofi_gen.api_v2:app --host 0.0.0.0 --port 8000

# Create user (get API key)
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "tier": "pro"}'

# Generate video
curl -X POST http://localhost:8000/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "rain",
    "duration": 7200,
    "fps": 30,
    "quality": "medium"
  }'

# Check status
curl http://localhost:8000/status/JOB_ID \
  -H "Authorization: Bearer YOUR_API_KEY"

# Download result
curl -O http://localhost:8000/download/JOB_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## 🔑 API Keys Setup

### Required Keys

| Service | Purpose | Get Key From |
|---------|---------|--------------|
| **Kie.ai** | AI music generation | https://kie.ai/dashboard |
| **Pexels** | Stock photos/videos | https://www.pexels.com/api |

### Optional Keys

| Service | Purpose | Get Key From |
|---------|---------|--------------|
| **Gemini** | AI prompt enhancement | https://aistudio.google.com/app/apikey |
| **OpenRouter** | Free AI alternative | https://openrouter.ai/keys |

### .env File Example

```env
# Required
KIE_API_KEY=your_kie_key_here
PEXELS_API_KEY=your_pexels_key_here

# Optional (for AI enhancement)
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
AI_PROVIDER=auto

# Database (for local setup)
DATABASE_URL=postgresql://lofi:password@localhost:5432/lofidb
REDIS_URL=redis://localhost:6379/0
```

---

## ☁️ VPS / Cloud Deployment

### Option 1: Docker on VPS (Recommended)

**Requirements:**
- Ubuntu 20.04+ / Debian 11+
- 2 CPU cores, 4GB RAM, 20GB SSD

**Deployment:**

```bash
# 1. SSH to your VPS
ssh user@your-vps-ip

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Clone and configure
git clone https://github.com/yourname/lofigen-pro.git
cd lofigen-pro
cp .env.example .env
nano .env  # Add your API keys

# 4. Production deployment
# Use production compose file (no reload, optimized workers)
docker-compose -f docker-compose.prod.yml up -d

# 5. Check status
docker-compose ps
docker-compose logs -f api

# 6. Create admin user
docker-compose exec api python -c "
from lofi_gen.db.connection import engine
from lofi_gen.db.models import Base, User, UserTier
import uuid
Base.metadata.create_all(bind=engine)
u = User(email='admin@example.com', api_key='lg_' + uuid.uuid4().hex, tier=UserTier.PRO)
# Add to DB...
print('Admin created!')
"
```

**With Nginx Reverse Proxy:**

```nginx
# /etc/nginx/sites-available/lofigen
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /download/ {
        alias /app/output/;
    }
}
```

### Option 2: Manual VPS Setup (Without Docker)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip ffmpeg postgresql redis-server nginx git

# 3. Setup PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE lofidb;"
sudo -u postgres psql -c "CREATE USER lofi WITH PASSWORD 'strongpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lofidb TO lofi;"

# 4. Setup Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 5. Clone and install
git clone https://github.com/yourname/lofigen-pro.git
cd lofigen-pro
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[api,all]"

# 6. Configure environment
sudo nano /etc/systemd/system/lofigen-api.service
```

**Systemd Service:**

```ini
# /etc/systemd/system/lofigen-api.service
[Unit]
Description=LofiGen API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=lofi
WorkingDirectory=/home/lofi/lofigen-pro
Environment="DATABASE_URL=postgresql://lofi:strongpassword@localhost:5432/lofidb"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="KIE_API_KEY=your_key"
Environment="PEXELS_API_KEY=your_key"
ExecStart=/home/lofi/lofigen-pro/venv/bin/uvicorn lofi_gen.api_v2:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable lofigen-api
sudo systemctl start lofigen-api
sudo systemctl status lofigen-api
```

---

## 🔧 Troubleshooting

### FFMPEG Not Found

```bash
# Check installation
which ffmpeg
ffmpeg -version

# If not found, install or add to PATH
export PATH="$PATH:/path/to/ffmpeg"
```

### Database Connection Error

```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Check connection
psql postgresql://lofi:password@localhost:5432/lofidb -c "SELECT 1;"
```

### Redis Connection Error

```bash
# Check Redis running
redis-cli ping  # Should return PONG

# Check connection
curl http://localhost:6379
```

### Docker Issues

```bash
# Rebuild images
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker
```

---

## 📁 Project Structure

```
lofi_gen/
├── core/          # Config, types, logging
├── ai/            # Prompt system, AI orchestrator
├── media/         # Video/audio engines, API clients
├── db/            # PostgreSQL models
├── pipeline/      # Main video pipeline
├── cli/           # Command line interface
├── api/           # FastAPI v1 (simple)
├── api_v2.py      # FastAPI v2 (with auth + DB)
├── web/           # Streamlit interface
├── tasks.py       # Celery background jobs
└── auth.py        # API authentication

docker-compose.yml         # Development
docker-compose.prod.yml    # Production
Dockerfile                 # Image definition
pyproject.toml             # Package definition
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 🤝 Support

- 📧 Email: support@yourdomain.com
- 💬 Discord: [your discord link]
- 🐛 Issues: [GitHub Issues](https://github.com/yourname/lofigen-pro/issues)

---

**Made with ❤️ for the Lofi Community**

---

**تم تحديث README.md بالكامل مع تعليمات التثبيت المحلي وعلى VPS** ✅
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
