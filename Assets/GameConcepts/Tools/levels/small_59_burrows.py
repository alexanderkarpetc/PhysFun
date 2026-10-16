"""Fungal room S59 - THE BURROWS.

A hillside in a cave, stepping down to the east in three terraces, and the cult living in
it the way a burrowing people would: each terrace has a home dug back into the hill under
the terrace above, its front a wall of stem slabs with a door and a window in it, an arch
of cap over the door. Behind the front, a room in the rock - beds, a cupboard, a rug, the
crop in boxes. Under the bottom terrace a cellar, down a shaft. The homes are joined
inside the hill by a crawl the cult uses and you can too.

On the top terrace is their garden: planters, lamp posts, and the puffballs they grow,
big and dry, at the terrace's edge over the doors below. You come in at the top, in the
garden, and look down the hill. Roll a puffball off the edge and it goes up against a
front door; or knock, or come in the back way through the crawl.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S59"

TERRACES = ((0, 172, 170), (172, 322, 238), (322, 470, 306))   # x0, x1, floor
WALL = 6
# the homes dug under the terrace above: pocket centre, radii, its floor, its front wall x
HOMES = {
    "upper": dict(c=(128, 216), r=(46, 24), floor=238, front=166),
    "lower": dict(c=(278, 284), r=(46, 24), floor=306, front=316),
}
CELLAR = dict(c=(396, 346), r=(54, 18), floor=360)
SHAFT_X = 344


def terrace_floor(lx):
    for x0, x1, fl in TERRACES:
        if x0 <= lx < x1:
            return fl
    return TERRACES[-1][2]


def in_home(lx, ly):
    for h in list(HOMES.values()) + [CELLAR]:
        (cx, cy), (rx, ry) = h["c"], h["r"]
        if ((lx - cx) / rx) ** 2 + ((ly - cy) / ry) ** 2 <= 1.0 and ly <= h["floor"]:
            return True
    return False


def burrow_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly <= terrace_floor(lx) or in_home(lx, ly):
            out.add((x, y))
    S = lambda pts: [(px_ + ox, py_ + oy) for px_, py_ in pts]
    out |= cave_mask([
        ("tube", S([(96, 232), (150, 262), (250, 300)]), 8),          # the crawl inside the hill
        ("tube", S([(SHAFT_X, 300), (SHAFT_X, 350)]), 9),             # the shaft to the cellar
        ("tube", S([(110, 196), (112, 176)]), 5),                      # a chimney onto the top terrace
    ], rough=0.06, top=0)
    return out


def front(X, Y, home):
    """A home's front: stem slabs from its roof to its floor, a door, a window, an arch."""
    h = HOMES[home]
    fx, fl = X(h["front"]), Y(h["floor"])
    top = Y(h["c"][1] - h["r"][1]) - 2
    plank_wall(fx, top, fx + WALL, fl - 32)
    flap_door(fx, fl - 30, 30, WALL)
    window(fx, Y(h["c"][1] - 12), fx + WALL, Y(h["c"][1] - 4))
    for k in range(-9, 10):                                         # the cap arch over the door
        y = fl - 34 - int(4 * (1 - (k / 9.0) ** 2))
        rect(fx + 3 + k, y, fx + 3 + k, y + 2, CAP_C if abs(k) < 8 else CAP_D)


