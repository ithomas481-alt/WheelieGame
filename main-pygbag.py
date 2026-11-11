import pygame
import sys
import math
import random
import json
import array
import os
import asyncio

# WebAssembly & Browser friendly relative path helper
def get_asset_path(relative_path):
    return relative_path.lstrip('/')

# =========================================================================
# GLOBALS & CONSTANTS
# =========================================================================
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 500
GROUND_Y = 400

COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_MAIN = (245, 245, 250)
COLOR_TEXT_MUTED = (160, 165, 175)
COLOR_TEXT_DARK = (15, 15, 20)
COLOR_DANGER = (220, 60, 60)
COLOR_SUCCESS = (50, 205, 50)

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

# State & Configuration
sfx_volume = 0.7
music_volume = 0.5
low_performance_mode = False
audio_enabled = False

current_playing_music = None
music_channel = None
active_music_sound = None

MENU_MUSIC_FILE = get_asset_path("assets/music_menu.ogg")

sound_click = None
sound_scrape = None
sound_slam = None

rear_wheel_img = None
front_wheel_img = None

# Pre-rendered Sky Surface Cache (Optimization #2)
PRE_RENDERED_SKIES = {}
LENS_OVERLAYS = {}

# Game Save State
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

# =========================================================================
# PROCEDURAL FALLBACK GENERATORS FOR ASSETS
# =========================================================================
def generate_procedural_wheel(size, rim_color=(200, 200, 210), spoke_count=12):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    radius = size // 2 - 2
    
    # Outer Tire
    pygame.draw.circle(surf, (20, 22, 26), (center, center), radius)
    pygame.draw.circle(surf, (35, 38, 45), (center, center), radius, 5)
    
    # Rim & Spokes
    rim_radius = radius - 8
    pygame.draw.circle(surf, rim_color, (center, center), rim_radius, 4)
    for i in range(spoke_count):
        ang = (2 * math.pi / spoke_count) * i
        x2 = center + int(math.cos(ang) * rim_radius)
        y2 = center + int(math.sin(ang) * rim_radius)
        pygame.draw.line(surf, (180, 185, 195), (center, center), (x2, y2), 2)
        
    # Center Hub
    pygame.draw.circle(surf, (50, 55, 65), (center, center), 9)
    pygame.draw.circle(surf, (230, 235, 245), (center, center), 5)
    return surf

def generate_procedural_frame(width, height, color_rgb, is_seatstand=False):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Main Tubing Joints
    r_axle = (width * 0.12, height * 0.80)
    f_axle = (width * 0.78, height * 0.80)
    bb = (width * 0.38, height * 0.75)
    seat_joint = (width * 0.32, height * 0.38)
    head_tube = (width * 0.68, height * 0.28)
    bars = (width * 0.64, height * 0.12)
    
    # Metal Frame Lines
    pygame.draw.line(surf, color_rgb, r_axle, bb, 7)
    pygame.draw.line(surf, color_rgb, r_axle, seat_joint, 7)
    pygame.draw.line(surf, color_rgb, bb, seat_joint, 8)
    pygame.draw.line(surf, color_rgb, bb, head_tube, 8)
    pygame.draw.line(surf, color_rgb, seat_joint, head_tube, 7)
    pygame.draw.line(surf, color_rgb, head_tube, f_axle, 7)
    pygame.draw.line(surf, (40, 40, 45), head_tube, bars, 6)
    pygame.draw.line(surf, (20, 20, 25), (bars[0]-15, bars[1]), (bars[0]+15, bars[1]), 5)

    # Rider Figure
    rider_color = (230, 235, 245)
    if is_seatstand:
        # Standing high on seat
        foot_pos = (seat_joint[0], seat_joint[1] - 8)
        hip = (seat_joint[0] - 10, seat_joint[1] - 45)
        head = (hip[0] + 15, hip[1] - 35)
        pygame.draw.line(surf, (30, 35, 45), foot_pos, hip, 6) # Legs
        pygame.draw.line(surf, rider_color, hip, head, 9)       # Torso
        pygame.draw.circle(surf, rider_color, (int(head[0]), int(head[1])), 10) # Head
        pygame.draw.line(surf, rider_color, (hip[0]+5, hip[1]-20), bars, 5)     # Arms
    else:
        # Seated riding position
        seat_pos = (seat_joint[0] - 12, seat_joint[1] - 10)
        pygame.draw.rect(surf, (20, 20, 25), (seat_pos[0]-15, seat_pos[1], 30, 8), border_radius=3)
        hip = (seat_pos[0], seat_pos[1] - 15)
        head = (hip[0] + 25, hip[1] - 30)
        pygame.draw.line(surf, (30, 35, 45), bb, hip, 6)
        pygame.draw.line(surf, rider_color, hip, head, 9)
        pygame.draw.circle(surf, rider_color, (int(head[0]), int(head[1])), 10)
        pygame.draw.line(surf, rider_color, (hip[0]+10, hip[1]-15), bars, 5)

    return surf

