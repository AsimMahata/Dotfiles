---
name: hyprland-ai-skill
description: Comprehensive Hyprland compositor configuration, troubleshooting, and optimization guide. Use when configuring monitors, workspaces, window rules, layer rules, animations, keybindings, gestures, decorations, plugins (hyprpm), and hyprctl IPC commands.
---

# Hyprland Configuration & Troubleshooting Guide

Comprehensive guide for configuring, optimizing, and debugging Hyprland (Wayland compositor).

---

## 1. Core Configuration Sections

### Monitor Configuration
Format: `monitor = name, resolution@refreshRate, position, scale`
```ini
# Auto-detect fallback
monitor = , preferred, auto, 1

# High-DPI screen with scaling (e.g. 2.8K 90Hz at 1.5x / 2x scale)
monitor = eDP-1, 2880x1800@90, 0x0, 1.5

# External monitor placed to the right
monitor = HDMI-A-1, 1920x1080@60, 1920x0, 1
```

### Autostart (`exec-once` vs `exec`)
```ini
exec-once = swww-daemon &
exec-once = waybar &
exec-once = swaync &
exec-once = /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
```

### Look & Feel (Decorations, Blur & Shadows)
```ini
decoration {
    rounding = 10
    active_opacity = 1.0
    inactive_opacity = 0.9

    blur {
        enabled = true
        size = 6
        passes = 3
        new_optimizations = true
        xray = false
    }

    shadow {
        enabled = true
        range = 15
        render_power = 3
        color = rgba(1a1a1aee)
    }
}
```

### Animations
```ini
animations {
    enabled = true
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05

    animation = windows, 1, 5, myBezier
    animation = windowsOut, 1, 5, default, popin 80%
    animation = border, 1, 10, default
    animation = borderangle, 1, 8, default
    animation = fade, 1, 5, default
    animation = workspaces, 1, 5, default, slide
}
```

---

## 2. Window & Layer Rules

### Window Rules (v2)
Syntax: `windowrulev2 = RULE, PATTERN`
```ini
# Open specific apps as floating
windowrulev2 = float, class:^(pavucontrol)$
windowrulev2 = float, class:^(blueman-manager)$
windowrulev2 = float, class:^(org.pulseaudio.pavucontrol)$
windowrulev2 = float, title:^(Open File)$
windowrulev2 = float, title:^(Save File)$

# Assign apps to specific workspaces
windowrulev2 = workspace 2, class:^(firefox|Brave-browser)$
windowrulev2 = workspace 3, class:^(kitty)$

# Suppress maximize events
windowrulev2 = suppressevent maximize, class:.*
```

### Layer Rules (for Waybar, SwayNC, Rofi)
```ini
layerrule = blur, waybar
layerrule = ignorezero, waybar
layerrule = blur, swaync-control-center
layerrule = blur, swaync-notification-window
layerrule = ignorezero, swaync-control-center
layerrule = ignorezero, swaync-notification-window
layerrule = blur, rofi
layerrule = ignorezero, rofi
```

---

## 3. Keybindings & Dispatchers

Binding Types:
- `bind = MOD, KEY, dispatcher, params` (Standard trigger)
- `binde = MOD, KEY, dispatcher, params` (Repeatable on hold)
- `bindm = MOD, KEY, dispatcher, params` (Mouse binds: movewindow, resizewindow)
- `bindl = MOD, KEY, dispatcher, params` (Locked screen / lid trigger)

Example Keybinds:
```ini
$mainMod = SUPER

# Window management
bind = $mainMod, Q, killactive,
bind = $mainMod, M, exit,
bind = $mainMod, V, togglefloating,
bind = $mainMod, F, fullscreen, 0
bind = $mainMod, P, pseudo,
bind = $mainMod, J, togglesplit,

# Navigation & Focus
bind = $mainMod, left, movefocus, l
bind = $mainMod, right, movefocus, r
bind = $mainMod, up, movefocus, u
bind = $mainMod, down, movefocus, d

# Workspaces
bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod SHIFT, 1, movetoworkspace, 1
bind = $mainMod SHIFT, 2, movetoworkspace, 2
bind = $mainMod SHIFT, 3, movetoworkspace, 3

# Mouse window control
bindm = $mainMod, mouse:272, movewindow
bindm = $mainMod, mouse:273, resizewindow
```

---

## 4. `hyprctl` Debugging & Runtime Inspection

Command | Description
:--- | :---
`hyprctl reload` | Reload configuration files without restart
`hyprctl monitors` | List active monitors, names, resolutions, scales, positions
`hyprctl workspaces` | List all open workspaces and active window count
`hyprctl clients` | Inspect all open windows (classes, titles, PID, floating status)
`hyprctl layers` | List all Wayland layers and surface names (Waybar, SwayNC, etc.)
`hyprctl version` | Display Hyprland build version and compile flags
