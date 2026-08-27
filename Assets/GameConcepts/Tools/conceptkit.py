"""Pixel-art concept sheets, drawn from code.

A concept sheet is a side-view cross-section of a level: rock mass, carved rooms,
props, characters, then a title bar and numbered callouts on top. This module owns
everything that is the same from sheet to sheet — palette, drawing primitives, the
3x5 label font, and a props library — so a new level is a short scene script that
describes only what that level contains. See `levels/` for the ones we have and
`README.md` for how to add another.

Native resolution is small on purpose (400x225): the art has to read as the same
20-PPU pixel art the game uses, so it is drawn at final pixel size and upscaled by
an integer factor with nearest-neighbour, never resampled.

Pure stdlib. The png writer is the one already in PixelArt/tools.
"""
import math
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PixelArt", "tools")
sys.path.insert(0, os.path.abspath(_TOOLS))
from pixelfix import write_png  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
#  Palette — Noita's 32 plus the ember ramp from MaterialLibrary.Wood
# ─────────────────────────────────────────────────────────────────────────────
VOID    = (16, 18, 21)
INK     = (12, 13, 16)

ROCK_D  = (35, 39, 44)
ROCK    = (53, 62, 70)
ROCK_M  = (71, 78, 90)
ROCK_L  = (89, 99, 113)
CAVE    = (26, 30, 35)
CAVE_L  = (38, 44, 52)

DIRT_D  = (55, 48, 38)
DIRT    = (81, 72, 54)
DIRT_L  = (149, 134, 101)

MET_D   = (52, 52, 52)
MET     = (99, 99, 99)
MET_L   = (135, 135, 135)
MET_XL  = (187, 187, 187)

WOOD_D  = (77, 58, 40)
WOOD    = (128, 96, 62)
WOOD_L  = (158, 121, 80)

GREEN   = (109, 130, 51)
GREEN_L = (159, 187, 83)
PALE_G  = (199, 215, 146)

BLUE    = (78, 92, 104)
BLUE_L  = (146, 164, 182)
BLUE_XL = (201, 204, 223)
CYAN    = (121, 201, 213)
ICE     = (96, 129, 140)
ICE_L   = (158, 200, 210)
ICE_XL  = (194, 252, 243)

RED     = (131, 59, 59)
RED_L   = (180, 80, 70)
PURPLE  = (71, 75, 111)

F_HOT   = (255, 244, 194)   # EmberHot
F_MID   = (255, 146, 34)    # EmberMid
F_COOL  = (146, 34, 12)     # EmberCool
CHAR    = (30, 26, 25)      # Charcoal

SKY_HI  = (147, 159, 183)
SKY_LO  = (90, 96, 110)
LABEL   = (223, 232, 192)

# ─────────────────────────────────────────────────────────────────────────────
#  Canvas + deterministic noise
# ─────────────────────────────────────────────────────────────────────────────
W = H = 0
buf = []
_seed = 1337


def new_canvas(w=400, h=225, seed=1337, bg=VOID):
    """Start a fresh sheet. Same seed -> byte-identical png, so a scene edit shows
    up as a real diff instead of a reshuffled dither."""
    global W, H, buf, _seed
    W, H, _seed = w, h, seed
    buf = [[bg for _ in range(w)] for _ in range(h)]


def rnd():
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed / 0x7FFFFFFF


def chance(p):
    return rnd() < p


def pick(seq):
    return seq[int(rnd() * len(seq)) % len(seq)]


def jitter(c, amount=14):
    """Nudge a colour so large flat fills do not look printed."""
    d = int((rnd() - 0.5) * 2 * amount)
    return tuple(max(0, min(255, v + d)) for v in c)


# ─────────────────────────────────────────────────────────────────────────────
#  Primitives
# ─────────────────────────────────────────────────────────────────────────────
def px(x, y, c, a=1.0):
    x, y = int(x), int(y)
    if 0 <= x < W and 0 <= y < H:
        if a >= 1.0:
            buf[y][x] = c
        else:
            o = buf[y][x]
            buf[y][x] = tuple(int(o[i] + (c[i] - o[i]) * a) for i in range(3))


