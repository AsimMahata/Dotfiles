#!/usr/bin/env bash
# Hyprlock MPRIS Title & Artist script
# Outputs plain text: Title — Artist (max 26 chars to fit lock screen card)

status=$(playerctl status 2>/dev/null)
if [ "$status" != "Playing" ] && [ "$status" != "Paused" ]; then
    echo "No media playing"
    exit 0
fi

title=$(playerctl metadata --format '{{title}}' 2>/dev/null | sed 's/[[:space:]]*—.*//' | cut -c 1-18)
artist=$(playerctl metadata --format '{{artist}}' 2>/dev/null | cut -c 1-12)

if [ -n "$title" ]; then
    if [ -n "$artist" ]; then
        info="$title — $artist"
    else
        info="$title"
    fi
else
    info="Unknown Track"
fi

# Truncate to 26 characters max
echo "$info" | cut -c 1-26
