# ☁️ Deployment Guide for Lofi Video Generator

This guide explains how to set up your automation tool on a Linux VPS (Ubuntu 22.04).

## 🛠️ Step 1: Server Preparation
Update your system and install core dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install ffmpeg git python3-pip python3-venv screen -y
```

## 📂 Step 2: Project Setup
Clone your repository and setup the Python environment:
```bash
git clone <your-repo-url>
cd viideo

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## ⚙️ Step 3: Firewall Configuration
Open the Streamlit port (8501) to access the UI:
```bash
sudo ufw allow 8501
```

## 🚀 Step 4: Running the App (Persistent)
Use `screen` to keep the app running after you disconnect:
```bash
# Start a new screen session
screen -S lofi

# Run the interface
streamlit run web_interface.py --server.port 8501 --server.address 0.0.0.0
```
*To detach:* Press `Ctrl+A` then `D`.
*To reattach:* Run `screen -r lofi`.

## 💡 Production Tips
1. **FFmpeg Hardware Acceleration:** If your VPS has a GPU (like AWS G4 instances), change `VIDEO_CODEC` in `config.py` to `h264_nvenc` for 10x faster rendering.
2. **Storage Management:** Since 4-hour videos are large (~2-5GB), consider adding an external volume or S3 bucket if you plan to keep archives.
3. **API Keys:** Make sure to set your `KIE_API_KEY` and `PEXELS_API_KEY` in `config.py` or as environment variables on the server.
