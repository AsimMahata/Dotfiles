#!/usr/bin/env python3
"""
Waybar Network Speed & Keyboard Layout ("dmeter") Engine
Provides real-time internet speed, active keyboard layout, and dynamic 59s/1s rotation.
- Daemonless / streaming JSON output for Waybar.
- Left-click (SIGUSR1): Cycles between Speed -> Layout -> Dynamic modes.
- Right-click: Opens GTK3 Layer-Shell settings modal.
- Settings update (SIGUSR2): Hot-reloads settings from state.json without restart.
- Zero external CLI overhead: reads /proc/net/dev directly (<0.01% CPU).
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
import html

STATE_DIR = os.path.expanduser("~/.config/waybar/scripts/net-layout")
STATE_FILE = os.path.join(STATE_DIR, "state.json")

DEFAULT_STATE = {
    "mode": "speed",             # "speed" | "layout" | "dynamic"
    "speed_format": "dominant",  # "dominant" | "dual" | "compact"
    "speed_duration": 59,        # seconds showing speed in dynamic mode
    "layout_duration": 1,        # seconds showing layout in dynamic mode
    "interface": "auto"          # "auto" or specific interface name
}

# Threading event to wake up the 1s loop immediately on signals
wake_event = threading.Event()
force_cycle = False
force_reload = False


def load_state():
    state = dict(DEFAULT_STATE)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                state.update(data)
        except Exception:
            pass
    return state


def save_state(state):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)
    except Exception:
        pass


def handle_sigusr1(signum, frame):
    """Left-click handler: cycle mode."""
    global force_cycle
    force_cycle = True
    wake_event.set()


def handle_sigusr2(signum, frame):
    """Settings update handler: reload state."""
    global force_reload
    force_reload = True
    wake_event.set()


def get_net_bytes(target_iface="auto"):
    """Read rx and tx bytes from /proc/net/dev with zero CLI overhead."""
    rx_total = 0
    tx_total = 0
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:]  # Skip header lines
            for line in lines:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                iface = iface.strip()
                if iface == "lo":
                    continue
                if target_iface != "auto" and iface != target_iface:
                    continue
                fields = data.split()
                if len(fields) >= 9:
                    rx_total += int(fields[0])
                    tx_total += int(fields[8])
    except Exception:
        pass
    return rx_total, tx_total


def get_default_interface_and_ip():
    """Retrieve default routing interface and IP."""
    try:
        out = subprocess.check_output(
            ["ip", "route", "get", "1.1.1.1"],
            stderr=subprocess.DEVNULL,
            timeout=0.3
        ).decode().strip()
        parts = out.split()
        if "dev" in parts and "src" in parts:
            dev_idx = parts.index("dev") + 1
            src_idx = parts.index("src") + 1
            return parts[dev_idx], parts[src_idx]
    except Exception:
        pass
    return "Unknown", "Offline"


def get_active_keyboard_layout():
    """Query Hyprland for active keyboard layout."""
    try:
        out = subprocess.check_output(
            ["hyprctl", "devices", "-j"],
            stderr=subprocess.DEVNULL,
            timeout=0.3
        ).decode()
        data = json.loads(out)
        keyboards = data.get("keyboards", [])
        for kb in keyboards:
            if kb.get("main", False):
                keymap = kb.get("active_keymap", "")
                # Extract short layout name, e.g. "English (US)" -> "US"
                if "(" in keymap and ")" in keymap:
                    short = keymap.split("(")[1].split(")")[0].strip()
                    return short.upper(), keymap
                layout = kb.get("layout", "")
                if layout:
                    return layout.upper(), keymap or layout
                return "US", keymap
        # Fallback to first keyboard if no main is marked
        if keyboards:
            kb = keyboards[0]
            layout = kb.get("layout", "") or "us"
            return layout.upper(), kb.get("active_keymap", layout)
    except Exception:
        pass
    return "US", "English (US)"


def format_speed(bytes_per_sec, compact=False):
    """Format speed rate into human-readable string."""
    if compact:
        if bytes_per_sec >= 1024 * 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.1f}G"
        elif bytes_per_sec >= 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024):.1f}M"
        elif bytes_per_sec >= 1024:
            return f"{bytes_per_sec / 1024:.0f}K"
        else:
            return f"{int(bytes_per_sec)}B"
    else:
        if bytes_per_sec >= 1024 * 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"
        elif bytes_per_sec >= 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
        elif bytes_per_sec >= 1024:
            return f"{bytes_per_sec / 1024:.0f} KB/s"
        else:
            return f"{int(bytes_per_sec)} B/s"


def main():
    signal.signal(signal.SIGUSR1, handle_sigusr1)
    signal.signal(signal.SIGUSR2, handle_sigusr2)
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    state = load_state()
    modes = ["speed", "layout", "dynamic"]
    if state["mode"] not in modes:
        state["mode"] = "speed"

    # Initial network baseline
    target_iface = state.get("interface", "auto")
    prev_rx, prev_tx = get_net_bytes(target_iface)
    prev_time = time.time()

    dynamic_timer = 0
    last_payload_str = ""

    # Cache keyboard layout and network details for 3 seconds to minimize IPC
    kb_cache_time = 0
    cached_kb_short = "US"
    cached_kb_full = "English (US)"
    net_info_cache_time = 0
    cached_iface = "enp0s20f0u1"
    cached_ip = "127.0.0.1"

    while True:
        now = time.time()
        dt = max(0.1, now - prev_time)

        # Handle signals
        global force_cycle, force_reload
        if force_cycle:
            force_cycle = False
            cur_idx = modes.index(state["mode"]) if state["mode"] in modes else 0
            state["mode"] = modes[(cur_idx + 1) % len(modes)]
            save_state(state)
            dynamic_timer = 0

        if force_reload:
            force_reload = False
            state = load_state()
            target_iface = state.get("interface", "auto")
            dynamic_timer = 0

        # Read current network bytes
        curr_rx, curr_tx = get_net_bytes(target_iface)
        rx_speed = max(0.0, (curr_rx - prev_rx) / dt)
        tx_speed = max(0.0, (curr_tx - prev_tx) / dt)
        prev_rx, prev_tx = curr_rx, curr_tx
        prev_time = now

        # Update cached keyboard info every 3s
        if now - kb_cache_time > 3.0 or state["mode"] in ("layout", "dynamic"):
            cached_kb_short, cached_kb_full = get_active_keyboard_layout()
            kb_cache_time = now

        # Update cached interface and IP every 5s
        if now - net_info_cache_time > 5.0:
            cached_iface, cached_ip = get_default_interface_and_ip()
            net_info_cache_time = now

        # Determine output text and css class
        active_mode = state.get("mode", "speed")
        speed_fmt = state.get("speed_format", "dominant")
        display_text = ""
        css_class = ""
        mode_label = ""

        # Dynamic mode timing
        speed_dur = max(1, int(state.get("speed_duration", 59)))
        layout_dur = max(1, int(state.get("layout_duration", 1)))
        total_cycle = speed_dur + layout_dur

        if active_mode == "speed":
            mode_label = "Internet Speed"
            css_class = "speed"
            if speed_fmt == "dual":
                display_text = f"↓ {format_speed(rx_speed, compact=True)}  ↑ {format_speed(tx_speed, compact=True)}"
            elif speed_fmt == "compact":
                display_text = format_speed(max(rx_speed, tx_speed), compact=True)
            else:  # dominant
                if rx_speed >= tx_speed:
                    display_text = f"󰇚  {format_speed(rx_speed)}"
                else:
                    display_text = f"󰕒  {format_speed(tx_speed)}"

        elif active_mode == "layout":
            mode_label = "Keyboard Layout"
            css_class = "layout"
            # As explicitly requested: no ascii/nerd icon, just write "US" or layout code
            display_text = cached_kb_short

        elif active_mode == "dynamic":
            cycle_pos = dynamic_timer % total_cycle
            mode_label = f"Dynamic ({speed_dur}s Speed / {layout_dur}s Layout)"

            if cycle_pos < speed_dur:
                css_class = "dynamic-speed"
                if speed_fmt == "dual":
                    display_text = f"↓ {format_speed(rx_speed, compact=True)}  ↑ {format_speed(tx_speed, compact=True)}"
                elif speed_fmt == "compact":
                    display_text = format_speed(max(rx_speed, tx_speed), compact=True)
                else:  # dominant
                    if rx_speed >= tx_speed:
                        display_text = f"󰇚  {format_speed(rx_speed)}"
                    else:
                        display_text = f"󰕒  {format_speed(tx_speed)}"
            else:
                css_class = "dynamic-layout"
                display_text = cached_kb_short

            dynamic_timer += 1

        # Rich Tooltip
        esc_kb = html.escape(cached_kb_full)
        esc_iface = html.escape(cached_iface)
        esc_ip = html.escape(cached_ip)
        rx_str = format_speed(rx_speed)
        tx_str = format_speed(tx_speed)

        tooltip = (
            f"<b><span color='#9ecafc'>󰛳 Network &amp; Layout Monitor</span></b>\n"
            f"<span color='#c2c7cf'>Mode:</span> <b>{mode_label}</b>\n\n"
            f"<b><span color='#9ecafc'>─── Speed Stats ───</span></b>\n"
            f"󰇚 Download: <b>{rx_str}</b>\n"
            f"󰕒 Upload:   <b>{tx_str}</b>\n"
            f"󰈀 Interface: <b>{esc_iface}</b> ({esc_ip})\n\n"
            f"<b><span color='#9ecafc'>─── Keyboard ───</span></b>\n"
            f"󰌌 Layout: <b>{esc_kb}</b> [{cached_kb_short}]\n\n"
            f"<small><span color='#8c9199'>Left-click: Cycle Mode (Speed ➔ Layout ➔ Dynamic)\n"
            f"Right-click: Settings Modal</span></small>"
        )

        payload = {
            "text": display_text,
            "tooltip": tooltip,
            "class": css_class
        }

        payload_str = json.dumps(payload)
        if payload_str != last_payload_str:
            last_payload_str = payload_str
            try:
                sys.stdout.write(payload_str + "\n")
                sys.stdout.flush()
            except (BrokenPipeError, IOError):
                sys.exit(0)

        # Sleep for 1.0 second, or wake up instantly on signal
        wake_event.wait(1.0)
        wake_event.clear()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        try:
            sys.stdout.close()
            sys.stderr.close()
        except Exception:
            pass
        os._exit(0)
