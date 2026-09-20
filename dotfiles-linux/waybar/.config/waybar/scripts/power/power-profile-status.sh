#!/usr/bin/env bash

# Fetch current power profile
PROFILE=$(powerprofilesctl get 2>/dev/null || echo "balanced")

case "$PROFILE" in
    "power-saver")
        NAME="Quiet (Power Saver)"
        ;;
    "performance")
        NAME="Performance"
        ;;
    "balanced"|*)
        NAME="Balanced"
        ;;
esac

printf '{"text":"%s","alt":"%s","tooltip":"Power Profile: %s\\nLeft-click: Cycle profile","class":"%s"}\n' "$PROFILE" "$PROFILE" "$NAME" "$PROFILE"
