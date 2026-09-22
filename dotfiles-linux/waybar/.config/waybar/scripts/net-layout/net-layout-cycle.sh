#!/usr/bin/env bash
# Cycle mode on Left-Click: Speed -> Layout -> Dynamic -> Speed

if pgrep -f "[n]et-layout.py" >/dev/null 2>&1; then
    pkill -SIGUSR1 -f "[n]et-layout.py"
else
    # Fallback state cycling if engine is restarting
    python3 -c '
import json, os
p = os.path.expanduser("~/.config/waybar/scripts/net-layout/state.json")
modes = ["speed", "layout", "dynamic"]
data = {"mode": "speed"}
if os.path.exists(p):
    try:
        with open(p, "r") as f: data = json.load(f)
    except: pass
cur = data.get("mode", "speed")
data["mode"] = modes[(modes.index(cur) + 1) % len(modes)] if cur in modes else "speed"
with open(p, "w") as f: json.dump(data, f, indent=2)
'
fi
