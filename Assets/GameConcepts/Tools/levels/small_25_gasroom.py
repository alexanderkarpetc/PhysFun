"""Small room S25 - THE GAS ROOM.

The assay bay: a low vault with a bottle store stepped down off its west end, a fume
hood over the bench in the east, and a copper manifold slung under the roof feeding
gauges, benches and racks. The racks are the room: tall steel gas bottles stood upright
in timber frames, chained in, one rack in the store and one free-standing in the middle
of the floor. Shoot a bottle's valve off and it goes like a rocket - across the room,
through whoever is in the way, and nose-first into the far wall, like the one already
sticking out of the east rock.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S25"

FLOOR = 226                     # the bay
STORE = 238                     # the bottle store, a step down in the west
NOOK = 106                      # the high nook in the east
MANIFOLD = 118
BOTTLES = ((70, 84, 96), (110, 58, 50), (128, 112, 60), (78, 96, 70), (90, 90, 98))


def gas_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if lx < 98:
            f = STORE
        elif lx > 318 and ly < 130:
            f = NOOK + 2 * math.sin(lx * 0.3)
        else:
            f = FLOOR + 2 * math.sin(lx * 0.06)
        if ly < f:
            out.add((x, y))
    return out


def bottle(cx, floor, h=34, c=(70, 84, 96), valve=True):
    """A tall gas bottle stood upright: body with a lit edge, a domed shoulder, a pale
    stencil band, the brass valve and its guard on top."""
    top = floor - h
    rect(cx - 3, top + 4, cx + 3, floor - 1, c)
    rect(cx - 3, top + 4, cx - 3, floor - 1, tuple(min(255, v + 34) for v in c))
    rect(cx + 3, top + 4, cx + 3, floor - 1, tuple(int(v * 0.65) for v in c))
    rect(cx - 2, top + 2, cx + 2, top + 3, c)
    rect(cx - 1, top + 1, cx + 1, top + 1, c)
    rect(cx - 3, top + 10, cx + 3, top + 11, (176, 170, 150))
    rect(cx - 3, floor - 2, cx + 3, floor - 1, MET_D)
    if valve:
        rect(cx - 1, top - 2, cx + 1, top, COPPER_L)
        px(cx + 2, top - 1, COPPER)
        rect(cx - 2, top - 4, cx + 2, top - 3, MET_D)                 # guard ring


def bottle_local(c=BOTTLES[1]):
    """One bottle on its side for draw_rotated, nose (valve end) at +x, 40x10."""
    rect(2, 2, 34, 8, c)
    rect(2, 2, 34, 2, tuple(min(255, v + 34) for v in c))
    rect(2, 8, 34, 8, tuple(int(v * 0.65) for v in c))
    rect(35, 3, 36, 7, c)
    rect(26, 2, 27, 8, (176, 170, 150))
    rect(37, 4, 38, 6, MET_D)                                       # sheared valve stub


def rack(x0, x1, floor, n, colors, h=34, top_extra=6):
    """A timber rack: posts at each end, a top rail, a chain band across the bottles."""
    for k in range(n):
        bottle(x0 + 6 + k * 9, floor, h, colors[k % len(colors)])
    rt = floor - h - top_extra
    for x in (x0, x1):
        beam(x, rt, floor - 1, 2, WOOD, WOOD_L)
    rect(x0, rt, x1 + 2, rt + 2, WOOD)
    rect(x0, rt, x1 + 2, rt, WOOD_L)
    rect(x0, floor - 3, x1 + 2, floor - 1, WOOD_D)
    for x in range(x0 + 2, x1, 2):                                  # the chain band
        px(x, floor - h + 14, MET_L if x % 4 else MET_D)


def gauge(x, y, r=4, needle=0.6):
    disc(x, y, r, MET_D)
    disc(x, y, r - 1, (200, 196, 180))
    line(x, y, x + math.cos(needle - math.pi / 2) * (r - 1.5), y + math.sin(needle - math.pi / 2) * (r - 1.5), RED)
    px(x, y, INK)


def pipe_h(x0, x1, y, c=COPPER, lit=COPPER_L):
    rect(x0, y, x1, y + 2, c)
    rect(x0, y, x1, y, lit)


def pipe_v(x, y0, y1, c=COPPER, lit=COPPER_L):
    rect(x, y0, x + 2, y1, c)
    rect(x, y0, x, y1, lit)


def bench(x0, x1, floor, top_h=14):
    t = floor - top_h
    rect(x0, t, x1, t + 2, WOOD)
    rect(x0, t, x1, t, WOOD_L)
    for x in (x0 + 2, x1 - 4):
        rect(x, t + 3, x + 2, floor - 1, WOOD_D)
    rect(x0 + 3, floor - 5, x1 - 3, floor - 4, WOOD_D)              # a shelf under
    return t


def gas_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly=FLOOR - 20: floor_at(m, X(lx), Y(ly))

    teeth(m, X(40), X(320), Y(70), 22)
    for x, y, d, rx, ry in ((10, 150, -1, 12, 9), (370, 180, 1, 12, 10)):
        x0 = ox + x
        while (x0, oy + y) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), oy + y, rx, ry, rough=0.25)

    # the manifold under the roof: a copper header on rods, drops to every rack and bench
    my = Y(MANIFOLD)
    pipe_h(X(30), X(296), my)
    for x in range(44, 296, 42):
        top = ceil_at(m, X(x), my - 4) + 1
        line(X(x), top, X(x), my - 1, MET_D)
    for x, to, g in ((56, STORE - 40, 0.9), (170, fl(170) - oy - 42, -0.4), (246, fl(240) - oy - 14, 1.4)):
        pipe_v(X(x), my + 3, Y(to) - 1)
        gauge(X(x) + 1, my + 12, 4, g)
        rect(X(x) - 2, Y(to) - 3, X(x) + 4, Y(to) - 1, MET_D)       # the regulator at the foot
    for x in (100, 210):                                           # big dials on the header
        gauge(X(x), my - 6, 6, 0.3 + x * 0.01)
        rect(X(x) - 1, my - 1, X(x) + 1, my, MET_D)
    valve(X(132), my + 1, 3)

    # the store: a long rack, stepped down
    sf = Y(STORE)
    rack(X(18), X(86), sf, 7, BOTTLES)
    stand("WizHollowhood", X(80) + 14, fl(94, STORE - 30), flip=True)

    # the free-standing rack in the middle of the bay, back to back
    ff = fl(170)
    rack(X(144), X(194), ff, 5, BOTTLES[2:] + BOTTLES[:2], h=36)
    stand("Sentinel", X(118), fl(118))
    stand("Gaper", X(212), fl(212), flip=True)

    # benches: assay crucibles, ore samples, a burner under the fume hood
    bt = bench(X(228), X(270), fl(240))
    for k in range(4):
        rect(X(232) + k * 6, bt - 4, X(235) + k * 6, bt - 1, (150, 140, 120))
        rect(X(232) + k * 6, bt - 4, X(235) + k * 6, bt - 4, (190, 182, 160))
    for k in range(3):
        disc(X(256) + k * 4, bt - 2, 1.6, pick([ORE, ROCK_L, DIRT_L]))
    hb = bench(X(286), X(326), fl(300))
    disc(X(306), hb - 3, 3, MET_D)                                  # the burner
    glow(X(306), hb - 5, 14, F_MID, 0.25)
    for k in range(3):
        px(X(305) + k, hb - 6 - k, pick([F_HOT, F_MID]))
    ht = hb - 34                                                    # the hood: a sloped steel canopy
    for i in range(10):
        rect(X(284) + i, ht + i, X(328) - i // 2, ht + i, MET if i else MET_L)
    rect(X(284), ht + 9, X(326), ht + 10, MET_D)
    duct_top = ceil_at(m, X(306), ht - 2) + 1
    rect(X(302), duct_top, X(310), ht, MET)
    rect(X(302), duct_top, X(302), ht, MET_L)
    rect(X(310), duct_top, X(310), ht, MET_D)
    for y in range(duct_top + 6, ht, 10):
        rect(X(302), y, X(310), y, MET_D)
    stand("WizGoldhood", X(298), fl(298), flip=True)

    # a bottle trolley by the east wall, and the one that already went
    tf = fl(346)
    rect(X(336), tf - 4, X(362), tf - 3, MET_D)
    for wx in (340, 358):
        disc(X(wx), tf - 2, 2, INK)
        px(X(wx), tf - 2, MET_L)
    for k in range(2):
        draw_rotated(40, 10, lambda k=k: bottle_local(BOTTLES[3 + k]), X(349), tf - 8 - k * 7, 0.0 if k else math.pi)
    stand("Pyro", X(276), fl(276), flip=True)

    nk = Y(NOOK)
    stand("BloodMage", X(352), nk, flip=True)
    crate_g(X(330), nk, 10)

    # the one that went: nose-first in the east wall over the bench, cracks round it
    wy = Y(160)
    wx = X(330)
    while (wx, wy) in m:
        wx += 1
    draw_rotated(40, 10, bottle_local, wx - 12, wy + 2, -0.22)
    for a, ln in ((0.5, 8), (-0.6, 7), (2.4, 6), (-2.2, 6), (1.4, 5)):
        x, y = wx + 6, wy
        for i in range(ln):
            x += math.cos(a + math.sin(i) * 0.4)
            y += math.sin(a + math.sin(i) * 0.4)
            px(x, y, INK)
    for _ in range(10):
        px(wx - 2 - rnd() * 14, wy + 6 + rnd() * 50 * rnd(), pick([ROCK_L, ROCK_M]), 0.8)

    # a sling of three bottles on a hoist chain, on its way to the racks
    top = ceil_at(m, X(206), Y(90)) + 1
    chain(X(206), top, Y(150))
    for k in range(3):
        draw_rotated(40, 10, lambda k=k: bottle_local(BOTTLES[(k * 2) % 5]), X(206), Y(156) + k * 7,
                     math.pi if k % 2 else 0.0)
    for sx in (190, 222):
        line(X(206), Y(150), X(sx), Y(154), MET_L)
    for x in (120, 250):
        lamp(X(x), my + 3, drop=10, bulb=LAMP, tint=LAMP, r=70, strength=0.14)
    lamp(X(40), ceil_at(m, X(40), Y(170)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.12)
    for k in range(3):                                              # spare valve caps on the store floor
        rect(X(92) + k * 4, sf - 2, X(93) + k * 4, sf - 1, COPPER)


ROOM = {
    "name": "THE GAS ROOM", "w": 380, "h": 300,
    "shapes": [([("blob", 196, 150, 172, 92)], 0.07),
               ([("blob", 54, 186, 50, 50),                    # the bottle store, stepped down
                 ("blob", 344, 92, 32, 22)], 0.1)],            # the high nook, east
    "sockets": {"T1": ("T", 120, 76), "T2": ("T", 250, 76),
                "L1": ("L", STORE, 24), "R1": ("R", FLOOR, 30),
                "R2": ("R", NOOK, 22)},
    "edit": gas_edit,
    "furnish": gas_furnish,
}


SHEET = {
    "seed": 72501,
    "callouts": [
        ("1 RACKS OF TALL GAS BOTTLES", (-122, 290), (150, 200)),
        ("2 SHOOT A VALVE: IT GOES LIKE A ROCKET", (60, 320), (338, 164)),
        ("3 MANIFOLD AND GAUGES", (220, -48), (210, 112)),
    ],
    "beats": [
        ("A BOTTLE WITH ITS VALVE SHOT OFF FLIES THE ROOM AND HITS WHAT IS THERE", (170, 180, 195)),
        ("THE PYRO AT THE BENCH IS ONE STRAY SHOT FROM SETTING THE RACKS OFF", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
