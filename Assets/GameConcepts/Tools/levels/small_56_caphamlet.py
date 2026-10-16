"""Fungal room S56 - THE CAP HAMLET.

Where the cult lives: three houses built the way Terraria's are, walls and floors and
doors, under giant mushrooms - each house is built against a mushroom's stem, or round it,
and its cap is the roof. Walls of stem slabs, floors of the same, doors of cap flesh on a
root frame; a loft up a ladder through a hatch; a window here and there; inside, beds and
racks and jars, the cult asleep or at table. The east house is the store, and it is
full of spore kegs.

You come in high on the west wall onto a shelf of fungus and look down over the roofs. A
ladder takes you down to the lane. Every house is a decision: a door, a window, the roof,
or through the wall. The caps are terrain on stems - burn the big one's stem and its
roof comes down on the loft.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S56"

FLOOR = 290
WALL = 6
LOOKOUT = 170                      # the shelf you come in on
# (stem x, stem height, cap radius) per house
SHROOMS = {"west": (108, 84, 50), "mid": (240, 104, 78), "east": (386, 76, 54)}
LOFT_W = FLOOR - 44                # the west house's loft floor
STOREY = FLOOR - 50                # the middle house's upstairs floor


def under(name):
    """The underside of a house's cap: its ceiling."""
    return FLOOR - SHROOMS[name][1] + 3


# each house: outside faces of its walls (x0, x1); the stem side has no wall of props
HOUSES = {"west": (60, 105), "mid": (170, 310), "east": (383, 434)}


def hamlet_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if y - oy <= FLOOR}


def fungal_wash(x0, y0, x1, y1):
    rect(x0, y0, x1, y1, (70, 58, 96), 0.12)


def hamlet_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR) + 1
    teeth(m, X(40), X(440), Y(80), 16)

    # the mushrooms the houses are built against
    for name, (sx, h, r) in SHROOMS.items():
        giant_shroom(X(sx), fl, h, r)

    # ── the west house: the stem is its east wall; a loft under the cap ──────────
    x0, x1 = HOUSES["west"]
    ceil = Y(under("west"))
    fungal_wash(X(x0), ceil, X(x1), fl - 1)
    plank_wall(X(x0), ceil, X(x0 + WALL), fl - 32)
    flap_door(X(x0), fl - 30, 30, WALL)
    window(X(x0), Y(LOFT_W - 34), X(x0 + WALL), Y(LOFT_W - 22))
    deck(X(x0 + WALL + 1), X(x1 - 1), Y(LOFT_W))
    trapdoor(X(x1 - 18), X(x1 - 1), Y(LOFT_W))                 # against the stem: no sliver past it
    ladder_up(X(x1 - 9), Y(LOFT_W), fl)
    prop("CapStool", X(72), fl)
    prop("GrowRack", X(84), fl)
    stand("Gaper", X(74), fl)
    prop("MushroomBed", X(80), Y(LOFT_W))
    stand("WizBogcap", X(72), Y(LOFT_W), flip=True)             # at the window, looking west
    hang("GlowLantern", X(84), ceil, 4)

    # ── the middle house: built round the stem, two rooms down and two up ────────
    x0, x1 = HOUSES["mid"]
    sx = SHROOMS["mid"][0]
    ceil = Y(under("mid"))
    fungal_wash(X(x0), ceil, X(x1), fl - 1)
    for wx in (x0, x1 - WALL):
        plank_wall(X(wx), ceil, X(wx + WALL), fl - 32)
        flap_door(X(wx), fl - 30, 30, WALL)
    window(X(x0), Y(STOREY - 34), X(x0 + WALL), Y(STOREY - 22))
    window(X(x1 - WALL), Y(STOREY - 34), X(x1), Y(STOREY - 22), shutter=True)
    deck(X(x0 + WALL + 1), X(sx - 6), Y(STOREY))
    deck(X(sx + 6), X(x1 - WALL - 1), Y(STOREY))
    ladder_up(X(200), Y(STOREY), fl)
    ladder_up(X(268), Y(STOREY), fl)
    # down west: the table
    prop("CapTable", X(218), fl)
    prop("CapStool", X(204), fl)
    stand("WizBogcap", X(208), fl)
    stand("WizBogcap", X(230), fl, flip=True)
    prop("CapCandles", X(218), fl - 11)
    # down east: the larder - a rack, a shelf of jars, a gaper
    prop("GrowRack", X(290), fl)
    prop("CapShelf", X(286), fl - 34, at="ceil")
    stand("Gaper", X(254), fl, flip=True)
    # up west: a bed, someone asleep in it
    prop("MushroomBed", X(208), Y(STOREY))
    stand("WizHollowhood", X(222), Y(STOREY), flip=True)
    # up east: a lookout at the shuttered window, a sack
    stand("WizBogcap", X(290), Y(STOREY), flip=True)
    prop("SporeSack", X(252), Y(STOREY))
    hang("GlowLantern", X(206), ceil, 4)
    hang("GlowLantern", X(276), ceil, 4)
    hang("GlowLantern", X(206), Y(STOREY) + 6, 3)
    hang("GlowLantern", X(276), Y(STOREY) + 6, 3)

    # ── the east house: the store, its stem the west wall, its door to the east ──
    x0, x1 = HOUSES["east"]
    ceil = Y(under("east"))
    fungal_wash(X(x0), ceil, X(x1), fl - 1)
    plank_wall(X(x1 - WALL), ceil, X(x1), fl - 32)
    flap_door(X(x1 - WALL), fl - 30, 30, WALL)
    for x in (394, 403, 412):
        prop("SporeKeg", X(x), fl)
    prop("SporeKeg", X(398), fl - 11)
    prop("SporeKeg", X(407), fl - 11)
    prop("SporeSack", X(422), fl)
    stand("WizBogcap", X(448), fl, flip=True)                    # outside, at the door
    hang("GlowLantern", X(408), ceil, 4)

    # ── outside: the shelf you come in on, the lane, the yard ────────────────────
    bracket(X(18), Y(LOOKOUT + 1), "L")
    ladder_up(X(40), Y(LOOKOUT + 1), fl)
    hang("SporePod", X(150), ceil_at(m, X(150), Y(180)) + 1, 30)
    stand("Minespider", X(338), fl)
    prop("MushroomBarrow", X(150), fl)
    hang("GlowLantern", X(340), ceil_at(m, X(340), Y(150)) + 1, 16)
    sprinkle(m, X(20), X(60), Y(FLOOR - 4), 2)
    sprinkle(m, X(320), X(380), Y(FLOOR - 4), 2)
    sprinkle(m, X(440), X(470), Y(FLOOR - 4), 1)


