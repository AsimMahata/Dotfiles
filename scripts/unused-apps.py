#!/usr/bin/env python3
"""
unused-apps: Package and Application Usage Auditor for Arch Linux.

Logic:
1. Queries explicitly installed top-level packages (pacman -Qetq).
2. Cross-references binaries in /usr/bin/ against:
   a. ActivityWatch GUI usage data (if available: exact active time in foreground).
   b. Filesystem Access Time (atime) for each binary on disk.
3. Identifies unused packages and outputs clean, actionable uninstall commands.
"""

import os
import sys
import time
import glob
import json
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

AW_URL = "http://localhost:5600/api/0"

# Core/essential packages that should never be marked for accidental removal
CORE_PACKAGES = {
    "base", "linux", "linux-firmware", "linux-headers", "intel-ucode", "amd-ucode",
    "sudo", "systemd", "systemd-libs", "polkit", "polkit-gnome", "networkmanager",
    "hyprland", "waybar", "rofi-wayland", "swaync", "wlogout", "swww", "awww",
    "pipewire", "pipewire-pulse", "wireplumber", "pavucontrol",
    "bluez", "bluez-utils", "fish", "kitty", "stow", "git", "yay",
    "xdg-desktop-portal", "xdg-desktop-portal-hyprland", "brightnessctl", "playerctl"
}

def get_hostname():
    import socket
    return socket.gethostname()

def fetch_activitywatch_apps(days=30):
    """Fetch app usage durations from local ActivityWatch server."""
    hostname = get_hostname()
    start_time = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Try hostname bucket first, then search any window bucket
    buckets_to_try = [f"aw-watcher-window_{hostname}"]
    try:
        with urllib.request.urlopen(f"{AW_URL}/buckets/", timeout=2) as r:
            buckets = json.loads(r.read().decode())
        for b in buckets:
            if b.startswith("aw-watcher-window") and b not in buckets_to_try:
                buckets_to_try.append(b)
    except Exception:
        pass

    app_durations = {}
    for bucket_id in buckets_to_try:
        url = f"{AW_URL}/buckets/{bucket_id}/events?start={start_time}&limit=50000"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "unused-apps/2.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                events = json.loads(resp.read().decode())
            for ev in events:
                app = ev.get("data", {}).get("app", "")
                if app:
                    app_clean = app.lower()
                    app_durations[app_clean] = app_durations.get(app_clean, 0) + ev.get("duration", 0)
            if app_durations:
                break
        except Exception:
            continue

    return app_durations

def get_explicit_packages():
    """Get explicitly installed top-level packages via pacman -Qetq."""
    try:
        out = subprocess.check_output(["pacman", "-Qetq"], text=True)
        return [p.strip() for p in out.strip().splitlines() if p.strip()]
    except Exception as e:
        print(f"Error running pacman: {e}", file=sys.stderr)
        return []

def get_package_binaries(pkg_name):
    """Get all executable files in /usr/bin provided by a package."""
    try:
        out = subprocess.check_output(["pacman", "-Ql", pkg_name], text=True)
        binaries = []
        for line in out.splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                fpath = parts[1].strip()
                if fpath.startswith("/usr/bin/") and not os.path.isdir(fpath):
                    binaries.append(fpath)
        return binaries
    except Exception:
        return []

