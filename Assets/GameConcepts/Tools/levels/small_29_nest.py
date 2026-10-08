"""Small room S29 - THE NEST.

A Minespider hive: one round chamber with bubbles budding off it on every side, the
whole of it strung with silk. The webs are rope nets - a great hammock across the middle
of the chamber, curtains across the throats into the bubbles, fans in the corners - and
they hold whatever the spiders have put on them: egg sacs, cocooned miners, a dropped
crate, the spiders themselves. Silk is rope, so it burns: a lantern caught in the
hammock is the match, and when a web goes, everything on it comes down.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S29"

SILK = (178, 174, 158)
SILK_D = (120, 118, 108)
SAC = (166, 158, 124)
SAC_L = (204, 196, 160)
SAC_D = (104, 96, 70)
WRAP = (150, 146, 130)
WRAP_D = (100, 98, 88)


def sag_line(x0, y0, x1, y1, sag, c=SILK, a=0.8):
    n = max(int(abs(x1 - x0) + abs(y1 - y0)), 2)
    for i in range(n + 1):
        t = i / float(n)
        px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * math.sin(math.pi * t), c, a)


def sag_pt(x0, y0, x1, y1, sag, t):
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)


def hammock(x0, y0, x1, y1, sag, strands=4, gap=3):
    """A rope net of silk slung between two walls: a few sagging strands, laced across.
    Returns the top strand as f(t) -> (x, y), for putting things on it."""
    for k in range(strands):
        sag_line(x0, y0 + k * gap, x1, y1 + k * gap, sag + k, SILK if k == 0 else SILK_D, 0.85)
    n = int(abs(x1 - x0) / 7)
    for i in range(1, n):
        t = i / float(n)
        ax, ay = sag_pt(x0, y0, x1, y1, sag, t)
        bx, by = sag_pt(x0, y0 + (strands - 1) * gap, x1, y1 + (strands - 1) * gap, sag + strands - 1,
                        t + (0.012 if i % 2 else -0.012))
        line(ax, ay, bx, by, SILK_D, 0.7)
    for (ax, ay) in ((x0, y0), (x1, y1)):                    # where it is glued to the rock
        for j in range(5):
            line(ax, ay + (strands - 1) * gap / 2.0, ax + (rnd() - 0.5) * 10, ay + (rnd() - 0.5) * 16, SILK, 0.5)
    return lambda t: sag_pt(x0, y0, x1, y1, sag, t)


def curtain(x, y0, y1, w, m):
    """A web hung across a throat: vertical strands from roof to floor, laced."""
    for k in range(0, w, 3):
        sag_line(x + k, y0, x + k + 2, y1, 2, SILK if k % 2 else SILK_D, 0.7)
    for y in range(int(y0) + 4, int(y1), 6):
        line(x - 1, y, x + w, y + 2, SILK_D, 0.6)


def tangle(x0, x1, ymid, m, n):
    """Loose silk across a throat: strands from roof to floor at a slant, crossing."""
    for _ in range(n):
        a = x0 + rnd() * (x1 - x0)
        b = x0 + rnd() * (x1 - x0)
        ya = ceil_at(m, int(a), ymid) + 1
        yb = floor_at(m, int(b), ymid)
        if yb - ya > 140:
            continue
        sag_line(a, ya, b, yb, (rnd() - 0.5) * 8, SILK if chance(0.5) else SILK_D, 0.6)
    for _ in range(n // 2):
        y = ymid + (rnd() - 0.5) * 40
        line(x0, y, x1, y + (rnd() - 0.5) * 10, SILK_D, 0.5)


def fan(cx, cy, m, r, a0, a1, spokes=7, rings=4):
    """Orb web in a corner: spokes out until they meet rock, rings across them."""
    ends = []
    for i in range(spokes):
        a = a0 + (a1 - a0) * i / float(spokes - 1)
        d = 0
        while d < r and (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)) in m:
            d += 1
        ends.append((a, d))
        line(cx, cy, cx + math.cos(a) * d, cy + math.sin(a) * d, SILK, 0.7)
    for k in range(1, rings + 1):
        f = k / float(rings + 1)
        for (a, d), (b, e) in zip(ends, ends[1:]):
            line(cx + math.cos(a) * d * f, cy + math.sin(a) * d * f,
                 cx + math.cos(b) * e * f, cy + math.sin(b) * e * f, SILK_D, 0.6)


def egg_sacs(x, roof, drop, n=4):
    """A bunch of egg sacs on short threads off the roof."""
    for i in range(n):
        ex = x + (i - n / 2.0) * 6 + rnd() * 2
        ey = roof + drop + (i % 2) * 6 + rnd() * 3
        line(x, roof, ex, ey - 5, SILK, 0.7)
        for yy in range(-5, 6):
            hw = int(3.6 * math.sqrt(max(0.0, 1 - (yy / 5.6) ** 2)))
            rect(ex - hw, ey + yy, ex + hw, ey + yy, SAC)
        px(ex - 1, ey - 3, SAC_L)
        px(ex - 2, ey - 2, SAC_L)
        line(ex + 1, ey - 4, ex - 1, ey + 4, SAC_D, 0.6)
        px(ex + 1, ey + 2, (90, 110, 60), 0.8)                # the thing inside


def cocoon(x, top, ln, roof=None, lying=False):
    """A wrapped body: a long bundle of silk, banded, a boot out of the end."""
    if roof is not None:
        line(x, roof, x, top, SILK, 0.8)
    if lying:
        for xx in range(-ln // 2, ln // 2 + 1):
            hh = int(4 * math.sqrt(max(0.0, 1 - (xx / (ln / 2.0 + 1)) ** 2)))
            rect(x + xx, top - hh, x + xx, top + hh, WRAP)
            if xx % 3 == 0:
                rect(x + xx, top - hh, x + xx, top + hh, WRAP_D)
        rect(x + ln // 2, top - 1, x + ln // 2 + 3, top + 2, (60, 52, 44))
        return
    for yy in range(ln):
        hw = int(4 * math.sqrt(max(0.0, 1 - ((yy - ln / 2.0) / (ln / 2.0 + 1)) ** 2))) + 1
        rect(x - hw, top + yy, x + hw, top + yy, WRAP)
        if yy % 3 == 0:
            line(x - hw, top + yy, x + hw, top + yy + 2, WRAP_D)
        px(x - hw, top + yy, SILK)
    rect(x - 2, top + ln, x + 1, top + ln + 3, (60, 52, 44))  # a boot


def bones(x, floor, n=6):
    for i in range(n):
        bx = x + rnd() * 24
        line(bx, floor - 1, bx + 4 + rnd() * 3, floor - 1 - rnd() * 3, (176, 168, 140))
    rect(x + 8, floor - 4, x + 12, floor - 1, (176, 168, 140))
    px(x + 9, floor - 3, INK)


def nest_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly: floor_at(m, X(lx), Y(ly))
    rf = lambda lx, ly: ceil_at(m, X(lx), Y(ly)) + 1

    teeth(m, X(110), X(280), Y(140), 14)
    teeth(m, X(40), X(130), Y(100), 6)
    teeth(m, X(260), X(350), Y(140), 6)
    # silk plastered over the rock: pale skins in the corners
    for (cx, cy, r, a0, a1) in ((40, 80, 60, 0.0, 1.6), (344, 120, 50, 1.6, 3.1),
                                (30, 284, 40, -1.5, 0.2), (180, 106, 60, 0.3, 2.8)):
        fan(X(cx), Y(cy), m, r, a0, a1)

    # the hammock across the middle of the chamber, and what is on it
    wl, wr = X(72), X(290)
    while (wl - 1, Y(206)) in m:
        wl -= 1
    while (wr + 1, Y(196)) in m:
        wr += 1
    top = hammock(wl, Y(206), wr, Y(196), 26)
    for t, what in ((0.18, "sp"), (0.32, "co"), (0.46, "crate"), (0.58, "sp"), (0.72, "lantern"),
                    (0.84, "co2")):
        x, y = top(t)
        y = int(y)
        if what == "sp":
            stand("Minespider", int(x), y)
        elif what == "co":
            cocoon(int(x), y - 5, 20, lying=True)
        elif what == "co2":
            cocoon(int(x), y - 5, 16, lying=True)
        elif what == "crate":
            crate_g(int(x) - 6, y, 11)
        else:                                                # the match: a miner's lantern, lit
            lx, ly = int(x), y
            rect(lx - 3, ly - 8, lx + 3, ly - 1, MET_D)
            rect(lx - 2, ly - 7, lx + 2, ly - 2, F_MID)
            px(lx, ly - 5, F_HOT)
            ring(lx, ly - 10, 2, MET_L)
            glow(lx, ly - 5, 40, F_MID, 0.18)
            for k in range(6):                               # the silk round it already going
                px(lx - 8 + k * 3, ly + 1 + (k % 2), pick([F_MID, F_COOL, F_HOT]))
            embers(lx - 10, ly - 16, lx + 10, ly - 4, 10)

    # egg sacs and cocoons off the roof
    for (lx, ly, drop, n) in ((150, 140, 10, 5), (214, 140, 6, 4), (250, 150, 14, 3), (100, 110, 6, 4),
                              (334, 140, 8, 4)):
        egg_sacs(X(lx), rf(lx, ly), drop, n)
    for (lx, ly, drop, ln) in ((180, 140, 16, 22), (126, 140, 26, 18), (234, 140, 30, 20)):
        r = rf(lx, ly)
        cocoon(X(lx), r + drop, ln, roof=r)
    stand("Minespider", X(196), Y(130))                      # down its thread
    line(X(196), rf(196, 120), X(196), Y(110), SILK, 0.8)

    # the throats: curtains of silk into the bubbles
    fan(X(136), Y(150), m, 46, -3.1, -1.7, 6, 3)
    fan(X(250), Y(176), m, 46, -1.4, 0.0, 6, 3)

    # the floor of the chamber under the hammock: what has dropped before
    cf = lambda lx: fl(lx, 260)
    bones(X(140), cf(140))
    bones(X(200), cf(200), 4)
    corpse(X(176), cf(176), c=(110, 96, 70))
    stand("Minespider", X(160), cf(160))
    stand("Minespider", X(226), cf(226), flip=True)
    for (lx, n) in ((130, 3), (244, 4)):                     # sacs laid on the floor
        for i in range(n):
            ex, ey = X(lx) + i * 7, cf(lx + i * 7) - 5
            disc(ex, ey, 4, SAC)
            px(ex - 1, ey - 2, SAC_L)

    # the bubbles
    stand("Minespider", X(70), fl(70, 120), flip=False)
    cocoon(X(52), fl(52, 120) - 4, 18, lying=True)
    stand("Gaper", X(300), fl(300, 170), flip=True)          # caught: half wrapped already
    for k in range(5):
        line(X(292), fl(300, 170) - 4 - k * 4, X(308), fl(300, 170) - 2 - k * 4, SILK, 0.8)
    stand("Minespider", X(330), fl(330, 170), flip=True)
    stand("Minespider", X(64), fl(64, 300))
    pick_x = X(92)
    line(pick_x, fl(92, 300) - 1, pick_x + 6, fl(92, 300) - 16, WOOD_D)
    rect(pick_x + 3, fl(92, 300) - 17, pick_x + 10, fl(92, 300) - 16, MET_L)
    stand("Minespider", X(296), fl(296, 300), flip=True)
    hammock(X(250), Y(300), X(342), Y(296), 6, 3, 2)          # a small net over the east pocket
    cocoon(X(320), fl(320, 300) - 4, 16, lying=True)
    stand("Ghast", X(270), Y(250), flip=True)
    lamp(X(56), rf(56, 290), drop=4, bulb=LAMP, tint=LAMP, r=40, strength=0.10)


ROOM = {
    "name": "THE NEST", "w": 360, "h": 380,
    "shapes": [([("blob", 182, 204, 112, 100)], 0.08),        # the chamber
               ([("blob", 80, 104, 52, 40),                    # bubble, north-west
                 ("blob", 300, 150, 52, 46),                   # bubble, east
                 ("blob", 70, 300, 54, 36),                    # pocket, south-west
                 ("blob", 292, 304, 54, 34),                   # pocket, south-east
                 ("tube", [(96, 292), (140, 270)], 14),
                 ("tube", [(226, 280), (268, 296)], 14),
                 ("tube", [(182, 290), (184, 316)], 13)], 0.12)],
    "sockets": {"T1": ("T", 80, 70), "T2": ("T", 300, 108),
                "L1": ("L", 322, 24), "R1": ("R", 178, 16),
                "R2": ("R", 322, 22), "B1": ("B", 184, 66)},
    "furnish": nest_furnish,
}


SHEET = {
    "seed": 72901,
    "callouts": [
        ("1 SILK NETS HOLD IT ALL UP", (-124, 400), (120, 214)),
        ("2 SACS AND COCOONS", (230, -46), (180, 160)),
        ("3 SILK BURNS", (280, 400), (244, 216)),
    ],
    "beats": [
        ("WEBS ARE ROPE NETS: THEY HOLD SPIDERS, SACS AND BODIES - AND THEY BURN", (170, 180, 195)),
        ("BURN OR CUT THE HAMMOCK AND THE MIDDLE OF THE NEST DROPS ON THE FLOOR", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
