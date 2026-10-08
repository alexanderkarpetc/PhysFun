"""Small room S39 - THE TRENCH.

A wide, low cave with earth for a floor, and a dug-in position across it: two trench
lines, timber-revetted, sandbag parapets with firing slits on their west lips, a timber
barricade and wire out in front. RiotBrutes hold the parapets, Grenadiers lob from
behind them, and the rear line has a dugout with the powder in it. You come in from the
west across the open, or along the sap - a timbered crawl under it that comes up between
the two lines. The cover is the toy: the walls are earth held up by boards, so shoot the
revetment out and the trench wall slumps in on whoever is in it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S39"

BAG = (122, 108, 78)
BAG_L = (156, 140, 104)
BAG_D = (84, 74, 54)
EARTH = (74, 62, 46)
WIRE = (120, 118, 112)

T1 = (190, 226)                  # trench lines: west and east wall x
T2 = (338, 374)
DEPTH = 32
STEP = 12                        # fire step height off the trench floor
DUG = (374, 404)                 # dugout in T2's rear wall
CRAWL = [(-8, 226), (60, 230), (170, 236), (240, 232), (264, 214), (272, 182)]
_crawl = {}


def ground(lx):
    t = min(1.0, max(0.0, (lx - 250) / 90.0))
    g = 174 - 12 * t * t * (3 - 2 * t) + 2 * math.sin(lx * 0.07)
    for cx, r, d in ((86, 16, 7), (150, 11, 5), (296, 10, 4)):        # shell holes
        if abs(lx - cx) < r:
            g += d * math.cos((lx - cx) / r * math.pi / 2)
    return g


def in_trench(lx, ly):
    for x0, x1 in (T1, T2):
        if x0 <= lx <= x1 and ly <= ground((x0 + x1) / 2) + DEPTH:
            return True
    return DUG[0] <= lx <= DUG[1] and ground(355) + DEPTH - 24 <= ly <= ground(355) + DEPTH


def trench_edit(air, ox, oy):
    if (ox, oy) not in _crawl:
        _crawl[(ox, oy)] = cave_mask([("tube", [(x + ox, y + oy) for x, y in CRAWL], 11)],
                                     rough=0.04, top=0)
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly <= ground(lx) or in_trench(lx, ly):
            out.add((x, y))
    out |= {p for p in _crawl[(ox, oy)] if 0 <= p[0] - ox < 460}
    return out


def sandbags(x0, x1, base, rows, slit=None):
    """Sandbags laid in courses, rounded ends, a slit left in one course."""
    for r in range(rows):
        y = base - 4 * (r + 1)
        off = 0 if r % 2 else 4
        for x in range(int(x0) - off, int(x1), 8):
            if slit and r == slit[0] and slit[1] <= x <= slit[2]:
                continue
            xa, xb = max(x, int(x0)), min(x + 7, int(x1))
            if xb - xa < 2:
                continue
            rect(xa, y, xb, y + 3, BAG)
            rect(xa + 1, y, xb - 1, y, BAG_L)
            rect(xa, y + 3, xb, y + 3, BAG_D)
            px(xa, y, BAG_D)
            px(xb, y, BAG_D)
            px((xa + xb) // 2, y + 1, BAG_D)


def revet(x, y0, y1, side):
    """Boards on a trench wall: posts every 10px and planks between, 3px into the earth.
    `side` -1 = the wall west of the trench (boards on its east face)."""
    xs = (x - 3, x - 1) if side < 0 else (x + 1, x + 3)
    for y in range(int(y0), int(y1) + 1):
        rect(xs[0], y, xs[1], y, WOOD if (y - int(y0)) % 4 else WOOD_D)
    for y in range(int(y0), int(y1), 10):
        rect(xs[0], y, xs[1], y + 1, WOOD_L)
    post = xs[1] if side < 0 else xs[0]
    rect(post, y0 - 3, post, y1, WOOD_D)


def trench(x0, x1, ox, oy, m, collapsed=False):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    g = ground((x0 + x1) / 2)
    floor = int(Y(g + DEPTH)) + 1
    gw, ge = Y(ground(x0)), Y(ground(x1))
    for x in range(X(x0), X(x1) + 1):                    # duckboards
        px(x, floor - 1, WOOD if x % 5 else WOOD_D)
    if not collapsed:
        revet(X(x0), gw, floor - 1, -1)
    revet(X(x1), ge, floor - 1, 1)
    rect(X(x0), floor - STEP, X(x0) + 8, floor - 1, WOOD_D)       # fire step
    rect(X(x0), floor - STEP, X(x0) + 8, floor - STEP, WOOD_L)
    if not collapsed:
        sandbags(X(x0) - 22, X(x0) + 5, gw, 5, slit=(2, X(x0) - 12, X(x0) - 4))
        rect(X(x0) - 22, gw - 13, X(x0) + 5, gw - 13, WOOD)      # lintel over the slit
    sandbags(X(x1) - 2, X(x1) + 16, ge, 2)                       # parados, behind
    return floor


def stake(x, base):
    rect(x, base - 9, x, base - 1, WOOD_D)
    px(x, base - 10, WOOD)


def wire(x0, x1, base, m):
    xs = list(range(int(x0), int(x1) + 1, 14))
    for x in xs:
        stake(x, floor_at(m, x, base - 20))
    for a, b in zip(xs, xs[1:]):
        fa, fb = floor_at(m, a, base - 20), floor_at(m, b, base - 20)
        for k in (4, 8):
            for i in range(b - a + 1):
                y = fa - k + (fb - fa) * i / (b - a) + 1.5 * math.sin(i * 0.9)
                if i % 3:
                    px(a + i, y, WIRE)
                else:
                    px(a + i, y, MET_XL)


def barricade(x, base):
    """Timber barricade: logs between two posts, a slit between the top two, on a
    footing of sandbags."""
    sandbags(x - 6, x + 26, base, 2)
    b = base - 8
    for k in range(5):
        y = b - 4 * (k + 1)
        if k == 3:
            rect(x - 2, y, x + 22, y + 3, (20, 22, 26))  # the slit
            continue
        rect(x - 2, y, x + 22, y + 3, WOOD)
        rect(x - 2, y, x + 22, y, WOOD_L)
        rect(x - 2, y + 3, x + 22, y + 3, WOOD_D)
        disc(x - 2, y + 1.5, 1.8, WOOD_D)
        px(x - 2, y + 1, WOOD_L)
    for px_ in (x + 2, x + 17):
        rect(px_, b - 22, px_ + 1, b, WOOD_D)


def trench_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    cw, ch = canvas_size()

    # the ground is earth: a band of it down from the surface, coarser deeper
    for lx in range(0, 460):
        g = int(ground(lx))
        for ly in range(g + 1, g + 46):
            p = (X(lx), Y(ly))
            if p in m:
                continue
            d = ly - g
            if d > 30 and rnd() < (d - 30) / 16.0:
                continue
            r = rnd()
            px(p[0], p[1], DIRT_D if r < 0.25 else EARTH if r < 0.7 else DIRT)
        if Y(g) + 1 < ch and (X(lx), Y(g)) in m:
            px(X(lx), Y(g) + 1, DIRT_L if lx % 3 else DIRT)

    teeth(m, X(20), X(450), Y(134), 34)
    for lx, drop in ((120, 10), (240, 16), (330, 14), (420, 8)):
        lamp(X(lx), ceil_at(m, X(lx), Y(134)) + 1, drop=drop, bulb=LAMP, tint=LAMP, r=60, strength=0.14)

    # the sap: timber sets every 18px along it
    for i in range(len(CRAWL) - 1):
        (ax, ay), (bx, by) = CRAWL[i], CRAWL[i + 1]
        n = int(math.hypot(bx - ax, by - ay) / 40)
        for k in range(1, n + 1):
            t = k / (n + 1)
            cx, cy = X(ax + (bx - ax) * t), Y(ay + (by - ay) * t)
            if not (X(4) < cx < X(456)):
                continue
            top = ceil_at(m, cx, cy) + 1
            bot = floor_at(m, cx, cy) - 1
            if bot - top > 30:
                continue
            rect(cx - 7, top, cx + 7, top + 1, WOOD)
            rect(cx - 6, top + 2, cx - 5, bot, WOOD_D)
            rect(cx - 7, bot - 1, cx + 7, bot, WOOD_D)
    lamp(X(150), ceil_at(m, X(150), Y(244)) + 1, drop=2, bulb=LAMP, tint=LAMP, r=26, strength=0.12)

    # the two lines
    f1 = trench(T1[0], T1[1], ox, oy, m)
    f2 = trench(T2[0], T2[1], ox, oy, m, collapsed=True)
    # T2's west wall has already been shot out: boards snapped, the earth slumped in
    gw = int(Y(ground(T2[0])))
    for lx in range(T2[0] - 6, T2[0] + 18):
        top = int(gw + 4 + max(0, lx - T2[0]) * 0.9 + rnd() * 2)
        for y in range(top, f2):
            if (X(lx), y) in m:
                px(X(lx), y, pick([EARTH, DIRT, DIRT_D, DIRT]))
    for k, (dx, dy, l) in enumerate(((2, 6, 10), (8, 14, 8), (12, 10, 9))):
        line(X(T2[0] + dx), gw + dy, X(T2[0] + dx + l), gw + dy + 5 - k * 3, WOOD)
    for k in range(5):                                    # bags rolled down into it
        bx = X(T2[0] - 10 + k * 6)
        by = floor_at(m, bx, gw - 8) - 3
        rect(bx, by, bx + 5, by + 2, BAG)
        rect(bx, by, bx + 5, by, BAG_L)
    rect(X(T2[0] + 12), f2 - 4, X(T2[0] + 16), f2 - 1, (60, 60, 64))   # a boot out of it
    for k in range(6):
        px(X(T2[0] + 6 + k * 2), f2 - 1, RED, 0.7)

    # the dugout off T2, framed, with the powder in it
    dtop = int(Y(ground(355) + DEPTH - 24))
    rect(X(DUG[0]) + 1, dtop - 1, X(DUG[1]), dtop, WOOD)
    for dx in (DUG[0] + 3, DUG[1] - 2):
        rect(X(dx), dtop + 1, X(dx) + 1, f2 - 1, WOOD_D)
    keg(X(384), f2)
    keg(X(388), f2 - 11)
    keg(X(392), f2)
    lamp(X(380), dtop + 1, drop=2, bulb=LAMP, tint=LAMP, r=24, strength=0.14)

    # out front: wire, a barricade, the shell holes
    wire(X(140), X(186), Y(174), m)
    barricade(X(110), floor_at(m, X(116), Y(140)))
    barricade(X(282), floor_at(m, X(288), Y(140)))
    corpse(X(92), floor_at(m, X(92), Y(140)))
    corpse(X(168), floor_at(m, X(168), Y(140)))

    # who holds it
    stand("RiotBrute", X(T1[0] + 4), f1 - STEP, flip=True)
    stand("Grenadier", X(T1[1] - 6), f1, flip=True)
    stand("Grenadier", X(T2[0] + 4), f2 - STEP, flip=True)
    stand("RiotBrute", X(T2[1] - 8), f2, flip=True)
    stand("WizDeepminer", X(298), floor_at(m, X(298), Y(140)), flip=True)   # behind the barricade
    stand("RiotBrute", X(428), floor_at(m, X(428), Y(140)), flip=True)
    crate_g(X(440), floor_at(m, X(440), Y(140)), 10)
    sandbags(X(410), X(436), floor_at(m, X(420), Y(140)), 2)
    # field cables strung under the roof, lamps on them
    for (a, b) in ((40, 200), (200, 330), (330, 440)):
        ya, yb = ceil_at(m, X(a), Y(134)) + 2, ceil_at(m, X(b), Y(134)) + 2
        cable(X(a), ya, X(b), yb, sag=14, c=MET_D)
    # a spotter's perch: planks on two brackets off the east wall, over the dugout
    py = Y(116)
    ex = X(456)
    while (ex, py - 4) not in m:
        ex -= 1
    rect(ex - 30, py, ex + 2, py + 2, WOOD)
    rect(ex - 30, py, ex + 2, py, WOOD_L)
    for bx in (ex - 26, ex - 6):
        line(bx, py + 3, bx + 8, py + 14, WOOD_D)
    stand("Grenadier", ex - 16, py, flip=True)


ROOM = {
    "name": "THE TRENCH", "w": 460, "h": 300,
    "shapes": [([("blob", 230, 164, 226, 66),
                 ("blob", 112, 100, 28, 22),             # roof pockets for the top ways
                 ("blob", 352, 98, 28, 24)], 0.07)],
    "sockets": {"T1": ("T", 112, 86), "T2": ("T", 352, 80),
                "L1": ("L", 174, 12), "L2": ("L", 237, 8),
                "R1": ("R", 162, 14)},
    "edit": trench_edit,
    "furnish": trench_furnish,
}


SHEET = {
    "seed": 73901,
    "callouts": [
        ("1 REVETTED TRENCH, SANDBAG PARAPET", (150, -50), (186, 164)),
        ("2 SHOOT THE BOARDS, THE WALL COMES IN", (230, 320), (348, 196)),
        ("3 THE SAP: A CRAWL UNDER IT", (-125, 320), (150, 234)),
    ],
    "beats": [
        ("THE COVER IS EARTH ON BOARDS: TAKE THE BOARDS, BURY THE LINE", (170, 180, 195)),
        ("BRUTES ON THE PARAPETS, GRENADIERS BEHIND, POWDER IN THE DUGOUT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
