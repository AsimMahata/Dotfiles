#!/usr/bin/env bash
# Two-tone clock output for Hyprlock
# White hours : Accent blue minutes

hour=$(date +"%H")
minute=$(date +"%M")

echo "<span weight='bold'>$hour : <span foreground='#9ecafc'>$minute</span></span>"
