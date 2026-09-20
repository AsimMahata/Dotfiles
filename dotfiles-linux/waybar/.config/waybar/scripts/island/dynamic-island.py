#!/usr/bin/env python3
"""
Waybar Dynamic Island & Desktop Companion Engine
Provides an animated pet companion that reacts to music, auto-morphs into system vitals,
shows media status, and alerts on high CPU/thermal loads.

Upgrades:
  U1 — Revamped idle frames (6 per animal)
  U2 — Unique music dance choreography
  U3 — CSS glow animations (handled in style.css)
  U4 — Multi-frame petted reactions
  U5 — Tiered heat alerts with throttling
  U6 — Sleep & wake transitions
  U7 — Affection milestones
"""

import sys
import time
import json
import subprocess
import os
import signal
import html

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
        "petted_frames": [
            f"ᓚᘏᗢ  ❗",
            f"ᓚᘏᗢ ❤️ ~",
            f"ᓚᘏᗢ (purr~)"
        ],
        "heat": f"ᓚᘏᗢ 🔥",
        "sleep": f"ᓚᘏᗢ zZ{NBSP}",
        "sleep_transition": [
            f"ᓚᘏᗢ ~{NBSP*2}",
            f"ᓚᘏᗢ z{NBSP*2}",
            f"ᓚᘏᗢ zZ{NBSP}"
        ],
        "wake_transition": [
            f"ᓚᘏᗢ  ❗",
            f"ᓚᘏᗢ ~{NBSP*2}",
            f"ᓚᘏᗢ ฅ{NBSP*2}"
        ]
    },
    {
        "name": "Usagi (Bunny)",
        "emoji": "🐰",
        "music_frames": [
            f"(\\_/) ♪{NBSP*3}~",
            f"{NBSP}(\\(\\ ♫{NBSP*2}~",
            f"(\\_/) ♬ ⌇{NBSP}~",
            f"{NBSP*2}(\\\\ ♪⌇{NBSP}",
            f"(\\_/) ♫{NBSP*2}~",
            f"{NBSP}(\\(\\ ♬{NBSP*3}"
        ],
        "idle_frames": [
            f"(\\_/) (• . •) ~",
            f"(\\_/) (•‿•)ノ",
            f"(\\(\\ ( ᵕ ᵕ ){NBSP}",
            f"(\\_/) (• •)?{NBSP}",
            f"(\\_/) (•ω•)ᵧ",
            f"(\\_/) (• . •)⌇"
        ],
        "petted_frames": [
            f"(\\_/) !{NBSP*3}",
            f"(\\_/) (ᵕᴗᵕ){NBSP}",
            f"(\\_/) ♡~{NBSP*2}"
        ],
        "heat": f"(\\_/) 🔥",
        "sleep": f"(\\_/) zZ{NBSP}",
        "sleep_transition": [
            f"(\\_/) ~{NBSP*3}",
            f"(\\_/) z{NBSP*3}",
            f"(\\_/) zZ{NBSP*2}"
        ],
        "wake_transition": [
            f"(\\_/) !{NBSP*3}",
            f"(\\_/) ~{NBSP*3}",
            f"(\\_/) (• . •) ~"
        ]
    },
    {
        "name": "Duck (Honk)",
        "emoji": "🦆",
        "music_frames": [
            f"( •ө•) ♪{NBSP*2}~",
            f"{NBSP}( •ө•)ᕗ ♫{NBSP}",
            f"( •ө•)彡 ♬{NBSP}",
            f"{NBSP*2}( •ө•) ♪{NBSP}",
            f"( •ө•)ᕗ ♫{NBSP}~",
            f"{NBSP}( •ө•)彡 ♬{NBSP}"
        ],
        "idle_frames": [
            f"( •ө•) ～{NBSP*2}",
            f"( •ө•)ᕗ ~♢",
            f"( ᵒөᵒ)  !{NBSP}",
            f"( •ө-)  ～{NBSP}",
            f"( •ө•)彡 ≋{NBSP}",
            f"( ˙ө˙ ) ～{NBSP}"
        ],
        "petted_frames": [
            f"( ᵒөᵒ) !{NBSP*2}",
            f"( ˘ө˘) ~{NBSP*2}",
            f"( ˘ө˘) ♡{NBSP*2}"
        ],
        "heat": f"( >ө<) 💨",
        "sleep": f"( -ө-) zZ{NBSP}",
        "sleep_transition": [
            f"( •ө•) ~{NBSP*2}",
            f"( -ө-) z{NBSP*2}",
            f"( -ө-) zZ{NBSP}"
        ],
        "wake_transition": [
            f"( ᵒөᵒ) !{NBSP*2}",
            f"( •ө•) ~{NBSP*2}",
            f"( •ө•) ～{NBSP*2}"
        ]
    },
    {
        "name": "Ghost (Booo)",
        "emoji": "👻",
        "music_frames": [
            f"꒰👻꒱ ♪{NBSP*2}~",
            f"{NBSP}꒰👻꒱ ♫{NBSP}~",
            f"{NBSP*2}꒰👻꒱ ♬⟡",
            f"{NBSP}꒰👻꒱ ♪⟡{NBSP}",
            f"꒰👻꒱ ♫{NBSP*3}",
            f"{NBSP*2}꒰👻꒱ ♬{NBSP}"
        ],
        "idle_frames": [
            f"{NBSP*2}꒰👻꒱{NBSP*3}~",
            f"{NBSP*3}꒰👻꒱ ···",
            f"꒰ 👻 ꒱ boo",
            f"{NBSP}꒰👻꒱ ᵕ̈{NBSP*2}",
            f"{NBSP*3}꒰👻꒱{NBSP}⟡",
            f"{NBSP*2}꒰ 👻꒱{NBSP}~"
        ],
        "petted_frames": [
            f"꒰👻꒱ !{NBSP*3}",
            f"꒰👻꒱ ᵕ̈{NBSP*2}",
            f"꒰👻꒱ ♡~{NBSP*2}"
        ],
        "heat": f"꒰👻꒱ 🔥",
        "sleep": f"꒰👻꒱ zZ{NBSP*2}",
        "sleep_transition": [
            f"꒰👻꒱ ~{NBSP*3}",
            f"꒰👻꒱ z{NBSP*3}",
            f"꒰👻꒱ zZ{NBSP*2}"
        ],
        "wake_transition": [
            f"꒰👻꒱ !{NBSP*3}",
            f"꒰👻꒱ ~{NBSP*3}",
            f"꒰👻꒱{NBSP*4}~"
        ]
    },
    {
        "name": "Crab (Rave)",
        "emoji": "🦀",
        "music_frames": [
            f"🦀 ♪ ✂{NBSP*2}~",
            f"{NBSP}🦀 ♫{NBSP}✂ ~",
            f"🦀 ♬ ✂✂{NBSP*2}",
            f"{NBSP}🦀 ♪{NBSP}✂{NBSP*2}",
            f"🦀 ♫ ✂{NBSP}~{NBSP}",
            f"{NBSP}🦀 ♬{NBSP*2}~{NBSP}"
        ],
        "idle_frames": [
            f"🦀 ~{NBSP*4}≋",
            f"🦀 ✂{NBSP*4}~",
            f"{NBSP}🦀{NBSP*2}·{NBSP}· ·",
            f"🦀 ~{NBSP*2}≋{NBSP*2}",
            f"{NBSP}🦀 ✂ ✂{NBSP*3}",
            f"🦀{NBSP*2}~ ≋{NBSP*2}"
        ],
        "petted_frames": [
            f"🦀 !{NBSP*4}",
            f"🦀 ~ ✂{NBSP*3}",
            f"🦀 ♡ ✂{NBSP*3}"
        ],
        "heat": f"🦀 ♨️",
        "sleep": f"🦀 zZ{NBSP*2}",
        "sleep_transition": [
            f"🦀 ~{NBSP*3}",
            f"🦀 z{NBSP*3}",
            f"🦀 zZ{NBSP*2}"
        ],
        "wake_transition": [
            f"🦀 !{NBSP*3}",
            f"🦀 ~{NBSP*3}",
            f"🦀 ~{NBSP*3}≋"
        ]
    },
    {
        "name": "Inu (Puppy)",
        "emoji": "🐶",
        "music_frames": [
            f"(U・x・U) ♪{NBSP}~",
            f"{NBSP}(՞•ﻌ•՞) ♫{NBSP}",
            f"(U・x・U) ♬∪",
            f"{NBSP}(՞•ﻌ•՞) ♪{NBSP}",
            f"(U・x・U) ♫~∪",
            f"{NBSP}(՞•ﻌ•՞) ♬{NBSP}"
        ],
        "idle_frames": [
            f"(U・x・U){NBSP*2}~",
            f"(U・x・U)ノ∪",
            f"(՞•ﻌ•՞){NBSP*2}♡",
            f"(U・x・U) ∪~",
            f"( ·ﻌ· ){NBSP}ha",
            f"(U・x・U) ~∪"
        ],
        "petted_frames": [
            f"(U・x・U) !{NBSP}",
            f"(՞•ﻌ•՞) ~{NBSP}",
            f"(՞•ﻌ•՞) ♡{NBSP}"
        ],
        "heat": f"(U・x・U) 🔥",
        "sleep": "(U・x・U) zZ",
        "sleep_transition": [
            f"(U・x・U) ~{NBSP}",
            f"(U・x・U) z{NBSP}",
            "(U・x・U) zZ"
        ],
        "wake_transition": [
            f"(U・x・U) !{NBSP}",
            f"(U・x・U) ~{NBSP}",
            f"(U・x・U){NBSP*2}~"
        ]
    }
]


