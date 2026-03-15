# Installation Guide - Lofi YouTube Video Generator

This guide will walk you through installing all necessary dependencies to run the Lofi YouTube Video Generator.

## Prerequisites

- **Python 3.7 or higher** - [Download Python](https://www.python.org/downloads/)
- **FFMPEG** - Installation instructions below

## Step 1: Install FFMPEG

FFMPEG is the core video processing engine. Choose your operating system:

### Windows Installation

#### Option A: Using Chocolatey (Recommended)

1. **Install Chocolatey** (if not already installed):
   - Open PowerShell as Administrator
   - Run: 
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
     ```

2. **Install FFMPEG**:
   ```powershell
   choco install ffmpeg
   ```

3. **Verify installation**:
   ```powershell
   ffmpeg -version
   ```

#### Option B: Manual Installation

1. **Download FFMPEG**:
   - Go to [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Click "Windows" → Select a build (e.g., gyan.dev)
   - Download "ffmpeg-release-full.7z"

2. **Extract and Add to PATH**:
   - Extract the archive (use 7-Zip)
   - Copy the `bin` folder path (e.g., `C:\ffmpeg\bin`)
   - Press `Win + X` → System → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" → Edit
   - Click "New" and paste the bin folder path
   - Click OK on all dialogs

3. **Verify installation**:
   - Open a new Command Prompt
   - Run: `ffmpeg -version`

---

### Linux Installation

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Fedora/RHEL/CentOS:
```bash
sudo dnf install ffmpeg
```

#### Arch Linux:
```bash
sudo pacman -S ffmpeg
```

#### Verify installation:
```bash
ffmpeg -version
```

---

### macOS Installation

#### Using Homebrew (Recommended):

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install FFMPEG**:
   ```bash
   brew install ffmpeg
   ```

3. **Verify installation**:
   ```bash
   ffmpeg -version
   ```

---

## Step 2: Install Python Dependencies

The script uses Python's standard library, so no additional packages are strictly required. However, you can optionally install ffmpeg-python for future enhancements:

```bash
# Optional - not required for current version
pip install ffmpeg-python
```

---

## Step 3: Download the Script

1. Download or clone the Lofi Video Generator files:
   - `lofi_video_generator.py` - Main script
   - `config.py` - Configuration settings
   - `ffmpeg_utils.py` - Utility functions

2. Place all files in the same directory

---

## Step 4: Verify Installation

Run the script with `--help` to ensure everything is working:

```bash
python lofi_video_generator.py --help
```

You should see the help message with usage instructions.

---

## Troubleshooting

### "FFMPEG is not installed or not in PATH"

**Windows:**
- Restart your terminal/PowerShell after installing FFMPEG
- Verify FFMPEG is in PATH: `echo $env:PATH` should include the FFMPEG bin directory

**Linux/macOS:**
- Run `which ffmpeg` to check if it's found
- Try `sudo apt install ffmpeg` or `brew install ffmpeg` again

### "Python is not recognized"

- Make sure Python is installed and added to PATH
- Try `python3` instead of `python` on Linux/macOS

### Permission Errors

**Windows:**
- Run PowerShell as Administrator

**Linux/macOS:**
- Use `sudo` for installation commands
- Ensure output directory has write permissions

---

## Next Steps

Once installation is complete, proceed to [README.md](README.md) for usage instructions and examples.

---

## System Requirements

### Minimum:
- **CPU**: Quad-core processor
- **RAM**: 8 GB
- **Storage**: 10 GB free space (for output file)

### Recommended for Faster Rendering:
- **CPU**: 8+ core processor
- **RAM**: 16 GB
- **Storage**: SSD with 20+ GB free space
- **GPU**: NVIDIA GPU (for hardware acceleration - advanced users)

---

## Getting Help

If you encounter issues:
1. Check that FFMPEG is installed: `ffmpeg -version`
2. Verify all input files exist and are valid media files
3. Check available disk space (a 4-hour 1080p video needs ~5-10 GB)
4. Try running with a shorter test video first
