"""Small room S35 - THE ZIPLINE.

A wide gap with a drop under it, and one steel cable across it on a slant: from a timber
A-frame on a high ledge in the west, down through a cleft, to an eye bolt in the wall of a
low ledge in the east. Hook trolleys run on it - one parked at the top, one halfway down
with somebody on it. A crew on each end. Ride the line across, or cut it: the cable goes
slack and whatever is on it goes to the bottom, where the last ones went.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S35"

WEST_FLOOR = 132
EAST_FLOOR = 288
NICHE_FLOOR = 158
PIT_FLOOR = 342
TOP = (126, 98)          # cable over the A-frame sheave
END = (428, 262)         # cable into the east eye bolt
STEEL = (150, 156, 164)
STEEL_D = (84, 88, 96)


def zip_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > PIT_FLOOR:
            continue
        if lx < 150 and ly > WEST_FLOOR and ly < WEST_FLOOR + 60:
            continue
        if lx > 352 and ly > EAST_FLOOR:
            continue
        if 314 < lx < 400 and NICHE_FLOOR < ly < NICHE_FLOOR + 30:
            continue
        out.add((x, y))
    return out


def cable_y(lx):
    """The line: straight, with a little sag in the middle."""
    t = (lx - TOP[0]) / float(END[0] - TOP[0])
    return TOP[1] + (END[1] - TOP[1]) * t + 7 * math.sin(math.pi * t)


def trolley(ox, oy, lx, hook=16):
    """A hook trolley: two grooved wheels on the cable, a side plate, a hook on a bar."""
    a, b = lx - 4, lx + 4
    ya, yb = cable_y(a), cable_y(b)
    for (wx, wy) in ((a, ya), (b, yb)):
        disc(ox + wx, oy + wy - 1, 2.6, MET)
        ring(ox + wx, oy + wy - 1, 2.6, MET_L)
        px(ox + wx, oy + wy - 1, MET_D)
    yc = cable_y(lx)
    rect(ox + lx - 5, oy + yc + 1, ox + lx + 5, oy + yc + 4, MET_D)        # side plate
    rect(ox + lx - 5, oy + yc + 1, ox + lx + 5, oy + yc + 1, MET_L)
    rect(ox + lx, oy + yc + 4, ox + lx, oy + yc + hook, MET_L)            # hanger
    rect(ox + lx - 5, oy + yc + hook, ox + lx + 5, oy + yc + hook + 1, MET_D)   # the bar you hold
    rect(ox + lx - 5, oy + yc + hook, ox + lx + 5, oy + yc + hook, MET_XL)
    return oy + yc + hook


def a_frame(ox, oy):
    tx, ty = ox + TOP[0], oy + TOP[1]
    f = oy + WEST_FLOOR + 1
    for (fx, w) in ((tx - 16, 3), (tx + 14, 3)):
        for k in range(w):
            line(fx + k, f - 1, tx - 1 + k, ty + 3, WOOD if k < w - 1 else WOOD_D)
    rect(tx - 10, ty + 16, tx + 10, ty + 18, WOOD_D)                       # cross tie
    rect(tx - 10, ty + 16, tx + 10, ty + 16, WOOD)
    rect(tx - 4, ty + 1, tx + 4, ty + 3, WOOD_D)                           # head block
    disc(tx, ty, 4, MET)                                                   # sheave
    ring(tx, ty, 4, MET_L)
    px(tx, ty, MET_D)
    for fx in (tx - 18, tx + 12):
        rect(fx, f - 3, fx + 7, f - 1, WOOD_D)                             # sole plates


def zip_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    wf, ef, pf = Y(WEST_FLOOR) + 1, Y(EAST_FLOOR) + 1, Y(PIT_FLOOR) + 1

    teeth(m, X(150), X(330), Y(200), 16)
    teeth(m, X(20), X(140), Y(110), 6)
    teeth(m, X(330), X(430), Y(250), 6)
    for (bx, by, rx, ry, d) in ((124, 220, 16, 9, -1), (346, 220, 12, 8, 1), (130, 300, 14, 9, -1)):
        x0 = X(bx)
        while (x0, Y(by)) in m:
            x0 += d
        rock_blob(x0 - d * 5, Y(by), rx, ry, rough=0.25)

    # the spire up out of the pit, under the middle of the line
    for k, (sx, sy, rx, ry) in enumerate(((246, 330, 26, 14), (248, 306, 18, 14), (244, 282, 13, 12),
                                          (247, 262, 9, 10), (246, 248, 6, 7))):
        rock_blob(X(sx), Y(sy), rx, ry, rough=0.22, clip=(X(0), Y(0), X(460), pf - 1))
    stand("Minespider", X(246), Y(241))

    # the pit: what came off the line before
    for k in range(3):
        scrap_pile(X(170 + k * 90) - 14, pf, 30, 5,
                   colors=((200, 196, 178), (160, 156, 140), ROCK_M, DIRT, MET_D))
    corpse(X(196), pf)
    corpse(X(300), pf, c=(84, 78, 74))
    rect(X(206), pf - 4, X(216), pf - 2, MET_D)                            # a trolley, smashed
    disc(X(208), pf - 5, 2.2, MET)
    line(X(216), pf - 2, X(222), pf - 8, MET_L)
    stand("Gaper", X(170), pf)
    stand("Ghast", X(196), Y(236))                                       # it flies

    # the line
    a_frame(ox, oy)
    bx, by = X(58), wf - 1                                                 # backstay to a ring bolt
    line(X(TOP[0]), Y(TOP[1]), bx, by - 3, STEEL_D)
    rect(bx - 3, by - 3, bx + 3, by - 1, MET_D)
    ring(bx, by - 5, 2, MET_L)
    tby = Y(TOP[1]) + (wf - 4 - Y(TOP[1])) * (TOP[0] - 92) / float(TOP[0] - 58)   # turnbuckle on the stay
    rect(X(88), tby - 2, X(96), tby + 1, MET)
    rect(X(88), tby - 2, X(96), tby - 2, MET_XL)
    prev = None
    for lx in range(TOP[0], END[0] + 1):
        y = Y(cable_y(lx))
        px(X(lx), y, STEEL)
        px(X(lx), y + 1, STEEL_D)
        if prev is not None and abs(prev - y) > 1:
            rect(X(lx), min(prev, y), X(lx), max(prev, y), STEEL)
        prev = y
    ex, ey = X(END[0]), Y(END[1])                                          # the eye bolt plate
    rect(ex, ey - 6, ex + 4, ey + 6, MET_D)
    rect(ex, ey - 6, ex, ey + 6, MET_L)
    ring(ex - 2, ey, 2.4, MET_XL)
    for k in range(3):                                                     # the buffer: sacks lashed under it
        cx = END[0] - 10 - k * 11
        cy = Y(cable_y(cx)) + 2
        rect(X(cx - 3), cy, X(cx + 3), cy + 8, (148, 128, 92))
        rect(X(cx - 4), cy + 2, X(cx + 4), cy + 6, (148, 128, 92))
        rect(X(cx - 3), cy, X(cx + 3), cy, (178, 158, 116))
        rect(X(cx - 3), cy + 8, X(cx + 3), cy + 8, (108, 92, 66))
        px(X(cx), cy - 1, (108, 92, 66))

    # the line before this one: cut at the head, hanging down the west wall, trolley still on
    hx, hy0 = X(TOP[0] + 3), Y(TOP[1]) + 4
    pts = [(hx, hy0), (X(152), Y(150)), (X(146), Y(210)), (X(150), Y(262))]
    for (ax, ay), (bx_, by_) in zip(pts, pts[1:]):
        line(ax, ay, bx_, by_, STEEL_D)
    ex_, ey_ = pts[-1]
    disc(ex_, ey_ + 2, 2.4, MET)
    rect(ex_ - 4, ey_ + 4, ex_ + 4, ey_ + 6, MET_D)
    rect(ex_, ey_ + 7, ex_, ey_ + 14, MET_L)
    rect(ex_ - 4, ey_ + 14, ex_ + 4, ey_ + 15, MET_XL)
    for k in range(4):
        px(ex_ + 1 - k, ey_ + 16 + k * 2, STEEL_D)

    # trolleys: one parked at the top, one halfway down with a rider
    trolley(ox, oy, TOP[0] + 16, hook=14)
    hy = trolley(ox, oy, 262, hook=10)
    stand("Gaper", X(262), hy + 22, flip=True)

    # the west end: the crew by the A-frame
    stand("Grenadier", X(80), wf)
    stand("WizCrimson", X(40), wf)
    keg(X(20), wf)
    crate_g(X(150), wf, 10)
    lamp(X(100), ceil_at(m, X(100), wf - 20) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)

    # the east end: the crew at the bottom of the line, and the niche over it
    stand("RiotBrute", X(372), ef, flip=True)
    stand("Pyro", X(396), ef, flip=True)
    crate_g(X(410), ef, 11)
    crate_g(X(412), ef - 12, 9)
    lamp(X(380), ceil_at(m, X(380), ef - 20) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)
    nf = Y(NICHE_FLOOR) + 1
    stand("Sentinel", X(342), nf, flip=True)
    keg(X(368), nf)
    lamp(X(240), ceil_at(m, X(240), Y(200)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=80, strength=0.12)


ROOM = {
    "name": "THE ZIPLINE", "w": 460, "h": 380,
    "shapes": [([("blob", 236, 238, 118, 116)], 0.09),                     # the gap and the pit
               ([("blob", 80, 108, 62, 34),                                 # west ledge, high
                 ("blob", 386, 266, 54, 30),                                # east ledge, low
                 ("blob", 352, 136, 46, 28),                                # east niche
                 ("tube", [(120, 116), (400, 266)], 26)], 0.1)],            # the cleft the line runs in
    "sockets": {"T1": ("T", 60, 80), "T2": ("T", 362, 112),
                "L1": ("L", WEST_FLOOR, 22), "R1": ("R", EAST_FLOOR, 26),
                "B1": ("B", 220, 42)},
    "edit": zip_edit,
    "furnish": zip_furnish,
}


SHEET = {
    "seed": 73501,
    "callouts": [
        ("1 RIDE THE LINE ACROSS", (244, 392), (262, 196)),
        ("2 CUT IT AND THE RIDER DROPS", (220, -46), (180, 130)),
        ("3 WHERE THE LAST ONES WENT", (-120, 392), (196, 340)),
    ],
    "beats": [
        ("ONE STEEL LINE, HIGH WEST TO LOW EAST: GRAB A TROLLEY AND GO", (170, 180, 195)),
        ("OR CUT THE LINE UNDER THE ONE WHO IS RIDING IT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
