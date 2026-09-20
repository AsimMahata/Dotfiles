#!/bin/bash
trap "exit 0" SIGTERM SIGINT
cava -p "$HOME/.config/waybar/profiles/music/cava.conf" | sed -u 's/;//g;s/0/ /g;s/1/▂/g;s/2/▃/g;s/3/▄/g;s/4/▅/g;s/5/▆/g;s/6/▇/g;s/7/█/g;'
