import pygame
import sys
import math
import random
import json
import array
import os
import asyncio  # 1. Keep asyncio imported

# Base directory for relative asset resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

# =========================================================================
# KEEP ALL HELPER FUNCTIONS & ASSET GENERATORS AT TOP LEVEL HERE
# (generate_tone_sound, generate_nyc_skyline, Catalogs, etc.)
# =========================================================================

# ... [Keep your catalogs, asset generator functions, etc. here] ...

async def main():
    global game_state, total_cash, high_score, equipped_paint, equipped_map
    global owned_paints, owned_underglows, owned_maps, throttle_level, brake_level
    global sfx_volume, music_volume, confirm_reset_active, previous_state_before_settings
    global active_stance, previous_stance, combo_multiplier, wheelie_combo_timer
    global wheelie_distance, session_cash_earned, scrape_cash_earned
    global pivot_x, pivot_y, world_offset, angle, angular_velocity, speed, wheel_spin
    global throttle_timer, brake_timer, shake_timer, shake_intensity, camera_y_offset
    global rear_susp_comp, rear_susp_vel, front_susp_comp, front_susp_vel
    global sparks, splashes, floating_popups, smoke_particles, active_garage_tab

    # 1. INITIALIZE PYGAME & WINDOW INSIDE MAIN
    pygame.init()
    pygame.joystick.init()

    # Gamepad Auto-Detection
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 500
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("SoFlow Wheelie Life - iOS Glass Edition")

    # 2. INITIALIZE CLOCK HERE (BEFORE THE WHILE LOOP)
    clock = pygame.time.Clock()

    # Load save data and assets
    load_game_data()
    load_all_paint_assets()

    # 3. GAME LOOP
    while True:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        current_map = get_current_map()

        # ... [Your entire event handling, game updates, physics & rendering code] ...

        pygame.display.flip()
        
        # 4. YIELD CONTROL TO BROWSER THREAD EVERY FRAME
        await asyncio.sleep(0)

# Entry point execution
if __name__ == "__main__":
    asyncio.run(main())

# =========================================================================
# INITIALIZATION, GAMEPAD & AUDIO ENGINE SETUP
# =========================================================================
pygame.init()
pygame.joystick.init()

# Gamepad Auto-Detection
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for joy in joysticks:
    joy.init()

try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    audio_enabled = True
except Exception as e:
    print(f"Mixer initialization error: {e}")
    audio_enabled = False

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 500
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("SoFlow Wheelie Life - iOS Glass Edition")
clock = pygame.time.Clock()

# Color Palette - iOS Translucent Glass & Monochrome Theme
GROUND_Y = 400

COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_MAIN = (245, 245, 250)
COLOR_TEXT_MUTED = (160, 165, 175)
COLOR_TEXT_DARK = (15, 15, 20)
COLOR_DANGER = (220, 60, 60)

GLASS_OVERLAY_DARK = (10, 12, 16, 190)
GLASS_BG_CARD = (255, 255, 255, 22)
GLASS_BG_CARD_HOVER = (255, 255, 255, 45)
GLASS_BG_ACTIVE = (255, 255, 255, 235)
GLASS_BORDER_SUBTLE = (255, 255, 255, 55)
GLASS_BORDER_HI = (255, 255, 255, 150)

# Base Dimensions for Bike Images
FRAME_WIDTH = 260
FRAME_HEIGHT = 180
SEATSTAND_WIDTH = 260
SEATSTAND_HEIGHT = 180

REAR_WHEEL_SIZE = 90   
FRONT_WHEEL_SIZE = 96  

SAVE_FILE = get_asset_path("save_data.json")

# Audio Engine State & Dual Fallback Channel
sfx_volume = 0.7
music_volume = 0.5
current_playing_music = None

music_channel = None
active_music_sound = None

MENU_MUSIC_FILE = get_asset_path("assets/music_menu.wav")

def generate_tone_sound(frequency, duration, volume=0.3):
    if not audio_enabled: return None
    n_samples = int(44100 * duration)
    buf = array.array('h', [0] * (n_samples * 2))
    for i in range(n_samples):
        t = float(i) / 44100.0
        val = int(32767.0 * volume * math.sin(2.0 * math.pi * frequency * t))
        val = max(-32768, min(32767, val))
        buf[i * 2] = val
        buf[i * 2 + 1] = val
    return pygame.mixer.Sound(buffer=buf)

def generate_noise_sound(duration, volume=0.2):
    if not audio_enabled: return None
    n_samples = int(44100 * duration)
    buf = array.array('h', [0] * (n_samples * 2))
    for i in range(n_samples):
        val = int(random.uniform(-32767, 32767) * volume)
        buf[i * 2] = val
        buf[i * 2 + 1] = val
    return pygame.mixer.Sound(buffer=buf)

# Load SFX with procedural fallbacks
try:
    sound_click = pygame.mixer.Sound(get_asset_path("assets/click.wav"))
except Exception:
    sound_click = generate_tone_sound(880, 0.05, 0.25)

try:
    sound_scrape = pygame.mixer.Sound(get_asset_path("assets/scrape.wav"))
except Exception:
    sound_scrape = generate_noise_sound(0.2, 0.18)

try:
    sound_slam = pygame.mixer.Sound(get_asset_path("assets/slam.wav"))
except Exception:
    sound_slam = generate_tone_sound(120, 0.15, 0.4)

def play_sfx(sound):
    if audio_enabled and sound:
        sound.set_volume(sfx_volume)
        sound.play()

def update_bg_music(target_music_file):
    global current_playing_music, active_music_sound, music_channel
    if not audio_enabled:
        return
    
    if current_playing_music == target_music_file:
        try:
            if music_channel and active_music_sound:
                music_channel.set_volume(music_volume)
            else:
                pygame.mixer.music.set_volume(music_volume)
        except Exception:
            pass
        return

    current_playing_music = target_music_file

    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

    if music_channel:
        music_channel.stop()
        active_music_sound = None

    if not target_music_file or not os.path.exists(target_music_file):
        if target_music_file:
            print(f"[AUDIO ERROR] File not found: {target_music_file}")
        return

    try:
        pygame.mixer.music.load(target_music_file)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
        return
    except Exception:
        pass

    try:
        active_music_sound = pygame.mixer.Sound(target_music_file)
        if music_channel is None:
            music_channel = pygame.mixer.Channel(7)
        music_channel.set_volume(music_volume)
        music_channel.play(active_music_sound, loops=-1)
    except Exception as err:
        print(f"[AUDIO ERROR] Could not play '{target_music_file}': {err}")

# =========================================================================
# SAVE SYSTEM & PLAYER DATA
# =========================================================================
total_cash = 100
high_score = 0.0
owned_paints = [0]
equipped_paint = 0
owned_underglows = [0]
equipped_underglow = 0
owned_maps = [0]
equipped_map = 0

throttle_level = 1
brake_level = 1

def load_game_data():
    global total_cash, high_score, owned_paints, equipped_paint
    global owned_underglows, equipped_underglow, owned_maps, equipped_map
    global throttle_level, brake_level, sfx_volume, music_volume
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            total_cash = data.get("total_cash", 100)
            high_score = float(data.get("high_score", 0.0))
            owned_paints = data.get("owned_paints", [0])
            equipped_paint = data.get("equipped_paint", 0)
            owned_underglows = data.get("owned_underglows", [0])
            equipped_underglow = data.get("equipped_underglow", 0)
            owned_maps = data.get("owned_maps", [0])
            equipped_map = data.get("equipped_map", 0)
            throttle_level = data.get("throttle_level", 1)
            brake_level = data.get("brake_level", 1)
            sfx_volume = data.get("sfx_volume", 0.7)
            music_volume = data.get("music_volume", 0.5)
    except Exception:
        reset_all_data_defaults()

