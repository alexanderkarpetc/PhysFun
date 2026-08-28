"""Concept 28 - THE GREAT STOPE.

One room. The ore body dipped, so the stope follows it: a single slanted void the width of
the sheet, sixty metres of it, and every floor in it is timber the crew put there. Stulls
wedged from footwall to hanging wall, staging laid on the stulls, ladders between the lifts,
ore passes dropped through the footwall to the haulage below.

This is [16] Timber Deep's idea taken to the end of its logic: the level is made of wood,
inside a hole made of rock, and the wood is holding the rock. The difference is that here
there is no floor underneath it - what a stull drops, it drops all the way to the sill.

No surface, no labels.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

VX0, VX1 = 28, 374               # the stope, west end to east end
DIP = 0.30                       # how fast the ore body falls away
LAMP_TINT = (255, 214, 140)
ORE = (159, 187, 83)


def hanging(x):
    """The roof of the stope - the hanging wall, following the dip."""
    return 44 + DIP * (x - VX0) - 5 * math.sin((x - VX0) / 46.0)


def foot(x):
    """The floor of it - the footwall, a little further down and not parallel."""
    return hanging(x) + 56 + 10 * math.sin((x - VX0) / 38.0 + 1.2)


def mid(x, t=0.5):
    return hanging(x) + (foot(x) - hanging(x)) * t


# ── local props ─────────────────────────────────────────────────────────────
def stope_void(x0, x1):
    """Carve the slanted void, roof and floor both ragged, both lit along the edge."""
    for x in range(int(x0), int(x1) + 1):
        yt, yb = hanging(x) + int(rnd() * 3), foot(x) - int(rnd() * 3)
        rect(x, yt, x, yb, CAVE)
        px(x, yt, ROCK_L, 0.85)                            # lit under the hanging wall
        px(x, yt + 1, ROCK_M, 0.55)
        if chance(0.3):
            px(x, yt + 2, ROCK_M, 0.3)
        rect(x, yb - 3, x, yb, ROCK_D)                     # the sill, as a floor slab
        px(x, yb - 3, ROCK_L)
        if chance(0.25):
            px(x, yb - 4, ROCK_M, 0.6)


def stull(x, wedge_top=True, snapped=False):
    """One timber wedged across the stope. The whole level stands on these."""
    yt, yb = hanging(x) + 2, foot(x) - 1
    if snapped:
        rect(x, yt, x + 2, yt + 9, WOOD_D)                 # stub in the roof
        rect(x, yb - 12, x + 2, yb, WOOD_D)                # stub in the floor
        for k in range(7):                                 # the rest of it, on the floor
            rect(x - 14 + k * 4, yb - 2 - rnd() * 3, x - 8 + k * 4, yb - 1, WOOD_D)
        for _ in range(20):
            px(x - 12 + rnd() * 26, yt + 10 + rnd() * (yb - yt - 20),
               pick([ROCK_M, ROCK_D, WOOD_D]))
        return
    rect(x, yt, x + 2, yb, WOOD)
    rect(x, yt, x, yb, WOOD_L)
    rect(x + 2, yt, x + 2, yb, WOOD_D)
    if wedge_top:                                          # driven tight against the roof
        for k in range(3):
            rect(x - 1 + k, yt - 3 + k, x + 3 - k, yt - 3 + k, WOOD_L if k == 0 else WOOD)
    for k in range(3):                                     # and against the floor
        rect(x - 1 + k, yb + 1 + k, x + 3 - k, yb + 1 + k, WOOD_D)


def staging(x0, x1, t=0.5, step=26):
    """Plank floor laid along the dip, on top of the stulls. Follows the ore body, so
    nothing in this room is level."""
    for x in range(int(x0), int(x1)):
        y = mid(x, t)
        px(x, y, WOOD)
        px(x, y + 1, WOOD_D)
    for x in range(int(x0), int(x1), step):                # bearers under it
        y = mid(x, t)
        rect(x, y + 2, x + 5, y + 3, WOOD_D)


def stope_ladder(x, t0, t1):
    y0, y1 = mid(x, t0), mid(x, t1)
    ladder(x, min(y0, y1) + 2, max(y0, y1) - 1, w=4, step=6)


def ore_pass(x, y0, y1, w=11):
    """A hole through the footwall, timbered, dropping ore to the haulage below."""
    rect(x, y0, x + w, y1, CAVE)
    for side in (x, x + w):
        rect(side, y0, side + 1, y1, WOOD_D)
    for y in range(int(y0), int(y1), 7):
        rect(x, y, x + w, y, WOOD_D, 0.7)
    for _ in range(10):
        px(x + 2 + rnd() * (w - 3), y0 + rnd() * (y1 - y0), pick([ORE, DIRT_L, ROCK_L]))
    rect(x - 2, y1 - 3, x + w + 2, y1, MET_D)              # chute gate at the bottom
    rect(x - 2, y1 - 3, x + w + 2, y1 - 3, MET_L)


def fill(x0, x1, t=0.9):
    """Waste packed back into the stope - the mine's own answer to the support problem."""
    for _ in range((x1 - x0) * 3):
        x = x0 + rnd() * (x1 - x0)
        y = foot(x) - rnd() * (foot(x) - mid(x, t))
        px(x, y, pick([ROCK_M, ROCK_D, DIRT, DIRT_D]))
    for x in range(int(x0), int(x1), 2):                   # crest of the fill, caught by
        px(x, mid(x, t), ROCK_L, 0.75)                     # the lamps above it


