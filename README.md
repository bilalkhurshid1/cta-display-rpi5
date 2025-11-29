# CTA Frame Project - Technical Documentation

**Modular, Production-Ready Architecture** | Raspberry Pi 5 | 7" Touchscreen Display

## 1. Project Overview

This project creates a Raspberry Pi 5 digital CTA train arrival display with a **clean, modular architecture** designed for maintainability and extensibility.

### Core Capabilities

- **Fullscreen Tkinter GUI** that fills a 7" Raspberry Pi touchscreen
- **CTA Train Tracker API Integration** with real-time arrival data
- **Live Display Information:**
  - Station title: Paulina → Loop
  - Primary next train ETA (large, bold)
  - Secondary train ETA (smaller)
- **Interactive Features:**
  - Touch animations with bubble effects
  - Smooth ripple transitions
  - Dynamic text color adapting to background brightness
- **Remote Image Upload:**
  - Flask backend with beautiful web UI
  - Protected by secret token authentication
  - Exposed globally via Cloudflare Tunnel
- **Production Features:**
  - Modular Python architecture (4 specialized modules)
  - Type hints throughout for IDE support
  - Clean separation of concerns
  - Robust error handling
  - System autostart on boot
  - Fullscreen kiosk mode (no taskbar)

## 2. Directory Structure (Final Working State) 

```
/home/bilal/cta-display-rpi5
│
├── cta-display.py           # Main application (178 lines)
├── animations.py            # Animation effects module (180 lines)
├── cta_api.py              # CTA API client module (90 lines)
├── image_utils.py          # Image processing module (115 lines)
├── photo_backend.py        # Flask upload backend (105 lines)
│
├── autostart-cta.sh        # Autostart script
├── run-cta.sh             # Manual run script
├── cloudflare_setup.sh    # Cloudflare setup script
├── check-tunnel.sh        # Health check script
│
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (secrets)
├── .gitignore           # Git ignore patterns
│
├── background/
│   └── current.jpg       # Active background image
│
├── images/
│   ├── henderson.png     # Upload page background
│   ├── redbutton.png     # Upload button image
│   ├── default.jpg       # Default background image
│   ├── bilal.png        # Flying animation character
│   ├── joey.png         # Flying animation character
│   ├── clark.png        # Flying animation character
│   └── harry.png        # Flying animation character
│
├── templates/
│   └── upload.html       # Flask template for upload UI
│
├── venv/                # Python virtual environment
│
├── cta.log             # Display app logs
└── photo_backend.log   # Backend app logs
```

## 3. The GUI Application - Modular Architecture

### Application Structure (Refactored)

#### **Main Application: `cta-display.py`**
- Application entry point and orchestration
- Tkinter UI setup and configuration
- Component initialization and coordination
- Update loop and display logic

#### **Animation Module: `animations.py`**
- **`BubbleAnimation` class**: Touch/click bubble effects
  - Spawns 3-5 bubbles on user interaction
  - Animated movement with physics (velocity, drift)
  - Automatic lifecycle management
- **`RippleAnimation` class**: Background transition effects
  - Ripple effect from screen center
  - Staggered animations (3 ripples)
  - Layered rendering above background

#### **CTA API Module: `cta_api.py`**
- **`CTAClient` class**: Clean API abstraction
  - Configurable route and destination filtering
  - Robust error handling
  - Returns structured train data
  - Calls: `http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx`
  - Polls every 15 seconds

#### **Image Utilities Module: `image_utils.py`**
- **`BackgroundManager` class**: Background image management
  - Automatic reload on file modification (mtime detection)
  - Image resizing and optimization
  - Canvas integration
- **`compute_luminance()`**: ITU-R BT.709 brightness calculation
  - Formula: `0.2126*R + 0.7152*G + 0.0722*B`
  - Returns luminance in range [0, 1]
- **`get_text_color_for_background()`**: Adaptive text theming
  - Light background (lum > 0.55) → black text
  - Dark background (lum ≤ 0.55) → white text

### Core Features

- **Full-screen Tkinter GUI** with kiosk mode
- **Dynamic text color** adapts to background brightness
- **Touch animations** with bubble effects
- **Smooth transitions** with ripple animations
- **Automatic background updates** when file changes
- **Robust error handling** prevents crashes
- **Graceful fallbacks**: "No Data", "No trains", etc.
- **Environment-based configuration** via `.env` file
- **Type hints** throughout for better IDE support
- **Escape key** to exit (debugging)

## 4. Image Upload Backend (photo_backend.py)

### Flask Application Structure

- **Flask server** running on port `5001`
- **Template rendering** via `render_template()` for proper separation of concerns
- **Clean Python logic**: Only application code in `.py` file

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

## 5. Cloudflare Tunnel Setup 

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

**Python Application Files:**
- `cta-display.py` - Main application
- `animations.py` - Animation effects module
- `cta_api.py` - CTA API client module
- `image_utils.py` - Image processing module
- `photo_backend.py` - Flask backend

**Configuration & Scripts:**
- `autostart-cta.sh` - Autostart script
- `run-cta.sh` - Manual run script
- `cloudflare_setup.sh` - Cloudflare setup script
- `check-tunnel.sh` - Health check script
- `requirements.txt` - Python dependencies
- `.env` (with `CTA_KEY` and `UPLOAD_TOKEN`)
- `.gitignore` - Git ignore patterns

**Templates & Assets:**
- `templates/` directory with `upload.html` template
- `images/` directory with all PNG files (henderson.png, redbutton.png, default.jpg, character PNGs)

**System Configuration:**
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

## 10. Known Good Behaviors

- ✅ Background successfully updated via Cloudflare
- ✅ GUI always fullscreen on boot
- ✅ No taskbar visible (continuously enforced)
- ✅ No mouse cursor visible
- ✅ API data updated every 15 seconds
- ✅ Text switched colors based on background brightness
- ✅ Touch animations working (bubble effects)
- ✅ Ripple transitions on background changes
- ✅ No crashes with robust error handling
- ✅ Cloudflare tunnel stable and auto-restarting via systemd
- ✅ Upload endpoint protected by secret token from .env
- ✅ Screen never blanks or goes to sleep
- ✅ Modular architecture with clean imports
- ✅ Type hints working with IDE autocomplete

## 11. Potential Future Improvements

- 📝 Add support for multiple stations/routes
- 📝 Add drop shadow/outline to text for better visibility on any background
- 📝 Add offline visual indicator when CTA API is unreachable
- 📝 Add web UI to change station
- 📝 Display service alerts or announcements
- 📝 Unit tests for modules
- 📝 Configuration file for display settings
- 📝 HTTPS termination directly on Pi instead of Cloudflare (optional)

## 14. Conclusion

This document captures the current state of the project with **production-ready architecture**:

### ✅ Core Functionality
- GUI working flawlessly
- Fullscreen kiosk mode with continuous enforcement
- Autostart working on boot
- Upload API working
- Cloudflare tunnel correctly configured
- Dynamic text color based on background luminance
- Background auto-refresh on file changes

### 🎯 Production Ready
The codebase is now production-ready with industry-standard architecture patterns, making it easy to maintain, extend, and debug.