def burrow_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    f1, f2, f3 = (Y(t[2]) + 1 for t in TERRACES)
    teeth(m, X(40), X(440), Y(130), 14)
    hang("SporePod", X(220), ceil_at(m, X(220), Y(150)) + 1, 20)
    hang("GlowLantern", X(380), ceil_at(m, X(380), Y(200)) + 1, 18)

    # ── the top terrace: the garden, and the puffballs at its edge ───────────────
    prop("PlanterBox", X(44), f1)
    prop("PlanterBox", X(70), f1)
    prop("GlowLampPost", X(26), f1)
    prop("GlowLampPost", X(96), f1)
    prop("GiantPuffball", X(136), f1)
    prop("GiantPuffball", X(158), f1)
    stand("WizBogcap", X(118), f1, flip=True)
    prop("DryingRack", X(84), f1)

    # ── the upper home, under the garden ─────────────────────────────────────────
    front(X, Y, "upper")
    fh = Y(HOMES["upper"]["floor"]) + 1
    prop("MushroomBed", X(108), fh)
    prop("CapCupboard", X(146), fh)
    prop("MycelRug", X(126), fh)
    stand("WizHollowhood", X(132), fh, flip=True)
    hang("GlowLantern", X(124), Y(HOMES["upper"]["c"][1] - 22), 3)

    # ── the middle terrace: a bench and a lamp outside the upper home's door ─────
    prop("RootChair", X(186), f2)
    prop("GlowLampPost", X(200), f2)
    prop("CropBasket", X(230), f2)
    stand("Gaper", X(256), f2)

    # ── the lower home, under the middle terrace ─────────────────────────────────
    front(X, Y, "lower")
    fh = Y(HOMES["lower"]["floor"]) + 1
    prop("CapTable", X(276), fh)
    prop("RootChair", X(258), fh)
    prop("PlanterBox", X(300), fh)
    stand("WizBogcap", X(268), fh)
    stand("WizBogcap", X(290), fh, flip=True)
    hang("GlowLantern", X(278), Y(HOMES["lower"]["c"][1] - 22), 3)

    # ── the bottom terrace, the shaft down, the cellar ───────────────────────────
    prop("GlowLampPost", X(440), f3)
    prop("MushroomBarrow", X(400), f3)
    stand("Minespider", X(372), f3, flip=True)
    ladder_up(X(SHAFT_X), f3 - 1, Y(CELLAR["floor"]) + 1)
    fc = Y(CELLAR["floor"]) + 1
    for x in (372, 381, 390):
        prop("SporeKeg", X(x), fc)
    prop("SporeSack", X(404), fc)
    prop("GrowRack", X(426), fc)
    stand("Minespider", X(416), fc, flip=True)

    sprinkle(m, X(176), X(320), Y(TERRACES[1][2] - 4), 3, gap=14)
    sprinkle(m, X(330), X(460), Y(TERRACES[2][2] - 4), 2, gap=14)


ROOM = {
    "name": "THE BURROWS", "w": 470, "h": 390,
    "shapes": [([
        ("blob", 236, 196, 230, 122),                          # the cave over the hill
        ("tube", [(300, 84), (296, 40), (300, 4)], 12),        # a chimney out of its roof
        ("tube", [(360, 292), (466, 292)], 14),                # the way out east, off the bottom terrace
    ] + [("blob",) + h["c"] + h["r"] for h in list(HOMES.values()) + [CELLAR]], 0.06)],
    "sockets": {"L1": ("L", TERRACES[0][2], 14), "R1": ("R", TERRACES[2][2], 16),
                "T1": ("T", 300, 12), "B1": ("B", 396, 30)},
    "edit": burrow_edit,
    "furnish": burrow_furnish,
}

BACK_HOUSES = [(84, 194, 166, 238), (234, 262, 316, 306)]
BACK_PATCHES = [(20, 130, 110, 168), (350, 330, 440, 358)]

SHEET = {
    "seed": 75901,
    "callouts": [
        ("1 IN AT THE TOP, IN THEIR GARDEN", (-150, 60), (40, 164)),
        ("2 PUFFBALLS AT THE EDGE, OVER A DOOR", (120, -50), (150, 160)),
        ("3 A HOME DUG UNDER EACH TERRACE", (-150, 300), (128, 226)),
        ("4 THE CRAWL INSIDE THE HILL", (100, 410), (200, 282)),
        ("5 THE CELLAR, DOWN THE SHAFT", (330, 410), (396, 352)),
    ],
    "beats": [
        ("A HILL OF HOMES: A FRONT DOOR ON EVERY TERRACE, ROOMS IN THE ROCK BEHIND", (170, 180, 195)),
        ("ROLL A PUFFBALL OFF THE GARDEN AND IT GOES UP AGAINST THE DOOR BELOW", F_MID),
        ("OR KNOCK - OR COME IN THE BACK WAY, THROUGH THE CRAWL THEY DUG", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
