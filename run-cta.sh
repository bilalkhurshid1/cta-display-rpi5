#!/bin/bash
set -e

APP_DIR="/home/bilal/cta-display-rpi5"
LOG_FILE="$APP_DIR/cta.log"

export DISPLAY=:0
export XAUTHORITY=/home/bilal/.Xauthority

# Kill all taskbars/panels for kiosk mode
echo "[run-cta] Hiding taskbars and panels..."
pkill lxpanel 2>/dev/null || true
pkill lxqt-panel 2>/dev/null || true
pkill waybar 2>/dev/null || true
pkill xfce4-panel 2>/dev/null || true
pkill mate-panel 2>/dev/null || true
pkill plank 2>/dev/null || true
pkill pcmanfm 2>/dev/null || true

# Start continuous panel killer in background
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

# Hide mouse cursor
if command -v unclutter &> /dev/null; then
  echo "[run-cta] Starting unclutter to hide cursor..."
  unclutter -idle 0.1 -root &
fi

# Disable screen blanking
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true

cd "$APP_DIR"

# Log and run
echo "========================================" >> "$LOG_FILE"
echo "[run-cta] Starting cta-display.py at $(date)" >> "$LOG_FILE"
python3 cta-display.py 2>&1 | tee -a "$LOG_FILE"