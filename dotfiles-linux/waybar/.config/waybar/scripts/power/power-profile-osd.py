#!/usr/bin/env python3
import os
import sys
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

PROFILE_CONFIGS = {
    "performance": {
        "title": "Performance Mode",
        "icon": "",
        "color_var": "@error",
        "fallback_color": "#ffb4ab",
        "fan_text": "Fans: High / Overboost 󰈐",
        "cpu_text": "Max CPU Clock • Higher Heat",
    },
    "balanced": {
        "title": "Balanced Mode",
        "icon": "",
        "color_var": "@primary",
        "fallback_color": "#abc7ff",
        "fan_text": "Fans: Dynamic / Standard 󰌪",
        "cpu_text": "Balanced Performance & Battery",
    },
    "power-saver": {
        "title": "Quiet Mode",
        "icon": "",
        "color_var": "#a6e3a1",
        "fallback_color": "#a6e3a1",
        "fan_text": "Fans: Silent / Low 󰌪",
        "cpu_text": "Power Throttled • Lowest Heat",
    },
}


class PowerProfileOSD(Gtk.Window):
    def __init__(self, next_profile, prev_profile=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("PowerProfileOSD")
        self.set_name("power-profile-osd")

        self.next_profile = next_profile if next_profile in PROFILE_CONFIGS else "balanced"
        self.prev_profile = prev_profile if prev_profile in PROFILE_CONFIGS else None

        # Layer Shell Configuration
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self, "power-profile-osd")
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        # Position at top center of screen, right below Waybar
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 54)

        # Main Card Box
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.set_name("osd-card")
        self.add(card)

        # Smooth Slide Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.stack.set_transition_duration(260)
        card.pack_start(self.stack, True, True, 0)

        # Populate rows
        if self.prev_profile and self.prev_profile != self.next_profile:
            prev_row = self.create_profile_row(self.prev_profile)
            self.stack.add_named(prev_row, self.prev_profile)

            next_row = self.create_profile_row(self.next_profile)
            self.stack.add_named(next_row, self.next_profile)

            self.stack.set_visible_child_name(self.prev_profile)
            # Trigger slide animation right after mapping
            GLib.timeout_add(35, self._trigger_slide)
        else:
            next_row = self.create_profile_row(self.next_profile)
            self.stack.add_named(next_row, self.next_profile)
            self.stack.set_visible_child_name(self.next_profile)

        # Load Styles
        self.apply_styles()

        # Auto-dismiss after 1600ms
        GLib.timeout_add(1600, self.on_timeout)

    def create_profile_row(self, profile_name):
        cfg = PROFILE_CONFIGS.get(profile_name, PROFILE_CONFIGS["balanced"])
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        row.set_name(f"osd-row-{profile_name}")

        # Icon
        lbl_icon = Gtk.Label(label=cfg["icon"])
        lbl_icon.set_name("osd-icon")
        lbl_icon.get_style_context().add_class(f"icon-{profile_name}")
        row.pack_start(lbl_icon, False, False, 0)

        # Content Box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        row.pack_start(content_box, True, True, 0)

        # Title
        lbl_title = Gtk.Label(label=cfg["title"])
        lbl_title.set_name("osd-title")
        lbl_title.get_style_context().add_class(f"title-{profile_name}")
        lbl_title.set_xalign(0.0)
        content_box.pack_start(lbl_title, False, False, 0)

        # Effects
        effects = f"{cfg['fan_text']}  •  {cfg['cpu_text']}"
        lbl_effects = Gtk.Label(label=effects)
        lbl_effects.set_name("osd-effects")
        lbl_effects.set_xalign(0.0)
        content_box.pack_start(lbl_effects, False, False, 0)

        return row

    def _trigger_slide(self):
        self.stack.set_visible_child_name(self.next_profile)
        return False

    def apply_styles(self):
        colors_file = os.path.expanduser("~/.config/waybar/colors.css")
        colors_css = ""
        if os.path.exists(colors_file):
            with open(colors_file, "r") as f:
                colors_css = f.read()

        css = f"""
        {colors_css}

        * {{
            font-family: "Adwaita Sans", "Inter", "DejaVu Sans", "JetBrainsMono Nerd Font", sans-serif;
        }}

        window#power-profile-osd {{
            background: transparent;
            background-color: transparent;
        }}

        #osd-card {{
            background: alpha(@background, 0.94);
            border: 1px solid alpha(@outline_variant, 0.45);
            border-radius: 18px;
            padding: 10px 22px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
        }}

        #osd-icon {{
            font-size: 24px;
            margin-right: 2px;
        }}

        #osd-title {{
            font-size: 13px;
            font-weight: 700;
        }}

        #osd-effects {{
            font-size: 11px;
            font-weight: 500;
            color: @on_surface_variant;
        }}

        .icon-performance, .title-performance {{
            color: @error;
        }}

        .icon-balanced, .title-balanced {{
            color: @primary;
        }}

        .icon-power-saver, .title-power-saver {{
            color: #a6e3a1;
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
            sys.stderr.write(f"Warning loading OSD CSS: {e}\n")

    def on_timeout(self):
        Gtk.main_quit()
        return False


def main():
    next_profile = sys.argv[1] if len(sys.argv) > 1 else "balanced"
    prev_profile = sys.argv[2] if len(sys.argv) > 2 else None
    win = PowerProfileOSD(next_profile, prev_profile)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
