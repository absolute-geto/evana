<div align="center">

# ⚡ Evana

**All your media tools in one lightweight Windows app.**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](#)

[Download](https://github.com/absolute-geto/evana/releases/latest) •
[Report Bug](https://github.com/absolute-geto/evana/issues) •
[Request Feature](https://github.com/absolute-geto/evana/issues)

</div>

---

## 📖 About

**Evana** is a free, open-source media suite for Windows that combines four essential tools into one clean, fast desktop application:

- 🎬 **Video Downloader** — Grab videos from 1000+ sites (YouTube, TikTok, Twitter, Vimeo, Instagram...)
- 🔄 **Format Converter** — Convert between MP4, MKV, WEBM, MP3, PNG, JPG, WEBP and more (powered by FFmpeg)
- ▶️ **Media Player** — Native video/audio playback with subtitle support and speed control
- 🖼️ **Photo Gallery** — Browse entire folders with auto-generated thumbnails

No ads. No sign-up. No telemetry. Everything happens on your computer.

> ⚠️ **Beta Release** — Features may change and bugs may exist. Updates released regularly.

---

## ✨ Features

| Feature | Status |
|---|---|
| Video Downloader | ✅ Stable |
| Format Converter | ✅ Stable |
| Media Player | ✅ Stable |
| Photo Gallery | ✅ Stable |
| Dark / Light Themes | ✅ Stable |
| Auto-update | 🚧 Planned |
| Mac / Linux builds | 🚧 Planned |

---

## 💻 System Requirements

- **OS:** Windows 10 or 11 (64-bit)
- **RAM:** 4 GB minimum
- **Storage:** ~150 MB free space
- **Internet:** Required only for video downloads

---

## 📥 Installation

### Option 1: Download the installer (recommended)

1. Go to the [**Releases page**](https://github.com/absolute-geto/evana/releases/latest)
2. Download `Evana_Setup_vX.X.X.exe`
3. Run the installer and follow the on-screen instructions

### Option 2: Run from source

```bash
# Clone the repo
git clone https://github.com/absolute-geto/evana.git
cd evana

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download FFmpeg (place in assets/bin/)
# Get it from: https://ffmpeg.org/download.html

# Run
python main.py
