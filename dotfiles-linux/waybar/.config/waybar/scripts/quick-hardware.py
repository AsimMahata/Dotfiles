#!/usr/bin/env python3
"""
Waybar Quick Hardware Resource Modal (Stateless, Bulletproof AAA UX)
A unified GTK Layer Shell modal for CPU and RAM monitoring.
- Uses SwayNC's fullscreen click-catcher technique: clicking outside instantly exits and frees the surface.
- No PID files, no background signals, zero ghost windows.
- Escape key and backdrop click dismiss cleanly.
- Displays live CPU, RAM, Swap, and Top Processes.
- Contains direct action button to launch BTOP.
- Matugen dynamic theming.
"""

import os
import sys
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib


# ---------------------------------------------------------
# Resource Data Helpers
# ---------------------------------------------------------
def read_cpu_stat():
    try:
        with open("/proc/stat", "r") as f:
            fields = [float(x) for x in f.readline().strip().split()[1:]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            return idle, total
    except Exception:
        return 0, 1


def get_cpu_details():
    load_str = "0.0, 0.0, 0.0"
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            load_str = f"{parts[0]}, {parts[1]}, {parts[2]}"
    except Exception:
        pass

    freq_ghz = 0.0
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("cpu MHz"):
                    mhz = float(line.split(":")[1].strip())
                    freq_ghz = mhz / 1000.0
                    break
    except Exception:
        pass

    return load_str, freq_ghz


def get_mem_details():
    mem = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    mem[parts[0].strip()] = int(parts[1].split()[0])
    except Exception:
        pass

    total_kb = mem.get("MemTotal", 1)
    avail_kb = mem.get("MemAvailable", 0)
    used_kb = max(0, total_kb - avail_kb)
    percent = (used_kb / total_kb) * 100.0

    swap_total_kb = mem.get("SwapTotal", 0)
    swap_free_kb = mem.get("SwapFree", 0)
    swap_used_kb = max(0, swap_total_kb - swap_free_kb)
    swap_percent = (swap_used_kb / swap_total_kb * 100.0) if swap_total_kb > 0 else 0.0

    return {
        "total_gb": total_kb / (1024 * 1024),
        "used_gb": used_kb / (1024 * 1024),
        "avail_gb": avail_kb / (1024 * 1024),
        "percent": percent,
        "swap_total_gb": swap_total_kb / (1024 * 1024),
        "swap_used_gb": swap_used_kb / (1024 * 1024),
        "swap_percent": swap_percent,
    }


def get_top_processes():
    procs = []
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "comm,%cpu,%mem", "--sort=-%mem"],
            stderr=subprocess.DEVNULL,
        ).decode().splitlines()
        seen = set()
        for line in out[1:]:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                if name in seen or name in ("ps", "systemd", "kworker"):
                    continue
                seen.add(name)
                procs.append({
                    "name": name,
                    "cpu": parts[1] + "%",
                    "mem": parts[2] + "%",
                })
                if len(procs) >= 3:
                    break
    except Exception:
        pass
    return procs


