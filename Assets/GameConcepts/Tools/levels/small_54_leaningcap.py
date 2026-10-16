"""Fungal room S54 - THE LEANING CAP.

A cave split by a pit, and over the pit a giant mushroom that grew sideways out of the
west wall: its stem is the bridge across, its cap stands at the far end by the east shelf.
The cult works the pit under it - racks, crates, spiders in the dark - in the mushroom's
shade. It hangs on its root alone. Burn the root, or burst the pod hung beside it, and the
whole thing comes down into the pit.

You come in on the west shelf, where the root is. The bridge is the quick way over to the
east door, in full view of the shelf over there; the pit is the slow way, through the
crew; the stem itself is the toy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S54"

SHELF = 196                        # both shelves' floor
PIT = 340                          # the pit's floor
ROOT = (122, 206)                  # where the mushroom grows out of the west wall
END = (334, 178)                   # where its cap stands
CAP_R = 30


def pit_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if (lx <= 124 or lx >= 376) and SHELF < ly < SHELF + 60:
            continue
        if 140 <= lx <= 360 and ly > PIT:
            continue
        out.add((x, y))
    return out


def pit_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    sf, pf = Y(SHELF) + 1, Y(PIT) + 1
    teeth(m, X(60), X(420), Y(120), 10)

    wall_shroom(X(ROOT[0]), Y(ROOT[1]), X(END[0]), Y(END[1]), CAP_R)

    # the west shelf: the way in, the root, the pod by it
    hang("GlowLantern", X(54), ceil_at(m, X(54), Y(170)) + 1, 8)
    hang("SporePod", X(108), ceil_at(m, X(108), Y(170)) + 1, 10)
    prop("CropBasket", X(40), sf)
    sprinkle(m, X(30), X(100), Y(SHELF - 4), 2)

    # the pit, in the mushroom's shade
    prop("GrowRack", X(160), pf)
    prop("GrowRack", X(184), pf)
    prop("MushroomCrate", X(300), pf)
    prop("MushroomCrate", X(300), pf - 17)
    prop("SporeSack", X(318), pf)
    stand("WizBogcap", X(214), pf)
    stand("WizBogcap", X(262), pf, flip=True)
    stand("Minespider", X(238), pf)
    stand("Minespider", X(340), pf, flip=True)
    hang("GlowLantern", X(236), ceil_at(m, X(236), Y(300)) + 1, 4)
    sprinkle(m, X(150), X(350), Y(PIT - 4), 4, gap=14)

    # the east shelf and its door
    stand("WizHollowhood", X(404), sf, flip=True)
    prop("SporeKeg", X(436), sf)
    hang("GlowLantern", X(420), ceil_at(m, X(420), Y(170)) + 1, 8)


ROOM = {
    "name": "THE LEANING CAP", "w": 480, "h": 380,
    "shapes": [([
        ("blob", 240, 150, 212, 72),                          # the cave
        ("blob", 250, 240, 124, 34),                          # its floor falling away
        ("blob", 250, 304, 128, 52),                          # the pit
    ], 0.1)],
    "sockets": {"L1": ("L", SHELF, 34), "R1": ("R", SHELF, 34), "B1": ("B", 250, 42),
                "T1": ("T", 400, 90)},
    "edit": pit_edit,
    "furnish": pit_furnish,
}

BACK_PATCHES = [(150, 280, 340, 336), (30, 160, 110, 190), (380, 160, 450, 190)]

SHEET = {
    "seed": 75401,
    "callouts": [
        ("1 IN ON THE WEST SHELF, BY THE ROOT", (-150, 120), (60, 190)),
        ("2 IT HANGS ON ITS ROOT ALONE", (-150, 250), (124, 208)),
        ("3 THE STEM IS THE BRIDGE", (200, -50), (230, 186)),
        ("4 THE CREW IN ITS SHADE", (100, 400), (238, 330)),
        ("5 THE POD BY THE ROOT", (-60, -50), (108, 150)),
    ],
    "beats": [
        ("A PIT, AND A MUSHROOM GROWN ACROSS IT OUT OF THE WALL", (170, 180, 195)),
        ("FELL: BURN THE ROOT OR BURST THE POD BY IT - THE WHOLE THING DROPS INTO THE PIT", F_MID),
        ("OR CROSS ON THE STEM TO THE EAST DOOR, IN FULL VIEW, OR GO DOWN THROUGH THE CREW", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
