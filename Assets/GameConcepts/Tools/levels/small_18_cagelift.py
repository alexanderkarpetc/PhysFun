"""Small room S18 - THE CAGE LIFT.

A shaft top to bottom, a winch chamber at its head and drifts off it on alternating
sides - east high, west in the middle, east low - with a sump at the foot. The cage
hangs in the shaft on one rope off a drum; the drum is held by a band brake on a
weighted lever. Knock the lever and the drum runs free: the cage, and whoever is in it,
goes to the bottom, onto whoever is in the sump.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S18"

SHAFT_X, SHAFT_R = 160, 21
CHAMBER_FLOOR = 108
CAGE_TOP, CAGE_BOT = 196, 226
DRUM = (84, 88, 13)          # winch drum centre and radius, local
SHEAVE = (152, 46, 8)        # head sheave over the shaft


def lift_edit(air, ox, oy):
    """A flat floor across the winch chamber, the shaft mouth left open."""
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if CHAMBER_FLOOR <= ly <= 132 and abs(lx - SHAFT_X) > SHAFT_R:
            continue
        out.add((x, y))
    return out


def cage_car(cx, top, bot):
    """The cage: an iron floor and roof, round bars, a bow and hook on top."""
    x0, x1 = cx - 14, cx + 14
    rect(x0, bot - 2, x1, bot, MET_D)
    rect(x0, bot - 2, x1, bot - 2, MET_L)
    rect(x0, top, x1, top + 2, MET_D)
    rect(x0, top, x1, top, MET_L)
    for x in range(x0, x1 + 1, 4):
        rect(x, top + 3, x, bot - 3, MET)
    rect(x0, top + 3, x0, bot - 3, MET_L)
    rect(x1, top + 3, x1, bot - 3, MET_D)
    line(x0 + 2, top, cx, top - 7, MET_D)
    line(x1 - 2, top, cx, top - 7, MET_D)
    disc(cx, top - 8, 1.6, MET_L)


def bars_over(cx, top, bot):
    """Redraw the cage bars over whoever stands in it."""
    for x in range(cx - 10, cx + 11, 4):
        rect(x, top + 3, x, bot - 3, MET, 0.85)


def drum(cx, cy, r):
    disc(cx, cy, r + 2, MET_D)
    disc(cx, cy, r, (92, 70, 46))
    for k in range(-r + 1, r, 2):                         # the rope wound on it
        rect(cx - r + 2, cy + k, cx + r - 2, cy + k, (176, 150, 104), 0.55)
    ring(cx, cy, r, MET_L)
    disc(cx, cy, 2.5, MET_D)
    disc(cx, cy, 1, MET_XL)


def lift_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly: floor_at(m, X(lx), Y(ly))

    # rock: teeth on every roof, shelves on the chamber walls
    teeth(m, X(50), X(270), Y(70), 18)
    teeth(m, X(190), X(300), Y(150), 7)
    teeth(m, X(20), X(130), Y(275), 7)
    teeth(m, X(190), X(300), Y(382), 6)

    # headframe over the shaft mouth: two raked legs, a cap, the sheave
    sx, sy, sr = SHEAVE
    cf = Y(CHAMBER_FLOOR)
    line(X(SHAFT_X - 32), cf - 1, X(sx - 3), Y(sy + 2), WOOD)
    line(X(SHAFT_X - 31), cf - 1, X(sx - 2), Y(sy + 2), WOOD_D)
    line(X(SHAFT_X + 32), cf - 1, X(sx + 3), Y(sy + 2), WOOD)
    line(X(SHAFT_X + 31), cf - 1, X(sx + 2), Y(sy + 2), WOOD_D)
    rect(X(SHAFT_X - 26), Y(sy + 4), X(SHAFT_X + 26), Y(sy + 6), WOOD)
    rect(X(SHAFT_X - 26), Y(sy + 4), X(SHAFT_X + 26), Y(sy + 4), WOOD_L)
    for lx in (SHAFT_X - 34, SHAFT_X + 28):              # collar timbers across the mouth
        rect(X(lx), cf - 3, X(lx + 6), cf - 1, WOOD_D)
    # drum and brake
    dx, dy, dr = DRUM
    rect(X(dx - 10), cf - 4, X(dx + 10), cf - 1, MET_D)  # bedplate
    line(X(dx - 8), cf - 4, X(dx - 3), Y(dy + 4), MET_D)
    line(X(dx + 8), cf - 4, X(dx + 3), Y(dy + 4), MET_D)
    # rope: drum top -> over the sheave -> down the shaft to the cage
    line(X(dx), Y(dy - dr), X(sx), Y(sy - sr), (176, 150, 104))
    line(X(sx + sr), Y(sy), X(sx + sr), Y(CAGE_TOP - 9), (176, 150, 104))
    line(X(sx + sr + 1), Y(sy), X(sx + sr + 1), Y(CAGE_TOP - 9), (120, 100, 70))
    drum(X(dx), Y(dy), dr)
    gear(X(sx), Y(sy), sr, teeth=0)
    # band brake: a strap round the drum to a lever, a weight at the lever's end
    ring(X(dx), Y(dy), dr + 3, (60, 54, 46))
    lx0, ly0 = dx - 16, dy + 12
    line(X(lx0), Y(ly0), X(dx - 46), Y(dy - 22), WOOD)
    line(X(lx0 + 1), Y(ly0), X(dx - 45), Y(dy - 22), WOOD_D)
    line(X(lx0), Y(ly0 - 1), X(dx - 46), Y(dy - 23), WOOD_L)
    hazard_slab(X(dx - 53), Y(dy - 31), 12, 10)
    rect(X(dx - 53), Y(dy - 31), X(dx - 41), Y(dy - 31), MET_L)
    line(X(lx0), Y(ly0), X(dx - dr - 2), Y(dy + 4), (60, 54, 46))
    disc(X(lx0), Y(ly0), 2, MET_L)                       # the pin
    hazard_slab(X(lx0 - 2), Y(ly0 + 4), 4, 3)
    stand("WizDeepminer", X(dx + 34), cf, flip=True)
    lamp(X(220), ceil_at(m, X(220), Y(80)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=70, strength=0.16)
    crate_g(X(250), cf, 12)
    keg(X(236), cf)
    stand("WizGoldhood", X(266), cf - 12)

    # the shaft: guide timbers down both walls, sills at every landing
    for gx in (SHAFT_X - SHAFT_R + 2, SHAFT_X + SHAFT_R - 4):
        for ly in range(CHAMBER_FLOOR + 6, 420, 26):
            if (X(gx), Y(ly)) in m and (X(gx), Y(ly + 14)) in m:
                rect(X(gx), Y(ly), X(gx + 1), Y(ly + 14), WOOD_D)

    # the cage, held at the first landing, with a brute in it
    cage_car(X(SHAFT_X), Y(CAGE_TOP), Y(CAGE_BOT))
    stand("RiotBrute", X(SHAFT_X), Y(CAGE_BOT - 2))
    bars_over(X(SHAFT_X), Y(CAGE_TOP), Y(CAGE_BOT))

    # drift A, east and high
    fa = fl(250, 150)
    stand("Grenadier", X(236), fa, flip=True)
    stand("Pyro", X(276), fl(276, 150), flip=True)
    stull(X(298), ceil_at(m, X(299), Y(150)) + 1, fl(299, 150) - 1)
    lamp(X(256), ceil_at(m, X(256), Y(150)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)
    rect(X(SHAFT_X + 18), fl(SHAFT_X + 24, 160) - 2, X(SHAFT_X + 34), fl(SHAFT_X + 24, 160) - 1, WOOD)

    # drift B, west and in the middle
    stand("WizBogcap", X(92), fl(92, 270))
    stand("Gaper", X(60), fl(60, 270))
    stull(X(118), ceil_at(m, X(119), Y(272)) + 1, fl(119, 272) - 1)
    scrap_pile(X(28), fl(36, 270), 18, 5, colors=(MET_D, DIRT, ROCK_M, WOOD_D))
    lamp(X(76), ceil_at(m, X(76), Y(270)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)
    rect(X(SHAFT_X - 34), fl(SHAFT_X - 26, 270) - 2, X(SHAFT_X - 18), fl(SHAFT_X - 26, 270) - 1, WOOD)

    # drift C, east and low
    stand("Sentinel", X(244), fl(244, 380), flip=True)
    crate_g(X(270), fl(276, 380), 11)
    lamp(X(230), ceil_at(m, X(230), Y(380)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)

    # the sump: the last cage that came down, and who is waiting under this one
    sf = fl(SHAFT_X, 425)
    for i, (a, b) in enumerate(((SHAFT_X - 26, SHAFT_X - 6), (SHAFT_X + 8, SHAFT_X + 24))):
        line(X(a), sf - 2 - i * 3, X(b), sf - 6 + i * 2, MET)
    for x in range(SHAFT_X - 22, SHAFT_X - 8, 4):
        line(X(x), sf - 2, X(x + 3), sf - 10, MET_D)
    corpse(X(SHAFT_X + 18), sf)
    stand("Minespider", X(SHAFT_X - 8), sf)

    # drop line, ghosted
    for ly in range(CAGE_BOT + 6, 410, 6):
        rect(X(SHAFT_X - 12), Y(ly), X(SHAFT_X - 12), Y(ly + 2), (200, 205, 190), 0.45)
        rect(X(SHAFT_X + 12), Y(ly), X(SHAFT_X + 12), Y(ly + 2), (200, 205, 190), 0.45)


ROOM = {
    "name": "THE CAGE LIFT", "w": 320, "h": 460,
    "shapes": [([("blob", 160, 70, 122, 46)], 0.10),                    # winch chamber
               ([("tube", [(SHAFT_X, 96), (SHAFT_X, 424)], SHAFT_R)], 0.02),   # shaft
               ([("tube", [(170, 168), (306, 150)], 17),               # drift A, east high
                 ("tube", [(150, 272), (12, 290)], 17),                # drift B, west mid
                 ("tube", [(170, 392), (306, 380)], 16)], 0.08),       # drift C, east low
               ([("blob", 246, 154, 46, 22),
                 ("blob", 78, 278, 52, 24),
                 ("blob", 236, 386, 44, 20),
                 ("blob", SHAFT_X, 428, 36, 18)], 0.12)],              # sump
    "sockets": {"T1": ("T", 96, 44), "T2": ("T", 226, 44),
                "L2": ("L", CHAMBER_FLOOR, 46),
                "R1": ("R", 167, 16), "L1": ("L", 306, 16), "R2": ("R", 396, 16)},
    "edit": lift_edit,
    "furnish": lift_furnish,
}


SHEET = {
    "seed": 71801,
    "callouts": [
        ("1 BAND BRAKE ON THE DRUM", (-150, 24), (68, 100)),
        ("2 CAGE ON ONE ROPE", (-120, 200), (146, 210)),
        ("3 SUMP AT THE FOOT", (200, 470), (160, 440)),
    ],
    "beats": [
        ("KNOCK THE LEVER: THE CAGE AND ITS BRUTE GO TO THE BOTTOM", (170, 180, 195)),
        ("WHOEVER WAITS IN THE SUMP IS UNDER IT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
