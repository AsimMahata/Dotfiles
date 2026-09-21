#!/usr/bin/env bash
# Hyprlock Album Artwork Fetcher
# Extracts current track cover or falls back to default album art

ART_OUT="/tmp/hyprlock-art.png"
DEFAULT_ART="$HOME/.config/hypr/hyprlock/assets/default-album.png"
URL_CACHE="/tmp/hyprlock-art-url.txt"

url=$(playerctl metadata mpris:artUrl 2>/dev/null)
last_url=$(cat "$URL_CACHE" 2>/dev/null)

if [ -n "$url" ] && [ "$url" != "$last_url" ]; then
    echo "$url" > "$URL_CACHE"
    if [[ "$url" == file://* ]]; then
        local_path="${url#file://}"
        if [ -f "$local_path" ]; then
            cp -f "$local_path" "$ART_OUT"
        fi
    elif [[ "$url" == http* ]]; then
        curl -s --connect-timeout 2 "$url" -o "${ART_OUT}.tmp" && mv -f "${ART_OUT}.tmp" "$ART_OUT"
    fi
fi

if [ ! -f "$ART_OUT" ]; then
    if [ -f "$DEFAULT_ART" ]; then
        cp -f "$DEFAULT_ART" "$ART_OUT"
    fi
fi

echo "$ART_OUT"
