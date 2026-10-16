"""Fungal room S48 - THE SPORE CHAPEL.

A round chamber, a dome of rock, with the cult's idol on a mound of mycelium in the
middle and the congregation on stools round it. By the altar is what they burn in the
censers: kegs and sacks of spore dust, stacked up. A shot into the stack and the service
is over; a burst sac from the crown does the same more quietly.

You come in high on the west wall onto a shelf of fungus and look down into the bowl
from above the censer. Brackets of shelf fungus spiral down the walls, one on each side,
so the way down is in plain sight of nobody - they face the idol. Under the floor, past
a crawl in the east corner, is the crypt where the dust is kept and the way out below.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S48"

FLOOR = 340
ALTAR = (220, 12)                  # mound centre x, its height
CORE = (220, 120, 20, 30)          # the rock hanging in the crown: centre, radii


def chapel_edit(air, ox, oy):
    out = set()
    cx, cy, rx, ry = CORE
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if 60 <= lx <= 306 and FLOOR < ly < FLOOR + 22:      # the floor is flat; the crypt is under it
            continue
        if ((lx - cx) / rx) ** 2 + ((ly - cy) / ry) ** 2 <= 1.0 and ly < cy + ry * 0.6:
            continue                                            # the core
        if ((lx - cx) / (rx * 0.6)) ** 2 + ((ly - cy - ry * 0.6) / (ry * 0.55)) ** 2 <= 1.0:
            continue                                            # its tip
        out.add((x, y))
    return out


def chapel_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(100), X(170), Y(140), 4)
    teeth(m, X(270), X(340), Y(140), 4)

    # the way in, and down: a spiral of shelf fungus
    bracket(X(90), Y(166), "L")
    bracket(X(369), Y(226), "R", glow=True)
    bracket(X(84), Y(286), "L")
    hang("GlowLantern", X(124), ceil_at(m, X(124), Y(150)) + 1, 10)
    hang("GlowLantern", X(328), ceil_at(m, X(328), Y(200)) + 1, 12)

    # the altar and what they pray to; the censer swings off the core's tip
    ax, ah = ALTAR
    myc_mound(X(ax), fl, 30, ah)
    prop("FungalIdol", X(ax), fl - ah)
    prop("CapCandles", X(ax - 22), fl - 6)
    prop("CapCandles", X(ax + 22), fl - 6)
    tip = ceil_at(m, X(ax), Y(240)) + 1
    hang("FungalCenser", X(ax), tip, 80)

    # the dust, stacked by the altar
    for x in (252, 261, 270):
        prop("SporeKeg", X(x), fl)
    prop("SporeKeg", X(256), fl - 11)
    prop("SporeKeg", X(265), fl - 11)
    prop("SporeSack", X(184), fl)

    # the congregation, facing in
    for x, flip in ((146, False), (168, False), (284, True), (304, True)):
        prop("CapStool", X(x - 6 if not flip else x + 6), fl)
        stand("WizBogcap", X(x), fl, flip=flip)
    hang("SporeSacs", X(160), ceil_at(m, X(160), Y(200)) + 1, 40)
    hang("SporeSacs", X(292), ceil_at(m, X(292), Y(200)) + 1, 40)

    # something kept up in the dome
    stand("Ghast", X(300), Y(196))

    # the crypt: dust in store, a spider, skulls
    cf = floor_at(m, X(300), Y(386))
    prop("SporeSack", X(268), cf)
    prop("SporeSack", X(280), cf)
    prop("SkullShrooms", X(326), cf)
    stand("Minespider", X(310), cf, flip=True)

    sprinkle(m, X(130), X(310), Y(FLOOR - 4), 6, gap=12)
    sprinkle(m, X(90), X(130), Y(290), 2)


ROOM = {
    "name": "THE SPORE CHAPEL", "w": 440, "h": 420,
    "shapes": [([
        ("blob", 220, 230, 150, 135),                         # the dome
        ("tube", [(16, 151), (94, 153)], 14),                 # the way in, high
        ("tube", [(366, 212), (424, 212)], 14),               # a side door off the east bracket
        ("blob", 296, 386, 60, 15),                           # the crypt
        ("tube", [(318, 334), (340, 358), (318, 382)], 9),    # the crawl down to it
    ], 0.1)],
    "sockets": {"L1": ("L", 166, 20), "R1": ("R", 226, 22), "B1": ("B", 296, 24)},
    "edit": chapel_edit,
    "furnish": chapel_furnish,
}

BACK_PATCHES = [(180, 230, 260, 330), (90, 250, 140, 320), (310, 260, 360, 320)]

SHEET = {
    "seed": 74801,
    "callouts": [
        ("1 IN HIGH, ON A SHELF OF FUNGUS", (-150, 100), (110, 164)),
        ("2 THE DUST BY THE ALTAR", (330, 445), (262, 332)),
        ("3 THEY ALL FACE THE IDOL", (-60, 445), (146, 330)),
        ("4 SPIRAL OF BRACKETS", (380, 290), (350, 228)),
        ("5 THE CRYPT", (-60, 400), (270, 386)),
        ("6 CENSER ON THE CORE", (240, -50), (220, 190)),
    ],
    "beats": [
        ("A ROUND ROOM ROUND ONE THING: THE IDOL, AND EVERYONE FACING IT", (170, 180, 195)),
        ("BLOW THE STACK OF SPORE KEGS AND THE CONGREGATION GOES WITH IT", F_MID),
        ("OR CLIMB DOWN THE BRACKETS BEHIND THEIR BACKS TO THE CRYPT AND OUT", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
