# Keybindings Reference

This document provides a comprehensive cheat sheet for all keybindings configured in these dotfiles.

---

## 🐧 Linux / Hyprland

> **Note:** `$mainMod` is mapped to the **<kbd>SUPER</kbd>** (Windows) key.

### 🚀 Application & Utility Shortcuts

| Keybinding | Action / Command | Description |
| :--- | :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>Return</kbd> | `$terminal` (`kitty`) | Launch Kitty terminal emulator |
| <kbd>SUPER</kbd> + <kbd>Tab</kbd> | `$menu` (`rofi`) | Open application launcher menu |
| <kbd>SUPER</kbd> + <kbd>Esc</kbd> | `hyprlauncher` | Open Hyprland application launcher |
| <kbd>SUPER</kbd> + <kbd>E</kbd> | `$fileManager` (`dolphin`) | Open Dolphin file manager |
| <kbd>SUPER</kbd> + <kbd>W</kbd> | `zen` | Open Zen Web Browser |
| <kbd>SUPER</kbd> + <kbd>M</kbd> | `$logoutmenu` (`wlogout`) | Open power / logout menu |
| <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>Delete</kbd> | `wlogout` | Open power / logout menu |
| <kbd>SUPER</kbd> + <kbd>L</kbd> | `hyprlock` | Lock the screen |
| <kbd>SUPER</kbd> + <kbd>N</kbd> | `swaync-client -t` | Toggle SwayNC notification center |
| <kbd>SUPER</kbd> + <kbd>R</kbd> | `~/.config/waybar/scripts/launch.sh` | Reload / restart Waybar |
| <kbd>SUPER</kbd> + <kbd>C</kbd> | `hyprpicker -a` | Pick screen color and copy hex to clipboard |
| <kbd>SUPER</kbd> + <kbd>B</kbd> | `wallpaper-switcher.py` | Open wallpaper selector |
| <kbd>SUPER</kbd> + <kbd>H</kbd> | `help-window.py` | Show Hyprland shortcuts help dialog |
| <kbd>SUPER</kbd> + <kbd>I</kbd> | `hyprsysteminfo` | Open Hyprland system information |
| <kbd>SUPER</kbd> + <kbd>End</kbd> | `kitty -1 fish -c "btop"` | Open BTOP resource monitor |

---

### 📸 Screenshots

| Keybinding | Action / Command | Description |
| :--- | :--- | :--- |
| <kbd>Print</kbd> | `hyprshot -m window` | Capture screenshot of focused window |
| <kbd>SUPER</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> | `hyprshot -m region` | Capture interactive region screenshot |

---

### 🪟 Window Management

| Keybinding | Action / Command | Description |
| :--- | :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>Q</kbd> | `killactive` | Close active window |
| <kbd>SUPER</kbd> + <kbd>F</kbd> | `fullscreen` | Toggle fullscreen mode |
| <kbd>SUPER</kbd> + <kbd>Alt</kbd> + <kbd>Space</kbd> | `togglefloating` | Toggle floating / tiled state |
| <kbd>SUPER</kbd> + <kbd>P</kbd> | `pseudo` | Toggle pseudotile mode for active window |
| <kbd>SUPER</kbd> + <kbd>J</kbd> | `layoutmsg, togglesplit` | Toggle split direction (horizontal/vertical) |
| <kbd>SUPER</kbd> + <kbd>Left Click (Hold)</kbd> | `movewindow` | Drag to move window |
| <kbd>SUPER</kbd> + <kbd>Right Click (Hold)</kbd> | `resizewindow` | Drag to resize window |

---

### 🧭 Window Focus & Navigation

| Keybinding | Action / Command | Description |
| :--- | :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>←</kbd> | `movefocus, l` | Move focus to left window |
| <kbd>SUPER</kbd> + <kbd>→</kbd> | `movefocus, r` | Move focus to right window |
| <kbd>SUPER</kbd> + <kbd>↑</kbd> | `movefocus, u` | Move focus to window above |
| <kbd>SUPER</kbd> + <kbd>↓</kbd> | `movefocus, d` | Move focus to window below |

---

### 📑 Workspace Controls

| Keybinding | Action / Command | Description |
| :--- | :--- | :--- |
| <kbd>SUPER</kbd> + <kbd>1</kbd> – <kbd>9</kbd>, <kbd>0</kbd> | `workspace [1-10]` | Switch to workspace 1–10 |
| <kbd>SUPER</kbd> + <kbd>Shift</kbd> + <kbd>1</kbd> – <kbd>9</kbd>, <kbd>0</kbd> | `movetoworkspace [1-10]` | Move active window to workspace 1–10 |
| <kbd>SUPER</kbd> + <kbd>S</kbd> | `togglespecialworkspace, magic` | Toggle special scratchpad workspace |
| <kbd>SUPER</kbd> + <kbd>Alt</kbd> + <kbd>S</kbd> | `movetoworkspace, special:magic` | Move active window to scratchpad |
| <kbd>SUPER</kbd> + <kbd>Mouse Wheel Up</kbd> | `workspace, e-1` | Switch to previous workspace |
| <kbd>SUPER</kbd> + <kbd>Mouse Wheel Down</kbd> | `workspace, e+1` | Switch to next workspace |

---

### 🔊 Multimedia & Hardware Keys

