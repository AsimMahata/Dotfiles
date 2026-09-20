
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
Install `hyprconf2lua` and typing stubs inside a local virtual environment (ignored in `.gitignore`):

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install hyprconf2lua PyGObject-stubs
# Symlink system PyGObject and cairo into venv site-packages for IDE language servers (Pyrefly / Pyright)
ln -sf /usr/lib/python3.14/site-packages/gi .venv/lib/python3.14/site-packages/
ln -sf /usr/lib/python3.14/site-packages/cairo .venv/lib/python3.14/site-packages/
```
*(Note: `--system-site-packages`, `PyGObject-stubs`, and symlinking `gi`/`cairo` (along with `pyproject.toml`'s `tool.pyrefly.search_path`) allow IDE language servers to resolve `gi.repository` and Arch system packages like `python-gobject`)*


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
2. Updated `dotfiles-linux/matugen/.config/matugen/config.toml` to point `[templates.hyprland]` directly to `hyprland-colors.lua` (outputting `~/.config/hypr/colors.lua`), and removed the legacy `hyprland-colors.conf` template.
3. In `hyprland.lua`, imported colors via `local colors = require("colors")` and mapped window border colors to `colors.secondary` and `colors.outline_variant`.
4. Removed `hyprland.conf` so Hyprland runs purely on `hyprland.lua`.
5. Fixed `kb_variant = ",pes_keypad"` string type in `hyprland.lua`.
6. Reloaded with `hyprctl reload full-reset` to switch compositor runtime to the Lua config manager.


---

## 7. Wlogout Styling & Blur Fix

- **Style & Appearance:**
  - Updated `dotfiles-linux/wlogout/.config/wlogout/style.css` with a translucent frosted background (`rgba(16, 20, 24, 0.55)`).
  - Removed default GTK button borders (`border: none;`) and introduced subtle floating cards (`rgba(255, 255, 255, 0.05)`) with smooth Matugen accent glows (`@primary`) on hover.
  - Centered icons cleanly above button text to eliminate visual overlap.
- **Hyprland Blur Rules:**
  - Added `blur = true` layer rules for `wlogout` and `logout_dialog` in `hyprland.lua` and `hyprland.conf`.
- **CSS Diagnostic Fix:**
  - Added `.vscode/settings.json` with `"css.validate": false` to prevent false-positive web CSS linter errors on GTK CSS variables (`@color`).

- **Git Tracking:**
  - Removed dynamically generated Matugen color files (`colors.*`, `colors.theme`) from git cache and updated `.gitignore` with `**/.config/**/colors.*` so wallpaper theme updates do not pollute git status.

---

## 8. Wallpaper Switcher UI Fix

- Updated `dotfiles-linux/hypr/.config/hypr/scripts/wallpaper-switcher.py`:
  - Styled regular buttons (Cancel) with a dark theme background (`#313244`), clear text (`#cdd6f4`), rounded borders (`10px`), and hover effects (`#45475a`) to prevent GTK light theme fallback.
  - Aligned the "Apply Selected" button styling with consistent borders, hover effects, and transitions.

---

## 9. Known Issues

- **Waybar Workspace Switching in Hyprland Lua:**
  - Described in [`issue.md`](file:///home/asim/setup/Dotfiles/issue.md).
  - Clicking workspace buttons in `waybar 0.15.0` fails due to Hyprland's Lua IPC dispatch syntax change. Fixable via `waybar-git` or by reverting to `hyprland.conf`.
- **Built-in Keyboard Double-Typing / Key Chatter [NOT FIXED]:**
  - Described in [`issue.md`](file:///home/asim/setup/Dotfiles/issue.md).
  - Single taps intermittently register twice (`a a`, double backspace) due to mechanical switch contact bounce and absence of a Linux software debounce filter. Fixable via compressed air or `keyd` debounce.

---

## 10. Antigravity IDE Dropped Keystrokes Fix (Fcitx5 IME Incompatibility)

- **The Issue:**
  - Keystrokes were intermittently dropping or failing to register when typing in Antigravity IDE (VS Code / Electron), despite normal behavior in other applications.
- **Root Cause:**
  - `fcitx5` (Flexible Contextual Input Tool for X 5) was running in the background via autostart.
  - **What Fcitx5 is:** An Input Method Editor (IME) daemon designed for typing complex, non-Latin scripts (such as Chinese, Japanese, Korean, Vietnamese) where multiple keystrokes compose a single character.
  - **The Incompatibility:** On Wayland, Chromium/Electron applications route all keyboard input through Wayland's `text-input-v3` protocol when an IME daemon is detected. Due to an upstream Chromium race condition between `keydown` events and IME commit callbacks, keystrokes are frequently swallowed or dropped during normal/fast typing.
- **The Fix:**
  - Terminated the running daemon: `pkill fcitx5`.
  - Removed/disabled `fcitx5` from Hyprland autostart in `hyprland.lua` since standard US/Latin keyboard layouts do not require an IME.
  - Removed malformed `kb_variant = ",pes_keypad"` duplicate input block from `hyprland.lua`, which caused XKB layout group desyncs and missing symbols (such as colon `:`).

---

## 11. ActivityWatch Setup (App Usage Tracking for Hyprland/Wayland)

- **Installation:**
  ```bash
  yay -S activitywatch-bin aw-awatcher
  ```
  *(Note: `activitywatch-bin` provides the core server and web UI, while `aw-awatcher` provides the native Wayland/Hyprland window and AFK watcher that replaces the X11-only default watchers).*
- **How to Launch:**
  - Start the server and Hyprland watcher:
    ```bash
    aw-server &
    aw-awatcher &
    ```
  - Open the web dashboard:
    Navigate to [http://localhost:5600](http://localhost:5600) in any browser (or run `xdg-open http://localhost:5600`).
- **Autostart in Hyprland:**
  Configured in `hyprland.lua`:
  ```lua
  hl.exec_cmd("aw-server & disown")
  hl.exec_cmd("aw-awatcher & disown")
  ```
- **Unused Apps Audit Script:**
  - Script located at [`scripts/unused-apps.py`](file:///home/asim/setup/Dotfiles/scripts/unused-apps.py).
  - Usage:
    ```bash
    # Check past 30 days (default)
    python3 scripts/unused-apps.py

    # Check past N days
    python3 scripts/unused-apps.py -d 14
    ```
  - Cross-references ActivityWatch recorded events against all installed desktop applications (`.desktop` files) and outputs a list of used apps with total active time and a list of apps never opened (0 hours).

---

## 12. Limine Bootloader & Entry Management (`limine-entry-tool`)

- **Installation:**
  ```bash
  yay -S limine-entry-tool
  ```
  *(Note: `limine-entry-tool` automates boot entry generation, kernel tracking, and EFI deployment for the Limine bootloader via ALPM libalpm hooks and CLI utilities).*
- **Key CLI Utilities:**
  - `limine-entry-tool`: Generates or updates Limine boot entries according to `/etc/limine-entry-tool.conf`.
  - `limine-list`: Lists active bootloader entries.
  - `limine-enroll-config` / `limine-reset-enroll`: Enrolls or resets Limine configurations.
  - `limine-install` / `limine-remove-entry` / `limine-scan`: Helper tools for inspecting and manipulating boot entries.
- **Verification / Usage:**
  - View current boot entries:
    ```bash
    limine-list
    ```
  - Generate/update entries:
    ```bash
    sudo limine-entry-tool
    ```

---

## Notes

* Keep GNOME installed until Hyprland is confirmed to be stable.
* Record configuration changes and fixes in this document as setup continues.


