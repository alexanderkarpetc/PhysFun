"""Fungal room S51 - THE COCOON LARDER.

A throat in the rock, a long drop from the roof to a bowl at the bottom, and the spiders'
larder: the people they caught, wrapped in mycelium and hung up to keep - in niches off
the throat, and from the bowl's roof over the spiders' own heads. A cocoon is heavier
than its rope looks. Cut one and it comes down on whatever is under it.

You come in at the top and look straight down the throat at the bowl. Shelves of fungus
zig-zag down its walls, so the way down is a climb, not a fall; each niche is a stop on
the way, and each has a way out of its own.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S51"

BOWL = 432                         # the bowl's floor
NICHE_L = dict(c=(108, 236), r=(40, 24), floor=254, xs=(74, 140))
NICHE_R = dict(c=(296, 156), r=(40, 22), floor=172, xs=(262, 330))


def larder_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if 96 <= lx <= 304 and BOWL < ly:
            continue
        if any(p["xs"][0] <= lx <= p["xs"][1] and p["floor"] < ly < p["floor"] + 30 for p in (NICHE_L, NICHE_R)):
            continue
        out.add((x, y))
    return out


def larder_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    bf = Y(BOWL) + 1

    # the climb down: shelves of fungus off alternate walls
    for y, side in ((112, "R"), (196, "L"), (282, "R"), (352, "L")):
        yy = Y(y)
        if side == "L":
            x = X(100)
            while (x, yy - 2) not in m:
                x += 1
            bracket(x - 1, yy, "L", glow=y == 282)
        else:
            x = X(300)
            while (x, yy - 2) not in m:
                x -= 1
            bracket(x + 1, yy, "R", glow=y == 282)

    # the niches, a cocoon in each, a way out of each
    lf, rf = Y(NICHE_L["floor"]) + 1, Y(NICHE_R["floor"]) + 1
    hang("Cocoon", X(112), ceil_at(m, X(112), Y(240)) + 1, 2)
    prop("SkullShrooms", X(86), lf)
    hang("Cocoon", X(300), ceil_at(m, X(300), Y(160)) + 1, 2)
    prop("PuffballSmall", X(318), rf)
    stand("WizBogcap", X(280), rf, flip=True)
    hang("GlowLantern", X(132), ceil_at(m, X(132), Y(240)) + 1, 4)

    # the bowl: the spiders, under the cocoons they hung
    for x in (124, 150, 278):
        hang("Cocoon", X(x), ceil_at(m, X(x), Y(410)) + 1, 4)
    for x, flip in ((136, False), (196, True), (276, True)):
        stand("Minespider", X(x), bf, flip=flip)
    prop("SkullShrooms", X(230), bf)
    prop("GiantPuffball", X(250), bf)
    stand("Ghast", X(200), Y(300))
    hang("GlowLantern", X(230), ceil_at(m, X(230), Y(400)) + 1, 8)
    sprinkle(m, X(104), X(300), Y(BOWL - 4), 5, gap=14)


ROOM = {
    "name": "THE COCOON LARDER", "w": 400, "h": 470,
    "shapes": [([
        ("tube", [(200, 66), (186, 130), (214, 240), (196, 340), (204, 400)], 44),   # the throat
        ("blob", 200, 404, 112, 36),                                                # the bowl
        ("blob",) + NICHE_L["c"] + NICHE_L["r"],
        ("blob",) + NICHE_R["c"] + NICHE_R["r"],
        ("tube", [(20, 240), (80, 244)], 14),                                       # out of the west niche
        ("tube", [(330, 160), (380, 160)], 13),                                     # out of the east niche
    ], 0.1)],
    "sockets": {"T1": ("T", 200, 30), "L1": ("L", NICHE_L["floor"], 22),
                "R1": ("R", NICHE_R["floor"], 22), "B1": ("B", 260, 40)},
    "edit": larder_edit,
    "furnish": larder_furnish,
}

BACK_PATCHES = [(150, 380, 260, 430), (80, 220, 130, 250), (270, 140, 320, 170), (170, 120, 230, 200)]

SHEET = {
    "seed": 75101,
    "callouts": [
        ("1 IN AT THE TOP, LOOKING DOWN", (240, -50), (200, 60)),
        ("2 SHELVES DOWN THE THROAT", (-150, 120), (170, 196)),
        ("3 THE LARDER OVER THEIR HEADS", (-140, 470), (184, 406)),
        ("4 CUT ONE", (330, 470), (278, 404)),
        ("5 A WAY OUT OF EACH NICHE", (250, 250), (330, 168)),
    ],
    "beats": [
        ("ONE LONG DROP, CLIMBED ON SHELVES - EVERY NICHE A STOP AND AN EXIT", (170, 180, 195)),
        ("CUT: THE COCOONS HANG FROM THE BOWL'S ROOF OVER THE SPIDERS THAT HUNG THEM", F_MID),
        ("OR SLIP OUT OF A NICHE HALFWAY DOWN AND NEVER REACH THE BOTTOM", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
