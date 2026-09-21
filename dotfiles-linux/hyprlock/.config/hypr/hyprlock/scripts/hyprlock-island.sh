#!/usr/bin/env bash
# Hyprlock Dynamic Island Status Script
# Outputs plain text formatted for the top capsule

# Battery
bat_cap=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || cat /sys/class/power_supply/BAT1/capacity 2>/dev/null || echo "100")
bat_stat=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || cat /sys/class/power_supply/BAT1/status 2>/dev/null || echo "Discharging")

if [ "$bat_stat" = "Charging" ]; then
    bat_icon="󰂄"
elif [ "$bat_cap" -ge 80 ]; then
    bat_icon="󰁹"
elif [ "$bat_cap" -ge 50 ]; then
    bat_icon="󰁾"
elif [ "$bat_cap" -ge 20 ]; then
    bat_icon="󰁻"
else
    bat_icon="󰁺"
fi
bat_str="$bat_icon ${bat_cap}%"

# Music / Now Playing
status=$(playerctl status 2>/dev/null)
if [ "$status" = "Playing" ] || [ "$status" = "Paused" ]; then
    song_title=$(playerctl metadata --format '{{title}}' 2>/dev/null | cut -c 1-20 | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')
    song_artist=$(playerctl metadata --format '{{artist}}' 2>/dev/null | cut -c 1-14 | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')
    if [ -n "$song_title" ]; then
        if [ -n "$song_artist" ]; then
            music_str="󰝚 $song_title - $song_artist"
        else
            music_str="󰝚 $song_title"
        fi
        if [ "$status" = "Playing" ]; then
            music_str="$music_str 󰘚"
        fi
    else
        music_str="󰣇 Arch Linux"
    fi
else
    music_str="󰣇 Arch Linux"
fi

# Network / WiFi (fast lookup without scanning)
if grep -q "up" /sys/class/net/e*/operstate 2>/dev/null; then
    wifi_str="󰈀 Ethernet"
elif grep -q "up" /sys/class/net/w*/operstate 2>/dev/null; then
    wifi_ssid=$(nmcli -t -f active,ssid dev wifi 2>/dev/null | grep '^yes:' | cut -d: -f2 | head -n1)
    if [ -n "$wifi_ssid" ]; then
        wifi_ssid_esc=$(echo "$wifi_ssid" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')
        wifi_str="󰤨 $wifi_ssid_esc"
    else
        wifi_str="󰤨 Connected"
    fi
else
    wifi_str="󰤮 Offline"
fi

echo "$bat_str   │   $music_str   │   $wifi_str"
