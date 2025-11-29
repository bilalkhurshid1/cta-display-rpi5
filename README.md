# CTA Frame Project - Technical Documentation

## 1. Project Overview

This project creates a Raspberry Pi 5 digital CTA train arrival display with the following capabilities:

- **Fullscreen Tkinter GUI** that fills a 7" Raspberry Pi touchscreen
- **Uses the CTA Train Tracker API**
- **Displays:**
  - Station title: Paulina → Loop
  - Primary next train ETA
  - Secondary train ETA
- **Dynamic text color** that adjusts to background luminance
- **Background image** loaded from: `/home/bilal/cta-display-rpi5/background/current.jpg`
- **Background image upload** through a Flask backend, protected by a secret token, and exposed globally using Cloudflare Tunnel
- **System autostarts** both:
  - `cta-display.py` (GUI)
  - `photo_backend.py` (upload API)
- **Fullscreen + no taskbar** on reboot (Kiosk mode)

## 2. Directory Structure (Final Working State) 

```
/home/bilal/cta-display-rpi5
│
├── cta-display.py
├── photo_backend.py
├── autostart-cta.sh
├── run-cta.sh
├── CLOUDFLARE_QUICK_START.sh
├── check-tunnel.sh
│
├── requirements.txt
├── .env
├── .gitignore
│
├── background/
│   └── current.jpg
│
├── images/
│   ├── henderson.png (background for upload page)
│   ├── redbutton.png
│   ├── default.jpg (default background image)
│   ├── bilal.png (flying animation)
│   ├── joey.png (flying animation)
│   ├── clark.png (flying animation)
│   └── harry.png (flying animation)
│
├── templates/
│   └── upload.html (Flask template for upload UI)
│
├── venv/ (Python virtual environment)
│
├── cta.log
└── photo_backend.log
```

## 3. The GUI Application (cta-display.py)

### Major features implemented:

- **Full-screen Tk window** (`-fullscreen`, `-topmost`, `-zoomed`)
- **Canvas as background holder**
- **Canvas text** for overlay content
- **Automatic background reload** when file mtime changes
- **Background sampled for luminance**, determines text theme:
  - Light background → black text
  - Dark background → white text
- **API calls every 15 seconds** using:
  - `http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx`
- **Robust error handling** that prevents crashing
- **Graceful fallback text** ("No Data", "No trains", etc.)
- **Environment variable configuration** using `.env` file for API keys
- **Escape key** to exit (for debugging)

### Luminance logic:

```python
thumb = img.resize((64, 64))
arr = np.array(thumb)/255
lum = mean(0.2126*r + 0.7152*g + 0.0722*b)
# Threshold (lum > 0.55) switches theme
```

## 4. Image Upload Backend (photo_backend.py)

### Flask Application Structure

- **Flask server** running on port `5001`
- **Refactored with Flask templates** using `templates/` directory
- **Template rendering** via `render_template()` for better separation of concerns

### API Routes

- **`/upload/<SECRET_TOKEN>`** - Upload endpoint (GET shows UI, POST processes upload)
- **`/reset/<SECRET_TOKEN>`** - Reset background to default image (POST)
- **`/health`** - Health check endpoint
- **`/images/<filename>`** - Serves static images from `images/` directory

### Supported Image Formats

- JPG/JPEG
- PNG
- GIF
- WebP
- HEIC

### Upload Process

1. File validation using `secure_filename()` and extension check
2. Temporary save to `background/tmp-<timestamp>-<filename>`
3. Atomic replacement: `os.replace(tmp_path, BG_PATH)`
4. Instant background update detected by GUI via mtime change

### Enhanced Upload UI (templates/upload.html)

#### Visual Design
- **Henderson background image** covering entire viewport
- **Animated red button** with floating animation and glow effects
- **Responsive design** adapts to mobile and desktop screens
- **Accessibility features** including ARIA labels and reduced motion support

#### Interactive Features
- **Floating animation**: Gentle up-and-down motion on the upload button
- **Hover effects**: Enhanced glow and lift on interaction
- **Flying images animation**: Character images (bilal, joey, clark, harry) fly across screen on successful upload
  - 40 total images (10 iterations × 4 characters)
  - Random positioning and bi-directional animation
  - 720-degree rotation during flight
  - 3-second animation duration
