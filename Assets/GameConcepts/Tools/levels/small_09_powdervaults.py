"""Small room S09 - THE POWDER VAULTS.

Four masonry vaults in a row, stepped down the slope of the drift they were cut into,
each one a barrel arch on pendant piers with a stack of powder kegs on its flags. One
FuseCord runs along the floor through every stack and hangs its tail over the last
step into the round sump at the low end. A Pyro walks among the kegs.

Light any of it and the cord carries the fire bay to bay, down the steps: the arches
go one after another, and whatever stands under them comes down with the masonry.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S09"

CORD = (176, 140, 87)            # FuseCord.cordColor
CORD_D = (115, 84, 48)           # FuseCord.cordShade

EDGES = (14, 90, 166, 242, 318)            # bay walls, west to east
FLOORS = (112, 126, 140, 154)              # each bay one step lower than the last
SPRING = 44                                # arch springing over the bay's floor
RISE = 30                                  # crown over the springing
SUMP = (378, 206, 54, 62)                  # the round sump at the low end


def bay_arch(i, x):
    """Intrados of bay i at x (local): a half ellipse from wall to wall."""
    x0, x1 = EDGES[i], EDGES[i + 1]
    cx, r = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    t = max(-1.0, min(1.0, (x - cx) / r))
    return FLOORS[i] - SPRING - RISE * math.sqrt(1 - t * t)


def vault_edit(air, ox, oy):
    out = {(x, y) for (x, y) in air if x - ox >= EDGES[-1] - 2 or y - oy > FLOORS[-1] + 60}
    for i in range(4):
        for x in range(EDGES[i], EDGES[i + 1] + 1):
            top = bay_arch(i, x)
            for y in range(int(top) + 1, FLOORS[i]):
                out.add((x + ox, y + oy))
    return out


def stone_at(x, y, ox, oy):
    """Coursed block for the flags and piers; voussoirs round each arch."""
    lx, ly = x - ox, y - oy
    for i in range(4):
        x0, x1 = EDGES[i], EDGES[i + 1]
        sp = FLOORS[i] - SPRING
        if x0 + 2 <= lx <= x1 - 2 and ly < sp:
            cx = (x0 + x1) / 2.0
            a = math.atan2((sp - ly) / RISE, (lx - cx) / ((x1 - x0) / 2.0))
            if int(a / 0.2) != int((a + 0.035) / 0.2):
                return STONE_D
            d = ((lx - cx) / ((x1 - x0) / 2.0 + 7)) ** 2 + ((sp - ly) / (RISE + 7)) ** 2
            return STONE_L if d > 0.98 else STONE
    if ly % 6 == 0:
        return STONE_D
    if (lx + (ly // 6) * 5) % 11 == 0:
        return STONE_D
    return STONE


def dilate(cells, n):
    out = set(cells)
    for _ in range(n):
        out |= {(x + dx, y + dy) for (x, y) in out for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    return out


def keg_stack(x, floor, rows):
    """Kegs racked on their ends, each row set back half a keg."""
    for r, n in enumerate(rows):
        for k in range(n):
            keg(int(x + r * 4.5 + k * 9), floor - r * 11)


def cord(points):
    """FuseCord: two-tone cord, pinned every so often."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)))
        for i in range(n + 1):
            x = ax + (bx - ax) * i / max(n, 1)
            y = ay + (by - ay) * i / max(n, 1)
            px(x, y, CORD)
            px(x, y + 1, CORD_D)
            if i % 18 == 0:
                px(x, y - 1, MET_L)


