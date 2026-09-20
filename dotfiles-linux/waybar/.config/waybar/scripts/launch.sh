#!/bin/bash

killall -9 waybar cava 2>/dev/null
pkill -f cat.py 2>/dev/null

waybar &

