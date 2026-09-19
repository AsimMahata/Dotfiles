
# Arch Linux Post-Installation Setup

This document records the post-installation setup performed after installing Arch Linux.

## 1. Terminal — Kitty

Install Kitty:

```bash
sudo pacman -S kitty
```

Launch:

```bash
kitty
```

---

## 2. Media Player — VLC

Install VLC:

```bash
sudo pacman -S vlc
```

Launch:

```bash
vlc
```

---

## 3. Hyprland & Waybar Desktop Environment

Install Hyprland, Waybar, notification daemon, launcher, and Wayland utilities:

```bash
sudo pacman -S hyprland kitty waybar rofi-wayland \
    swaync swww grim slurp wl-clipboard \
    polkit-gnome xdg-desktop-portal-hyprland
```

Install Audio, Network, Bluetooth, and Required Fonts:

```bash
sudo pacman -S brightnessctl playerctl \
    networkmanager network-manager-applet \
    bluez bluez-utils \
    pipewire pipewire-pulse wireplumber pavucontrol \
    ttf-jetbrains-mono-nerd ttf-font-awesome
```

Install AUR dependencies (such as wlogout for Waybar power menu):

```bash
yay -S wlogout
```

Enable required services:

```bash
sudo systemctl enable --now bluetooth.service
sudo systemctl enable --now NetworkManager.service
```

Do not remove GNOME until Hyprland has been verified to work correctly.

---

## 4. Fish Shell

Install Fish:

```bash
sudo pacman -S fish
```

Start Fish:

```bash
fish
```

Make Fish the default shell:

```bash
chsh -s /usr/bin/fish
```

Verify:

```bash
echo $SHELL
```

Expected:

```text
/usr/bin/fish
```

Log out and back in after changing the default shell.

---

## 5. GNU Stow

Install Stow:

```bash
sudo pacman -S stow
```

Dotfiles should follow the Stow structure:

```text
dotfiles-linux/
└── nvim/
    └── .config/
        └── nvim/
            ├── init.lua
            └── ...
```

From the dotfiles root:

```bash
stow nvim
```

This creates a symlink such as:

```text
~/.config/nvim
    -> ~/src/D/dotfiles-linux/nvim/.config/nvim
```

---

## 6. Hyprland Lua Migration (`hyprconf2lua`)

Hyprland 0.57 removes support for `.conf` files in favor of `.lua` format. Migration steps and tooling:

### Backup
Configs are backed up before migration:

```bash
mkdir -p setup/backup/hypr
cp -r dotfiles-linux/hypr/.config/hypr/* setup/backup/hypr/
```

### Virtual Environment & Tool Installation
Install `hyprconf2lua` inside a local virtual environment (ignored in `.gitignore`):

```bash
python3 -m venv .venv
.venv/bin/pip install hyprconf2lua
```

### Configuration Conversion
Convert `.conf` files to `.lua`:

```bash
# Convert hyprland.conf
.venv/bin/hyprconf2lua dotfiles-linux/hypr/.config/hypr/hyprland.conf -o dotfiles-linux/hypr/.config/hypr/hyprland.lua --report

# Convert colors.conf
.venv/bin/hyprconf2lua dotfiles-linux/hypr/.config/hypr/colors.conf -o dotfiles-linux/hypr/.config/hypr/colors.lua --report
```

Symlink updated configs via Stow:

```bash
stow -R -d dotfiles-linux -t ~ hypr
```

### Matugen Dynamic Theming for Hyprland Lua
To ensure dynamic wallpaper theming via Matugen generates Lua colors:
1. Created template `dotfiles-linux/matugen/.config/matugen/templates/hyprland-colors.lua` to export color variables as a Lua table (and populate `_G`).
2. Updated `dotfiles-linux/matugen/.config/matugen/config.toml` to add `[templates.hyprland_lua]` generating `~/.config/hypr/colors.lua`.
3. In `hyprland.lua`, imported colors via `local colors = require("colors")` and mapped window border colors to `colors.secondary` and `colors.outline_variant`.


---

## Notes

* Keep GNOME installed until Hyprland is confirmed to be stable.
* Record configuration changes and fixes in this document as setup continues.

