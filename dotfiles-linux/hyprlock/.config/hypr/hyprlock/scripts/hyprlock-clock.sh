#!/usr/bin/env bash
# Two-tone clock output for Hyprlock
# White hours : Accent blue minutes

hour=$(date +"%H")
minute=$(date +"%M")

accent="#9ecafc"
if [ -f "$HOME/.config/hypr/colors.conf" ]; then
    hex=$(grep -E '^\$primary[[:space:]]*=' "$HOME/.config/hypr/colors.conf" | grep -oE '[0-9a-fA-F]{6}' | head -n1)
    if [ -n "$hex" ]; then
        accent="#$hex"
    fi
fi

echo "<span weight='bold'>$hour : <span foreground='$accent'>$minute</span></span>"
