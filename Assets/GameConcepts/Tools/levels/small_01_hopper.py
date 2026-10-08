"""Small room S01 - THE HOPPER.

A bowl with a heap of ore in it, standing on a timber gate across the throat; under the
gate, the pit, where the enemies are. Burn or shoot the gate and the heap comes down on
them. The pit's roof is the bowl's floor, on two stulls.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S01"


def hopper_furnish(ox, oy, m):
    # the heap: a lens of ore filling the bottom of the bowl, standing on the gate
    heap = set()
    for x in range(ox + 100, ox + 282):
        top = oy + 166 + ((x - ox - 190) / 88.0) ** 2 * 36
        y = int(top)
        while (x, y) in m and y < oy + 213:
            heap.add((x, y))
            y += 1
    for (x, y) in heap:
        r = rnd()
        px(x, y, ORE if r < 0.12 else DIRT if r < 0.45 else DIRT_D if r < 0.65 else ROCK_M if r < 0.85 else ROCK_L)
    for _ in range(26):
        x = ox + 115 + rnd() * 150
        y = oy + 176 + rnd() * 30
        if (int(x), int(y)) in heap:
            disc(x, y, 2 + rnd() * 3, pick([ROCK_L, ROCK_M, ORE, DIRT_L]))
    for (x, y) in heap:
        if (x, y - 1) not in heap:
            px(x, y, DIRT_L)

    # the gate across the throat, wedged into both walls
    for t in range(4):
        rect(ox + 166, oy + 213 + t, ox + 214, oy + 213 + t, WOOD if t < 3 else WOOD_D)
    rect(ox + 166, oy + 213, ox + 214, oy + 213, WOOD_L)
    for wx in (ox + 163, ox + 212):
        rect(wx, oy + 217, wx + 5, oy + 220, WOOD_D)
    beam(ox + 188, oy + 217, oy + 236, 3)
    rect(ox + 182, oy + 236, ox + 197, oy + 238, WOOD_D)

    # the bowl: a plank walk slung across under the roof, between the two top sockets
    teeth(m, ox + 60, ox + 320, oy + 120, 16)
    wy = oy + 96
    roof = lambda x: ceil_at(m, x, wy - 4) + 1
    for x in range(ox + 92, ox + 292):
        px(x, wy, WOOD_L if x % 9 == 0 else WOOD)
        px(x, wy + 1, WOOD)
        px(x, wy + 2, WOOD_D)
    for hx in (ox + 100, ox + 160, ox + 222, ox + 284):
        line(hx, roof(hx), hx, wy, MET_D)
    lamp(ox + 190, ceil_at(m, ox + 190, oy + 120) + 1, drop=14, bulb=LAMP, tint=LAMP, r=110, strength=0.17)
    stand("WizHollowhood", ox + 140, wy)
    stand("Pyro", ox + 66, floor_at(m, ox + 66, oy + 140))
    stand("Grenadier", ox + 318, floor_at(m, ox + 318, oy + 140), flip=True)
    # a hoist over the heap: the bucket that filled it, still hanging
    chain(ox + 250, wy + 3, oy + 140)
    rect(ox + 243, oy + 140, ox + 257, oy + 150, MET)
    rect(ox + 243, oy + 140, ox + 257, oy + 140, MET_XL)
    rect(ox + 244, oy + 141, ox + 256, oy + 142, ORE)

    # the pit: its roof is the bowl's floor, on two stulls
    teeth(m, ox + 60, ox + 320, oy + 320, 12)
    for sx in (ox + 82, ox + 298):
        stull(sx, ceil_at(m, sx + 1, oy + 330) + 1, floor_at(m, sx + 1, oy + 330) - 1)
    ceil = ceil_at(m, ox + 120, oy + 320) + 1
    lamp(ox + 120, ceil, drop=8, bulb=LAMP, tint=LAMP, r=80, strength=0.15)
    for cx in (ox + 118, ox + 262):
        f = floor_at(m, cx, oy + 330)
        scrap_pile(cx - 14, f, 28, 6, colors=(MET_D, DIRT, ROCK_M, DIRT_D, ORE))
    stand("Gaper", ox + 150, floor_at(m, ox + 150, oy + 330))
    stand("RiotBrute", ox + 192, floor_at(m, ox + 192, oy + 330), flip=True)
    stand("Gaper", ox + 234, floor_at(m, ox + 234, oy + 330), flip=True)
    corpse(ox + 320, floor_at(m, ox + 320, oy + 330))


ROOM = {
    "name": "THE HOPPER", "w": 380, "h": 420,
    "shapes": [([("blob", 190, 130, 160, 78),                 # the bowl
                 ("blob", 190, 330, 152, 56)], 0.12),         # the pit
               ([("tube", [(190, 196), (190, 268)], 16)], 0.08)],   # the throat
    "sockets": {"T1": ("T", 110, 74), "T2": ("T", 280, 74),
                "L1": ("L", 140, 60), "R1": ("R", 140, 60),
                "L2": ("L", 372, 64), "R2": ("R", 372, 64)},
    "furnish": hopper_furnish,
}


SHEET = {
    "seed": 70101,
    "callouts": [
        ("1 ORE ON A TIMBER GATE", (-110, -50), (190, 214)),
        ("2 BURN THE GATE, DROP THE HEAP", (200, 440), (190, 300)),
        ("3 STULLS HOLD THE PIT ROOF", (-120, 440), (84, 300)),
    ],
    "beats": [
        ("THE HEAP IS THE WEAPON, THE PIT IS WHERE THEY STAND", (170, 180, 195)),
        ("PYRO AND GRENADIER ON THE BOWL'S LIP", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
