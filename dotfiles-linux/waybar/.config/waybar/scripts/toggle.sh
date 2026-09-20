#!/bin/bash

WAYBAR_DIR="$HOME/.config/waybar"
CURRENT=$(readlink -f "$WAYBAR_DIR/config.jsonc")

if [[ "$CURRENT" == *"music"* ]]; then
    ln -sfn "profiles/default/config.jsonc" "$WAYBAR_DIR/config.jsonc"
    notify-send -a "Waybar" "Waybar Profile" "Switched to Default Bar" -t 1500 -i audio-speakers
else
    ln -sfn "profiles/music/config.jsonc" "$WAYBAR_DIR/config.jsonc"
    notify-send -a "Waybar" "Waybar Profile" "Switched to Music Bar" -t 1500 -i audio-card
fi

killall -9 waybar cava 2>/dev/null
waybar &
