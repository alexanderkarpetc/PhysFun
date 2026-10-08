"""Small room S17 - THE BOULDER RUN.

A half-pipe: one round bowl worn smooth, a nose of rock hanging into it from the roof,
so the room is a U with a lip at each end. On the west lip a boulder sits chocked on a
timber wedge; down in the bottom of the bowl and up on the east lip, the enemies.
Knock the chock and the boulder drops into the bowl, runs the bottom and climbs the far
side, and rolls back - again and again, a little less each time.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S17"

BOWL_CX, BOWL_LIP, BOWL_DEPTH, BOWL_R = 230, 150, 172, 148
BOULDER_R = 17
BOULDER_X = 56          # boulder centre on the west lip


def bowl_floor(lx):
    """Local floor line of the half-pipe: flat lips, a round bottom between them."""
    u = (lx - BOWL_CX) / BOWL_R
    if abs(u) >= 1:
        return BOWL_LIP + (4 if lx > BOWL_CX else 0)
    return BOWL_LIP + BOWL_DEPTH * math.sqrt(1 - u * u) + (4 if lx > BOWL_CX else 0) * (abs(u) ** 6)


def nose_bottom(lx):
    """Underside of the rock nose hanging from the roof, local; None where there is none."""
    u = (lx - BOWL_CX) / 108.0
    if abs(u) >= 1:
        return None
    return 20 + 200 * math.sqrt(1 - u * u) + 5 * math.sin(lx * 0.21) + 3 * math.cos(lx * 0.53)


def run_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > bowl_floor(lx):
            continue
        nb = nose_bottom(lx)
        if nb is not None and ly < nb:
            continue
        out.add((x, y))
    return out


def boulder(cx, cy, r):
    """A round boulder, lit from up-left, cracked, with a scuffed band where it rolled."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            lit = (-dx * 0.6 - dy * 0.8) / r
            if d > r - 1.2:
                c = ROCK_D
            elif lit > 0.55:
                c = STONE_L
            elif lit > 0.1:
                c = STONE
            elif lit > -0.45:
                c = (100, 94, 80)
            else:
                c = STONE_D
            if chance(0.1):
                c = jitter(c, 10)
            px(x, y, c)
    for a0, ln in ((0.6, 11), (2.4, 8), (4.1, 9)):
        x, y = cx + math.cos(a0) * r * 0.2, cy + math.sin(a0) * r * 0.2
        for i in range(ln):
            x += math.cos(a0 + math.sin(i * 1.7) * 0.5)
            y += math.sin(a0 + math.sin(i * 1.7) * 0.5)
            px(x, y, STONE_D)
    px(cx - r * 0.45, cy - r * 0.5, (210, 200, 176))


def chock(x, floor, w=11, h=9):
    """Timber wedge against the boulder's downhill side, its thick end to the boulder."""
    for i in range(h):
        x1 = x + int(w * (h - i) / h)
        rect(x, floor - 1 - i, x1, floor - 1 - i, WOOD if i else WOOD_D)
    line(x, floor - h, x + w, floor - 1, WOOD_L)
    rect(x + 1, floor - h + 1, x + 2, floor - h + 2, MET_D)   # the spike that pins it


def scuff(m, ox, oy, lx0, lx1):
    """The track the boulder wore into the bowl: pale scored rock along the floor."""
    for lx in range(lx0, lx1):
        f = floor_at(m, ox + lx, oy + bowl_floor(lx) - 6)
        px(ox + lx, f, STONE_L if lx % 5 else ROCK_L)
        if lx % 3 == 0:
            px(ox + lx, f + 1, STONE_D)


