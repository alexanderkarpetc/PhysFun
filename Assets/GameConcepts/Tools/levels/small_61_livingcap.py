"""Fungal room S61 - THE LIVING CAP.

One mushroom, big enough to live in - the way Terraria's living trees are lived in. Its
stem is hollowed into five rooms stacked up its middle, one over the next, a hatch in
every floor on alternate sides and a ladder up through it; slits for windows; an arch for
a door at its foot. Its cap is hollowed into the cult's hall. All of it is the mushroom:
walls, floors and roof are stem and cap, and they burn.

You come in high on the west wall onto a shelf, level with the hall's west window, and
can go straight in at the top. Or in at the door at the foot and up through every room.
The fourth room up is the store, under the hall's floor.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S61"

FLOOR = 420
CX, HW, H, R = 220, 32, 250, 124
IN0, IN1 = CX - 24, CX + 24        # the rooms' inside, x
# the storeys: (top of the room's air, its floor row), bottom up
ROOMS = [(386, 421), (342, 378), (298, 334), (254, 290), (210, 246)]
SLAB = 8                           # floor thickness between rooms
HALL_FLOOR = 171                   # the hall's floor row (the stem's top)


def hatch_x(i):
    """The hatch over room i: east side for even rooms, west for odd."""
    return (CX + 8, CX + 24) if i % 2 == 0 else (CX - 24, CX - 8)


def holes():
    """Everything carved out of the mushroom, room coords."""
    out = []
    for i, (top, fl) in enumerate(ROOMS):
        out.append((IN0, top, IN1, fl - 1))
        hx0, hx1 = hatch_x(i)
        above = ROOMS[i + 1][1] if i + 1 < len(ROOMS) else HALL_FLOOR
        out.append((hx0, above, hx1, top - 1))                  # the hatch up out of it
        side = -1 if i % 2 else 1                               # a window slit, alternate sides
        wx = CX + side * (HW + 6)
        out.append((min(wx, CX + side * 20), top + 10, max(wx, CX + side * 20), top + 17))
    out.append((CX - 44, ROOMS[0][1] - 31, IN0, ROOMS[0][1] - 1))   # the door at the foot, west
    out += [(140, 126, 300, HALL_FLOOR - 1), (180, 112, 260, 126)]  # the hall
    out += [(98, 146, 140, 156), (300, 146, 342, 156)]              # its windows
    out.append((CX - 6, 96, CX + 6, 112))                           # the chimney out of its crown
    return out


def cap_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def cap_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(40), X(400), Y(60), 14)

    living_shroom(X(CX), fl, HW, H, R, [(X(a), Y(b), X(c), Y(d)) for a, b, c, d in holes()])

    # ladders up through the hatches
    for i, (top, rfl) in enumerate(ROOMS):
        hx0, hx1 = hatch_x(i)
        above = ROOMS[i + 1][1] if i + 1 < len(ROOMS) else HALL_FLOOR
        ladder_up(X((hx0 + hx1) // 2), Y(above), Y(rfl))

    def lamp(i):
        top = ROOMS[i][0]
        hx0, hx1 = hatch_x(i)
        x = CX - 14 if hx0 > CX else CX + 14
        hang("GlowLantern", X(x), Y(top), 2)

    def on(i):
        return Y(ROOMS[i][1])

    # 0, at the door: a gaper on a rug
    prop("MycelRug", X(CX - 8), on(0))
    stand("Gaper", X(CX - 10), on(0))
    lamp(0)
    # 1, the kitchen
    prop("CapTable", X(CX + 2), on(1))
    prop("RootChair", X(CX - 16), on(1))
    stand("WizBogcap", X(CX - 6), on(1))
    lamp(1)
    # 2, where they sleep
    prop("MushroomBed", X(CX - 8), on(2))
    prop("CapCupboard", X(CX + 14), on(2))
    stand("WizHollowhood", X(CX - 4), on(2), flip=True)
    lamp(2)
    # 3, the grow room
    prop("GrowRack", X(CX + 10), on(3))
    prop("PlanterBox", X(CX - 12), on(3))
    stand("Minespider", X(CX - 6), on(3))
    lamp(3)
    # 4, the store under the hall
    for x in (CX - 18, CX - 9, CX):
        prop("SporeKeg", X(x), on(4))
    prop("SporeKeg", X(CX - 14), on(4) - 11)
    prop("SporeSack", X(CX + 2), on(4) - 11)
    stand("WizBogcap", X(CX + 16), on(4), flip=True)
    lamp(4)

    # the hall in the cap
    hf = Y(HALL_FLOOR)
    prop("FungalIdol", X(CX), hf)
    prop("CapCandles", X(CX - 22), hf)
    prop("CapCandles", X(CX + 22), hf)
    stand("WizMaskwraith", X(CX + 44), hf, flip=True)
    stand("WizBogcap", X(CX - 46), hf)
    stand("WizBogcap", X(CX - 64), hf)
    hang("SporeSacs", X(CX - 30), Y(126), 2)
    hang("SporeSacs", X(CX + 30), Y(126), 2)
    hang("GlowLantern", X(CX - 60), Y(126), 2)
    hang("GlowLantern", X(CX + 60), Y(126), 2)

    # outside: the shelf you come in on, lamps round the foot, growth
    bracket(X(24), Y(151), "L")
    prop("GlowLampPost", X(150), fl)
    prop("GlowLampPost", X(300), fl)
    prop("MushroomBarrow", X(330), fl)
    stand("Minespider", X(370), fl, flip=True)
    stand("Ghast", X(90), Y(280))
    sprinkle(m, X(20), X(170), Y(FLOOR - 4), 4, gap=14)
    sprinkle(m, X(270), X(420), Y(FLOOR - 4), 4, gap=14)


ROOM = {
    "name": "THE LIVING CAP", "w": 440, "h": 450,
    "shapes": [([
        ("blob", 220, 230, 212, 210),                         # the cave
        ("blob", 220, 400, 214, 40),                          # its floor, wide
    ], 0.06)],
    "sockets": {"L1": ("L", 150, 26), "R1": ("R", FLOOR, 16), "T1": ("T", 220, 22)},
    "edit": cap_edit,
    "furnish": cap_furnish,
}

BACK_HOUSES = [(IN0, ROOMS[-1][0], IN1, FLOOR), (140, 112, 300, HALL_FLOOR)]
BACK_PATCHES = [(20, 360, 140, 418), (300, 360, 420, 418)]

SHEET = {
    "seed": 76101,
    "callouts": [
        ("1 IN HIGH, AT THE HALL'S WINDOW", (-150, 90), (60, 148)),
        ("2 FIVE ROOMS UP THE STEM", (-150, 300), (200, 330)),
        ("3 THE HATCHES ZIG-ZAG", (330, 470), (236, 380)),
        ("4 THE STORE UNDER THE HALL", (330, 240), (210, 230)),
        ("5 THE HALL IN THE CAP", (240, -50), (220, 150)),
    ],
    "beats": [
        ("A MUSHROOM LIVED IN LIKE A TREE: ROOMS UP THE STEM, A HALL IN THE CAP", (170, 180, 195)),
        ("UP THROUGH EVERY ROOM FROM THE DOOR, OR IN AT THE TOP BY THE WINDOW", (170, 180, 195)),
        ("BLOW THE STORE AND THE HALL'S FLOOR GOES - OR SET THE STEM ALIGHT", F_MID),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
