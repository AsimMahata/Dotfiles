#!/usr/bin/env bash
# Toggle GTK3 Settings Modal for Network & Layout module

PIDS=$(pgrep -f "[q]uick-net-settings.py")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

# Close other open quick modals to prevent overlap
pkill -f "quick-slider.py" 2>/dev/null
pkill -f "quick-hardware.py" 2>/dev/null
pkill -f "quick-connectivity.py" 2>/dev/null
pkill -f "island-settings.py" 2>/dev/null

# Launch settings modal
python3 ~/.config/waybar/scripts/net-layout/quick-net-settings.py &