def at(x, y):
    x, y = int(x), int(y)
    return buf[y][x] if 0 <= x < W and 0 <= y < H else VOID


def rect(x0, y0, x1, y1, c, a=1.0):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            px(x, y, c, a)


def frame(x0, y0, x1, y1, c):
    for x in range(int(x0), int(x1) + 1):
        px(x, y0, c)
        px(x, y1, c)
    for y in range(int(y0), int(y1) + 1):
        px(x0, y, c)
        px(x1, y, c)


def line(x0, y0, x1, y1, c, a=1.0):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c, a)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c, a=1.0):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px(x, y, c, a)


def ring(cx, cy, r, c):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if (r - 0.9) ** 2 <= d <= r * r:
                px(x, y, c)


def glow(cx, cy, r, c, strength=0.55):
    """Quadratic falloff. Cheap stand-in for the light the game's emitters cast."""
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r:
                px(x, y, c, strength * (1 - d / r) ** 2)


def vignette(strength=0.55):
    for y in range(H):
        for x in range(W):
            dx = abs(x - W / 2) / (W / 2)
            dy = abs(y - H / 2) / (H / 2)
            v = (dx ** 3 + dy ** 3) * strength
            if v > 0.02:
                px(x, y, VOID, min(v, strength))


# ─────────────────────────────────────────────────────────────────────────────
#  3x5 label font (M/N/W are wider — at 3px they read as H/K/V)
# ─────────────────────────────────────────────────────────────────────────────
FONT = {
    'A': ("###", "# #", "###", "# #", "# #"), 'B': ("## ", "# #", "## ", "# #", "## "),
    'C': ("###", "#  ", "#  ", "#  ", "###"), 'D': ("## ", "# #", "# #", "# #", "## "),
    'E': ("###", "#  ", "## ", "#  ", "###"), 'F': ("###", "#  ", "## ", "#  ", "#  "),
    'G': ("###", "#  ", "# #", "# #", "###"), 'H': ("# #", "# #", "###", "# #", "# #"),
    'I': ("###", " # ", " # ", " # ", "###"), 'J': ("  #", "  #", "  #", "# #", "###"),
    'K': ("# #", "# #", "## ", "# #", "# #"), 'L': ("#  ", "#  ", "#  ", "#  ", "###"),
    'M': ("#   #", "## ##", "# # #", "#   #", "#   #"),
    'N': ("#  #", "## #", "# ##", "#  #", "#  #"),
    'O': ("###", "# #", "# #", "# #", "###"), 'P': ("###", "# #", "###", "#  ", "#  "),
    'Q': ("###", "# #", "# #", "###", "  #"), 'R': ("###", "# #", "###", "## ", "# #"),
    'S': ("###", "#  ", "###", "  #", "###"), 'T': ("###", " # ", " # ", " # ", " # "),
    'U': ("# #", "# #", "# #", "# #", "###"), 'V': ("# #", "# #", "# #", "# #", " # "),
    'W': ("#   #", "#   #", "# # #", "## ##", "#   #"),
    'X': ("# #", "# #", " # ", "# #", "# #"), 'Y': ("# #", "# #", " # ", " # ", " # "),
    'Z': ("###", "  #", " # ", "#  ", "###"),
    '0': ("###", "# #", "# #", "# #", "###"), '1': (" # ", "## ", " # ", " # ", "###"),
    '2': ("###", "  #", "###", "#  ", "###"), '3': ("###", "  #", "###", "  #", "###"),
    '4': ("# #", "# #", "###", "  #", "  #"), '5': ("###", "#  ", "###", "  #", "###"),
    '6': ("###", "#  ", "###", "# #", "###"), '7': ("###", "  #", "  #", "  #", "  #"),
    '8': ("###", "# #", "###", "# #", "###"), '9': ("###", "# #", "###", "  #", "###"),
    '-': ("   ", "   ", "###", "   ", "   "), '.': ("   ", "   ", "   ", "   ", " # "),
    ',': ("   ", "   ", "   ", " # ", "#  "), ':': ("   ", " # ", "   ", " # ", "   "),
    '/': ("  #", "  #", " # ", "#  ", "#  "), '!': (" # ", " # ", " # ", "   ", " # "),
    '+': ("   ", " # ", "###", " # ", "   "), '=': ("   ", "###", "   ", "###", "   "), "'": (" # ", " # ", "   ", "   ", "   "),
    '>': ("#  ", " # ", "  #", " # ", "#  "), '(': (" ##", " # ", " # ", " # ", " ##"),
    ')': ("## ", "  #", "  #", "  #", "## "), '?': ("###", "  #", " ##", "   ", " # "),
    ' ': ("   ", "   ", "   ", "   ", "   "),
}