# ---------------------------------------------------------
# Modal Window
# ---------------------------------------------------------
class QuickHardwareModal(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.set_title("WaybarQuickHardware")
        self.set_name("waybar-quick-hardware")

        # Layer Shell setup: Fullscreen transparent click-catcher (SwayNC pattern)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "waybar-quick-hardware")

        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        # Transparent Backdrop: Clicking outside exits and cleanly destroys surface
        self.backdrop = Gtk.EventBox()
        self.backdrop.set_name("modal-backdrop")
        self.backdrop.connect("button-press-event", self.on_backdrop_clicked)
        self.add(self.backdrop)

        # Positioning Wrapper: Aligns card under Waybar hardware pill
        wrapper = Gtk.Box()
        wrapper.set_halign(Gtk.Align.END)
        wrapper.set_valign(Gtk.Align.START)
        wrapper.set_margin_top(48)
        wrapper.set_margin_end(380)
        self.backdrop.add(wrapper)

        # Card EventBox: Intercepts clicks to prevent closing when clicking inside
        self.card_event_box = Gtk.EventBox()
        self.card_event_box.set_name("card-event-box")
        self.card_event_box.connect("button-press-event", lambda w, e: True)
        wrapper.add(self.card_event_box)

        # Main Card Box (Note: Never name attribute self.container per GTK3 C struct rule)
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.card_box.set_name("modal-container")
        self.card_event_box.add(self.card_box)

        # 1. Header: Title & CPU Architecture
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        icon_lbl = Gtk.Label(label="󰍛")
        icon_lbl.set_name("header-icon")
        header_box.pack_start(icon_lbl, False, False, 0)

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label="System Resources")
        title_lbl.set_name("header-title")
        title_lbl.set_xalign(0.0)
        title_vbox.pack_start(title_lbl, False, False, 0)

        subtitle_lbl = Gtk.Label(label="12th Gen Intel Core i5-12500H • 16 Threads")
        subtitle_lbl.set_name("header-subtitle")
        subtitle_lbl.set_xalign(0.0)
        title_vbox.pack_start(subtitle_lbl, False, False, 0)

        header_box.pack_start(title_vbox, True, True, 0)
        self.card_box.pack_start(header_box, False, False, 0)

        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep1.set_name("card-separator")
        self.card_box.pack_start(sep1, False, False, 0)

        # 2. CPU Utilization Section
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        cpu_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        cpu_title = Gtk.Label(label="  CPU Load")
        cpu_title.set_name("metric-title")
        cpu_title.set_xalign(0.0)
        cpu_top.pack_start(cpu_title, True, True, 0)

        self.cpu_badge = Gtk.Label(label="--%")
        self.cpu_badge.set_name("metric-badge-cpu")
        self.cpu_badge.set_xalign(1.0)
        cpu_top.pack_start(self.cpu_badge, False, False, 0)
        cpu_box.pack_start(cpu_top, False, False, 0)

        self.cpu_progress = Gtk.ProgressBar()
        self.cpu_progress.get_style_context().add_class("cpu-bar")
        cpu_box.pack_start(self.cpu_progress, False, False, 0)

        self.cpu_details_lbl = Gtk.Label(label="Load Average: --  •  Freq: -- GHz")
        self.cpu_details_lbl.set_name("metric-details")
        self.cpu_details_lbl.set_xalign(0.0)
        cpu_box.pack_start(self.cpu_details_lbl, False, False, 0)

        self.card_box.pack_start(cpu_box, False, False, 0)

        # 3. Memory Utilization Section
        mem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        mem_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        mem_title = Gtk.Label(label="  Memory (RAM)")
        mem_title.set_name("metric-title")
        mem_title.set_xalign(0.0)
        mem_top.pack_start(mem_title, True, True, 0)

        self.mem_badge = Gtk.Label(label="-- / -- (--%)")
        self.mem_badge.set_name("metric-badge-ram")
        self.mem_badge.set_xalign(1.0)
        mem_top.pack_start(self.mem_badge, False, False, 0)
        mem_box.pack_start(mem_top, False, False, 0)

        self.mem_progress = Gtk.ProgressBar()
        self.mem_progress.get_style_context().add_class("ram-bar")
        mem_box.pack_start(self.mem_progress, False, False, 0)

        self.mem_details_lbl = Gtk.Label(label="Available: -- GB  •  Swap: -- / -- GB")
        self.mem_details_lbl.set_name("metric-details")
        self.mem_details_lbl.set_xalign(0.0)
        mem_box.pack_start(self.mem_details_lbl, False, False, 0)

        self.card_box.pack_start(mem_box, False, False, 0)

        # 4. Top Processes Section
        proc_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        proc_title = Gtk.Label(label="󰒋  Top Active Processes")
        proc_title.set_name("proc-header")
        proc_title.set_xalign(0.0)
        proc_section.pack_start(proc_title, False, False, 0)

        self.proc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.proc_box.set_name("proc-list-box")
        proc_section.pack_start(self.proc_box, False, False, 0)

        self.card_box.pack_start(proc_section, False, False, 0)

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_name("card-separator")
        self.card_box.pack_start(sep2, False, False, 0)

        # 5. Footer Actions (BTOP button & Close)
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        btn_btop = Gtk.Button(label="󰒋  Open BTOP Monitor")
        btn_btop.set_name("btn-btop")
        btn_btop.connect("clicked", self.on_launch_btop)
        actions_box.pack_start(btn_btop, True, True, 0)

        btn_close = Gtk.Button(label="󰅖  Close")
        btn_close.set_name("btn-close")
        btn_close.connect("clicked", lambda w: Gtk.main_quit())
        actions_box.pack_start(btn_close, False, False, 0)

        self.card_box.pack_start(actions_box, False, False, 0)

        # Keybinds (Escape to close)
        self.connect("key-press-event", self.on_key_press)

        # Stats state initialization
        self.prev_idle, self.prev_total = read_cpu_stat()
        self.refresh_stats()

        # Update stats every 1.5 seconds while open
        GLib.timeout_add(1500, self.refresh_stats)

    def _set_bar_tier(self, widget, pct):
        ctx = widget.get_style_context()
        for c in ["tier-low", "tier-medium", "tier-high", "tier-critical"]:
            ctx.remove_class(c)
        if pct >= 85:
            ctx.add_class("tier-critical")
        elif pct >= 70:
            ctx.add_class("tier-high")
        elif pct >= 40:
            ctx.add_class("tier-medium")
        else:
            ctx.add_class("tier-low")

    def refresh_stats(self):
        # 1. CPU
        idle, total = read_cpu_stat()
        d_idle = idle - self.prev_idle
        d_total = total - self.prev_total
        self.prev_idle = idle
        self.prev_total = total

        cpu_pct = 0.0
        if d_total > 0:
            cpu_pct = max(0.0, min(100.0, (1.0 - (d_idle / d_total)) * 100.0))

        load_str, freq_ghz = get_cpu_details()
        self.cpu_badge.set_text(f"{cpu_pct:.1f}%")
        self.cpu_progress.set_fraction(cpu_pct / 100.0)
        self._set_bar_tier(self.cpu_progress, cpu_pct)
        self.cpu_details_lbl.set_text(f"Load Average: {load_str}  •  Freq: {freq_ghz:.2f} GHz")

        # 2. Memory
        mem = get_mem_details()
        self.mem_badge.set_text(f"{mem['used_gb']:.1f}G / {mem['total_gb']:.1f}G ({mem['percent']:.0f}%)")
        self.mem_progress.set_fraction(min(1.0, mem['percent'] / 100.0))
        self._set_bar_tier(self.mem_progress, mem['percent'])
        self.mem_details_lbl.set_text(
            f"Available: {mem['avail_gb']:.1f} GiB  •  Swap: {mem['swap_used_gb']:.1f}G / {mem['swap_total_gb']:.1f}G"
        )

        # 3. Top Processes
        for child in self.proc_box.get_children():
            self.proc_box.remove(child)

        procs = get_top_processes()
        for p in procs:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            lbl_name = Gtk.Label(label=f"• {p['name']}")
            lbl_name.set_name("proc-name")
            lbl_name.set_xalign(0.0)
            row.pack_start(lbl_name, True, True, 0)

            lbl_stat = Gtk.Label(label=f"RAM: {p['mem']}  CPU: {p['cpu']}")
            lbl_stat.set_name("proc-stat")
            lbl_stat.set_xalign(1.0)
            row.pack_start(lbl_stat, False, False, 0)
            self.proc_box.pack_start(row, False, False, 0)

        self.proc_box.show_all()
        return True

    def on_launch_btop(self, widget):
        # Cleanly launch btop in kitty terminal and close the modal
        subprocess.Popen(["kitty", "-1", "fish", "-c", "btop"])
        Gtk.main_quit()

    def on_backdrop_clicked(self, widget, event):
        Gtk.main_quit()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False