- **Live feedback**: "Thank you!" → "Background updated!" with thumbnail preview
- **Reset button**: Fixed position button to restore default background

#### Animation System
- **CSS keyframe animations** for smooth floating effect
- **JavaScript-generated flying images** with dynamic positioning
- **Automatic cleanup** removes animated elements after completion
- **Respects `prefers-reduced-motion`** for accessibility

> **Important note:** `UPLOAD_TOKEN` is loaded from `.env` file.

## 5. Cloudflare Tunnel Setup (Working State)

- **Tunnel name:** `houseframe`
- **Public domain:** `frame.snappify.cc`

### Config file location:

`/etc/cloudflared/config.yml`

```yaml
tunnel: 6e8543a9-6611-4286-b612-3d813c110e0e
credentials-file: /home/bilal/.cloudflared/6e8543a9-6611-4286-b612-3d813c110e0e.json

ingress:
  - hostname: frame.snappify.cc
    service: http://localhost:5001
  - service: http_status:404
```

### Quick Setup and Health Check Scripts

- **`CLOUDFLARE_QUICK_START.sh`**: Automated setup script that guides through the entire Cloudflare tunnel setup process
- **`check-tunnel.sh`**: Comprehensive health check script that verifies:
  - Flask backend is running
  - Cloudflare tunnel service status
  - Public endpoint accessibility
  - DNS configuration
  - Configuration files

### Systemd service

**File:** `/etc/systemd/system/cloudflared.service`

```ini
[Unit]
Description=Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/cloudflared --config /etc/cloudflared/config.yml tunnel run
Restart=on-failure
User=cloudflared

[Install]
WantedBy=multi-user.target
```

**Enabled via:**

```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```
## 6. Autostart Setup

### Autostart Script

**Location:** `/home/bilal/cta-display-rpi5/autostart-cta.sh`

Enhanced version with:
- Waits for X server to be ready (up to 30 seconds)
- Waits for network connectivity (up to 30 seconds)
- Kills taskbars/panels multiple times to ensure kiosk mode
- Starts continuous panel killer background process
- Uses `unclutter` to hide mouse cursor
- Disables screen blanking and power management
- Comprehensive logging with timestamps
- Better process management

### Manual Run Script

**Location:** `/home/bilal/cta-display-rpi5/run-cta.sh`

Simplified script for manually running the display (without autostart):
- Sets up kiosk mode
- Hides cursor and taskbars
- Runs display in foreground with logging

### Desktop Entry File

**Location:** `~/.config/autostart/cta-display.desktop`

```ini
[Desktop Entry]
Type=Application
Name=CTA Display
Exec=/home/bilal/cta-display-rpi5/autostart-cta.sh
X-GNOME-Autostart-enabled=true
```
## 7. Kiosk Mode (No Taskbar)

Working state was achieved by:

1. **Installing** `raspberrypi-ui-mods`
2. **Setting window manager** to hide panel
3. **Ensuring LXPanel was removed / disabled:**
   ```bash
   mv ~/.config/lxpanel ~/.config/lxpanel.disabled
   ```
4. **Ensuring the Tk window used:**
   ```python
   root.attributes("-fullscreen", True)
   root.attributes("-topmost", True)
   root.attributes("-zoomed", True)
   ```
## 8. Networking / Upload Pipeline

**Flow:**

1. Remote app calls `https://frame.snappify.cc/upload/<secret>`
2. Cloudflare Tunnel → Pi `photo_backend.py`
3. Image saved → `current.jpg`
4. Tk app detects mtime change
5. Background updates instantly

## 9. Things to Reproduce for a Fresh Install

### ✔ Required files to restore:
- `cta-display.py`
- `photo_backend.py`
- `autostart-cta.sh`
- `run-cta.sh`
- `CLOUDFLARE_QUICK_START.sh`
- `check-tunnel.sh`
- `requirements.txt`
- `.env` (with `CTA_KEY` and `UPLOAD_TOKEN`)
- `.gitignore`
- `templates/` directory with `upload.html` template
- `images/` directory with all PNG files (henderson.png, redbutton.png, default.jpg, character PNGs)
- `~/.config/autostart/cta-display.desktop`
- `/etc/cloudflared/config.yml`
- `~/.cloudflared/<ID>.json`

### ✔ Python dependencies (via requirements.txt):
```bash
pip3 install -r requirements.txt
```

