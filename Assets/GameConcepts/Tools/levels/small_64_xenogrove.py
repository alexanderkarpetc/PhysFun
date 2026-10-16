"""Fungal room S64 - THE XENOFUNGUS GROVE.

After Deep Rock Galactic's Fungus Bogs: one big cavern full of fungi of every size - the
big ones are platforms - with plate-shaped fungus growing flat out of the walls, two
glowing giants lighting the place, vines hanging from the roof to break up the view, and
on the floor the exploding plants a nest of spiders lives among, ready to go off one
after another.

You come in high on the west wall and cross the cavern over the tops of the fungi to a
door high in the east, plate by cap. Under you, the nest. The cult has a camp on the
tallest glowing cap. Shoot one plant in the nest and the rest go with it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S64"

FLOOR = 396
# the big fungi: stem x, height, cap radius, cap kind
FUNGI = [(92, 112, 34, "cap"), (196, 180, 50, "glowcap"), (304, 122, 40, "cap"), (402, 214, 44, "glowcap")]


def cap_top(i):
    sx, h, r, _ = FUNGI[i]
    return FLOOR + 1 - h - int(r * 0.55)


def grove_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def grove_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(40), X(440), Y(80), 18)

    for sx, h, r, kind in FUNGI:
        giant_shroom(X(sx), fl, h, r, cap=kind)
        if kind == "glowcap":                                      # its gills, lit, under the cap
            under = fl - h + 3
            for dx in range(-r + 10, r - 18, 18):
                prop("GillGlow", X(sx + dx + 8), under, at="ceil")

    # plates grown flat out of the walls: the steps between the caps
    for y, side in ((150, "L"), (240, "L"), (316, "L"), (162, "R"), (262, "R")):
        yy = Y(y)
        x = X(240)
        step = -1 if side == "L" else 1
        while (x + step, yy - 2) in m:
            x += step
        bracket(x, yy, side, glow=y in (240, 262))

    # vines hanging from the roof, in the way of the view
    for x in (140, 252, 350, 446):
        prop("Vines", X(x), ceil_at(m, X(x), Y(160)) + 1, at="ceil")
    prop("HangMoss", X(60), ceil_at(m, X(60), Y(120)) + 1, at="ceil")

    # the cult's camp on the tallest glowing cap
    t = Y(cap_top(1)) + 1
    prop("CropBasket", X(180), t + 1)
    stand("WizBogcap", X(196), t + 1)
    stand("WizBogcap", X(214), t + 2, flip=True)
    prop("GlowLampPost", X(170), t + 2)
    # a look-out on the far giant, by the door
    t = Y(cap_top(3)) + 1
    stand("WizHollowhood", X(402), t + 1, flip=True)

    # the nest on the floor, among the plants that go off
    for x in (132, 156, 248, 268, 346):
        prop("PuffballSmall", X(x), fl)
    prop("GiantPuffball", X(228), fl)
    prop("GiantPuffball", X(360), fl)
    hang("SporeSacs", X(144), ceil_at(m, X(144), Y(330)) + 1, 60)
    hang("SporeSacs", X(258), ceil_at(m, X(258), Y(340)) + 1, 50)
    for x, flip in ((120, False), (176, True), (244, False), (330, True), (440, True)):
        stand("Minespider", X(x), fl, flip=flip)
    sprinkle(m, X(20), X(460), Y(FLOOR - 4), 6, gap=18)

    hang("GlowLantern", X(36), ceil_at(m, X(36), Y(130)) + 1, 6)


ROOM = {
    "name": "THE XENOFUNGUS GROVE", "w": 480, "h": 430,
    "shapes": [([
        ("blob", 240, 214, 226, 196),                         # the cavern
        ("blob", 240, 380, 228, 34),                          # its floor
        ("tube", [(16, 136), (60, 138)], 14),                 # in, high west
        ("tube", [(420, 148), (476, 148)], 14),               # out, high east
    ], 0.06)],
    "sockets": {"L1": ("L", 150, 16), "R1": ("R", 162, 14), "B1": ("B", 240, 34)},
    "edit": grove_edit,
    "furnish": grove_furnish,
}

BACK_PATCHES = [(110, 330, 380, 394), (20, 120, 70, 150)]

SHEET = {
    "seed": 76401,
    "callouts": [
        ("1 IN HIGH ON THE WEST WALL", (-150, 60), (40, 146)),
        ("2 THE BIG ONES ARE PLATFORMS", (60, -50), (196, 180)),
        ("3 PLATES OUT OF THE WALLS", (-150, 250), (40, 240)),
        ("4 THE NEST AMONG THE PLANTS THAT GO OFF", (60, 450), (228, 388)),
        ("5 OUT HIGH IN THE EAST", (350, -50), (440, 150)),
    ],
    "beats": [
        ("AFTER DEEP ROCK GALACTIC'S FUNGUS BOGS: CROSS A CAVERN ON THE TOPS OF THE FUNGI", (170, 180, 195)),
        ("CHAIN: ONE SHOT INTO THE NEST AND THE PLANTS GO OFF ONE AFTER ANOTHER", F_MID),
        ("THE GLOWING GIANTS LIGHT THE WAY; THE VINES HIDE WHO IS ON THE NEXT CAP", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
