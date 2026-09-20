
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
7. Added `fullscreen-no-rounding` window rule in `hyprland.lua` (`rounding = 0`, `border_size = 0`) for edge-to-edge fullscreen windows.


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
  - Explicitly configured `kb_layout = "us"` with empty `kb_variant`, `kb_model`, `kb_options`, and `kb_rules` in `hyprland.lua` to enforce a single US keyboard layout without secondary variants.

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

## 13. Video Playback Quality & Scaling Optimization (Hyprland)

- **The Issue:**
  - On high-DPI displays (such as 2880×1800 @ 2× scale), video playback and text/subtitles appeared pixelated and suffered from edge aliasing/jaggies in Hyprland compared to GNOME.
- **Root Causes:**
  1. Missing VA-API driver and Wayland platform environment variables, causing video players (Firefox/Zen, Chromium, VLC) to fall back to software (CPU) decoding.
  2. Direct scanout disabled by default, routing fullscreen video through Hyprland's GLES2 compositor shaders instead of direct GPU hardware scanout.
  3. Default XWayland nearest-neighbor upscaling (`xwayland:use_nearest_neighbor = true`), stretching 1440×900 surfaces to 2880×1800 with jagged pixels.
  4. Window rounding (`rounding = 10`) clipping video subsurfaces and fullscreen windows with shader aliasing.
- **Configuration Adjustments (`hyprland.lua`):**
  - Added hardware acceleration and Wayland environment variables:
    ```lua
    hl.env("LIBVA_DRIVER_NAME", "iHD")
    hl.env("VDPAU_DRIVER", "va_gl")
    hl.env("MOZ_ENABLE_WAYLAND", "1")
    hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
    hl.env("GDK_BACKEND", "wayland,x11,*")
    hl.env("QT_QPA_PLATFORM", "wayland;xcb")
    ```
  - Enabled direct scanout for fullscreen surfaces:
    ```lua
    hl.config({
        render = {
            direct_scanout = 1,
        },
    })
    ```
  - Enabled crisp XWayland HiDPI scaling:
    ```lua
    hl.config({
        xwayland = {
            force_zero_scaling = true,
            use_nearest_neighbor = false,
        },
    })
    ```
  - Disabled rounding and borders on fullscreen windows:
    ```lua
    hl.window_rule({
        name  = "fullscreen-no-rounding",
        match = {
            fullscreen = 1,
        },
        rounding = 0,
        border = false,
    })
    ```

---

## 14. Waybar Quick Sliders (Volume & Brightness Modals — AAA UX)

- **Feature:**
  - Implemented unified, interactive modal sliders for Volume and Brightness triggered by clicking the Waybar `pulseaudio` and `battery` modules.
  - Inspired by SwayNC's `layer-shell-cover-screen` architecture: uses an invisible, transparent fullscreen click-catcher so clicking anywhere outside the popup dismisses it immediately.
  - Seamless mode switching: clicking Volume while Brightness is open (or vice versa) switches instantly in 0ms without backdrop collision or process deadlocks.
  - Supports live volume (`wpctl`) and brightness (`brightnessctl`) sliding at 60fps non-blocking, mouse scroll adjustments, Escape key dismiss, and toggle on repeated clicks.
