#!/usr/bin/env bash
# If brightness slider is already running, close it (toggle)
PIDS=$(pgrep -f "quick-slider.py --mode brightness")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

# Close any other open slider (e.g. volume) and launch brightness
pkill -f "quick-slider.py" 2>/dev/null
python3 ~/.config/waybar/scripts/quick-slider.py --mode brightness &
