# Installed Packages & Applications

This document maintains an inventory of all explicitly installed applications, tools, and background daemons on this system, explaining what each does and why it is installed.

---

## 1. Desktop Environment & Window Manager

| Package | Source | Description / Purpose |
| :--- | :--- | :--- |
| **`hyprland`** | Official (`pacman`) | Dynamic tiling Wayland compositor (the main desktop environment). |
| **`waybar`** | Official (`pacman`) | Highly customizable status bar for Wayland/Hyprland. |
| **`rofi-wayland`** | Official (`pacman`) | Application launcher and window switcher adapted for Wayland. |
| **`swaync`** | Official (`pacman`) | Notification daemon with a slide-out control center widget. |
| **`wlogout`** | AUR (`yay`) | Wayland-native power/logout menu (Lock, Logout, Suspend, Reboot, Shutdown). |
| **`swww` / `awww`** | Official / AUR | Animated Wayland wallpaper daemon. |
| **`grim`** | Official (`pacman`) | Wayland screenshot utility (captures raw pixels). |
| **`slurp`** | Official (`pacman`) | Region selection tool (used with `grim` or `hyprshot` for partial screenshots). |
| **`wl-clipboard`** | Official (`pacman`) | Command-line copy/paste tool for Wayland (`wl-copy`, `wl-paste`). |
| **`xdg-desktop-portal-hyprland`** | Official (`pacman`) | XDG desktop portal backend for screen sharing, file pickers, and permissions. |
| **`polkit-gnome`** | Official (`pacman`) | Graphical authentication agent for root/sudo permission prompts. |

---

## 2. Terminal, Shell & System Management

| Package | Source | Description / Purpose |
| :--- | :--- | :--- |
| **`kitty`** | Official (`pacman`) | GPU-accelerated terminal emulator. |
| **`fish`** | Official (`pacman`) | User-friendly interactive shell with autosuggestions and syntax highlighting. |
| **`stow`** | Official (`pacman`) | Symlink farm manager used to manage dotfiles in `~/.config`. |
| **`fastfetch`** | Official (`pacman`) | Fast, lightweight system information tool (neofetch alternative). |
| **`btop`** | Official (`pacman`) | Resource monitor showing CPU, memory, disks, network, and process usage. |
| **`limine-entry-tool`** | AUR (`yay`) | CLI tool and ALPM hooks to automate boot entry management and EFI deployment for the Limine bootloader. |

---

## 3. Audio, Bluetooth & Hardware Control

| Package | Source | Description / Purpose |
| :--- | :--- | :--- |
| **`pipewire`** | Official (`pacman`) | Low-latency multimedia server for Wayland. |
| **`pipewire-pulse`** | Official (`pacman`) | PulseAudio replacement server running on PipeWire. |
| **`wireplumber`** | Official (`pacman`) | Modular session and policy manager for PipeWire. |
| **`pavucontrol`** | Official (`pacman`) | PulseAudio/PipeWire volume control GUI. |
| **`bluez` / `bluez-utils`** | Official (`pacman`) | Linux Bluetooth protocol stack and command-line utilities (`bluetoothctl`). |
| **`networkmanager`** | Official (`pacman`) | Network management daemon (Wi-Fi, Ethernet, VPN). |
| **`network-manager-applet`** | Official (`pacman`) | System tray applet for NetworkManager (`nm-applet`). |
| **`brightnessctl`** | Official (`pacman`) | Device backlight and brightness controller. |
| **`playerctl`** | Official (`pacman`) | Command-line media player controller (play/pause/next for Spotify, browsers, VLC). |
| **`quick-slider.py`** | Local Script (`waybar/scripts`) | Unified GTK Layer Shell modal slider daemon for Volume & Brightness. |
| **`volume-toggle.sh`** | Local Script (`waybar/scripts`) | Ultra-fast (0ms) IPC toggle launcher for volume mode (SIGUSR1). |
| **`brightness-toggle.sh`** | Local Script (`waybar/scripts`) | Ultra-fast (0ms) IPC toggle launcher for brightness mode (SIGUSR2). |
| **`quick-connectivity.py`** | Local Script (`waybar/scripts`) | Unified GTK Layer Shell modal quick-settings popup for Network & Bluetooth (AAA UX). |
| **`connectivity-toggle.sh`** | Local Script (`waybar/scripts`) | Ultra-fast (0ms) toggle launcher for quick-connectivity.py. |

---

## 4. Fonts & Theming

| Package | Source | Description / Purpose |
| :--- | :--- | :--- |
| **`ttf-jetbrains-mono-nerd`** | Official (`pacman`) | Primary monospace coding font with icons/glyphs for terminals and Waybar. |
| **`ttf-font-awesome`** | Official (`pacman`) | Iconic font and CSS framework used by status bar icons. |
| **`matugen`** | AUR (`yay`) | Material You dynamic color palette generator based on the active wallpaper. |

---

## 5. GUI Applications

| Package | Source | Description / Purpose |
| :--- | :--- | :--- |
| **`vlc`** | Official (`pacman`) | Media player supporting virtually all video and audio formats. |
| **`dolphin`** | Official (`pacman`) | KDE file manager. |

---

## 6. Activity & Usage Tracking (For Monthly App Audit)

| Package | Source | Description / Purpose |
| :--- | :--- | :--- |
| **`activitywatch-bin`** | AUR (`yay`) | Core ActivityWatch service: runs local `aw-server` and hosts web dashboard (`http://localhost:5600`). |
| **`aw-awatcher`** | AUR (`yay`) | Native Wayland/Hyprland compiled Rust watcher. Replaces the X11-only default watchers to record active windows and idle time on Hyprland. |

---

## 7. Custom Dotfiles Utilities & Audit Scripts

| Utility | Location | Description / Purpose |
| :--- | :--- | :--- |
| **`unused-apps.py`** | [`scripts/unused-apps.py`](file:///home/asim/setup/Dotfiles/scripts/unused-apps.py) | Audit script that queries ActivityWatch data for the past N days and cross-references against installed `.desktop` applications to identify apps with 0 usage. |
