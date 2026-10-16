"""Fungal room S53 - THE TINDER RING.

A round chamber whose floor is a bowl, and the bowl is full: a mat of mycelium gone dry
as straw, knee deep, and on it the cult dancing a ring round a glowing giant. Over the
ring hang the spore pods they dance for. A pod that bursts throws fire, and the mat burns
like timber - the whole floor, with everyone on it.

You come in high on the east wall onto a shelf, above the dance and out of its light.
Shelves go round the dome to the chimney in the crown; the way out west is at the bowl's
rim, past the ring.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S53"

FLOOR = 300
CENTRE = 210


def ring_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if not (100 <= x - ox <= 320 and y - oy > FLOOR)}


def ring_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(110), X(310), Y(120), 8)

    # the mat: dry mycelium over the whole bowl floor
    mat_top = fl - 6
    myc_mound(X(CENTRE), fl, 92, 6, mat="tinder")

    # the giant they dance round, and the ring
    prop("GlowGiant", X(CENTRE), mat_top)
    def on_mat(x):
        u = (x - CENTRE) / 92.0
        return fl - int(6 * max(0.0, 1 - u * u) ** 0.5)
    for x, flip in ((150, False), (176, False), (246, True), (272, True)):
        stand("WizBogcap", X(x), on_mat(x), flip=flip)
    stand("Gaper", X(108), floor_at(m, X(108), Y(280)), flip=False)
    for x, drop in ((176, 40), (246, 46)):
        hang("SporePod", X(x), ceil_at(m, X(x), Y(200)) + 1, drop)
    prop("CapCandles", X(CENTRE - 30), mat_top)
    prop("CapCandles", X(CENTRE + 30), mat_top)

    # the way in, high in the east; shelves round the dome
    bracket(X(346), Y(166), "R")
    bracket(X(62), Y(200), "L", glow=True)
    bracket(X(309), Y(132), "R", glow=True)
    hang("GlowLantern", X(296), ceil_at(m, X(296), Y(150)) + 1, 8)
    stand("Ghast", X(130), Y(176))

    sprinkle(m, X(300), X(340), Y(FLOOR - 4), 1, kinds=("GlowCaps", "FungalMoss"))


ROOM = {
    "name": "THE TINDER RING", "w": 420, "h": 380,
    "shapes": [([
        ("blob", CENTRE, 214, 150, 112),                      # the dome and its bowl
        ("tube", [(340, 152), (418, 152)], 14),               # in, high on the east
        ("tube", [(16, 278), (122, 284)], 14),                # out, at the bowl's west rim
        ("tube", [(CENTRE, 110), (CENTRE + 6, 60), (CENTRE, 8)], 12),   # the chimney
    ], 0.1)],
    "sockets": {"R1": ("R", 166, 18), "L1": ("L", 292, 20), "T1": ("T", CENTRE, 12)},
    "edit": ring_edit,
    "furnish": ring_furnish,
}

BACK_PATCHES = [(150, 220, 270, 295), (66, 180, 116, 230), (300, 140, 345, 180)]

SHEET = {
    "seed": 75301,
    "callouts": [
        ("1 IN HIGH, OUT OF THE LIGHT", (300, -50), (370, 160)),
        ("2 THE MAT IS DRY AS STRAW", (-60, 400), (180, 296)),
        ("3 THE PODS THEY DANCE UNDER", (-150, 60), (176, 210)),
        ("4 SHELVES ROUND THE DOME", (-150, 150), (80, 196)),
    ],
    "beats": [
        ("A ROUND ROOM WITH A FLOOR THAT BURNS", (170, 180, 195)),
        ("BURN: A BURST POD THROWS FIRE ONTO THE MAT, AND THE RING GOES UP WITH IT", F_MID),
        ("OR GO ROUND THE DOME ON THE SHELVES TO THE CHIMNEY, OVER THE DANCE", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
