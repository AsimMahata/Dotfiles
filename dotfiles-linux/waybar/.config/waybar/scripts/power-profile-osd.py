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
    def __init__(self, profile_name):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("PowerProfileOSD")
        self.set_name("power-profile-osd")

        cfg = PROFILE_CONFIGS.get(profile_name, PROFILE_CONFIGS["balanced"])

        # Layer Shell Configuration
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self, "power-profile-osd")
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        # Position at the top center of the screen, right below Waybar
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 54)

        # Main Card Box
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        card.set_name("osd-card")
        self.add(card)

        # Icon
        lbl_icon = Gtk.Label(label=cfg["icon"])
        lbl_icon.set_name("osd-icon")
        card.pack_start(lbl_icon, False, False, 0)

        # Content Text Box (Vertical)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.pack_start(content_box, True, True, 0)

        # Title Label
        lbl_title = Gtk.Label(label=cfg["title"])
        lbl_title.set_name("osd-title")
        lbl_title.set_xalign(0.0)
        content_box.pack_start(lbl_title, False, False, 0)

        # Subtitle / Effects Label
        fan_str = cfg["fan_text"]
        cpu_str = cfg["cpu_text"]
        effects = f"{fan_str}  •  {cpu_str}"
        lbl_effects = Gtk.Label(label=effects)
        lbl_effects.set_name("osd-effects")
        lbl_effects.set_xalign(0.0)
        content_box.pack_start(lbl_effects, False, False, 0)

        # Load Styles
        self.apply_styles(cfg)

        # Auto-dismiss after 1500ms (1.5 seconds)
        GLib.timeout_add(1500, self.on_timeout)

    def apply_styles(self, cfg):
        colors_file = os.path.expanduser("~/.config/waybar/colors.css")
        colors_css = ""
        if os.path.exists(colors_file):
            with open(colors_file, "r") as f:
                colors_css = f.read()

        accent_color = cfg["color_var"] if "@" in cfg["color_var"] else cfg["fallback_color"]

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
            color: {accent_color};
            margin-right: 2px;
        }}

        #osd-title {{
            font-size: 13px;
            font-weight: 700;
            color: {accent_color};
        }}

        #osd-effects {{
            font-size: 11px;
            font-weight: 500;
            color: @on_surface_variant;
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
    profile = sys.argv[1] if len(sys.argv) > 1 else "balanced"
    win = PowerProfileOSD(profile)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