# =========================================================================
# CATALOGS & DATA
# =========================================================================
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
    {"id": 0, "name": "NYC Midnight", "price": 0, "sky_top": (6, 10, 24), "sky_bottom": (16, 28, 48), "road_color": (32, 35, 42), "dash_color": (240, 245, 255, 180), "far_layer": None, "near_layer": None, "has_stars": True, "has_rain": True, "streetlights": True, "lamp_color": (255, 240, 180), "lens_filter": "NYC_NIGHT_LENS", "music": get_asset_path("assets/music_nyc.ogg")},
    {"id": 1, "name": "Sunset Highway", "price": 180, "sky_top": (40, 15, 60), "sky_bottom": (245, 110, 50), "road_color": (45, 38, 42), "dash_color": (255, 210, 80, 210), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 190, 90), "lens_filter": "SUNSET_AMBER_LENS", "music": get_asset_path("assets/music_sunset.ogg")},
    {"id": 2, "name": "Neon Cyber Grid", "price": 450, "sky_top": (12, 4, 28), "sky_bottom": (35, 10, 60), "road_color": (18, 14, 28), "dash_color": (0, 240, 255, 220), "far_layer": None, "near_layer": None, "has_stars": True, "has_rain": True, "streetlights": True, "lamp_color": (255, 0, 160), "lens_filter": "CYBER_SCANLINE_LENS", "music": get_asset_path("assets/music_cyber.ogg")},
    {"id": 3, "name": "Cherry Blossom Forest", "price": 320, "sky_top": (38, 15, 45), "sky_bottom": (240, 130, 175), "road_color": (42, 28, 38), "dash_color": (255, 190, 220, 210), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": False, "lamp_color": (255, 180, 220), "has_petals": True, "lens_filter": "CHERRY_BLOOM_LENS", "music": get_asset_path("assets/music_cherry.ogg")},
    {"id": 4, "name": "California Coast", "price": 500, "sky_top": (20, 30, 75), "sky_bottom": (255, 140, 40), "road_color": (48, 40, 36), "dash_color": (255, 220, 120, 220), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 220, 140), "lens_filter": "CALIFORNIA_GOLDEN_LENS", "music": get_asset_path("assets/music_cali.ogg")},
    {"id": 5, "name": "Alpine Mountain Pass", "price": 10000, "sky_top": (10, 25, 50), "sky_bottom": (140, 185, 220), "road_color": (50, 58, 68), "dash_color": (230, 245, 255, 230), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (180, 225, 255), "has_snow": True, "lens_filter": "ALPINE_FROST_LENS", "music": get_asset_path("assets/music_alpine.ogg")},
    {"id": 6, "name": "Volcanic Magma Canyon", "price": 10000, "sky_top": (18, 4, 6), "sky_bottom": (180, 40, 15), "road_color": (28, 20, 24), "dash_color": (255, 90, 20, 240), "far_layer": None, "near_layer": None, "has_stars": False, "has_rain": False, "streetlights": True, "lamp_color": (255, 110, 30), "has_embers": True, "lens_filter": "VOLCANIC_GLOW_LENS", "music": get_asset_path("assets/music_volcano.ogg")}
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

