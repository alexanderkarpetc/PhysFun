"""Fungal room S57 - THE STALK TOWER.

A tall cave with one giant mushroom in it, and the cult's tower built round its stem, the
way a Starbound tower climbs: four storeys of stem-slab floors, the stem up the middle of
every one, so each storey is two rooms - one each side of it. The ladders go up through
hatches on alternate sides, so the way to the top is a zig-zag through every room. At
the top, under the cap, is their shrine and the one who keeps it.

You come in high on the east wall onto a shelf, level with the second storey and across
from its window - shuttered, so they do not see you, and you do not see them. Shelves go
on up the cave wall to the cap's rim and the chimney. In the store at the foot of the
tower are the kegs; the cap is a roof on a stem, and stems burn.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S57"

FLOOR = 424
STEM_X, STEM_H, CAP_R = 190, 272, 92
X0, X1 = 128, 252                  # the tower's outside faces
WALL = 6
STOREYS = [FLOOR - 70, FLOOR - 140, FLOOR - 210]   # the floors above the ground one
LOOKOUT = FLOOR - 140              # the shelf you come in on: level with the 2nd storey


def under():
    return FLOOR - STEM_H + 3


def tower_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def tower_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    ceil = Y(under())
    teeth(m, X(40), X(340), Y(60), 10)

    giant_shroom(X(STEM_X), fl, STEM_H, CAP_R)
    rect(X(X0), ceil, X(X1), fl - 1, (70, 58, 96), 0.12)

    # the walls, top to bottom, a door each side at the foot, a window a storey
    for wx in (X0, X1 - WALL):
        plank_wall(X(wx), ceil, X(wx + WALL), fl - 32)
        flap_door(X(wx), fl - 30, 30, WALL)
    for i, y in enumerate(STOREYS):
        wx = X0 if i % 2 == 0 else X1 - WALL
        window(X(wx), Y(y - 34), X(wx + WALL), Y(y - 22), shutter=(y == LOOKOUT))
    window(X(X1 - WALL), Y(STOREYS[2] - 34), X(X1), Y(STOREYS[2] - 22))

    # the floors, each side of the stem, and the zig-zag of ladders
    floors = [FLOOR] + STOREYS
    for i, y in enumerate(STOREYS):
        deck(X(X0 + WALL + 1), X(STEM_X - 6), Y(y))
        deck(X(STEM_X + 6), X(X1 - WALL - 1), Y(y))
        lx = 143 if i % 2 == 0 else 237             # hatch against the wall: no sliver of floor past it
        ladder_up(X(lx), Y(y), Y(floors[i]) + 1)

    def on(i):
        return Y(floors[i]) + (1 if i == 0 else 0)

    # ground: the store east, the door-keeper west
    for x in (204, 213, 222):
        prop("SporeKeg", X(x), on(0))
    prop("SporeKeg", X(208), on(0) - 11)
    prop("SporeKeg", X(217), on(0) - 11)
    prop("SporeSack", X(234), on(0))
    stand("Gaper", X(170), on(0))
    prop("CapStool", X(144), on(0))
    # first storey: beds west, the table east
    prop("MushroomBed", X(170), on(1))
    stand("WizHollowhood", X(146), on(1))
    prop("CapTable", X(214), on(1))
    stand("WizBogcap", X(204), on(1))
    stand("WizBogcap", X(230), on(1), flip=True)
    # second storey: the racks west, a watcher at the shuttered window east
    prop("GrowRack", X(170), on(2))
    stand("Minespider", X(148), on(2))
    stand("WizBogcap", X(238), on(2), flip=True)
    prop("CapShelf", X(214), Y(STOREYS[1] - 34), at="ceil")
    # the top: the shrine under the cap
    prop("FungalIdol", X(168), on(3))
    prop("CapCandles", X(148), on(3))
    stand("WizMaskwraith", X(220), on(3), flip=True)
    prop("SporeJars", X(238), on(3))

    for i, y in enumerate(floors[1:] + [under()]):
        for lx in (160, 220):
            hang("GlowLantern", X(lx), Y(y) + (6 if i < 3 else 0), 3)

    # outside: the shelf you come in on, and the shelves on up the cave wall to the cap
    bracket(X(344), Y(LOOKOUT + 1), "R")
    bracket(X(352), Y(LOOKOUT - 62), "R", glow=True)
    bracket(X(30), Y(FLOOR - 90), "L")
    bracket(X(26), Y(FLOOR - 170), "L", glow=True)
    hang("SporePod", X(300), ceil_at(m, X(300), Y(200)) + 1, 24)
    stand("Ghast", X(80), Y(180))
    sprinkle(m, X(20), X(120), Y(FLOOR - 4), 3)
    sprinkle(m, X(260), X(360), Y(FLOOR - 4), 3)


ROOM = {
    "name": "THE STALK TOWER", "w": 380, "h": 460,
    "shapes": [([
        ("blob", 190, 236, 172, 196),                         # the cave, tall
        ("blob", 190, 392, 178, 46),                          # its floor, wide
        ("tube", [(344, LOOKOUT - 14), (378, LOOKOUT - 14)], 14),   # in, onto the shelf
        ("tube", [(112, 84), (104, 40), (110, 4)], 12),       # the chimney, off the cap's rim
    ], 0.06)],
    "sockets": {"R1": ("R", LOOKOUT, 18), "L1": ("L", FLOOR, 16), "T1": ("T", 110, 12)},
    "edit": tower_edit,
    "furnish": tower_furnish,
}

BACK_PATCHES = [(30, 300, 110, 410), (270, 330, 350, 410)]

SHEET = {
    "seed": 75701,
    "callouts": [
        ("1 IN ON THE SHELF, AT THE SHUTTERED WINDOW", (300, -50), (350, 280)),
        ("2 TWO ROOMS A STOREY, THE STEM BETWEEN", (-150, 470), (190, 330)),
        ("3 THE LADDERS ZIG-ZAG", (-150, 210), (143, 300)),
        ("4 THE KEGS AT THE FOOT", (200, 470), (214, 410)),
        ("5 THE SHRINE UNDER THE CAP", (-120, -50), (190, 200)),
    ],
    "beats": [
        ("A TOWER ROUND A STEM: EIGHT ROOMS, A FLOOR OR THE STEM BETWEEN EACH", (170, 180, 195)),
        ("CLIMB IT ROOM BY ROOM, OR GO UP THE CAVE WALL ON THE SHELVES AND IN AT THE TOP", (170, 180, 195)),
        ("OR BLOW THE KEGS AT ITS FOOT - OR BURN THE STEM AND DROP THE CAP ON THE SHRINE", F_MID),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
