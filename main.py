import array
import math
import os
import random
import sys
import pygame

pygame.init()
try:
    pygame.key.stop_text_input()
except Exception:
    pass

try:
    pygame.mixer.init(22050, -16, 1, 512)
except Exception:
    pass

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w if info.current_w > 0 else 720
SCREEN_HEIGHT = info.current_h if info.current_h > 0 else 1280
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FOULOLOU MILOUD'S RIVAL CENTIPEDE")

HEADER_HEIGHT = 84
GAME_HEIGHT = int(SCREEN_HEIGHT * 0.49)
PANEL_HEIGHT = SCREEN_HEIGHT - GAME_HEIGHT
clock = pygame.time.Clock()

has_accelerometer = False
accelerometer_sensor = None
try:
    from plyer import accelerometer
    accelerometer.enable()
    accelerometer_sensor = accelerometer
    has_accelerometer = True
except Exception:
    has_accelerometer = False

vibrator_sensor = None
try:
    from plyer import vibrator
    vibrator_sensor = vibrator
except Exception:
    vibrator_sensor = None

def trigger_vibrate(duration=0.08):
    if vibrator_sensor:
        try:
            vibrator_sensor.vibrate(duration)
        except Exception:
            pass

# ----------------- مجلد الصوت -----------------
CANDIDATE_PATHS = [
    "/storage/emulated/0/Download/music",
    "/storage/emulated/0/Download",
    os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd(), "music"),
    os.path.join(os.getcwd(), "music")
]

MUSIC_FOLDER = CANDIDATE_PATHS[0]
for p in CANDIDATE_PATHS:
    if os.path.exists(p) and os.path.isdir(p):
        MUSIC_FOLDER = p
        break

audio_playlist = ["AUDIO: OFF"]
current_audio_idx = 0
audio_banner_text = ""
audio_banner_timer = 0

