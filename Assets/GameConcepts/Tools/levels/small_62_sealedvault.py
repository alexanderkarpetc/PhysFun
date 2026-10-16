"""Fungal room S62 - THE SEALED VAULT.

After Noita's Fungal Caverns: tight passages lined with steel beams you cannot dig, rooms
sealed shut that only a blast will open, giant explosive fungi growing about, and a hidden
altar - an inverted triangle of brickwork - with something kept on it.

Five cells in the rock joined by crawls. Two are walled off with brick where the crawls
meet them: the cult's vault in the north-east, with the altar, and the spiders' larder in
the south-east, which is also the way out. Next to each plug grows what will open it - a
puffball by the vault's, a cluster of sacs by the larder's. Steel beams cross the hub and
line the crawls: a blast will not move them, and nothing digs round them.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fungalkit import *  # noqa: F403,E402

CODE = "S62"

CELLS = {
    "A": dict(c=(66, 112), r=(48, 26), floor=130, xs=(22, 110)),     # the way in
    "B": dict(c=(212, 192), r=(64, 34), floor=220, xs=(152, 272)),   # the hub
    "C": dict(c=(372, 108), r=(54, 30), floor=132, xs=(322, 422)),   # the vault (sealed)
    "D": dict(c=(352, 290), r=(56, 30), floor=312, xs=(300, 404)),   # the larder (sealed)
    "E": dict(c=(110, 292), r=(52, 28), floor=312, xs=(62, 158)),
}
SEAL_C = (304, 104, 312, 136)      # brick plugs where the crawls meet the sealed cells
SEAL_D = (288, 290, 296, 318)


def vault_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if any(c["xs"][0] <= lx <= c["xs"][1] and c["floor"] < ly < c["floor"] + 40 for c in CELLS.values()):
            continue
        out.add((x, y))
    S = lambda pts: [(px_ + ox, py_ + oy) for px_, py_ in pts]
    return out | cave_mask([
        ("tube", S([(100, 124), (136, 150), (170, 196)]), 11),        # A -> B
        ("tube", S([(170, 214), (142, 252), (122, 296)]), 10),        # B -> E
        ("tube", S([(264, 196), (290, 150), (318, 122)]), 10),        # B -> C, to the plug
        ("tube", S([(156, 306), (226, 318), (300, 304)]), 10),        # E -> D, to the plug
        ("tube", S([(382, 86), (386, 44), (382, 4)]), 10),            # up out of the vault
    ], rough=0.06, top=0)


def vault_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    F = {k: Y(c["floor"]) + 1 for k, c in CELLS.items()}
    for c in CELLS.values():
        teeth(m, X(c["c"][0] - c["r"][0] + 10), X(c["c"][0] + c["r"][0] - 10), Y(c["c"][1]), 3)

    # the seals, and what grows by them
    slab(*[X(v) if i % 2 == 0 else Y(v) for i, v in enumerate(SEAL_C)], mat="brick")
    slab(*[X(v) if i % 2 == 0 else Y(v) for i, v in enumerate(SEAL_D)], mat="brick")
    prop("GiantPuffball", X(256), F["B"])
    hang("SporeSacs", X(272), ceil_at(m, X(272), Y(300)) + 1, 2)

    # steel: a beam across the hub, posts in the lower cell, the crawl roofs lined
    slab(X(176), Y(186), X(248), Y(189), mat="steel")
    slab(X(96), Y(286), X(99), Y(F["E"] - oy - 1), mat="steel")
    slab(X(122), Y(146), X(150), Y(147), mat="steel")
    slab(X(200), Y(306), X(240), Y(307), mat="steel")

    # A, the way in: a look down the crawl at the hub
    hang("GlowLantern", X(60), ceil_at(m, X(60), Y(110)) + 1, 6)
    prop("CropBasket", X(40), F["A"])
    sprinkle(m, X(30), X(100), Y(126), 2)

    # B, the hub: the crew under the beam, kegs against the wall
    stand("WizBogcap", X(196), F["B"])
    stand("WizBogcap", X(226), F["B"], flip=True)
    stand("Gaper", X(170), F["B"])
    prop("SporeKeg", X(160), F["B"])
    prop("SporeKeg", X(169), F["B"] - 11)
    hang("GlowLantern", X(212), Y(186) + 5, 4)

    # C, the vault: the altar - an inverted triangle of brick - and its keeper
    cx, fl = 372, CELLS["C"]["floor"]
    for k in range(5):                                              # widest at the top
        slab(X(cx - 16 + k * 3), Y(fl - 22 + k * 4), X(cx + 16 - k * 3), Y(fl - 19 + k * 4), mat="brick")
    slab(X(cx - 2), Y(fl - 2), X(cx + 2), Y(fl), mat="brick")
    prop("FungalIdol", X(cx), Y(fl - 22))
    prop("CapCandles", X(cx - 30), F["C"])
    prop("SporeJars", X(cx + 30), F["C"])
    stand("WizMaskwraith", X(400), F["C"], flip=True)
    hang("GlowLantern", X(344), ceil_at(m, X(344), Y(100)) + 1, 4)

    # D, the larder: cocoons, spiders, the way out
    for x in (330, 362):
        hang("Cocoon", X(x), ceil_at(m, X(x), Y(290)) + 1, 2)
    stand("Minespider", X(318), F["D"])
    stand("Minespider", X(380), F["D"], flip=True)

    # E: spiders between the steel posts
    stand("Minespider", X(80), F["E"])
    stand("Minespider", X(130), F["E"], flip=True)
    prop("SkullShrooms", X(110), F["E"])
    sprinkle(m, X(64), X(156), Y(306), 2)


ROOM = {
    "name": "THE SEALED VAULT", "w": 460, "h": 370,
    "shapes": [([("blob",) + c["c"] + c["r"] for c in CELLS.values()], 0.1)],
    "sockets": {"L1": ("L", CELLS["A"]["floor"], 22), "R1": ("R", CELLS["D"]["floor"], 58),
                "T1": ("T", 382, 8), "B1": ("B", 110, 60)},
    "edit": vault_edit,
    "furnish": vault_furnish,
}

BACK_HOUSES = [(330, 86, 414, 131)]
BACK_PATCHES = [(170, 170, 250, 215), (310, 270, 395, 310)]

SHEET = {
    "seed": 76201,
    "callouts": [
        ("1 IN, LOOKING DOWN THE CRAWL", (-150, 50), (60, 120)),
        ("2 BRICK: A BLAST OPENS IT", (250, -50), (308, 120)),
        ("3 THE PUFFBALL BY THE PLUG", (60, 400), (256, 212)),
        ("4 STEEL: NOTHING DIGS IT", (-60, -50), (212, 188)),
        ("5 THE ALTAR, AN INVERTED TRIANGLE", (380, 160), (372, 118)),
        ("6 THE WAY OUT IS THROUGH THE LARDER", (280, 400), (352, 300)),
    ],
    "beats": [
        ("AFTER NOITA'S FUNGAL CAVERNS: TIGHT CRAWLS, STEEL YOU CANNOT DIG, ROOMS SEALED SHUT", (170, 180, 195)),
        ("BLOW: ROLL THE PUFFBALL INTO THE PLUG, BURST THE SACS BY THE OTHER", F_MID),
        ("THE VAULT KEEPS THE ALTAR AND ITS KEEPER; THE LARDER KEEPS THE WAY OUT", (170, 180, 195)),
    ],
}


def build():
    return fungal_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
