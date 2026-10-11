"""Small room S42 - THE ROLLWAY.

A ring of tunnel round a core of solid rock. From the west entry it runs east along the
top, drops down the east side, comes back west along the bottom into a low pocket, and
a ladder shaft up the west side closes the loop. The core is the point: whichever way
round you go, the next bend hides the next group, so you meet them one at a time.

The track falls the whole way round, and at the top of it a boulder sits on a timber
chock. Knock the chock out and it goes the way you would have - along the top, down
the drop, back along the bottom - and fetches up against the kegs in the low pocket.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from housekit import *  # noqa: F403,E402

CODE = "S42"

TOP = [(30, 104), (120, 98), (200, 116), (280, 118), (346, 140), (392, 184)]
DROP = [(392, 184), (420, 232), (406, 270), (378, 298)]
BOTTOM = [(378, 298), (310, 304), (250, 328), (170, 318), (116, 336)]
SHAFT = [(62, 300), (48, 220), (64, 160), (58, 112)]
POCKET = (82, 324, 54, 34)
BOULDER = (136, 104)


def roll_edit(air, ox, oy):
    S = lambda pts: [(x + ox, y + oy) for x, y in pts]
    return air | cave_mask([
        ("tube", S(TOP), 21),
        ("tube", S(DROP), 22),
        ("tube", S(BOTTOM), 21),
        ("tube", S(SHAFT), 11),
    ], rough=0.13, top=0)


def boulder(cx, cy, r):
    disc(cx, cy, r, STONE)
    for _ in range(50):
        a, d = rnd() * 6.283, rnd() * r * 0.9
        px(cx + d * math.cos(a), cy + d * math.sin(a), pick([STONE_D, STONE, STONE_L]))
    for k in range(-r + 3, r - 2):
        px(cx + k, cy - int((r * r - k * k) ** 0.5) + 1, STONE_L)
    ring(cx, cy, r, STONE_D)


def chock(x, floor):
    """A timber wedge under the boulder's downhill side."""
    for k in range(8):
        rect(x, floor - 1 - k, x + 9 - k, floor - 1 - k, WOOD if k else WOOD_D)
    rect(x, floor - 8, x, floor - 1, WOOD_L)


def roll_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    F = lambda lx, ly: floor_at(m, X(lx), Y(ly))

    teeth(m, X(120), X(360), Y(110), 14)
    teeth(m, X(150), X(390), Y(310), 12)
    teeth(m, X(380), X(430), Y(230), 4)
    # the core: solid, with a vein in it so it reads as rock and not as a hole
    x, y = X(140), Y(214)
    for k in range(90):
        x += 2
        y += pick([-1, 0, 0, 1])
        if rnd() < 0.7:
            rect(x, y, x + 1 + int(rnd() * 2), y + int(rnd() * 2), ORE, 0.75)

    # the top: the boulder on its chock, the track falling east, one lookout at the bend
    bx = X(BOULDER[0])
    by = F(BOULDER[0], 100)
    boulder(bx, by - 15, 15)
    chock(bx + 12, F(BOULDER[0] + 14, 100))
    for lx in range(110, 340, 34):
        fy = F(lx, 110)
        rect(X(lx), fy - 1, X(lx) + 1, fy - 1, (170, 176, 186), 0.5)       # grooves the last one cut
    stand("Gaper", X(330), F(330, 120))
    warm_lamp(X(220), ceil_at(m, X(220), Y(110)) + 1, drop=4, r=60)

    # the drop: a niche in the east wall with a sentinel in it
    rock_blob(X(424), Y(246), 16, 6, rough=0.2)
    stand("Sentinel", X(416), Y(240) - 1, flip=True)
    warm_lamp(X(386), ceil_at(m, X(386), Y(200)) + 1, drop=6, r=46)

    # the bottom: two walking it, round the next bend from the drop
    stand("RiotBrute", X(300), F(300, 310), flip=True)
    stand("Pyro", X(240), F(240, 320), flip=True)
    crate_g(X(330), F(330, 310), 11)
    warm_lamp(X(270), ceil_at(m, X(270), Y(320)) + 1, drop=4, r=60)

    # the low pocket: where everything ends up, kegs stacked against the west wall
    fp = F(84, 330)
    for x in (40, 51, 62):
        keg(X(x), F(x, 330))
    keg(X(46), F(46, 330) - 11)
    keg(X(57), F(57, 330) - 11)
    stand("WizBonecrown", X(80), F(80, 330), flip=True)
    stand("Grenadier", X(120), F(120, 330), flip=True)
    warm_lamp(X(84), ceil_at(m, X(84), Y(320)) + 1, drop=6, r=50)

    # the ladder shaft up the west side, back to the top
    ladder_up(X(56), Y(124), Y(298))
    sprite("Ghast", X(48), Y(190))


ROOM = {
    "name": "THE ROLLWAY", "w": 440, "h": 400,
    "shapes": [([("blob",) + POCKET], 0.1)],
    "sockets": {"L1": ("L", 120, 30), "T1": ("T", 250, 106),
                "R1": ("R", 330, 40), "B1": ("B", 96, 52)},
    "edit": roll_edit,
    "furnish": roll_furnish,
}


SHEET = {
    "seed": 74201,
    "callouts": [
        ("1 BOULDER ON A CHOCK", (-125, -50), (136, 96)),
        ("2 THE TRACK FALLS ALL THE WAY ROUND", (150, -50), (360, 150)),
        ("3 EVERY BEND HIDES THE NEXT ONE", (250, 420), (390, 290)),
        ("4 KEGS WHERE IT STOPS", (-125, 420), (52, 320)),
        ("5 LADDER BACK UP", (-125, 200), (58, 220)),
    ],
    "beats": [
        ("A RING ROUND SOLID ROCK: YOU MEET THEM ONE BEND AT A TIME", (170, 180, 195)),
        ("KNOCK THE CHOCK OUT AND THE BOULDER RUNS THE WHOLE TRACK - KEGS LAST", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
