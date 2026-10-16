"""Fungal room S55 - THE SPORE FOAM.

The rock here is a sponge: eight bubbles packed together, thin walls between them, each
joined to the next by a hole you can crawl through. The cult has filled the middle ones
with its sacs of spore - hung in clusters, a nest in every bubble - and lives among them.
A burst sac throws fire through the holes into the next bubble, where the next sacs hang.

You come in at the west bubble and see into the next one through the hole. From any
bubble you see one or two others and no more. Set one going and it goes round the foam on
its own; or crawl round the edge of it - over the top, or under through the store - and
out the far side.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S55"

BUBBLES = {                        # centre, radii
    "A": (62, 206, 42, 32),        # the way in
    "B": (146, 142, 36, 30),
    "C": (150, 258, 40, 32),
    "D": (240, 196, 46, 38),       # the nest
    "E": (334, 126, 42, 30),
    "F": (334, 256, 44, 34),
    "G": (240, 318, 42, 26),       # the store
    "H": (408, 194, 26, 40),       # the way out
}
SHRINK = 0.8                       # the bubbles as carved: smaller than their spacing, so rock stands between
HOLES = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E"), ("D", "F"),
         ("C", "G"), ("G", "F"), ("E", "H"), ("F", "H")]


def floor_of(k):
    cx, cy, rx, ry = BUBBLES[k]
    return cy + int(ry * SHRINK * 0.75)


def foam_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        cut = False
        for k, (cx, cy, rx, ry) in BUBBLES.items():
            if abs(lx - cx) < rx * 0.7 and floor_of(k) < ly < cy + ry + 6:
                cut = True                                      # each bubble a flat floor
        if not cut:
            out.add((x, y))
    holes = []
    for a, b in HOLES:
        ax, ay, _, _ = BUBBLES[a]
        bx, by, _, _ = BUBBLES[b]
        fy = max(floor_of(a), floor_of(b)) - 10 if abs(ay - by) < 60 else None
        if fy is not None and abs(ay - by) < 40:
            pts = [(ax + ox, floor_of(a) - 9 + oy), (bx + ox, floor_of(b) - 9 + oy)]
        else:
            pts = [(ax + ox, ay + oy), (bx + ox, by + oy)]
        holes.append(("tube", pts, 9))
    return out | cave_mask(holes, rough=0.08, top=0)


def foam_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    F = {k: Y(floor_of(k)) + 1 for k in BUBBLES}

    def fl(k, x):
        return floor_at(m, X(x), Y(BUBBLES[k][1]))

    def roof(k, x):
        return ceil_at(m, X(x), Y(BUBBLES[k][1])) + 1

    # A, the way in
    hang("GlowLantern", X(50), roof("A", 50), 6)
    prop("CropBasket", X(40), fl("A", 40))

    # B: something drifting
    stand("Ghast", X(146), Y(140))

    # C and F: sacs, a keeper each
    hang("SporeSacs", X(150), roof("C", 150), 6)
    stand("WizBogcap", X(166), fl("C", 166), flip=True)
    hang("SporeSacs", X(330), roof("F", 330), 6)
    stand("WizBogcap", X(348), fl("F", 348), flip=True)
    stand("Minespider", X(316), fl("F", 316))

    # D, the nest: two clusters and a pod, two of them asleep under it
    hang("SporePod", X(236), roof("D", 236), 4)
    hang("SporeSacs", X(258), roof("D", 258), 8)
    hang("SporeSacs", X(218), roof("D", 218), 10)
    stand("WizBogcap", X(226), fl("D", 226))
    stand("Gaper", X(256), fl("D", 256), flip=True)

    # E: a look-out of theirs at the top
    stand("WizHollowhood", X(334), fl("E", 334), flip=True)
    hang("GlowLantern", X(350), roof("E", 350), 4)

    # G, the store under it all
    for x in (226, 235):
        prop("SporeKeg", X(x), fl("G", x))
    prop("SporeSack", X(250), fl("G", 250))
    stand("Minespider", X(262), fl("G", 262), flip=True)

    # H, the way out
    hang("GlowLantern", X(408), roof("H", 408), 6)

    for k in BUBBLES:
        cx, cy, rx, ry = BUBBLES[k]
        sprinkle(m, X(cx - rx * 0.6), X(cx + rx * 0.6), Y(floor_of(k) - 4), 1, gap=12)


ROOM = {
    "name": "THE SPORE FOAM", "w": 440, "h": 370,
    "shapes": [([("blob", cx, cy, rx * SHRINK, ry * SHRINK) for cx, cy, rx, ry in BUBBLES.values()], 0.12)],
    "sockets": {"L1": ("L", floor_of("A"), 22), "T1": ("T", 334, 104),
                "R1": ("R", floor_of("H"), 16), "B1": ("B", 240, 40)},
    "edit": foam_edit,
    "furnish": foam_furnish,
}

BACK_PATCHES = [(200, 170, 280, 225), (110, 240, 180, 280), (300, 240, 370, 280)]

SHEET = {
    "seed": 75501,
    "callouts": [
        ("1 IN AT THE WEST BUBBLE", (-150, 120), (50, 220)),
        ("2 THE NEST", (180, -50), (238, 170)),
        ("3 EVERY HOLE CARRIES THE FIRE ON", (360, 400), (290, 230)),
        ("4 THE STORE UNDER IT ALL", (-60, 400), (232, 330)),
        ("5 THEIR LOOK-OUT", (380, -50), (334, 140)),
    ],
    "beats": [
        ("EIGHT BUBBLES, THIN WALLS: FROM ANY ONE YOU SEE ONE OR TWO MORE", (170, 180, 195)),
        ("BLOW: A BURST SAC SETS OFF THE NEXT THROUGH THE HOLES - THE FOAM GOES UP ON ITS OWN", F_MID),
        ("OR CRAWL ROUND THE EDGE OF IT, OVER THE TOP OR UNDER THROUGH THE STORE", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
