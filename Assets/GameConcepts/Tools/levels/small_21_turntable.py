"""Small room S21 - THE TURNTABLE.

A round room with an iron turntable on a stone pier in the middle of it, and four rail
spurs running off it in an X: two climbing to shelves high on the walls, where loaded
ore tubs are parked on chocks, and two running down to shelves low on the walls, where
the spurs end at buffer stops - and where the crew stand. The table carries one length
of track, so it joins one high spur to one low one at a time. Turn it, knock a chock,
and a tub runs the whole diagonal through the table into whoever is at the buffers.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S21"

HUB = (210, 172)                 # the table's kingpin
TR = 44                          # table radius
SLOPE = 0.36                     # every spur runs at this angle
TAN = math.tan(SLOPE)
FLOOR = 330
HI_SHELF, HI_END = 128, 90       # high shelves: floor line, where the spur meets them (dist from wall side)
LO_SHELF = 224


def spur_y(lx, up):
    """Rail line of a spur at local x. up=True: the climbing pair, else the falling pair."""
    d = abs(lx - HUB[0])
    return HUB[1] - d * TAN if up else HUB[1] + d * TAN


def table_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR + 3 * math.sin(lx * 0.08):
            continue
        for side in (-1, 1):
            far = (lx - HUB[0]) * side                 # distance out from the hub, this side
            # high shelf: flat top at HI_SHELF, wall-side of where the climbing spur lands
            hi_x = HUB[0] + side * ((HUB[1] - HI_SHELF) / TAN)
            if (lx - hi_x) * side >= 0 and HI_SHELF <= ly <= HI_SHELF + 18 + ((lx - hi_x) * side) * 0.9:
                break
            # low shelf: flat top at LO_SHELF out to the wall, falling away under it
            lo_x = HUB[0] + side * ((LO_SHELF - HUB[1]) / TAN)
            if (lx - lo_x) * side >= 0 and ly >= LO_SHELF:
                break
            if far > 0 and ly >= LO_SHELF + 26 and (lx - (lo_x - side * (ly - LO_SHELF - 26) * 0.7)) * side >= 0:
                break
        else:
            out.add((x, y))
    return out


def turntable_local():
    """The table drawn level on a 100x100 canvas: a spoked iron wheel round the kingpin,
    a timber deck across its diameter with the rails on top, a latch at each end."""
    c = 50
    disc(c, c, TR, MET_D)
    disc(c, c, TR - 3, (40, 42, 46))
    ring(c, c, TR, MET_L)
    ring(c, c, TR - 3, MET)
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        line(c + math.cos(a) * 6, c + math.sin(a) * 6, c + math.cos(a) * (TR - 3), c + math.sin(a) * (TR - 3), MET)
    for k in range(16):                                      # rim rollers
        a = k * math.pi / 8
        disc(c + math.cos(a) * (TR - 1.5), c + math.sin(a) * (TR - 1.5), 1.0, MET_XL)
    rect(c - TR, c + 1, c + TR, c + 4, WOOD)                 # the deck
    rect(c - TR, c + 4, c + TR, c + 4, WOOD_D)
    for x in range(c - TR + 3, c + TR - 2, 7):
        rect(x, c + 1, x + 2, c + 3, WOOD_D)
    rect(c - TR, c, c + TR, c, MET_XL)                       # the rail
    rect(c - TR, c - 1, c + TR, c - 1, MET_L)
    for e in (c - TR, c + TR - 3):                           # latches
        rect(e, c - 3, e + 3, c + 5, RED)
        rect(e, c - 3, e + 3, c - 3, RED_L)
    disc(c, c + 10, 6, MET)
    ring(c, c + 10, 6, MET_L)
    disc(c, c + 10, 2, INK)


def track(x0, y0, x1, y1, posts_to=None):
    """A spur seen side-on: a timber bed three thick, rail on top, ties showing under."""
    for t in range(1, 5):
        line(x0, y0 + t, x1, y1 + t, WOOD if t < 4 else WOOD_D)
    line(x0, y0, x1, y1, MET_XL)
    line(x0, y0 - 1, x1, y1 - 1, MET_L)
    n = int(abs(x1 - x0) / 7)
    for i in range(n + 1):
        t = i / max(n, 1)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        rect(x, y + 2, x + 1, y + 3, WOOD_D)


def tub_on(x, y, ang, chock=None):
    """An ore tub standing on a rail point (x, y) on a slope of `ang`; chock = -1/+1 puts a
    wedge on that side of its downhill wheel."""
    nx, ny = math.sin(ang), -math.cos(ang)
    draw_rotated(32, 20, tub_cart, x + nx * 10, y + ny * 10, ang)
    if chock:
        cx, cy = x + math.cos(ang) * 13 * chock, y + math.sin(ang) * 13 * chock
        for i in range(4):
            rect(cx - (3 - i), cy - 1 - i, cx + (3 - i), cy - 1 - i, WOOD_L if i == 3 else WOOD)


def buffer_at(x, floor, face):
    """Buffer stop: two timber legs and a cross head with a red band, facing the spur."""
    rect(x - 2, floor - 12, x + 2, floor - 1, WOOD_D)
    line(x - 1, floor - 1, x - 1 - face * 8, floor - 10, WOOD)
    rect(x - 2 + face * 2, floor - 14, x + 2 + face * 2, floor - 7, WOOD)
    rect(x - 2 + face * 2, floor - 12, x + 2 + face * 2, floor - 10, RED_L)


def table_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    hx, hy = X(HUB[0]), Y(HUB[1])

    teeth(m, X(60), X(360), Y(120), 22)
    # rock back into the room: bulges off both walls between the shelves, a mound on the floor
    for x, y, d, rx, ry in ((40, 182, -1, 16, 11), (380, 178, 1, 15, 10), (150, 334, 0, 22, 9),
                            (300, 336, 0, 18, 8)):
        x0 = ox + x
        if d:
            while (x0, oy + y) in m:
                x0 += d
            x0 -= d * (rx // 3)
        rock_blob(x0, oy + y, rx, ry, rough=0.25)

    # the pier under the table, and the crank that turns it
    fy = Y(FLOOR)
    pt = hy + TR - 2
    rect(hx - 11, pt, hx + 11, fy - 1, STONE)
    rect(hx - 11, pt, hx - 11, fy - 1, STONE_L)
    rect(hx + 11, pt, hx + 11, fy - 1, STONE_D)
    for y in range(pt + 6, fy, 9):
        rect(hx - 11, y, hx + 11, y, STONE_D)
        px(hx - 3 + (y % 2) * 6, y + 4, STONE_D)
    rect(hx - 17, pt - 2, hx + 17, pt + 3, STONE_D)
    rect(hx - 17, pt - 2, hx + 17, pt - 2, STONE_L)
    rect(hx - 16, fy - 4, hx + 16, fy - 1, STONE_D)
    gear(hx + 22, pt + 14, 7, teeth=9)                       # pinion on the rim
    line(hx + 22, pt + 14, hx + 34, pt + 34, MET_L)          # the crank handle
    rect(hx + 32, pt + 34, hx + 36, pt + 36, WOOD)
    rect(hx + 12, pt + 12, hx + 22, pt + 15, MET_D)

    # the four spurs, each from the table's rim to its shelf
    for side in (-1, 1):
        hi_x = HUB[0] + side * ((HUB[1] - HI_SHELF) / TAN)
        lo_x = HUB[0] + side * ((LO_SHELF - HUB[1]) / TAN)
        r0 = HUB[0] + side * (TR + 2)
        track(X(r0), Y(spur_y(r0, True)), X(hi_x), Y(HI_SHELF))
        track(X(r0), Y(spur_y(r0, False)), X(lo_x), Y(LO_SHELF))
        wall_hi = X(hi_x)
        while (wall_hi, Y(HI_SHELF) - 2) in m:
            wall_hi += side
        wall_lo = X(lo_x)
        while (wall_lo, Y(LO_SHELF) - 2) in m:
            wall_lo += side
        track(X(hi_x), Y(HI_SHELF), wall_hi - side * 2, Y(HI_SHELF))
        track(X(lo_x), Y(LO_SHELF), wall_lo - side * 14, Y(LO_SHELF))
        buffer_at(wall_lo - side * 10, Y(LO_SHELF), -side)
        # the falling spurs stand on trestle legs to the floor; the climbing ones hang from the roof
        for k in (0.35, 0.75):
            lx = r0 + (lo_x - r0) * k
            ty = Y(spur_y(lx, False)) + 4
            f = floor_at(m, X(lx), ty + 2)
            beam(X(lx) - 1, ty, f - 1, 2, WOOD_D, WOOD)
            line(X(lx), f - 1, X(lx) + side * 10, ty + 10, WOOD_D)
            lx2 = r0 + (hi_x - r0) * k
            ty2 = Y(spur_y(lx2, True)) + 4
            line(X(lx2), ceil_at(m, X(lx2), ty2 - 6) + 1, X(lx2), ty2, MET_D)

    # the table itself, turned to join the north-west spur to the south-east one
    draw_rotated(100, 100, turntable_local, hx, hy, SLOPE)
    glow(hx, hy, 60, (200, 190, 160), 0.06)

    # what is on the rails: tubs chocked high up, one on the table, the crew low down
    a = SLOPE
    for side, d in ((-1, 70), (1, 64)):
        lx = HUB[0] + side * d
        tub_on(X(lx), Y(spur_y(lx, True)), -a * side, chock=-side)
    tub_on(X(HUB[0] - 14), hy - 14 * TAN + 0.5, a)
    for side in (-1, 1):
        hi_x = HUB[0] + side * ((HUB[1] - HI_SHELF) / TAN)
        tub_on(X(hi_x + side * 22), Y(HI_SHELF), 0)
    lo = Y(LO_SHELF)
    stand("RiotBrute", X(366), lo, flip=True)
    stand("Gaper", X(348), lo, flip=True)
    stand("WizCrimson", X(52), lo)
    stand("Minespider", X(66), lo)
    stand("Grenadier", X(384), Y(HI_SHELF), flip=True)
    stand("WizDeepminer", X(36), Y(HI_SHELF))

    # the floor under it all: the last tub that went off the end, and its load
    draw_rotated(32, 20, tub_cart, X(118), fy - 9, math.pi + 0.15)
    for _ in range(40):
        x = 92 + rnd() * 60
        disc(X(x), fy - 1 - rnd() * 3, 1 + rnd() * 1.5, pick([ORE, DIRT_L, ROCK_L, DIRT]))
    corpse(X(150), fy)
    scrap_pile(X(318), fy, 22, 5, colors=(MET_D, MET, DIRT, ORE, WOOD_D))
    rect(X(322), fy - 9, X(330), fy - 8, MET_L)       # a bent axle off the last wreck
    disc(X(334), fy - 4, 3.2, INK)
    disc(X(334), fy - 4, 1.4, MET_L)
    stand("Ghast", X(176), fy)
    stand("BloodMage", X(262), fy, flip=True)
    crate_g(X(282), fy)
    crate_g(X(296), fy, 10)
    keg(X(306), fy)
    for k in range(4):                                       # spare rail lengths stacked by the pier
        rect(X(236), fy - 2 - k * 2, X(256), fy - 2 - k * 2, MET_L if k % 2 else MET)

    # a hoist over the table for lifting tubs back on
    top = ceil_at(m, hx - 4, Y(60)) + 1
    chain(hx - 4, top, hy - 62)
    rect(hx - 8, hy - 62, hx, hy - 59, MET_D)
    line(hx - 4, hy - 59, hx - 4, hy - 53, MET_L)
    line(hx - 4, hy - 53, hx, hy - 51, MET_L)
    lamp(X(166), ceil_at(m, X(166), Y(90)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=80, strength=0.15)
    lamp(X(256), ceil_at(m, X(256), Y(90)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=80, strength=0.15)


ROOM = {
    "name": "THE TURNTABLE", "w": 420, "h": 380,
    "shapes": [([("blob", 210, 190, 176, 160)], 0.07)],
    "sockets": {"T1": ("T", 136, 64), "T2": ("T", 288, 64),
                "L1": ("L", HI_SHELF, 58), "R1": ("R", HI_SHELF, 58),
                "L2": ("L", LO_SHELF, 46), "R2": ("R", LO_SHELF, 46)},
    "edit": table_edit,
    "furnish": table_furnish,
}


SHEET = {
    "seed": 72101,
    "callouts": [
        ("1 THE TABLE PICKS THE LINE", (-128, 26), (180, 150)),
        ("2 LOADED TUBS ON CHOCKS", (-128, 156), (146, 142)),
        ("3 THE CREW AT THE BUFFERS", (200, 396), (352, 216)),
    ],
    "beats": [
        ("TURN THE TABLE, KNOCK A CHOCK: THE TUB RUNS THE DIAGONAL", (170, 180, 195)),
        ("WHOEVER STANDS AT THE BUFFER AT THE FOOT OF IT TAKES IT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