def rockfall(x, n=60):
    """Hanging wall that has already come away, and the dust still standing in it."""
    for _ in range(n):
        rx = x + (rnd() - 0.5) * 30
        ry = hanging(rx) + rnd() * (foot(rx) - hanging(rx))
        px(rx, ry, pick([ROCK_M, ROCK_D, DIRT]))
    for _ in range(16):
        rx = x + (rnd() - 0.5) * 34
        disc(rx, hanging(rx) + rnd() * 30, 1 + rnd() * 3.5, (150, 146, 138), 0.12)


def slab_hanging(x, w=26, d=7):
    """A slab of roof mid-detachment: cracked out, still up there. For now."""
    for k in range(d):
        rect(x, hanging(x) + k, x + w, hanging(x) + k, ROCK_M if k else ROCK_L)
    for _ in range(10):
        cx = x + rnd() * w
        line(cx, hanging(cx) - 1, cx + 3 - rnd() * 6, hanging(cx) - 6, ROCK_D, 0.8)
    for i in range(4):
        px(x + rnd() * w, hanging(x) + d + 2 + i * 3, DIRT_L, 0.5)


def build():
    new_canvas(400, 225, seed=52814)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=26)
    for _ in range(44):
        rect(rnd() * cw, rnd() * 14, rnd() * cw + 6, rnd() * 14 + 1, ROCK_D, 0.5)

    ROOMS = [
        (18, 14, 206, 38),      # top drift, feeding the stope
        (14, 178, 188, 208),    # haulage under the footwall
        (330, 16, 392, 62),     # hoist chamber, east
        (60, 36, 82, 52),       # winze from the top drift into the stope
        (24, 150, 48, 182),     # west end -> haulage
    ]
    carve_all(ROOMS)
    stope_void(VX0, VX1)

    # ── the timber that makes the room usable ──────────────────────────────
    SNAPPED = 214
    for x in range(VX0 + 10, VX1 - 6, 24):
        stull(x, snapped=(x == SNAPPED))
    staging(VX0 + 6, VX1 - 8, 0.34)
    staging(VX0 + 30, VX1 - 24, 0.66)
    for x, t0, t1 in ((70, 0.34, 0.66), (150, 0.34, 0.66), (230, 0.34, 0.66),
                      (110, 0.66, 0.95), (196, 0.66, 0.95)):
        stope_ladder(x, t0, t1)
    for x in range(VX0 + 20, VX1 - 20, 58):                # rope hand-lines up the dip
        for y in range(int(mid(x, 0.34)) - 8, int(mid(x, 0.34)), 3):
            px(x + 8, y, WOOD_L)
            px(x + 9, y + 1, WOOD_D)

    # ── what is in the stope ──────────────────────────────────────────────
    fill(VX0 + 4, 120, 0.86)
    fill(268, VX1 - 6, 0.82)
    rockfall(SNAPPED, 70)
    slab_hanging(96, 30, 7)
    for _ in range(30):                                    # ore in the walls
        x = VX0 + rnd() * (VX1 - VX0)
        y = hanging(x) + 3 + rnd() * 6
        rect(x, y, x + 1 + rnd() * 2, y, pick([ORE, PALE_G]), 0.9)
    for _ in range(24):
        x = VX0 + rnd() * (VX1 - VX0)
        y = foot(x) - 2 - rnd() * 5
        rect(x, y, x + 1 + rnd() * 2, y, pick([ORE, DIRT_L]), 0.85)

    for lx in range(VX0 + 26, VX1 - 20, 52):               # lamps on the stulls
        lamp(lx + 3, mid(lx, 0.30), drop=3, bulb=LAMP_TINT, tint=LAMP_TINT,
             r=22, strength=0.24)
    for _ in range(26):
        x = VX0 + rnd() * (VX1 - VX0)
        disc(x, mid(x, rnd()), 1 + rnd() * 3, (146, 142, 130), 0.09)

    # ── the crew, working the lifts ───────────────────────────────────────
    for x, t, coat, trim, right in ((58, 0.34, DIRT_L, RED, True),
                                    (132, 0.34, MET_L, GREEN, False),
                                    (188, 0.34, DIRT_L, DIRT_L, False),
                                    (300, 0.34, MET_L, RED, False),
                                    (86, 0.66, DIRT_L, GREEN, True),
                                    (206, 0.66, MET_L, DIRT_L, False)):
        humanoid(x, mid(x, t) - 12, coat, trim, face_right=right)
    for x, t0, t1 in ((296, 0.34, 0.66), (340, 0.66, 0.94)):
        stope_ladder(x, t0, t1)
    for x, t, coat, trim in ((330, 0.66, DIRT_L, GREEN), (352, 0.34, MET_L, RED)):
        humanoid(x, mid(x, t) - 12, coat, trim, face_right=False)
    for x in (312, 344):
        crate(x, mid(x, 0.66) - 8, 7)
    scrap_pile(316, mid(316, 0.94), 30, 10, (ROCK_M, ROCK_D, DIRT, WOOD_D))
    for x, t in ((246, 0.34), (170, 0.66)):
        crate(x, mid(x, t) - 8, 7)
    barrel(276, mid(276, 0.34) - 8, WOOD, WOOD_L, MET_L)
    ragdoll(SNAPPED + 18, mid(SNAPPED + 18, 0.5), RED_L)
    ragdoll(124, foot(124) - 12)
    tracer(300, mid(300, 0.34) - 8, 268, mid(268, 0.34) - 6)

    player(150, mid(150, 0.34) - 12)
    binny(164, mid(164, 0.34) - 24)
    tk_beam(154, mid(154, 0.34) - 8, 186, mid(186, 0.34) - 20)
    rect(180, mid(186, 0.34) - 26, 194, mid(186, 0.34) - 18, WOOD)   # a stull, in the air
    rect(180, mid(186, 0.34) - 26, 194, mid(186, 0.34) - 26, WOOD_L)

    # ── ore passes down to the haulage ────────────────────────────────────
    for px_ in (54, 104, 156):
        ore_pass(px_, foot(px_) - 2, 180, 11)

    # ── 1  top drift ─────────────────────────────────────────────────────
    floor_slab(18, 206, 32, 4, ROCK_D, ROCK_L)
    rock_teeth(22, 202, 16, 12)
    rails(22, 202, 30, broken=(150, 162))
    cart(40, 21)
    cart(122, 21, tipped=True)
    plank(20, 16, 204, 16, 2)
    for pxx in (30, 92, 168):
        beam(pxx, 17, 32, 2, WOOD_D, WOOD)
    humanoid(76, 20, MET_L, DIRT_L)
    lamp(60, 17, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    lamp(180, 17, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    for y in range(38, int(hanging(70)), 3):               # the winze, into the stope
        px(70, y, WOOD_L)
        px(71, y + 1, WOOD_D)

    # ── 2  haulage under the footwall ────────────────────────────────────
    floor_slab(14, 188, 202, 5, DIRT_D, DIRT)
    rock_teeth(18, 184, 180, 10)
    rails(18, 186, 200, broken=(120, 132))
    cart(28, 191)
    cart(96, 191)
    cart(152, 191, tipped=True)
    plank(16, 182, 186, 182, 2)
    for pxx in (24, 78, 140, 180):
        beam(pxx, 183, 202, 2, WOOD_D, WOOD)
    humanoid(62, 190, DIRT_L, RED, face_right=False)
    humanoid(168, 190, MET_L, GREEN, face_right=False)
    for _ in range(26):                                    # ore off the passes
        px(50 + rnd() * 120, 196 + rnd() * 5, pick([ORE, DIRT_L, ROCK_L]), 0.85)
    lamp(44, 183, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    lamp(160, 183, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.22)
    binny(112, 190)

    # ── 3  hoist chamber, east ──────────────────────────────────────────
    floor_slab(330, 392, 56, 4, ROCK_D, ROCK_L)
    rock_teeth(334, 388, 18, 8)
    gear(352, 38, 11, teeth=10)
    gear(376, 30, 7, teeth=8)
    line(352, 38, 376, 30, WOOD_D)
    line(353, 39, 377, 31, WOOD)
    disc(340, 44, 4, MET)
    ring(340, 44, 4, MET_XL)
    for y in range(48, int(hanging(340)) + 8):              # rope down into the stope
        px(340, y, MET_L if y % 3 else MET_D)
    rect(332, int(hanging(340)) + 8, 348, int(hanging(340)) + 14, MET)   # skip
    frame(332, int(hanging(340)) + 8, 348, int(hanging(340)) + 14, MET_XL)
    humanoid(362, 44, MET_L, DIRT_L, face_right=False)
    lamp(344, 18, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)

    # ── the way out, at the deep east end of the stope ───────────────────
    ex = VX1 - 30
    door(ex, foot(ex) - 28, 24, 26)
    glow(ex + 12, foot(ex) - 14, 22, PALE_G, 0.16)

    vignette()
    return save(out_path("LevelConcept_TheGreatStope.png"))


if __name__ == "__main__":
    build()
