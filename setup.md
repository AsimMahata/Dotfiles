
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

## 3. Hyprland

Install Hyprland and basic Wayland utilities:

```bash
sudo pacman -S hyprland kitty waybar rofi-wayland \
    dunst swww grim slurp wl-clipboard \
    polkit-gnome xdg-desktop-portal-hyprland
```

Additional utilities:

```bash
sudo pacman -S brightnessctl playerctl \
    network-manager-applet pavucontrol \
    thunar
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

## Notes

* Keep GNOME installed until Hyprland is confirmed to be stable.
* Record configuration changes and fixes in this document as setup continues.
