#!/usr/bin/env python3
"""
Waybar Dynamic Island Settings Modal (Compact & Minimal)
A sleek, compact GTK3 + GtkLayerShell settings interface for the Dynamic Island companion.
- Fullscreen transparent click-catcher (SwayNC pattern): clicking outside cleanly destroys the surface.
- Stateless lifecycle: exits with Gtk.main_quit() on backdrop click or Escape.
- Hot-updates island-config.json so changes take effect immediately on the bar.
- Fully themed with Matugen colors from ~/.config/waybar/colors.css.
"""

import os
import sys
import json
import time
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib

CONFIG_FILE = os.path.expanduser("~/.config/waybar/scripts/island/island-config.json")
LEGACY_STATS_FILE = os.path.expanduser("~/.config/waybar/scripts/island/stats.json")

ANIMALS = [
    {"name": "Neko (Cat)", "emoji": "🐱"},
    {"name": "Usagi (Bunny)", "emoji": "🐰"},
    {"name": "Duck (Honk)", "emoji": "🦆"},
    {"name": "Ghost (Booo)", "emoji": "👻"},
    {"name": "Crab (Rave)", "emoji": "🦀"},
    {"name": "Inu (Puppy)", "emoji": "🐶"}
]

DEFAULT_SETTINGS = {
    "auto_cycle": True,
    "default_mode": 0,
    "sleep_enabled": True,
    "sleep_timeout": 15,
    "heat_alerts_enabled": True,
    "temp_warm": 70,
    "temp_hot": 80,
    "temp_critical": 90,
    "decay_enabled": True,
    "decay_interval": 1800,
    "music_dance_enabled": True,
    "marquee_max_len": 13
}

def get_affection_info(score):
    if score >= 100:
        return "Soulmate", "💖"
    elif score >= 50:
        return "Best Friend", "❤️"
    elif score >= 25:
        return "Friend", "🧡"
    elif score >= 10:
        return "Acquaintance", "💛"
    else:
        return "Stranger", "🤍"


