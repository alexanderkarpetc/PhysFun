"""Small room S02 - THE CANTED DRIFT.

One drift corner to corner on a slope, rails down it, a loaded tub at the top on a
chock. Halfway down the floor drops into the magazine and the rails cross on a
trestle; a pocket above the bottom end holds the throwers.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S02"


DRIFT_A, DRIFT_B = (20, 100), (420, 330)
SLOPE = math.atan2(DRIFT_B[1] - DRIFT_A[1], DRIFT_B[0] - DRIFT_A[0])


def drift_rail_y(x):
    """Rail line along the drift floor, local."""
    t = (x - DRIFT_A[0]) / (DRIFT_B[0] - DRIFT_A[0])
    return DRIFT_A[1] + (DRIFT_B[1] - DRIFT_A[1]) * t + 32


def drift_furnish(ox, oy, m):
    # rails, laid straight down the slope; where the floor drops away (the hole) they
    # run on over a trestle
    for x in range(16, 424):
        y = drift_rail_y(x)
        px(ox + x, oy + y, MET_XL)
        px(ox + x, oy + y + 1, MET_D)
        if x % 9 == 0:
            rect(ox + x - 2, oy + y + 2, ox + x + 2, oy + y + 3, WOOD_D)
    tx0, tx1 = 118, 160
    bot = floor_at(m, ox + 139, oy + 250)
    for lx in (tx0 + 4, tx1 - 6):
        beam(ox + lx, oy + int(drift_rail_y(lx)) + 4, bot - 1, 3, WOOD, WOOD_L)
    line(ox + tx0 + 6, oy + drift_rail_y(tx0) + 8, ox + tx1 - 6, bot - 4, WOOD_D)
    line(ox + tx1 - 6, oy + drift_rail_y(tx1) + 8, ox + tx0 + 6, bot - 4, WOOD_D)

    # the cart at the top, on a chock
    cx = 62
    ry = drift_rail_y(cx)
    s, c = math.sin(SLOPE), math.cos(SLOPE)
    draw_rotated(32, 20, tub_cart, ox + cx + s * 9, oy + ry - c * 9, SLOPE)
    wx, wy = ox + cx + 19, oy + drift_rail_y(cx + 19)
    for i in range(6):
        rect(wx + i, wy - 6 + i, wx + 5, wy - 6 + i, WOOD_L if i == 0 else WOOD)

    # lamps down the drift
    for lx in (120, 250, 360):
        lamp(ox + lx, ceil_at(m, ox + lx, oy + int(drift_rail_y(lx)) - 20) + 1, drop=6,
             bulb=LAMP, tint=LAMP, r=60, strength=0.14)

    # the barricade at the bottom, and who is behind it
    f = floor_at(m, ox + 372, oy + 330)
    for i, bx in enumerate((364, 370, 376)):
        rect(ox + bx, f - 30 + i * 2, ox + bx + 4, f - 1, WOOD)
        rect(ox + bx, f - 30 + i * 2, ox + bx + 4, f - 30 + i * 2, WOOD_L)
    rect(ox + 358, f - 20, ox + 384, f - 18, WOOD_D)
    stand("Sentinel", ox + 404, floor_at(m, ox + 404, oy + 330), flip=True)
    stand("RiotBrute", ox + 330, floor_at(m, ox + 330, oy + 300), flip=True)

    # the magazine under the trestle
    mf = floor_at(m, ox + 74, oy + 265)
    for i, kx in enumerate((52, 62, 72, 57, 67)):
        keg(ox + kx, mf - (11 if i >= 3 else 0))
    crate_g(ox + 82, floor_at(m, ox + 88, oy + 265))
    teeth(m, ox + 60, ox + 400, oy + 200, 14)
    stand("Pyro", ox + 168, floor_at(m, ox + 168, oy + 265), flip=True)
    lamp(ox + 100, ceil_at(m, ox + 100, oy + 260) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.14)

    # the upper pocket, over the bottom of the drift
    stand("Grenadier", ox + 340, floor_at(m, ox + 340, oy + 100), flip=True)
    stand("WizHollowhood", ox + 296, floor_at(m, ox + 296, oy + 100), flip=True)
    lamp(ox + 320, ceil_at(m, ox + 320, oy + 100) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.14)


ROOM = {
    "name": "THE CANTED DRIFT", "w": 440, "h": 380,
    "shapes": [([("tube", [DRIFT_A, DRIFT_B], 34)], 0.03),
               ([("blob", 320, 106, 74, 40),                 # upper pocket
                 ("blob", 116, 270, 78, 42)], 0.12),          # the magazine
               ([("tube", [(300, 138), (268, 228)], 12),     # crawl up to the pocket
                 ("tube", [(139, 190), (139, 238)], 13)], 0.08)],   # the hole under the rail
    "sockets": {"T1": ("T", 330, 74), "R2": ("R", 140, 64),
                "L1": ("L", 134, 26), "R1": ("R", 364, 26),
                "L2": ("L", 304, 52), "B1": ("B", 116, 70)},
    "furnish": drift_furnish,
}


SHEET = {
    "seed": 70202,
    "callouts": [
        ("1 TUB ON A CHOCK", (-100, -50), (62, 112)),
        ("2 TRESTLE OVER THE KEGS", (-120, 420), (139, 215)),
        ("3 BARRICADE AT THE BOTTOM", (240, 420), (372, 330)),
    ],
    "beats": [
        ("KICK THE CHOCK: THE TUB RUNS THE WHOLE SLOPE", (170, 180, 195)),
        ("OR BURN THE TRESTLE AND DROP IT IN THE MAGAZINE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
