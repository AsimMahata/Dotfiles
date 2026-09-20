#!/usr/bin/env python3
import sys
import time
import json
import subprocess
import os
import signal

def sig_handler(signum, frame):
    os._exit(0)

signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT, sig_handler)

NBSP = "\u00a0"
walking_cat_frames = [
    f"ᓚᘏᗢ ♪{NBSP*4}",
    f"{NBSP}ᓚᘏᗢ ♫{NBSP*3}",
    f"{NBSP*2}ᓚᘏᗢ ♬{NBSP*2}",
    f"{NBSP*3}ᓚᘏᗢ ♪{NBSP}",
    f"{NBSP*4}ᓚᘏᗢ ♫",
    f"{NBSP*3}ᓚᘏᗢ ♪{NBSP}",
    f"{NBSP*2}ᓚᘏᗢ ♬{NBSP*2}",
    f"{NBSP}ᓚᘏᗢ ♫{NBSP*3}",
]

def get_player_info():
    try:
        status_proc = subprocess.run(
            ["playerctl", "status"],
            capture_output=True,
            text=True,
            timeout=0.3
        )
        status = status_proc.stdout.strip()
        if not status:
            return "Stopped", "No music playing"
        
        meta_proc = subprocess.run(
            ["playerctl", "metadata", "--format", "{{ artist }} - {{ title }}"],
            capture_output=True,
            text=True,
            timeout=0.3
        )
        meta = meta_proc.stdout.strip()
        if not meta or meta == " - ":
            meta = "Playing audio"
        return status, meta
    except Exception:
        return "Stopped", "No player active"

def main():
    frame_idx = 0
    poll_counter = 0
    status, meta = "Stopped", "No music playing"

    while True:
        # Check player status every ~1.6s (every 8 ticks at 200ms)
        if poll_counter % 8 == 0:
            status, meta = get_player_info()
        poll_counter += 1

        if status == "Playing":
            cat_text = walking_cat_frames[frame_idx % len(walking_cat_frames)]
            tooltip = f"󰎆 Vibing to: {meta}\nLeft-click: Play/Pause\nRight-click: Next track"
            css_class = "playing"
            frame_idx += 1
        elif status == "Paused":
            cat_text = f"ᓚᘏᗢ zZ{NBSP*3}"
            tooltip = f"󰏤 Sleeping (Paused): {meta}\nLeft-click: Resume"
            css_class = "paused"
        else:
            cat_text = f"ᓚᘏᗢ ~{NBSP*4}"
            tooltip = "Cat is chilling (No music active)\nLeft-click: Play"
            css_class = "stopped"

        payload = {
            "text": cat_text,
            "tooltip": tooltip,
            "class": css_class
        }
        
        try:
            sys.stdout.write(json.dumps(payload) + "\n")
            sys.stdout.flush()
        except (BrokenPipeError, IOError):
            sys.exit(0)
        time.sleep(0.2)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(0)