def text_w(s):
    return sum(len(FONT.get(ch, FONT[' '])[0]) + 1 for ch in s.upper()) - 1


def text(x, y, s, c=LABEL, shadow=True):
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT[' '])
        gw = len(g[0])
        for ry in range(5):
            for rx in range(gw):
                if g[ry][rx] == '#':
                    if shadow:
                        px(cx + rx + 1, y + ry + 1, INK)
                    px(cx + rx, y + ry, c)
        cx += gw + 1
    return cx


def tag(x, y, s, c=LABEL):
    """Label on a dark plate, so it stays legible over busy art."""
    w = text_w(s)
    rect(x - 2, y - 2, x + w + 1, y + 6, INK, 0.78)
    rect(x - 2, y - 2, x + w + 1, y - 2, c, 0.35)
    text(x, y, s, c, shadow=False)
    return w


def callout(tx, ty, s, ax, ay, c=LABEL):
    """Numbered label with a leader line to the thing it names."""
    w = tag(tx, ty, s, c)
    x0 = tx if ax < tx else tx + w
    line(x0, ty + 3, ax, ay, (120, 130, 145), 0.9)
    disc(ax, ay, 1.4, (120, 130, 145))


def title_bar(name, subtitle="VERTICAL SLICE / SIDE CROSS-SECTION"):
    rect(0, 0, W - 1, 16, INK, 0.55)
    text(6, 4, name, PALE_G)
    tag(W - 4 - text_w(subtitle), 5, subtitle, (150, 165, 185))


def legend(x, y, lines, width=92):
    """Bottom-corner plate: the beats this level is built to teach."""
    rect(x - 3, y - 4, x + width, y + 8 * len(lines) - 2, INK, 0.72)
    frame(x - 3, y - 4, x + width, y + 8 * len(lines) - 2, (70, 80, 92))
    for i, (s, c) in enumerate(lines):
        text(x, y + i * 8, s, c, shadow=False)


# ─────────────────────────────────────────────────────────────────────────────
#  Terrain
# ─────────────────────────────────────────────────────────────────────────────
def sky(surf, hi=SKY_HI, lo=SKY_LO, smog=9):
    for y in range(0, surf + 6):
        t = y / (surf + 6)
        rect(0, y, W - 1, y, tuple(int(hi[i] + (lo[i] - hi[i]) * t) for i in range(3)))
    for _ in range(smog):
        yy = 4 + int(rnd() * (surf - 8))
        x0 = int(rnd() * W)
        rect(x0, yy, x0 + 40 + int(rnd() * 130), yy + 1, (168, 176, 192), 0.16)


def rock_mass(surf, base=ROCK, dark=ROCK_D, mid=ROCK_M, soil=DIRT, soil_lit=DIRT_L, strata=14):
    rect(0, surf, W - 1, H - 1, base)
    for y in range(surf, H):
        for x in range(W):
            r = rnd()
            if r < 0.13:
                px(x, y, dark)
            elif r < 0.20:
                px(x, y, mid)
    for _ in range(strata):
        yy = surf + 6 + int(rnd() * (H - surf - 10))
        x = 0
        while x < W:
            ln = 8 + int(rnd() * 26)
            rect(x, yy, x + ln, yy + (1 if chance(0.4) else 0),
                 dark if chance(0.6) else mid, 0.7)
            x += ln + int(rnd() * 12)
    for x in range(W):
        d = 4 + int(rnd() * 3)
        rect(x, surf, x, surf + d, soil)
        px(x, surf, soil_lit)