def vault_furnish(ox, oy, m):
    # the masonry: everything solid within a few px of a bay's air
    bays = {(x, y) for (x, y) in m if x - ox < EDGES[-1] - 1 and y - oy < FLOORS[-1] + 2}
    ring = dilate(bays, 6) - m
    for (x, y) in ring:
        if x - ox < EDGES[-1] + 4 and 0 <= y - oy:
            px(x, y, stone_at(x, y, ox, oy))
    # the step faces and the flags get a lit top
    for i in range(4):
        rect(ox + EDGES[i], oy + FLOORS[i], ox + EDGES[i + 1], oy + FLOORS[i], STONE_L)

    # the sump at the low end: rough rock, teeth, junk the vaults were cleared into
    teeth(m, ox + 330, ox + 430, oy + 170, 10)
    rock_blob(ox + 428, oy + 206, 16, 10, rough=0.25)
    sf = floor_at(m, ox + 380, oy + 230)
    # a keg sling still on its hoist chain over the sump
    hy = ceil_at(m, ox + 392, oy + 190) + 1
    rect(ox + 386, hy, ox + 398, hy + 2, MET_D)
    chain(ox + 392, hy + 3, oy + 196)
    line(ox + 392, oy + 196, ox + 381, oy + 202, (150, 130, 96))
    line(ox + 392, oy + 196, ox + 403, oy + 202, (150, 130, 96))
    keg(ox + 382, oy + 213)
    keg(ox + 392, oy + 213)
    rect(ox + 381, oy + 213, ox + 402, oy + 213, (150, 130, 96))
    scrap_pile(ox + 340, sf, 30, 7, colors=(WOOD_D, KEG, MET_D, ROCK_M, DIRT))
    crate_g(ox + 400, floor_at(m, ox + 406, oy + 230))
    crate_g(ox + 403, floor_at(m, ox + 406, oy + 230) - 12, 10)
    lamp(ox + 380, ceil_at(m, ox + 380, oy + 190) + 1, drop=10, bulb=LAMP, tint=LAMP,
         r=70, strength=0.14)

    # kegs in every bay
    stacks = ((24, (4, 3, 2)), (104, (5, 4, 2)), (186, (3, 2)), (252, (4, 3, 2, 1)))
    for i, (sx, rows) in enumerate(stacks):
        keg_stack(ox + sx, oy + FLOORS[i], rows)
    keg(ox + 218, oy + FLOORS[2])                       # one rolled out of its stack
    crate_g(ox + 64, oy + FLOORS[0], 11)
    crate_g(ox + 146, oy + FLOORS[1], 10)

    # the cord: festooned pier to pier along the springing, a lead down into the top of
    # every stack, and the tail over the last step into the sump
    pins = [(ox + EDGES[0] + 3, oy + FLOORS[0] - SPRING + 4)]
    pins += [(ox + EDGES[i + 1], oy + FLOORS[min(i + 1, 3)] - SPRING + 3) for i in range(4)]
    for i, ((ax, ay), (bx, by)) in enumerate(zip(pins, pins[1:])):
        sx, rows = stacks[i]
        tx = ox + sx + int((len(rows) - 1) * 4.5) + 4
        ty = oy + FLOORS[i] - len(rows) * 11 + 1
        low = (tx, max(ay, by) + 12)
        cord([(ax, ay), ((ax + low[0]) / 2, (ay + low[1]) / 2 + 2), low,
              ((bx + low[0]) / 2, (by + low[1]) / 2 + 2), (bx, by)])
        cord([low, (tx, ty)])
    for (x, y) in pins:
        rect(x - 1, y - 2, x + 1, y - 1, MET_D)
    lx, ly = pins[-1]
    cord([(lx, ly), (lx + 6, ly + 14), (lx + 7, oy + FLOORS[3] + 6), (lx + 9, oy + FLOORS[3] + 30)])

    # lamps in the crowns, caged
    for i in range(4):
        cx = (EDGES[i] + EDGES[i + 1]) // 2
        top = oy + int(bay_arch(i, cx)) + 1
        lamp(ox + cx, top, drop=5, bulb=LAMP, tint=LAMP, r=46, strength=0.12)

    stand("Pyro", ox + 80, oy + FLOORS[0])
    stand("WizGoldhood", ox + 160, oy + FLOORS[1], flip=True)
    stand("Grenadier", ox + 232, oy + FLOORS[2], flip=True)
    stand("Gaper", ox + 304, oy + FLOORS[3], flip=True)
    stand("RiotBrute", ox + 366, sf, flip=True)
    corpse(ox + 410, floor_at(m, ox + 416, oy + 230))

    # the spoil crawl under the row: where the burst kegs were swept, and the long way
    # round to the sump
    teeth(m, ox + 40, ox + 330, oy + 268, 14)
    pf = floor_at(m, ox + 128, oy + 272)
    for k, bx in enumerate((100, 112, 146)):
        f = floor_at(m, ox + bx + 4, oy + 272)
        rect(ox + bx, f - 3, ox + bx + 8, f - 1, KEG)            # staves, burst
        rect(ox + bx + 1, f - 4, ox + bx + 3, f - 4, KEG_L)
        px(ox + bx + 6, f - 2, MET_D)
    scrap_pile(ox + 170, floor_at(m, ox + 180, oy + 272), 24, 5,
               colors=(WOOD_D, KEG, DIRT, ROCK_M, CHAR))
    lamp(ox + 128, ceil_at(m, ox + 128, oy + 270) + 1, drop=4, bulb=LAMP, tint=LAMP,
         r=44, strength=0.12)
    for sx in (52, 214):
        stull(ox + sx, ceil_at(m, ox + sx + 1, oy + 274) + 1, floor_at(m, ox + sx + 1, oy + 274) - 1)
    rock_blob(ox + 44, oy + 300, 28, 9, rough=0.3)
    stand("Minespider", ox + 126, pf)
    stand("WizBogcap", ox + 270, floor_at(m, ox + 270, oy + 268), flip=True)


ROOM = {
    "name": "THE POWDER VAULTS", "w": 440, "h": 320,
    "shapes": [([("blob",) + SUMP], 0.1),
               ([("tube", [(306, 140), (346, 160)], 16),
                 ("tube", [(346, 246), (240, 272), (120, 280), (10, 274)], 14)], 0.07),
               ([("blob", 128, 272, 44, 20)], 0.12)],          # the spoil pocket
    "sockets": {"T1": ("T", 52, 40), "T2": ("T", 204, 70),
                "L1": ("L", FLOORS[0], 20), "L2": ("L", 289, 16),
                "R1": ("R", 226, 24), "B1": ("B", 236, 40)},
    "edit": vault_edit,
    "furnish": vault_furnish,
}


SHEET = {
    "seed": 70901,
    "callouts": [
        ("1 FOUR VAULTS, STEPPED DOWN", (-110, -50), (128, 50)),
        ("2 ONE CORD THROUGH EVERY STACK", (-120, 196), (90, 84)),
        ("3 TAIL HANGS INTO THE SUMP", (300, 345), (327, 182)),
    ],
    "beats": [
        ("LIGHT ONE BAY, THE CORD CARRIES IT DOWN THE ROW", (170, 180, 195)),
        ("PYRO AMONG THE KEGS, GRENADIER ONE BAY DOWN", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