| Keybinding | Action / Command | Description |
| :--- | :--- | :--- |
| <kbd>XF86AudioRaiseVolume</kbd> | `wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+` | Increase volume (+5%) |
| <kbd>XF86AudioLowerVolume</kbd> | `wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-` | Decrease volume (-5%) |
| <kbd>XF86AudioMute</kbd> | `wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle` | Toggle audio mute |
| <kbd>XF86AudioMicMute</kbd> | `wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle` | Toggle microphone mute |
| <kbd>XF86MonBrightnessUp</kbd> | `brightnessctl set 5%+` | Increase screen brightness |
| <kbd>XF86MonBrightnessDown</kbd> | `brightnessctl set 5%-` | Decrease screen brightness |
| <kbd>XF86AudioPlay</kbd> / <kbd>Pause</kbd> | `playerctl play-pause` | Play / Pause media playback |
| <kbd>XF86AudioNext</kbd> | `playerctl next` | Next media track |
| <kbd>XF86AudioPrev</kbd> | `playerctl previous` | Previous media track |

---

## 🐱 Kitty Terminal Shortcuts

| Keybinding | Action | Description |
| :--- | :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>C</kbd> | `copy_or_interrupt` | Copy selection (if text selected) or send interrupt `SIGINT` |
| <kbd>Ctrl</kbd> + <kbd>F</kbd> | Kitty Search Kitten | Interactive search in terminal scrollback buffer |
| <kbd>Page Up</kbd> | `scroll_page_up` | Scroll up one page in scrollback |
| <kbd>Page Down</kbd> | `scroll_page_down` | Scroll down one page in scrollback |
| <kbd>Ctrl</kbd> + <kbd>+</kbd> / <kbd>=</kbd> | `change_font_size +1` | Increase terminal font size |
| <kbd>Ctrl</kbd> + <kbd>-</kbd> / <kbd>_</kbd> | `change_font_size -1` | Decrease terminal font size |
| <kbd>Ctrl</kbd> + <kbd>0</kbd> | `change_font_size 0` | Reset terminal font size to default |

---

## 🪟 Windows / GlazeWM

### Window Focus & Movement

| Keybinding | Command | Description |
| :--- | :--- | :--- |
| <kbd>Alt</kbd> + <kbd>H</kbd> / <kbd>←</kbd> | `focus --direction left` | Focus left window |
| <kbd>Alt</kbd> + <kbd>L</kbd> / <kbd>→</kbd> | `focus --direction right` | Focus right window |
| <kbd>Alt</kbd> + <kbd>K</kbd> / <kbd>↑</kbd> | `focus --direction up` | Focus upper window |
| <kbd>Alt</kbd> + <kbd>J</kbd> / <kbd>↓</kbd> | `focus --direction down` | Focus lower window |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>H</kbd> / <kbd>←</kbd> | `move --direction left` | Move window left |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>L</kbd> / <kbd>→</kbd> | `move --direction right` | Move window right |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>K</kbd> / <kbd>↑</kbd> | `move --direction up` | Move window up |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>J</kbd> / <kbd>↓</kbd> | `move --direction down` | Move window down |

### Window State & Sizing

| Keybinding | Command | Description |
| :--- | :--- | :--- |
| <kbd>Alt</kbd> + <kbd>U</kbd> / <kbd>P</kbd> | `resize --width -2% / +2%` | Shrink / expand window width |
| <kbd>Alt</kbd> + <kbd>I</kbd> / <kbd>O</kbd> | `resize --height -2% / +2%` | Shrink / expand window height |
| <kbd>Alt</kbd> + <kbd>R</kbd> | `wm-enable-binding-mode resize` | Enter interactive resize mode (<kbd>HJKL</kbd>/<kbd>Arrows</kbd>, <kbd>Esc</kbd> to exit) |
| <kbd>Alt</kbd> + <kbd>V</kbd> | `toggle-tiling-direction` | Toggle horizontal / vertical tiling split |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>Space</kbd> | `toggle-floating --centered` | Toggle floating state |
| <kbd>Alt</kbd> + <kbd>T</kbd> | `toggle-tiling` | Return window to tiling state |
| <kbd>Alt</kbd> + <kbd>F</kbd> | `toggle-fullscreen` | Toggle fullscreen |
| <kbd>Alt</kbd> + <kbd>M</kbd> | `toggle-minimized` | Minimize window |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>Q</kbd> | `close` | Close focused window |
| <kbd>Ctrl</kbd> + <kbd>Space</kbd> | `wm-cycle-focus` | Cycle focus (tiling → floating → fullscreen) |

### Workspace & WM Control

| Keybinding | Command | Description |
| :--- | :--- | :--- |
| <kbd>Alt</kbd> + <kbd>Return</kbd> | `shell-exec wt` | Launch Windows Terminal |
| <kbd>Alt</kbd> + <kbd>1</kbd> – <kbd>9</kbd> | `focus --workspace [1-9]` | Switch to workspace 1–9 |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>1</kbd> – <kbd>9</kbd> | `move --workspace [1-9]` | Move window and switch to workspace 1–9 |
| <kbd>Alt</kbd> + <kbd>A</kbd> / <kbd>S</kbd> | `focus --prev/next-active-workspace` | Switch to previous / next active workspace |
| <kbd>Alt</kbd> + <kbd>D</kbd> | `focus --recent-workspace` | Switch to most recent workspace |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd> | `wm-reload-config` | Reload GlazeWM configuration |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>W</kbd> | `wm-redraw` | Redraw all windows |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd> | `wm-toggle-pause` | Pause / unpause GlazeWM keybindings |
| <kbd>Alt</kbd> + <kbd>Shift</kbd> + <kbd>E</kbd> | `wm-exit` | Exit GlazeWM process |
