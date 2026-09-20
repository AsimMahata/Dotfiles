#!/usr/bin/env bash

# Cycle order: power-saver -> balanced -> performance -> power-saver
CURRENT=$(powerprofilesctl get 2>/dev/null || echo "balanced")

case "$CURRENT" in
    "power-saver")
        NEXT="balanced"
        ;;
    "balanced")
        NEXT="performance"
        ;;
    "performance"|*)
        NEXT="power-saver"
        ;;
esac

# Trigger OSD overlay HUD asynchronously immediately for instant visual feedback
pkill -f power-profile-osd.py 2>/dev/null
~/.config/waybar/scripts/power/power-profile-osd.py "$NEXT" "$CURRENT" &

# Set power profile in background and signal Waybar
powerprofilesctl set "$NEXT"

# Signal Waybar to refresh custom/power-profile instantly (RTMIN+8)
pkill -RTMIN+8 waybar 2>/dev/null
