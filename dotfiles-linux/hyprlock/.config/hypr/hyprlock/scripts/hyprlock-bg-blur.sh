#!/usr/bin/env bash
# Pre-render scaled & blurred background for Hyprlock asynchronously
# This enables instant 0ms lockscreen startup with blur_passes = 0

CACHE_DIR="$HOME/.cache/hyprlock"
OUT_IMG="$CACHE_DIR/hyprlock-bg.png"
TMP_IMG="$CACHE_DIR/hyprlock-bg.tmp.png"

mkdir -p "$CACHE_DIR"

IMG="$1"
if [ -z "$IMG" ]; then
    # Read current image from Hyprlock colors.conf
    if [ -f "$HOME/.config/hypr/colors.conf" ]; then
        IMG=$(grep -E '^\$image[[:space:]]*=' "$HOME/.config/hypr/colors.conf" | cut -d'=' -f2- | xargs)
    fi
fi

if [ -z "$IMG" ] || [ ! -f "$IMG" ]; then
    exit 0
fi

# Use ffmpeg for high-speed multithreaded scaling and boxblur (takes ~1-2s in background)
if command -v ffmpeg &>/dev/null; then
    ffmpeg -y -i "$IMG" -vf "scale=2880:1800:force_original_aspect_ratio=increase,crop=2880:1800,boxblur=25:5" -update 1 "$TMP_IMG" &>/dev/null && mv -f "$TMP_IMG" "$OUT_IMG"
elif command -v magick &>/dev/null; then
    magick "$IMG" -resize 2880x1800^ -gravity center -extent 2880x1800 -scale 10% -resize 1000% "$TMP_IMG" &>/dev/null && mv -f "$TMP_IMG" "$OUT_IMG"
fi
