"""Small room S04 - THE BELFRY.

A tall shaft with a dome at the top and an iron bell hung in the dome on one chain off a
timber headbeam. Ledges are cut into the walls at three heights, a side each in turn;
the foot of the shaft is a flat floor with powder kegs on it. Cut the chain and the bell
falls the whole height onto whoever is standing at the bottom.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S04"

BELL_X = 150
BEAM_Y = 58
BELL_TOP, BELL_LIP = 112, 162
FOOT = 432                       # the floor at the bottom of the shaft
# ledges cut into the walls: (side, floor y, how far the lip juts into the shaft)
LEDGES = (("L", 186, 104), ("R", 268, 196), ("L", 346, 104))
BRONZE = (86, 78, 64)
BRONZE_L = (132, 118, 90)
BRONZE_D = (50, 45, 37)
DROP = (150, 160, 180)


def belfry_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FOOT:
            continue
        cut = False
        for side, fy, lip in LEDGES:
            if fy <= ly < fy + 40 and ((side == "L" and lx < lip) or (side == "R" and lx > lip)):
                cut = True
        if not cut:
            out.add((x, y))
    return out


def heavy_chain(x, y0, y1):
    """Bell chain: big alternating links, two pixels wide - the one thing holding it."""
    for i, y in enumerate(range(int(y0), int(y1), 4)):
        if i % 2:
            rect(x - 1, y, x + 1, y + 3, MET_L)
            px(x, y + 1, INK)
            px(x, y + 2, INK)
        else:
            rect(x, y, x, y + 3, MET_XL)
            px(x + 1, y + 1, MET_D)


def bell(cx, top, lip):
    """The bell side-on: crown loop, waist, flared lip and a clapper hanging out of it."""
    rect(cx - 4, top - 6, cx + 4, top - 1, BRONZE_D)
    rect(cx - 2, top - 5, cx + 2, top - 2, INK)
    h = lip - top
    for i in range(h + 1):
        t = i / h
        half = 9 + 13 * t ** 1.7 + (5 * (t - 0.86) / 0.14 if t > 0.86 else 0)
        y = top + i
        rect(cx - half, y, cx + half, y, BRONZE)
        rect(cx - half, y, cx - half + 1, y, BRONZE_L)
        rect(cx + half - 2, y, cx + half, y, BRONZE_D)
        if i in (6, int(h * 0.55), h - 5):
            rect(cx - half, y, cx + half, y, BRONZE_D)      # cast bands
    for i in range(int(h * 0.15), int(h * 0.8)):          # the highlight down its west face
        px(cx - 9 - 9 * (i / h) ** 1.7, top + i, (170, 154, 118))
    rect(cx - 26, lip, cx + 26, lip + 1, BRONZE_D)
    line(cx, lip - 8, cx + 2, lip + 6, MET_D)               # clapper
    disc(cx + 2, lip + 7, 2.6, MET_D)
    px(cx + 1, lip + 6, MET_L)


def headbeam(x0, x1, y):
    rect(x0, y, x1, y + 4, WOOD)
    rect(x0, y, x1, y, WOOD_L)
    rect(x0, y + 4, x1, y + 4, WOOD_D)
    for x in range(int(x0) + 6, int(x1), 17):
        px(x, y + 2, WOOD_D)
    for wx in (x0 + 1, x1 - 7):                             # wedges driven in at both ends
        rect(wx, y - 3, wx + 6, y - 1, WOOD_D)


def ledge_planks(x0, x1, y):
    """Boards laid out over the lip of a ledge, so it reaches a little further."""
    for x in range(int(x0), int(x1), 6):
        rect(x, y - 2, x + 4, y - 1, WOOD)
        px(x, y - 2, WOOD_L)


def drop_line(x, y0, y1):
    for y in range(int(y0), int(y1), 7):
        rect(x, y, x, y + 2, DROP, 0.45)
    for i in range(4):                                      # arrowhead over the foot
        rect(x - 4 + i, y1 - 8 + i, x + 4 - i, y1 - 8 + i, DROP, 0.55)


def wall_shelf(m, ox, oy, side, ly, rx, ry):
    """A rock shelf grown out of the shaft wall at height ly - found by scanning out from
    the middle of the shaft, so it is always attached to the wall it sticks out of."""
    x, step = ox + BELL_X, (-1 if side == "L" else 1)
    while (x, oy + ly) in m:
        x += step
    rock_blob(x - step * (rx // 3), oy + ly, rx, ry, rough=0.25)


def belfry_furnish(ox, oy, m):
    # rock: teeth off the dome and the ledge roofs, shelves off the shaft walls
    teeth(m, ox + 60, ox + 240, oy + 60, 18)
    for (side, fy, lip) in LEDGES:
        x0, x1 = (ox + 14, ox + lip - 4) if side == "L" else (ox + lip + 4, ox + 286)
        teeth(m, x0, x1, oy + fy - 10, 6)
    for side, by, rx, ry in (("R", 172, 14, 8), ("L", 250, 13, 8), ("R", 372, 15, 9),
                             ("L", 398, 12, 8), ("L", 112, 12, 7), ("R", 120, 10, 6),
                             ("R", 310, 10, 6)):
        wall_shelf(m, ox, oy, side, by, rx, ry)

    # the bell, its beam and its one chain
    headbeam(ox + 52, ox + 248, oy + BEAM_Y)
    rect(ox + BELL_X - 6, oy + BEAM_Y + 5, ox + BELL_X + 6, oy + BEAM_Y + 7, MET_D)   # yoke
    heavy_chain(ox + BELL_X, oy + BEAM_Y + 8, oy + BELL_TOP - 5)
    glow(ox + BELL_X, oy + 140, 60, LAMP, 0.10)
    bell(ox + BELL_X, oy + BELL_TOP, oy + BELL_LIP)
    lamp(ox + 210, oy + BEAM_Y + 5, drop=10, bulb=LAMP, tint=LAMP, r=70, strength=0.14)
    drop_line(ox + BELL_X, oy + BELL_LIP + 14, oy + FOOT - 30)

    # the ledges
    for i, (side, fy, lip) in enumerate(LEDGES):
        ly = oy + fy
        if side == "L":
            ledge_planks(ox + lip - 2, ox + lip + 12, ly)
            lamp(ox + 40, ceil_at(m, ox + 40, ly - 6) + 1, drop=4, bulb=LAMP, tint=LAMP,
                 r=46, strength=0.13)
        else:
            ledge_planks(ox + lip - 12, ox + lip + 2, ly)
            lamp(ox + 262, ceil_at(m, ox + 262, ly - 6) + 1, drop=4, bulb=LAMP, tint=LAMP,
                 r=46, strength=0.13)
    f1, f2, f3 = (oy + fy for _, fy, _ in LEDGES)
    crate_g(ox + 22, f1)
    stand("Grenadier", ox + 88, f1)
    stand("WizBonecrown", ox + 58, f1)
    keg(ox + 268, f2)
    stand("Sentinel", ox + 222, f2, flip=True)
    scrap_pile(ox + 24, f3, 20, 5, colors=(MET_D, DIRT, ROCK_M, WOOD_D))
    stand("Pyro", ox + 82, f3)
    sprite("Ghast", ox + 176, oy + 300, flip=True)

    # the foot of the shaft: kegs, the crew, and whatever the bell landed on last time
    fy = oy + FOOT
    for i, kx in enumerate((136, 145, 154, 140, 149)):
        keg(ox + kx, fy - (11 if i >= 3 else 0))
    crate_g(ox + 168, fy)
    scrap_pile(ox + 50, fy, 30, 6, colors=(BRONZE_D, MET_D, DIRT, ROCK_M))
    stand("Gaper", ox + 110, fy)
    stand("RiotBrute", ox + 196, fy, flip=True)
    stand("Gaper", ox + 226, fy, flip=True)
    stand("Minespider", ox + 76, fy)
    corpse(ox + 252, fy)
    glow(ox + 150, fy - 20, 80, LAMP, 0.10)


ROOM = {
    "name": "THE BELFRY", "w": 300, "h": 460,
    "shapes": [([("blob", 150, 84, 100, 58),                   # the dome the bell hangs in
                 ("blob", 150, 410, 120, 40)], 0.10),          # the foot
               ([("tube", [(150, 90), (144, 200), (156, 320), (150, 410)], 56)], 0.06),
               ([("blob", 58, 166, 50, 26),                    # ledges, a side each in turn
                 ("blob", 244, 248, 50, 26),
                 ("blob", 58, 328, 48, 24)], 0.12)],
    "sockets": {"T1": ("T", 92, 44), "T2": ("T", 212, 44),
                "L1": ("L", 186, 20), "R1": ("R", 268, 18),
                "L2": ("L", FOOT, 40), "R2": ("R", FOOT, 40)},
    "edit": belfry_edit,
    "furnish": belfry_furnish,
}


SHEET = {
    "seed": 70404,
    "callouts": [
        ("1 BELL ON ONE CHAIN", (-160, 40), (151, 90)),
        ("2 LEDGES, SIDE TO SIDE", (-160, 280), (40, 346)),
        ("3 KEGS AT THE FOOT", (316, 470), (150, 424)),
    ],
    "beats": [
        ("CUT THE CHAIN: THE BELL FALLS THE WHOLE SHAFT", (170, 180, 195)),
        ("THROWERS ON THE LEDGES, A GHAST IN THE GAP", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
