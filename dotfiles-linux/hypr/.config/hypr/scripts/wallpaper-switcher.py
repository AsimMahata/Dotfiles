#!/usr/bin/env python3
"""
Curved 3D Floating Cover-Flow Wallpaper Switcher for Hyprland / Wayland.
- Fullscreen transparent click-catcher pattern (GtkLayerShell Layer.TOP).
- Parabolic cover-flow height arching (center is tallest, flanking cards decrease in size).
- Mouse wheel scrolling & arrow key navigation with 60fps coalescing.
- Space to shuffle, Enter to apply, Escape to dismiss.
- Clean formatted titles, thumbnail caching, and live Matugen theming.
"""

import os
import sys
import json
import random
import signal
import subprocess
from pathlib import Path
from threading import Thread

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, GtkLayerShell


def check_toggle():
    """If an instance of wallpaper-switcher is already running, terminate it and exit (toggle behavior)."""
    my_pid = os.getpid()
    try:
        out = subprocess.check_output(["pgrep", "-f", "wallpaper-switcher.py"]).decode().split()
        other_pids = [int(p) for p in out if int(p) != my_pid]
        if other_pids:
            for p in other_pids:
                try:
                    os.kill(p, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            sys.exit(0)
    except subprocess.CalledProcessError:
        pass
    except Exception:
        pass


# -----------------------------------------------------------------------------
# CSS Styling (GTK3 Compliant with Dynamic Matugen Colors)
# -----------------------------------------------------------------------------
def get_css():
    colors_file = os.path.expanduser("~/.config/waybar/colors.css")
    colors_css = ""
    if os.path.exists(colors_file):
        try:
            with open(colors_file, "r") as f:
                colors_css = f.read()
        except Exception:
            pass

    return f"""
    {colors_css}

    * {{
        font-family: "Inter", "Adwaita Sans", "DejaVu Sans", "JetBrainsMono Nerd Font", sans-serif;
    }}

    window#hyprwallpaper-window,
    #modal-backdrop {{
        background: transparent;
        background-color: transparent;
    }}

    #card-event-box {{
        background: transparent;
    }}

    /* Active Info & Palette Badge */
    #info-badge {{
        background-color: @surface_container;
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.6);
        border-radius: 18px;
        padding: 6px 18px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.65);
    }}

    #title-label {{
        font-size: 14px;
        font-weight: 700;
        color: @on_surface;
    }}

    #meta-label {{
        font-size: 11px;
        font-weight: 500;
        color: alpha(@on_surface, 0.65);
    }}

    /* Card Frames (Parabolic Arching) */
    .flow-card {{
        background-color: alpha(@surface_container_lowest, 0.5);
        border-radius: 16px;
        padding: 3px;
        transition: all 180ms ease-in-out;
    }}

    #card-center {{
        border: 2px solid @primary;
        border-radius: 20px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7);
    }}

    #card-near {{
        border: 1px solid alpha(@outline_variant, 0.45);
        border-radius: 16px;
        opacity: 0.85;
    }}

    #card-far {{
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 12px;
        opacity: 0.55;
    }}

    /* Control Bar (Solid Pill) */
    #action-bar {{
        background-color: @surface_container;
        border: 1px solid alpha(@outline_variant, 0.6);
        border-radius: 24px;
        padding: 6px 16px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.75);
    }}

    button.dock-btn {{
        border-radius: 14px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
        background-color: transparent;
        background-image: none;
        color: @on_surface;
        border: none;
        box-shadow: none;
        outline: none;
        transition: all 150ms ease-in-out;
    }}

    button.dock-btn:hover {{
        background-color: alpha(@on_surface, 0.12);
        color: @primary;
        border: none;
        box-shadow: none;
    }}

    button.dock-btn.suggested-action {{
        background-color: @primary;
        color: @on_primary;
        border: none;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
    }}

    button.dock-btn.suggested-action:hover {{
        background-color: @primary_fixed;
        color: @on_primary_fixed;
        border: none;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
    }}

    button.dock-btn:disabled {{
        background-color: alpha(@on_surface, 0.08);
        color: alpha(@on_surface, 0.35);
        border: none;
        box-shadow: none;
    }}

    /* Mini Matugen Color Chips */
    .color-chip {{
        min-width: 12px;
        min-height: 12px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    .chip-primary {{ background-color: @primary; }}
    .chip-surface {{ background-color: @surface; }}
    .chip-tertiary {{ background-color: @tertiary; }}
    .chip-secondary {{ background-color: @secondary; }}
    """


# -----------------------------------------------------------------------------
# Wallpaper Switcher App
# -----------------------------------------------------------------------------
class WallpaperSwitcher(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.set_title("HyprWallpaper")
        self.set_name("hyprwallpaper-window")

        # Layer Shell: Fullscreen transparent click-catcher (SwayNC pattern)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "hyprwallpaper")

        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        # Grab keyboard exclusively so Arrow keys, Space, Enter, and Esc work instantly
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)

        # Apply CSS
        self.apply_css()

        # Directories
        self.pictures_dir = Path.home() / "Pictures/wallpapers"
        self.cache_root = Path.home() / ".cache/hyprwallpaper"
        self.thumb_dir = self.cache_root / "thumbnails"
        self.count_file = self.cache_root / "counts/counts.json"

        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.count_file.parent.mkdir(parents=True, exist_ok=True)

        self.usage_counts = self.load_counts()
        self.wallpapers = self.discover_wallpapers()
        self.current_index = 0
        self.pixbuf_cache = {}

        # Scroll Throttling State (60fps)
        self.scroll_timer_active = False
        self.scroll_delta = 0

        # Build UI Structure
        self.build_ui()

        # Connect global keyboard shortcuts
        self.connect("key-press-event", self.on_key_press)

        # Initial render of coverflow
        if self.wallpapers:
            self.render_coverflow()

    def apply_css(self):
        provider = Gtk.CssProvider()
        try:
            provider.load_from_data(get_css().encode())
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            sys.stderr.write(f"Warning loading CSS: {e}\n")

    # -------------------------------------------------------------------------
    # Wallpaper Discovery & Usage Counts
    # -------------------------------------------------------------------------
    def load_counts(self):
        if self.count_file.exists():
            try:
                with open(self.count_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_counts(self):
        try:
            with open(self.count_file, "w") as f:
                json.dump(self.usage_counts, f, indent=2)
        except Exception:
            pass

    def img_key(self, img_path):
        try:
            return str(img_path.relative_to(self.pictures_dir))
        except ValueError:
            return str(img_path.name)

    def discover_wallpapers(self):
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        images = []
        if self.pictures_dir.exists():
            for root, dirs, files in os.walk(self.pictures_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    p = Path(root) / f
                    if p.suffix.lower() in exts:
                        images.append(p)

        # Sort by usage counts descending, then filename
        images.sort(
            key=lambda p: (
                -self.usage_counts.get(self.img_key(p), 0),
                str(p.name).lower(),
            )
        )
        return images

    def format_title(self, img_path):
        stem = img_path.stem
        # Clean @17fav -> Favorite 17
        if stem.startswith("@") and "fav" in stem:
            num = "".join(filter(str.isdigit, stem))
            return f"Favorite #{num}" if num else "Favorite"
        # Clean random digits if title is just numbers
        if stem.isdigit():
            return f"Wallpaper #{stem[:6]}"
        # Replace underscores and hyphens
        cleaned = stem.replace("_", " ").replace("-", " ")
        return cleaned.title()

    # -------------------------------------------------------------------------
    # UI Hierarchy
    # -------------------------------------------------------------------------
    def build_ui(self):
        # 1. Fullscreen Transparent Backdrop (Click to dismiss)
        self.backdrop = Gtk.EventBox()
        self.backdrop.set_name("modal-backdrop")
        self.backdrop.connect("button-press-event", self.on_backdrop_clicked)
        self.add(self.backdrop)

        # 2. Centered Alignment Wrapper (Floats near bottom center)
        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrapper.set_halign(Gtk.Align.CENTER)
        wrapper.set_valign(Gtk.Align.END)
        wrapper.set_margin_bottom(50)
        self.backdrop.add(wrapper)

        # 3. Card EventBox (Intercepts clicks & handles mouse wheel scroll)
        self.card_event_box = Gtk.EventBox()
        self.card_event_box.set_name("card-event-box")
        self.card_event_box.add_events(Gdk.EventMask.SCROLL_MASK)
        self.card_event_box.connect("button-press-event", lambda w, e: True)
        self.card_event_box.connect("scroll-event", self.on_dock_scroll)
        wrapper.add(self.card_event_box)

        # 4. Main Vertical Dock Container
        dock_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        dock_vbox.set_halign(Gtk.Align.CENTER)
        self.card_event_box.add(dock_vbox)

        # 4A. Metadata & Palette Info Pill (Floats above cards)
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.info_box.set_name("info-badge")
        self.info_box.set_halign(Gtk.Align.CENTER)

        self.lbl_title = Gtk.Label()
        self.lbl_title.set_name("title-label")
        self.info_box.pack_start(self.lbl_title, False, False, 0)

        self.lbl_meta = Gtk.Label()
        self.lbl_meta.set_name("meta-label")
        self.info_box.pack_start(self.lbl_meta, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.info_box.pack_start(sep, False, False, 2)

        # Matugen Palette Chips
        palette_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        palette_box.set_valign(Gtk.Align.CENTER)
        for chip_class in ["chip-primary", "chip-surface", "chip-tertiary", "chip-secondary"]:
            chip = Gtk.Box()
            chip.get_style_context().add_class("color-chip")
            chip.get_style_context().add_class(chip_class)
            palette_box.pack_start(chip, False, False, 0)
        self.info_box.pack_start(palette_box, False, False, 0)

        dock_vbox.pack_start(self.info_box, False, False, 0)

        # 4B. Parabolic Coverflow Cards Container
        self.cards_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.cards_hbox.set_halign(Gtk.Align.CENTER)
        self.cards_hbox.set_valign(Gtk.Align.CENTER)
        dock_vbox.pack_start(self.cards_hbox, False, False, 0)

        # 4C. Sleek Glass Action Bar (Bottom Controls)
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_bar.set_name("action-bar")
        action_bar.set_halign(Gtk.Align.CENTER)

        # Prev Button
        btn_prev = Gtk.Button(label="❮")
        btn_prev.set_relief(Gtk.ReliefStyle.NONE)
        btn_prev.get_style_context().add_class("dock-btn")
        btn_prev.connect("clicked", lambda *_: self.navigate(-1))
        action_bar.pack_start(btn_prev, False, False, 0)

        # Shuffle Button
        btn_shuffle = Gtk.Button(label="🎲 Shuffle")
        btn_shuffle.set_relief(Gtk.ReliefStyle.NONE)
        btn_shuffle.get_style_context().add_class("dock-btn")
        btn_shuffle.connect("clicked", lambda *_: self.shuffle_wallpaper())
        action_bar.pack_start(btn_shuffle, False, False, 0)

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        action_bar.pack_start(sep2, False, False, 4)

        # Status Spinner
        self.spinner = Gtk.Spinner()
        action_bar.pack_start(self.spinner, False, False, 0)

        # Apply Button
        self.btn_apply = Gtk.Button(label="Apply Wallpaper")
        self.btn_apply.set_relief(Gtk.ReliefStyle.NONE)
        self.btn_apply.get_style_context().add_class("dock-btn")
        self.btn_apply.get_style_context().add_class("suggested-action")
        self.btn_apply.connect("clicked", lambda *_: self.apply_current_wallpaper())
        action_bar.pack_start(self.btn_apply, False, False, 0)

        # Close / Cancel Button
        btn_close = Gtk.Button(label="Cancel")
        btn_close.set_relief(Gtk.ReliefStyle.NONE)
        btn_close.get_style_context().add_class("dock-btn")
        btn_close.connect("clicked", lambda *_: self.close_app())
        action_bar.pack_start(btn_close, False, False, 0)

        # Next Button
        btn_next = Gtk.Button(label="❯")
        btn_next.set_relief(Gtk.ReliefStyle.NONE)
        btn_next.get_style_context().add_class("dock-btn")
        btn_next.connect("clicked", lambda *_: self.navigate(1))
        action_bar.pack_start(btn_next, False, False, 0)

        dock_vbox.pack_start(action_bar, False, False, 0)

    # -------------------------------------------------------------------------
    # Thumbnail Loading & Caching
    # -------------------------------------------------------------------------
    def get_pixbuf(self, img_path, target_w, target_h):
        cache_key = (str(img_path), target_w, target_h)
        if cache_key in self.pixbuf_cache:
            return self.pixbuf_cache[cache_key]

        thumb_file = self.thumb_dir / f"{img_path.stem}_{img_path.stat().st_size}.png"
        try:
            if thumb_file.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(thumb_file), target_w, target_h, True
                )
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(img_path), target_w, target_h, True
                )
                # Cache thumbnail file for next time
                try:
                    pixbuf.savev(str(thumb_file), "png", [], [])
                except Exception:
                    pass

            self.pixbuf_cache[cache_key] = pixbuf
            return pixbuf
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Parabolic Coverflow Rendering
    # -------------------------------------------------------------------------
    def render_coverflow(self):
        # Clear existing cards
        for child in self.cards_hbox.get_children():
            self.cards_hbox.remove(child)

        if not self.wallpapers:
            self.lbl_title.set_text("No Wallpapers Found")
            self.lbl_meta.set_text("Place images in ~/Pictures/wallpapers")
            return

        total = len(self.wallpapers)
        curr = self.wallpapers[self.current_index]

        # Update metadata badge
        self.lbl_title.set_text(self.format_title(curr))
        self.lbl_meta.set_text(f"[{self.current_index + 1} of {total}]")

        # Parabolic scale geometry: 5 cards (Offsets: -2, -1, 0, 1, 2)
        # Center = 260x162, Near = 190x118, Far = 135x84
        configs = [
            (-2, 135, 84, "card-far"),
            (-1, 190, 118, "card-near"),
            (0, 260, 162, "card-center"),
            (1, 190, 118, "card-near"),
            (2, 135, 84, "card-far"),
        ]

        for offset, w, h, style_id in configs:
            idx = (self.current_index + offset) % total
            img_path = self.wallpapers[idx]

            card_ev = Gtk.EventBox()
            card_ev.set_valign(Gtk.Align.CENTER)
            card_ev.get_style_context().add_class("flow-card")
            card_ev.set_name(style_id)

            pixbuf = self.get_pixbuf(img_path, w, h)
            if pixbuf:
                image = Gtk.Image.new_from_pixbuf(pixbuf)
            else:
                image = Gtk.Image.new_from_icon_name("image-missing", Gtk.IconSize.DIALOG)

            card_ev.add(image)

            # Clicking a card: if center -> apply; if flanking -> rotate to it
            target_idx = idx
            if offset == 0:
                card_ev.connect(
                    "button-press-event",
                    lambda w, e: self.apply_current_wallpaper(),
                )
            else:
                card_ev.connect(
                    "button-press-event",
                    lambda w, e, o=offset: self.navigate(o),
                )

            self.cards_hbox.pack_start(card_ev, False, False, 0)

        self.cards_hbox.show_all()

    # -------------------------------------------------------------------------
    # Navigation & Interaction
    # -------------------------------------------------------------------------
    def navigate(self, direction):
        if not self.wallpapers:
            return
        self.current_index = (self.current_index + direction) % len(self.wallpapers)
        self.render_coverflow()

    def shuffle_wallpaper(self):
        if not self.wallpapers:
            return
        self.current_index = random.randint(0, len(self.wallpapers) - 1)
        self.render_coverflow()

    def on_dock_scroll(self, widget, event):
        # 60fps coalesced scrolling
        is_next = event.direction == Gdk.ScrollDirection.DOWN or (
            event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y > 0
        ) or event.direction == Gdk.ScrollDirection.RIGHT
        is_prev = event.direction == Gdk.ScrollDirection.UP or (
            event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y < 0
        ) or event.direction == Gdk.ScrollDirection.LEFT

        if is_next:
            self.scroll_delta += 1
        elif is_prev:
            self.scroll_delta -= 1

        if not self.scroll_timer_active:
            self.scroll_timer_active = True
            GLib.timeout_add(16, self._flush_scroll)

        return True

    def _flush_scroll(self):
        if self.scroll_delta != 0:
            step = 1 if self.scroll_delta > 0 else -1
            self.scroll_delta = 0
            self.navigate(step)
        self.scroll_timer_active = False
        return False

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close_app()
            return True
        elif event.keyval in (Gdk.KEY_Right, Gdk.KEY_Down, Gdk.KEY_l):
            self.navigate(1)
            return True
        elif event.keyval in (Gdk.KEY_Left, Gdk.KEY_Up, Gdk.KEY_h):
            self.navigate(-1)
            return True
        elif event.keyval == Gdk.KEY_space:
            self.shuffle_wallpaper()
            return True
        elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.apply_current_wallpaper()
            return True
        return False

    def on_backdrop_clicked(self, widget, event):
        # Click outside: destroy surface immediately
        self.close_app()
        return True

    def close_app(self):
        self.destroy()
        Gtk.main_quit()

    # -------------------------------------------------------------------------
    # Apply Wallpaper & Matugen
    # -------------------------------------------------------------------------
    def apply_current_wallpaper(self):
        if not self.wallpapers:
            return

        img = self.wallpapers[self.current_index]
        key = self.img_key(img)

        # Increment usage count
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        self.save_counts()

        # UI state
        self.btn_apply.set_sensitive(False)
        self.spinner.start()
        self.lbl_title.set_text(f"Applying: {self.format_title(img)}…")

        def job():
            try:
                # Ensure awww-daemon is running
                subprocess.run(
                    "pgrep -x awww-daemon >/dev/null || (awww-daemon & sleep 0.4)",
                    shell=True,
                    close_fds=True,
                )

                # Run matugen
                subprocess.run(
                    ["matugen", "image", "--source-color-index", "0", str(img)],
                    capture_output=True,
                    text=True,
                    check=True,
                    close_fds=True,
                )
                GLib.idle_add(self.close_app)
            except Exception as e:
                GLib.idle_add(self.on_apply_error, str(e))

        Thread(target=job, daemon=True).start()

    def on_apply_error(self, msg):
        self.spinner.stop()
        self.btn_apply.set_sensitive(True)
        self.lbl_title.set_text("Failed to apply theme")
        sys.stderr.write(f"Apply error: {msg}\n")


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    check_toggle()
    signal.signal(signal.SIGTERM, lambda *_: Gtk.main_quit())
    app = WallpaperSwitcher()
    app.show_all()
    Gtk.main()
