"""Small room S33 - THE ROOTS.

A round chamber that a tree found from above. Its root mass has come down through the
roof as one trunk and split: a thick root runs down to the west wall, another down to
the floor - the ways up and down the room - and two more run east under a piece of the
roof that has parted along a crack. They wrap under it and into the east wall, and they
are all that holds it. Hair roots hang off everything. The crew camp under the loose roof.
Roots are wood: set them alight and they burn back along their length, and when the two
under the slab go, the roof comes down on the camp.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S33"

FLOOR = 358
SLAB_X0, SLAB_X1 = 216, 336
SLAB = set()
SLAB_C = (76, 74, 68)
SLAB_L = (110, 106, 96)
SLAB_D = (48, 47, 44)
BARK = (86, 70, 54)
BARK_L = (120, 98, 72)
BARK_D = (54, 43, 33)
HAIR = (70, 58, 46)
TRUNK_X = 168

# roots: (polyline in local coords, radius at start, radius at end)
ROOT_W = ([(TRUNK_X - 6, 130), (130, 170), (92, 206), (56, 236), (18, 252)], 8, 5)      # to the west wall
ROOT_F = ([(TRUNK_X + 2, 150), (164, 214), (146, 276), (126, 330), (114, FLOOR + 6)], 9, 5)  # to the floor
ROOT_S1 = ([(TRUNK_X + 10, 132), (206, 168), (238, 200), (276, 210), (312, 204),
            (340, 186), (372, 170), (396, 166)], 7, 5)                                    # under the slab
ROOT_S2 = ([(TRUNK_X + 14, 150), (214, 196), (252, 214), (292, 218), (326, 210),
            (356, 200), (396, 196)], 6, 4)


def slab_bottom(lx):
    t = (lx - (SLAB_X0 + SLAB_X1) / 2.0) / ((SLAB_X1 - SLAB_X0) / 2.0)
    return 180 + 22 * math.sqrt(max(0.0, 1 - t * t)) + 2 * math.sin(lx * 0.37)


def floor_line(lx):
    return FLOOR + 4 * math.sin(lx * 0.045 + 1.0)


def roots_edit(air, ox, oy):
    out = {(x, y) for (x, y) in air if y - oy < floor_line(x - ox)}
    SLAB.clear()
    roofs = {}
    for (x, y) in out:
        lx = x - ox
        if SLAB_X0 <= lx < SLAB_X1 and y - oy < roofs.get(lx, 10 ** 6):
            roofs[lx] = y - oy
    for lx, roof in roofs.items():
        for ly in range(roof + 3, int(slab_bottom(lx)) + 1):
            SLAB.add((lx, ly))
            out.discard((ox + lx, oy + ly))
    return out


def paint_slab(ox, oy, m):
    """The loose roof: rock gone dirty with soil that has washed down the root runs,
    bedding across it, and the crack round its top in ink."""
    for (lx, ly) in SLAB:
        r = rnd()
        px(ox + lx, oy + ly, SLAB_D if r < 0.12 else DIRT if r < 0.2 else ROCK_M if r < 0.27 else SLAB_C)
    for k in range(4):
        base = 120 + k * 16
        for lx in range(SLAB_X0, SLAB_X1):
            ly = int(base + 3 * math.sin(lx * 0.05 + k))
            if (lx, ly) in SLAB and (lx, ly - 2) in SLAB and (lx, ly + 2) in SLAB:
                px(ox + lx, oy + ly, SLAB_D, 0.7)
    for (lx, ly) in SLAB:
        if (lx, ly + 1) not in SLAB:
            px(ox + lx, oy + ly, SLAB_L)
        if (lx, ly - 1) not in SLAB:
            for d in range(1, 4):
                px(ox + lx, oy + ly - d, INK)
        for d in (-1, 1):                                  # the crack down its sides
            if (lx + d, ly) not in SLAB and (ox + lx + d, oy + ly) not in m:
                px(ox + lx + d, oy + ly, INK)
                px(ox + lx + 2 * d, oy + ly, INK, 0.6)


def _along(pts, r0, r1, step=0.7):
    total = sum(math.hypot(bx - ax, by - ay) for (ax, ay), (bx, by) in zip(pts, pts[1:]))
    s = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ln = math.hypot(bx - ax, by - ay)
        n = max(int(ln / step), 1)
        for i in range(n):
            t = i / n
            yield ax + (bx - ax) * t, ay + (by - ay) * t, r0 + (r1 - r0) * ((s + ln * t) / total)
        s += ln


def root(pts, r0, r1, ox, oy):
    """A root: a tapering wooden rope with a lit back and a dark belly, bark flecks
    along it - wobbly enough that it reads as grown, not laid."""
    P = [(ox + x, oy + y) for x, y in pts]
    for x, y, r in _along(P, r0, r1):
        disc(x, y, r, BARK)
    for x, y, r in _along(P, r0, r1, 1.5):
        px(x, y - r + 1, BARK_L)
        px(x, y - r + 2, BARK_L, 0.5)
        px(x, y + r - 1, BARK_D)
        if chance(0.2):
            px(x + rnd() * 2 - 1, y + (rnd() - 0.5) * r, BARK_D)
    return P


def root_y(pts, r0, r1, lx):
    """Top surface of a root at local x (for standing things on it)."""
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if min(ax, bx) <= lx <= max(ax, bx) and ax != bx:
            t = (lx - ax) / float(bx - ax)
            return ay + (by - ay) * t - (r0 + (r1 - r0) * 0.5)
    return None


def hair(x, y, ln, drift=0):
    """A hair root hanging: one pixel wide, kinked, paler at the tip."""
    cx = x
    for i in range(int(ln)):
        if chance(0.25):
            cx += pick([-1, 1]) + drift * 0.2
        px(cx, y + i, HAIR if i < ln - 2 else BARK_L)


def roots_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    paint_slab(ox, oy, m)
    teeth(m, X(40), X(150), Y(160), 10)
    teeth(m, X(340), X(380), Y(200), 3)
    for (bx, by, rx, ry, d) in ((30, 310, 14, 9, -1), (380, 300, 12, 9, 1), (380, 240, 9, 6, 1)):
        x0 = X(bx)
        while (x0, Y(by)) in m:
            x0 += d
        rock_blob(x0 - d * 4, Y(by), rx, ry, rough=0.25)

    # the trunk: down through the roof, flaring where it took the rock
    for y in range(-2, 150):
        t = max(0.0, (y - 40) / 110.0)
        r = 15 - 6 * t + (5 if 70 < y < 104 else 0) * math.sin((y - 70) / 34.0 * math.pi)
        wob = 3 * math.sin(y * 0.07)
        x0, x1 = X(TRUNK_X + wob - r), X(TRUNK_X + wob + r)
        rect(x0, Y(y), x1, Y(y), BARK)
        px(x0, Y(y), BARK_L)
        px(x0 + 1, Y(y), BARK_L, 0.5)
        px(x1, Y(y), BARK_D)
        if y % 5 == 0:
            for k in range(3):
                px(x0 + 3 + rnd() * (x1 - x0 - 6), Y(y) + rnd() * 3, BARK_D)
    for k in range(9):                                     # stones the roots grew round
        a = rnd() * 6.28
        disc(X(TRUNK_X + math.cos(a) * 8), Y(60 + rnd() * 50), 1.5 + rnd(), pick([ROCK_L, ROCK_M, STONE_D]))
    for (side, y0, ln, dy) in ((-1, 14, 40, 14), (1, 26, 52, 4), (-1, 52, 30, -6), (1, 66, 34, 16)):
        root([(TRUNK_X + side * 10, y0), (TRUNK_X + side * (ln * 0.5), y0 + dy * 0.6 + 3),
              (TRUNK_X + side * ln, y0 + dy)], 3, 1, ox, oy)

    # the roots that hold the slab first (behind), then the walkable ones
    for pts, r0, r1 in (ROOT_S2, ROOT_S1):
        root(pts, r0, r1, ox, oy)
    for lx in (230, 262, 300, 326):                        # fingers up into the crack
        y0 = slab_bottom(lx)
        root([(lx, y0 + 6), (lx + 3, y0 - 10), (lx - 2, y0 - 26), (lx + 2, y0 - 40)], 3, 1, ox, oy)
    for pts, r0, r1 in (ROOT_W, ROOT_F):
        root(pts, r0, r1, ox, oy)

    # hair roots off the roof and the roots
    for _ in range(40):
        lx = 40 + rnd() * 320
        if SLAB_X0 - 4 < lx < SLAB_X1 + 4:
            y0 = Y(slab_bottom(lx)) + 1
        else:
            y0 = ceil_at(m, X(lx), Y(220)) + 1
        hair(X(lx), y0, 5 + rnd() * 18)
    for pts, r0, r1 in (ROOT_W, ROOT_S1, ROOT_S2):
        for x, y, r in list(_along(pts, r0, r1, 9))[1:-1]:
            if chance(0.6):
                hair(X(x), Y(y + r - 1), 4 + rnd() * 14)

    # it has gone before: a root burned through, and what it was holding, on the floor
    root([(206, 200), (204, 226), (210, 250), (206, 266)], 4, 3, ox, oy)
    for k in range(7):
        px(X(204 + rnd() * 5), Y(262 + k), CHAR if k > 1 else BARK_D)
    px(X(207), Y(268), F_COOL)
    px(X(205), Y(270), F_MID, 0.8)
    rock_blob(X(196), Y(floor_line(196)) - 2, 26, 12, rough=0.3, clip=(X(160), Y(200), X(240), Y(floor_line(196)) + 1))
    for _ in range(14):
        disc(X(168 + rnd() * 56), Y(floor_line(196)) - 8 - rnd() * 6, 1.5 + rnd() * 2.5, pick([SLAB_C, SLAB_D, ROCK_M]))
    for k in range(4):
        line(X(172 + k * 12), Y(floor_line(190)) - 14 - k % 2 * 3, X(178 + k * 12), Y(floor_line(190)) - 10, CHAR)

    # the camp's way up: a rope ladder off the cradle, and a sack of stores hung off it
    rope = (120, 104, 78)
    lx0, ytop = 270, 214
    fy0 = floor_line(270)
    for x in (lx0, lx0 + 6):
        for y in range(ytop, int(fy0)):
            px(X(x + (1 if (y // 9) % 2 else 0)), Y(y), rope)
    for y in range(ytop + 6, int(fy0) - 2, 7):
        rect(X(lx0 + 1), Y(y), X(lx0 + 5), Y(y), WOOD)
    line(X(306), Y(218), X(306), Y(256), rope)
    sack_c, sack_l = (148, 128, 92), (178, 158, 116)
    rect(X(300), Y(256), X(312), Y(270), sack_c)
    rect(X(299), Y(259), X(313), Y(267), sack_c)
    rect(X(300), Y(256), X(312), Y(256), sack_l)
    for pts, r0, r1 in (ROOT_S1, ROOT_S2):                 # long hair off the cradle
        for x, y, r in list(_along(pts, r0, r1, 6))[3:-3]:
            if chance(0.5):
                hair(X(x), Y(y + r - 1), 10 + rnd() * 26)

    # shelf fungus on the floor root, pale, no glow
    for (lx, ly) in ((150, 250), (140, 280), (132, 300)):
        rect(X(lx - 6), Y(ly), X(lx - 1), Y(ly) + 1, (176, 160, 130))
        px(X(lx - 6), Y(ly) + 2, (130, 118, 96))

    # the camp under the loose roof
    fl = lambda lx: Y(floor_line(lx)) + 1
    for cx in (250, 314):
        lamp(X(cx), Y(slab_bottom(cx)) + 1, drop=6, bulb=LAMP, tint=LAMP, r=56, strength=0.14)
    crate_g(X(340), fl(346), 11)
    crate_g(X(342), fl(346) - 12, 9)
    keg(X(222), fl(226))
    for bx in (262, 300):                                   # bedrolls
        f = fl(bx + 6)
        rect(X(bx), f - 3, X(bx + 13), f - 1, (92, 70, 60))
        rect(X(bx), f - 3, X(bx + 13), f - 3, (122, 96, 80))
    stand("Gaper", X(244), fl(244))
    stand("RiotBrute", X(284), fl(284), flip=True)
    stand("WizBogcap", X(322), fl(322), flip=True)
    corpse(X(204), fl(204))

    # on the roots, and round the sides
    pts, r0, r1 = ROOT_W
    stand("Pyro", X(104), Y(root_y(pts, r0, r1, 104)) + 1, flip=True)
    stand("Sentinel", X(36), Y(root_y(pts, r0, r1, 36)) + 1)
    stand("Minespider", X(372), fl(372), flip=True)
    stand("Gaper", X(60), fl(60))
    scrap_pile(X(70), fl(80), 26, 5, colors=(DIRT, ROCK_M, BARK_D, DIRT_D))
    lamp(X(124), ceil_at(m, X(124), Y(200)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=60, strength=0.13)


ROOM = {
    "name": "THE ROOTS", "w": 400, "h": 420,
    "shapes": [([("blob", 200, 236, 172, 150)], 0.09),
               ([("blob", 86, 110, 46, 30),                  # pocket under T1
                 ("blob", 352, 140, 30, 26),                 # pocket under T2
                 ("blob", 52, 338, 50, 24),                  # floor pocket west
                 ("blob", 350, 338, 48, 24),                 # floor pocket east
                 ("tube", [(TRUNK_X, 110), (TRUNK_X, 60)], 22)], 0.12)],   # where the trunk came in
    "sockets": {"T1": ("T", 80, 84), "T2": ("T", 354, 118),
                "L1": ("L", 252, 22), "L2": ("L", FLOOR, 12), "R1": ("R", FLOOR, 14)},
    "edit": roots_edit,
    "furnish": roots_furnish,
}


SHEET = {
    "seed": 73301,
    "callouts": [
        ("1 ONLY THE ROOTS HOLD IT", (190, -46), (300, 214)),
        ("2 ROOTS ARE WOOD: THEY BURN", (-120, 432), (110, 192)),
        ("3 THE CAMP UNDER IT", (240, 432), (280, 340)),
    ],
    "beats": [
        ("WALK THE ROOTS UP AND DOWN, OR SET THEM ALIGHT", (170, 180, 195)),
        ("BURN THE TWO UNDER THE SLAB AND THE ROOF COMES DOWN ON THE CAMP", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
