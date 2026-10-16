"""Fungal room S66 - THE GLOWING HOLLOW.

After Terraria's Glowing Mushroom biome and the house its mushroom-dweller moves into:
a hollow lit by giant glowing mushrooms, the floor gone to mycelium, and in the middle a
house built by the book - a box with a door at each end, a floor of platforms across the
middle to make two storeys, a table, a chair and a light on each. The hermit who lives
there keeps his spores about him: sacs of them hung round the house and under the caps.

You come in high on the west wall, on a shelf, and look across at the house between the
giants. Its doors are real doors; its upstairs is reached through the platforms, the way
Terraria's are; its walls are grown, and burn.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S66"

FLOOR = 330
LOOKOUT = 190
HX0, HX1, HH = 140, 252, 72        # the house: outside faces, wall height
MID = FLOOR - 36                   # its row of platforms
GIANTS = [(56, 112, 40), (318, 106, 32), (404, 176, 50)]   # stem x, height, cap radius


def hollow_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def hollow_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(40), X(420), Y(90), 14)

    for sx, h, r in GIANTS:
        giant_shroom(X(sx), fl, h, r, cap="glowcap")
        under = fl - h + 3
        for dx in range(-r + 8, r - 16, 18):
            prop("GillGlow", X(sx + dx + 8), under, at="ceil")
    myc_mound(X(110), fl, 18, 5)
    myc_mound(X(350), fl, 22, 6)

    # the house, by the book: walls, a flat roof, a door each end, windows up
    grown_house(X(HX0), X(HX1), fl, HH, 0, doors=("L", "R"),
                windows=[("L", fl - 64, fl - 54), ("R", fl - 64, fl - 54)])
    prop("CapDoor", X(HX0 + 2), fl, at="floor")
    prop("CapDoor", X(HX1 - 2), fl, at="floor")
    for k in range(6):                                              # platforms across the middle
        prop("CapDeck", X(HX0 + 14 + k * 18), Y(MID), at="ceil")
    # downstairs: table, chair, light - and the hermit
    prop("CapTable", X(178), fl)
    prop("RootChair", X(160), fl)
    prop("GlowLampPost", X(226), fl)
    stand("WizGoldhood", X(198), fl, flip=True)
    # upstairs: bed, cupboard, jars, a light
    prop("MushroomBed", X(170), Y(MID))
    prop("CapCupboard", X(234), Y(MID))
    prop("SporeJars", X(206), Y(MID))
    hang("GlowLantern", X(196), fl - HH, 2)

    # his spores, hung round the house
    for x in (120, 270):
        hang("SporeSacs", X(x), ceil_at(m, X(x), Y(200)) + 1, 40)
    hang("SporePod", X(300), fl - 106 + 3, 2)

    # guards at both doors, a spider under the far giant, something drifting
    stand("WizBogcap", X(124), fl)
    stand("WizBogcap", X(270), fl, flip=True)
    stand("Minespider", X(392), fl, flip=True)
    stand("Ghast", X(300), Y(140))

    bracket(X(14), Y(LOOKOUT + 1), "L")
    sprinkle(m, X(16), X(130), Y(FLOOR - 4), 4, kinds=("GlowCaps", "FungalMoss", "GlowSpindles", "GlowBell"))
    sprinkle(m, X(262), X(450), Y(FLOOR - 4), 5, kinds=("GlowCaps", "FungalMoss", "GlowSpindles", "GlowBell"))


ROOM = {
    "name": "THE GLOWING HOLLOW", "w": 460, "h": 370,
    "shapes": [([
        ("blob", 230, 196, 218, 156),                         # the hollow
        ("blob", 230, 300, 222, 40),                          # its floor
        ("tube", [(230, 56), (226, 30), (230, 4)], 12),       # a chimney
    ], 0.06)],
    "sockets": {"L1": ("L", LOOKOUT, 18), "R1": ("R", FLOOR, 16), "T1": ("T", 230, 12)},
    "edit": hollow_edit,
    "furnish": hollow_furnish,
}

BACK_HOUSES = [(HX0, FLOOR - HH, HX1, FLOOR)]
BACK_PATCHES = [(20, 280, 120, 328), (290, 270, 440, 328)]

SHEET = {
    "seed": 76601,
    "callouts": [
        ("1 IN HIGH, ACROSS FROM THE HOUSE", (-150, 100), (24, 186)),
        ("2 A HOUSE BY THE BOOK: DOORS, PLATFORMS, A LIGHT", (40, -50), (196, 290)),
        ("3 GLOWING GIANTS LIGHT THE HOLLOW", (310, -50), (404, 160)),
        ("4 HIS SPORES, HUNG ROUND IT", (80, 390), (120, 250)),
    ],
    "beats": [
        ("AFTER TERRARIA'S GLOWING MUSHROOM BIOME AND THE HOUSE ITS DWELLER LIVES IN", (170, 180, 195)),
        ("BLOW: BURST HIS SPORES ON THE GUARDS AT HIS DOORS", F_MID),
        ("OR IN AT A DOOR AND UP THROUGH THE PLATFORMS, TERRARIA STYLE", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
