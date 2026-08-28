"""Concept 27 - THE INCLINE.

Where [17] the hollow column is a vertical line through the sheet, this is a diagonal one:
one rope-haulage incline running corner to corner, with the whole level hung off it. A drum
house at the head, a train of cars roped to it, sheaves every few metres to keep the rope
off the floor, and stations cut in wherever the workings needed one.

The rope is the level. It is under load the entire length of the sheet, it passes through
every room worth being in, and it is holding four loaded cars on a gradient - so the
question the level asks is never "can I get down there", it is "what is attached to what".

No surface, no labels.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

HEAD = (26, 46)                  # top of the incline, inside the drum house
FOOT = (376, 194)                # bottom of it, in the loading station
HALF = 12                        # the drift is 24 tall, measured vertically
LAMP_TINT = (255, 214, 140)


def slope_at(x):
    t = (x - HEAD[0]) / (FOOT[0] - HEAD[0])
    return HEAD[1] + (FOOT[1] - HEAD[1]) * t


# ── local props ─────────────────────────────────────────────────────────────
def slope_drift(x0, x1, half=HALF):
    """Carve the incline itself: a band following the gradient, with a ragged roof and
    a lit floor line, so it reads as one continuous road rather than a row of rooms."""
    for x in range(int(x0), int(x1) + 1):
        y = slope_at(x)
        jt = int(rnd() * 3)
        rect(x, y - half + jt, x, y + half, CAVE)
        px(x, y - half + jt, CAVE_L, 0.5)
    for x in range(int(x0), int(x1) + 1):                  # the road bed
        y = slope_at(x)
        rect(x, y + half - 3, x, y + half, ROCK_D)
        px(x, y + half - 3, ROCK_L)


def slope_rails(x0, x1, step=9, broken=None):
    """Track on the gradient: rail, then a sleeper every few pixels across it."""
    for x in range(int(x0), int(x1)):
        if broken and broken[0] <= x <= broken[1]:
            continue
        y = slope_at(x) + HALF - 4
        px(x, y, MET_XL)
        px(x, y + 1, MET)
    for x in range(int(x0), int(x1), step):
        if broken and broken[0] <= x <= broken[1]:
            continue
        y = slope_at(x) + HALF - 2
        rect(x, y, x + 4, y + 1, WOOD_D)
        px(x, y, WOOD)


def slope_sets(x0, x1, step=26):
    """Timber sets down the road: two legs and a cap, square to the gradient. Without
    them the incline reads as a rail line drawn on rock instead of a drift."""
    for x in range(int(x0), int(x1), step):
        y = slope_at(x)
        rect(x - 10, y - HALF + 2, x + 10, y - HALF + 3, WOOD)
        rect(x - 10, y - HALF + 2, x + 10, y - HALF + 2, WOOD_L)
        for lx in (x - 10, x + 9):
            rect(lx, y - HALF + 3, lx + 1, y + HALF - 3, WOOD_D)
            px(lx, y - HALF + 4, WOOD)


def sheave(x):
    """Rope roller in the road bed. Small, but it is what says 'this rope moves'."""
    y = slope_at(x) + HALF - 6
    rect(x - 3, y + 2, x + 3, y + 4, MET_D)
    disc(x, y, 2.4, MET)
    ring(x, y, 2.4, MET_XL)
    px(x, y, INK)


def haul_rope(x0, x1, c=MET_L):
    for x in range(int(x0), int(x1)):
        y = slope_at(x) + HALF - 7
        px(x, y, c if x % 3 else MET_D)


def slope_car(x, loaded=True, wrecked=False):
    """A car on the gradient. Sits on the rail line, leaning with the road."""
    y = slope_at(x) + HALF - 5
    if wrecked:
        for _ in range(22):
            px(x - 8 + rnd() * 18, y - 8 + rnd() * 10, pick([MET_D, MET, ROCK_M]))
        for wx in (x - 4, x + 6):
            disc(wx, y + 1, 2, INK)
            disc(wx, y + 1, 1, MET_L)
        return
    rect(x, y - 7, x + 13, y, MET)
    rect(x, y - 7, x + 13, y - 7, MET_XL)
    rect(x + 1, y - 6, x + 12, y - 4, (58, 46, 34))
    if loaded:
        for _ in range(9):
            px(x + 2 + int(rnd() * 10), y - 8 + int(rnd() * 3),
               pick([DIRT_L, GREEN_L, ROCK_L]))
    rect(x, y, x + 13, y + 1, MET_D)
    for wx in (x + 3, x + 10):
        disc(wx, y + 2, 2, INK)
        disc(wx, y + 2, 1, MET_L)


def coupling(x0, x1):
    y0, y1 = slope_at(x0) + HALF - 6, slope_at(x1) + HALF - 6
    line(x0, y0, x1, y1, MET_L)
    line(x0, y0 + 1, x1, y1 + 1, MET_D)


def drum(cx, cy, r=13):
    disc(cx, cy, r, MET)
    ring(cx, cy, r, MET_XL)
    for i in range(int(r / 3)):
        ring(cx, cy, r - 3 - i * 3, WOOD_D if i % 2 else WOOD)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        line(cx, cy, cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2), MET_D, 0.8)
    disc(cx, cy, 2.4, MET_D)
    ring(cx, cy, 2.4, MET_L)
    for k in range(12):                                    # brake band round the top
        a = -2.4 + k * 0.16
        px(cx + math.cos(a) * (r + 2), cy + math.sin(a) * (r + 2), MET_XL)


def refuge(x, depth=9):
    """A man-hole cut in the upper wall: the only place on the road that is not the road."""
    y = slope_at(x)
    rect(x - 7, y - HALF - depth, x + 7, y - HALF + 2, CAVE)
    for rx in range(int(x) - 7, int(x) + 8):
        px(rx, y - HALF - depth, CAVE_L, 0.5)
    rect(x - 7, y - HALF - 1, x + 7, y - HALF + 1, ROCK_D)
    px(x - 7, y - HALF - 1, ROCK_L)


def stone_steps(x0, x1, n=9):
    """Footway alongside, cut as steps into the road bed."""
    for k in range(n):
        x = x0 + (x1 - x0) * k / n
        y = slope_at(x) + HALF - 3
        rect(x, y - 2, x + int((x1 - x0) / n) - 1, y - 1, ROCK_M)
        px(x, y - 2, ROCK_L)


def catch_pit(x0, x1, y):
    """Baulks of timber across the foot of the incline, and what they have caught."""
    rect(x0, y, x1, y + 6, CAVE)
    for bx in range(int(x0), int(x1), 7):
        rect(bx, y, bx + 4, y + 6, WOOD_D)
        rect(bx, y, bx + 4, y, WOOD)
    for _ in range(24):
        px(x0 + rnd() * (x1 - x0), y - 4 + rnd() * 6, pick([MET_D, MET, ROCK_M, WOOD_D]))


def ore_bin(x, base, w=26, h=14):
    rect(x, base - h, x + w, base, MET_D)
    rect(x, base - h, x + w, base - h, MET_L)
    rect(x + 2, base - h + 2, x + w - 2, base - h + 5, (58, 46, 34))
    for _ in range(14):
        px(x + 3 + rnd() * (w - 5), base - h - 1 + rnd() * 4,
           pick([GREEN_L, PALE_G, DIRT_L]))
    for k in range(3):                                     # gate at the bottom
        rect(x + w // 2 - 4 + k * 3, base - 3, x + w // 2 - 3 + k * 3, base, MET_L)


def chute(x, y0, y1, w=12, tilt=0):
    for i in range(int(y1 - y0)):
        t = i / max(y1 - y0, 1)
        sx = x + tilt * t
        rect(sx, y0 + i, sx + 1, y0 + i, MET_D)
        rect(sx + w, y0 + i, sx + w + 1, y0 + i, MET_D)
        px(sx, y0 + i, MET_L)
    for _ in range(8):
        px(x + 2 + rnd() * (w - 3) + tilt * rnd(), y0 + rnd() * (y1 - y0),
           pick([ROCK_L, DIRT_L, GREEN_L]))


def build():
    new_canvas(400, 225, seed=52713)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=24)
    for _ in range(42):
        rect(rnd() * cw, rnd() * 14, rnd() * cw + 6, rnd() * 14 + 1, ROCK_D, 0.5)

    ROOMS = [
        (12, 16, 98, 60),       # drum house, at the head
        (112, 14, 256, 52),     # upper loading gallery
        (26, 118, 178, 158),    # west gallery, under the road
        (20, 176, 198, 210),    # deep drift
        (298, 46, 392, 94),     # ore pass house, east
        (268, 162, 392, 210),   # loading station at the foot
        (146, 50, 166, 100),    # gallery -> road, as a chute shaft
        (150, 102, 172, 124),   # road -> west gallery
        (58, 156, 82, 178),     # west gallery -> deep drift
        (344, 92, 368, 166),    # ore pass down to the station
    ]
    carve_all(ROOMS)
    slope_drift(20, 382)
    for x in (200, 232):                                   # a passing loop, widened
        rect(x - 16, slope_at(x) - HALF - 8, x + 16, slope_at(x) - HALF + 2, CAVE)

    # ── the road ──────────────────────────────────────────────────────────
    slope_sets(38, 372, 27)
    slope_rails(24, 380, broken=(300, 314))
    for x in range(60, 380, 46):
        sheave(x)
    haul_rope(40, 300)
    stone_steps(60, 140, 8)
    stone_steps(240, 300, 6)
    for rx in (120, 216, 300):
        refuge(rx, 10)
    refuge_crew = ((120, MET_L, GREEN), (216, DIRT_L, RED))
    for rx, coat, trim in refuge_crew:
        humanoid(rx - 3, slope_at(rx) - HALF - 8, coat, trim, face_right=False)
    for lx in range(80, 380, 60):
        lamp(lx, slope_at(lx) - HALF + 2, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT,
             r=20, strength=0.24)
    for _ in range(16):                                    # dust the cars kick up
        x = 240 + rnd() * 140
        disc(x, slope_at(x) - 4 + rnd() * 8, 1 + rnd() * 3, (146, 140, 128), 0.11)
    for _ in range(26):                                    # spillage down the road
        x = 30 + rnd() * 340
        px(x, slope_at(x) + HALF - 5 + rnd() * 3, pick([DIRT_L, ROCK_L, GREEN_L]), 0.8)

    # ── the train, four cars on the rope ──────────────────────────────────
    train = (250, 268, 286, 304)
    for k, x in enumerate(train):
        slope_car(x, loaded=(k != 3))
    for a, b in zip(train, train[1:]):
        coupling(a + 13, b)
    haul_rope(230, 252, MET_XL)
    slope_car(330, wrecked=True)                           # and one that got away
    for _ in range(18):
        px(316 + rnd() * 40, slope_at(316 + rnd() * 40) + HALF - 8 + rnd() * 6,
           pick([MET_D, ROCK_M]), 0.8)

    # ── 1  drum house ─────────────────────────────────────────────────────
    floor_slab(12, 98, 54, 4, ROCK_D, ROCK_L)
    rock_teeth(16, 94, 18, 10)
    drum(44, 36, 13)
    rect(40, 50, 48, 54, MET_D)                            # bed
    rect(40, 50, 48, 50, MET_L)
    rect(43, 36, 45, 50, MET)
    gear(70, 42, 9, teeth=9)
    line(57, 34, 70, 42, WOOD_D)
    line(58, 35, 71, 43, WOOD)
    haul_rope(44, 60, MET_XL)
    line(44, 36, 40, 44, MET_L)
    lever = 84
    rect(lever, 40, lever + 1, 52, MET_L)                  # brake lever
    disc(lever, 39, 1.6, RED_L)
    humanoid(88, 42, MET_L, DIRT_L, face_right=False)
    lamp(28, 18, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.28)
    pipe_run(14, 96, 20)

    # ── 2  upper loading gallery ──────────────────────────────────────────
    floor_slab(112, 256, 46, 4, ROCK_D, ROCK_L)
    rock_teeth(116, 252, 16, 12)
    rails(116, 252, 44, broken=(200, 212))
    cart(130, 35)
    cart(176, 35, tipped=True)
    ore_bin(216, 45, 30, 16)
    chute(148, 52, 96, 12, tilt=2)                         # down onto the road
    plank(114, 16, 254, 18, 2)
    for pxx in (124, 168, 232):
        beam(pxx, 18, 46, 2, WOOD_D, WOOD)
    humanoid(154, 34, DIRT_L, GREEN, face_right=False)
    humanoid(200, 34, MET_L, RED)
    tracer(202, 38, 176, 40)
    for lx in (140, 208):
        lamp(lx, 18, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    scrap_pile(240, 45, 14, 6, (DIRT, DIRT_D, ROCK_M))

    # ── 3  west gallery, under the road ───────────────────────────────────
    floor_slab(26, 178, 152, 4, DIRT_D, DIRT)
    rock_teeth(30, 174, 120, 12)
    plank(28, 120, 176, 120, 2)
    for pxx in (36, 76, 116, 156):
        beam(pxx, 121, 152, 2, WOOD_D, WOOD)
    rails(30, 176, 150, broken=(96, 112))
    cart(46, 141)
    ore_bin(122, 151, 26, 14)
    humanoid(70, 140, DIRT_L, RED, face_right=False)
    player(96, 140)
    binny(110, 130)
    tk_beam(102, 144, 132, 132)
    rect(126, 128, 140, 136, ROCK_M)                       # a rock, held
    rect(126, 128, 140, 128, ROCK_L)
    ladder(160, 122, 150, w=4, step=6)
    for lx in (56, 140):
        lamp(lx, 121, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    rubble(90, 146, 120, 151, 26, (ROCK_M, ROCK_D, DIRT))

    # ── 4  deep drift ─────────────────────────────────────────────────────
    floor_slab(20, 198, 204, 5, DIRT_D, DIRT)
    rock_teeth(24, 194, 178, 12)
    rails(24, 196, 202)
    cart(60, 193)
    cart(140, 193, tipped=True)
    plank(22, 180, 196, 180, 2)
    for pxx in (32, 96, 168):
        beam(pxx, 181, 204, 2, WOOD_D, WOOD)
    ore_bin(104, 203, 28, 15)
    humanoid(84, 192, MET_L, GREEN, face_right=False)
    ragdoll(160, 188)
    lamp(48, 181, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    lamp(150, 181, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.22)
    binny(176, 192)

    # ── 5  ore pass house, east ───────────────────────────────────────────
    floor_slab(298, 392, 88, 4, ROCK_D, ROCK_L)
    rock_teeth(302, 388, 48, 10)
    ore_bin(310, 87, 30, 16)
    ore_bin(350, 87, 26, 14)
    chute(346, 92, 164, 14, tilt=2)                        # down to the station
    conveyor(302, 388, 66, direction=1)
    for _ in range(20):
        px(304 + rnd() * 82, 63 + rnd() * 3, pick([DIRT_L, GREEN_L, ROCK_L]))
    humanoid(330, 76, DIRT_L, RED, face_right=False)
    lamp(320, 50, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    lamp(376, 50, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.22)

    # ── 6  station at the foot ────────────────────────────────────────────
    floor_slab(268, 392, 204, 5, ROCK_D, ROCK_L)
    rock_teeth(272, 388, 164, 12)
    catch_pit(352, 382, 194)
    rails(272, 350, 202, broken=(320, 330))
    cart(284, 193)
    ore_bin(300, 203, 28, 15)
    plank(270, 172, 390, 174, 2)
    for pxx in (280, 330, 378):
        beam(pxx, 174, 202, 2, WOOD_D, WOOD)
    humanoid(340, 192, MET_L, RED, face_right=False)
    ragdoll(322, 188, RED_L)
    scrap_pile(356, 203, 30, 12, (MET_D, MET, ROCK_M, WOOD_D))
    door(272, 176, 22, 26)
    glow(283, 189, 20, PALE_G, 0.16)
    lamp(310, 174, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    for _ in range(18):
        disc(276 + rnd() * 110, 176 + rnd() * 26, 1 + rnd() * 3, (146, 140, 128), 0.10)

    vignette()
    return save(out_path("LevelConcept_TheIncline.png"))


if __name__ == "__main__":
    build()
