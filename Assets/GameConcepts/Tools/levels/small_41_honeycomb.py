"""Small room S41 - THE HONEYCOMB.

Not one hall but four pockets in the rock, each with its own floor and its own people,
joined by a crawl, a drop hole, a shaft and a tube with a plank plug in it. Rock stands
between every pair, so from any pocket you see that pocket and nothing else: the room
is four small fights in a row, not one big one.

The pockets are tied together by one rope. It is made fast on a cleat in the north
pocket, runs down a hole bored through the rock, and holds a net of ore over the crew
in the east pocket, who cannot see the cleat and do not know what is over them. Cut it
up there and the fight down there is over before it starts. Or shoot out the plug, drop
down the shaft, and have all of them at once.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from housekit import *  # noqa: F403,E402

CODE = "S41"

# pocket: centre, radii, floor y, flattened x-range
A = dict(c=(80, 236), r=(60, 38), floor=258, xs=(26, 128))      # west, the way in
B = dict(c=(214, 116), r=(74, 38), floor=142, xs=(160, 286))     # north, the tie
C = dict(c=(338, 268), r=(86, 54), floor=304, xs=(256, 424))     # east, the crew
D = dict(c=(168, 330), r=(50, 26), floor=346, xs=(122, 216))     # south, the store
HOLE_X = 276                                                     # the rope's bore
NET_Y = 238
FRAME_H = 22                                                     # the sheave frame over it


def tubes(ox, oy):
    S = lambda pts: [(x + ox, y + oy) for x, y in pts]
    return cave_mask([
        ("tube", S([(108, 250), (134, 200), (156, 134)]), 11),      # A -> B, a slanted crawl
        ("tube", S([(112, 256), (128, 300), (146, 340)]), 9),       # A -> D, a drop hole
        ("tube", S([(204, 340), (240, 330), (266, 300)]), 10),      # D -> C, the plugged tube
        ("tube", S([(284, 128), (310, 180), (318, 226)]), 9),       # B -> C, the drop shaft
    ], rough=0.08, top=0)


def honey_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        cut = False
        for p in (A, B, C, D):
            if p["xs"][0] <= lx <= p["xs"][1] and p["floor"] < ly < p["floor"] + 60:
                cut = True
        if not cut:
            out.add((x, y))
    return out | tubes(ox, oy)


def cargo_net(cx, top, w=30, h=22):
    """A net of ore on a hook: the mesh, and the lumps showing through it."""
    rect(cx - 2, top, cx + 2, top + 2, MET_L)
    line(cx, top + 2, cx - w // 2, top + 8, MET_D)
    line(cx, top + 2, cx + w // 2, top + 8, MET_D)
    for k in range(40):
        x = cx - w // 2 + 2 + rnd() * (w - 4)
        y = top + 9 + rnd() * (h - 6)
        rect(x, y, x + 2 + rnd() * 3, y + 1 + rnd() * 2, pick([ORE, STONE, STONE_D, (170, 140, 80)]))
    for k in range(-w // 2, w // 2 + 1, 3):
        px(cx + k, top + 8, ROPE_D)
        px(cx + k, top + h + 3, ROPE_D)
    for y in range(top + 8, top + h + 4, 3):
        px(cx - w // 2, y, ROPE_D)
        px(cx + w // 2, y, ROPE_D)


def sheave_frame(x, floor):
    """Two timber legs astride the bore and a crossbar with a sheave on it: the rope comes
    off the crossbar, so there is a man-high length of it in the north pocket to cut."""
    top = floor - FRAME_H
    for dx in (-7, 6):
        rect(x + dx, top, x + dx + 1, floor - 1, WOOD)
        rect(x + dx, top, x + dx, floor - 1, WOOD_L)
    rect(x - 8, top - 2, x + 8, top, WOOD)
    rect(x - 8, top - 2, x + 8, top - 2, WOOD_L)
    pulley(x, top + 3)


def honey_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    for p in (A, B, C, D):
        teeth(m, X(p["c"][0] - p["r"][0] + 10), X(p["c"][0] + p["r"][0] - 10), Y(p["c"][1]), 6)
        warm_lamp(X(p["c"][0] - 10), ceil_at(m, X(p["c"][0] - 10), Y(p["c"][1])) + 1, drop=6,
                  r=int(p["r"][0] * 1.1))

    # A, the way in: one gaper with its back to you, and a crate to stand on
    fa = Y(A["floor"]) + 1
    stand("Gaper", X(96), fa)
    crate_g(X(44), fa, 11)

    # B, the north pocket: the sheave frame over the bore, two on watch by it
    fb = Y(B["floor"]) + 1
    rect(X(HOLE_X - 2), fb, X(HOLE_X + 2), Y(232), CAVE)          # the bore through the rock
    sheave_frame(X(HOLE_X), fb)
    rope([(X(HOLE_X), fb - FRAME_H + 3), (X(HOLE_X), Y(216))])
    stand("WizCrimson", X(206), fb)
    stand("Grenadier", X(178), fb)
    keg(X(226), fb)
    sack(X(160), fb)

    # C, the east pocket: the net over the crew, who are looking the other way
    fc = Y(C["floor"]) + 1
    rope([(X(HOLE_X), Y(214)), (X(HOLE_X), Y(NET_Y))])
    cargo_net(X(HOLE_X), Y(NET_Y), 34, 22)
    stand("RiotBrute", X(286), fc, flip=True)
    stand("Gaper", X(264), fc)
    stand("Pyro", X(308), fc, flip=True)
    rock_blob(X(414), Y(250), 18, 7, rough=0.2)                     # a shelf on the east wall
    stand("Sentinel", X(406), Y(244) - 1, flip=True)
    crate_g(X(330), fc, 12)
    crate_g(X(331), fc - 12, 10)
    keg(X(372), fc)

    # D, the store: kegs and a spider, and the plank plug in the tube to C
    fd = Y(D["floor"]) + 1
    for k, x in enumerate((134, 145, 156)):
        keg(X(x), fd)
    keg(X(140), fd - 11)
    stand("Minespider", X(188), fd, flip=True)
    plank_wall(X(234), Y(318), X(239), Y(343))                       # the plug
    for k in range(5):
        rect(X(230 + k * 2), Y(316) - k, X(231 + k * 2), Y(316) - k, WOOD_D)

    # a ladder up the drop shaft, so B -> C is a way back too
    ladder_up(X(314), Y(184), Y(C["floor"]))


ROOM = {
    "name": "THE HONEYCOMB", "w": 440, "h": 380,
    "shapes": [([("blob",) + p["c"] + p["r"] for p in (A, B, C, D)], 0.1)],
    "sockets": {"L1": ("L", A["floor"], 24), "T1": ("T", 214, 82),
                "R1": ("R", C["floor"], 20), "B1": ("B", 168, 36)},
    "edit": honey_edit,
    "furnish": honey_furnish,
}


SHEET = {
    "seed": 74101,
    "callouts": [
        ("1 EACH POCKET SEES ONLY ITSELF", (-125, -50), (150, 190)),
        ("2 THE ROPE HANGS FROM HERE", (250, -50), (276, 124)),
        ("3 AND HOLDS THIS", (330, 400), (290, 250)),
        ("4 PLANK PLUG", (40, 400), (236, 330)),
        ("5 DROP SHAFT", (446, 150), (314, 196)),
    ],
    "beats": [
        ("FOUR POCKETS, FOUR SMALL FIGHTS - ROCK BETWEEN THEM BREAKS SIGHT", (170, 180, 195)),
        ("CUT THE ROPE UP NORTH AND THE NET LANDS ON THE EAST CREW, WHO NEVER SAW YOU", F_MID),
        ("OR SHOOT THE PLUG AND DROP THE SHAFT, AND HAVE THEM ALL AT ONCE", (170, 180, 195)),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
