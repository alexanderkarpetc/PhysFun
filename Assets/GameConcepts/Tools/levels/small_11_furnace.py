"""Small room S11 - THE FURNACE.

A tall gourd of a room with a brick muffle furnace at the bottom of it, still burning:
fire in the box, flames out of both stoke holes, a brick flue up the middle. Round the
flue is the timber the men who fed it built - posts off the floor, a charging deck at
the flue head, and ramps off the deck to ledges in the walls - all of it dry, all of it
hung with coal sacks, and the enemies stand on it.

The toy is a fire that never goes out sitting under a lot of wood. Knock a sack into
the stoke hole, burn a post, or just wait for an ember to find the deck.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S11"

BRICK = (116, 60, 46)
BRICK_D = (74, 38, 31)
BRICK_L = (152, 88, 62)
SACK = (70, 64, 54)
SACK_L = (98, 90, 76)
SMOKE = (80, 76, 72)


def brick(x0, y0, x1, y1):
    """Fired brick in stretcher bond, hot side up."""
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            joint = (y - int(y0)) % 4 == 3 or (x + ((y - int(y0)) // 4) * 4) % 8 == 0
            px(x, y, BRICK_D if joint else BRICK)
    rect(x0, y0, x1, y0, BRICK_L)


def coal_sack(x, floor):
    rect(x + 1, floor - 9, x + 10, floor - 1, SACK)
    rect(x, floor - 6, x + 11, floor - 2, SACK)
    rect(x + 3, floor - 11, x + 8, floor - 10, (52, 48, 42))
    rect(x + 1, floor - 9, x + 10, floor - 9, SACK_L)
    px(x + 5, floor - 12, (52, 48, 42))


def coal_heap(x, floor, w, h):
    for i in range(w):
        t = abs(i - w / 2.0) / (w / 2.0)
        top = floor - int(h * (1 - t * t))
        for y in range(top, floor):
            px(x + i, y, pick([CHAR, CHAR, (44, 40, 38), ROCK_D]))
        if chance(0.25):
            px(x + i, top, (70, 66, 62))


def deck(x0, x1, y, posts=()):
    """Plank deck: two boards and the joist under them."""
    rect(x0, y, x1, y + 1, WOOD)
    rect(x0, y, x1, y, WOOD_L)
    rect(x0, y + 2, x1, y + 3, WOOD_D)
    for x in range(int(x0) + 3, int(x1), 7):
        px(x, y, WOOD_D)


def ramp(x0, y0, x1, y1):
    for t in range(3):
        line(x0, y0 + t, x1, y1 + t, (WOOD_L, WOOD, WOOD_D)[t])
    n = int(abs(x1 - x0) / 7)
    for k in range(1, n):
        f = k / float(n)
        px(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f - 1, WOOD_D)


def brace(x0, y0, x1, y1):
    line(x0, y0, x1, y1, WOOD_D)
    line(x0 + 1, y0, x1 + 1, y1, WOOD)


def smoke(x0, y0, x1, y1, n=70):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), 2 + rnd() * 4, SMOKE, 0.08)


def furnace(cx, floor):
    """The muffle furnace seen in section: brick box, fire inside, a stoke hole each
    side, a dome over it and the flue out of the dome."""
    x0, x1, top = cx - 46, cx + 46, floor - 58
    brick(x0, top, x1, floor - 1)
    # the dome
    for i in range(-46, 47):
        dy = int(16 * math.sqrt(max(0.0, 1 - (i / 46.0) ** 2)))
        rect(cx + i, top - dy, cx + i, top, BRICK if (i + dy) % 5 else BRICK_D)
        px(cx + i, top - dy, BRICK_L)
    # iron tie-rods and bands
    for yy in (top + 6, floor - 12):
        rect(x0 - 2, yy, x1 + 2, yy + 1, MET_D)
    for xx in (x0 - 2, x1 + 1):
        rect(xx, top - 2, xx + 1, floor - 1, MET_D)
    # the box: hot inside, coal bed, fire
    bx0, bx1, by0, by1 = x0 + 8, x1 - 8, top - 4, floor - 7
    rect(bx0, by0, bx1, by1, (60, 22, 14))
    glow(cx, (by0 + by1) / 2, 46, F_MID, 0.5)
    rect(bx0, by1 - 4, bx1, by1, CHAR)
    for _ in range(40):
        px(bx0 + rnd() * (bx1 - bx0), by1 - 4 + rnd() * 4, pick([F_MID, F_HOT, F_COOL]))
    fire_patch(bx0 + 2, by0 + 14, bx1 - 2, by1 - 4, 46, 1.3)
    fire_patch(bx0 + 6, by1 - 14, bx1 - 6, by1 - 4, 30, 0.8)
    # the muffle: a fireclay box standing in the fire, what the furnace is for
    rect(cx - 16, by1 - 26, cx + 16, by1 - 5, (150, 120, 96))
    rect(cx - 13, by1 - 23, cx + 13, by1 - 8, (230, 150, 70))
    rect(cx - 16, by1 - 26, cx + 16, by1 - 26, (196, 170, 140))
    # stoke holes both sides, and the flames that lick out of them
    for side in (-1, 1):
        hx = x0 if side < 0 else x1 - 7
        rect(hx, floor - 26, hx + 7, floor - 8, (60, 22, 14))
        for k in range(16):
            fx = (x0 - 2 - rnd() * 14) if side < 0 else (x1 + 2 + rnd() * 14)
            disc(fx, floor - 12 - rnd() * 14, 1 + rnd() * 2, pick([F_HOT, F_MID, F_COOL]), 0.85)
        glow(x0 - 8 if side < 0 else x1 + 8, floor - 16, 36, F_MID, 0.35)
    # the flue
    fy_top = top - 112
    brick(cx - 9, fy_top, cx + 9, top - 14)
    rect(cx - 3, fy_top, cx + 3, top - 14, (44, 20, 14))
    for yy in range(int(fy_top) + 10, int(top) - 14, 24):
        rect(cx - 11, yy, cx + 11, yy + 1, MET_D)
    glow(cx, fy_top, 22, F_MID, 0.3)
    embers(cx - 30, fy_top - 110, cx + 30, fy_top - 2, 50)
    smoke(cx - 40, fy_top - 120, cx + 40, fy_top - 4, 80)
    return fy_top


def furnace_furnish(ox, oy, m):
    cx = ox + 190
    F = floor_at(m, cx, oy + 330)
    teeth(m, ox + 60, ox + 330, oy + 150, 18)
    rock_blob(ox + 40, oy + 300, 18, 30, rough=0.25)
    rock_blob(ox + 342, oy + 288, 16, 26, rough=0.25)

    fy_top = furnace(cx, F)

    # the timber: four posts off the floor to the charging deck round the flue head
    dy = int(fy_top) + 2
    deck(cx - 56, cx + 56, dy)
    for pxl in (cx - 54, cx - 34, cx + 32, cx + 52):
        beam(pxl, dy + 4, F - 1, 3, WOOD, WOOD_L)
    brace(cx - 52, dy + 6, cx - 34, F - 30)
    brace(cx + 54, dy + 6, cx + 34, F - 30)
    brace(cx - 52, F - 30, cx - 34, dy + 40)
    ladder(cx - 46, dy + 4, F - 1, w=6, step=6, c=WOOD_L, rail=WOOD_D)

    # gangways off the deck up to the rock ledges, west and east
    wl = (ox + 70, floor_at(m, ox + 70, oy + 160))
    el = (ox + 312, floor_at(m, ox + 312, oy + 140))
    ramp(cx - 56, dy, wl[0] + 14, wl[1] - 1)
    ramp(cx + 56, dy, el[0] - 14, el[1] - 1)
    for (x0, y0, x1, y1) in ((cx - 56, dy, wl[0] + 14, wl[1]), (cx + 56, dy, el[0] - 14, el[1])):
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        beam(mx - 1, my + 3, floor_at(m, mx, my + 6) - 1, 2, WOOD, WOOD_L)

    # the headframe over the deck: two legs to a crown beam pinned under the roof, a
    # sheave, and a skip of coal still hanging off it
    roof = ceil_at(m, cx, oy + 120) + 1
    crown = roof + 14
    for lx in (cx - 44, cx + 42):
        line(lx, dy - 1, cx + (lx - cx) * 0.25, crown + 2, WOOD_D)
        line(lx + 1, dy - 1, cx + (lx - cx) * 0.25 + 1, crown + 2, WOOD)
        line(lx + 2, dy - 1, cx + (lx - cx) * 0.25 + 2, crown + 2, WOOD_L)
    rect(cx - 30, crown, cx + 30, crown + 3, WOOD)
    rect(cx - 30, crown, cx + 30, crown, WOOD_L)
    for px_ in (cx - 24, cx + 22):
        beam(px_, roof, crown - 1, 2, WOOD_D, WOOD)
    disc(cx + 14, crown + 8, 5, MET)
    ring(cx + 14, crown + 8, 5, MET_L)
    disc(cx + 14, crown + 8, 1.4, MET_D)
    sy = crown + 74
    line(cx + 19, crown + 8, cx + 19, sy - 6, (150, 130, 96))
    rect(cx + 11, sy - 4, cx + 27, sy + 6, MET)
    rect(cx + 11, sy - 4, cx + 27, sy - 4, MET_XL)
    coal_heap(cx + 12, sy - 3, 15, 4)
    line(cx + 19, sy - 6, cx + 12, sy - 4, (150, 130, 96))
    line(cx + 19, sy - 6, cx + 26, sy - 4, (150, 130, 96))

    # coal: sacks on every deck, a heap by the west stoke hole, a shovel stood in it
    for sx in (cx - 52, cx + 40):
        coal_sack(sx, dy)
    coal_sack(wl[0] - 20, wl[1])
    coal_sack(wl[0] - 32, wl[1])
    coal_sack(el[0] + 12, el[1])
    coal_heap(cx - 96, F, 34, 10)
    line(cx - 80, F - 9, cx - 72, F - 26, WOOD_L)
    rect(cx - 82, F - 10, cx - 78, F - 7, MET)
    for sx in (cx + 92, cx + 104, cx + 98):
        coal_sack(sx, F if sx != cx + 98 else F - 10)
    lamp(ox + 60, ceil_at(m, ox + 60, oy + 160) + 1, drop=5, bulb=LAMP, tint=LAMP, r=50, strength=0.12)
    lamp(ox + 316, ceil_at(m, ox + 316, oy + 140) + 1, drop=5, bulb=LAMP, tint=LAMP, r=50, strength=0.12)

    # stulls under both ledges, and the stock pile of timber for more of all this
    for sx in (ox + 62, ox + 318):
        top = floor_at(m, sx + 1, oy + 150) + 2
        while (sx + 1, top) not in m and top < oy + 380:
            top += 1
        stull(sx, top, floor_at(m, sx + 1, top) - 1)
    lf = floor_at(m, ox + 290, oy + 330)
    for r in range(4):
        for k in range(5 - r):
            lx = ox + 268 + r * 4 + k * 7
            disc(lx + 3, lf - 4 - r * 6, 3, WOOD)
            ring(lx + 3, lf - 4 - r * 6, 3, WOOD_D)
            px(lx + 3, lf - 4 - r * 6, WOOD_L)
    stand("Pyro", cx + 20, dy, flip=True)
    stand("WizDeepminer", cx - 30, dy)
    stand("Grenadier", el[0] - 2, el[1], flip=True)
    stand("BloodMage", wl[0] + 2, wl[1])
    stand("Gaper", cx - 118, floor_at(m, cx - 118, oy + 330))
    stand("RiotBrute", cx + 74, F, flip=True)


ROOM = {
    "name": "THE FURNACE", "w": 380, "h": 400,
    "shapes": [([("blob", 190, 300, 156, 82),                  # the furnace hall
                 ("blob", 200, 150, 120, 96)], 0.1),            # the flue space
               ([("blob", 52, 168, 46, 22),                     # west ledge pocket
                 ("blob", 330, 150, 44, 22)], 0.14)],           # east ledge pocket
    "sockets": {"T1": ("T", 140, 70), "T2": ("T", 262, 62),
                "L1": ("L", 340, 40), "R1": ("R", 340, 40),
                "L2": ("L", 188, 14), "R2": ("R", 170, 14)},
    "furnish": furnace_furnish,
}


SHEET = {
    "seed": 71101,
    "callouts": [
        ("1 MUFFLE FURNACE, ALWAYS LIT", (-120, 418), (150, 350)),
        ("2 CHARGING DECK ON DRY POSTS", (-120, -50), (140, 222)),
        ("3 A SKIP OF COAL OVER THE FLUE", (230, 418), (217, 162)),
    ],
    "beats": [
        ("A FIRE THAT NEVER GOES OUT UNDER A ROOM OF TIMBER", (170, 180, 195)),
        ("PYRO ON THE DECK, BRUTE BY THE STOKE HOLE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
