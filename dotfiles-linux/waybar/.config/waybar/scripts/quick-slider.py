#!/usr/bin/env python3
"""
Waybar Quick Slider (Stateless, Bulletproof AAA UX)
A unified GTK Layer Shell modal slider for Volume and Brightness.
- Uses SwayNC's fullscreen click-catcher technique: clicking outside instantly exits and frees the surface.
- No PID files, no background signals, zero ghost windows.
- Smooth 60fps non-blocking volume & brightness dragging.
- Mouse wheel scroll adjustment & Escape key dismiss.
"""

import os
import sys
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib


# ---------------------------------------------------------
# Audio & Brightness Backend Helpers
# ---------------------------------------------------------
def get_volume_state():
    try:
        out = subprocess.check_output(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            stderr=subprocess.DEVNULL,
        ).decode()
        parts = out.strip().split()
        vol = float(parts[1]) if len(parts) > 1 else 0.5
        muted = "[MUTED]" in out
        return int(round(vol * 100)), muted
    except Exception:
        return 50, False


def get_brightness_state():
    try:
        out = subprocess.check_output(
            ["brightnessctl", "-m"],
            stderr=subprocess.DEVNULL,
        ).decode()
        parts = out.strip().split(",")
        return max(1, min(100, int(parts[3].rstrip("%"))))
    except Exception:
        return 50


