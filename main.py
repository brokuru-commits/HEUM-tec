#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, math, random
from datetime import datetime

# ============================================================
# SYSTEM TWEAKS: Bildschirmschoner auf dem Pi erzwingen aus!
# ============================================================
os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '0'
try:
    # Verhindert DPMS (Blackscreen) auf X11-Systemen wie dem Pi
    os.system("xset s off > /dev/null 2>&1")
    os.system("xset -dpms > /dev/null 2>&1")
    os.system("xset s noblank > /dev/null 2>&1")
except:
    pass

import pygame
from hacking_game import HackingGame
from critl_personality import CRITLPersonality
from boot_screen import BootScreen
from update_screen import UpdateScreen
from update_system import UpdateSystem

# ============================================================
# FIXED SPECS (640x480 GOLD-STANDARD)
# ============================================================
W, H = 640, 480
FPS = 25

# --- GLOBAL STATES ---
success_flash_time = 0
active_event = None
ev_start = 0
ev_dur = 0

# --- TIME CONFIG (Adjust for Lore or Hardware Drift) ---
TIME_OFFSET_H = 0    # Hours
TIME_OFFSET_M = 0    # Minutes
LORE_YEAR_OFFSET = 0 # Reverted from Lore Offset (51) to Actual Year

from datetime import timedelta
def get_adjusted_time():
    """Returns the current time with configured offsets applied"""
    now = datetime.now()
    # Apply time offsets
    adjusted = now + timedelta(hours=TIME_OFFSET_H, minutes=TIME_OFFSET_M)
    return adjusted

# FARBEN
GREEN      = (55, 200, 55)
GREEN_SOFT = (55, 200, 55, 100)
DIM_GREEN  = (10, 40, 10, 150)
BLUE       = (0, 190, 255)
DIM_BLUE   = (0, 50, 100)
RED        = (255, 50, 50)
WARN       = (255, 180, 60)
WARNING    = WARN # Alias for backward compatibility and lint fix
ORANGE     = (255, 150, 50)
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GRAY       = (100, 100, 100)

# PFADE
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
BG_PATH   = os.path.join(ASSET_DIR, "bg.png")
FONT_PATH = os.path.join(ASSET_DIR, "Monofonto.ttf")
TXT_PATH  = os.path.join(ASSET_DIR, "emotions.txt")
ART_PATH  = os.path.join(ASSET_DIR, "art.txt") 

# DEBUG OUTPUT
print("--- STARTE CRITL OS V2.1 ---")
print(f"Checke Asset-Ordner: {ASSET_DIR}")

CRITL_PATHS = {
    1: os.path.join(ASSET_DIR, "1.png"), 
    2: os.path.join(ASSET_DIR, "2.png"),
    3: os.path.join(ASSET_DIR, "3.png"), 
    4: os.path.join(ASSET_DIR, "4.png"),
    5: os.path.join(ASSET_DIR, "3.png"), # Fallback: Angry -> Grumpy
    6: os.path.join(ASSET_DIR, "4.png"), # Fallback: Snacking -> Happy
    7: os.path.join(ASSET_DIR, "3.png"), # Fallback: Panic -> Grumpy
    8: os.path.join(ASSET_DIR, "4.png")  # Fallback: Elite -> Happy
}

# ============================================================
# STUNDENPLAN
# ============================================================
PLAN_RAW = [
    ("07:30","08:00","VORBEREITUNG"), ("08:00","08:45","UNTERRICHT"), ("08:45","08:50","PAUSE"),
    ("08:50","09:35","UNTERRICHT"), ("09:35","09:55","PAUSE"), ("09:55","10:40","UNTERRICHT"),
    ("10:40","10:45","PAUSE"), ("10:45","11:30","UNTERRICHT"), ("11:30","11:50","PAUSE"),
    ("11:50","12:35","UNTERRICHT"), ("12:35","12:40","PAUSE"), ("12:40","13:25","UNTERRICHT"),
    ("13:25","13:35","PAUSE"), ("13:35","14:20","UNTERRICHT"), ("14:20","14:25","PAUSE"),
    ("14:25","15:10","UNTERRICHT"), ("15:10","15:15","PAUSE"), ("15:15","16:00","UNTERRICHT")
]

def number_lessons(plan):
    n=1; out=[]
    for a,b,l in plan:
        if l=="UNTERRICHT": l=f"{n}."; n+=1
        out.append((a,b,l))
    return out
PLAN = number_lessons(PLAN_RAW)

def to_sec(t):
    h,m = map(int,t.split(":")); return h*3600+m*60

def get_status(now):
    cur = now.hour*3600+now.minute*60+now.second
    for a,b,l in PLAN:
        s,e = to_sec(a),to_sec(b)
        if s<=cur<e: return l, e-cur, (cur-s)/(e-s), a, b
    return "FEIERABEND", 0, 1.0, "--:--", "--:--"

def fmt(sec):
    m,s = divmod(int(sec),60); return f"{m:02d}:{s:02d}"

def clamp(x,a,b): return a if x<a else b if x>b else x

def blend(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))

# ============================================================
# SYSTEM STATS & DATEI LOADER
# ============================================================
def get_pi_stats():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
    except: temp = 0.0
    try: load = os.getloadavg()[0]
    except: load = 0.5
    watts = 3.2 + (load * 1.5)
    return temp, watts

