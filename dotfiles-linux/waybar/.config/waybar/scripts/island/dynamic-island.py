#!/usr/bin/env python3
"""
Waybar Dynamic Island & Desktop Companion Engine
Provides an animated pet companion that reacts to music, auto-morphs into system vitals,
shows media status, and alerts on high CPU/thermal loads.
"""

import sys
import time
import json
import subprocess
import os
import signal

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

NBSP = "\u00a0"

ANIMALS = [
    {
        "name": "Neko (Cat)",
        "emoji": "🐱",
        "music_frames": [
            f"ᓚᘏᗢ ♪{NBSP*3}",
            f"{NBSP}ᓚᘏᗢ ♫{NBSP*2}",
            f"{NBSP*2}ᓚᘏᗢ ♬{NBSP}",
            f"{NBSP*3}ᓚᘏᗢ ♪",
            f"{NBSP*2}ᓚᘏᗢ ♬{NBSP}",
            f"{NBSP}ᓚᘏᗢ ♫{NBSP*2}"
        ],
        "idle_frames": [
            f"ᓚᘏᗢ ~{NBSP*2}",
            f"ᓚᘏᗢ ฅ{NBSP*2}",
            f"ᓚᘏᗢ ~{NBSP*2}",
            f"ᓚᘏᗢ ฅ^{NBSP}"
        ],
        "petted": f"ᓚᘏᗢ ❤️ (purr~)",
        "heat": f"ᓚᘏᗢ 🔥",
        "sleep": f"ᓚᘏᗢ zZ{NBSP}"
    },
    {
        "name": "Usagi (Bunny)",
        "emoji": "🐰",
        "music_frames": [
            f"(\\_/) ♪{NBSP*2}",
            f"{NBSP}(\\_/) ♫{NBSP}",
            f"{NBSP*2}(\\_/) ♬",
            f"{NBSP}(\\_/) ♫{NBSP}"
        ],
        "idle_frames": [
            "(\\_/) (• . •)",
            "(\\(\\ (•‿•)",
            "(\\_/) ( •_•)"
        ],
        "petted": "(\\_/) />❤️",
        "heat": "(\\_/) 🔥",
        "sleep": f"(\\_/) zZ{NBSP}"
    },
    {
        "name": "Duck (Honk)",
        "emoji": "🦆",
        "music_frames": [
            f"( •ө•) ♪{NBSP*2}",
            f"{NBSP}( •ө•) ♫{NBSP}",
            f"{NBSP*2}( •ө•) ♬",
            f"{NBSP}( •ө•) ♫{NBSP}"
        ],
        "idle_frames": [
            "( •ө•) ~",
            "( •ө•) quack",
            "( •ө•)"
        ],
        "petted": "( •ө•) ❤️",
        "heat": "( >ө<) 💨",
        "sleep": f"( -ө-) zZ{NBSP}"
    },
    {
        "name": "Ghost (Booo)",
        "emoji": "👻",
        "music_frames": [
            f"👻 ♪{NBSP*3}",
            f"{NBSP}👻 ♫{NBSP*2}",
            f"{NBSP*2}👻 ♬{NBSP}",
            f"{NBSP*3}👻 ♪"
        ],
        "idle_frames": [
            "(っ'-')╮ 👻",
            "(つ•̀ᴥ•́)つ",
            "👻 booo~"
        ],
        "petted": "👻 ❤️",
        "heat": "👻 🔥",
        "sleep": f"👻 zZ{NBSP*2}"
    },
    {
        "name": "Crab (Rave)",
        "emoji": "🦀",
        "music_frames": [
            "(V)(°,,,,°)(V) ♪",
            f"{NBSP}🦀 rave ♫{NBSP}",
            "(V)(°,,,,°)(V) ♬",
            f"{NBSP}🦀 ♫{NBSP*2}"
        ],
        "idle_frames": [
            "🦀 ~",
            "(V)(°,,,,°)(V)",
            "🦀 *snip*"
        ],
        "petted": "🦀 ❤️",
        "heat": "🦀 ♨️",
        "sleep": f"🦀 zZ{NBSP*2}"
    },
    {
        "name": "Inu (Puppy)",
        "emoji": "🐶",
        "music_frames": [
            f"(U・x・U) ♪{NBSP*2}",
            f"{NBSP}(՞•ﻌ•՞) ♫{NBSP}",
            f"{NBSP*2}(U・x・U) ♬",
            f"{NBSP}(՞•ﻌ•՞) ♫{NBSP}"
        ],
        "idle_frames": [
            "(U・x・U)ノ",
            "(՞•ﻌ•՞) woof!",
            "(U・x・U) ~"
        ],
        "petted": "(՞•ﻌ•՞) ❤️",
        "heat": "(U・x・U) 🔥",
        "sleep": "(U・x・U) zZ"
    }
]