Or install system packages:
```bash
sudo apt install python3-pil.imagetk python3-numpy python3-requests \
    python3-dateutil python3-flask python3-dotenv unclutter
```

### ✔ Cloudflare setup:
Use the automated setup script:
```bash
./CLOUDFLARE_QUICK_START.sh
```

Or follow manual steps in the script.

### ✔ Kiosk mode setup:
- Install `unclutter` for cursor hiding
- Autostart script handles panel killing
- Enable autostart desktop entry

### ✔ Environment variables (.env file):
```bash
CTA_KEY=bfc31d046ce64491815093ebf7ae09d7
UPLOAD_TOKEN=<your_secret_token_here>
```

### ✔ Required directories:
```bash
mkdir -p /home/bilal/cta-display-rpi5/background
mkdir -p /home/bilal/cta-display-rpi5/images
mkdir -p /home/bilal/cta-display-rpi5/templates
mkdir -p ~/.config/autostart
```

### ✔ Health check:
```bash
./check-tunnel.sh
```
## 10. Recent Improvements

### Code Quality & Configuration
- ✅ **Environment variables**: Moved secrets to `.env` file (CTA_KEY, UPLOAD_TOKEN)
- ✅ **Virtual environment**: Added `venv/` for isolated Python dependencies
- ✅ **Requirements file**: Added `requirements.txt` for easy dependency management
- ✅ **Git integration**: Added `.gitignore` to exclude sensitive files

### User Interface Enhancements
- ✅ **Refactored Flask templates**: Moved HTML to `templates/upload.html` for better code organization
- ✅ **Enhanced upload UI**: Beautiful henderson.png background with animated red button
- ✅ **Floating animation**: Gentle up-and-down motion with CSS keyframes
- ✅ **Glow effects**: Dynamic drop-shadow effects on hover and active states
- ✅ **Flying images animation**: 40 character images fly across screen on successful upload
  - Random vertical positioning and bi-directional movement
  - 720-degree rotation during 3-second flight
  - Automatic cleanup after animation
- ✅ **Reset functionality**: One-click button to restore default background
- ✅ **Image serving**: Backend serves static images from `/images/` directory
- ✅ **Better feedback**: "Thank you!" → "Background updated!" with thumbnail preview
- ✅ **Accessibility**: ARIA labels and reduced motion support

### Operational Improvements
- ✅ **Automated Cloudflare setup**: `CLOUDFLARE_QUICK_START.sh` script
- ✅ **Health check script**: `check-tunnel.sh` for comprehensive diagnostics
- ✅ **Manual run script**: `run-cta.sh` for testing without autostart
- ✅ **Robust autostart**: Enhanced with X server wait, network wait, and better kiosk mode
- ✅ **Cursor hiding**: Uses `unclutter` to hide mouse cursor
- ✅ **Screen blanking prevention**: Disables DPMS and screen blanking
- ✅ **Continuous panel killer**: Background process to maintain kiosk mode
- ✅ **Health endpoint**: `/health` route for monitoring backend status

## 11. Known Good Behaviors

- ✅ Background successfully updated via Cloudflare
- ✅ GUI always fullscreen on boot
- ✅ No taskbar visible (continuously enforced)
- ✅ No mouse cursor visible
- ✅ API data updated every 15 seconds
- ✅ Text switched colors based on background brightness
- ✅ No crashes with robust error handling
- ✅ Cloudflare tunnel stable and auto-restarting via systemd
- ✅ Upload endpoint protected by secret token from .env
- ✅ Screen never blanks or goes to sleep

## 12. Potential Future Improvements

- 📝 Add drop shadow/outline to text for better visibility on any background
- 📝 Add offline visual indicator when CTA API is unreachable
- 📝 Add local caching of last successful train ETA
- 📝 Add web UI to change polling frequency or station
- 📝 Add support for multiple stations/routes
- 📝 Display service alerts or announcements
- 📝 HTTPS termination directly on Pi instead of Cloudflare (optional)

## 13. Conclusion

This document captures the exact state of the project at the moment everything was stable:

- ✅ GUI working flawlessly
- ✅ Fullscreen kiosk mode
- ✅ Autostart correct
- ✅ Upload API working
- ✅ Cloudflare tunnel correctly configured
- ✅ Dynamic text color
- ✅ Background auto-refresh