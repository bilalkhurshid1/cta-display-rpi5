#!/bin/bash
set -e

APP_DIR="/home/bilal/cta-display-rpi5"
DISPLAY_LOG="$APP_DIR/cta.log"
BACKEND_LOG="$APP_DIR/photo_backend.log"

# Give network + X time to come up
sleep 12

export DISPLAY=:0
export XAUTHORITY=/home/bilal/.Xauthority

cd "$APP_DIR"

# Start the upload backend in the background if not already running
if ! pgrep -f "photo_backend.py" > /dev/null; then
  echo "[start-cta] Starting photo_backend.py" >> "$BACKEND_LOG"
  python3 photo_backend.py >> "$BACKEND_LOG" 2>&1 &
fi

# Start the CTA display (foreground)
echo "[start-cta] Starting cta-display.py" >> "$DISPLAY_LOG"
python3 cta-display.py >> "$DISPLAY_LOG" 2>&1