# State variables
current_animal_idx = 0
affection_score = 0
petted_until = 0.0
awake_until = 0.0
force_mode = None  # None: auto-cycle, 0: PET, 1: VITALS, 2: MUSIC
force_mode_until = 0.0
last_media_meta = ""
music_tick = 0

def marquee_scroll(text: str, max_len: int = 13, tick: int = 0) -> str:
    """Smooth bounce ticker (moving left to right and back) for any text exceeding max_len."""
    clean = text.strip()
    if len(clean) <= max_len:
        return clean
    
    max_shift = len(clean) - max_len
    hold_ticks = 8  # ~1.75s pause at start and end
    total_cycle = (max_shift + hold_ticks) * 2
    pos = tick % total_cycle
    
    if pos < hold_ticks:
        shift = 0
    elif pos < hold_ticks + max_shift:
        shift = pos - hold_ticks
    elif pos < hold_ticks + max_shift + hold_ticks:
        shift = max_shift
    else:
        shift = max_shift - (pos - (hold_ticks + max_shift + hold_ticks))
        
    return clean[shift : shift + max_len]

def handle_sigterm(signum, frame):
    os._exit(0)

def handle_pet(signum, frame):
    """SIGUSR1: Pet the companion (Left-click) - wakes up for 15s!"""
    global affection_score, petted_until, awake_until
    affection_score += 1
    petted_until = time.time() + 3.0
    awake_until = time.time() + 15.0

def handle_switch_animal(signum, frame):
    """SIGUSR2: Switch companion animal (Right-click) - wakes up for 15s!"""
    global current_animal_idx, awake_until
    current_animal_idx = (current_animal_idx + 1) % len(ANIMALS)
    awake_until = time.time() + 15.0

def handle_morph_mode(signum, frame):
    """SIGRTMIN+1: Force cycle display mode (Middle-click)"""
    global force_mode, force_mode_until
    if force_mode is None:
        force_mode = 1  # Switch to VITALS
    else:
        force_mode = (force_mode + 1) % 3
    force_mode_until = time.time() + 10.0

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)
signal.signal(signal.SIGUSR1, handle_pet)
signal.signal(signal.SIGUSR2, handle_switch_animal)
try:
    signal.signal(signal.SIGRTMIN + 1, handle_morph_mode)
except Exception:
    pass

def get_system_vitals():
    cpu_pct = 0
    cpu_temp = 45.0
    ram_used = 0.0
    ram_total = 0.0
    ram_pct = 0

    if HAS_PSUTIL:
        try:
            cpu_pct = int(psutil.cpu_percent(interval=None))
            mem = psutil.virtual_memory()
            ram_used = round(mem.used / (1024 ** 3), 1)
            ram_total = round(mem.total / (1024 ** 3), 1)
            ram_pct = int(mem.percent)

            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps and temps['coretemp']:
                cpu_temp = temps['coretemp'][0].current
            elif 'acpitz' in temps and temps['acpitz']:
                cpu_temp = temps['acpitz'][0].current
            elif temps:
                first_sensor = list(temps.values())[0]
                if first_sensor:
                    cpu_temp = first_sensor[0].current
        except Exception:
            pass

    return cpu_pct, int(round(cpu_temp)), ram_used, ram_total, ram_pct

def get_media_status():
    try:
        status_proc = subprocess.run(
            ["playerctl", "status"],
            capture_output=True,
            text=True,
            timeout=0.25
        )
        status = status_proc.stdout.strip()
        if not status:
            return "Stopped", "", ""
        
        meta_proc = subprocess.run(
            ["playerctl", "metadata", "--format", "{{ title }} - {{ artist }}"],
            capture_output=True,
            text=True,
            timeout=0.25
        )
        meta = meta_proc.stdout.strip()
        if not meta or meta == " - ":
            meta = "Audio Playing"
        return status, meta, status
    except Exception:
        return "Stopped", "", ""

