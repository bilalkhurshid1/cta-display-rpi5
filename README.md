# CTA Frame Project - Technical Documentation

> Complete technical state of project (working fullscreen on reboot)  
> Brain dump / migration reference

## 1. Project Overview

This project creates a Raspberry Pi 5 digital CTA train arrival display with the following capabilities:

- **Fullscreen Tkinter GUI** that fills a 7" Raspberry Pi touchscreen
- **Uses the CTA Train Tracker API**
- **Displays:**
  - Station title: Paulina → Loop
  - Primary next train ETA
  - Secondary train ETA
- **Dynamic text color** that adjusts to background luminance
- **Background image** loaded from: `/home/bilal/cta-frame/background/current.jpg`
- **Background image upload** through a Flask backend, protected by a secret token, and exposed globally using Cloudflare Tunnel
- **System autostarts** both:
  - `cta-display.py` (GUI)
  - `photo_backend.py` (upload API)
- **Fullscreen + no taskbar** on reboot (Kiosk mode)

## 2. Directory Structure (Final Working State)

```
/home/bilal/cta-frame
│
├── cta-display.py
├── autostart-cta.sh
├── photo_backend.py
│
├── background/
│   └── current.jpg
│
├── cta.log
├── photo_backend.log
│
└── .env (optional)
```

## 3. The GUI Application (cta-display.py)

### Major features implemented:

- **Full-screen Tk window** (`-fullscreen`, `-topmost`, `-zoomed`)
- **Canvas as background holder**
- **Labels drawn over the image** instead of canvas text
- **Automatic background reload** when file mtime changes
- **Background sampled for luminance**, determines text theme:
  - Light background → black text
  - Dark background → white text
- **API calls every 15 seconds** using:
  - `http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx`
- **Robust error handling** that prevents crashing
- **Graceful fallback text** ("No Data", "No trains", etc.)

### Luminance logic:

```python
thumb = img.resize((64, 64))
arr = np.array(thumb)/255
lum = mean(0.2126*r + 0.7152*g + 0.0722*b)
# Threshold (lum > 0.55) switches theme
```

## 4. Image Upload Backend (photo_backend.py)

- **Flask server** running on port `5001`
- **Route:** `/upload/<SECRET_TOKEN>`
- **Accepts any of:**
  - JPG
  - PNG
  - GIF
  - WebP
  - HEIC
- **Saves as:**
  - `background/tmp-<timestamp>-<filename>`
  - Then atomically: `os.replace(tmp_path, BG_PATH)`
- **HTML upload form** with drag-and-drop

> **Important note:** `SECRET_TOKEN` must either be hardcoded or loaded from environment.

## 5. Cloudflare Tunnel Setup (Working State)

- **Tunnel name:** `houseframe`
- **Public domain:** `frame.snappify.cc`

### Config file location:

`/etc/cloudflared/config.yml`

```yaml
tunnel: 6e8543a9-6611-4286-b612-3d813c110e0e
credentials-file: /etc/cloudflared/6e8543a9-6611-4286-b612-3d813c110e0e.json

ingress:
  - hostname: frame.snappify.cc
    service: http://localhost:5001
  - service: http_status:404
```

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

**Location:** `/home/bilal/cta-frame/autostart-cta.sh`

```bash
#!/bin/bash
set -e

APP_DIR="/home/bilal/cta-frame"
DISPLAY_LOG="$APP_DIR/cta.log"
BACKEND_LOG="$APP_DIR/photo_backend.log"

sleep 12

export DISPLAY=:0
export XAUTHORITY=/home/bilal/.Xauthority

cd "$APP_DIR"

if ! pgrep -f "photo_backend.py" > /dev/null; then
    echo "[start-cta] Starting photo_backend.py" >> "$BACKEND_LOG"
    python3 photo_backend.py >> "$BACKEND_LOG" 2>&1 &
fi

echo "[start-cta] Starting cta-display.py" >> "$DISPLAY_LOG"
python3 cta-display.py >> "$DISPLAY_LOG" 2>&1
```

### Desktop Entry File

**Location:** `~/.config/autostart/cta-display.desktop`

```ini
[Desktop Entry]
Type=Application
Name=CTA Display
Exec=/home/bilal/cta-frame/autostart-cta.sh
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
- `cta-env` (optional)
- `~/.config/autostart/cta-display.desktop`
- `/etc/cloudflared/config.yml`
- `/etc/cloudflared/<ID>.json`

### ✔ Required system packages:
```bash
sudo apt install python3-pil.imagetk python3-numpy python3-requests \
    python3-dateutil python3-flask cloudflared
```

### ✔ Kiosk mode setup:
- Disable LXPanel or hide panel
- Enable autostart desktop entry

### ✔ API key:
```python
CTA_KEY = "bfc31d046ce64491815093ebf7ae09d7"
```

### ✔ Required directories:
```bash
mkdir -p /home/bilal/cta-frame/background
mkdir -p ~/.config/autostart
```
## 10. Known Good Behaviors Before Breakage

- ✅ Background successfully updated via Cloudflare
- ✅ GUI always fullscreen on boot
- ✅ No taskbar visible
- ✅ API data updated every 15 seconds
- ✅ Text switched colors based on background brightness
- ✅ No crashes
- ✅ Cloudflare tunnel stable and auto-restarting via systemd
- ✅ Upload endpoint protected by secret token

## 11. Remaining Improvements Not Implemented

- 📝 Add drop shadow text for more clarity
- 📝 Add offline visual indicator
- 📝 Add local caching of last successful train ETA
- 📝 Add web UI to change polling frequency
- 📝 HTTPS termination directly on Pi instead of Cloudflare (optional)

## 12. Conclusion

This document captures the exact state of the project at the moment everything was stable:

- ✅ GUI working flawlessly
- ✅ Fullscreen kiosk mode
- ✅ Autostart correct
- ✅ Upload API working
- ✅ Cloudflare tunnel correctly configured
- ✅ Dynamic text color
- ✅ Background auto-refresh

**You can now re-create the environment from scratch safely.**