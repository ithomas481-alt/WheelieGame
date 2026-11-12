import pygame
import sys
import math
import random
import json
import array
import os
import asyncio
from collections import deque

def get_asset_path(relative_path):
    return relative_path.lstrip('/')

def find_audio_asset(stem_name):
    for ext in (".ogg", ".mp3", ".wav"):
        candidate = get_asset_path(f"assets/{stem_name}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 500
GROUND_Y = 400

COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_MAIN = (245, 245, 250)
COLOR_TEXT_MUTED = (160, 165, 175)
COLOR_TEXT_DARK = (15, 15, 20)
COLOR_DANGER = (220, 60, 60)
COLOR_SUCCESS = (50, 205, 50)
COLOR_GOLD = (255, 210, 60)

GLASS_OVERLAY_DARK = (10, 12, 16, 190)
GLASS_BG_CARD = (255, 255, 255, 22)
GLASS_BG_CARD_HOVER = (255, 255, 255, 45)
GLASS_BG_ACTIVE = (255, 255, 255, 235)
GLASS_BORDER_SUBTLE = (255, 255, 255, 55)
GLASS_BORDER_HI = (255, 255, 255, 150)

FRAME_WIDTH = 260
FRAME_HEIGHT = 180
SEATSTAND_WIDTH = 260
SEATSTAND_HEIGHT = 180

REAR_WHEEL_SIZE = 90
FRONT_WHEEL_SIZE = 96

SAVE_FILE = get_asset_path("save_data.json")

sfx_volume = 0.7
music_volume = 0.5
low_performance_mode = False
audio_enabled = False
browser_audio_unlocked = False

current_playing_music = None
music_channel = None
active_music_sound = None

sound_click = None
sound_scrape = None
sound_slam = None
scrape_sound_cooldown = 0.0

rear_wheel_img = None
front_wheel_img = None

PRE_RENDERED_SKIES = {}
LENS_OVERLAYS = {}
LAMP_GLOW_SURFACES = {}
SPEED_VIGNETTE_SURF = None

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

def generate_procedural_wheel(size, rim_color=(200, 200, 210), spoke_count=12):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    radius = size // 2 - 2
    pygame.draw.circle(surf, (20, 22, 26), (center, center), radius)
    pygame.draw.circle(surf, (35, 38, 45), (center, center), radius, 5)
    rim_radius = radius - 8
    pygame.draw.circle(surf, rim_color, (center, center), rim_radius, 4)
    for i in range(spoke_count):
        ang = (2 * math.pi / spoke_count) * i
        x2 = center + int(math.cos(ang) * rim_radius)
        y2 = center + int(math.sin(ang) * rim_radius)
        pygame.draw.line(surf, (180, 185, 195), (center, center), (x2, y2), 2)
    pygame.draw.circle(surf, (50, 55, 65), (center, center), 9)
    pygame.draw.circle(surf, (230, 235, 245), (center, center), 5)
    return surf

def generate_procedural_frame(width, height, color_rgb, is_seatstand=False):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    r_axle = (width * 0.12, height * 0.80)
    f_axle = (width * 0.78, height * 0.80)
    bb = (width * 0.38, height * 0.75)
    seat_joint = (width * 0.32, height * 0.38)
    head_tube = (width * 0.68, height * 0.28)
    bars = (width * 0.64, height * 0.12)

    pygame.draw.line(surf, color_rgb, r_axle, bb, 7)
    pygame.draw.line(surf, color_rgb, r_axle, seat_joint, 7)
    pygame.draw.line(surf, color_rgb, bb, seat_joint, 8)
    pygame.draw.line(surf, color_rgb, bb, head_tube, 8)
    pygame.draw.line(surf, color_rgb, seat_joint, head_tube, 7)
    pygame.draw.line(surf, color_rgb, head_tube, f_axle, 7)
    pygame.draw.line(surf, (40, 40, 45), head_tube, bars, 6)
    pygame.draw.line(surf, (20, 20, 25), (bars[0]-15, bars[1]), (bars[0]+15, bars[1]), 5)

    rider_color = (230, 235, 245)
    if is_seatstand:
        foot_pos = (seat_joint[0], seat_joint[1] - 8)
        hip = (seat_joint[0] - 10, seat_joint[1] - 45)
        head = (hip[0] + 15, hip[1] - 35)
        pygame.draw.line(surf, (30, 35, 45), foot_pos, hip, 6)
        pygame.draw.line(surf, rider_color, hip, head, 9)
        pygame.draw.circle(surf, rider_color, (int(head[0]), int(head[1])), 10)
        pygame.draw.line(surf, rider_color, (hip[0]+5, hip[1]-20), bars, 5)
    else:
        seat_pos = (seat_joint[0] - 12, seat_joint[1] - 10)
        pygame.draw.rect(surf, (20, 20, 25), (seat_pos[0]-15, seat_pos[1], 30, 8), border_radius=3)
        hip = (seat_pos[0], seat_pos[1] - 15)
        head = (hip[0] + 25, hip[1] - 30)
        pygame.draw.line(surf, (30, 35, 45), bb, hip, 6)
        pygame.draw.line(surf, rider_color, hip, head, 9)
        pygame.draw.circle(surf, rider_color, (int(head[0]), int(head[1])), 10)
        pygame.draw.line(surf, rider_color, (hip[0]+10, hip[1]-15), bars, 5)

    return surf

PAINTS_CATALOG = [
    {"id": 0, "name": "Factory Red", "price": 0, "file": get_asset_path("assets/frame_red.png"), "file_seatstand": get_asset_path("assets/frame_red_seatstand.png"), "hud_color": (220, 50, 50)},
    {"id": 1, "name": "Cyber Cyan", "price": 100, "file": get_asset_path("assets/frame_cyan.png"), "file_seatstand": get_asset_path("assets/frame_cyan_seatstand.png"), "hud_color": (0, 210, 255)},
    {"id": 2, "name": "Sunset Gold", "price": 250, "file": get_asset_path("assets/frame_gold.png"), "file_seatstand": get_asset_path("assets/frame_gold_seatstand.png"), "hud_color": (255, 200, 50)},
    {"id": 3, "name": "Hyper Purple", "price": 400, "file": get_asset_path("assets/frame_purple.png"), "file_seatstand": get_asset_path("assets/frame_purple_seatstand.png"), "hud_color": (200, 60, 255)},
    {"id": 4, "name": "Stealth Black", "price": 650, "file": get_asset_path("assets/frame_black.png"), "file_seatstand": get_asset_path("assets/frame_black_seatstand.png"), "hud_color": (60, 60, 70)}
]

UNDERGLOW_CATALOG = [
    {"id": 0, "name": "Electric Cyan", "price": 0, "color": (0, 210, 255)},
    {"id": 1, "name": "Acid Green", "price": 75, "color": (40, 230, 90)},
    {"id": 2, "name": "Lava Red", "price": 150, "color": (255, 50, 50)},
    {"id": 3, "name": "Deep Violet", "price": 300, "color": (180, 50, 255)},
    {"id": 4, "name": "Solar Yellow", "price": 450, "color": (255, 230, 30)}
]

MAPS_CATALOG = [
    {"id": 0, "name": "NYC Midnight", "price": 0, "sky_top": (6, 10, 24), "sky_bottom": (16, 28, 48), "road_color": (26, 30, 38), "dash_color": (240, 245, 255, 180), "far_layer": None, "near_layer": None, "has_stars": True, "has_rain": True, "wet_road": True, "streetlights": True, "lamp_color": (255, 240, 180), "lens_filter": "NYC_NIGHT_LENS", "music_stem": "music_nyc"},
    {"id": 1, "name": "Sunset Highway", "price": 180, "sky_top": (40, 15, 60), "sky_bottom": (245, 110, 50), "road_color": (45, 38, 42), "dash_color": (255, 210, 80, 210), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 190, 90), "lens_filter": "SUNSET_AMBER_LENS", "music_stem": "music_sunset"},
    {"id": 2, "name": "Neon Cyber Grid", "price": 450, "sky_top": (12, 4, 28), "sky_bottom": (35, 10, 60), "road_color": (18, 14, 28), "dash_color": (0, 240, 255, 220), "far_layer": None, "near_layer": None, "has_stars": True, "has_rain": True, "wet_road": True, "streetlights": True, "lamp_color": (255, 0, 160), "cyber_grid": True, "lens_filter": "CYBER_SCANLINE_LENS", "music_stem": "music_cyber"},
    {"id": 3, "name": "Cherry Blossom Forest", "price": 320, "sky_top": (38, 15, 45), "sky_bottom": (240, 130, 175), "road_color": (42, 28, 38), "dash_color": (255, 190, 220, 210), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": False, "lamp_color": (255, 180, 220), "has_petals": True, "lens_filter": "CHERRY_BLOOM_LENS", "music_stem": "music_cherry"},
    {"id": 4, "name": "California Coast", "price": 500, "sky_top": (20, 30, 75), "sky_bottom": (255, 140, 40), "road_color": (48, 40, 36), "dash_color": (255, 220, 120, 220), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 220, 140), "has_sun": True, "lens_filter": "CALIFORNIA_GOLDEN_LENS", "music_stem": "music_cali"},
    {"id": 5, "name": "Alpine Mountain Pass", "price": 10000, "sky_top": (10, 25, 50), "sky_bottom": (140, 185, 220), "road_color": (44, 52, 64), "dash_color": (230, 245, 255, 230), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (180, 225, 255), "has_snow": True, "snow_edge": True, "lens_filter": "ALPINE_FROST_LENS", "music_stem": "music_alpine"},
    {"id": 6, "name": "Volcanic Magma Canyon", "price": 10000, "sky_top": (18, 4, 6), "sky_bottom": (180, 40, 15), "road_color": (28, 20, 24), "dash_color": (255, 90, 20, 240), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 110, 30), "has_embers": True, "lava_edge": True, "lens_filter": "VOLCANIC_GLOW_LENS", "music_stem": "music_volcano"}
]

UPGRADE_PRICES = {
    "throttle": {2: 120, 3: 300, 4: 650},
    "brake": {2: 100, 3: 250, 4: 550}
}

frame_images_normal = {}
frame_images_seatstand = {}

