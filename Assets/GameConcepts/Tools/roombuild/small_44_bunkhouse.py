"""S44 THE BUNKHOUSE, assembled.

The house is props, all from `roomprops_structures` through `roombuild.structures`: plank
walls with the open windows left as gaps (the shuttered one is wall), Doors front, back and
in both partitions (E opens them, enemies never do), one-way decks for the upstairs floor,
the attic floor and the porch, a ladder up through the hatch, and a slate roof laid along
both pitches - walkable, so the way in over the roof is a real one.

Not exported: the stove and its flue, the porch roof and post, the woodpile, the furniture
(lamps and interiors are only on the sheet). The ledge west and the cave are terrain.

The back wall (`backwall`, drawn by backwalls.py) is the inside of the house: boards up to
the eave and on into the gable, wainscot under a rail on both storeys, a beam behind each
floor, studs and a king post, and a window in three of the rooms with the cave behind it.
"""
from roombuild import structures as B

ORIGIN = (0, 0)


def hooks(add, mod):
    h = B.hooks(add, mod)
    h.pop("shed_roof", None)        # the porch roof stays sheet-only (its beam is in the back wall)
    return h


def furnish(add, mod, ox, oy):
    B.finish(add)


def backwall(b, mod):
    S = mod
    x0, x1 = S.HX0, S.HX1
    fl, md, ev = S.FLOOR, S.MID, S.EAVE
    cx, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0

    # boards: the storeys, then the gable up under the roof's pitches
    b.rect(x0, ev, x1, fl - 1, "back_planks")
    b.under_roof(x0, x1, lambda x: ev - S.RIDGE * (1 - abs(x - cx) / half) + 6, ev)

    for floor in (fl, md):
        b.wainscot(x0, x1, floor)

    # studs, the king post, and a beam behind each floor
    for sx, top, bottom in ((170, md + 5, fl - 20), (250, md + 5, fl - 20),
                            (158, ev + 5, md - 20), (266, ev + 5, md - 20)):
        b.beam(sx, top, sx + 4, bottom)
    b.beam(int(cx) - 2, ev - S.RIDGE + 8, int(cx) + 2, ev)
    b.beam(x0, ev - 1, x1, ev + 4)
    b.beam(x0, md - 1, x1, md + 4)

    # the porch: its post and the beam of its roof, which the porch lamp hangs from
    b.beam(x0 - 35, fl - 42, x0 - 31, fl - 1)
    b.beam(x0 - 37, fl - 43, x0, fl - 38)

    # windows onto the cave
    b.window(136, 196, 152, 214)         # upstairs west
    b.window(318, 196, 336, 214)         # upstairs east
    b.window(282, 251, 302, 269)         # bunk room
