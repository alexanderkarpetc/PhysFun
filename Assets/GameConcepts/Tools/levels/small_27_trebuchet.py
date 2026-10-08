"""Small room S27 - THE TREBUCHET.

A long, low lens of a cave with a trough down its middle. On the west knoll stands a
timber trebuchet, cocked: the counterweight box wound up high, the long arm hauled down
to the ground and pinned there by a trigger, a stone lying in the sling. It is laid on
the east rise, where the crew have built a timber hoarding - a log palisade with a fire
step and a plank roof - and shoot from behind it. Trip the trigger and the stone goes
over the trough and through the hoarding; wind it again with the windlass and it throws
again.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S27"

KNOLL = 238                     # the trebuchet's floor
TROUGH = 290
RISE = 252                      # the hoarding's floor
AXLE = (132, 160)
LONG, SHORT = 108, 32
ARM_A = math.asin((KNOLL - 8 - AXLE[1]) / float(LONG))   # cocked: long end on the ground
PERCH = 172
PAL_X = 330                     # west face of the palisade
ROPE = (166, 144, 100)
ROPE_D = (100, 82, 56)


def floor_y(lx):
    def ease(a, b, t):
        t = max(0.0, min(1.0, t))
        return a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * t))
    if lx < 176:
        return KNOLL
    if lx < 236:
        return ease(KNOLL, TROUGH, (lx - 176) / 60.0)
    if lx < 296:
        return TROUGH + 2 * math.sin(lx * 0.3)
    return ease(TROUGH, RISE, (lx - 296) / 34.0)


def treb_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= floor_y(lx):
            continue
        if ly >= PERCH and ((lx - 452) / 56.0) ** 2 + ((ly - PERCH - 8) / 12.0) ** 2 < 1:
            continue                                         # a perch off the east wall
        out.add((x, y))
    return out


def rope(x0, y0, x1, y1):
    line(x0, y0, x1, y1, ROPE)
    line(x0, y0 + 1, x1, y1 + 1, ROPE_D)


def timber(x0, y0, x1, y1, w=3):
    """A squared timber from one point to another, w thick, lit on top."""
    for t in range(w):
        line(x0, y0 + t, x1, y1 + t, WOOD_L if t == 0 else WOOD if t < w - 1 else WOOD_D)


def trebuchet(X, Y):
    ax, ay = X(AXLE[0]), Y(AXLE[1])
    fy = Y(KNOLL)
    ca, sa = math.cos(ARM_A), math.sin(ARM_A)
    # the frame: sole timbers, two A-frame legs to the axle, braces
    rect(X(78), fy - 4, X(192), fy - 1, WOOD_D)
    rect(X(78), fy - 4, X(192), fy - 4, WOOD)
    for fx in (94, 170):
        timber(X(fx), fy - 4, ax - 1, ay + 2, 5)
    timber(X(108), fy - 34, X(156), fy - 34, 3)
    timber(X(102), fy - 4, ax, ay + 36, 2)
    timber(X(162), fy - 4, ax + 2, ay + 36, 2)
    # the arm: long end down west to the ground, short end up east
    tip = (ax - LONG * ca, ay + LONG * sa)
    stub = (ax + SHORT * ca, ay - SHORT * sa)
    timber(tip[0], tip[1] - 2, stub[0], stub[1] - 2, 5)
    for k in range(4):                                       # iron bands
        f = 0.2 + k * 0.22
        bx, by = tip[0] + (stub[0] - tip[0]) * f, tip[1] + (stub[1] - tip[1]) * f
        rect(bx, by - 3, bx + 1, by + 3, MET_D)
    disc(ax, ay, 4, MET)
    ring(ax, ay, 4, MET_L)
    px(ax, ay, INK)
    # the counterweight: a timber box of rock, hung off the short end, wound up high
    bx, by = stub[0], stub[1]
    rect(bx - 1, by, bx + 1, by + 6, MET_D)
    rect(bx - 19, by + 6, bx + 19, by + 38, WOOD_D)
    rect(bx - 18, by + 7, bx + 18, by + 37, WOOD)
    for yy in range(int(by) + 13, int(by) + 38, 6):
        rect(bx - 18, yy, bx + 18, yy, WOOD_D)
    for xx in (bx - 9, bx + 9):
        rect(xx, by + 7, xx, by + 37, WOOD_D)
    rect(bx - 18, by + 7, bx + 18, by + 7, WOOD_L)
    for i in range(12):
        disc(bx - 15 + i * 2.8, by + 6, 2.4, pick([ROCK_L, ROCK_M, ROCK]))
    rect(bx - 20, by + 6, bx + 20, by + 7, MET_D)
    rect(bx - 20, by + 37, bx + 20, by + 38, MET_D)
    # the sling: from the tip back east along the trough, the stone in its pouch
    sx, sy = X(122), fy - 7
    rope(tip[0], tip[1] + 1, sx - 6, sy + 2)
    rope(tip[0] + 1, tip[1] + 3, sx - 6, sy + 4)
    disc(sx, sy, 6.5, ROCK_M)
    disc(sx - 1.5, sy - 1.5, 4, ROCK_L)
    disc(sx + 2, sy + 2, 2.5, ROCK)
    for t in range(-6, 7):
        px(sx + t, sy + 6 - abs(t) // 3, ROPE_D)
    # the trigger: an iron hook on the tip, a pin through a stake, a lanyard off it
    tx = X(16)
    rect(tx, fy - 14, tx + 3, fy - 1, WOOD)
    rect(tx - 1, fy - 15, tx + 4, fy - 14, WOOD_D)
    rope(tip[0] - 1, tip[1] + 1, tx + 4, fy - 10)
    rect(tx + 4, fy - 12, tx + 9, fy - 10, MET_L)            # the pin
    px(tx + 9, fy - 13, MET_XL)
    cable(tx + 9, fy - 11, tx + 30, fy - 2, sag=3, c=ROPE)   # lanyard to pull it
    # the windlass that cocks it
    wx, wy = X(184), fy - 13
    disc(wx, wy, 8, WOOD_D)
    ring(wx, wy, 8, WOOD_L)
    for k in range(4):
        a = k * math.pi / 4 + 0.3
        line(wx - math.cos(a) * 11, wy - math.sin(a) * 11, wx + math.cos(a) * 11, wy + math.sin(a) * 11, WOOD)
    disc(wx, wy, 2, MET_L)
    rope(wx, wy - 8, stub[0] + 1, stub[1] + 3)
    return tip, (sx, sy)


def hoarding(X, Y):
    """Log palisade with pointed tops, a plank fire step behind and a lean-to roof."""
    fy = Y(RISE)
    top = fy - 40
    for i, lx in enumerate(range(PAL_X, PAL_X + 14, 4)):
        h = 40 - (i % 2) * 3
        rect(X(lx), fy - h, X(lx) + 3, fy - 1, WOOD if i % 2 else WOOD_D)
        rect(X(lx), fy - h, X(lx), fy - 1, WOOD_L)
        px(X(lx) + 1, fy - h - 1, WOOD_L)
        px(X(lx) + 2, fy - h - 1, WOOD)
        px(X(lx) + 1, fy - h - 2, WOOD_L)
    for yy in (fy - 30, fy - 12):                            # wales across the logs
        rect(X(PAL_X - 1), yy, X(PAL_X + 14), yy + 1, WOOD_D)
    rect(X(PAL_X + 3), fy - 26, X(PAL_X + 5), fy - 22, INK)  # a loophole
    # fire step behind
    step = fy - 16
    rect(X(PAL_X + 14), step, X(PAL_X + 64), step + 2, WOOD)
    rect(X(PAL_X + 14), step, X(PAL_X + 64), step, WOOD_L)
    for lx in (PAL_X + 20, PAL_X + 42, PAL_X + 62):
        rect(X(lx), step + 3, X(lx) + 2, fy - 1, WOOD_D)
    # the roof: planks from the palisade top up to the east wall
    for t in range(3):
        line(X(PAL_X - 2), top - 6 + t, X(PAL_X + 110), top - 34 + t,
             WOOD_L if t == 0 else WOOD if t == 1 else WOOD_D)
    for lx in range(PAL_X + 6, PAL_X + 100, 16):            # rafters' ends
        yy = top - 6 - (lx - PAL_X + 2) * 28 / 112.0
        rect(X(lx), yy + 3, X(lx) + 1, yy + 6, WOOD_D)
    rect(X(PAL_X + 80), top - 22, X(PAL_X + 83), fy - 1, WOOD)      # the roof's post
    rect(X(PAL_X + 80), top - 22, X(PAL_X + 80), fy - 1, WOOD_L)
    return step


def treb_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx: Y(int(floor_y(lx)))

    teeth(m, X(140), X(330), Y(110), 22)
    teeth(m, X(30), X(140), Y(140), 8)
    teeth(m, X(330), X(440), Y(150), 8)
    # a lip of roof rock over the trough, and shelves off both walls
    rock_blob(X(250), Y(84), 46, 26, rough=0.2)
    rock_blob(X(284), Y(100), 18, 16, rough=0.25)
    rock_blob(X(14), Y(180), 16, 30, rough=0.2)
    rock_blob(X(446), Y(196), 14, 26, rough=0.2)

    # the throw it is laid for: a high lob, over the trough onto the hoarding roof
    for i in range(0, 60):
        t = i / 59.0
        x = X(128) + (X(350) - X(128)) * t
        y = Y(118) + (Y(214) - Y(118)) * t - 110 * t * (1 - t)
        if i % 3 == 0:
            rect(x, y, x + 1, y, (200, 190, 160), 0.45)

    tip, stone = trebuchet(X, Y)
    for (lx, r, up) in ((56, 6, 0), (69, 6, 0), (62, 5, 10)):          # spare shot
        disc(X(lx), Y(KNOLL) - r - up, r, ROCK_M)
        disc(X(lx) - 2, Y(KNOLL) - r - up - 2, r * 0.45, ROCK_L)
        px(X(lx) + 2, Y(KNOLL) - r - up + 2, ROCK_D)
    lamp(X(196), ceil_at(m, X(196), Y(150)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=70, strength=0.14)
    stand("RiotBrute", X(214), fl(214))

    # the trough: what the last throws left, and what lives in it now
    for (lx, r) in ((222, 6), (258, 9), (282, 5), (300, 7)):
        rock_blob(X(lx), fl(lx) - r // 2, r + 3, r, rough=0.3)
    corpse(X(256), fl(256))
    for k in range(5):
        line(X(262 + k * 3), fl(262) - 1, X(266 + k * 4), fl(262) - 8 - k, WOOD_D)   # a smashed mantlet
    stand("Minespider", X(276), fl(276))
    stand("Gaper", X(240), fl(240) , flip=True)
    # a stalagmite stump in the trough, under the line of the throw
    base = fl(300)
    for k, (dx, dy, rx, ry) in enumerate(((0, -6, 14, 10), (-2, -20, 10, 10), (1, -32, 7, 9), (-1, -42, 4, 7))):
        rock_blob(X(300) + dx, base + dy, rx, ry, rough=0.22)
    chain(X(196), ceil_at(m, X(196), Y(150)) + 1, Y(126))
    stand("Ghast", X(262), Y(176), flip=True)
    stand("Reaper", X(416), Y(PERCH), flip=True)
    cage(X(286), Y(122), Y(146), ceil_at(m, X(286), Y(110)) + 1)

    # the hoarding and the crew behind it
    step = hoarding(X, Y)
    fy = Y(RISE)
    stand("Grenadier", X(PAL_X + 24), step, flip=True)
    stand("WizDeepminer", X(PAL_X + 48), step, flip=True)
    stand("Pyro", X(PAL_X + 96), fy, flip=True)
    keg(X(PAL_X + 66), fy)
    keg(X(PAL_X + 75), fy)
    crate_g(X(PAL_X + 104), fy, 11)
    crate_g(X(PAL_X + 106), fy - 12, 9)
    lamp(X(PAL_X + 56), Y(RISE) - 52, drop=3, bulb=LAMP, tint=LAMP, r=40, strength=0.12)
    for k in range(4):                                       # bolts stuck in the palisade
        line(X(PAL_X - 6), fy - 34 + k * 7, X(PAL_X), fy - 33 + k * 7, MET_L)
    stand("WizCrimson", X(410), fy, flip=True)


ROOM = {
    "name": "THE TREBUCHET", "w": 460, "h": 330,
    "shapes": [([("blob", 232, 190, 220, 106),               # the lens
                 ("blob", 258, 262, 76, 40)], 0.07),           # the trough
               ([("blob", 70, 118, 46, 34),                    # a bell off the west roof
                 ("blob", 386, 136, 52, 34)], 0.12)],          # and one off the east
    "sockets": {"T1": ("T", 70, 90), "T2": ("T", 386, 100), "T3": ("T", 232, 86),
                "L1": ("L", KNOLL, 12), "R1": ("R", RISE, 40), "B1": ("B", 262, 44)},
    "edit": treb_edit,
    "furnish": treb_furnish,
}


SHEET = {
    "seed": 72701,
    "callouts": [
        ("1 COCKED, STONE IN THE SLING", (-124, 330), (122, 228)),
        ("2 PULL THE PIN", (-124, 290), (24, 226)),
        ("3 TIMBER HOARDING", (330, 350), (338, 236)),
    ],
    "beats": [
        ("PULL THE PIN: THE STONE GOES OVER THE TROUGH AND THROUGH THE HOARDING", (170, 180, 195)),
        ("THE CREW SHOOTS FROM BEHIND TIMBER - WIND THE WINDLASS AND THROW AGAIN", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