def load_single_frame_png(filename, target_w, target_h, fallback_color=(220, 50, 50), is_seatstand=False):
    try:
        surf = pygame.image.load(filename).convert_alpha()
        return pygame.transform.scale(surf, (target_w, target_h))
    except Exception:
        return generate_procedural_frame(target_w, target_h, fallback_color, is_seatstand=is_seatstand)

def load_all_paint_assets():
    global frame_images_normal, frame_images_seatstand
    for item in PAINTS_CATALOG:
        pid = item["id"]
        frame_images_normal[pid] = load_single_frame_png(item["file"], FRAME_WIDTH, FRAME_HEIGHT, fallback_color=item["hud_color"], is_seatstand=False)
        seatstand_file = item.get("file_seatstand", item["file"].replace(".png", "_seatstand.png"))
        frame_images_seatstand[pid] = load_single_frame_png(seatstand_file, SEATSTAND_WIDTH, SEATSTAND_HEIGHT, fallback_color=item["hud_color"], is_seatstand=True)

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

def play_sfx(sound):
    if audio_enabled and sound:
        try:
            sound.set_volume(sfx_volume)
            sound.play()
        except Exception:
            pass

def update_bg_music(target_stem, force_restart=False):
    global current_playing_music, active_music_sound, music_channel
    if not audio_enabled: return

    target_music_file = find_audio_asset(target_stem) if target_stem else None

    if not force_restart and current_playing_music == target_music_file:
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
        try:
            music_channel.stop()
        except Exception:
            pass
        active_music_sound = None

    if not target_music_file:
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
    except Exception:
        pass

def save_game_data():
    data = {
        "total_cash": total_cash, "high_score": high_score,
        "owned_paints": owned_paints, "equipped_paint": equipped_paint,
        "owned_underglows": owned_underglows, "equipped_underglow": equipped_underglow,
        "owned_maps": owned_maps, "equipped_map": equipped_map,
        "throttle_level": throttle_level, "brake_level": brake_level,
        "sfx_volume": sfx_volume, "music_volume": music_volume,
        "low_performance_mode": low_performance_mode
    }
    try:
        with open(SAVE_FILE, "w") as f: json.dump(data, f, indent=4)
    except Exception: pass

def reset_all_data_defaults():
    global total_cash, high_score, owned_paints, equipped_paint
    global owned_underglows, equipped_underglow, owned_maps, equipped_map
    global throttle_level, brake_level, low_performance_mode
    total_cash, high_score = 100, 0.0
    owned_paints, equipped_paint = [0], 0
    owned_underglows, equipped_underglow = [0], 0
    owned_maps, equipped_map = [0], 0
    throttle_level, brake_level = 1, 1
    low_performance_mode = False
    save_game_data()

def load_game_data():
    global total_cash, high_score, owned_paints, equipped_paint
    global owned_underglows, equipped_underglow, owned_maps, equipped_map
    global throttle_level, brake_level, sfx_volume, music_volume, low_performance_mode
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
            low_performance_mode = data.get("low_performance_mode", False)
    except Exception: reset_all_data_defaults()

def get_font(font_name, size, bold=False):
    try: return pygame.font.SysFont(font_name, int(size), bold=bold)
    except Exception: return pygame.font.Font(None, int(size))

def draw_glass_box(surface, rect, bg_color=GLASS_BG_CARD, border_color=GLASS_BORDER_SUBTLE, border_radius=16, border_width=1):
    glass_surf = pygame.Surface((int(rect.width), int(rect.height)), pygame.SRCALPHA)
    pygame.draw.rect(glass_surf, bg_color, (0, 0, int(rect.width), int(rect.height)), border_radius=int(border_radius))
    if border_width > 0:
        pygame.draw.rect(glass_surf, border_color, (0, 0, int(rect.width), int(rect.height)), width=int(border_width), border_radius=int(border_radius))
    surface.blit(glass_surf, (int(rect.x), int(rect.y)))

