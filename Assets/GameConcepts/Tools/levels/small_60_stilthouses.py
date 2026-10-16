"""Fungal room S60 - THE STILT HOUSES.

A low wide cave whose floor is a mat of dry mycelium, and the cult's houses stood up off
it on stilts of stem - three of them at three heights, grown whole: stilts, floor slab,
walls, arches, a roof of cap. Steps of cap slices go from porch to porch; a ladder comes
down from the middle one to the mat. Spiders walk the mat between the stilts.

Everything here burns: the mat like straw, the stilts like timber. A burst pod over the
mat sets it going, the fire climbs the stilts, and a house whose stilts have burnt comes
down - it is terrain, one piece with them. You come in high on the west wall and can step
down onto the first roof.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S60"

FLOOR = 320
LOOKOUT = 160
# houses: x0, x1, floor line, wall height, ridge, doors, stilt xs
HOUSES = {
    "west": (40, 120, 226, 40, 14, ("R",), (46, 108)),
    "mid": (190, 300, 196, 46, 22, ("L", "R"), (196, 241, 288)),
    "east": (360, 440, 240, 38, 14, ("L",), (366, 428)),
}
SLAB_T = 5
STILT_W = 6


def stilt_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def steps(X, Y, pts):
    """Cap slices for steps, each with its top at (x centre, y)."""
    for x, y in pts:
        prop("CapDeck", X(x), Y(y), at="ceil")


def stilt_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(30), X(450), Y(80), 16)

    myc_mound(X(240), fl, 216, 6, mat="tinder")                   # the mat

    for name, (x0, x1, f, h, ridge, doors, stilts) in HOUSES.items():
        for sx in stilts:
            slab(X(sx), Y(f + SLAB_T + 1), X(sx + STILT_W), fl - 1)
        slab(X(x0), Y(f), X(x1), Y(f + SLAB_T))
        side = "R" if "R" not in doors else "L"
        grown_house(X(x0), X(x1), Y(f), h, ridge, doors=doors,
                    windows=[(side, Y(f - 30), Y(f - 22))] if name != "mid" else [])

    # the west house: where they eat
    f = Y(HOUSES["west"][2])
    prop("CapTable", X(80), f)
    prop("RootChair", X(64), f)
    stand("WizBogcap", X(70), f)
    stand("WizBogcap", X(96), f, flip=True)
    hang("GlowLantern", X(80), f - 38, 3)

    # the middle house: where they sleep, a watcher at the east arch
    f = Y(HOUSES["mid"][2])
    prop("MushroomBed", X(214), f)
    prop("MushroomBed", X(248), f)
    prop("CapCupboard", X(276), f)
    stand("WizHollowhood", X(230), f)
    stand("WizBogcap", X(290), f, flip=True)
    hang("GlowLantern", X(222), f - 46, 3)
    hang("GlowLantern", X(268), f - 46, 3)

    # the east house: the store
    f = Y(HOUSES["east"][2])
    for x in (390, 399, 408, 417):
        prop("SporeKeg", X(x), f)
    prop("SporeKeg", X(395), f - 11)
    prop("SporeSack", X(426), f)
    stand("WizBogcap", X(376), f, flip=True)
    hang("GlowLantern", X(404), f - 38, 3)

    # porch to porch, and down to the mat
    steps(X, Y, [(132, 226), (152, 216), (172, 206)])
    steps(X, Y, [(312, 196), (332, 212), (350, 228)])
    ladder_up(X(318), Y(197), fl - 6)

    # the mat: the pods over it, the spiders on it
    hang("SporePod", X(160), ceil_at(m, X(160), Y(150)) + 1, 44)
    hang("SporePod", X(334), ceil_at(m, X(334), Y(150)) + 1, 40)
    stand("Minespider", X(150), fl - 6)
    stand("Minespider", X(330), fl - 6, flip=True)
    stand("Gaper", X(260), fl - 6)
    prop("GlowLampPost", X(176), fl - 6)
    prop("GlowLampPost", X(450), fl - 3)

    # the way in: a shelf high on the west wall, over the first roof
    bracket(X(18), Y(LOOKOUT + 1), "L")
    hang("GlowLantern", X(40), ceil_at(m, X(40), Y(140)) + 1, 6)


ROOM = {
    "name": "THE STILT HOUSES", "w": 480, "h": 360,
    "shapes": [([
        ("blob", 240, 180, 228, 150),                         # the cave
        ("blob", 240, 290, 232, 46),                          # its floor, wide
        ("tube", [(246, 70), (240, 36), (246, 4)], 12),       # a chimney over the middle roof
    ], 0.06)],
    "sockets": {"L1": ("L", LOOKOUT, 22), "R1": ("R", FLOOR, 16), "T1": ("T", 246, 12)},
    "edit": stilt_edit,
    "furnish": stilt_furnish,
}

BACK_HOUSES = [(44, 188, 116, 225), (194, 150, 296, 195), (364, 202, 436, 239)]
BACK_PATCHES = [(130, 280, 360, 316)]

SHEET = {
    "seed": 76001,
    "callouts": [
        ("1 IN HIGH, OVER THE FIRST ROOF", (-150, 80), (30, 156)),
        ("2 STILTS OF STEM - THEY BURN", (-80, 380), (108, 290)),
        ("3 A FLOOR OF DRY MYCELIUM", (220, 380), (240, 316)),
        ("4 STEPS PORCH TO PORCH", (120, -50), (172, 204)),
        ("5 THE STORE", (420, 140), (404, 230)),
    ],
    "beats": [
        ("THREE HOUSES ON STILTS OVER A FLOOR THAT BURNS", (170, 180, 195)),
        ("BURN: A POD SETS THE MAT GOING, THE FIRE CLIMBS THE STILTS, THE HOUSES COME DOWN", F_MID),
        ("OR GO ROOF TO ROOF AND PORCH TO PORCH AND NEVER TOUCH THE MAT", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
