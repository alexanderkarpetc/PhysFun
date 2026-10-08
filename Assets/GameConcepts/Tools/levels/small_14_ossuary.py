"""Small room S14 - THE OSSUARY.

A round chamber whose walls are cut into rows of bone niches, skulls stacked in every
one. The floor across the middle is not rock: it is a crust of packed bone meal a few
pixels thick over a void nobody filled in, already cracked through, with one hole where
a piece has gone. Under it, a drop onto rock spikes and whoever fell in last time.

The crust takes a character's weight and not much more. A blast, a heavy body landing,
or a few shots into it, and the middle of the floor goes - with whoever is standing on
it. The blood mage and the bone-crown stand right in the middle.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S14"

BONE = (199, 190, 160)
BONE_D = (146, 138, 114)
MEAL = (96, 88, 72)           # packed bone meal: the crust
MEAL_L = (138, 128, 104)
CANDLE = (255, 214, 140)

CH = (200, 190, 172, 150)     # the chamber
FLOOR = 286
CRUST = 6
VOID = (200, 314, 132, 28)    # the void under the crust
HOLE = (264, 271)             # where a piece of crust has already gone
NICHE_W, NICHE_H = 20, 8
NICHES = [("L", 80), ("L", 98), ("L", 116), ("L", 134), ("L", 218), ("L", 236),
          ("R", 80), ("R", 98), ("R", 116), ("R", 134), ("R", 202), ("R", 220), ("R", 238)]
SHELVES = [(36, 194, 42, 16),     # west ledge
           (364, 178, 42, 16),    # east ledge (R2)
           (200, 50, 62, 36),     # the roof boss the crown hangs off
           (128, 46, 20, 16), (272, 48, 20, 14)]


def wall_x(side, y):
    cx, cy, rx, ry = CH
    t = max(0.0, 1 - ((y - cy) / ry) ** 2)
    return cx - rx * math.sqrt(t) if side == "L" else cx + rx * math.sqrt(t)


def niche_box(side, y):
    xw = int(wall_x(side, y))
    if side == "L":
        return xw - NICHE_W + 3, y - NICHE_H, xw + 3, y - 1
    return xw - 3, y - NICHE_H, xw + NICHE_W - 3, y - 1


def in_void(lx, ly):
    cx, cy, rx, ry = VOID
    wob = 1 + 0.07 * math.sin(lx * 0.17) + 0.05 * math.sin(lx * 0.05 + 1)
    return ly >= FLOOR + CRUST and ((lx - cx) / rx) ** 2 + ((ly - cy) / ry) ** 2 <= wob


def oss_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR:
            continue
        if any(((lx - cx) / rx) ** 2 + ((ly - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in SHELVES):
            continue
        out.add((x, y))
    cx, cy, rx, ry = VOID
    for ly in range(cy - ry - 2, cy + ry + 3):
        for lx in range(cx - rx - 8, cx + rx + 9):
            if in_void(lx, ly):
                out.add((lx + ox, ly + oy))
    for lx in range(HOLE[0], HOLE[1] + 1):              # the hole already in it
        for ly in range(FLOOR - 1, FLOOR + CRUST + 1):
            out.add((lx + ox, ly + oy))
    for side, y in NICHES:
        x0, y0, x1, y1 = niche_box(side, y)
        for ly in range(y0, y1 + 1):
            for lx in range(x0, x1 + 1):
                out.add((lx + ox, ly + oy))
    return out


def skull(x, y, flip=False):
    """4x4 skull, sitting with its jaw on y."""
    rect(x, y - 3, x + 3, y - 1, BONE)
    rect(x + 1, y - 4, x + 2, y - 4, BONE)
    px(x + (2 if flip else 1), y - 2, INK)
    px(x + (3 if flip else 0), y - 2, INK if chance(0.5) else BONE_D)
    rect(x, y, x + 3, y, BONE_D)


def long_bone(x, y, ln):
    rect(x, y, x + ln, y, BONE)
    px(x, y - 1, BONE)
    px(x + ln, y - 1, BONE)
    px(x + ln // 2, y, BONE_D)


def fill_niche(x0, y0, x1, y1, candle=False):
    for k in range(3):                                   # long bones stacked like wood
        long_bone(x0 + 1 + k, y1 - k, x1 - x0 - 3 - k)
    sx = x0 + 2
    while sx + 3 < x1 - 1:
        skull(sx, y1 - 2, flip=chance(0.5))
        sx += 5
    if candle:
        cx = (x0 + x1) // 2
        rect(cx, y0 + 1, cx, y0 + 2, BONE)
        px(cx, y0, CANDLE)
        glow(cx, y0, 22, CANDLE, 0.16)


def charnel_heap(m, cx, half, base, peak):
    """A mound of bones on solid floor. Only painted where there is air, so it sits in
    the room and not in the rock."""
    for x in range(cx - half, cx + half + 1):
        t = abs(x - cx) / half
        top = base - peak * (1 - t * t)
        for y in range(int(top), base):
            if (x, y) in m:
                r = rnd()
                px(x, y, BONE_D if r < 0.14 else MEAL if r < 0.55 else DIRT_D if r < 0.85 else DIRT)
        if (x, int(top)) in m:
            px(x, int(top), BONE_D)
    for _ in range(int(half * peak / 30)):
        x = cx - half * 0.7 + rnd() * half * 1.4
        t = abs(x - cx) / half
        y = base - 2 - rnd() * (peak - 4) * (1 - t * t)
        if (int(x), int(y)) in m and (int(x) + 3, int(y) - 4) in m:
            skull(int(x), int(y), flip=chance(0.5))
    for _ in range(int(half / 3)):
        x = cx - half * 0.8 + rnd() * half * 1.6
        t = abs(x - cx) / half
        y = base - 1 - rnd() * peak * (1 - t * t)
        long_bone(int(x), int(y), 3 + int(rnd() * 4))


def gibbet(x, roof, top):
    chain(x, roof, top)
    rect(x - 7, top, x + 7, top + 1, MET_D)
    rect(x - 7, top + 24, x + 7, top + 25, MET_D)
    for bx in range(x - 7, x + 8, 3):
        rect(bx, top + 2, bx, top + 23, MET)
    skull(x - 2, top + 9)
    rect(x - 1, top + 10, x + 1, top + 17, BONE_D)
    line(x - 1, top + 18, x - 3, top + 23, BONE)
    line(x + 1, top + 18, x + 3, top + 23, BONE)


def stalagmites(x0, x1, floor_fn, n):
    for _ in range(n):
        x = int(x0 + rnd() * (x1 - x0))
        base = floor_fn(x)
        ln = 5 + int(rnd() * 10)
        for i in range(ln):
            half = max(0, int((ln - i) / 3))
            rect(x - half, base - i, x + half, base - i, ROCK_M)
        px(x, base - ln + 1, ROCK_L)


def oss_furnish(ox, oy, m):
    teeth(m, ox + 50, ox + 350, oy + 120, 26)

    # niches: bones racked in, skulls along the front, candles in a few
    for i, (side, y) in enumerate(NICHES):
        x0, y0, x1, y1 = niche_box(side, y)
        fill_niche(ox + x0, oy + y0, ox + x1, oy + y1, candle=i in (1, 4, 7, 10))

    # the crust: bone meal, lit along its top, cracked right through
    cx, cy, rx, ry = VOID
    crust_x = [lx for lx in range(cx - rx - 6, cx + rx + 7)
               if any(in_void(lx, ly) for ly in range(FLOOR + CRUST, FLOOR + CRUST + 3))]
    for lx in crust_x:
        if HOLE[0] <= lx <= HOLE[1]:
            continue
        for d in range(CRUST):
            px(ox + lx, oy + FLOOR + d, MEAL if rnd() > 0.18 else pick([BONE_D, DIRT_D, MEAL_L]))
        px(ox + lx, oy + FLOOR, MEAL_L)
        if chance(0.12):
            px(ox + lx, oy + FLOOR + 1 + int(rnd() * 4), BONE)
    for _ in range(9):                                   # cracks through it
        x = ox + crust_x[0] + 6 + rnd() * (len(crust_x) - 12)
        if HOLE[0] - 3 <= x - ox <= HOLE[1] + 3:
            continue
        for d in range(CRUST + 1):
            px(x, oy + FLOOR + d, INK)
            x += pick([-1, 0, 0, 1])
        px(x, oy + FLOOR + CRUST + 1, MEAL)              # a grain falling
        px(x + 1, oy + FLOOR + CRUST + 6 + int(rnd() * 8), MEAL_L, 0.7)
    for _ in range(5):                                   # hairlines along the top
        x = ox + crust_x[0] + rnd() * len(crust_x)
        for i in range(6 + int(rnd() * 8)):
            px(x + i, oy + FLOOR + 1 + (i // 4) % 2, INK, 0.7)
    for lx in (HOLE[0] - 1, HOLE[1] + 1):                # broken edges of the hole
        rect(ox + lx, oy + FLOOR + 1, ox + lx, oy + FLOOR + CRUST + 1, MEAL_L)

    # the void: spikes and the last ones through
    vf = lambda x: floor_at(m, x, oy + FLOOR + CRUST + 2) - 1
    stalagmites(ox + cx - rx + 22, ox + cx + rx - 22, vf, 30)
    for bx in (ox + 150, ox + 214, ox + 258):
        b = vf(bx)
        for _ in range(8):
            line(bx + rnd() * 14, b - rnd() * 2, bx + rnd() * 14 + 3, b - rnd() * 4, BONE)
        skull(bx + 4, b - 1)
    skull(ox + 266, vf(ox + 268) - 3)                    # the piece that went, and its rider
    rect(ox + 262, vf(ox + 262) - 2, ox + 272, vf(ox + 262) - 1, MEAL)
    for i in range(8):                                    # dust still sifting down
        px(ox + 266 + pick([-1, 0, 1, 2]), oy + FLOOR + CRUST + 3 + i * 3, MEAL_L, 0.6)

    # floor at the walls is real rock: the overflow is shovelled up against it
    charnel_heap(m, ox + 96, 22, oy + FLOOR, 20)
    charnel_heap(m, ox + 304, 22, oy + FLOOR, 24)
    gibbet(ox + 248, ceil_at(m, ox + 248, oy + 100) + 1, oy + 132)
    gibbet(ox + 112, ceil_at(m, ox + 112, oy + 100) + 1, oy + 118)

    # the ledges, and the lamp of the place: a candle crown off the roof
    crown_x = ox + 200
    top = ceil_at(m, crown_x, oy + 110) + 1
    chain(crown_x, top, oy + 120)
    rect(crown_x - 12, oy + 120, crown_x + 12, oy + 121, MET_D)
    for k in range(-12, 13, 6):
        rect(crown_x + k, oy + 118, crown_x + k, oy + 119, BONE)
        px(crown_x + k, oy + 117, CANDLE)
    glow(crown_x, oy + 118, 110, CANDLE, 0.14)
    for k in (-10, -3, 4, 10):
        skull(crown_x + k - 2, oy + 127)

    stand("BloodMage", ox + 196, oy + FLOOR)
    stand("WizBonecrown", ox + 228, oy + FLOOR, flip=True)
    stand("Gaper", ox + 156, oy + FLOOR)
    fe = floor_at(m, ox + 342, oy + 150)
    stand("Grenadier", ox + 340, fe, flip=True)
    fw = floor_at(m, ox + 58, oy + 160)
    stand("WizRamskull", ox + 60, fw)
    stand("Ghast", ox + 160, oy + 196)


ROOM = {
    "name": "THE OSSUARY", "w": 400, "h": 380,
    "shapes": [([("blob",) + CH], 0.04)],
    "sockets": {"T1": ("T", 130, 64), "T2": ("T", 280, 66),
                "L1": ("L", FLOOR, 60), "R1": ("R", FLOOR, 60),
                "R2": ("R", 162, 44)},
    "edit": oss_edit,
    "furnish": oss_furnish,
}


SHEET = {
    "seed": 71401,
    "callouts": [
        ("1 BONE NICHES ROUND THE WALLS", (-120, -50), (62, 112)),
        ("2 THE FLOOR IS A CRUST", (-120, 400), (140, 290)),
        ("3 ...OVER A DROP ONTO SPIKES", (196, 400), (236, 330)),
    ],
    "beats": [
        ("BLOW THE MIDDLE OUT: THE MAGES GO THROUGH IT", (170, 180, 195)),
        ("THE GRENADIER BREAKS IT FOR YOU IF YOU STAND THERE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