def build_sky_surface(sky_top, sky_bot):
    surf = pygame.Surface((WINDOW_WIDTH, 340))
    for y in range(340):
        ratio = y / 340.0
        r = int(sky_top[0] * (1 - ratio) + sky_bot[0] * ratio)
        g = int(sky_top[1] * (1 - ratio) + sky_bot[1] * ratio)
        b = int(sky_top[2] * (1 - ratio) + sky_bot[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (WINDOW_WIDTH, y))
    return surf

def build_speed_vignette_surface():
    surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    for i in range(18):
        alpha = int((18 - i) * 6.5)
        thickness = i * 8
        pygame.draw.rect(surf, (5, 8, 16, alpha), (thickness, thickness, WINDOW_WIDTH - thickness * 2, WINDOW_HEIGHT - thickness * 2), width=10, border_radius=24)
    return surf

def build_lamp_glow_surface(lamp_color):
    surf = pygame.Surface((160, 210), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (*lamp_color, 44), [(80, 12), (12, 210), (148, 210)])
    pygame.draw.polygon(surf, (*lamp_color, 68), [(80, 12), (42, 210), (118, 210)])
    pygame.draw.circle(surf, (*lamp_color, 160), (80, 14), 16)
    pygame.draw.circle(surf, (255, 255, 255, 235), (80, 14), 6)
    return surf

def build_lens_overlay(lens_type):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    if lens_type == "NYC_NIGHT_LENS":
        pygame.draw.rect(overlay, (10, 24, 52, 28), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
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
    elif lens_type == "ALPINE_FROST_LENS":
        pygame.draw.rect(overlay, (175, 225, 255, 26), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    elif lens_type == "VOLCANIC_GLOW_LENS":
        pygame.draw.rect(overlay, (255, 50, 10, 40), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    return overlay

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
    neon_colors = [(255, 0, 128), (0, 240, 255), (180, 0, 255)]
    random.seed(505 if is_far else 606)
    x = 0
    while x < width:
        w = random.randint(40, 85)
        h = random.randint(110, 260) if is_far else random.randint(70, 180)
        pygame.draw.rect(surf, base_color, (x, height - h, w, h))
        neon_c = random.choice(neon_colors)
        pygame.draw.line(surf, (*neon_c, 220), (x, height - h), (x + w, height - h), 3)
        pygame.draw.line(surf, (*neon_c, 120), (x + 6, height - h), (x + 6, height), 1)
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
    if not is_far:
        for tx in range(40, width, 160):
            trunk_h = random.randint(75, 115)
            pygame.draw.rect(surf, (35, 16, 24), (tx - 5, height - trunk_h, 10, trunk_h))
            pygame.draw.circle(surf, (255, 150, 200, 180), (tx, height - trunk_h), 36)
            pygame.draw.circle(surf, (255, 185, 220, 200), (tx - 20, height - trunk_h + 10), 26)
            pygame.draw.circle(surf, (255, 185, 220, 200), (tx + 20, height - trunk_h + 10), 26)
    return surf

def generate_california_coast(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(909 if is_far else 910)
    pts = [(0, height)]
    for x in range(0, width + 60, 60):
        h = random.randint(50, 130)
        pts.append((int(x), int(height - h)))
    pts.append((width, height))
    pygame.draw.polygon(surf, (65, 35, 25) if is_far else (40, 20, 15), pts)
    if not is_far:
        for px in range(70, width, 210):
            top_y = height - random.randint(120, 165)
            pygame.draw.line(surf, (25, 14, 12), (px, height), (px + 8, top_y), 6)
            for ang in (-2.5, -1.9, -1.2, -0.5, 0.2):
                fx = px + 8 + int(math.cos(ang) * 34)
                fy = top_y + int(math.sin(ang) * 20)
                pygame.draw.line(surf, (25, 14, 12), (px + 8, top_y), (fx, fy), 3)
    return surf

def generate_alpine_mountains(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(111 if is_far else 222)
    pts = [(0, height)]
    peaks = []
    for x in range(0, width + 65, 65):
        h = random.randint(120, 250) if is_far else random.randint(60, 140)
        py = int(height - h)
        pts.append((int(x), py))
        if is_far and h > 170:
            peaks.append((int(x), py))
    pts.append((width, height))
    pygame.draw.polygon(surf, (40, 50, 70) if is_far else (25, 32, 48), pts)
    for px, py in peaks:
        pygame.draw.polygon(surf, (230, 244, 255, 225), [(px, py), (px - 24, py + 42), (px + 24, py + 42)])
    return surf

def generate_volcanic_canyon(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(333 if is_far else 444)
    pts = [(0, height)]
    for x in range(0, width + 70, 70):
        h = random.randint(100, 230) if is_far else random.randint(50, 130)
        pts.append((int(x), int(height - h)))
    pts.append((width, height))
    pygame.draw.polygon(surf, (24, 12, 14) if is_far else (16, 8, 10), pts)
    if not is_far:
        for lx in range(30, width, 140):
            pygame.draw.line(surf, (255, 80, 15, 200), (lx, height - 10), (lx + 35, height - 45), 3)
    return surf

NYC_FAR, NYC_NEAR = None, None
SUNSET_FAR, SUNSET_NEAR = None, None
CYBER_FAR, CYBER_NEAR = None, None
CHERRY_FAR, CHERRY_NEAR = None, None
CALI_FAR, CALI_NEAR = None, None
ALPINE_FAR, ALPINE_NEAR = None, None
VOLCANO_FAR, VOLCANO_NEAR = None, None

async def init_procedural_backgrounds():
    global NYC_FAR, NYC_NEAR, SUNSET_FAR, SUNSET_NEAR, CYBER_FAR, CYBER_NEAR
    global CHERRY_FAR, CHERRY_NEAR, CALI_FAR, CALI_NEAR, ALPINE_FAR, ALPINE_NEAR, VOLCANO_FAR, VOLCANO_NEAR
    NYC_FAR = generate_nyc_skyline(2000, 320, True); await asyncio.sleep(0)
    NYC_NEAR = generate_nyc_skyline(2000, 320, False); await asyncio.sleep(0)
    SUNSET_FAR = generate_sunset_mountains(2000, 320, True); await asyncio.sleep(0)
    SUNSET_NEAR = generate_sunset_mountains(2000, 320, False); await asyncio.sleep(0)
    CYBER_FAR = generate_cyber_skyline(2000, 320, True); await asyncio.sleep(0)
    CYBER_NEAR = generate_cyber_skyline(2000, 320, False); await asyncio.sleep(0)
    CHERRY_FAR = generate_cherry_blossom_forest(2000, 320, True); await asyncio.sleep(0)
    CHERRY_NEAR = generate_cherry_blossom_forest(2000, 320, False); await asyncio.sleep(0)
    CALI_FAR = generate_california_coast(2000, 320, True); await asyncio.sleep(0)
    CALI_NEAR = generate_california_coast(2000, 320, False); await asyncio.sleep(0)
    ALPINE_FAR = generate_alpine_mountains(2000, 320, True); await asyncio.sleep(0)
    ALPINE_NEAR = generate_alpine_mountains(2000, 320, False); await asyncio.sleep(0)
    VOLCANO_FAR = generate_volcanic_canyon(2000, 320, True); await asyncio.sleep(0)
    VOLCANO_NEAR = generate_volcanic_canyon(2000, 320, False); await asyncio.sleep(0)

STARS_SURF = pygame.Surface((1000, 300), pygame.SRCALPHA)
random.seed(777)
for _ in range(85):
    sx = random.randint(0, 1000)
    sy = random.randint(0, 220)
    pygame.draw.circle(STARS_SURF, (200, 235, 255, random.randint(120, 255)), (int(sx), int(sy)), 1)

# 150 dual-layer weather particles for NYC rain, Alpine snow, Cherry petals, Volcanic embers
weather_particles = []
for idx in range(150):
    layer = 1 if idx < 70 else 0  # 1 = foreground, 0 = background
    weather_particles.append([
        random.uniform(0, WINDOW_WIDTH + 200),
        random.uniform(0, GROUND_Y),
        random.uniform(0.95, 1.45) if layer == 1 else random.uniform(0.60, 0.90),
        random.uniform(0, math.pi * 2),
        layer
    ])

rain_splashes = []
speed_lines = []
for _ in range(28):
    speed_lines.append([
        random.uniform(0, WINDOW_WIDTH),
        random.choice([random.uniform(15, 125), random.uniform(345, WINDOW_HEIGHT - 15)]),
        random.uniform(60, 160),
        random.uniform(0.8, 1.4)
    ])

bike_ghost_history = deque(maxlen=4)
smoke_particles, sparks = [], []

def update_maps_catalog_layers():
    MAPS_CATALOG[0]["far_layer"], MAPS_CATALOG[0]["near_layer"] = NYC_FAR, NYC_NEAR
    MAPS_CATALOG[1]["far_layer"], MAPS_CATALOG[1]["near_layer"] = SUNSET_FAR, SUNSET_NEAR
    MAPS_CATALOG[2]["far_layer"], MAPS_CATALOG[2]["near_layer"] = CYBER_FAR, CYBER_NEAR
    MAPS_CATALOG[3]["far_layer"], MAPS_CATALOG[3]["near_layer"] = CHERRY_FAR, CHERRY_NEAR
    MAPS_CATALOG[4]["far_layer"], MAPS_CATALOG[4]["near_layer"] = CALI_FAR, CALI_NEAR
    MAPS_CATALOG[5]["far_layer"], MAPS_CATALOG[5]["near_layer"] = ALPINE_FAR, ALPINE_NEAR
    MAPS_CATALOG[6]["far_layer"], MAPS_CATALOG[6]["near_layer"] = VOLCANO_FAR, VOLCANO_NEAR

def get_current_underglow_color():
    return UNDERGLOW_CATALOG[equipped_underglow]["color"]

def get_current_map():
    return MAPS_CATALOG[equipped_map]

REAR_AXLE_ORIGIN = pygame.math.Vector2(FRAME_WIDTH * 0.08, FRAME_HEIGHT * 0.82)
FRONT_AXLE_ORIGIN = pygame.math.Vector2(FRAME_WIDTH * 0.76, FRAME_HEIGHT * 0.82)
AXLE_OFFSET_VECTOR = FRONT_AXLE_ORIGIN - REAR_AXLE_ORIGIN

SEATSTAND_REAR_AXLE_ORIGIN = pygame.math.Vector2(SEATSTAND_WIDTH * 0.18, SEATSTAND_HEIGHT * 0.82)
SEATSTAND_FRONT_AXLE_ORIGIN = pygame.math.Vector2(SEATSTAND_WIDTH * 0.90, SEATSTAND_HEIGHT * 0.82)
SEATSTAND_AXLE_OFFSET_VECTOR = SEATSTAND_FRONT_AXLE_ORIGIN - SEATSTAND_REAR_AXLE_ORIGIN

rear_susp_comp, rear_susp_vel = 0.0, 0.0
front_susp_comp, front_susp_vel = 0.0, 0.0
active_stance = "SEATED"
combo_multiplier = 1.0
wheelie_combo_timer = 0.0

game_state = "MENU"
previous_state_before_settings = "MENU"
confirm_reset_active = False

wheelie_distance = 0.0
session_cash_earned = 0
scrape_cash_earned = 0.0
cash_banked_this_run = False

pivot_x = 300
pivot_y = GROUND_Y - (REAR_WHEEL_SIZE // 2)
world_offset = 0.0

angle, angular_velocity, speed, wheel_spin = 0.0, 0.0, 0.0, 0.0
throttle_timer, brake_timer = 0.0, 0.0
shake_timer, shake_intensity = 0, 0.0
cam_x_offset, cam_y_offset = 0.0, 0.0

play_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, 155, 190, 48)
garage_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 95, 155, 190, 48)
settings_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 + 130, 155, 190, 48)

hud_pause_rect = pygame.Rect(WINDOW_WIDTH - 125, 20, 105, 38)

tab_paints_rect = pygame.Rect(40, 110, 205, 42)
tab_underglow_rect = pygame.Rect(265, 110, 205, 42)
tab_maps_rect = pygame.Rect(490, 110, 205, 42)
tab_upgrades_rect = pygame.Rect(715, 110, 245, 42)

garage_back_rect = pygame.Rect(40, 30, 130, 40)
settings_back_rect = pygame.Rect(40, 30, 130, 40)

sfx_minus_rect = pygame.Rect(440, 130, 44, 44)
sfx_plus_rect = pygame.Rect(660, 130, 44, 44)
music_minus_rect = pygame.Rect(440, 190, 44, 44)
music_plus_rect = pygame.Rect(660, 190, 44, 44)
low_perf_toggle_rect = pygame.Rect(WINDOW_WIDTH // 2 - 195, 260, 390, 44)
reset_data_rect = pygame.Rect(WINDOW_WIDTH // 2 - 195, 325, 390, 44)

confirm_yes_rect = pygame.Rect(WINDOW_WIDTH // 2 - 130, 280, 120, 42)
confirm_no_rect = pygame.Rect(WINDOW_WIDTH // 2 + 10, 280, 120, 42)

pause_resume_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 150, 280, 48)
pause_restart_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 215, 280, 48)
pause_settings_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 280, 280, 48)
pause_menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 345, 280, 48)

gameover_retry_rect = pygame.Rect(WINDOW_WIDTH // 2 - 220, 345, 210, 50)
gameover_menu_rect = pygame.Rect(WINDOW_WIDTH // 2 + 10, 345, 210, 50)

active_garage_tab = "PAINTS"

def trigger_screen_shake(intensity, duration):
    global shake_intensity, shake_timer
    if low_performance_mode: return
    shake_intensity = max(shake_intensity, intensity)
    shake_timer = duration

def bank_session_cash():
    global total_cash, session_cash_earned, cash_banked_this_run
    if not cash_banked_this_run and session_cash_earned > 0:
        total_cash += session_cash_earned
        cash_banked_this_run = True
        save_game_data()

def rotate_around_pivot(surface, image, angle, pivot, origin, alpha=255):
    image_rect = image.get_rect(topleft=(int(pivot[0] - origin.x), int(pivot[1] - origin.y)))
    offset = pygame.math.Vector2(pivot) - image_rect.center
    rotated_offset = offset.rotate(-angle)
    rect = image.get_rect(center=pygame.math.Vector2(pivot) - rotated_offset)
    rotated_image = pygame.transform.rotate(image, angle)
    if alpha < 255:
        rotated_image.set_alpha(alpha)
    rect = rotated_image.get_rect(center=(int(rect.centerx), int(rect.centery)))
    surface.blit(rotated_image, rect)

def draw_suspension_hardware(surface, rear_axle_pos, frame_rear_mount, front_axle_pos, frame_front_mount):
    rear_vec = frame_rear_mount - rear_axle_pos
    if rear_vec.length() > 0:
        pygame.draw.line(surface, (50, 55, 65), (int(rear_axle_pos.x), int(rear_axle_pos.y)), (int(frame_rear_mount.x), int(frame_rear_mount.y)), 6)
        pygame.draw.line(surface, (180, 190, 200), (int(rear_axle_pos.x), int(rear_axle_pos.y)), (int(frame_rear_mount.x), int(frame_rear_mount.y)), 2)

    front_vec = frame_front_mount - front_axle_pos
    dist_front = front_vec.length()
    if dist_front > 0:
        dir_front = front_vec.normalize()
        lower_end = front_axle_pos + dir_front * (dist_front * 0.52)
        pygame.draw.line(surface, (25, 30, 40), (int(front_axle_pos.x), int(front_axle_pos.y)), (int(lower_end.x), int(lower_end.y)), 8)
        pygame.draw.line(surface, (210, 220, 235), (int(lower_end.x), int(lower_end.y)), (int(frame_front_mount.x), int(frame_front_mount.y)), 5)

def reset_game():
    global angle, angular_velocity, speed, world_offset, wheel_spin
    global shake_timer, shake_intensity, cam_x_offset, cam_y_offset, wheelie_distance, game_state
    global throttle_timer, brake_timer, session_cash_earned, scrape_cash_earned
    global wheelie_combo_timer, combo_multiplier, active_stance, cash_banked_this_run
    global rear_susp_comp, rear_susp_vel, front_susp_comp, front_susp_vel

    angle, angular_velocity, speed, wheel_spin = 0.0, 0.0, 0.0, 0.0
    world_offset, wheelie_distance = 0.0, 0.0
    session_cash_earned, scrape_cash_earned = 0, 0.0
    cash_banked_this_run = False
    wheelie_combo_timer, combo_multiplier = 0.0, 1.0
    active_stance = "SEATED"
    throttle_timer, brake_timer = 0.0, 0.0
    shake_timer, shake_intensity = 0, 0.0
    cam_x_offset, cam_y_offset = 0.0, 0.0
    rear_susp_comp, rear_susp_vel = 0.0, 0.0
    front_susp_comp, front_susp_vel = 0.0, 0.0
    sparks.clear(); smoke_particles.clear(); rain_splashes.clear(); bike_ghost_history.clear()
    game_state = "PLAYING"

def render_map_weather_and_props(surface, current_map, rendered_g_y, current_speed, dt):
    if low_performance_mode:
        return

    # 1. Streetlights & glowing cones along the road
    if current_map.get("streetlights", False):
        lamp_c = current_map.get("lamp_color", (255, 240, 180))
        glow_img = LAMP_GLOW_SURFACES.get(lamp_c)
        spacing = 360
        start_x = int((-world_offset * 0.85) % spacing) - spacing
        for lx in range(start_x, WINDOW_WIDTH + spacing, spacing):
            pole_top = rendered_g_y - 195
            pygame.draw.rect(surface, (28, 32, 40), (lx - 3, pole_top, 6, 195))
            pygame.draw.line(surface, (28, 32, 40), (lx, pole_top), (lx + 24, pole_top - 6), 5)
            if glow_img:
                surface.blit(glow_img, (lx + 24 - 80, pole_top - 18))
            if current_map.get("wet_road", False):
                ref_surf = pygame.Surface((120, 26), pygame.SRCALPHA)
                pygame.draw.ellipse(ref_surf, (*lamp_c, 34), (0, 0, 120, 26))
                surface.blit(ref_surf, (lx - 36, rendered_g_y + 12))

    # 2. Active weather particles (NYC Rain, Alpine Snow, Cherry Petals, Volcanic Embers)
    has_rain = current_map.get("has_rain", False)
    has_petals = current_map.get("has_petals", False)
    has_snow = current_map.get("has_snow", False)
    has_embers = current_map.get("has_embers", False)

    if has_rain or has_petals or has_snow or has_embers:
        wind = current_speed * 0.72
        for p in weather_particles:
            p[3] += dt * 3.2
            is_fg = (p[4] == 1)

            if has_rain:
                slant_x = (3.8 + wind) * p[2]
                drop_y = (16.5 if is_fg else 11.5) * p[2]
                p[0] -= slant_x
                p[1] += drop_y
                if p[1] >= rendered_g_y:
                    if is_fg and len(rain_splashes) < 40 and random.random() < 0.45:
                        rain_splashes.append([p[0], rendered_g_y + random.uniform(2, 42), 7])
                    p[1] = random.uniform(-60, -5)
                    p[0] = random.uniform(0, WINDOW_WIDTH + 260)
                else:
                    streak_col = (185, 225, 255) if is_fg else (105, 145, 195)
                    streak_w = 2 if is_fg else 1
                    tail_x = int(p[0] + slant_x * 1.15)
                    tail_y = int(p[1] - drop_y * 1.15)
                    pygame.draw.line(surface, streak_col, (int(p[0]), int(p[1])), (tail_x, tail_y), streak_w)

            elif has_snow:
                swirl = math.sin(p[3]) * (1.4 if is_fg else 0.7)
                p[0] -= (1.4 + wind * 0.65 + swirl)
                p[1] += (3.2 if is_fg else 2.0) * p[2]
                if p[1] >= rendered_g_y:
                    p[1] = random.uniform(-40, -5)
                    p[0] = random.uniform(0, WINDOW_WIDTH + 220)
                if is_fg:
                    pygame.draw.circle(surface, (195, 225, 250), (int(p[0]), int(p[1])), 4)
                    pygame.draw.circle(surface, (250, 253, 255), (int(p[0]), int(p[1])), 2)
                else:
                    pygame.draw.circle(surface, (220, 236, 250), (int(p[0]), int(p[1])), 2)

            elif has_petals:
                p[0] -= (1.8 + wind * 0.7 + math.sin(p[3]) * 0.9)
                p[1] += 2.3 * p[2]
                if p[1] >= rendered_g_y:
                    p[1] = random.uniform(-30, 0)
                    p[0] = random.uniform(0, WINDOW_WIDTH + 180)
                pygame.draw.ellipse(surface, (255, 175, 215), (int(p[0]), int(p[1]), 8 if is_fg else 6, 4))

            elif has_embers:
                p[0] -= (1.5 + wind * 0.65 + math.sin(p[3]) * 1.1)
                p[1] -= 2.5 * p[2]
                if p[1] < 20:
                    p[1] = rendered_g_y - random.uniform(0, 25)
                    p[0] = random.uniform(0, WINDOW_WIDTH + 180)
                c = (255, random.randint(90, 190), 25)
                pygame.draw.circle(surface, c, (int(p[0]), int(p[1])), 3 if is_fg else 2)

            if p[0] < -40:
                p[0] += WINDOW_WIDTH + 240
            elif p[0] > WINDOW_WIDTH + 260:
                p[0] -= WINDOW_WIDTH + 260

        # Render animated NYC rain splashes on wet road
        if has_rain:
            for sp_drop in rain_splashes[:]:
                sp_drop[0] -= current_speed * 0.9
                sp_drop[2] -= 1
                if sp_drop[2] <= 0:
                    rain_splashes.remove(sp_drop)
                else:
                    spread = (8 - sp_drop[2]) * 1.4
                    sx, sy = int(sp_drop[0]), int(sp_drop[1])
                    pygame.draw.line(surface, (190, 225, 255), (sx, sy), (int(sx - spread), int(sy - 4)), 1)
                    pygame.draw.line(surface, (190, 225, 255), (sx, sy), (int(sx + spread), int(sy - 4)), 1)

def render_motion_blur_vfx(surface, current_speed, dt):
    if low_performance_mode or current_speed <= 11.0:
        return

    blur_ratio = min(1.0, (current_speed - 11.0) / 18.0)

    # 1. Peripheral speed wind-streak lines
    streak_color = (220, 235, 255)
    for sl in speed_lines:
        sl[0] -= (18.0 + current_speed * 1.8) * sl[3]
        if sl[0] + sl[2] < 0:
            sl[0] = WINDOW_WIDTH + random.uniform(10, 140)
            sl[1] = random.choice([random.uniform(15, 125), random.uniform(345, WINDOW_HEIGHT - 15)])
        line_len = int(sl[2] * (0.5 + blur_ratio * 1.1))
        pygame.draw.line(surface, streak_color, (int(sl[0]), int(sl[1])), (int(sl[0] + line_len), int(sl[1])), 1 if blur_ratio < 0.5 else 2)

    # 2. Dynamic tunnel-vision speed vignette
    if SPEED_VIGNETTE_SURF is not None:
        SPEED_VIGNETTE_SURF.set_alpha(int(blur_ratio * 175))
        surface.blit(SPEED_VIGNETTE_SURF, (0, 0))

def draw_forza_speedometer(surface, current_speed, max_speed, current_angle, score, mouse_pos):
    center_x = WINDOW_WIDTH - 120
    center_y = WINDOW_HEIGHT - 110
    draw_glass_box(surface, pygame.Rect(center_x - 95, center_y - 95, 190, 190), bg_color=(15, 18, 24, 180), border_color=GLASS_BORDER_HI, border_radius=95, border_width=2)

    mph_val = int(current_speed * 2.2)
    font_large = get_font("Helvetica", 42, bold=True)
    font_unit = get_font("Helvetica", 13, bold=True)

    speed_txt = font_large.render(f"{mph_val}", True, COLOR_WHITE)
    unit_txt = font_unit.render("MPH", True, COLOR_TEXT_MUTED)

    surface.blit(speed_txt, (center_x - speed_txt.get_width() // 2, center_y - 28))
    surface.blit(unit_txt, (center_x - unit_txt.get_width() // 2, center_y + 18))

    draw_glass_box(surface, pygame.Rect(20, 20, 390, 112), bg_color=(15, 18, 24, 180), border_color=GLASS_BORDER_HI, border_radius=18, border_width=2)
    font_hud = get_font("Helvetica", 13, bold=True)
    dist_txt = font_hud.render(f"MAP: {get_current_map()['name'].upper()}   |   COMBO: {combo_multiplier:.1f}x", True, COLOR_WHITE)
    cash_txt = font_hud.render(f"DISTANCE: {int(score)} m   |   BANK: ${int(total_cash)}", True, COLOR_TEXT_MUTED)
    run_cash_txt = font_hud.render(f"RUN EARNINGS: +${session_cash_earned}", True, COLOR_SUCCESS)
    surface.blit(dist_txt, (36, 32))
    surface.blit(cash_txt, (36, 58))
    surface.blit(run_cash_txt, (36, 84))

    is_p_hover = hud_pause_rect.collidepoint(mouse_pos)
    draw_glass_box(surface, hud_pause_rect, bg_color=GLASS_BG_ACTIVE if is_p_hover else (15, 18, 24, 180), border_color=GLASS_BORDER_HI, border_radius=12)
    p_lbl = font_hud.render("II PAUSE", True, COLOR_TEXT_DARK if is_p_hover else COLOR_WHITE)
    surface.blit(p_lbl, (hud_pause_rect.centerx - p_lbl.get_width() // 2, hud_pause_rect.centery - p_lbl.get_height() // 2))

    if 82.0 <= current_angle < 102.0 and current_speed > 1.0:
        scrape_lbl = get_font("Helvetica", 18, bold=True).render("FENDER SCRAPE! +$$$", True, COLOR_GOLD)
        surface.blit(scrape_lbl, (WINDOW_WIDTH // 2 - scrape_lbl.get_width() // 2, 30))

async def main():
    global window, audio_enabled, browser_audio_unlocked, sound_click, sound_scrape, sound_slam, scrape_sound_cooldown
    global rear_wheel_img, front_wheel_img, game_state, total_cash, high_score
    global equipped_paint, equipped_map, equipped_underglow, throttle_level, brake_level
    global sfx_volume, music_volume, low_performance_mode, confirm_reset_active
    global previous_state_before_settings, active_stance, combo_multiplier
    global wheelie_combo_timer, wheelie_distance, session_cash_earned, scrape_cash_earned
    global angle, angular_velocity, speed, world_offset, wheel_spin, active_garage_tab
    global rear_susp_comp, rear_susp_vel, front_susp_comp, front_susp_vel
    global cam_x_offset, cam_y_offset, throttle_timer, brake_timer, shake_timer, shake_intensity
    global SPEED_VIGNETTE_SURF

    pygame.init()
    pygame.joystick.init()

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("SoFlow Wheelie Life - Web Edition")
    clock = pygame.time.Clock()

    window.fill((10, 12, 16))
    loading_lbl = get_font("Helvetica", 24, bold=True).render("LOADING ENGINE & MAPS...", True, COLOR_WHITE)
    window.blit(loading_lbl, (WINDOW_WIDTH//2 - loading_lbl.get_width()//2, WINDOW_HEIGHT//2 - 12))
    pygame.display.flip()
    await asyncio.sleep(0)

    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        audio_enabled = True
    except Exception:
        audio_enabled = False

    if audio_enabled:
        click_path = find_audio_asset("click")
        scrape_path = find_audio_asset("scrape")
        slam_path = find_audio_asset("slam")
        try: sound_click = pygame.mixer.Sound(click_path) if click_path else generate_tone_sound(880, 0.05, 0.25)
        except Exception: sound_click = generate_tone_sound(880, 0.05, 0.25)
        try: sound_scrape = pygame.mixer.Sound(scrape_path) if scrape_path else generate_noise_sound(0.2, 0.18)
        except Exception: sound_scrape = generate_noise_sound(0.2, 0.18)
        try: sound_slam = pygame.mixer.Sound(slam_path) if slam_path else generate_tone_sound(120, 0.15, 0.4)
        except Exception: sound_slam = generate_tone_sound(120, 0.15, 0.4)

    try:
        raw_wheel = pygame.image.load(get_asset_path("assets/wheel.png")).convert_alpha()
        bounds = raw_wheel.get_bounding_rect()
        tight = raw_wheel.subsurface(bounds)
        max_d = max(tight.get_size())
        cent = pygame.Surface((max_d, max_d), pygame.SRCALPHA)
        cent.blit(tight, ((max_d - tight.get_width()) // 2, (max_d - tight.get_height()) // 2))
        rear_wheel_img = pygame.transform.scale(cent, (REAR_WHEEL_SIZE, REAR_WHEEL_SIZE))
        front_wheel_img = pygame.transform.scale(cent, (FRONT_WHEEL_SIZE, FRONT_WHEEL_SIZE))
    except Exception:
        rear_wheel_img = generate_procedural_wheel(REAR_WHEEL_SIZE)
        front_wheel_img = generate_procedural_wheel(FRONT_WHEEL_SIZE)

    SPEED_VIGNETTE_SURF = build_speed_vignette_surface()
    await asyncio.sleep(0)

    for m in MAPS_CATALOG:
        PRE_RENDERED_SKIES[m["id"]] = build_sky_surface(m["sky_top"], m["sky_bottom"])
        if m.get("lens_filter"):
            LENS_OVERLAYS[m["lens_filter"]] = build_lens_overlay(m["lens_filter"])
        lamp_c = m.get("lamp_color")
        if lamp_c and lamp_c not in LAMP_GLOW_SURFACES:
            LAMP_GLOW_SURFACES[lamp_c] = build_lamp_glow_surface(lamp_c)
        await asyncio.sleep(0)

    await init_procedural_backgrounds()
    update_maps_catalog_layers()
    load_game_data()
    load_all_paint_assets()

    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for joy in joysticks: joy.init()

    while True:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        current_map = get_current_map()
        if scrape_sound_cooldown > 0:
            scrape_sound_cooldown = max(0.0, scrape_sound_cooldown - dt)

        # Dynamic Camera VFX: speed pull-back, wheelie upward tracking & spring shake
        if game_state == "PLAYING" and not low_performance_mode:
            target_cam_x = -min(70.0, speed * 2.3)
            target_cam_y = min(46.0, max(0.0, (angle - 12.0) * 0.55))
        else:
            target_cam_x = 0.0
            target_cam_y = 0.0

        lerp_t = min(1.0, dt * 6.5)
        cam_x_offset += (target_cam_x - cam_x_offset) * lerp_t
        cam_y_offset += (target_cam_y - cam_y_offset) * lerp_t

        shake_x, shake_y = 0.0, 0.0
        if shake_timer > 0:
            shake_timer -= 1
            shake_x = random.uniform(-shake_intensity, shake_intensity)
            shake_y = random.uniform(-shake_intensity, shake_intensity)
        else:
            shake_intensity = 0.0

        # Subtle high-speed chassis vibration & fender scrape micro-shake
        if game_state == "PLAYING" and not low_performance_mode:
            if 82.0 <= angle < 102.0 and speed > 1.0:
                shake_x += random.uniform(-2.2, 2.2)
                shake_y += random.uniform(-2.2, 2.2)
            elif speed > 18.0:
                vib = (speed - 18.0) * 0.08
                shake_y += random.uniform(-vib, vib)

        desired_music_stem = "music_menu" if game_state in ["MENU", "GARAGE"] else current_map.get("music_stem", "music_menu")
        update_bg_music(desired_music_stem)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                bank_session_cash()
                save_game_data(); pygame.quit(); sys.exit()

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN) and not browser_audio_unlocked:
                browser_audio_unlocked = True
                update_bg_music(desired_music_stem, force_restart=True)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm_reset_active:
                    if confirm_yes_rect.collidepoint(event.pos):
                        play_sfx(sound_click); reset_all_data_defaults(); confirm_reset_active = False
                    elif confirm_no_rect.collidepoint(event.pos):
                        play_sfx(sound_click); confirm_reset_active = False
                    continue

                if game_state == "MENU":
                    if play_btn_rect.collidepoint(event.pos): play_sfx(sound_click); reset_game()
                    elif garage_btn_rect.collidepoint(event.pos): play_sfx(sound_click); game_state = "GARAGE"
                    elif settings_btn_rect.collidepoint(event.pos): play_sfx(sound_click); previous_state_before_settings = "MENU"; game_state = "SETTINGS"

                elif game_state == "PLAYING":
                    if hud_pause_rect.collidepoint(event.pos):
                        play_sfx(sound_click); game_state = "PAUSED"

                elif game_state == "GARAGE":
                    if garage_back_rect.collidepoint(event.pos): play_sfx(sound_click); save_game_data(); game_state = "MENU"
                    elif tab_paints_rect.collidepoint(event.pos): play_sfx(sound_click); active_garage_tab = "PAINTS"
                    elif tab_underglow_rect.collidepoint(event.pos): play_sfx(sound_click); active_garage_tab = "UNDERGLOW"
                    elif tab_maps_rect.collidepoint(event.pos): play_sfx(sound_click); active_garage_tab = "MAPS"
                    elif tab_upgrades_rect.collidepoint(event.pos): play_sfx(sound_click); active_garage_tab = "UPGRADES"
                    else:
                        if active_garage_tab == "PAINTS":
                            for idx, item in enumerate(PAINTS_CATALOG):
                                card = pygame.Rect(50 + idx * 175, 180, 160, 240)
                                if card.collidepoint(event.pos):
                                    if item["id"] in owned_paints: equipped_paint = item["id"]; play_sfx(sound_click); save_game_data()
                                    elif total_cash >= item["price"]: total_cash -= item["price"]; owned_paints.append(item["id"]); equipped_paint = item["id"]; play_sfx(sound_click); save_game_data()
                        elif active_garage_tab == "UNDERGLOW":
                            for idx, item in enumerate(UNDERGLOW_CATALOG):
                                card = pygame.Rect(50 + idx * 175, 180, 160, 240)
                                if card.collidepoint(event.pos):
                                    if item["id"] in owned_underglows: equipped_underglow = item["id"]; play_sfx(sound_click); save_game_data()
                                    elif total_cash >= item["price"]: total_cash -= item["price"]; owned_underglows.append(item["id"]); equipped_underglow = item["id"]; play_sfx(sound_click); save_game_data()
                        elif active_garage_tab == "MAPS":
                            for idx, item in enumerate(MAPS_CATALOG):
                                card = pygame.Rect(35 + (idx % 4) * 235, 170 + (idx // 4) * 135, 220, 125)
                                if card.collidepoint(event.pos):
                                    if item["id"] in owned_maps: equipped_map = item["id"]; play_sfx(sound_click); save_game_data()
                                    elif total_cash >= item["price"]: total_cash -= item["price"]; owned_maps.append(item["id"]); equipped_map = item["id"]; play_sfx(sound_click); save_game_data()
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
                    if pause_resume_rect.collidepoint(event.pos): play_sfx(sound_click); game_state = "PLAYING"
                    elif pause_restart_rect.collidepoint(event.pos): play_sfx(sound_click); bank_session_cash(); reset_game()
                    elif pause_settings_rect.collidepoint(event.pos): play_sfx(sound_click); previous_state_before_settings = "PAUSED"; game_state = "SETTINGS"
                    elif pause_menu_rect.collidepoint(event.pos): play_sfx(sound_click); bank_session_cash(); save_game_data(); game_state = "MENU"

                elif game_state == "GAMEOVER":
                    if gameover_retry_rect.collidepoint(event.pos): play_sfx(sound_click); reset_game()
                    elif gameover_menu_rect.collidepoint(event.pos): play_sfx(sound_click); save_game_data(); game_state = "MENU"

                elif game_state == "SETTINGS":
                    if settings_back_rect.collidepoint(event.pos): play_sfx(sound_click); save_game_data(); game_state = previous_state_before_settings
                    elif sfx_minus_rect.collidepoint(event.pos): sfx_volume = max(0.0, round(sfx_volume - 0.1, 1)); play_sfx(sound_click)
                    elif sfx_plus_rect.collidepoint(event.pos): sfx_volume = min(1.0, round(sfx_volume + 0.1, 1)); play_sfx(sound_click)
                    elif music_minus_rect.collidepoint(event.pos): music_volume = max(0.0, round(music_volume - 0.1, 1)); play_sfx(sound_click)
                    elif music_plus_rect.collidepoint(event.pos): music_volume = min(1.0, round(music_volume + 0.1, 1)); play_sfx(sound_click)
                    elif low_perf_toggle_rect.collidepoint(event.pos): low_performance_mode = not low_performance_mode; play_sfx(sound_click); save_game_data()
                    elif reset_data_rect.collidepoint(event.pos): play_sfx(sound_click); confirm_reset_active = True

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if game_state == "PLAYING": game_state = "PAUSED"
                    elif game_state == "PAUSED": game_state = "PLAYING"
                    elif game_state == "SETTINGS": game_state = previous_state_before_settings
                    elif game_state == "GARAGE": save_game_data(); game_state = "MENU"
                elif game_state == "MENU":
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]: play_sfx(sound_click); reset_game()
                    elif event.key == pygame.K_g: play_sfx(sound_click); game_state = "GARAGE"
                    elif event.key == pygame.K_s: play_sfx(sound_click); previous_state_before_settings = "MENU"; game_state = "SETTINGS"
                elif game_state == "GAMEOVER":
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]: play_sfx(sound_click); reset_game()

        keys = pygame.key.get_pressed()
        if game_state == "PLAYING":
            is_w_pressed = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_RIGHT] or keys[pygame.K_d]
            is_space_pressed = keys[pygame.K_SPACE]
            is_braking = keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_a]
            is_shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_e]

            active_stance = "SEAT_STANDER" if (is_shift_pressed and angle > 15.0) else "SEATED"

            accel_mult = 1.0 + (throttle_level - 1) * 0.20
            brake_mult = 1.0 + (brake_level - 1) * 0.22

            if is_w_pressed:
                throttle_timer += dt
                surge = 1.0 if throttle_timer < 0.3 else min(1.85, 1.0 + (throttle_timer - 0.3) * 2.2)
                speed = min(speed + 0.32 * surge * accel_mult, 30.0)
                angular_velocity += (0.42 if active_stance == "SEAT_STANDER" else 0.38) * surge * accel_mult

                if not low_performance_mode and speed < 10.0 and random.random() < 0.55:
                    smoke_particles.append([
                        pivot_x + cam_x_offset - 28 + random.uniform(-6, 6),
                        GROUND_Y + cam_y_offset - 10,
                        random.uniform(-3.0, -1.0),
                        random.uniform(-1.5, -0.3),
                        random.uniform(7, 13),
                        160
                    ])
            else:
                throttle_timer = 0.0
                speed = max(0.0, speed - 0.025)

            if is_space_pressed and not is_w_pressed: angular_velocity += 0.45

            if is_braking:
                brake_timer += dt
                speed = max(0.0, speed - (0.04 + min(1.0, brake_timer / 0.8) * 0.08) * brake_mult)
                angular_velocity -= 0.45 * brake_mult
            else: brake_timer = 0.0

            if angle > 0:
                diff = angle - 55.0
                angular_velocity += (abs(diff) / 55.0) * 0.10 * (1.0 if diff > 0 else -1.0)

            angular_velocity *= 0.94
            angle += angular_velocity
            world_offset += speed
            wheel_spin = (wheel_spin + speed * 7) % 360

            if angle <= 0:
                if angular_velocity < -0.4: play_sfx(sound_slam); trigger_screen_shake(10.0, 9)
                angle = 0; angular_velocity = 0

            if angle > 5.0:
                wheelie_combo_timer += dt
                combo_multiplier = min(5.0, 1.0 + int(wheelie_combo_timer // 2.0) * 0.5)
                wheelie_distance += speed * 0.15 * combo_multiplier
                if wheelie_distance > high_score: high_score = wheelie_distance

                if 82.0 <= angle < 102.0 and speed > 1.0:
                    scrape_cash_earned += dt * 30.0
                    if scrape_sound_cooldown <= 0.0:
                        play_sfx(sound_scrape)
                        scrape_sound_cooldown = 0.22
                    if not low_performance_mode:
                        for _ in range(2):
                            sparks.append([
                                pivot_x + cam_x_offset - 35 + random.uniform(-6, 6),
                                GROUND_Y + cam_y_offset - 12,
                                random.uniform(-6.0, -2.0),
                                random.uniform(-4.0, -1.0),
                                random.randint(10, 18)
                            ])
            else:
                wheelie_combo_timer = 0.0
                combo_multiplier = 1.0

            session_cash_earned = int(wheelie_distance * 0.50) + int(scrape_cash_earned)

            if angle >= 102.0:
                game_state = "GAMEOVER"
                bank_session_cash()

        rendered_g_y = int(GROUND_Y + cam_y_offset + shake_y)
        rendered_bike_x = pivot_x + cam_x_offset + shake_x

        window.blit(PRE_RENDERED_SKIES[equipped_map], (0, 0))

        if current_map.get("has_stars", False):
            window.blit(STARS_SURF, (0, int(cam_y_offset * 0.15)))

        if current_map.get("has_sun", False):
            sun_y = int(235 + cam_y_offset * 0.2)
            pygame.draw.circle(window, (255, 225, 130), (WINDOW_WIDTH // 2, sun_y), 48)
            if not low_performance_mode:
                sun_glow = pygame.Surface((220, 220), pygame.SRCALPHA)
                pygame.draw.circle(sun_glow, (255, 190, 80, 55), (110, 110), 105)
                window.blit(sun_glow, (WINDOW_WIDTH // 2 - 110, sun_y - 110))

        if current_map["far_layer"]:
            far_s = (world_offset * 0.15) % 1000
            far_y = int(80 + cam_y_offset * 0.35 + shake_y * 0.3)
            window.blit(current_map["far_layer"], (int(-far_s), far_y))
            window.blit(current_map["far_layer"], (int(-far_s + 1000), far_y))

        if current_map["near_layer"]:
            near_s = (world_offset * 0.35) % 1000
            near_y = int(120 + cam_y_offset * 0.65 + shake_y * 0.6)
            window.blit(current_map["near_layer"], (int(-near_s), near_y))
            window.blit(current_map["near_layer"], (int(-near_s + 1000), near_y))

        pygame.draw.rect(window, current_map["road_color"], (0, rendered_g_y, WINDOW_WIDTH, WINDOW_HEIGHT - rendered_g_y))

        if current_map.get("cyber_grid", False) and not low_performance_mode:
            pygame.draw.line(window, (255, 0, 180), (0, rendered_g_y), (WINDOW_WIDTH, rendered_g_y), 3)
            for gx in range(int((-world_offset) % 100), WINDOW_WIDTH, 100):
                pygame.draw.line(window, (0, 220, 255), (gx, rendered_g_y), (gx - 60, WINDOW_HEIGHT), 2)
        elif current_map.get("lava_edge", False):
            pygame.draw.line(window, (255, 95, 20), (0, rendered_g_y), (WINDOW_WIDTH, rendered_g_y), 4)
        elif current_map.get("snow_edge", False):
            pygame.draw.rect(window, (225, 240, 255), (0, rendered_g_y, WINDOW_WIDTH, 6))

        # Motion-blurred road dashes (stretch horizontally as speed climbs)
        dash_len = 40 + (int(speed * 2.1) if (not low_performance_mode and speed > 10.0) else 0)
        for x in range(int((-world_offset) % 110) - 60, WINDOW_WIDTH + 60, 110):
            pygame.draw.line(window, current_map["dash_color"][:3], (x, rendered_g_y + 30), (x + dash_len, rendered_g_y + 30), 4)

        render_map_weather_and_props(window, current_map, rendered_g_y, speed if game_state == "PLAYING" else 3.0, dt)

        active_frame = frame_images_seatstand[equipped_paint] if active_stance == "SEAT_STANDER" else frame_images_normal[equipped_paint]
        active_rear_orig = SEATSTAND_REAR_AXLE_ORIGIN if active_stance == "SEAT_STANDER" else REAR_AXLE_ORIGIN
        active_axle_off = SEATSTAND_AXLE_OFFSET_VECTOR if active_stance == "SEAT_STANDER" else AXLE_OFFSET_VECTOR

        rear_w_pos = pygame.math.Vector2(rendered_bike_x, rendered_g_y - (REAR_WHEEL_SIZE // 2))
        frame_pivot = rear_w_pos + pygame.math.Vector2(0, rear_susp_comp).rotate(-angle)
        frame_front_m = frame_pivot + active_axle_off.rotate(-angle)
        front_w_pos = frame_pivot + (active_axle_off.normalize() * (active_axle_off.length() - front_susp_comp)).rotate(-angle)

        # Underglow + wet asphalt reflection for NYC / Cyber rain maps
        glow_c = get_current_underglow_color()
        glow_surf = pygame.Surface((260, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*glow_c, 75), (0, 0, 260, 50))
        window.blit(glow_surf, (int(rear_w_pos.x - 30), rendered_g_y - 18))
        if current_map.get("wet_road", False) and not low_performance_mode:
            wet_surf = pygame.Surface((280, 32), pygame.SRCALPHA)
            pygame.draw.ellipse(wet_surf, (*glow_c, 42), (0, 0, 280, 32))
            window.blit(wet_surf, (int(rear_w_pos.x - 40), rendered_g_y + 8))

        for sm in smoke_particles[:]:
            sm[0] += sm[2]
            sm[1] += sm[3]
            sm[4] += 0.35
            sm[5] -= 6
            if sm[5] <= 0:
                smoke_particles.remove(sm)
            else:
                s_surf = pygame.Surface((int(sm[4]*2), int(sm[4]*2)), pygame.SRCALPHA)
                pygame.draw.circle(s_surf, (220, 225, 235, max(0, int(sm[5]))), (int(sm[4]), int(sm[4])), int(sm[4]))
                window.blit(s_surf, (int(sm[0] - sm[4]), int(sm[1] - sm[4])))

        # Record & render multi-frame motion blur ghost trail on bike & wheels at high speed
        if game_state == "PLAYING" and not low_performance_mode:
            bike_ghost_history.append((active_frame, angle, (frame_pivot.x, frame_pivot.y), active_rear_orig, (rear_w_pos.x, rear_w_pos.y), (front_w_pos.x, front_w_pos.y), wheel_spin))
            if speed > 11.0 and len(bike_ghost_history) >= 2:
                blur_ratio = min(1.0, (speed - 11.0) / 18.0)
                ghosts = list(bike_ghost_history)[:-1]
                for g_idx, g_data in enumerate(ghosts):
                    g_frame, g_ang, g_piv, g_orig, g_rw, g_fw, g_spin = g_data
                    trail_shift = (len(ghosts) - g_idx) * (speed * 0.75)
                    g_alpha = int((18 + g_idx * 14) * blur_ratio)
                    if g_alpha > 4:
                        g_rw_img = pygame.transform.rotate(rear_wheel_img, -g_spin)
                        g_rw_img.set_alpha(g_alpha)
                        window.blit(g_rw_img, g_rw_img.get_rect(center=(int(g_rw[0] - trail_shift), int(g_rw[1]))))

                        rotate_around_pivot(window, g_frame, g_ang, (g_piv[0] - trail_shift, g_piv[1]), g_orig, alpha=g_alpha)

                        g_fw_img = pygame.transform.rotate(front_wheel_img, -g_spin)
                        g_fw_img.set_alpha(g_alpha)
                        window.blit(g_fw_img, g_fw_img.get_rect(center=(int(g_fw[0] - trail_shift), int(g_fw[1]))))

        rot_rear = pygame.transform.rotate(rear_wheel_img, -wheel_spin)
        window.blit(rot_rear, rot_rear.get_rect(center=(int(rear_w_pos.x), int(rear_w_pos.y))))
        rotate_around_pivot(window, active_frame, angle, (frame_pivot.x, frame_pivot.y), active_rear_orig)
        rot_front = pygame.transform.rotate(front_wheel_img, -wheel_spin)
        window.blit(rot_front, rot_front.get_rect(center=(int(front_w_pos.x), int(front_w_pos.y))))

        draw_suspension_hardware(window, rear_w_pos, frame_pivot, front_w_pos, frame_front_m)

        for sp in sparks[:]:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[3] += 0.25
            sp[4] -= 1
            if sp[4] <= 0:
                sparks.remove(sp)
            else:
                pygame.draw.circle(window, (255, 210, 80), (int(sp[0]), int(sp[1])), 3)

        if game_state == "PLAYING":
            render_motion_blur_vfx(window, speed, dt)

        if not low_performance_mode and current_map.get("lens_filter") in LENS_OVERLAYS:
            window.blit(LENS_OVERLAYS[current_map["lens_filter"]], (0, 0))

        if game_state == "PLAYING":
            draw_forza_speedometer(window, speed, 30.0, angle, wheelie_distance, mouse_pos)

        elif game_state == "MENU":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill(GLASS_OVERLAY_DARK)
            window.blit(glass_bg, (0, 0))
            header = pygame.Rect(WINDOW_WIDTH // 2 - 280, 25, 560, 100)
            draw_glass_box(window, header, bg_color=(255, 255, 255, 15), border_color=GLASS_BORDER_HI, border_radius=22)
            t_txt = get_font("Helvetica", 48, bold=True).render("SOFLOW WHEELIE LIFE", True, COLOR_WHITE)
            sub_txt = get_font("Helvetica", 15, bold=True).render(f"BANK: ${int(total_cash)}   |   BEST WHEELIE: {int(high_score)} m", True, COLOR_TEXT_MUTED)
            window.blit(t_txt, (header.centerx - t_txt.get_width() // 2, header.y + 14))
            window.blit(sub_txt, (header.centerx - sub_txt.get_width() // 2, header.y + 70))

            for b_txt_str, rect in [("PLAY [ENTER]", play_btn_rect), ("GARAGE [G]", garage_btn_rect), ("SETTINGS [S]", settings_btn_rect)]:
                is_h = rect.collidepoint(mouse_pos)
                draw_glass_box(window, rect, bg_color=GLASS_BG_ACTIVE if is_h else GLASS_BG_CARD, border_color=COLOR_WHITE if is_h else GLASS_BORDER_SUBTLE, border_radius=16)
                txt = get_font("Helvetica", 18, bold=True).render(b_txt_str, True, COLOR_TEXT_DARK if is_h else COLOR_WHITE)
                window.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        elif game_state == "GARAGE":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((8, 10, 14, 235))
            window.blit(glass_bg, (0, 0))

            title_font = get_font("Helvetica", 28, bold=True)
            hud_font = get_font("Helvetica", 15, bold=True)
            item_title_font = get_font("Helvetica", 13, bold=True)
            btn_font = get_font("Helvetica", 15, bold=True)

            is_back_hover = garage_back_rect.collidepoint(mouse_pos)
            draw_glass_box(window, garage_back_rect, bg_color=GLASS_BG_CARD_HOVER if is_back_hover else GLASS_BG_CARD, border_radius=12)
            back_txt = hud_font.render("< BACK", True, COLOR_WHITE)
            window.blit(back_txt, (garage_back_rect.centerx - back_txt.get_width() // 2, garage_back_rect.centery - back_txt.get_height() // 2))

            window.blit(title_font.render("GARAGE & CUSTOM SHOP", True, COLOR_WHITE), (190, 34))
            window.blit(hud_font.render(f"CASH: ${int(total_cash)}", True, COLOR_SUCCESS), (WINDOW_WIDTH - 180, 40))

            tabs = [("PAINTS", tab_paints_rect), ("UNDERGLOW", tab_underglow_rect), ("MAPS", tab_maps_rect), ("UPGRADES", tab_upgrades_rect)]
            for tab_name, rect in tabs:
                is_active = (active_garage_tab == tab_name)
                is_hover = rect.collidepoint(mouse_pos)
                draw_glass_box(window, rect, bg_color=GLASS_BG_ACTIVE if is_active else (GLASS_BG_CARD_HOVER if is_hover else GLASS_BG_CARD), border_radius=14)
                t_txt = btn_font.render(tab_name, True, COLOR_TEXT_DARK if is_active else COLOR_WHITE)
                window.blit(t_txt, (rect.centerx - t_txt.get_width() // 2, rect.centery - t_txt.get_height() // 2))

            if active_garage_tab == "PAINTS":
                for idx, item in enumerate(PAINTS_CATALOG):
                    card_rect = pygame.Rect(50 + idx * 175, 180, 160, 240)
                    is_owned = item["id"] in owned_paints; is_eq = (equipped_paint == item["id"]); is_hover = card_rect.collidepoint(mouse_pos)
                    draw_glass_box(window, card_rect, bg_color=(255, 255, 255, 35) if is_hover else GLASS_BG_CARD, border_color=COLOR_WHITE if is_eq else GLASS_BORDER_SUBTLE, border_radius=16)

                    preview_rect = pygame.Rect(card_rect.x + 20, card_rect.y + 20, 120, 70)
                    pygame.draw.rect(window, item["hud_color"], preview_rect, border_radius=10)
                    name_lbl = item_title_font.render(item["name"], True, COLOR_WHITE)
                    window.blit(name_lbl, (card_rect.centerx - name_lbl.get_width() // 2, card_rect.y + 105))

                    btn_box = pygame.Rect(card_rect.x + 15, card_rect.y + 175, 130, 40)
                    b_txt_str = "EQUIPPED" if is_eq else ("EQUIP" if is_owned else f"${item['price']}")
                    draw_glass_box(window, btn_box, bg_color=GLASS_BG_ACTIVE if is_eq else GLASS_BG_CARD_HOVER, border_radius=10)
                    b_txt = hud_font.render(b_txt_str, True, COLOR_TEXT_DARK if is_eq else COLOR_WHITE)
                    window.blit(b_txt, (btn_box.centerx - b_txt.get_width() // 2, btn_box.centery - b_txt.get_height() // 2))

            elif active_garage_tab == "UNDERGLOW":
                for idx, item in enumerate(UNDERGLOW_CATALOG):
                    card_rect = pygame.Rect(50 + idx * 175, 180, 160, 240)
                    is_owned = item["id"] in owned_underglows; is_eq = (equipped_underglow == item["id"]); is_hover = card_rect.collidepoint(mouse_pos)
                    draw_glass_box(window, card_rect, bg_color=(255, 255, 255, 35) if is_hover else GLASS_BG_CARD, border_color=COLOR_WHITE if is_eq else GLASS_BORDER_SUBTLE, border_radius=16)

                    preview_rect = pygame.Rect(card_rect.x + 20, card_rect.y + 20, 120, 70)
                    pygame.draw.rect(window, (15, 15, 20), preview_rect, border_radius=10)
                    pygame.draw.ellipse(window, item["color"], (preview_rect.x + 10, preview_rect.y + 20, 100, 30))
                    name_lbl = item_title_font.render(item["name"], True, COLOR_WHITE)
                    window.blit(name_lbl, (card_rect.centerx - name_lbl.get_width() // 2, card_rect.y + 105))

                    btn_box = pygame.Rect(card_rect.x + 15, card_rect.y + 175, 130, 40)
                    b_txt_str = "EQUIPPED" if is_eq else ("EQUIP" if is_owned else f"${item['price']}")
                    draw_glass_box(window, btn_box, bg_color=GLASS_BG_ACTIVE if is_eq else GLASS_BG_CARD_HOVER, border_radius=10)
                    b_txt = hud_font.render(b_txt_str, True, COLOR_TEXT_DARK if is_eq else COLOR_WHITE)
                    window.blit(b_txt, (btn_box.centerx - b_txt.get_width() // 2, btn_box.centery - b_txt.get_height() // 2))

            elif active_garage_tab == "MAPS":
                for idx, item in enumerate(MAPS_CATALOG):
                    col, row = idx % 4, idx // 4
                    card_rect = pygame.Rect(35 + col * 235, 170 + row * 135, 220, 125)
                    is_owned = item["id"] in owned_maps; is_eq = (equipped_map == item["id"])
                    draw_glass_box(window, card_rect, bg_color=(255, 255, 255, 35) if card_rect.collidepoint(mouse_pos) else GLASS_BG_CARD, border_color=COLOR_WHITE if is_eq else GLASS_BORDER_SUBTLE, border_radius=14)
                    window.blit(item_title_font.render(item["name"], True, COLOR_WHITE), (card_rect.x + 15, card_rect.y + 15))

                    btn_box = pygame.Rect(card_rect.x + 100, card_rect.y + 70, 110, 35)
                    b_txt_str = "EQUIPPED" if is_eq else ("EQUIP" if is_owned else f"${item['price']}")
                    draw_glass_box(window, btn_box, bg_color=GLASS_BG_ACTIVE if is_eq else GLASS_BG_CARD_HOVER, border_radius=8)
                    b_txt = hud_font.render(b_txt_str, True, COLOR_TEXT_DARK if is_eq else COLOR_WHITE)
                    window.blit(b_txt, (btn_box.centerx - b_txt.get_width() // 2, btn_box.centery - b_txt.get_height() // 2))

            elif active_garage_tab == "UPGRADES":
                t_card = pygame.Rect(120, 180, 340, 240)
                draw_glass_box(window, t_card, bg_color=GLASS_BG_CARD, border_radius=20)
                window.blit(btn_font.render("THROTTLE ENGINE STAGE", True, COLOR_WHITE), (t_card.x + 35, t_card.y + 25))
                window.blit(hud_font.render(f"Stage Level: {throttle_level} / 4", True, COLOR_TEXT_MUTED), (t_card.x + 35, t_card.y + 65))

                t_btn = pygame.Rect(t_card.x + 70, t_card.y + 155, 200, 48)
                t_str = "MAX LEVEL" if throttle_level >= 4 else f"UPGRADE ${UPGRADE_PRICES['throttle'][throttle_level + 1]}"
                draw_glass_box(window, t_btn, bg_color=GLASS_BG_ACTIVE if throttle_level >= 4 else GLASS_BG_CARD_HOVER, border_radius=12)
                t_txt = btn_font.render(t_str, True, COLOR_TEXT_DARK if throttle_level >= 4 else COLOR_WHITE)
                window.blit(t_txt, (t_btn.centerx - t_txt.get_width() // 2, t_btn.centery - t_txt.get_height() // 2))

                b_card = pygame.Rect(540, 180, 340, 240)
                draw_glass_box(window, b_card, bg_color=GLASS_BG_CARD, border_radius=20)
                window.blit(btn_font.render("REAR BRAKE STAGE", True, COLOR_WHITE), (b_card.x + 35, b_card.y + 25))
                window.blit(hud_font.render(f"Stage Level: {brake_level} / 4", True, COLOR_TEXT_MUTED), (b_card.x + 35, b_card.y + 65))

                b_btn = pygame.Rect(b_card.x + 70, b_card.y + 155, 200, 48)
                b_str = "MAX LEVEL" if brake_level >= 4 else f"UPGRADE ${UPGRADE_PRICES['brake'][brake_level + 1]}"
                draw_glass_box(window, b_btn, bg_color=GLASS_BG_ACTIVE if brake_level >= 4 else GLASS_BG_CARD_HOVER, border_radius=12)
                b_txt = btn_font.render(b_str, True, COLOR_TEXT_DARK if brake_level >= 4 else COLOR_WHITE)
                window.blit(b_txt, (b_btn.centerx - b_txt.get_width() // 2, b_btn.centery - b_txt.get_height() // 2))

        elif game_state == "SETTINGS":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((8, 10, 14, 235))
            window.blit(glass_bg, (0, 0))
            panel = pygame.Rect(WINDOW_WIDTH // 2 - 320, 100, 640, 360)
            draw_glass_box(window, panel, bg_color=GLASS_BG_CARD, border_color=GLASS_BORDER_SUBTLE, border_radius=20)

            lbl_font = get_font("Helvetica", 18, bold=True)
            btn_font = get_font("Helvetica", 15, bold=True)

            window.blit(lbl_font.render(f"SFX VOLUME: {int(sfx_volume * 100)}%", True, COLOR_WHITE), (panel.x + 40, 140))
            draw_glass_box(window, sfx_minus_rect, bg_color=GLASS_BG_CARD_HOVER, border_radius=10)
            draw_glass_box(window, sfx_plus_rect, bg_color=GLASS_BG_CARD_HOVER, border_radius=10)
            window.blit(lbl_font.render("-", True, COLOR_WHITE), (sfx_minus_rect.centerx - 5, sfx_minus_rect.centery - 12))
            window.blit(lbl_font.render("+", True, COLOR_WHITE), (sfx_plus_rect.centerx - 6, sfx_plus_rect.centery - 12))

            window.blit(lbl_font.render(f"MUSIC VOLUME: {int(music_volume * 100)}%", True, COLOR_WHITE), (panel.x + 40, 200))
            draw_glass_box(window, music_minus_rect, bg_color=GLASS_BG_CARD_HOVER, border_radius=10)
            draw_glass_box(window, music_plus_rect, bg_color=GLASS_BG_CARD_HOVER, border_radius=10)
            window.blit(lbl_font.render("-", True, COLOR_WHITE), (music_minus_rect.centerx - 5, music_minus_rect.centery - 12))
            window.blit(lbl_font.render("+", True, COLOR_WHITE), (music_plus_rect.centerx - 6, music_plus_rect.centery - 12))

            is_h = low_perf_toggle_rect.collidepoint(mouse_pos)
            draw_glass_box(window, low_perf_toggle_rect, bg_color=(50, 205, 50, 180) if low_performance_mode else (GLASS_BG_CARD_HOVER if is_h else GLASS_BG_CARD), border_radius=14)
            mode_label = "CHROMEBOOK MODE: ON (MAX FPS)" if low_performance_mode else "GRAPHICS: BEAUTIFUL MODE (FULL VFX)"
            p_txt = btn_font.render(mode_label, True, COLOR_TEXT_DARK if low_performance_mode else COLOR_WHITE)
            window.blit(p_txt, (low_perf_toggle_rect.centerx - p_txt.get_width() // 2, low_perf_toggle_rect.centery - p_txt.get_height() // 2))

            draw_glass_box(window, reset_data_rect, bg_color=(220, 60, 60, 100), border_radius=14)
            r_txt = btn_font.render("RESET SAVE PROGRESS", True, COLOR_WHITE)
            window.blit(r_txt, (reset_data_rect.centerx - r_txt.get_width() // 2, reset_data_rect.centery - r_txt.get_height() // 2))

            draw_glass_box(window, settings_back_rect, bg_color=GLASS_BG_CARD, border_radius=12)
            b_txt = btn_font.render("< BACK", True, COLOR_WHITE)
            window.blit(b_txt, (settings_back_rect.centerx - b_txt.get_width() // 2, settings_back_rect.centery - b_txt.get_height() // 2))

            if confirm_reset_active:
                dialog_rect = pygame.Rect(WINDOW_WIDTH // 2 - 220, 140, 440, 220)
                draw_glass_box(window, dialog_rect, bg_color=(20, 24, 32, 245), border_radius=20)
                window.blit(get_font("Helvetica", 18, bold=True).render("CONFIRM DATA RESET?", True, COLOR_DANGER), (dialog_rect.centerx - 100, dialog_rect.y + 30))

                draw_glass_box(window, confirm_yes_rect, bg_color=(220, 60, 60, 220), border_radius=10)
                window.blit(btn_font.render("YES, RESET", True, COLOR_WHITE), (confirm_yes_rect.centerx - 40, confirm_yes_rect.centery - 10))

                draw_glass_box(window, confirm_no_rect, bg_color=GLASS_BG_CARD, border_radius=10)
                window.blit(btn_font.render("CANCEL", True, COLOR_WHITE), (confirm_no_rect.centerx - 30, confirm_no_rect.centery - 10))

        elif game_state == "PAUSED":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((10, 12, 16, 180))
            window.blit(glass_bg, (0, 0))
            p_modal = pygame.Rect(WINDOW_WIDTH // 2 - 180, 65, 360, 370)
            draw_glass_box(window, p_modal, bg_color=(255, 255, 255, 25), border_radius=22)
            window.blit(get_font("Helvetica", 36, bold=True).render("PAUSED", True, COLOR_WHITE), (p_modal.centerx - 65, p_modal.y + 30))

            for b_name, rect in [("RESUME", pause_resume_rect), ("RESTART", pause_restart_rect), ("SETTINGS", pause_settings_rect), ("MAIN MENU", pause_menu_rect)]:
                is_h = rect.collidepoint(mouse_pos)
                draw_glass_box(window, rect, bg_color=GLASS_BG_ACTIVE if is_h else GLASS_BG_CARD, border_radius=14)
                t = get_font("Helvetica", 18, bold=True).render(b_name, True, COLOR_TEXT_DARK if is_h else COLOR_WHITE)
                window.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

        elif game_state == "GAMEOVER":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((10, 12, 16, 220))
            window.blit(glass_bg, (0, 0))
            modal = pygame.Rect(WINDOW_WIDTH // 2 - 260, 50, 520, 380)
            draw_glass_box(window, modal, bg_color=(25, 28, 36, 240), border_color=GLASS_BORDER_HI, border_radius=24, border_width=2)

            go_txt = get_font("Helvetica", 48, bold=True).render("LOOPED OUT!", True, COLOR_DANGER)
            window.blit(go_txt, (modal.centerx - go_txt.get_width() // 2, modal.y + 30))

            stat_font = get_font("Helvetica", 20, bold=True)
            dist_lbl = stat_font.render(f"DISTANCE: {int(wheelie_distance)} m   (BEST: {int(high_score)} m)", True, COLOR_WHITE)
            earned_lbl = stat_font.render(f"CASH EARNED: +${session_cash_earned}", True, COLOR_SUCCESS)
            bank_lbl = stat_font.render(f"TOTAL BANK: ${int(total_cash)}", True, COLOR_GOLD)

            window.blit(dist_lbl, (modal.centerx - dist_lbl.get_width() // 2, modal.y + 115))
            window.blit(earned_lbl, (modal.centerx - earned_lbl.get_width() // 2, modal.y + 160))
            window.blit(bank_lbl, (modal.centerx - bank_lbl.get_width() // 2, modal.y + 205))

            for b_name, rect in [("TRY AGAIN [SPACE]", gameover_retry_rect), ("MAIN MENU", gameover_menu_rect)]:
                is_h = rect.collidepoint(mouse_pos)
                draw_glass_box(window, rect, bg_color=GLASS_BG_ACTIVE if is_h else GLASS_BG_CARD, border_color=COLOR_WHITE if is_h else GLASS_BORDER_SUBTLE, border_radius=14)
                t = get_font("Helvetica", 16, bold=True).render(b_name, True, COLOR_TEXT_DARK if is_h else COLOR_WHITE)
                window.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
