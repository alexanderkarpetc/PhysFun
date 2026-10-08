"""Small room S23 - THE TIMBER CHUTE.

A tall room in three shapes: a log landing high in the east, a hall low across the
bottom, and between them, cut on a long slant through the rock, a timber chute. A dozen
logs are stacked on the landing at the chute's head, and the only thing holding the
pile is one stake at the lip with an iron pin through it. Pull the pin - shoot it, burn
the stake - and the logs go down the chute, come off its foot into the hall and roll
the length of the floor into the crew camped at the far end.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S23"

LANDING = 130                     # landing floor
LIP = 240                         # where the landing drops into the chute
CHUTE = ((236, 132), (58, 322))   # chute tube centre line, head to foot
CHUTE_R = 16
LOFT = 140                        # the winch loft floor, north-west
BUBBLE = 258                      # the side bubble floor, east
LOG_R = 5
END = (128, 104, 72)              # end grain
END_D = (92, 72, 50)


def hall_floor(lx):
    """The hall falls gently east, so what comes off the chute keeps rolling."""
    return 392 + (lx - 40) * 0.035


def chute_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > 300 and ly >= hall_floor(lx):
            continue
        if LIP < lx < 350 and ly < 180 and ly >= LANDING and not (330 < lx < 347):
            continue
        if lx < 150 and ly < 200 and ly >= LOFT:
            continue
        if 255 < lx < 345 and 200 < ly < 290 and ly >= BUBBLE and not (318 < lx < 338):
            continue
        out.add((x, y))
    return out


def log_end(cx, cy, r=LOG_R):
    """A log seen end-on: bark ring, end grain, growth rings, a check crack."""
    disc(cx, cy, r, WOOD_D)
    disc(cx, cy, r - 1, END)
    ring(cx, cy, r - 2.5, END_D)
    px(cx, cy, END_D)
    line(cx, cy, cx + r - 1, cy - 1, END_D)


def chute_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly: floor_at(m, X(lx), Y(ly))

    teeth(m, X(236), X(346), Y(90), 8)
    teeth(m, X(30), X(140), Y(100), 7)
    teeth(m, X(70), X(350), Y(320), 16)
    for x, y, d, rx, ry in ((250, 236, -1, 10, 8), (24, 386, -1, 12, 9)):
        x0 = ox + x
        while (x0, oy + y) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), oy + y, rx, ry, rough=0.25)

    # the chute: a plank bed laid on the floor of the cut, a side board, trestles under
    (hx, hy), (fx, fy) = CHUTE
    ln = math.hypot(fx - hx, fy - hy)
    dx, dy = (fx - hx) / ln, (fy - hy) / ln
    nx, ny = -dy, dx                                    # points down-right, onto the cut's floor
    if ny < 0:
        nx, ny = -nx, -ny
    off = CHUTE_R - 5
    bx0, by0 = X(hx + nx * off) + 4, Y(hy + ny * off) - 1
    bx1, by1 = X(fx + nx * off) - 8, Y(fy + ny * off) + 6
    for t in range(4):
        line(bx0, by0 + t, bx1, by1 + t, WOOD if t < 3 else WOOD_D)
    line(bx0, by0, bx1, by1, WOOD_L)
    line(bx0 - 3, by0 - 7, bx1 - 3, by1 - 7, WOOD_D)    # the side board, behind
    for k in range(1, 9):
        t = k / 9.0
        sx, sy = bx0 + (bx1 - bx0) * t, by0 + (by1 - by0) * t
        line(sx - 3, sy - 7, sx, sy, WOOD_D)            # side board posts
        f = floor_at(m, sx, sy + 4)
        if f - sy < 18:
            rect(sx, sy + 4, sx + 1, f - 1, WOOD_D)
    # the kicker at the foot: a curved lip that throws them out level onto the hall floor
    for i in range(12):
        px(bx1 - 2 + i, by1 + 3 + int(3 * math.sin(i / 11.0 * math.pi / 2)), WOOD)
        px(bx1 - 2 + i, by1 + 4 + int(3 * math.sin(i / 11.0 * math.pi / 2)), WOOD_D)
    for k in range(5):                                  # scuffs down the bed where logs ran
        t = 0.15 + k * 0.17
        px(bx0 + (bx1 - bx0) * t + 2, by0 + (by1 - by0) * t - 1, WOOD_L, 0.8)

    # the landing: the stack, the stake at the lip and the pin through it
    lf = Y(LANDING)
    rows = ((5, 0), (4, LOG_R), (3, 2 * LOG_R))
    for r_i, (n, inset) in enumerate(rows):
        for k in range(n):
            cx = X(LIP + 12) + inset + k * (2 * LOG_R) + 1
            cy = lf - LOG_R - r_i * (2 * LOG_R - 1)
            log_end(cx, cy)
    sx = X(LIP + 2)
    beam(sx, lf - 18, lf + 6, 3, WOOD, WOOD_L)          # the stake, driven into the lip
    rect(sx - 3, lf - 14, sx + 7, lf - 13, MET_XL)      # the pin through it
    ring(sx - 5, lf - 13.5, 2.2, MET_L)
    cable(sx - 7, lf - 13, X(LIP - 30), Y(96), sag=10, c=(120, 100, 70))   # rope from the pin...
    rect(X(LIP - 34), Y(94), X(LIP - 28), Y(97), MET_D)                    # ...to a cleat on the roof rock
    glow(sx + 2, lf - 13, 12, F_MID, 0.18)
    rect(sx - 9, lf - 12, sx - 7, lf - 8, RED_L)       # a rag tied to the ring
    stand("WizGoldhood", X(318), fl(318, 110), flip=True)
    for k in range(3):                                 # wedges and a cant hook against the wall
        rect(X(304), lf - 3 - k * 3, X(308), lf - 1 - k * 3, WOOD_D)
    line(X(328), lf - 26, X(326), lf - 1, WOOD_D)
    line(X(328), lf - 26, X(331), lf - 23, MET_L)
    ladder(X(335), lf, Y(BUBBLE), w=6, step=6)

    # the winch loft over in the north-west, and the haul road along the top
    lo = Y(LOFT)
    for k in range(3):
        log_end(X(54) + k * 10, lo - LOG_R)
    log_end(X(59), lo - 3 * LOG_R + 1)
    rect(X(100), lo - 16, X(104), lo - 1, WOOD_D)      # windlass
    rect(X(118), lo - 16, X(122), lo - 1, WOOD_D)
    disc(X(111), lo - 14, 5, WOOD)
    ring(X(111), lo - 14, 5, WOOD_D)
    line(X(111), lo - 14, X(118), lo - 22, WOOD_L)
    cable(X(111), lo - 19, X(LIP + 10), lf - 30, sag=-4, c=(120, 100, 70))
    stand("Grenadier", X(84), lo)
    lamp(X(70), ceil_at(m, X(70), lo - 20) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)
    lamp(X(290), ceil_at(m, X(290), lf - 30) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)

    # the side bubble: a lookout over the hall, a ladder down
    bb = Y(BUBBLE)
    stand("Sentinel", X(292), bb)
    crate_g(X(268), bb)
    ladder(X(325), bb, fl(330, 300) - 1, w=6, step=6)

    # the hall: two logs that came down last time, and the camp at the low east end
    log_end(X(150), fl(150, 380) - LOG_R)
    log_end(X(196), fl(196, 380) - LOG_R)
    for k in range(4):
        px(X(70 + k * 18), fl(70 + k * 18, 380) - 1, WOOD_L, 0.6)
    for lx, name, flip in ((236, "Gaper", True), (262, "RiotBrute", True), (284, "WizBogcap", True),
                           (306, "Ghast", True), (122, "Reaper", False)):
        stand(name, X(lx), fl(lx, 380), flip=flip)
    f = fl(330, 380)
    crate_g(X(322), f)
    crate_g(X(334), f, 10)
    for bx in (250, 292):                               # bedrolls along the low end
        g = fl(bx + 6, 380)
        rect(X(bx), g - 3, X(bx + 13), g - 1, (92, 70, 60))
        rect(X(bx), g - 3, X(bx + 13), g - 3, (122, 96, 80))
    g = fl(214, 380)
    rect(X(206), g - 2, X(222), g - 1, CHAR)            # a cold fire ring
    for k in range(5):
        px(X(207 + k * 3), g - 3, ROCK_L)
    corpse(X(170), fl(170, 380))
    lamp(X(250), ceil_at(m, X(250), Y(360)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=80, strength=0.15)
    lamp(X(110), ceil_at(m, X(110), Y(360)) + 1, drop=5, bulb=LAMP, tint=LAMP, r=50, strength=0.11)


ROOM = {
    "name": "THE TIMBER CHUTE", "w": 360, "h": 440,
    "shapes": [([("blob", 290, 104, 56, 36),                     # the landing
                 ("blob", 82, 112, 56, 38),                      # the winch loft
                 ("tube", [(120, 128), (250, 118)], 13)], 0.1),  # haul road between them
               ([("tube", [CHUTE[0], CHUTE[1]], CHUTE_R)], 0.05),
               ([("blob", 200, 356, 160, 56)], 0.08),            # the hall
               ([("blob", 300, 236, 46, 30),                     # side bubble
                 ("tube", [(338, 128), (338, 214)], 8),
                 ("tube", [(328, 262), (328, 314)], 9)], 0.1)],
    "sockets": {"T1": ("T", 296, 74), "T2": ("T", 82, 80),
                "L1": ("L", LOFT, 32), "L2": ("L", 392, 58),
                "R1": ("R", 403, 22), "R2": ("R", BUBBLE, 24)},
    "edit": chute_edit,
    "furnish": chute_furnish,
}


SHEET = {
    "seed": 72301,
    "callouts": [
        ("1 TWELVE LOGS, ONE PIN", (250, -50), (244, 116)),
        ("2 THE CHUTE", (-104, 210), (156, 232)),
        ("3 THEY ROLL THE HALL INTO THE CAMP", (40, 460), (262, 392)),
    ],
    "beats": [
        ("PULL THE PIN: THE PILE GOES DOWN THE CHUTE AND ACROSS THE HALL", (170, 180, 195)),
        ("OR BURN THE STAKE FROM BELOW, OR RIDE A LOG DOWN YOURSELF", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
