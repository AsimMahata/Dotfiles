#!/bin/bash

killall -9 waybar cava 2>/dev/null
pkill -f cat.py 2>/dev/null
pkill -f dynamic-island.py 2>/dev/null
pkill -f net-layout.py 2>/dev/null

waybar & disown

