#!/usr/bin/env bash
# If connectivity modal is already running, close it (toggle)
PIDS=$(pgrep -f "quick-connectivity.py")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

# Close any other open quick modal (e.g. volume/brightness slider) and launch connectivity modal
pkill -f "quick-slider.py" 2>/dev/null
python3 ~/.config/waybar/scripts/connectivity/quick-connectivity.py &