ROOM = {
    "name": "THE CAP HAMLET", "w": 480, "h": 340,
    "shapes": [([
        ("blob", 240, 200, 228, 150),                         # the cave
        ("blob", 240, 270, 232, 40),                          # its floor, wide
        ("tube", [(240, 64), (236, 34), (240, 6)], 12),       # the chimney over the big cap
    ], 0.06)],
    "sockets": {"L1": ("L", LOOKOUT, 20), "R1": ("R", FLOOR, 16), "T1": ("T", 240, 12)},
    "edit": hamlet_edit,
    "furnish": hamlet_furnish,
}

BACK_PATCHES = [(140, 230, 168, 286), (316, 240, 380, 288), (10, 180, 60, 230)]

SHEET = {
    "seed": 75601,
    "callouts": [
        ("1 IN HIGH, OVER THE ROOFS", (-150, 60), (30, 166)),
        ("2 A LOFT UP A LADDER", (-120, 380), (96, 250)),
        ("3 BUILT ROUND THE STEM: FOUR ROOMS", (130, 380), (240, 262)),
        ("4 THE STORE: SPORE KEGS", (330, 380), (404, 280)),
        ("5 CAPS ARE THE ROOFS - BURN A STEM", (190, -50), (240, 160)),
    ],
    "beats": [
        ("THREE HOUSES UNDER THREE MUSHROOMS: WALLS, FLOORS, DOORS, A WINDOW EACH", (170, 180, 195)),
        ("EVERY HOUSE IS A DECISION: THE DOOR, THE WINDOW, THE ROOF, OR THROUGH THE WALL", (170, 180, 195)),
        ("BLOW THE STORE, OR BURN A STEM AND BRING ITS ROOF DOWN ON THE LOFT", F_MID),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
