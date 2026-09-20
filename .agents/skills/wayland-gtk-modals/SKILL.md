---
name: wayland-gtk-modals
description: Guide for creating Wayland desktop modals, popups, sliders, and overlay widgets using Python, GTK 3, and GtkLayerShell. Use when building or debugging custom popups, Waybar widget modals, or interactive desktop overlays on Hyprland.
---

# Building Wayland GTK Modals & Popups (`GtkLayerShell`)

This skill documents the architecture, best practices, and hard-earned lessons for creating high-performance, crash-proof modals, popups, and dropdowns on Wayland (Hyprland / Sway) using **Python 3**, **GTK 3**, and **`GtkLayerShell`**.

Reference document: [`gtk.md`](file:///home/asim/setup/Dotfiles/gtk.md).

---

## 1. Architecture: The Fullscreen Click-Catcher (SwayNC Pattern)

### The Problem with Compact Popups on Wayland
On Wayland, a client cannot globally grab pointer clicks outside its own surface (for security reasons). If you create a small compact window (e.g. 250x50px) anchored under a bar:
- The compositor does not reliably send a "click-outside" event when clicking the desktop or other applications.
- Spurious `focus-out-event` and `leave-notify-event` signals fire on window realization (~300–600ms after mapping), causing the window to prematurely vanish before the user can interact with it.

### The Solution: Fullscreen Transparent Backdrop
Follow the **SwayNC `layer-shell-cover-screen` pattern**:
1. Anchor the `Gtk.Window` to **all 4 edges** (`TOP`, `BOTTOM`, `LEFT`, `RIGHT`) on `GtkLayerShell.Layer.TOP`.
2. The root container is an invisible, 100% transparent `Gtk.EventBox` (`modal-backdrop`).
3. The actual UI card is packed inside an alignment wrapper (`halign = END`, `valign = START`) with margins placing it directly under the bar module.
4. The card is wrapped in its own `Gtk.EventBox` (`card-event-box`) that intercepts its own clicks and scrolls.
5. Clicking **inside** the card interacts with controls (slider, buttons).
6. Clicking **anywhere outside** hits the transparent backdrop and immediately dismisses the modal.

```
┌────────────────────────────────────────────────────────┐
│ Fullscreen Window (Layer.TOP, Anchored to all 4 edges)  │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Transparent Backdrop EventBox (Click = Close)      │ │
│ │                                                    │ │
│ │                             ┌───────────────────┐  │ │
│ │                             │ Card EventBox     │  │ │
│ │                             │ [ 󰕾 ───●─── 75% ] │  │ │
│ │                             └───────────────────┘  │ │
│ │                                                    │ │
│ │                                                    │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## 2. Critical Pitfalls & Rules for Agents

### ❌ Pitfall 1: The Background Daemon & PID File Trap
**What went wrong:**
Keeping the modal running as a persistent background daemon, toggling with `SIGUSR1`, and hiding with `win.hide()`.
- On Wayland with `GtkLayerShell`, calling `win.hide()` does not reliably unmap the transparent input region on all compositors. An invisible ghost surface remains over the entire screen, swallowing all mouse clicks and preventing Waybar or applications from responding.
- PID files in `/tmp` easily get desynchronized or point to dead/stuck processes, resulting in clicks doing nothing.

**✅ The Fix: Clean Stateless Process Termination**
- When dismissing (clicking outside or pressing `Escape`), call `Gtk.main_quit()` to **terminate the process completely**.
- Exiting immediately destroys the Wayland surface in the compositor — zero ghost windows, zero blocked clicks.
- Use a clean bash toggle launcher with `pkill` and `pgrep` (see Section 3).

---

### ❌ Pitfall 2: Synchronous Subprocess Spam During Slider Dragging
**What went wrong:**
Calling `subprocess.run(["wpctl", "set-volume", ...])` directly inside the slider's `value-changed` callback.
- Dragging a slider generates 60–120 events per second.
- `subprocess.run` synchronously blocks the GTK main UI thread for ~18ms per call.
- 10 calls = ~180ms of total UI freeze. The slider stutters, drops frames, and feels severely laggy.

**✅ The Fix: 60fps Coalesced Non-Blocking Controller**
Use a throttled async controller with `GLib.timeout_add(16, ...)` (16ms = 60fps) and non-blocking `subprocess.Popen`:

```python
class AudioController:
    def __init__(self):
        self.pending_val = None
        self.timer_active = False

    def set_volume_async(self, val):
        self.pending_val = max(0, min(100, val))
        if not self.timer_active:
            self.timer_active = True
            GLib.timeout_add(16, self._flush)

    def _flush(self):
        if self.pending_val is not None:
            val = self.pending_val
            self.pending_val = None
            val_float = val / 100.0
            subprocess.Popen(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val_float:.2f}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self.timer_active = False
        return False
```
*Result: The UI slider tracks mouse movement at your monitor's full refresh rate (144Hz/60Hz) with zero lag, while hardware adjustments follow smoothly in the background.*

---

### ❌ Pitfall 3: PyGObject Struct Name Collision (`self.container`)
**What went wrong:**
Naming an instance variable `self.container = Gtk.Box(...)` on a class inheriting from `Gtk.Window`.
- In C, `GtkWindow` inherits from `GtkContainer`, which has an internal struct field named `container`.
- PyGObject throws: `RuntimeError: field is not writable`.

**✅ The Fix:**
Never name attributes `self.container` or `self.window` on GTK widget subclasses. Use descriptive names like `self.card_container` or `self.content_box`.

---

### ❌ Pitfall 4: GTK3 CSS vs GTK4 / Web CSS (`transform` Crash)
**What went wrong:**
Using modern web / GTK4 CSS properties like `transform: scale(1.15);` or `transition: transform ...;`.
- GTK3's CSS engine does not support `transform`.
- `provider.load_from_data(...)` throws a fatal `gi.repository.GLib.GError: 'transform' is not a valid property name` and terminates the script before the window can even show.

**✅ The Fix:**
1. Stick to valid GTK3 CSS properties (`background-color`, `border`, `border-radius`, `box-shadow`, `padding`, `margin`, `color`).
2. **Always** wrap `provider.load_from_data()` in a `try...except` block so minor CSS syntax errors never crash the entire modal:
```python
provider = Gtk.CssProvider()
try:
    provider.load_from_data(css.encode())
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
except Exception as e:
    sys.stderr.write(f"Warning loading CSS: {e}\n")
```

---

### ❌ Pitfall 5: Hyprland Fullscreen Layer Blur
**What went wrong:**
Adding `hl.layer_rule({ match = { namespace = "my-modal" }, blur = true })` in `hyprland.lua`.
- Because the window uses the fullscreen click-catcher technique, Hyprland will blur the **entire monitor** like a lockscreen.

**✅ The Fix:**
Do **not** apply layer-rule blur to fullscreen modal namespaces. Instead, style the card itself with a rich dark translucent background and deep drop shadow in CSS:
```css
#modal-container {
    background: alpha(@background, 0.92);
    border: 1px solid alpha(@outline_variant, 0.5);
    border-radius: 20px;
    padding: 10px 18px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}
