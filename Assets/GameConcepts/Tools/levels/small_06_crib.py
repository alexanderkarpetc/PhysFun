"""Small room S06 - THE CRIB.

A round room whose roof has let go: one big slab of it has parted from the rock along a
crack and is standing on a single timber crib - a log-cabin stack of square sets - on a
rubble mound in the middle of the floor. The crew camp under it, on both sides of the
crib. Burn the crib, or shoot it out, and the slab drops on the camp.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S06"

FLOOR = 324
SLAB_X0, SLAB_X1 = 92, 308
CRIB_X, CRIB_W = 176, 48
MOUND_TOP = 272
SLAB = set()                    # local cells of the slab, filled in by the edit
SLAB_C = (82, 86, 92)
SLAB_L = (112, 118, 126)
SLAB_D = (50, 54, 60)


def slab_bottom(lx):
    return 198 - 46 * ((lx - 200) / 108.0) ** 2 + 2 * math.sin(lx * 0.31)


def mound_top(lx):
    return min(FLOOR, MOUND_TOP + 0.012 * (lx - 200) ** 2)


def crib_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR:
            continue
        if ly >= mound_top(lx):
            continue
        if ly >= 176 and ((lx - 8) / 98.0) ** 2 + ((ly - 204) / 28.0) ** 2 < 1:
            continue                                        # the west perch's floor
        if ly >= 214 and ((lx - 404) / 84.0) ** 2 + ((ly - 240) / 26.0) ** 2 < 1:
            continue                                        # the east perch's floor
        out.add((x, y))
    # the slab: everything from 3px under the roof down to its own underside. The 3px
    # left as air is the crack it parted along.
    SLAB.clear()
    roofs = {}
    for (x, y) in out:
        lx = x - ox
        if SLAB_X0 <= lx < SLAB_X1 and y - oy < roofs.get(lx, 10 ** 6):
            roofs[lx] = y - oy
    for lx, roof in roofs.items():
        for ly in range(roof + 3, int(slab_bottom(lx)) + 1):
            SLAB.add((lx, ly))
            out.discard((ox + lx, oy + ly))
    return out


def paint_slab(ox, oy):
    """Roof rock gone loose: its own darker body, bedding lines across it, a lit
    underside, and the crack round its top in ink."""
    for (lx, ly) in SLAB:
        r = rnd()
        px(ox + lx, oy + ly, SLAB_D if r < 0.12 else ROCK_M if r < 0.2 else SLAB_C)
    for k in range(5):                                       # bedding
        base = 96 + k * 16
        for lx in range(SLAB_X0, SLAB_X1):
            ly = base + 4 * math.sin(lx * 0.045 + k)
            if (lx, int(ly)) in SLAB and (lx, int(ly) - 2) in SLAB and (lx, int(ly) + 2) in SLAB:
                px(ox + lx, oy + ly, SLAB_D, 0.7)
    for (lx, ly) in SLAB:
        if (lx, ly + 1) not in SLAB:
            px(ox + lx, oy + ly, SLAB_L)
            px(ox + lx, oy + ly - 1, SLAB_C)
        if (lx, ly - 1) not in SLAB:
            for d in range(1, 4):
                px(ox + lx, oy + ly - d, INK)
    for lx in (SLAB_X0 + 2, SLAB_X0 + 30, SLAB_X1 - 40, SLAB_X1 - 6):   # dust out of the crack
        top = min((ly for (x, ly) in SLAB if x == lx), default=None)
        if top is None:
            continue
        for i in range(6):
            px(ox + lx + rnd() * 3, oy + slab_bottom(lx) + 4 + i * 5 + rnd() * 3, DIRT_L, 0.6)


def crib(x, base, top, w):
    """Log-cabin crib side-on: courses alternate between two end-grain blocks and a
    beam laid across them, so it reads as a stack, not a post."""
    y, course = base, 0
    while y > top + 5:
        if course % 2:
            rect(x - 2, y - 5, x + w + 2, y - 1, WOOD)
            rect(x - 2, y - 5, x + w + 2, y - 5, WOOD_L)
            rect(x - 2, y - 1, x + w + 2, y - 1, WOOD_D)
            for k in range(x + 5, x + w - 2, 11):
                px(k, y - 3, WOOD_D)
        else:
            for bx in (x, x + w - 9):                       # end grain, ring and heart
                rect(bx, y - 5, bx + 9, y - 1, WOOD_D)
                disc(bx + 4.5, y - 3, 2.2, WOOD)
                px(bx + 4, y - 3, WOOD_L)
            rect(x + 10, y - 5, x + w - 10, y - 1, (62, 47, 33))   # the back course, through the hollow
            rect(x + 10, y - 5, x + w - 10, y - 5, (84, 64, 44))
        y -= 5
        course += 1
    for side in (-1, 1):                                     # wedges driven in under the slab
        wx = x + w // 2 + side * 8
        for i in range(4):
            rect(wx - 4 + (i if side > 0 else 0), top + i, wx + 4 - (0 if side > 0 else i), top + i,
                 WOOD_L if i == 0 else WOOD)
    rect(x - 2, top + 4, x + w + 2, y, WOOD_D)


def crush_marks(x, y):
    """Splits in the top courses, where the load comes on."""
    for i in range(5):
        px(x + i, y + i // 2, INK)
    for i in range(4):
        px(x + 20 - i, y + 3 + i, INK)


def crib_furnish(ox, oy, m):
    paint_slab(ox, oy)
    teeth(m, ox + 20, ox + SLAB_X0 - 4, oy + 150, 6)
    teeth(m, ox + SLAB_X1 + 4, ox + 380, oy + 160, 6)
    for x, y, d, rx, ry in ((40, 290, -1, 14, 9), (360, 300, 1, 14, 8), (30, 140, -1, 10, 7),
                            (370, 196, 1, 10, 7)):
        x0, y0 = ox + x, oy + y
        while (x0, y0) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), y0, rx, ry, rough=0.25)

    # the mound and the crib on it
    for lx in range(140, 262):
        top = int(mound_top(lx))
        for ly in range(top, min(top + 4, FLOOR)):
            px(ox + lx, oy + ly, pick([DIRT, DIRT_L, ROCK_M, DIRT_D]))
    cb = oy + int(mound_top(CRIB_X + CRIB_W // 2))
    ct = oy + int(slab_bottom(CRIB_X + CRIB_W // 2)) + 1
    crib(ox + CRIB_X, cb, ct, CRIB_W)
    crush_marks(ox + CRIB_X + 6, ct + 8)
    lamp(ox + CRIB_X - 2, ct + 30, drop=6, bulb=LAMP, tint=LAMP, r=70, strength=0.16)   # hung off the crib
    rect(ox + CRIB_X - 4, ct + 30, ox + CRIB_X, ct + 30, MET_D)

    # the camp under the slab, both sides of the crib
    fy = oy + FLOOR
    for cx in (130, 274):
        lamp(ox + cx, oy + int(slab_bottom(cx)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.12)
    keg(ox + 226, oy + int(mound_top(230)))
    keg(ox + 162, oy + int(mound_top(166)))
    crate_g(ox + 96, fy)
    crate_g(ox + 40, fy)
    crate_g(ox + 44, fy - 13, 10)
    for bx in (100, 300):                                    # bedrolls
        rect(ox + bx, fy - 3, ox + bx + 13, fy - 1, (92, 70, 60))
        rect(ox + bx, fy - 3, ox + bx + 13, fy - 3, (122, 96, 80))
        rect(ox + bx + 10, fy - 4, ox + bx + 13, fy - 2, (150, 140, 120))
    for k in range(3):                                       # picks leaned on the east wall
        line(ox + 350 + k * 4, fy - 1, ox + 356 + k * 4, fy - 20, WOOD_D)
        rect(ox + 353 + k * 4, fy - 21, ox + 359 + k * 4, fy - 20, MET_L)
    scrap_pile(ox + 300, fy, 24, 5, colors=(MET_D, DIRT, ROCK_M, WOOD_D))
    stand("Gaper", ox + 120, fy)
    stand("WizRamskull", ox + 146, oy + int(mound_top(146)))
    stand("RiotBrute", ox + 262, oy + int(mound_top(262)), flip=True)
    stand("BloodMage", ox + 290, fy, flip=True)
    stand("Gaper", ox + 72, fy)
    corpse(ox + 330, fy)

    # the perches either side, out from under it
    p1 = oy + 176
    stand("Grenadier", ox + 70, p1)
    crate_g(ox + 24, p1, 10)
    p2 = oy + 214
    stand("Sentinel", ox + 352, p2, flip=True)
    lamp(ox + 22, ceil_at(m, ox + 22, p1 - 6) + 1, drop=4, bulb=LAMP, tint=LAMP, r=40, strength=0.12)


ROOM = {
    "name": "THE CRIB", "w": 400, "h": 380,
    "shapes": [([("blob", 200, 215, 176, 140),
                 ("blob", 200, 300, 170, 40)], 0.08),          # the floor
               ([("blob", 52, 154, 56, 30),                    # the west perch
                 ("blob", 356, 196, 48, 26)], 0.12)],          # the east perch
    "sockets": {"T1": ("T", 44, 130), "T2": ("T", 344, 140),
                "L1": ("L", 176, 12), "R1": ("R", 214, 16),
                "L2": ("L", FLOOR, 44), "R2": ("R", FLOOR, 44)},
    "edit": crib_edit,
    "furnish": crib_furnish,
}


SHEET = {
    "seed": 70606,
    "callouts": [
        ("1 ROOF SLAB, PARTED", (230, -50), (250, 110)),
        ("2 ONE CRIB HOLDS IT", (296, 400), (217, 240)),
        ("3 THE CAMP UNDER IT", (-120, 400), (120, 310)),
    ],
    "beats": [
        ("BURN OR SHOOT OUT THE CRIB, THE SLAB DROPS ON THE CAMP", (170, 180, 195)),
        ("GRENADIER AND SENTINEL ON THE PERCHES, CLEAR OF IT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