- **Scripts & Architecture Guide:**
  - [`quick-slider.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/sliders/quick-slider.py): Unified GTK3 + `GtkLayerShell` application managing both volume and brightness modes with dynamic Matugen theming.
  - [`volume-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/sliders/volume-toggle.sh): Stateless bash toggle launcher.
  - [`brightness-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/sliders/brightness-toggle.sh): Stateless bash toggle launcher.
  - [`gtk.md`](file:///home/asim/setup/Dotfiles/gtk.md): Comprehensive architectural guide and pitfalls/best practices reference for building Wayland GTK Layer Shell modals.
- **Changes in [`dotfiles-linux/waybar/.config/waybar/config.jsonc`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/config.jsonc):**
  - Set `pulseaudio` `"on-click": "~/.config/waybar/scripts/sliders/volume-toggle.sh"`.
  - Set `battery` `"on-click": "~/.config/waybar/scripts/sliders/brightness-toggle.sh"`.
  - Retained `"on-click-right": "pavucontrol"` on `pulseaudio` for full audio mixer access.

---

## 15. Waybar Unified Connectivity & Quick Modal (Network & Bluetooth — AAA UX)

- **Feature:**
  - Combined the previously separated `network` and `bluetooth` Waybar modules into a single unified pill (`group/connectivity`).
  - Implemented an interactive, Matugen-themed GTK Layer Shell quick-settings modal for Network and Bluetooth controls.
  - Follows SwayNC's `layer-shell-cover-screen` fullscreen click-catcher pattern: clicking outside or pressing <kbd>Esc</kbd> cleanly destroys the surface with zero ghost windows.
  - Includes real-time status display (Wi-Fi SSID, Ethernet Wired status, IP address, Bluetooth device & battery %), non-blocking toggle switches for Wi-Fi and Bluetooth radios, and quick-launch buttons for full system settings (`nm-connection-editor` and `blueman-manager`).
  - Integrated an interactive Wi-Fi network scanner with a scrollable list of nearby networks, signal strength indicators, security lock badges, and click-to-connect support.
- **Scripts:**
  - [`quick-connectivity.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/connectivity/quick-connectivity.py): GTK3 + `GtkLayerShell` quick-settings modal application with dynamic Matugen theming, Wi-Fi scanner, and Bluetooth manager.
  - [`connectivity-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/connectivity/connectivity-toggle.sh): Stateless bash toggle launcher with 0ms toggle response.
- **Waybar Changes:**
  - In [`config.jsonc`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/config.jsonc): replaced `"network", "bluetooth"` in `modules-right` with `"group/connectivity"`, fixed `format-ethernet` wired icon/text, configured `format-linked` with Proton VPN shield icon (`󰖂 Proton`) in brand purple (`#6d4aff`) for `ipv6leakintrf0`, and routed clicks to `~/.config/waybar/scripts/connectivity/connectivity-toggle.sh`.
  - In [`style.css`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/style.css): styled `#connectivity` as the pill surface with transparent inner modules, divider, `#connectivity #network.linked` brand purple state (`#6d4aff`), and proper color palette.

---

## 16. Waybar Power Profiles & GNOME-Style On-Screen Display (OSD)

- **Feature:**
  - Integrated custom Waybar module `custom/power-profile` inside `group/power` with profile-specific styling and icons.
  - Waybar's native `power-profiles-daemon` module hardcodes click events and ignores `"on-click"`, so `custom/power-profile` is used with `power-profile-status.sh` (JSON return-type, signal 8) and `power-profile-cycle.sh` on click.
  - Implemented a lightweight, GNOME-style glassmorphic On-Screen Display (OSD HUD) that overlays briefly on the top of the display when cycling power profiles (without sending notification spam to SwayNC).
  - Mode-specific colors and hardware effect summaries:
    - **Performance (``):** Coral/Red highlight — `Fans: High / Overboost 󰈐 • Max CPU Clock • Higher Heat`
    - **Balanced (``):** Blue highlight — `Fans: Dynamic / Standard 󰌪 • Balanced Performance & Battery`
    - **Quiet (``):** Emerald/Green highlight — `Fans: Silent / Low 󰌪 • Power Throttled • Lowest Heat`
- **Scripts:**
  - [`power-profile-status.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/power/power-profile-status.sh): Outputs JSON status (`text`, `alt`, `tooltip`, `class`) for Waybar.
  - [`power-profile-cycle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/power/power-profile-cycle.sh): Cycles `powerprofilesctl` modes, sends `SIGRTMIN+8` to Waybar for an instant 0ms update, and triggers the OSD HUD.
  - [`power-profile-osd.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/power/power-profile-osd.py): GTK Layer Shell overlay widget with `Gtk.Stack` slide-left transition (current profile slides left, new profile slides in from right) and 1.6s auto-dismiss.

## 17. Waybar Unified Hardware Resources & Quick Modal (CPU & RAM — AAA UX)

- **Feature:**
  - Combined the previously separated `cpu` and `memory` pills into a single, unified `group/hardware` capsule matching the design of `group/connectivity` and `group/power`.
  - **Dynamic Mini-Gauges:** Integrated JetBrains Mono Nerd Font circular progress rings (`format-icons`: `["󰝦", "󰪞", "󰪟", "󰪠", "󰪡", "󰪢", "󰪣", "󰪤", "󰪥"]`) that visually fill up as CPU and RAM utilization increases.
  - **Clean Hover Tooltips:** Standardized GTK3 tooltips with crisp padding, clean lines, and zero rendering artifacts.
  - **Interactive Actions & Modal:**
    - **Left-Click (CPU or RAM):** Toggles display format (RAM switches between `4.8G/15.2G` and `31%`; CPU switches between usage and clock frequency).
    - **Right-Click (CPU or RAM):** Opens the stateless GTK3 Layer Shell modal ([`quick-hardware.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/quick-hardware.py)) with live CPU/RAM progress bars, load averages, swap details, top processes, and an action button to launch `btop`.
  - **Dynamic Tiered Icon Coloring (Option B):**
    - The circular gauge icons (`{icon}`) dynamically change color according to percentage utilization:
      - **0% – 39% (Low):** Cyan / Teal (`#80d5d0`)
      - **40% – 69% (Medium):** Mint / Soft Green (`#b0ccc9`)
      - **70% – 84% (High):** Warm Amber (`#f9e2af`)
      - **85% – 100% (Critical):** Coral Red (`#ffb4ab`)
    - Numbers and metric text remain crisp white (`@on_surface`) for maximum contrast and readability.
    - Inside the modal, the CPU and RAM progress bars dynamically mirror these active load tier colors.