def load_quotes():
    data = {
        "neutral": ["System läuft.", "Alles stabil.", "Guck nicht so!"],
        "genervt": ["Nein Martin.", "Wartung? Später.", "Kein Wunderheiler."],
        "müde": ["Energie bei 2%.", "Pause? Jetzt?", "Simuliere Bereitschaft."],
        "arbeit": ["Scan läuft...", "Langeweile erkannt.", "Effizienz? Nö."]
    }
    if os.path.exists(TXT_PATH):
        try:
            file_data = {"neutral":[], "genervt":[], "müde":[], "arbeit":[]}
            with open(TXT_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        cat, txt = line.split(":", 1)
                        cat = cat.strip().lower()
                        txt = txt.strip()
                        if cat in file_data and txt:
                            file_data[cat].append(txt)
            for k in file_data:
                if file_data[k]:
                    data[k] = file_data[k]
        except: pass
    return data

def load_faces():
    faces = ["NO FILE", "CHECK", "ASSETS"]
    if os.path.exists(ART_PATH):
        try:
            with open(ART_PATH, "r", encoding="utf-8") as f:
                loaded = [line.strip() for line in f if line.strip()]
            if loaded:
                print(f"OK: {len(loaded)} ASCII-Arts geladen.")
                faces = loaded
            else:
                faces = ["FILE", "EMPTY"]
        except Exception as e:
            print(f"Error reading art.txt: {e}")
    else:
        print("WARNUNG: art.txt fehlt!")
    return faces

# ============================================================
# TEXTE & EVENTS CONFIG
# ============================================================
CRITL_QUOTES = load_quotes()
CRITL_FACES = load_faces() 

EVENTS = [
    {"type":"rads",     "min":25, "max":45},
    {"type":"critical", "min":30, "max":45},
    {"type":"vats",     "min":20, "max":40},
    {"type":"error",    "min":20, "max":35},
    {"type":"chem",     "min":20, "max":35},
    {"type":"vision",   "min":25, "max":45},
    {"type":"censored", "min":20, "max":45},
    {"type":"emote",    "min":10, "max":15},
    {"type":"glitch_blue", "min":3, "max":5},
    {"type":"glitch_green","min":3, "max":5},
    {"type":"glitch_blue", "min":3, "max":5}, 
    {"type":"glitch_green","min":3, "max":5},
    {"type":"matrix",   "min":15, "max":30},
    {"type":"sonar",    "min":15, "max":30},
    {"type":"bioscan",  "min":15, "max":30},
    {"type":"hacking",  "min":999, "max":999},
    {"type":"doge",     "min":10, "max":20},
    {"type":"success_kid","min":10, "max":20},
    {"type":"this_is_fine","min":10, "max":20},
    {"type":"grumpy_cat",  "min":10, "max":20},
    {"type":"surprised_pikachu","min":10, "max":20},
    {"type":"pain_harold", "min":10, "max":20}
]

# Command-Line Arguments checken
DEBUG_MODE = "--debug" in sys.argv or "--windowed" in sys.argv

pygame.init()

# Mit pygame.FULLSCREEN | pygame.NOFRAME wird es wieder echtes Vollbild ohne Ränder
display_flags = pygame.FULLSCREEN | pygame.NOFRAME
if DEBUG_MODE:
    display_flags = 0 # Normales Fenster für Debugging
    print("DEBUG MODE AKTIV: Starte im Fenstermodus.")

screen = pygame.display.set_mode((W,H), display_flags)

# Hier entscheidest du über den Mauszeiger:
# True  = Mauszeiger ist sichtbar (gut für Touch/Bedienung)
# False = Mauszeiger ist unsichtbar (besserer Retro-Look)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

def load_font(size):
    try: return pygame.font.Font(FONT_PATH,size)
    except: return pygame.font.SysFont("monospace",size)

font_time, font_large, font_body, font_small, font_v_small = load_font(75), load_font(48), load_font(32), load_font(24), load_font(18)

# ROBUSTER FONT LOADER
font_smilie = None
possible_fonts = ["dejavu sans", "noto sans", "arial", "segoe ui", "symbola", "freesans"]
for f_name in possible_fonts:
    try:
        f = pygame.font.SysFont(f_name, 32, bold=True)
        if f: 
            font_smilie = f
            break
    except: continue

if not font_smilie:
    font_smilie = pygame.font.SysFont(None, 35, bold=True)

try: bg = pygame.transform.scale(pygame.image.load(BG_PATH),(W,H))
except: 
    # Procedural Pip-Boy Background Fallback
    bg = pygame.Surface((W,H))
    bg.fill((5, 15, 5)) # Very dark green
    # Subtle Scanlines
    for y in range(0, H, 2):
        pygame.draw.line(bg, (0, 10, 0), (0, y), (W, y))
    # Glowing Corner Accents
    pygame.draw.rect(bg, (20, 60, 20), (0,0,W,H), 8) # Outer border
    pygame.draw.line(bg, GREEN, (20, 20), (100, 20), 2) # Top Left
    pygame.draw.line(bg, GREEN, (20, 20), (20, 100), 2)
    pygame.draw.line(bg, GREEN, (W-100, 20), (W-20, 20), 2) # Top Right
    pygame.draw.line(bg, GREEN, (W-20, 20), (W-20, 100), 2)

critl_imgs={}
for k,p in CRITL_PATHS.items():
    try: critl_imgs[k]=pygame.transform.smoothscale(pygame.image.load(p).convert_alpha(),(350,350))
    except: critl_imgs[k]=None

STORY_ASSETS = {}
SCALED_CACHE = {} # Cache for smoothscaled images: {(asset_name, w, h): surface}
def get_story_asset(asset_name):
    if not asset_name: return None
    if asset_name in STORY_ASSETS: return STORY_ASSETS[asset_name]
    
    # Try multiple paths
    paths = [
        os.path.join("assets", "stories", f"{asset_name}.png"),
        os.path.join("assets", "stories", asset_name),
        os.path.join("assets", f"{asset_name}.png")
    ]
    
    for p in paths:
        if os.path.exists(p):
            try:
                img = pygame.image.load(p).convert_alpha()
                # Determine scale: Story images are often larger/backgrounds
                # But for now we stick to a consistent size for character overrides
                # or scale to fill a significant area
                scaled = pygame.transform.smoothscale(img, (350, 350))
                STORY_ASSETS[asset_name] = scaled
                return scaled
            except: continue
    return None

# INIT HACKING GAME
hacking_game = HackingGame(screen, font_body, font_small)
critl = CRITLPersonality()

# INIT UPDATE SYSTEM
updater = UpdateSystem()
boot_screen = BootScreen(screen, W, H)
update_screen = UpdateScreen(screen, W, H)

# ============================================================
# ZEICHEN-HELFER
# ============================================================
def draw_text_wrapped(text, x, y, font, color, max_w=580):
    words = text.split(' '); lines = []; cur_l = ""
    for w_ in words:
        if font.size(cur_l + w_)[0] < max_w: cur_l += w_ + " "
        else: lines.append(cur_l); cur_l = w_ + " "
    lines.append(cur_l)
    for i, l in enumerate(lines):
        screen.blit(font.render(l.strip(), True, color), (x, y + i * (font.get_height() + 2)))

def draw_bar(x, y, w, h, prog, is_pause, remain, label, t_start, t_end):
    pygame.draw.rect(screen, DIM_GREEN, (x, y, w, h))
    pygame.draw.rect(screen, GREEN, (x, y, w, h), 5) # Thicker border
    col = BLUE if is_pause else (blend(GREEN, WARN, 1-remain/120) if remain <= 120 else GREEN)
    fill_w = int((w - 10) * prog)
    if fill_w > 0: pygame.draw.rect(screen, col, (x + 5, y + 5, fill_w, h - 10))
    full_text = f"{t_start}-{t_end} | {label}"
    if remain > 0: full_text += f" | NOCH {fmt(remain)}"
    
    # Use larger font if it fits, else body font
    s_light_large = font_large.render(full_text, True, GREEN_SOFT)
    if s_light_large.get_width() < w - 20:
        s_light = s_light_large
        s_dark = font_large.render(full_text, True, BLACK)
    else:
        s_light = font_body.render(full_text, True, GREEN_SOFT)
        s_dark  = font_body.render(full_text, True, BLACK)
        
    tx = x + (w - s_light.get_width()) // 2
    ty = y + (h - s_light.get_height()) // 2 + 3 # Improved vertical shift for visual center
    screen.set_clip(pygame.Rect(x+5, y+5, fill_w, h-10))
    screen.blit(s_dark, (tx, ty))
    screen.set_clip(pygame.Rect(x+5+fill_w, y+5, w-10-fill_w, h-10))
    screen.blit(s_light, (tx, ty))
    screen.set_clip(None)

def draw_speech_bubble(text, source_pos):
    if not text: return
    style = getattr(critl, 'speech_style', 'default')
    
    # Larger width for narrative
    max_w = 400 if style == "event" else 200
    pad = 15
    
    # Wrap text
    words = text.split(' ')
    lines = []
    current_line = ""
    target_font = font_body if style == "event" else font_v_small
    
    for w in words:
        test_line = current_line + w + " "
        if target_font.size(test_line)[0] < max_w:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = w + " "
    lines.append(current_line)
    
    # Calculate bubble size
    tw = max(target_font.size(l)[0] for l in lines)
    th = len(lines) * (target_font.get_height() + 2)
    bw, bh = tw + pad*2, th + pad*2
    
    # Position: Default (above CRITL) or Narrative (Centered Bottom)
    if style == "event":
        bx = W // 2 - bw // 2
        by = H - bh - 160 # Above needs footer
    else:
        bx = source_pos[0] - bw - 10
        by = source_pos[1] - bh // 2
    
    # Draw bubble box
    pygame.draw.rect(screen, BLACK, (bx, by, bw, bh))
    pygame.draw.rect(screen, GREEN, (bx, by, bw, bh), 2)
    
    # Draw text
    for i, line in enumerate(lines):
        txt_surf = target_font.render(line.strip(), True, GREEN)
        screen.blit(txt_surf, (bx + pad, by + pad + i * (target_font.get_height() + 2)))
    
    # Sink tail deleted for narrative look
    if style == "default":
        pygame.draw.polygon(screen, GREEN, [(bx+bw, by+bh//2-5), (bx+bw+10, by+bh//2), (bx+bw, by+bh//2+5)])

def draw_edge_scan(t):
    lw, lx = 60, int((t * 100) % W)
    cv = int(math.sin(t * 2) * 127 + 128); col = (0, 255, cv)
    y_pos = H - 5 # Moved further down
    if lx + lw > W:
        pygame.draw.line(screen, col, (lx, y_pos), (W, y_pos), 1)
        pygame.draw.line(screen, col, (0, y_pos), (lw - (W - lx), y_pos), 1)
    else: pygame.draw.line(screen, col, (lx, y_pos), (lx + lw, y_pos), 1)

def tint(color, alpha):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((color[0], color[1], color[2], alpha))
    screen.blit(s, (0, 0))


def draw_status_icons(t):
    start_x, y, r, g, b = W - 110, 20, 80, 255, 80
    w_v = int(100 + 100 * math.sin(t * 0.8))
    s_w = pygame.Surface((34,34), pygame.SRCALPHA)
    for i in range(3): pygame.draw.arc(s_w, (r, g, b, w_v), (5+i*4, 8+i*4, 24-i*8, 24-i*8), math.pi/4, 3*math.pi/4, 2)
    screen.blit(s_w, (start_x, y))
    r_v = int(100 + 100 * math.sin(t * 0.5))
    s_r = pygame.Surface((34,34), pygame.SRCALPHA); c=(17,17)
    pygame.draw.circle(s_r, (r, g, b, r_v), c, 4)
    for i in range(3):
        ang = i * (2 * math.pi / 3) - (math.pi / 2)
        p1 = (c[0] + 14 * math.cos(ang - 0.5), c[1] + 14 * math.sin(ang - 0.5))
        p2 = (c[0] + 14 * math.cos(ang + 0.5), c[1] + 14 * math.sin(ang + 0.5))
        pygame.draw.polygon(s_r, (r, g, b, r_v), [c, p1, p2])
    screen.blit(s_r, (start_x + 35, y))
    bc = (200, 255, 200, 255) if random.random() > 0.98 else (r//2, g//2, b//2, 100)
    s_b = pygame.Surface((34,34), pygame.SRCALPHA)
    pts = [(17, 4), (24, 16), (17, 16), (20, 30), (10, 16), (17, 16)]
    pygame.draw.polygon(s_b, bc, pts)
    screen.blit(s_b, (start_x + 70, y))
    
    # SYSTEM ICON removed
    return None

def draw_icon(icon_type, x, y):
    s = pygame.Surface((30, 30), pygame.SRCALPHA)
    if icon_type == "hacking":
        # Terminal prompt >_
        pygame.draw.line(s, GREEN, (5, 5), (15, 15), 3)
        pygame.draw.line(s, GREEN, (5, 25), (15, 15), 3)
        if (time.time() * 2) % 2 > 1: # Blinking cursor
            pygame.draw.line(s, GREEN, (18, 25), (28, 25), 3)
    elif icon_type == "lore":
        # Document/Book icon
        pygame.draw.rect(s, GREEN, (5, 5, 20, 24), 2)
        pygame.draw.line(s, GREEN, (9, 10), (21, 10), 1)
        pygame.draw.line(s, GREEN, (9, 15), (21, 15), 1)
        pygame.draw.line(s, GREEN, (9, 20), (17, 20), 1)
    elif icon_type == "bonding":
        # Linked circles/Heart vibe
        pygame.draw.circle(s, GREEN, (10, 15), 8, 2)
        pygame.draw.circle(s, GREEN, (20, 15), 8, 2)
    elif icon_type == "inventory":
        # Floppy disk icon
        pygame.draw.rect(s, GREEN, (4, 4, 22, 22), 2)
        pygame.draw.rect(s, GREEN, (8, 4, 14, 8), 1) # Label
        pygame.draw.rect(s, GREEN, (10, 18, 10, 8), 1) # Shutter
    screen.blit(s, (x, y))

# draw_rpg_overlay removed
# draw_choice_ui eliminated

# ============================================================
# BOOT SEQUENCE
# ============================================================
def run_boot_sequence():
    """Run boot sequence on startup with automatic update check"""
    # 1. Check for updates (Forced check on every boot)
    print("Update Check: Prüfe auf neue Versionen...")
    update_info = updater.check_for_updates(force=True)
    
    # 2. If update available, run update process
    if update_info:
        print(f"Update gefunden: {update_info.get('version')}")
        # Run the update UI (Download + Install)
        if update_screen.run_full_update(update_info):
            print("Update erfolgreich. Starte System neu...")
            # Restart the script
            pygame.quit()
            os.execv(sys.executable, [sys.executable] + sys.argv)
            sys.exit()
    
    # 3. Regular boot screen
    if not boot_screen.run_boot_sequence(update_info):
        return False
    
    return True

# ============================================================
# MAIN LOOP
# ============================================================
if __name__ == "__main__":
    # Run boot sequence
    print("Starting boot sequence...")
    if not run_boot_sequence():
        print("Boot interrupted")
        pygame.quit()
        sys.exit()
    
    # Clear event queue to avoid "ghost" inputs from the boot wait
    pygame.event.clear()
    
    # active_event, ev_start, ev_dur = None, 0, 0 # These are now global
    next_event = time.time() + 120
    last_update_check = time.time() 

    active_quote, q_until, next_quote = "", 0, time.time()+20
    active_face, last_face_change = "INIT", 0 

    # State for complex effects
    matrix_drops = []
    sonar_blips = []
    need_flashes = {} # {action: expiry_time}
    critl_flash = 0   # expiry_time

    while True:
        t_now = time.time()
        
        # ----------------------------------------------------
        # SCHLAFMODUS (ABENDS & WOCHENENDE)
        # ----------------------------------------------------
        now = get_adjusted_time()
        ist_wochenende = now.weekday() >= 5  # 5 = Samstag, 6 = Sonntag
        # Erst ab 18:00, damit Leute noch nachmittags ungestört arbeiten können
        ist_feierabend = now.hour >= 18 or now.hour < 7
        
        # DETERMINE MOOD & IMG EARLY FOR EVENTS
        mood = "neutral"
        if active_event and "min" in active_event and 25 <= active_event["min"] <= 45: mood = "traurig" # Rads/Vision roughly
        elif active_event and active_event["type"] == "critical": mood = "wuetend"
        elif active_event and active_event.get("type") == "emote": mood = "gluecklich"
        # Fallback/Default Mood logic from bottom of loop could be complex, 
        # but for visual effects we just need A image.
        
        # Let's grab the standard image based on basic state
        # We can refine this, but for now let's just use the current face logic helper
        # actually, the original logic was:
        # if active_event: set mood based on event
        # else: set mood based on time/sentence
        # We can just initialize img = None and handle it safely
        
        img = None
        # Pre-fetch image for effects
        # Simpler: Just resolve mood image here if possible, or use a default one for effects
        base_img = critl_imgs.get(1) # Neutral as default
    
        # SCHLAFMODUS - Optimiert für niedrigen Stromverbrauch
        if ist_wochenende or ist_feierabend:
            screen.fill(BLACK)
            
            # Deutlichere Animation, damit der Screen nicht schwarz wirkt (Bug-Fix)
            pulse = (math.sin(t_now * 2.0) + 1) / 2  # Flotteres Pulsieren
            dim_val = int(80 + 120 * pulse)          # Viel heller (80 bis 200)
            sleep_color = (0, dim_val, 0)
            
            # Zentrierter "Zzz..." Text
            zzz_text = "Zzzzz..."
            zzz_surf = font_time.render(zzz_text, True, sleep_color)
            zzz_x = (W - zzz_surf.get_width()) // 2
            zzz_y = (H - zzz_surf.get_height()) // 2 - 40
            screen.blit(zzz_surf, (zzz_x, zzz_y))
            
            # Status Info
            status_grund = "WOCHENENDE" if ist_wochenende else "FEIERABEND"
            display_year = now.year + LORE_YEAR_OFFSET
            status_text = f"SLEEP MODE | {status_grund} | {now.strftime('%d.%m.')}{display_year} {now.strftime('%H:%M')}"
            status_surf = font_small.render(status_text, True, sleep_color)
            screen.blit(status_surf, ((W - status_surf.get_width()) // 2, zzz_y + 80))
            
            # Minimaler Rahmen
            pygame.draw.rect(screen, sleep_color, (20, 20, W-40, H-40), 2)
            
            pygame.display.flip()
            time.sleep(0.1)  # Nur 0.1s Pause, damit das Pulsieren flüssig ist und Events reagieren
            
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_q): 
                    pygame.quit()
                    sys.exit()
            continue
            
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                critl.save_memory()
                pygame.quit()
                sys.exit()
            
            if e.type == pygame.KEYDOWN:
                # --- DEBUG MODE: TRIGGER EVENTS ---
                debug_map = {
                    pygame.K_F1: "rads", pygame.K_F2: "critical", pygame.K_F3: "vats",
                    pygame.K_F4: "error", pygame.K_F5: "chem", pygame.K_F6: "vision",
                    pygame.K_F7: "censored", pygame.K_F8: "emote", pygame.K_F9: "this_is_fine",
                    pygame.K_F10: "grumpy_cat", pygame.K_F11: "surprised_pikachu", pygame.K_F12: "pain_harold"
                }
                if e.key in debug_map:
                    ev_type = debug_map[e.key]
                    active_event = next((ev for ev in EVENTS if ev["type"] == ev_type), {"type": ev_type, "min": 10, "max": 20})
                    ev_start = time.time()
                    ev_dur = active_event.get("max", 15)
                    # critl.trigger_event_speech(ev_type)
                    print(f"DEBUG: Triggered event {ev_type}")
                
                if e.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
    
                if active_event and active_event["type"] == "hacking":
                     res = hacking_game.handle_click((mx, my))
                     if res == "EXIT":
                          active_event = None
    
        label, remain, prog, t_s, t_e = get_status(now)
        is_p = "PAUSE" in label or "VORBEREITUNG" in label
        
        screen.blit(bg, (0, 0))
        
        # UPDATE CRITL
        temp_pi, _ = get_pi_stats()
        critl.update(t_now, temp_pi, is_p, active_event)
        
        # Poll Success Trigger
        if critl.success_trigger:
            success_flash_time = time.time() + 2.0
            critl.success_trigger = False
            print("RAINBOW FLASH TRIGGERED!")
    
        if active_event:
            # Default duration if for some reason it slipped through
            if 'ev_dur' not in locals() or ev_dur <= 0: ev_dur = 1
            p_ev = clamp((t_now - ev_start) / ev_dur, 0, 1)
            et = active_event["type"]
    
            if et == "hacking":
                 hacking_game.draw(pygame.mouse.get_pos())
    
            elif et == "glitch_blue":
                tint((0, 50, 100), 40)
                sy = int(p_ev * H)
                pygame.draw.line(screen, (100, 200, 255), (0, sy), (W, sy), 3)
                pygame.draw.line(screen, (100, 200, 255), (0, sy-2), (W, sy-2), 1)
            
            elif et in ["doge", "success_kid", "this_is_fine", "grumpy_cat", "surprised_pikachu", "pain_harold"]:
                # --- MEME EVENT DISPLAY ---
                img = get_story_asset(et)
                if img:
                    # Subtle Zoom/Bounce Effect
                    scale_pulse = 1.0 + 0.05 * math.sin(t_now * 5)
                    sw, sh = int(350 * scale_pulse), int(350 * scale_pulse)
                    
                    # Use a cache to avoid smoothscale every frame (important for Pi)
                    # We round to nearest 5 pixels to improve cache hits while keeping animation smooth
                    c_sw, c_sh = (sw // 5) * 5, (sh // 5) * 5
                    cache_key = (et, c_sw, c_sh)
                    if cache_key not in SCALED_CACHE:
                        # Limit cache size
                        if len(SCALED_CACHE) > 50: SCALED_CACHE.clear()
                        SCALED_CACHE[cache_key] = pygame.transform.smoothscale(img, (c_sw, c_sh))
                    
                    img_scaled = SCALED_CACHE[cache_key]
                    screen.blit(img_scaled, (W//2 - c_sw//2, H//2 - c_sh//2))
                
                # Special Flair for "This is Fine"
                if et == "this_is_fine":
                    tint((255, 100, 0), int(30 + 30 * math.sin(t_now * 8)))
                    # Reduced fire sparks for performance
                    for _ in range(12):
                        rx, ry = random.randint(0, W), random.randint(0, H)
                        pygame.draw.circle(screen, (255, random.randint(150, 255), 0), (rx, ry), random.randint(1, 3))
                        if random.random() > 0.95:
                            pygame.draw.line(screen, (255, 200, 50), (rx, ry), (rx, ry - random.randint(10, 30)), 1)
            elif et == "glitch_green":
                for _ in range(600):
                    screen.set_at((random.randrange(W), random.randrange(H)), (100, 255, 100))
    
            elif et == "rads":
                # RADIATION SYMBOL ANIMATION
                tint((40, 40, 0), 100) # Yellowish tint
                
                cx, cy = W//2, H//2
                angle = t_now * 45 % 360
                pulse = (math.sin(t_now * 8) + 1) / 2 # 0 to 1
                
                # Base Circle
                color_base = (200, 180, 0)
                color_sym = (0, 0, 0)
                
                # Draw Symbol Background (Yellow Circle)
                pygame.draw.circle(screen, color_base, (cx, cy), 120)
                pygame.draw.circle(screen, color_sym, (cx, cy), 20) # Center dot
                
                # Draw 3 Blades
                for i in range(3):
                    start_ang = angle + i * 120
                    # Large arc requires rect
                    # This is tricky in pure pygame primitives, let's allow lines
                    # Simple approximation: Polygon triangles rotating?
                    
                    # Better: Use Arc?
                    rect = pygame.Rect(cx-110, cy-110, 220, 220)
                    pygame.draw.arc(screen, color_sym, rect, math.radians(start_ang), math.radians(start_ang + 60), 110)
                    # Fill is hard with arc, let's just use thick lines or sector polygon if needed
                    # For retro look, just thick arcs are okay or lines
                    
                    # Let's try polygon sectors for "filled" look
                    pts = [(cx, cy)]
                    for a in range(int(start_ang), int(start_ang + 60 + 1), 10):
                       rad = math.radians(a)
                       pts.append((cx + 110 * math.cos(rad), cy + 110 * math.sin(rad)))
                    pygame.draw.polygon(screen, color_sym, pts)
    
    
                # Flashing Warning
                if pulse > 0.5:
                    warn_box = pygame.Rect(cx - 150, cy + 140, 300, 50)
                    pygame.draw.rect(screen, RED, warn_box)
                    pygame.draw.rect(screen, (100, 0, 0), warn_box, 3)
                    
                    txt = font_body.render("HIGH RADIATION", True, BLACK)
                    screen.blit(txt, (cx - txt.get_width()//2, cy + 150))
                
                # Sound viz (Geiger Ticks visual)
                for i in range(10):
                    rx = random.randint(20, W-20)
                    ry = random.randint(20, H-20)
                    pygame.draw.line(screen, GREEN, (rx, ry), (rx+5, ry+5), 1)
    
            elif et == "critical":
                tint(RED, 60) # Red tint
                shake = int(4 + 10 * p_ev)
                ox, oy = random.randint(-shake, shake), random.randint(-shake, shake)
                
                # Copy screen to create shake/blur
                screen.blit(screen.copy(), (ox, oy))
                
                # Critical Hit Text
                cx, cy = W//2, H//2
                
                # Flash
                if int(t_now * 10) % 2 == 0:
                    pygame.draw.rect(screen, RED, (cx - 200, cy - 40, 400, 80))
                    msg = font_time.render("CRITICAL HIT!", True, WHITE) # Large font
                    screen.blit(msg, (cx - msg.get_width()//2, cy - 40))
                else:
                     msg = font_time.render("CRITICAL HIT!", True, RED)
                     screen.blit(msg, (cx - msg.get_width()//2, cy - 40))
    
            elif et == "vats":
                # IMPROVED VATS
                tint((0, 20, 0), 100)
                
                # Scanlines for VATS usually go horizontal
                for y in range(0, H, 4):
                    pygame.draw.line(screen, (0, 50, 0), (0, y), (W, y))
    
                cx, cy = W//2, H//2
                
                # Target Reticle
                pygame.draw.circle(screen, GREEN, (cx, cy), 150, 2)
                pygame.draw.line(screen, GREEN, (cx-160, cy), (cx-50, cy), 2)
                pygame.draw.line(screen, GREEN, (cx+50, cy), (cx+160, cy), 2)
                pygame.draw.line(screen, GREEN, (cx, cy-160), (cx, cy-50), 2)
                pygame.draw.line(screen, GREEN, (cx, cy+50), (cx, cy+160), 2)
                
                parts = ["HEAD", "TORSO", "L.ARM", "R.ARM", "R.LEG", "L.LEG"]
                active_idx = int(t_now * 1.5) % len(parts)
                active_part = parts[active_idx]
                
                # Draw Box for Part Stats
                box_x, box_y = W - 220, H - 250
                pygame.draw.rect(screen, DIM_GREEN, (box_x, box_y, 200, 200))
                pygame.draw.rect(screen, GREEN, (box_x, box_y, 200, 200), 2)
                
                hit_chance = 95 - (active_idx * 12) + int(math.sin(t_now)*5)
                if hit_chance > 95: hit_chance = 95
                
                screen.blit(font_body.render(f"{active_part}", True, GREEN_SOFT), (box_x + 10, box_y + 10))
                screen.blit(font_large.render(f"{hit_chance}%", True, GREEN), (box_x + 10, box_y + 50))
                
                # Sound bar visualization
                for i in range(10):
                    h_ = random.randint(5, 40)
                    pygame.draw.rect(screen, GREEN, (box_x + 10 + i*15, box_y + 120, 10, h_))
    
            elif et == "error":
                # FATAL TERMINAL ERROR
                screen.fill((0, 0, 120)) # Blue Screen of functionality
                
                # RobCo header
                pygame.draw.rect(screen, WHITE, (50, 50, W-100, 40))
                screen.blit(font_body.render("ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM", True, (0,0,120)), (60, 55))
                
                # Error Box
                pygame.draw.rect(screen, WHITE, (W//2 - 200, H//2 - 100, 400, 200), 2)
                screen.blit(font_large.render("SYSTEM FAILURE", True, WHITE), (W//2 - 180, H//2 - 80))
                
                # Hex Dump
                start_y = H//2 - 20
                for i in range(5):
                     hex_str = f"0x{random.randint(0, 65535):04X}  " + " ".join([f"{random.randint(0,255):02X}" for _ in range(8)])
                     screen.blit(font_small.render(hex_str, True, WHITE), (W//2 - 190, start_y + i * 25))
    
                screen.blit(font_v_small.render("Press ANY KEY to reboot...", True, WHITE), (W//2 - 100, H//2 + 150))
    
            elif et == "chem":
                r = int(127+127*math.sin(t_now*4))
                g = int(127+127*math.sin(t_now*4+2))
                b = int(127+127*math.sin(t_now*4+4))
                tint((r, g, b), 80)
                off_x = int(math.sin(t_now * 5) * 10)
                off_y = int(math.cos(t_now * 5) * 10)
                off_y = int(math.cos(t_now * 5) * 10)
                if base_img: 
                    pass # Ghost images hidden during events
    
            elif et == "vision":
                vp = int(130 + 30 * math.sin(t_now * 1.5))
                tint((100, 255, 100), vp)
                for i in range(3):
                    sy = int((t_now * [150, 250, 400][i] + i * 100) % H)
                    s_l = pygame.Surface((W, 3), pygame.SRCALPHA); s_l.fill((255, 255, 255, 60))
                    screen.blit(s_l, (0, sy))
                screen.blit(pygame.transform.flip(s_l, False, True), (0, sy-50))
                pygame.draw.circle(screen, BLACK, (W//2, H//2), 350, 100) 
                cx, cy = W//2, H//2
                pygame.draw.line(screen, GREEN_SOFT, (cx-40, cy), (cx+40, cy), 1)
                pygame.draw.line(screen, GREEN_SOFT, (cx, cy-40), (cx, cy+40), 1)
                dist = int(140 + math.sin(t_now)*10)
                screen.blit(font_v_small.render(f"DIST: {dist}m", True, GREEN), (cx+50, cy+50))
                for i in range(0, W, 50):
                    off = (i + int(t_now * 50)) % W
                    pygame.draw.line(screen, GREEN_SOFT, (off, 0), (off, 15), 2)
                    if i % 100 == 0: screen.blit(font_v_small.render(f"{i}", True, GREEN_SOFT), (off-10, 20))
                batt_w = int(50 - (p_ev * 50))
                pygame.draw.rect(screen, GREEN, (W-70, 20, 50, 15), 1)
                pygame.draw.rect(screen, GREEN, (W-70+1, 21, batt_w, 13))
                screen.blit(font_v_small.render("BATT", True, GREEN), (W-70, 5))
    
            elif et == "censored":
                for y in range(0, H, 20):
                    line = "CONFIDENTIAL " * 10
                    off_x = int(t_now * 20) % 100
                    col = (30, 10, 0)
                    screen.blit(font_v_small.render(line, True, col), (-off_x, y))
                tint(BLACK, 150)
                lx, ly = W//2 - 25, H//2 - 120
                pygame.draw.rect(screen, RED, (lx, ly+40, 50, 40)) 
                pygame.draw.arc(screen, RED, (lx, ly, 50, 50), 0, math.pi, 3) 
                if int(t_now * 4) % 2 == 0:
                    box_rect = (W//2 - 200, H//2 - 60, 400, 160)
                    pygame.draw.rect(screen, BLACK, box_rect)
                    pygame.draw.rect(screen, RED, box_rect, 5)
                    txt1 = font_body.render("ACCESS DENIED", True, RED)
                    txt2 = font_small.render("SECURITY CLEARANCE REQUIRED", True, RED)
                    screen.blit(txt1, (W//2 - txt1.get_width()//2, H//2 - 20))
                    screen.blit(txt2, (W//2 - txt2.get_width()//2, H//2 + 30))
    
            elif et == "matrix":
                # Init drops if needed
                if not matrix_drops:
                    for x in range(0, W, 15):
                        matrix_drops.append({'x': x, 'y': random.randint(-H, 0), 'speed': random.randint(5, 15), 'char': chr(random.randint(33, 126))})
                
                # Dark background
                s = pygame.Surface((W,H)); s.set_alpha(50); s.fill(BLACK)
                screen.blit(s, (0,0))
                
                # Draw and update drops
                for drop in matrix_drops:
                    # Trail
                    for i in range(5):
                        alpha = 255 - i * 50
                        char_render = font_small.render(drop['char'], True, (0, 255, 0))
                        char_render.set_alpha(alpha)
                        screen.blit(char_render, (drop['x'], drop['y'] - i * 15))
                    
                    drop['y'] += drop['speed']
                    if random.random() > 0.95: drop['char'] = chr(random.randint(33, 126))
                    if drop['y'] > H: 
                        drop['y'] = random.randint(-50, 0)
                        drop['speed'] = random.randint(5, 15)
    
            elif et == "sonar":
                tint((0, 20, 0), 30)
                cx, cy = W//2, H//2
                radius = min(W, H) // 2 - 20
                
                # Grid
                pygame.draw.circle(screen, (0, 100, 0), (cx, cy), radius, 2)
                pygame.draw.circle(screen, (0, 60, 0), (cx, cy), radius*2//3, 1)
                pygame.draw.circle(screen, (0, 60, 0), (cx, cy), radius//3, 1)
                pygame.draw.line(screen, (0, 60, 0), (cx, cy-radius), (cx, cy+radius), 1)
                pygame.draw.line(screen, (0, 60, 0), (cx-radius, cy), (cx+radius, cy), 1)
    
                # Sweep
                angle = (t_now * 2) % (2 * math.pi)
                ex = cx + math.cos(angle) * radius
                ey = cy + math.sin(angle) * radius
                pygame.draw.line(screen, (0, 255, 0), (cx, cy), (ex, ey), 3)
                
                # Blips
                if random.random() > 0.98:
                    dist = random.randint(50, radius)
                    a = random.random() * 2 * math.pi
                    sonar_blips.append({'x': cx + math.cos(a)*dist, 'y': cy + math.sin(a)*dist, 'life': 1.0})
                
                for blip in sonar_blips[:]:
                    blip['life'] -= 0.02
                    if blip['life'] <= 0: sonar_blips.remove(blip); continue
                    col = (0, int(255*blip['life']), 0)
                    pygame.draw.circle(screen, col, (int(blip['x']), int(blip['y'])), 5)
    
            elif et == "bioscan":
                tint((0, 0, 50), 50)
                scan_y = int((math.sin(t_now) + 1) / 2 * H)
                
                # Scan line
                pygame.draw.line(screen, (0, 255, 255), (0, scan_y), (W, scan_y), 5)
                s_grad = pygame.Surface((W, 50), pygame.SRCALPHA)
                for i in range(50):
                    pygame.draw.line(s_grad, (0, 255, 255, 100-i*2), (0, i), (W, i))
                screen.blit(s_grad, (0, scan_y))
                screen.blit(pygame.transform.flip(s_grad, False, True), (0, scan_y-50))
                
                # Data side
                pygame.draw.rect(screen, (0, 50, 100), (W-200, 100, 180, 300), 2)
                for i in range(10):
                    w_bar = int((math.sin(t_now*5 + i) + 1) * 80)
                    pygame.draw.rect(screen, (0, 200, 255), (W-190, 120 + i*25, w_bar, 15))
                
                screen.blit(font_small.render(f"POS: {scan_y}", True, (0, 255, 255)), (W-180, 80))
                if abs(scan_y - H//2) < 50:
                     screen.blit(font_body.render("SUBJECT DETECTED", True, WARNING), (W//2-100, H//2))
            
            elif et == "emote":
                # Heart/Sparkle particles around CRITL
                cx, cy = W - 185, 215 # Center of CRITL
                for i in range(10):
                    t_off = t_now * 2 + i * 0.5
                    px = cx + math.cos(t_off) * (40 + 20 * math.sin(t_now * 3))
                    py = cy + math.sin(t_off) * (40 + 20 * math.cos(t_now * 3))
                    size = int(5 + 3 * math.sin(t_now * 5 + i))
                    # Draw a small heart or diamond
                    pygame.draw.circle(screen, ORANGE, (int(px), int(py)), size)
                    pygame.draw.circle(screen, RED, (int(px), int(py)), size // 2)

            if t_now - ev_start >= ev_dur: 
                active_event = None
                matrix_drops = [] # Reset state
                sonar_blips = [] # Reset state
    
    
        else:
            # --- DASHBOARD ---
            # Drawing moved to the bottom unified section
            pass
            
            pi_temp, pi_watts = get_pi_stats()
            stat_text = font_v_small.render(f"TEMP: {pi_temp:.1f}C  PWR: {pi_watts:.1f}W", True, GREEN_SOFT)
            screen.blit(stat_text, (20, 10))
            screen.blit(font_time.render(now.strftime("%H:%M"), True, GREEN), (30, 45))
            
            draw_status_icons(t_now)
            wd = {"Monday":"MONTAG","Tuesday":"DIENSTAG","Wednesday":"MITTWOCH","Thursday":"DONNERSTAG","Friday":"FREITAG","Saturday":"SAMSTAG","Sunday":"SONNTAG"}
            display_year = now.year + LORE_YEAR_OFFSET
            screen.blit(font_body.render(f"{wd.get(now.strftime('%A'),'TAG')}, {now.strftime('%d.%m.')}{display_year}", True, GREEN_SOFT), (35, 120))
            
    
            # SMILIE AUS DATEI
            if t_now - last_face_change > 5:
                if CRITL_FACES:
                    active_face = random.choice(CRITL_FACES)
                else:
                    active_face = "NO FILE"
                last_face_change = t_now
            
            # Rendern
            screen.blit(font_smilie.render(active_face, True, (20, 100, 20)), (37, 182))
            screen.blit(font_smilie.render(active_face, True, GREEN), (35, 180))
            
            draw_bar(20, H-100, 600, 80, prog, is_p, remain, label, t_s, t_e)
            
            # Draw Controls (Left Side)
            # draw_games_button() removed
    
        draw_edge_scan(t_now)
        if not active_event and t_now > next_event:
            active_event = random.choice(EVENTS)
            ev_start, ev_dur = t_now, random.randint(active_event["min"], active_event["max"])
            next_event = t_now + random.randint(120, 300) 
            # TRIGGER EVENT SPEECH
            critl.trigger_event_speech(active_event["type"])
            
        if not active_event:
            # --- DRAW CRITL ---
            img_idx = critl.get_image_index(is_p)
            critl_img = critl_imgs.get(img_idx)
            
            # Story Image Override
            if critl.active_image_override:
                # Check if it's a numeric index (for mood overrides) or a string key (for story assets)
                try:
                    ov_idx = int(critl.active_image_override)
                    override_img = critl_imgs.get(ov_idx)
                except (ValueError, TypeError):
                    override_img = get_story_asset(critl.active_image_override)
                
                if override_img:
                    screen.blit(override_img, (W - 360, 40))
                else:
                    if critl_img: screen.blit(critl_img, (W - 360, 40))
            else:
                if critl_img:
                    screen.blit(critl_img, (W - 360, 40))
            
            # CRITL Flash Effect
            if t_now < critl_flash:
                s_flash = pygame.Surface((350, 350), pygame.SRCALPHA)
                s_flash.fill((255, 150, 0, 80)) # Light orange tint
                screen.blit(s_flash, (W - 360, 40), special_flags=pygame.BLEND_RGBA_ADD)


        
            # --- DRAW SPEECH ---
            speech = critl.get_current_speech()
            if speech:
                draw_speech_bubble(speech, (W - 300, 270))
            
        else:
            # --- TINT THE MONITOR DURING EVENTS ---
            et = active_event.get("type")
            if et == "critical" or et == "red_alert": tint(RED, 40)
            elif "glitch" in str(et): tint(BLUE, 30)
            elif et == "rads": tint((200, 200, 0), 40)
            elif et == "matrix": tint(GREEN, 20)
            else: tint(GREEN, 15)

        # draw_choice_ui() call removed
        
    
            
        # --- GLOBAL SCANLINES (Drawn over EVERYTHING for Fallout vibe) ---
        sl = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 3): # Thicker/more frequent scanlines
            pygame.draw.line(sl, (0, 20, 0, 50), (0, y), (W, y), 1)
        screen.blit(sl, (0,0))
    
        pygame.display.flip()
