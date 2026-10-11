"""Small room S45 - THE KEEP.

A stone tower built against the east wall of a tall cave: four floors, each a closed
room of masonry with a hatch in its ceiling, and a battlement on top. Its west face has
an iron door at the foot and arrow slits up it - the people inside see you through
them, and all you see is a slit. Every floor is a room you cannot look into until you
are in it.

Two ways to take it: force the door and fight up, hatch by hatch, or come along the
ledge on the west wall, cross the plank bridge to the battlement and work down. Or do
neither. The powder is kept on the ground floor, on the other side of the west wall.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from housekit import *  # noqa: F403,E402

CODE = "S45"

GROUND = 420
TX0, TX1 = 206, 336            # outside faces of the tower
WALL = 8
FLOORS = (420, 354, 288, 222)  # floor tops: ground, 2, 3, battlement
SLAB = 6
LEDGE = (24, 120, 222)         # x0, x1, top of the west ledge
HATCHES = ((TX0 + WALL + 4, ), (TX1 - WALL - 22, ), (TX0 + WALL + 4, ))


def keep_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > GROUND:
            continue
        if lx > TX1 - 2 and ly > FLOORS[3] - 14:
            continue                                     # the tower is built into the east wall
        out.add((x, y))
    return out


def plank_bridge(x0, y0, x1, y1, sag):
    n = int(abs(x1 - x0) / 5)
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        rect(x, y, x + 3, y + 1, WOOD if i % 2 else WOOD_L)
        rect(x, y + 2, x + 3, y + 2, WOOD_D)
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        pts.append((x0 + (x1 - x0) * t, y0 - 12 + (y1 - y0) * t + sag * 2.6 * t * (1 - t)))
    rope(pts)
    for i in range(0, n + 1, 3):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        line(x, y0 - 12 + (y1 - y0) * t + sag * 2.6 * t * (1 - t),
             x, y0 + (y1 - y0) * t + sag * 4 * t * (1 - t), ROPE_D)


def tower(X, Y):
    x0, x1 = X(TX0), X(TX1)
    top = Y(FLOORS[3])
    interior(x0, top, x1, Y(GROUND))
    # walls, ground to battlement, with merlons
    masonry(x0, top - 2, x0 + WALL, Y(GROUND))
    masonry(x1 - WALL, top - 2, x1, Y(GROUND))
    for mx in range(int(x0), int(x1) - 4, 14):
        if mx > x0 + WALL and mx < x1 - WALL - 6:
            continue
        masonry(mx, top - 12, mx + 7, top - 3)
    masonry(x0 - 3, Y(GROUND) - 6, x0 + WALL + 2, Y(GROUND))     # a battered foot
    # floors, each with a hatch, and ladders under them
    for i, fy in enumerate(FLOORS[1:]):
        y = Y(fy)
        hx = X(HATCHES[i][0] - TX0 + TX0)
        stone_slab(x0 + WALL, hx - 1, y, SLAB)
        stone_slab(hx + 18, x1 - WALL, y, SLAB)
        trapdoor(hx, hx + 17, y, open_=(i == 2))
        ladder_up(hx + 9, y, Y(FLOORS[i]))
    # the door at the foot, and the slits up the west face
    fl = Y(GROUND)
    rect(x0, fl - 31, x0 + WALL, fl - 1, CAVE)
    iron_door(x0 + 2, fl - 30, w=WALL - 4, h=29)
    for fy in FLOORS[1:3]:
        arrow_slit(x0, Y(fy) - 22, WALL, 8)
    arrow_slit(x0, fl - 52, WALL, 8)
    arrow_slit(x1 - WALL, Y(FLOORS[1]) - 22, WALL, 8)


def keep_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    teeth(m, X(40), X(380), Y(70), 18)

    # the west ledge the bridge starts from
    lx0, lx1, ly = LEDGE
    rock_blob(X(lx0 + 30), Y(ly) + 9, 66, 10, rough=0.12, clip=(X(lx0) - 40, Y(ly), X(lx1) + 8, Y(ly) + 30))
    stand("Gaper", X(70), Y(ly))
    warm_lamp(X(60), ceil_at(m, X(60), Y(ly) - 20) + 1, drop=10, r=46)

    tower(X, Y)
    plank_bridge(X(lx1), Y(ly) - 1, X(TX0) - 1, Y(FLOORS[3]) - 1, 16)

    # ground floor: the magazine, against the west wall, and the brute on the door
    fl = Y(GROUND) + 1
    for x in (TX0 + 12, TX0 + 23, TX0 + 34):
        keg(X(x), fl)
    keg(X(TX0 + 18), fl - 11)
    keg(X(TX0 + 29), fl - 11)
    stand("RiotBrute", X(TX1 - 30), fl, flip=True)
    warm_lamp(X((TX0 + TX1) // 2), Y(FLOORS[1]) + SLAB, drop=3, r=40, strength=0.2)
    # second floor: two at the slit, a table
    f2 = Y(FLOORS[1]) + 1
    stand("Sentinel", X(TX0 + 26), f2)
    stand("Gaper", X(TX1 - 44), f2, flip=True)
    table(X(TX0 + 50), f2, 16)
    warm_lamp(X((TX0 + TX1) // 2), Y(FLOORS[2]) + SLAB, drop=3, r=40, strength=0.2)
    # third floor: the bonecrown at the slit, a bunk
    f3 = Y(FLOORS[2]) + 1
    stand("WizBonecrown", X(TX0 + 24), f3)
    bunk(X(TX1 - 40), f3, tiers=2, w=24)
    stand("Pyro", X(TX0 + 64), f3, flip=True)
    warm_lamp(X((TX0 + TX1) // 2), Y(FLOORS[3]) + SLAB, drop=3, r=40, strength=0.2)
    # battlement: a grenadier over the bridge, a brazier
    f4 = Y(FLOORS[3]) + 1
    stand("Grenadier", X(TX0 + 28), f4)
    rect(X(TX1 - 30), f4 - 8, X(TX1 - 20), f4 - 1, MET_D)
    rect(X(TX1 - 29), f4 - 10, X(TX1 - 21), f4 - 8, EMBER)
    glow(X(TX1 - 25), f4 - 12, 40, F_MID, 0.22)

    # the cave floor: the approach, a spider and a cart of rubble for cover
    fg = Y(GROUND) + 1
    stand("Minespider", X(160), fg)
    crate_g(X(110), fg, 12)
    crate_g(X(122), fg, 10)
    for k in range(18):
        x = X(40) + rnd() * 50
        rect(x, fg - 2 - rnd() * 3, x + 3, fg - 1, pick([STONE, STONE_D, ROCK_M]))
    warm_lamp(X(150), ceil_at(m, X(150), Y(300)) + 1, drop=10, r=60)


ROOM = {
    "name": "THE KEEP", "w": 420, "h": 460,
    "shapes": [([("blob", 214, 262, 196, 200)], 0.06)],
    "sockets": {"L1": ("L", GROUND, 68), "L2": ("L", LEDGE[2], 26),
                "T1": ("T", 110, 84), "T2": ("T", 300, 72)},
    "edit": keep_edit,
    "furnish": keep_furnish,
}


SHEET = {
    "seed": 74501,
    "callouts": [
        ("1 BRIDGE TO THE TOP", (-125, -50), (160, 234)),
        ("2 SLITS: THEY SEE YOU, YOU SEE A SLIT", (180, -50), (210, 330)),
        ("3 IRON DOOR, SHUT", (-125, 484), (210, 404)),
        ("4 THE POWDER IS BEHIND THIS WALL", (160, 484), (226, 410)),
    ],
    "beats": [
        ("A STONE KEEP: FOUR FLOORS, EACH A SHUT ROOM, ONE HATCH UP", (170, 180, 195)),
        ("FORCE THE DOOR AND FIGHT UP, OR CROSS THE BRIDGE AND WORK DOWN", (170, 180, 195)),
        ("OR BLOW THE WEST WALL AT THE FOOT, WHERE THE KEGS ARE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
