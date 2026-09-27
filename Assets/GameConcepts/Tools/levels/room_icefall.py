"""Room concept 05 - THE ICEFALL (big room).

~3.6 x 3 screens at game scale. A glacier has flowed into the mine from the east: the
top of the room is ice, the bottom is rock, and the line between them runs corner to
corner. The toy is PhysMaterial.Ice as the code has it - brittle, durability 3.5,
crackability 0.55 - which means ice does nothing until it does everything at once. A
round either scuffs it or runs a split, the split is drawn before the slab lets go,
and the default round shears ~3.3 units: a pillar, a ledge, a bridge, a hanging slab.

So everything held up in this room is held by ice. Three columns carry the shelf the
second wave stands on; a pre-cracked slab hangs over the main gallery with a frozen
tub of loot above it; a serac pile leans on one timber. The grenadiers in wave 2 are
the room's joke on the player - every grenade they throw runs splits in your roof.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

FLOOR = 700
ICE_BANDS = ((60, 90, 102), (70, 102, 114), (80, 114, 126))
MORAINE = (58, 60, 58)
COLD = (150, 205, 226)          # PhysMaterial.Ice swatch
LAMP = (255, 214, 140)
GLACIER = [(0, 190), (300, 232), (560, 330), (700, 452), (1000, 470), (1150, 560),
           (1400, 610), (1600, 622)]


def g(x):
    """Underside of the glacier at x: above this line is ice, below it rock."""
    for (ax, ay), (bx, by) in zip(GLACIER, GLACIER[1:]):
        if ax <= x <= bx:
            t = (x - ax) / (bx - ax)
            return ay + (by - ay) * t + 6 * math.sin(x / 37.0)
    return GLACIER[-1][1]


# ── local props ─────────────────────────────────────────────────────────────
def glacier(top=46):
    """Fill everything above g(x) with banded ice, bubbles, and a dirty moraine seam
    where it grinds on the rock."""
    cw, _ = canvas_size()
    for x in range(cw):
        gy = int(g(x))
        for y in range(top, gy):
            band = int((y + 0.18 * x + 7 * math.sin(x * 0.011)) / 9) % 3
            px(x, y, ICE_BANDS[band])
            if chance(0.008):
                px(x, y, ICE_L)
        for k in range(4):
            px(x, gy + k, MORAINE if chance(0.7) else pick([DIRT, ROCK_L, ROCK_D]))


def split(points, c=ICE_XL):
    """A crack the ice has already run: bright line, dark shadow under it."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay + 1, bx, by + 1, (40, 60, 70))
        line(ax, ay, bx, by, c)


def jag(x0, y0, x1, y1, n=8, amp=4):
    pts = []
    for i in range(n + 1):
        t = i / n
        o = 0 if i in (0, n) else (rnd() - 0.5) * 2 * amp
        pts.append((x0 + (x1 - x0) * t + (o if abs(y1 - y0) > abs(x1 - x0) else 0),
                    y0 + (y1 - y0) * t + (o if abs(y1 - y0) <= abs(x1 - x0) else 0)))
    return pts


def ice_fill(x0, y0, x1, y1):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            px(x, y, ICE_BANDS[int((y + 0.18 * x) / 9) % 3])


def ice_column(x, y0, y1, w=26, cracked=False):
    """An ice pillar carrying the shelf above. 26px is well inside one round's reach."""
    ice_fill(x, y0, x + w, y1)
    rect(x, y0, x + 1, y1, ICE_L)
    rect(x + w - 1, y0, x + w, y1, (48, 74, 86))
    for _ in range(6):                                       # inclusions
        yy = y0 + rnd() * (y1 - y0)
        line(x + 4, yy, x + w - 5, yy + 3, ICE, 0.6)
    rect(x - 4, y1 - 6, x + w + 4, y1, ICE_BANDS[2])         # flared foot
    rect(x - 4, y0, x + w + 4, y0 + 5, ICE_BANDS[2])          # flared head
    if cracked:
        split(jag(x - 2, y0 + 70, x + w + 2, y0 + 88, 5, 3))


