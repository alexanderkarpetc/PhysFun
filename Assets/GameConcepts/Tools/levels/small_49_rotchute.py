"""Fungal room S49 - THE ROT CHUTE.

The room is one long throat slanting down from the north-west to a camp in the south-east,
the floor of it a slope you stand on at an angle. At the top is the landing you come in
on, and on it the logs the cult has dragged in to grow the crop on: two rotten trunks
laid along the landing's edge, a keg of spore dust wedged in behind them. At the bottom
is the camp - the barrow, the crates, a table and the crew round it - straight down the
line of the chute.

Blow the keg and the logs go over the edge and down the throat into the camp. Or walk
down the slope past the man posted halfway, or climb the side shaft up out of the middle
of it and leave them to it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S49"

LANDING = 112                      # the landing's floor
CAMP = 304                         # the camp's floor
SHAFT_X = 252


def chute_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if 12 <= lx <= 126 and LANDING < ly < LANDING + 40:
            continue
        if 314 <= lx <= 450 and CAMP < ly < CAMP + 40:
            continue
        out.add((x, y))
    return out


def chute_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    lf, cf = Y(LANDING) + 1, Y(CAMP) + 1

    # the landing: the logs on its lip, the keg behind them
    prop("SporeKeg", X(28), lf)
    prop("RotLog", X(84), lf)
    prop("RotLogShort", X(90), lf - 12)
    hang("GlowLantern", X(40), ceil_at(m, X(40), Y(90)) + 1, 6)
    sprinkle(m, X(16), X(46), Y(LANDING - 4), 1, kinds=("GlowCaps", "FungalMoss"))

    # the chute: one of them posted at the shaft
    sf = floor_at(m, X(SHAFT_X + 18), Y(170))
    stand("WizBogcap", X(SHAFT_X + 18), sf, flip=True)
    ladder_up(X(SHAFT_X), Y(46), floor_at(m, X(SHAFT_X), Y(150)))
    hang("SporeSacs", X(160), ceil_at(m, X(160), Y(120)) + 1, 10)

    # the camp, straight down the line of the chute
    prop("CapTable", X(372), cf)
    prop("CapStool", X(352), cf)
    prop("CapStool", X(394), cf)
    prop("MushroomBarrow", X(428), cf)
    prop("MushroomCrate", X(330), cf)
    prop("CropBasket", X(372), cf - 12)
    stand("WizBogcap", X(358), cf)
    stand("Gaper", X(392), cf, flip=True)
    stand("WizBogcap", X(414), cf, flip=True)
    hang("SporePod", X(398), ceil_at(m, X(398), Y(280)) + 1, 14)
    hang("GlowLantern", X(340), ceil_at(m, X(340), Y(280)) + 1, 12)
    sprinkle(m, X(316), X(450), Y(CAMP - 4), 4, gap=14)


ROOM = {
    "name": "THE ROT CHUTE", "w": 460, "h": 360,
    "shapes": [([
        ("blob", 70, 92, 62, 30),                             # the landing
        ("tube", [(112, 104), (240, 176), (370, 256)], 32),   # the chute
        ("blob", 384, 276, 74, 42),                           # the camp
        ("tube", [(SHAFT_X, 160), (SHAFT_X + 6, 100), (SHAFT_X, 40)], 12),   # the side shaft
    ], 0.1)],
    "sockets": {"L1": ("L", LANDING, 16), "T1": ("T", SHAFT_X, 44), "R1": ("R", CAMP, 18)},
    "edit": chute_edit,
    "furnish": chute_furnish,
}

BACK_PATCHES = [(330, 250, 440, 300), (20, 70, 60, 110), (180, 130, 230, 170)]

SHEET = {
    "seed": 74901,
    "callouts": [
        ("1 THE LANDING - YOU SEE DOWN THE LINE", (-140, 40), (60, 100)),
        ("2 BLOW THE KEG BEHIND THE LOGS", (-60, -50), (28, 106)),
        ("3 AND THEY GO DOWN THE CHUTE", (-40, 380), (220, 200)),
        ("4 THE CAMP AT THE FOOT", (300, 380), (372, 296)),
        ("5 SIDE SHAFT UP AND OUT", (280, -50), (252, 90)),
    ],
    "beats": [
        ("ONE SLOPE TOP TO BOTTOM: EVERYTHING AT THE TOP ENDS UP IN THE CAMP", (170, 180, 195)),
        ("ROLL: THE KEG SENDS TWO ROTTEN LOGS DOWN THE THROAT INTO THE CREW", F_MID),
        ("OR WALK DOWN PAST THE ONE AT THE SHAFT - OR CLIMB IT AND LEAVE", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
