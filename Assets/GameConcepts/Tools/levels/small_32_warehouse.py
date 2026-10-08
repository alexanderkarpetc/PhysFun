"""Small room S32 - THE WAREHOUSE.

A store cut into the rock under a vault that is high in the west and comes down low in
the east, and filled with it: five tall timber racks in a row, each shelf loaded with
crates, sacks and kegs on pallets, more stacked on top. The racks get shorter as the roof
comes down. The westmost has lost a foot and leans on the next one already. The crew
stand in the aisles between them. Knock a rack over and its load avalanches into the
next, and that one goes too, east, down the row, onto whoever is in the aisles.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S32"

FLOOR = 290
RACK_W = 38
RACKS = ((128, 132), (196, 116), (264, 98), (332, 80))   # upright racks: left x, height
LEAN = (60, 136)                                           # the leaning one: left x, height
SACK = (148, 128, 92)
SACK_L = (178, 158, 116)
SACK_D = (108, 92, 66)
LEDGE_Y = 168


def ware_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def sack(x, floor, w=10):
    rect(x + 1, floor - 7, x + w - 1, floor - 1, SACK)
    rect(x, floor - 5, x + w, floor - 2, SACK)
    rect(x + 1, floor - 7, x + w - 1, floor - 7, SACK_L)
    rect(x + 1, floor - 1, x + w - 1, floor - 1, SACK_D)
    rect(x + w // 2 - 1, floor - 9, x + w // 2 + 1, floor - 8, SACK_D)   # the tie
    px(x + 2, floor - 5, SACK_L)


def pallet(x0, x1, floor):
    rect(x0, floor - 3, x1, floor - 3, WOOD)
    for bx in (x0, (x0 + x1) // 2 - 1, x1 - 2):
        rect(bx, floor - 2, bx + 2, floor - 1, WOOD_D)


def load(x0, x1, floor, kind, slid=0):
    """One bay of a shelf: a pallet and what is on it. `slid` shoves it east (the
    leaning rack's loads have gone to the low end)."""
    x0 += slid
    x1 = min(x1, x1 + slid)
    pallet(x0, x1, floor)
    f = floor - 3
    if kind == 0:                                  # crates, two high
        crate_g(x0 + 1, f, 11)
        crate_g(x0 + 13, f, 11)
        crate_g(x0 + 6, f - 12, 10)
    elif kind == 1:                                # sacks, piled
        sack(x0 + 1, f)
        sack(x0 + 11, f)
        sack(x0 + 21, f, 9)
        sack(x0 + 6, f - 7)
        sack(x0 + 16, f - 7, 9)
    elif kind == 2:                                # kegs
        keg(x0 + 1, f)
        keg(x0 + 11, f)
        keg(x0 + 21, f)
        keg(x0 + 6, f - 11)
    else:                                          # mixed
        crate_g(x0 + 1, f, 12)
        sack(x0 + 15, f)
        keg(x0 + 26, f)


def rack(x, base, h, kinds, top_kind=None, slid=0, w=RACK_W):
    """A timber rack side-on: two uprights, shelves, cross braces, a load on each shelf."""
    n = len(kinds)
    step = h // n
    for k in range(n):                              # braces first, behind everything
        y0, y1 = base - k * step, base - (k + 1) * step
        line(x + 3, y0 - 1, x + w - 3, y1 + 3, (66, 50, 35))
    for ux in (x, x + w - 3):
        rect(ux, base - h, ux + 3, base - 1, WOOD)
        rect(ux, base - h, ux, base - 1, WOOD_L)
        rect(ux + 3, base - h, ux + 3, base - 1, WOOD_D)
    for k in range(n):
        sy = base - k * step
        if k:
            rect(x - 1, sy - 2, x + w + 1, sy, WOOD)
            rect(x - 1, sy - 2, x + w + 1, sy - 2, WOOD_L)
            rect(x - 1, sy, x + w + 1, sy, WOOD_D)
            load(x + 3, x + w - 4, sy - 2, kinds[k], slid)
        else:
            load(x + 3, x + w - 4, sy, kinds[k], slid)
    rect(x - 1, base - h - 2, x + w + 1, base - h, WOOD)
    rect(x - 1, base - h - 2, x + w + 1, base - h - 2, WOOD_L)
    if top_kind is not None:
        load(x + 1, x + w - 2, base - h - 2, top_kind, slid)


def slanted_ladder(x0, y0, x1, y1, w=6, step=6):
    """The ladder trolley: two rails on a slant, rungs between, hooks at the top and
    wheels at the foot."""
    ln = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / ln * w, (x1 - x0) / ln * w
    line(x0, y0, x1, y1, MET_D)
    line(x0 + nx, y0 + ny, x1 + nx, y1 + ny, MET_D)
    k = step
    while k < ln - 2:
        t = k / ln
        ax, ay = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        line(ax, ay, ax + nx, ay + ny, MET_L)
        k += step
    for (hx, hy) in ((x0, y0), (x0 + nx, y0 + ny)):
        rect(hx - 1, hy - 3, hx + 1, hy - 3, MET_XL)        # hook over the rail
        px(hx - 1, hy - 2, MET_XL)
    for (wx, wy) in ((x1, y1), (x1 + nx, y1 + ny)):
        disc(wx, wy - 2, 2, INK)
        px(wx, wy - 2, MET_L)


def ware_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fy = Y(FLOOR) + 1

    teeth(m, X(30), X(250), Y(140), 18)
    teeth(m, X(250), X(430), Y(200), 10)
    # the west shelf of rock, a perch over the leaning rack
    x0 = X(0)
    while (x0, Y(LEDGE_Y)) not in m:
        x0 += 1
    rock_blob(x0 + 8, Y(LEDGE_Y) + 7, 30, 8, rough=0.18)
    for (bx, by, rx, ry, d) in ((440, 250, 12, 9, 1), (20, 270, 10, 8, -1)):
        xx = X(bx)
        while (xx, Y(by)) in m:
            xx += d
        rock_blob(xx - d * 3, Y(by), rx, ry, rough=0.25)

    # the leaning rack: drawn upright on its own canvas, pivoted on its east foot
    lx0, lh = LEAN
    cw, ch = RACK_W + 8, lh + 30
    pivot_local = (RACK_W + 3, ch - 2)
    ang = math.asin((RACKS[0][0] - 1 - (lx0 + RACK_W)) / float(lh))
    sa, ca = math.sin(ang), math.cos(ang)
    dx, dy = pivot_local[0] - cw / 2, pivot_local[1] - ch / 2
    px_w, py_w = X(lx0 + RACK_W), fy - 1
    cx = px_w - (ca * dx - sa * dy)
    cy = py_w - (sa * dx + ca * dy)
    draw_rotated(cw, ch, lambda: rack(4, ch - 2, lh, (3, 1, 0, 2), top_kind=None, slid=3),
                 cx, cy, ang)
    # a wedge of rubble where the west foot gave way, and what already came off it
    for k in range(10):
        px(X(lx0 + k), fy - 1 - (k % 2), pick([DIRT, ROCK_M, WOOD_D]))
    crate_g(X(104), fy, 11)
    sack(X(116), fy)
    sack(X(110), fy - 12, 9)
    for k in range(5):
        px(X(103 + k * 3), fy - 14 - k * 4, DIRT_L, 0.6)

    # the upright racks, getting shorter under the roof
    kinds = ((0, 1, 2, 0), (1, 3, 0), (2, 0, 1), (3, 1))
    tops = (1, 3, 2, 0)
    for i, ((rx, rh), ks) in enumerate(zip(RACKS, kinds)):
        rack(X(rx), fy, rh, ks, top_kind=tops[i])

    # the ladder trolley: a rail along the rack fronts and a ladder hooked on it
    ry = fy - 106
    rect(X(RACKS[1][0] - 2), ry, X(RACKS[2][0] + RACK_W + 2), ry + 1, MET_D)
    rect(X(RACKS[1][0] - 2), ry, X(RACKS[2][0] + RACK_W + 2), ry, MET_L)
    slanted_ladder(X(246), ry + 3, X(232), fy - 1)
    stand("WizGoldhood", X(244), fy - 52)

    # the crew in the aisles
    stand("Gaper", X(112), fy)
    stand("Pyro", X(181), fy, flip=True)
    stand("RiotBrute", X(316), fy, flip=True)
    stand("Gaper", X(390), fy, flip=True)
    stand("WizHollowhood", X(420), fy, flip=True)
    stand("Grenadier", X(x0 - ox + 14), Y(LEDGE_Y) + 1)
    stand("Reaper", X(RACKS[3][0] + 18), fy - RACKS[3][1] - 2 - 3 - 22, flip=True)

    # a cargo net still on the hoist chain over the aisles, and a bare hook
    nx, ny = X(249), Y(124)
    chain(nx, ceil_at(m, nx, ny) + 1, ny - 4)
    rect(nx - 2, ny - 5, nx + 2, ny - 4, MET_L)
    line(nx, ny - 4, nx - 13, ny + 4, MET_D)
    line(nx, ny - 4, nx + 13, ny + 4, MET_D)
    sack(nx - 13, ny + 13)
    sack(nx - 3, ny + 13)
    sack(nx + 5, ny + 13, 9)
    sack(nx - 8, ny + 6)
    crate_g(nx - 4, ny + 26, 9)
    for k in range(-14, 15, 3):
        px(nx + k, ny + 4 + abs(k) // 5, MET_D)
        px(nx + k, ny + 26, MET_D)
    for k in range(4, 26, 3):
        px(nx - 14, ny + k, MET_D)
        px(nx + 14, ny + k, MET_D)
    hx = X(160)
    chain(hx, ceil_at(m, hx, Y(130)) + 1, Y(128))
    line(hx, Y(128), hx, Y(133), MET_L)
    line(hx, Y(133), hx + 3, Y(131), MET_L)

    # odds and ends on the floor east, where the row ends
    sack(X(372), fy)
    crate_g(X(404), fy, 10)
    keg(X(436), fy)
    for lx in (84, 226, 392):
        lamp(X(lx), ceil_at(m, X(lx), Y(200)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=70, strength=0.14)


ROOM = {
    "name": "THE WAREHOUSE", "w": 460, "h": 340,
    "shapes": [([("blob", 156, 206, 144, 126),            # the high west vault
                 ("blob", 330, 240, 112, 72)], 0.08),     # the low east bay
               ([("blob", 372, 176, 34, 24)], 0.12)],     # a pocket in the east roof
    "sockets": {"T1": ("T", 110, 90), "T2": ("T", 196, 98),
                "L1": ("L", FLOOR, 40), "R1": ("R", FLOOR, 34),
                "L2": ("L", LEDGE_Y, 10)},
    "edit": ware_edit,
    "furnish": ware_furnish,
}


SHEET = {
    "seed": 73201,
    "callouts": [
        ("1 ALREADY LEANING", (-120, 40), (100, 160)),
        ("2 EACH STACK FALLS ON THE NEXT", (180, 352), (230, 200)),
        ("3 LADDER TROLLEY", (-120, 352), (240, 240)),
    ],
    "beats": [
        ("KNOCK THE FIRST RACK: THE ROW GOES EAST, ONE INTO THE NEXT", (170, 180, 195)),
        ("THE CREW STAND IN THE AISLES, THE PYRO NEXT TO THE KEGS", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