# ---------------------------------------------------------
# Styles
# ---------------------------------------------------------
def apply_styles():
    colors_file = os.path.expanduser("~/.config/waybar/colors.css")
    colors_css = ""
    if os.path.exists(colors_file):
        with open(colors_file, "r") as f:
            colors_css = f.read()

    css = f"""
    {colors_css}

    * {{
        font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", sans-serif;
        font-size: 12px;
        font-weight: 500;
    }}

    window#waybar-quick-hardware,
    #modal-backdrop {{
        background-color: transparent;
        background: transparent;
    }}

    #card-event-box {{
        background: transparent;
    }}

    #modal-container {{
        background: alpha(@background, 0.96);
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.6);
        border-radius: 20px;
        padding: 20px 24px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.65);
        min-width: 380px;
    }}

    #header-icon {{
        color: @primary;
        font-size: 26px;
    }}

    #header-title {{
        color: @on_surface;
        font-size: 15px;
        font-weight: 700;
    }}

    #header-subtitle {{
        color: @on_surface_variant;
        font-size: 11px;
    }}

    #card-separator {{
        background-color: alpha(@outline_variant, 0.3);
        min-height: 1px;
        margin: 4px 0;
    }}

    #metric-title {{
        color: @on_surface;
        font-size: 12px;
        font-weight: 700;
    }}

    #metric-badge-cpu,
    #metric-badge-ram {{
        color: @on_surface;
        font-weight: 700;
        font-size: 12px;
    }}

    #metric-details {{
        color: @on_surface_variant;
        font-size: 11px;
    }}

    progressbar trough {{
        min-height: 8px;
        border-radius: 4px;
        background-color: alpha(@on_surface, 0.12);
        border: none;
    }}

    progressbar.tier-low progress {{
        background-color: @primary;
        border-radius: 4px;
        border: none;
    }}

    progressbar.tier-medium progress {{
        background-color: @secondary;
        border-radius: 4px;
        border: none;
    }}

    progressbar.tier-high progress {{
        background-color: #f9e2af;
        border-radius: 4px;
        border: none;
    }}

    progressbar.tier-critical progress {{
        background-color: @error;
        border-radius: 4px;
        border: none;
    }}

    #proc-header {{
        color: @secondary;
        font-weight: 700;
        font-size: 11px;
    }}

    #proc-list-box {{
        background: alpha(@on_surface, 0.04);
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 10px;
        padding: 8px 10px;
    }}

    #proc-name {{
        color: @on_surface;
        font-size: 11px;
    }}

    #proc-stat {{
        color: @on_surface_variant;
        font-size: 11px;
    }}

    #btn-btop {{
        background: @primary;
        color: @on_primary_fixed;
        border: none;
        border-radius: 12px;
        padding: 9px 16px;
        font-weight: 700;
        font-size: 12px;
        transition: all 0.2s ease;
    }}

    #btn-btop:hover {{
        background: @primary_fixed;
        box-shadow: 0 0 14px alpha(@primary, 0.45);
    }}

    #btn-close {{
        background: alpha(@on_surface, 0.1);
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.4);
        border-radius: 12px;
        padding: 9px 16px;
        font-weight: 600;
        font-size: 12px;
        transition: all 0.2s ease;
    }}

    #btn-close:hover {{
        background: alpha(@on_surface, 0.2);
        color: #ffffff;
    }}
    """

    provider = Gtk.CssProvider()
    try:
        provider.load_from_data(css.encode())
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    except Exception as e:
        sys.stderr.write(f"Warning loading CSS: {e}\n")


def main():
    apply_styles()
    win = QuickHardwareModal()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