- **Scripts:**
  - [`quick-hardware.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/hardware/quick-hardware.py): Stateless GTK3 + `GtkLayerShell` modal with live CPU/RAM monitoring, top processes, and a BTOP launcher button.
  - [`hardware-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/hardware/hardware-toggle.sh): Stateless bash toggle launcher.
- **Files Modified:**
  - [`dotfiles-linux/waybar/.config/waybar/config.jsonc`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/config.jsonc): Replaced `"cpu", "memory"` with `"group/hardware"`, routed clicks to `~/.config/waybar/scripts/hardware/hardware-toggle.sh`, and cleaned up tooltip formatting.
  - [`dotfiles-linux/waybar/.config/waybar/style.css`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/style.css): Styled `#hardware`, `#hardware #cpu`, `#hardware #memory` with divider, hover color transitions, clean tooltip rules, and an exact 5px gap (`margin-left: 5px;`) separating `#hardware` from the center `#workspaces` pill.
## 18. Hardware Acceleration & Thermal Throttling Diagnosis

- **Issue:**
  - Experienced desktop UI lag, stuttering, and micro-freezes on Hyprland, raising concerns that hardware acceleration might not be working.
- **Investigation & Findings:**
  - **Hardware Acceleration Confirmed Active:**
    - Compositor (Hyprland 0.56) is actively rendering via Mesa Intel Iris Xe Graphics (ADL GT2) on `/dev/dri/renderD128` (DRM backend, OpenGL 3.2, high-priority EGL context).
    - Monitor running at native `2880x1800@90Hz` (scale 2) with hardware cursors enabled.
    - Native Wayland GPU processes confirmed running for Brave and Antigravity IDE (Electron).
  - **Root Cause of Lag (Severe Thermal Throttling):**
    - High CPU temperatures (84°C+ under moderate load) on the Intel Core i5-12500H.
    - Recorded over **609,000 thermal throttling events** in `/sys/devices/system/cpu/cpu0/thermal_throttle/package_throttle_count` totaling nearly 50 minutes of cumulative throttling.
    - System was actively hitting hardware thermal limits, repeatedly forcing CPU cores down to **400 MHz** (the lowest emergency frequency), causing severe frame drops, input latency, and UI stutter.
  - **Contributing Causes:**
    - `power-profiles-daemon` was locked in `performance` mode, pumping maximum wattage into the CPU inside a thin ASUS chassis.
    - `thermald` (Intel Thermal Daemon) was not installed, so the system lacked DPTF proactive thermal management and had to rely on emergency hardware PROCHOT (400 MHz drops).
