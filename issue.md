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
