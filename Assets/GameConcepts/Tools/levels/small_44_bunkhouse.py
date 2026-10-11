"""Small room S44 - THE BUNKHOUSE.

A two-storey timber house built on the floor of a wide cave, the way Terraria houses
stand: plank walls, plank floors, flap doors, an attic under a slate roof. The crew live
in it - two rooms down, two up, a lookout in the attic - and each room is closed off
from the next by a wall or a floor. From outside you see nobody but whoever is at a
window, and they see you.

Every way in is a decision: the front door off the porch, the back door off the yard,
over the roof and in at the gable, or straight through the planks. It is all timber,
and there is a pyro in the kitchen next to the stove.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from housekit import *  # noqa: F403,E402

CODE = "S44"

FLOOR = 300
HX0, HX1 = 112, 352            # outside faces of the west and east walls
MID = 240                      # top of the upstairs deck
EAVE = 180                     # top of the wall plate
RIDGE = 50                     # roof height over the eave
WALL = 8
INNER_DN = 226                 # downstairs partition x
INNER_UP = 214                 # upstairs partition x
HATCH = 300                    # x of the hatch upstairs


def bunk_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def house(X, Y):
    fl, md, ev = Y(FLOOR), Y(MID), Y(EAVE)
    x0, x1 = X(HX0), X(HX1)
    interior(x0, ev, x1, fl)
    pitched_roof(x0, x1, ev, RIDGE)
    rect(x0, ev, x1, ev + 3, WOOD_D)                                # wall plate
    rect(x0, ev, x1, ev, WOOD_L)
    # walls, with their doors and windows cut out of them
    plank_wall(x0, ev + 4, x0 + WALL, fl - 32)                     # west, over the front door
    plank_wall(x1 - WALL, ev + 4, x1, fl - 32)                     # east, over the back door
    window(x0, md - 38, x0 + WALL, md - 22)                         # upstairs west window
    window(x1 - WALL, md - 38, x1, md - 22, shutter=True)           # upstairs east, shuttered
    window(x0, fl - 54, x0 + WALL, fl - 42)                         # kitchen window, high
    flap_door(x0, fl - 30, 30, WALL)                                # front door
    flap_door(x1 - WALL, fl - 30, 30, WALL)                         # back door
    # the upstairs deck, with its hatch, and the ladder under it
    deck(x0 + WALL + 1, X(HATCH) - 1, md)
    deck(X(HATCH) + 18, x1 - WALL - 1, md)
    trapdoor(X(HATCH), X(HATCH) + 17, md)
    ladder_up(X(HATCH) + 9, md, fl)
    # partitions
    plank_wall(X(INNER_DN), md + 4, X(INNER_DN) + 5, fl - 32)
    flap_door(X(INNER_DN), fl - 30, 30, 5)
    plank_wall(X(INNER_UP), ev + 4, X(INNER_UP) + 5, md - 32)
    flap_door(X(INNER_UP), md - 30, 30, 5)
    # the attic floor and the gable window west
    deck(x0 + WALL + 1, x1 - WALL - 1, ev + 4, thick=3, joists=False)
    rect(X(225), ev - 28, X(239), ev - 18, CAVE)                    # gable vent, a slot
    # the porch out front and the yard out back
    deck(x0 - 34, x0 - 1, fl - 4, thick=4, joists=False)
    post(x0 - 34, fl - 40, fl - 1, 2)
    shed_roof(x0 - 36, x0, fl - 42, fl - 38, 3)


def bunk_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl, md, ev = Y(FLOOR) + 1, Y(MID), Y(EAVE)
    teeth(m, X(20), X(440), Y(80), 22)

    house(X, Y)

    # kitchen (down, west): stove with its flue through every floor, table, two at it
    stove(X(126), fl, flue_to=ev - 34)
    for y in (md, ev + 4):
        rect(X(130), y, X(133), y + 3, MET_D)
    table(X(176), fl, 20)
    stool(X(168), fl)
    shelf(X(186), fl - 28, 20)
    stand("Pyro", X(150), fl)
    stand("Gaper", X(206), fl, flip=True)
    warm_lamp(X(190), md + 4, drop=4, r=48, strength=0.2)
    # bunk room (down, east)
    bunk(X(236), fl)
    bunk(X(316), fl)
    stand("RiotBrute", X(280), fl, flip=True)
    warm_lamp(X(286), md + 4, drop=4, r=48, strength=0.2)
    # upstairs west: a goldhood at the open window, looking down on the porch
    stand("WizGoldhood", X(142), md + 1)
    sack(X(180), md + 1)
    sack(X(190), md + 1)
    warm_lamp(X(170), ev + 7, drop=3, r=44, strength=0.2)
    # upstairs east: a grenadier by the hatch and the shuttered window
    stand("Grenadier", X(282), md + 1, flip=True)
    keg(X(330), md + 1)
    crate_g(X(256), md + 1, 11)
    warm_lamp(X(276), ev + 7, drop=3, r=44, strength=0.2)
    # the attic: a sentinel at the gable slot, crates
    stand("Sentinel", X(214), ev + 4)
    crate_g(X(176), ev + 4, 9)
    crate_g(X(282), ev + 4, 9)

    # outside: the porch lamp, a woodpile and a sleeper in the yard, a ledge east
    warm_lamp(X(HX0 - 18), fl - 38, drop=4, r=50)
    for k in range(4):
        for j in range(4 - k):
            disc(X(366) + j * 7 + k * 3, fl - 4 - k * 6, 3, WOOD)
            ring(X(366) + j * 7 + k * 3, fl - 4 - k * 6, 3, WOOD_D)
    stand("Gaper", X(410), fl, flip=True)
    rock_blob(X(40), Y(226), 30, 8, rough=0.2)
    stand("Minespider", X(44), Y(218))
    warm_lamp(X(400), ceil_at(m, X(400), Y(250)) + 1, drop=8, r=60)


ROOM = {
    "name": "THE BUNKHOUSE", "w": 460, "h": 360,
    "shapes": [([("blob", 230, 206, 220, 132)], 0.06)],
    "sockets": {"L1": ("L", FLOOR, 42), "R1": ("R", FLOOR, 38),
                "T1": ("T", 120, 96), "T2": ("T", 380, 100)},
    "edit": bunk_edit,
    "furnish": bunk_furnish,
}


SHEET = {
    "seed": 74401,
    "callouts": [
        ("1 A WINDOW IS A SIGHT LINE BOTH WAYS", (-125, -50), (116, 210)),
        ("2 OVER THE ROOF, IN AT THE GABLE", (250, -50), (232, 158)),
        ("3 FLAP DOORS: PUSH THROUGH OR SHOOT OFF", (-125, 384), (116, 284)),
        ("4 A PYRO BY THE STOVE", (270, 384), (150, 290)),
    ],
    "beats": [
        ("A TIMBER HOUSE IN A CAVE: FIVE ROOMS, A WALL OR A FLOOR BETWEEN EACH", (170, 180, 195)),
        ("FRONT DOOR, BACK DOOR, THE ROOF, OR STRAIGHT THROUGH THE PLANKS", (170, 180, 195)),
        ("IT IS ALL TIMBER - AND THE KITCHEN HAS A STOVE AND A PYRO", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
