"""Fungal room S65 - THE MUSHTREE CAMP.

After Don't Starve's mushtree forests and the camps made in them: a low cave grown thick
with tall thin mushtrees, dark between them, and in the middle the one patch of light -
a camp under the biggest tree, with its planters of crop, its drying rack, its tent, and
the foragers round the lamp. Out in the dark the spiders wait for whoever leaves it.

You come in high in the dark west grove, on the caps, and see the camp lit from there;
nobody in the light can see into the dark. The big tree's cap is the camp's roof, on one
stem. The way on is through the dark east grove.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S65"

FLOOR = 300
LOOKOUT = 150
# mushtrees: stem x, height, cap radius, kind
TREES = [(40, 134, 18, "cap"), (84, 100, 20, "glowcap"), (128, 128, 16, "cap"),
         (240, 112, 46, "cap"),                                         # the camp's tree
         (352, 120, 18, "glowcap"), (398, 96, 22, "cap"), (444, 140, 18, "glowcap")]


def camp_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def camp_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(30), X(450), Y(80), 14)

    for sx, h, r, kind in TREES:
        giant_shroom(X(sx), fl, h, r, cap=kind)
        if kind == "glowcap":
            prop("GillGlow", X(sx), fl - h + 3, at="ceil")

    # the camp under the big tree, the only light
    prop("GlowLampPost", X(240), fl)
    for x in (184, 206, 274):
        prop("PlanterBox", X(x), fl)
    prop("DryingRack", X(300), fl)
    prop("CapStool", X(226), fl)
    prop("CapStool", X(256), fl)
    prop("CropBasket", X(170), fl)
    prop("MushroomCrate", X(318), fl)
    grown_house(X(150), X(176), fl, 22, 10, doors=("R",), shed="L")      # a tent, against the dark
    stand("WizBogcap", X(220), fl)
    stand("WizBogcap", X(262), fl, flip=True)
    stand("WizBogcap", X(290), fl, flip=True)
    stand("WizHollowhood", X(162), fl)
    hang("SporePod", X(222), fl - 112 + 4, 6)                               # under the tree's cap

    # out in the dark: spiders, waiting
    for x, flip in ((60, False), (108, True), (376, False), (420, True)):
        stand("Minespider", X(x), fl, flip=flip)
    prop("SkullShrooms", X(96), fl)
    prop("SkullShrooms", X(432), fl)

    # the way in: a shelf high in the west grove, onto the caps
    bracket(X(18), Y(LOOKOUT + 1), "L")
    sprinkle(m, X(20), X(150), Y(FLOOR - 4), 4, kinds=("FungalMoss", "PaleSprouts", "InkCap", "MossTuft"))
    sprinkle(m, X(330), X(470), Y(FLOOR - 4), 4, kinds=("FungalMoss", "PaleSprouts", "InkCap", "MossTuft"))


ROOM = {
    "name": "THE MUSHTREE CAMP", "w": 480, "h": 340,
    "shapes": [([
        ("blob", 240, 176, 228, 140),                         # the cave
        ("blob", 240, 270, 232, 40),                          # its floor, wide
        ("tube", [(240, 50), (236, 26), (240, 4)], 12),       # a chimney over the camp
    ], 0.06)],
    "sockets": {"L1": ("L", LOOKOUT, 22), "R1": ("R", FLOOR, 16), "T1": ("T", 240, 10)},
    "edit": camp_edit,
    "furnish": camp_furnish,
}

BACK_HOUSES = [(150, 279, 176, 300)]
BACK_PATCHES = [(170, 240, 320, 298)]

SHEET = {
    "seed": 76501,
    "callouts": [
        ("1 IN HIGH, IN THE DARK", (-150, 60), (30, 146)),
        ("2 THE ONE PATCH OF LIGHT", (180, -50), (240, 270)),
        ("3 THE TREE'S CAP IS THE CAMP'S ROOF", (330, -50), (240, 188)),
        ("4 SPIDERS IN THE DARK GROVES", (-60, 360), (108, 296)),
        ("5 THE WAY ON, THROUGH THE DARK", (330, 360), (420, 296)),
    ],
    "beats": [
        ("AFTER DON'T STARVE'S MUSHTREE FORESTS: A CAMP IN THE ONE LIGHT, THE DARK ALL ROUND", (170, 180, 195)),
        ("FELL: BURN THE BIG TREE'S STEM AND ITS CAP COMES DOWN ON THE CAMP", F_MID),
        ("OR STAY IN THE DARK, OVER THE CAPS - THE SPIDERS ARE THERE TOO", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
