"""Small room S19 - THE STAMP MILL.

A low hall round a stamp battery: five iron-shod stamps on a timber frame, lifted by
cams on one shaft and dropped, over and over, onto a mortar bed. A feed belt runs under
them from the ore bin in the east to the fines pit in the west, and everything on the
belt goes under the stamps - ore, and the enemies standing on it. The drive is a belt
off a flywheel in the west alcove.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S19"

HALL_FLOOR = 274
ALCOVE_FLOOR = 212
BIN_FLOOR, BIN_LIP = 152, 338
BELT_Y = 244                      # top of the feed belt
BELT_X0, BELT_X1 = 122, 392
POSTS = (150, 252)                # the battery frame
HEADER = 162
CAM_Y = 188
STAMPS = (169, 185, 201, 217, 233)
LIFT = (0, 12, 19, 6, 0)          # how far each stamp is up, this frame
FLY = (60, 186, 18)               # flywheel in the west alcove


def mill_edit(air, ox, oy):
    """Flatten the hall floor east of the pit."""
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > HALL_FLOOR and 160 < lx < 380:
            continue
        if ly > ALCOVE_FLOOR and lx < 104 and ly < 240:
            continue
        if BIN_FLOOR <= ly <= 232 - (lx - 340) * 0.0 and lx > BIN_LIP + (ly - BIN_FLOOR) * 0.55 + 3 * math.sin(ly * 0.4):
            continue
        out.add((x, y))
    return out


def stamp(cx, belt, lift, top_stop):
    """One stamp: the iron shoe and head, the stem, a tappet collar."""
    bot = belt - 1 - lift
    hx0, hx1 = int(cx - 6), int(cx + 6)
    rect(hx0, bot - 17, hx1, bot, MET)                  # head
    rect(hx0, bot - 17, hx1, bot - 17, MET_XL)
    rect(hx0, bot - 4, hx1, bot, MET_D)                 # shoe
    rect(hx0, bot - 11, hx1, bot - 10, MET_D)
    rect(hx0, bot - 17, hx0, bot, MET_L)
    rect(hx1, bot - 17, hx1, bot, MET_D)
    sx = int(cx - 1)
    rect(sx, top_stop - lift, sx + 2, bot - 18, MET_L)  # stem
    rect(sx + 2, top_stop - lift, sx + 2, bot - 18, MET_D)
    ty = CAM_Y_ABS[0] + 6 - lift
    rect(sx - 3, ty, sx + 5, ty + 3, MET_D)             # tappet
    rect(sx - 3, ty, sx + 5, ty, MET_L)


CAM_Y_ABS = [0]


def flywheel(cx, cy, r):
    disc(cx, cy, r, MET_D)
    disc(cx, cy, r - 3, CAVE)
    ring(cx, cy, r, MET_L)
    ring(cx, cy, r - 3, MET)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        line(cx, cy, cx + math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3), MET)
    disc(cx, cy, 3, MET_L)
    disc(cx, cy, 1, INK)


def mill_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly: floor_at(m, X(lx), Y(ly))
    CAM_Y_ABS[0] = Y(CAM_Y)
    belt = Y(BELT_Y)
    hf = Y(HALL_FLOOR)

    teeth(m, X(110), X(330), Y(150), 20)
    teeth(m, X(20), X(110), Y(180), 6)

    # the frame: two posts, a header, knee braces, guide timbers for the stems
    for px_ in POSTS:
        beam(X(px_ - 2), Y(HEADER), hf - 1, 5, WOOD, WOOD_L)
        rect(X(px_ - 2), Y(HEADER), X(px_ + 3), Y(HEADER), WOOD_D)
        rect(X(px_ - 6), hf - 3, X(px_ + 7), hf - 1, WOOD_D)          # sole plate
    rect(X(POSTS[0] - 6), Y(HEADER) - 6, X(POSTS[1] + 7), Y(HEADER), WOOD)
    rect(X(POSTS[0] - 6), Y(HEADER) - 6, X(POSTS[1] + 7), Y(HEADER) - 6, WOOD_L)
    rect(X(POSTS[0] - 6), Y(HEADER), X(POSTS[1] + 7), Y(HEADER), WOOD_D)
    for gy in (HEADER + 10, CAM_Y + 14):
        rect(X(POSTS[0] + 3), Y(gy), X(POSTS[1] - 2), Y(gy) + 2, WOOD_D)
        rect(X(POSTS[0] + 3), Y(gy), X(POSTS[1] - 2), Y(gy), WOOD)
    line(X(POSTS[0] + 3), Y(HEADER + 12), X(POSTS[0] + 12), Y(HEADER + 1), WOOD)
    line(X(POSTS[1] - 2), Y(HEADER + 12), X(POSTS[1] - 11), Y(HEADER + 1), WOOD)
    # roof bolts holding the header up to the rock
    for bx in (POSTS[0] + 10, 200, POSTS[1] - 22):
        top = ceil_at(m, X(bx), Y(HEADER - 8)) + 1
        if top > Y(HEADER - 60):
            line(X(bx), top, X(bx), Y(HEADER - 7), MET_D)

    # the mortar bed under the stamps
    rect(X(156), belt + 4, X(244), hf - 1, MET_D)
    rect(X(156), belt + 4, X(244), belt + 4, MET_L)
    for x in range(X(160), X(242), 10):
        rect(x, belt + 8, x + 5, belt + 9, (40, 40, 42))

    # the belt, west-running, on trestles to the floor
    conveyor(X(BELT_X0), X(BELT_X1), belt, direction=-1, chevron=(130, 150, 90))
    for lx in range(BELT_X0 + 6, BELT_X1, 26):
        if 150 < lx < 250:
            continue
        f = fl(lx, BELT_Y + 6)
        rect(X(lx), belt + 4, X(lx + 1), f - 1, WOOD_D)
        line(X(lx), f - 1, X(lx + 8), belt + 5, WOOD_D)

    # cam shaft, cams, drive pulley and belt from the flywheel
    rect(X(POSTS[0] - 10), Y(CAM_Y) - 1, X(POSTS[1] + 4), Y(CAM_Y) + 1, MET_D)
    rect(X(POSTS[0] - 10), Y(CAM_Y) - 1, X(POSTS[1] + 4), Y(CAM_Y) - 1, MET_L)
    for i, sx in enumerate(STAMPS):
        a = 1.1 * i + 0.4
        disc(X(sx + 4) + math.cos(a) * 2, Y(CAM_Y) + math.sin(a) * 2, 3.2, MET)
    for i, sx in enumerate(STAMPS):
        stamp(X(sx), belt, LIFT[i], Y(HEADER + 3))
    fx, fy, fr = FLY
    flywheel(X(fx), Y(fy), fr)
    disc(X(POSTS[0] - 10), Y(CAM_Y), 7, MET)
    ring(X(POSTS[0] - 10), Y(CAM_Y), 7, MET_L)
    line(X(fx), Y(fy - fr), X(POSTS[0] - 10), Y(CAM_Y - 7), (60, 52, 42))
    line(X(fx), Y(fy + fr), X(POSTS[0] - 10), Y(CAM_Y + 7), (60, 52, 42))
    af = Y(ALCOVE_FLOOR)
    rect(X(fx - 4), Y(fy), X(fx + 4), af - 1, MET_D)      # the pedestal
    rect(X(fx - 9), af - 3, X(fx + 9), af - 1, MET_D)
    rect(X(fx - 9), af - 3, X(fx + 9), af - 3, MET_L)
    stand("Pyro", X(fx + 30), af)
    keg(X(fx - 40), af)

    # what the stamps have got so far, and what is coming
    corpse(X(STAMPS[0]), belt, blood=RED)
    rect(X(STAMPS[4] - 6), belt - 2, X(STAMPS[4] + 6), belt - 1, ORE)
    for lx in (262, 296, 322, 352, 372):
        disc(X(lx), belt - 3, 2.5 + rnd() * 1.5, pick([ORE, ROCK_L, DIRT_L, ROCK_M]))
    stand("RiotBrute", X(280), belt)
    stand("Gaper", X(310), belt, flip=False)
    stand("WizHollowhood", X(338), belt, flip=False)
    for lx in (270, 300, 328):                          # dragged: chevron ghosts at their feet
        for k in range(3):
            px(X(lx - k * 3), belt - 1, (200, 205, 190), 0.5)

    # the ore bin up in the east and its chute onto the belt
    bin_f = Y(BIN_FLOOR)
    heap = [(x, bin_f - int(12 * (1 - ((x - 376) / 40.0) ** 2))) for x in range(340, 416)]
    for x, top in heap:
        if (X(x), Y(0) + top - oy) in m or True:
            for y in range(top, bin_f):
                if (X(x), y) in m:
                    r = rnd()
                    px(X(x), y, ORE if r < 0.15 else DIRT if r < 0.5 else ROCK_M if r < 0.8 else DIRT_D)
    for t in range(-2, 3):                               # the chute off the bin lip
        line(X(BIN_LIP + 2 + t), bin_f, X(350 + t), belt - 12, WOOD if t < 2 else WOOD_D)
    line(X(BIN_LIP - 1), bin_f, X(347), belt - 12, WOOD_L)
    line(X(BIN_LIP - 3), bin_f - 3, X(345), belt - 15, WOOD_D)
    line(X(BIN_LIP + 2), bin_f - 4, X(BIN_LIP + 2), bin_f, WOOD_D)
    for k in range(5):
        disc(X(342 + k * 2), bin_f + 6 + k * 3, 1.5, pick([ORE, DIRT_L, ROCK_L]))
    stand("Grenadier", X(404), bin_f - 9, flip=True)

    # the fines pit in the west: crushed ore off the belt's end
    pf = fl(100, 290)
    for x in range(80, 160):
        top = pf - int(12 * max(0.0, 1 - ((x - 124) / 30.0) ** 2))
        for y in range(top, pf):
            if (X(x), y) in m:
                px(X(x), y, DIRT if (x + y) % 3 else DIRT_L)
    for k in range(10):
        px(X(BELT_X0 - 3 - k % 3), belt + 4 + k * 2, pick([DIRT_L, ORE, DIRT]), 0.8)
    stand("Minespider", X(98), fl(98, 280))

    lamp(X(300), ceil_at(m, X(300), Y(180)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=90, strength=0.16)
    lamp(X(80), ceil_at(m, X(80), Y(190)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.14)
    stand("WizRamskull", X(412), fl(412, 250), flip=True)
    # an ore skip on a chain over the belt, and more rock off the hall roof
    teeth(m, X(270), X(330), Y(170), 8)
    chain(X(296), ceil_at(m, X(296), Y(180)) + 1, Y(196))
    rect(X(288), Y(196), X(305), Y(208), MET)
    rect(X(288), Y(196), X(305), Y(196), MET_XL)
    rect(X(289), Y(197), X(304), Y(198), ORE)
    rect(X(288), Y(203), X(305), Y(203), MET_D)


ROOM = {
    "name": "THE STAMP MILL", "w": 440, "h": 340,
    "shapes": [([("blob", 250, 202, 162, 78)], 0.08),           # the hall
               ([("blob", 70, 186, 54, 32),                     # drive alcove, west
                 ("blob", 362, 124, 48, 30),                    # ore bin, east
                 ("blob", 120, 290, 42, 26)], 0.12),            # fines pit
               ([("tube", [(380, 256), (444, 254)], 15)], 0.06)],  # east drift at belt foot
    "sockets": {"T1": ("T", 250, 128), "T2": ("T", 362, 100),
                "L1": ("L", ALCOVE_FLOOR, 22), "R1": ("R", 269, 20),
                "R2": ("R", 150, 36), "B1": ("B", 120, 28)},
    "edit": mill_edit,
    "furnish": mill_furnish,
}


SHEET = {
    "seed": 71901,
    "callouts": [
        ("1 FIVE STAMPS ON ONE CAM SHAFT", (-120, 60), (184, 196)),
        ("2 THEY RIDE THE BELT IN", (250, 360), (310, 246)),
        ("3 FLYWHEEL DRIVE", (-120, 240), (60, 186)),
    ],
    "beats": [
        ("THE STAMPS NEVER STOP: WHAT THE BELT BRINGS, THEY CRUSH", (170, 180, 195)),
        ("KNOCK THEM ONTO THE BELT, OR STOP THE FLYWHEEL TO WALK IT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
