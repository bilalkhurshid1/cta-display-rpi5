#!/bin/bash
set -e

APP_DIR="/home/bilal/cta-display-rpi5"
DISPLAY_LOG="$APP_DIR/cta.log"
BACKEND_LOG="$APP_DIR/photo_backend.log"

# Ensure log directory exists
mkdir -p "$APP_DIR"

# Initialize logs with startup timestamp
echo "========================================" >> "$DISPLAY_LOG"
echo "[autostart-cta] Script started at $(date)" >> "$DISPLAY_LOG"
echo "========================================" >> "$BACKEND_LOG"
echo "[autostart-cta] Script started at $(date)" >> "$BACKEND_LOG"

# Wait for X server to be ready
echo "[autostart-cta] Waiting for X server..." >> "$DISPLAY_LOG"
for i in {1..30}; do
  if xset q &>/dev/null; then
    echo "[autostart-cta] X server is ready (attempt $i)" >> "$DISPLAY_LOG"
    break
  fi
  sleep 1
done

# Wait for network to be ready
echo "[autostart-cta] Waiting for network..." >> "$DISPLAY_LOG"
for i in {1..30}; do
  if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "[autostart-cta] Network is ready (attempt $i)" >> "$DISPLAY_LOG"
    break
  fi
  sleep 1
done

export DISPLAY=:0
export XAUTHORITY=/home/bilal/.Xauthority

# Kill all taskbars/panels for kiosk mode (first pass)
echo "[autostart-cta] Hiding taskbars and panels..." >> "$DISPLAY_LOG"
pkill lxpanel 2>/dev/null || true
pkill lxqt-panel 2>/dev/null || true
pkill waybar 2>/dev/null || true
pkill xfce4-panel 2>/dev/null || true
pkill mate-panel 2>/dev/null || true
pkill plank 2>/dev/null || true
pkill pcmanfm 2>/dev/null || true

# Wait a moment for panels to fully terminate
sleep 1

# Kill again in case they're auto-restarting
echo "[autostart-cta] Second panel kill pass..." >> "$DISPLAY_LOG"
pkill lxpanel 2>/dev/null || true
pkill lxqt-panel 2>/dev/null || true
pkill waybar 2>/dev/null || true
pkill xfce4-panel 2>/dev/null || true
pkill mate-panel 2>/dev/null || true
pkill plank 2>/dev/null || true
pkill pcmanfm 2>/dev/null || true

# Start a background process to continuously kill panels
echo "[autostart-cta] Starting continuous panel killer..." >> "$DISPLAY_LOG"
(
  while true; do
    sleep 3
    pkill lxpanel 2>/dev/null || true
    pkill lxqt-panel 2>/dev/null || true
    pkill waybar 2>/dev/null || true
    pkill xfce4-panel 2>/dev/null || true
    pkill mate-panel 2>/dev/null || true
    pkill plank 2>/dev/null || true
    pkill pcmanfm 2>/dev/null || true
  done
) &

# Hide mouse cursor after 0.1 seconds of inactivity
if command -v unclutter &> /dev/null; then
  echo "[autostart-cta] Starting unclutter to hide cursor..." >> "$DISPLAY_LOG"
  unclutter -idle 0.1 -root &
else
  echo "[autostart-cta] Warning: unclutter not installed, cursor will be visible" >> "$DISPLAY_LOG"
fi

# Disable screen blanking and power management
echo "[autostart-cta] Disabling screen blanking..." >> "$DISPLAY_LOG"
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true

cd "$APP_DIR"

# Start the upload backend in the background if not already running
if ! pgrep -f "photo_backend.py" > /dev/null; then
  echo "[autostart-cta] Starting photo_backend.py at $(date)" >> "$BACKEND_LOG"
  python3 photo_backend.py >> "$BACKEND_LOG" 2>&1 &
  echo "[autostart-cta] photo_backend.py started with PID $!" >> "$BACKEND_LOG"
else
  echo "[autostart-cta] photo_backend.py already running" >> "$BACKEND_LOG"
fi

# Start the CTA display (foreground)
echo "[autostart-cta] Starting cta-display.py at $(date)" >> "$DISPLAY_LOG"
echo "[autostart-cta] Working directory: $(pwd)" >> "$DISPLAY_LOG"
echo "[autostart-cta] Python version: $(python3 --version)" >> "$DISPLAY_LOG"
python3 cta-display.py >> "$DISPLAY_LOG" 2>&1

# If we get here, the display script exited
echo "[autostart-cta] cta-display.py exited at $(date)" >> "$DISPLAY_LOG"