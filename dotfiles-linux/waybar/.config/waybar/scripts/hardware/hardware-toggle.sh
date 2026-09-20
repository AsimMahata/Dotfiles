#!/usr/bin/env bash
# If hardware modal is already running, close it (toggle)
PIDS=$(pgrep -f "quick-hardware.py")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

# Close any other open quick modals and launch hardware modal
pkill -f "quick-slider.py" 2>/dev/null
pkill -f "quick-connectivity.py" 2>/dev/null
python3 ~/.config/waybar/scripts/hardware/quick-hardware.py &