```

---

## 3. The Stateless Bash Toggle Pattern

Do not use PID files or signal daemons. Use this clean, fail-safe bash launcher pattern:

```bash
#!/usr/bin/env bash
# If the slider is already open in this mode, close it (toggle behavior)
PIDS=$(pgrep -f "quick-slider.py --mode volume")
if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null
    exit 0
fi

# Close any other open slider mode (e.g. brightness) to prevent overlap
pkill -f "quick-slider.py" 2>/dev/null

# Launch the requested mode
python3 ~/.config/waybar/scripts/quick-slider.py --mode volume &
```

---

## 4. Summary Checklist for Future Modals

| Check | Requirement |
| :--- | :--- |
| **Backdrop** | Window anchored to all 4 edges on `Layer.TOP` with a transparent `Gtk.EventBox`. |
| **Card EventBox** | UI card wrapped in an `EventBox` that intercepts clicks (`return True`). |
| **Dismiss** | Backdrop click and `Escape` key call `Gtk.main_quit()` for complete surface destruction. |
| **Dragging** | Throttled with `GLib.timeout_add(16, ...)` and non-blocking `subprocess.Popen`. |
| **Naming** | Never use `self.container` or `self.window` on widget classes. |
| **CSS** | No `transform` property; wrap `load_from_data` in `try...except`. |
| **Toggling** | Use `pgrep -f` / `kill` in bash launchers; avoid `/tmp/*.pid` files. |
| **Scrolling** | Connect `scroll-event` on `card_event_box` with `add_events(Gdk.EventMask.SCROLL_MASK)`. |
