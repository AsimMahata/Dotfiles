#!/usr/bin/env bash
# Hyprlock MPRIS Progress Bar

status=$(playerctl status 2>/dev/null)
if [ "$status" != "Playing" ] && [ "$status" != "Paused" ]; then
    exit 0
fi

pos=$(playerctl position 2>/dev/null | cut -d. -f1)
len_raw=$(playerctl metadata mpris:length 2>/dev/null)

pct=0
if [ -n "$len_raw" ] && [ "$len_raw" -gt 0 ] && [ -n "$pos" ]; then
    len=$(( len_raw / 1000000 ))
    if [ "$len" -gt 0 ]; then
        pct=$(( (pos * 100) / len ))
    fi
fi

if [ "$pct" -gt 100 ]; then pct=100; fi
if [ "$pct" -lt 0 ]; then pct=0; fi

total_chars=20
filled_chars=$(( (pct * total_chars) / 100 ))
unfilled_chars=$(( total_chars - filled_chars ))

bar_filled=""
for ((i=0; i<filled_chars; i++)); do bar_filled="${bar_filled}━"; done

bar_unfilled=""
for ((i=0; i<unfilled_chars; i++)); do bar_unfilled="${bar_unfilled}─"; done

echo "${bar_filled}${bar_unfilled}"