- **Remediation & Installation:**
  - Switch power profile to `balanced` to avoid excessive heat spikes and sustain smooth clock frequencies:
    ```bash
    powerprofilesctl set balanced
    ```
  - Install and enable `thermald` (Intel Thermal Daemon) to regulate thermal curves via DPTF and prevent abrupt 400 MHz emergency throttling:
    ```bash
    sudo pacman -S thermald
    sudo systemctl enable --now thermald
    ```
  - Verify service status:
    ```bash
    systemctl status thermald
    ```

## 19. Waybar Dual-Profile Architecture & Toggleable Music Bar (CAVA, MPRIS & Animated Cat)

- **Overview:**
  - Implemented a dual-profile Waybar architecture supporting instant switching between the standard productivity bar and a dedicated music/visualizer bar with persistent state across restarts, reboots, and Hyprland reloads.
- **Profiles Architecture:**
  - `~/.config/waybar/profiles/default/config.jsonc`: Full productivity bar (workspaces, hardware stats, connectivity, volume, battery, notifications, clock).
  - `~/.config/waybar/profiles/music/config.jsonc`: Focused music/visualizer bar featuring:
    - **Left:** App launcher (`custom/app`) and player status (`mpris` with playback icons, song title, and artist).
    - **Center (Dual Companion Pills):**
      - `custom/island`: Multi-animal dynamic companion & vitals engine (`ᓚᘏᗢ`, `🐰`, `🦆`, `👻`, `🦀`, `🐶`) with dancing music animations, marquee title bounce, petting, vitals, and heat alerts.
      - `custom/cava`: Super-wide 42-bar Monstercat wave visualizer streaming real-time audio frequencies with organic wave physics and 8-level Unicode bar heights (` ▂▃▄▅▆▇█`).
    - **Right:** Volume (`pulseaudio`), power profile/battery (`group/power`), clock, and power menu (`custom/power`).
  - `~/.config/waybar/config.jsonc`: A relative symlink pointing to the active profile (`profiles/default/config.jsonc` or `profiles/music/config.jsonc`).
  - **Git Tracking Note:** To prevent Git from flagging `config.jsonc` as modified when toggling profiles, run `git update-index --skip-worktree dotfiles-linux/waybar/.config/waybar/config.jsonc`.
