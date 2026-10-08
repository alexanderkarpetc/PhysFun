"""Small room S28 - THE WRECKING BALL.

A tall cave with a rock shelf off its west wall. On the shelf stands a timber jib crane -
mast, jib out over the room, a stay from the masthead to the jib's end - and off the jib's
end hangs an iron ball on a chain, hauled back west to the shelf and tied off to a
bollard. Below, across the bowl of the floor, the crew have put up timber: a plank
barricade, a plank hut, a lean-to on the east wall. Cut the tie and the ball swings down
through all of it and up the far side, and back, and again, a little lower each time.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S28"

SHELF = 188                     # the shelf's floor
BOWL = 270                      # the floor at the bottom of the swing
EAST = 238                      # the east floor
MAST_X = 28
JIB_Y = 66
PIVOT = (226, 72)
CHAIN = 186
TIE_A = 1.0                    # radians west of hanging straight down
BALL_R = 13
ROPE = (166, 144, 100)
ROPE_D = (100, 82, 56)


def floor_y(lx):
    def ease(a, b, t):
        t = max(0.0, min(1.0, t))
        return a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * t))
    if lx < 300:
        return BOWL + 2 * math.sin(lx * 0.21)
    return ease(BOWL, EAST, (lx - 300) / 70.0)


def shelf_rock(lx, ly):
    """The shelf: thick at the wall, its underside tapering out to a lip."""
    return SHELF <= ly <= SHELF + 30 and lx < 134 - (ly - SHELF) * 2.2


def ball_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= floor_y(lx) or shelf_rock(lx, ly):
            continue
        if ((lx - 408) / 44.0) ** 2 + ((ly - 140) / 12.0) ** 2 < 1 and ly >= 132:
            continue                                         # the east ledge
        out.add((x, y))
    return out


def rope(x0, y0, x1, y1):
    line(x0, y0, x1, y1, ROPE)
    line(x0, y0 + 1, x1, y1 + 1, ROPE_D)


def slant_chain(x0, y0, x1, y1):
    n = int(math.hypot(x1 - x0, y1 - y0) / 3)
    for i in range(n + 1):
        t = i / float(n)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if i % 2:
            rect(x - 1, y - 1, x + 1, y + 1, MET_D)
            px(x, y, MET_L)
        else:
            rect(x, y - 1, x + 1, y, MET)


def iron_ball(cx, cy, r):
    disc(cx, cy, r + 1, INK)
    disc(cx, cy, r, MET_D)
    disc(cx - r * 0.25, cy - r * 0.25, r * 0.7, MET)
    disc(cx - r * 0.4, cy - r * 0.4, r * 0.3, MET_L)
    px(cx - r * 0.5, cy - r * 0.5, MET_XL)
    for k in range(8):                                      # a band of rivets
        a = k * math.pi / 4
        px(cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2) * 0.3, MET_XL if k < 4 else MET)
    rect(cx - 2, cy - r - 4, cx + 2, cy - r, MET_D)         # the lifting eye
    ring(cx, cy - r - 5, 2.5, MET_L)


def plank_wall(x, floor, h, w=8):
    """Vertical planks side-on: a wall the ball goes through."""
    for k in range(0, w, 3):
        hh = h - (k * 7 % 5)
        rect(x + k, floor - hh, x + k + 2, floor - 1, WOOD if k % 2 else WOOD_D)
        rect(x + k, floor - hh, x + k, floor - 1, WOOD_L)
    for yy in (floor - h + 6, floor - 8):
        rect(x - 1, yy, x + w, yy + 1, WOOD_D)


def jib_crane(X, Y, m):
    fy = Y(SHELF)
    mx = X(MAST_X)
    top = Y(JIB_Y - 30)
    beam(mx - 2, top, fy - 1, 5, WOOD, WOOD_L)                 # mast
    rect(mx - 9, fy - 4, mx + 12, fy - 1, WOOD_D)             # its foot, and the kneebraces
    line(mx - 8, fy - 1, mx - 2, fy - 18, WOOD_D)
    line(mx + 11, fy - 1, mx + 3, fy - 18, WOOD_D)
    jy = Y(JIB_Y)
    jx1 = X(PIVOT[0] + 8)
    for t in range(4):                                       # the jib
        rect(mx - 2, jy + t, jx1, jy + t, WOOD_L if t == 0 else WOOD if t < 3 else WOOD_D)
    for k in range(mx + 10, jx1, 18):
        rect(k, jy + 1, k, jy + 2, WOOD_D)
    for t in range(3):                                       # the strut under it
        line(mx + 3, Y(JIB_Y + 50) + t, X(MAST_X + 70), jy + 3 + t, WOOD if t < 2 else WOOD_D)
    line(mx + 1, top + 2, jx1 - 2, jy, MET_D)                # the stay, masthead to jib end
    line(mx + 1, top + 3, jx1 - 2, jy + 1, MET)
    line(mx, top + 4, X(8), Y(JIB_Y + 30), MET_D)            # backstay to the wall
    disc(X(8), Y(JIB_Y + 30), 2.5, MET_L)
    rect(mx - 4, top - 2, mx + 6, top, MET_D)                # masthead cap
    # the sheave at the jib's end that the chain runs over
    px_, py_ = X(PIVOT[0]), Y(PIVOT[1])
    disc(px_, py_, 4, MET)
    ring(px_, py_, 4, MET_L)
    px(px_, py_, INK)
    # the winch on the shelf, its rope up the mast
    wx, wy = X(118), fy - 9
    rect(wx - 6, wy - 4, wx + 6, wy + 4, WOOD_D)
    disc(wx, wy, 4, MET)
    ring(wx, wy, 4, MET_L)
    line(wx + 4, wy, wx + 10, wy - 6, MET_L)
    rect(wx - 7, fy - 2, wx + 7, fy - 1, WOOD_D)


def ball_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx: Y(int(floor_y(lx)))

    teeth(m, X(120), X(380), Y(120), 22)
    teeth(m, X(20), X(110), Y(100), 6)
    for (x, y, rx, ry) in ((10, 290, 14, 20), (390, 270, 14, 16), (260, 30, 30, 14)):
        rock_blob(X(x), Y(y), rx, ry, rough=0.22)

    # the shelf's lip, lit, and the alcove under it
    jib_crane(X, Y, m)

    # the swing it will make: dotted arc, west tie-off to the east wall and back
    pvx, pvy = X(PIVOT[0]), Y(PIVOT[1])
    for i in range(70):
        a = -TIE_A + 2 * TIE_A * i / 69.0
        if i % 2 == 0:
            x = pvx + math.sin(a) * CHAIN
            y = pvy + math.cos(a) * CHAIN
            rect(x, y, x + 1, y + 1, (210, 200, 168), 0.7)

    # the ball, hauled back and tied off
    bx = pvx - math.sin(TIE_A) * CHAIN
    by = pvy + math.cos(TIE_A) * CHAIN
    slant_chain(pvx, pvy + 2, bx, by - BALL_R - 6)
    iron_ball(bx, by, BALL_R)
    mx = X(MAST_X)                                           # tied off to the mast
    rope(bx - 3, by - BALL_R - 4, mx + 2, by - 18)
    rope(bx - BALL_R + 1, by + 2, mx + 2, by - 4)
    for i in range(4):
        rect(mx - 3, by - 20 + i * 2, mx + 5, by - 20 + i * 2, ROPE)
        rect(mx - 3, by - 6 + (i % 2) * 2, mx + 5, by - 6 + (i % 2) * 2, ROPE)
    stand("WizBogcap", X(100), Y(SHELF), flip=True)
    # a lamp line strung from the jib's end to the east wall
    ew = X(330)
    while (ew, Y(110)) in m:
        ew += 1
    cable(pvx + 4, pvy + 2, ew, Y(110), sag=16, c=MET_D)
    for f in (0.3, 0.62):
        lx_ = pvx + 4 + (ew - pvx - 4) * f
        ly_ = pvy + 2 + (Y(110) - pvy - 2) * f + 16 * math.sin(math.pi * f)
        lamp(lx_, ly_, drop=3, bulb=LAMP, tint=LAMP, r=40, strength=0.12)
    lamp(X(MAST_X + 1), Y(JIB_Y + 4), drop=8, bulb=LAMP, tint=LAMP, r=60, strength=0.14)

    # the bowl: timber across the bottom of the swing, and the crew behind it
    plank_wall(X(160), fl(160), 34, 9)
    line(X(170), fl(172) - 1, X(160 + 9), fl(160) - 30, WOOD_D)     # prop
    line(X(184), fl(184) - 1, X(169), fl(169) - 22, WOOD_D)
    stand("RiotBrute", X(184), fl(184), flip=True)
    stand("Gaper", X(214), fl(214), flip=True)
    hx0, hx1 = 248, 300                                      # the hut
    hf = fl(274)
    plank_wall(X(hx0), hf, 40, 7)
    plank_wall(X(hx1 - 6), hf, 40, 7)
    for t in range(3):
        line(X(hx0 - 4), hf - 42 + t, X(hx1 + 4), hf - 46 + t,
             WOOD_L if t == 0 else WOOD if t == 1 else WOOD_D)
    stand("Grenadier", X(264), hf, flip=True)
    stand("WizGoldhood", X(284), hf, flip=True)
    keg(X(hx0 + 8), hf)
    lamp(X(274), hf - 44, drop=2, bulb=LAMP, tint=LAMP, r=34, strength=0.12)
    # the lean-to on the east slope
    ex = 340
    plank_wall(X(ex), fl(ex), 30, 7)
    for t in range(3):
        line(X(ex - 3), fl(ex) - 32 + t, X(396), fl(396) - 44 + t, WOOD if t < 2 else WOOD_D)
    stand("Pyro", X(364), fl(364), flip=True)
    crate_g(X(378), fl(380), 10)
    corpse(X(128), fl(128))

    # the alcove under the shelf
    stand("Minespider", X(70), fl(70))
    crate_g(X(36), fl(36), 11)
    lamp(X(90), Y(SHELF + 22), drop=3, bulb=LAMP, tint=LAMP, r=36, strength=0.12)

    # the east ledge, in reach of the end of the swing
    stand("Sentinel", X(386), Y(132), flip=True)
    stand("Ghast", X(320), Y(118), flip=True)
    hook_x = X(140)                                          # a spare hook block off the jib
    chain(hook_x, Y(JIB_Y + 4), Y(JIB_Y + 34))
    rect(hook_x - 3, Y(JIB_Y + 34), hook_x + 4, Y(JIB_Y + 40), MET_D)
    line(hook_x, Y(JIB_Y + 40), hook_x, Y(JIB_Y + 46), MET_L)
    line(hook_x, Y(JIB_Y + 46), hook_x + 3, Y(JIB_Y + 44), MET_L)


ROOM = {
    "name": "THE WRECKING BALL", "w": 400, "h": 340,
    "shapes": [([("blob", 214, 172, 194, 142),               # the swing
                 ("blob", 210, 256, 196, 30),                  # the floor, wide
                 ("blob", 80, 90, 76, 66)], 0.07),             # head room for the mast
               ([("blob", 330, 70, 40, 26)], 0.14)],           # a bell off the east roof
    "sockets": {"T1": ("T", 150, 38), "T2": ("T", 330, 52),
                "L1": ("L", SHELF, 26), "L2": ("L", BOWL, 50),
                "R1": ("R", EAST, 16), "R2": ("R", 132, 24)},
    "edit": ball_edit,
    "furnish": ball_furnish,
}


SHEET = {
    "seed": 72801,
    "callouts": [
        ("1 CUT THE TIE", (-124, 206), (40, 170)),
        ("2 IRON BALL ON THE JIB", (-124, -46), (64, 158)),
        ("3 TIMBER IN ITS PATH", (300, 360), (300, 250)),
    ],
    "beats": [
        ("CUT THE TIE: THE BALL SWINGS THROUGH THE BARRICADE, THE HUT AND THE LEAN-TO", (170, 180, 195)),
        ("AND BACK AGAIN - THE BOWL IS NO PLACE TO STAND, THE SHELF IS", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
