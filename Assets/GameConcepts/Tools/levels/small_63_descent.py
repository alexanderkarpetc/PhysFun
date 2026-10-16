"""Fungal room S63 - THE DESCENT.

After Hollow Knight's way down through the Fungal Wastes to the Mantis Village: a long
drop with a warning at the top of it, a tribe's homes clinging to the walls on the way
down, and at the bottom the arena where its three champions sit and bar the way deeper.

A shaft from the roof to a bowl. At the top, before the drop, what is left of the last
one who came this way, hung up as a warning. Off the shaft, in bubbles in the rock on
alternate sides, the tribe's pod-houses grown on their ledges, each with its arch
facing the drop; shelves of fungus step down between them. At the bottom the champions
on their brick seats, two masses of caps hung over the arena; under it, the way on.
You can leave the descent halfway - out of the west pod or the east one - and never
meet them.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S63"

ARENA = 440
PODS = {   # bubble centre, radii, floor, house x0..x1, its arch side, its roof's high side
    "P1": dict(c=(108, 120), r=(52, 30), floor=140, house=(70, 130), door="R", shed="L"),
    "P2": dict(c=(298, 202), r=(52, 30), floor=222, house=(270, 330), door="L", shed="R"),
    "P3": dict(c=(104, 292), r=(52, 30), floor=312, house=(66, 126), door="R", shed="L"),
}


def descent_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > ARENA:
            continue
        cut = False
        for p in PODS.values():
            (cx, cy), (rx, ry) = p["c"], p["r"]
            if abs(lx - cx) <= rx * 0.85 and p["floor"] < ly < p["floor"] + 40:
                cut = True
        if not cut:
            out.add((x, y))
    return out


def descent_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    af = Y(ARENA) + 1

    # the warning at the top of the drop
    prop("SkullShrooms", X(178), floor_at(m, X(178), Y(60)))
    hang("Cocoon", X(222), ceil_at(m, X(222), Y(50)) + 1, 4)
    hang("GlowLantern", X(180), ceil_at(m, X(180), Y(40)) + 1, 6)

    # the pod-houses, each on its ledge, arch to the drop
    for k, p in PODS.items():
        f = Y(p["floor"])
        x0, x1 = p["house"]
        grown_house(X(x0), X(x1), f, 32, 10, doors=(p["door"],), shed=p["shed"])
        hang("GlowLantern", X((x0 + x1) // 2), f - 32, 2)
    f1, f2, f3 = (Y(p["floor"]) + 0 for p in PODS.values())
    prop("MushroomBed", X(96), f1)
    stand("WizBogcap", X(112), f1, flip=True)
    prop("CapCupboard", X(316), f2)
    stand("WizBogcap", X(290), f2)
    stand("WizHollowhood", X(306), f2)
    prop("RootChair", X(80), f3)
    stand("Gaper", X(106), f3, flip=True)

    # shelves down the shaft between the pods
    for y, side in ((176, "R"), (262, "L"), (352, "R"), (392, "L")):
        yy = Y(y)
        x = X(200)                                               # from the shaft's middle out to its wall
        step = -1 if side == "L" else 1
        while (x + step, yy - 2) in m:
            x += step
        bracket(x, yy, side, glow=y in (176, 352))
    stand("Ghast", X(200), Y(250))

    # the arena: three brick seats, three champions, the caps hung over them
    for x, who, flip in ((140, "WizRamskull", False), (200, "WizMaskwraith", False), (260, "WizBonecrown", True)):
        slab(X(x - 9), af - 10, X(x + 9), af - 1, mat="brick")
        stand(who, X(x), af - 10, flip=flip)
    for x in (150, 250):
        hang("HangingCaps", X(x), ceil_at(m, X(x), Y(410)) + 1, 6)
    hang("GlowLantern", X(110), ceil_at(m, X(110), Y(410)) + 1, 8)
    hang("GlowLantern", X(290), ceil_at(m, X(290), Y(410)) + 1, 8)
    sprinkle(m, X(70), X(330), Y(ARENA - 4), 5, gap=14)


ROOM = {
    "name": "THE DESCENT", "w": 400, "h": 480,
    "shapes": [([
        ("tube", [(200, 50), (186, 120), (212, 240), (196, 350)], 34),   # the drop
        ("blob", 200, 410, 152, 44),                                     # the arena
    ] + [("blob",) + p["c"] + p["r"] for p in PODS.values()] + [
        ("tube", [(16, 298), (60, 300)], 14),                            # out of the west pod
        ("tube", [(346, 208), (396, 208)], 14),                          # out of the east pod
    ], 0.08)],
    "sockets": {"T1": ("T", 200, 20), "L1": ("L", PODS["P3"]["floor"], 18),
                "R1": ("R", PODS["P2"]["floor"], 18), "B1": ("B", 200, 42)},
    "edit": descent_edit,
    "furnish": descent_furnish,
}

BACK_HOUSES = [(p["house"][0], p["floor"] - 32, p["house"][1], p["floor"] - 1) for p in PODS.values()]
BACK_PATCHES = [(110, 380, 290, 438)]

SHEET = {
    "seed": 76301,
    "callouts": [
        ("1 A WARNING AT THE TOP", (240, -50), (222, 60)),
        ("2 POD-HOUSES ON THE WALLS", (-150, 60), (100, 124)),
        ("3 SHELVES DOWN BETWEEN THEM", (300, 300), (240, 352)),
        ("4 THE CHAMPIONS BAR THE WAY ON", (-140, 500), (200, 420)),
        ("5 OR LEAVE HALFWAY", (300, 110), (380, 216)),
    ],
    "beats": [
        ("AFTER HOLLOW KNIGHT'S MANTIS VILLAGE: A LONG DROP, A TRIBE ON ITS WALLS, AN ARENA AT THE FOOT", (170, 180, 195)),
        ("DROP: CUT THE CAPS HUNG OVER THE THREE CHAMPIONS", F_MID),
        ("OR GO DOWN POD BY POD - OR OUT OF A POD HALFWAY AND NEVER MEET THEM", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