# ─── State & Persistence ───
STATS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "stats.json")
DECAY_INTERVAL = 7200.0  # 2 hours per affection point decay

current_animal_idx = 0
affection_score = 0
last_decay_time = time.time()
last_pet_time = time.time()

def load_stats():
    """Loads persistent companion state and calculates offline affection decay."""
    global affection_score, current_animal_idx, last_decay_time, last_pet_time
    now = time.time()
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            affection_score = int(data.get("affection_score", 0))
            current_animal_idx = int(data.get("current_animal_idx", 0)) % len(ANIMALS)
            last_decay_time = float(data.get("last_decay_time", now))
            last_pet_time = float(data.get("last_pet_time", now))

            # Offline decay calculation: 1 heart lost per 2 hours
            if now > last_decay_time:
                decay_units = int((now - last_decay_time) // DECAY_INTERVAL)
                if decay_units > 0:
                    affection_score = max(0, affection_score - decay_units)
                    last_decay_time += decay_units * DECAY_INTERVAL
                    save_stats()
            return
        except Exception:
            pass

    affection_score = 0
    current_animal_idx = 0
    last_decay_time = now
    last_pet_time = now
    save_stats()

def save_stats():
    """Atomically persists companion state to stats.json."""
    global affection_score, current_animal_idx, last_decay_time, last_pet_time
    data = {
        "affection_score": affection_score,
        "current_animal_idx": current_animal_idx,
        "last_decay_time": last_decay_time,
        "last_pet_time": last_pet_time
    }
    try:
        tmp_file = STATS_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, STATS_FILE)
    except Exception:
        pass

