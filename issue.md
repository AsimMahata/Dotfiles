# Known Issue: Waybar Workspaces Click Unresponsive in Hyprland Lua

## 1. Description of the Issue
Clicking on workspace indicators in the Waybar bar does nothing (it fails to switch to the clicked workspace), even though the workspace pills are visible and reflect current workspace state.

---

## 2. Root Cause (Why It Is Like This)
1. **Hyprland Lua IPC Protocol Change:**
   - Following the migration of the Hyprland configuration from `hyprland.conf` to `hyprland.lua`, Hyprland evaluates all incoming IPC `dispatch` commands as Lua expressions (`return hl.dispatch(...)`).
   - The legacy command format (`hyprctl dispatch workspace <id>`) is no longer valid syntax in Lua mode and fails with:
     ```text
     error: [string "return hl.dispatch(workspace 2)"]:1: ')' expected near '2'
     ```
   - Hyprland in Lua mode now expects:
     ```bash
     hyprctl dispatch 'hl.dsp.focus({ workspace = <id> })'
     ```
2. **Waybar 0.15.0 Hardcoded IPC Calls:**
   - The stable Arch package (`waybar 0.15.0`) connects directly to Hyprland's UNIX domain socket (`$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket.sock`).
   - On workspace button clicks, Waybar sends the legacy `dispatch workspace <id>` string.
   - Because Hyprland is in Lua mode, it rejects the command as a Lua syntax error, resulting in no action.

---

## 3. Available Fixes

### Option 1: Install `waybar-git` (Recommended if staying on Lua)
Upstream Waybar has merged native support for Hyprland's Lua IPC dispatcher into `master`.

To install the latest version from AUR:
```bash
yay -S waybar-git
```
*(When prompted, replace the official `waybar` package with `waybar-git`).*

### Option 2: Revert Hyprland back to `hyprland.conf` (If keeping stable Waybar)
Hyprland's standard `.conf` configuration mode natively processes legacy `dispatch workspace <id>` commands without errors.

To revert:
1. Restore `hyprland.conf`:
   ```bash
   cp setup/backup/hypr/hyprland.conf dotfiles-linux/hypr/.config/hypr/
   ```
2. Remove `hyprland.lua`:
   ```bash
   rm dotfiles-linux/hypr/.config/hypr/hyprland.lua ~/.config/hypr/hyprland.lua
   ```
3. Restow and reload:
   ```bash
   stow -R -d dotfiles-linux -t ~ hypr
   hyprctl reload full-reset
   ```

---

# Issue 2: Built-in Keyboard Double-Typing / Key Chatter [NOT FIXED]

## 1. Description of the Issue
Single quick taps on keys (most frequently observed on `a`, `f`, and `backspace`) intermittently register twice (e.g. `a a`, double backspace).

- **Status:** **[NOT FIXED]**

---

## 2. Root Cause (Why It Is Like This)
1. **Mechanical Switch Contact Bounce (Key Chatter):**
   - The laptop's built-in keyboard (`at-translated-set-2-keyboard`) has slight physical switch bounce where the electrical contacts bounce upon being pressed, producing two electrical closures within 5–15 milliseconds.
2. **Lack of Default Linux Software Debounce:**
   - Unlike Windows and macOS (which have default driver-level debounce windows of 20–30ms), standard Linux input drivers do not filter contact bounce by default.
   - Hyprland's default repeat delay is 600ms, meaning these double inputs are not auto-repeat triggers, but raw duplicate keydown events occurring faster than humanly possible.

---

## 3. Available Fixes (Pending)

### Option 1: Hardware Cleaning
- Blow compressed air under and around the affected keycaps (`a`, `f`, `backspace`) to clear microscopic dust/oxidation causing contact bounce.

### Option 2: Software Debounce via `keyd`
- Install `keyd` and configure a 25ms–30ms debounce filter in `/etc/keyd/default.conf` so Linux automatically drops duplicate signals from the same key occurring within 30ms.
