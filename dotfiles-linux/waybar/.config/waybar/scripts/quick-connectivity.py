#!/usr/bin/env python3
"""
Waybar Quick Connectivity Modal (Stateless, AAA UX)
A unified GTK Layer Shell modal for Network and Bluetooth controls.
- Uses SwayNC's fullscreen click-catcher technique: clicking outside instantly exits and frees the surface.
- No PID files, no background signals, zero ghost windows.
- Non-blocking toggles for Wi-Fi and Bluetooth.
- Escape key and backdrop click dismiss.
- Matugen dynamic theming.
"""

import os
import sys
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib, Pango


# ---------------------------------------------------------
# Network & Bluetooth State Helpers
# ---------------------------------------------------------
def get_network_info():
    info = {
        "type": "disconnected",
        "name": "Disconnected",
        "ip": "",
        "signal": 0,
        "wifi_enabled": False,
    }
    try:
        res = (
            subprocess.check_output(
                ["nmcli", "radio", "wifi"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        info["wifi_enabled"] = res == "enabled"
    except Exception:
        pass

    try:
        out = (
            subprocess.check_output(
                ["nmcli", "-t", "-f", "TYPE,NAME,DEVICE,STATE", "con", "show", "--active"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
            .splitlines()
        )
        for line in out:
            parts = line.split(":")
            if len(parts) >= 4 and parts[3] == "activated":
                con_type, name, dev = parts[0], parts[1], parts[2]
                if "wireless" in con_type or "802-11-wireless" in con_type:
                    info["type"] = "wifi"
                    info["name"] = name
                    try:
                        sig_out = (
                            subprocess.check_output(
                                ["nmcli", "-t", "-f", "IN-USE,SIGNAL", "dev", "wifi"],
                                stderr=subprocess.DEVNULL,
                            )
                            .decode()
                            .strip()
                            .splitlines()
                        )
                        for s_line in sig_out:
                            if s_line.startswith("*"):
                                info["signal"] = int(s_line.split(":")[-1])
                                break
                    except Exception:
                        pass
                elif "ethernet" in con_type or "802-3-ethernet" in con_type:
                    info["type"] = "ethernet"
                    info["name"] = name or "Wired Connection"

                try:
                    ip_out = (
                        subprocess.check_output(
                            ["nmcli", "-g", "IP4.ADDRESS", "device", "show", dev],
                            stderr=subprocess.DEVNULL,
                        )
                        .decode()
                        .strip()
                    )
                    info["ip"] = ip_out.split("/")[0] if ip_out else ""
                except Exception:
                    pass
                break
    except Exception:
        pass
    return info


def scan_wifi_networks(rescan=False):
    cmd = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "dev", "wifi", "list"]
    if rescan:
        cmd.extend(["--rescan", "yes"])
    try:
        out = (
            subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
            .splitlines()
        )
        networks = {}
        for line in out:
            parts = line.split(":")
            if len(parts) >= 4:
                in_use = parts[0].strip() == "*"
                ssid = parts[1].strip()
                if not ssid:
                    continue
                try:
                    signal = int(parts[2].strip())
                except ValueError:
                    signal = 0
                security = parts[3].strip()
                is_secured = bool(security and security != "--")

                # Deduplicate by SSID, preferring in-use or highest signal
                if ssid not in networks or in_use or signal > networks[ssid]["signal"]:
                    networks[ssid] = {
                        "in_use": in_use,
                        "ssid": ssid,
                        "signal": signal,
                        "security": security,
                        "is_secured": is_secured,
                    }
        # Sort: in-use first, then by signal descending
        return sorted(
            networks.values(),
            key=lambda x: (1 if x["in_use"] else 0, x["signal"]),
            reverse=True,
        )
    except Exception:
        return []


def get_wifi_signal_icon(signal):
    if signal >= 75:
        return "󰤨"
    elif signal >= 50:
        return "󰤥"
    elif signal >= 25:
        return "󰤢"
    else:
        return "󰤟"


def get_bluetooth_info():
    info = {
        "powered": False,
        "device": "No device connected",
        "battery": "",
    }
    try:
        show_out = (
            subprocess.check_output(["bluetoothctl", "show"], stderr=subprocess.DEVNULL)
            .decode()
        )
        info["powered"] = "Powered: yes" in show_out

        info_out = (
            subprocess.check_output(["bluetoothctl", "info"], stderr=subprocess.DEVNULL)
            .decode()
        )
        for line in info_out.splitlines():
            line = line.strip()
            if line.startswith("Name:"):
                info["device"] = line.replace("Name:", "").strip()
            elif line.startswith("Alias:"):
                info["device"] = line.replace("Alias:", "").strip()
            elif "Battery Percentage:" in line:
                info["battery"] = line.split(":")[-1].strip()
    except Exception:
        pass
    return info


# ---------------------------------------------------------
# Modal Window
# ---------------------------------------------------------
class QuickConnectivity(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.set_title("WaybarQuickConnectivity")
        self.set_name("waybar-quick-connectivity")

        # Layer Shell: Fullscreen transparent click-catcher (SwayNC pattern)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "waybar-quick-connectivity")

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

        # Positioning Wrapper: Aligns card under connectivity pill
        wrapper = Gtk.Box()
        wrapper.set_halign(Gtk.Align.END)
        wrapper.set_valign(Gtk.Align.START)
        wrapper.set_margin_top(44)
        wrapper.set_margin_end(230)
        self.backdrop.add(wrapper)

        # Card EventBox: Stops click propagation to backdrop
        self.card_event_box = Gtk.EventBox()
        self.card_event_box.set_name("card-event-box")
        self.card_event_box.connect("button-press-event", lambda w, e: True)
        wrapper.add(self.card_event_box)

        # Main Card Box (do not name self.container to avoid Gtk.Container struct collision)
        self.card_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12
        )
        self.card_box.set_name("modal-container")
        self.card_event_box.add(self.card_box)

        # State tracking
        self._is_scanning = False

        # Build UI Sections
        self._updating_ui = True
        self.build_header()
        self.build_network_section()
        self.build_bluetooth_section()
        self.refresh_data()
        self._updating_ui = False

        self.connect("key-press-event", self.on_key_press)

    def on_backdrop_clicked(self, widget, event):
        Gtk.main_quit()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    def build_header(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_name("header-box")

        title_lbl = Gtk.Label(label="󰤨  Connectivity")
        title_lbl.set_name("header-title")
        title_lbl.set_xalign(0.0)
        header_box.pack_start(title_lbl, True, True, 0)

        close_btn = Gtk.Button()
        close_btn.set_name("close-btn")
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_lbl = Gtk.Label(label="󰅖")
        close_lbl.set_name("close-icon")
        close_btn.add(close_lbl)
        close_btn.connect("clicked", lambda b: Gtk.main_quit())
        header_box.pack_end(close_btn, False, False, 0)

        self.card_box.pack_start(header_box, False, False, 0)

    def build_network_section(self):
        net_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        net_card.set_name("section-card")

        # Top row: icon, name & ip, toggle switch
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.net_icon = Gtk.Label()
        self.net_icon.set_name("section-icon")
        top_row.pack_start(self.net_icon, False, False, 0)

        net_text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.net_title = Gtk.Label()
        self.net_title.set_name("section-title")
        self.net_title.set_xalign(0.0)
        self.net_title.set_ellipsize(Pango.EllipsizeMode.END)
        self.net_title.set_max_width_chars(20)
        net_text_box.pack_start(self.net_title, False, False, 0)

        self.net_sub = Gtk.Label()
        self.net_sub.set_name("section-subtitle")
        self.net_sub.set_xalign(0.0)
        self.net_sub.set_ellipsize(Pango.EllipsizeMode.END)
        self.net_sub.set_max_width_chars(25)
        net_text_box.pack_start(self.net_sub, False, False, 0)

        top_row.pack_start(net_text_box, True, True, 0)
        net_card.pack_start(top_row, False, False, 0)

        # Available Networks Section
        self.wifi_networks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.wifi_networks_box.set_name("wifi-networks-box")

        wifi_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        wifi_header.set_name("wifi-header-box")

        wifi_hdr_icon = Gtk.Label(label="󰤨")
        wifi_hdr_icon.set_name("wifi-header-icon")
        wifi_header.pack_start(wifi_hdr_icon, False, False, 0)

        wifi_hdr_lbl = Gtk.Label(label="Wi-Fi")
        wifi_hdr_lbl.set_name("wifi-header-title")
        wifi_hdr_lbl.set_xalign(0.0)
        wifi_header.pack_start(wifi_hdr_lbl, True, True, 0)

        self.scan_btn = Gtk.Button()
        self.scan_btn.set_name("scan-btn")
        self.scan_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.scan_btn.set_tooltip_text("Scan for Wi-Fi networks")
        self.scan_icon = Gtk.Label(label="󰑐")
        self.scan_icon.set_name("scan-icon")
        self.scan_btn.add(self.scan_icon)
        self.scan_btn.connect("clicked", lambda b: self.start_wifi_scan(rescan=True))
        wifi_header.pack_end(self.scan_btn, False, False, 0)

        self.wifi_switch = Gtk.Switch()
        self.wifi_switch.set_name("toggle-switch")
        self.wifi_switch.set_valign(Gtk.Align.CENTER)
        self.wifi_switch.connect("state-set", self.on_wifi_toggled)
        wifi_header.pack_end(self.wifi_switch, False, False, 0)

        self.wifi_networks_box.pack_start(wifi_header, False, False, 0)

        self.wifi_off_lbl = Gtk.Label(label="Wi-Fi is turned off")
        self.wifi_off_lbl.set_name("wifi-status-lbl")
        self.wifi_off_lbl.set_xalign(0.0)
        self.wifi_networks_box.pack_start(self.wifi_off_lbl, False, False, 0)

        # Scrolled list of networks
        self.scrolled_nets = Gtk.ScrolledWindow()
        self.scrolled_nets.set_name("wifi-scrolled-window")
        self.scrolled_nets.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_nets.set_min_content_height(70)
        self.scrolled_nets.set_max_content_height(150)
        self.scrolled_nets.set_propagate_natural_height(True)

        self.wifi_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.wifi_list_box.set_name("wifi-list-box")
        self.scrolled_nets.add(self.wifi_list_box)

        self.wifi_networks_box.pack_start(self.scrolled_nets, False, False, 0)
        net_card.pack_start(self.wifi_networks_box, False, False, 0)

        # Action row: settings button
        net_btn = Gtk.Button(label="󰖩  Network Settings")
        net_btn.set_name("action-btn")
        net_btn.connect("clicked", self.on_open_network_settings)
        net_card.pack_start(net_btn, False, False, 0)

        self.card_box.pack_start(net_card, False, False, 0)

    def build_bluetooth_section(self):
        bt_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        bt_card.set_name("section-card")

        # Top row: icon, name & status, toggle switch
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.bt_icon = Gtk.Label()
        self.bt_icon.set_name("section-icon")
        top_row.pack_start(self.bt_icon, False, False, 0)

        bt_text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.bt_title = Gtk.Label(label="Bluetooth")
        self.bt_title.set_name("section-title")
        self.bt_title.set_xalign(0.0)
        self.bt_title.set_ellipsize(Pango.EllipsizeMode.END)
        self.bt_title.set_max_width_chars(20)
        bt_text_box.pack_start(self.bt_title, False, False, 0)

        self.bt_sub = Gtk.Label()
        self.bt_sub.set_name("section-subtitle")
        self.bt_sub.set_xalign(0.0)
        self.bt_sub.set_ellipsize(Pango.EllipsizeMode.END)
        self.bt_sub.set_max_width_chars(25)
        bt_text_box.pack_start(self.bt_sub, False, False, 0)

        top_row.pack_start(bt_text_box, True, True, 0)

        self.bt_switch = Gtk.Switch()
        self.bt_switch.set_name("toggle-switch")
        self.bt_switch.set_valign(Gtk.Align.CENTER)
        self.bt_switch.connect("state-set", self.on_bluetooth_toggled)
        top_row.pack_end(self.bt_switch, False, False, 0)

        bt_card.pack_start(top_row, False, False, 0)

        # Action row: blueman button
        bt_btn = Gtk.Button(label="󰂱  Bluetooth Devices")
        bt_btn.set_name("action-btn")
        bt_btn.connect("clicked", self.on_open_bluetooth_settings)
        bt_card.pack_start(bt_btn, False, False, 0)

        self.card_box.pack_start(bt_card, False, False, 0)

    # ---------------------------------------------------------
    # Data Refresh & Handlers
    # ---------------------------------------------------------
    def refresh_data(self):
        net = get_network_info()
        bt = get_bluetooth_info()

        # Update Network UI
        if net["type"] == "wifi":
            self.net_icon.set_text("󰛳")
            self.net_title.set_text(net["name"])
            details = []
            if net["signal"] > 0:
                details.append(f"Signal: {net['signal']}%")
            if net["ip"]:
                details.append(f"IP: {net['ip']}")
            self.net_sub.set_text(" • ".join(details) if details else "Connected")
        elif net["type"] == "ethernet":
            self.net_icon.set_text("󰈀")
            self.net_title.set_text(net["name"])
            self.net_sub.set_text(f"IP: {net['ip']}" if net["ip"] else "Connected (Wired)")
        else:
            self.net_icon.set_text("󰅛")
            self.net_title.set_text("Not Connected")
            self.net_sub.set_text("Wi-Fi is on" if net["wifi_enabled"] else "Wi-Fi is disabled")

        self.wifi_switch.set_active(net["wifi_enabled"])

        # Update Wi-Fi networks box visibility & initial scan
        if net["wifi_enabled"]:
            self.scrolled_nets.set_visible(True)
            self.scan_btn.set_visible(True)
            self.wifi_off_lbl.set_visible(False)
            if not self.wifi_list_box.get_children() and not self._is_scanning:
                self.start_wifi_scan(rescan=False)
        else:
            self.scrolled_nets.set_visible(False)
            self.scan_btn.set_visible(False)
            self.wifi_off_lbl.set_visible(True)

        # Update Bluetooth UI
        if bt["powered"]:
            if bt["device"] != "No device connected":
                self.bt_icon.set_text("󰂱")
                self.bt_title.set_text(bt["device"])
                sub = "Connected"
                if bt["battery"]:
                    sub += f" • Battery: {bt['battery']}"
                self.bt_sub.set_text(sub)
            else:
                self.bt_icon.set_text("󰂯")
                self.bt_title.set_text("Bluetooth")
                self.bt_sub.set_text("Powered on • No device")
        else:
            self.bt_icon.set_text("󰂲")
            self.bt_title.set_text("Bluetooth")
            self.bt_sub.set_text("Disabled")

        self.bt_switch.set_active(bt["powered"])

    def on_wifi_toggled(self, switch, state):
        if self._updating_ui:
            return

        def _toggle():
            cmd = "on" if state else "off"
            subprocess.run(
                ["nmcli", "radio", "wifi", cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            GLib.idle_add(self._delayed_refresh)

        import threading

        threading.Thread(target=_toggle, daemon=True).start()

    def on_bluetooth_toggled(self, switch, state):
        if self._updating_ui:
            return

        def _toggle():
            import time

            if state:
                subprocess.run(
                    ["rfkill", "unblock", "bluetooth"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(0.3)
                subprocess.run(
                    ["bluetoothctl", "power", "on"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.run(
                    ["bluetoothctl", "power", "off"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    ["rfkill", "block", "bluetooth"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            GLib.idle_add(self._delayed_refresh)

        import threading

        threading.Thread(target=_toggle, daemon=True).start()

    def _delayed_refresh(self):
        self._updating_ui = True
        self.refresh_data()
        self._updating_ui = False
        return False

    def on_open_network_settings(self, btn):
        subprocess.Popen(
            ["nm-connection-editor"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        Gtk.main_quit()

    def on_open_bluetooth_settings(self, btn):
        subprocess.Popen(
            ["blueman-manager"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        Gtk.main_quit()

    # ---------------------------------------------------------
    # Wi-Fi Scanning & Connection
    # ---------------------------------------------------------
    def start_wifi_scan(self, rescan=False):
        if self._is_scanning:
            return
        self._is_scanning = True
        self.scan_btn.set_sensitive(False)
        self.scan_icon.set_text("󰑮")

        def _scan():
            nets = scan_wifi_networks(rescan=rescan)
            GLib.idle_add(self._populate_wifi_list, nets)

        import threading

        threading.Thread(target=_scan, daemon=True).start()

    def _populate_wifi_list(self, networks):
        for child in self.wifi_list_box.get_children():
            self.wifi_list_box.remove(child)

        if not networks:
            no_nets = Gtk.Label(label="No networks found")
            no_nets.set_name("wifi-status-lbl")
            self.wifi_list_box.pack_start(no_nets, False, False, 4)
        else:
            for net in networks:
                row_btn = Gtk.Button()
                row_btn.set_name("wifi-row-btn")
                row_btn.set_relief(Gtk.ReliefStyle.NONE)
                if net["in_use"]:
                    row_btn.get_style_context().add_class("active")

                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

                sig_lbl = Gtk.Label(label=get_wifi_signal_icon(net["signal"]))
                sig_lbl.set_name("wifi-row-signal")
                row_box.pack_start(sig_lbl, False, False, 0)

                ssid_lbl = Gtk.Label(label=net["ssid"])
                ssid_lbl.set_name("wifi-row-ssid")
                ssid_lbl.set_xalign(0.0)
                ssid_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                ssid_lbl.set_max_width_chars(18)
                row_box.pack_start(ssid_lbl, True, True, 0)

                if net["is_secured"]:
                    lock_lbl = Gtk.Label(label="󰌾")
                    lock_lbl.set_name("wifi-row-lock")
                    row_box.pack_start(lock_lbl, False, False, 0)

                if net["in_use"]:
                    check_lbl = Gtk.Label(label="󰄬")
                    check_lbl.set_name("wifi-row-check")
                    row_box.pack_end(check_lbl, False, False, 0)

                row_btn.add(row_box)
                ssid = net["ssid"]
                is_secured = net["is_secured"]
                in_use = net["in_use"]
                row_btn.connect(
                    "clicked",
                    lambda b, s=ssid, sec=is_secured, u=in_use: self.on_wifi_row_clicked(
                        s, sec, u
                    ),
                )
                self.wifi_list_box.pack_start(row_btn, False, False, 0)

        self.wifi_list_box.show_all()
        self.scan_icon.set_text("󰑐")
        self.scan_btn.set_sensitive(True)
        self._is_scanning = False
        return False

    def on_wifi_row_clicked(self, ssid, is_secured, in_use):
        if in_use:
            return

        def _connect():
            res = subprocess.run(
                ["nmcli", "dev", "wifi", "connect", ssid],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0 and "Secrets were required" in res.stderr:
                # Open network manager to prompt for password
                subprocess.Popen(
                    ["nm-connection-editor"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                GLib.idle_add(Gtk.main_quit)
            else:
                GLib.idle_add(self._delayed_refresh)

        import threading

        threading.Thread(target=_connect, daemon=True).start()


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
        font-size: 12px;
        font-weight: 400;
    }}

    window#waybar-quick-connectivity,
    #modal-backdrop {{
        background-color: transparent;
        background: transparent;
    }}

    #card-event-box {{
        background: transparent;
    }}

    #modal-container {{
        background: alpha(@background, 0.94);
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.5);
        border-radius: 20px;
        padding: 16px 20px;
        min-width: 310px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.55);
    }}

    #header-box {{
        margin-bottom: 4px;
    }}

    #header-title {{
        color: @primary;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.2px;
    }}

    #close-btn {{
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0 4px;
        border-radius: 50px;
        transition: background-color 0.2s ease;
    }}

    #close-btn:hover {{
        background: alpha(@on_surface, 0.1);
    }}

    #close-icon {{
        color: @on_surface_variant;
        font-size: 15px;
    }}

    #close-btn:hover #close-icon {{
        color: @error;
    }}

    #section-card {{
        background: alpha(@on_surface, 0.05);
        border: 1px solid alpha(@outline_variant, 0.3);
        border-radius: 14px;
        padding: 12px 14px;
    }}

    #section-icon {{
        color: @primary;
        font-size: 22px;
        min-width: 28px;
    }}

    #section-title {{
        color: @on_surface;
        font-size: 13px;
        font-weight: 600;
    }}

    #section-subtitle {{
        color: @on_surface_variant;
        font-size: 11px;
        font-weight: 400;
    }}

    #toggle-switch {{
        margin-left: 8px;
    }}

    #toggle-switch:checked {{
        background-color: @primary;
    }}

    #action-btn {{
        background: alpha(@on_surface, 0.07);
        color: @on_surface;
        border: 1px solid alpha(@outline_variant, 0.25);
        border-radius: 10px;
        padding: 7px 12px;
        margin-top: 4px;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.1px;
        transition: all 0.2s ease;
    }}

    #action-btn:hover {{
        background: alpha(@primary, 0.18);
        color: @primary;
        border-color: @primary;
    }}

    #wifi-networks-box {{
        margin-top: 4px;
        background: alpha(@on_surface, 0.03);
        border: 1px solid alpha(@outline_variant, 0.2);
        border-radius: 12px;
        padding: 8px 10px;
    }}

    #wifi-header-box {{
        margin-bottom: 4px;
    }}

    #wifi-header-icon {{
        color: @primary;
        font-size: 15px;
        min-width: 18px;
    }}

    #wifi-header-title {{
        color: @on_surface;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.1px;
    }}

    #scan-btn {{
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 2px 6px;
        border-radius: 50px;
        transition: background-color 0.2s ease;
    }}

    #scan-btn:hover {{
        background: alpha(@on_surface, 0.1);
    }}

    #scan-icon {{
        color: @primary;
        font-size: 14px;
    }}

    #wifi-scrolled-window {{
        background: transparent;
    }}

    #wifi-row-btn {{
        background: transparent;
        border: none;
        box-shadow: none;
        border-radius: 8px;
        padding: 5px 8px;
        transition: background-color 0.15s ease;
    }}

    #wifi-row-btn:hover {{
        background: alpha(@on_surface, 0.08);
    }}

    #wifi-row-btn.active {{
        background: alpha(@primary, 0.15);
    }}

    #wifi-row-signal {{
        color: @primary;
        font-size: 15px;
        min-width: 20px;
    }}

    #wifi-row-ssid {{
        color: @on_surface;
        font-size: 12px;
        font-weight: 500;
    }}

    #wifi-row-lock {{
        color: @on_surface_variant;
        font-size: 12px;
    }}

    #wifi-row-check {{
        color: @primary;
        font-size: 14px;
        font-weight: bold;
    }}

    #wifi-status-lbl {{
        color: @on_surface_variant;
        font-size: 11px;
        font-style: italic;
        padding: 8px;
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
    win = QuickConnectivity()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