def carve(x0, y0, x1, y1, rough=2, air=CAVE, lip=CAVE_L):
    """Hollow a room. Ceiling and floor get a ragged edge and a lit lip, which is
    what stops a rectangular room from reading as a rectangle."""
    for x in range(int(x0), int(x1) + 1):
        jt, jb = int(rnd() * (rough + 1)), int(rnd() * (rough + 1))
        for y in range(int(y0) + jt, int(y1) - jb + 1):
            px(x, y, air)
    for x in range(int(x0), int(x1) + 1):
        for y in range(int(y0), int(y1) + 1):
            if at(x, y) == air:
                if at(x, y - 1) != air:
                    px(x, y, lip, 0.5)
                break


def carve_all(rooms, **kw):
    for r in rooms:
        carve(*r, **kw)


def floor_slab(x0, x1, y, thick=4, c=ROCK_D, lit=ROCK_L):
    rect(x0, y, x1, y + thick, c)
    rect(x0, y, x1, y, lit)


# ─────────────────────────────────────────────────────────────────────────────
#  Props
# ─────────────────────────────────────────────────────────────────────────────
def scrap_pile(x, base, w, h, colors=(MET_D, MET, RED, DIRT, GREEN, MET_L)):
    for _ in range(w * h // 3):
        sx = x + int(rnd() * w)
        fall = 1 - abs(sx - (x + w / 2)) / (w / 1.4)
        sy = base - int(rnd() * h * max(fall, 0))
        rect(sx, sy, sx + 1 + int(rnd() * 3), sy + 1, pick(list(colors)))


def rubble(x0, y0, x1, y1, n=30, colors=(MET_D, DIRT, MET)):
    for _ in range(n):
        px(x0 + int(rnd() * (x1 - x0)), y0 + int(rnd() * max(y1 - y0, 1)), pick(list(colors)))


def crate(x, y, s=7, wood=True):
    c, cl, cd = (WOOD, WOOD_L, WOOD_D) if wood else (MET, MET_L, MET_D)
    rect(x, y, x + s, y + s, c)
    frame(x, y, x + s, y + s, cd)
    line(x, y, x + s, y + s, cl)
    line(x + s, y, x, y + s, cl)


def barrel(x, y, c=GREEN, cl=GREEN_L, band=PALE_G, w=5, h=7):
    rect(x, y, x + w, y + h, c)
    rect(x, y, x + w, y, cl)
    rect(x, y + h // 2, x + w, y + h // 2, band)


def plank(x0, y0, x1, y1, thick=2, burn=False):
    for t in range(thick):
        line(x0, y0 + t, x1, y1 + t, WOOD if t < thick - 1 else WOOD_D)
    if burn:
        for _ in range(int(abs(x1 - x0) / 2) + 2):
            f = rnd()
            px(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, F_MID if chance(0.6) else F_HOT)


def beam(x, y0, y1, w=3, c=WOOD, lit=WOOD_L):
    rect(x, y0, x + w, y1, c)
    rect(x, y0, x, y1, lit)


def ladder(x, y0, y1, w=6, step=8, c=MET_L, rail=MET_D):
    rect(x - 1, y0, x - 1, y1, rail)
    rect(x + w + 1, y0, x + w + 1, y1, rail)
    for y in range(int(y0) + 2, int(y1), step):
        rect(x, y, x + w, y, c)


def catwalk(x0, x1, y, drop=10, c=MET_D, lit=MET_L, posts=14):
    rect(x0, y, x1, y + 1, c)
    rect(x0, y, x1, y, lit)
    for x in range(int(x0) + 4, int(x1) - 2, posts):
        rect(x, y + 2, x, y + drop, c)


def pipe_run(x0, x1, y, c=MET_D, lit=MET_L, hangers=16):
    rect(x0, y, x1, y + 2, c)
    rect(x0, y, x1, y, lit)
    for x in range(int(x0) + 6, int(x1) - 4, hangers):
        rect(x, y + 3, x + 1, y + 5, c)


def lamp(x, y, drop=6, bulb=PALE_G, tint=(255, 236, 170), r=22, strength=0.22):
    line(x, y, x, y + drop, MET_D)
    disc(x, y + drop + 2, 2.2, bulb)
    glow(x, y + drop + 4, r, tint, strength)


def conveyor(x0, x1, y, direction=1, chevron=GREEN_L):
    """Hazards/Conveyor: belt with chevrons pointing the way it drags things."""
    rect(x0, y, x1, y + 3, MET_D)
    rect(x0, y, x1, y, MET_L)
    for x in range(x0 + 2, x1 - 1, 6):
        for k in range(3):
            px(x + (k if direction > 0 else -k), y + 1 + k % 2, chevron)
    for cx in (x0 + 2, x1 - 2):
        disc(cx, y + 2, 2.2, MET)
        ring(cx, y + 2, 2.2, MET_XL)
    for x in range(x0 + 6, x1 - 4, 14):
        rect(x, y + 4, x + 1, y + 9, MET_D)


def gear(cx, cy, r, teeth=8, c=MET, lit=MET_XL, hub=MET_D):
    """Hazards/Grinder: kinematic wheel, teeth proud of the rim."""
    disc(cx, cy, r, c)
    ring(cx, cy, r, lit)
    disc(cx, cy, r * 0.35, hub)
    for i in range(teeth):
        a = i * 2 * math.pi / teeth
        disc(cx + math.cos(a) * (r + 1.6), cy + math.sin(a) * (r + 1.6), 1.6, MET_L)
    glow(cx, cy, r + 8, (150, 170, 190), 0.10)


def spikes(x, y0, y1, side=1, step=7, c=MET_XL):
    for y in range(int(y0), int(y1), step):
        for k in range(3):
            px(x + k * side, y + k, c)


def fire_patch(x0, y0, x1, y1, n=26, size=1.6):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0),
             1 + rnd() * size, pick([F_HOT, F_MID, F_COOL]), 0.85)


