#!/usr/bin/env bash
# If volume slider is already running, close it (toggle)
PIDS=$(pgrep -f "quick-slider.py --mode volume")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

# Close any other open slider (e.g. brightness) and launch volume
pkill -f "quick-slider.py" 2>/dev/null
python3 ~/.config/waybar/scripts/quick-slider.py --mode volume &
