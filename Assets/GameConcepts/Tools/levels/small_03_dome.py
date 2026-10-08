"""Small room S03 - THE COIL DOME.

A round room with a Tesla coil on a rock plinth in the middle. Everything metal in it
is a target: two steel grates hung on chains at mid height, a cage off the roof, the
steel plate on the west half of the floor. The east half is duckboards.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S03"


DOME = (210, 230, 185, 150)
DOME_FLOOR = 366
PLINTH_TOP = 306


def dome_roof(m, ox, oy):
    return lambda x: ceil_at(m, x, oy + 200) + 1


def dome_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= DOME_FLOOR and 20 < lx < 400:
            continue
        if ly >= PLINTH_TOP and abs(lx - 210) <= 22 + (ly - PLINTH_TOP) * 0.35:
            continue
        out.add((x, y))
    return out


def dome_furnish(ox, oy, m):
    roof = dome_roof(m, ox, oy)
    teeth(m, ox + 60, ox + 360, oy + 200, 22)
    # outcrops under the grates, so the walls are not one smooth curve
    for bx, by in ((44, 292), (378, 292), (70, 132), (352, 140)):
        rock_blob(ox + bx, oy + by, 22, 12, rough=0.25)
    tesla(ox + 210, oy + PLINTH_TOP)
    # the dynamo that feeds it, and the cable along the floor
    fy0 = oy + DOME_FLOOR
    rect(ox + 252, fy0 - 18, ox + 276, fy0 - 3, (70, 74, 66))
    rect(ox + 252, fy0 - 18, ox + 276, fy0 - 18, MET_L)
    disc(ox + 264, fy0 - 11, 5, COPPER)
    disc(ox + 264, fy0 - 11, 2, MET_D)
    rect(ox + 230, fy0 - 3, ox + 252, fy0 - 3, INK)
    hung_grate(ox + 24, ox + 150, oy + 225, (ox + 70, ox + 140), roof)
    hung_grate(ox + 270, ox + 396, oy + 225, (ox + 280, ox + 350), roof)
    cage(ox + 300, oy + 128, oy + 158, roof(ox + 300))

    # floor: steel plate on the west half (conducts), duckboards on the east
    fy = oy + DOME_FLOOR
    rect(ox + 50, fy - 2, ox + 180, fy - 1, MET)
    rect(ox + 50, fy - 2, ox + 180, fy - 2, MET_L)
    for x in range(ox + 244, ox + 372, 7):
        rect(x, fy - 2, x + 5, fy - 1, WOOD)
        rect(x, fy - 2, x + 5, fy - 2, WOOD_L)

    arc(ox + 196, oy + PLINTH_TOP - 58, ox + 132, oy + 224, jag=6)
    arc(ox + 226, oy + PLINTH_TOP - 60, ox + 296, oy + 158, jag=5)
    arc(ox + 204, oy + PLINTH_TOP - 52, ox + 160, fy - 3, jag=7, fork=0.35)

    stand("Sentinel", ox + 92, oy + 225)
    stand("WizCrimson", ox + 330, oy + 225, flip=True)
    stand("Minespider", ox + 116, fy - 2)
    stand("Gaper", ox + 300, fy - 2, flip=True)


ROOM = {
    "name": "THE COIL DOME", "w": 420, "h": 420,
    "shapes": [([("blob",) + DOME], 0.06)],
    "sockets": {"T1": ("T", 130, 120), "T2": ("T", 300, 120),
                "L1": ("L", 225, 36), "R1": ("R", 225, 36),
                "L2": ("L", DOME_FLOOR, 110), "R2": ("R", DOME_FLOOR, 110)},
    "edit": dome_edit,
    "furnish": dome_furnish,
}


SHEET = {
    "seed": 70303,
    "callouts": [
        ("1 COIL ARCS TO THE NEAREST METAL", (180, -50), (210, 250)),
        ("2 GRATES ON CHAINS", (-120, 150), (60, 226)),
        ("3 STEEL WEST, TIMBER EAST", (60, 440), (120, 364)),
    ],
    "beats": [
        ("STAND ON WOOD, PULL THEM ONTO METAL", (170, 180, 195)),
        ("SENTINEL AND CRIMSON MAGE ON THE GRATES", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