- **Scripts & Helpers:**
  - [`toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/toggle.sh): Stateless bash launcher that checks the active symlink target, atomically updates the symlink with `ln -sfn`, terminates old Waybar/CAVA/cat instances (`killall -9 waybar cava; pkill -f cat.py`), launches Waybar, and sends desktop notification via `notify-send`.
  - [`cat.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/profiles/music/cat.py): Animated walking cat widget streaming JSON status and tooltips to Waybar.
  - [`cava.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/profiles/music/cava.sh): Streams 42-bar frequency data from `cava.conf` formatted via `sed` to Unicode bar characters.
  - [`cava.conf`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/profiles/music/cava.conf): Dedicated 60fps raw ASCII CAVA configuration with Monstercat smoothing and wave physics configured for PipeWire/PulseAudio.
- **Hyprland Shortcut:**
  - Bound `SUPER + SHIFT + M` in [`hyprland.lua`](file:///home/asim/setup/Dotfiles/dotfiles-linux/hypr/.config/hypr/hyprland.lua) to execute `~/.config/waybar/scripts/toggle.sh`.

---

## 20. Waybar Dynamic Island & Scripts Folder Reorganization (Feature-Domain / Module-Wise Architecture)

- **Feature & Architecture:**
  - **Reorganized `~/.config/waybar/scripts/` into Feature-Domain (Module-Wise) Subdirectories:**
    - `scripts/sliders/`: All slider modal & launcher files ([`quick-slider.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/sliders/quick-slider.py), [`volume-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/sliders/volume-toggle.sh), [`brightness-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/sliders/brightness-toggle.sh)).
    - `scripts/connectivity/`: All network & bluetooth modal & launcher files ([`quick-connectivity.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/connectivity/quick-connectivity.py), [`connectivity-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/connectivity/connectivity-toggle.sh)).
    - `scripts/hardware/`: All CPU & RAM monitor modal & launcher files ([`quick-hardware.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/hardware/quick-hardware.py), [`hardware-toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/hardware/hardware-toggle.sh)).
    - `scripts/power/`: All power profile OSD, cycle, and status feed files ([`power-profile-osd.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/power/power-profile-osd.py), [`power-profile-cycle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/power/power-profile-cycle.sh), [`power-profile-status.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/power/power-profile-status.sh)).
    - `scripts/island/`: Dynamic Island & Desktop Companion engine ([`dynamic-island.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/island/dynamic-island.py)).
    - `scripts/`: Clean root containing only bar lifecycle scripts ([`launch.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/launch.sh), [`toggle.sh`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/toggle.sh)).
  - **Cyber Dynamic Island Widget (`custom/island`):**
    - Placed in the free portion of the default bar (`modules-left`, right after `hyprland/window`).
    - **Multi-Animal Companions:** Features animated Cat (`ᓚᘏᗢ`), Bunny (`(\_/)`), Duck (`( •ө•)`), Ghost (`👻`), Crab (`🦀`), and Doggo (`(U・x・U)`).
    - **Dynamic State Morphing:**
      - **Pet Mode:** Lively animated companion (paces/dances when music plays; stretches, grooms, or sleeps when idle).
      - **Vitals Mode:** Auto-morphs to display live CPU temperature (`🌡️ 52°C`) and load (`󰻠 18%`).
      - **Music Peek Mode:** Shows currently playing song title and artist marquee (`󰎆 Song - Artist`).
      - **Heat/Overload Alert:** Instantly triggers an alert state (`(；•̀д•́) 82°C 🔥`) with coral red styling if CPU temp > 80°C or CPU > 85%.
    - **Instant Interactive Controls:**
      - **Left-Click:** Pet the companion (`pkill -SIGUSR1 -f dynamic-island.py`) — triggers a happy purr animation with floating hearts (`❤️`) and increments affection counter.
      - **Right-Click:** Switch companion animal (`pkill -SIGUSR2 -f dynamic-island.py`).
      - **Middle-Click:** Force cycle view mode (`pkill -SIGRTMIN+1 -f dynamic-island.py`).
    - **Styling:** Matugen-themed pill in `style.css` with `@on_primary_fixed` background, glowing `@primary` borders, and responsive `.playing`, `.idle`, `.petted`, `.vitals`, `.music`, and `.alert` state classes.

---

## 21. Waybar Theming Harmonization (Language, Window & Workspaces)

- **Problem:**
  - `hyprland/language` (`us`): Used `background: @secondary_fixed` (`#e0e1f9`) and dark navy text, rendering as an inverted white pill that clashed with the dark theme.
  - `hyprland/window` (`Dotfiles - Antigravity IDE`): Used `background: @inverse_on_surface` (`#303036`, flat dark grey) with narrow `10px` padding, lacking the midnight-blue tint and sizing of adjacent pills.
  - `hyprland/workspaces`: Container was flat `@background` (`#131318`), inactive buttons were dull grey circles (`alpha(@on_surface, 0.1)`), and the active workspace was a flat 50% grey pill (`alpha(@on_surface, 0.5)`), missing the palette's accent colors and glow.
- **Solution:**
  - In [`dotfiles-linux/waybar/.config/waybar/style.css`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/style.css):
    - **Language (`#language`):** Updated to `background: @on_primary_fixed; color: @primary;` to match the bar's deep midnight-blue aesthetic.
    - **Active Window (`#window`):** Updated to `background: @on_primary_fixed; padding-left: 15px; padding-right: 15px; border: 1px solid alpha(@outline_variant, 0.4);` for unified pill sizing and subtle borders. Added `"max-length": 25` in `config.jsonc` to avoid layout jitter from long titles.
    - **Workspaces (`#workspaces` & buttons):** Styled container with `background: @on_primary_fixed; border-radius: 50px; padding: 0 6px;`. Inactive buttons use `alpha(@primary, 0.2)` with `alpha(@primary, 0.45)` on hover. Active workspace styled with `@primary` accent background, `@on_primary` text, and a glowing `box-shadow: 0 0 10px alpha(@primary, 0.4)`.
    - **Dynamic Island Size Stabilization, Marquee, Sleep Mechanic & Redesign:** Set `min-width: 145px;` in `style.css` (avoiding GTK3 `max-width` which causes crashes) and implemented a smooth left-to-right bounce marquee ticker in [`dynamic-island.py`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/island/dynamic-island.py) for music titles and long text.
    - **Full Kaomoji Font Coverage & Original Aesthetic:** Installed `NotoSansYi-Regular.ttf` and `otf-ipafont` (IPAMincho/IPAGothic) to `~/.local/share/fonts/` to provide native font coverage for Yi syllables (`꒰ ꒱` U+A4B0/A4B1) and Japanese/CJK characters (`ノ`, `・`, `彡`, `～`). Restored the complete expressive original designs across all companions (`꒰👻꒱`, `(•‿•)ノ`, `(՞•ﻌ•՞)`, etc.) with zero tofu / hex boxes.
    - **Hover Tooltip Fix:** Resolved issue where hovering over the island displayed nothing. The root cause was unescaped ampersands (`&`) in status strings (e.g. `Awake & chilling`) causing GTK Pango markup parsing failures. Added `html.escape()` sanitization to all dynamic tooltip strings (`esc_animal`, `esc_mood`, `esc_title`, `esc_media`) so the rich Pango tooltip displays reliably on hover.
    - **Interactive Non-Interrupting Throttle & Tiered Alerts:** Implemented tiered heat alerts (`warm` at 70°C, `hot` at 80°C, `critical` at 90°C). When the user clicks the island (pet, switch animal, or cycle mode), active warm/hot alerts are dismissed immediately, granting a 30-second interaction immunity window where non-critical alerts are suppressed. Non-critical alerts display for a readable 3.5s before throttling for 35s, while critical alerts always break through for hardware safety. Affection milestones (Stranger → Soulmate) track petting progress in the rich Pango tooltip.
    - **Persistent Affection & 2-Hour Decay (`stats.json`):** Companion stats are persisted at runtime in [`dotfiles-linux/waybar/.config/waybar/scripts/island/stats.json`](file:///home/asim/setup/Dotfiles/dotfiles-linux/waybar/.config/waybar/scripts/island/stats.json) (ignored in git via `.gitignore`). Affection increments +1 per pet click and decreases by 1 every 2 hours based on stored timestamps (both online during execution and offline across system reboots). Tooltip displays current affection level, bond bar, and countdown to next decay. Selected companion animal also persists across restarts.

---

## Notes

* Keep GNOME installed until Hyprland is confirmed to be stable.
* Record configuration changes and fixes in this document as setup continues.



