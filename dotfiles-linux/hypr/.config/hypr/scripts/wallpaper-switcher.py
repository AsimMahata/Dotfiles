#!/usr/bin/env python3
import gi
import os
import sys
import subprocess
import json
from pathlib import Path
from threading import Thread

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk


CSS = """
window {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

flowboxchild {
    padding: 8px;
    margin: 4px;
    border-radius: 12px;
    border: 2px solid transparent;
    transition: all 150ms ease-in-out;
}

flowboxchild:hover {
    background-color: rgba(205, 214, 244, 0.1);
}

flowboxchild:selected {
    background-color: rgba(137, 180, 250, 0.2);
    border: 2px solid #89b4fa;
}

searchentry {
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 14px;
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
}

button {
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 600;
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 150ms ease-in-out;
}

button:hover {
    background-color: #45475a;
    color: #ffffff;
    border-color: rgba(255, 255, 255, 0.16);
}

button.suggested-action {
    background-color: #89b4fa;
    color: #11111b;
    border: 1px solid #89b4fa;
}

button.suggested-action:hover {
    background-color: #b4befe;
    border-color: #b4befe;
}

button.suggested-action:disabled {
    background-color: rgba(205, 214, 244, 0.08);
    color: rgba(205, 214, 244, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.04);
}
"""