def save_game_data():
    data = {
        "total_cash": total_cash,
        "high_score": high_score,
        "owned_paints": owned_paints,
        "equipped_paint": equipped_paint,
        "owned_underglows": owned_underglows,
        "equipped_underglow": equipped_underglow,
        "owned_maps": owned_maps,
        "equipped_map": equipped_map,
        "throttle_level": throttle_level,
        "brake_level": brake_level,
        "sfx_volume": sfx_volume,
        "music_volume": music_volume
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

def reset_all_data_defaults():
    global total_cash, high_score, owned_paints, equipped_paint
    global owned_underglows, equipped_underglow, owned_maps, equipped_map
    global throttle_level, brake_level
    total_cash = 100
    high_score = 0.0
    owned_paints = [0]
    equipped_paint = 0
    owned_underglows = [0]
    equipped_underglow = 0
    owned_maps = [0]
    equipped_map = 0
    throttle_level = 1
    brake_level = 1
    save_game_data()

load_game_data()

def get_font(font_name, size, bold=False):
    try:
        return pygame.font.SysFont(font_name, int(size), bold=bold)
    except Exception:
        return pygame.font.Font(None, int(size))

def draw_glass_box(surface, rect, bg_color=GLASS_BG_CARD, border_color=GLASS_BORDER_SUBTLE, border_radius=16, border_width=1):
    glass_surf = pygame.Surface((int(rect.width), int(rect.height)), pygame.SRCALPHA)
    pygame.draw.rect(glass_surf, bg_color, (0, 0, int(rect.width), int(rect.height)), border_radius=int(border_radius))
    if border_width > 0:
        pygame.draw.rect(glass_surf, border_color, (0, 0, int(rect.width), int(rect.height)), width=int(border_width), border_radius=int(border_radius))
    surface.blit(glass_surf, (int(rect.x), int(rect.y)))

# =========================================================================
# 1. PROCEDURAL BACKGROUND & MAP ASSET GENERATORS
# =========================================================================
def generate_nyc_skyline(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    base_color = (18, 26, 44) if is_far else (10, 16, 30)
    window_color = (80, 200, 255, 160) if is_far else (140, 235, 255, 210)
    random.seed(42 if is_far else 101)
    x = 0
    while x < width:
        w = random.randint(35, 75) if is_far else random.randint(45, 95)
        h = random.randint(90, 240) if is_far else random.randint(60, 170)
        pygame.draw.rect(surf, base_color, (x, height - h, w, h))
        if random.random() < 0.35:
            spire_w = max(4, w // 8)
            spire_h = random.randint(25, 60)
            pygame.draw.rect(surf, base_color, (x + (w // 2) - (spire_w // 2), height - h - spire_h, spire_w, spire_h))
            pygame.draw.circle(surf, (0, 210, 255, 220), (int(x + (w // 2)), int(height - h - spire_h)), 2)
        for wx in range(x + 6, x + w - 6, 11):
            for wy in range(height - h + 12, height - 12, 16):
                if random.random() < 0.65:
                    pygame.draw.rect(surf, window_color, (wx, wy, 4, 7))
        x += w + (random.randint(4, 12) if is_far else random.randint(8, 20))
    return surf

def generate_sunset_mountains(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    color = (45, 20, 50) if is_far else (25, 10, 35)
    random.seed(202 if is_far else 303)
    pts = [(0, height)]
    step = 40 if is_far else 60
    for x in range(0, width + step, step):
        h = random.randint(80, 180) if is_far else random.randint(40, 110)
        pts.append((int(x), int(height - h)))
    pts.append((width, height))
    pygame.draw.polygon(surf, color, pts)
    return surf

def generate_cyber_skyline(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    base_color = (20, 12, 35) if is_far else (12, 6, 24)
    neon_colors = [(255, 0, 128), (0, 240, 255), (180, 0, 255), (255, 220, 0)]
    random.seed(505 if is_far else 606)
    x = 0
    while x < width:
        w = random.randint(40, 85)
        h = random.randint(110, 260) if is_far else random.randint(70, 180)
        pygame.draw.rect(surf, base_color, (x, height - h, w, h))
        neon_c = random.choice(neon_colors)
        alpha_c = (*neon_c, 180 if is_far else 230)
        pygame.draw.line(surf, alpha_c, (x, height - h), (x + w, height - h), 3)
        x += w + random.randint(6, 18)
    return surf

def generate_cherry_blossom_forest(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(808 if is_far else 809)
    hill_color = (42, 20, 48) if is_far else (28, 12, 32)
    pts = [(0, height)]
    step = 50 if is_far else 70
    for x in range(0, width + step, step):
        h = random.randint(90, 180) if is_far else random.randint(40, 110)
        pts.append((int(x), int(height - h)))
    pts.append((width, height))
    pygame.draw.polygon(surf, hill_color, pts)

    tree_count = 18 if is_far else 10
    for _ in range(tree_count):
        tx = random.randint(0, width)
        ty = height - (random.randint(20, 90) if is_far else random.randint(10, 40))
        trunk_w = 5 if is_far else 10
        trunk_h = random.randint(40, 65) if is_far else random.randint(75, 115)
        trunk_color = (48, 28, 34) if is_far else (35, 18, 24)
        branch_color = (40, 22, 28)
        top_y = ty - trunk_h
        pygame.draw.rect(surf, trunk_color, (tx - trunk_w//2, top_y, trunk_w, trunk_h))
        bw = 3 if is_far else 5
        pygame.draw.line(surf, branch_color, (tx, top_y + 20), (tx - (14 if is_far else 28), top_y - (5 if is_far else 15)), bw)
        pygame.draw.line(surf, branch_color, (tx, top_y + 25), (tx + (16 if is_far else 32), top_y - (8 if is_far else 20)), bw)
        cluster_color_base = (245, 125, 175, 215) if is_far else (255, 105, 168, 240)
        cluster_color_light = (255, 190, 220, 230) if is_far else (255, 180, 215, 250)
        offsets = [(-18, -12), (18, -15), (0, -28), (-8, 8), (10, 5)] if not is_far else [(-10, -8), (10, -10), (0, -18)]
        for ox, oy in offsets:
            rad = random.randint(14, 22) if is_far else random.randint(22, 36)
            cx, cy = tx + ox, top_y + oy
            pygame.draw.circle(surf, cluster_color_base, (int(cx), int(cy)), int(rad))
            pygame.draw.circle(surf, cluster_color_light, (int(cx - rad//4), int(cy - rad//4)), int(rad * 0.65))
    return surf

def generate_california_coast(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(909 if is_far else 910)
    if is_far:
        cliff_color = (65, 35, 25)
        pts = [(0, height)]
        for x in range(0, width + 60, 60):
            h = random.randint(50, 130)
            pts.append((int(x), int(height - h)))
        pts.append((width, height))
        pygame.draw.polygon(surf, cliff_color, pts)
        pygame.draw.circle(surf, (255, 210, 80, 230), (int(width // 2), int(height - 20)), 75)
        pygame.draw.circle(surf, (255, 255, 190, 255), (int(width // 2), int(height - 20)), 50)
    else:
        for i in range(16):
            px = random.randint(0, width)
            py = height - 5
            trunk_h = random.randint(110, 180)
            curve = random.randint(-20, 20)
            pygame.draw.line(surf, (28, 18, 12), (int(px), int(py)), (int(px + curve), int(py - trunk_h)), 7)
            top_x, top_y = px + curve, py - trunk_h
            for angle_deg in range(0, 360, 40):
                rad = math.radians(angle_deg)
                lx = int(top_x + math.cos(rad) * random.randint(32, 55))
                ly = int(top_y + math.sin(rad) * random.randint(18, 38) + 12)
                pygame.draw.line(surf, (22, 16, 10), (int(top_x), int(top_y)), (int(lx), int(ly)), 3)
    return surf

def generate_alpine_mountains(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(111 if is_far else 222)
    rock_color = (40, 50, 70) if is_far else (25, 32, 48)
    snow_color = (235, 245, 255) if is_far else (200, 220, 240)
    
    pts = [(0, height)]
    snow_caps = []
    step = 45 if is_far else 65
    for x in range(0, width + step, step):
        h = random.randint(120, 250) if is_far else random.randint(60, 140)
        peak_x, peak_y = int(x), int(height - h)
        pts.append((peak_x, peak_y))
        if random.random() < 0.7:
            snow_caps.append((peak_x, peak_y, random.randint(25, 45)))
    pts.append((width, height))
    
    pygame.draw.polygon(surf, rock_color, pts)
    for cx, cy, cap_size in snow_caps:
        cap_pts = [
            (cx, cy),
            (cx - cap_size, cy + cap_size * 0.9),
            (cx - cap_size * 0.3, cy + cap_size * 0.6),
            (cx, cy + cap_size * 0.8),
            (cx + cap_size * 0.4, cy + cap_size * 0.5),
            (cx + cap_size, cy + cap_size * 0.9)
        ]
        pygame.draw.polygon(surf, snow_color, cap_pts)

    if not is_far:
        for _ in range(25):
            tx = random.randint(0, width)
            ty = height - random.randint(10, 50)
            tw = random.randint(12, 22)
            th = random.randint(45, 85)
            pine_color = (15, 35, 28)
            pygame.draw.polygon(surf, pine_color, [(tx, ty - th), (tx - tw, ty), (tx + tw, ty)])
            pygame.draw.polygon(surf, (220, 235, 245, 180), [(tx, ty - th), (tx - tw * 0.6, ty - th * 0.4), (tx + tw * 0.6, ty - th * 0.4)])
    return surf

def generate_volcanic_canyon(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(333 if is_far else 444)
    base_color = (24, 12, 14) if is_far else (16, 8, 10)
    lava_color = (255, 60, 10) if is_far else (255, 120, 20)
    
    pts = [(0, height)]
    step = 50 if is_far else 70
    peaks = []
    for x in range(0, width + step, step):
        h = random.randint(100, 230) if is_far else random.randint(50, 130)
        peak_x, peak_y = int(x), int(height - h)
        pts.append((peak_x, peak_y))
        if h > 160: peaks.append((peak_x, peak_y))
    pts.append((width, height))
    
    pygame.draw.polygon(surf, base_color, pts)
    for px, py in peaks:
        pygame.draw.circle(surf, (*lava_color, 160), (px, py), random.randint(15, 35))
        for _ in range(4):
            end_x = px + random.randint(-40, 40)
            end_y = py + random.randint(20, 90)
            pygame.draw.line(surf, (*lava_color, 220), (px, py), (end_x, end_y), random.randint(2, 4))
    return surf

NYC_FAR = generate_nyc_skyline(2000, 320, is_far=True)
NYC_NEAR = generate_nyc_skyline(2000, 320, is_far=False)
SUNSET_FAR = generate_sunset_mountains(2000, 320, is_far=True)
SUNSET_NEAR = generate_sunset_mountains(2000, 320, is_far=False)
CYBER_FAR = generate_cyber_skyline(2000, 320, is_far=True)
CYBER_NEAR = generate_cyber_skyline(2000, 320, is_far=False)
CHERRY_FAR = generate_cherry_blossom_forest(2000, 320, is_far=True)
CHERRY_NEAR = generate_cherry_blossom_forest(2000, 320, is_far=False)
CALI_FAR = generate_california_coast(2000, 320, is_far=True)
CALI_NEAR = generate_california_coast(2000, 320, is_far=False)
ALPINE_FAR = generate_alpine_mountains(2000, 320, is_far=True)
ALPINE_NEAR = generate_alpine_mountains(2000, 320, is_far=False)
VOLCANO_FAR = generate_volcanic_canyon(2000, 320, is_far=True)
VOLCANO_NEAR = generate_volcanic_canyon(2000, 320, is_far=False)

STARS_SURF = pygame.Surface((1000, 300), pygame.SRCALPHA)
random.seed(777)
for _ in range(85):
    sx = random.randint(0, 1000)
    sy = random.randint(0, 220)
    sa = random.randint(120, 255)
    pygame.draw.circle(STARS_SURF, (200, 235, 255, sa), (int(sx), int(sy)), random.choice([1, 1, 2]))

rain_drops = []
for _ in range(65):
    rain_drops.append({
        'x': random.randint(-50, WINDOW_WIDTH + 50),
        'y': random.randint(0, WINDOW_HEIGHT),
        'speed': random.uniform(8, 15),
        'length': random.randint(10, 18)
    })

cherry_petals = []
for _ in range(50):
    cherry_petals.append({
        'x': random.randint(-50, WINDOW_WIDTH + 50),
        'y': random.randint(0, WINDOW_HEIGHT),
        'speed_y': random.uniform(1.2, 3.2),
        'speed_x': random.uniform(1.5, 4.0),
        'size': random.randint(3, 6),
        'rot': random.uniform(0, 360)
    })

snow_flakes = []
for _ in range(70):
    snow_flakes.append({
        'x': random.randint(-50, WINDOW_WIDTH + 50),
        'y': random.randint(0, WINDOW_HEIGHT),
        'speed_y': random.uniform(1.0, 2.5),
        'speed_x': random.uniform(-0.8, 0.8),
        'size': random.randint(2, 5)
    })

volcanic_embers = []
for _ in range(60):
    volcanic_embers.append({
        'x': random.randint(0, WINDOW_WIDTH),
        'y': random.randint(0, WINDOW_HEIGHT),
        'vx': random.uniform(-2.5, -0.5),
        'vy': random.uniform(-2.5, -0.8),
        'size': random.uniform(2.0, 5.0),
        'color': random.choice([(255, 90, 20), (255, 180, 40), (255, 40, 0)])
    })

motion_lines = []
for _ in range(35):
    motion_lines.append({
        'x': random.randint(0, WINDOW_WIDTH),
        'y': random.randint(80, GROUND_Y - 30),
        'length': random.randint(50, 180),
        'speed_mult': random.uniform(0.9, 1.6)
    })

smoke_particles = []

# Wheel Asset Loading
try:
    raw_wheel = pygame.image.load(get_asset_path("assets/wheel.png")).convert_alpha()
except Exception:
    raw_wheel = pygame.Surface((90, 90), pygame.SRCALPHA)
    pygame.draw.circle(raw_wheel, (30, 30, 30), (45, 45), 45, 8)
    pygame.draw.line(raw_wheel, (200, 200, 200), (0, 45), (90, 45), 3)
    pygame.draw.line(raw_wheel, (200, 200, 200), (45, 0), (45, 90), 3)

wheel_bounds = raw_wheel.get_bounding_rect()
tight_wheel = raw_wheel.subsurface(wheel_bounds)
w, h = tight_wheel.get_size()
max_dim = max(w, h)
centered_wheel_surf = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)
centered_wheel_surf.blit(tight_wheel, ((max_dim - w) // 2, (max_dim - h) // 2))

rear_wheel_img = pygame.transform.scale(centered_wheel_surf, (REAR_WHEEL_SIZE, REAR_WHEEL_SIZE))
front_wheel_img = pygame.transform.scale(centered_wheel_surf, (FRONT_WHEEL_SIZE, FRONT_WHEEL_SIZE))

# =========================================================================
# 2. CATALOGS & DATA
# =========================================================================
PAINTS_CATALOG = [
    {
        "id": 0, "name": "Factory Red", "price": 0,
        "file": get_asset_path("assets/frame_red.png"),
        "file_seatstand": get_asset_path("assets/frame_red_seatstand.png"),
        "hud_color": (220, 50, 50)
    },
    {
        "id": 1, "name": "Cyber Cyan", "price": 100,
        "file": get_asset_path("assets/frame_cyan.png"),
        "file_seatstand": get_asset_path("assets/frame_cyan_seatstand.png"),
        "hud_color": (0, 210, 255)
    },
    {
        "id": 2, "name": "Sunset Gold", "price": 250,
        "file": get_asset_path("assets/frame_gold.png"),
        "file_seatstand": get_asset_path("assets/frame_gold_seatstand.png"),
        "hud_color": (255, 200, 50)
    },
    {
        "id": 3, "name": "Hyper Purple", "price": 400,
        "file": get_asset_path("assets/frame_purple.png"),
        "file_seatstand": get_asset_path("assets/frame_purple_seatstand.png"),
        "hud_color": (200, 60, 255)
    },
    {
        "id": 4, "name": "Stealth Black", "price": 650,
        "file": get_asset_path("assets/frame_black.png"),
        "file_seatstand": get_asset_path("assets/frame_black_seatstand.png"),
        "hud_color": (60, 60, 70)
    }
]

UNDERGLOW_CATALOG = [
    {"id": 0, "name": "Electric Cyan", "price": 0, "color": (0, 210, 255)},
    {"id": 1, "name": "Acid Green", "price": 75, "color": (40, 230, 90)},
    {"id": 2, "name": "Lava Red", "price": 150, "color": (255, 50, 50)},
    {"id": 3, "name": "Deep Violet", "price": 300, "color": (180, 50, 255)},
    {"id": 4, "name": "Solar Yellow", "price": 450, "color": (255, 230, 30)}
]

MAPS_CATALOG = [
    {
        "id": 0, "name": "NYC Midnight", "price": 0,
        "sky_top": (6, 10, 24), "sky_bottom": (16, 28, 48),
        "road_color": (32, 35, 42), "dash_color": (240, 245, 255, 180),
        "far_layer": NYC_FAR, "near_layer": NYC_NEAR,
        "has_stars": True, "has_rain": True, "streetlights": True, "lamp_color": (255, 240, 180),
        "lens_filter": "NYC_NIGHT_LENS",
        "music": get_asset_path("assets/music_nyc.wav")
    },
    {
        "id": 1, "name": "Sunset Highway", "price": 180,
        "sky_top": (40, 15, 60), "sky_bottom": (245, 110, 50),
        "road_color": (45, 38, 42), "dash_color": (255, 210, 80, 210),
        "far_layer": SUNSET_FAR, "near_layer": SUNSET_NEAR,
        "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 190, 90),
        "lens_filter": "SUNSET_AMBER_LENS",
        "music": get_asset_path("assets/music_sunset.wav")
    },
    {
        "id": 2, "name": "Neon Cyber Grid", "price": 450,
        "sky_top": (12, 4, 28), "sky_bottom": (35, 10, 60),
        "road_color": (18, 14, 28), "dash_color": (0, 240, 255, 220),
        "far_layer": CYBER_FAR, "near_layer": CYBER_NEAR,
        "has_stars": True, "has_rain": True, "streetlights": True, "lamp_color": (255, 0, 160),
        "lens_filter": "CYBER_SCANLINE_LENS",
        "music": get_asset_path("assets/music_cyber.wav")
    },
    {
        "id": 3, "name": "Cherry Blossom Forest", "price": 320,
        "sky_top": (38, 15, 45), "sky_bottom": (240, 130, 175),
        "road_color": (42, 28, 38), "dash_color": (255, 190, 220, 210),
        "far_layer": CHERRY_FAR, "near_layer": CHERRY_NEAR,
        "has_stars": False, "has_rain": False, "streetlights": False, "lamp_color": (255, 180, 220),
        "has_petals": True, "lens_filter": "CHERRY_BLOOM_LENS",
        "music": get_asset_path("assets/music_cherry.wav")
    },
    {
        "id": 4, "name": "California Coast", "price": 500,
        "sky_top": (20, 30, 75), "sky_bottom": (255, 140, 40),
        "road_color": (48, 40, 36), "dash_color": (255, 220, 120, 220),
        "far_layer": CALI_FAR, "near_layer": CALI_NEAR,
        "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 220, 140),
        "lens_filter": "CALIFORNIA_GOLDEN_LENS",
        "music": get_asset_path("assets/music_cali.wav")
    },
    {
        "id": 5, "name": "Alpine Mountain Pass", "price": 10000,
        "sky_top": (10, 25, 50), "sky_bottom": (140, 185, 220),
        "road_color": (50, 58, 68), "dash_color": (230, 245, 255, 230),
        "far_layer": ALPINE_FAR, "near_layer": ALPINE_NEAR,
        "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (180, 225, 255),
        "has_snow": True, "lens_filter": "ALPINE_FROST_LENS",
        "music": get_asset_path("assets/music_alpine.wav")
    },
    {
        "id": 6, "name": "Volcanic Magma Canyon", "price": 10000,
        "sky_top": (18, 4, 6), "sky_bottom": (180, 40, 15),
        "road_color": (28, 20, 24), "dash_color": (255, 90, 20, 240),
        "far_layer": VOLCANO_FAR, "near_layer": VOLCANO_NEAR,
        "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 110, 30),
        "has_embers": True, "lens_filter": "VOLCANIC_GLOW_LENS",
        "music": get_asset_path("assets/music_volcano.wav")
    }
]

UPGRADE_PRICES = {
    "throttle": {2: 120, 3: 300, 4: 650},
    "brake": {2: 100, 3: 250, 4: 550}
}

active_garage_tab = "PAINTS"

def load_single_frame_png(filename, target_w, target_h, fallback_filename=None):
    if fallback_filename is None:
        fallback_filename = get_asset_path("assets/frame_rider.png")
    try:
        surf = pygame.image.load(filename).convert_alpha()
        return pygame.transform.scale(surf, (target_w, target_h))
    except Exception:
        try:
            surf = pygame.image.load(fallback_filename).convert_alpha()
            return pygame.transform.scale(surf, (target_w, target_h))
        except Exception:
            surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (220, 50, 50), (40, 40, target_w - 80, 50), border_radius=8)
            return surf

frame_images_normal = {}
frame_images_seatstand = {}

def load_all_paint_assets():
    global frame_images_normal, frame_images_seatstand
    for item in PAINTS_CATALOG:
        pid = item["id"]
        frame_images_normal[pid] = load_single_frame_png(item["file"], FRAME_WIDTH, FRAME_HEIGHT)
        seatstand_file = item.get("file_seatstand", item["file"].replace(".png", "_seatstand.png"))
        try:
            surf = pygame.image.load(seatstand_file).convert_alpha()
            frame_images_seatstand[pid] = pygame.transform.scale(surf, (SEATSTAND_WIDTH, SEATSTAND_HEIGHT))
        except Exception:
            frame_images_seatstand[pid] = frame_images_normal[pid]

load_all_paint_assets()

def get_current_underglow_color():
    return UNDERGLOW_CATALOG[equipped_underglow]["color"]

def get_current_map():
    return MAPS_CATALOG[equipped_map]

def draw_camera_aesthetic_overlay(surface, lens_type):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    if lens_type == "NYC_NIGHT_LENS":
        pygame.draw.rect(overlay, (10, 20, 45, 25), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.rect(overlay, (0, 5, 18, 65), (0, 0, WINDOW_WIDTH, 70))
        pygame.draw.rect(overlay, (0, 5, 18, 50), (0, WINDOW_HEIGHT - 60, WINDOW_WIDTH, 60))
    elif lens_type == "SUNSET_AMBER_LENS":
        pygame.draw.rect(overlay, (255, 120, 20, 32), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.circle(overlay, (255, 180, 50, 40), (int(WINDOW_WIDTH // 2), 200), 300)
    elif lens_type == "CYBER_SCANLINE_LENS":
        pygame.draw.rect(overlay, (180, 0, 255, 22), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(overlay, (0, 240, 255, 18), (0, int(y)), (WINDOW_WIDTH, int(y)), 1)
    elif lens_type == "CHERRY_BLOOM_LENS":
        pygame.draw.rect(overlay, (255, 100, 170, 30), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.circle(overlay, (255, 220, 240, 45), (int(WINDOW_WIDTH // 2), 120), 280)
    elif lens_type == "CALIFORNIA_GOLDEN_LENS":
        pygame.draw.rect(overlay, (255, 160, 40, 35), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.circle(overlay, (255, 240, 150, 50), (int(WINDOW_WIDTH // 2), 280), 220, width=14)
        pygame.draw.circle(overlay, (255, 255, 220, 65), (int(WINDOW_WIDTH // 2 - 80), 160), 60)
    elif lens_type == "ALPINE_FROST_LENS":
        pygame.draw.rect(overlay, (160, 220, 255, 28), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.circle(overlay, (255, 255, 255, 35), (int(WINDOW_WIDTH // 2), 100), 320)
    elif lens_type == "VOLCANIC_GLOW_LENS":
        pygame.draw.rect(overlay, (255, 50, 10, 40), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.circle(overlay, (255, 140, 20, 45), (int(WINDOW_WIDTH // 2), 250), 350)
    surface.blit(overlay, (0, 0))

# =========================================================================
# 3. AXLE ORIGIN & BIKE GEOMETRY
# =========================================================================
REAR_AXLE_X_RATIO = 0.08   
REAR_AXLE_Y_RATIO = 0.82   
FRONT_AXLE_X_RATIO = 0.76  
FRONT_AXLE_Y_RATIO = 0.82  

REAR_AXLE_ORIGIN = pygame.math.Vector2(FRAME_WIDTH * REAR_AXLE_X_RATIO, FRAME_HEIGHT * REAR_AXLE_Y_RATIO)
FRONT_AXLE_ORIGIN = pygame.math.Vector2(FRAME_WIDTH * FRONT_AXLE_X_RATIO, FRAME_HEIGHT * FRONT_AXLE_Y_RATIO)
AXLE_OFFSET_VECTOR = FRONT_AXLE_ORIGIN - REAR_AXLE_ORIGIN

SEATSTAND_REAR_AXLE_X_RATIO = 0.18   
SEATSTAND_REAR_AXLE_Y_RATIO = 0.82   
SEATSTAND_FRONT_AXLE_X_RATIO = 0.90  
SEATSTAND_FRONT_AXLE_Y_RATIO = 0.82  

SEATSTAND_REAR_AXLE_ORIGIN = pygame.math.Vector2(SEATSTAND_WIDTH * SEATSTAND_REAR_AXLE_X_RATIO, SEATSTAND_HEIGHT * SEATSTAND_REAR_AXLE_Y_RATIO)
SEATSTAND_FRONT_AXLE_ORIGIN = pygame.math.Vector2(SEATSTAND_WIDTH * SEATSTAND_FRONT_AXLE_X_RATIO, SEATSTAND_HEIGHT * SEATSTAND_FRONT_AXLE_Y_RATIO)
SEATSTAND_AXLE_OFFSET_VECTOR = SEATSTAND_FRONT_AXLE_ORIGIN - SEATSTAND_REAR_AXLE_ORIGIN

rear_susp_comp = 0.0
rear_susp_vel = 0.0
front_susp_comp = 0.0
front_susp_vel = 0.0

SUSP_K = 240.0
SUSP_C = 16.0
MAX_SUSP_COMP = 18.0

active_stance = "SEATED"
previous_stance = "SEATED"
combo_multiplier = 1.0
wheelie_combo_timer = 0.0

game_state = "MENU"
previous_state_before_settings = "MENU"
confirm_reset_active = False

wheelie_distance = 0.0
session_cash_earned = 0
scrape_cash_earned = 0.0

pivot_x = 300
pivot_y = GROUND_Y - (REAR_WHEEL_SIZE // 2)
world_offset = 0.0

angle = 0.0
angular_velocity = 0.0
speed = 0.0
wheel_spin = 0.0

throttle_timer = 0.0
brake_timer = 0.0

shake_timer = 0
shake_intensity = 0.0
camera_y_offset = 0.0

sparks = []
splashes = []
floating_popups = []

# Menu Hitboxes
play_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, 155, 190, 48)
garage_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 95, 155, 190, 48)
settings_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 + 130, 155, 190, 48)

tab_paints_rect = pygame.Rect(40, 110, 205, 42)
tab_underglow_rect = pygame.Rect(265, 110, 205, 42)
tab_maps_rect = pygame.Rect(490, 110, 205, 42)
tab_upgrades_rect = pygame.Rect(715, 110, 245, 42)

garage_back_rect = pygame.Rect(40, 30, 130, 40)
settings_back_rect = pygame.Rect(40, 30, 130, 40)

# Settings Controls
sfx_minus_rect = pygame.Rect(440, 160, 44, 44)
sfx_plus_rect = pygame.Rect(660, 160, 44, 44)
music_minus_rect = pygame.Rect(440, 230, 44, 44)
music_plus_rect = pygame.Rect(660, 230, 44, 44)
reset_data_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 325, 300, 48)

confirm_yes_rect = pygame.Rect(WINDOW_WIDTH // 2 - 130, 280, 120, 42)
confirm_no_rect = pygame.Rect(WINDOW_WIDTH // 2 + 10, 280, 120, 42)

# Pause Menu Controls
pause_resume_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 150, 280, 48)
pause_restart_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 215, 280, 48)
pause_settings_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 280, 280, 48)
pause_menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 345, 280, 48)

def trigger_screen_shake(intensity, duration):
    global shake_intensity, shake_timer
    shake_intensity = max(shake_intensity, intensity)
    shake_timer = duration

def add_floating_popup(text, color, x=WINDOW_WIDTH // 2, y=140):
    floating_popups.append({
        'x': float(x), 'y': float(y), 'text': text, 'color': color, 'life': 1.0, 'vy': -1.2
    })

def rotate_around_pivot(surface, image, angle, pivot, origin):
    image_rect = image.get_rect(topleft=(int(pivot[0] - origin.x), int(pivot[1] - origin.y)))
    offset = pygame.math.Vector2(pivot) - image_rect.center
    rotated_offset = offset.rotate(-angle)
    rect = image.get_rect(center=pygame.math.Vector2(pivot) - rotated_offset)
    rotated_image = pygame.transform.rotate(image, angle)
    rect = rotated_image.get_rect(center=(int(rect.centerx), int(rect.centery)))
    surface.blit(rotated_image, rect)

def draw_suspension_hardware(surface, rear_axle_pos, frame_rear_mount, front_axle_pos, frame_front_mount):
    rear_vec = frame_rear_mount - rear_axle_pos
    dist_rear = rear_vec.length()
    if dist_rear > 0:
        dir_rear = rear_vec.normalize()
        pygame.draw.line(surface, (50, 55, 65), (int(rear_axle_pos.x), int(rear_axle_pos.y)), (int(frame_rear_mount.x), int(frame_rear_mount.y)), 6)
        pygame.draw.line(surface, (180, 190, 200), (int(rear_axle_pos.x), int(rear_axle_pos.y)), (int(frame_rear_mount.x), int(frame_rear_mount.y)), 2)
        num_coils = 5
        for c in range(num_coils):
            t1 = c / float(num_coils)
            t2 = (c + 0.5) / float(num_coils)
            p1 = rear_axle_pos + dir_rear * (t1 * dist_rear)
            p2 = rear_axle_pos + dir_rear * (t2 * dist_rear)
            perp = pygame.math.Vector2(-dir_rear.y, dir_rear.x) * 4.5
            p1_p = p1 + perp
            p2_m = p2 - perp
            pygame.draw.line(surface, COLOR_WHITE, (int(p1_p.x), int(p1_p.y)), (int(p2_m.x), int(p2_m.y)), 3)

    front_vec = frame_front_mount - front_axle_pos
    dist_front = front_vec.length()
    if dist_front > 0:
        dir_front = front_vec.normalize()
        lower_end = front_axle_pos + dir_front * (dist_front * 0.52)
        pygame.draw.line(surface, (25, 30, 40), (int(front_axle_pos.x), int(front_axle_pos.y)), (int(lower_end.x), int(lower_end.y)), 8)
        pygame.draw.line(surface, (210, 220, 235), (int(lower_end.x), int(lower_end.y)), (int(frame_front_mount.x), int(frame_front_mount.y)), 5)
        pygame.draw.line(surface, (255, 255, 255), (int(lower_end.x), int(lower_end.y)), (int(frame_front_mount.x), int(frame_front_mount.y)), 2)

def reset_game():
    global angle, angular_velocity, speed, world_offset, wheel_spin
    global shake_timer, shake_intensity, camera_y_offset, wheelie_distance, game_state
    global throttle_timer, brake_timer, sparks, splashes, session_cash_earned, scrape_cash_earned
    global wheelie_combo_timer, combo_multiplier, active_stance, previous_stance
    global rear_susp_comp, rear_susp_vel, front_susp_comp, front_susp_vel

    angle = 0.0
    angular_velocity = 0.0
    speed = 0.0
    wheel_spin = 0.0
    world_offset = 0.0
    wheelie_distance = 0.0
    session_cash_earned = 0
    scrape_cash_earned = 0.0
    wheelie_combo_timer = 0.0
    combo_multiplier = 1.0
    active_stance = "SEATED"
    previous_stance = "SEATED"

    throttle_timer = 0.0
    brake_timer = 0.0
    shake_timer = 0
    shake_intensity = 0.0
    camera_y_offset = 0.0
    rear_susp_comp = 0.0
    rear_susp_vel = 0.0
    front_susp_comp = 0.0
    front_susp_vel = 0.0
    sparks.clear()
    splashes.clear()
    smoke_particles.clear()
    floating_popups.clear()
    load_all_paint_assets()
    game_state = "PLAYING"

def draw_forza_speedometer(surface, current_speed, max_speed, current_angle, score):
    center_x = WINDOW_WIDTH - 120
    center_y = WINDOW_HEIGHT - 110
    radius = 80

    draw_glass_box(surface, pygame.Rect(center_x - 95, center_y - 95, 190, 190), bg_color=(15, 18, 24, 180), border_color=GLASS_BORDER_HI, border_radius=95, border_width=2)

    start_angle = 135
    total_span = 270
    speed_ratio = min(1.0, current_speed / max_speed)
    active_span = speed_ratio * total_span

    for i in range(19):
        tick_ratio = i / 18.0
        tick_deg = start_angle + tick_ratio * total_span
        tick_rad = math.radians(tick_deg)
        inner_r = radius - 8
        outer_r = radius + (4 if i % 3 == 0 else 0)
        x1 = center_x + inner_r * math.cos(tick_rad)
        y1 = center_y + inner_r * math.sin(tick_rad)
        x2 = center_x + outer_r * math.cos(tick_rad)
        y2 = center_y + outer_r * math.sin(tick_rad)
        color = COLOR_WHITE if tick_ratio <= 0.85 else (200, 200, 200)
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(surface, color, (int(x1), int(y1)), (int(x2), int(y2)), thickness)

    if active_span > 0:
        arc_rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
        arc_start_rad = math.radians(- (start_angle + active_span))
        arc_end_rad = math.radians(-start_angle)
        pygame.draw.arc(surface, COLOR_WHITE, arc_rect, arc_start_rad, arc_end_rad, 5)

    gear = max(1, min(6, int(speed_ratio * 5.9) + 1))
    mph_val = int(current_speed * 2.2)
    
    font_large = get_font("Helvetica", 42, bold=True)
    font_unit = get_font("Helvetica", 13, bold=True)
    font_gear = get_font("Helvetica", 24, bold=True)

    speed_txt = font_large.render(f"{mph_val}", True, COLOR_WHITE)
    unit_txt = font_unit.render("MPH", True, COLOR_TEXT_MUTED)
    gear_txt = font_gear.render(f"G{gear}", True, COLOR_WHITE)

    surface.blit(speed_txt, (center_x - speed_txt.get_width() // 2, center_y - 28))
    surface.blit(unit_txt, (center_x - unit_txt.get_width() // 2, center_y + 18))
    surface.blit(gear_txt, (center_x - 65, center_y + 35))

    draw_glass_box(surface, pygame.Rect(20, 20, 360, 110), bg_color=(15, 18, 24, 180), border_color=GLASS_BORDER_HI, border_radius=18, border_width=2)

    font_hud = get_font("Helvetica", 13, bold=True)
    cur_map_name = get_current_map()["name"]
    dist_txt = font_hud.render(f"MAP: {cur_map_name.upper()}", True, COLOR_WHITE)
    live_cash_preview = int(total_cash + (score * 0.1) + scrape_cash_earned)
    cash_txt = font_hud.render(f"DISTANCE: {int(score)} m   |   ${live_cash_preview}", True, COLOR_TEXT_MUTED)
    
    if active_stance == "SEAT_STANDER":
        trick_str = f"SEAT STAND IMAGE SWAP! ({combo_multiplier:.1f}x)"
    elif current_angle > 85:
        trick_str = f"FENDER SCRAPE! (+${int(scrape_cash_earned)})"
    elif current_angle > 48:
        trick_str = f"SWEET SPOT WHEELIE! ({combo_multiplier:.1f}x)"
    else:
        trick_str = f"SEATED ROAD CRUISE"

    angle_txt = font_hud.render(trick_str, True, COLOR_WHITE)

    surface.blit(dist_txt, (36, 32))
    surface.blit(cash_txt, (36, 56))
    surface.blit(angle_txt, (36, 80))

# =========================================================================
# MAIN LOOP
# =========================================================================
while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()
    current_map = get_current_map()

    if game_state in ["MENU", "GARAGE"]:
        update_bg_music(MENU_MUSIC_FILE)
    elif game_state in ["PLAYING", "PAUSED", "GAMEOVER"]:
        update_bg_music(current_map.get("music", MENU_MUSIC_FILE))
    elif game_state == "SETTINGS":
        if previous_state_before_settings in ["MENU", "GARAGE"]:
            update_bg_music(MENU_MUSIC_FILE)
        else:
            update_bg_music(current_map.get("music", MENU_MUSIC_FILE))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game_data()
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if confirm_reset_active:
                if confirm_yes_rect.collidepoint(event.pos):
                    play_sfx(sound_click)
                    reset_all_data_defaults()
                    confirm_reset_active = False
                elif confirm_no_rect.collidepoint(event.pos):
                    play_sfx(sound_click)
                    confirm_reset_active = False
                continue

            if game_state == "MENU":
                if play_btn_rect.collidepoint(event.pos):
                    play_sfx(sound_click)
                    reset_game()
                elif garage_btn_rect.collidepoint(event.pos):
                    play_sfx(sound_click)
                    game_state = "GARAGE"
                elif settings_btn_rect.collidepoint(event.pos):
                    play_sfx(sound_click)
                    previous_state_before_settings = "MENU"
                    game_state = "SETTINGS"

            elif game_state == "GARAGE":
                if garage_back_rect.collidepoint(event.pos):
                    play_sfx(sound_click)
                    save_game_data()
                    game_state = "MENU"
                elif tab_paints_rect.collidepoint(event.pos):
                    play_sfx(sound_click); active_garage_tab = "PAINTS"
                elif tab_underglow_rect.collidepoint(event.pos):
                    play_sfx(sound_click); active_garage_tab = "UNDERGLOW"
                elif tab_maps_rect.collidepoint(event.pos):
                    play_sfx(sound_click); active_garage_tab = "MAPS"
                elif tab_upgrades_rect.collidepoint(event.pos):
                    play_sfx(sound_click); active_garage_tab = "UPGRADES"
                else:
                    if active_garage_tab == "PAINTS":
                        for idx, item in enumerate(PAINTS_CATALOG):
                            card_rect = pygame.Rect(50 + idx * 175, 180, 160, 240)
                            if card_rect.collidepoint(event.pos):
                                if item["id"] in owned_paints:
                                    equipped_paint = item["id"]; play_sfx(sound_click); save_game_data()
                                elif total_cash >= item["price"]:
                                    total_cash -= item["price"]; owned_paints.append(item["id"])
                                    equipped_paint = item["id"]; play_sfx(sound_click); save_game_data()

                    elif active_garage_tab == "UNDERGLOW":
                        for idx, item in enumerate(UNDERGLOW_CATALOG):
                            card_rect = pygame.Rect(50 + idx * 175, 180, 160, 240)
                            if card_rect.collidepoint(event.pos):
                                if item["id"] in owned_underglows:
                                    equipped_underglow = item["id"]; play_sfx(sound_click); save_game_data()
                                elif total_cash >= item["price"]:
                                    total_cash -= item["price"]; owned_underglows.append(item["id"])
                                    equipped_underglow = item["id"]; play_sfx(sound_click); save_game_data()

                    elif active_garage_tab == "MAPS":
                        for idx, item in enumerate(MAPS_CATALOG):
                            col = idx % 4
                            row = idx // 4
                            card_rect = pygame.Rect(35 + col * 235, 170 + row * 135, 220, 125)
                            if card_rect.collidepoint(event.pos):
                                if item["id"] in owned_maps:
                                    equipped_map = item["id"]; play_sfx(sound_click); save_game_data()
                                elif total_cash >= item["price"]:
                                    total_cash -= item["price"]; owned_maps.append(item["id"])
                                    equipped_map = item["id"]; play_sfx(sound_click); save_game_data()

                    elif active_garage_tab == "UPGRADES":
                        t_card = pygame.Rect(120, 180, 340, 240)
                        if t_card.collidepoint(event.pos):
                            nxt = throttle_level + 1
                            if nxt <= 4 and total_cash >= UPGRADE_PRICES["throttle"][nxt]:
                                total_cash -= UPGRADE_PRICES["throttle"][nxt]; throttle_level = nxt
                                play_sfx(sound_click); save_game_data()

                        b_card = pygame.Rect(540, 180, 340, 240)
                        if b_card.collidepoint(event.pos):
                            nxt = brake_level + 1
                            if nxt <= 4 and total_cash >= UPGRADE_PRICES["brake"][nxt]:
                                total_cash -= UPGRADE_PRICES["brake"][nxt]; brake_level = nxt
                                play_sfx(sound_click); save_game_data()

            elif game_state == "PAUSED":
                if pause_resume_rect.collidepoint(event.pos):
                    play_sfx(sound_click); game_state = "PLAYING"
                elif pause_restart_rect.collidepoint(event.pos):
                    play_sfx(sound_click); reset_game()
                elif pause_settings_rect.collidepoint(event.pos):
                    play_sfx(sound_click); previous_state_before_settings = "PAUSED"; game_state = "SETTINGS"
                elif pause_menu_rect.collidepoint(event.pos):
                    play_sfx(sound_click); save_game_data(); game_state = "MENU"

            elif game_state == "SETTINGS":
                if settings_back_rect.collidepoint(event.pos):
                    play_sfx(sound_click); save_game_data(); game_state = previous_state_before_settings
                elif sfx_minus_rect.collidepoint(event.pos):
                    sfx_volume = max(0.0, round(sfx_volume - 0.1, 1)); play_sfx(sound_click)
                elif sfx_plus_rect.collidepoint(event.pos):
                    sfx_volume = min(1.0, round(sfx_volume + 0.1, 1)); play_sfx(sound_click)
                elif music_minus_rect.collidepoint(event.pos):
                    music_volume = max(0.0, round(music_volume - 0.1, 1)); play_sfx(sound_click)
                    if music_channel and active_music_sound: music_channel.set_volume(music_volume)
                    else: pygame.mixer.music.set_volume(music_volume)
                elif music_plus_rect.collidepoint(event.pos):
                    music_volume = min(1.0, round(music_volume + 0.1, 1)); play_sfx(sound_click)
                    if music_channel and active_music_sound: music_channel.set_volume(music_volume)
                    else: pygame.mixer.music.set_volume(music_volume)
                elif reset_data_rect.collidepoint(event.pos):
                    play_sfx(sound_click); confirm_reset_active = True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if confirm_reset_active:
                    confirm_reset_active = False
                elif game_state == "PLAYING":
                    game_state = "PAUSED"
                elif game_state == "PAUSED":
                    game_state = "PLAYING"
                elif game_state == "SETTINGS":
                    game_state = previous_state_before_settings
                elif game_state == "GARAGE":
                    save_game_data(); game_state = "MENU"
            elif game_state == "MENU":
                if event.key in [pygame.K_RETURN, pygame.K_SPACE]: reset_game()
                elif event.key == pygame.K_g: game_state = "GARAGE"
                elif event.key == pygame.K_s: previous_state_before_settings = "MENU"; game_state = "SETTINGS"
            elif game_state == "GAMEOVER":
                if event.key in [pygame.K_RETURN, pygame.K_SPACE]: reset_game()
                elif event.key == pygame.K_ESCAPE: game_state = "MENU"

    # Input Mapping: Dual Gamepad & Keyboard Controls
    keys = pygame.key.get_pressed()
    joy_throttle, joy_brake, joy_pitch, joy_stance = False, False, False, False

    if joysticks:
        try:
            j = joysticks[0]
            axis_y = j.get_axis(1)
            axis_x = j.get_axis(0)
            btn_a = j.get_button(0) if j.get_numbuttons() > 0 else 0
            btn_b = j.get_button(1) if j.get_numbuttons() > 1 else 0
            btn_rb = j.get_button(5) if j.get_numbuttons() > 5 else 0

            if axis_y < -0.3 or btn_a: joy_throttle = True
            if axis_y > 0.3 or btn_b: joy_brake = True
            if axis_x < -0.3: joy_pitch = True
            if btn_rb: joy_stance = True
        except Exception:
            pass

    accel_mult = 1.0 + (throttle_level - 1) * 0.20
    brake_mult = 1.0 + (brake_level - 1) * 0.22
    max_physical_speed = 27.5 + (throttle_level - 1) * 2.5

    # GAMEPLAY LOGIC & PHYSICAL 60 MPH SPEED TUNING
    if game_state == "PLAYING":
        prev_angle = angle
        prev_angular_velocity = angular_velocity

        is_w_pressed = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_RIGHT] or keys[pygame.K_d] or joy_throttle
        is_space_pressed = keys[pygame.K_SPACE] or joy_pitch
        is_braking = keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_a] or joy_brake
        is_shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_e] or joy_stance

        if is_shift_pressed and angle > 15.0:
            new_stance = "SEAT_STANDER"
        else:
            new_stance = "SEATED"

        if new_stance != active_stance:
            previous_stance = active_stance
            active_stance = new_stance
            if active_stance == "SEAT_STANDER":
                add_floating_popup("SEAT STANDER SPRITE SWAP!", COLOR_WHITE, pivot_x, 140)

        if is_w_pressed:
            throttle_timer += dt
            power_surge = 1.0 if throttle_timer < 0.3 else min(1.85, 1.0 + (throttle_timer - 0.3) * 2.2)
            base_accel = 0.32 * power_surge * accel_mult
            lift_modifier = 0.42 if active_stance == "SEAT_STANDER" else 0.38
            base_lift = lift_modifier * power_surge * accel_mult

            if is_space_pressed:
                speed = min(speed + base_accel * 1.15, max_physical_speed)
                angular_velocity = max(-0.5, angular_velocity - 0.25)
            else:
                speed = min(speed + base_accel, max_physical_speed)
                angular_velocity += base_lift
        else:
            throttle_timer = 0.0
            speed = max(0.0, speed - 0.025)

        if is_space_pressed and not is_w_pressed:
            angular_velocity += 0.45

        if is_braking:
            brake_timer += dt
            brake_ratio = min(1.0, brake_timer / 0.8)
            brake_decel = (0.04 + 0.08 * brake_ratio) * brake_mult
            brake_down_torque = (0.38 + 0.55 * brake_ratio) * brake_mult
            speed = max(0.0, speed - brake_decel)
            angular_velocity -= brake_down_torque
        else:
            brake_timer = 0.0

        if angle > 0:
            sweet_spot = 55.0
            diff = angle - sweet_spot
            torque_dir = 1.0 if diff > 0 else -1.0
            angular_velocity += (abs(diff) / sweet_spot) * 0.10 * torque_dir

        angular_velocity *= 0.94
        angle += angular_velocity
        world_offset += speed
        wheel_spin = (wheel_spin + speed * 7) % 360

        rear_force = 0.0
        front_force = 0.0
        if is_w_pressed: rear_force += 110.0 * (speed / max_physical_speed + 0.5)
        if active_stance == "SEAT_STANDER": rear_force += 35.0
        if angle > 80.0: rear_force += (angle - 80.0) * 8.0
        if angle > 5.0: front_force -= 35.0
        
        if angle <= 0:
            if prev_angle > 2.0 and prev_angular_velocity < -0.4:
                slam_force = min(12.0, abs(prev_angular_velocity) * 8.0)
                trigger_screen_shake(intensity=slam_force, duration=8)
                play_sfx(sound_slam)
                add_floating_popup("FRONT SLAM!", COLOR_WHITE, pivot_x + 50, GROUND_Y - 40)
                front_force += slam_force * 180.0
            angle = 0
            if angular_velocity < 0: angular_velocity = 0

        rear_accel = rear_force - (SUSP_K * rear_susp_comp) - (SUSP_C * rear_susp_vel)
        rear_susp_vel += rear_accel * dt
        rear_susp_comp = max(-4.0, min(MAX_SUSP_COMP, rear_susp_comp + rear_susp_vel * dt))

        front_accel = front_force - (SUSP_K * front_susp_comp) - (SUSP_C * front_susp_vel)
        front_susp_vel += front_accel * dt
        front_susp_comp = max(-6.0, min(MAX_SUSP_COMP, front_susp_comp + front_susp_vel * dt))

        if angle > 5.0:
            wheelie_distance += speed * 0.12 * combo_multiplier
            if wheelie_distance > high_score: high_score = wheelie_distance
            wheelie_combo_timer += dt

            if active_stance == "SEAT_STANDER":
                if wheelie_combo_timer >= 1.0 and combo_multiplier < 4.0:
                    combo_multiplier += 0.5; wheelie_combo_timer = 0.0
                    add_floating_popup(f"STANDER COMBO! {combo_multiplier:.1f}x", COLOR_WHITE, pivot_x, 150)
            elif 48.0 <= angle <= 65.0:
                if wheelie_combo_timer >= 1.4 and combo_multiplier < 3.0:
                    combo_multiplier += 0.5; wheelie_combo_timer = 0.0
                    add_floating_popup(f"SWEET SPOT COMBO! {combo_multiplier:.1f}x", COLOR_WHITE, pivot_x, 150)
        else:
            combo_multiplier = 1.0; wheelie_combo_timer = 0.0

        if angle >= 102.0:
            game_state = "GAMEOVER"
            dist_cash = int(wheelie_distance * 0.10)
            session_cash_earned = dist_cash + int(scrape_cash_earned)
            total_cash += session_cash_earned
            save_game_data()
            speed = 0
            trigger_screen_shake(intensity=16.0, duration=22)

    # Dynamic Camera & Shake
    target_cam_y = (angle / 102.0) * 38.0
    camera_y_offset += (target_cam_y - camera_y_offset) * 0.1

    shake_x, shake_y = 0, 0
    if shake_timer > 0:
        shake_x = random.randint(-int(shake_intensity), int(shake_intensity))
        shake_y = random.randint(-int(shake_intensity), int(shake_intensity))
        shake_intensity *= 0.86; shake_timer -= 1

    # RENDER WORLD & MAP
    sky_top = current_map["sky_top"]; sky_bot = current_map["sky_bottom"]
    for y in range(300):
        ratio = y / 300.0
        r = int(sky_top[0] * (1 - ratio) + sky_bot[0] * ratio)
        g = int(sky_top[1] * (1 - ratio) + sky_bot[1] * ratio)
        b = int(sky_top[2] * (1 - ratio) + sky_bot[2] * ratio)
        pygame.draw.line(window, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    if current_map.get("has_stars", False): window.blit(STARS_SURF, (0, 0))

    if speed > 5.0:
        for m in motion_lines:
            m['x'] -= speed * m['speed_mult'] * 2.2
            if m['x'] < -180: m['x'] = WINDOW_WIDTH + random.randint(10, 100); m['y'] = random.randint(80, GROUND_Y - 30)
            pygame.draw.line(window, (255, 255, 255, min(120, int(speed * 4))), (int(m['x']), int(m['y'])), (int(m['x'] + m['length'] * (speed / 16.0)), int(m['y'])), 1)

    if current_map.get("has_rain", False):
        for drop in rain_drops:
            drop['y'] += drop['speed']
            drop['x'] -= (speed * 0.35 + 2.0)
            if drop['y'] > WINDOW_HEIGHT: drop['y'] = random.randint(-20, 0); drop['x'] = random.randint(-50, WINDOW_WIDTH + 50)
            if drop['x'] < -50: drop['x'] = WINDOW_WIDTH + 50
            pygame.draw.line(window, (160, 220, 255, 110), (int(drop['x']), int(drop['y'])), (int(drop['x'] - 3), int(drop['y'] + drop['length'])), 1)

    if current_map.get("has_snow", False):
        for flake in snow_flakes:
            flake['y'] += flake['speed_y']
            flake['x'] -= (speed * 0.3 + flake['speed_x'])
            if flake['y'] > WINDOW_HEIGHT or flake['x'] < -20: flake['y'] = random.randint(-20, 0); flake['x'] = random.randint(0, WINDOW_WIDTH + 50)
            pygame.draw.circle(window, (240, 248, 255, 220), (int(flake['x']), int(flake['y'])), flake['size'])

    if current_map.get("has_embers", False):
        for emb in volcanic_embers:
            emb['x'] += emb['vx'] - (speed * 0.4)
            emb['y'] += emb['vy']
            if emb['y'] < -10 or emb['x'] < -20: emb['y'] = WINDOW_HEIGHT + random.randint(0, 20); emb['x'] = random.randint(0, WINDOW_WIDTH + 50)
            pygame.draw.circle(window, (*emb['color'], 210), (int(emb['x']), int(emb['y'])), int(emb['size']))

    if current_map.get("has_petals", False):
        for p in cherry_petals:
            p['y'] += p['speed_y']; p['x'] -= (speed * 0.4 + p['speed_x']); p['rot'] += 2.0
            if p['y'] > WINDOW_HEIGHT or p['x'] < -20: p['y'] = random.randint(-30, 0); p['x'] = random.randint(0, WINDOW_WIDTH + 60)
            petal_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.ellipse(petal_surf, (255, 170, 210, 220), (0, 0, int(p['size'] * 2), int(p['size'])))
            rot_p = pygame.transform.rotate(petal_surf, p['rot'])
            window.blit(rot_p, (int(p['x']), int(p['y'])))

    far_scroll = (world_offset * 0.15) % 1000
    window.blit(current_map["far_layer"], (int(-far_scroll), 80))
    window.blit(current_map["far_layer"], (int(-far_scroll + 1000), 80))

    near_scroll = (world_offset * 0.35) % 1000
    window.blit(current_map["near_layer"], (int(-near_scroll), 120))
    window.blit(current_map["near_layer"], (int(-near_scroll + 1000), 120))

    rendered_ground_y = int(GROUND_Y + camera_y_offset + shake_y)
    pygame.draw.rect(window, current_map["road_color"], (0, rendered_ground_y, WINDOW_WIDTH, WINDOW_HEIGHT - rendered_ground_y))
    dash_col = current_map["dash_color"]
    for x in range(int((-world_offset + shake_x) % 80), WINDOW_WIDTH, 80):
        pygame.draw.line(window, dash_col, (x, rendered_ground_y + 30), (x + 40, rendered_ground_y + 30), 4)

    if current_map.get("streetlights", False):
        lamp_col = current_map.get("lamp_color", (255, 240, 180))
        lamp_spacing = 380
        start_lamp_x = int((-world_offset + shake_x) % lamp_spacing)
        for lx in range(start_lamp_x - lamp_spacing, WINDOW_WIDTH + lamp_spacing, lamp_spacing):
            lamp_top_y = rendered_ground_y - 190
            pygame.draw.line(window, (45, 55, 70), (lx, rendered_ground_y), (lx, lamp_top_y), 9)
            pygame.draw.line(window, (65, 80, 100), (lx, lamp_top_y), (lx + 38, lamp_top_y), 6)
            pygame.draw.circle(window, lamp_col, (lx + 38, lamp_top_y + 6), 10)
            light_cone = pygame.Surface((220, 190), pygame.SRCALPHA)
            cone_pts = [(110, 0), (0, 190), (220, 190)]
            pygame.draw.polygon(light_cone, (*lamp_col, 42), cone_pts)
            window.blit(light_cone, (lx + 38 - 110, lamp_top_y + 6))

    if active_stance == "SEAT_STANDER":
        active_frame_img = frame_images_seatstand.get(equipped_paint, frame_images_normal[equipped_paint])
        active_rear_origin = SEATSTAND_REAR_AXLE_ORIGIN
        active_axle_offset = SEATSTAND_AXLE_OFFSET_VECTOR
    else:
        active_frame_img = frame_images_normal[equipped_paint]
        active_rear_origin = REAR_AXLE_ORIGIN
        active_axle_offset = AXLE_OFFSET_VECTOR

    rear_wheel_pos = pygame.math.Vector2(pivot_x + shake_x, rendered_ground_y - (REAR_WHEEL_SIZE // 2))
    susp_vector = pygame.math.Vector2(0, rear_susp_comp).rotate(-angle)
    frame_pivot_pos = rear_wheel_pos + susp_vector

    frame_front_mount = frame_pivot_pos + active_axle_offset.rotate(-angle)
    fork_dir = active_axle_offset.normalize()
    effective_fork_len = active_axle_offset.length() - front_susp_comp
    front_wheel_pos = frame_pivot_pos + (fork_dir * effective_fork_len).rotate(-angle)

    if game_state == "PLAYING":
        if is_w_pressed and random.random() < 0.35:
            smoke_particles.append({
                'x': rear_wheel_pos.x - 10, 'y': rear_wheel_pos.y + 15,
                'vx': -speed * 0.4 - random.uniform(1.0, 2.5), 'vy': random.uniform(-1.0, 0.5),
                'radius': random.uniform(4.0, 8.0), 'alpha': 170, 'color': (200, 205, 215), 'life': 1.0
            })
        if is_braking and speed > 2.0 and random.random() < 0.5:
            smoke_particles.append({
                'x': rear_wheel_pos.x, 'y': rendered_ground_y - 4,
                'vx': -speed * 0.6, 'vy': random.uniform(-1.5, -0.3),
                'radius': random.uniform(6.0, 12.0), 'alpha': 190, 'color': (230, 230, 240), 'life': 0.8
            })

    new_smoke = []
    for sm in smoke_particles:
        sm['x'] += sm['vx']; sm['y'] += sm['vy']; sm['life'] -= dt * 1.5
        sm['radius'] += dt * 8.0
        if sm['life'] > 0:
            new_smoke.append(sm)
            sm_surf = pygame.Surface((int(sm['radius'] * 2 + 2), int(sm['radius'] * 2 + 2)), pygame.SRCALPHA)
            pygame.draw.circle(sm_surf, (*sm['color'], int(sm['alpha'] * sm['life'])), (int(sm['radius'] + 1), int(sm['radius'] + 1)), int(sm['radius']))
            window.blit(sm_surf, (int(sm['x']), int(sm['y'])))
    smoke_particles = new_smoke

    ug_color = get_current_underglow_color()
    underglow_layer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    glow_x = rear_wheel_pos.x + 35
    glow_y = rendered_ground_y + 4
    glow_scale = 1.0 + (angle / 100.0) * 0.8
    pygame.draw.ellipse(underglow_layer, (*ug_color, int(45 * glow_scale)), (int(glow_x - 90 * glow_scale), int(glow_y - 12), int(180 * glow_scale), 24))
    window.blit(underglow_layer, (0, 0))

    if game_state == "PLAYING" and angle > 85.0:
        scrape_x = rear_wheel_pos.x - 12
        scrape_y = rendered_ground_y + 2
        trigger_screen_shake(intensity=1.5, duration=2)
        scrape_cash_earned += 0.05 * combo_multiplier
        if random.random() < 0.2: play_sfx(sound_scrape)

        for _ in range(random.randint(4, 9)):
            sparks.append({
                'x': scrape_x + random.uniform(-4, 4), 'y': scrape_y + random.uniform(-2, 2),
                'vx': random.uniform(-16.0, -5.0), 'vy': random.uniform(-7.0, -1.5),
                'size': random.uniform(2.5, 5.0),
                'color': random.choice([(255, 240, 150), (255, 180, 40), (255, 90, 0)]),
                'life': random.uniform(0.12, 0.35)
            })

    new_sparks = []
    for s in sparks:
        s['x'] += s['vx']; s['y'] += s['vy']; s['vy'] += 0.45; s['life'] -= dt
        s['size'] = max(0.5, s['size'] - dt * 6.0)
        if s['life'] > 0:
            new_sparks.append(s)
            spark_surf = pygame.Surface((int(s['size'] * 2 + 2), int(s['size'] * 2 + 2)), pygame.SRCALPHA)
            pygame.draw.circle(spark_surf, s['color'], (int(s['size'] + 1), int(s['size'] + 1)), int(s['size']))
            window.blit(spark_surf, (int(s['x']), int(s['y'])))
    sparks = new_sparks

    rotated_rear = pygame.transform.rotate(rear_wheel_img, -wheel_spin)

    # Expanded Motion Ghosting across high-speed thresholds
    if speed > 5.0:
        blur_amount = min(5, int((speed - 5.0) / 4.5) + 1)
        for g in range(1, blur_amount + 1):
            ghost_offset = g * (speed * 0.5)
            ghost_alpha = max(15, int(95 / (g * 1.4)))

            ghost_frame = active_frame_img.copy()
            ghost_frame.set_alpha(ghost_alpha)
            rotate_around_pivot(window, ghost_frame, angle, (frame_pivot_pos.x - ghost_offset, frame_pivot_pos.y), active_rear_origin)

            ghost_rear = rotated_rear.copy()
            ghost_rear.set_alpha(ghost_alpha)
            window.blit(ghost_rear, ghost_rear.get_rect(center=(int(rear_wheel_pos.x - ghost_offset), int(rear_wheel_pos.y))))

    window.blit(rotated_rear, rotated_rear.get_rect(center=(int(rear_wheel_pos.x), int(rear_wheel_pos.y))))
    rotate_around_pivot(window, active_frame_img, angle, (frame_pivot_pos.x, frame_pivot_pos.y), active_rear_origin)
    rotated_front = pygame.transform.rotate(front_wheel_img, -wheel_spin)
    window.blit(rotated_front, rotated_front.get_rect(center=(int(front_wheel_pos.x), int(front_wheel_pos.y))))

    draw_suspension_hardware(window, rear_wheel_pos, frame_pivot_pos, front_wheel_pos, frame_front_mount)
    draw_camera_aesthetic_overlay(window, current_map.get("lens_filter", "NYC_NIGHT_LENS"))

    new_popups = []
    for pop in floating_popups:
        pop['y'] += pop['vy']; pop['life'] -= dt * 1.2
        if pop['life'] > 0:
            new_popups.append(pop)
            pop_font = get_font("Helvetica", int(20 * (0.8 + (1.0 - pop['life']) * 0.4)), bold=True)
            txt_s = pop_font.render(pop['text'], True, pop['color'])
            txt_s.set_alpha(int(min(255, pop['life'] * 255)))
            window.blit(txt_s, (int(pop['x'] - txt_s.get_width() // 2), int(pop['y'])))
    floating_popups = new_popups

    # =========================================================================
    # iOS GLASS UI OVERLAYS & MENUS
    # =========================================================================
    if game_state == "PLAYING":
        draw_forza_speedometer(window, speed, max_physical_speed, angle, wheelie_distance)

    elif game_state == "PAUSED":
        draw_forza_speedometer(window, speed, max_physical_speed, angle, wheelie_distance)
        
        glass_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glass_overlay.fill((10, 12, 16, 180))
        window.blit(glass_overlay, (0, 0))

        p_modal = pygame.Rect(WINDOW_WIDTH // 2 - 180, 65, 360, 370)
        draw_glass_box(window, p_modal, bg_color=(255, 255, 255, 25), border_color=GLASS_BORDER_HI, border_radius=22)

        p_font = get_font("Helvetica", 36, bold=True)
        btn_font = get_font("Helvetica", 18, bold=True)
        p_txt = p_font.render("GAME PAUSED", True, COLOR_WHITE)
        window.blit(p_txt, (p_modal.centerx - p_txt.get_width() // 2, p_modal.y + 30))

        btns = [
            ("RESUME  [ESC]", pause_resume_rect),
            ("RESTART", pause_restart_rect),
            ("SETTINGS", pause_settings_rect),
            ("MAIN MENU", pause_menu_rect)
        ]

        for b_name, rect in btns:
            is_h = rect.collidepoint(mouse_pos)
            draw_glass_box(window, rect, 
                           bg_color=GLASS_BG_ACTIVE if is_h else GLASS_BG_CARD, 
                           border_color=COLOR_WHITE if is_h else GLASS_BORDER_SUBTLE, 
                           border_radius=14, border_width=2)
            t = btn_font.render(b_name, True, COLOR_TEXT_DARK if is_h else COLOR_WHITE)
            window.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    elif game_state == "MENU":
        glass_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glass_overlay.fill(GLASS_OVERLAY_DARK)
        window.blit(glass_overlay, (0, 0))

        title_font = get_font("Helvetica", 48, bold=True)
        sub_font = get_font("Helvetica", 15, bold=True)
        ctrl_font = get_font("Helvetica", 13)
        btn_font = get_font("Helvetica", 18, bold=True)

        header_rect = pygame.Rect(WINDOW_WIDTH // 2 - 280, 25, 560, 100)
        draw_glass_box(window, header_rect, bg_color=(255, 255, 255, 15), border_color=GLASS_BORDER_HI, border_radius=22)

        title_txt = title_font.render("SOFLOW WHEELIE LIFE", True, COLOR_WHITE)
        high_txt = sub_font.render(f"BEST: {int(high_score)} m   •   CASH: ${int(total_cash)}   •   MAP: {current_map['name']}", True, COLOR_TEXT_MUTED)

        window.blit(title_txt, (header_rect.centerx - title_txt.get_width() // 2, header_rect.y + 16))
        window.blit(high_txt, (header_rect.centerx - high_txt.get_width() // 2, header_rect.y + 66))

        menu_btns = [("PLAY  [ENTER]", play_btn_rect), ("GARAGE  [G]", garage_btn_rect), ("SETTINGS  [S]", settings_btn_rect)]
        for b_title, rect in menu_btns:
            is_hover = rect.collidepoint(mouse_pos)
            draw_glass_box(window, rect, 
                           bg_color=GLASS_BG_ACTIVE if is_hover else GLASS_BG_CARD, 
                           border_color=COLOR_WHITE if is_hover else GLASS_BORDER_SUBTLE, 
                           border_radius=16, border_width=2)
            b_txt = btn_font.render(b_title, True, COLOR_TEXT_DARK if is_hover else COLOR_WHITE)
            window.blit(b_txt, (rect.centerx - b_txt.get_width() // 2, rect.centery - b_txt.get_height() // 2))

        box_rect = pygame.Rect(WINDOW_WIDTH // 2 - 270, 230, 540, 230)
        draw_glass_box(window, box_rect, bg_color=(255, 255, 255, 14), border_color=GLASS_BORDER_SUBTLE, border_radius=20)

        joy_status = f"Gamepad Connected: {joysticks[0].get_name()}" if joysticks else "Gamepad: Disconnected (Plug in USB/Bluetooth controller)"

        c1 = ctrl_font.render("[ W ] / [ UP ]: Throttle Boost   •   [ SPACE ]: Pitch Wheelie Up", True, COLOR_WHITE)
        c2 = ctrl_font.render("[ S ] / [ DOWN ]: Rear Brake Tap   •   [ ESC ]: Pause Menu", True, COLOR_WHITE)
        c3 = ctrl_font.render("[ SHIFT ] / [ E ]: Hold Seat Stander (Swaps to Seat Stand PNG!)", True, COLOR_WHITE)
        c4 = ctrl_font.render(f"Gamepad: {joy_status}", True, COLOR_TEXT_MUTED)
        c5 = ctrl_font.render("Speed Engine Calibrated to 60+ MPH True World Velocity", True, COLOR_WHITE)

        window.blit(c1, (box_rect.x + 24, box_rect.y + 24))
        window.blit(c2, (box_rect.x + 24, box_rect.y + 60))
        window.blit(c3, (box_rect.x + 24, box_rect.y + 96))
        window.blit(c4, (box_rect.x + 24, box_rect.y + 138))
        window.blit(c5, (box_rect.x + 24, box_rect.y + 172))

    elif game_state == "SETTINGS":
        glass_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glass_overlay.fill((8, 10, 14, 235))
        window.blit(glass_overlay, (0, 0))

        title_font = get_font("Helvetica", 28, bold=True)
        lbl_font = get_font("Helvetica", 18, bold=True)
        btn_font = get_font("Helvetica", 16, bold=True)

        is_back_hover = settings_back_rect.collidepoint(mouse_pos)
        draw_glass_box(window, settings_back_rect, bg_color=GLASS_BG_CARD_HOVER if is_back_hover else GLASS_BG_CARD, border_color=GLASS_BORDER_HI if is_back_hover else GLASS_BORDER_SUBTLE, border_radius=12)
        back_txt = btn_font.render("< BACK", True, COLOR_WHITE)
        window.blit(back_txt, (settings_back_rect.centerx - back_txt.get_width() // 2, settings_back_rect.centery - back_txt.get_height() // 2))

        s_title = title_font.render("AUDIO & GAME SETTINGS", True, COLOR_WHITE)
        window.blit(s_title, (190, 34))

        panel_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, 110, 640, 330)
        draw_glass_box(window, panel_rect, bg_color=GLASS_BG_CARD, border_color=GLASS_BORDER_SUBTLE, border_radius=20)

        sfx_lbl = lbl_font.render(f"SFX VOLUME: {int(sfx_volume * 100)}%", True, COLOR_WHITE)
        window.blit(sfx_lbl, (panel_rect.x + 40, 170))
        
        draw_glass_box(window, sfx_minus_rect, bg_color=GLASS_BG_CARD_HOVER if sfx_minus_rect.collidepoint(mouse_pos) else GLASS_BG_CARD, border_radius=10)
        draw_glass_box(window, sfx_plus_rect, bg_color=GLASS_BG_CARD_HOVER if sfx_plus_rect.collidepoint(mouse_pos) else GLASS_BG_CARD, border_radius=10)
        window.blit(lbl_font.render("-", True, COLOR_WHITE), (sfx_minus_rect.centerx - 5, sfx_minus_rect.centery - 12))
        window.blit(lbl_font.render("+", True, COLOR_WHITE), (sfx_plus_rect.centerx - 6, sfx_plus_rect.centery - 12))

        mus_lbl = lbl_font.render(f"MUSIC VOLUME: {int(music_volume * 100)}%", True, COLOR_WHITE)
        window.blit(mus_lbl, (panel_rect.x + 40, 240))

        draw_glass_box(window, music_minus_rect, bg_color=GLASS_BG_CARD_HOVER if music_minus_rect.collidepoint(mouse_pos) else GLASS_BG_CARD, border_radius=10)
        draw_glass_box(window, music_plus_rect, bg_color=GLASS_BG_CARD_HOVER if music_plus_rect.collidepoint(mouse_pos) else GLASS_BG_CARD, border_radius=10)
        window.blit(lbl_font.render("-", True, COLOR_WHITE), (music_minus_rect.centerx - 5, music_minus_rect.centery - 12))
        window.blit(lbl_font.render("+", True, COLOR_WHITE), (music_plus_rect.centerx - 6, music_plus_rect.centery - 12))

        is_reset_h = reset_data_rect.collidepoint(mouse_pos)
        draw_glass_box(window, reset_data_rect, 
                       bg_color=(220, 60, 60, 120) if is_reset_h else (220, 60, 60, 45), 
                       border_color=COLOR_DANGER if is_reset_h else (220, 60, 60, 120), 
                       border_radius=14, border_width=2)
        r_txt = btn_font.render("RESET SAVE & DATA PROGRESS", True, COLOR_WHITE)
        window.blit(r_txt, (reset_data_rect.centerx - r_txt.get_width() // 2, reset_data_rect.centery - r_txt.get_height() // 2))

        if confirm_reset_active:
            dialog_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            dialog_overlay.fill((0, 0, 0, 180))
            window.blit(dialog_overlay, (0, 0))

            dialog_rect = pygame.Rect(WINDOW_WIDTH // 2 - 220, 140, 440, 220)
            draw_glass_box(window, dialog_rect, bg_color=(20, 24, 32, 245), border_color=GLASS_BORDER_HI, border_radius=20)

            c_font = get_font("Helvetica", 18, bold=True)
            cs_font = get_font("Helvetica", 13)
            
            c_head = c_font.render("CONFIRM DATA RESET", True, COLOR_DANGER)
            c_msg = cs_font.render("Are you sure? This will wipe cash, paints, maps & upgrades!", True, COLOR_TEXT_MUTED)

            window.blit(c_head, (dialog_rect.centerx - c_head.get_width() // 2, dialog_rect.y + 30))
            window.blit(c_msg, (dialog_rect.centerx - c_msg.get_width() // 2, dialog_rect.y + 70))

            is_y_h = confirm_yes_rect.collidepoint(mouse_pos)
            draw_glass_box(window, confirm_yes_rect, bg_color=(220, 60, 60, 220) if is_y_h else (220, 60, 60, 100), border_radius=10)
            y_t = btn_font.render("YES, RESET", True, COLOR_WHITE)
            window.blit(y_t, (confirm_yes_rect.centerx - y_t.get_width() // 2, confirm_yes_rect.centery - y_t.get_height() // 2))

            is_n_h = confirm_no_rect.collidepoint(mouse_pos)
            draw_glass_box(window, confirm_no_rect, bg_color=GLASS_BG_ACTIVE if is_n_h else GLASS_BG_CARD, border_radius=10)
            n_t = btn_font.render("CANCEL", True, COLOR_TEXT_DARK if is_n_h else COLOR_WHITE)
            window.blit(n_t, (confirm_no_rect.centerx - n_t.get_width() // 2, confirm_no_rect.centery - n_t.get_height() // 2))

    elif game_state == "GARAGE":
        glass_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glass_overlay.fill((8, 10, 14, 235))
        window.blit(glass_overlay, (0, 0))

        title_font = get_font("Helvetica", 28, bold=True)
        hud_font = get_font("Helvetica", 15, bold=True)
        item_title_font = get_font("Helvetica", 13, bold=True)
        btn_font = get_font("Helvetica", 15, bold=True)

        is_back_hover = garage_back_rect.collidepoint(mouse_pos)
        draw_glass_box(window, garage_back_rect, bg_color=GLASS_BG_CARD_HOVER if is_back_hover else GLASS_BG_CARD, border_color=GLASS_BORDER_HI if is_back_hover else GLASS_BORDER_SUBTLE, border_radius=12)
        back_txt = hud_font.render("< BACK", True, COLOR_WHITE)
        window.blit(back_txt, (garage_back_rect.centerx - back_txt.get_width() // 2, garage_back_rect.centery - back_txt.get_height() // 2))

        g_title = title_font.render("GARAGE & CUSTOM SHOP", True, COLOR_WHITE)
        cash_hdr = hud_font.render(f"CASH: ${int(total_cash)}", True, COLOR_TEXT_MUTED)
        window.blit(g_title, (190, 34))
        window.blit(cash_hdr, (WINDOW_WIDTH - 180, 40))

        tabs = [("PAINTS", tab_paints_rect), ("UNDERGLOW", tab_underglow_rect), ("MAPS", tab_maps_rect), ("UPGRADES", tab_upgrades_rect)]
        for tab_name, rect in tabs:
            is_active = (active_garage_tab == tab_name)
            is_hover = rect.collidepoint(mouse_pos)
            draw_glass_box(window, rect, 
                           bg_color=GLASS_BG_ACTIVE if is_active else (GLASS_BG_CARD_HOVER if is_hover else GLASS_BG_CARD), 
                           border_color=COLOR_WHITE if (is_active or is_hover) else GLASS_BORDER_SUBTLE, 
                           border_radius=14)
            t_txt = btn_font.render(tab_name, True, COLOR_TEXT_DARK if is_active else COLOR_WHITE)
            window.blit(t_txt, (rect.centerx - t_txt.get_width() // 2, rect.centery - t_txt.get_height() // 2))

        if active_garage_tab == "PAINTS":
            for idx, item in enumerate(PAINTS_CATALOG):
                card_rect = pygame.Rect(50 + idx * 175, 180, 160, 240)
                is_owned = item["id"] in owned_paints; is_eq = (equipped_paint == item["id"]); is_hover = card_rect.collidepoint(mouse_pos)
                draw_glass_box(window, card_rect, bg_color=(255, 255, 255, 35) if is_hover else GLASS_BG_CARD, border_color=COLOR_WHITE if is_eq else (GLASS_BORDER_HI if is_hover else GLASS_BORDER_SUBTLE), border_radius=16)

                preview_rect = pygame.Rect(card_rect.x + 20, card_rect.y + 20, 120, 70)
                pygame.draw.rect(window, item["hud_color"], preview_rect, border_radius=10)
                pygame.draw.rect(window, COLOR_WHITE, preview_rect, width=1, border_radius=10)
                name_txt = item_title_font.render(item["name"], True, COLOR_WHITE)
                window.blit(name_txt, (card_rect.centerx - name_txt.get_width() // 2, card_rect.y + 105))

                btn_box = pygame.Rect(card_rect.x + 15, card_rect.y + 175, 130, 40)
                if is_eq:
                    draw_glass_box(window, btn_box, bg_color=GLASS_BG_ACTIVE, border_color=COLOR_WHITE, border_radius=10)
                    b_txt = hud_font.render("EQUIPPED", True, COLOR_TEXT_DARK)
                elif is_owned:
                    draw_glass_box(window, btn_box, bg_color=(255, 255, 255, 45), border_color=GLASS_BORDER_HI, border_radius=10)
                    b_txt = hud_font.render("EQUIP", True, COLOR_WHITE)
                else:
                    can_afford = total_cash >= item["price"]
                    draw_glass_box(window, btn_box, bg_color=(255, 255, 255, 20) if can_afford else (0, 0, 0, 40), border_color=GLASS_BORDER_SUBTLE, border_radius=10)
                    b_txt = hud_font.render(f"${item['price']}", True, COLOR_WHITE if can_afford else COLOR_TEXT_MUTED)
                window.blit(b_txt, (btn_box.centerx - b_txt.get_width() // 2, btn_box.centery - b_txt.get_height() // 2))

        elif active_garage_tab == "UNDERGLOW":
            for idx, item in enumerate(UNDERGLOW_CATALOG):
                card_rect = pygame.Rect(50 + idx * 175, 180, 160, 240)
                is_owned = item["id"] in owned_underglows; is_eq = (equipped_underglow == item["id"]); is_hover = card_rect.collidepoint(mouse_pos)
                draw_glass_box(window, card_rect, bg_color=(255, 255, 255, 35) if is_hover else GLASS_BG_CARD, border_color=COLOR_WHITE if is_eq else (GLASS_BORDER_HI if is_hover else GLASS_BORDER_SUBTLE), border_radius=16)

                preview_rect = pygame.Rect(card_rect.x + 20, card_rect.y + 20, 120, 70)
                pygame.draw.rect(window, (15, 15, 20), preview_rect, border_radius=10)
                pygame.draw.ellipse(window, item["color"], (preview_rect.x + 10, preview_rect.y + 20, 100, 30))
                pygame.draw.rect(window, COLOR_WHITE, preview_rect, width=1, border_radius=10)
                name_txt = item_title_font.render(item["name"], True, COLOR_WHITE)
                window.blit(name_txt, (card_rect.centerx - name_txt.get_width() // 2, card_rect.y + 105))

                btn_box = pygame.Rect(card_rect.x + 15, card_rect.y + 175, 130, 40)
                if is_eq:
                    draw_glass_box(window, btn_box, bg_color=GLASS_BG_ACTIVE, border_color=COLOR_WHITE, border_radius=10)
                    b_txt = hud_font.render("EQUIPPED", True, COLOR_TEXT_DARK)
                elif is_owned:
                    draw_glass_box(window, btn_box, bg_color=(255, 255, 255, 45), border_color=GLASS_BORDER_HI, border_radius=10)
                    b_txt = hud_font.render("EQUIP", True, COLOR_WHITE)
                else:
                    can_afford = total_cash >= item["price"]
                    draw_glass_box(window, btn_box, bg_color=(255, 255, 255, 20) if can_afford else (0, 0, 0, 40), border_color=GLASS_BORDER_SUBTLE, border_radius=10)
                    b_txt = hud_font.render(f"${item['price']}", True, COLOR_WHITE if can_afford else COLOR_TEXT_MUTED)
                window.blit(b_txt, (btn_box.centerx - b_txt.get_width() // 2, btn_box.centery - b_txt.get_height() // 2))

        elif active_garage_tab == "MAPS":
            for idx, item in enumerate(MAPS_CATALOG):
                col = idx % 4
                row = idx // 4
                card_rect = pygame.Rect(35 + col * 235, 170 + row * 135, 220, 125)
                is_owned = item["id"] in owned_maps; is_eq = (equipped_map == item["id"]); is_hover = card_rect.collidepoint(mouse_pos)
                draw_glass_box(window, card_rect, bg_color=(255, 255, 255, 35) if is_hover else GLASS_BG_CARD, border_color=COLOR_WHITE if is_eq else (GLASS_BORDER_HI if is_hover else GLASS_BORDER_SUBTLE), border_radius=14)

                preview_rect = pygame.Rect(card_rect.x + 8, card_rect.y + 8, 85, 55)
                prev_surf = pygame.Surface((85, 55))
                for py in range(35):
                    r_p = int(item["sky_top"][0] * (1 - py/35) + item["sky_bottom"][0] * (py/35))
                    g_p = int(item["sky_top"][1] * (1 - py/35) + item["sky_bottom"][1] * (py/35))
                    b_p = int(item["sky_top"][2] * (1 - py/35) + item["sky_bottom"][2] * (py/35))
                    pygame.draw.line(prev_surf, (r_p, g_p, b_p), (0, py), (85, py))
                pygame.draw.rect(prev_surf, item["road_color"], (0, 35, 85, 20))
                window.blit(prev_surf, preview_rect)
                pygame.draw.rect(window, COLOR_WHITE, preview_rect, width=1, border_radius=6)

                name_txt = item_title_font.render(item["name"], True, COLOR_WHITE)
                window.blit(name_txt, (card_rect.x + 100, card_rect.y + 12))

                btn_box = pygame.Rect(card_rect.x + 100, card_rect.y + 70, 110, 35)
                if is_eq:
                    draw_glass_box(window, btn_box, bg_color=GLASS_BG_ACTIVE, border_color=COLOR_WHITE, border_radius=8)
                    b_txt = hud_font.render("EQUIPPED", True, COLOR_TEXT_DARK)
                elif is_owned:
                    draw_glass_box(window, btn_box, bg_color=(255, 255, 255, 45), border_color=GLASS_BORDER_HI, border_radius=8)
                    b_txt = hud_font.render("EQUIP", True, COLOR_WHITE)
                else:
                    can_afford = total_cash >= item["price"]
                    draw_glass_box(window, btn_box, bg_color=(255, 255, 255, 20) if can_afford else (0, 0, 0, 40), border_color=GLASS_BORDER_SUBTLE, border_radius=8)
                    b_txt = hud_font.render(f"${item['price']}", True, COLOR_WHITE if can_afford else COLOR_TEXT_MUTED)
                window.blit(b_txt, (btn_box.centerx - b_txt.get_width() // 2, btn_box.centery - b_txt.get_height() // 2))

        elif active_garage_tab == "UPGRADES":
            t_card = pygame.Rect(120, 180, 340, 240)
            draw_glass_box(window, t_card, bg_color=(255, 255, 255, 30) if t_card.collidepoint(mouse_pos) else GLASS_BG_CARD, border_color=GLASS_BORDER_HI, border_radius=20)
            t_title = btn_font.render("THROTTLE ENGINE STAGE", True, COLOR_WHITE)
            window.blit(t_title, (t_card.centerx - t_title.get_width() // 2, t_card.y + 22))
            t_desc = hud_font.render(f"Current Level: STAGE {throttle_level} / 4", True, COLOR_TEXT_MUTED)
            window.blit(t_desc, (t_card.centerx - t_desc.get_width() // 2, t_card.y + 65))

            p_bar = pygame.Rect(t_card.x + 40, t_card.y + 105, 260, 16)
            draw_glass_box(window, p_bar, bg_color=(15, 18, 24, 160), border_color=GLASS_BORDER_SUBTLE, border_radius=8)
            if throttle_level > 0:
                pygame.draw.rect(window, COLOR_WHITE, (p_bar.x, p_bar.y, int(260 * (throttle_level / 4.0)), 16), border_radius=8)

            t_btn = pygame.Rect(t_card.x + 70, t_card.y + 155, 200, 48)
            if throttle_level >= 4:
                draw_glass_box(window, t_btn, bg_color=GLASS_BG_ACTIVE, border_color=COLOR_WHITE, border_radius=12)
                tb_txt = btn_font.render("MAX LEVEL", True, COLOR_TEXT_DARK)
            else:
                nxt_price = UPGRADE_PRICES["throttle"][throttle_level + 1]
                can_a = total_cash >= nxt_price
                draw_glass_box(window, t_btn, bg_color=(255, 255, 255, 45) if can_a else (0, 0, 0, 50), border_color=COLOR_WHITE if can_a else GLASS_BORDER_SUBTLE, border_radius=12)
                tb_txt = btn_font.render(f"UPGRADE ${nxt_price}", True, COLOR_WHITE if can_a else COLOR_TEXT_MUTED)
            window.blit(tb_txt, (t_btn.centerx - tb_txt.get_width() // 2, t_btn.centery - tb_txt.get_height() // 2))

            b_card = pygame.Rect(540, 180, 340, 240)
            draw_glass_box(window, b_card, bg_color=(255, 255, 255, 30) if b_card.collidepoint(mouse_pos) else GLASS_BG_CARD, border_color=GLASS_BORDER_HI, border_radius=20)
            b_title = btn_font.render("REAR BRAKE RECOVERY STAGE", True, COLOR_WHITE)
            window.blit(b_title, (b_card.centerx - b_title.get_width() // 2, b_card.y + 22))
            b_desc = hud_font.render(f"Current Level: STAGE {brake_level} / 4", True, COLOR_TEXT_MUTED)
            window.blit(b_desc, (b_card.centerx - b_desc.get_width() // 2, b_card.y + 65))

            p_bar_b = pygame.Rect(b_card.x + 40, b_card.y + 105, 260, 16)
            draw_glass_box(window, p_bar_b, bg_color=(15, 18, 24, 160), border_color=GLASS_BORDER_SUBTLE, border_radius=8)
            if brake_level > 0:
                pygame.draw.rect(window, COLOR_WHITE, (p_bar_b.x, p_bar_b.y, int(260 * (brake_level / 4.0)), 16), border_radius=8)

            b_btn = pygame.Rect(b_card.x + 70, b_card.y + 155, 200, 48)
            if brake_level >= 4:
                draw_glass_box(window, b_btn, bg_color=GLASS_BG_ACTIVE, border_color=COLOR_WHITE, border_radius=12)
                bb_txt = btn_font.render("MAX LEVEL", True, COLOR_TEXT_DARK)
            else:
                nxt_price_b = UPGRADE_PRICES["brake"][brake_level + 1]
                can_ab = total_cash >= nxt_price_b
                draw_glass_box(window, b_btn, bg_color=(255, 255, 255, 45) if can_ab else (0, 0, 0, 50), border_color=COLOR_WHITE if can_ab else GLASS_BORDER_SUBTLE, border_radius=12)
                bb_txt = btn_font.render(f"UPGRADE ${nxt_price_b}", True, COLOR_WHITE if can_ab else COLOR_TEXT_MUTED)
            window.blit(bb_txt, (b_btn.centerx - bb_txt.get_width() // 2, b_btn.centery - bb_txt.get_height() // 2))

    elif game_state == "GAMEOVER":
        glass_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glass_overlay.fill((10, 12, 16, 220))
        window.blit(glass_overlay, (0, 0))

        go_font = get_font("Helvetica", 52, bold=True)
        sub_font = get_font("Helvetica", 16, bold=True)
        btn_font = get_font("Helvetica", 20, bold=True)

        modal_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, 60, 500, 360)
        draw_glass_box(window, modal_rect, bg_color=(255, 255, 255, 20), border_color=GLASS_BORDER_HI, border_radius=24)

        go_txt = go_font.render("LOOPED OUT!", True, COLOR_WHITE)
        score_txt = sub_font.render(f"Wheelie Distance: {int(wheelie_distance)} m", True, COLOR_WHITE)
        earned_txt = sub_font.render(f"Total Cash Gained: +${session_cash_earned} (Scrapes: ${int(scrape_cash_earned)})", True, COLOR_TEXT_MUTED)

        window.blit(go_txt, (modal_rect.centerx - go_txt.get_width() // 2, modal_rect.y + 35))
        window.blit(score_txt, (modal_rect.centerx - score_txt.get_width() // 2, modal_rect.y + 125))
        window.blit(earned_txt, (modal_rect.centerx - earned_txt.get_width() // 2, modal_rect.y + 165))

        retry_btn_rect = pygame.Rect(modal_rect.centerx - 110, modal_rect.y + 240, 220, 52)
        is_hovered = retry_btn_rect.collidepoint(mouse_pos)
        
        draw_glass_box(window, retry_btn_rect, 
                       bg_color=GLASS_BG_ACTIVE if is_hovered else (255, 255, 255, 45), 
                       border_color=COLOR_WHITE if is_hovered else GLASS_BORDER_SUBTLE, 
                       border_radius=16)

        retry_btn_txt = btn_font.render("RETRY  [ENTER]", True, COLOR_TEXT_DARK if is_hovered else COLOR_WHITE)
        window.blit(retry_btn_txt, (retry_btn_rect.centerx - retry_btn_txt.get_width() // 2, retry_btn_rect.centery - retry_btn_txt.get_height() // 2))

        if pygame.mouse.get_pressed()[0] and is_hovered:
            play_sfx(sound_click)
            reset_game()

    pygame.display.flip()