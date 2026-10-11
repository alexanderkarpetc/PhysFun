"""Small room S43 - THE SWITCHBACK.

A tall cave fitted out with timber decks: four levels, each split in two by a plank
bulkhead with a flap door in it, the levels joined by ladders at alternate ends. Coming
in at the top, the way down zig-zags - across a level, through its door, down the
ladder, back the other way - so the room is eight cells and you take them one at a
time, each behind a door or under a deck.

The decks are one-way, Terraria style: you come up through them from below and stand
on them from above, and holding S drops you through. So nothing makes you keep to the
zig-zag - drop straight down and you land in the middle of the cell below. They are
timber too: burn one, cut one, blow a hole in one.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from housekit import *  # noqa: F403,E402

CODE = "S43"

GROUND = 420
DECKS = (170, 250, 330)                      # deck tops, top level down
LEVELS = (DECKS[0], DECKS[1], DECKS[2], GROUND)   # the floor of each level
BULK = (236, 168, 262, 196)                  # bulkhead x per level
LADDERS = ("E", "W", "E")                    # which end of each deck its ladder comes up at


def sw_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= GROUND}


def walls_at(m, y, cx):
    xl = cx
    while (xl - 1, y) in m:
        xl -= 1
    xr = cx
    while (xr + 1, y) in m:
        xr += 1
    return xl, xr


def sw_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    cx = X(210)
    teeth(m, X(80), X(340), Y(80), 14)

    # one-way decks, wall to wall, and the ladder up through each at alternate ends
    for i, dy in enumerate(DECKS):
        y = Y(dy)
        xl, xr = walls_at(m, y - 1, cx)
        for x in (xl + 2, xr - 4):                         # where the deck is let into the rock
            rect(x - 2, y + 1, x + 4, y + 6, ROCK_M)
        deck(xl, xr, y)
        lx = xr - 21 if LADDERS[i] == "E" else xl + 21
        ladder_up(lx, y, Y(LEVELS[i + 1]))

    # bulkheads: plank from the level's ceiling down to a door at its floor
    for i, bx in enumerate(BULK):
        fl = Y(LEVELS[i])
        roof = Y(DECKS[i - 1]) + 4 if i else ceil_at(m, X(bx), fl - 40) + 1
        plank_wall(X(bx), roof, X(bx) + 6, fl - 33)
        flap_door(X(bx), fl - 30, 30, 6)

    # props under the decks so each cell reads as a room: a lamp and its furniture
    cells = []
    for i in range(4):
        fl = Y(LEVELS[i])
        top = Y(DECKS[i - 1]) + 4 if i else Y(LEVELS[0] - 60)
        xl, xr = walls_at(m, fl - 8, cx)
        cells.append((xl, X(BULK[i]), X(BULK[i]) + 6, xr, fl, top))
        for (a, b) in ((xl, X(BULK[i])), (X(BULK[i]) + 6, xr)):
            lx = (a + b) // 2 + (0 if i else 24)
            warm_lamp(lx, top if i else ceil_at(m, lx, fl - 20) + 1, drop=4 if i else 30, r=40)

    # level 1, the dome: the way in (west), two by the open hatch (east)
    fl = Y(LEVELS[0])
    crate_g(X(120), fl, 11)
    keg(X(140), fl)
    stand("Gaper", X(290), fl, flip=True)
    stand("Grenadier", X(316), fl, flip=True)
    # level 2: under the first deck; a pyro east, a wizard west at the next hatch
    fl = Y(LEVELS[1])
    stand("Pyro", X(300), fl, flip=True)
    table(X(220), fl)
    stool(X(212), fl)
    stand("WizHollowhood", X(112), fl)
    sack(X(132), fl)
    # level 3: the brute holds the west cell, two more east by the last hatch
    fl = Y(LEVELS[2])
    stand("RiotBrute", X(130), fl)
    bunk(X(70), fl)
    stand("WizCrimson", X(300), fl, flip=True)
    stand("Gaper", X(326), fl, flip=True)
    # level 4, the cave floor: a reaper at the foot of the ladder, the magazine west
    fl = Y(LEVELS[3])
    stand("Reaper", X(272), fl, flip=True)
    stand("Sentinel", X(150), fl)
    for x in (112, 123, 134):
        keg(X(x), fl)
    keg(X(118), fl - 11)


ROOM = {
    "name": "THE SWITCHBACK", "w": 420, "h": 460,
    "shapes": [([("blob", 210, 250, 182, 212)], 0.07)],
    "sockets": {"T1": ("T", 130, 64), "R1": ("R", LEVELS[1], 34),
                "L1": ("L", LEVELS[2], 48), "B1": ("B", 230, 40)},
    "edit": sw_edit,
    "furnish": sw_furnish,
}


SHEET = {
    "seed": 74301,
    "callouts": [
        ("1 EIGHT CELLS, ONE FIGHT EACH", (-125, -50), (180, 210)),
        ("2 LADDERS AT ALTERNATE ENDS", (230, -50), (346, 200)),
        ("3 A FLAP DOOR IN EVERY BULKHEAD", (-125, 484), (171, 236)),
        ("4 ONE-WAY DECKS: UP THROUGH, S TO DROP", (262, 484), (220, 332)),
    ],
    "beats": [
        ("IN AT THE TOP, AND DOWN IN A ZIG-ZAG: DOOR, LADDER, DOOR, LADDER", (170, 180, 195)),
        ("EACH CELL SEES ONLY ITSELF UNTIL ITS DOOR SWINGS", (170, 180, 195)),
        ("OR HOLD S AND DROP THROUGH A DECK - INTO THE MIDDLE OF THE NEXT FIGHT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
