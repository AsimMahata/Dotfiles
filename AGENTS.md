# Agent Guidelines & Rules

## Maintenance of System Documentation & Tracking

Whenever any new package, application, tool, or dotfile is added, modified, or removed:

1. **Document in [`setup.md`](file:///home/asim/setup/Dotfiles/setup.md):**
   - Record exact installation commands (`pacman`, `yay`, `pip`, etc.), enabled systemd services, configuration adjustments, and launch/verification steps.
   - Maintain `setup.md` as an accurate, self-contained, reproducible log of the system setup.

2. **Update [`packages.md`](file:///home/asim/setup/Dotfiles/packages.md):**
   - Add every newly installed package or custom script to the package inventory table with its package name, source (`pacman`, `yay`, or local script), and purpose.

3. **Update ActivityWatch Categories ([`aw-category-export.json`](file:///home/asim/setup/Dotfiles/aw-category-export.json)):**
   - Whenever a new user-facing application or GUI tool is added, add its process/binary name to the appropriate category regex rule in `aw-category-export.json` with an accurate, distinct brand color so screen time is automatically categorized.

4. **Track Issues in [`issue.md`](file:///home/asim/setup/Dotfiles/issue.md):**
   - Record any active, unresolved, or pending system bugs with their root causes and available fixes.

## No Trial-and-Error Fixes Without Permission

- **Definite Fixes Only:** Only apply fixes directly if the exact root cause and verified solution are known with certainty.
- **Ask Before Speculative Changes:** If a solution requires trial-and-error, experimental workarounds, or uncertain troubleshooting, you must explain the situation and ask for user permission before executing commands or modifying files, to avoid breaking working system components.

## Building Wayland Desktop Modals & Widgets

Whenever creating, modifying, or troubleshooting any desktop popup, modal, slider, or overlay widget (for Waybar, Hyprland, or custom scripts):

- **Refer to [`gtk.md`](file:///home/asim/setup/Dotfiles/gtk.md) and the `wayland-gtk-modals` skill ([`SKILL.md`](file:///home/asim/setup/Dotfiles/.agents/skills/wayland-gtk-modals/SKILL.md)):**
  - **Architecture:** Always use the SwayNC fullscreen transparent click-catcher pattern (`GtkLayerShell` anchored across all 4 edges on `Layer.TOP` with an inner card). Never rely on raw `focus-out` or `leave-notify` events on compact windows, as they fire spuriously on Wayland.
  - **Stateless Lifecycle:** Never use background daemons, `/tmp/*.pid` files, or `win.hide()`. Exiting cleanly with `Gtk.main_quit()` on backdrop click or `Escape` ensures the Wayland surface is fully destroyed without leaving ghost input regions. Use `pgrep -f` / `kill` in bash launchers for toggling.
  - **Performance:** Always throttle slider changes to 60fps via `GLib.timeout_add(16, ...)` and non-blocking `subprocess.Popen` (never synchronous `subprocess.run`).
  - **GTK3 Pitfalls:** Never name widget attributes `self.container`, avoid unsupported GTK3 CSS like `transform`, and wrap `provider.load_from_data` in `try...except`.
