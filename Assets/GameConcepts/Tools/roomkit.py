"""Room concept sheets - one room of a run, drawn at the game's own scale.

The level sheets are drawn at 400x225 with 12px stand-in humanoids, so a sheet there is
roughly two screens across and the characters are symbols. A room sheet is the other
way round: 800x450 native, upscaled x2 to the same 1600x900, and every pixel is a
20-PPU sprite pixel. The camera (orthographic size 6.05) sees 430x242 of them, so the
sheet is ~1.9 screens each way and a room drawn on it is the size it will be in game.
That is what lets the real character sprites in `Characters/` be pasted in as they are.

On top of conceptkit this adds only what a room needs and a level does not:

* the label furniture at 2x, so the text stays the same size on the png as on the
  level sheets (the art is at 2x, not 4x);
* `sprite` / `stand` to paste `Characters/Char_*.png`, and a player and a half-size
  Binny at the same scale;
* the run furniture - `exit_door` with the reward it leads to shown above it, and
  `reward_pedestal` for what the room pays out on clear;
* `screen_frame`, a dashed box one camera wide, so every sheet carries its own scale.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "PixelArt", "tools")))
from conceptkit import *  # noqa: F403,E402
import conceptkit as _ck  # noqa: E402
import png as _png  # noqa: E402

SCREEN_W, SCREEN_H = 430, 242       # what the camera sees, in sprite pixels
HAZARD = (217, 210, 74)             # the RiotBrute's stripe yellow
LEADER = (120, 130, 145)


# ─────────────────────────────────────────────────────────────────────────────
#  Label furniture at 2x
# ─────────────────────────────────────────────────────────────────────────────
def btext_w(s, k=2):
    return _ck.text_w(s) * k


def btext(x, y, s, c=LABEL, shadow=True, k=2):
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT[' '])
        gw = len(g[0])
        for ry in range(5):
            for rx in range(gw):
                if g[ry][rx] == '#':
                    if shadow:
                        rect(cx + rx * k + 1, y + ry * k + 1, cx + rx * k + k, y + ry * k + k, INK)
                    rect(cx + rx * k, y + ry * k, cx + rx * k + k - 1, y + ry * k + k - 1, c)
        cx += (gw + 1) * k
    return cx


def btag(x, y, s, c=LABEL):
    w = btext_w(s)
    rect(x - 4, y - 4, x + w + 3, y + 13, INK, 0.8)
    rect(x - 4, y - 4, x + w + 3, y - 4, c, 0.35)
    btext(x, y, s, c, shadow=False)
    return w


def bcallout(tx, ty, s, ax, ay, c=LABEL):
    """Numbered label with a leader line to the thing it names. The line leaves from
    whichever end of the plate is nearer the anchor."""
    w = btag(tx, ty, s, c)
    x0 = tx - 4 if ax < tx + w / 2 else tx + w + 3
    line(x0, ty + 4, ax, ay, LEADER, 0.9)
    disc(ax, ay, 2.2, LEADER)


def btitle_bar(name, subtitle):
    cw, _ = canvas_size()
    rect(0, 0, cw - 1, 30, INK, 0.6)
    btext(12, 9, name, PALE_G)
    btag(cw - 10 - btext_w(subtitle), 10, subtitle, (150, 165, 185))


def blegend(x, y, lines, width):
    h = 16 * len(lines)
    rect(x - 6, y - 7, x + width, y + h - 2, INK, 0.78)
    frame(x - 6, y - 7, x + width, y + h - 2, (70, 80, 92))
    for i, (s, c) in enumerate(lines):
        btext(x, y + i * 16, s, c, shadow=False)


def screen_frame(x, y, label="1 SCREEN"):
    """One camera's worth of room, dashed, so the sheet carries its own scale."""
    c = (150, 165, 185)
    for i in range(0, SCREEN_W, 10):
        rect(x + i, y, x + min(i + 5, SCREEN_W), y, c, 0.55)
        rect(x + i, y + SCREEN_H, x + min(i + 5, SCREEN_W), y + SCREEN_H, c, 0.55)
    for j in range(0, SCREEN_H, 10):
        rect(x, y + j, x, y + min(j + 5, SCREEN_H), c, 0.55)
        rect(x + SCREEN_W, y + j, x + SCREEN_W, y + min(j + 5, SCREEN_H), c, 0.55)
    btext(x + 6, y + SCREEN_H - 10, label, c, shadow=True, k=1)


