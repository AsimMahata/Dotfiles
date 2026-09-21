#!/usr/bin/env bash
# Hyprlock Weather Widget Script
# Reads from 15-min cache for instantaneous response, fetches wttr.in in background

CACHE_FILE="/tmp/hyprlock-weather.cache"

# If cache is missing or older than 15 mins (900s), refresh in background
if [ ! -f "$CACHE_FILE" ] || [ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0))) -gt 900 ]; then
    (
        res=$(curl -s --connect-timeout 2 "wttr.in/?format=%c+%t+%C" 2>/dev/null)
        if [ -n "$res" ]; then
            echo "$res" > "$CACHE_FILE"
        fi
    ) &
fi

if [ -f "$CACHE_FILE" ]; then
    raw=$(cat "$CACHE_FILE")
fi

if [ -z "$raw" ]; then
    echo "󰖔 28°C"
    echo "<span font_size=\"9pt\" alpha=\"70%\">Clear Sky</span>"
    exit 0
fi

temp=$(echo "$raw" | grep -oE '[+-]?[0-9]+°C' | head -n1 | tr -d '+')
cond=$(echo "$raw" | sed -E 's/.*[+-]?[0-9]+°C[[:space:]]*//' | sed 's/^[ \t]*//' | cut -c 1-16)

hour=$(date +%H)
is_night=0
if [ "$hour" -ge 19 ] || [ "$hour" -lt 6 ]; then
    is_night=1
fi

icon="󰖐"
case "${cond,,}" in
    *clear*|*sunny*)
        if [ "$is_night" -eq 1 ]; then icon="󰖔"; else icon="󰖙"; fi
        ;;
    *rain*|*drizzle*|*shower*)
        icon="󰖖"
        ;;
    *thunder*)
        icon="󰖓"
        ;;
    *snow*)
        icon="󰖘"
        ;;
    *fog*|*mist*)
        icon="󰖑"
        ;;
    *cloud*|*overcast*)
        icon="󰖐"
        ;;
esac

echo "$icon $temp"
echo "<span font_size=\"9pt\" alpha=\"70%\">$cond</span>"