def get_package_description(pkg_name):
    """Get a short description of the package from pacman -Qi."""
    try:
        out = subprocess.check_output(["pacman", "-Qi", pkg_name], text=True)
        for line in out.splitlines():
            if line.startswith("Description"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return ""

def format_duration(seconds):
    """Format seconds into readable hours/minutes."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m"
    hours = minutes / 60
    return f"{hours:.1f}h"

def format_time_ago(dt):
    """Format a datetime into 'X days ago'."""
    now = datetime.now()
    diff = now - dt
    if diff.days == 0:
        hours = diff.seconds // 3600
        return f"{hours}h ago" if hours > 0 else "today"
    elif diff.days == 1:
        return "yesterday"
    else:
        return f"{diff.days}d ago"

def main():
    parser = argparse.ArgumentParser(description="Find installed packages you don't use on Arch Linux.")
    parser.add_argument("-d", "--days", type=int, default=30, help="Consider unused if not accessed in N days (default: 30)")
    parser.add_argument("--all", action="store_true", help="Include core/system packages in output")
    args = parser.parse_args()

    cutoff_time = time.time() - (args.days * 86400)
    cutoff_dt = datetime.now() - timedelta(days=args.days)

    print(f"\n🔍 Auditing installed packages (Threshold: {args.days} days)...")
    
    # 1. Fetch ActivityWatch data
    aw_apps = fetch_activitywatch_apps(days=args.days)
    if aw_apps:
        print(f"  ✓ Connected to ActivityWatch ({len(aw_apps)} unique apps logged)")
    else:
        print("  ℹ ActivityWatch server not detected or empty; relying on filesystem access time (atime).")

    # 2. Query explicitly installed packages
    packages = get_explicit_packages()
    print(f"  ✓ Found {len(packages)} explicitly installed top-level packages.\n")

    used_packages = []
    unused_packages = []

    for pkg in packages:
        # Check core exemption
        is_core = pkg in CORE_PACKAGES
        if is_core and not args.all:
            continue

        desc = get_package_description(pkg)
        binaries = get_package_binaries(pkg)

        # Check ActivityWatch matching
        aw_duration = 0
        for b in binaries:
            bname = os.path.basename(b).lower()
            if bname in aw_apps:
                aw_duration = max(aw_duration, aw_apps[bname])
            if pkg.lower() in aw_apps:
                aw_duration = max(aw_duration, aw_apps[pkg.lower()])

        # Check filesystem atime on binaries
        latest_atime = 0
        for b in binaries:
            try:
                st = os.stat(b)
                latest_atime = max(latest_atime, st.st_atime)
            except OSError:
                continue

        # Decision Logic:
        # 1. If ActivityWatch has recorded active focus > 10s -> USED
        # 2. If atime > cutoff_time -> USED (recently executed/read)
        # 3. Otherwise -> UNUSED
        has_recent_atime = latest_atime > cutoff_time
        has_aw_usage = aw_duration > 10

        if has_aw_usage or has_recent_atime:
            last_access_str = ""
            if has_aw_usage:
                last_access_str = f"AW: {format_duration(aw_duration)}"
            elif latest_atime > 0:
                last_access_str = f"Access: {format_time_ago(datetime.fromtimestamp(latest_atime))}"
            
            used_packages.append((pkg, desc, last_access_str, is_core))
        else:
            last_access_str = "Never" if latest_atime == 0 else f"{format_time_ago(datetime.fromtimestamp(latest_atime))}"
            unused_packages.append((pkg, desc, last_access_str, binaries))

    # Print Results
    print("=" * 70)
    print(f"🟢 ACTIVELY USED PACKAGES (Past {args.days} days): {len(used_packages)}")
    print("=" * 70)
    for pkg, desc, status, is_core in sorted(used_packages, key=lambda x: x[0]):
        core_tag = " [Core]" if is_core else ""
        print(f"  ✓ {pkg:<25} {status:<18} {desc[:35]}{core_tag}")

    print("\n" + "=" * 70)
    print(f"🔴 UNUSED PACKAGES (0 usage in past {args.days} days): {len(unused_packages)}")
    print("=" * 70)
    if unused_packages:
        for pkg, desc, last_seen, binaries in sorted(unused_packages, key=lambda x: x[0]):
            bin_str = f"[{', '.join(os.path.basename(b) for b in binaries[:2])}]" if binaries else "[library/data]"
            print(f"  ✗ {pkg:<25} (Last: {last_seen:<10}) {desc[:35]}")
            print(f"    └─ To remove: sudo pacman -Rns {pkg}")
    else:
        print("  🎉 All your explicitly installed packages have been used recently!")

    print(f"\n💡 Summary: {len(used_packages)} used, {len(unused_packages)} unused out of {len(packages)} top-level packages.\n")

if __name__ == "__main__":
    main()