def scan_music_folder():
    global audio_playlist, MUSIC_FOLDER
    tracks = ["AUDIO: OFF"]
    found_folder = None
    for p in CANDIDATE_PATHS:
        if os.path.exists(p) and os.path.isdir(p):
            try:
                files = [f for f in sorted(os.listdir(p)) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
                if files:
                    found_folder = p
                    tracks.extend(files)
                    break
            except Exception:
                pass
    if found_folder:
        MUSIC_FOLDER = found_folder
    audio_playlist = tracks

scan_music_folder()

def change_track(step=1):
    global current_audio_idx, audio_banner_text, audio_banner_timer
    scan_music_folder()
    if len(audio_playlist) <= 1:
        audio_banner_text = "NO SONGS IN MUSIC FOLDER!"
        audio_banner_timer = 90
        return

    current_audio_idx = (current_audio_idx + step) % len(audio_playlist)
    track_name = audio_playlist[current_audio_idx]
    
    if track_name == "AUDIO: OFF":
        pygame.mixer.music.stop()
        audio_banner_text = "AUDIO STOPPED"
    else:
        file_path = os.path.join(MUSIC_FOLDER, track_name)
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(0.65)
            pygame.mixer.music.play(-1)
            audio_banner_text = f"PLAYING: {track_name[:16]}"
        except Exception:
            audio_banner_text = f"CANNOT PLAY: {track_name[:16]}"
    audio_banner_timer = 90

# ----------------- المؤثرات الصوتية -----------------
def generate_sound(freq_start, freq_end, duration_sec, volume=0.3):
    sample_rate = 22050
    n_samples = int(sample_rate * duration_sec)
    buf = array.array('h')
    for i in range(n_samples):
        t = float(i) / n_samples
        cur_freq = freq_start + (freq_end - freq_start) * t
        val = math.sin(2.0 * math.pi * cur_freq * (float(i) / sample_rate))
        envelope = (1.0 - t) * volume
        buf.append(int(val * 32767 * envelope))
    return pygame.mixer.Sound(buf)

try:
    snd_eat = generate_sound(450, 950, 0.08, 0.25)
    snd_hunt = generate_sound(600, 1300, 0.15, 0.35)
    snd_bonus = generate_sound(300, 1400, 0.25, 0.35)
    snd_quest = generate_sound(500, 1500, 0.30, 0.40)
    snd_alert = generate_sound(800, 400, 0.18, 0.30)
    snd_gameover = generate_sound(350, 100, 0.40, 0.40)
    snd_hit = generate_sound(220, 140, 0.15, 0.40)
    snd_kill = generate_sound(150, 900, 0.35, 0.45)
    snd_repulse = generate_sound(700, 200, 0.20, 0.35)
    snd_levelup = generate_sound(320, 1600, 0.45, 0.45)
except Exception:
    snd_eat = snd_hunt = snd_bonus = snd_quest = snd_alert = snd_gameover = snd_hit = snd_kill = snd_repulse = snd_levelup = None

def play_sound(snd):
    if snd:
        try: snd.play()
        except Exception: pass

# ----------------- حفظ البيانات -----------------
HIGHSCORE_FILE = "centipede_save.txt"

def load_game_data():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                lines = f.read().strip().split(",")
                return int(lines[0]), int(lines[1])
        except Exception:
            return 0, 0
    return 0, 0

def save_game_data(score, coins):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(f"{score},{coins}")
    except Exception:
        pass

high_score, total_coins = load_game_data()

font_player_name = pygame.font.SysFont("arial", 28, bold=True)
font_title = pygame.font.SysFont("arial", 46, bold=True)
font_btn_giant = pygame.font.SysFont("arial", 32, bold=True)
font_circle_giant = pygame.font.SysFont("arial", 27, bold=True)
font_side_btn = pygame.font.SysFont("arial", 24, bold=True)
font_score_bold = pygame.font.SysFont("arial", 24, bold=True)
font_big_bold = pygame.font.SysFont("arial", 64, bold=True)

in_menu = True

lvl_banner_timer = 0
lvl_banner_x = -SCREEN_WIDTH
lvl_banner_text = ""
lvl_banner_sub = ""

banner_bw = int(SCREEN_WIDTH * 0.88)
banner_bh = 50
banner_surf = pygame.Surface((banner_bw, banner_bh), pygame.SRCALPHA)

SNAKE_SKINS = [
    {"name": "1/16 NEON GREEN",   "dark": (10, 150, 40),  "light": (30, 255, 90),   "glow": (140, 255, 160)},
    {"name": "2/16 ULTRA CYAN",    "dark": (0, 140, 190),  "light": (0, 240, 255),   "glow": (170, 250, 255)},
    {"name": "3/16 HYPER ORANGE",  "dark": (190, 50, 0),   "light": (255, 120, 0),   "glow": (255, 200, 90)},
    {"name": "4/16 GOLDEN SUN",    "dark": (170, 130, 0),  "light": (255, 230, 0),   "glow": (255, 255, 150)},
    {"name": "5/16 PLASMA VIOLET", "dark": (120, 20, 180), "light": (220, 60, 255),  "glow": (245, 160, 255)},
    {"name": "6/16 POLAR ICE",     "dark": (50, 90, 125),  "light": (150, 230, 255), "glow": (220, 250, 255)},
    {"name": "7/16 CRIMSON BLOOD", "dark": (170, 10, 35),  "light": (255, 40, 85),   "glow": (255, 130, 160)},
    {"name": "8/16 RADIOACTIVE",   "dark": (95, 150, 0),   "light": (210, 255, 0),   "glow": (235, 255, 130)},
    {"name": "9/16 HOT PINK",      "dark": (170, 20, 110), "light": (255, 55, 200),  "glow": (255, 160, 235)},
    {"name": "10/16 DEEP OCEAN",   "dark": (10, 60, 160),  "light": (40, 160, 255),  "glow": (150, 215, 255)},
    {"name": "11/16 MAGMA LAVA",   "dark": (180, 40, 10),  "light": (255, 100, 20),  "glow": (255, 190, 80)},
    {"name": "12/16 CHROME WHITE", "dark": (110, 120, 135),"light": (235, 245, 255), "glow": (255, 255, 255)},
    {"name": "13/16 METALLIC COPPER","dark": (140, 65, 25),"light": (245, 140, 70),  "glow": (255, 195, 130)},
    {"name": "14/16 AQUA MINT",    "dark": (20, 140, 125), "light": (50, 255, 230),  "glow": (170, 255, 245)},
    {"name": "15/16 COSMIC DUSK",  "dark": (80, 20, 130),  "light": (180, 80, 255),  "glow": (220, 160, 255)},
    {"name": "16/16 SHADOW ONYX",  "dark": (35, 40, 50),   "light": (140, 155, 170), "glow": (210, 220, 235)}
]

selected_color = 0
SPEED_LEVELS = ["SPEED: 1x (SLOW)", "SPEED: 2x (NORMAL)", "SPEED: 3x (FAST)", "SPEED: 4x (TURBO)"]
selected_speed = 1

CONTROL_MODES = ["CTRL: BUTTONS", "CTRL: SWIPE", "CTRL: GYRO"]
CONTROL_SHORT = ["PAD", "SWIPE", "GYRO"]
selected_control = 0

OBJECT_MODE_NAMES = ["OBJECTS: ALL ON", "OBJECTS: WALLS", "OBJECTS: CHASER", "OBJECTS: PETS", "OBJECTS: OFF"]
selected_objects = 0
DIFFICULTY_MODES = ["DIFF: EASY (5 LIVES)", "DIFF: NORMAL (3 LIVES)", "DIFF: HARD (2 LIVES)", "DIFF: EXTREME (1 LIFE)"]
selected_diff = 1

# ----------------- تصميم الأرضية -----------------
world_surface = pygame.Surface((SCREEN_WIDTH, GAME_HEIGHT))

for y_line in range(GAME_HEIGHT):
    factor = y_line / GAME_HEIGHT
    r_val = int(32 + factor * 14)
    g_val = int(60 + factor * 22)
    b_val = int(14 + factor * 8)
    pygame.draw.line(world_surface, (r_val, g_val, b_val), (0, y_line), (SCREEN_WIDTH, y_line))

random.seed(42)
for _ in range(75):
    gx = random.randint(15, SCREEN_WIDTH - 15)
    gy = random.randint(HEADER_HEIGHT + 15, GAME_HEIGHT - 15)
    pygame.draw.line(world_surface, (55, 105, 26), (gx, gy), (gx - 3, gy - 7), 2)
    pygame.draw.line(world_surface, (68, 128, 32), (gx, gy), (gx, gy - 9), 2)
    pygame.draw.line(world_surface, (55, 105, 26), (gx, gy), (gx + 3, gy - 7), 2)

for _ in range(30):
    fx = random.randint(20, SCREEN_WIDTH - 20)
    fy = random.randint(HEADER_HEIGHT + 20, GAME_HEIGHT - 20)
    fcol = random.choice([(255, 240, 100), (255, 140, 180), (240, 240, 255), (140, 200, 255)])
    pygame.draw.circle(world_surface, fcol, (fx, fy), 2)

for _ in range(18):
    rx = random.randint(25, SCREEN_WIDTH - 25)
    ry = random.randint(HEADER_HEIGHT + 25, GAME_HEIGHT - 25)
    pygame.draw.ellipse(world_surface, (80, 85, 75), (rx, ry, random.randint(6, 12), random.randint(4, 7)))

path_points = [
    (-20, int(GAME_HEIGHT * 0.72)),
    (int(SCREEN_WIDTH * 0.32), int(GAME_HEIGHT * 0.58)),
    (int(SCREEN_WIDTH * 0.65), int(GAME_HEIGHT * 0.62)),
    (SCREEN_WIDTH + 20, int(GAME_HEIGHT * 0.32))
]
pygame.draw.lines(world_surface, (95, 70, 36), False, path_points, int(SCREEN_WIDTH * 0.16))
pygame.draw.lines(world_surface, (125, 95, 50), False, path_points, int(SCREEN_WIDTH * 0.13))
pygame.draw.lines(world_surface, (150, 120, 70), False, path_points, int(SCREEN_WIDTH * 0.08))

random.seed()

panel_bg_surface = pygame.Surface((SCREEN_WIDTH, PANEL_HEIGHT))
panel_bg_surface.fill((11, 14, 20))

grid_sz = 38
for gx in range(0, SCREEN_WIDTH, grid_sz):
    pygame.draw.line(panel_bg_surface, (18, 26, 38), (gx, 0), (gx, PANEL_HEIGHT), 1)
for gy in range(0, PANEL_HEIGHT, grid_sz):
    pygame.draw.line(panel_bg_surface, (18, 26, 38), (0, gy), (SCREEN_WIDTH, gy), 1)

# ----------------- تجهيز خلفية القائمة الفنية الثابتة -----------------
menu_bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

for y_s in range(SCREEN_HEIGHT):
    factor = y_s / SCREEN_HEIGHT
    r_val = int(8 + factor * 22)
    g_val = int(10 + factor * 14)
    b_val = int(24 + factor * 40)
    pygame.draw.line(menu_bg_surface, (r_val, g_val, b_val), (0, y_s), (SCREEN_WIDTH, y_s))

moon_x = int(SCREEN_WIDTH * 0.5)
moon_y = int(SCREEN_HEIGHT * 0.42)
pygame.draw.circle(menu_bg_surface, (30, 45, 75), (moon_x, moon_y), 135)
pygame.draw.circle(menu_bg_surface, (45, 68, 105), (moon_x, moon_y), 125)
pygame.draw.circle(menu_bg_surface, (230, 242, 255), (moon_x, moon_y), 115)
pygame.draw.circle(menu_bg_surface, (255, 255, 255), (moon_x - 12, moon_y - 12), 105)

random.seed(101)
for _ in range(45):
    star_x = random.randint(10, SCREEN_WIDTH - 10)
    star_y = random.randint(15, int(SCREEN_HEIGHT * 0.85))
    star_sz = random.choice([1, 2, 2])
    pygame.draw.circle(menu_bg_surface, (255, 255, 255), (star_x, star_y), star_sz)
random.seed()

building_defs = [
    (0, int(SCREEN_HEIGHT * 0.72), 70, 350),
    (60, int(SCREEN_HEIGHT * 0.68), 90, 400),
    (140, int(SCREEN_HEIGHT * 0.75), 80, 320),
    (SCREEN_WIDTH - 220, int(SCREEN_HEIGHT * 0.74), 75, 340),
    (SCREEN_WIDTH - 150, int(SCREEN_HEIGHT * 0.66), 85, 420),
    (SCREEN_WIDTH - 70, int(SCREEN_HEIGHT * 0.71), 75, 360)
]
for bx, by, bw, bh in building_defs:
    pygame.draw.rect(menu_bg_surface, (14, 18, 30), (bx, by, bw, bh))
    pygame.draw.rect(menu_bg_surface, (0, 180, 255), (bx, by, bw, bh), 1)
    for wy in range(by + 16, by + bh - 40, 24):
        for wx in range(bx + 12, bx + bw - 14, 18):
            if (wx + wy) % 5 != 0:
                pygame.draw.rect(menu_bg_surface, (0, 240, 255), (wx, wy, 8, 12))

# ----------------- البركة المائية المتغيرة -----------------
pond_rect = pygame.Rect(int(SCREEN_WIDTH * 0.30), int(GAME_HEIGHT * 0.54), int(SCREEN_WIDTH * 0.40), int(GAME_HEIGHT * 0.28))

POND_THEMES = [
    {"deep": (20, 80, 150),  "mid": (35, 140, 210), "glow": (140, 230, 255), "bank": (60, 48, 25)},
    {"deep": (15, 110, 120), "mid": (30, 180, 170), "glow": (160, 255, 240), "bank": (50, 52, 28)},
    {"deep": (70, 25, 120),  "mid": (120, 45, 180), "glow": (220, 150, 255), "bank": (55, 35, 45)},
    {"deep": (15, 90, 60),   "mid": (30, 160, 100), "glow": (140, 255, 190), "bank": (50, 45, 20)},
    {"deep": (120, 40, 20),  "mid": (200, 75, 30),  "glow": (255, 190, 120), "bank": (65, 38, 18)}
]

curr_pond_theme_idx = 0
next_pond_theme_idx = 1
pond_transition = 0.0

def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

def draw_water_pond(surface, timer):
    global curr_pond_theme_idx, next_pond_theme_idx, pond_transition
    pond_transition += 0.003
    if pond_transition >= 1.0:
        pond_transition = 0.0
        curr_pond_theme_idx = next_pond_theme_idx
        next_pond_theme_idx = random.choice([i for i in range(len(POND_THEMES)) if i != curr_pond_theme_idx])

    t1 = POND_THEMES[curr_pond_theme_idx]
    t2 = POND_THEMES[next_pond_theme_idx]

    c_bank = lerp_color(t1['bank'], t2['bank'], pond_transition)
    c_deep = lerp_color(t1['deep'], t2['deep'], pond_transition)
    c_mid = lerp_color(t1['mid'], t2['mid'], pond_transition)
    c_glow = lerp_color(t1['glow'], t2['glow'], pond_transition)

    pygame.draw.ellipse(surface, c_bank, (pond_rect.x - 7, pond_rect.y - 5, pond_rect.width + 14, pond_rect.height + 10))
    pygame.draw.ellipse(surface, c_deep, pond_rect)
    pygame.draw.ellipse(surface, c_mid, (pond_rect.x + 8, pond_rect.y + 6, pond_rect.width - 16, pond_rect.height - 12))

    for idx, speed_factor in enumerate([1.5, 2.3, 0.8]):
        wave_t = (timer * speed_factor + idx * 1.8) % 3.0
        w_expand = int(wave_t * 9)
        w_rect = pygame.Rect(
            pond_rect.centerx - 30 - w_expand,
            pond_rect.centery - 12 - (w_expand // 2),
            60 + w_expand * 2,
            24 + w_expand
        )
        pygame.draw.ellipse(surface, c_glow, w_rect, 1)

    glint_x = pond_rect.centerx - 22 + int(math.sin(timer * 1.5) * 5)
    glint_y = pond_rect.centery - 10
    pygame.draw.ellipse(surface, (255, 255, 255), (glint_x, glint_y, 32, 8))
    pygame.draw.ellipse(surface, c_glow, (glint_x - 4, glint_y - 2, 40, 12), 1)

TREE_SEASONS = [
    {"top": (52, 138, 44), "mid": (28, 92, 32), "dark": (16, 58, 22)},
    {"top": (240, 160, 20), "mid": (200, 100, 15), "dark": (140, 60, 10)},
    {"top": (255, 130, 170), "mid": (220, 80, 130), "dark": (150, 40, 80)},
    {"top": (80, 210, 235), "mid": (35, 150, 180), "dark": (15, 90, 120)},
    {"top": (190, 90, 255), "mid": (130, 40, 200), "dark": (80, 20, 130)}
]
current_season_idx = 0
season_shift_timer = 400

tall_trees = [
    (int(SCREEN_WIDTH * 0.12), int(GAME_HEIGHT * 0.24), 32),
    (int(SCREEN_WIDTH * 0.88), int(GAME_HEIGHT * 0.20), 30),
    (int(SCREEN_WIDTH * 0.14), int(GAME_HEIGHT * 0.82), 28),
    (int(SCREEN_WIDTH * 0.86), int(GAME_HEIGHT * 0.82), 29),
    (int(SCREEN_WIDTH * 0.50), int(GAME_HEIGHT * 0.18), 26)
]

def update_trees_season(current_level):
    global current_season_idx, season_shift_timer
    season_shift_timer -= 1
    if season_shift_timer <= 0:
        current_season_idx = (current_season_idx + 1) % len(TREE_SEASONS)
        season_shift_timer = max(180, 450 - current_level * 30)

def draw_tree(surface, x, y, r):
    pal = TREE_SEASONS[current_season_idx]
    pygame.draw.ellipse(surface, (15, 26, 8), (x - int(r * 1.3), y + 4, int(r * 2.6), int(r * 1.1)))
    pygame.draw.rect(surface, (65, 38, 16), (x - 6, y - 28, 12, 34), border_radius=4)
    pygame.draw.circle(surface, pal['dark'], (x, y - 28), r)
    pygame.draw.circle(surface, pal['mid'], (x - 4, y - 32), int(r * 0.82))
    pygame.draw.circle(surface, pal['top'], (x - 6, y - 35), int(r * 0.52))

# ----------------- المهام والجسيمات -----------------
QUEST_POOL = [
    {"desc": "HUNT 2 RABBITS", "type": "HUNT_RABBIT", "target": 2, "count": 0},
    {"desc": "EAT 4 APPLES", "type": "EAT_APPLE", "target": 4, "count": 0},
    {"desc": "USE 2 BOOSTS", "type": "USE_BOOST", "target": 2, "count": 0},
    {"desc": "HUNT 2 SQUIRRELS", "type": "HUNT_SQUIRREL", "target": 2, "count": 0},
    {"desc": "DEFEAT 1 RIVAL", "type": "KILL_RIVAL", "target": 1, "count": 0}
]
active_quest = random.choice(QUEST_POOL)
quest_banner_timer = 0
quest_banner_text = ""

def progress_quest(q_type, amt=1):
    global active_quest, total_coins, quest_banner_text, quest_banner_timer
    if active_quest['type'] == q_type:
        active_quest['count'] += amt
        if active_quest['count'] >= active_quest['target']:
            total_coins += 50
            play_sound(snd_quest)
            trigger_vibrate(0.20)
            quest_banner_text = "QUEST COMPLETE! +50 COINS"
            quest_banner_timer = 120
            active_quest = random.choice(QUEST_POOL)
            active_quest['count'] = 0

particles = []

def emit_particles(x, y, color, count=10):
    for _ in range(count):
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(1.5, 4.0)
        particles.append({
            'x': float(x),
            'y': float(y),
            'vx': math.cos(ang) * spd,
            'vy': math.sin(ang) * spd,
            'r': random.uniform(2.0, 4.0),
            'color': color,
            'life': random.randint(12, 20)
        })

def update_and_draw_particles(surface):
    for p in particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['r'] = max(0.5, p['r'] - 0.16)
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)
        else:
            pygame.draw.circle(surface, p['color'], (int(p['x']), int(p['y'])), int(p['r']))

# ----------------- الحيوانات -----------------
ANIMAL_TYPES = ['RABBIT', 'MOUSE', 'SQUIRREL']

def create_animal():
    atype = random.choice(ANIMAL_TYPES)
    if atype == 'RABBIT':
        col = (255, 245, 245)
        dcol = (255, 140, 160)
        sz = 20
    elif atype == 'SQUIRREL':
        col = (230, 110, 30)
        dcol = (170, 65, 15)
        sz = 22
    else:
        col = (160, 155, 165)
        dcol = (90, 85, 95)
        sz = 18

    return {
        'type': atype,
        'x': float(random.randint(70, SCREEN_WIDTH - 70)),
        'y': float(random.randint(HEADER_HEIGHT + 30, GAME_HEIGHT - 70)),
        'angle': random.uniform(0, 2 * math.pi),
        'speed': random.uniform(0.7, 1.4),
        'turn_timer': random.randint(60, 180),
        'hop_timer': random.uniform(0, 5),
        'body_col': col,
        'detail_col': dcol,
        'size': sz
    }

animals = [create_animal() for _ in range(random.randint(3, 4))]

def update_animals(hx, hy):
    for a in animals:
        a['turn_timer'] -= 1
        a['hop_timer'] += 0.12
        if a['turn_timer'] <= 0:
            a['angle'] += random.uniform(-1.2, 1.2)
            a['turn_timer'] = random.randint(50, 150)

        dist = math.hypot(a['x'] - hx, a['y'] - hy)
        spd = a['speed']
        if pond_rect.collidepoint(int(a['x']), int(a['y'])):
            spd *= 0.5

        if magnet_timer > 0 and dist < 140:
            pull_angle = math.atan2(hy - a['y'], hx - a['x'])
            a['x'] += math.cos(pull_angle) * 3.5
            a['y'] += math.sin(pull_angle) * 3.5
        elif dist < 95:
            escape_angle = math.atan2(a['y'] - hy, a['x'] - hx)
            a['angle'] = escape_angle
            a['x'] += math.cos(a['angle']) * (spd * 2.2)
            a['y'] += math.sin(a['angle']) * (spd * 2.2)
        else:
            a['x'] += math.cos(a['angle']) * spd
            a['y'] += math.sin(a['angle']) * spd

        a['x'] = max(30, min(SCREEN_WIDTH - 30, a['x']))
        a['y'] = max(HEADER_HEIGHT + 25, min(GAME_HEIGHT - 30, a['y']))

def draw_animal(surface, a):
    ax, ay = int(a['x']), int(a['y'])
    b_col = a['body_col']
    d_col = a['detail_col']
    sz = a['size']
    hop = int(math.sin(a['hop_timer'] * 3.5) * 3)

    pygame.draw.ellipse(surface, (14, 24, 8), (ax - sz, ay + sz // 2, sz * 2, sz // 2 + 3))

    if a['type'] == 'RABBIT':
        pygame.draw.ellipse(surface, b_col, (ax - sz, ay - sz // 2 + hop, sz * 2, int(sz * 1.3)))
        pygame.draw.ellipse(surface, b_col, (ax - 7, ay - sz - 14 + hop, 7, 18))
        pygame.draw.ellipse(surface, b_col, (ax + 1, ay - sz - 14 + hop, 7, 18))
        pygame.draw.ellipse(surface, d_col, (ax - 5, ay - sz - 12 + hop, 3, 14))
        pygame.draw.ellipse(surface, d_col, (ax + 3, ay - sz - 12 + hop, 3, 14))
        pygame.draw.circle(surface, (255, 255, 255), (ax - sz + 2, ay + hop), 5)
        pygame.draw.circle(surface, (255, 80, 100), (ax + sz - 2, ay - 2 + hop), 3)
        pygame.draw.circle(surface, (20, 20, 20), (ax + 6, ay - 6 + hop), 3)
    elif a['type'] == 'SQUIRREL':
        pygame.draw.ellipse(surface, b_col, (ax - sz, ay - sz // 2 + hop, sz * 2, int(sz * 1.1)))
        pygame.draw.circle(surface, b_col, (ax + sz - 4, ay - 4 + hop), int(sz * 0.65))
        pygame.draw.ellipse(surface, d_col, (ax - sz - 12, ay - sz - 8 + hop, 16, 26))
        pygame.draw.circle(surface, b_col, (ax - sz - 4, ay - sz + hop), 8)
        pygame.draw.circle(surface, (10, 10, 10), (ax + sz - 1, ay - 6 + hop), 3)
    elif a['type'] == 'MOUSE':
        pygame.draw.ellipse(surface, b_col, (ax - sz, ay - sz // 2 + hop, int(sz * 1.9), sz))
        pygame.draw.circle(surface, d_col, (ax + 2, ay - sz + 2 + hop), 6)
        pygame.draw.circle(surface, d_col, (ax + 12, ay - sz + 2 + hop), 6)
        pygame.draw.circle(surface, (255, 170, 180), (ax + 2, ay - sz + 2 + hop), 3)
        pygame.draw.circle(surface, (255, 170, 180), (ax + 12, ay - sz + 2 + hop), 3)
        pygame.draw.line(surface, d_col, (ax - sz, ay + hop), (ax - sz - 14, ay - 4 + hop), 3)
        pygame.draw.circle(surface, (10, 10, 10), (ax + sz - 2, ay - 2 + hop), 2)
        pygame.draw.circle(surface, (255, 100, 120), (ax + sz + 3, ay + hop), 2)

# ----------------- المكافآت -----------------
powerup_item = {'x': -100, 'y': -100, 'type': 'REPULSE', 'active': False, 'timer': 160, 'duration': 340}
freeze_timer = 0
shield_timer = 0
magnet_timer = 0
double_points_timer = 0
repulse_timer = 0

def update_powerups():
    global freeze_timer, shield_timer, magnet_timer, double_points_timer, repulse_timer
    if freeze_timer > 0: freeze_timer -= 1
    if shield_timer > 0: shield_timer -= 1
    if magnet_timer > 0: magnet_timer -= 1
    if double_points_timer > 0: double_points_timer -= 1
    if repulse_timer > 0: repulse_timer -= 1

    powerup_item['timer'] -= 1
    if powerup_item['timer'] <= 0:
        powerup_item['active'] = not powerup_item['active']
        if powerup_item['active']:
            powerup_item['type'] = random.choice(['MAGNET', 'MUSHROOM', 'FREEZE', 'SHIELD', 'REPULSE'])
            powerup_item['x'] = random.randint(60, SCREEN_WIDTH - 60)
            powerup_item['y'] = random.randint(HEADER_HEIGHT + 30, GAME_HEIGHT - 60)
            powerup_item['timer'] = powerup_item['duration']
        else:
            powerup_item['timer'] = random.randint(200, 380)

def draw_powerup(surface, timer):
    if not powerup_item['active']: return
    px, py = int(powerup_item['x']), int(powerup_item['y'])
    pulse = abs(math.sin(timer * 5)) * 4

    if powerup_item['type'] == 'REPULSE':
        col = (200, 50, 255)
        pygame.draw.circle(surface, col, (px, py), int(16 + pulse), 2)
        pygame.draw.circle(surface, (80, 20, 120), (px, py), 13)
        pygame.draw.circle(surface, (255, 140, 255), (px, py), 7, 2)
        pygame.draw.line(surface, (255, 255, 255), (px - 5, py), (px + 5, py), 2)
        pygame.draw.line(surface, (255, 255, 255), (px, py - 5), (px, py + 5), 2)
    elif powerup_item['type'] == 'MAGNET':
        pygame.draw.circle(surface, (255, 70, 70), (px, py), int(15 + pulse), 2)
        pygame.draw.arc(surface, (255, 40, 40), (px - 10, py - 10, 20, 20), 0, math.pi, 4)
        pygame.draw.rect(surface, (220, 220, 255), (px - 10, py, 6, 6))
        pygame.draw.rect(surface, (220, 220, 255), (px + 4, py, 6, 6))
    elif powerup_item['type'] == 'MUSHROOM':
        pygame.draw.circle(surface, (255, 215, 0), (px, py), int(15 + pulse), 2)
        pygame.draw.arc(surface, (255, 200, 0), (px - 11, py - 12, 22, 18), 0, math.pi, 0)
        pygame.draw.circle(surface, (255, 255, 255), (px - 4, py - 6), 2)
        pygame.draw.circle(surface, (255, 255, 255), (px + 4, py - 6), 2)
        pygame.draw.rect(surface, (255, 250, 220), (px - 4, py - 4, 8, 10), border_radius=2)
    elif powerup_item['type'] == 'FREEZE':
        col = (0, 220, 255)
        pygame.draw.circle(surface, col, (px, py), int(15 + pulse), 2)
        pygame.draw.circle(surface, (30, 80, 140), (px, py), 13)
        pygame.draw.line(surface, (255, 255, 255), (px - 7, py), (px + 7, py), 2)
        pygame.draw.line(surface, (255, 255, 255), (px, py - 7), (px, py + 7), 2)
    else:
        col = (255, 215, 0)
        pygame.draw.circle(surface, col, (px, py), int(15 + pulse), 2)
        pygame.draw.circle(surface, (140, 100, 20), (px, py), 13)
        pygame.draw.circle(surface, (255, 255, 255), (px, py), 7, 2)

# ----------------- التفاح المتغير -----------------
APPLE_COLORS = [
    {"dark": (140, 15, 30),  "light": (255, 40, 60),   "glow": (255, 130, 150)},
    {"dark": (10, 120, 40),  "light": (0, 255, 110),   "glow": (130, 255, 170)},
    {"dark": (0, 100, 150),  "light": (0, 235, 255),   "glow": (170, 245, 255)},
    {"dark": (140, 100, 0),  "light": (255, 220, 0),   "glow": (255, 250, 130)},
    {"dark": (160, 40, 0),   "light": (255, 110, 0),   "glow": (255, 185, 80)},
    {"dark": (90, 15, 140),  "light": (210, 50, 255),  "glow": (235, 150, 255)},
    {"dark": (140, 10, 90),  "light": (255, 45, 190),  "glow": (255, 150, 225)},
    {"dark": (15, 115, 105), "light": (40, 255, 220),  "glow": (160, 255, 240)}
]

apple_pos = [int(SCREEN_WIDTH * 0.5), int(GAME_HEIGHT * 0.38)]
apple_color_idx = 0
apple_color_timer = 120

def update_apple(hx, hy):
    global apple_color_idx, apple_color_timer, apple_pos
    apple_color_timer -= 1
    if apple_color_timer <= 0:
        apple_color_idx = (apple_color_idx + 1) % len(APPLE_COLORS)
        apple_color_timer = random.randint(90, 160)

    if magnet_timer > 0:
        dx = hx - apple_pos[0]
        dy = hy - apple_pos[1]
        dist = math.hypot(dx, dy)
        if dist < 170 and dist > 5:
            apple_pos[0] += (dx / dist) * 4.5
            apple_pos[1] += (dy / dist) * 4.5

def respawn_apple():
    global apple_pos, apple_color_idx
    apple_pos = [random.randint(45, SCREEN_WIDTH - 45), random.randint(HEADER_HEIGHT + 25, GAME_HEIGHT - 45)]
    apple_color_idx = random.randint(0, len(APPLE_COLORS) - 1)

def draw_3d_apple(surface, pos, r=16):
    x, y = int(pos[0]), int(pos[1])
    col = APPLE_COLORS[apple_color_idx]
    pygame.draw.circle(surface, col['glow'], (x, y), r + 4, 1)
    pygame.draw.ellipse(surface, (18, 30, 10), (x - r, y + r // 2, r * 2, r))
    pygame.draw.circle(surface, col['dark'], (x, y), r)
    pygame.draw.circle(surface, col['light'], (x - 3, y - 3), int(r * 0.75))
    pygame.draw.circle(surface, (255, 255, 255), (x - 5, y - 5), max(2, int(r * 0.3)))
    pygame.draw.line(surface, (80, 45, 20), (x, y - r + 2), (x + 3, y - r - 6), 2)
    pygame.draw.circle(surface, (50, 230, 50), (x + 5, y - r - 6), 3)

# ----------------- الحواجز -----------------
wall_defs = [
    pygame.Rect(int(SCREEN_WIDTH * 0.25), int(GAME_HEIGHT * 0.38), int(SCREEN_WIDTH * 0.15), 14),
    pygame.Rect(int(SCREEN_WIDTH * 0.65), int(GAME_HEIGHT * 0.26), 14, int(GAME_HEIGHT * 0.18)),
    pygame.Rect(int(SCREEN_WIDTH * 0.44), int(GAME_HEIGHT * 0.82), int(SCREEN_WIDTH * 0.16), 14)
]
wall_states = [{'timer': random.randint(100, 200), 'visible': False, 'duration': 350} for _ in range(3)]

def update_walls():
    for state in wall_states:
        state['timer'] -= 1
        if state['timer'] <= 0:
            state['visible'] = not state['visible']
            state['timer'] = state['duration'] if state['visible'] else random.randint(180, 360)

def draw_timed_wall(surface, rect):
    pygame.draw.rect(surface, (120, 115, 110), rect, border_radius=4)
    pygame.draw.rect(surface, (255, 60, 50), rect, width=2, border_radius=4)

chaser_data = {'x': 30.0, 'y': float(HEADER_HEIGHT + 30), 'speed': 1.6, 'visible': False, 'timer': 200, 'duration': 360}
def update_chaser(hx, hy):
    chaser_data['timer'] -= 1
    if chaser_data['timer'] <= 0:
        chaser_data['visible'] = not chaser_data['visible']
        if chaser_data['visible']:
            play_sound(snd_alert)
            chaser_data['timer'] = chaser_data['duration']
            corners = [
                (35.0, float(HEADER_HEIGHT + 25)),
                (float(SCREEN_WIDTH - 35), float(HEADER_HEIGHT + 25)),
                (35.0, float(GAME_HEIGHT - 35)),
                (float(SCREEN_WIDTH - 35), float(GAME_HEIGHT - 35))
            ]
            chaser_data['x'], chaser_data['y'] = random.choice(corners)
        else:
            chaser_data['timer'] = random.randint(250, 450)

    if chaser_data['visible']:
        current_spd = chaser_data['speed'] * 0.45 if freeze_timer > 0 else chaser_data['speed']
        dx = hx - chaser_data['x']
        dy = hy - chaser_data['y']
        dist = math.hypot(dx, dy)
        if dist > 2:
            chaser_data['x'] += (dx / dist) * current_spd
            chaser_data['y'] += (dy / dist) * current_spd
        return dist < 24
    return False

# ----------------- الثعبان المنافس -----------------
RIVAL_COLOR_PALETTES = [
    {"dark": (130, 20, 160), "light": (230, 40, 255), "glow": (255, 120, 255)},
    {"dark": (180, 20, 30),  "light": (255, 70, 70),   "glow": (255, 150, 150)},
    {"dark": (20, 120, 160), "light": (40, 230, 255),  "glow": (140, 255, 255)},
    {"dark": (160, 90, 0),   "light": (255, 170, 0),   "glow": (255, 230, 100)},
    {"dark": (20, 140, 60),  "light": (50, 255, 120),  "glow": (160, 255, 180)}
]

class RivalSnake:
    def __init__(self):
        self.alive = True
        self.respawn_timer = 0
        self.reset()

    def reset(self):
        start_x = random.choice([40.0, float(SCREEN_WIDTH - 40)])
        start_y = random.uniform(float(HEADER_HEIGHT + 35), float(GAME_HEIGHT - 70))
        self.points = [[start_x, start_y + i * 8] for i in range(16)]
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = 2.4
        self.score = 0
        pal = random.choice(RIVAL_COLOR_PALETTES)
        self.color_dark = pal['dark']
        self.color_light = pal['light']
        self.color_glow = pal['glow']
        self.alive = True
        self.respawn_timer = 0

    def trigger_death(self):
        self.alive = False
        self.respawn_timer = random.randint(200, 380)

    def update(self, apple_p, pet_list, player_head):
        global quest_banner_text, quest_banner_timer

        if not self.alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.reset()
                quest_banner_text = "A NEW RIVAL HAS ENTERED!"
                quest_banner_timer = 90
                play_sound(snd_alert)
            return

        hx, hy = self.points[0][0], self.points[0][1]

        if repulse_timer > 0:
            dist_to_p = math.hypot(hx - player_head[0], hy - player_head[1])
            if dist_to_p < 185:
                repulse_ang = math.atan2(hy - player_head[1], hx - player_head[0])
                force = max(5.0, (185 - dist_to_p) * 0.12)
                self.angle = repulse_ang
                nx = hx + math.cos(repulse_ang) * (self.speed + force)
                ny = hy + math.sin(repulse_ang) * (self.speed + force)
                nx = max(20, min(SCREEN_WIDTH - 20, nx))
                ny = max(HEADER_HEIGHT + 20, min(GAME_HEIGHT - 20, ny))
                self.points.insert(0, [nx, ny])
                self.points.pop()
                emit_particles(hx, hy, (200, 80, 255), count=2)
                return

        best_t = (apple_p[0], apple_p[1], 'APPLE', None)
        min_dist = math.hypot(hx - apple_p[0], hy - apple_p[1])

        for a in pet_list:
            d = math.hypot(hx - a['x'], hy - a['y'])
            if d < min_dist:
                min_dist = d
                best_t = (a['x'], a['y'], 'PET', a)

        tx, ty, t_type, p_obj = best_t
        target_a = math.atan2(ty - hy, tx - hx)
        diff = (target_a - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += diff * 0.16

        nx = hx + math.cos(self.angle) * self.speed
        ny = hy + math.sin(self.angle) * self.speed

        nx = max(20, min(SCREEN_WIDTH - 20, nx))
        ny = max(HEADER_HEIGHT + 20, min(GAME_HEIGHT - 20, ny))
        self.points.insert(0, [nx, ny])

        stole = False
        if math.hypot(nx - apple_p[0], ny - apple_p[1]) < 22:
            stole = True
            respawn_apple()
            self.score += 1
            self.speed = min(4.2, self.speed + 0.12)
            emit_particles(apple_p[0], apple_p[1], self.color_light, count=8)
            quest_banner_text = "RIVAL STOLE THE APPLE!"
            quest_banner_timer = 90
            play_sound(snd_alert)
            trigger_vibrate(0.08)

        if not stole and t_type == 'PET' and p_obj in pet_list:
            if math.hypot(nx - p_obj['x'], ny - p_obj['y']) < 24:
                stole = True
                pet_list.remove(p_obj)
                pet_list.append(create_animal())
                self.score += 1
                self.speed = min(4.2, self.speed + 0.12)
                emit_particles(nx, ny, self.color_light, count=8)
                quest_banner_text = "RIVAL STOLE YOUR PREY!"
                quest_banner_timer = 90
                play_sound(snd_alert)
                trigger_vibrate(0.08)

        if not stole:
            self.points.pop()

    def draw(self, surface):
        if not self.alive:
            return

        r = 13
        for idx, pt in enumerate(reversed(self.points)):
            px, py = int(pt[0]), int(pt[1])
            pygame.draw.circle(surface, self.color_dark, (px, py), r - 2)
            pygame.draw.circle(surface, self.color_light, (px - 1, py - 2), int((r - 2) * 0.72))

        hx, hy = int(self.points[0][0]), int(self.points[0][1])
        pygame.draw.circle(surface, self.color_glow, (hx, hy), r + 2, 2)
        pygame.draw.circle(surface, self.color_dark, (hx, hy), r)
        pygame.draw.circle(surface, self.color_light, (hx - 2, hy - 2), int(r * 0.75))

        e1x = hx + int(math.cos(self.angle + 0.7) * (r - 2))
        e1y = hy + int(math.sin(self.angle + 0.7) * (r - 2))
        e2x = hx + int(math.cos(self.angle - 0.7) * (r - 2))
        e2y = hy + int(math.sin(self.angle - 0.7) * (r - 2))
        pygame.draw.circle(surface, (255, 30, 30), (e1x, e1y), 4)
        pygame.draw.circle(surface, (255, 30, 30), (e2x, e2y), 4)

rival_snake = RivalSnake()

# ----------------- كائن "أم أربعة وأربعين" -----------------
class RealisticCentipede:
    def __init__(self):
        self.is_paused = False
        self.level = 1
        self.next_level_score = 1000
        self.current_step = 1000
        self.hits = 0
        self.max_lives = 3
        self.invulnerable_timer = 0
        self.custom_colors = None
        self.wiggle_phase = 0.0
        self.leg_phase = 0.0
        self.reset()

    def reset(self):
        sx = SCREEN_WIDTH // 2
        sy = int(GAME_HEIGHT * 0.32)
        self.points = [[sx, sy + i * 9] for i in range(24)]
        self.angle = -math.pi / 2
        self.target_angle = self.angle
        self.score = 0
        self.level = 1
        self.next_level_score = 1000
        self.current_step = 1000
        self.alive = True
        self.boost_timer = 0
        self.hits = 0
        self.max_lives = [5, 3, 2, 1][selected_diff]
        self.invulnerable_timer = 0
        self.wiggle_phase = 0.0
        self.leg_phase = 0.0
        skin = SNAKE_SKINS[selected_color]
        self.custom_colors = {"dark": skin['dark'], "light": skin['light'], "glow": skin['glow']}
        rival_snake.reset()

    def get_colors(self):
        if double_points_timer > 0:
            c_val = int((math.sin(timer * 8) + 1.0) * 127)
            return (c_val, 255 - c_val, 200), (255, 230, 80), (255, 255, 180)
        if self.custom_colors:
            return self.custom_colors['dark'], self.custom_colors['light'], self.custom_colors['glow']
        skin = SNAKE_SKINS[selected_color]
        return skin['dark'], skin['light'], skin['glow']

    def get_base_speed(self):
        spd = [2.5, 3.8, 5.0, 6.4][selected_speed]
        spd += (self.level - 1) * 0.12
        spd -= self.hits * 0.15
        if pond_rect.collidepoint(int(self.points[0][0]), int(self.points[0][1])):
            spd *= 0.65
        if self.boost_timer > 0:
            spd *= 1.80
        return max(1.6, spd)

    def trigger_hit(self):
        if self.invulnerable_timer > 0 or shield_timer > 0:
            return False
        self.hits += 1
        self.invulnerable_timer = 60
        trigger_vibrate(0.12)
        play_sound(snd_hit)
        if self.hits >= self.max_lives:
            self.alive = False
            play_sound(snd_gameover)
            return True
        return False

    def update(self):
        global shield_timer, freeze_timer, magnet_timer, double_points_timer, repulse_timer
        global total_coins, quest_banner_text, quest_banner_timer
        global lvl_banner_timer, lvl_banner_x, lvl_banner_text, lvl_banner_sub

        if not self.alive or self.is_paused:
            return

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        if self.boost_timer > 0:
            self.boost_timer -= 1

        self.wiggle_phase += 0.28
        self.leg_phase += 0.45

        diff = (self.target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += diff * 0.38

        spd = self.get_base_speed()
        wiggle_offset = math.sin(self.wiggle_phase) * 1.8
        hx = self.points[0][0] + math.cos(self.angle) * spd - math.sin(self.angle) * wiggle_offset
        hy = self.points[0][1] + math.sin(self.angle) * spd + math.cos(self.angle) * wiggle_offset

        r = 17 + self.hits * 3
        if hx < r or hx > SCREEN_WIDTH - r or hy < HEADER_HEIGHT + r or hy > GAME_HEIGHT - r:
            self.trigger_hit()
            return

        if selected_objects in (0, 1):
            hrect = pygame.Rect(hx - r, hy - r, r * 2, r * 2)
            for i, w in enumerate(wall_defs):
                if wall_states[i]['visible'] and hrect.colliderect(w):
                    self.trigger_hit()
                    return

        if selected_objects in (0, 2):
            if update_chaser(hx, hy):
                self.trigger_hit()
                return

        if rival_snake.alive:
            eaten_rival = False
            for r_pt in rival_snake.points:
                if math.hypot(hx - r_pt[0], hy - r_pt[1]) < r + 14:
                    eaten_rival = True
                    break

            if eaten_rival:
                rival_snake.trigger_death()
                pts = 200 if double_points_timer > 0 else 100
                self.score += pts
                total_coins += 25
                emit_particles(hx, hy, (255, 120, 255), count=16)
                play_sound(snd_kill)
                trigger_vibrate(0.18)
                quest_banner_text = f"DEVOURED RIVAL! +{pts} PTS"
                quest_banner_timer = 110
                progress_quest("KILL_RIVAL", 1)

        for pt in self.points[16:]:
            if math.hypot(hx - pt[0], hy - pt[1]) < r:
                self.trigger_hit()
                return

        self.points.insert(0, [hx, hy])

        ate = False

        if math.hypot(hx - apple_pos[0], hy - apple_pos[1]) < r + 14:
            pts = 20 if double_points_timer > 0 else 10
            self.score += pts
            total_coins += 2
            ate_col = APPLE_COLORS[apple_color_idx]
            self.custom_colors = {"dark": ate_col['dark'], "light": ate_col['light'], "glow": ate_col['glow']}
            play_sound(snd_eat)
            trigger_vibrate(0.04)
            emit_particles(apple_pos[0], apple_pos[1], ate_col['light'], count=6)
            respawn_apple()
            progress_quest("EAT_APPLE", 1)
            ate = True

        if selected_objects in (0, 3):
            for a in animals:
                if math.hypot(hx - a['x'], hy - a['y']) < r + a['size']:
                    pts = 100 if double_points_timer > 0 else 50
                    self.score += pts
                    total_coins += 10
                    play_sound(snd_hunt)
                    trigger_vibrate(0.08)
                    emit_particles(a['x'], a['y'], (255, 230, 100), count=10)
                    if a['type'] == 'RABBIT':
                        progress_quest("HUNT_RABBIT", 1)
                    elif a['type'] == 'SQUIRREL':
                        progress_quest("HUNT_SQUIRREL", 1)
                    animals.remove(a)
                    animals.append(create_animal())
                    ate = True
                    break

        if self.score >= self.next_level_score:
            self.level += 1
            self.current_step += 100
            self.next_level_score += self.current_step

            lvl_banner_x = -banner_bw
            lvl_banner_timer = 160
            lvl_banner_text = f"LEVEL UP! LEVEL {self.level}"
            lvl_banner_sub = f"+100 COINS & LIFE REPAIRED! (NEXT: {self.next_level_score}P)"

            total_coins += 100
            if self.hits > 0:
                self.hits -= 1

            play_sound(snd_levelup)
            trigger_vibrate(0.25)
            for _ in range(3):
                emit_particles(
                    SCREEN_WIDTH // 2 + random.randint(-60, 60),
                    HEADER_HEIGHT + 40,
                    random.choice([(255, 215, 0), (0, 240, 255), (255, 80, 180), (100, 255, 120)]),
                    count=12
                )

        if powerup_item['active'] and math.hypot(hx - powerup_item['x'], hy - powerup_item['y']) < r + 15:
            if powerup_item['type'] == 'REPULSE':
                repulse_timer = 320
                play_sound(snd_repulse)
                quest_banner_text = "REPULSION FIELD ACTIVATED!"
                quest_banner_timer = 90
            elif powerup_item['type'] == 'MAGNET':
                magnet_timer = 300
                play_sound(snd_bonus)
            elif powerup_item['type'] == 'MUSHROOM':
                double_points_timer = 250
                play_sound(snd_bonus)
            elif powerup_item['type'] == 'FREEZE':
                freeze_timer = 200
                play_sound(snd_bonus)
            else:
                shield_timer = 200
                play_sound(snd_bonus)

            emit_particles(powerup_item['x'], powerup_item['y'], (220, 80, 255), count=12)
            powerup_item['active'] = False
            powerup_item['timer'] = random.randint(220, 400)

        if not ate:
            self.points.pop()

    def draw_3d(self, surface):
        dark, light, glow = self.get_colors()
        max_rad = 17 + self.hits * 3
        total_pts = len(self.points)

        for idx in range(1, total_pts):
            pt = self.points[idx]
            prev_pt = self.points[idx - 1]
            seg_angle = math.atan2(prev_pt[1] - pt[1], prev_pt[0] - pt[0])
            leg_wave = math.sin(self.leg_phase + idx * 0.65) * 6
            leg_len = max_rad + 12

            r_ang = seg_angle + math.pi / 2.2
            knee_rx = pt[0] + math.cos(r_ang) * (leg_len * 0.6)
            knee_ry = pt[1] + math.sin(r_ang) * (leg_len * 0.6)
            tip_rx = pt[0] + math.cos(r_ang) * leg_len + math.cos(seg_angle) * leg_wave
            tip_ry = pt[1] + math.sin(r_ang) * leg_len + math.sin(seg_angle) * leg_wave
            pygame.draw.line(surface, dark, (pt[0], pt[1]), (knee_rx, knee_ry), 4)
            pygame.draw.line(surface, light, (knee_rx, knee_ry), (tip_rx, tip_ry), 3)

            l_ang = seg_angle - math.pi / 2.2
            knee_lx = pt[0] + math.cos(l_ang) * (leg_len * 0.6)
            knee_ly = pt[1] + math.sin(l_ang) * (leg_len * 0.6)
            tip_lx = pt[0] + math.cos(l_ang) * leg_len + math.cos(seg_angle) * (-leg_wave)
            tip_ly = pt[1] + math.sin(l_ang) * leg_len + math.sin(seg_angle) * (-leg_wave)
            pygame.draw.line(surface, dark, (pt[0], pt[1]), (knee_lx, knee_ly), 4)
            pygame.draw.line(surface, light, (knee_lx, knee_ly), (tip_lx, tip_ly), 3)

        for idx in range(total_pts - 1, 0, -1):
            pt = self.points[idx]
            ratio = 1.0 - (idx / total_pts)
            r = max(5, int(max_rad * (0.35 + 0.65 * math.sin(ratio * (math.pi / 2)))))
            px, py = int(pt[0]), int(pt[1])

            pygame.draw.ellipse(surface, (12, 20, 8), (px - r, py + r // 3, r * 2, r))
            pygame.draw.circle(surface, dark, (px, py), r)
            pygame.draw.circle(surface, light, (px - 2, py - 3), max(3, int(r * 0.72)))
            pygame.draw.circle(surface, (255, 255, 255), (px - 3, py - 4), max(1, int(r * 0.28)))

        hx, hy = self.points[0][0], self.points[0][1]
        head_len = max_rad * 1.5
        head_w = max_rad * 1.3

        tip_x = hx + math.cos(self.angle) * head_len
        tip_y = hy + math.sin(self.angle) * head_len
        left_x = hx + math.cos(self.angle + 2.3) * head_w
        left_y = hy + math.sin(self.angle + 2.3) * head_w
        right_x = hx + math.cos(self.angle - 2.3) * head_w
        right_y = hy + math.sin(self.angle - 2.3) * head_w

        head_pts = [(tip_x, tip_y), (left_x, left_y), (hx, hy), (right_x, right_y)]

        if repulse_timer > 0:
            rep_rad = int(55 + math.sin(timer * 12) * 8)
            pygame.draw.circle(surface, (210, 80, 255), (int(hx), int(hy)), rep_rad, 3)
            pygame.draw.circle(surface, (255, 160, 255), (int(hx), int(hy)), rep_rad - 6, 1)

        if shield_timer > 0:
            pygame.draw.circle(surface, (255, 215, 0), (int(hx), int(hy)), int(head_len + 8), 4)
        if magnet_timer > 0:
            pygame.draw.circle(surface, (255, 80, 80), (int(hx), int(hy)), int(head_len + 12), 2)

        pygame.draw.polygon(surface, dark, head_pts)
        inner_pts = [
            (tip_x - math.cos(self.angle) * 4, tip_y - math.sin(self.angle) * 4),
            (left_x * 0.85 + hx * 0.15, left_y * 0.85 + hy * 0.15),
            (right_x * 0.85 + hx * 0.15, right_y * 0.85 + hy * 0.15)
        ]
        pygame.draw.polygon(surface, light, inner_pts)

        ant_l = 26
        ant1_x = tip_x + math.cos(self.angle + 0.40) * ant_l
        ant1_y = tip_y + math.sin(self.angle + 0.40) * ant_l
        pygame.draw.line(surface, light, (tip_x, tip_y), (ant1_x, ant1_y), 3)
        pygame.draw.circle(surface, (255, 255, 255), (int(ant1_x), int(ant1_y)), 3)

        ant2_x = tip_x + math.cos(self.angle - 0.40) * ant_l
        ant2_y = tip_y + math.sin(self.angle - 0.40) * ant_l
        pygame.draw.line(surface, light, (tip_x, tip_y), (ant2_x, ant2_y), 3)
        pygame.draw.circle(surface, (255, 255, 255), (int(ant2_x), int(ant2_y)), 3)

        pincer_rx = tip_x + math.cos(self.angle + 0.9) * 12
        pincer_ry = tip_y + math.sin(self.angle + 0.9) * 12
        pincer_lx = tip_x + math.cos(self.angle - 0.9) * 12
        pincer_ly = tip_y + math.sin(self.angle - 0.9) * 12
        pygame.draw.line(surface, (255, 40, 50), (tip_x, tip_y), (pincer_rx, pincer_ry), 3)
        pygame.draw.line(surface, (255, 40, 50), (tip_x, tip_y), (pincer_lx, pincer_ly), 3)

        eye_dist = head_w * 0.62
        eye_fwd = head_len * 0.42
        e1_x = int(hx + math.cos(self.angle) * eye_fwd + math.cos(self.angle + math.pi / 2) * eye_dist)
        e1_y = int(hy + math.sin(self.angle) * eye_fwd + math.sin(self.angle + math.pi / 2) * eye_dist)
        e2_x = int(hx + math.cos(self.angle) * eye_fwd - math.cos(self.angle + math.pi / 2) * eye_dist)
        e2_y = int(hy + math.sin(self.angle) * eye_fwd - math.sin(self.angle + math.pi / 2) * eye_dist)

        for ex, ey in [(e1_x, e1_y), (e2_x, e2_y)]:
            pygame.draw.circle(surface, (255, 230, 20), (ex, ey), 5)
            pygame.draw.circle(surface, (10, 10, 10), (ex, ey), 3)
            pygame.draw.circle(surface, (255, 255, 255), (ex - 1, ey - 1), 1)

snake = RealisticCentipede()

# ----------------- تكبير الأزرار الدائرية العلوية والأزرار الجانبية -----------------
CIRCLE_RAD = 56          # تكبير نصف قطر أزرار الخيارات من 48 إلى 56
SIDE_BTN_RAD = 42        # تكبير نصف قطر زري PLAY و BOOST من 32 إلى 42

circ_y1 = GAME_HEIGHT + int(PANEL_HEIGHT * 0.13)
circ_y2 = GAME_HEIGHT + int(PANEL_HEIGHT * 0.28)

circ_menu = (int(SCREEN_WIDTH * 0.18), circ_y1)
circ_mode = (int(SCREEN_WIDTH * 0.50), circ_y1)
circ_skin = (int(SCREEN_WIDTH * 0.82), circ_y1)

circ_speed = (int(SCREEN_WIDTH * 0.24), circ_y2)
circ_music = (int(SCREEN_WIDTH * 0.76), circ_y2)

circ_nitro = (SCREEN_WIDTH - 64, GAME_HEIGHT + int(PANEL_HEIGHT * 0.54))
circ_pause_left = (64, GAME_HEIGHT + int(PANEL_HEIGHT * 0.54))

# ----------------- قرص التحكم -----------------
dpad_center_x = SCREEN_WIDTH // 2
dpad_center_y = GAME_HEIGHT + int(PANEL_HEIGHT * 0.54)
DPAD_OUTER_RAD = int(SCREEN_WIDTH * 0.31)
DPAD_STICK_RAD = int(DPAD_OUTER_RAD * 0.34)

stick_curr_x = float(dpad_center_x)
stick_curr_y = float(dpad_center_y)
is_dragging_stick = False

def draw_fast_dpad(surface, cx, cy, rad, stick_x, stick_y):
    pygame.draw.circle(surface, (14, 20, 30), (cx, cy), rad)
    pygame.draw.circle(surface, (0, 190, 240), (cx, cy), rad, 4)
    pygame.draw.circle(surface, (22, 55, 85), (cx, cy), int(rad * 0.72), 2)
    pygame.draw.line(surface, (25, 60, 90), (cx - rad + 8, cy), (cx + rad - 8, cy), 1)
    pygame.draw.line(surface, (25, 60, 90), (cx, cy - rad + 8), (cx, cy + rad - 8), 1)

    offset = int(rad * 0.68)
    arrow_sz = int(rad * 0.26)

    pts_up = [(cx, cy - offset - arrow_sz // 2), (cx - arrow_sz, cy - offset + arrow_sz // 2), (cx + arrow_sz, cy - offset + arrow_sz // 2)]
    pygame.draw.polygon(surface, (0, 240, 255), pts_up)

    pts_down = [(cx, cy + offset + arrow_sz // 2), (cx - arrow_sz, cy + offset - arrow_sz // 2), (cx + arrow_sz, cy + offset - arrow_sz // 2)]
    pygame.draw.polygon(surface, (0, 240, 255), pts_down)

    pts_left = [(cx - offset - arrow_sz // 2, cy), (cx - offset + arrow_sz // 2, cy - arrow_sz), (cx - offset + arrow_sz // 2, cy + arrow_sz)]
    pygame.draw.polygon(surface, (0, 240, 255), pts_left)

    pts_right = [(cx + offset + arrow_sz // 2, cy), (cx + offset - arrow_sz // 2, cy - arrow_sz), (cx + offset - arrow_sz // 2, cy + arrow_sz)]
    pygame.draw.polygon(surface, (0, 240, 255), pts_right)

    if is_dragging_stick:
        pygame.draw.line(surface, (0, 255, 240), (cx, cy), (int(stick_x), int(stick_y)), 3)

    sx, sy = int(stick_x), int(stick_y)
    pygame.draw.circle(surface, (12, 18, 28), (sx, sy), DPAD_STICK_RAD + 2)
    pygame.draw.circle(surface, (0, 240, 255), (sx, sy), DPAD_STICK_RAD, 3)
    pygame.draw.circle(surface, (25, 65, 100), (sx, sy), DPAD_STICK_RAD - 4)
    pygame.draw.circle(surface, (255, 255, 255), (sx - 3, sy - 3), max(2, DPAD_STICK_RAD // 4))

# زر الإيقاف العلوي
btn_pause_rect = pygame.Rect(SCREEN_WIDTH - 110, 16, 94, 52)
touch_start_pos = None

# ----------------- الحلقة الرئيسية -----------------
timer = 0.0
running = True

while running:
    clock.tick(60)
    timer += 0.05

    if not is_dragging_stick:
        stick_curr_x += (dpad_center_x - stick_curr_x) * 0.35
        stick_curr_y += (dpad_center_y - stick_curr_y) * 0.35

    if not in_menu and selected_control == 2:
        if has_accelerometer and accelerometer_sensor:
            try:
                accel_data = accelerometer_sensor.acceleration
                if accel_data and accel_data[0] is not None:
                    ax, ay = accel_data[0], accel_data[1]
                    if abs(ax) > 1.2 or abs(ay) > 1.2:
                        snake.target_angle = math.atan2(-ay, ax)
            except Exception:
                pass

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: snake.target_angle = -math.pi / 2
            elif event.key == pygame.K_DOWN: snake.target_angle = math.pi / 2
            elif event.key == pygame.K_LEFT: snake.target_angle = math.pi
            elif event.key == pygame.K_RIGHT: snake.target_angle = 0
            elif event.key == pygame.K_SPACE:
                if in_menu:
                    in_menu = False
                    snake.reset()
                else:
                    snake.is_paused = not snake.is_paused

        elif event.type == pygame.MOUSEBUTTONDOWN:
            touch_start_pos = event.pos
            mx, my = event.pos

            if in_menu:
                bw = min(530, SCREEN_WIDTH - 140)
                bx = SCREEN_WIDTH // 2 - bw // 2
                start_y = 95
                bottom_clearance = 160
                btn_gap = 10
                total_usable_h = SCREEN_HEIGHT - start_y - bottom_clearance
                btn_height = max(50, int((total_usable_h - (6 * btn_gap)) / 7.0) - 14)

                r_play = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 0, bw, btn_height)
                r_skin = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 1, bw, btn_height)
                r_speed = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 2, bw, btn_height)
                r_ctrl = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 3, bw, btn_height)
                r_obj = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 4, bw, btn_height)
                r_music = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 5, bw, btn_height)
                r_diff = pygame.Rect(bx, start_y + (btn_height + btn_gap) * 6, bw, btn_height)

                if r_play.collidepoint(mx, my):
                    in_menu = False
                    snake.reset()
                elif r_skin.collidepoint(mx, my):
                    selected_color = (selected_color + 1) % len(SNAKE_SKINS)
                    skin = SNAKE_SKINS[selected_color]
                    snake.custom_colors = {"dark": skin['dark'], "light": skin['light'], "glow": skin['glow']}
                elif r_speed.collidepoint(mx, my):
                    selected_speed = (selected_speed + 1) % len(SPEED_LEVELS)
                elif r_ctrl.collidepoint(mx, my):
                    selected_control = (selected_control + 1) % len(CONTROL_MODES)
                elif r_obj.collidepoint(mx, my):
                    selected_objects = (selected_objects + 1) % len(OBJECT_MODE_NAMES)
                elif r_music.collidepoint(mx, my):
                    change_track(1)
                elif r_diff.collidepoint(mx, my):
                    selected_diff = (selected_diff + 1) % len(DIFFICULTY_MODES)
                    snake.max_lives = [5, 3, 2, 1][selected_diff]
            else:
                if btn_pause_rect.collidepoint(mx, my):
                    snake.is_paused = not snake.is_paused
                    continue

                if math.hypot(mx - circ_menu[0], my - circ_menu[1]) <= CIRCLE_RAD + 8:
                    in_menu = True
                    continue

                if not snake.alive:
                    snake.reset()
                else:
                    # فحص الضغط على الأزرار الجانبية المكبرة بدقة
                    if math.hypot(mx - circ_pause_left[0], my - circ_pause_left[1]) <= SIDE_BTN_RAD + 6:
                        snake.is_paused = not snake.is_paused
                    elif math.hypot(mx - circ_nitro[0], my - circ_nitro[1]) <= SIDE_BTN_RAD + 6:
                        snake.boost_timer = 50
                        progress_quest("USE_BOOST", 1)
                        play_sound(snd_alert)
                    elif math.hypot(mx - circ_mode[0], my - circ_mode[1]) <= CIRCLE_RAD + 8:
                        selected_control = (selected_control + 1) % len(CONTROL_MODES)
                    elif math.hypot(mx - circ_skin[0], my - circ_skin[1]) <= CIRCLE_RAD + 8:
                        selected_color = (selected_color + 1) % len(SNAKE_SKINS)
                        skin = SNAKE_SKINS[selected_color]
                        snake.custom_colors = {"dark": skin['dark'], "light": skin['light'], "glow": skin['glow']}
                    elif math.hypot(mx - circ_speed[0], my - circ_speed[1]) <= CIRCLE_RAD + 8:
                        selected_speed = (selected_speed + 1) % len(SPEED_LEVELS)
                    elif math.hypot(mx - circ_music[0], my - circ_music[1]) <= CIRCLE_RAD + 8:
                        change_track(1)

                    dist_to_center = math.hypot(mx - dpad_center_x, my - dpad_center_y)
                    if dist_to_center <= DPAD_STICK_RAD + 12:
                        is_dragging_stick = True
                    elif selected_control == 0 and dist_to_center <= DPAD_OUTER_RAD + 20:
                        dx = mx - dpad_center_x
                        dy = my - dpad_center_y
                        if abs(dx) > abs(dy):
                            snake.target_angle = 0 if dx > 0 else math.pi
                        else:
                            snake.target_angle = math.pi / 2 if dy > 0 else -math.pi / 2

        elif event.type == pygame.MOUSEMOTION:
            if is_dragging_stick:
                mx, my = event.pos
                dx = mx - dpad_center_x
                dy = my - dpad_center_y
                dist = math.hypot(dx, dy)
                max_reach = DPAD_OUTER_RAD - DPAD_STICK_RAD

                if dist > max_reach:
                    stick_curr_x = dpad_center_x + (dx / dist) * max_reach
                    stick_curr_y = dpad_center_y + (dy / dist) * max_reach
                else:
                    stick_curr_x = mx
                    stick_curr_y = my

                if dist > 8:
                    snake.target_angle = math.atan2(dy, dx)

        elif event.type == pygame.MOUSEBUTTONUP:
            is_dragging_stick = False
            if not in_menu and selected_control == 1 and touch_start_pos:
                end_pos = event.pos
                dx = end_pos[0] - touch_start_pos[0]
                dy = end_pos[1] - touch_start_pos[1]
                if math.hypot(dx, dy) > 25:
                    if abs(dx) > abs(dy):
                        snake.target_angle = 0 if dx > 0 else math.pi
                    else:
                        snake.target_angle = math.pi / 2 if dy > 0 else -math.pi / 2
            touch_start_pos = None

    screen.fill((8, 12, 18))

    if in_menu:
        screen.blit(menu_bg_surface, (0, 0))

        title_pulse = int(math.sin(timer * 4) * 20)
        t_col = (0, min(255, 235 + title_pulse), 160)
        t_surf = font_title.render("REAL CENTIPEDE", True, t_col)
        screen.blit(t_surf, (SCREEN_WIDTH // 2 - t_surf.get_width() // 2, 28))

        bw = min(530, SCREEN_WIDTH - 140)
        bx = SCREEN_WIDTH // 2 - bw // 2
        start_y = 95
        bottom_clearance = 160
        btn_gap = 10
        total_usable_h = SCREEN_HEIGHT - start_y - bottom_clearance
        btn_height = max(50, int((total_usable_h - (6 * btn_gap)) / 7.0) - 14)

        r_play = pygame.Rect(bx, start_y, bw, btn_height)
        pygame.draw.rect(screen, (0, 180, 80), r_play, border_radius=14)
        pygame.draw.rect(screen, (160, 255, 180), r_play, width=3, border_radius=14)
        st_txt = font_title.render("START GAME", True, (255, 255, 255))
        screen.blit(st_txt, (r_play.centerx - st_txt.get_width() // 2, r_play.centery - st_txt.get_height() // 2))

        menu_items = [
            (SNAKE_SKINS[selected_color]['name'], SNAKE_SKINS[selected_color]['light'], (36, 18, 28)),
            (SPEED_LEVELS[selected_speed], (255, 230, 0), (40, 34, 10)),
            (CONTROL_MODES[selected_control], (0, 230, 255), (10, 32, 44)),
            (OBJECT_MODE_NAMES[selected_objects], (170, 255, 50), (24, 40, 12)),
            (f"AUDIO: {audio_playlist[current_audio_idx][:14]}", (255, 80, 210), (40, 14, 36)),
            (DIFFICULTY_MODES[selected_diff], (255, 60, 60), (44, 12, 12))
        ]

        for idx, (txt, fg_col, bg_col) in enumerate(menu_items):
            rect = pygame.Rect(bx, start_y + (btn_height + btn_gap) * (idx + 1), bw, btn_height)
            pygame.draw.rect(screen, bg_col, rect, border_radius=14)
            pygame.draw.rect(screen, fg_col, rect, width=2, border_radius=14)
            surf = font_btn_giant.render(txt, True, fg_col)
            screen.blit(surf, (rect.centerx - surf.get_width() // 2, rect.centery - surf.get_height() // 2))

    else:
        if selected_objects in (0, 1): update_walls()
        if selected_objects in (0, 3): update_animals(snake.points[0][0], snake.points[0][1])
        update_trees_season(snake.level)
        update_powerups()
        update_apple(snake.points[0][0], snake.points[0][1])
        snake.update()
        rival_snake.update(apple_pos, animals, snake.points[0])

        screen.blit(world_surface, (0, 0))

        draw_water_pond(screen, timer)

        for tx, ty, tr in tall_trees:
            draw_tree(screen, tx, ty, tr)

        if selected_objects in (0, 1):
            for i, rect in enumerate(wall_defs):
                if wall_states[i]['visible']: draw_timed_wall(screen, rect)

        if selected_objects in (0, 3):
            for a in animals:
                draw_animal(screen, a)

        if selected_objects in (0, 2) and chaser_data['visible']:
            cx, cy = int(chaser_data['x']), int(chaser_data['y'])
            pygame.draw.circle(screen, (255, 30, 30), (cx, cy), 14)
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 4)

        draw_powerup(screen, timer)
        draw_3d_apple(screen, apple_pos)
        
        rival_snake.draw(screen)
        snake.draw_3d(screen)
        update_and_draw_particles(screen)

        if lvl_banner_timer > 0:
            lvl_banner_timer -= 1
            target_x = SCREEN_WIDTH // 2 - banner_bw // 2
            if lvl_banner_timer > 30:
                lvl_banner_x += (target_x - lvl_banner_x) * 0.18
            else:
                lvl_banner_x += (SCREEN_WIDTH + 50 - lvl_banner_x) * 0.16

            banner_surf.fill((16, 26, 42, 205))
            pygame.draw.rect(banner_surf, (255, 215, 0), (0, 0, banner_bw, banner_bh), width=2, border_radius=12)

            t1 = font_player_name.render(lvl_banner_text, True, (255, 235, 50))
            t2 = font_score_bold.render(lvl_banner_sub, True, (0, 255, 210))
            banner_surf.blit(t1, (banner_bw // 2 - t1.get_width() // 2, 4))
            banner_surf.blit(t2, (banner_bw // 2 - t2.get_width() // 2, 26))

            screen.blit(banner_surf, (int(lvl_banner_x), HEADER_HEIGHT + 6))

        bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT)
        pygame.draw.rect(screen, (12, 16, 24), bar_rect)
        pygame.draw.line(screen, (0, 255, 170), (0, HEADER_HEIGHT), (SCREEN_WIDTH, HEADER_HEIGHT), 4)

        name_surf = font_player_name.render("FOULOLOU MILOUD", True, (0, 255, 190))
        screen.blit(name_surf, (16, HEADER_HEIGHT // 2 - name_surf.get_height() // 2))

        q_text = f"[LVL {snake.level} -> {snake.next_level_score}P]  COINS: {total_coins}"
        sc_txt = font_score_bold.render(q_text, True, (255, 230, 80))
        screen.blit(sc_txt, (SCREEN_WIDTH // 2 - sc_txt.get_width() // 2, HEADER_HEIGHT // 2 - sc_txt.get_height() // 2))

        lives_str = f"LIVES: {max(0, snake.max_lives - snake.hits)}"
        hud_right = font_score_bold.render(f"SC:{snake.score}  {lives_str}", True, (255, 255, 255))
        screen.blit(hud_right, (btn_pause_rect.left - hud_right.get_width() - 18, HEADER_HEIGHT // 2 - hud_right.get_height() // 2))

        pygame.draw.rect(screen, (25, 35, 50), btn_pause_rect, border_radius=10)
        pygame.draw.rect(screen, (0, 210, 255), btn_pause_rect, width=2, border_radius=10)
        p_symbol = "PLAY" if snake.is_paused else "PAUSE"
        p_surf = font_score_bold.render(p_symbol, True, (0, 210, 255))
        screen.blit(p_surf, (btn_pause_rect.centerx - p_surf.get_width() // 2, btn_pause_rect.centery - p_surf.get_height() // 2))

        # ----------------- لوحة التحكم السفلية ورسم الأزرار المكبرة -----------------
        screen.blit(panel_bg_surface, (0, GAME_HEIGHT))
        pygame.draw.line(screen, (0, 210, 255), (0, GAME_HEIGHT), (SCREEN_WIDTH, GAME_HEIGHT), 3)

        pygame.draw.line(screen, (0, 110, 160), circ_menu, circ_mode, 2)
        pygame.draw.line(screen, (0, 110, 160), circ_mode, circ_skin, 2)
        pygame.draw.line(screen, (80, 40, 130), circ_speed, (dpad_center_x, dpad_center_y), 1)
        pygame.draw.line(screen, (80, 40, 130), circ_music, (dpad_center_x, dpad_center_y), 1)

        # الأزرار الدائرية الخمسة المكبرة (CIRCLE_RAD = 56)
        top_five_circles = [
            (circ_menu, "MENU", (255, 215, 0)),
            (circ_mode, CONTROL_SHORT[selected_control], (0, 230, 255)),
            (circ_skin, "SKIN", SNAKE_SKINS[selected_color]['light']),
            (circ_speed, "SPEED", (255, 230, 0)),
            (circ_music, "MUSIC", (255, 80, 220))
        ]
        
        for pos, label, col in top_five_circles:
            pygame.draw.circle(screen, (16, 24, 38), pos, CIRCLE_RAD)
            pygame.draw.circle(screen, col, pos, CIRCLE_RAD, 3)
            pygame.draw.circle(screen, (255, 255, 255), pos, CIRCLE_RAD - 6, 1)
            txt_s = font_circle_giant.render(label, True, col)
            screen.blit(txt_s, (pos[0] - txt_s.get_width() // 2, pos[1] - txt_s.get_height() // 2))

        # زر PAUSE/PLAY الأيسر المكبر (SIDE_BTN_RAD = 42)
        pause_glow = (180, 255, 200) if snake.is_paused else (140, 240, 255)
        pygame.draw.circle(screen, (18, 26, 40), circ_pause_left, SIDE_BTN_RAD)
        pygame.draw.circle(screen, pause_glow, circ_pause_left, SIDE_BTN_RAD, 3)
        pause_lbl_txt = "PLAY" if snake.is_paused else "PAUSE"
        pause_lbl = font_side_btn.render(pause_lbl_txt, True, pause_glow)
        screen.blit(pause_lbl, (circ_pause_left[0] - pause_lbl.get_width() // 2, circ_pause_left[1] - pause_lbl.get_height() // 2))

        # زر BOOST الأيمن المكبر (SIDE_BTN_RAD = 42)
        pygame.draw.circle(screen, (180, 50, 10), circ_nitro, SIDE_BTN_RAD)
        pygame.draw.circle(screen, (255, 160, 40), circ_nitro, SIDE_BTN_RAD, 3)
        nitro_lbl = font_side_btn.render("BOOST", True, (255, 255, 255))
        screen.blit(nitro_lbl, (circ_nitro[0] - nitro_lbl.get_width() // 2, circ_nitro[1] - nitro_lbl.get_height() // 2))

        if selected_control == 0:
            draw_fast_dpad(screen, dpad_center_x, dpad_center_y, DPAD_OUTER_RAD, stick_curr_x, stick_curr_y)
        elif selected_control == 1:
            info_txt = font_title.render("SWIPE SCREEN TO STEER", True, (0, 230, 255))
            screen.blit(info_txt, (dpad_center_x - info_txt.get_width() // 2, dpad_center_y - 20))
        elif selected_control == 2:
            info_txt = font_title.render("TILT PHONE TO STEER", True, (255, 215, 0))
            screen.blit(info_txt, (dpad_center_x - info_txt.get_width() // 2, dpad_center_y - 25))
            pygame.draw.circle(screen, (40, 50, 65), (dpad_center_x, dpad_center_y + 40), 45, 4)
            gx = dpad_center_x + int(math.cos(snake.angle) * 35)
            gy = dpad_center_y + 40 + int(math.sin(snake.angle) * 35)
            pygame.draw.line(screen, (0, 255, 180), (dpad_center_x, dpad_center_y + 40), (gx, gy), 5)
            pygame.draw.circle(screen, (255, 255, 255), (gx, gy), 9)

        if quest_banner_timer > 0:
            quest_banner_timer -= 1
            qb_surf = font_score_bold.render(quest_banner_text, True, (255, 80, 80) if "STOLE" in quest_banner_text else (0, 255, 140))
            screen.blit(qb_surf, (SCREEN_WIDTH // 2 - qb_surf.get_width() // 2, GAME_HEIGHT + 10))
        elif audio_banner_timer > 0:
            audio_banner_timer -= 1
            ab_surf = font_score_bold.render(audio_banner_text, True, (255, 235, 60))
            screen.blit(ab_surf, (SCREEN_WIDTH // 2 - ab_surf.get_width() // 2, GAME_HEIGHT + 10))

        if snake.is_paused:
            pause_overlay = font_big_bold.render("PAUSED", True, (0, 220, 255))
            screen.blit(pause_overlay, (SCREEN_WIDTH // 2 - pause_overlay.get_width() // 2, GAME_HEIGHT // 2 - 30))

        if not snake.alive:
            if snake.score > high_score:
                high_score = snake.score
            save_game_data(high_score, total_coins)
            gov = font_big_bold.render("GAME OVER", True, (255, 40, 40))
            screen.blit(gov, (SCREEN_WIDTH // 2 - gov.get_width() // 2, GAME_HEIGHT // 2 - 25))
            ret = font_score_bold.render("TAP ANYWHERE TO RETRY", True, (255, 255, 255))
            screen.blit(ret, (SCREEN_WIDTH // 2 - ret.get_width() // 2, GAME_HEIGHT // 2 + 40))

    pygame.display.flip()

pygame.quit()
sys.exit()
