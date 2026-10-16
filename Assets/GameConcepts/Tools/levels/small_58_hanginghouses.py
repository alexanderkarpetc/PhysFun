"""Fungal room S58 - THE HANGING HOUSES.

A chasm, and over it two giant mushrooms grown down out of the roof, their caps hanging
flat side up - floors in mid-air - and on each cap a house the cult grew there: walls of
stem, a roof of cap, arches for doors. Below, at the bottom of the drop, the spiders'
nest, and the cocoons the spiders hung from the undersides of the caps.

The houses are terrain like the mushrooms, all one piece with the cap they stand on, and
each cap hangs on its stem alone. Burn a stem where it comes out of the roof and the cap
goes down into the nest with the house on it and whoever is in the house.

You come in on a ledge on the west wall, level with the first cap; a shelf of fungus is
the step across. From the second cap a shelf on the east wall takes you to the far ledge.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S58"

PIT = 330
WEST = (70, 150)                   # the west ledge: its edge x, its floor
EAST = (414, 210)                  # the east ledge
# hanging mushrooms: (stem x, its height below the roof, cap radius)
CAPS = {"A": (148, None, 58), "B": (306, None, 64)}
TOPS = {"A": 150, "B": 196}        # the floor line on each cap


def chasm_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if lx <= WEST[0] and ly > WEST[1]:
            continue
        if lx >= EAST[0] and ly > EAST[1]:
            continue
        if ly > PIT:
            continue
        out.add((x, y))
    return out


def chasm_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    pf = Y(PIT) + 1

    for k, (sx, _, r) in CAPS.items():
        roof = ceil_at(m, X(sx), Y(100)) + 1
        hanging_shroom(X(sx), roof, Y(TOPS[k]) - roof, r)

    # ── cap A: a small house, the stem its west wall, its arch to the east ───────
    fa = Y(TOPS["A"])
    grown_house(X(152), X(198), fa, 38, 16, doors=("R",), windows=[("R", fa - 34, fa - 33)], shed="L")
    prop("MushroomBed", X(170), fa)
    prop("CapCupboard", X(190), fa)
    stand("WizBogcap", X(180), fa, flip=True)
    prop("GlowLampPost", X(102), fa)
    prop("PlanterBox", X(124), fa)
    stand("Gaper", X(114), fa)                                    # on the porch, looking at the drop

    # ── cap B: a bigger one round its stem, a room each side, arches out both ends
    fb = Y(TOPS["B"])
    grown_house(X(256), X(356), fb, 44, 22, doors=("L", "R"),
                windows=[("L", fb - 40, fb - 33), ("R", fb - 40, fb - 33)])
    prop("CapTable", X(282), fb)
    prop("RootChair", X(268), fb)
    stand("WizBogcap", X(290), fb, flip=True)
    prop("MycelRug", X(330), fb)
    prop("MushroomBed", X(332), fb)
    stand("WizHollowhood", X(342), fb, flip=True)
    hang("GlowLantern", X(282), fb - 44 + 1, 4)
    hang("GlowLantern", X(330), fb - 44 + 1, 4)

    # the steps across: a shelf off the west ledge, a shelf off the east wall
    bracket(X(WEST[0]), Y(WEST[1] + 1), "L")
    bracket(X(EAST[0] - 1), Y(EAST[1] + 1), "R", glow=True)
    prop("SporeKeg", X(30), Y(WEST[1]) + 1)
    prop("CropBasket", X(44), Y(WEST[1]) + 1)
    hang("GlowLantern", X(40), ceil_at(m, X(40), Y(120)) + 1, 6)
    prop("GlowLampPost", X(440), Y(EAST[1]) + 1)

    # under the caps: the cocoons, the nest at the bottom of the drop
    for x, k in ((130, "A"), (166, "A"), (290, "B"), (326, "B")):
        sx, _, r = CAPS[k]
        under = Y(TOPS[k]) + int(r * 0.5 * (1 - ((x - sx) / float(r)) ** 2) ** 0.5)
        hang("Cocoon", X(x), under, 2)
    for x, flip in ((150, False), (226, True), (300, False), (360, True)):
        stand("Minespider", X(x), pf, flip=flip)
    prop("GiantPuffball", X(250), pf)
    prop("SkullShrooms", X(190), pf)
    prop("SkullShrooms", X(340), pf)
    sprinkle(m, X(90), X(400), Y(PIT - 4), 6, gap=16)
    # rock bulging off the chasm walls, so the drop is not one empty shaft
    rock_blob(X(78), Y(250), 22, 12, rough=0.2)
    rock_blob(X(404), Y(270), 20, 10, rough=0.2)
    stand("Minespider", X(78), Y(238), flip=False)


ROOM = {
    "name": "THE HANGING HOUSES", "w": 480, "h": 370,
    "shapes": [([
        ("blob", 240, 186, 226, 170),                         # the chasm
        ("blob", 240, 326, 200, 26),                          # the nest at its foot
    ], 0.06)],
    "sockets": {"L1": ("L", WEST[1], 16), "R1": ("R", EAST[1], 18), "B1": ("B", 240, 42)},
    "edit": chasm_edit,
    "furnish": chasm_furnish,
}

BACK_HOUSES = [(152, 112, 198, 149), (256, 152, 356, 195)]
BACK_PATCHES = [(150, 290, 330, 328), (20, 110, 60, 145)]

SHEET = {
    "seed": 75801,
    "callouts": [
        ("1 IN ON THE WEST LEDGE", (-150, 60), (40, 146)),
        ("2 HOUSES GROWN ON CAPS HUNG FROM THE ROOF", (-60, -50), (306, 160)),
        ("3 BURN A STEM - IT ALL GOES DOWN", (330, -50), (306, 80)),
        ("4 THE NEST AT THE BOTTOM", (100, 390), (226, 326)),
        ("5 COCOONS UNDER THE CAPS", (330, 390), (290, 240)),
    ],
    "beats": [
        ("TWO HOUSES ON TWO CAPS OVER A DROP: STEP ACROSS ON THE SHELVES", (170, 180, 195)),
        ("FELL: A BURNT STEM DROPS ITS CAP, ITS HOUSE AND ITS PEOPLE INTO THE NEST", F_MID),
        ("OR GO DOWN INTO THE NEST AND OUT UNDER IT ALL", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