def hanging_slab(x0, x1, y, depth):
    """Ice hanging below the ceiling, split round three sides already: the slab the
    split outlines is what comes down."""
    for x in range(int(x0), int(x1) + 1):
        t = (x - x0) / max(x1 - x0, 1)
        d = int(depth * (0.55 + 0.45 * math.sin(math.pi * t)))
        for yy in range(int(y), int(y) + d):
            px(x, yy, ICE_BANDS[int((yy + 0.18 * x) / 9) % 3])
        px(x, y + d, ICE_L)
    split(jag(x0 + 8, y - 30, x1 - 8, y - 26, 10, 3))
    split(jag(x0 + 8, y - 30, x0 + 2, y + depth * 0.6, 4, 2))
    split(jag(x1 - 8, y - 26, x1 - 2, y + depth * 0.6, 4, 2))
    icicles(x0 + 6, x1 - 6, y + depth - 2, 14, ICE_L, ICE_XL)


def frozen(draw, x0, y0, x1, y1):
    """Something caught in the ice: drawn, then glazed over so it reads as inside."""
    draw()
    rect(x0, y0, x1, y1, ICE_BANDS[1], 0.45)
    for _ in range(int((x1 - x0) / 4)):
        px(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), ICE_L, 0.6)


def frozen_tub(x, y):
    def draw():
        rect(x, y, x + 36, y + 16, MET)
        rect(x, y, x + 36, y, MET_XL)
        rect(x + 2, y + 2, x + 34, y + 6, (58, 46, 34))
        for _ in range(26):
            px(x + 3 + rnd() * 30, y + 1 + rnd() * 4, pick([HAZARD, MET_L, (158, 121, 80)]))
        for wx in (x + 8, x + 28):
            disc(wx, y + 19, 3.5, INK)
            disc(wx, y + 19, 1.5, MET_L)
        crate(x + 42, y + 6, 12)
        crate(x + 44, y - 6, 11)
    frozen(draw, x - 4, y - 10, x + 60, y + 24)


def frozen_body(x, y, flip=False):
    def draw():
        rect(x, y, x + 12, y + 3, (99, 104, 101))
        rect(x - 3, y + 1, x, y + 3, DIRT_L)
        line(x + 12, y + 3, x + 18, y + 6, INK)
        line(x + 10, y + 3, x + 14, y + 8, INK)
    frozen(draw, x - 5, y - 3, x + 20, y + 10)


def serac_pile(x0, floor, prop_x):
    """Seracs: big ice blocks piled against the glacier face, the front one standing on
    a single timber. Knock the timber, or shear the one it holds."""
    blocks = [(x0 + 90, floor - 34, 42, 34), (x0 + 50, floor - 30, 40, 30),
              (x0 + 100, floor - 70, 36, 36), (x0 + 60, floor - 62, 38, 32),
              (x0 + 108, floor - 104, 30, 34), (x0 + 72, floor - 92, 32, 30),
              (x0 + 12, floor - 60, 34, 26)]
    for bx, by, w, h in blocks:
        ice_fill(bx, by, bx + w, by + h)
        frame(bx, by, bx + w, by + h, ICE)
        line(bx + 1, by + 1, bx + w - 1, by + 1, ICE_L)
        line(bx + 2, by + 2, bx + 6, by + h - 3, ICE_XL, 0.5)
    beam(prop_x, floor - 34, floor - 1, 3)                   # the timber the front block sits on
    rect(prop_x - 3, floor - 36, prop_x + 6, floor - 34, WOOD_L)
    split(jag(x0 + 50, floor - 62, x0 + 90, floor - 58, 4, 2))


def ice_bridge(x0, x1, y):
    ice_fill(x0, y, x1, y + 7)
    rect(x0, y, x1, y, ICE_L)
    rect(x0, y + 7, x1, y + 7, (48, 74, 86))
    split(jag((x0 + x1) / 2 - 2, y, (x0 + x1) / 2 + 2, y + 7, 2, 1))
    icicles(x0 + 2, x1 - 2, y + 8, 6, ICE_L, ICE_XL)


def ice_plug(x0, y0, x1, y1):
    ice_fill(x0, y0, x1, y1)
    frame(x0, y0, x1, y1, ICE)
    for k in range(3):
        line(x0 + 3 + k * 9, y0 + 3, x0 + 8 + k * 9, y1 - 3, ICE_XL, 0.5)