def run_furnish(ox, oy, m):
    def fl(lx, from_y=None):
        return floor_at(m, ox + lx, oy + (from_y if from_y is not None else bowl_floor(lx) - 8))

    # the nose: teeth off its underside, a lamp at its tip; teeth off the lip roofs
    teeth(m, ox + 132, ox + 330, oy + 230, 22)
    teeth(m, ox + 20, ox + 120, oy + 110, 8)
    teeth(m, ox + 345, ox + 440, oy + 110, 8)
    tip = ceil_at(m, ox + BOWL_CX, oy + 300) + 1
    cage(ox + BOWL_CX, tip + 12, tip + 34, tip)                # an old gibbet off the nose
    lx = BOWL_CX - 26
    lamp(ox + lx, ceil_at(m, ox + lx, oy + 300) + 1, drop=6, bulb=LAMP, tint=LAMP, r=110,
         strength=0.16)
    stand("Ghast", ox + 300, oy + 222, flip=True)
    for lx in (52, 400):
        lamp(ox + lx, ceil_at(m, ox + lx, oy + 130) + 1, drop=5, bulb=LAMP, tint=LAMP,
             r=55, strength=0.13)
    # shelves on the outer walls, above the lips
    rock_blob(ox + 14, oy + 104, 14, 9, rough=0.3)
    rock_blob(ox + 448, oy + 100, 16, 10, rough=0.3)

    scuff(m, ox, oy, 52, 410)

    # the west lip: a boulder on a chock, and the next ones waiting behind it
    f = fl(BOULDER_X, 120)
    boulder(ox + BOULDER_X, f - BOULDER_R - 1, BOULDER_R)
    chock(ox + BOULDER_X + 10, f)
    boulder(ox + 26, f - 12, 11)
    boulder(ox + 22, f - 30, 8)
    rect(ox + 12, f - 3, ox + 40, f - 1, WOOD_D)                      # the sill they sit on
    line(ox + 35, f - 1, ox + 45, f - 40, MET_L)                      # a pry bar, leaning

    # the bottom of the bowl: what the last run left, and who stands in it now
    corpse(ox + 158, fl(158))
    scrap_pile(ox + 300, fl(306), 14, 4, colors=(MET_D, DIRT, ROCK_M, WOOD_D))
    stand("RiotBrute", ox + 206, fl(206))
    stand("Gaper", ox + 256, fl(256), flip=True)
    stand("Minespider", ox + 178, fl(178))
    stand("WizBogcap", ox + 282, fl(282), flip=True)
    for bx in (196, 268, 300):
        disc(ox + bx, fl(bx) - 2, 2, STONE)

    # the east lip: a crate breastwork and the throwers behind it
    crate_g(ox + 384, fl(390, 120), 11)
    crate_g(ox + 396, fl(402, 120), 11)
    crate_g(ox + 389, fl(395, 120) - 11, 10)
    stand("Grenadier", ox + 420, fl(420, 120), flip=True)
    stand("WizRamskull", ox + 440, fl(440, 120), flip=True)

    # the run, ghosted: where it goes once the chock is out
    for lx in range(BOULDER_X + 30, 373):
        if (lx // 4) % 2 == 0:
            y = oy + bowl_floor(lx) - BOULDER_R - 6
            px(ox + lx, y, (200, 205, 190), 0.55)
    ax, ay = ox + 372, oy + bowl_floor(372) - BOULDER_R - 6
    for k in range(5):
        px(ax - k, ay + k, (200, 205, 190), 0.8)
        px(ax - 4 + k, ay + 4, (200, 205, 190), 0.8)


ROOM = {
    "name": "THE BOULDER RUN", "w": 460, "h": 380,
    "shapes": [([("blob", 230, 210, 214, 150)], 0.05),
               ([("blob", 58, 112, 64, 40),             # west lip
                 ("blob", 404, 112, 64, 40)], 0.10)],   # east lip
    "sockets": {"T1": ("T", 58, 76), "T2": ("T", 412, 76),
                "L1": ("L", 150, 12), "R1": ("R", 154, 12),
                "B1": ("B", 230, 48)},
    "edit": run_edit,
    "furnish": run_furnish,
}


SHEET = {
    "seed": 71701,
    "callouts": [
        ("1 BOULDER ON A CHOCK", (-120, 196), (BOULDER_X, 128)),
        ("2 THEY STAND IN THE BOTTOM", (-110, 400), (206, 300)),
        ("3 CRATES ON THE FAR LIP", (388, 204), (396, 140)),
    ],
    "beats": [
        ("KNOCK THE CHOCK: IT RUNS THE BOWL, UP THE FAR SIDE AND BACK", (170, 180, 195)),
        ("EVERY PASS IS LOWER - THE BOTTOM GETS IT EVERY TIME", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
