#!/usr/bin/env python3
"""
Waybar Network Speed & Keyboard Layout Settings Modal
A sleek GTK3 + GtkLayerShell settings interface adhering strictly to gtk.md.
- Fullscreen transparent click-catcher (SwayNC pattern): clicking outside cleanly destroys surface.
- Stateless lifecycle: exits with Gtk.main_quit() on backdrop click or Escape.
- Hot-updates state.json and notifies net-layout.py via SIGUSR2.
- Fully themed with Matugen colors from ~/.config/waybar/colors.css.
- No transform CSS properties, throttled slider adjustments.
"""

import os
import sys
import json
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib

STATE_DIR = os.path.expanduser("~/.config/waybar/scripts/net-layout")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
COLORS_FILE = os.path.expanduser("~/.config/waybar/colors.css")

DEFAULT_STATE = {
    "mode": "speed",
    "speed_format": "dominant",
    "speed_duration": 59,
    "layout_duration": 1,
    "interface": "auto"
}


def load_state():
    state = dict(DEFAULT_STATE)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state.update(json.load(f))
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
        # Hot-notify running engine
        subprocess.Popen(
            ["pkill", "-SIGUSR2", "-f", "net-layout.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def get_available_interfaces():
    """Discover network interfaces from /proc/net/dev."""
    ifaces = []
    try:
        with open("/proc/net/dev", "r") as f:
            for line in f.readlines()[2:]:
                if ":" in line:
                    iface = line.split(":", 1)[0].strip()
                    if iface != "lo" and not iface.startswith("dummy"):
                        ifaces.append(iface)
    except Exception:
        pass
    return ifaces


class QuickNetSettings(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("NetLayoutSettings")
        self.set_name("net-layout-settings-window")

        self.state = load_state()
        self.save_timer_id = None

        # GtkLayerShell: Fullscreen transparent backdrop (SwayNC pattern)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "waybar-quick-net-settings")

        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        # Transparent Backdrop: Click outside exits cleanly
        self.backdrop = Gtk.EventBox()
        self.backdrop.set_name("modal-backdrop")
        self.backdrop.connect("button-press-event", self.on_backdrop_clicked)
        self.add(self.backdrop)

        # Positioning Wrapper: Aligns card under top-left Waybar module
        wrapper = Gtk.Box()
        wrapper.set_halign(Gtk.Align.START)
        wrapper.set_valign(Gtk.Align.START)
        wrapper.set_margin_left(65)
        wrapper.set_margin_top(44)
        self.backdrop.add(wrapper)

        # Card EventBox: intercepts inner clicks so they don't hit backdrop
        self.card_event_box = Gtk.EventBox()
        self.card_event_box.set_name("card-event-box")
        self.card_event_box.connect("button-press-event", lambda w, e: True)
        wrapper.add(self.card_event_box)

        # Main Compact Card Box (315px width)
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.card_box.set_name("modal-container")
        self.card_box.set_size_request(315, -1)
        self.card_event_box.add(self.card_box)

        # Build UI Sections
        self.build_header()
        self.build_mode_selector()
        self.build_format_selector()
        self.build_dynamic_timing_controls()
        self.build_interface_selector()
        self.build_footer()

        self.connect("key-press-event", self.on_key_press)

    def on_backdrop_clicked(self, widget, event):
        Gtk.main_quit()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    def schedule_save(self):
        if self.save_timer_id is not None:
            GLib.source_remove(self.save_timer_id)
        self.save_timer_id = GLib.timeout_add(100, self._do_save)

    def _do_save(self):
        save_state(self.state)
        self.save_timer_id = None
        return False

    def build_header(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_name("header-box")

        icon_label = Gtk.Label(label="󰒓")
        icon_label.set_name("header-icon")

        title_label = Gtk.Label(label="Network & Layout")
        title_label.set_name("header-title")
        title_label.set_xalign(0.0)

        close_btn = Gtk.Button(label="✕")
        close_btn.set_name("close-btn")
        close_btn.connect("clicked", lambda w: Gtk.main_quit())

        header_box.pack_start(icon_label, False, False, 0)
        header_box.pack_start(title_label, True, True, 0)
        header_box.pack_end(close_btn, False, False, 0)

        self.card_box.pack_start(header_box, False, False, 0)

    def build_mode_selector(self):
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section_box.set_name("section-box")

        sec_title = Gtk.Label(label="ACTIVE MODE")
        sec_title.set_name("section-label")
        sec_title.set_xalign(0.0)
        section_box.pack_start(sec_title, False, False, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_homogeneous(True)

        self.mode_buttons = {}
        modes = [
            ("speed", "Speed", "󰇚"),
            ("layout", "Layout", "US"),
            ("dynamic", "Dynamic", "󰑖")
        ]

        active_mode = self.state.get("mode", "speed")

        for m_key, m_label, m_icon in modes:
            btn = Gtk.Button()
            btn_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            btn_inner.set_halign(Gtk.Align.CENTER)

            icon_lbl = Gtk.Label(label=m_icon)
            text_lbl = Gtk.Label(label=m_label)

            btn_inner.pack_start(icon_lbl, False, False, 0)
            btn_inner.pack_start(text_lbl, False, False, 0)
            btn.add(btn_inner)

            if m_key == active_mode:
                btn.set_name("mode-btn-active")
            else:
                btn.set_name("mode-btn")

            btn.connect("clicked", self.on_mode_clicked, m_key)
            btn_box.pack_start(btn, True, True, 0)
            self.mode_buttons[m_key] = btn

        section_box.pack_start(btn_box, False, False, 0)
        self.card_box.pack_start(section_box, False, False, 0)

    def on_mode_clicked(self, widget, mode_key):
        self.state["mode"] = mode_key
        for m_key, btn in self.mode_buttons.items():
            if m_key == mode_key:
                btn.set_name("mode-btn-active")
            else:
                btn.set_name("mode-btn")
        self.schedule_save()

    def build_format_selector(self):
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section_box.set_name("section-box")

        sec_title = Gtk.Label(label="SPEED FORMAT")
        sec_title.set_name("section-label")
        sec_title.set_xalign(0.0)
        section_box.pack_start(sec_title, False, False, 0)

        formats = [
            ("dominant", "Dominant Rate (󰇚 / 󰕒 MB/s)"),
            ("dual", "Dual Stream (↓ DL  ↑ UL)"),
            ("compact", "Compact Minimal (2.4M)")
        ]

        active_fmt = self.state.get("speed_format", "dominant")
        self.fmt_combo = Gtk.ComboBoxText()
        self.fmt_combo.set_name("custom-combobox")

        for key, label in formats:
            self.fmt_combo.append(key, label)

        self.fmt_combo.set_active_id(active_fmt)
        self.fmt_combo.connect("changed", self.on_format_changed)
        section_box.pack_start(self.fmt_combo, False, False, 0)

        self.card_box.pack_start(section_box, False, False, 0)

    def on_format_changed(self, combo):
        active_id = combo.get_active_id()
        if active_id:
            self.state["speed_format"] = active_id
            self.schedule_save()

    def build_dynamic_timing_controls(self):
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        section_box.set_name("section-box")

        sec_title = Gtk.Label(label="DYNAMIC CYCLE DURATION")
        sec_title.set_name("section-label")
        sec_title.set_xalign(0.0)
        section_box.pack_start(sec_title, False, False, 0)

        # Speed Duration Slider
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        speed_lbl = Gtk.Label(label="Speed duration:")
        speed_lbl.set_name("slider-label")
        speed_lbl.set_xalign(0.0)

        cur_speed_dur = int(self.state.get("speed_duration", 59))
        self.speed_val_lbl = Gtk.Label(label=f"{cur_speed_dur}s")
        self.speed_val_lbl.set_name("slider-val-label")

        speed_box.pack_start(speed_lbl, True, True, 0)
        speed_box.pack_end(self.speed_val_lbl, False, False, 0)
        section_box.pack_start(speed_box, False, False, 0)

        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 120, 1)
        self.speed_scale.set_name("slider-scale")
        self.speed_scale.set_value(cur_speed_dur)
        self.speed_scale.set_draw_value(False)
        self.speed_scale.connect("value-changed", self.on_speed_scale_changed)
        section_box.pack_start(self.speed_scale, False, False, 0)

        # Layout Duration Slider
        layout_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        layout_lbl = Gtk.Label(label="Layout flash duration:")
        layout_lbl.set_name("slider-label")
        layout_lbl.set_xalign(0.0)

        cur_layout_dur = int(self.state.get("layout_duration", 1))
        self.layout_val_lbl = Gtk.Label(label=f"{cur_layout_dur}s")
        self.layout_val_lbl.set_name("slider-val-label")

        layout_box.pack_start(layout_lbl, True, True, 0)
        layout_box.pack_end(self.layout_val_lbl, False, False, 0)
        section_box.pack_start(layout_box, False, False, 0)

        self.layout_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 1)
        self.layout_scale.set_name("slider-scale")
        self.layout_scale.set_value(cur_layout_dur)
        self.layout_scale.set_draw_value(False)
        self.layout_scale.connect("value-changed", self.on_layout_scale_changed)
        section_box.pack_start(self.layout_scale, False, False, 0)

        self.card_box.pack_start(section_box, False, False, 0)

    def on_speed_scale_changed(self, scale):
        val = int(scale.get_value())
        self.speed_val_lbl.set_text(f"{val}s")
        self.state["speed_duration"] = val
        self.schedule_save()

    def on_layout_scale_changed(self, scale):
        val = int(scale.get_value())
        self.layout_val_lbl.set_text(f"{val}s")
        self.state["layout_duration"] = val
        self.schedule_save()

    def build_interface_selector(self):
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section_box.set_name("section-box")

        sec_title = Gtk.Label(label="NETWORK INTERFACE")
        sec_title.set_name("section-label")
        sec_title.set_xalign(0.0)
        section_box.pack_start(sec_title, False, False, 0)

        self.iface_combo = Gtk.ComboBoxText()
        self.iface_combo.set_name("custom-combobox")
        self.iface_combo.append("auto", "All Interfaces (Auto)")

        ifaces = get_available_interfaces()
        for iface in ifaces:
            self.iface_combo.append(iface, iface)

        cur_iface = self.state.get("interface", "auto")
        self.iface_combo.set_active_id(cur_iface if cur_iface in ifaces else "auto")
        self.iface_combo.connect("changed", self.on_interface_changed)
        section_box.pack_start(self.iface_combo, False, False, 0)

        self.card_box.pack_start(section_box, False, False, 0)

    def on_interface_changed(self, combo):
        active_id = combo.get_active_id()
        if active_id:
            self.state["interface"] = active_id
            self.schedule_save()

    def build_footer(self):
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer_box.set_margin_top(4)

        hint_label = Gtk.Label(label="Esc or click outside to close")
        hint_label.set_name("hint-label")
        hint_label.set_xalign(0.0)

        close_btn = Gtk.Button(label="Done")
        close_btn.set_name("done-btn")
        close_btn.connect("clicked", lambda w: Gtk.main_quit())

        footer_box.pack_start(hint_label, True, True, 0)
        footer_box.pack_end(close_btn, False, False, 0)
        self.card_box.pack_start(footer_box, False, False, 0)


def apply_styles():
    colors_css = ""
    if os.path.exists(COLORS_FILE):
        try:
            with open(COLORS_FILE, "r") as f:
                colors_css = f.read()
        except Exception:
            pass

    css = f"""
    {colors_css}

    * {{
        font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", sans-serif;
    }}

    window#waybar-quick-net-settings,
    window#net-layout-settings-window,
    window,
    #modal-backdrop {{
        background-color: transparent;
        background: transparent;
    }}

    #card-event-box {{
        background: transparent;
    }}

    #modal-container {{
        background: alpha(@background, 0.94);
        border: 1px solid alpha(@outline_variant, 0.45);
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.6);
    }}

    #header-icon {{
        font-size: 15px;
        color: @primary;
    }}

    #header-title {{
        font-size: 13px;
        font-weight: 700;
        color: @on_surface;
    }}

    #close-btn {{
        background: transparent;
        color: alpha(@on_surface, 0.6);
        border: none;
        padding: 2px 6px;
        font-size: 12px;
        border-radius: 6px;
    }}

    #close-btn:hover {{
        background: alpha(@error, 0.2);
        color: @error;
    }}

    #section-box {{
        background: alpha(@surface_container, 0.3);
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 12px;
        padding: 8px 10px;
    }}

    #section-label {{
        font-size: 9px;
        font-weight: 700;
        color: alpha(@on_surface, 0.6);
        letter-spacing: 0.5px;
    }}

    #mode-btn {{
        background: alpha(@surface_container_high, 0.5);
        border: 1px solid alpha(@outline_variant, 0.3);
        border-radius: 8px;
        padding: 6px 0;
        color: @on_surface;
        font-size: 11px;
        font-weight: 600;
    }}

    #mode-btn:hover {{
        background: alpha(@primary, 0.15);
        border-color: @primary;
        color: @primary;
    }}

    #mode-btn-active {{
        background: @primary;
        border: 1px solid @primary;
        border-radius: 8px;
        padding: 6px 0;
        color: @on_primary;
        font-size: 11px;
        font-weight: 700;
    }}

    #custom-combobox {{
        background: alpha(@surface_container_high, 0.4);
        border: 1px solid alpha(@outline_variant, 0.3);
        border-radius: 8px;
        color: @on_surface;
        font-size: 11px;
        padding: 2px 4px;
    }}

    #slider-label {{
        font-size: 10px;
        color: @on_surface;
    }}

    #slider-val-label {{
        font-size: 10px;
        font-weight: 700;
        color: @primary;
    }}

    #slider-scale trough {{
        min-height: 4px;
        border-radius: 2px;
        background-color: alpha(@on_surface, 0.15);
    }}

    #slider-scale highlight {{
        min-height: 4px;
        border-radius: 2px;
        background-color: @primary;
    }}

    #slider-scale slider {{
        min-height: 12px;
        min-width: 12px;
        margin: -4px 0;
        border-radius: 50%;
        background-color: @primary;
        border: 1.5px solid @background;
    }}

    #hint-label {{
        font-size: 9px;
        color: alpha(@on_surface, 0.4);
    }}

    #done-btn {{
        background: @primary;
        color: @on_primary;
        font-size: 10px;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        padding: 4px 12px;
    }}

    #done-btn:hover {{
        background: alpha(@primary, 0.85);
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
    win = QuickNetSettings()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