def build():
    new_canvas(1600, 900, seed=90413)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)
    glacier()

    carve_all([
        (14, 600, 360, FLOOR),           # A  entry tunnel, rock
        (360, 440, 1100, FLOOR),         # B  the gallery - rock roof west, ice roof east
        (40, 250, 600, 380),             # F  upper west chamber, exit A
        (14, 330, 44, 380),              #    exit A alcove
        (540, 376, 580, 444),            #    F -> B shaft
        (600, 252, 900, 292),            #    ice tunnel F -> C
        (900, 140, 1560, 290),           # C  the shelf - wave 2 stands here
        (1100, 330, 1560, 560),          # D  pillar hall under the shelf
        (1100, 600, 1590, FLOOR),        # E  east floor, exit B
        (1480, 556, 1512, 604),          #    D -> E ladder
    ], rough=3)
    for (x0, y0, x1, y1) in ((1062, 140, 1100, 200), (1056, 196, 1094, 260),
                             (1064, 256, 1100, 330), (1058, 326, 1100, 444)):
        carve(x0, y0, x1, y1, rough=2)                        # the crevasse, zigzagging down
    rock_teeth(20, 356, 602, 24)
    rock_teeth(44, 300, 252, 20)
    rock_blob(420, FLOOR, 50, 12, clip=(0, 0, 1600, FLOOR))

    floor_slab(14, 1590, FLOOR, 6)
    floor_slab(40, 540, 380, 6)
    floor_slab(580, 600, 380, 6)
    floor_slab(14, 44, 380, 4)
    floor_slab(900, 1056, 290, 6, ICE_BANDS[2], ICE_L)
    floor_slab(1104, 1560, 290, 6, ICE_BANDS[2], ICE_L)
    floor_slab(600, 900, 292, 4, ICE_BANDS[2], ICE_L)
    floor_slab(1100, 1480, 560, 6, ICE_BANDS[2], ICE_L)
    floor_slab(1512, 1560, 560, 6, ICE_BANDS[2], ICE_L)

    # icicles off every ice ceiling
    icicles(700, 1096, 442, 40, ICE_L, ICE_XL)
    icicles(904, 1556, 142, 50, ICE_L, ICE_XL)
    icicles(1104, 1556, 332, 36, ICE_L, ICE_XL)
    icicles(1200, 1586, 602, 26, ICE_L, ICE_XL)
    icicles(604, 896, 254, 18, ICE_L, ICE_XL)

    # ── light: warm in the rock, cold in the ice ────────────────────────────
    for lx, ly, r in ((100, 606, 110), (260, 606, 90), (420, 446, 110), (620, 446, 100),
                      (160, 256, 100), (400, 256, 90)):
        lamp(lx, ly, drop=6, bulb=LAMP, tint=LAMP, r=r, strength=0.22)
    for cx, cy, r in ((1230, 220, 170), (1330, 450, 170), (900, 560, 180), (1350, 650, 140),
                      (750, 272, 90), (1080, 300, 120)):
        glow(cx, cy, r, COLD, 0.1)

    # ── B  the gallery: the slab, what is frozen over it, the seracs ────────
    frozen_tub(772, 372)
    frozen_body(700, 330)
    frozen_body(960, 400)
    frozen_body(1260, 90)
    hanging_slab(730, 900, 442, 30)
    serac_pile(940, FLOOR, 1000)
    for k in range(3):
        crate(500 + k * 14, FLOOR - 13, 12)
    scrap_pile(620, FLOOR - 10, 60, 10)
    reward_pedestal(470, FLOOR, "heart", ghost=True)
    stand("Gaper", 640, FLOOR)
    stand("Gaper", 860, FLOOR, flip=True)
    stand("Minespider", 720, FLOOR)
    corpse(560, FLOOR)

    # ── A  entry ────────────────────────────────────────────────────────────
    hazard_slab(14, FLOOR - 30, 6, 29)
    rect(12, FLOOR - 33, 22, FLOOR - 31, MET_D)
    disc(17, FLOOR - 37, 1.5, RED_L)
    glow(17, FLOOR - 37, 7, RED_L, 0.4)
    hero(60, FLOOR)
    binny_half(86, FLOOR - 60)
    rubble(60, FLOOR - 2, 350, FLOOR, 60, (ROCK_M, ROCK_D, ICE))

    # ── F  upper west chamber ───────────────────────────────────────────────
    ladder(552, 384, FLOOR - 1, w=8, step=7)
    exit_door(18, 380, "gun")
    stand("Minespider", 300, 380, flip=True)
    for k in range(2):
        barrel(420 + k * 12, 366, MET, MET_L, HAZARD, w=9, h=13)
    crate(200, 367, 12)
    ice_fill(440, 252, 600, 262)                             # the ice roof creeping in

    # ── C  the shelf ────────────────────────────────────────────────────────
    ice_bridge(1054, 1106, 286)
    stand("Grenadier", 1000, 290, flip=True)
    stand("Grenadier", 1250, 290, flip=True)
    stand("Sentinel", 1420, 290, flip=True)
    for x0, x1 in ((920, 960), (1300, 1360)):
        rect(x0, 272, x1, 289, ICE_BANDS[2])                 # ice blocks for cover
        frame(x0, 272, x1, 289, ICE)
    lob(1240, 272, 1150, 288, 40)
    split(jag(1150, 290, 1170, 330, 4, 3))

    # ── D  the pillar hall ──────────────────────────────────────────────────
    for x, cr in ((1190, False), (1320, True), (1450, False)):
        ice_column(x, 296, 560, 26, cr)
    stand("Reaper", 1262, 560, flip=True)
    ladder(1492, 560, 699, w=8, step=7)
    split(jag(1110, 312, 1560, 318, 20, 3))                  # the shelf, already parting

    # ── E  east floor, exit B behind ice ────────────────────────────────────
    stand("RiotBrute", 1350, FLOOR, flip=True)
    ice_plug(1540, 640, 1578, FLOOR - 1)
    exit_door(1584, FLOOR, "skull")
    for k in range(3):
        ice_block(1200 + k * 26, FLOOR - 12, 12, 11)
    corpse(1430, FLOOR)

    for x, y, t in ((634, FLOOR - 36, "W1"), (854, FLOOR - 36, "W1"), (714, FLOOR - 30, "W1"),
                    (294, 350, "W1"), (994, 254, "W2"), (1244, 254, "W2"), (1414, 252, "W2"),
                    (1256, 524, "W3"), (1344, FLOOR - 38, "W3")):
        wave_tag(x, y, t, {"W1": PALE_G, "W2": F_MID, "W3": RED_L}[t])

    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(14, 462)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 05:  THE ICEFALL",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(120, 740, "1 IN UNDER THE ROCK", 40, 690)
    bcallout(40, 80, "2 ICE SHEARS IN SLABS - THE SPLIT SHOWS FIRST", 300, 236)
    bcallout(380, 520, "3 SLAB, AND WHAT IS FROZEN OVER IT", 800, 440)
    bcallout(1040, 116, "4 THREE COLUMNS HOLD THE SHELF", 1330, 470)
    bcallout(620, 80, "5 THEIR GRENADES CRACK YOUR ROOF", 1100, 200)
    bcallout(640, 190, "6 ICE BRIDGE", 1070, 288)
    bcallout(620, 600, "7 SERACS ON ONE TIMBER", 1000, 680)
    bcallout(1100, 80, "8 FROZEN: CUT IT OUT", 1270, 96)
    bcallout(1330, 740, "9 EXIT B IS ICE", 1556, 660)
    bcallout(40, 540, "10 PEDESTAL ON CLEAR", 470, 670)
    blegend(20, 822, [
        ("BEATS", CYAN),
        ("ICE DOES NOTHING, THEN EVERYTHING AT ONCE", (170, 180, 195)),
        ("W1 IN THE GALLERY  W2 ON THE SHELF  W3 UNDER IT", F_MID),
    ], 640)
    glyph_key(1180, 796)
    return save(out_path("RoomConcept_Icefall.png"), scale=2)


def lob(x0, y0, x1, y1, peak=40, c=F_MID):
    """A grenade's arc, dotted, and the splits it is about to run."""
    for i in range(0, 31):
        t = i / 30
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t - peak * 4 * t * (1 - t)
        px(x, y, c, 0.9 if i % 2 else 0.4)
    disc(x1, y1, 2, MET_D)
    px(x1, y1 - 2, F_HOT)


if __name__ == "__main__":
    build()