class WallpaperSwitcher(Gtk.Window):
    def __init__(self):
        super().__init__(title="Theme Wallpaper Switcher")

        self.set_wmclass("hyprwallpaper", "HyprWallpaper")
        self.set_default_size(980, 580)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(12)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        # Apply CSS styling
        self.apply_css()

        self.pictures_dir = Path.home() / "Pictures/wallpapers"
        if not self.pictures_dir.exists():
            self.show_error_dialog(f"Directory not found: {self.pictures_dir}")
            return

        # Cache directories
        self.cache_root = Path.home() / ".cache/hyprwallpaper"
        self.thumb_dir = self.cache_root / "thumbnails"
        self.count_dir = self.cache_root / "counts"
        self.count_file = self.count_dir / "counts.json"

        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.count_dir.mkdir(parents=True, exist_ok=True)

        self.usage_counts = self.load_counts()
        self.image_widgets = []
        self.selected_img = None

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Search Bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search wallpapers…")
        self.search_entry.connect("search-changed", self.on_search_changed)
        main_box.pack_start(self.search_entry, False, False, 0)

        # Wallpaper Grid View
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scrolled, True, True, 0)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(8)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.connect("selected-children-changed", self.on_selection_changed)
        # Note: Do NOT connect child-activated so clicking never automatically applies
        scrolled.add(self.flowbox)

        # Bottom Bar: Status, Spinner & Buttons
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(bottom_box, False, False, 4)

        self.spinner = Gtk.Spinner()
        bottom_box.pack_start(self.spinner, False, False, 0)

        self.status_label = Gtk.Label(label="Select a wallpaper and click 'Apply Selected'")
        self.status_label.set_halign(Gtk.Align.START)
        bottom_box.pack_start(self.status_label, False, False, 0)

        # Action Buttons
        btn_box = Gtk.Box(spacing=10)
        bottom_box.pack_end(btn_box, False, False, 0)

        close_btn = Gtk.Button(label="Cancel")
        close_btn.connect("clicked", lambda *_: self.close_app())
        btn_box.pack_start(close_btn, False, False, 0)

        self.apply_button = Gtk.Button(label="Apply Selected")
        self.apply_button.get_style_context().add_class("suggested-action")
        self.apply_button.set_sensitive(False)
        self.apply_button.connect("clicked", self.on_apply_clicked)
        btn_box.pack_start(self.apply_button, False, False, 0)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", lambda *_: Gtk.main_quit())

        self.load_images()

    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS.encode())
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ---------- COUNTS ----------

    def load_counts(self):
        if self.count_file.exists():
            try:
                with open(self.count_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_counts(self):
        with open(self.count_file, "w") as f:
            json.dump(self.usage_counts, f, indent=2)

    def img_key(self, img_path):
        try:
            return str(img_path.relative_to(self.pictures_dir))
        except ValueError:
            return str(img_path.name)

    # ---------- IMAGE LOADING ----------

    def load_images(self):
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
        images = []

        for root, dirs, files in os.walk(self.pictures_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() in exts:
                    images.append(p)

        # Sort by usage count descending, then filename
        images.sort(
            key=lambda p: (-self.usage_counts.get(self.img_key(p), 0), str(p.name).lower())
        )

        self.flowbox.foreach(lambda c: self.flowbox.remove(c))
        self.image_widgets.clear()

        for img in images:
            child = self.create_image_widget(img)
            self.image_widgets.append((img, child))
            self.flowbox.add(child)

        self.status_label.set_text(f"Loaded {len(images)} wallpapers. Select one and click 'Apply Selected'.")
        self.flowbox.show_all()

    def create_image_widget(self, img_path):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        thumb = self.thumb_dir / f"{img_path.stem}_{img_path.stat().st_size}.png"

        try:
            if thumb.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(thumb))
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(img_path), 200, 130, True
                )
                pixbuf.savev(str(thumb), "png", [], [])

            image = Gtk.Image.new_from_pixbuf(pixbuf)
        except Exception:
            image = Gtk.Image.new_from_icon_name(
                "image-missing", Gtk.IconSize.DIALOG
            )

        rel = self.img_key(img_path)

        label = Gtk.Label(label=f"{img_path.name}")
        label.set_ellipsize(3) # END
        label.set_max_width_chars(22)

        box.pack_start(image, False, False, 0)
        box.pack_start(label, False, False, 0)

        child = Gtk.FlowBoxChild()
        child.add(box)
        child.img_path = img_path
        child.search_text = str(rel).lower()

        return child

    # ---------- UI ACTIONS ----------

    def on_search_changed(self, entry):
        q = entry.get_text().lower().strip()
        shown = 0

        for _, child in self.image_widgets:
            ok = not q or q in child.search_text
            child.set_visible(ok)
            if ok:
                shown += 1

        self.status_label.set_text(f"Showing {shown} wallpapers")

    def on_selection_changed(self, box):
        selected = box.get_selected_children()
        if selected and hasattr(selected[0], "img_path"):
            self.selected_img = selected[0].img_path
            self.apply_button.set_sensitive(True)
            self.status_label.set_text(f"Selected: {self.selected_img.name} — Click 'Apply Selected' to set")
        else:
            self.selected_img = None
            self.apply_button.set_sensitive(False)
            self.status_label.set_text("Select a wallpaper and click 'Apply Selected'")

    def on_apply_clicked(self, *_):
        # ONLY apply when the user explicitly clicks this button
        if not self.selected_img:
            sel = self.flowbox.get_selected_children()
            if sel and hasattr(sel[0], "img_path"):
                self.selected_img = sel[0].img_path

        if self.selected_img:
            self.apply_image(self.selected_img)

    def apply_image(self, img):
        key = self.img_key(img)

        # increment usage count
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        self.save_counts()

        # Update UI to applying state
        self.apply_button.set_sensitive(False)
        self.search_entry.set_sensitive(False)
        self.flowbox.set_sensitive(False)
        self.spinner.start()
        self.status_label.set_text(f"Applying theme & wallpaper for {img.name}…")

        self.run_matugen(img)

    def run_matugen(self, img):
        def job():
            try:
                # Ensure awww-daemon is running before setting wallpaper
                subprocess.run(
                    "pgrep -x awww-daemon >/dev/null || (awww-daemon & sleep 0.4)",
                    shell=True,
                    close_fds=True,
                )

                subprocess.run(
                    ["matugen", "image", "--source-color-index", "0", str(img)],
                    capture_output=True,
                    text=True,
                    check=True,
                    close_fds=True,
                )
                GLib.idle_add(self.close_app)
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() or e.stdout.strip() or str(e)
                GLib.idle_add(self.on_apply_error, err_msg)
            except Exception as e:
                GLib.idle_add(self.on_apply_error, str(e))

        Thread(target=job, daemon=True).start()

    def on_apply_error(self, msg):
        self.spinner.stop()
        self.apply_button.set_sensitive(True)
        self.search_entry.set_sensitive(True)
        self.flowbox.set_sensitive(True)
        self.status_label.set_text("Failed to apply wallpaper theme.")
        self.show_error_dialog(msg)

    def show_error_dialog(self, msg):
        d = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Theme Switch Error",
        )
        d.format_secondary_text(msg)
        d.run()
        d.destroy()

    def close_app(self):
        self.destroy()
        Gtk.main_quit()

    def on_key_press(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close_app()
            return True
        return False


if __name__ == "__main__":
    app = WallpaperSwitcher()
    app.show_all()
    Gtk.main()
