---
name: linux-ricing
description: Comprehensive Linux ricing workflow and maintenance guide for Arch Linux, Hyprland, Waybar, Rofi, SwayNC, Wlogout, Matugen, Waypaper, and GNU Stow. Use when customizing desktop appearance, theming, status bars, launchers, fonts, or managing dotfiles.
---

# Linux Ricing & Dotfiles Maintenance Guide

This skill provides expert guidance on ricing and maintaining a cohesive modern Wayland desktop environment on Arch Linux using Hyprland and associated tools.

---

## 1. System Architecture & Stack

Your desktop environment is composed of modular Wayland utilities managed via GNU Stow:

Component | Tool | Config Location | Role
:--- | :--- | :--- | :---
**Compositor** | Hyprland | `~/.config/hypr/` | Window manager, animations, keybinds, monitors
**Status Bar** | Waybar | `~/.config/waybar/` | System stats, workspaces, tray, notifications, audio
**App Launcher** | Rofi (rofi-wayland) | `~/.config/rofi/` | Application runner and custom menus
**Notification Center** | SwayNC | `~/.config/swaync/` | Notification daemon, control center, DND toggle
**Power Menu** | Wlogout | `~/.config/wlogout/` | Lock, suspend, logout, reboot, shutdown screen
**Terminal** | Kitty | `~/.config/kitty/` | GPU-accelerated terminal emulator
**Wallpaper Engine** | swww / Waypaper | `~/.config/waypaper/` | Dynamic wallpaper switcher with transition effects
**Color Generation** | Matugen | `~/.config/matugen/` | Material You color palette extraction from wallpaper
**Dotfile Manager** | GNU Stow | `~/setup/Dotfiles/` | Symlink manager for modular dotfiles

---

## 2. Dotfiles Management with GNU Stow

All configuration files should follow the Stow directory structure in `dotfiles-linux/`:

```text
Dotfiles/
└── dotfiles-linux/
    ├── hypr/
    │   └── .config/hypr/
    ├── waybar/
    │   └── .config/waybar/
    ├── rofi/
    │   └── .config/rofi/
    ├── swaync/
    │   └── .config/swaync/
    ├── wlogout/
    │   └── .config/wlogout/
    └── kitty/
        └── .config/kitty/
```

### Deployment Commands:
From the root of `Dotfiles/`:
```bash
# Stow a single module (e.g., waybar)
stow -d dotfiles-linux -t ~ waybar

# Restow / update symlinks
stow -R -d dotfiles-linux -t ~ waybar

# Unstow
stow -D -d dotfiles-linux -t ~ waybar
```

---

## 3. Theming & Color Synchronization Workflow

To achieve a unified visual style:

1. **Wallpaper & Colors**: Matugen extracts colors from the active wallpaper and generates color files (e.g. `colors.css`, `colors.conf`).
2. **Waybar Theming**: Uses `@import 'colors.css';` in `style.css` for consistent dynamic color tokens (`@background`, `@on_surface`, `@primary`, `@secondary`).
3. **Hyprland Theming**: Uses `source = ~/.config/hypr/colors.conf` for window border colors (`$secondary`, `$outline_variant`).
4. **Typography**: Ensure `ttf-jetbrains-mono-nerd` is installed and set as the primary font family in `style.css` and `kitty.conf`.

---

## 4. Live Reload & Testing Runbook

When editing configurations, test changes immediately without restarting the session:

* **Hyprland**:
  ```bash
  hyprctl reload
  ```
* **Waybar**:
  ```bash
  killall waybar && waybar &
  ```
* **SwayNC**:
  ```bash
  swaync-client -R && swaync-client -rs
  ```
* **Rofi**:
  ```bash
  rofi -show drun
  ```
* **Wlogout**:
  ```bash
  wlogout
  ```

---

## 5. Ricing Guidelines & Best Practices

* **Always preserve modularity**: Keep color definitions separated into `colors.css` / `colors.conf` so theme switchers can update them automatically.
* **Preserve existing keybinds**: When modifying Hyprland or Waybar configs, check `keymap.md` and existing config bindings first to avoid collisions.
* **Layer Rules for Wayland**: Apply blur and transparency to Waybar, SwayNC, and Rofi via Hyprland layer rules:
  ```ini
  layerrule = blur, waybar
  layerrule = ignorezero, waybar
  layerrule = blur, swaync-control-center
  layerrule = blur, rofi
  ```
