#!/usr/bin/env bash
# Dynamic Island Settings Modal Toggle
# If already running, kill it to close; otherwise, launch it.

PIDS=$(pgrep -f "island-settings.py")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

python3 ~/.config/waybar/scripts/island/island-settings.py &