class CompactIslandSettings(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("IslandSettings")
        self.set_name("island-settings-window")

        self.load_config()
        self.save_timer_id = None

        # GtkLayerShell: Fullscreen transparent backdrop
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "waybar-island-settings")

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

        # Positioning Wrapper: Center under top Waybar
        wrapper = Gtk.Box()
        wrapper.set_halign(Gtk.Align.CENTER)
        wrapper.set_valign(Gtk.Align.START)
        wrapper.set_margin_top(44)
        self.backdrop.add(wrapper)

        # Card EventBox: intercepts inner clicks
        self.card_event_box = Gtk.EventBox()
        self.card_event_box.set_name("card-event-box")
        self.card_event_box.connect("button-press-event", lambda w, e: True)
        wrapper.add(self.card_event_box)

        # Main Compact Card Box (290px width)
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        self.card_box.set_name("modal-container")
        self.card_box.set_size_request(290, -1)
        self.card_event_box.add(self.card_box)

        # Build Compact UI
        self.build_header()
        self.build_animal_strip()
        self.build_companion_status()
        self.build_settings_list()

        self.connect("key-press-event", self.on_key_press)

    def load_config(self):
        target = CONFIG_FILE if os.path.exists(CONFIG_FILE) else LEGACY_STATS_FILE
        self.config_data = {
            "current_animal_idx": 0,
            "settings": dict(DEFAULT_SETTINGS),
            "animals": {}
        }
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config_data["current_animal_idx"] = int(data.get("current_animal_idx", 0)) % len(ANIMALS)
                loaded_settings = data.get("settings", {})
                if isinstance(loaded_settings, dict):
                    self.config_data["settings"] = {**DEFAULT_SETTINGS, **loaded_settings}
                if "animals" in data and isinstance(data["animals"], dict):
                    self.config_data["animals"] = data["animals"]
            except Exception:
                pass

        now = time.time()
        for a in ANIMALS:
            name = a["name"]
            if name not in self.config_data["animals"]:
                self.config_data["animals"][name] = {
                    "affection_score": 0,
                    "last_decay_time": now,
                    "last_pet_time": now
                }

    def schedule_save(self):
        if self.save_timer_id is not None:
            GLib.source_remove(self.save_timer_id)
        self.save_timer_id = GLib.timeout_add(100, self._do_save)

    def _do_save(self):
        self.save_timer_id = None
        try:
            tmp_file = CONFIG_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)
            os.replace(tmp_file, CONFIG_FILE)
        except Exception as e:
            sys.stderr.write(f"Error saving config: {e}\n")
        return False

    def on_backdrop_clicked(self, widget, event):
        Gtk.main_quit()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    # ---------------------------------------------------------
    # UI Builders
    # ---------------------------------------------------------
    def build_header(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        lbl_title = Gtk.Label(label="🐾 Island Settings")
        lbl_title.set_name("header-title")
        lbl_title.set_xalign(0.0)
        header_box.pack_start(lbl_title, True, True, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_name("close-btn")
        btn_close.set_relief(Gtk.ReliefStyle.NONE)
        btn_close.connect("clicked", lambda b: Gtk.main_quit())
        header_box.pack_start(btn_close, False, False, 0)

        self.card_box.pack_start(header_box, False, False, 0)

    def build_animal_strip(self):
        # Single horizontal row of 6 circular/rounded emoji buttons
        strip_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        strip_box.set_homogeneous(True)

        self.animal_buttons = []
        cur_idx = self.config_data["current_animal_idx"]

        for idx, a in enumerate(ANIMALS):
            btn = Gtk.Button()
            btn.set_name("animal-btn-active" if idx == cur_idx else "animal-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)

            lbl = Gtk.Label(label=a["emoji"])
            lbl.set_name("animal-emoji")
            btn.add(lbl)

            btn.connect("clicked", self.on_animal_selected, idx)
            strip_box.pack_start(btn, True, True, 0)
            self.animal_buttons.append(btn)

        self.card_box.pack_start(strip_box, False, False, 0)

    def on_animal_selected(self, btn, idx):
        self.config_data["current_animal_idx"] = idx
        for i, b in enumerate(self.animal_buttons):
            b.set_name("animal-btn-active" if i == idx else "animal-btn")
        self.schedule_save()
        self.update_companion_status()

    def build_companion_status(self):
        self.status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.status_box.set_name("status-chip")

        self.lbl_status = Gtk.Label()
        self.lbl_status.set_name("status-label")
        self.lbl_status.set_xalign(0.0)
        self.status_box.pack_start(self.lbl_status, True, True, 0)

        self.btn_pet = Gtk.Button(label="Pet ❤️")
        self.btn_pet.set_name("pet-btn")
        self.btn_pet.connect("clicked", self.on_pet_clicked)
        self.status_box.pack_start(self.btn_pet, False, False, 0)

        self.card_box.pack_start(self.status_box, False, False, 0)
        self.update_companion_status()

    def update_companion_status(self):
        cur_idx = self.config_data["current_animal_idx"]
        animal = ANIMALS[cur_idx]
        stats = self.config_data["animals"].get(animal["name"], {"affection_score": 0})
        score = int(stats.get("affection_score", 0))
        title, heart = get_affection_info(score)

        short_name = animal["name"].split()[0]
        self.lbl_status.set_markup(
            f"<b>{animal['emoji']} {short_name}</b> • <span color='#f9a8d4'>{title} {heart}</span> ({score})"
        )

    def on_pet_clicked(self, btn):
        cur_idx = self.config_data["current_animal_idx"]
        animal = ANIMALS[cur_idx]
        stats = self.config_data["animals"].get(animal["name"], {"affection_score": 0})
        stats["affection_score"] = int(stats.get("affection_score", 0)) + 1
        stats["last_pet_time"] = time.time()
        self.config_data["animals"][animal["name"]] = stats
        self.schedule_save()
        self.update_companion_status()
        subprocess.Popen(["pkill", "-SIGUSR1", "-f", "dynamic-island.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def build_settings_list(self):
        settings = self.config_data["settings"]

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        list_box.set_name("settings-list")

        # Toggles
        list_box.pack_start(self.create_compact_toggle("🔄 Auto-Cycle Views", settings.get("auto_cycle", True), "auto_cycle"), False, False, 0)
        list_box.pack_start(self.create_compact_toggle("💤 Idle Sleep", settings.get("sleep_enabled", True), "sleep_enabled"), False, False, 0)
        list_box.pack_start(self.create_compact_toggle("🌡️ Thermal Alerts", settings.get("heat_alerts_enabled", True), "heat_alerts_enabled"), False, False, 0)
        list_box.pack_start(self.create_compact_toggle("💔 Affection Decay", settings.get("decay_enabled", True), "decay_enabled"), False, False, 0)
        list_box.pack_start(self.create_compact_toggle("🎵 Music Dancing", settings.get("music_dance_enabled", True), "music_dance_enabled"), False, False, 0)

        # Sliders (Sleep timeout & Alert temp)
        list_box.pack_start(self.create_compact_slider("⏱️ Sleep After", 5, 60, settings.get("sleep_timeout", 15), "s", "sleep_timeout"), False, False, 0)
        list_box.pack_start(self.create_compact_slider("🔥 Alert Temp", 60, 95, settings.get("temp_hot", 80), "°C", "temp_hot"), False, False, 0)

        self.card_box.pack_start(list_box, False, False, 0)

    def create_compact_toggle(self, label_text, initial_val, key):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_name("compact-row")

        lbl = Gtk.Label(label=label_text)
        lbl.set_name("row-label")
        lbl.set_xalign(0.0)
        row.pack_start(lbl, True, True, 0)

        switch = Gtk.Switch()
        switch.set_active(bool(initial_val))
        switch.set_valign(Gtk.Align.CENTER)
        switch.connect("state-set", self.on_toggle_changed, key)
        row.pack_start(switch, False, False, 0)

        return row

    def on_toggle_changed(self, switch, state, key):
        self.config_data["settings"][key] = state
        self.schedule_save()
        return False

    def create_compact_slider(self, label_text, min_val, max_val, cur_val, unit, key):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.set_name("compact-row")

        lbl = Gtk.Label(label=label_text)
        lbl.set_name("row-label")
        lbl.set_xalign(0.0)
        row.pack_start(lbl, False, False, 0)

        adj = Gtk.Adjustment(value=cur_val, lower=min_val, upper=max_val, step_increment=1, page_increment=5)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        scale.set_name("slider-scale")
        scale.set_size_request(85, 14)
        scale.set_draw_value(False)

        lbl_val = Gtk.Label(label=f"{int(cur_val)}{unit}")
        lbl_val.set_name("slider-val-label")
        lbl_val.set_size_request(32, -1)
        lbl_val.set_xalign(1.0)

        scale.connect("value-changed", self.on_slider_changed, key, unit, lbl_val)

        row.pack_start(scale, True, True, 0)
        row.pack_start(lbl_val, False, False, 0)

        return row

    def on_slider_changed(self, scale, key, unit, lbl_val):
        val = int(scale.get_value())
        lbl_val.set_text(f"{val}{unit}")
        self.config_data["settings"][key] = val
        if key == "temp_hot":
            # Keep warm and critical tiers proportionally synced
            self.config_data["settings"]["temp_warm"] = max(50, val - 10)
            self.config_data["settings"]["temp_critical"] = min(105, val + 10)
        self.schedule_save()


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
        font-family: "Adwaita Sans", "Inter", "DejaVu Sans", "JetBrainsMono Nerd Font", sans-serif;
        font-size: 11px;
    }}

    window#island-settings-window,
    #modal-backdrop {{
        background-color: transparent;
        background: transparent;
    }}

    #card-event-box {{
        background: transparent;
    }}

    #modal-container {{
        background: alpha(@background, 0.95);
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.45);
        border-radius: 18px;
        padding: 10px 14px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6);
    }}

    #header-title {{
        color: @primary;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }}

    #close-btn {{
        color: @outline;
        font-size: 11px;
        font-weight: bold;
        padding: 1px 6px;
        border-radius: 50%;
        background: transparent;
    }}

    #close-btn:hover {{
        background: alpha(@error, 0.2);
        color: @error;
    }}

    #animal-btn {{
        background: alpha(@surface_container, 0.5);
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 10px;
        padding: 4px 0;
        transition: all 0.2s ease;
    }}

    #animal-btn:hover {{
        background: alpha(@surface_container_high, 0.85);
        border-color: alpha(@primary, 0.6);
    }}

    #animal-btn-active {{
        background: @primary;
        border: 1px solid @primary;
        border-radius: 10px;
        padding: 4px 0;
    }}

    #animal-emoji {{
        font-size: 15px;
    }}

    #status-chip {{
        background: alpha(@surface_container_high, 0.4);
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 10px;
        padding: 4px 8px;
    }}

    #status-label {{
        font-size: 10px;
        color: @on_surface;
    }}

    #pet-btn {{
        background: alpha(@primary, 0.15);
        color: @primary;
        font-weight: 700;
        font-size: 10px;
        border-radius: 12px;
        border: 1px solid alpha(@primary, 0.35);
        padding: 1px 8px;
    }}

    #pet-btn:hover {{
        background: @primary;
        color: @on_primary;
    }}

    #settings-list {{
        background: alpha(@surface_container, 0.35);
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 12px;
        padding: 6px 10px;
    }}

    #compact-row {{
        min-height: 22px;
        padding: 1px 0;
    }}

    #row-label {{
        font-size: 10px;
        font-weight: 500;
        color: @on_surface;
    }}

    switch {{
        min-width: 28px;
        min-height: 14px;
        border-radius: 8px;
        background-color: alpha(@on_surface, 0.2);
    }}

    switch:checked {{
        background-color: @primary;
    }}

    switch slider {{
        min-width: 10px;
        min-height: 10px;
        border-radius: 50%;
        background-color: @on_primary;
        margin: 2px;
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
    win = CompactIslandSettings()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
