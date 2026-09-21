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
    song_title=$(playerctl metadata --format '{{title}}' 2>/dev/null | cut -c 1-20)
    song_artist=$(playerctl metadata --format '{{artist}}' 2>/dev/null | cut -c 1-14)
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
wifi_ssid=$(iwgetid -r 2>/dev/null)
if [ -z "$wifi_ssid" ]; then
    wifi_ssid=$(nmcli -t -f NAME,TYPE c show --active 2>/dev/null | grep ":802-11-wireless" | head -n1 | cut -d: -f1)
fi

if [ -n "$wifi_ssid" ]; then
    wifi_str="󰤨 $wifi_ssid"
elif nmcli -t -f TYPE c show --active 2>/dev/null | grep -q "802-3-ethernet" || ip route get 1.1.1.1 &>/dev/null; then
    wifi_str="󰈀 Ethernet"
else
    wifi_str="󰤮 Offline"
fi

echo "$bat_str   │   $music_str   │   $wifi_str"
