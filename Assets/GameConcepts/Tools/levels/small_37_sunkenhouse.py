"""Small room S37 - THE SUNKEN HOUSE.

A two-storey stone house the ground took down with it. It came to rest at 24 degrees:
its high corner on a rock ledge by the west entry, its low corner sunk in its own
rubble, and the cave wall has grown into its west side. Every floor in it is a ramp
and every wall a slope, so everything in it - furniture, kegs, bodies, whatever is
dropped or knocked over - slides downhill and piles against the low wall of each room.
The one level floor in the house is the west pitch of its roof.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402
import conceptkit as _ck  # noqa: E402

CODE = "S37"

ANG = 0.42                       # ~24 degrees, east side down
HC = (225, 211)                  # where the house's middle lands (local room coords)
BW, BH = 200, 190                # the house, drawn upright
TOP = 24                         # headroom over the ridge, for the chimney
FLOOR = 362
SLATE = (112, 66, 54)            # clay tile
SLATE_L = (150, 94, 72)
CLOTH = (96, 62, 66)
PLASTER = (110, 102, 88)


def in_swallow(lx, ly):
    """The cave's west wall, grown in over the house's west wall: a tongue of rock from
    the wall whose east edge runs parallel to the tilted wall, 16px inside the house."""
    edge = 166 - (ly - 136) * 0.446 + 4 * math.sin(ly * 0.3)
    return lx < edge and ly < 222 + 4 * math.sin(lx * 0.17)


def house_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > FLOOR:
            continue
        if lx < 92 + 3 * math.sin(ly * 0.5) and ly > 268:
            continue                                      # the ledge the high corner sits on
        if 214 < lx < 344 and ly > FLOOR - 26 * max(0.0, 1 - ((lx - 278) / 64.0) ** 2):
            continue                                      # rubble the low corner sank into
        if in_swallow(lx, ly):
            continue                                      # the cave wall, grown into the house
        if lx > 384 + 4 * math.sin(ly * 0.4) and 250 <= ly < 262 + (lx - 384) * 0.3:
            continue                                      # a shelf off the east wall
        out.add((x, y))
    return out


# ── the house, upright, in its own coords ───────────────────────────────────
UP_FLOOR, LOW_FLOOR = 112, 182          # tops of the middle floor and the ground slab


def wardrobe(x, y):                      # on its back, 30x10
    rect(x, y, x + 30, y + 9, WOOD_D)
    rect(x, y, x + 30, y, WOOD)
    rect(x + 2, y + 2, x + 13, y + 7, WOOD)
    rect(x + 16, y + 2, x + 28, y + 7, WOOD)
    px(x + 14, y + 5, MET_L)


def table_side(x, y):                    # on its side, legs out
    rect(x, y, x + 2, y + 16, WOOD)
    for k in (2, 13):
        rect(x + 3, y + k, x + 12, y + k + 1, WOOD_D)


def bed(x, y):
    rect(x, y + 4, x + 34, y + 9, WOOD_D)
    rect(x + 1, y, x + 33, y + 4, CLOTH)
    rect(x + 1, y, x + 33, y, (130, 92, 96))
    rect(x + 26, y - 2, x + 33, y + 1, PLASTER)
    rect(x, y - 6, x + 2, y + 9, WOOD_D)


def chair(x, y):
    rect(x, y, x + 1, y + 10, WOOD)
    rect(x, y + 5, x + 7, y + 6, WOOD)
    rect(x + 6, y + 6, x + 7, y + 10, WOOD_D)


def books(x, y, n=7):
    for k in range(n):
        rect(x + k * 3, y - 2 - (k % 3), x + k * 3 + 2, y, pick([RED, PURPLE, DIRT_L, GREEN, BLUE]))


def house_upright():
    w = BW
    # roof: two pitches of slate on rafters, the attic inside them
    for x in range(0, w):
        top = 2 + 38 * abs(x - 100) / 100.0
        for d in range(8):
            px(x, top + d, SLATE_L if d == 0 else SLATE if (x // 4 + d) % 3 else (82, 48, 40))
    rect(98, 0, 102, 4, SLATE_L)
    rect(96, 26, 104, 33, KEY)                                  # gable vent
    masonry(0, 40, w - 1, 47)                                  # wall plate
    masonry(0, 48, 9, BH - 1)                                  # west wall
    masonry(w - 10, 48, w - 1, BH - 1)                         # east wall
    masonry(8, UP_FLOOR, w - 9, UP_FLOOR + 7)                  # the middle floor
    masonry(0, LOW_FLOOR, w - 1, BH - 1)                       # the ground slab
    masonry(96, 48, 103, UP_FLOOR - 1)                         # upstairs partition
    masonry(120, UP_FLOOR + 8, 127, LOW_FLOOR - 1)             # downstairs partition
    rect(96, 80, 103, UP_FLOOR - 1, KEY)                       # doorways: gaps, nothing in them
    rect(120, 150, 127, LOW_FLOOR - 1, KEY)
    rect(0, 150, 9, LOW_FLOOR - 1, KEY)                        # the front door, west
    rect(0, 146, 11, 149, STONE_L)
    rect(150, UP_FLOOR, 172, UP_FLOOR + 7, KEY)                # stair hole
    for k in range(9):                                         # the stair, still nailed in
        rect(132 + k * 5, LOW_FLOOR - 6 - k * 7, 138 + k * 5, LOW_FLOOR - 5 - k * 7, WOOD)
    for (wy0, wy1) in ((70, 88),):                             # windows, east, upstairs
        rect(w - 10, wy0, w - 1, wy1, KEY)
        rect(w - 11, wy1 + 1, w, wy1 + 2, STONE_L)
    rect(w - 10, 142, w - 1, 162, KEY)                         # east wall burst, downstairs
    for k in range(6):
        rect(w - 10 + int(rnd() * 8), 138 + int(rnd() * 28), w - 8 + int(rnd() * 8),
             139 + int(rnd() * 28), KEY)
    for (x0, x1, y) in ((8, 95, 48), (104, 191, 48), (8, 119, UP_FLOOR + 8), (128, 191, UP_FLOOR + 8)):
        rect(x0, y, x1, y + 1, PLASTER)                        # ceiling plaster, cracked
        for _ in range((x1 - x0) // 6):
            px(x0 + rnd() * (x1 - x0), y + 2, PLASTER, 0.8)

    # upstairs west: a table and a chest, slid to the partition
    table_side(80, UP_FLOOR - 17)
    rect(64, UP_FLOOR - 10, 79, UP_FLOOR - 1, WOOD_D)           # chest
    rect(64, UP_FLOOR - 10, 79, UP_FLOOR - 10, WOOD_L)
    rect(70, UP_FLOOR - 7, 72, UP_FLOOR - 5, MET_L)
    books(88, UP_FLOOR - 18, 3)
    # upstairs east: the bed, a wardrobe on its back, a chair, all down at the east wall
    bed(152, UP_FLOOR - 10)
    wardrobe(158, UP_FLOOR - 22)
    chair(176, UP_FLOOR - 33)
    books(150, UP_FLOOR - 22 + 0, 4)
    # attic: crates slid to the east eave
    for cx, cy, s in ((150, 33, 6), (160, 33, 6), (156, 27, 6)):
        rect(cx, cy, cx + s, cy + s - 1, WOOD)
        frame(cx, cy, cx + s, cy + s - 1, WOOD_D)
    # downstairs west: the hearth on the west wall, crates and barrels at the partition
    masonry(8, LOW_FLOOR - 26, 22, LOW_FLOOR - 1)
    rect(10, LOW_FLOOR - 18, 20, LOW_FLOOR - 1, (30, 26, 25))
    for cx, cy in ((96, LOW_FLOOR - 13), (108, LOW_FLOOR - 13), (102, LOW_FLOOR - 26)):
        rect(cx, cy, cx + 11, cy + 12, WOOD)
        frame(cx, cy, cx + 11, cy + 12, WOOD_D)
        line(cx, cy, cx + 11, cy + 12, WOOD_D)
    # downstairs east: everything else, piled at the burst wall
    for k in range(18):
        x = 160 + rnd() * 30
        y = LOW_FLOOR - 2 - rnd() * (x - 150) * 0.5
        rect(x, y, x + 3 + rnd() * 6, y + 2 + rnd() * 3, pick([WOOD, WOOD_D, STONE, STONE_D, CLOTH]))
    table_side(176, LOW_FLOOR - 17)


def house_and_chimney():
    """The house, moved down TOP rows, and its chimney stack on the east pitch."""
    house_upright()
    _ck.buf = [[KEY] * BW for _ in range(TOP)] + _ck.buf[:BH]
    masonry(150, 4, 162, TOP + 26)
    rect(148, 1, 164, 4, STONE_D)
    rect(148, 1, 164, 1, STONE_L)
    rect(153, 2, 159, 3, (30, 26, 25))


def paste_tilted(w, h, draw_fn, cx, cy, angle, air):
    """draw_rotated, but only where the room has air: where the rock has grown into the
    house its masonry shows through faintly, as rock with courses in it."""
    saved = (_ck.W, _ck.H, _ck.buf)
    _ck.W, _ck.H = w, h
    _ck.buf = [[KEY for _ in range(w)] for _ in range(h)]
    draw_fn()
    local = _ck.buf
    _ck.W, _ck.H, _ck.buf = saved
    ca, sa = math.cos(angle), math.sin(angle)
    R = int(math.hypot(w, h) / 2) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            lx = ca * dx + sa * dy + w / 2
            ly = -sa * dx + ca * dy + h / 2
            if 0 <= lx < w and 0 <= ly < h:
                c = local[int(ly)][int(lx)]
                if c == KEY:
                    continue
                if (x, y) in air:
                    px(x, y, c)
                else:
                    px(x, y, c, 0.22)

    def to_world(lx, ly):
        dx, dy = lx - w / 2, ly - h / 2
        return cx + ca * dx - sa * dy, cy + sa * dx + ca * dy
    return to_world


def streak(x, y, ang, n=4, ln=7):
    """Slide marks behind a thing going downhill: short lines uphill of it."""
    for k in range(n):
        d = 4 + k * 3
        x0 = x - math.cos(ang) * d
        y0 = y - math.sin(ang) * d - k * 1.5
        line(x0, y0, x0 - math.cos(ang) * ln, y0 - math.sin(ang) * ln, (170, 176, 186), 0.45)


def house_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    teeth(m, X(236), X(420), Y(110), 16)

    # the ledge and the rubble the house came to rest on
    for lx in range(222, 340):
        top = floor_at(m, X(lx), Y(300))
        for y in range(top, top + 3):
            px(X(lx), y, pick([STONE, STONE_D, ROCK_M, DIRT]))
    for _ in range(40):
        lx = 230 + rnd() * 110
        top = floor_at(m, X(lx), Y(300))
        rect(X(lx), top - 2, X(lx) + 2 + rnd() * 4, top - 1, pick([STONE, STONE_L, STONE_D]))

    to_w = paste_tilted(BW, BH + TOP, house_and_chimney, X(HC[0]), Y(HC[1]), ANG, m)
    W = lambda lx, ly: tuple(int(round(v)) for v in to_w(lx, ly + TOP))

    # lamps hang plumb from ceilings that are not level any more
    for lx, ly, drop in ((40, 50, 12), (150, 50, 8), (60, UP_FLOOR + 10, 10)):
        x, y = W(lx, ly)
        lamp(x, y, drop=drop, bulb=LAMP, tint=LAMP, r=48, strength=0.14)

    # the people living in it, standing on ramps
    stand("WizCrimson", *W(40, UP_FLOOR))
    stand("Gaper", *W(132, UP_FLOOR), flip=True)
    stand("RiotBrute", *W(58, LOW_FLOOR))
    stand("WizMaskwraith", *W(150, LOW_FLOOR), flip=True)
    # the west pitch of the roof is the one level floor in the house
    stand("Sentinel", *W(56, 21))
    # things on their way down
    rx, ry = W(28, UP_FLOOR - 5)
    disc(rx, ry, 5, KEG)
    ring(rx, ry, 5, MET_D)
    line(rx - 4, ry, rx + 4, ry, MET_D)
    streak(rx, ry + 2, ANG)
    cx_, cy_ = W(90, LOW_FLOOR)
    corpse(cx_ + 6, cy_ + 3)
    streak(cx_ + 2, cy_ - 1, ANG, 3)

    # outside: under the house, east of it, and on the ledge
    fl = Y(FLOOR)
    stand("Minespider", X(150), floor_at(m, X(150), Y(330)))
    scrap_pile(X(116), floor_at(m, X(116), Y(330)), 30, 6, colors=(STONE_D, STONE, DIRT, ROCK_M))
    for lx, d in ((180, 0), (196, 1)):
        top = floor_at(m, X(lx), Y(330))
        rect(X(lx), top - 3, X(lx + 6), top - 1, pick([STONE, STONE_D]))
    stand("Grenadier", X(392), fl, flip=True)
    stand("WizGoldhood", X(410), Y(250), flip=True)                 # on the east shelf
    crate_g(X(392), Y(250), 10)
    stand("Pyro", X(360), fl, flip=True)
    keg(X(404), fl)
    crate_g(X(418), fl, 10)
    lamp(X(380), ceil_at(m, X(380), Y(260)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=60, strength=0.14)
    lx_ = Y(268)
    stand("WizBogcap", X(46), lx_)
    lamp(X(70), ceil_at(m, X(70), Y(250)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=40, strength=0.12)
    # the rock that grew into the west wall: a lit lip where it meets the house
    for lx in range(14, 126):
        for ly in range(140, 226):
            if in_swallow(lx, ly) and not in_swallow(lx, ly - 1) and (X(lx), Y(ly) - 1) in m:
                px(X(lx), Y(ly), ROCK_L)
    # a roof beam that went off the east pitch, leaning on the east wall, and rock off it
    for t in range(3):
        line(X(336 + t), Y(FLOOR) - 1, X(404 + t), Y(282), WOOD if t < 2 else WOOD_D)
    line(X(335), Y(FLOOR) - 1, X(403), Y(282), WOOD_L)
    for lx, ly, d, rx, ry in ((428, 320, 1, 14, 10), (430, 196, 1, 12, 9)):
        x0, y0 = X(lx), Y(ly)
        while (x0, y0) not in m and x0 > X(300):
            x0 -= 1
        while (x0, y0) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), y0, rx, ry, rough=0.25)
    stand("Gaper", X(312), floor_at(m, X(312), Y(330)), flip=True)
    # slates off the steep east pitch: a few on their way, the rest heaped at its foot
    for k, t in enumerate((0.3, 0.55, 0.8)):
        x, y = W(100 + t * 99, 2 + t * 38 - 3)
        rect(x, y, x + 4, y + 1, SLATE_L)
        streak(x, y, ANG + 0.38, 2, 5)
    for k in range(26):
        lx = 336 + rnd() * 40
        top = floor_at(m, X(lx), Y(330))
        rect(X(lx), top - 1 - int(rnd() * 3), X(lx) + 3, top - 1, pick([SLATE, SLATE_L, (52, 56, 66)]))
    # rubble spilled out of the burst east wall, down onto the heap
    bx, by = W(BW - 4, 160)
    for k in range(16):
        t = rnd()
        x = bx + 4 + t * 34 + rnd() * 4
        y = floor_at(m, int(x), by)
        rect(x, y - 2, x + 2 + rnd() * 4, y - 1, pick([WOOD, STONE, CLOTH, WOOD_D]))


ROOM = {
    "name": "THE SUNKEN HOUSE", "w": 440, "h": 400,
    "shapes": [([("blob", 220, 218, 204, 160)], 0.07),
               ([("blob", 56, 248, 64, 24),                # the west entry, onto the ledge
                 ("blob", 386, 290, 56, 76)], 0.12)],      # the east bay
    "sockets": {"T1": ("T", 238, 70), "T2": ("T", 366, 112),
                "L1": ("L", 268, 24), "R1": ("R", FLOOR, 30),
                "R2": ("R", 250, 36), "B1": ("B", 168, 46)},
    "edit": house_edit,
    "furnish": house_furnish,
}


SHEET = {
    "seed": 73701,
    "callouts": [
        ("1 A HOUSE AT 24 DEGREES", (250, -50), (300, 190)),
        ("2 FLOORS ARE RAMPS: IT ALL SLIDES DOWN", (196, 428), (262, 296)),
        ("3 THE ROCK HAS ITS WEST WALL", (-125, 300), (100, 190)),
        ("4 THE ROOF IS THE ONE LEVEL FLOOR", (-125, -50), (186, 140)),
    ],
    "beats": [
        ("KNOCK ANYTHING LOOSE AND IT RUNS DOWNHILL INTO WHOEVER IS BELOW", (170, 180, 195)),
        ("FIGHT UP THE RAMPS OR COME DOWN OFF THE ROOF", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
