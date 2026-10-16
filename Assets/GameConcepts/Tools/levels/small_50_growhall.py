"""Fungal room S50 - THE GROW HALL.

The cult's farm: four pockets in the rock, each with its racks of logs and its crop, joined
by crawls - rock between every pair, so each pocket is its own small fight. The middle
one is the hall where the crew eats, at a table cut from a giant cap, and over the table
the cult has let the crop grow down from the roof: two masses of caps on stalks, each
heavier than a man, hanging by a cord of stalk each.

Cut a cord and a mass of caps lands on the table. You see the table from the crawl you
come in by, and the cords from there too. Up the slanted crawl is the store, with the
logs and the dust and the way out east; down the drop hole is the cellar, where the
spiders keep the racks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S50"

A = dict(c=(80, 200), r=(64, 34), floor=226, xs=(22, 138))     # west, the way in
B = dict(c=(242, 228), r=(92, 50), floor=268, xs=(160, 322))   # the hall
C = dict(c=(366, 120), r=(72, 32), floor=146, xs=(302, 432))   # the store
D = dict(c=(196, 336), r=(72, 24), floor=352, xs=(132, 258))   # the cellar


def tubes(ox, oy):
    S = lambda pts: [(x + ox, y + oy) for x, y in pts]
    return cave_mask([
        ("tube", S([(128, 214), (150, 226), (170, 240)]), 11),     # A -> B, the crawl in
        ("tube", S([(306, 222), (330, 176), (350, 140)]), 11),     # B -> C, slanted
        ("tube", S([(250, 266), (234, 300), (214, 330)]), 9),      # B -> D, the drop hole
    ], rough=0.08, top=0)


def hall_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if any(p["xs"][0] <= lx <= p["xs"][1] and p["floor"] < ly < p["floor"] + 60 for p in (A, B, C, D)):
            continue
        out.add((x, y))
    return out | tubes(ox, oy)


def hall_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    for p in (A, B, C, D):
        teeth(m, X(p["c"][0] - p["r"][0] + 12), X(p["c"][0] + p["r"][0] - 12), Y(p["c"][1]), 4)
    fa, fb, fc, fd = (Y(p["floor"]) + 1 for p in (A, B, C, D))

    # A, the way in: one tending a rack, his back to you
    prop("GrowRack", X(110), fa)
    stand("WizBogcap", X(88), fa)
    prop("CropBasket", X(66), fa)
    hang("GlowLantern", X(50), ceil_at(m, X(50), Y(200)) + 1, 8)

    # B, the hall: the table, the crew, and the crop hung over them
    prop("CapTable", X(238), fb)
    prop("CapStool", X(214), fb)
    prop("CapStool", X(262), fb)
    prop("SporeJars", X(232), fb - 12)
    stand("WizBogcap", X(220), fb)
    stand("Gaper", X(254), fb, flip=True)
    stand("WizBogcap", X(280), fb, flip=True)
    for x, drop in ((226, 12), (262, 18)):
        hang("HangingCaps", X(x), ceil_at(m, X(x), Y(220)) + 1, drop)
    prop("GrowRack", X(178), fb)
    prop("GrowRack", X(306), fb)
    hang("GlowLantern", X(300), ceil_at(m, X(300), Y(220)) + 1, 10)

    # C, the store: logs, dust, the way out east
    prop("RotLog", X(356), fc)
    prop("SporeKeg", X(318), fc)
    prop("SporeKeg", X(327), fc)
    prop("SporeSack", X(408), fc)
    stand("WizHollowhood", X(392), fc, flip=True)
    hang("GlowLantern", X(410), ceil_at(m, X(410), Y(120)) + 1, 6)

    # D, the cellar: racks in the dark, spiders
    prop("GrowRack", X(150), fd)
    prop("GrowRack", X(176), fd)
    stand("Minespider", X(210), fd)
    stand("Minespider", X(238), fd, flip=True)
    prop("MushroomCrate", X(248), fd)

    for p in (A, B, C, D):
        sprinkle(m, X(p["xs"][0] + 4), X(p["xs"][1] - 4), Y(p["floor"] - 4), 2, gap=14)


ROOM = {
    "name": "THE GROW HALL", "w": 460, "h": 380,
    "shapes": [([("blob",) + p["c"] + p["r"] for p in (A, B, C, D)], 0.1)],
    "sockets": {"L1": ("L", A["floor"], 22), "T1": ("T", 366, 90),
                "R1": ("R", C["floor"], 28), "B1": ("B", 196, 30)},
    "edit": hall_edit,
    "furnish": hall_furnish,
}

BACK_PATCHES = [(200, 190, 290, 260), (40, 180, 120, 220), (320, 100, 410, 140), (150, 320, 250, 350)]

SHEET = {
    "seed": 75001,
    "callouts": [
        ("1 THE CRAWL IN - THE TABLE IN VIEW", (-130, 140), (140, 220)),
        ("2 THE CROP HUNG OVER THE TABLE", (-40, -50), (226, 196)),
        ("3 CUT A CORD", (300, -50), (262, 180)),
        ("4 STORE", (470, 70), (400, 140)),
        ("5 THE CELLAR", (-60, 400), (190, 346)),
    ],
    "beats": [
        ("FOUR POCKETS, FOUR FIGHTS - ROCK BETWEEN EVERY PAIR", (170, 180, 195)),
        ("DROP: CUT A STALK CORD AND A MASS OF CAPS LANDS ON THE TABLE", F_MID),
        ("OR GO ROUND BY THE CELLAR AND THE STORE AND LEAVE THE HALL EATING", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
