"""Fungal room S52 - THE PUFFBALL SLOPE.

A wide cave with a hill in it: a terrace high in the east, a long slope of mycelium down
from it, and the cult's camp at the foot. On the terrace the puffballs have grown big and
dry - barrels of spore, held back from the slope by nothing but a lip of rock. A knock
sets one off; so does a hard landing.

You come in on the terrace, among them, and the whole slope is under you. Push one over
the lip and it rolls down into the camp and goes up there. Or go down the slope yourself,
or up the chimney over the middle of it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S52"

CAMP = 300                         # the camp's floor
TERRACE = 200                      # the terrace's floor
SLOPE = (184, 316)                 # where the slope runs, x


def ground(lx):
    """The floor line of the hill, local coords."""
    if lx < SLOPE[0]:
        return CAMP
    if lx < SLOPE[1]:
        return CAMP - (lx - SLOPE[0]) / float(SLOPE[1] - SLOPE[0]) * (CAMP - TERRACE)
    if lx < SLOPE[1] + 8:
        return TERRACE - 6                                    # the lip
    return TERRACE


def slope_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if (y - oy) <= ground(x - ox)}


def slope_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    cf, tf = Y(CAMP) + 1, Y(TERRACE) + 1
    teeth(m, X(80), X(420), Y(160), 10)

    # the terrace: the puffballs behind the lip, the way in
    for x in (340, 366, 392):
        prop("GiantPuffball", X(x), tf)
    prop("PuffballSmall", X(414), tf)
    hang("GlowLantern", X(430), ceil_at(m, X(430), Y(180)) + 1, 8)
    sprinkle(m, X(330), X(450), Y(TERRACE - 4), 2, kinds=("GlowCaps", "FungalMoss", "PaleSprouts"))

    # the slope: a spider on its way up, growth all down it
    sx = 250
    stand("Minespider", X(sx), floor_at(m, X(sx), Y(220)), flip=True)

    # the camp at the foot
    giant_shroom(X(70), cf, 54, 24, 2)
    prop("CapTable", X(118), cf)
    prop("CapStool", X(98), cf)
    prop("MushroomBarrow", X(156), cf)
    prop("MushroomCrate", X(44), cf)
    prop("SporeSack", X(176), cf)
    stand("WizBogcap", X(104), cf)
    stand("Gaper", X(134), cf, flip=True)
    stand("WizBogcap", X(164), cf, flip=True)
    stand("WizHollowhood", X(58), cf)
    hang("GlowLantern", X(130), ceil_at(m, X(130), Y(260)) + 1, 14)
    hang("SporePod", X(190), ceil_at(m, X(190), Y(240)) + 1, 18)
    sprinkle(m, X(30), X(184), Y(CAMP - 4), 4, gap=14)


ROOM = {
    "name": "THE PUFFBALL SLOPE", "w": 480, "h": 360,
    "shapes": [([
        ("blob", 240, 214, 222, 102),                         # the cave
        ("tube", [(16, 286), (110, 288)], 14),                # the way out west
        ("tube", [(244, 140), (236, 70), (244, 10)], 12),     # the chimney
    ], 0.1)],
    "sockets": {"R1": ("R", TERRACE, 28), "L1": ("L", CAMP, 22), "T1": ("T", 244, 14)},
    "edit": slope_edit,
    "furnish": slope_furnish,
}

BACK_PATCHES = [(40, 230, 180, 290), (330, 150, 440, 190)]

SHEET = {
    "seed": 75201,
    "callouts": [
        ("1 IN ON THE TERRACE, AMONG THEM", (350, -50), (420, 190)),
        ("2 A LIP OF ROCK IS ALL THAT HOLDS THEM", (230, 380), (322, 196)),
        ("3 PUSH ONE OVER", (60, -50), (300, 214)),
        ("4 THE CAMP AT THE FOOT", (-120, 380), (120, 292)),
    ],
    "beats": [
        ("A HILL IN A CAVE: WHATEVER STARTS ON TOP ENDS UP IN THE CAMP", (170, 180, 195)),
        ("ROLL AND BLOW: A PUFFBALL OVER THE LIP GOES UP WHEN IT HITS THE BOTTOM", F_MID),
        ("OR WALK DOWN THE SLOPE PAST THE SPIDER, OR TAKE THE CHIMNEY OVER IT ALL", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