def wave_tag(x, y, s, c=F_MID):
    """Small W1/W2/W3 marker over an enemy: which wave it belongs to."""
    w = text_w(s)
    rect(x - 2, y - 2, x + w + 1, y + 6, INK, 0.75)
    text(x, y, s, c, shadow=False)


# ─────────────────────────────────────────────────────────────────────────────
#  Characters, pasted from the real sprites
# ─────────────────────────────────────────────────────────────────────────────
_CHARS = os.path.abspath(os.path.join(HERE, "..", "Characters"))
_BINNY = os.path.abspath(os.path.join(HERE, "..", "Binny", "Binny_Master.png"))
_cache = {}


def _load(path):
    if path not in _cache:
        w, h, pix = _png.load(path)
        _cache[path] = (w, h, pix)
    return _cache[path]


def _paste(w, h, pix, x, y, flip=False, tint=None):
    for j in range(h):
        for i in range(w):
            p = pix[j][w - 1 - i if flip else i]
            if len(p) == 4 and p[3] < 128:
                continue
            c = p[:3]
            if tint:
                c = tuple(int(c[k] + (tint[0][k] - c[k]) * tint[1]) for k in range(3))
            px(x + i, y + j, c)


def _foot_row(h, pix):
    for j in range(h - 1, -1, -1):
        if any(len(p) == 4 and p[3] >= 128 for p in pix[j]):
            return j
    return h - 1


def sprite(name, x, y, flip=False, tint=None):
    """Paste `Characters/Char_<name>.png` with its top-left at (x, y). The sprites
    face right; flip=True turns them round."""
    w, h, pix = _load(os.path.join(_CHARS, "Char_%s.png" % name))
    _paste(w, h, pix, x, y, flip, tint)