class AudioController:
    def __init__(self):
        self.pending_val = None
        self.timer_active = False

    def set_volume_async(self, val):
        self.pending_val = max(0, min(100, val))
        if not self.timer_active:
            self.timer_active = True
            GLib.timeout_add(16, self._flush)

    def _flush(self):
        if self.pending_val is not None:
            val = self.pending_val
            self.pending_val = None
            val_float = val / 100.0
            subprocess.Popen(
                [
                    "wpctl",
                    "set-volume",
                    "@DEFAULT_AUDIO_SINK@",
                    f"{val_float:.2f}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self.timer_active = False
        return False

    def toggle_mute_async(self):
        subprocess.Popen(
            ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class BrightnessController:
    def __init__(self):
        self.pending_val = None
        self.timer_active = False

    def set_brightness_async(self, val):
        self.pending_val = max(1, min(100, val))
        if not self.timer_active:
            self.timer_active = True
            GLib.timeout_add(16, self._flush)

    def _flush(self):
        if self.pending_val is not None:
            val = self.pending_val
            self.pending_val = None
            subprocess.Popen(
                ["brightnessctl", "set", f"{val}%"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self.timer_active = False
        return False


# ---------------------------------------------------------
# Modal Window
# ---------------------------------------------------------
class QuickSlider(Gtk.Window):
    def __init__(self, mode, audio_ctrl, bright_ctrl):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.mode = mode
        self.audio_ctrl = audio_ctrl
        self.bright_ctrl = bright_ctrl

        self.set_title("WaybarQuickSlider")
        self.set_name("waybar-quick-slider")

        # Layer Shell: Fullscreen transparent click-catcher (SwayNC pattern)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "waybar-quick-slider")

        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.ON_DEMAND
        )

        # Transparent Backdrop: Clicking outside exits and cleanly destroys surface
        self.backdrop = Gtk.EventBox()
        self.backdrop.set_name("modal-backdrop")
        self.backdrop.connect("button-press-event", self.on_backdrop_clicked)
        self.add(self.backdrop)

        # Positioning Wrapper: Aligns card under respective Waybar icon
        wrapper = Gtk.Box()
        wrapper.set_halign(Gtk.Align.END)
        wrapper.set_valign(Gtk.Align.START)
        wrapper.set_margin_top(44)
        margin_end = 160 if mode == "volume" else 105
        wrapper.set_margin_end(margin_end)
        self.backdrop.add(wrapper)

        # Card EventBox: Stops click propagation & enables mouse scrolling
        self.card_event_box = Gtk.EventBox()
        self.card_event_box.set_name("card-event-box")
        self.card_event_box.add_events(Gdk.EventMask.SCROLL_MASK)
        self.card_event_box.connect("button-press-event", lambda w, e: True)
        self.card_event_box.connect("scroll-event", self.on_card_scroll)
        wrapper.add(self.card_event_box)

        # Card Container
        self.card_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=12
        )
        self.card_container.set_name("modal-container")
        self.card_event_box.add(self.card_container)

        # Icon / Button
        self.btn_icon = Gtk.Button()
        self.btn_icon.set_name("icon-btn")
        self.btn_icon.set_relief(Gtk.ReliefStyle.NONE)
        self.lbl_icon = Gtk.Label()
        self.lbl_icon.set_name("icon-label")
        self.btn_icon.add(self.lbl_icon)
        self.btn_icon.connect("clicked", self.on_icon_clicked)
        self.card_container.pack_start(self.btn_icon, False, False, 0)

        # Slider Scale
        self.adjustment = Gtk.Adjustment(
            value=50, lower=0, upper=100, step_increment=1, page_increment=5
        )
        self.scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adjustment
        )
        self.scale.set_name("slider-scale")
        self.scale.set_size_request(160, 24)
        self.scale.set_draw_value(False)
        self.scale.connect("value-changed", self.on_slider_changed)
        self.card_container.pack_start(self.scale, True, True, 0)

        # Percentage Label
        self.lbl_percent = Gtk.Label()
        self.lbl_percent.set_name("percent-label")
        self.lbl_percent.set_size_request(44, -1)
        self.lbl_percent.set_xalign(1.0)
        self.card_container.pack_start(self.lbl_percent, False, False, 0)

        # Initialize Mode Data
        self._updating_ui = True
        if mode == "volume":
            self.vol, self.is_muted = get_volume_state()
            self.adjustment.set_lower(0)
            self.adjustment.set_value(self.vol)
            self.update_volume_ui()
        else:
            self.brightness = get_brightness_state()
            self.adjustment.set_lower(1)
            self.adjustment.set_value(self.brightness)
            self.update_brightness_ui()
        self._updating_ui = False

        self.connect("key-press-event", self.on_key_press)

    def on_backdrop_clicked(self, widget, event):
        # Clicked outside: clean exit destroys the Wayland surface immediately
        Gtk.main_quit()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    # ---------------------------------------------------------
    # UI Updates
    # ---------------------------------------------------------
    def get_volume_icon(self, vol, muted):
        if muted:
            return ""
        elif vol == 0:
            return ""
        elif vol < 50:
            return ""
        else:
            return ""

    def get_brightness_icon(self, val):
        if val < 30:
            return "󰃞"
        elif val < 70:
            return "󰃟"
        else:
            return "󰃠"

    def update_volume_ui(self):
        self.lbl_icon.set_text(self.get_volume_icon(self.vol, self.is_muted))
        if self.is_muted:
            self.lbl_percent.set_text("Mute")
            self.scale.set_sensitive(False)
        else:
            self.lbl_percent.set_text(f"{self.vol}%")
            self.scale.set_sensitive(True)

    def update_brightness_ui(self):
        self.lbl_icon.set_text(self.get_brightness_icon(self.brightness))
        self.lbl_percent.set_text(f"{self.brightness}%")
        self.scale.set_sensitive(True)

    # ---------------------------------------------------------
    # Controls Interaction
    # ---------------------------------------------------------
    def on_slider_changed(self, scale):
        if self._updating_ui:
            return

        val = int(scale.get_value())
        if self.mode == "volume":
            self.vol = val
            self.audio_ctrl.set_volume_async(val)
            if self.is_muted:
                self.is_muted = False
            self.update_volume_ui()
        else:
            self.brightness = val
            self.bright_ctrl.set_brightness_async(val)
            self.update_brightness_ui()

    def on_icon_clicked(self, btn):
        if self.mode == "volume":
            self.audio_ctrl.toggle_mute_async()
            self.is_muted = not self.is_muted
            self.update_volume_ui()

    def on_card_scroll(self, widget, event):
        step = 5
        is_up = event.direction == Gdk.ScrollDirection.UP or (
            event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y < 0
        )
        is_down = event.direction == Gdk.ScrollDirection.DOWN or (
            event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y > 0
        )

        if not (is_up or is_down):
            return False

        if self.mode == "volume":
            new_val = (
                min(100, self.vol + step) if is_up else max(0, self.vol - step)
            )
        else:
            new_val = (
                min(100, self.brightness + step)
                if is_up
                else max(1, self.brightness - step)
            )

        self.scale.set_value(new_val)
        return True


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
        font-family: "JetBrains Mono Nerd Font", "JetBrainsMono Nerd Font", monospace;
        font-size: 13px;
        font-weight: bold;
    }}

    window#waybar-quick-slider,
    #modal-backdrop {{
        background-color: transparent;
        background: transparent;
    }}

    #card-event-box {{
        background: transparent;
    }}

    #modal-container {{
        background: alpha(@background, 0.92);
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.5);
        border-radius: 20px;
        padding: 10px 18px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }}

    #icon-btn {{
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0 6px;
        border-radius: 50px;
        transition: background-color 0.2s ease;
    }}

    #icon-btn:hover {{
        background: alpha(@on_surface, 0.1);
    }}

    #icon-label {{
        color: @primary;
        font-size: 17px;
    }}

    #icon-btn:hover #icon-label {{
        color: @tertiary_fixed;
    }}

    #slider-scale trough {{
        min-height: 8px;
        min-width: 150px;
        border-radius: 4px;
        background-color: alpha(@on_surface, 0.18);
    }}

    #slider-scale highlight {{
        min-height: 8px;
        border-radius: 4px;
        background-color: @primary;
    }}

    #slider-scale slider {{
        min-height: 18px;
        min-width: 18px;
        margin: -5px 0;
        border-radius: 50%;
        background-color: @primary;
        border: 2px solid @background;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
        transition: background-color 0.2s ease;
    }}

    #slider-scale slider:hover {{
        background-color: @primary_fixed;
    }}

    #percent-label {{
        color: @on_surface;
        font-weight: bold;
        font-size: 13px;
        min-width: 44px;
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
    mode = "volume"
    if "--mode" in sys.argv:
        try:
            idx = sys.argv.index("--mode")
            mode = sys.argv[idx + 1]
        except Exception:
            pass

    apply_styles()
    audio_ctrl = AudioController()
    bright_ctrl = BrightnessController()
    win = QuickSlider(mode, audio_ctrl, bright_ctrl)
    win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
