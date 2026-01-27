#!/usr/bin/env python3
import gi
import os
import subprocess
import json
import hashlib
from pathlib import Path
from threading import Thread

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk


class WallpaperSwitcher(Gtk.Window):
    def __init__(self):
        super().__init__(title="Theme Wallpaper Switcher")

        self.set_wmclass("hyprwallpaper", "HyprWallpaper")
        self.set_default_size(1000, 550)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.pictures_dir = Path.home() / "Pictures/wallpapers"
        if not self.pictures_dir.exists():
            self.show_error_dialog(f"Directory not found: {self.pictures_dir}")
            return

        # cache paths
        self.cache_root = Path.home() / ".cache/hyprwallpaper"
        self.thumb_dir = self.cache_root / "thumbnails"
        self.count_dir = self.cache_root / "counts"
        self.count_file = self.count_dir / "counts.json"

        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.count_dir.mkdir(parents=True, exist_ok=True)

        self.usage_counts = self.load_counts()
        self.image_widgets = []

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        self.add(main_box)

        # Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search wallpapers…")
        self.search_entry.connect("search-changed", self.on_search_changed)
        main_box.pack_start(self.search_entry, False, False, 0)

        # Scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        main_box.pack_start(scrolled, True, True, 0)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_max_children_per_line(10)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.connect("selected-children-changed", self.on_selection_changed)
        scrolled.add(self.flowbox)

        # Status
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        main_box.pack_start(self.status_label, False, False, 0)

        # Buttons
        btn_box = Gtk.Box(spacing=10)
        main_box.pack_start(btn_box, False, False, 0)

        self.apply_button = Gtk.Button(label="Apply Selected")
        self.apply_button.set_sensitive(False)
        self.apply_button.connect("clicked", self.on_apply_clicked)
        btn_box.pack_end(self.apply_button, False, False, 0)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda *_: self.destroy())
        btn_box.pack_end(close_btn, False, False, 0)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self.load_images()

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
        rel = str(img_path.relative_to(self.pictures_dir))
        return rel

    # ---------- IMAGE LOADING ----------

    def load_images(self):
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
        images = []

        for root, dirs, files in os.walk(self.pictures_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if Path(f).suffix.lower() in exts:
                    images.append(Path(root) / f)

        # sort by usage count desc, then name
        images.sort(
            key=lambda p: (-self.usage_counts.get(self.img_key(p), 0), str(p))
        )

        self.flowbox.foreach(lambda c: self.flowbox.remove(c))
        self.image_widgets.clear()

        for img in images:
            child = self.create_image_widget(img)
            self.image_widgets.append((img, child))
            self.flowbox.add(child)

        self.status_label.set_text(f"Loaded {len(images)} images")

    def create_image_widget(self, img_path):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        thumb = self.thumb_dir / (img_path.name + ".png")

        try:
            if thumb.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(thumb))
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    str(img_path), 200, 150
                )
                pixbuf.savev(str(thumb), "png", [], [])

            image = Gtk.Image.new_from_pixbuf(pixbuf)
        except Exception:
            image = Gtk.Image.new_from_icon_name(
                "image-missing", Gtk.IconSize.DIALOG
            )

        rel = img_path.relative_to(self.pictures_dir)
        count = self.usage_counts.get(self.img_key(img_path), 0)

        label = Gtk.Label(label=f"{rel}")
        label.set_ellipsize(1)
        label.set_max_width_chars(25)

        box.pack_start(image, False, False, 0)
        box.pack_start(label, False, False, 0)

        child = Gtk.FlowBoxChild()
        child.add(box)
        child.img_path = img_path
        child.search_text = str(rel).lower()

        return child

    # ---------- UI ACTIONS ----------

    def on_search_changed(self, entry):
        q = entry.get_text().lower()
        shown = 0

        for _, child in self.image_widgets:
            ok = q in child.search_text
            child.set_visible(ok)
            if ok:
                shown += 1

        self.status_label.set_text(f"Showing {shown} images")

    def on_selection_changed(self, box):
        self.apply_button.set_sensitive(bool(box.get_selected_children()))

    def on_apply_clicked(self, *_):
        sel = self.flowbox.get_selected_children()
        if not sel:
            return

        img = sel[0].img_path
        key = self.img_key(img)

        # increment count
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        self.save_counts()

        self.apply_button.set_sensitive(False)
        self.run_matugen(img)

    def run_matugen(self, img):
        def job():
            try:
                subprocess.run(
                    ["matugen", "image", str(img)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                GLib.idle_add(self.destroy)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, str(e))

        Thread(target=job, daemon=True).start()

    def show_error_dialog(self, msg):
        d = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Error",
        )
        d.format_secondary_text(msg)
        d.run()
        d.destroy()

    def on_key_press(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()


if __name__ == "__main__":
    app = WallpaperSwitcher()
    app.show_all()
    Gtk.main()
