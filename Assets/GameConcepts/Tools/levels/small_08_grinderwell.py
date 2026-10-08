"""Small room S08 - THE GRINDER WELL.

A round room whose floor is a funnel: both sides slope in to a throat in the middle,
and in the throat two toothed wheels mesh, turning in. Under them, a little bin cave
where what went through comes out. Belts on rock ledges either side, at different
heights, drag toward the funnel and tip off their ends onto the slope. Anything that
goes off a belt - a crate, a keg, a Gaper - slides down to the wheels.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S08"

CX = 200
THROAT = 22                      # half width of the throat
WHEEL_Y, WHEEL_R = 372, 14
WEST_LEDGE, EAST_LEDGE = 150, 204
PERCH = 108
RUBBER = (40, 38, 40)


def funnel(lx):
    return 362 - 0.85 * abs(lx - CX)


def well_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= funnel(lx) and not (abs(lx - CX) < THROAT and ly < 392):
            if ly < 392:
                continue
        if ly >= WEST_LEDGE and ((lx + 4) / 128.0) ** 2 + ((ly - WEST_LEDGE - 12) / 22.0) ** 2 < 1:
            continue                                        # west ledge
        if ly >= EAST_LEDGE and ((lx - 404) / 116.0) ** 2 + ((ly - EAST_LEDGE - 10) / 20.0) ** 2 < 1:
            continue                                        # east ledge
        if ly >= PERCH and ((lx - 400) / 64.0) ** 2 + ((ly - PERCH - 8) / 14.0) ** 2 < 1:
            continue                                        # the perch over it
        out.add((x, y))
    return out


def belt(x0, x1, top, d):
    """A conveyor laid on a ledge: rubber on top, frame and rollers under, drums at both
    ends, chevrons the way it drags. Stands 6px proud of the rock."""
    rect(x0, top + 3, x1, top + 5, MET_D)
    rect(x0, top + 3, x1, top + 3, MET)
    for x in range(int(x0) + 6, int(x1) - 4, 9):
        disc(x, top + 4, 1.2, MET_L)
    rect(x0, top, x1, top + 2, RUBBER)
    rect(x0, top, x1, top, MET_L)
    for x in range(int(x0) + 6, int(x1) - 4, 10):
        px(x, top + 1, GREEN_L)
        px(x - d, top, GREEN_L)
        px(x - d, top + 2, GREEN_L)
    for ex in (x0 + 3, x1 - 3):
        disc(ex, top + 3, 3.4, MET)
        ring(ex, top + 3, 3.4, MET_L)
        px(ex, top + 3, MET_D)


def grinder(cx, cy, r):
    """Two wheels meshing in the throat, turning in, and the steel lip plates either
    side that steer everything between them."""
    for side in (-1, 1):
        wx = cx + side * r
        disc(wx, cy, r, MET)
        disc(wx, cy, r - 3, MET_D)
        ring(wx, cy, r, MET_XL)
        disc(wx, cy, 3, MET_L)
        px(wx, cy, INK)
        for i in range(12):
            a = i * 2 * math.pi / 12 + (0.26 if side > 0 else 0)
            for k in range(1, 4):
                px(wx + math.cos(a) * (r + k), wy_(cy, a, r, k), MET_XL if k < 3 else MET_L)
        for k in range(3):                                  # turning in
            a = (-1.2 if side < 0 else math.pi + 1.2) + k * 0.12 * side
            px(wx + math.cos(a) * (r - 5), cy + math.sin(a) * (r - 5), F_HOT, 0.8)
    for _ in range(36):                                     # what is going through
        px(cx - 4 + rnd() * 8, cy - r - 4 + rnd() * (2 * r + 10), pick([RED, RED_L, MET_L, WOOD, DIRT_L]), 0.85)
    glow(cx, cy, 34, (190, 120, 90), 0.10)


def wy_(cy, a, r, k):
    return cy + math.sin(a) * (r + k)


def lip_plates(ox, oy):
    """Steel lining down the last of the funnel, so the slope is slick near the throat."""
    for side in (-1, 1):
        for i in range(48):
            lx = CX + side * (THROAT + i)
            y = funnel(lx)
            px(ox + lx, oy + y - 1, MET_L)
            px(ox + lx, oy + y, MET)
            if i % 8 == 0:
                px(ox + lx, oy + y - 1, MET_XL)


def well_furnish(ox, oy, m):
    teeth(m, ox + 50, ox + 350, oy + 120, 24)
    for x, y, d, rx, ry in ((200, 236, -1, 20, 10), (200, 262, 1, 18, 9), (200, 110, -1, 14, 9),
                            (200, 150, 1, 12, 7), (200, 196, -1, 10, 6)):
        x0, y0 = ox + x, oy + y
        while (x0, y0) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), y0, rx, ry, rough=0.25)
    for x, rx, ry in ((258, 14, 26), (110, 12, 16)):        # big teeth off the roof
        top = ceil_at(m, ox + x, oy + 200)
        rock_blob(ox + x, top + ry // 2, rx, ry, rough=0.3)
    for x, r in ((150, 7), (300, 6), (90, 5)):               # boulders sat on the slopes
        disc(ox + x, oy + funnel(x) - r + 1, r, ROCK_M)
        disc(ox + x - 1, oy + funnel(x) - r, r - 2, ROCK_L)
        px(ox + x + r - 2, oy + funnel(x) - 2, ROCK_D)
    lip_plates(ox, oy)
    for lx in range(36, 170, 3):                            # gravel and scrap on the slopes
        if chance(0.35):
            px(ox + lx, oy + funnel(lx) - 1, pick([ORE, DIRT_L, MET_L, ROCK_L]))
    for lx in range(230, 364, 3):
        if chance(0.35):
            px(ox + lx, oy + funnel(lx) - 1, pick([ORE, DIRT_L, MET_L, ROCK_L]))

    # the wheels and the bin under them
    grinder(ox + CX, oy + WHEEL_Y, WHEEL_R)
    bf = floor_at(m, ox + CX, oy + 396)
    scrap_pile(ox + CX - 22, bf, 44, 6, colors=(MET_D, RED, DIRT, MET, WOOD_D))
    for i in range(5):
        px(ox + CX - 2 + rnd() * 4, oy + WHEEL_Y + WHEEL_R + 4 + i * 3, pick([RED, MET_L, WOOD]))

    # west belt: drags east, tips off over the funnel
    wt = oy + WEST_LEDGE - 6
    belt(ox + 30, ox + 120, wt, 1)
    crate_g(ox + 44, wt, 10)
    keg(ox + 98, wt)
    stand("Gaper", ox + 74, wt)
    for i in range(4):
        px(ox + 126 + i * 2, wt + 8 + i * 9, pick([ORE, DIRT_L, MET_L]), 0.8)
    lamp(ox + 70, ceil_at(m, ox + 70, wt - 10) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)

    # east belt: drags west
    et = oy + EAST_LEDGE - 6
    belt(ox + 286, ox + 380, et, -1)
    rect(ox + 300, et - 4, ox + 314, et - 1, (98, 92, 80))   # a tub of ore riding it
    rect(ox + 300, et - 4, ox + 314, et - 4, ORE)
    stand("RiotBrute", ox + 344, et, flip=True)
    corpse(ox + 368, et)
    for i in range(4):
        px(ox + 280 - i * 2, et + 8 + i * 9, pick([ORE, DIRT_L, MET_L]), 0.8)

    # the perch over the east belt, and who slid in already
    stand("WizGoldhood", ox + 360, oy + PERCH, flip=True)
    lamp(ox + 372, ceil_at(m, ox + 372, oy + PERCH - 8) + 1, drop=4, bulb=LAMP, tint=LAMP, r=46, strength=0.13)
    stand("Minespider", ox + 112, oy + int(funnel(112)))
    stand("Gaper", ox + 268, oy + int(funnel(268)), flip=True)
    stand("Pyro", ox + 60, oy + int(funnel(60)))
    # over the throat: a skip of ore on one chain, and a cage off the roof
    roof = ceil_at(m, ox + CX + 20, oy + 200) + 1
    chain(ox + CX + 20, roof, oy + 214)
    rect(ox + CX + 11, oy + 214, ox + CX + 29, oy + 228, MET)
    rect(ox + CX + 11, oy + 214, ox + CX + 29, oy + 214, MET_XL)
    rect(ox + CX + 12, oy + 215, ox + CX + 28, oy + 217, ORE)
    rect(ox + CX + 11, oy + 222, ox + CX + 29, oy + 222, MET_D)
    cage(ox + 140, oy + 150, oy + 176, ceil_at(m, ox + 140, oy + 150) + 1)
    lamp(ox + CX - 30, ceil_at(m, ox + CX - 30, oy + 200) + 1, drop=20, bulb=LAMP, tint=LAMP, r=90, strength=0.12)
    cable(ox + 290, ceil_at(m, ox + 290, oy + 160) + 4, ox + CX - 30, ceil_at(m, ox + CX - 30, oy + 200) + 3, sag=10)


ROOM = {
    "name": "THE GRINDER WELL", "w": 400, "h": 440,
    "shapes": [([("blob", CX, 222, 182, 156)], 0.07),
               ([("blob", CX, 404, 36, 14)], 0.08)],           # the bin under the wheels
    "sockets": {"T1": ("T", 120, 100), "T2": ("T", 290, 96),
                "L1": ("L", WEST_LEDGE, 34), "R1": ("R", EAST_LEDGE, 28),
                "R2": ("R", PERCH, 50), "B1": ("B", CX, 30)},
    "edit": well_edit,
    "furnish": well_furnish,
}


SHEET = {
    "seed": 70808,
    "callouts": [
        ("1 BELTS DRAG TO THE LIP", (-122, 40), (40, WEST_LEDGE - 4)),
        ("2 THE FLOOR IS A FUNNEL", (-122, 460), (130, 252)),
        ("3 WHEELS MESH IN THE THROAT", (230, 460), (CX + 14, WHEEL_Y + 6)),
    ],
    "beats": [
        ("OFF A BELT, DOWN THE SLOPE, THROUGH THE WHEELS", (170, 180, 195)),
        ("STAND THEM ON A BELT, OR KNOCK THEM DOWN THE FUNNEL", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
