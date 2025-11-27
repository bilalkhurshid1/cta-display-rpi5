#!/bin/bash
set -e

export DISPLAY=:0
export XAUTHORITY=/home/bilal/.Xauthority

# Kill any existing panel
pkill lxpanel 2>/dev/null || true

cd /home/bilal/cta-display-rpi5
python3 cta-display.py