# Audio Generators
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
        sound.set_volume(sfx_volume)
        sound.play()

def update_bg_music(target_music_file):
    global current_playing_music, active_music_sound, music_channel
    if not audio_enabled: return
    if current_playing_music == target_music_file:
        try:
            if music_channel and active_music_sound: music_channel.set_volume(music_volume)
            else: pygame.mixer.music.set_volume(music_volume)
        except Exception: pass
        return

    current_playing_music = target_music_file
    try: pygame.mixer.music.stop()
    except Exception: pass

    if music_channel:
        music_channel.stop()
        active_music_sound = None

    if not target_music_file or not os.path.exists(target_music_file): return

    try:
        pygame.mixer.music.load(target_music_file)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
        return
    except Exception: pass

    try:
        active_music_sound = pygame.mixer.Sound(target_music_file)
        if music_channel is None: music_channel = pygame.mixer.Channel(7)
        music_channel.set_volume(music_volume)
        music_channel.play(active_music_sound, loops=-1)
    except Exception: pass

# =========================================================================
# SAVE SYSTEM & UTILS
# =========================================================================
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

# =========================================================================
# PRE-RENDERED SKY GRADIENTS (OPTIMIZATION #2)
# =========================================================================
def build_sky_surface(sky_top, sky_bot):
    surf = pygame.Surface((WINDOW_WIDTH, 300))
    for y in range(300):
        ratio = y / 300.0
        r = int(sky_top[0] * (1 - ratio) + sky_bot[0] * ratio)
        g = int(sky_top[1] * (1 - ratio) + sky_bot[1] * ratio)
        b = int(sky_top[2] * (1 - ratio) + sky_bot[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (WINDOW_WIDTH, y))
    return surf

def build_lens_overlay(lens_type):
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
    elif lens_type == "ALPINE_FROST_LENS":
        pygame.draw.rect(overlay, (160, 220, 255, 28), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    elif lens_type == "VOLCANIC_GLOW_LENS":
        pygame.draw.rect(overlay, (255, 50, 10, 40), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    return overlay

# =========================================================================
# PROCEDURAL BACKGROUND GENERATORS
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
        pygame.draw.line(surf, (*neon_c, 200), (x, height - h), (x + w, height - h), 3)
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
    return surf

def generate_alpine_mountains(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(111 if is_far else 222)
    rock_color = (40, 50, 70) if is_far else (25, 32, 48)
    pts = [(0, height)]
    for x in range(0, width + 65, 65):
        h = random.randint(120, 250) if is_far else random.randint(60, 140)
        pts.append((int(x), int(height - h)))
    pts.append((width, height))
    pygame.draw.polygon(surf, rock_color, pts)
    return surf

def generate_volcanic_canyon(width, height, is_far):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    random.seed(333 if is_far else 444)
    base_color = (24, 12, 14) if is_far else (16, 8, 10)
    pts = [(0, height)]
    for x in range(0, width + 70, 70):
        h = random.randint(100, 230) if is_far else random.randint(50, 130)
        pts.append((int(x), int(height - h)))
    pts.append((width, height))
    pygame.draw.polygon(surf, base_color, pts)
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
    sa = random.randint(120, 255)
    pygame.draw.circle(STARS_SURF, (200, 235, 255, sa), (int(sx), int(sy)), 1)

# Particle System Lists
rain_drops = [{'x': random.randint(-50, WINDOW_WIDTH + 50), 'y': random.randint(0, WINDOW_HEIGHT), 'speed': random.uniform(8, 15), 'length': random.randint(10, 18)} for _ in range(60)]
cherry_petals = [{'x': random.randint(-50, WINDOW_WIDTH + 50), 'y': random.randint(0, WINDOW_HEIGHT), 'speed_y': random.uniform(1.2, 3.2), 'speed_x': random.uniform(1.5, 4.0), 'size': random.randint(3, 6), 'rot': random.uniform(0, 360)} for _ in range(40)]
snow_flakes = [{'x': random.randint(-50, WINDOW_WIDTH + 50), 'y': random.randint(0, WINDOW_HEIGHT), 'speed_y': random.uniform(1.0, 2.5), 'speed_x': random.uniform(-0.8, 0.8), 'size': random.randint(2, 5)} for _ in range(50)]
volcanic_embers = [{'x': random.randint(0, WINDOW_WIDTH), 'y': random.randint(0, WINDOW_HEIGHT), 'vx': random.uniform(-2.5, -0.5), 'vy': random.uniform(-2.5, -0.8), 'size': random.uniform(2.0, 5.0), 'color': random.choice([(255, 90, 20), (255, 180, 40)])} for _ in range(40)]
motion_lines = [{'x': random.randint(0, WINDOW_WIDTH), 'y': random.randint(80, GROUND_Y - 30), 'length': random.randint(50, 180), 'speed_mult': random.uniform(0.9, 1.6)} for _ in range(25)]

smoke_particles = []
sparks = []
floating_popups = []

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

# =========================================================================
# AXLE GEOMETRY
# =========================================================================
REAR_AXLE_ORIGIN = pygame.math.Vector2(FRAME_WIDTH * 0.08, FRAME_HEIGHT * 0.82)
FRONT_AXLE_ORIGIN = pygame.math.Vector2(FRAME_WIDTH * 0.76, FRAME_HEIGHT * 0.82)
AXLE_OFFSET_VECTOR = FRONT_AXLE_ORIGIN - REAR_AXLE_ORIGIN

SEATSTAND_REAR_AXLE_ORIGIN = pygame.math.Vector2(SEATSTAND_WIDTH * 0.18, SEATSTAND_HEIGHT * 0.82)
SEATSTAND_FRONT_AXLE_ORIGIN = pygame.math.Vector2(SEATSTAND_WIDTH * 0.90, SEATSTAND_HEIGHT * 0.82)
SEATSTAND_AXLE_OFFSET_VECTOR = SEATSTAND_FRONT_AXLE_ORIGIN - SEATSTAND_REAR_AXLE_ORIGIN

rear_susp_comp, rear_susp_vel = 0.0, 0.0
front_susp_comp, front_susp_vel = 0.0, 0.0
SUSP_K, SUSP_C, MAX_SUSP_COMP = 240.0, 16.0, 18.0

active_stance = "SEATED"
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

angle, angular_velocity, speed, wheel_spin = 0.0, 0.0, 0.0, 0.0
throttle_timer, brake_timer = 0.0, 0.0
shake_timer, shake_intensity, camera_y_offset = 0, 0.0, 0.0

# UI Hitboxes
play_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, 155, 190, 48)
garage_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 95, 155, 190, 48)
settings_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 + 130, 155, 190, 48)

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
low_perf_toggle_rect = pygame.Rect(WINDOW_WIDTH // 2 - 170, 260, 340, 44)
reset_data_rect = pygame.Rect(WINDOW_WIDTH // 2 - 170, 325, 340, 44)

confirm_yes_rect = pygame.Rect(WINDOW_WIDTH // 2 - 130, 280, 120, 42)
confirm_no_rect = pygame.Rect(WINDOW_WIDTH // 2 + 10, 280, 120, 42)

pause_resume_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 150, 280, 48)
pause_restart_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 215, 280, 48)
pause_settings_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 280, 280, 48)
pause_menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 345, 280, 48)

active_garage_tab = "PAINTS"

def trigger_screen_shake(intensity, duration):
    global shake_intensity, shake_timer
    if low_performance_mode: return
    shake_intensity = max(shake_intensity, intensity)
    shake_timer = duration

def add_floating_popup(text, color, x=WINDOW_WIDTH // 2, y=140):
    floating_popups.append({'x': float(x), 'y': float(y), 'text': text, 'color': color, 'life': 1.0, 'vy': -1.2})

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
    global shake_timer, shake_intensity, camera_y_offset, wheelie_distance, game_state
    global throttle_timer, brake_timer, session_cash_earned, scrape_cash_earned
    global wheelie_combo_timer, combo_multiplier, active_stance
    global rear_susp_comp, rear_susp_vel, front_susp_comp, front_susp_vel

    angle, angular_velocity, speed, wheel_spin = 0.0, 0.0, 0.0, 0.0
    world_offset, wheelie_distance = 0.0, 0.0
    session_cash_earned, scrape_cash_earned = 0, 0.0
    wheelie_combo_timer, combo_multiplier = 0.0, 1.0
    active_stance = "SEATED"

    throttle_timer, brake_timer = 0.0, 0.0
    shake_timer, shake_intensity, camera_y_offset = 0, 0.0, 0.0
    rear_susp_comp, rear_susp_vel = 0.0, 0.0
    front_susp_comp, front_susp_vel = 0.0, 0.0
    sparks.clear(); smoke_particles.clear(); floating_popups.clear()
    game_state = "PLAYING"

def draw_forza_speedometer(surface, current_speed, max_speed, current_angle, score):
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

    draw_glass_box(surface, pygame.Rect(20, 20, 360, 100), bg_color=(15, 18, 24, 180), border_color=GLASS_BORDER_HI, border_radius=18, border_width=2)
    font_hud = get_font("Helvetica", 13, bold=True)
    dist_txt = font_hud.render(f"MAP: {get_current_map()['name'].upper()}", True, COLOR_WHITE)
    cash_txt = font_hud.render(f"DISTANCE: {int(score)} m   |   CASH: ${int(total_cash)}", True, COLOR_TEXT_MUTED)
    surface.blit(dist_txt, (36, 32))
    surface.blit(cash_txt, (36, 60))

# =========================================================================
# ASYNC MAIN LOOP & INITIALIZATION
# =========================================================================
async def main():
    global window, audio_enabled, sound_click, sound_scrape, sound_slam
    global rear_wheel_img, front_wheel_img, game_state, total_cash, high_score
    global equipped_paint, equipped_map, equipped_underglow, throttle_level, brake_level
    global sfx_volume, music_volume, low_performance_mode, confirm_reset_active
    global previous_state_before_settings, active_stance, combo_multiplier
    global wheelie_combo_timer, wheelie_distance, session_cash_earned, scrape_cash_earned
    global angle, angular_velocity, speed, world_offset, wheel_spin, active_garage_tab
    global rear_susp_comp, rear_susp_vel, front_susp_comp, front_susp_vel, camera_y_offset
    global throttle_timer, brake_timer

    pygame.init()
    pygame.joystick.init()

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("SoFlow Wheelie Life - Web Edition")
    clock = pygame.time.Clock()

    # Loading Screen
    window.fill((10, 12, 16))
    loading_lbl = get_font("Helvetica", 24, bold=True).render("LOADING ENGINE & MAPS...", True, COLOR_WHITE)
    window.blit(loading_lbl, (WINDOW_WIDTH//2 - loading_lbl.get_width()//2, WINDOW_HEIGHT//2 - 12))
    pygame.display.flip()
    await asyncio.sleep(0)

    # 1. Safe Audio Init
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        audio_enabled = True
    except Exception:
        audio_enabled = False

    if audio_enabled:
        try: sound_click = pygame.mixer.Sound(get_asset_path("assets/click.ogg"))
        except Exception: sound_click = generate_tone_sound(880, 0.05, 0.25)
        try: sound_scrape = pygame.mixer.Sound(get_asset_path("assets/scrape.ogg"))
        except Exception: sound_scrape = generate_noise_sound(0.2, 0.18)
        try: sound_slam = pygame.mixer.Sound(get_asset_path("assets/slam.ogg"))
        except Exception: sound_slam = generate_tone_sound(120, 0.15, 0.4)

    # 2. Safe Texture Loading (Fallback to crisp procedural wheels if PNG missing)
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

    await asyncio.sleep(0)

    # 3. Pre-render Skies & Lens Overlays (Optimization #2)
    for m in MAPS_CATALOG:
        PRE_RENDERED_SKIES[m["id"]] = build_sky_surface(m["sky_top"], m["sky_bottom"])
        if m.get("lens_filter"):
            LENS_OVERLAYS[m["lens_filter"]] = build_lens_overlay(m["lens_filter"])
        await asyncio.sleep(0)

    # 4. Async Map & Save Loading
    await init_procedural_backgrounds()
    update_maps_catalog_layers()
    load_game_data()
    load_all_paint_assets()

    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for joy in joysticks: joy.init()

    # MAIN GAME LOOP
    while True:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        current_map = get_current_map()

        if game_state in ["MENU", "GARAGE"]: update_bg_music(MENU_MUSIC_FILE)
        else: update_bg_music(current_map.get("music", MENU_MUSIC_FILE))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data(); pygame.quit(); sys.exit()

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

                elif game_state == "PAUSED":
                    if pause_resume_rect.collidepoint(event.pos): play_sfx(sound_click); game_state = "PLAYING"
                    elif pause_restart_rect.collidepoint(event.pos): play_sfx(sound_click); reset_game()
                    elif pause_settings_rect.collidepoint(event.pos): play_sfx(sound_click); previous_state_before_settings = "PAUSED"; game_state = "SETTINGS"
                    elif pause_menu_rect.collidepoint(event.pos): play_sfx(sound_click); save_game_data(); game_state = "MENU"

                elif game_state == "SETTINGS":
                    if settings_back_rect.collidepoint(event.pos): play_sfx(sound_click); save_game_data(); game_state = previous_state_before_settings
                    elif sfx_minus_rect.collidepoint(event.pos): sfx_volume = max(0.0, round(sfx_volume - 0.1, 1)); play_sfx(sound_click)
                    elif sfx_plus_rect.collidepoint(event.pos): sfx_volume = min(1.0, round(sfx_volume + 0.1, 1)); play_sfx(sound_click)
                    elif music_minus_rect.collidepoint(event.pos): music_volume = max(0.0, round(music_volume - 0.1, 1)); play_sfx(sound_click)
                    elif music_plus_rect.collidepoint(event.pos): music_volume = min(1.0, round(music_volume + 0.1, 1)); play_sfx(sound_click)
                    elif low_perf_toggle_rect.collidepoint(event.pos): low_performance_mode = not low_performance_mode; play_sfx(sound_click); save_game_data()
                    elif reset_data_rect.collidepoint(event.pos): play_sfx(sound_click); confirm_reset_active = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == "PLAYING": game_state = "PAUSED"
                    elif game_state == "PAUSED": game_state = "PLAYING"
                    elif game_state == "SETTINGS": game_state = previous_state_before_settings
                    elif game_state == "GARAGE": save_game_data(); game_state = "MENU"
                elif game_state in ["MENU", "GAMEOVER"] and event.key in [pygame.K_RETURN, pygame.K_SPACE]: reset_game()

        # Keyboard / Controls Physics
        keys = pygame.key.get_pressed()
        if game_state == "PLAYING":
            is_w = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_RIGHT]
            is_space = keys[pygame.K_SPACE]
            is_brake = keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT]
            is_shift = keys[pygame.K_LSHIFT] or keys[pygame.K_e]

            active_stance = "SEAT_STANDER" if (is_shift and angle > 15.0) else "SEATED"

            if is_w:
                throttle_timer += dt
                surge = 1.0 if throttle_timer < 0.3 else min(1.85, 1.0 + (throttle_timer - 0.3) * 2.2)
                speed = min(speed + 0.32 * surge, 30.0)
                angular_velocity += (0.42 if active_stance == "SEAT_STANDER" else 0.38) * surge
            else:
                throttle_timer = 0.0
                speed = max(0.0, speed - 0.025)

            if is_space and not is_w: angular_velocity += 0.45

            if is_brake:
                brake_timer += dt
                speed = max(0.0, speed - (0.04 + min(1.0, brake_timer / 0.8) * 0.08))
                angular_velocity -= 0.45
            else: brake_timer = 0.0

            if angle > 0:
                diff = angle - 55.0
                angular_velocity += (abs(diff) / 55.0) * 0.10 * (1.0 if diff > 0 else -1.0)

            angular_velocity *= 0.94
            angle += angular_velocity
            world_offset += speed
            wheel_spin = (wheel_spin + speed * 7) % 360

            if angle <= 0:
                if angular_velocity < -0.4: play_sfx(sound_slam); trigger_screen_shake(10.0, 8)
                angle = 0; angular_velocity = 0

            if angle > 5.0:
                wheelie_distance += speed * 0.12 * combo_multiplier
                if wheelie_distance > high_score: high_score = wheelie_distance
            else: combo_multiplier = 1.0

            if angle >= 102.0:
                game_state = "GAMEOVER"
                session_cash_earned = int(wheelie_distance * 0.10) + int(scrape_cash_earned)
                total_cash += session_cash_earned
                save_game_data()

        # RENDER ENGINE (OPTIMIZED)
        # 1. Blit Pre-Rendered Sky Surface (Fastest render possible!)
        window.blit(PRE_RENDERED_SKIES[equipped_map], (0, 0))

        if current_map.get("has_stars", False): window.blit(STARS_SURF, (0, 0))

        if current_map["far_layer"]:
            far_s = (world_offset * 0.15) % 1000
            window.blit(current_map["far_layer"], (int(-far_s), 80))
            window.blit(current_map["far_layer"], (int(-far_s + 1000), 80))

        if current_map["near_layer"]:
            near_s = (world_offset * 0.35) % 1000
            window.blit(current_map["near_layer"], (int(-near_s), 120))
            window.blit(current_map["near_layer"], (int(-near_s + 1000), 120))

        rendered_g_y = int(GROUND_Y + camera_y_offset)
        pygame.draw.rect(window, current_map["road_color"], (0, rendered_g_y, WINDOW_WIDTH, WINDOW_HEIGHT - rendered_g_y))
        for x in range(int((-world_offset) % 80), WINDOW_WIDTH, 80):
            pygame.draw.line(window, current_map["dash_color"], (x, rendered_g_y + 30), (x + 40, rendered_g_y + 30), 4)

        # Bike & Wheel Rendering
        active_frame = frame_images_seatstand[equipped_paint] if active_stance == "SEAT_STANDER" else frame_images_normal[equipped_paint]
        active_rear_orig = SEATSTAND_REAR_AXLE_ORIGIN if active_stance == "SEAT_STANDER" else REAR_AXLE_ORIGIN
        active_axle_off = SEATSTAND_AXLE_OFFSET_VECTOR if active_stance == "SEAT_STANDER" else AXLE_OFFSET_VECTOR

        rear_w_pos = pygame.math.Vector2(pivot_x, rendered_g_y - (REAR_WHEEL_SIZE // 2))
        frame_pivot = rear_w_pos + pygame.math.Vector2(0, rear_susp_comp).rotate(-angle)
        frame_front_m = frame_pivot + active_axle_off.rotate(-angle)
        front_w_pos = frame_pivot + (active_axle_off.normalize() * (active_axle_off.length() - front_susp_comp)).rotate(-angle)

        rot_rear = pygame.transform.rotate(rear_wheel_img, -wheel_spin)
        window.blit(rot_rear, rot_rear.get_rect(center=(int(rear_w_pos.x), int(rear_w_pos.y))))
        rotate_around_pivot(window, active_frame, angle, (frame_pivot.x, frame_pivot.y), active_rear_orig)
        rot_front = pygame.transform.rotate(front_wheel_img, -wheel_spin)
        window.blit(rot_front, rot_front.get_rect(center=(int(front_w_pos.x), int(front_w_pos.y))))

        draw_suspension_hardware(window, rear_w_pos, frame_pivot, front_w_pos, frame_front_m)

        # Pre-cached Lens Overlays
        if not low_performance_mode and current_map.get("lens_filter") in LENS_OVERLAYS:
            window.blit(LENS_OVERLAYS[current_map["lens_filter"]], (0, 0))

        # Menus & Overlays
        if game_state == "PLAYING":
            draw_forza_speedometer(window, speed, 30.0, angle, wheelie_distance)
        elif game_state == "MENU":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill(GLASS_OVERLAY_DARK)
            window.blit(glass_bg, (0, 0))
            header = pygame.Rect(WINDOW_WIDTH // 2 - 280, 25, 560, 100)
            draw_glass_box(window, header, bg_color=(255, 255, 255, 15), border_color=GLASS_BORDER_HI, border_radius=22)
            t_txt = get_font("Helvetica", 48, bold=True).render("SOFLOW WHEELIE LIFE", True, COLOR_WHITE)
            window.blit(t_txt, (header.centerx - t_txt.get_width() // 2, header.y + 16))

            for b_txt_str, rect in [("PLAY [ENTER]", play_btn_rect), ("GARAGE", garage_btn_rect), ("SETTINGS", settings_btn_rect)]:
                is_h = rect.collidepoint(mouse_pos)
                draw_glass_box(window, rect, bg_color=GLASS_BG_ACTIVE if is_h else GLASS_BG_CARD, border_color=COLOR_WHITE if is_h else GLASS_BORDER_SUBTLE, border_radius=16)
                txt = get_font("Helvetica", 18, bold=True).render(b_txt_str, True, COLOR_TEXT_DARK if is_h else COLOR_WHITE)
                window.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        elif game_state == "SETTINGS":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((8, 10, 14, 235))
            window.blit(glass_bg, (0, 0))
            panel = pygame.Rect(WINDOW_WIDTH // 2 - 320, 100, 640, 360)
            draw_glass_box(window, panel, bg_color=GLASS_BG_CARD, border_color=GLASS_BORDER_SUBTLE, border_radius=20)
            
            is_h = low_perf_toggle_rect.collidepoint(mouse_pos)
            draw_glass_box(window, low_perf_toggle_rect, bg_color=(50, 205, 50, 180) if low_performance_mode else (GLASS_BG_CARD_HOVER if is_h else GLASS_BG_CARD), border_radius=14)
            p_txt = get_font("Helvetica", 15, bold=True).render(f"CHROMEBOOK MODE: {'ON (MAX FPS)' if low_performance_mode else 'OFF'}", True, COLOR_TEXT_DARK if low_performance_mode else COLOR_WHITE)
            window.blit(p_txt, (low_perf_toggle_rect.centerx - p_txt.get_width() // 2, low_perf_toggle_rect.centery - p_txt.get_height() // 2))

            draw_glass_box(window, settings_back_rect, bg_color=GLASS_BG_CARD, border_radius=12)
            b_txt = get_font("Helvetica", 15, bold=True).render("< BACK", True, COLOR_WHITE)
            window.blit(b_txt, (settings_back_rect.centerx - b_txt.get_width() // 2, settings_back_rect.centery - b_txt.get_height() // 2))

        elif game_state == "GARAGE":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((8, 10, 14, 235))
            window.blit(glass_bg, (0, 0))
            draw_glass_box(window, garage_back_rect, bg_color=GLASS_BG_CARD, border_radius=12)
            b_txt = get_font("Helvetica", 15, bold=True).render("< BACK", True, COLOR_WHITE)
            window.blit(b_txt, (garage_back_rect.centerx - b_txt.get_width() // 2, garage_back_rect.centery - b_txt.get_height() // 2))

        elif game_state == "GAMEOVER":
            glass_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA); glass_bg.fill((10, 12, 16, 220))
            window.blit(glass_bg, (0, 0))
            modal = pygame.Rect(WINDOW_WIDTH // 2 - 250, 60, 500, 360)
            draw_glass_box(window, modal, bg_color=(255, 255, 255, 20), border_radius=24)
            go_txt = get_font("Helvetica", 52, bold=True).render("LOOPED OUT!", True, COLOR_WHITE)
            window.blit(go_txt, (modal.centerx - go_txt.get_width() // 2, modal.y + 35))

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