def main():
    global force_mode, force_mode_until, last_media_meta, music_tick, awake_until
    frame_idx = 0
    poll_counter = 0

    # Cached readings
    cpu_pct, cpu_temp, ram_used, ram_total, ram_pct = get_system_vitals()
    player_status, media_meta, player_raw = get_media_status()

    while True:
        now = time.time()

        # Update vitals & media every 7 ticks (~1.5s)
        if poll_counter % 7 == 0:
            cpu_pct, cpu_temp, ram_used, ram_total, ram_pct = get_system_vitals()
            player_status, media_meta, player_raw = get_media_status()
            if media_meta != last_media_meta:
                last_media_meta = media_meta
                music_tick = 0
        poll_counter += 1
        music_tick += 1

        animal = ANIMALS[current_animal_idx]
        is_playing = (player_status == "Playing")
        is_heat_alert = (cpu_temp >= 80 or cpu_pct >= 85)

        # Keep awake while music is playing
        if is_playing:
            awake_until = now + 15.0

        is_awake = is_playing or (now < awake_until) or (now < force_mode_until)

        # Determine active mode
        if now < force_mode_until and force_mode is not None:
            active_mode = force_mode
        else:
            force_mode = None
            # Auto cycle when awake: 0..119 ticks (0-26s) -> PET
            #                        120..149 ticks (26-33s) -> VITALS
            #                        150..179 ticks (33-40s) -> MUSIC (if playing)
            cycle_pos = poll_counter % 180
            if cycle_pos < 120:
                active_mode = 0  # PET
            elif cycle_pos < 150:
                active_mode = 1  # VITALS
            else:
                active_mode = 2 if is_playing else 0  # MUSIC or PET

        # Content building
        css_class = "pet"
        extra_info = ""

        # Priority 1: High Heat / Load Alert Override
        if is_heat_alert:
            display_text = f"{animal['heat']} {cpu_temp}°C"
            css_class = "alert"
            mood = "Overheating! 🔥"
        # Priority 2: Sleeping Mode (when music stopped and not petted/awake)
        elif not is_awake:
            display_text = animal['sleep']
            css_class = "sleeping"
            mood = "Sleeping peacefully 💤 (Click to wake up!)"
        # Priority 3: Petted Reaction
        elif now < petted_until:
            display_text = animal['petted']
            css_class = "petted"
            mood = "Ecstatic & Loved! ✨"
        # Priority 4: Normal Awake Modes
        elif active_mode == 1:  # VITALS
            display_text = f"🌡️ {cpu_temp}°C • 󰻠 {cpu_pct}%"
            css_class = "vitals"
            mood = "Monitoring System"
        elif active_mode == 2 and is_playing:  # MUSIC
            # Marquee scrolling song title (left to right bounce) so it never expands the bar
            scrolled_title = marquee_scroll(media_meta, max_len=13, tick=music_tick)
            display_text = f"󰎆 {scrolled_title}"
            css_class = "music"
            mood = f"Vibing to {media_meta}"
        else:  # PET (Awake & chilling or dancing)
            if is_playing:
                frames = animal['music_frames']
                display_text = frames[frame_idx % len(frames)]
                css_class = "playing"
                mood = f"Dancing to {media_meta}"
            else:
                frames = animal['idle_frames']
                display_text = frames[(frame_idx // 3) % len(frames)]
                css_class = "idle"
                rem_sec = max(1, int(awake_until - now))
                mood = f"Awake & chilling ({rem_sec}s until sleep)"

        # Safeguard: if any mode's text exceeds 16 chars, smoothly marquee it
        if len(display_text) > 16:
            display_text = marquee_scroll(display_text, max_len=16, tick=frame_idx)

        frame_idx += 1

        # Tooltip with Rich Pango Markup
        media_line = f"󰎆 {media_meta}" if media_meta else "󰝚 Idle (No music playing)"
        tooltip = (
            f"<span size='larger' weight='bold' foreground='#bcc3ff'>🐾 Dynamic Island</span>\n"
            f"<span foreground='#c4c5dd'>Companion:</span> <b>{animal['name']}</b> ({mood})\n"
            f"<span foreground='#c4c5dd'>Affection:</span> <b>{affection_score}</b> ❤️\n\n"
            f"<span weight='bold' foreground='#bcc3ff'>─── System Vitals ───</span>\n"
            f"🌡️ CPU Temp:  <b>{cpu_temp}°C</b>\n"
            f"󰻠 CPU Usage: <b>{cpu_pct}%</b>\n"
            f"󰍛 Memory:    <b>{ram_used}G / {ram_total}G ({ram_pct}%)</b>\n\n"
            f"<span weight='bold' foreground='#bcc3ff'>─── Media ───</span>\n"
            f"{media_line}\n\n"
            f"<span size='smaller' foreground='#90909a'>Left-click: Pet (+1 ❤️)\nRight-click: Switch Companion\nMiddle-click: Cycle View Mode</span>"
        )

        payload = {
            "text": display_text,
            "tooltip": tooltip,
            "class": css_class
        }

        try:
            sys.stdout.write(json.dumps(payload) + "\n")
            sys.stdout.flush()
        except (BrokenPipeError, IOError):
            sys.exit(0)

        time.sleep(0.22)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        try:
            sys.stdout.close()
            sys.stderr.close()
        except Exception:
            pass
        os._exit(0)