petted_until = 0.0
awake_until = 0.0
force_mode = None  # None: auto-cycle, 0: PET, 1: VITALS, 2: MUSIC
force_mode_until = 0.0
last_media_meta = ""
music_tick = 0

# U5: Heat throttling & user interaction immunity
last_heat_show_time = 0.0
heat_showing_until = 0.0
heat_alert_tier = None
user_active_until = 0.0

# U6: Sleep/wake transitions
sleep_transition_start = 0.0
wake_transition_start = 0.0
was_asleep = False


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


# U7: Affection milestones
def get_affection_info(score):
    """Returns (title, heart_emoji, progress_bar) based on affection score."""
    if score >= 100:
        filled = 10
        return "Soulmate", "💖", "█" * filled
    elif score >= 50:
        filled = min(10, 5 + (score - 50) * 5 // 50)
        empty = 10 - filled
        return "Best Friend", "❤️", "█" * filled + "░" * empty
    elif score >= 25:
        filled = min(10, 3 + (score - 25) * 2 // 25)
        empty = 10 - filled
        return "Friend", "🧡", "█" * filled + "░" * empty
    elif score >= 10:
        filled = min(10, 1 + (score - 10) * 2 // 15)
        empty = 10 - filled
        return "Acquaintance", "💛", "█" * filled + "░" * empty
    else:
        filled = max(0, score * 1 // 10)
        empty = 10 - filled
        return "Stranger", "🤍", "█" * filled + "░" * empty


def handle_sigterm(signum, frame):
    os._exit(0)

def handle_pet(signum, frame):
    """SIGUSR1: Pet the companion (Left-click) - wakes up & grants immunity from non-critical alerts!"""
    global affection_score, petted_until, awake_until, wake_transition_start, last_heat_show_time
    global heat_showing_until, heat_alert_tier, user_active_until, last_pet_time
    now = time.time()
    if now > awake_until:
        wake_transition_start = now
    affection_score += 1
    last_pet_time = now
    save_stats()
    petted_until = now + 3.0
    awake_until = now + 15.0
    user_active_until = now + 30.0
    # Reset heat throttle & dismiss any active warm/hot alert so interaction is uninterrupted
    last_heat_show_time = now
    heat_showing_until = 0.0
    heat_alert_tier = None

def handle_switch_animal(signum, frame):
    """SIGUSR2: Switch companion animal (Right-click) - wakes up & grants immunity from non-critical alerts!"""
    global current_animal_idx, awake_until, wake_transition_start, last_heat_show_time
    global heat_showing_until, heat_alert_tier, user_active_until
    now = time.time()
    if now > awake_until:
        wake_transition_start = now
    current_animal_idx = (current_animal_idx + 1) % len(ANIMALS)
    save_stats()
    awake_until = now + 15.0
    user_active_until = now + 30.0
    last_heat_show_time = now
    heat_showing_until = 0.0
    heat_alert_tier = None


def handle_morph_mode(signum, frame):
    """SIGRTMIN+1: Force cycle display mode (Middle-click)"""
    global force_mode, force_mode_until, last_heat_show_time
    global heat_showing_until, heat_alert_tier, user_active_until
    now = time.time()
    user_active_until = now + 30.0
    last_heat_show_time = now
    heat_showing_until = 0.0
    heat_alert_tier = None
    if force_mode is None:
        force_mode = 1  # Switch to VITALS
    else:
        force_mode = (force_mode + 1) % 3
    force_mode_until = now + 10.0

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
    global last_heat_show_time, sleep_transition_start, wake_transition_start, was_asleep
    global affection_score, last_decay_time
    load_stats()
    frame_idx = 0
    poll_counter = 0
    last_payload_str = ""

    # Cached readings
    cpu_pct, cpu_temp, ram_used, ram_total, ram_pct = get_system_vitals()
    player_status, media_meta, player_raw = get_media_status()

    while True:
        now = time.time()

        # Online decay: 1 affection point lost every 2 hours
        if now - last_decay_time >= DECAY_INTERVAL:
            decay_units = int((now - last_decay_time) // DECAY_INTERVAL)
            if decay_units > 0:
                affection_score = max(0, affection_score - decay_units)
                last_decay_time += decay_units * DECAY_INTERVAL
                save_stats()

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

        # U5: Tiered heat detection
        current_heat_tier = None  # None, "warm", "hot", "critical"
        if cpu_temp >= 90 or cpu_pct >= 95:
            current_heat_tier = "critical"
        elif cpu_temp >= 80 or cpu_pct >= 85:
            current_heat_tier = "hot"
        elif cpu_temp >= 70:
            current_heat_tier = "warm"

        # Check if user is actively interacting with the island
        is_user_active = (now < user_active_until) or (now < petted_until)

        # Trigger heat alert if cooldown passed
        # Critical alert: ALWAYS interrupts immediately, 10s cooldown
        if current_heat_tier == "critical":
            if now >= last_heat_show_time + 10.0:
                heat_showing_until = now + 4.0
                heat_alert_tier = "critical"
                last_heat_show_time = now
        # Warm / Hot alert: ONLY when user is NOT actively interacting, 35s cooldown
        elif current_heat_tier is not None and not is_user_active:
            if now >= last_heat_show_time + 35.0:
                heat_showing_until = now + 3.5
                heat_alert_tier = current_heat_tier
                last_heat_show_time = now

        is_showing_heat = (now < heat_showing_until) and (heat_alert_tier is not None)

        # Keep awake while music is playing
        if is_playing:
            awake_until = now + 15.0

        is_awake = is_playing or (now < awake_until) or (now < force_mode_until)

        # U6: Track sleep/wake transitions
        if not is_awake and not was_asleep:
            # Just fell asleep — start sleep transition
            sleep_transition_start = now
            was_asleep = True
        elif is_awake and was_asleep:
            was_asleep = False

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

        # Priority 1: Heat Alert (throttled; non-critical never interrupts active user)
        if is_showing_heat:
            if heat_alert_tier == "critical":
                display_text = f"⚠️ 🔥 {cpu_temp}°C !!"
                css_class = "critical"
                mood = "CRITICAL TEMPERATURE! 🔥🔥"
            elif heat_alert_tier == "hot":
                display_text = f"{animal['heat']} {cpu_temp}°C"
                css_class = "alert"
                mood = "Overheating! 🔥"
            else:  # warm
                display_text = f"{animal['heat']} 🌡️ {cpu_temp}°C"
                css_class = "warm"
                mood = f"Getting warm... {cpu_temp}°C"

        # Priority 2: U6 — Wake transition (plays for ~0.7s after waking from sleep)
        elif now < wake_transition_start + 0.66:
            elapsed = now - wake_transition_start
            frame = min(2, int(elapsed / 0.22))
            display_text = animal['wake_transition'][frame]
            css_class = "waking"
            mood = "Waking up! ✨"

        # Priority 3: U6 — Sleep transition (plays for ~0.7s after falling asleep)
        elif was_asleep and now < sleep_transition_start + 0.66:
            elapsed = now - sleep_transition_start
            frame = min(2, int(elapsed / 0.22))
            display_text = animal['sleep_transition'][frame]
            css_class = "sleeping"
            mood = "Falling asleep... 💤"

        # Priority 4: Sleeping Mode (when music stopped and not petted/awake)
        elif not is_awake:
            display_text = animal['sleep']
            css_class = "sleeping"
            mood = "Sleeping peacefully 💤 (Click to wake up!)"

        # Priority 5: U4 — Petted Reaction (3-frame sequence)
        elif now < petted_until:
            pet_elapsed = petted_until - now  # 3.0 -> 0.0
            pet_progress = 3.0 - pet_elapsed  # 0.0 -> 3.0
            pet_frame = min(2, int(pet_progress))
            display_text = animal['petted_frames'][pet_frame]
            css_class = "petted"
            mood = "Ecstatic & Loved! ✨"

        # Priority 6: Normal Awake Modes
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
                display_text = frames[(frame_idx // 5) % len(frames)]
                css_class = "idle"
                mood = "Awake & chilling"

        # Safeguard: if any mode's text exceeds 16 chars, smoothly marquee it
        if len(display_text) > 16:
            display_text = marquee_scroll(display_text, max_len=16, tick=frame_idx)

        frame_idx += 1

        # U7: Affection info for tooltip
        aff_title, aff_heart, aff_bar = get_affection_info(affection_score)

        decay_info = ""
        if affection_score > 0:
            mins_left = max(1, int((last_decay_time + DECAY_INTERVAL - now) // 60))
            decay_info = f" <small><span color='#90909a'>(-1 in {mins_left}m)</span></small>"

        # Tooltip with Rich Pango Markup (escaped so GTK never drops the tooltip on unescaped & or < >)
        media_raw = f"󰎆 {media_meta}" if media_meta else "󰝚 Idle (No music playing)"
        esc_animal = html.escape(str(animal['name']))
        esc_mood = html.escape(str(mood))
        esc_title = html.escape(str(aff_title))
        esc_media = html.escape(str(media_raw))

        tooltip = (
            f"<b><span color='#bcc3ff'>🐾 Dynamic Island</span></b>\n"
            f"<span color='#c4c5dd'>Companion:</span> <b>{esc_animal}</b> ({esc_mood})\n"
            f"<span color='#c4c5dd'>Affection:</span> <b>{esc_title}</b> {aff_heart} ({affection_score}){decay_info}\n"
            f"<span color='#c4c5dd'>Progress:</span>  {aff_bar}\n\n"
            f"<b><span color='#bcc3ff'>─── System Vitals ───</span></b>\n"
            f"🌡️ CPU Temp:  <b>{cpu_temp}°C</b>\n"
            f"󰻠 CPU Usage: <b>{cpu_pct}%</b>\n"
            f"󰍛 Memory:    <b>{ram_used}G / {ram_total}G ({ram_pct}%)</b>\n\n"
            f"<b><span color='#bcc3ff'>─── Media ───</span></b>\n"
            f"{esc_media}\n\n"
            f"<small><span color='#90909a'>Left-click: Pet (+1 {aff_heart})\nRight-click: Switch Companion\nMiddle-click: Cycle View Mode</span></small>"
        )

        payload = {
            "text": display_text,
            "tooltip": tooltip,
            "class": css_class
        }

        payload_str = json.dumps(payload)
        if payload_str != last_payload_str:
            last_payload_str = payload_str
            try:
                sys.stdout.write(payload_str + "\n")
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
