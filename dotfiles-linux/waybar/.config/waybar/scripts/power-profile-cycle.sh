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

powerprofilesctl set "$NEXT"

# Trigger OSD overlay HUD asynchronously
~/.config/waybar/scripts/power-profile-osd.py "$NEXT" &
