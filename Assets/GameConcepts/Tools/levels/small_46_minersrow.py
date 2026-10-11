"""Small room S46 - MINERS' ROW.

A cave that steps down to the east in three shelves, a one-storey hut on each: plank
walls, a lean-to roof, a flap door on the uphill side and a window on the downhill one.
Nobody in one hut can see into the next. Coming down the row you take them one at a
time - open a door, clear a hut, take the steps down to the next door.

The middle one is the powder shed, and the pyro is outside it, at the door.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from housekit import *  # noqa: F403,E402

CODE = "S46"

SHELVES = ((0, 168, 196), (168, 312, 248), (312, 460, 300))   # x0, x1, floor
HUTS = ((44, 124, 46), (216, 288, 42), (360, 446, 48))        # x0, x1, wall height
WALL = 6
STEPS, STEP_RUN = 7, 5          # timber steps down each drop: count, and how far each one runs


def step_at(x, y0, y1, k):
    """Top-left of the k-th step down a drop whose lip is at x, from floor y0 to floor y1."""
    return x - 6 + k * STEP_RUN, y0 + 2 + k * (y1 - y0) // STEPS


def row_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        for x0, x1, fl in SHELVES:
            if x0 <= lx < x1 and ly > fl:
                break
        else:
            out.add((x, y))
    return out


def hut(X, Y, i, door_w=True):
    (hx0, hx1, h), fl = HUTS[i], Y(SHELVES[i][2])
    x0, x1 = X(hx0), X(hx1)
    top = fl - h
    interior(x0, top, x1, fl)
    shed_roof(x0, x1, top - 8, top - 1, 4)
    plank_wall(x0, top - 4, x0 + WALL, fl - 32)                   # up to the high end of the roof
    flap_door(x0, fl - 30, 30, WALL)
    plank_wall(x1 - WALL, top + 3, x1, fl)
    window(x1 - WALL, fl - 30, x1, fl - 20, shutter=(i == 1))
    rect(x0, top + 3, x1, top + 4, WOOD_D)
    return x0, x1, top, fl + 1


def row_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    teeth(m, X(20), X(160), Y(110), 8)
    teeth(m, X(170), X(310), Y(160), 8)
    teeth(m, X(320), X(450), Y(210), 8)

    # timber steps down each drop, with a post and a lamp at the head
    for i in range(2):
        x = X(SHELVES[i][1]) - 2
        y0, y1 = Y(SHELVES[i][2]), Y(SHELVES[i + 1][2])
        for k in range(STEPS):
            sx, sy = step_at(x, y0, y1, k)
            rect(sx, sy, sx + STEP_RUN, sy + 1, WOOD)
            rect(sx, sy, sx + STEP_RUN, sy, WOOD_L)
            post(sx + STEP_RUN - 2, sy + 2, y1, 1)
        post(x - 14, y0 - 34, y0 - 1, 2)
        warm_lamp(x - 12, y0 - 34, drop=4, r=54)

    # hut 1: two playing cards
    x0, x1, top, fl = hut(X, Y, 0)
    table(x0 + 26, fl, 16)
    stool(x0 + 14, fl)
    stand("Gaper", x0 + 20, fl)
    stand("WizBogcap", x0 + 54, fl, flip=True)
    warm_lamp((x0 + x1) // 2, top + 5, drop=3, r=36, strength=0.2)
    # hut 2: the powder shed, and the pyro at its door
    x0, x1, top, fl = hut(X, Y, 1)
    for k, x in enumerate((x0 + 16, x0 + 27, x0 + 38, x0 + 49)):
        keg(x, fl)
    keg(x0 + 21, fl - 11)
    keg(x0 + 32, fl - 11)
    keg(x0 + 43, fl - 11)
    stand("Grenadier", x1 - 14, fl, flip=True)
    stand("Pyro", x0 - 14, fl)
    # hut 3: two rooms, a brute in the first, the boss and a reaper in the back
    x0, x1, top, fl = hut(X, Y, 2)
    mid = x0 + 42
    plank_wall(mid, top - 2, mid + 4, fl - 33)
    flap_door(mid, fl - 31, 30, 4)
    bunk(x0 + 10, fl - 1, tiers=1, w=18)
    stand("RiotBrute", x0 + 26, fl)
    stand("WizRamskull", mid + 14, fl, flip=True)
    stand("Reaper", mid + 30, fl, flip=True)
    shelf(mid + 8, fl - 30, 20)
    warm_lamp(x0 + 26, top + 5, drop=3, r=34, strength=0.2)
    warm_lamp(mid + 26, top + 5, drop=3, r=34, strength=0.2)

    # the yard bits: a crate stack by hut 1, a cart by hut 3, a spider on the top shelf
    crate_g(X(140), Y(196) + 1, 11)
    crate_g(X(144), Y(196) - 10, 9)
    crate_g(X(298), Y(248) + 1, 10)
    stand("Minespider", X(20), Y(196) + 1)


ROOM = {
    "name": "MINERS ROW", "w": 460, "h": 340,
    "shapes": [([("blob", 90, 140, 100, 64), ("blob", 236, 188, 100, 68),
                 ("blob", 374, 238, 96, 70)], 0.07)],
    "sockets": {"L1": ("L", SHELVES[0][2], 22), "R1": ("R", SHELVES[2][2], 22),
                "T1": ("T", 90, 80), "T2": ("T", 250, 126)},
    "edit": row_edit,
    "furnish": row_furnish,
}


SHEET = {
    "seed": 74601,
    "callouts": [
        ("1 ONE HUT, ONE DOOR, ONE FIGHT", (-125, -50), (48, 182)),
        ("2 THE POWDER SHED", (250, -50), (250, 222)),
        ("3 STEPS DOWN THE ROW", (-125, 364), (180, 228)),
        ("4 PLANK WALLS: SHOOT THROUGH, SET ALIGHT", (150, 364), (363, 276)),
    ],
    "beats": [
        ("THREE HUTS DOWN A STEPPED CAVE: OPEN A DOOR, CLEAR A HUT, STEP DOWN", (170, 180, 195)),
        ("NOBODY IN ONE HUT CAN SEE INTO THE NEXT", (170, 180, 195)),
        ("THE MIDDLE ONE IS THE POWDER SHED, AND THE PYRO IS AT ITS DOOR", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
