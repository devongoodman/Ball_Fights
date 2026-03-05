import pygame
import random
import math
import sys
import subprocess
import os

pygame.init()

# ── Recording helpers ────────────────────────────────────────
FFMPEG_PATH = os.path.join(os.environ.get("LOCALAPPDATA", ""),
    "Microsoft", "WinGet", "Packages",
    "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe",
    "ffmpeg-8.0.1-full_build", "bin", "ffmpeg.exe")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


def get_record_filename():
    """Return next available Record.mp4, Record 1.mp4, Record 2.mp4, etc."""
    base = os.path.join(DOWNLOADS_DIR, "Record.mp4")
    if not os.path.exists(base):
        return base
    i = 1
    while True:
        path = os.path.join(DOWNLOADS_DIR, f"Record {i}.mp4")
        if not os.path.exists(path):
            return path
        i += 1


def start_recording(width, height, fps=30):
    """Start an FFmpeg subprocess that accepts raw RGBA frames via stdin.
    Returns the process, or None if FFmpeg not found."""
    if not os.path.exists(FFMPEG_PATH):
        return None
    out_path = get_record_filename()
    proc = subprocess.Popen([
        FFMPEG_PATH,
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "20",
        out_path
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc._record_path = out_path
    return proc


def record_frame(proc, surface):
    """Write one frame to the FFmpeg process."""
    if proc and proc.stdin:
        try:
            data = pygame.image.tobytes(surface, "RGB")
            proc.stdin.write(data)
        except (BrokenPipeError, OSError):
            pass


def stop_recording(proc):
    """Close the FFmpeg process and finalize the video."""
    if proc and proc.stdin:
        try:
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        proc.wait()

BASE_WIDTH, BASE_HEIGHT = 600, 450
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Fights")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
title_font = pygame.font.SysFont("Arial", 36)
big_font = pygame.font.SysFont("Arial", 48)
small_font = pygame.font.SysFont("Arial", 14)

BASE_BALL_RADIUS = 25
BALL_RADIUS = BASE_BALL_RADIUS
ZOMBIE_SPEED = 3.5
SWORDSMAN_SPEED = 3.0
SPEARMAN_SPEED = 2.8
TRAPPER_SPEED = 2.6
ZOMBIE_DAMAGE = 5
SWORD_DAMAGE = 10
SPEAR_DAMAGE = 5
TRAP_DAMAGE = 5
SWORD_LENGTH = BALL_RADIUS * 2
SWORD_SPIN_SPEED = 0.06
WALL_BOUNCE_FRAMES = 20
COLLISION_BOUNCE_FRAMES = 25
SPEAR_SPEED = 6.0
SPEAR_COOLDOWN = 120       # frames between spear throws
PIN_DURATION = 180          # 3 seconds at 60fps
TRAP_COOLDOWN = 240         # frames between trap placements
TRAP_RADIUS = BASE_BALL_RADIUS * 4
TRAP_BOUNCES = 5

BOMBER_SPEED = 2.5
BOMB_DAMAGE = 15
BOMB_TIMER = 120          # 2 seconds fuse
BOMB_COOLDOWN = 180
BOMB_KNOCKBACK = 18.0

HEALER_SPEED = 2.8
HEAL_AMOUNT = 2
HEAL_COOLDOWN = 30
HEAL_RANGE = 120

NINJA_SPEED = 4.5
NINJA_BACKSTAB_DAMAGE = 15
NINJA_INVIS_DURATION = 180    # 3 sec invisible
NINJA_INVIS_COOLDOWN = 180    # 3 sec before can go invis again

SHIELD_SPEED = 3.0
SHIELD_COUNT = 1
SHIELD_SPIN_SPEED = 0.05
SHIELD_ARC = 1.2              # radians per shield segment (wider for single shield)
SHIELD_DAMAGE = 5

SNIPER_SPEED = 2.0
SNIPER_BULLET_SPEED = 14.0
SNIPER_DAMAGE = 20
SNIPER_COOLDOWN = 150         # frames between shots

BERSERKER_SPEED = 3.0
BERSERKER_BASE_DAMAGE = 5

CHAINSAW_SPEED = 3.2
CHAINSAW_DAMAGE = 3            # per hit tick while touching
CHAINSAW_HIT_COOLDOWN = 5     # frames between damage ticks
CHAINSAW_LENGTH = BALL_RADIUS * 1.8
CHAINSAW_SPIN_SPEED = 0.12     # faster spin than sword

FORTIFIER_SPEED = 2.5
FORT_WALL_COOLDOWN = 180       # frames between wall placements
FORT_WALL_HP = 5               # hits before breaking
FORT_WALL_WIDTH = 60
FORT_WALL_THICKNESS = 8
FORT_EXPLODE_TIMER = 180       # 3 seconds at 60fps
FORT_EXPLODE_DAMAGE = 10
FORT_EXPLODE_RADIUS = BALL_RADIUS * 5

ARCHER_SPEED = 2.6
ARCHER_DAMAGE = 8
ARCHER_ARROW_SPEED = 10.0
ARCHER_COOLDOWN = 90           # faster than sniper (150) but not spammy

VAMPIRE_SPEED = 3.5
VAMPIRE_DAMAGE = 8
VAMPIRE_LIFESTEAL = 0.5        # heals 50% of damage dealt
VAMPIRE_HIT_COOLDOWN = 25

TANK_SPEED = 1.0
TANK_HP = 150                  # starts with 150 HP instead of 100
TANK_DAMAGE = 7
TANK_HIT_COOLDOWN = 15
TANK_ARMOR = 0.5               # takes 50% damage from all sources

WIZARD_SPEED = 2.4
WIZARD_DAMAGE = 6              # direct hit
WIZARD_SPLASH_DAMAGE = 4       # AoE splash to nearby enemies
WIZARD_SPLASH_RADIUS = BALL_RADIUS * 3
WIZARD_ORB_SPEED = 7.0
WIZARD_COOLDOWN = 110          # slower than archer, but AoE

ASSASSIN_SPEED = 3.0
ASSASSIN_DASH_SPEED = 8.0      # burst speed during dash
ASSASSIN_DAMAGE = 18            # big hit on dash strike
ASSASSIN_DASH_COOLDOWN = 180    # 3 seconds between dashes
ASSASSIN_DASH_DURATION = 15     # frames of dashing
ASSASSIN_RETREAT_SPEED = 6.0    # speed boost after hitting
ASSASSIN_RETREAT_DURATION = 20  # frames of retreating

NECRO_SPEED = 2.3
NECRO_RAISE_RANGE = BALL_RADIUS * 6   # must be near the corpse
NECRO_RAISE_COOLDOWN = 300            # 5 seconds between raises
NECRO_ZOMBIE_HP = 100                 # raised zombies have full HP

ICE_MAGE_SPEED = 2.5
ICE_MAGE_DAMAGE = 5
ICE_BOLT_SPEED = 8.0
ICE_MAGE_COOLDOWN = 80
ICE_SLOW_FACTOR = 0.4                # slowed enemies move at 40% speed
ICE_SLOW_DURATION = 120              # 2 seconds of slow

SUMMONER_SPEED = 2.3
SUMMONER_COOLDOWN = 600              # 10 seconds between summons
SUMMONER_MAX_MINIONS = 3             # max active minions
SUMMONER_MINION_HP = 15              # minions are weak
SUMMONER_MINION_RADIUS_SCALE = 0.5   # half size

MIRROR_SPEED = 2.8
MIRROR_DAMAGE = 4
MIRROR_HIT_COOLDOWN = 20

CHARGER_SPEED = 2.0            # slow normally
CHARGER_CHARGE_SPEED = 9.0     # very fast when charging
CHARGER_DAMAGE = 20            # big hit on charge impact
CHARGER_CHARGE_COOLDOWN = 200  # ~3.3 sec between charges
CHARGER_CHARGE_DURATION = 30   # frames of charging
CHARGER_WINDUP = 40            # frames of slowing down before charge

MIMIC_SPEED = 3.0
MIMIC_COPY_DURATION = 600      # 10 seconds before next copy

TEAM_COLORS = [
    (220, 60, 60),    # red
    (60, 120, 220),   # blue
    (60, 200, 80),    # green
    (220, 180, 40),   # yellow
    (180, 60, 220),   # purple
    (220, 130, 40),   # orange
]

ROLES = ["zombie", "swordsman", "spearman", "trapper", "bomber", "healer", "ninja", "shield", "sniper", "berserker", "chainsaw", "fortifier", "vampire", "archer", "wizard", "tank", "assassin", "necromancer", "ice_mage", "summoner", "mirror", "charger", "mimic"]

ROLE_SPEEDS = {
    "zombie": ZOMBIE_SPEED,
    "swordsman": SWORDSMAN_SPEED,
    "spearman": SPEARMAN_SPEED,
    "trapper": TRAPPER_SPEED,
    "bomber": BOMBER_SPEED,
    "healer": HEALER_SPEED,
    "ninja": NINJA_SPEED,
    "shield": SHIELD_SPEED,
    "sniper": SNIPER_SPEED,
    "berserker": BERSERKER_SPEED,
    "chainsaw": CHAINSAW_SPEED,
    "fortifier": FORTIFIER_SPEED,
    "vampire": VAMPIRE_SPEED,
    "archer": ARCHER_SPEED,
    "wizard": WIZARD_SPEED,
    "tank": TANK_SPEED,
    "assassin": ASSASSIN_SPEED,
    "necromancer": NECRO_SPEED,
    "ice_mage": ICE_MAGE_SPEED,
    "summoner": SUMMONER_SPEED,
    "mirror": MIRROR_SPEED,
    "charger": CHARGER_SPEED,
    "mimic": MIMIC_SPEED,
}


# ── Projectiles & objects ──────────────────────────────────

class Spear:
    def __init__(self, x, y, dx, dy, team_id, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.angle = math.atan2(dy, dx)
        self.length = 20
        self.carried_ball = None  # ball being dragged to wall

    def move(self):
        self.x += self.dx
        self.y += self.dy

        # drag the carried ball along
        if self.carried_ball is not None:
            self.carried_ball.x = self.x
            self.carried_ball.y = self.y
            self.carried_ball.vx = 0
            self.carried_ball.vy = 0

            # check if spear hit a wall -> pin the ball there
            hit_wall = False
            if self.x - self.carried_ball.radius <= 0:
                self.carried_ball.x = self.carried_ball.radius
                hit_wall = True
            if self.x + self.carried_ball.radius >= WIDTH:
                self.carried_ball.x = WIDTH - self.carried_ball.radius
                hit_wall = True
            if self.y - self.carried_ball.radius <= 0:
                self.carried_ball.y = self.carried_ball.radius
                hit_wall = True
            if self.y + self.carried_ball.radius >= HEIGHT:
                self.carried_ball.y = HEIGHT - self.carried_ball.radius
                hit_wall = True

            if hit_wall:
                self.carried_ball.pinned_timer = PIN_DURATION
                self.carried_ball.carried_by_spear = False
                self.carried_ball = None
                self.alive = False
            return

        # die if off screen (no carried ball)
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        # shaft
        x1 = int(self.x - cos_a * self.length / 2)
        y1 = int(self.y - sin_a * self.length / 2)
        x2 = int(self.x + cos_a * self.length / 2)
        y2 = int(self.y + sin_a * self.length / 2)
        pygame.draw.line(surface, (160, 120, 60), (x1, y1), (x2, y2), 3)
        # spearhead
        perp_x, perp_y = -sin_a, cos_a
        tip_x = int(self.x + cos_a * (self.length / 2 + 6))
        tip_y = int(self.y + sin_a * (self.length / 2 + 6))
        p1 = (x2, y2)
        p2 = (int(x2 + perp_x * 4), int(y2 + perp_y * 4))
        p3 = (tip_x, tip_y)
        p4 = (int(x2 - perp_x * 4), int(y2 - perp_y * 4))
        pygame.draw.polygon(surface, (180, 180, 190), [p2, p3, p4])


class Trap:
    def __init__(self, x, y, team_id, color):
        self.x = x
        self.y = y
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.radius = TRAP_RADIUS
        self.pulse = 0
        self.captured_ball = None
        self.bounces_left = TRAP_BOUNCES

    def update(self):
        """Handle captured ball bouncing inside the trap."""
        if self.captured_ball is None:
            return
        if not self.captured_ball.alive:
            self.captured_ball.trapped_in = None
            self.captured_ball = None
            self.alive = False
            return
        b = self.captured_ball
        # check if ball hits the trap boundary
        dx = b.x - self.x
        dy = b.y - self.y
        d = math.sqrt(dx * dx + dy * dy)
        inner_r = self.radius - b.radius
        if d >= inner_r and inner_r > 0:
            # reflect velocity off circular wall
            nx, ny = dx / max(d, 0.01), dy / max(d, 0.01)
            # push back inside
            b.x = self.x + nx * (inner_r - 1)
            b.y = self.y + ny * (inner_r - 1)
            # reflect velocity
            dot = b.vx * nx + b.vy * ny
            if dot > 0:  # only if moving outward
                b.vx -= 2 * dot * nx
                b.vy -= 2 * dot * ny
                # add slight random angle
                angle = math.atan2(b.vy, b.vx)
                angle += random.uniform(-0.3, 0.3)
                spd = math.sqrt(b.vx ** 2 + b.vy ** 2)
                # give it some speed if it's too slow
                spd = max(spd, 3.0)
                b.vx = math.cos(angle) * spd
                b.vy = math.sin(angle) * spd
                # damage + count bounce
                b.hp -= TRAP_DAMAGE
                self.bounces_left -= 1
                if self.bounces_left <= 0:
                    self.captured_ball.trapped_in = None
                    self.captured_ball = None
                    self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        self.pulse = (self.pulse + 0.03) % (2 * math.pi)
        c = tuple(max(0, min(255, v // 2 + 60)) for v in self.color)
        # outer ring
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), self.radius, 2)
        # inner ring
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), int(self.radius * 0.7), 1)
        # teeth around edge
        num_teeth = 10
        for i in range(num_teeth):
            a = i * 2 * math.pi / num_teeth + self.pulse
            ox = int(self.x + math.cos(a) * self.radius)
            oy = int(self.y + math.sin(a) * self.radius)
            ix = int(self.x + math.cos(a) * (self.radius - 6))
            iy = int(self.y + math.sin(a) * (self.radius - 6))
            pygame.draw.line(surface, c, (ox, oy), (ix, iy), 2)
        # bounces left indicator
        if self.captured_ball is not None:
            bl = font.render(str(self.bounces_left), True, (255, 100, 100))
            surface.blit(bl, (self.x - bl.get_width() // 2, self.y - self.radius - 18))


class Bomb:
    def __init__(self, x, y, team_id, color):
        self.x = x
        self.y = y
        self.team_id = team_id
        self.color = color
        self.timer = BOMB_TIMER
        self.alive = True
        self.exploding = False
        self.explode_frames = 10
        self.radius = 8
        self.explosion_radius = BALL_RADIUS * 5

    def update(self):
        if self.exploding:
            self.explode_frames -= 1
            if self.explode_frames <= 0:
                self.alive = False
            return
        self.timer -= 1
        if self.timer <= 0:
            self.exploding = True

    def draw(self, surface):
        if not self.alive:
            return
        if self.exploding:
            alpha = self.explode_frames / 10.0
            r = int(self.explosion_radius * (1.0 - alpha * 0.5))
            c = (255, int(150 * alpha), 0)
            pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r, 3)
            pygame.draw.circle(surface, (255, 255, int(200 * alpha)),
                               (int(self.x), int(self.y)), r // 2)
        else:
            pulse = 1.0 if self.timer % 30 < 15 else 0.6
            c = (int(80 * pulse), int(40 * pulse), int(10 * pulse))
            pygame.draw.circle(surface, c, (int(self.x), int(self.y)), self.radius)
            # fuse spark
            if self.timer % 20 < 10:
                sx = int(self.x + random.uniform(-3, 3))
                sy = int(self.y - self.radius + random.uniform(-3, 0))
                pygame.draw.circle(surface, (255, 200, 50), (sx, sy), 2)
            # countdown text
            sec = max(1, (self.timer // 60) + 1)
            t = small_font.render(str(sec), True, (255, 100, 100))
            surface.blit(t, (self.x - t.get_width() // 2, self.y - self.radius - 14))


class Bullet:
    def __init__(self, x, y, dx, dy, team_id, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.angle = math.atan2(dy, dx)

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if self.x < -10 or self.x > WIDTH + 10 or self.y < -10 or self.y > HEIGHT + 10:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        # trail
        trail_len = 10
        tx = self.x - math.cos(self.angle) * trail_len
        ty = self.y - math.sin(self.angle) * trail_len
        pygame.draw.line(surface, (255, 255, 200), (int(tx), int(ty)), (int(self.x), int(self.y)), 2)
        # bullet dot
        pygame.draw.circle(surface, (255, 255, 100), (int(self.x), int(self.y)), 3)


class Arrow:
    def __init__(self, x, y, dx, dy, team_id, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.angle = math.atan2(dy, dx)

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if self.x < -10 or self.x > WIDTH + 10 or self.y < -10 or self.y > HEIGHT + 10:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        # shaft
        tail_x = self.x - cos_a * 12
        tail_y = self.y - sin_a * 12
        pygame.draw.line(surface, (160, 120, 60), (int(tail_x), int(tail_y)),
                         (int(self.x), int(self.y)), 2)
        # arrowhead
        perp_x, perp_y = -sin_a, cos_a
        tip_x = self.x + cos_a * 5
        tip_y = self.y + sin_a * 5
        pygame.draw.polygon(surface, (200, 200, 210), [
            (int(self.x + perp_x * 3), int(self.y + perp_y * 3)),
            (int(self.x - perp_x * 3), int(self.y - perp_y * 3)),
            (int(tip_x), int(tip_y))
        ])
        # fletching
        for side in (-1, 1):
            fx = tail_x + perp_x * 3 * side
            fy = tail_y + perp_y * 3 * side
            pygame.draw.line(surface, (180, 50, 50), (int(tail_x), int(tail_y)),
                             (int(fx), int(fy)), 1)


class IceBolt:
    def __init__(self, x, y, dx, dy, team_id, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.angle = math.atan2(dy, dx)

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if self.x < -10 or self.x > WIDTH + 10 or self.y < -10 or self.y > HEIGHT + 10:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        perp_x, perp_y = -sin_a, cos_a
        # icy crystal shape
        tip_x = self.x + cos_a * 7
        tip_y = self.y + sin_a * 7
        tail_x = self.x - cos_a * 5
        tail_y = self.y - sin_a * 5
        side1 = (int(self.x + perp_x * 3), int(self.y + perp_y * 3))
        side2 = (int(self.x - perp_x * 3), int(self.y - perp_y * 3))
        pygame.draw.polygon(surface, (140, 200, 255), [
            (int(tip_x), int(tip_y)), side1, (int(tail_x), int(tail_y)), side2
        ])
        # bright center
        pygame.draw.circle(surface, (200, 230, 255), (int(self.x), int(self.y)), 2)
        # frost trail
        for i in range(2):
            tx = self.x - cos_a * (i + 1) * 5
            ty = self.y - sin_a * (i + 1) * 5
            pygame.draw.circle(surface, (100, 180, 255), (int(tx), int(ty)), 1)


class MagicOrb:
    def __init__(self, x, y, dx, dy, team_id, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.exploding = False
        self.explode_frames = 8
        self.pulse = 0

    def move(self):
        if self.exploding:
            self.explode_frames -= 1
            if self.explode_frames <= 0:
                self.alive = False
            return
        self.x += self.dx
        self.y += self.dy
        self.pulse += 0.15
        if self.x < -10 or self.x > WIDTH + 10 or self.y < -10 or self.y > HEIGHT + 10:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        if self.exploding:
            # purple explosion ring
            alpha = self.explode_frames / 8.0
            r = int(WIZARD_SPLASH_RADIUS * (1.0 - alpha * 0.4))
            pygame.draw.circle(surface, (180, 80, 255), (int(self.x), int(self.y)), r, 2)
            pygame.draw.circle(surface, (220, 150, 255), (int(self.x), int(self.y)), r // 2, 1)
            return
        # glowing orb with pulsing size
        orb_r = 5 + int(math.sin(self.pulse) * 1.5)
        pygame.draw.circle(surface, (140, 50, 220), (int(self.x), int(self.y)), orb_r + 2)
        pygame.draw.circle(surface, (200, 120, 255), (int(self.x), int(self.y)), orb_r)
        pygame.draw.circle(surface, (240, 200, 255), (int(self.x), int(self.y)), orb_r // 2)
        # sparkle trail
        trail_x = self.x - self.dx * 1.2
        trail_y = self.y - self.dy * 1.2
        pygame.draw.circle(surface, (180, 100, 255), (int(trail_x), int(trail_y)), 2)


class FortWall:
    def __init__(self, x, y, angle, team_id, color, explosive=False, blast_dir=None):
        self.x = x
        self.y = y
        self.angle = angle  # orientation of the wall
        self.team_id = team_id
        self.color = color
        self.alive = True
        self.explosive = explosive
        self.hp = 1 if explosive else FORT_WALL_HP
        self.timer = FORT_EXPLODE_TIMER if explosive else -1
        self.width = FORT_WALL_WIDTH
        self.thickness = FORT_WALL_THICKNESS
        self.exploding = False
        self.explode_frames = 10
        # direction the explosion fires toward (unit vector)
        self.blast_dx = blast_dir[0] if blast_dir else 0.0
        self.blast_dy = blast_dir[1] if blast_dir else 0.0

    def endpoints(self):
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        hw = self.width / 2
        return (self.x - cos_a * hw, self.y - sin_a * hw,
                self.x + cos_a * hw, self.y + sin_a * hw)

    def update(self):
        if self.exploding:
            self.explode_frames -= 1
            if self.explode_frames <= 0:
                self.alive = False
            return
        if self.explosive:
            self.timer -= 1
            if self.timer <= 0:
                self.exploding = True
        if self.hp <= 0:
            if self.explosive:
                self.exploding = True  # detonate on hit
            else:
                self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        x1, y1, x2, y2 = self.endpoints()
        if self.exploding:
            # directional explosion cone
            alpha = self.explode_frames / 10.0
            r = int(FORT_EXPLODE_RADIUS * (1.0 - alpha * 0.5))
            blast_angle = math.atan2(self.blast_dy, self.blast_dx)
            spread = math.pi / 3  # 60 degree cone
            segments = 8
            points = [(int(self.x), int(self.y))]
            for i in range(segments + 1):
                a = blast_angle - spread + (2 * spread * i / segments)
                points.append((int(self.x + math.cos(a) * r),
                                int(self.y + math.sin(a) * r)))
            if len(points) >= 3:
                c = (255, int(180 * alpha), 0)
                pygame.draw.polygon(surface, c, points, 3)
            return
        if self.explosive:
            # orange-red pulsing wall
            pulse = 0.7 + 0.3 * math.sin(self.timer * 0.1)
            c = (int(220 * pulse), int(100 * pulse), 30)
        else:
            # solid team-colored wall
            c = tuple(min(255, v + 40) for v in self.color)
        pygame.draw.line(surface, c, (int(x1), int(y1)), (int(x2), int(y2)), self.thickness)
        # hp pips
        for i in range(self.hp):
            px = self.x + (i - self.hp / 2) * 6
            py = self.y - self.thickness - 4
            pygame.draw.circle(surface, (200, 200, 200), (int(px), int(py)), 2)


# ── UI helpers ──────────────────────────────────────────────

class Button:
    def __init__(self, x, y, w, h, text, color=(70, 70, 90)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hovered = False

    def draw(self, surface):
        c = tuple(min(255, v + 30) for v in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        pygame.draw.rect(surface, (150, 150, 160), self.rect, 2, border_radius=6)
        label = font.render(self.text, True, (255, 255, 255))
        surface.blit(label, (self.rect.centerx - label.get_width() // 2,
                             self.rect.centery - label.get_height() // 2))

    def update(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)


ARENA_SIZES = [
    (540,  960, "Record"),
    (450,  340, "Tiny"),
    (600,  450, "1v1"),
    (660,  495, "2v2"),
    (720,  540, "3v3"),
    (792,  594, "4v4"),
    (860,  645, "5v5"),
    (960,  720, "Big"),
]


def setup_menu(saved_teams=None, saved_num_teams=None, saved_arena_idx=None):
    if saved_teams is not None and saved_num_teams is not None:
        teams = [list(t) for t in saved_teams]
        num_teams = saved_num_teams
    else:
        teams = [["zombie"], ["swordsman"]]
        num_teams = 2

    arena_idx = saved_arena_idx if saved_arena_idx is not None else 2  # default 1v1

    def sync_teams():
        nonlocal teams, num_teams
        # clamp num_teams to valid range
        num_teams = max(2, min(6, num_teams))
        while len(teams) < num_teams:
            teams.append([ROLES[len(teams) % len(ROLES)]])
        while len(teams) > num_teams:
            teams.pop()

    sync_teams()
    prev_size = (0, 0)
    COL_W = 200  # width per column
    minus_teams_rect = pygame.Rect(0, 0, 0, 0)
    plus_teams_rect = pygame.Rect(0, 0, 0, 0)
    minus_arena_rect = pygame.Rect(0, 0, 0, 0)
    plus_arena_rect = pygame.Rect(0, 0, 0, 0)

    # search dropdown state: (team_index, member_index) or None
    search_open = None
    search_text = ""
    dropdown_scroll = 0  # scroll offset for dropdown list

    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEWHEEL and search_open is not None:
                filtered = [r for r in ROLES if search_text.lower() in r.lower()]
                max_scroll = max(0, len(filtered) - 8)
                dropdown_scroll = max(0, min(max_scroll, dropdown_scroll - event.y))
                continue
            if event.type == pygame.KEYDOWN and search_open is not None:
                if event.key == pygame.K_ESCAPE:
                    search_open = None
                    search_text = ""
                    dropdown_scroll = 0
                elif event.key == pygame.K_BACKSPACE:
                    search_text = search_text[:-1]
                    dropdown_scroll = 0
                elif event.key == pygame.K_RETURN:
                    # select first match
                    filtered = [r for r in ROLES if search_text.lower() in r.lower()]
                    if filtered:
                        si, sj = search_open
                        teams[si][sj] = filtered[dropdown_scroll]
                    search_open = None
                    search_text = ""
                    dropdown_scroll = 0
                elif event.unicode and event.unicode.isprintable():
                    search_text += event.unicode
                    dropdown_scroll = 0
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # check if clicking a dropdown option
                if search_open is not None and hasattr(setup_menu, '_dropdown_rects'):
                    clicked_option = False
                    for role_name, drect in setup_menu._dropdown_rects:
                        if drect.collidepoint(mx, my):
                            si, sj = search_open
                            teams[si][sj] = role_name
                            search_open = None
                            search_text = ""
                            clicked_option = True
                            break
                    if clicked_option:
                        continue
                    # clicking outside dropdown closes it
                    search_open = None
                    search_text = ""
                    dropdown_scroll = 0
                if minus_arena_rect.collidepoint(mx, my) and arena_idx > 0:
                    arena_idx -= 1
                if plus_arena_rect.collidepoint(mx, my) and arena_idx < len(ARENA_SIZES) - 1:
                    arena_idx += 1
                if randomize_btn.clicked(mx, my):
                    for i in range(len(teams)):
                        for j in range(len(teams[i])):
                            teams[i][j] = random.choice(ROLES)
                if randomize_all_btn.clicked(mx, my):
                    num_teams = random.randint(2, 6)
                    teams = []
                    for i in range(num_teams):
                        count = random.randint(1, 5)
                        teams.append([random.choice(ROLES) for _ in range(count)])
                    sync_teams()
                if tourney_btn.clicked(mx, my):
                    return "tournament", teams, num_teams, arena_idx
                if interactive_btn.clicked(mx, my):
                    return "interactive", teams, num_teams, arena_idx
                if start_btn.clicked(mx, my):
                    sync_teams()
                    result = []
                    for i in range(num_teams):
                        for role in teams[i]:
                            result.append({"team_id": i, "role": role})
                    return result, teams, num_teams, arena_idx
                if minus_teams_rect.collidepoint(mx, my) and num_teams > 2:
                    num_teams -= 1
                    sync_teams()
                if plus_teams_rect.collidepoint(mx, my) and num_teams < 6:
                    num_teams += 1
                    sync_teams()
                for i in range(min(num_teams, len(teams))):
                    rects = member_rects.get(i, [])
                    for j, mr in enumerate(rects):
                        if "role" in mr and mr["role"].collidepoint(mx, my):
                            search_open = (i, j)
                            search_text = ""
                        if "remove" in mr and mr["remove"].collidepoint(mx, my) and len(teams[i]) > 1:
                            teams[i].pop(j)
                            break
                    tr = team_rects.get(i, {})
                    if "add" in tr and tr["add"].collidepoint(mx, my) and len(teams[i]) < 5:
                        teams[i].append(ROLES[0])

        # recompute layout AFTER events so indices are always fresh
        sync_teams()
        use_cols = 2 if num_teams >= 4 else 1
        if use_cols == 2:
            left_teams = (num_teams + 1) // 2
        else:
            left_teams = num_teams

        def col_height(team_indices):
            h = 0
            for i in team_indices:
                h += 28 + len(teams[i]) * 28 + 10
            return h

        left_indices = list(range(left_teams))
        right_indices = list(range(left_teams, num_teams))
        left_h = col_height(left_indices)
        right_h = col_height(right_indices) if right_indices else 0
        content_h = max(left_h, right_h)

        needed_h = 150 + content_h + 170
        menu_h = max(BASE_HEIGHT, min(needed_h, 900))
        menu_w = max(BASE_WIDTH, COL_W * use_cols + 250)
        new_size = (menu_w, menu_h)
        if new_size != prev_size:
            screen = pygame.display.set_mode(new_size)
            prev_size = new_size

        randomize_btn = Button(menu_w // 2 - 195, menu_h - 70, 110, 45, "RANDOMIZE", (90, 60, 120))
        randomize_all_btn = Button(menu_w // 2 + 85, menu_h - 70, 130, 45, "RANDOM ALL", (120, 50, 90))
        start_btn = Button(menu_w // 2 - 80, menu_h - 70, 160, 45, "START FIGHT!")
        tourney_btn = Button(menu_w // 2 - 130, menu_h - 120, 120, 35, "TOURNAMENT", (60, 90, 130))
        interactive_btn = Button(menu_w // 2 + 10, menu_h - 120, 120, 35, "INTERACTIVE", (90, 60, 100))
        randomize_btn.update(mx, my)
        randomize_all_btn.update(mx, my)
        start_btn.update(mx, my)
        tourney_btn.update(mx, my)
        interactive_btn.update(mx, my)

        screen.fill((20, 20, 30))
        t = title_font.render("Ball Fights - Setup", True, (255, 255, 255))
        screen.blit(t, (menu_w // 2 - t.get_width() // 2, 20))

        ty = 65
        label = font.render("Teams:", True, (200, 200, 200))
        screen.blit(label, (menu_w // 2 - 90, ty))

        minus_teams_rect = pygame.Rect(menu_w // 2, ty - 2, 30, 26)
        plus_teams_rect = pygame.Rect(menu_w // 2 + 70, ty - 2, 30, 26)
        pygame.draw.rect(screen, (80, 80, 100), minus_teams_rect, border_radius=4)
        pygame.draw.rect(screen, (80, 80, 100), plus_teams_rect, border_radius=4)
        m_label = font.render("-", True, (255, 255, 255))
        p_label = font.render("+", True, (255, 255, 255))
        screen.blit(m_label, (minus_teams_rect.centerx - m_label.get_width() // 2,
                              minus_teams_rect.centery - m_label.get_height() // 2))
        screen.blit(p_label, (plus_teams_rect.centerx - p_label.get_width() // 2,
                              plus_teams_rect.centery - p_label.get_height() // 2))
        num_label = font.render(str(num_teams), True, (255, 255, 255))
        screen.blit(num_label, (menu_w // 2 + 42 - num_label.get_width() // 2, ty))

        # arena size selector
        ay = ty + 30
        a_label = font.render("Arena:", True, (200, 200, 200))
        screen.blit(a_label, (menu_w // 2 - 90, ay))
        minus_arena_rect = pygame.Rect(menu_w // 2, ay - 2, 30, 26)
        plus_arena_rect = pygame.Rect(menu_w // 2 + 200, ay - 2, 30, 26)
        pygame.draw.rect(screen, (80, 80, 100), minus_arena_rect, border_radius=4)
        pygame.draw.rect(screen, (80, 80, 100), plus_arena_rect, border_radius=4)
        screen.blit(m_label, (minus_arena_rect.centerx - m_label.get_width() // 2,
                              minus_arena_rect.centery - m_label.get_height() // 2))
        screen.blit(p_label, (plus_arena_rect.centerx - p_label.get_width() // 2,
                              plus_arena_rect.centery - p_label.get_height() // 2))
        aw, ah, a_hint = ARENA_SIZES[arena_idx]
        arena_text = font.render(f"{aw}x{ah} ({a_hint})", True, (255, 255, 255))
        screen.blit(arena_text, (menu_w // 2 + 38, ay))

        team_rects = {}
        member_rects = {}

        for col in range(use_cols):
            col_x = 20 + col * (COL_W + 40)
            col_teams = left_indices if col == 0 else right_indices
            cur_y = 140

            for i in col_teams:
                team_rects[i] = {}
                member_rects[i] = []
                color = TEAM_COLORS[i % len(TEAM_COLORS)]

                pygame.draw.circle(screen, color, (col_x + 10, cur_y + 10), 10)
                tl = font.render(f"Team {i + 1}", True, color)
                screen.blit(tl, (col_x + 28, cur_y))

                add_rect = pygame.Rect(col_x + 120, cur_y - 2, 22, 22)
                team_rects[i]["add"] = add_rect
                pygame.draw.rect(screen, (50, 100, 50), add_rect, border_radius=4)
                screen.blit(small_font.render("+", True, (255, 255, 255)),
                            (add_rect.centerx - 3, add_rect.centery - 7))

                cur_y += 28
                for j, role in enumerate(teams[i]):
                    mr = {}
                    role_rect = pygame.Rect(col_x + 30, cur_y, 100, 24)
                    mr["role"] = role_rect
                    pygame.draw.rect(screen, (60, 60, 80), role_rect, border_radius=4)
                    pygame.draw.rect(screen, color, role_rect, 2, border_radius=4)
                    rl = small_font.render(role.capitalize(), True, (255, 255, 255))
                    screen.blit(rl, (role_rect.centerx - rl.get_width() // 2,
                                     role_rect.centery - rl.get_height() // 2))
                    if len(teams[i]) > 1:
                        rem_rect = pygame.Rect(col_x + 136, cur_y, 22, 24)
                        mr["remove"] = rem_rect
                        pygame.draw.rect(screen, (100, 40, 40), rem_rect, border_radius=4)
                        screen.blit(small_font.render("x", True, (255, 255, 255)),
                                    (rem_rect.centerx - 3, rem_rect.centery - 7))

                    member_rects[i].append(mr)
                    cur_y += 28
                cur_y += 10

        hint = small_font.render("Click role to search  |  + to add member  |  x to remove", True, (120, 120, 140))
        screen.blit(hint, (menu_w // 2 - hint.get_width() // 2, menu_h - 110))

        randomize_btn.draw(screen)
        randomize_all_btn.draw(screen)
        start_btn.draw(screen)
        tourney_btn.draw(screen)
        interactive_btn.draw(screen)

        # draw search dropdown on top of everything
        setup_menu._dropdown_rects = []
        if search_open is not None:
            si, sj = search_open
            rects = member_rects.get(si, [])
            if sj < len(rects) and "role" in rects[sj]:
                anchor = rects[sj]["role"]
                # search box
                sb_x = anchor.x
                sb_y = anchor.y + anchor.height + 2
                sb_w = 130
                pygame.draw.rect(screen, (40, 40, 55), (sb_x, sb_y, sb_w, 22))
                pygame.draw.rect(screen, (150, 150, 200), (sb_x, sb_y, sb_w, 22), 1)
                cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
                stxt = small_font.render(search_text + cursor, True, (255, 255, 255))
                screen.blit(stxt, (sb_x + 4, sb_y + 4))
                # filtered results — scrollable, show 8 at a time
                filtered = [r for r in ROLES if search_text.lower() in r.lower()]
                max_visible = 8
                max_scroll = max(0, len(filtered) - max_visible)
                dropdown_scroll = min(dropdown_scroll, max_scroll)
                visible = filtered[dropdown_scroll:dropdown_scroll + max_visible]
                dy = sb_y + 24
                for role_name in visible:
                    opt_rect = pygame.Rect(sb_x, dy, sb_w, 20)
                    hovered = opt_rect.collidepoint(mx, my)
                    bg = (70, 70, 100) if hovered else (50, 50, 65)
                    pygame.draw.rect(screen, bg, opt_rect)
                    pygame.draw.rect(screen, (100, 100, 120), opt_rect, 1)
                    rl = small_font.render(role_name.capitalize(), True, (255, 255, 255))
                    screen.blit(rl, (sb_x + 4, dy + 3))
                    setup_menu._dropdown_rects.append((role_name, opt_rect))
                    dy += 20
                # scroll indicators
                if dropdown_scroll > 0:
                    pygame.draw.polygon(screen, (180, 180, 200), [
                        (sb_x + sb_w - 10, sb_y + 28), (sb_x + sb_w - 6, sb_y + 24), (sb_x + sb_w - 2, sb_y + 28)])
                if dropdown_scroll < max_scroll:
                    pygame.draw.polygon(screen, (180, 180, 200), [
                        (sb_x + sb_w - 10, dy - 4), (sb_x + sb_w - 6, dy), (sb_x + sb_w - 2, dy - 4)])

        pygame.display.flip()
        clock.tick(60)


# ── Ball class ──────────────────────────────────────────────

class Ball:
    def __init__(self, x, y, color, team_id, role):
        self.x = x
        self.y = y
        self.color = color
        self.team_id = team_id
        self.role = role
        self.hp = TANK_HP if role == "tank" else 100
        self.max_hp = self.hp
        self.radius = BALL_RADIUS
        self.vx = 0.0
        self.vy = 0.0
        self.hit_cooldown = 0
        self.bounce_timer = 0
        self.sword_angle = random.uniform(0, 2 * math.pi)
        self.speed = ROLE_SPEEDS.get(role, 3.0)
        self.strafe_dir = random.choice([-1, 1])
        self.alive = True
        # spearman
        self.spear_cooldown = random.randint(30, 90)
        # trapper
        self.trap_cooldown = random.randint(30, 90)
        # bomber
        self.bomb_cooldown = random.randint(30, 90)
        # healer
        self.heal_cooldown = 0
        # shield
        self.shield_angle = random.uniform(0, 2 * math.pi)
        # sniper
        self.sniper_cooldown = random.randint(30, 90)
        # ninja
        self.invisible = False
        self.invis_timer = 0
        self.invis_cooldown = random.randint(60, 120)
        # chainsaw
        self.chainsaw_angle = random.uniform(0, 2 * math.pi)
        # fortifier
        self.wall_cooldown = random.randint(30, 90)
        # archer
        self.archer_cooldown = random.randint(20, 50)
        # wizard
        self.wizard_cooldown = random.randint(30, 70)
        # assassin
        self.assassin_dash_cooldown = random.randint(30, 90)
        self.assassin_dashing = 0       # frames left in dash
        self.assassin_retreating = 0    # frames left in retreat
        self.assassin_dash_target = None
        self.assassin_retreat_dx = 0.0
        self.assassin_retreat_dy = 0.0
        # necromancer
        self.necro_cooldown = random.randint(60, 120)
        # ice mage
        self.ice_cooldown = random.randint(20, 50)
        # summoner
        self.summon_cooldown = random.randint(60, 120)
        self.minions = []  # track active minions
        self.is_minion = False  # true for summoned minions
        # charger
        self.charge_cooldown = random.randint(30, 80)
        self.charging = 0           # frames left in charge
        self.charge_windup = 0      # frames left in windup
        self.charge_dx = 0.0
        self.charge_dy = 0.0
        # mimic
        self.mimic_timer = 0        # frames until next copy allowed
        self.mimic_original = (role == "mimic")  # is this a mimic?
        self.mimic_display_role = None  # the role it's currently copying
        # debuffs
        self.slow_timer = 0             # frames of slow remaining
        self.pinned_timer = 0       # frames pinned to wall
        self.trap_bounces = 0       # remaining damaging bounces
        self.carried_by_spear = False  # being dragged by a spear
        self.trapped_in = None          # reference to trap cage

    @property
    def rage_multiplier(self):
        """At 100 HP: 1.0x. At 50 HP: 1.75x. At 25 HP: 2.1x. At 10 HP: 2.35x."""
        if self.role != "berserker":
            return 1.0
        missing = max(0, 100 - self.hp)
        return 1.0 + missing / 66.0

    MELEE_ROLES = {"zombie", "swordsman", "berserker", "shield", "chainsaw", "vampire", "tank", "charger"}
    RANGED_ROLES = {"sniper", "archer", "wizard", "ice_mage", "spearman", "bomber", "trapper", "fortifier"}
    PRIORITY_ROLES = {"healer", "shield"}  # high-value targets for ninja

    def _focus_leader(self, enemies):
        """When 3+ enemy teams are alive, prefer targeting the team with the most total HP."""
        team_hp = {}
        for b in enemies:
            team_hp[b.team_id] = team_hp.get(b.team_id, 0) + b.hp
        if len(team_hp) < 2:
            return enemies
        leader_team = max(team_hp, key=team_hp.get)
        avg_other = sum(hp for tid, hp in team_hp.items() if tid != leader_team) / max(len(team_hp) - 1, 1)
        if team_hp[leader_team] > avg_other * 1.3:
            focused = [b for b in enemies if b.team_id == leader_team]
            if focused:
                return focused
        return enemies

    def find_target(self, all_balls):
        enemies = [b for b in all_balls
                   if b is not self and b.alive and b.team_id != self.team_id
                   and not (b.role == "ninja" and b.invisible)]
        if not enemies:
            return None

        if self.role == "zombie":
            # brainless — just go for nearest, no strategy
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        # ignore minions when their summoner is alive — go for the summoner instead
        non_minions = [b for b in enemies if not b.is_minion]
        if non_minions:
            enemies = non_minions

        # gang up on the leading team (all roles except zombie)
        enemies = self._focus_leader(enemies)

        # tank targeting rules:
        # - melee units avoid tanks if allies have ranged units to deal with them
        if self.role in self.MELEE_ROLES and self.role not in ("zombie", "tank"):
            has_ranged_ally = any(b.alive and b.team_id == self.team_id and b.role in self.RANGED_ROLES
                                 for b in all_balls if b is not self)
            if has_ranged_ally:
                non_tanks = [b for b in enemies if b.role != "tank"]
                if non_tanks:
                    enemies = non_tanks

        if self.role == "spearman":
            free = [b for b in enemies
                    if b.pinned_timer == 0 and not b.carried_by_spear and b.trapped_in is None]
            if free:
                return min(free, key=lambda b: dist(self.x, self.y, b.x, b.y))
            # secondary: prefer tanks
            tanks = [b for b in enemies if b.role == "tank"]
            if tanks:
                return min(tanks, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: b.hp)

        if self.role == "ninja":
            # assassin — prioritize healers and shields
            priority = [b for b in enemies if b.role in self.PRIORITY_ROLES]
            if priority:
                return min(priority, key=lambda b: dist(self.x, self.y, b.x, b.y))
            # then go for lowest HP
            return min(enemies, key=lambda b: b.hp)

        if self.role == "vampire":
            # hunt lowest HP enemies to lifesteal
            return min(enemies, key=lambda b: b.hp)

        if self.role == "sniper":
            # pick off melee enemies that are fighting up close
            melee = [b for b in enemies if b.role in self.MELEE_ROLES]
            if melee:
                return min(melee, key=lambda b: dist(self.x, self.y, b.x, b.y))
            # secondary: prefer tanks
            tanks = [b for b in enemies if b.role == "tank"]
            if tanks:
                return min(tanks, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role in self.MELEE_ROLES and self.role != "zombie":
            # melee fighters target other melee first
            melee = [b for b in enemies if b.role in self.MELEE_ROLES]
            if melee:
                return min(melee, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "archer":
            # archer targets nearest, but prefer tanks secondarily
            tanks = [b for b in enemies if b.role == "tank"]
            if tanks:
                return min(tanks, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "assassin":
            # hunt lowest HP enemies — finisher
            return min(enemies, key=lambda b: b.hp)

        if self.role == "necromancer":
            # seek lowest HP ally to stay near and protect
            allies = [b for b in all_balls if b.alive and b.team_id == self.team_id and b is not self]
            if allies:
                return min(allies, key=lambda b: b.hp)
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "charger":
            # target nearest enemy to charge at
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "mirror":
            # prioritize ranged enemies to walk into their projectiles
            ranged = [b for b in enemies if b.role in ("sniper", "archer", "wizard", "ice_mage", "spearman")]
            if ranged:
                return min(ranged, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "summoner":
            # target nearest enemy (summoner stays back, minions fight)
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "ice_mage":
            # prioritize enemies that aren't already slowed
            unslowed = [b for b in enemies if b.slow_timer <= 0]
            if unslowed:
                return min(unslowed, key=lambda b: dist(self.x, self.y, b.x, b.y))
            # secondary: prefer tanks
            tanks = [b for b in enemies if b.role == "tank"]
            if tanks:
                return min(tanks, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        if self.role == "wizard":
            # target enemy with most allies nearby (maximize splash)
            def cluster_score(b):
                nearby = sum(1 for e in enemies if e is not b and dist(b.x, b.y, e.x, e.y) < WIZARD_SPLASH_RADIUS)
                return nearby
            return max(enemies, key=cluster_score)

        if self.role == "fortifier":
            # fortifier targets nearest, but prefer tanks secondarily
            tanks = [b for b in enemies if b.role == "tank"]
            if tanks:
                return min(tanks, key=lambda b: dist(self.x, self.y, b.x, b.y))
            return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

        # default: nearest enemy
        return min(enemies, key=lambda b: dist(self.x, self.y, b.x, b.y))

    def seek(self, target, all_balls=None):
        if self.bounce_timer > 0 or self.pinned_timer > 0 or self.carried_by_spear or self.trapped_in is not None or target is None:
            return

        dx = target.x - self.x
        dy = target.y - self.y
        d = math.sqrt(dx * dx + dy * dy)
        if d < 0.01:
            return
        nx, ny = dx / d, dy / d

        if self.role == "zombie":
            self.vx = nx * self.speed
            self.vy = ny * self.speed

        elif self.role == "swordsman":
            ideal_dist = self.radius + SWORD_LENGTH * 0.8
            if d < ideal_dist - 10:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal_dist + 30:
                if random.random() < 0.008:
                    self.strafe_dir *= -1
                sx = -ny * self.strafe_dir
                sy = nx * self.strafe_dir
                self.vx = sx * self.speed
                self.vy = sy * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "spearman":
            # keep medium distance for throwing
            ideal = BALL_RADIUS * 5
            if d < ideal - 20:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 30:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "trapper":
            # stay away, lure enemies into traps
            ideal = BALL_RADIUS * 4
            if d < ideal:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 40:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "bomber":
            # approach to medium range, drop bomb, then retreat
            ideal = BALL_RADIUS * 4
            if d < ideal - 10:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 30:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "healer":
            if all_balls is None:
                return
            enemies = [e for e in all_balls if e.alive and e.team_id != self.team_id]
            allies_hurt = [a for a in all_balls if a is not self and a.alive
                           and a.team_id == self.team_id and a.hp < a.max_hp]

            # always prioritize going to the weakest ally
            if allies_hurt:
                heal_target = min(allies_hurt, key=lambda a: a.hp)
                hx = heal_target.x - self.x
                hy = heal_target.y - self.y
                hd = max(math.sqrt(hx * hx + hy * hy), 0.01)

                # if enemy is very close, blend flee + heal direction
                flee_nx, flee_ny = 0, 0
                if enemies:
                    nearest_enemy = min(enemies, key=lambda e: dist(self.x, self.y, e.x, e.y))
                    ed = dist(self.x, self.y, nearest_enemy.x, nearest_enemy.y)
                    if ed < BALL_RADIUS * 3:
                        flee_nx = (self.x - nearest_enemy.x) / max(ed, 0.01)
                        flee_ny = (self.y - nearest_enemy.y) / max(ed, 0.01)

                # move toward hurt ally, with flee mixed in
                mx = (hx / hd) + flee_nx * 0.5
                my = (hy / hd) + flee_ny * 0.5
                md = max(math.sqrt(mx * mx + my * my), 0.01)
                self.vx = (mx / md) * self.speed
                self.vy = (my / md) * self.speed
            else:
                # no one hurt — stay near allies, always flee enemies
                allies = [a for a in all_balls if a is not self and a.alive
                          and a.team_id == self.team_id]
                move_x, move_y = 0.0, 0.0
                if allies:
                    # drift toward center of team
                    cx = sum(a.x for a in allies) / len(allies)
                    cy = sum(a.y for a in allies) / len(allies)
                    ddx = cx - self.x
                    ddy = cy - self.y
                    dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                    move_x += ddx / dd * 0.5
                    move_y += ddy / dd * 0.5
                if enemies:
                    # always flee from nearest enemy, not just when close
                    nearest_enemy = min(enemies, key=lambda e: dist(self.x, self.y, e.x, e.y))
                    ed = dist(self.x, self.y, nearest_enemy.x, nearest_enemy.y)
                    ex = self.x - nearest_enemy.x
                    ey = self.y - nearest_enemy.y
                    move_x += (ex / max(ed, 0.01))
                    move_y += (ey / max(ed, 0.01))
                md = max(math.sqrt(move_x * move_x + move_y * move_y), 0.01)
                self.vx = (move_x / md) * self.speed
                self.vy = (move_y / md) * self.speed

        elif self.role == "shield":
            if all_balls is None:
                self.vx = nx * self.speed
                self.vy = ny * self.speed
                return
            allies = [a for a in all_balls if a is not self and a.alive
                      and a.team_id == self.team_id]
            enemies = [e for e in all_balls if e.alive and e.team_id != self.team_id
                       and not (e.role == "ninja" and e.invisible)]
            if allies:
                # protect mode — find weakest ally and stay between them and nearest enemy
                weakest = min(allies, key=lambda a: a.hp)
                if enemies:
                    threat = min(enemies, key=lambda e: dist(weakest.x, weakest.y, e.x, e.y))
                    # position between weakest ally and their threat
                    gx = (weakest.x + threat.x) / 2
                    gy = (weakest.y + threat.y) / 2
                    # stay closer to ally side
                    gx = weakest.x + (gx - weakest.x) * 0.6
                    gy = weakest.y + (gy - weakest.y) * 0.6
                    dx2 = gx - self.x
                    dy2 = gy - self.y
                    dd = max(math.sqrt(dx2 * dx2 + dy2 * dy2), 0.01)
                    self.vx = (dx2 / dd) * self.speed
                    self.vy = (dy2 / dd) * self.speed
                else:
                    # no enemies, stay near weakest ally
                    dx2 = weakest.x - self.x
                    dy2 = weakest.y - self.y
                    dd = max(math.sqrt(dx2 * dx2 + dy2 * dy2), 0.01)
                    if dd > BALL_RADIUS * 2:
                        self.vx = (dx2 / dd) * self.speed * 0.5
                        self.vy = (dy2 / dd) * self.speed * 0.5
                    else:
                        self.vx *= 0.5
                        self.vy *= 0.5
            else:
                # no allies — charge at enemy
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "berserker":
            # charge at enemy, speed scales with rage
            mult = self.rage_multiplier
            self.vx = nx * self.speed * mult
            self.vy = ny * self.speed * mult

        elif self.role == "sniper":
            # stay very far away, strafe
            ideal = BALL_RADIUS * 10
            if d < ideal - 30:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 40:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "ninja":
            if self.invisible:
                # rush straight at target for backstab
                self.vx = nx * self.speed
                self.vy = ny * self.speed
            else:
                # keep distance, wait for invisibility
                ideal = BALL_RADIUS * 5
                if d < ideal:
                    self.vx = -nx * self.speed
                    self.vy = -ny * self.speed
                else:
                    if random.random() < 0.01:
                        self.strafe_dir *= -1
                    self.vx = -ny * self.strafe_dir * self.speed * 0.5
                    self.vy = nx * self.strafe_dir * self.speed * 0.5

        elif self.role == "chainsaw":
            # charge straight at enemy — wants to be touching them
            self.vx = nx * self.speed
            self.vy = ny * self.speed

        elif self.role == "vampire":
            # charge at target, wants to be in melee range
            self.vx = nx * self.speed
            self.vy = ny * self.speed

        elif self.role == "tank":
            # body-block — charge at nearest enemy to draw aggro
            self.vx = nx * self.speed
            self.vy = ny * self.speed

        elif self.role == "wizard":
            # stay far back, lob orbs
            ideal = BALL_RADIUS * 8
            if d < ideal - 20:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 30:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "assassin":
            if self.assassin_retreating > 0:
                # retreat — run away from where we hit
                self.vx = self.assassin_retreat_dx * ASSASSIN_RETREAT_SPEED
                self.vy = self.assassin_retreat_dy * ASSASSIN_RETREAT_SPEED
                self.assassin_retreating -= 1
            elif self.assassin_dashing > 0:
                # dashing — charge at target fast
                self.vx = nx * ASSASSIN_DASH_SPEED
                self.vy = ny * ASSASSIN_DASH_SPEED
                self.assassin_dashing -= 1
                if self.assassin_dashing == 0:
                    # dash expired without hitting, go to cooldown
                    self.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
            elif self.assassin_dash_cooldown <= 0 and d < BALL_RADIUS * 8:
                # start dash
                self.assassin_dashing = ASSASSIN_DASH_DURATION
                self.assassin_dash_target = target
            else:
                # circle at medium range waiting for cooldown
                ideal = BALL_RADIUS * 5
                if d < ideal - 15:
                    self.vx = -nx * self.speed
                    self.vy = -ny * self.speed
                elif d < ideal + 20:
                    if random.random() < 0.01:
                        self.strafe_dir *= -1
                    self.vx = -ny * self.strafe_dir * self.speed
                    self.vy = nx * self.strafe_dir * self.speed
                else:
                    self.vx = nx * self.speed
                    self.vy = ny * self.speed

        elif self.role == "necromancer":
            if all_balls is not None:
                # seek lowest HP ally to stay near
                allies = [b for b in all_balls if b.alive and b.team_id == self.team_id and b is not self]
                if allies:
                    weakest = min(allies, key=lambda b: b.hp)
                    ax = weakest.x - self.x
                    ay_d = weakest.y - self.y
                    ad = max(math.sqrt(ax * ax + ay_d * ay_d), 0.01)
                    # stay near the weakest ally but keep some distance
                    ideal = BALL_RADIUS * 4
                    if ad > ideal:
                        self.vx = (ax / ad) * self.speed
                        self.vy = (ay_d / ad) * self.speed
                    else:
                        # orbit nearby
                        if random.random() < 0.01:
                            self.strafe_dir *= -1
                        self.vx = -ay_d / ad * self.strafe_dir * self.speed * 0.5
                        self.vy = ax / ad * self.strafe_dir * self.speed * 0.5
                else:
                    # no allies, flee from enemies
                    self.vx = -nx * self.speed
                    self.vy = -ny * self.speed
            else:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed

        elif self.role == "charger":
            if self.charging > 0:
                # locked direction during charge
                self.vx = self.charge_dx * CHARGER_CHARGE_SPEED
                self.vy = self.charge_dy * CHARGER_CHARGE_SPEED
                self.charging -= 1
                if self.charging == 0:
                    self.charge_cooldown = CHARGER_CHARGE_COOLDOWN
            elif self.charge_windup > 0:
                # slowing down, aiming at target
                self.vx = nx * self.speed * 0.2
                self.vy = ny * self.speed * 0.2
                self.charge_windup -= 1
                if self.charge_windup == 0:
                    # lock in charge direction
                    self.charge_dx = nx
                    self.charge_dy = ny
                    self.charging = CHARGER_CHARGE_DURATION
            elif self.charge_cooldown <= 0 and d < BALL_RADIUS * 10:
                # start windup
                self.charge_windup = CHARGER_WINDUP
            else:
                # walk toward target normally
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "mirror":
            # flee from melee enemies, approach ranged ones
            if target.role in self.MELEE_ROLES:
                # run away from melee
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            else:
                # approach ranged enemies to intercept projectiles
                ideal = BALL_RADIUS * 5
                if d < ideal - 10:
                    if random.random() < 0.01:
                        self.strafe_dir *= -1
                    self.vx = -ny * self.strafe_dir * self.speed
                    self.vy = nx * self.strafe_dir * self.speed
                else:
                    self.vx = nx * self.speed
                    self.vy = ny * self.speed

        elif self.role == "summoner":
            # stay very far back, let minions fight
            ideal = BALL_RADIUS * 9
            if d < ideal - 20:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 30:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed * 0.6
                self.vy = nx * self.strafe_dir * self.speed * 0.6
            else:
                self.vx = nx * self.speed * 0.5
                self.vy = ny * self.speed * 0.5

        elif self.role == "ice_mage":
            # stay at range, kite enemies
            ideal = BALL_RADIUS * 7
            if d < ideal - 20:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 30:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "archer":
            # keep medium distance (closer than sniper, farther than spearman)
            ideal = BALL_RADIUS * 7
            if d < ideal - 20:
                self.vx = -nx * self.speed
                self.vy = -ny * self.speed
            elif d < ideal + 30:
                if random.random() < 0.01:
                    self.strafe_dir *= -1
                self.vx = -ny * self.strafe_dir * self.speed
                self.vy = nx * self.strafe_dir * self.speed
            else:
                self.vx = nx * self.speed
                self.vy = ny * self.speed

        elif self.role == "fortifier":
            if all_balls is None:
                self.vx = nx * self.speed
                self.vy = ny * self.speed
            else:
                allies_hurt = [a for a in all_balls if a is not self and a.alive
                               and a.team_id == self.team_id and a.hp < 100
                               and a.role not in ("fortifier", "shield")]
                if allies_hurt:
                    # protect mode — stay near weakest ally
                    weakest = min(allies_hurt, key=lambda a: a.hp)
                    dx2 = weakest.x - self.x
                    dy2 = weakest.y - self.y
                    dd = max(math.sqrt(dx2 * dx2 + dy2 * dy2), 0.01)
                    # stay close but not on top
                    if dd > BALL_RADIUS * 3:
                        self.vx = (dx2 / dd) * self.speed
                        self.vy = (dy2 / dd) * self.speed
                    else:
                        # face toward nearest enemy
                        self.vx = nx * self.speed * 0.3
                        self.vy = ny * self.speed * 0.3
                else:
                    # no hurt allies — push toward enemy aggressively
                    ideal = BALL_RADIUS * 4
                    if d < ideal:
                        if random.random() < 0.01:
                            self.strafe_dir *= -1
                        self.vx = -ny * self.strafe_dir * self.speed
                        self.vy = nx * self.strafe_dir * self.speed
                    else:
                        self.vx = nx * self.speed
                        self.vy = ny * self.speed

        elif self.role == "mimic":
            # charge straight at nearest enemy to copy their role
            self.vx = nx * self.speed
            self.vy = ny * self.speed

        # team cohesion — pull toward teammates (all roles)
        if all_balls is not None:
            allies = [a for a in all_balls if a is not self and a.alive
                      and a.team_id == self.team_id]
            if allies:
                cx = sum(a.x for a in allies) / len(allies)
                cy = sum(a.y for a in allies) / len(allies)
                dx_c = cx - self.x
                dy_c = cy - self.y
                dd_c = max(math.sqrt(dx_c * dx_c + dy_c * dy_c), 0.01)
                # stronger pull the farther away (but capped)
                pull = min(dd_c / (BALL_RADIUS * 8), 1.0) * 0.3
                self.vx += (dx_c / dd_c) * self.speed * pull
                self.vy += (dy_c / dd_c) * self.speed * pull

    def move(self):
        if self.carried_by_spear:
            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1
            return
        if self.trapped_in is not None:
            # move inside trap — trap.update() handles bouncing
            self.x += self.vx
            self.y += self.vy
            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1
            if self.spear_cooldown > 0:
                self.spear_cooldown -= 1
            if self.trap_cooldown > 0:
                self.trap_cooldown -= 1
            if self.bomb_cooldown > 0:
                self.bomb_cooldown -= 1
            if self.heal_cooldown > 0:
                self.heal_cooldown -= 1
            if self.invis_cooldown > 0:
                self.invis_cooldown -= 1
            if self.sniper_cooldown > 0:
                self.sniper_cooldown -= 1
            if self.archer_cooldown > 0:
                self.archer_cooldown -= 1
            if self.wizard_cooldown > 0:
                self.wizard_cooldown -= 1
            if self.assassin_dash_cooldown > 0:
                self.assassin_dash_cooldown -= 1
            if self.necro_cooldown > 0:
                self.necro_cooldown -= 1
            if self.ice_cooldown > 0:
                self.ice_cooldown -= 1
            if self.summon_cooldown > 0:
                self.summon_cooldown -= 1
            if self.charge_cooldown > 0:
                self.charge_cooldown -= 1
            if self.mimic_timer > 0:
                self.mimic_timer -= 1
                if self.mimic_timer == 0 and self.mimic_original:
                    self.role = "mimic"
                    self.speed = MIMIC_SPEED
            if self.invisible:
                self.invis_timer -= 1
                if self.invis_timer <= 0:
                    self.invisible = False
                    self.invis_cooldown = NINJA_INVIS_COOLDOWN
            if self.role == "swordsman":
                self.sword_angle += SWORD_SPIN_SPEED
            if self.role == "chainsaw":
                self.chainsaw_angle += CHAINSAW_SPIN_SPEED
            if self.wall_cooldown > 0:
                self.wall_cooldown -= 1
            return
        if self.pinned_timer > 0:
            self.pinned_timer -= 1
            self.vx = 0
            self.vy = 0
            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1
            if self.spear_cooldown > 0:
                self.spear_cooldown -= 1
            if self.trap_cooldown > 0:
                self.trap_cooldown -= 1
            if self.bomb_cooldown > 0:
                self.bomb_cooldown -= 1
            if self.heal_cooldown > 0:
                self.heal_cooldown -= 1
            if self.invis_cooldown > 0:
                self.invis_cooldown -= 1
            if self.sniper_cooldown > 0:
                self.sniper_cooldown -= 1
            if self.archer_cooldown > 0:
                self.archer_cooldown -= 1
            if self.wizard_cooldown > 0:
                self.wizard_cooldown -= 1
            if self.assassin_dash_cooldown > 0:
                self.assassin_dash_cooldown -= 1
            if self.necro_cooldown > 0:
                self.necro_cooldown -= 1
            if self.ice_cooldown > 0:
                self.ice_cooldown -= 1
            if self.summon_cooldown > 0:
                self.summon_cooldown -= 1
            if self.charge_cooldown > 0:
                self.charge_cooldown -= 1
            if self.mimic_timer > 0:
                self.mimic_timer -= 1
                if self.mimic_timer == 0 and self.mimic_original:
                    self.role = "mimic"
                    self.speed = MIMIC_SPEED
            if self.invisible:
                self.invis_timer -= 1
                if self.invis_timer <= 0:
                    self.invisible = False
                    self.invis_cooldown = NINJA_INVIS_COOLDOWN
            if self.role == "swordsman":
                self.sword_angle += SWORD_SPIN_SPEED
            if self.role == "chainsaw":
                self.chainsaw_angle += CHAINSAW_SPIN_SPEED
            if self.wall_cooldown > 0:
                self.wall_cooldown -= 1
            return

        # apply slow debuff
        if self.slow_timer > 0:
            self.x += self.vx * ICE_SLOW_FACTOR
            self.y += self.vy * ICE_SLOW_FACTOR
            self.slow_timer -= 1
        else:
            self.x += self.vx
            self.y += self.vy

        bounced = False
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx)
            bounced = True
        if self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -abs(self.vx)
            bounced = True
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = abs(self.vy)
            bounced = True
        if self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy = -abs(self.vy)
            bounced = True

        if bounced:
            angle = math.atan2(self.vy, self.vx)
            angle += random.uniform(-0.4, 0.4)
            spd = math.sqrt(self.vx ** 2 + self.vy ** 2)
            self.vx = math.cos(angle) * spd
            self.vy = math.sin(angle) * spd
            self.bounce_timer = WALL_BOUNCE_FRAMES

        if self.bounce_timer > 0:
            self.bounce_timer -= 1
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        if self.spear_cooldown > 0:
            self.spear_cooldown -= 1
        if self.trap_cooldown > 0:
            self.trap_cooldown -= 1
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1
        if self.heal_cooldown > 0:
            self.heal_cooldown -= 1
        if self.invis_cooldown > 0:
            self.invis_cooldown -= 1
        if self.sniper_cooldown > 0:
            self.sniper_cooldown -= 1
        if self.archer_cooldown > 0:
            self.archer_cooldown -= 1
        if self.wizard_cooldown > 0:
            self.wizard_cooldown -= 1
        if self.assassin_dash_cooldown > 0:
            self.assassin_dash_cooldown -= 1
        if self.necro_cooldown > 0:
            self.necro_cooldown -= 1
        if self.ice_cooldown > 0:
            self.ice_cooldown -= 1
        if self.summon_cooldown > 0:
            self.summon_cooldown -= 1
        if self.charge_cooldown > 0:
            self.charge_cooldown -= 1
        if self.mimic_timer > 0:
            self.mimic_timer -= 1
            if self.mimic_timer == 0 and self.mimic_original:
                # revert to mimic base — ready to copy again
                self.role = "mimic"
                self.speed = MIMIC_SPEED
        # ninja auto-invisibility
        if self.role == "ninja":
            if self.invisible:
                self.invis_timer -= 1
                if self.invis_timer <= 0:
                    self.invisible = False
                    self.invis_cooldown = NINJA_INVIS_COOLDOWN
            elif self.invis_cooldown <= 0:
                self.invisible = True
                self.invis_timer = NINJA_INVIS_DURATION
        if self.role == "swordsman":
            self.sword_angle += SWORD_SPIN_SPEED
        if self.role == "chainsaw":
            self.chainsaw_angle += CHAINSAW_SPIN_SPEED
        if self.wall_cooldown > 0:
            self.wall_cooldown -= 1

    def take_damage(self, amount):
        """Apply damage with armor reduction for tank."""
        if self.role == "tank":
            amount = max(1, int(amount * TANK_ARMOR))
        self.hp -= amount

    def apply_knockback(self, nx, ny, strength):
        if self.pinned_timer > 0 or self.carried_by_spear:
            return
        if self.trapped_in is not None:
            return
        if self.role == "tank":
            strength *= 0.4  # tanks are hard to push
        self.vx = nx * strength
        self.vy = ny * strength
        self.bounce_timer = COLLISION_BOUNCE_FRAMES

    def sword_tip(self):
        return (self.x + math.cos(self.sword_angle) * (self.radius + SWORD_LENGTH),
                self.y + math.sin(self.sword_angle) * (self.radius + SWORD_LENGTH))

    def chainsaw_tip(self):
        return (self.x + math.cos(self.chainsaw_angle) * (self.radius + CHAINSAW_LENGTH),
                self.y + math.sin(self.chainsaw_angle) * (self.radius + CHAINSAW_LENGTH))

    def try_place_wall(self, target, walls, all_balls):
        if self.role != "fortifier" or self.wall_cooldown > 0 or target is None:
            return
        allies_hurt = [a for a in all_balls if a is not self and a.alive
                       and a.team_id == self.team_id and a.hp < 100
                       and a.role not in ("fortifier", "shield")]
        if allies_hurt:
            # protective wall — place between weakest ally and nearest enemy
            weakest = min(allies_hurt, key=lambda a: a.hp)
            enemies = [e for e in all_balls if e.alive and e.team_id != self.team_id]
            if not enemies:
                return
            threat = min(enemies, key=lambda e: dist(weakest.x, weakest.y, e.x, e.y))
            wx = (weakest.x + threat.x) / 2
            wy = (weakest.y + threat.y) / 2
            wall_angle = math.atan2(threat.y - weakest.y, threat.x - weakest.x) + math.pi / 2
            wx = max(FORT_WALL_WIDTH // 2, min(WIDTH - FORT_WALL_WIDTH // 2, wx))
            wy = max(FORT_WALL_WIDTH // 2, min(HEIGHT - FORT_WALL_WIDTH // 2, wy))
            walls.append(FortWall(wx, wy, wall_angle, self.team_id, self.color, explosive=False))
        else:
            # explosive wall — place near enemy
            dx = target.x - self.x
            dy = target.y - self.y
            d = max(math.sqrt(dx * dx + dy * dy), 0.01)
            place_dist = min(d * 0.5, BALL_RADIUS * 3)
            wx = self.x + (dx / d) * place_dist
            wy = self.y + (dy / d) * place_dist
            wall_angle = math.atan2(dy, dx) + math.pi / 2
            wx = max(FORT_WALL_WIDTH // 2, min(WIDTH - FORT_WALL_WIDTH // 2, wx))
            wy = max(FORT_WALL_WIDTH // 2, min(HEIGHT - FORT_WALL_WIDTH // 2, wy))
            blast_dir = (dx / d, dy / d)  # explodes toward target
            walls.append(FortWall(wx, wy, wall_angle, self.team_id, self.color, explosive=True, blast_dir=blast_dir))
        self.wall_cooldown = FORT_WALL_COOLDOWN

    def try_throw_spear(self, target, spears):
        if self.role != "spearman" or self.spear_cooldown > 0 or target is None:
            return
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        spears.append(Spear(self.x, self.y, dx / d * SPEAR_SPEED, dy / d * SPEAR_SPEED,
                            self.team_id, self.color))
        self.spear_cooldown = SPEAR_COOLDOWN

    def try_place_trap(self, target, traps):
        if self.role != "trapper" or self.trap_cooldown > 0 or target is None:
            return
        # place trap between self and target with imperfect aim
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        # add aim offset — trap lands off-target sometimes
        angle = math.atan2(dy, dx) + random.uniform(-0.5, 0.5)
        place_dist = min(d * 0.5, BALL_RADIUS * 3) + random.uniform(-20, 20)
        place_dist = max(BALL_RADIUS * 2, place_dist)
        tx = self.x + math.cos(angle) * place_dist
        ty = self.y + math.sin(angle) * place_dist
        # clamp to arena
        tx = max(TRAP_RADIUS, min(WIDTH - TRAP_RADIUS, tx))
        ty = max(TRAP_RADIUS, min(HEIGHT - TRAP_RADIUS, ty))
        traps.append(Trap(tx, ty, self.team_id, self.color))
        self.trap_cooldown = TRAP_COOLDOWN

    def aim_shield(self, all_balls):
        if self.role != "shield":
            return
        enemies = [e for e in all_balls if e.alive and e.team_id != self.team_id
                   and not (e.role == "ninja" and e.invisible)]
        if enemies:
            nearest = min(enemies, key=lambda e: dist(self.x, self.y, e.x, e.y))
            target_angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
            # smoothly rotate toward target
            diff = (target_angle - self.shield_angle + math.pi) % (2 * math.pi) - math.pi
            self.shield_angle += diff * 0.15

    def is_angle_in_shield(self, angle, attacker_role=None):
        """Check if an angle from ball center falls within any shield arc.
        50% chance the hit breaks through. Snipers always bypass shields."""
        if self.role != "shield":
            return False
        if attacker_role == "sniper":
            return False  # snipers bypass shields
        for i in range(SHIELD_COUNT):
            center = self.shield_angle + i * (2 * math.pi / SHIELD_COUNT)
            diff = (angle - center + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) <= SHIELD_ARC / 2:
                if random.random() < 0.50:
                    return False  # shield pierced
                return True
        return False

    def try_heal(self, all_balls):
        if self.role != "healer" or self.heal_cooldown > 0:
            return
        healed = False
        # heal nearby allies
        for ally in all_balls:
            if ally is self or ally.team_id != self.team_id or not ally.alive:
                continue
            if dist(self.x, self.y, ally.x, ally.y) <= HEAL_RANGE:
                if ally.hp < ally.max_hp:
                    ally.hp = min(ally.max_hp, ally.hp + HEAL_AMOUNT)
                    healed = True
        if healed:
            self.heal_cooldown = HEAL_COOLDOWN

    def try_fire_bullet(self, target, bullets):
        if self.role != "sniper" or self.sniper_cooldown > 0 or target is None:
            return
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        bullets.append(Bullet(self.x, self.y, dx / d * SNIPER_BULLET_SPEED,
                              dy / d * SNIPER_BULLET_SPEED, self.team_id, self.color))
        self.sniper_cooldown = SNIPER_COOLDOWN

    def try_fire_arrow(self, target, arrows):
        if self.role != "archer" or self.archer_cooldown > 0 or target is None:
            return
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        arrows.append(Arrow(self.x, self.y, dx / d * ARCHER_ARROW_SPEED,
                            dy / d * ARCHER_ARROW_SPEED, self.team_id, self.color))
        self.archer_cooldown = ARCHER_COOLDOWN

    def try_cast_orb(self, target, orbs):
        if self.role != "wizard" or self.wizard_cooldown > 0 or target is None:
            return
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        orbs.append(MagicOrb(self.x, self.y, dx / d * WIZARD_ORB_SPEED,
                             dy / d * WIZARD_ORB_SPEED, self.team_id, self.color))
        self.wizard_cooldown = WIZARD_COOLDOWN

    def try_fire_ice_bolt(self, target, ice_bolts):
        if self.role != "ice_mage" or self.ice_cooldown > 0 or target is None:
            return
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        ice_bolts.append(IceBolt(self.x, self.y, dx / d * ICE_BOLT_SPEED,
                                 dy / d * ICE_BOLT_SPEED, self.team_id, self.color))
        self.ice_cooldown = ICE_MAGE_COOLDOWN

    def try_drop_bomb(self, target, bombs):
        if self.role != "bomber" or self.bomb_cooldown > 0 or target is None:
            return
        # drop bomb slightly towards the target
        dx = target.x - self.x
        dy = target.y - self.y
        d = max(math.sqrt(dx * dx + dy * dy), 0.01)
        drop_dist = min(d * 0.3, BALL_RADIUS * 2)
        bx = self.x + (dx / d) * drop_dist
        by = self.y + (dy / d) * drop_dist
        bx = max(10, min(WIDTH - 10, bx))
        by = max(10, min(HEIGHT - 10, by))
        bombs.append(Bomb(bx, by, self.team_id, self.color))
        self.bomb_cooldown = BOMB_COOLDOWN

    def draw(self, surface):
        if not self.alive:
            return

        # ninja invisible — draw faint outline only
        if self.role == "ninja" and self.invisible:
            faint = tuple(max(0, v // 4) for v in self.color)
            pygame.draw.circle(surface, faint, (int(self.x), int(self.y)), self.radius, 1)
            return

        # pin indicator
        if self.pinned_timer > 0:
            pygame.draw.circle(surface, (150, 50, 50), (int(self.x), int(self.y)),
                               self.radius + 4, 2)

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

        # HP number on ball
        hp_text = small_font.render(str(max(0, self.hp)), True, (255, 255, 255))
        surface.blit(hp_text, (self.x - hp_text.get_width() // 2, self.y - hp_text.get_height() // 2))

        if self.role == "zombie":
            self._draw_zombie_arms(surface)

        if self.role == "swordsman":
            self._draw_sword(surface)

        if self.role == "berserker":
            # rage glow — redder and bigger outline as HP drops
            mult = self.rage_multiplier
            if mult > 1.1:
                intensity = min(255, int((mult - 1.0) * 180))
                pygame.draw.circle(surface, (intensity, 0, 0),
                                   (int(self.x), int(self.y)), self.radius + 3 + int(mult * 2), 2)

        if self.role == "shield":
            # draw rotating shield arcs
            r = self.radius + 12
            for i in range(SHIELD_COUNT):
                a = self.shield_angle + i * (2 * math.pi / SHIELD_COUNT)
                segments = 5
                for j in range(segments):
                    a1 = a - SHIELD_ARC / 2 + j * SHIELD_ARC / segments
                    a2 = a - SHIELD_ARC / 2 + (j + 1) * SHIELD_ARC / segments
                    x1 = self.x + math.cos(a1) * r
                    y1 = self.y + math.sin(a1) * r
                    x2 = self.x + math.cos(a2) * r
                    y2 = self.y + math.sin(a2) * r
                    pygame.draw.line(surface, (160, 100, 40), (int(x1), int(y1)), (int(x2), int(y2)), 4)

        if self.role == "healer":
            # green cross on ball
            cx, cy = int(self.x), int(self.y)
            s = self.radius // 3
            pygame.draw.line(surface, (0, 255, 0), (cx - s, cy), (cx + s, cy), 3)
            pygame.draw.line(surface, (0, 255, 0), (cx, cy - s), (cx, cy + s), 3)
            # heal range ring (always visible)
            pygame.draw.circle(surface, (0, 100, 0), (cx, cy), HEAL_RANGE, 1)

        if self.role == "spearman":
            self._draw_spearman_spear(surface)

        if self.role == "trapper":
            self._draw_trapper_jaws(surface)

        if self.role == "bomber":
            self._draw_bomber_fuse(surface)

        if self.role == "sniper":
            self._draw_sniper_scope(surface)

        if self.role == "chainsaw":
            self._draw_chainsaw(surface)

        if self.role == "fortifier":
            self._draw_fortifier(surface)

        if self.role == "vampire":
            self._draw_vampire(surface)

        if self.role == "archer":
            self._draw_archer(surface)

        if self.role == "wizard":
            self._draw_wizard(surface)

        if self.role == "tank":
            self._draw_tank(surface)

        if self.role == "assassin":
            self._draw_assassin(surface)

        if self.role == "necromancer":
            self._draw_necromancer(surface)

        if self.role == "ice_mage":
            self._draw_ice_mage(surface)

        if self.role == "summoner":
            self._draw_summoner(surface)

        if self.role == "mirror":
            self._draw_mirror(surface)

        if self.role == "charger":
            self._draw_charger(surface)

        if self.role == "mimic" and not self.mimic_display_role:
            self._draw_mimic(surface)

        if self.mimic_original and self.mimic_display_role and self.role != "mimic":
            # draw a small "M" indicator so you know it's a mimic
            m_text = small_font.render("M", True, (255, 255, 0))
            surface.blit(m_text, (int(self.x) + self.radius - 2, int(self.y) - self.radius - 10))

        # slow visual overlay
        if self.slow_timer > 0:
            pygame.draw.circle(surface, (100, 180, 255),
                               (int(self.x), int(self.y)), self.radius + 3, 1)

        # health bar
        bar_w = 40
        bar_h = 5
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.radius - 12
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        hp_w = max(0, (self.hp / self.max_hp) * bar_w)
        bar_color = (0, 200, 0) if self.hp > 40 else (200, 200, 0) if self.hp > 20 else (200, 0, 0)
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, hp_w, bar_h))

    def _draw_sword(self, surface):
        angle = self.sword_angle
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        perp_x, perp_y = -sin_a, cos_a

        bx = self.x + cos_a * self.radius
        by = self.y + sin_a * self.radius

        handle_len = 8
        hx = bx + cos_a * handle_len
        hy = by + sin_a * handle_len
        pygame.draw.line(surface, (139, 90, 43), (int(bx), int(by)), (int(hx), int(hy)), 4)

        guard_w = 7
        g1 = (int(hx + perp_x * guard_w), int(hy + perp_y * guard_w))
        g2 = (int(hx - perp_x * guard_w), int(hy - perp_y * guard_w))
        pygame.draw.line(surface, (160, 160, 170), g1, g2, 3)

        blade_len = SWORD_LENGTH - handle_len - 2
        blade_w = 3
        bsx, bsy = hx + cos_a * 2, hy + sin_a * 2
        bex = bsx + cos_a * blade_len
        bey = bsy + sin_a * blade_len

        pts = [
            (bsx + perp_x * blade_w, bsy + perp_y * blade_w),
            (bex + perp_x * 1, bey + perp_y * 1),
            (bex - perp_x * 1, bey - perp_y * 1),
            (bsx - perp_x * blade_w, bsy - perp_y * blade_w),
        ]
        pts_i = [(int(p[0]), int(p[1])) for p in pts]
        pygame.draw.polygon(surface, (190, 195, 210), pts_i)
        pygame.draw.polygon(surface, (220, 225, 235), pts_i, 1)

        tip_x = bex + cos_a * 4
        tip_y = bey + sin_a * 4
        pygame.draw.polygon(surface, (210, 215, 225), [
            (int(bex + perp_x * 1), int(bey + perp_y * 1)),
            (int(bex - perp_x * 1), int(bey - perp_y * 1)),
            (int(tip_x), int(tip_y))
        ])

    def _draw_zombie_arms(self, surface):
        # face direction of movement, or default forward
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            face = math.atan2(self.vy, self.vx)
        else:
            face = 0.0
        arm_color = tuple(max(0, v - 40) for v in self.color)
        r = self.radius
        arm_len = r * 0.4
        hand_len = arm_len * 0.35

        for side in (-1, 1):
            # shoulder: perpendicular to facing direction
            shoulder_angle = face + side * 1.3
            sx = self.x + math.cos(shoulder_angle) * r
            sy = self.y + math.sin(shoulder_angle) * r

            # stubby upper arm reaches forward
            elbow_angle = face + side * 0.4
            ex = sx + math.cos(elbow_angle) * arm_len
            ey = sy + math.sin(elbow_angle) * arm_len

            # hand/fingers angle inward (grabby)
            hand_angle = face - side * 0.3
            hx = ex + math.cos(hand_angle) * hand_len
            hy = ey + math.sin(hand_angle) * hand_len

            # draw chunky arm segments
            pygame.draw.line(surface, arm_color, (int(sx), int(sy)), (int(ex), int(ey)), 5)
            pygame.draw.line(surface, arm_color, (int(ex), int(ey)), (int(hx), int(hy)), 4)

            # three little fingers
            for f in (-0.5, 0.0, 0.5):
                finger_angle = hand_angle + f * 0.6
                fx = hx + math.cos(finger_angle) * (hand_len * 0.35)
                fy = hy + math.sin(finger_angle) * (hand_len * 0.4)
                pygame.draw.line(surface, arm_color, (int(hx), int(hy)), (int(fx), int(fy)), 1)

    def _draw_spearman_spear(self, surface):
        # small spear held alongside the ball, pointing in movement direction
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            face = math.atan2(self.vy, self.vx)
        else:
            face = 0.0
        r = self.radius
        # shaft starts at the side, extends forward
        cos_f, sin_f = math.cos(face), math.sin(face)
        perp_x, perp_y = -sin_f, cos_f
        # offset to the right side
        sx = self.x + perp_x * r * 0.7 - cos_f * r * 0.5
        sy = self.y + perp_y * r * 0.7 - sin_f * r * 0.5
        ex = sx + cos_f * r * 1.8
        ey = sy + sin_f * r * 1.8
        # wooden shaft
        pygame.draw.line(surface, (160, 120, 60), (int(sx), int(sy)), (int(ex), int(ey)), 3)
        # spearhead triangle
        tip_x = ex + cos_f * 6
        tip_y = ey + sin_f * 6
        p1 = (int(ex + perp_x * 3), int(ey + perp_y * 3))
        p2 = (int(ex - perp_x * 3), int(ey - perp_y * 3))
        p3 = (int(tip_x), int(tip_y))
        pygame.draw.polygon(surface, (180, 180, 190), [p1, p2, p3])

    def _draw_trapper_jaws(self, surface):
        # purple magic wisps orbiting the ball
        import time
        t = time.time() * 2.0
        cx, cy = self.x, self.y
        r = self.radius
        num_wisps = 5
        for i in range(num_wisps):
            base_angle = i * 2 * math.pi / num_wisps + t
            # wisp floats at varying distance
            wisp_r = r + 6 + math.sin(t * 1.5 + i * 1.2) * 4
            wx = cx + math.cos(base_angle) * wisp_r
            wy = cy + math.sin(base_angle) * wisp_r
            # draw a short fading trail behind the wisp
            for j in range(3):
                trail_angle = base_angle - (j + 1) * 0.2
                trail_r = wisp_r - j * 1.5
                tx = cx + math.cos(trail_angle) * trail_r
                ty = cy + math.sin(trail_angle) * trail_r
                alpha = 180 - j * 60
                pygame.draw.circle(surface, (160, 60, max(0, alpha)), (int(tx), int(ty)), max(1, 2 - j))
            # bright wisp head
            pygame.draw.circle(surface, (200, 100, 255), (int(wx), int(wy)), 3)
            pygame.draw.circle(surface, (255, 180, 255), (int(wx), int(wy)), 1)

    def _draw_bomber_fuse(self, surface):
        # lit fuse sticking out the top with a flickering spark
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # fuse line curving up from top
        fuse_base = (cx + 2, cy - r + 2)
        fuse_mid = (cx + 5, cy - r - 5)
        fuse_tip = (cx + 3, cy - r - 10)
        pygame.draw.line(surface, (80, 60, 40), fuse_base, fuse_mid, 2)
        pygame.draw.line(surface, (80, 60, 40), fuse_mid, fuse_tip, 2)
        # flickering spark at tip
        import time
        flicker = int(time.time() * 10) % 3
        spark_colors = [(255, 200, 50), (255, 150, 30), (255, 255, 100)]
        pygame.draw.circle(surface, spark_colors[flicker], fuse_tip, 3)
        # small bomb icon on ball — filled dark circle with highlight
        pygame.draw.circle(surface, (50, 40, 30), (cx, cy), r // 3)
        pygame.draw.circle(surface, (90, 70, 50), (cx - 2, cy - 2), r // 6)

    def _draw_sniper_scope(self, surface):
        # bold crosshair/scope overlay on the ball
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        scope_r = r + 6
        # outer scope ring
        pygame.draw.circle(surface, (255, 50, 50), (cx, cy), scope_r, 2)
        # crosshair lines extending past the ball
        gap = 4
        pygame.draw.line(surface, (255, 50, 50), (cx - scope_r, cy), (cx - gap, cy), 2)
        pygame.draw.line(surface, (255, 50, 50), (cx + gap, cy), (cx + scope_r, cy), 2)
        pygame.draw.line(surface, (255, 50, 50), (cx, cy - scope_r), (cx, cy - gap), 2)
        pygame.draw.line(surface, (255, 50, 50), (cx, cy + gap), (cx, cy + scope_r), 2)
        # center dot
        pygame.draw.circle(surface, (255, 50, 50), (cx, cy), 2)

    def _draw_chainsaw(self, surface):
        angle = self.chainsaw_angle
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        r = self.radius
        # bar extending from ball
        bx = self.x + cos_a * r
        by = self.y + sin_a * r
        ex = self.x + cos_a * (r + CHAINSAW_LENGTH)
        ey = self.y + sin_a * (r + CHAINSAW_LENGTH)
        # chainsaw bar (dark gray)
        pygame.draw.line(surface, (100, 100, 110), (int(bx), int(by)), (int(ex), int(ey)), 5)
        # teeth along the bar (jagged edge)
        perp_x, perp_y = -sin_a, cos_a
        num_teeth = 6
        for i in range(num_teeth):
            t = (i + 0.5) / num_teeth
            tx = bx + (ex - bx) * t
            ty = by + (ey - by) * t
            side = 1 if i % 2 == 0 else -1
            tooth_x = tx + perp_x * 4 * side
            tooth_y = ty + perp_y * 4 * side
            pygame.draw.line(surface, (200, 200, 50), (int(tx), int(ty)),
                             (int(tooth_x), int(tooth_y)), 2)
        # orange tip
        pygame.draw.circle(surface, (220, 140, 30), (int(ex), int(ey)), 3)

    def _draw_fortifier(self, surface):
        # small wall/brick icon on the ball
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # draw small brick pattern
        bw, bh = r // 2, r // 4
        # top row — 2 bricks
        pygame.draw.rect(surface, (160, 120, 80), (cx - bw, cy - bh - 1, bw, bh))
        pygame.draw.rect(surface, (140, 100, 60), (cx, cy - bh - 1, bw, bh))
        # bottom row — offset
        pygame.draw.rect(surface, (140, 100, 60), (cx - bw + bw // 2, cy + 1, bw, bh))
        # outlines
        pygame.draw.rect(surface, (100, 80, 50), (cx - bw, cy - bh - 1, bw, bh), 1)
        pygame.draw.rect(surface, (100, 80, 50), (cx, cy - bh - 1, bw, bh), 1)
        pygame.draw.rect(surface, (100, 80, 50), (cx - bw + bw // 2, cy + 1, bw, bh), 1)

    def _draw_vampire(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # two fangs hanging from upper area
        fang_w = 2
        fang_h = r // 2
        for side in (-1, 1):
            fx = cx + side * (r // 3)
            fy = cy + 2
            # white fang triangle
            pygame.draw.polygon(surface, (240, 240, 240), [
                (fx - fang_w, fy),
                (fx + fang_w, fy),
                (fx, fy + fang_h)
            ])
        # red glow ring (blood aura)
        pygame.draw.circle(surface, (150, 0, 0), (cx, cy), r + 4, 1)
        # small red eyes
        pygame.draw.circle(surface, (255, 0, 0), (cx - r // 4, cy - r // 4), 2)
        pygame.draw.circle(surface, (255, 0, 0), (cx + r // 4, cy - r // 4), 2)

    def _draw_archer(self, surface):
        # bow on the side, quiver of arrows on back
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            face = math.atan2(self.vy, self.vx)
        else:
            face = 0.0
        cx, cy = self.x, self.y
        r = self.radius
        cos_f, sin_f = math.cos(face), math.sin(face)
        perp_x, perp_y = -sin_f, cos_f
        # bow — arc on the right side facing forward
        bow_cx = cx + perp_x * r * 0.8
        bow_cy = cy + perp_y * r * 0.8
        bow_r = r * 0.7
        # draw bow arc (semicircle facing forward)
        segments = 6
        bow_points = []
        for i in range(segments + 1):
            a = face - 0.8 + (1.6 * i / segments)
            bx = bow_cx + math.cos(a) * bow_r
            by = bow_cy + math.sin(a) * bow_r
            bow_points.append((int(bx), int(by)))
        for i in range(len(bow_points) - 1):
            pygame.draw.line(surface, (139, 90, 43), bow_points[i], bow_points[i + 1], 3)
        # bowstring
        pygame.draw.line(surface, (200, 200, 200), bow_points[0], bow_points[-1], 1)
        # quiver on back (3 small arrows)
        back_x = cx - cos_f * r * 0.6
        back_y = cy - sin_f * r * 0.6
        for i in range(3):
            offset = (i - 1) * 3
            qx = back_x + perp_x * offset
            qy = back_y + perp_y * offset
            tip_x = qx - cos_f * r * 0.5
            tip_y = qy - sin_f * r * 0.5
            pygame.draw.line(surface, (160, 120, 60), (int(qx), int(qy)),
                             (int(tip_x), int(tip_y)), 1)
            # tiny arrowhead
            pygame.draw.circle(surface, (200, 200, 210), (int(tip_x), int(tip_y)), 1)

    def _draw_wizard(self, surface):
        # wizard hat and staff
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # pointy hat on top
        hat_base_l = (cx - r // 2, cy - r + 2)
        hat_base_r = (cx + r // 2, cy - r + 2)
        hat_tip = (cx, cy - r - 12)
        pygame.draw.polygon(surface, (100, 40, 180), [hat_base_l, hat_base_r, hat_tip])
        pygame.draw.polygon(surface, (140, 70, 220), [hat_base_l, hat_base_r, hat_tip], 1)
        # hat brim
        pygame.draw.line(surface, (80, 30, 160),
                         (cx - r // 2 - 3, cy - r + 2), (cx + r // 2 + 3, cy - r + 2), 2)
        # star on hat
        pygame.draw.circle(surface, (255, 220, 100), (cx, cy - r - 4), 2)
        # purple aura ring
        pygame.draw.circle(surface, (140, 50, 220), (cx, cy), r + 5, 1)

    def _draw_tank(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # thick armor ring
        pygame.draw.circle(surface, (120, 120, 140), (cx, cy), r + 3, 3)
        # armor plates (4 segments around the ball)
        for i in range(4):
            a = i * math.pi / 2 + 0.4
            x1 = cx + int(math.cos(a) * (r + 1))
            y1 = cy + int(math.sin(a) * (r + 1))
            x2 = cx + int(math.cos(a + 0.8) * (r + 1))
            y2 = cy + int(math.sin(a + 0.8) * (r + 1))
            pygame.draw.line(surface, (160, 160, 180), (x1, y1), (x2, y2), 4)
        # small chevron/arrow emblem on center
        pygame.draw.line(surface, (200, 200, 220), (cx - 4, cy - 2), (cx, cy - 5), 2)
        pygame.draw.line(surface, (200, 200, 220), (cx, cy - 5), (cx + 4, cy - 2), 2)

    def _draw_assassin(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # dagger held in front
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            face = math.atan2(self.vy, self.vx)
        else:
            face = 0.0
        cos_f, sin_f = math.cos(face), math.sin(face)
        # blade
        bx = self.x + cos_f * r
        by = self.y + sin_f * r
        tip_x = bx + cos_f * r * 0.6
        tip_y = by + sin_f * r * 0.6
        pygame.draw.line(surface, (200, 200, 220), (int(bx), int(by)), (int(tip_x), int(tip_y)), 2)
        # dagger handle
        hx = bx - cos_f * 4
        hy = by - sin_f * 4
        pygame.draw.line(surface, (100, 60, 30), (int(hx), int(hy)), (int(bx), int(by)), 3)
        # dash trail effect when dashing
        if self.assassin_dashing > 0:
            for i in range(3):
                trail_x = cx - int(cos_f * (i + 1) * 8)
                trail_y = cy - int(sin_f * (i + 1) * 8)
                alpha = 150 - i * 50
                pygame.draw.circle(surface, (alpha, alpha // 2, alpha // 2),
                                   (trail_x, trail_y), r - i * 2, 1)
        # dark cloak outline
        pygame.draw.circle(surface, (40, 40, 50), (cx, cy), r + 2, 1)

    def _draw_necromancer(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # skull face
        # eye sockets
        pygame.draw.circle(surface, (0, 0, 0), (cx - r // 4, cy - r // 6), r // 5)
        pygame.draw.circle(surface, (0, 0, 0), (cx + r // 4, cy - r // 6), r // 5)
        # green glowing eyes
        pygame.draw.circle(surface, (0, 220, 60), (cx - r // 4, cy - r // 6), r // 8)
        pygame.draw.circle(surface, (0, 220, 60), (cx + r // 4, cy - r // 6), r // 8)
        # nose hole
        pygame.draw.polygon(surface, (0, 0, 0), [
            (cx - 2, cy + 1), (cx + 2, cy + 1), (cx, cy + 4)
        ])
        # teeth line
        for i in range(-2, 3):
            tx = cx + i * 3
            pygame.draw.line(surface, (200, 200, 200), (tx, cy + r // 4), (tx, cy + r // 4 + 3), 1)
        # dark red aura
        pygame.draw.circle(surface, (150, 30, 30), (cx, cy), r + 5, 1)
        # raise range ring (red)
        pygame.draw.circle(surface, (100, 20, 20), (cx, cy), int(NECRO_RAISE_RANGE), 1)

    def _draw_ice_mage(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # ice crystal crown on top
        for i in range(3):
            bx = cx + (i - 1) * (r // 3)
            by = cy - r + 2
            tip_y = by - 8 - (2 if i == 1 else 0)  # center crystal taller
            pygame.draw.polygon(surface, (140, 200, 255), [
                (bx - 3, by), (bx + 3, by), (bx, tip_y)
            ])
            pygame.draw.polygon(surface, (200, 230, 255), [
                (bx - 3, by), (bx + 3, by), (bx, tip_y)
            ], 1)
        # frost aura ring
        pygame.draw.circle(surface, (100, 180, 255), (cx, cy), r + 5, 1)
        # snowflake dots orbiting
        import time
        t = time.time() * 1.5
        for i in range(4):
            a = t + i * math.pi / 2
            sx = cx + int(math.cos(a) * (r + 4))
            sy = cy + int(math.sin(a) * (r + 4))
            pygame.draw.circle(surface, (220, 240, 255), (sx, sy), 1)

    def _draw_summoner(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # glowing summoning circle
        pygame.draw.circle(surface, (255, 180, 50), (cx, cy), r + 6, 1)
        # orbiting star symbols
        import time
        t = time.time() * 2.0
        for i in range(3):
            a = t + i * 2 * math.pi / 3
            sx = cx + int(math.cos(a) * (r + 5))
            sy = cy + int(math.sin(a) * (r + 5))
            # tiny 4-point star
            for da in range(4):
                sa = da * math.pi / 2
                ex = sx + int(math.cos(sa) * 3)
                ey = sy + int(math.sin(sa) * 3)
                pygame.draw.line(surface, (255, 220, 100), (sx, sy), (ex, ey), 1)
        # minion count indicator
        self.minions = [m for m in self.minions if m.alive]
        count = len(self.minions)
        if count > 0:
            ct = small_font.render(f"{count}/{SUMMONER_MAX_MINIONS}", True, (255, 220, 100))
            surface.blit(ct, (cx - ct.get_width() // 2, cy + r + 6))

    def _draw_mirror(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # shiny reflective surface — bright white-silver ring
        pygame.draw.circle(surface, (220, 220, 240), (cx, cy), r + 2, 2)
        # inner shine highlight
        pygame.draw.circle(surface, (240, 240, 255), (cx - r // 4, cy - r // 4), r // 3, 1)
        # sparkle reflections rotating around
        import time
        t = time.time() * 3.0
        for i in range(6):
            a = t + i * math.pi / 3
            sx = cx + int(math.cos(a) * (r - 2))
            sy = cy + int(math.sin(a) * (r - 2))
            # alternating bright sparkles
            if i % 2 == 0:
                pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 2)
            else:
                pygame.draw.circle(surface, (200, 220, 255), (sx, sy), 1)

    def _draw_charger(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # bull horns
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            face = math.atan2(self.vy, self.vx)
        else:
            face = 0.0
        cos_f, sin_f = math.cos(face), math.sin(face)
        perp_x, perp_y = -sin_f, cos_f
        for side in (-1, 1):
            # horn base at top-sides
            hx = self.x + cos_f * r * 0.5 + perp_x * r * 0.6 * side
            hy = self.y + sin_f * r * 0.5 + perp_y * r * 0.6 * side
            # horn tip curves forward
            tip_x = hx + cos_f * r * 0.7 + perp_x * r * 0.3 * side
            tip_y = hy + sin_f * r * 0.7 + perp_y * r * 0.3 * side
            pygame.draw.line(surface, (200, 180, 140), (int(hx), int(hy)),
                             (int(tip_x), int(tip_y)), 3)
        # windup indicator — red pulsing ring
        if self.charge_windup > 0:
            pulse = 1.0 if self.charge_windup % 10 < 5 else 0.5
            pygame.draw.circle(surface, (int(255 * pulse), 0, 0), (cx, cy), r + 5, 2)
        # charge trail
        if self.charging > 0:
            for i in range(3):
                trail_x = cx - int(cos_f * (i + 1) * 10)
                trail_y = cy - int(sin_f * (i + 1) * 10)
                c = 200 - i * 60
                pygame.draw.circle(surface, (c, c // 2, 0), (trail_x, trail_y), r - i * 3, 1)

    def _draw_mimic(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        # question mark on the ball
        pygame.draw.circle(surface, (255, 255, 0), (cx + 1, cy - r // 4), r // 4, 1)
        pygame.draw.line(surface, (255, 255, 0), (cx + 1, cy - r // 4 + r // 4), (cx + 1, cy + 2), 1)
        pygame.draw.circle(surface, (255, 255, 0), (cx + 1, cy + r // 4), 1)
        # yellow shimmer ring
        pygame.draw.circle(surface, (255, 255, 100), (cx, cy), r + 3, 1)


# ── Helpers ─────────────────────────────────────────────────

def dist(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def resolve_collision(b1, b2):
    dx = b2.x - b1.x
    dy = b2.y - b1.y
    d = max(dist(b1.x, b1.y, b2.x, b2.y), 0.01)
    nx, ny = dx / d, dy / d

    overlap = (b1.radius + b2.radius) - d
    if overlap > 0:
        b1.x -= nx * overlap / 2
        b1.y -= ny * overlap / 2
        b2.x += nx * overlap / 2
        b2.y += ny * overlap / 2

    kb = 5.0 + random.uniform(-1.5, 2.0)
    angle_jitter = random.uniform(-0.3, 0.3)
    cos_j, sin_j = math.cos(angle_jitter), math.sin(angle_jitter)
    jnx = nx * cos_j - ny * sin_j
    jny = nx * sin_j + ny * cos_j

    b1.apply_knockback(-jnx, -jny, kb)
    b2.apply_knockback(jnx, jny, kb)


def point_near_segment(px, py, ax, ay, bx, by, threshold):
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq == 0:
        return dist(px, py, ax, ay) <= threshold
    t = max(0, min(1, (apx * abx + apy * aby) / ab_len_sq))
    closest_x = ax + t * abx
    closest_y = ay + t * aby
    return dist(px, py, closest_x, closest_y) <= threshold



def spawn_balls(team_configs):
    balls = []
    margin = BALL_RADIUS + SWORD_LENGTH + 10
    for cfg in team_configs:
        team_id = cfg["team_id"]
        color = TEAM_COLORS[team_id % len(TEAM_COLORS)]
        for _attempt in range(100):
            x = random.randint(margin, WIDTH - margin)
            y = random.randint(margin, HEIGHT - margin)
            ok = all(dist(x, y, b.x, b.y) > BALL_RADIUS * 4 for b in balls)
            if ok:
                break
        balls.append(Ball(x, y, color, team_id, cfg["role"]))
    return balls


# ── Game loop ───────────────────────────────────────────────

def game(team_configs, arena_idx=0):
    global WIDTH, HEIGHT, screen, BALL_RADIUS, SWORD_LENGTH, TRAP_RADIUS
    total_balls = len(team_configs)

    aw, ah, a_hint = ARENA_SIZES[arena_idx]
    WIDTH = aw
    HEIGHT = ah
    recording = a_hint == "Record"

    if total_balls > 6:
        BALL_RADIUS = max(12, BASE_BALL_RADIUS - (total_balls - 6) * 2)
    else:
        BALL_RADIUS = BASE_BALL_RADIUS
    SWORD_LENGTH = BALL_RADIUS * 2
    TRAP_RADIUS = BALL_RADIUS * 4
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    rec_proc = start_recording(WIDTH, HEIGHT) if recording else None

    balls = spawn_balls(team_configs)
    spears = []
    traps = []
    bombs = []
    bullets = []
    arrows = []
    orbs = []
    ice_bolts = []
    walls = []
    winner_team = None
    speed_options = [1, 2, 4, 10]
    speed_index = 0
    paused = False
    stale_timer = 0  # frames elapsed, triggers mutate at 2 min (7200 frames)
    STALE_THRESHOLD = 7200  # 2 minutes at 60fps

    def mutate_teams(balls_list):
        """Replace one unit from each team with a random melee unit."""
        melee_list = list(Ball.MELEE_ROLES)
        alive_teams = {}
        for b in balls_list:
            if b.alive:
                if b.team_id not in alive_teams:
                    alive_teams[b.team_id] = []
                alive_teams[b.team_id].append(b)
        for tid, members in alive_teams.items():
            # pick a random member to replace
            victim = random.choice(members)
            victim.alive = False
            victim.hp = 0
            # spawn a random melee unit at their position
            new_role = random.choice(melee_list)
            color = TEAM_COLORS[tid % len(TEAM_COLORS)]
            new_ball = Ball(victim.x, victim.y, color, tid, new_role)
            balls_list.append(new_ball)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    stop_recording(rec_proc)
                    game(team_configs, arena_idx)
                    return
                if event.key == pygame.K_m:
                    stop_recording(rec_proc)
                    return
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_1:
                    speed_index = 0
                if event.key == pygame.K_2:
                    speed_index = 1
                if event.key == pygame.K_3:
                    speed_index = 2
                if event.key == pygame.K_4:
                    speed_index = 3
                if event.key == pygame.K_x:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_CTRL and mods & pygame.KMOD_SHIFT:
                        stop_recording(rec_proc)
                        return
                    mutate_teams(balls)

        game_speed = speed_options[speed_index]

        if winner_team is not None:
            screen.fill((20, 20, 30))
            if winner_team == -1:
                text = big_font.render("Draw!", True, (255, 255, 255))
            else:
                color = TEAM_COLORS[winner_team % len(TEAM_COLORS)]
                text = big_font.render(f"Team {winner_team + 1} Wins!", True, color)
            r1 = font.render("R = Rematch  |  M = Menu", True, (180, 180, 180))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(r1, (WIDTH // 2 - r1.get_width() // 2, HEIGHT // 2 + 30))
            pygame.display.flip()
            if rec_proc:
                record_frame(rec_proc, screen)
            clock.tick(60)
            continue

        for _tick in range(game_speed):
            if winner_team is not None or paused:
                break

            # stale match timer — mutate after 2 minutes
            stale_timer += 1
            if stale_timer >= STALE_THRESHOLD:
                mutate_teams(balls)
                stale_timer = 0

            alive_balls = [b for b in balls if b.alive]

            # AI + movement + abilities
            for b in alive_balls:
                target = b.find_target(alive_balls)
                b.seek(target, alive_balls)
                b.move()
                b.try_throw_spear(target, spears)
                b.try_place_trap(target, traps)
                b.try_drop_bomb(target, bombs)
                b.try_heal(alive_balls)
                b.aim_shield(alive_balls)
                b.try_fire_bullet(target, bullets)
                b.try_fire_arrow(target, arrows)
                b.try_cast_orb(target, orbs)
                b.try_fire_ice_bolt(target, ice_bolts)
                b.try_place_wall(target, walls, alive_balls)

            # summoner spawns minions
            for b in alive_balls:
                if b.role != "summoner" or b.summon_cooldown > 0:
                    continue
                # clean dead minions from list
                b.minions = [m for m in b.minions if m.alive]
                if len(b.minions) >= SUMMONER_MAX_MINIONS:
                    continue
                # spawn a minion near the summoner
                angle = random.uniform(0, 2 * math.pi)
                mx = b.x + math.cos(angle) * (b.radius * 2.5)
                my = b.y + math.sin(angle) * (b.radius * 2.5)
                mx = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, mx))
                my = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, my))
                minion = Ball(mx, my, b.color, b.team_id, "zombie")
                minion.hp = SUMMONER_MINION_HP
                minion.max_hp = SUMMONER_MINION_HP
                minion.radius = max(8, int(BALL_RADIUS * SUMMONER_MINION_RADIUS_SCALE))
                minion.is_minion = True
                balls.append(minion)
                b.minions.append(minion)
                b.summon_cooldown = SUMMONER_COOLDOWN

            # move spears
            for s in spears:
                if s.alive:
                    s.move()

            # spear hit detection
            for s in spears:
                if not s.alive or s.carried_ball is not None:
                    continue
                for b in alive_balls:
                    if b.team_id == s.team_id or b.carried_by_spear:
                        continue
                    if dist(s.x, s.y, b.x, b.y) <= b.radius + 5:
                        # mirror reflects spears
                        if b.role == "mirror":
                            s.dx = -s.dx
                            s.dy = -s.dy
                            s.angle = math.atan2(s.dy, s.dx)
                            s.team_id = b.team_id
                            s.x += s.dx * 2
                            s.y += s.dy * 2
                            break
                        # shield blocks spears
                        if b.role == "shield":
                            angle = math.atan2(s.y - b.y, s.x - b.x)
                            if b.is_angle_in_shield(angle):
                                s.alive = False
                                break
                        b.take_damage(SPEAR_DAMAGE)
                        # free from trap if trapped
                        if b.trapped_in is not None:
                            b.trapped_in.captured_ball = None
                            b.trapped_in.alive = False
                            b.trapped_in = None
                        b.carried_by_spear = True
                        b.pinned_timer = 0
                        b.vx = 0
                        b.vy = 0
                        s.carried_ball = b
                        break

            # trap trigger detection + update
            for t in traps:
                if not t.alive:
                    continue
                # update captured ball bouncing
                if t.captured_ball is not None:
                    t.update()
                    continue
                # check if enemy walks into trap
                for b in alive_balls:
                    if b.team_id == t.team_id or b.trapped_in is not None or b.carried_by_spear or b.pinned_timer > 0:
                        continue
                    if dist(t.x, t.y, b.x, b.y) <= t.radius:
                        t.captured_ball = b
                        b.trapped_in = t
                        # give ball initial bounce velocity
                        angle = random.uniform(0, 2 * math.pi)
                        b.vx = math.cos(angle) * 4.0
                        b.vy = math.sin(angle) * 4.0
                        b.bounce_timer = 0
                        break

            # move bullets
            for bl in bullets:
                if bl.alive:
                    bl.move()

            # bullet hit detection
            for bl in bullets:
                if not bl.alive:
                    continue
                for b in alive_balls:
                    if b.team_id == bl.team_id:
                        continue
                    if dist(bl.x, bl.y, b.x, b.y) <= b.radius + 3:
                        # mirror reflects bullets
                        if b.role == "mirror":
                            bl.dx = -bl.dx
                            bl.dy = -bl.dy
                            bl.angle = math.atan2(bl.dy, bl.dx)
                            bl.team_id = b.team_id
                            bl.x += bl.dx * 2
                            bl.y += bl.dy * 2
                            break
                        # shield blocks bullets (snipers bypass)
                        if b.role == "shield":
                            angle = math.atan2(bl.y - b.y, bl.x - b.x)
                            if b.is_angle_in_shield(angle, attacker_role="sniper"):
                                bl.alive = False
                                break
                        b.take_damage(SNIPER_DAMAGE)
                        bl.alive = False
                        # small knockback
                        ddx = b.x - bl.x
                        ddy = b.y - bl.y
                        dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                        b.apply_knockback(ddx / dd, ddy / dd, 5.0)
                        break

            # move arrows
            for ar in arrows:
                if ar.alive:
                    ar.move()

            # arrow hit detection
            for ar in arrows:
                if not ar.alive:
                    continue
                for b in alive_balls:
                    if b.team_id == ar.team_id:
                        continue
                    if dist(ar.x, ar.y, b.x, b.y) <= b.radius + 4:
                        # mirror reflects arrows
                        if b.role == "mirror":
                            ar.dx = -ar.dx
                            ar.dy = -ar.dy
                            ar.angle = math.atan2(ar.dy, ar.dx)
                            ar.team_id = b.team_id
                            ar.x += ar.dx * 2
                            ar.y += ar.dy * 2
                            break
                        # shield blocks arrows
                        if b.role == "shield":
                            angle = math.atan2(ar.y - b.y, ar.x - b.x)
                            if b.is_angle_in_shield(angle):
                                ar.alive = False
                                break
                        b.take_damage(ARCHER_DAMAGE)
                        ar.alive = False
                        # small knockback
                        ddx = b.x - ar.x
                        ddy = b.y - ar.y
                        dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                        b.apply_knockback(ddx / dd, ddy / dd, 3.0)
                        break

            # move orbs + hit detection
            for orb in orbs:
                if not orb.alive:
                    continue
                orb.move()
                if orb.exploding:
                    continue
                # check if orb hits an enemy
                for b in alive_balls:
                    if b.team_id == orb.team_id:
                        continue
                    if dist(orb.x, orb.y, b.x, b.y) <= b.radius + 6:
                        # mirror reflects orbs
                        if b.role == "mirror":
                            orb.dx = -orb.dx
                            orb.dy = -orb.dy
                            orb.team_id = b.team_id
                            orb.x += orb.dx * 2
                            orb.y += orb.dy * 2
                            break
                        # shield blocks orbs
                        if b.role == "shield":
                            angle = math.atan2(orb.y - b.y, orb.x - b.x)
                            if b.is_angle_in_shield(angle):
                                orb.alive = False
                                break
                        # direct hit
                        b.take_damage(WIZARD_DAMAGE)
                        # explode — splash damage to nearby enemies
                        orb.exploding = True
                        for other in alive_balls:
                            if other is b or other.team_id == orb.team_id:
                                continue
                            if dist(orb.x, orb.y, other.x, other.y) <= WIZARD_SPLASH_RADIUS:
                                other.take_damage(WIZARD_SPLASH_DAMAGE)
                        break

            # move ice bolts + hit detection
            for ib in ice_bolts:
                if not ib.alive:
                    continue
                ib.move()
                for b in alive_balls:
                    if b.team_id == ib.team_id:
                        continue
                    if dist(ib.x, ib.y, b.x, b.y) <= b.radius + 4:
                        # mirror reflects ice bolts
                        if b.role == "mirror":
                            ib.dx = -ib.dx
                            ib.dy = -ib.dy
                            ib.angle = math.atan2(ib.dy, ib.dx)
                            ib.team_id = b.team_id
                            ib.x += ib.dx * 2
                            ib.y += ib.dy * 2
                            break
                        if b.role == "shield":
                            angle = math.atan2(ib.y - b.y, ib.x - b.x)
                            if b.is_angle_in_shield(angle):
                                ib.alive = False
                                break
                        b.take_damage(ICE_MAGE_DAMAGE)
                        b.slow_timer = ICE_SLOW_DURATION
                        ib.alive = False
                        break

            # bomb update + explosion damage
            for bomb in bombs:
                if not bomb.alive:
                    continue
                was_exploding = bomb.exploding
                bomb.update()
                if bomb.exploding and not was_exploding:
                    for b in alive_balls:
                        if b.team_id == bomb.team_id:
                            continue
                        d = dist(bomb.x, bomb.y, b.x, b.y)
                        if d <= bomb.explosion_radius:
                            b.take_damage(BOMB_DAMAGE)
                            dx = b.x - bomb.x
                            dy = b.y - bomb.y
                            dd = max(d, 0.01)
                            b.apply_knockback(dx / dd, dy / dd, BOMB_KNOCKBACK)

            # body collisions
            for i in range(len(alive_balls)):
                for j in range(i + 1, len(alive_balls)):
                    a, b = alive_balls[i], alive_balls[j]
                    if a.team_id == b.team_id:
                        if dist(a.x, a.y, b.x, b.y) <= a.radius + b.radius:
                            resolve_collision(a, b)
                        continue

                    if dist(a.x, a.y, b.x, b.y) <= a.radius + b.radius:
                        if a.role == "zombie" and a.hit_cooldown == 0:
                            blocked = False
                            if b.role == "shield":
                                angle = math.atan2(a.y - b.y, a.x - b.x)
                                blocked = b.is_angle_in_shield(angle)
                            if not blocked:
                                b.take_damage(ZOMBIE_DAMAGE)
                            a.hit_cooldown = 5
                        if b.role == "zombie" and b.hit_cooldown == 0:
                            blocked = False
                            if a.role == "shield":
                                angle = math.atan2(b.y - a.y, b.x - a.x)
                                blocked = a.is_angle_in_shield(angle)
                            if not blocked:
                                a.take_damage(ZOMBIE_DAMAGE)
                            b.hit_cooldown = 5
                        # berserker rage damage
                        if a.role == "berserker" and a.hit_cooldown == 0:
                            dmg = int(BERSERKER_BASE_DAMAGE * a.rage_multiplier)
                            blocked = False
                            if b.role == "shield":
                                angle = math.atan2(a.y - b.y, a.x - b.x)
                                blocked = b.is_angle_in_shield(angle)
                            if not blocked:
                                b.take_damage(dmg)
                            a.hit_cooldown = 20
                        if b.role == "berserker" and b.hit_cooldown == 0:
                            dmg = int(BERSERKER_BASE_DAMAGE * b.rage_multiplier)
                            blocked = False
                            if a.role == "shield":
                                angle = math.atan2(b.y - a.y, b.x - a.x)
                                blocked = a.is_angle_in_shield(angle)
                            if not blocked:
                                a.take_damage(dmg)
                            b.hit_cooldown = 20
                        # shield charge damage — hits fast on contact
                        if a.role == "shield" and a.hit_cooldown == 0:
                            b.take_damage(SHIELD_DAMAGE)
                            a.hit_cooldown = 10
                        if b.role == "shield" and b.hit_cooldown == 0:
                            a.take_damage(SHIELD_DAMAGE)
                            b.hit_cooldown = 10
                        # ninja backstab
                        if a.role == "ninja" and a.invisible and a.hit_cooldown == 0:
                            b.take_damage(NINJA_BACKSTAB_DAMAGE)
                            a.invisible = False
                            a.invis_timer = 0
                            a.invis_cooldown = NINJA_INVIS_COOLDOWN
                            a.hit_cooldown = 30
                        if b.role == "ninja" and b.invisible and b.hit_cooldown == 0:
                            a.take_damage(NINJA_BACKSTAB_DAMAGE)
                            b.invisible = False
                            b.invis_timer = 0
                            b.invis_cooldown = NINJA_INVIS_COOLDOWN
                            b.hit_cooldown = 30
                        # vampire lifesteal
                        if a.role == "vampire" and a.hit_cooldown == 0:
                            blocked = False
                            if b.role == "shield":
                                angle = math.atan2(a.y - b.y, a.x - b.x)
                                blocked = b.is_angle_in_shield(angle)
                            if not blocked:
                                b.take_damage(VAMPIRE_DAMAGE)
                                a.hp = min(a.max_hp, a.hp + int(VAMPIRE_DAMAGE * VAMPIRE_LIFESTEAL))
                            a.hit_cooldown = VAMPIRE_HIT_COOLDOWN
                        if b.role == "vampire" and b.hit_cooldown == 0:
                            blocked = False
                            if a.role == "shield":
                                angle = math.atan2(b.y - a.y, b.x - a.x)
                                blocked = a.is_angle_in_shield(angle)
                            if not blocked:
                                a.take_damage(VAMPIRE_DAMAGE)
                                b.hp = min(b.max_hp, b.hp + int(VAMPIRE_DAMAGE * VAMPIRE_LIFESTEAL))
                            b.hit_cooldown = VAMPIRE_HIT_COOLDOWN
                        # tank contact damage
                        if a.role == "tank" and a.hit_cooldown == 0:
                            blocked = False
                            if b.role == "shield":
                                angle = math.atan2(a.y - b.y, a.x - b.x)
                                blocked = b.is_angle_in_shield(angle)
                            if not blocked:
                                b.take_damage(TANK_DAMAGE)
                            a.hit_cooldown = TANK_HIT_COOLDOWN
                        if b.role == "tank" and b.hit_cooldown == 0:
                            blocked = False
                            if a.role == "shield":
                                angle = math.atan2(b.y - a.y, b.x - a.x)
                                blocked = a.is_angle_in_shield(angle)
                            if not blocked:
                                a.take_damage(TANK_DAMAGE)
                            b.hit_cooldown = TANK_HIT_COOLDOWN
                        # assassin dash strike
                        if a.role == "assassin" and a.assassin_dashing > 0 and a.hit_cooldown == 0:
                            blocked = False
                            if b.role == "shield":
                                angle = math.atan2(a.y - b.y, a.x - b.x)
                                blocked = b.is_angle_in_shield(angle)
                            if not blocked:
                                b.take_damage(ASSASSIN_DAMAGE)
                            a.hit_cooldown = 30
                            a.assassin_dashing = 0
                            a.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
                            # start retreat — run opposite direction
                            ddx = a.x - b.x
                            ddy = a.y - b.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            a.assassin_retreat_dx = ddx / dd
                            a.assassin_retreat_dy = ddy / dd
                            a.assassin_retreating = ASSASSIN_RETREAT_DURATION
                        if b.role == "assassin" and b.assassin_dashing > 0 and b.hit_cooldown == 0:
                            blocked = False
                            if a.role == "shield":
                                angle = math.atan2(b.y - a.y, b.x - a.x)
                                blocked = a.is_angle_in_shield(angle)
                            if not blocked:
                                a.take_damage(ASSASSIN_DAMAGE)
                            b.hit_cooldown = 30
                            b.assassin_dashing = 0
                            b.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
                            ddx = b.x - a.x
                            ddy = b.y - a.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.assassin_retreat_dx = ddx / dd
                            b.assassin_retreat_dy = ddy / dd
                            b.assassin_retreating = ASSASSIN_RETREAT_DURATION
                        # mirror contact damage
                        if a.role == "mirror" and a.hit_cooldown == 0:
                            b.take_damage(MIRROR_DAMAGE)
                            a.hit_cooldown = MIRROR_HIT_COOLDOWN
                        if b.role == "mirror" and b.hit_cooldown == 0:
                            a.take_damage(MIRROR_DAMAGE)
                            b.hit_cooldown = MIRROR_HIT_COOLDOWN
                        # charger slam damage
                        if a.role == "charger" and a.charging > 0 and a.hit_cooldown == 0:
                            blocked = False
                            if b.role == "shield":
                                angle = math.atan2(a.y - b.y, a.x - b.x)
                                blocked = b.is_angle_in_shield(angle)
                            if not blocked:
                                b.take_damage(CHARGER_DAMAGE)
                                ddx = b.x - a.x
                                ddy = b.y - a.y
                                dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                b.apply_knockback(ddx / dd, ddy / dd, 15.0)
                            a.hit_cooldown = 30
                            a.charging = 0
                            a.charge_cooldown = CHARGER_CHARGE_COOLDOWN
                        if b.role == "charger" and b.charging > 0 and b.hit_cooldown == 0:
                            blocked = False
                            if a.role == "shield":
                                angle = math.atan2(b.y - a.y, b.x - a.x)
                                blocked = a.is_angle_in_shield(angle)
                            if not blocked:
                                a.take_damage(CHARGER_DAMAGE)
                                ddx = a.x - b.x
                                ddy = a.y - b.y
                                dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                a.apply_knockback(ddx / dd, ddy / dd, 15.0)
                            b.hit_cooldown = 30
                            b.charging = 0
                            b.charge_cooldown = CHARGER_CHARGE_COOLDOWN
                        # mimic copies role on contact
                        if a.mimic_original and a.mimic_timer <= 0 and b.team_id != a.team_id:
                            a.role = b.role
                            a.speed = ROLE_SPEEDS.get(b.role, 3.0)
                            a.mimic_display_role = b.role
                            a.mimic_timer = MIMIC_COPY_DURATION
                        if b.mimic_original and b.mimic_timer <= 0 and a.team_id != b.team_id:
                            b.role = a.role
                            b.speed = ROLE_SPEEDS.get(a.role, 3.0)
                            b.mimic_display_role = a.role
                            b.mimic_timer = MIMIC_COPY_DURATION
                        resolve_collision(a, b)

            # sword hits
            for b in alive_balls:
                if b.role != "swordsman" or b.hit_cooldown > 0:
                    continue
                sbx = b.x + math.cos(b.sword_angle) * b.radius
                sby = b.y + math.sin(b.sword_angle) * b.radius
                tx, ty = b.sword_tip()
                for other in alive_balls:
                    if other is b or not other.alive or other.team_id == b.team_id:
                        continue
                    if point_near_segment(other.x, other.y, sbx, sby, tx, ty, other.radius + 3):
                        # shield blocks swords
                        if other.role == "shield":
                            angle = math.atan2(tx - other.y, tx - other.x)
                            if other.is_angle_in_shield(angle):
                                b.hit_cooldown = 20
                                break
                        other.take_damage(SWORD_DAMAGE)
                        b.hit_cooldown = 20
                        ddx = other.x - b.x
                        ddy = other.y - b.y
                        dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                        other.apply_knockback(ddx / dd, ddy / dd, 10.0)
                        break

            # chainsaw hits — damage on cooldown, no knockback
            for b in alive_balls:
                if b.role != "chainsaw" or b.hit_cooldown > 0:
                    continue
                cbx = b.x + math.cos(b.chainsaw_angle) * b.radius
                cby = b.y + math.sin(b.chainsaw_angle) * b.radius
                ctx, cty = b.chainsaw_tip()
                for other in alive_balls:
                    if other is b or not other.alive or other.team_id == b.team_id:
                        continue
                    if point_near_segment(other.x, other.y, cbx, cby, ctx, cty, other.radius + 3):
                        # shield blocks chainsaw
                        if other.role == "shield":
                            angle = math.atan2(ctx - other.y, ctx - other.x)
                            if other.is_angle_in_shield(angle):
                                continue
                        other.take_damage(CHAINSAW_DAMAGE)
                        b.hit_cooldown = CHAINSAW_HIT_COOLDOWN
                        break

            # wall update + ball-wall collisions
            for w in walls:
                if not w.alive:
                    continue
                w.update()
                if w.exploding:
                    # directional explosion damage on first frame
                    if w.explode_frames == 9:
                        blast_angle = math.atan2(w.blast_dy, w.blast_dx)
                        spread = math.pi / 3  # 60 degree cone
                        for b in alive_balls:
                            if b.team_id == w.team_id:
                                continue
                            d = dist(w.x, w.y, b.x, b.y)
                            if d > FORT_EXPLODE_RADIUS:
                                continue
                            # check if ball is in the blast cone
                            angle_to = math.atan2(b.y - w.y, b.x - w.x)
                            diff = (angle_to - blast_angle + math.pi) % (2 * math.pi) - math.pi
                            if abs(diff) <= spread:
                                b.take_damage(FORT_EXPLODE_DAMAGE)
                                ddx = b.x - w.x
                                ddy = b.y - w.y
                                dd = max(d, 0.01)
                                b.apply_knockback(ddx / dd, ddy / dd, 12.0)
                    continue
                # ball-wall collision (enemies bounce off, wall takes damage)
                x1, y1, x2, y2 = w.endpoints()
                for b in alive_balls:
                    if b.team_id == w.team_id:
                        continue
                    if point_near_segment(b.x, b.y, x1, y1, x2, y2, b.radius + w.thickness // 2):
                        w.hp -= 1
                        # bounce ball away from wall center
                        ddx = b.x - w.x
                        ddy = b.y - w.y
                        dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                        b.apply_knockback(ddx / dd, ddy / dd, 6.0)

            # kill dead balls
            newly_dead = []
            for b in balls:
                if b.hp <= 0 and b.alive:
                    b.alive = False
                    newly_dead.append(b)

            # necromancer raise dead — any death in circle (own team or enemy), except zombies
            for necro in alive_balls:
                if necro.role != "necromancer" or not necro.alive or necro.necro_cooldown > 0:
                    continue
                for corpse in newly_dead:
                    if corpse.role == "zombie":
                        continue
                    if dist(necro.x, necro.y, corpse.x, corpse.y) <= NECRO_RAISE_RANGE:
                        # raise as zombie on necromancer's team
                        corpse.alive = True
                        corpse.hp = NECRO_ZOMBIE_HP
                        corpse.max_hp = NECRO_ZOMBIE_HP
                        corpse.team_id = necro.team_id
                        corpse.color = necro.color
                        corpse.role = "zombie"
                        corpse.speed = ZOMBIE_SPEED
                        corpse.hit_cooldown = 0
                        corpse.bounce_timer = 0
                        corpse.pinned_timer = 0
                        corpse.carried_by_spear = False
                        corpse.trapped_in = None
                        necro.necro_cooldown = NECRO_RAISE_COOLDOWN
                        break  # one raise per tick

            # clean up dead projectiles/traps/bombs/walls
            spears = [s for s in spears if s.alive]
            traps = [t for t in traps if t.alive]
            bombs = [bm for bm in bombs if bm.alive]
            bullets = [bl for bl in bullets if bl.alive]
            arrows = [ar for ar in arrows if ar.alive]
            orbs = [orb for orb in orbs if orb.alive]
            ice_bolts = [ib for ib in ice_bolts if ib.alive]
            walls = [w for w in walls if w.alive]

            # check for winner
            alive_teams = set(b.team_id for b in balls if b.alive)
            if len(alive_teams) == 1:
                winner_team = alive_teams.pop()
            elif len(alive_teams) == 0:
                winner_team = -1

        # ── draw ──
        screen.fill((20, 20, 30))
        pygame.draw.rect(screen, (80, 80, 80), (0, 0, WIDTH, HEIGHT), 2)

        # draw traps, bombs, walls first (under balls)
        for w in walls:
            w.draw(screen)
        for t in traps:
            t.draw(screen)
        for bm in bombs:
            bm.draw(screen)

        for b in balls:
            b.draw(screen)

        # draw spears and bullets on top
        for s in spears:
            s.draw(screen)
        for bl in bullets:
            bl.draw(screen)
        for ar in arrows:
            ar.draw(screen)
        for orb in orbs:
            orb.draw(screen)
        for ib in ice_bolts:
            ib.draw(screen)

        # HUD
        hud_y = 8
        shown_teams = sorted(set(cfg["team_id"] for cfg in team_configs))
        for team_id in shown_teams:
            color = TEAM_COLORS[team_id % len(TEAM_COLORS)]
            team_balls = [b for b in balls if b.team_id == team_id and b.alive]
            total_hp = sum(b.hp for b in team_balls)
            alive_count = len(team_balls)
            roles = set(b.role for b in team_balls)
            role_str = "/".join(r.capitalize() for r in sorted(roles)) if roles else "Dead"
            text = font.render(f"T{team_id+1} {role_str}: {total_hp}HP [{alive_count}]",
                               True, color)
            screen.blit(text, (10, hud_y))
            hud_y += 20

        # speed indicator
        if paused:
            speed_text = font.render("PAUSED  (Space)", True, (255, 255, 100))
        else:
            speed_text = font.render(f"Speed: {game_speed}x  (1/2/3/4)", True, (180, 180, 180))
        screen.blit(speed_text, (WIDTH - speed_text.get_width() - 10, 8))

        # mutate hint + timer
        secs_left = max(0, (STALE_THRESHOLD - stale_timer)) // 60
        mutate_text = small_font.render(f"X = Mutate  |  Auto-mutate in {secs_left}s", True, (120, 120, 140))
        screen.blit(mutate_text, (WIDTH - mutate_text.get_width() - 10, 28))

        if recording:
            rec_label = small_font.render("REC", True, (255, 50, 50))
            screen.blit(rec_label, (10, HEIGHT - 20))

        pygame.display.flip()
        if rec_proc:
            record_frame(rec_proc, screen)
        clock.tick(60)


def tournament_menu(arena_idx):
    """Setup screen for bracket tournament. Returns (bracket, arena_idx, realistic) or None to go back."""
    global screen

    # bracket = list of entries, each entry is a list of roles (one team)
    bracket = [["zombie"], ["swordsman"], ["spearman"], ["trapper"]]
    scroll_offset = 0
    search_open = None  # index into bracket
    search_text = ""
    dropdown_scroll = 0
    prev_size = (0, 0)
    realistic = False

    PRESETS = {
        "Every Role": [[r] for r in ROLES],
        "5 of Each": [[r] * 5 for r in ROLES],
        "Random 8": None,   # generated on click
        "Random 16": None,
        "Melee Brawl": [[r] for r in ["zombie", "swordsman", "berserker", "chainsaw", "vampire", "tank", "charger", "shield"]],
        "Ranged War": [[r] for r in ["sniper", "archer", "wizard", "ice_mage", "spearman", "bomber", "trapper", "fortifier"]],
    }

    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEWHEEL:
                if search_open is not None:
                    filtered = [r for r in ROLES if search_text.lower() in r.lower()]
                    max_s = max(0, len(filtered) - 8)
                    dropdown_scroll = max(0, min(max_s, dropdown_scroll - event.y))
                else:
                    max_s = max(0, len(bracket) * 34 - 300)
                    scroll_offset = max(0, min(max_s, scroll_offset - event.y * 20))
                continue
            if event.type == pygame.KEYDOWN and search_open is not None:
                if event.key == pygame.K_ESCAPE:
                    search_open = None
                    search_text = ""
                    dropdown_scroll = 0
                elif event.key == pygame.K_BACKSPACE:
                    search_text = search_text[:-1]
                    dropdown_scroll = 0
                elif event.key == pygame.K_RETURN:
                    filtered = [r for r in ROLES if search_text.lower() in r.lower()]
                    if filtered:
                        idx = min(dropdown_scroll, len(filtered) - 1)
                        bracket[search_open].append(filtered[idx])
                    search_open = None
                    search_text = ""
                    dropdown_scroll = 0
                elif event.unicode and event.unicode.isprintable():
                    search_text += event.unicode
                    dropdown_scroll = 0
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # dropdown click
                if search_open is not None and hasattr(tournament_menu, '_dd_rects'):
                    clicked_dd = False
                    for role_name, drect in tournament_menu._dd_rects:
                        if drect.collidepoint(mx, my):
                            bracket[search_open].append(role_name)
                            search_open = None
                            search_text = ""
                            dropdown_scroll = 0
                            clicked_dd = True
                            break
                    if clicked_dd:
                        continue
                    search_open = None
                    search_text = ""
                    dropdown_scroll = 0

                # back button
                if back_btn.clicked(mx, my):
                    return None

                # start tournament
                if start_btn.clicked(mx, my) and len(bracket) >= 2:
                    return bracket, arena_idx, realistic

                # arena size
                if minus_arena_rect.collidepoint(mx, my) and arena_idx > 0:
                    arena_idx -= 1
                if plus_arena_rect.collidepoint(mx, my) and arena_idx < len(ARENA_SIZES) - 1:
                    arena_idx += 1

                # realistic toggle
                if realistic_rect.collidepoint(mx, my):
                    realistic = not realistic

                # add team
                if add_team_btn.clicked(mx, my):
                    bracket.append([ROLES[len(bracket) % len(ROLES)]])

                # presets
                for name, rect in preset_rects:
                    if rect.collidepoint(mx, my):
                        if name == "Random 8":
                            bracket = [[random.choice(ROLES) for _ in range(random.randint(1, 3))] for _ in range(8)]
                        elif name == "Random 16":
                            bracket = [[random.choice(ROLES) for _ in range(random.randint(1, 3))] for _ in range(16)]
                        elif name in PRESETS and PRESETS[name] is not None:
                            bracket = [list(t) for t in PRESETS[name]]

                # per-entry buttons
                for idx, entry_r in enumerate(entry_rects):
                    if "add_role" in entry_r and entry_r["add_role"].collidepoint(mx, my):
                        search_open = idx
                        search_text = ""
                        dropdown_scroll = 0
                    if "remove" in entry_r and entry_r["remove"].collidepoint(mx, my) and len(bracket) > 2:
                        bracket.pop(idx)
                        break
                    # click individual roles to remove them
                    for ri, role_rect in enumerate(entry_r.get("roles", [])):
                        if role_rect.collidepoint(mx, my) and len(bracket[idx]) > 1:
                            bracket[idx].pop(ri)
                            break

        # layout
        menu_w = 650
        menu_h = max(BASE_HEIGHT, 500)
        new_size = (menu_w, menu_h)
        if new_size != prev_size:
            screen = pygame.display.set_mode(new_size)
            prev_size = new_size

        back_btn = Button(15, 15, 70, 30, "BACK", (80, 60, 60))
        start_btn = Button(menu_w // 2 - 80, menu_h - 55, 160, 42, "START!", (50, 100, 60))
        add_team_btn = Button(menu_w // 2 + 100, menu_h - 55, 100, 42, "+ TEAM", (60, 80, 100))
        back_btn.update(mx, my)
        start_btn.update(mx, my)
        add_team_btn.update(mx, my)

        screen.fill((20, 20, 30))
        t = title_font.render("Tournament Bracket", True, (255, 255, 255))
        screen.blit(t, (menu_w // 2 - t.get_width() // 2, 15))

        # arena selector
        ay = 55
        a_label = font.render("Arena:", True, (200, 200, 200))
        screen.blit(a_label, (20, ay))
        minus_arena_rect = pygame.Rect(90, ay - 2, 26, 24)
        plus_arena_rect = pygame.Rect(280, ay - 2, 26, 24)
        pygame.draw.rect(screen, (80, 80, 100), minus_arena_rect, border_radius=4)
        pygame.draw.rect(screen, (80, 80, 100), plus_arena_rect, border_radius=4)
        ml = font.render("-", True, (255, 255, 255))
        pl = font.render("+", True, (255, 255, 255))
        screen.blit(ml, (minus_arena_rect.centerx - ml.get_width() // 2,
                         minus_arena_rect.centery - ml.get_height() // 2))
        screen.blit(pl, (plus_arena_rect.centerx - pl.get_width() // 2,
                         plus_arena_rect.centery - pl.get_height() // 2))
        aw, ah, a_hint = ARENA_SIZES[arena_idx]
        at = font.render(f"{aw}x{ah} ({a_hint})", True, (255, 255, 255))
        screen.blit(at, (124, ay))

        # realistic mode toggle
        realistic_rect = pygame.Rect(20, ay + 28, 120, 24)
        r_bg = (40, 120, 60) if realistic else (60, 60, 80)
        r_border = (80, 200, 100) if realistic else (100, 100, 130)
        if realistic_rect.collidepoint(mx, my):
            r_bg = (50, 140, 70) if realistic else (70, 70, 100)
        pygame.draw.rect(screen, r_bg, realistic_rect, border_radius=4)
        pygame.draw.rect(screen, r_border, realistic_rect, 1, border_radius=4)
        r_label = small_font.render("Realistic" if not realistic else "Realistic ON", True, (255, 255, 255))
        screen.blit(r_label, (realistic_rect.centerx - r_label.get_width() // 2,
                               realistic_rect.centery - r_label.get_height() // 2))

        # presets
        px = 330
        preset_label = font.render("Presets:", True, (200, 200, 200))
        screen.blit(preset_label, (px, 55))
        preset_rects = []
        py = 55
        ppx = px + 75
        for name in PRESETS:
            pr = pygame.Rect(ppx, py - 2, 80, 22)
            hovered = pr.collidepoint(mx, my)
            bg = (70, 70, 100) if hovered else (50, 50, 70)
            pygame.draw.rect(screen, bg, pr, border_radius=4)
            pygame.draw.rect(screen, (100, 100, 130), pr, 1, border_radius=4)
            pl2 = small_font.render(name, True, (255, 255, 255))
            screen.blit(pl2, (pr.centerx - pl2.get_width() // 2, pr.centery - pl2.get_height() // 2))
            preset_rects.append((name, pr))
            ppx += 85
            if ppx + 80 > menu_w:
                ppx = px + 75
                py += 26

        # bracket entries
        entry_rects = []
        bracket_y_start = 90
        clip_top = bracket_y_start
        clip_bottom = menu_h - 70
        entries_label = font.render(f"Bracket ({len(bracket)} teams):", True, (200, 200, 200))
        screen.blit(entries_label, (20, bracket_y_start - 2))
        bracket_y_start += 24

        for idx, team_roles in enumerate(bracket):
            ey = bracket_y_start + idx * 34 - scroll_offset
            er = {}
            if ey < clip_top - 34 or ey > clip_bottom:
                entry_rects.append(er)
                continue
            # team number
            color = TEAM_COLORS[idx % len(TEAM_COLORS)]
            pygame.draw.circle(screen, color, (30, ey + 12), 8)
            num_t = small_font.render(str(idx + 1), True, (255, 255, 255))
            screen.blit(num_t, (30 - num_t.get_width() // 2, ey + 12 - num_t.get_height() // 2))

            # role tags
            rx = 48
            role_rects_list = []
            for ri, role in enumerate(team_roles):
                rw = max(50, small_font.size(role.capitalize())[0] + 10)
                rr = pygame.Rect(rx, ey + 2, rw, 20)
                role_rects_list.append(rr)
                hovered = rr.collidepoint(mx, my)
                bg = (90, 50, 50) if hovered else (60, 60, 80)
                pygame.draw.rect(screen, bg, rr, border_radius=3)
                pygame.draw.rect(screen, color, rr, 1, border_radius=3)
                rl = small_font.render(role.capitalize(), True, (255, 255, 255))
                screen.blit(rl, (rr.centerx - rl.get_width() // 2, rr.centery - rl.get_height() // 2))
                rx += rw + 3
            er["roles"] = role_rects_list

            # + role button
            add_r = pygame.Rect(rx + 2, ey + 2, 20, 20)
            er["add_role"] = add_r
            pygame.draw.rect(screen, (50, 100, 50), add_r, border_radius=3)
            screen.blit(small_font.render("+", True, (255, 255, 255)),
                        (add_r.centerx - 3, add_r.centery - 7))

            # x remove team button
            if len(bracket) > 2:
                rem_r = pygame.Rect(menu_w - 35, ey + 2, 20, 20)
                er["remove"] = rem_r
                pygame.draw.rect(screen, (100, 40, 40), rem_r, border_radius=3)
                screen.blit(small_font.render("x", True, (255, 255, 255)),
                            (rem_r.centerx - 3, rem_r.centery - 7))

            entry_rects.append(er)

        # hint
        hint = small_font.render("Click role to remove  |  + to add role  |  Scroll to browse  |  x to remove team",
                                 True, (120, 120, 140))
        screen.blit(hint, (menu_w // 2 - hint.get_width() // 2, menu_h - 70))

        back_btn.draw(screen)
        start_btn.draw(screen)
        add_team_btn.draw(screen)

        # dropdown for adding roles
        tournament_menu._dd_rects = []
        if search_open is not None and 0 <= search_open < len(entry_rects):
            er = entry_rects[search_open]
            if "add_role" in er:
                anchor = er["add_role"]
                sb_x = anchor.x
                sb_y = anchor.y + anchor.height + 2
                sb_w = 130
                pygame.draw.rect(screen, (40, 40, 55), (sb_x, sb_y, sb_w, 22))
                pygame.draw.rect(screen, (150, 150, 200), (sb_x, sb_y, sb_w, 22), 1)
                cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
                stxt = small_font.render(search_text + cursor, True, (255, 255, 255))
                screen.blit(stxt, (sb_x + 4, sb_y + 4))
                filtered = [r for r in ROLES if search_text.lower() in r.lower()]
                max_visible = 8
                max_s = max(0, len(filtered) - max_visible)
                dropdown_scroll = min(dropdown_scroll, max_s)
                visible = filtered[dropdown_scroll:dropdown_scroll + max_visible]
                dy = sb_y + 24
                for role_name in visible:
                    opt_rect = pygame.Rect(sb_x, dy, sb_w, 20)
                    hovered = opt_rect.collidepoint(mx, my)
                    bg = (70, 70, 100) if hovered else (50, 50, 65)
                    pygame.draw.rect(screen, bg, opt_rect)
                    pygame.draw.rect(screen, (100, 100, 120), opt_rect, 1)
                    rl = small_font.render(role_name.capitalize(), True, (255, 255, 255))
                    screen.blit(rl, (sb_x + 4, dy + 3))
                    tournament_menu._dd_rects.append((role_name, opt_rect))
                    dy += 20
                if dropdown_scroll > 0:
                    pygame.draw.polygon(screen, (180, 180, 200), [
                        (sb_x + sb_w - 10, sb_y + 28), (sb_x + sb_w - 6, sb_y + 24), (sb_x + sb_w - 2, sb_y + 28)])
                if dropdown_scroll < max_s:
                    pygame.draw.polygon(screen, (180, 180, 200), [
                        (sb_x + sb_w - 10, dy - 4), (sb_x + sb_w - 6, dy), (sb_x + sb_w - 2, dy - 4)])

        pygame.display.flip()
        clock.tick(60)


def run_tournament(bracket, arena_idx, realistic=False):
    """Run a single-elimination bracket tournament, return to menu when done."""
    global WIDTH, HEIGHT, screen, BALL_RADIUS, SWORD_LENGTH, TRAP_RADIUS

    # simple approach: shuffle teams, pair them all up, leftover odd one gets a bye
    n = len(bracket)
    teams_shuffled = list(bracket)
    random.shuffle(teams_shuffled)

    # build first round directly — real matches first, then byes at the end
    first_round = []
    i = 0
    while i + 1 < n:
        first_round.append((teams_shuffled[i], teams_shuffled[i + 1], None))
        i += 2
    if i < n:
        # odd team out gets a bye
        first_round.append((teams_shuffled[i], None, None))

    # build the rest of the rounds structure (empty placeholders)
    rounds = [first_round]
    num_matches = len(first_round)
    while num_matches > 1:
        num_matches = (num_matches + 1) // 2
        rounds.append([(None, None, None)] * num_matches)

    # helper to get role list from a team entry (plain list or realistic dict)
    def get_roles(team):
        if team is None:
            return None
        if isinstance(team, dict):
            return team["roles"]
        return team

    def show_bracket_screen(rounds, current_round_idx, match_idx, prompt_text):
        """Display bracket and wait for click/key to continue."""
        bw = 800
        bh = max(500, len(rounds[0]) * 50 + 200)
        screen_local = pygame.display.set_mode((bw, bh))

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    waiting = False

            screen_local.fill((20, 20, 30))
            t = title_font.render("Tournament", True, (255, 255, 255))
            screen_local.blit(t, (bw // 2 - t.get_width() // 2, 10))

            # draw rounds
            num_rounds = len(rounds)
            col_w = min(180, (bw - 40) // max(num_rounds, 1))
            for ri, rnd in enumerate(rounds):
                rx = 20 + ri * col_w
                round_label = small_font.render(f"Round {ri + 1}" if ri < num_rounds - 1 else "Final",
                                                True, (180, 180, 200))
                screen_local.blit(round_label, (rx, 50))
                for mi, (a, b, winner) in enumerate(rnd):
                    my_off = 75 + mi * 48
                    # team A
                    a_roles = get_roles(a)
                    b_roles = get_roles(b)
                    if a_roles is not None:
                        a_str = "/".join(r[:5].capitalize() for r in a_roles)
                    else:
                        a_str = "BYE"
                    if b_roles is not None:
                        b_str = "/".join(r[:5].capitalize() for r in b_roles)
                    else:
                        b_str = "BYE"

                    a_color = (200, 200, 200)
                    b_color = (200, 200, 200)
                    if winner is not None:
                        if get_roles(winner) == a_roles:
                            a_color = (100, 255, 100)
                            b_color = (255, 80, 80)
                        else:
                            b_color = (100, 255, 100)
                            a_color = (255, 80, 80)
                    # highlight current match
                    if ri == current_round_idx and mi == match_idx and winner is None:
                        pygame.draw.rect(screen_local, (60, 60, 90),
                                         (rx - 2, my_off - 2, col_w - 10, 44), border_radius=4)

                    at = small_font.render(a_str[:20], True, a_color)
                    bt = small_font.render(b_str[:20], True, b_color)
                    screen_local.blit(at, (rx + 4, my_off))
                    screen_local.blit(bt, (rx + 4, my_off + 20))
                    pygame.draw.line(screen_local, (80, 80, 100),
                                     (rx, my_off + 40), (rx + col_w - 15, my_off + 40), 1)

            # prompt
            pt = font.render(prompt_text, True, (255, 255, 100))
            screen_local.blit(pt, (bw // 2 - pt.get_width() // 2, bh - 35))

            pygame.display.flip()
            clock.tick(60)

    def play_match(team_a_roles, team_b_roles, hp_a=None, hp_b=None):
        """Play a single match between two teams. Returns the winning team's roles.
        hp_a/hp_b: optional list of HP values parallel to team_a_roles/team_b_roles for realistic mode."""
        configs = []
        for role in team_a_roles:
            configs.append({"team_id": 0, "role": role})
        for role in team_b_roles:
            configs.append({"team_id": 1, "role": role})

        aw, ah, a_hint = ARENA_SIZES[arena_idx]
        WIDTH_l = aw
        HEIGHT_l = ah
        t_recording = a_hint == "Record"
        total_balls = len(configs)
        if total_balls > 6:
            br = max(12, BASE_BALL_RADIUS - (total_balls - 6) * 2)
        else:
            br = BASE_BALL_RADIUS

        # set globals for game systems
        global WIDTH, HEIGHT, BALL_RADIUS, SWORD_LENGTH, TRAP_RADIUS
        WIDTH = WIDTH_l
        HEIGHT = HEIGHT_l
        BALL_RADIUS = br
        SWORD_LENGTH = BALL_RADIUS * 2
        TRAP_RADIUS = BALL_RADIUS * 4
        screen_g = pygame.display.set_mode((WIDTH, HEIGHT))

        t_rec_proc = start_recording(WIDTH, HEIGHT) if t_recording else None

        balls = spawn_balls(configs)
        # apply HP overrides for realistic mode
        if hp_a or hp_b:
            idx_a = 0
            idx_b = 0
            for ball in balls:
                if ball.team_id == 0 and hp_a and idx_a < len(hp_a):
                    ball.hp = hp_a[idx_a]
                    idx_a += 1
                elif ball.team_id == 1 and hp_b and idx_b < len(hp_b):
                    ball.hp = hp_b[idx_b]
                    idx_b += 1
        spears, traps, bombs, bullets, arrows, orbs, ice_bolts, walls = [], [], [], [], [], [], [], []
        speed_options = [1, 2, 4, 10]
        speed_index = 0
        paused = False
        winner_team = None
        t_stale_timer = 0
        T_STALE_THRESHOLD = 7200

        def t_mutate_teams(balls_list):
            melee_list = list(Ball.MELEE_ROLES)
            alive_teams = {}
            for b in balls_list:
                if b.alive:
                    if b.team_id not in alive_teams:
                        alive_teams[b.team_id] = []
                    alive_teams[b.team_id].append(b)
            for tid, members in alive_teams.items():
                victim = random.choice(members)
                victim.alive = False
                victim.hp = 0
                new_role = random.choice(melee_list)
                color = TEAM_COLORS[tid % len(TEAM_COLORS)]
                new_ball = Ball(victim.x, victim.y, color, tid, new_role)
                balls_list.append(new_ball)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_CTRL and mods & pygame.KMOD_SHIFT:
                            stop_recording(t_rec_proc)
                            return "abort"
                        t_mutate_teams(balls)
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    if event.key == pygame.K_1:
                        speed_index = 0
                    if event.key == pygame.K_2:
                        speed_index = 1
                    if event.key == pygame.K_3:
                        speed_index = 2
                    if event.key == pygame.K_4:
                        speed_index = 3

            game_speed = speed_options[speed_index]

            if winner_team is not None:
                # show result briefly then return
                screen_g.fill((20, 20, 30))
                if winner_team == 0:
                    w_roles = team_a_roles
                    w_label = "/".join(r.capitalize() for r in team_a_roles)
                    color = TEAM_COLORS[0]
                    w_tid = 0
                elif winner_team == 1:
                    w_roles = team_b_roles
                    w_label = "/".join(r.capitalize() for r in team_b_roles)
                    color = TEAM_COLORS[1]
                    w_tid = 1
                else:
                    # draw — random pick
                    w_tid = random.choice([0, 1])
                    w_roles = team_a_roles if w_tid == 0 else team_b_roles
                    w_label = "/".join(r.capitalize() for r in w_roles)
                    color = (200, 200, 200)
                text = font.render(f"Winner: {w_label}", True, color)
                hint = small_font.render("Click or press any key to continue", True, (150, 150, 150))
                screen_g.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 20))
                screen_g.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 20))
                pygame.display.flip()

                # wait for input
                wait = True
                while wait:
                    for ev in pygame.event.get():
                        if ev.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if ev.type == pygame.MOUSEBUTTONDOWN or ev.type == pygame.KEYDOWN:
                            wait = False
                    clock.tick(60)

                # in realistic mode, return survivors with HP
                if realistic:
                    survivors = [(b.role, b.hp) for b in balls if b.alive and b.team_id == w_tid]
                    if not survivors:
                        survivors = [(w_roles[0], 1)]
                    stop_recording(t_rec_proc)
                    return {"roles": [s[0] for s in survivors], "hp": [s[1] for s in survivors]}
                stop_recording(t_rec_proc)
                return w_roles

            for _tick in range(game_speed):
                if winner_team is not None or paused:
                    break

                t_stale_timer += 1
                if t_stale_timer >= T_STALE_THRESHOLD:
                    t_mutate_teams(balls)
                    t_stale_timer = 0

                alive_balls = [b for b in balls if b.alive]
                for b in alive_balls:
                    target = b.find_target(alive_balls)
                    b.seek(target, alive_balls)
                    b.move()
                    b.try_throw_spear(target, spears)
                    b.try_place_trap(target, traps)
                    b.try_drop_bomb(target, bombs)
                    b.try_heal(alive_balls)
                    b.aim_shield(alive_balls)
                    b.try_fire_bullet(target, bullets)
                    b.try_fire_arrow(target, arrows)
                    b.try_cast_orb(target, orbs)
                    b.try_fire_ice_bolt(target, ice_bolts)
                    b.try_place_wall(target, walls, alive_balls)

                # summoner spawns
                for b in alive_balls:
                    if b.role != "summoner" or b.summon_cooldown > 0:
                        continue
                    b.minions = [m for m in b.minions if m.alive]
                    if len(b.minions) >= SUMMONER_MAX_MINIONS:
                        continue
                    angle = random.uniform(0, 2 * math.pi)
                    smx = b.x + math.cos(angle) * (b.radius * 2.5)
                    smy = b.y + math.sin(angle) * (b.radius * 2.5)
                    smx = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, smx))
                    smy = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, smy))
                    minion = Ball(smx, smy, b.color, b.team_id, "zombie")
                    minion.hp = SUMMONER_MINION_HP
                    minion.max_hp = SUMMONER_MINION_HP
                    minion.radius = max(8, int(BALL_RADIUS * SUMMONER_MINION_RADIUS_SCALE))
                    minion.is_minion = True
                    balls.append(minion)
                    b.minions.append(minion)
                    b.summon_cooldown = SUMMONER_COOLDOWN

                for s in spears:
                    if s.alive:
                        s.move()
                for s in spears:
                    if not s.alive or s.carried_ball is not None:
                        continue
                    for b in alive_balls:
                        if b.team_id == s.team_id or b.carried_by_spear:
                            continue
                        if dist(s.x, s.y, b.x, b.y) <= b.radius + 5:
                            if b.role == "mirror":
                                s.dx = -s.dx
                                s.dy = -s.dy
                                s.angle = math.atan2(s.dy, s.dx)
                                s.team_id = b.team_id
                                s.x += s.dx * 2
                                s.y += s.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(s.y - b.y, s.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    s.alive = False
                                    break
                            b.take_damage(SPEAR_DAMAGE)
                            if b.trapped_in is not None:
                                b.trapped_in.captured_ball = None
                                b.trapped_in.alive = False
                                b.trapped_in = None
                            b.carried_by_spear = True
                            b.pinned_timer = 0
                            b.vx = 0
                            b.vy = 0
                            s.carried_ball = b
                            break

                for t in traps:
                    if not t.alive:
                        continue
                    if t.captured_ball is not None:
                        t.update()
                        continue
                    for b in alive_balls:
                        if b.team_id == t.team_id or b.trapped_in is not None or b.carried_by_spear or b.pinned_timer > 0:
                            continue
                        if dist(t.x, t.y, b.x, b.y) <= t.radius:
                            t.captured_ball = b
                            b.trapped_in = t
                            ta = random.uniform(0, 2 * math.pi)
                            b.vx = math.cos(ta) * 4.0
                            b.vy = math.sin(ta) * 4.0
                            b.bounce_timer = 0
                            break

                for bl in bullets:
                    if bl.alive:
                        bl.move()
                for bl in bullets:
                    if not bl.alive:
                        continue
                    for b in alive_balls:
                        if b.team_id == bl.team_id:
                            continue
                        if dist(bl.x, bl.y, b.x, b.y) <= b.radius + 3:
                            if b.role == "mirror":
                                bl.dx = -bl.dx
                                bl.dy = -bl.dy
                                bl.angle = math.atan2(bl.dy, bl.dx)
                                bl.team_id = b.team_id
                                bl.x += bl.dx * 2
                                bl.y += bl.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(bl.y - b.y, bl.x - b.x)
                                if b.is_angle_in_shield(sa, attacker_role="sniper"):
                                    bl.alive = False
                                    break
                            b.take_damage(SNIPER_DAMAGE)
                            bl.alive = False
                            ddx = b.x - bl.x
                            ddy = b.y - bl.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.apply_knockback(ddx / dd, ddy / dd, 5.0)
                            break

                for ar in arrows:
                    if ar.alive:
                        ar.move()
                for ar in arrows:
                    if not ar.alive:
                        continue
                    for b in alive_balls:
                        if b.team_id == ar.team_id:
                            continue
                        if dist(ar.x, ar.y, b.x, b.y) <= b.radius + 4:
                            if b.role == "mirror":
                                ar.dx = -ar.dx
                                ar.dy = -ar.dy
                                ar.angle = math.atan2(ar.dy, ar.dx)
                                ar.team_id = b.team_id
                                ar.x += ar.dx * 2
                                ar.y += ar.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(ar.y - b.y, ar.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    ar.alive = False
                                    break
                            b.take_damage(ARCHER_DAMAGE)
                            ar.alive = False
                            ddx = b.x - ar.x
                            ddy = b.y - ar.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.apply_knockback(ddx / dd, ddy / dd, 3.0)
                            break

                for orb in orbs:
                    if not orb.alive:
                        continue
                    orb.move()
                    if orb.exploding:
                        continue
                    for b in alive_balls:
                        if b.team_id == orb.team_id:
                            continue
                        if dist(orb.x, orb.y, b.x, b.y) <= b.radius + 6:
                            if b.role == "mirror":
                                orb.dx = -orb.dx
                                orb.dy = -orb.dy
                                orb.team_id = b.team_id
                                orb.x += orb.dx * 2
                                orb.y += orb.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(orb.y - b.y, orb.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    orb.alive = False
                                    break
                            b.take_damage(WIZARD_DAMAGE)
                            orb.exploding = True
                            for other in alive_balls:
                                if other is b or other.team_id == orb.team_id:
                                    continue
                                if dist(orb.x, orb.y, other.x, other.y) <= WIZARD_SPLASH_RADIUS:
                                    other.take_damage(WIZARD_SPLASH_DAMAGE)
                            break

                for ib in ice_bolts:
                    if not ib.alive:
                        continue
                    ib.move()
                    for b in alive_balls:
                        if b.team_id == ib.team_id:
                            continue
                        if dist(ib.x, ib.y, b.x, b.y) <= b.radius + 4:
                            if b.role == "mirror":
                                ib.dx = -ib.dx
                                ib.dy = -ib.dy
                                ib.angle = math.atan2(ib.dy, ib.dx)
                                ib.team_id = b.team_id
                                ib.x += ib.dx * 2
                                ib.y += ib.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(ib.y - b.y, ib.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    ib.alive = False
                                    break
                            b.take_damage(ICE_MAGE_DAMAGE)
                            b.slow_timer = ICE_SLOW_DURATION
                            ib.alive = False
                            break

                for bomb in bombs:
                    if not bomb.alive:
                        continue
                    was_exploding = bomb.exploding
                    bomb.update()
                    if bomb.exploding and not was_exploding:
                        for b in alive_balls:
                            if b.team_id == bomb.team_id:
                                continue
                            d_b = dist(bomb.x, bomb.y, b.x, b.y)
                            if d_b <= bomb.explosion_radius:
                                b.take_damage(BOMB_DAMAGE)
                                dx = b.x - bomb.x
                                dy = b.y - bomb.y
                                dd = max(d_b, 0.01)
                                b.apply_knockback(dx / dd, dy / dd, BOMB_KNOCKBACK)

                for i in range(len(alive_balls)):
                    for j in range(i + 1, len(alive_balls)):
                        a, b = alive_balls[i], alive_balls[j]
                        if a.team_id == b.team_id:
                            if dist(a.x, a.y, b.x, b.y) <= a.radius + b.radius:
                                resolve_collision(a, b)
                            continue
                        if dist(a.x, a.y, b.x, b.y) <= a.radius + b.radius:
                            # all the same collision logic from game()
                            if a.role == "zombie" and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(ZOMBIE_DAMAGE)
                                a.hit_cooldown = 5
                            if b.role == "zombie" and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(ZOMBIE_DAMAGE)
                                b.hit_cooldown = 5
                            if a.role == "berserker" and a.hit_cooldown == 0:
                                dmg = int(BERSERKER_BASE_DAMAGE * a.rage_multiplier)
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(dmg)
                                a.hit_cooldown = 20
                            if b.role == "berserker" and b.hit_cooldown == 0:
                                dmg = int(BERSERKER_BASE_DAMAGE * b.rage_multiplier)
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(dmg)
                                b.hit_cooldown = 20
                            if a.role == "shield" and a.hit_cooldown == 0:
                                b.take_damage(SHIELD_DAMAGE)
                                a.hit_cooldown = 10
                            if b.role == "shield" and b.hit_cooldown == 0:
                                a.take_damage(SHIELD_DAMAGE)
                                b.hit_cooldown = 10
                            if a.role == "ninja" and a.invisible and a.hit_cooldown == 0:
                                b.take_damage(NINJA_BACKSTAB_DAMAGE)
                                a.invisible = False
                                a.invis_timer = 0
                                a.invis_cooldown = NINJA_INVIS_COOLDOWN
                                a.hit_cooldown = 30
                            if b.role == "ninja" and b.invisible and b.hit_cooldown == 0:
                                a.take_damage(NINJA_BACKSTAB_DAMAGE)
                                b.invisible = False
                                b.invis_timer = 0
                                b.invis_cooldown = NINJA_INVIS_COOLDOWN
                                b.hit_cooldown = 30
                            if a.role == "vampire" and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(VAMPIRE_DAMAGE)
                                    a.hp = min(a.max_hp, a.hp + int(VAMPIRE_DAMAGE * VAMPIRE_LIFESTEAL))
                                a.hit_cooldown = VAMPIRE_HIT_COOLDOWN
                            if b.role == "vampire" and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(VAMPIRE_DAMAGE)
                                    b.hp = min(b.max_hp, b.hp + int(VAMPIRE_DAMAGE * VAMPIRE_LIFESTEAL))
                                b.hit_cooldown = VAMPIRE_HIT_COOLDOWN
                            if a.role == "tank" and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(TANK_DAMAGE)
                                a.hit_cooldown = TANK_HIT_COOLDOWN
                            if b.role == "tank" and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(TANK_DAMAGE)
                                b.hit_cooldown = TANK_HIT_COOLDOWN
                            if a.role == "assassin" and a.assassin_dashing > 0 and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(ASSASSIN_DAMAGE)
                                a.hit_cooldown = 30
                                a.assassin_dashing = 0
                                a.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
                                ddx = a.x - b.x
                                ddy = a.y - b.y
                                dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                a.assassin_retreat_dx = ddx / dd
                                a.assassin_retreat_dy = ddy / dd
                                a.assassin_retreating = ASSASSIN_RETREAT_DURATION
                            if b.role == "assassin" and b.assassin_dashing > 0 and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(ASSASSIN_DAMAGE)
                                b.hit_cooldown = 30
                                b.assassin_dashing = 0
                                b.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
                                ddx = b.x - a.x
                                ddy = b.y - a.y
                                dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                b.assassin_retreat_dx = ddx / dd
                                b.assassin_retreat_dy = ddy / dd
                                b.assassin_retreating = ASSASSIN_RETREAT_DURATION
                            if a.role == "mirror" and a.hit_cooldown == 0:
                                b.take_damage(MIRROR_DAMAGE)
                                a.hit_cooldown = MIRROR_HIT_COOLDOWN
                            if b.role == "mirror" and b.hit_cooldown == 0:
                                a.take_damage(MIRROR_DAMAGE)
                                b.hit_cooldown = MIRROR_HIT_COOLDOWN
                            if a.role == "charger" and a.charging > 0 and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(CHARGER_DAMAGE)
                                    ddx = b.x - a.x
                                    ddy = b.y - a.y
                                    dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                    b.apply_knockback(ddx / dd, ddy / dd, 15.0)
                                a.hit_cooldown = 30
                                a.charging = 0
                                a.charge_cooldown = CHARGER_CHARGE_COOLDOWN
                            if b.role == "charger" and b.charging > 0 and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(CHARGER_DAMAGE)
                                    ddx = a.x - b.x
                                    ddy = a.y - b.y
                                    dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                    a.apply_knockback(ddx / dd, ddy / dd, 15.0)
                                b.hit_cooldown = 30
                                b.charging = 0
                                b.charge_cooldown = CHARGER_CHARGE_COOLDOWN
                            if a.mimic_original and a.mimic_timer <= 0 and b.team_id != a.team_id:
                                a.role = b.role
                                a.speed = ROLE_SPEEDS.get(b.role, 3.0)
                                a.mimic_display_role = b.role
                                a.mimic_timer = MIMIC_COPY_DURATION
                            if b.mimic_original and b.mimic_timer <= 0 and a.team_id != b.team_id:
                                b.role = a.role
                                b.speed = ROLE_SPEEDS.get(a.role, 3.0)
                                b.mimic_display_role = a.role
                                b.mimic_timer = MIMIC_COPY_DURATION
                            resolve_collision(a, b)

                for b in alive_balls:
                    if b.role != "swordsman" or b.hit_cooldown > 0:
                        continue
                    sbx = b.x + math.cos(b.sword_angle) * b.radius
                    sby = b.y + math.sin(b.sword_angle) * b.radius
                    tx, ty = b.sword_tip()
                    for other in alive_balls:
                        if other is b or not other.alive or other.team_id == b.team_id:
                            continue
                        if point_near_segment(other.x, other.y, sbx, sby, tx, ty, other.radius + 3):
                            if other.role == "shield":
                                sa = math.atan2(ty - other.y, tx - other.x)
                                if other.is_angle_in_shield(sa):
                                    b.hit_cooldown = 20
                                    break
                            other.take_damage(SWORD_DAMAGE)
                            b.hit_cooldown = 20
                            ddx = other.x - b.x
                            ddy = other.y - b.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            other.apply_knockback(ddx / dd, ddy / dd, 10.0)
                            break

                for b in alive_balls:
                    if b.role != "chainsaw" or b.hit_cooldown > 0:
                        continue
                    cbx = b.x + math.cos(b.chainsaw_angle) * b.radius
                    cby = b.y + math.sin(b.chainsaw_angle) * b.radius
                    ctx, cty = b.chainsaw_tip()
                    for other in alive_balls:
                        if other is b or not other.alive or other.team_id == b.team_id:
                            continue
                        if point_near_segment(other.x, other.y, cbx, cby, ctx, cty, other.radius + 3):
                            if other.role == "shield":
                                sa = math.atan2(cty - other.y, ctx - other.x)
                                if other.is_angle_in_shield(sa):
                                    continue
                            other.take_damage(CHAINSAW_DAMAGE)
                            b.hit_cooldown = CHAINSAW_HIT_COOLDOWN
                            break

                for w in walls:
                    if not w.alive:
                        continue
                    w.update()
                    if w.exploding:
                        if w.explode_frames == 9:
                            blast_angle = math.atan2(w.blast_dy, w.blast_dx)
                            spread = math.pi / 3
                            for b in alive_balls:
                                if b.team_id == w.team_id:
                                    continue
                                d_w = dist(w.x, w.y, b.x, b.y)
                                if d_w > FORT_EXPLODE_RADIUS:
                                    continue
                                angle_to = math.atan2(b.y - w.y, b.x - w.x)
                                diff = (angle_to - blast_angle + math.pi) % (2 * math.pi) - math.pi
                                if abs(diff) <= spread:
                                    b.take_damage(FORT_EXPLODE_DAMAGE)
                                    ddx = b.x - w.x
                                    ddy = b.y - w.y
                                    dd = max(d_w, 0.01)
                                    b.apply_knockback(ddx / dd, ddy / dd, 12.0)
                        continue
                    x1, y1, x2, y2 = w.endpoints()
                    for b in alive_balls:
                        if b.team_id == w.team_id:
                            continue
                        if point_near_segment(b.x, b.y, x1, y1, x2, y2, b.radius + w.thickness // 2):
                            w.hp -= 1
                            ddx = b.x - w.x
                            ddy = b.y - w.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.apply_knockback(ddx / dd, ddy / dd, 6.0)

                newly_dead = []
                for b in balls:
                    if b.hp <= 0 and b.alive:
                        b.alive = False
                        newly_dead.append(b)
                for necro in alive_balls:
                    if necro.role != "necromancer" or not necro.alive or necro.necro_cooldown > 0:
                        continue
                    for corpse in newly_dead:
                        if corpse.role == "zombie":
                            continue
                        if dist(necro.x, necro.y, corpse.x, corpse.y) <= NECRO_RAISE_RANGE:
                            corpse.alive = True
                            corpse.hp = NECRO_ZOMBIE_HP
                            corpse.max_hp = NECRO_ZOMBIE_HP
                            corpse.team_id = necro.team_id
                            corpse.color = necro.color
                            corpse.role = "zombie"
                            corpse.speed = ZOMBIE_SPEED
                            corpse.hit_cooldown = 0
                            corpse.bounce_timer = 0
                            corpse.pinned_timer = 0
                            corpse.carried_by_spear = False
                            corpse.trapped_in = None
                            necro.necro_cooldown = NECRO_RAISE_COOLDOWN
                            break

                spears = [s for s in spears if s.alive]
                traps = [t_obj for t_obj in traps if t_obj.alive]
                bombs = [bm for bm in bombs if bm.alive]
                bullets = [bl for bl in bullets if bl.alive]
                arrows = [ar for ar in arrows if ar.alive]
                orbs = [orb for orb in orbs if orb.alive]
                ice_bolts = [ib for ib in ice_bolts if ib.alive]
                walls = [w for w in walls if w.alive]

                alive_teams = set(b.team_id for b in balls if b.alive)
                if len(alive_teams) == 1:
                    winner_team = alive_teams.pop()
                elif len(alive_teams) == 0:
                    winner_team = -1

            # draw
            screen_g.fill((20, 20, 30))
            pygame.draw.rect(screen_g, (80, 80, 80), (0, 0, WIDTH, HEIGHT), 2)
            for w in walls:
                w.draw(screen_g)
            for t_obj in traps:
                t_obj.draw(screen_g)
            for bm in bombs:
                bm.draw(screen_g)
            for b in balls:
                b.draw(screen_g)
            for s in spears:
                s.draw(screen_g)
            for bl in bullets:
                bl.draw(screen_g)
            for ar in arrows:
                ar.draw(screen_g)
            for orb in orbs:
                orb.draw(screen_g)
            for ib in ice_bolts:
                ib.draw(screen_g)

            # HUD
            for tid in range(2):
                color = TEAM_COLORS[tid % len(TEAM_COLORS)]
                team_balls = [b for b in balls if b.team_id == tid and b.alive]
                total_hp = sum(b.hp for b in team_balls)
                alive_count = len(team_balls)
                roles = set(b.role for b in team_balls)
                role_str = "/".join(r.capitalize() for r in sorted(roles)) if roles else "Dead"
                text = font.render(f"T{tid+1} {role_str}: {total_hp}HP [{alive_count}]", True, color)
                screen_g.blit(text, (10, 8 + tid * 20))

            if paused:
                speed_text = font.render("PAUSED  (Space)", True, (255, 255, 100))
            else:
                speed_text = font.render(f"Speed: {speed_options[speed_index]}x  (1/2/3/4)", True, (180, 180, 180))
            screen_g.blit(speed_text, (WIDTH - speed_text.get_width() - 10, 8))

            t_secs_left = max(0, (T_STALE_THRESHOLD - t_stale_timer)) // 60
            mt = small_font.render(f"X = Mutate  |  Auto-mutate in {t_secs_left}s", True, (120, 120, 140))
            screen_g.blit(mt, (WIDTH - mt.get_width() - 10, 28))

            if t_recording:
                rec_label = small_font.render("REC", True, (255, 50, 50))
                screen_g.blit(rec_label, (10, HEIGHT - 20))

            pygame.display.flip()
            if t_rec_proc:
                record_frame(t_rec_proc, screen_g)
            clock.tick(60)

    # in realistic mode, convert initial bracket entries to dicts with full HP
    if realistic:
        def to_realistic(team):
            if team is None:
                return None
            if isinstance(team, dict):
                return team
            roles = team
            hp = [TANK_HP if r == "tank" else 100 for r in roles]
            return {"roles": roles, "hp": hp}
        for ri in range(len(rounds)):
            rounds[ri] = [(to_realistic(a), to_realistic(b), w) for a, b, w in rounds[ri]]

    # run through all rounds
    champion = None
    for ri, matchups in enumerate(rounds):
        winners = []
        for mi, (a, b, _) in enumerate(matchups):
            if a is None and b is None:
                winners.append(None)
                rounds[ri][mi] = (a, b, None)
                continue
            if a is None:
                winners.append(b)
                rounds[ri][mi] = (a, b, b)
                continue
            if b is None:
                winners.append(a)
                rounds[ri][mi] = (a, b, a)
                continue

            # show bracket before match
            show_bracket_screen(rounds, ri, mi, f"Round {ri+1} Match {mi+1}: Click to start")

            # play the match
            a_roles = get_roles(a)
            b_roles = get_roles(b)
            hp_a = a["hp"] if realistic and isinstance(a, dict) else None
            hp_b = b["hp"] if realistic and isinstance(b, dict) else None
            winner_result = play_match(a_roles, b_roles, hp_a, hp_b)
            if winner_result == "abort":
                return
            rounds[ri][mi] = (a, b, winner_result)
            winners.append(winner_result)

        # between rounds: apply 15 HP regen in realistic mode
        if realistic:
            for w in winners:
                if w is not None and isinstance(w, dict):
                    max_hps = [TANK_HP if r == "tank" else 100 for r in w["roles"]]
                    w["hp"] = [min(hp + 15, mx) for hp, mx in zip(w["hp"], max_hps)]

        # build next round from winners
        if ri + 1 < len(rounds):
            next_matchups = []
            for i in range(0, len(winners), 2):
                na = winners[i]
                nb = winners[i + 1] if i + 1 < len(winners) else None
                next_matchups.append((na, nb, None))
            rounds[ri + 1] = next_matchups
        else:
            champion = winners[0] if winners else None

    # show final bracket
    if champion:
        champ_str = "/".join(r.capitalize() for r in get_roles(champion))
    else:
        champ_str = "???"
    show_bracket_screen(rounds, len(rounds) - 1, 0, f"Champion: {champ_str}!  Click to return to menu")


# ── Interactive Roguelike Mode ─────────────────────────────
def interactive_mode():
    global WIDTH, HEIGHT, screen, BALL_RADIUS, SWORD_LENGTH, TRAP_RADIUS

    ROLE_PRICES = {
        "zombie": 30,
        "swordsman": 40, "spearman": 75, "trapper": 75,
        "berserker": 50, "chainsaw": 50, "charger": 50, "bomber": 50,
        "vampire": 60, "archer": 60, "fortifier": 60, "ice_mage": 60,
        "ninja": 75, "assassin": 75, "shield": 75, "wizard": 75, "summoner": 75,
        "sniper": 80, "mimic": 80, "mirror": 80,
        "healer": 100, "necromancer": 75, "tank": 100,
    }
    KILL_BOUNTY = {
        "zombie": 10, "swordsman": 15, "spearman": 15, "trapper": 15,
        "berserker": 20, "chainsaw": 20, "charger": 20, "bomber": 20,
        "vampire": 25, "archer": 25, "fortifier": 25, "ice_mage": 25,
        "ninja": 30, "assassin": 30, "shield": 30, "wizard": 30, "summoner": 30,
        "sniper": 35, "mimic": 35, "mirror": 35,
        "healer": 40, "necromancer": 30, "tank": 40,
    }
    HEAL_POTION_COST = 30
    SHOP_ROLES = [
        "zombie", "swordsman", "spearman", "trapper",
        "berserker", "chainsaw", "charger", "bomber",
        "vampire", "archer", "fortifier", "ice_mage",
        "ninja", "assassin", "shield", "wizard", "summoner",
        "sniper", "mimic", "mirror",
        "healer", "necromancer", "tank",
    ]

    def get_arena_size(total):
        if total <= 3:
            return 450, 340
        elif total <= 6:
            return 600, 450
        elif total <= 10:
            return 660, 495
        elif total <= 16:
            return 720, 540
        elif total <= 24:
            return 792, 594
        elif total <= 35:
            return 860, 645
        else:
            return 960, 720

    # structured waves — each wave has a fixed roster, gets harder each level
    WAVE_TABLE = {
        1:  ["zombie"],
        2:  ["zombie", "zombie"],
        3:  ["swordsman", "zombie"],
        4:  ["swordsman", "spearman"],
        5:  ["zombie", "zombie", "swordsman"],
        6:  ["trapper", "swordsman", "zombie"],
        7:  ["berserker", "spearman", "zombie"],
        8:  ["bomber", "chainsaw", "swordsman"],
        9:  ["trapper", "berserker", "spearman", "zombie"],
        10: ["vampire", "swordsman", "zombie", "zombie"],
        11: ["archer", "chainsaw", "bomber", "zombie"],
        12: ["fortifier", "ice_mage", "spearman", "swordsman"],
        13: ["charger", "vampire", "berserker", "trapper"],
        14: ["archer", "ice_mage", "chainsaw", "swordsman", "zombie"],
        15: ["ninja", "vampire", "berserker", "spearman", "zombie"],
        16: ["assassin", "shield", "archer", "swordsman", "zombie"],
        17: ["wizard", "fortifier", "charger", "chainsaw", "trapper"],
        18: ["summoner", "ninja", "vampire", "berserker", "spearman"],
        19: ["sniper", "shield", "assassin", "archer", "ice_mage", "zombie"],
        20: ["healer", "tank", "wizard", "charger", "berserker", "swordsman"],
        21: ["necromancer", "vampire", "ninja", "assassin", "bomber", "chainsaw"],
        22: ["mirror", "mimic", "sniper", "shield", "wizard", "summoner"],
        23: ["tank", "healer", "necromancer", "assassin", "ninja", "charger", "berserker"],
        24: ["sniper", "wizard", "archer", "ice_mage", "fortifier", "shield", "summoner"],
        25: ["tank", "healer", "necromancer", "mirror", "mimic", "sniper", "assassin", "ninja"],
    }

    def get_enemy_wave(wave):
        if wave in WAVE_TABLE:
            return list(WAVE_TABLE[wave])
        # past wave 25: use wave 25 as base, add 1 extra unit per 2 waves
        base = list(WAVE_TABLE[25])
        extras = (wave - 25) // 2
        all_hard = ["tank", "healer", "necromancer", "sniper", "assassin", "ninja",
                    "wizard", "mirror", "mimic", "charger", "shield", "summoner",
                    "vampire", "berserker", "archer", "ice_mage", "fortifier"]
        for _ in range(extras):
            base.append(random.choice(all_hard))
        return base

    # ── shop screen ──
    def shop_screen(player_team, gold, wave, next_enemies):
        global WIDTH, HEIGHT, screen
        # width as wide as needed, height capped at 700
        shop_w = max(800, 220 + len(SHOP_ROLES) * 52)
        MAX_SHOP_H = 700
        content_h = max(500, 160 + max(len(player_team), len(next_enemies)) * 48 + 140)
        shop_h = min(content_h, MAX_SHOP_H)
        WIDTH, HEIGHT = shop_w, shop_h
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

        selected_ball = None
        scroll_offset = 0  # shop role scroll
        max_visible = max(1, (WIDTH - 240) // 52)
        max_scroll = max(0, len(SHOP_ROLES) - max_visible)
        view_scroll = 0  # vertical scroll for the whole view
        max_view_scroll = max(0, content_h - shop_h)
        message = ""
        message_timer = 0

        while True:
            mx, my = pygame.mouse.get_pos()
            # adjust mouse y for vertical scroll
            amy = my + view_scroll
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                    # scroll up: try view scroll first, then shop scroll
                    if view_scroll > 0:
                        view_scroll = max(0, view_scroll - 30)
                    else:
                        scroll_offset = max(0, scroll_offset - 1)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                    # scroll down: try view scroll first, then shop scroll
                    if view_scroll < max_view_scroll:
                        view_scroll = min(max_view_scroll, view_scroll + 30)
                    else:
                        scroll_offset = min(max_scroll, scroll_offset + 1)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # fight button (fixed at bottom of screen)
                    fight_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 50, 120, 40)
                    if fight_rect.collidepoint(mx, my) and len(player_team) > 0:
                        return "fight", player_team, gold
                    # quit button (fixed at bottom of screen)
                    quit_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT - 50, 120, 40)
                    if quit_rect.collidepoint(mx, my):
                        return "quit", player_team, gold

                    # click on player ball to select (scrolled)
                    for i, info in enumerate(player_team):
                        bx, by = 55, 120 + i * 48 - view_scroll
                        if (mx - bx) ** 2 + (my - by) ** 2 <= (BALL_RADIUS + 8) ** 2:
                            selected_ball = i
                            break

                    # heal button (scrolled)
                    if selected_ball is not None and 0 <= selected_ball < len(player_team):
                        heal_rect = pygame.Rect(140, 120 + selected_ball * 48 - 14 - view_scroll, 50, 28)
                        if heal_rect.collidepoint(mx, my):
                            info = player_team[selected_ball]
                            max_hp = TANK_HP if info["role"] == "tank" else 100
                            if gold >= HEAL_POTION_COST and info["hp"] < max_hp:
                                gold -= HEAL_POTION_COST
                                info["hp"] = max_hp
                                message = f"Healed {info['role'].capitalize()}!"
                                message_timer = 120

                    # sell button (scrolled)
                    if selected_ball is not None and 0 <= selected_ball < len(player_team):
                        sell_rect = pygame.Rect(140, 120 + selected_ball * 48 + 16 - view_scroll, 50, 28)
                        if sell_rect.collidepoint(mx, my):
                            info = player_team[selected_ball]
                            sell_price = ROLE_PRICES.get(info["role"], 30) // 2
                            gold += sell_price
                            sold_name = info["role"].capitalize()
                            player_team.pop(selected_ball)
                            selected_ball = None
                            message = f"Sold {sold_name}! (+{sell_price}g)"
                            message_timer = 120

                    # buy role (fixed near bottom)
                    buy_y = HEIGHT - 100
                    for idx in range(len(SHOP_ROLES)):
                        vi = idx - scroll_offset
                        if vi < 0 or vi >= max_visible:
                            continue
                        rx = 120 + vi * 52
                        role_rect = pygame.Rect(rx, buy_y, 48, 60)
                        if role_rect.collidepoint(mx, my):
                            role = SHOP_ROLES[idx]
                            price = ROLE_PRICES[role]
                            if gold >= price:
                                gold -= price
                                max_hp = TANK_HP if role == "tank" else 100
                                player_team.append({"role": role, "hp": max_hp})
                                message = f"Bought {role.capitalize()}! (-{price}g)"
                                message_timer = 120
                                max_view_scroll = max(0, (160 + max(len(player_team), len(next_enemies)) * 48 + 140) - shop_h)
                            else:
                                message = f"Not enough gold! Need {price}g"
                                message_timer = 120
                            break

            # ── draw shop ──
            screen.fill((24, 24, 36))
            vs = view_scroll  # shorthand

            # title (fixed at top)
            title = title_font.render(f"Wave {wave}", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 12))
            gold_text = font.render(f"Gold: {gold}", True, (255, 215, 80))
            screen.blit(gold_text, (WIDTH // 2 - gold_text.get_width() // 2, 52))

            # scroll indicator
            if max_view_scroll > 0:
                si = small_font.render(f"Scroll: {view_scroll}/{max_view_scroll}", True, (100, 100, 120))
                screen.blit(si, (10, 55))

            # left panel: your team (scrollable)
            panel_h = max(200, len(player_team) * 48 + 40)
            pygame.draw.rect(screen, (35, 40, 55), (10, 90 - vs, 195, panel_h), border_radius=8)
            team_label = font.render("Your Team", True, (120, 200, 255))
            screen.blit(team_label, (55, 95 - vs))
            for i, info in enumerate(player_team):
                bx, by = 55, 120 + i * 48 - vs
                if by < 60 or by > HEIGHT - 120:
                    continue  # clip off-screen items
                role = info["role"]
                hp = info["hp"]
                max_hp = TANK_HP if role == "tank" else 100
                c = TEAM_COLORS[0]
                pygame.draw.circle(screen, c, (bx, by), 14)
                if selected_ball == i:
                    pygame.draw.circle(screen, (255, 255, 100), (bx, by), 17, 2)
                rl = small_font.render(role.capitalize(), True, (220, 220, 255))
                screen.blit(rl, (bx + 20, by - 14))
                bar_w = 70
                bar_x = bx + 20
                bar_y = by + 4
                pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, 6))
                hp_frac = max(0, hp / max_hp)
                bar_color = (0, 200, 0) if hp_frac > 0.4 else (200, 200, 0) if hp_frac > 0.2 else (200, 0, 0)
                pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_w * hp_frac), 6))
                hp_label = small_font.render(f"{hp}/{max_hp}", True, (180, 180, 180))
                screen.blit(hp_label, (bar_x + bar_w + 4, bar_y - 4))

            # heal & sell buttons for selected (scrollable)
            if selected_ball is not None and 0 <= selected_ball < len(player_team):
                sel_y = 120 + selected_ball * 48 - vs
                if 60 < sel_y < HEIGHT - 120:
                    # heal
                    heal_rect = pygame.Rect(140, sel_y - 14, 50, 28)
                    hc = (60, 180, 60) if heal_rect.collidepoint(mx, my) else (50, 140, 50)
                    pygame.draw.rect(screen, hc, heal_rect, border_radius=4)
                    hl = small_font.render("Heal", True, (255, 255, 255))
                    screen.blit(hl, (heal_rect.centerx - hl.get_width() // 2, heal_rect.centery - hl.get_height() // 2))
                    price_l = small_font.render(f"{HEAL_POTION_COST}g", True, (255, 215, 80))
                    screen.blit(price_l, (heal_rect.right + 4, heal_rect.centery - price_l.get_height() // 2))
                    # sell
                    sell_rect = pygame.Rect(140, sel_y + 16, 50, 28)
                    sc = (180, 60, 60) if sell_rect.collidepoint(mx, my) else (140, 50, 50)
                    pygame.draw.rect(screen, sc, sell_rect, border_radius=4)
                    sl = small_font.render("Sell", True, (255, 255, 255))
                    screen.blit(sl, (sell_rect.centerx - sl.get_width() // 2, sell_rect.centery - sl.get_height() // 2))
                    sell_price = ROLE_PRICES.get(player_team[selected_ball]["role"], 30) // 2
                    sp_l = small_font.render(f"+{sell_price}g", True, (255, 215, 80))
                    screen.blit(sp_l, (sell_rect.right + 4, sell_rect.centery - sp_l.get_height() // 2))

            # right panel: enemy preview (scrollable)
            epanel_x = WIDTH - 195
            epanel_h = max(200, len(next_enemies) * 40 + 40)
            pygame.draw.rect(screen, (55, 35, 35), (epanel_x, 90 - vs, 185, epanel_h), border_radius=8)
            enemy_label = font.render("Next Wave", True, (255, 120, 120))
            screen.blit(enemy_label, (epanel_x + 40, 95 - vs))
            for i, role in enumerate(next_enemies):
                ey = 120 + i * 40 - vs
                if ey < 60 or ey > HEIGHT - 120:
                    continue
                pygame.draw.circle(screen, TEAM_COLORS[1], (epanel_x + 30, ey), 12)
                rl = small_font.render(role.capitalize(), True, (255, 180, 180))
                screen.blit(rl, (epanel_x + 50, ey - 8))

            # bottom: shop row
            buy_y = HEIGHT - 100
            pygame.draw.rect(screen, (30, 30, 48), (110, buy_y - 8, WIDTH - 220, 76), border_radius=8)
            shop_label = small_font.render("Buy Units:", True, (180, 180, 200))
            screen.blit(shop_label, (120, buy_y - 22))
            # scroll arrows
            if scroll_offset > 0:
                arrow_l = font.render("<", True, (200, 200, 200))
                screen.blit(arrow_l, (112, buy_y + 18))
            if scroll_offset < max_scroll:
                arrow_r = font.render(">", True, (200, 200, 200))
                screen.blit(arrow_r, (WIDTH - 118, buy_y + 18))
            for idx in range(len(SHOP_ROLES)):
                vi = idx - scroll_offset
                if vi < 0 or vi >= max_visible:
                    continue
                rx = 120 + vi * 52
                role = SHOP_ROLES[idx]
                price = ROLE_PRICES[role]
                role_rect = pygame.Rect(rx, buy_y, 48, 60)
                can_afford = gold >= price
                bg = (50, 60, 80) if can_afford else (40, 35, 35)
                if role_rect.collidepoint(mx, my) and can_afford:
                    bg = (70, 80, 110)
                pygame.draw.rect(screen, bg, role_rect, border_radius=4)
                pygame.draw.rect(screen, (120, 120, 140), role_rect, 1, border_radius=4)
                # role name (abbreviated to fit)
                name = role[:6].capitalize()
                nl = small_font.render(name, True, (255, 255, 255) if can_afford else (120, 120, 120))
                screen.blit(nl, (rx + 24 - nl.get_width() // 2, buy_y + 6))
                # price
                pl = small_font.render(f"{price}g", True, (255, 215, 80) if can_afford else (100, 90, 50))
                screen.blit(pl, (rx + 24 - pl.get_width() // 2, buy_y + 40))

            # fight / quit buttons
            fight_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 50, 120, 40)
            quit_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT - 50, 120, 40)
            fc = (60, 180, 60) if fight_rect.collidepoint(mx, my) else (50, 150, 50)
            qc = (180, 60, 60) if quit_rect.collidepoint(mx, my) else (150, 50, 50)
            pygame.draw.rect(screen, fc, fight_rect, border_radius=6)
            pygame.draw.rect(screen, qc, quit_rect, border_radius=6)
            fl = font.render("FIGHT!", True, (255, 255, 255))
            ql = font.render("QUIT", True, (255, 255, 255))
            screen.blit(fl, (fight_rect.centerx - fl.get_width() // 2, fight_rect.centery - fl.get_height() // 2))
            screen.blit(ql, (quit_rect.centerx - ql.get_width() // 2, quit_rect.centery - ql.get_height() // 2))

            # message
            if message_timer > 0:
                message_timer -= 1
                msg = font.render(message, True, (255, 255, 180))
                screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 140))

            pygame.display.flip()
            clock.tick(60)

    # ── battle ──
    def run_battle(player_team, enemy_roles):
        global WIDTH, HEIGHT, screen, BALL_RADIUS, SWORD_LENGTH, TRAP_RADIUS

        total = len(player_team) + len(enemy_roles)
        aw, ah = get_arena_size(total)
        WIDTH, HEIGHT = aw, ah
        if total > 6:
            BALL_RADIUS = max(12, BASE_BALL_RADIUS - (total - 6) * 2)
        else:
            BALL_RADIUS = BASE_BALL_RADIUS
        SWORD_LENGTH = BALL_RADIUS * 2
        TRAP_RADIUS = BALL_RADIUS * 4
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

        # spawn player balls with HP overrides
        configs = []
        for info in player_team:
            configs.append({"team_id": 0, "role": info["role"]})
        for role in enemy_roles:
            configs.append({"team_id": 1, "role": role})
        balls = spawn_balls(configs)
        # apply saved HP to player balls
        pi = 0
        for b in balls:
            if b.team_id == 0 and pi < len(player_team):
                b.hp = player_team[pi]["hp"]
                pi += 1

        spears, traps, bombs, bullets, arrows, orbs, ice_bolts, walls = [], [], [], [], [], [], [], []
        speed_options = [1, 2, 4, 10]
        speed_index = 0
        paused = False
        winner_team = None
        stale_timer = 0
        STALE_THRESHOLD = 7200
        kill_gold = 0  # gold earned from killing enemies

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    if event.key == pygame.K_1:
                        speed_index = 0
                    if event.key == pygame.K_2:
                        speed_index = 1
                    if event.key == pygame.K_3:
                        speed_index = 2
                    if event.key == pygame.K_4:
                        speed_index = 3

            if winner_team is not None:
                # return survivors + gold earned from kills
                survivors = []
                for b in balls:
                    if b.team_id == 0 and b.alive:
                        survivors.append({"role": b.role, "hp": b.hp})
                return survivors, (winner_team == 0), kill_gold

            game_speed = speed_options[speed_index]

            for _tick in range(game_speed):
                if winner_team is not None or paused:
                    break

                stale_timer += 1
                if stale_timer >= STALE_THRESHOLD:
                    # mutate: replace one unit from each team with random melee
                    melee_list = list(Ball.MELEE_ROLES)
                    alive_teams_map = {}
                    for b in balls:
                        if b.alive:
                            alive_teams_map.setdefault(b.team_id, []).append(b)
                    for tid, members in alive_teams_map.items():
                        victim = random.choice(members)
                        victim.alive = False
                        victim.hp = 0
                        new_role = random.choice(melee_list)
                        color = TEAM_COLORS[tid % len(TEAM_COLORS)]
                        new_ball = Ball(victim.x, victim.y, color, tid, new_role)
                        balls.append(new_ball)
                    stale_timer = 0

                alive_balls = [b for b in balls if b.alive]
                for b in alive_balls:
                    target = b.find_target(alive_balls)
                    b.seek(target, alive_balls)
                    b.move()
                    b.try_throw_spear(target, spears)
                    b.try_place_trap(target, traps)
                    b.try_drop_bomb(target, bombs)
                    b.try_heal(alive_balls)
                    b.aim_shield(alive_balls)
                    b.try_fire_bullet(target, bullets)
                    b.try_fire_arrow(target, arrows)
                    b.try_cast_orb(target, orbs)
                    b.try_fire_ice_bolt(target, ice_bolts)
                    b.try_place_wall(target, walls, alive_balls)

                # summoner spawns
                for b in alive_balls:
                    if b.role != "summoner" or b.summon_cooldown > 0:
                        continue
                    b.minions = [m for m in b.minions if m.alive]
                    if len(b.minions) >= SUMMONER_MAX_MINIONS:
                        continue
                    angle = random.uniform(0, 2 * math.pi)
                    smx = b.x + math.cos(angle) * (b.radius * 2.5)
                    smy = b.y + math.sin(angle) * (b.radius * 2.5)
                    smx = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, smx))
                    smy = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, smy))
                    minion = Ball(smx, smy, b.color, b.team_id, "zombie")
                    minion.hp = SUMMONER_MINION_HP
                    minion.max_hp = SUMMONER_MINION_HP
                    minion.radius = max(8, int(BALL_RADIUS * SUMMONER_MINION_RADIUS_SCALE))
                    minion.is_minion = True
                    balls.append(minion)
                    b.minions.append(minion)
                    b.summon_cooldown = SUMMONER_COOLDOWN

                # spear movement & hits
                for s in spears:
                    if s.alive:
                        s.move()
                for s in spears:
                    if not s.alive or s.carried_ball is not None:
                        continue
                    for b in alive_balls:
                        if b.team_id == s.team_id or b.carried_by_spear:
                            continue
                        if dist(s.x, s.y, b.x, b.y) <= b.radius + 5:
                            if b.role == "mirror":
                                s.dx = -s.dx
                                s.dy = -s.dy
                                s.angle = math.atan2(s.dy, s.dx)
                                s.team_id = b.team_id
                                s.x += s.dx * 2
                                s.y += s.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(s.y - b.y, s.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    s.alive = False
                                    break
                            b.take_damage(SPEAR_DAMAGE)
                            if b.trapped_in is not None:
                                b.trapped_in.captured_ball = None
                                b.trapped_in.alive = False
                                b.trapped_in = None
                            b.carried_by_spear = True
                            b.pinned_timer = 0
                            b.vx = 0
                            b.vy = 0
                            s.carried_ball = b
                            break

                # trap trigger & update
                for t in traps:
                    if not t.alive:
                        continue
                    if t.captured_ball is not None:
                        t.update()
                        continue
                    for b in alive_balls:
                        if b.team_id == t.team_id or b.trapped_in is not None or b.carried_by_spear or b.pinned_timer > 0:
                            continue
                        if dist(t.x, t.y, b.x, b.y) <= t.radius:
                            t.captured_ball = b
                            b.trapped_in = t
                            ta = random.uniform(0, 2 * math.pi)
                            b.vx = math.cos(ta) * 4.0
                            b.vy = math.sin(ta) * 4.0
                            b.bounce_timer = 0
                            break

                # bullets
                for bl in bullets:
                    if bl.alive:
                        bl.move()
                for bl in bullets:
                    if not bl.alive:
                        continue
                    for b in alive_balls:
                        if b.team_id == bl.team_id:
                            continue
                        if dist(bl.x, bl.y, b.x, b.y) <= b.radius + 3:
                            if b.role == "mirror":
                                bl.dx = -bl.dx
                                bl.dy = -bl.dy
                                bl.angle = math.atan2(bl.dy, bl.dx)
                                bl.team_id = b.team_id
                                bl.x += bl.dx * 2
                                bl.y += bl.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(bl.y - b.y, bl.x - b.x)
                                if b.is_angle_in_shield(sa, attacker_role="sniper"):
                                    bl.alive = False
                                    break
                            b.take_damage(SNIPER_DAMAGE)
                            bl.alive = False
                            ddx = b.x - bl.x
                            ddy = b.y - bl.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.apply_knockback(ddx / dd, ddy / dd, 5.0)
                            break

                # arrows
                for ar in arrows:
                    if ar.alive:
                        ar.move()
                for ar in arrows:
                    if not ar.alive:
                        continue
                    for b in alive_balls:
                        if b.team_id == ar.team_id:
                            continue
                        if dist(ar.x, ar.y, b.x, b.y) <= b.radius + 4:
                            if b.role == "mirror":
                                ar.dx = -ar.dx
                                ar.dy = -ar.dy
                                ar.angle = math.atan2(ar.dy, ar.dx)
                                ar.team_id = b.team_id
                                ar.x += ar.dx * 2
                                ar.y += ar.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(ar.y - b.y, ar.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    ar.alive = False
                                    break
                            b.take_damage(ARCHER_DAMAGE)
                            ar.alive = False
                            ddx = b.x - ar.x
                            ddy = b.y - ar.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.apply_knockback(ddx / dd, ddy / dd, 3.0)
                            break

                # orbs
                for orb in orbs:
                    if not orb.alive:
                        continue
                    orb.move()
                    if orb.exploding:
                        continue
                    for b in alive_balls:
                        if b.team_id == orb.team_id:
                            continue
                        if dist(orb.x, orb.y, b.x, b.y) <= b.radius + 6:
                            if b.role == "mirror":
                                orb.dx = -orb.dx
                                orb.dy = -orb.dy
                                orb.team_id = b.team_id
                                orb.x += orb.dx * 2
                                orb.y += orb.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(orb.y - b.y, orb.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    orb.alive = False
                                    break
                            b.take_damage(WIZARD_DAMAGE)
                            orb.exploding = True
                            for other in alive_balls:
                                if other is b or other.team_id == orb.team_id:
                                    continue
                                if dist(orb.x, orb.y, other.x, other.y) <= WIZARD_SPLASH_RADIUS:
                                    other.take_damage(WIZARD_SPLASH_DAMAGE)
                            break

                # ice bolts
                for ib in ice_bolts:
                    if not ib.alive:
                        continue
                    ib.move()
                    for b in alive_balls:
                        if b.team_id == ib.team_id:
                            continue
                        if dist(ib.x, ib.y, b.x, b.y) <= b.radius + 4:
                            if b.role == "mirror":
                                ib.dx = -ib.dx
                                ib.dy = -ib.dy
                                ib.angle = math.atan2(ib.dy, ib.dx)
                                ib.team_id = b.team_id
                                ib.x += ib.dx * 2
                                ib.y += ib.dy * 2
                                break
                            if b.role == "shield":
                                sa = math.atan2(ib.y - b.y, ib.x - b.x)
                                if b.is_angle_in_shield(sa):
                                    ib.alive = False
                                    break
                            b.take_damage(ICE_MAGE_DAMAGE)
                            b.slow_timer = ICE_SLOW_DURATION
                            ib.alive = False
                            break

                # bombs
                for bomb in bombs:
                    if not bomb.alive:
                        continue
                    was_exploding = bomb.exploding
                    bomb.update()
                    if bomb.exploding and not was_exploding:
                        for b in alive_balls:
                            if b.team_id == bomb.team_id:
                                continue
                            d_b = dist(bomb.x, bomb.y, b.x, b.y)
                            if d_b <= bomb.explosion_radius:
                                b.take_damage(BOMB_DAMAGE)
                                dx = b.x - bomb.x
                                dy = b.y - bomb.y
                                dd = max(d_b, 0.01)
                                b.apply_knockback(dx / dd, dy / dd, BOMB_KNOCKBACK)

                # ball-ball collisions
                for i in range(len(alive_balls)):
                    for j in range(i + 1, len(alive_balls)):
                        a, b = alive_balls[i], alive_balls[j]
                        if a.team_id == b.team_id:
                            if dist(a.x, a.y, b.x, b.y) <= a.radius + b.radius:
                                resolve_collision(a, b)
                            continue
                        if dist(a.x, a.y, b.x, b.y) <= a.radius + b.radius:
                            if a.role == "zombie" and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(ZOMBIE_DAMAGE)
                                a.hit_cooldown = 5
                            if b.role == "zombie" and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(ZOMBIE_DAMAGE)
                                b.hit_cooldown = 5
                            if a.role == "berserker" and a.hit_cooldown == 0:
                                dmg = int(BERSERKER_BASE_DAMAGE * a.rage_multiplier)
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(dmg)
                                a.hit_cooldown = 20
                            if b.role == "berserker" and b.hit_cooldown == 0:
                                dmg = int(BERSERKER_BASE_DAMAGE * b.rage_multiplier)
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(dmg)
                                b.hit_cooldown = 20
                            if a.role == "shield" and a.hit_cooldown == 0:
                                b.take_damage(SHIELD_DAMAGE)
                                a.hit_cooldown = 10
                            if b.role == "shield" and b.hit_cooldown == 0:
                                a.take_damage(SHIELD_DAMAGE)
                                b.hit_cooldown = 10
                            if a.role == "ninja" and a.invisible and a.hit_cooldown == 0:
                                b.take_damage(NINJA_BACKSTAB_DAMAGE)
                                a.invisible = False
                                a.invis_timer = 0
                                a.invis_cooldown = NINJA_INVIS_COOLDOWN
                                a.hit_cooldown = 30
                            if b.role == "ninja" and b.invisible and b.hit_cooldown == 0:
                                a.take_damage(NINJA_BACKSTAB_DAMAGE)
                                b.invisible = False
                                b.invis_timer = 0
                                b.invis_cooldown = NINJA_INVIS_COOLDOWN
                                b.hit_cooldown = 30
                            if a.role == "vampire" and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(VAMPIRE_DAMAGE)
                                    a.hp = min(a.max_hp, a.hp + int(VAMPIRE_DAMAGE * VAMPIRE_LIFESTEAL))
                                a.hit_cooldown = VAMPIRE_HIT_COOLDOWN
                            if b.role == "vampire" and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(VAMPIRE_DAMAGE)
                                    b.hp = min(b.max_hp, b.hp + int(VAMPIRE_DAMAGE * VAMPIRE_LIFESTEAL))
                                b.hit_cooldown = VAMPIRE_HIT_COOLDOWN
                            if a.role == "tank" and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(TANK_DAMAGE)
                                a.hit_cooldown = TANK_HIT_COOLDOWN
                            if b.role == "tank" and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(TANK_DAMAGE)
                                b.hit_cooldown = TANK_HIT_COOLDOWN
                            if a.role == "assassin" and a.assassin_dashing > 0 and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(ASSASSIN_DAMAGE)
                                a.hit_cooldown = 30
                                a.assassin_dashing = 0
                                a.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
                                ddx = a.x - b.x
                                ddy = a.y - b.y
                                dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                a.assassin_retreat_dx = ddx / dd
                                a.assassin_retreat_dy = ddy / dd
                                a.assassin_retreating = ASSASSIN_RETREAT_DURATION
                            if b.role == "assassin" and b.assassin_dashing > 0 and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(ASSASSIN_DAMAGE)
                                b.hit_cooldown = 30
                                b.assassin_dashing = 0
                                b.assassin_dash_cooldown = ASSASSIN_DASH_COOLDOWN
                                ddx = b.x - a.x
                                ddy = b.y - a.y
                                dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                b.assassin_retreat_dx = ddx / dd
                                b.assassin_retreat_dy = ddy / dd
                                b.assassin_retreating = ASSASSIN_RETREAT_DURATION
                            if a.role == "mirror" and a.hit_cooldown == 0:
                                b.take_damage(MIRROR_DAMAGE)
                                a.hit_cooldown = MIRROR_HIT_COOLDOWN
                            if b.role == "mirror" and b.hit_cooldown == 0:
                                a.take_damage(MIRROR_DAMAGE)
                                b.hit_cooldown = MIRROR_HIT_COOLDOWN
                            if a.role == "charger" and a.charging > 0 and a.hit_cooldown == 0:
                                blocked = False
                                if b.role == "shield":
                                    sa = math.atan2(a.y - b.y, a.x - b.x)
                                    blocked = b.is_angle_in_shield(sa)
                                if not blocked:
                                    b.take_damage(CHARGER_DAMAGE)
                                    ddx = b.x - a.x
                                    ddy = b.y - a.y
                                    dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                    b.apply_knockback(ddx / dd, ddy / dd, 15.0)
                                a.hit_cooldown = 30
                                a.charging = 0
                                a.charge_cooldown = CHARGER_CHARGE_COOLDOWN
                            if b.role == "charger" and b.charging > 0 and b.hit_cooldown == 0:
                                blocked = False
                                if a.role == "shield":
                                    sa = math.atan2(b.y - a.y, b.x - a.x)
                                    blocked = a.is_angle_in_shield(sa)
                                if not blocked:
                                    a.take_damage(CHARGER_DAMAGE)
                                    ddx = a.x - b.x
                                    ddy = a.y - b.y
                                    dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                                    a.apply_knockback(ddx / dd, ddy / dd, 15.0)
                                b.hit_cooldown = 30
                                b.charging = 0
                                b.charge_cooldown = CHARGER_CHARGE_COOLDOWN
                            if a.mimic_original and a.mimic_timer <= 0 and b.team_id != a.team_id:
                                a.role = b.role
                                a.speed = ROLE_SPEEDS.get(b.role, 3.0)
                                a.mimic_display_role = b.role
                                a.mimic_timer = MIMIC_COPY_DURATION
                            if b.mimic_original and b.mimic_timer <= 0 and a.team_id != b.team_id:
                                b.role = a.role
                                b.speed = ROLE_SPEEDS.get(a.role, 3.0)
                                b.mimic_display_role = a.role
                                b.mimic_timer = MIMIC_COPY_DURATION
                            resolve_collision(a, b)

                # sword hits
                for b in alive_balls:
                    if b.role != "swordsman" or b.hit_cooldown > 0:
                        continue
                    sbx = b.x + math.cos(b.sword_angle) * b.radius
                    sby = b.y + math.sin(b.sword_angle) * b.radius
                    tx, ty = b.sword_tip()
                    for other in alive_balls:
                        if other is b or not other.alive or other.team_id == b.team_id:
                            continue
                        if point_near_segment(other.x, other.y, sbx, sby, tx, ty, other.radius + 3):
                            if other.role == "shield":
                                sa = math.atan2(ty - other.y, tx - other.x)
                                if other.is_angle_in_shield(sa):
                                    b.hit_cooldown = 20
                                    break
                            other.take_damage(SWORD_DAMAGE)
                            b.hit_cooldown = 20
                            ddx = other.x - b.x
                            ddy = other.y - b.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            other.apply_knockback(ddx / dd, ddy / dd, 10.0)
                            break

                # chainsaw hits
                for b in alive_balls:
                    if b.role != "chainsaw" or b.hit_cooldown > 0:
                        continue
                    cbx = b.x + math.cos(b.chainsaw_angle) * b.radius
                    cby = b.y + math.sin(b.chainsaw_angle) * b.radius
                    ctx, cty = b.chainsaw_tip()
                    for other in alive_balls:
                        if other is b or not other.alive or other.team_id == b.team_id:
                            continue
                        if point_near_segment(other.x, other.y, cbx, cby, ctx, cty, other.radius + 3):
                            if other.role == "shield":
                                sa = math.atan2(cty - other.y, ctx - other.x)
                                if other.is_angle_in_shield(sa):
                                    continue
                            other.take_damage(CHAINSAW_DAMAGE)
                            b.hit_cooldown = CHAINSAW_HIT_COOLDOWN
                            break

                # wall collisions
                for w in walls:
                    if not w.alive:
                        continue
                    w.update()
                    if w.exploding:
                        if w.explode_frames == 9:
                            blast_angle = math.atan2(w.blast_dy, w.blast_dx)
                            spread = math.pi / 3
                            for b in alive_balls:
                                if b.team_id == w.team_id:
                                    continue
                                d_w = dist(w.x, w.y, b.x, b.y)
                                if d_w > FORT_EXPLODE_RADIUS:
                                    continue
                                angle_to = math.atan2(b.y - w.y, b.x - w.x)
                                diff = (angle_to - blast_angle + math.pi) % (2 * math.pi) - math.pi
                                if abs(diff) <= spread:
                                    b.take_damage(FORT_EXPLODE_DAMAGE)
                                    ddx = b.x - w.x
                                    ddy = b.y - w.y
                                    dd = max(d_w, 0.01)
                                    b.apply_knockback(ddx / dd, ddy / dd, 12.0)
                        continue
                    x1, y1, x2, y2 = w.endpoints()
                    for b in alive_balls:
                        if b.team_id == w.team_id:
                            continue
                        if point_near_segment(b.x, b.y, x1, y1, x2, y2, b.radius + w.thickness // 2):
                            w.hp -= 1
                            ddx = b.x - w.x
                            ddy = b.y - w.y
                            dd = max(math.sqrt(ddx * ddx + ddy * ddy), 0.01)
                            b.apply_knockback(ddx / dd, ddy / dd, 6.0)

                # necromancer resurrection + kill bounty
                newly_dead = []
                for b in balls:
                    if b.hp <= 0 and b.alive:
                        b.alive = False
                        newly_dead.append(b)
                        # award gold for killing enemies
                        if b.team_id == 1 and not b.is_minion:
                            kill_gold += KILL_BOUNTY.get(b.role, 10)
                for necro in alive_balls:
                    if necro.role != "necromancer" or not necro.alive or necro.necro_cooldown > 0:
                        continue
                    for corpse in newly_dead:
                        if corpse.role == "zombie":
                            continue
                        if dist(necro.x, necro.y, corpse.x, corpse.y) <= NECRO_RAISE_RANGE:
                            corpse.alive = True
                            corpse.hp = NECRO_ZOMBIE_HP
                            corpse.max_hp = NECRO_ZOMBIE_HP
                            corpse.team_id = necro.team_id
                            corpse.color = necro.color
                            corpse.role = "zombie"
                            corpse.speed = ZOMBIE_SPEED
                            corpse.hit_cooldown = 0
                            corpse.bounce_timer = 0
                            corpse.pinned_timer = 0
                            corpse.carried_by_spear = False
                            corpse.trapped_in = None
                            necro.necro_cooldown = NECRO_RAISE_COOLDOWN
                            break

                # cleanup
                spears = [s for s in spears if s.alive]
                traps = [t_obj for t_obj in traps if t_obj.alive]
                bombs = [bm for bm in bombs if bm.alive]
                bullets = [bl for bl in bullets if bl.alive]
                arrows = [ar for ar in arrows if ar.alive]
                orbs = [orb for orb in orbs if orb.alive]
                ice_bolts = [ib for ib in ice_bolts if ib.alive]
                walls = [w for w in walls if w.alive]

                # win check
                alive_teams = set(b.team_id for b in balls if b.alive)
                if len(alive_teams) == 1:
                    winner_team = alive_teams.pop()
                elif len(alive_teams) == 0:
                    winner_team = -1

            # ── draw ──
            screen.fill((20, 20, 30))
            pygame.draw.rect(screen, (80, 80, 80), (0, 0, WIDTH, HEIGHT), 2)
            for w in walls:
                w.draw(screen)
            for t_obj in traps:
                t_obj.draw(screen)
            for bm in bombs:
                bm.draw(screen)
            for b in balls:
                b.draw(screen)
            for s in spears:
                s.draw(screen)
            for bl in bullets:
                bl.draw(screen)
            for ar in arrows:
                ar.draw(screen)
            for orb in orbs:
                orb.draw(screen)
            for ib in ice_bolts:
                ib.draw(screen)

            # HUD
            for tid in range(2):
                color = TEAM_COLORS[tid % len(TEAM_COLORS)]
                team_balls = [b for b in balls if b.team_id == tid and b.alive]
                total_hp = sum(b.hp for b in team_balls)
                alive_count = len(team_balls)
                roles = set(b.role for b in team_balls)
                role_str = "/".join(r.capitalize() for r in sorted(roles)) if roles else "Dead"
                label = "Player" if tid == 0 else "Enemy"
                text = font.render(f"{label} {role_str}: {total_hp}HP [{alive_count}]", True, color)
                screen.blit(text, (10, 8 + tid * 20))

            if paused:
                speed_text = font.render("PAUSED  (Space)", True, (255, 255, 100))
            else:
                speed_text = font.render(f"Speed: {speed_options[speed_index]}x  (1/2/3/4)", True, (180, 180, 180))
            screen.blit(speed_text, (WIDTH - speed_text.get_width() - 10, 8))

            pygame.display.flip()
            clock.tick(60)

    # ── surrender screen ──
    def surrender_screen(player_team, enemy_roles, gold, wave):
        global WIDTH, HEIGHT, screen
        WIDTH, HEIGHT = 600, 450
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

        accept_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT - 80, 140, 40)
        decline_btn = pygame.Rect(WIDTH // 2 + 20, HEIGHT - 80, 140, 40)

        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if accept_btn.collidepoint(mx, my):
                        # accept: gain all enemy units at full HP for free
                        for role in enemy_roles:
                            max_hp = TANK_HP if role == "tank" else 100
                            player_team.append({"role": role, "hp": max_hp})
                        return "accept", player_team, gold
                    if decline_btn.collidepoint(mx, my):
                        return "decline", player_team, gold

            screen.fill((24, 24, 36))
            t = title_font.render("Enemy Surrender!", True, (255, 220, 80))
            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 30))

            desc = font.render("The enemy sees your strength and offers to yield.", True, (200, 200, 220))
            screen.blit(desc, (WIDTH // 2 - desc.get_width() // 2, 80))
            desc2 = font.render("Accept: gain their units free. Decline: fight for kill gold.", True, (180, 180, 200))
            screen.blit(desc2, (WIDTH // 2 - desc2.get_width() // 2, 110))

            # show enemy units being offered
            ey = 150
            for i, role in enumerate(enemy_roles):
                pygame.draw.circle(screen, TEAM_COLORS[1], (WIDTH // 2 - 60 + (i % 6) * 40, ey + (i // 6) * 45), 14)
                rl = small_font.render(role[:6].capitalize(), True, (255, 180, 180))
                screen.blit(rl, (WIDTH // 2 - 75 + (i % 6) * 40, ey + (i // 6) * 45 + 16))

            # buttons
            ac = (60, 180, 60) if accept_btn.collidepoint(mx, my) else (50, 150, 50)
            dc = (180, 60, 60) if decline_btn.collidepoint(mx, my) else (150, 50, 50)
            pygame.draw.rect(screen, ac, accept_btn, border_radius=6)
            pygame.draw.rect(screen, dc, decline_btn, border_radius=6)
            al = font.render("ACCEPT", True, (255, 255, 255))
            dl = font.render("DECLINE", True, (255, 255, 255))
            screen.blit(al, (accept_btn.centerx - al.get_width() // 2, accept_btn.centery - al.get_height() // 2))
            screen.blit(dl, (decline_btn.centerx - dl.get_width() // 2, decline_btn.centery - dl.get_height() // 2))

            pygame.display.flip()
            clock.tick(60)

    # ── main interactive loop ──
    gold = 200
    wave = 1
    player_team = [{"role": "zombie", "hp": 100}]

    while True:
        enemy_roles = get_enemy_wave(wave)
        action, player_team, gold = shop_screen(player_team, gold, wave, enemy_roles)
        if action == "quit":
            return

        # check for enemy surrender: if player power >= 25% more than enemy
        player_power = sum(ROLE_PRICES.get(info["role"], 30) * (info["hp"] / (TANK_HP if info["role"] == "tank" else 100))
                          for info in player_team)
        enemy_power = sum(ROLE_PRICES.get(r, 30) for r in enemy_roles)
        surrendered = False
        if player_power >= enemy_power * 1.25 and random.random() < 0.25:
            result, player_team, gold = surrender_screen(player_team, enemy_roles, gold, wave)
            if result == "accept":
                surrendered = True

        if not surrendered:
            survivors, won, earned = run_battle(player_team, enemy_roles)
            gold += earned

            if not won or not survivors:
                # game over screen
                WIDTH, HEIGHT = 600, 450
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
                screen.fill((30, 10, 10))
                t = big_font.render("Game Over!", True, (255, 80, 80))
                wv = font.render(f"You reached Wave {wave}", True, (255, 255, 255))
                kg = font.render(f"Kill bounty earned: {earned}g", True, (255, 215, 80))
                hint = small_font.render("Click to return to menu", True, (150, 150, 150))
                screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 60))
                screen.blit(wv, (WIDTH // 2 - wv.get_width() // 2, HEIGHT // 2))
                screen.blit(kg, (WIDTH // 2 - kg.get_width() // 2, HEIGHT // 2 + 30))
                screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 60))
                pygame.display.flip()
                waiting = True
                while waiting:
                    for ev in pygame.event.get():
                        if ev.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if ev.type == pygame.MOUSEBUTTONDOWN or ev.type == pygame.KEYDOWN:
                            waiting = False
                    clock.tick(60)
                return

            # survivors get 15 HP regen (capped at max)
            for info in survivors:
                max_hp = TANK_HP if info["role"] == "tank" else 100
                info["hp"] = min(max_hp, info["hp"] + 15)
            player_team = survivors

        gold += 50 + wave * 10
        wave += 1


def main():
    global WIDTH, HEIGHT, screen
    saved_teams = None
    saved_num_teams = None
    saved_arena_idx = None
    while True:
        WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        result = setup_menu(saved_teams, saved_num_teams, saved_arena_idx)
        team_configs, saved_teams, saved_num_teams, saved_arena_idx = result
        if team_configs == "tournament":
            t_result = tournament_menu(saved_arena_idx)
            if t_result is not None:
                bracket, saved_arena_idx, realistic = t_result
                run_tournament(bracket, saved_arena_idx, realistic)
        elif team_configs == "interactive":
            interactive_mode()
        else:
            game(team_configs, saved_arena_idx)


if __name__ == "__main__":
    main()
