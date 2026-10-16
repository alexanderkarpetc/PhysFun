"""Fungal room S47 - THE CAP FOREST.

A wide bowl with three giant mushrooms grown up out of its floor, and the cult harvesting
the crop in their shade. The mushrooms are terrain: stems of fibre, caps of flesh, both
burning like wood - and a cap stands on nothing but its stem. Burn a stem, or blow it
with the spore pod hung beside it, and the cap comes down on the harvesters.

You come in on a ledge high on the west wall and see the whole bowl from it before anyone
sees you. The caps are a road across the top of the room: hop from one to the next and
you are at the chimney in the roof without touching the floor. Or go down and through
them, past the barrow and the crates, to the low door on the east side.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S47"

FLOOR = 320                        # the bowl's floor
LEDGE = 162                        # the look-out's floor
SHROOMS = [                        # (stem x, height, cap radius, lean)
    (170, 92, 32, -3),
    (282, 112, 40, 4),
    (384, 68, 28, 0),
]


def forest_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if 40 <= lx <= 440 and ly > FLOOR:
            continue
        if 14 <= lx <= 128 and LEDGE < ly < LEDGE + 50:
            continue
        out.add((x, y))
    return out


def forest_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(150), X(360), Y(200), 9)

    for sx, h, r, lean in SHROOMS:
        giant_shroom(X(sx), fl, h, r, lean)
    myc_mound(X(232), fl, 16, 7)
    myc_mound(X(424), fl, 12, 9)

    # the look-out: a lamp, a basket someone left
    hang("GlowLantern", X(84), ceil_at(m, X(84), Y(LEDGE - 10)) + 1, 8)
    prop("CropBasket", X(40), Y(LEDGE) + 1)
    sprinkle(m, X(20), X(120), Y(LEDGE - 4), 3)

    # under the first cap: harvest in hand, backs to the ledge
    stand("WizBogcap", X(150), fl)
    stand("Gaper", X(198), fl, flip=True)
    prop("MushroomBarrow", X(116), fl)
    prop("MushroomCrate", X(214), fl)

    # between the first two: a spore pod hung over them
    roof = ceil_at(m, X(226), Y(220)) + 1
    hang("SporePod", X(226), roof, 26)
    stand("WizBogcap", X(244), fl, flip=True)

    # under the tall one: a spider in its shade, a sack of dust against the stem
    stand("Minespider", X(310), fl, flip=True)
    prop("SporeSack", X(262), fl)
    prop("CropBasket", X(300), fl)

    # on the third cap, a look-out of theirs - facing the east door, not the ledge
    stand("WizBogcap", X(388), fl - 68 - int(28 * 0.55))
    hang("SporeSacs", X(342), ceil_at(m, X(342), Y(240)) + 1, 18)

    # the east door, low, past the third mushroom
    stand("Gaper", X(424), fl - 9, flip=True)
    hang("GlowLantern", X(410), ceil_at(m, X(410), Y(280)) + 1, 10)

    sprinkle(m, X(60), X(440), Y(FLOOR - 4), 9)


ROOM = {
    "name": "THE CAP FOREST", "w": 460, "h": 380,
    "shapes": [([
        ("blob", 250, 250, 205, 100),                         # the bowl
        ("blob", 70, 140, 58, 32),                            # the look-out
        ("tube", [(112, 150), (146, 168), (178, 196)], 15),   # its mouth onto the bowl
        ("tube", [(300, 166), (310, 110), (300, 46)], 13),    # the chimney
    ], 0.1)],
    "sockets": {"L1": ("L", LEDGE, 18), "T1": ("T", 300, 50),
                "R1": ("R", FLOOR, 30)},
    "edit": forest_edit,
    "furnish": forest_furnish,
}

BACK_PATCHES = [(140, 230, 200, 300), (250, 200, 320, 290), (360, 250, 410, 300), (30, 120, 100, 150)]

SHEET = {
    "seed": 74701,
    "callouts": [
        ("1 THE LOOK-OUT", (-130, 70), (60, 150)),
        ("2 BURN A STEM - THE CAP COMES DOWN", (40, 400), (170, 280)),
        ("3 SPORE POD OVER THE HARVEST", (-60, -50), (226, 250)),
        ("4 THE CAPS ARE A ROAD", (330, -50), (300, 172)),
        ("5 THEIR LOOK-OUT FACES EAST", (300, 420), (388, 228)),
    ],
    "beats": [
        ("FROM THE LEDGE YOU SEE THE WHOLE BOWL, AND NOBODY IN IT IS LOOKING UP", (170, 180, 195)),
        ("FELL A MUSHROOM: FIRE OR A BURST POD ON THE STEM DROPS THE CAP ON THE CREW", F_MID),
        ("OR CROSS THE CAPS TO THE CHIMNEY AND NEVER TOUCH THE FLOOR", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
