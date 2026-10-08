"""Small room S31 - THE PATERNOSTER.

A tall shaft with a paternoster lift in it: an endless loop of open timber cars on one
chain, going up the west side, over a sprocket under the roof and down the east side,
round a second sprocket in the drive pit at the bottom. It never stops. Landings come off
the shaft at odd heights on both sides, so you step on, ride, and step off where you like.
The roof over the top sprocket is low and toothed: whatever is standing on a car when it
goes over the top is pressed into it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S31"

CX = 170                       # loop centre line
TOP_Y, BOT_Y, R = 98, 378, 28  # sprocket centres and radius (the chain runs on R)
UP_X, DN_X = CX - R, CX + R    # the up run (west) and the down run (east)
CAR_W = 24
UP_DECKS = (136, 178, 220, 262, 304, 346)
DN_DECKS = (118, 160, 202, 244, 286, 328, 370)
LANDINGS = ((0, 104, 172), (236, 340, 262), (0, 104, 358), (226, 340, 118))  # x0, x1, floor
PIT_FLOOR = 428
IRON_STRAP = (70, 66, 60)


def pater_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > PIT_FLOOR:
            continue
        cut = False
        for x0, x1, f in LANDINGS:
            if x0 <= lx < x1 and f < ly < f + 40:
                cut = True
        if not cut:
            out.add((x, y))
    return out


def sprocket(cx, cy, r):
    """Iron sprocket: a rim, teeth for the chain, six spokes, a fat hub."""
    disc(cx, cy, r - 1, MET_D)
    disc(cx, cy, r - 5, CAVE)
    ring(cx, cy, r - 1, MET_L)
    ring(cx, cy, r - 4, MET)
    for k in range(16):
        a = k * math.pi / 8
        disc(cx + math.cos(a) * r, cy + math.sin(a) * r, 1.3, MET)
    for k in range(6):
        a = k * math.pi / 3 + 0.25
        line(cx, cy, cx + math.cos(a) * (r - 5), cy + math.sin(a) * (r - 5), MET)
    disc(cx, cy, 4, MET_L)
    disc(cx, cy, 2, MET_D)


def loop_points(step=2.0):
    """The chain path: up the west run, over the top, down the east, round the bottom."""
    pts = []
    y = BOT_Y
    while y > TOP_Y:
        pts.append((UP_X, y))
        y -= step
    n = int(math.pi * R / step)
    for i in range(n + 1):
        a = math.pi + math.pi * i / n          # west -> over the top -> east
        pts.append((CX + math.cos(a) * R, TOP_Y + math.sin(a) * R))
    y = TOP_Y
    while y < BOT_Y:
        pts.append((DN_X, y))
        y += step
    for i in range(n + 1):
        a = math.pi * i / n                    # east -> under the bottom -> west
        pts.append((CX + math.cos(a) * R, BOT_Y + math.sin(a) * R))
    return pts


def chain_loop(ox, oy):
    for i, (x, y) in enumerate(loop_points(1.5)):
        c = MET_L if (i // 2) % 2 == 0 else MET_D
        px(ox + x, oy + y, c)
        px(ox + x + 1, oy + y, MET_D)


def car(x_pin, deck, side):
    """One open car: a timber deck out from its chain pin, an iron knee brace under it,
    a low rail at the outer end. side=-1 hangs it west of the chain, +1 east."""
    x0, x1 = (x_pin - CAR_W, x_pin) if side < 0 else (x_pin, x_pin + CAR_W)
    rect(x0, deck, x1, deck + 2, WOOD)
    rect(x0, deck, x1, deck, WOOD_L)
    rect(x0, deck + 2, x1, deck + 2, WOOD_D)
    for k in range(x0 + 3, x1, 6):
        px(k, deck + 1, WOOD_D)
    out = x0 if side < 0 else x1
    line(x_pin, deck + 12, out + (3 if side < 0 else -3), deck + 3, IRON_STRAP)   # knee brace
    line(x_pin, deck + 11, out + (4 if side < 0 else -4), deck + 3, MET_D)
    rect(x_pin - 1, deck - 3, x_pin + 1, deck + 12, MET_D)                         # the pin plate
    px(x_pin, deck - 2, MET_XL)
    rect(out, deck - 7, out, deck - 1, WOOD_D)                                     # end rail
    rect(min(out, out - 3 * side), deck - 7, max(out, out - 3 * side), deck - 7, WOOD)


def top_car(cx, deck):
    """The car going over the top: level on the sprocket, pinned at its middle."""
    rect(cx - CAR_W // 2, deck, cx + CAR_W // 2, deck + 2, WOOD)
    rect(cx - CAR_W // 2, deck, cx + CAR_W // 2, deck, WOOD_L)
    rect(cx - CAR_W // 2, deck + 2, cx + CAR_W // 2, deck + 2, WOOD_D)
    rect(cx - 1, deck + 3, cx + 1, deck + 6, MET_D)
    for e in (cx - CAR_W // 2, cx + CAR_W // 2):
        rect(e, deck - 7, e, deck - 1, WOOD_D)


def tower(ox, oy):
    """The timber frame inside the loop that carries both sprocket shafts."""
    xa, xb = ox + CX - 11, ox + CX + 9
    for x in (xa, xb):
        beam(x, oy + TOP_Y + 4, oy + BOT_Y - 4, 2, WOOD_D, WOOD)
    y = TOP_Y + 26
    k = 0
    while y < BOT_Y - 26:
        rect(xa, oy + y, xb + 2, oy + y + 1, WOOD_D)
        if k % 2:
            line(xa + 2, oy + y + 2, xb, oy + y + 30, (66, 50, 35))
        else:
            line(xb, oy + y + 2, xa + 2, oy + y + 30, (66, 50, 35))
        y += 32
        k += 1


def pater_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly: floor_at(m, X(lx), Y(ly))

    # rock back on the shaft walls, clear of the cars
    for (bx, by, rx, ry, d) in ((104, 300, 12, 8, -1), (236, 180, 10, 7, 1), (236, 330, 12, 8, 1),
                                (104, 236, 8, 6, -1)):
        x0, y0 = X(bx), Y(by)
        while (x0, y0) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), y0, rx, ry, rough=0.25)
    teeth(m, X(20), X(100), Y(150), 6)
    teeth(m, X(240), X(330), Y(240), 6)
    teeth(m, X(20), X(100), Y(336), 5)
    teeth(m, X(240), X(320), Y(100), 4)
    teeth(m, X(110), X(230), Y(300), 6)

    # the roof over the top: low, toothed, and it has had someone already
    roof_x0, roof_x1 = 138, 204
    for lx in range(roof_x0, roof_x1, 5):
        top = ceil_at(m, X(lx), Y(70)) + 1
        ln = 6 + int(rnd() * 7)
        for i in range(ln):
            half = max(0, (ln - i) // 3)
            rect(X(lx) - half, top + i, X(lx) + half, top + i, ROCK_M)
        px(X(lx), top + ln - 1, ROCK_L)
        if 150 < lx < 190 and chance(0.6):
            px(X(lx), top + ln, RED, 0.9)
            px(X(lx), top + ln + 1 + int(rnd() * 3), RED, 0.7)

    tower(ox, oy)
    sprocket(X(CX), Y(TOP_Y), R - 2)
    sprocket(X(CX), Y(BOT_Y), R - 2)
    chain_loop(ox, oy)

    for d in UP_DECKS:
        car(X(UP_X), Y(d), -1)
    for d in DN_DECKS:
        car(X(DN_X), Y(d), 1)
    top_car(X(CX), Y(TOP_Y - R - 4))
    corpse(X(CX), Y(TOP_Y - R - 4), c=(84, 78, 74))           # flattened on the way over
    for k in range(6):
        px(X(CX - 10 + k * 4), Y(TOP_Y - R - 5) - int(rnd() * 2), RED)

    # the drive: a winding engine in the pit, belted to the bottom shaft
    pf = Y(PIT_FLOOR) + 1
    fx, fy = X(86), Y(398)
    rect(fx - 4, fy, fx + 4, pf - 1, MET_D)
    rect(fx - 12, pf - 4, fx + 12, pf - 1, MET_D)
    rect(fx - 12, pf - 4, fx + 12, pf - 4, MET_L)
    disc(fx, fy, 14, MET_D)
    disc(fx, fy, 11, CAVE)
    ring(fx, fy, 14, MET_L)
    ring(fx, fy, 11, MET)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.4
        line(fx, fy, fx + math.cos(a) * 11, fy + math.sin(a) * 11, MET)
    disc(fx, fy, 2.5, MET_L)
    belt = (60, 52, 42)
    line(fx, fy - 14, X(CX), Y(BOT_Y) - 5, belt)
    line(fx, fy + 14, X(CX), Y(BOT_Y) + 5, belt)
    rect(fx + 18, pf - 9, fx + 30, pf - 1, MET)                 # the engine block
    rect(fx + 18, pf - 9, fx + 30, pf - 9, MET_XL)
    rect(fx + 22, pf - 16, fx + 25, pf - 10, MET_D)              # exhaust stub
    keg(X(46), pf)
    crate_g(X(250), pf)
    crate_g(X(262), pf, 9)
    scrap_pile(X(200), pf, 26, 5, colors=(MET_D, DIRT, ROCK_M, WOOD_D))
    stand("Minespider", X(230), pf, flip=True)
    lamp(X(118), ceil_at(m, X(118), Y(400)) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.15)

    # riders, and the crew on the landings
    stand("Gaper", X(UP_X - 12), Y(UP_DECKS[0]))
    stand("WizBonecrown", X(UP_X - 12), Y(UP_DECKS[4]))
    stand("RiotBrute", X(DN_X + 12), Y(DN_DECKS[2]), flip=True)
    l1 = Y(LANDINGS[0][2]) + 1
    stand("Sentinel", X(64), l1)
    crate_g(X(18), l1)
    crate_g(X(20), l1 - 12, 9)
    lamp(X(88), ceil_at(m, X(88), l1 - 10) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)
    r1 = Y(LANDINGS[1][2]) + 1
    stand("Grenadier", X(270), r1, flip=True)
    keg(X(312), r1)
    keg(X(322), r1)
    lamp(X(296), ceil_at(m, X(296), r1 - 10) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)
    l2 = Y(LANDINGS[2][2]) + 1
    stand("WizDeepminer", X(70), l2)
    for k in range(3):                                         # picks on the wall
        line(X(14 + k * 4), l2 - 1, X(20 + k * 4), l2 - 20, WOOD_D)
        rect(X(17 + k * 4), l2 - 21, X(23 + k * 4), l2 - 20, MET_L)
    t2 = Y(LANDINGS[3][2]) + 1
    stand("Pyro", X(290), t2, flip=True)
    # a lever by the east landing, left as it was: the brake nobody uses
    line(X(244), r1 - 1, X(250), r1 - 14, MET_D)
    disc(X(250), r1 - 15, 1.6, RED_L)


ROOM = {
    "name": "THE PATERNOSTER", "w": 340, "h": 450,
    "shapes": [([("tube", [(CX, 150), (CX, 404)], 66),             # the shaft
                 ("blob", CX, 90, 52, 42),                         # the top, low and tight
                 ("blob", CX, 410, 112, 26)], 0.08),               # the drive pit
               ([("blob", 52, 150, 54, 26),                        # west landing, high
                 ("blob", 282, 240, 60, 26),                       # east landing
                 ("blob", 56, 336, 62, 26),                        # west landing, low
                 ("blob", 262, 104, 54, 24)], 0.12)],              # east niche under T2
    "sockets": {"T1": ("T", 50, 128), "T2": ("T", 280, 84),
                "L1": ("L", 172, 8), "R1": ("R", 262, 10),
                "L2": ("L", 358, 8), "B1": ("B", 170, 26)},
    "edit": pater_edit,
    "furnish": pater_furnish,
}


SHEET = {
    "seed": 73101,
    "callouts": [
        ("1 CARS ON AN ENDLESS CHAIN", (-140, 250), (UP_X - 14, 222)),
        ("2 LOW ROOF OVER THE TOP", (90, -46), (CX + 6, 56)),
        ("3 DRIVE IN THE PIT", (-140, 470), (86, 398)),
    ],
    "beats": [
        ("UP THE WEST SIDE, DOWN THE EAST, NEVER STOPS: STEP ON, STEP OFF", (170, 180, 195)),
        ("KNOCK ONE ONTO A RISING CAR AND LET THE ROOF HAVE HIM", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