def embers(x0, y0, x1, y1, n=60):
    for _ in range(n):
        px(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0),
           pick([F_HOT, F_MID]), 0.5 + rnd() * 0.5)


def water(x0, y0, x1, y1, c=(48, 86, 104), lit=(96, 150, 168)):
    rect(x0, y0, x1, y1, c, 0.85)
    for x in range(int(x0), int(x1), 3):
        px(x + int(rnd() * 2), y0, lit, 0.7)


def ice_block(x, y, w=10, h=10):
    rect(x, y, x + w, y + h, ICE, 0.9)
    frame(x, y, x + w, y + h, ICE_L)
    line(x + 1, y + 1, x + w - 2, y + h - 3, ICE_XL, 0.6)
    line(x + w - 2, y + 2, x + w // 2, y + h - 1, ICE_L, 0.5)


def icicles(x0, x1, y, n=10, c=ICE_L, tip=ICE_XL):
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 2 + int(rnd() * 6)
        for k in range(ln):
            px(x, y + k, c if k < ln - 1 else tip)


def door(x, y, w=34, h=38, c=MET, lit=MET_XL, inner=MET_D):
    rect(x, y, x + w, y + h, c)
    frame(x, y, x + w, y + h, lit)
    rect(x + 4, y + 4, x + w - 4, y + h - 4, inner)
    cx, cy = x + w // 2, y + h // 2
    disc(cx, cy, 7, c)
    ring(cx, cy, 7, lit)
    for i in range(4):
        a = i * math.pi / 2 + 0.6
        line(cx, cy, cx + math.cos(a) * 6, cy + math.sin(a) * 6, lit)
    rect(x - 2, y + h, x + w + 2, y + h + 4, MET_D)


# ─────────────────────────────────────────────────────────────────────────────
#  Characters (side view, the ~7x11 humanoid the ragdoll cutter wants:
#  visible neck notch, a gap between arm and torso)
# ─────────────────────────────────────────────────────────────────────────────
def humanoid(x, y, coat=MET_L, trim=DIRT_L, face_right=True, arm_out=True, head=None):
    d = 1 if face_right else -1
    rect(x + 2, y, x + 4, y + 2, head or coat)
    px(x + (4 if face_right else 2), y + 1, INK)
    px(x + 3, y + 3, trim)
    rect(x + 2, y + 4, x + 4, y + 8, coat)
    rect(x + 2, y + 4, x + 2, y + 8, trim)
    if arm_out:
        rect(x + 3 + d * 2, y + 5, x + 3 + d * 4, y + 5, trim)
    rect(x + 2, y + 9, x + 2, y + 11, INK)
    rect(x + 4, y + 9, x + 4, y + 11, INK)


def player(x, y, coat=BLUE, cuff=BLUE_L, skin=DIRT_L):
    rect(x + 2, y, x + 4, y + 2, skin)
    px(x + 4, y + 1, INK)
    rect(x + 1, y + 3, x + 5, y + 8, coat)
    rect(x + 1, y + 3, x + 1, y + 8, tuple(int(v * 0.75) for v in coat))
    rect(x + 2, y + 4, x + 4, y + 4, cuff)
    rect(x + 5, y + 4, x + 7, y + 4, skin)
    rect(x + 2, y + 9, x + 2, y + 11, INK)
    rect(x + 4, y + 9, x + 4, y + 11, INK)


def binny(x, y, eye=PALE_G, thruster=CYAN):
    """The recycler follower: hopper hole on top, dumb face, hover wash below."""
    rect(x, y + 2, x + 10, y + 9, MET_L)
    rect(x, y + 2, x + 10, y + 2, MET_XL)
    rect(x, y + 9, x + 10, y + 9, MET_D)
    rect(x + 2, y, x + 8, y + 1, MET_D)
    rect(x + 3, y, x + 7, y, INK)
    rect(x + 1, y + 4, x + 9, y + 7, (30, 34, 40))
    px(x + 3, y + 5, eye)
    px(x + 7, y + 5, eye)
    px(x + 3, y + 6, INK)
    px(x + 7, y + 6, INK)
    rect(x + 4, y + 6, x + 6, y + 6, thruster)
    disc(x + 5, y + 12, 2.2, F_MID, 0.5)
    disc(x + 5, y + 11, 1.4, thruster, 0.8)
    glow(x + 5, y + 6, 9, thruster, 0.20)


def ragdoll(x, y, trail=RED_L):
    """A corpse mid-flight — what the grinder and the impact solver leave behind."""
    rect(x, y, x + 2, y + 1, DIRT_L)
    rect(x + 2, y + 2, x + 5, y + 3, MET_L)
    rect(x + 5, y + 4, x + 7, y + 4, INK)
    rect(x + 3, y + 4, x + 4, y + 6, INK)
    for i in range(5):
        px(x - 2 - i, y - 1 - i, trail, 0.8)


def tk_beam(x0, y0, x1, y1, c=CYAN):
    """Telekinesis: the held object and the line back to the hand."""
    line(x0, y0, x1, y1, c, 0.35)
    ring(x1, y1, 4, c)
    glow(x1, y1, 9, c, 0.25)


def tracer(x0, y0, x1, y1, c=F_MID):
    disc(x0, y0, 1.6, F_HOT, 0.9)
    line(x0, y0, x1, y1, c, 0.75)


# ─────────────────────────────────────────────────────────────────────────────
#  Output
# ─────────────────────────────────────────────────────────────────────────────
def save(path, scale=4):
    rows = []
    for row in buf:
        big = []
        for c in row:
            big.extend([(c[0], c[1], c[2], 255)] * scale)
        for _ in range(scale):
            rows.append(big)
    write_png(path, rows)
    print("wrote %s  %dx%d" % (path, W * scale, H * scale))
    return path


def out_path(name):
    """Sheets land next to the scene scripts' parent — Assets/GameConcepts/."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", name))


# ─────────────────────────────────────────────────────────────────────────────
#  Industrial props — shared by the sheets from 05 on
# ─────────────────────────────────────────────────────────────────────────────
def tank(x, y, w, h, c=MET, lit=MET_L, dark=MET_D, bands=3):
    """Pressure vessel: flat fill, lit left edge, banded seams, feet."""
    rect(x, y, x + w, y + h, c)
    rect(x, y, x, y + h, lit)
    rect(x + w, y, x + w, y + h, dark)
    rect(x, y, x + w, y, lit)
    for i in range(1, bands + 1):
        by = y + h * i // (bands + 1)
        rect(x, by, x + w, by, dark)
    rect(x - 1, y + h, x + 2, y + h + 3, dark)
    rect(x + w - 2, y + h, x + w + 1, y + h + 3, dark)


def vat(x0, y0, x1, y1, liquid=(90, 150, 70), lit=(150, 210, 110), wall=MET):
    """Open vat. The liquid line sits a little below the rim so it reads as a level."""
    rect(x0, y0, x1, y1, wall)
    rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, (24, 28, 34))
    surface = y0 + 6
    rect(x0 + 2, surface, x1 - 2, y1 - 2, liquid, 0.9)
    rect(x0 + 2, surface, x1 - 2, surface, lit)
    for x in range(int(x0) + 3, int(x1) - 3, 6):
        px(x + int(rnd() * 3), surface - 1, lit, 0.7)
    glow((x0 + x1) / 2, surface + 4, (x1 - x0) * 0.6, lit, 0.18)
    rect(x0, y0, x1, y0, MET_L)


def liquid_pool(x0, y0, x1, y1, c=(48, 86, 104), lit=(120, 176, 196)):
    rect(x0, y0, x1, y1, c, 0.88)
    rect(x0, y0 + (y1 - y0) // 2, x1, y1, tuple(int(v * 0.6) for v in c), 0.7)
    for x in range(int(x0), int(x1), 7):
        rect(x, y0, x + 3, y0, lit, 0.6)
    glow((x0 + x1) / 2, y0 + 2, (x1 - x0) * 0.35, lit, 0.18)


def valve(x, y, r=4, c=MET_L, hub=MET_D):
    ring(x, y, r, c)
    disc(x, y, 1.4, hub)
    for a in range(4):
        ang = a * math.pi / 2 + 0.4
        line(x, y, x + math.cos(ang) * r, y + math.sin(ang) * r, c)


def fan(cx, cy, r, blades=4, c=MET_L, housing=MET_D):
    ring(cx, cy, r + 2, housing)
    ring(cx, cy, r + 1, housing)
    for i in range(blades):
        a = i * 2 * math.pi / blades + 0.5
        line(cx, cy, cx + math.cos(a) * r, cy + math.sin(a) * r, c)
        line(cx + math.cos(a) * r, cy + math.sin(a) * r,
             cx + math.cos(a + 0.5) * r * 0.7, cy + math.sin(a + 0.5) * r * 0.7, c, 0.7)
    disc(cx, cy, 2, MET)


def chain(x, y0, y1, c=MET_L, dark=MET_D):
    for y in range(int(y0), int(y1), 3):
        px(x, y, c)
        px(x + 1, y + 1, dark)


def cable(x0, y0, x1, y1, sag=6, c=MET_D):
    """Drooping line — the thing that makes a ceiling read as maintained, then abandoned."""
    steps = max(int(abs(x1 - x0)), 2)
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
        px(x, y, c)


def column(x, y0, y1, w=6, c=(126, 118, 100), lit=(168, 158, 136), dark=(78, 72, 60)):
    rect(x, y0, x + w, y1, c)
    rect(x, y0, x, y1, lit)
    rect(x + w, y0, x + w, y1, dark)
    rect(x - 2, y0, x + w + 2, y0 + 2, lit)          # capital
    rect(x - 2, y1 - 2, x + w + 2, y1, lit)          # base
    for y in range(int(y0) + 6, int(y1) - 4, 9):     # course lines
        rect(x, y, x + w, y, dark, 0.6)


def arch(cx, y, w, h, c=(126, 118, 100), lit=(168, 158, 136), broken=False):
    for i in range(int(w / 2)):
        t = i / (w / 2)
        dy = int(h * (1 - t * t) ** 0.5)
        if broken and t > 0.55 and chance(0.5):
            continue
        rect(cx - i - 1, y - dy, cx - i, y - dy + 3, c)
        rect(cx + i, y - dy, cx + i + 1, y - dy + 3, c)
        px(cx - i, y - dy, lit)
        px(cx + i, y - dy, lit)


def grate(x0, x1, y, c=MET_D, lit=MET_L):
    rect(x0, y, x1, y + 1, c)
    rect(x0, y, x1, y, lit)
    for x in range(int(x0), int(x1), 4):
        rect(x, y, x, y + 1, lit, 0.5)


def stairs(x, y, steps=6, dx=7, dy=5, c=MET_D, lit=MET_L):
    for i in range(steps):
        sx = x + i * dx
        sy = y - i * dy
        rect(sx, sy, sx + dx, sy + 2, c)
        rect(sx, sy, sx + dx, sy, lit)


def rails(x0, x1, y, ties=9, c=MET_XL, tie=WOOD_D, broken=None):
    for x in range(int(x0), int(x1)):
        if broken and broken[0] <= x <= broken[1]:
            continue
        px(x, y, c)
        px(x, y + 1, MET)
    for x in range(int(x0), int(x1), ties):
        if broken and broken[0] <= x <= broken[1]:
            continue
        rect(x, y + 2, x + 4, y + 3, tie)


def cart(x, y, load=True, tipped=False):
    rect(x, y, x + 13, y + 7, MET)
    rect(x, y, x + 13, y, MET_XL)
    rect(x + 1, y + 1, x + 12, y + 3, (58, 46, 34))
    if load:
        for _ in range(9):
            px(x + 2 + int(rnd() * 10), y - 1 + int(rnd() * 3), pick([DIRT_L, GREEN_L, MET_L]))
    rect(x, y + 7, x + 13, y + 8, MET_D)
    for wx in (x + 3, x + 10):
        disc(wx, y + 9, 2, INK)
        disc(wx, y + 9, 1, MET_L)
    if tipped:
        for i in range(14):
            px(x + 14 + i, y + 9 - int(rnd() * 3), pick([DIRT_L, DIRT, GREEN_L]))


def steam_plume(x, y, r=18, n=40, c=(190, 210, 220), up=True):
    d = -1 if up else 1
    for _ in range(n):
        t = rnd()
        disc(x + (rnd() - 0.5) * r * (0.4 + t), y + d * t * r,
             1 + rnd() * 3, c, 0.16)


def sparks(x, y, n=14, spread=10, c=F_HOT):
    for _ in range(n):
        px(x + (rnd() - 0.5) * spread, y + (rnd() - 0.5) * spread * 0.6,
           pick([c, F_MID]), 0.5 + rnd() * 0.5)


def spore_cloud(x0, y0, x1, y1, n=60, c=(150, 200, 120)):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), 1 + rnd() * 2.5, c, 0.14)


def mushroom(x, base, h=14, cap=18, stem=(210, 200, 180), skin=(150, 90, 110),
             gills=(240, 230, 200)):
    rect(x - 2, base - h, x + 2, base, stem)
    rect(x - 2, base - h, x - 2, base, gills)
    for i in range(4):
        w = cap // 2 - i * 2
        rect(x - w, base - h - 4 + i, x + w, base - h - 4 + i, skin if i else gills)
    disc(x, base - h - 2, cap / 2.4, skin, 0.9)
    rect(x - cap // 2, base - h - 1, x + cap // 2, base - h, gills, 0.8)
    glow(x, base - h - 2, cap, (120, 200, 150), 0.10)