def stand(name, cx, floor, flip=False, tint=None):
    """Paste a character with its feet on `floor`, centred on cx."""
    w, h, pix = _load(os.path.join(_CHARS, "Char_%s.png" % name))
    foot = _foot_row(h, pix)
    _paste(w, h, pix, cx - w // 2, floor - 1 - foot, flip, tint)


def corpse(cx, floor, c=(99, 104, 101), blood=RED):
    """What a wave leaves on the floor: a heap and a smear, not a pose."""
    rect(cx - 6, floor - 3, cx + 6, floor - 1, c)
    rect(cx - 6, floor - 3, cx - 3, floor - 2, tuple(int(v * 0.7) for v in c))
    for i in range(10):
        px(cx - 12 + i * 2 + int(rnd() * 2), floor - 1, blood, 0.8)


# Hooded wanderer, facing right: tiny glowing eye, red scarf so they read among the
# enemies, short gun held forward (well under body height, per the weapon rule).
_HERO = [
    "....aaa.......",
    "...abbba......",
    "..abbbbba.....",
    "..abbccb......",
    "..abbce.......",
    "..aabbb.......",
    "...addda......",
    "..abddbba.....",
    ".abbbbbbbffff.",
    ".abbbbbbffmmf.",
    ".abbbbbba..f..",
    ".abbbbbba.....",
    "..abbbbba.....",
    "..abbbbbb.....",
    "..agg.gga.....",
    "..ag...ga.....",
    "..ag...ga.....",
    "..ag...ga.....",
    ".hhh..hhh.....",
]
_HERO_PAL = {
    'a': (38, 44, 56), 'b': (78, 92, 104), 'c': (22, 24, 28), 'e': (121, 201, 213),
    'd': (180, 80, 70), 'f': (99, 99, 99), 'm': (135, 135, 135), 'g': (52, 52, 52),
    'h': (30, 30, 34),
}


def hero(cx, floor, face_right=True):
    w, h = len(_HERO[0]), len(_HERO)
    x0, y0 = cx - 5, floor - h
    for j, row in enumerate(_HERO):
        for i, ch in enumerate(row):
            if ch != '.':
                px(x0 + (i if face_right else w - 1 - i), y0 + j, _HERO_PAL[ch])
    px(x0 + (5 if face_right else w - 6), y0 + 4, _HERO_PAL['e'])
    glow(x0 + (5 if face_right else w - 6), y0 + 4, 5, CYAN, 0.25)


def binny_half(x, y):
    """Binny_Master at half size - the master is drawn at 2x the character sprites."""
    w, h, pix = _load(_BINNY)
    for j in range(0, h, 2):
        for i in range(0, w, 2):
            p = None
            for dj, di in ((0, 0), (0, 1), (1, 0), (1, 1)):
                if j + dj < h and i + di < w:
                    q = pix[j + dj][i + di]
                    if len(q) < 4 or q[3] >= 128:
                        p = q
                        break
            if p:
                px(x + i // 2, y + j // 2, p[:3])
    disc(x + 10, y + 25, 2.5, F_MID, 0.45)
    glow(x + 10, y + 12, 16, CYAN, 0.12)


# ─────────────────────────────────────────────────────────────────────────────
#  Energy
# ─────────────────────────────────────────────────────────────────────────────
def arc(x0, y0, x1, y1, jag=5, seg=7, c=CYAN, core=ICE_XL, fork=0.25):
    """ArcField discharge: a jagged path with a hot core, a cold fringe and a glow
    along it. `fork` is the chance per joint of a short dead-end branch."""
    n = max(int(math.hypot(x1 - x0, y1 - y0) / seg), 2)
    nx, ny = -(y1 - y0), (x1 - x0)
    ln = math.hypot(nx, ny) or 1
    nx, ny = nx / ln, ny / ln
    pts = []
    for i in range(n + 1):
        t = i / n
        o = 0 if i in (0, n) else (rnd() - 0.5) * 2 * jag
        pts.append((x0 + (x1 - x0) * t + nx * o, y0 + (y1 - y0) * t + ny * o))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        line(ax + 1, ay, bx + 1, by, c, 0.55)
        line(ax, ay, bx, by, core)
    for (ax, ay) in pts[1:-1:2]:
        glow(ax, ay, 9, c, 0.16)
    for (ax, ay) in pts[1:-1]:
        if chance(fork):
            bx, by = ax + (rnd() - 0.5) * 16, ay + (rnd() - 0.5) * 16
            line(ax, ay, bx, by, c, 0.8)
    glow(x1, y1, 12, c, 0.3)
    disc(x1, y1, 1.6, core)


def hazard_slab(x, y, w, h):
    """A door seen side-on: the slab that fills the gap, striped so it reads as a
    door and not as more wall."""
    rect(x, y, x + w, y + h, INK)
    for j in range(h + 1):
        for i in range(w + 1):
            if ((i + j) // 3) % 2 == 0:
                px(x + i, y + j, HAZARD)
    frame(x, y, x + w, y + h, MET_D)


# ─────────────────────────────────────────────────────────────────────────────
#  Run furniture: the reward glyphs, the doors that show them, the pedestal
# ─────────────────────────────────────────────────────────────────────────────
GLYPHS = {
    # weapon mod
    "gun": (["###########.", "############", "######......", "###.........",
             "###.........", "............"], (187, 187, 187)),
    # Binny module
    "gear": ([".#..#..#.", "#########", ".##...##.", "##.....##", ".##...##.",
              "#########", ".#..#..#."], (121, 201, 213)),
    # heal
    "heart": ([".##...##.", "####.####", "#########", ".#######.", "..#####..",
               "...###...", "....#...."], (180, 80, 70)),
    # scrap - the currency Binny eats
    "scrap": (["..###....", ".#####.#.", "#######..", "######.##", ".####.###",
               "..#..####"], (158, 121, 80)),
    # an elite room: harder, pays double
    "skull": ([".#######.", "#########", "##..#..##", "#########", ".###.###.",
               ".#.#.#.#."], (199, 215, 146)),
}


def glyph(name, cx, cy, glow_=True):
    rows, c = GLYPHS[name]
    w, h = len(rows[0]), len(rows)
    x0, y0 = cx - w // 2, cy - h // 2
    if glow_:
        glow(cx, cy, 14, c, 0.28)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '#':
                px(x0 + i, y0 + j, c)


def exit_door(x, floor, reward, h=30, w=6, sealed=True):
    """An exit, seen side-on in the wall's thickness: striped slab in the opening, and
    above it a plaque with the reward on the far side - which is the whole choice the
    room hands you, so it has to read across the room."""
    y = floor - h
    rect(x - 2, y - 3, x + w + 2, y - 1, MET_D)          # lintel
    rect(x - 2, y - 3, x + w + 2, y - 3, MET_L)
    hazard_slab(x, y, w, h - 1)
    lamp_c = RED_L if sealed else GREEN_L
    disc(x + w // 2, y - 6, 1.5, lamp_c)
    glow(x + w // 2, y - 6, 7, lamp_c, 0.4)
    # plaque on a bracket, facing into the room
    pcx, pcy = x + w // 2, y - 20
    rect(pcx - 9, pcy - 7, pcx + 9, pcy + 7, (30, 34, 40))
    frame(pcx - 9, pcy - 7, pcx + 9, pcy + 7, MET_L)
    glyph(reward, pcx, pcy)


def reward_pedestal(cx, floor, reward, ghost=False):
    """What the room pays on clear: a squat plinth and the reward floating over it.
    ghost=True draws it faint, for a pedestal that only rises when the wave is dead."""
    a = 0.45 if ghost else 1.0
    rect(cx - 9, floor - 10, cx + 9, floor - 1, STONE_D, a)
    rect(cx - 7, floor - 13, cx + 7, floor - 10, STONE, a)
    rect(cx - 7, floor - 13, cx + 7, floor - 13, STONE_L, a)
    rect(cx - 9, floor - 10, cx + 9, floor - 10, STONE_L, a)
    _, c = GLYPHS[reward]
    glow(cx, floor - 24, 22, c, 0.35 if not ghost else 0.2)
    glyph(reward, cx, floor - 24, glow_=False)
    for i in range(6):
        px(cx - 6 + rnd() * 12, floor - 16 - rnd() * 18, c, 0.6)


def glyph_key(x, y, w=250):
    """Bottom-corner plate: what each door plaque promises."""
    items = [("gun", "WEAPON MOD"), ("gear", "BINNY MODULE"), ("heart", "HEAL"),
             ("scrap", "SCRAP"), ("skull", "ELITE: X2")]
    h = 16 * ((len(items) + 1) // 2) + 20
    rect(x - 6, y - 7, x + w, y + h - 2, INK, 0.78)
    frame(x - 6, y - 7, x + w, y + h - 2, (70, 80, 92))
    btext(x, y, "DOOR PLAQUES", CYAN, shadow=False)
    for k, (g, s) in enumerate(items):
        cx = x + 8 + (k % 2) * (w // 2)
        cy = y + 24 + (k // 2) * 16
        glyph(g, cx, cy + 3, glow_=False)
        btext(cx + 12, cy - 2, s, (170, 180, 195), shadow=False, k=1)
