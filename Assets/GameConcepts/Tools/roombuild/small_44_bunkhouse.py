"""S44 THE BUNKHOUSE, assembled.

The house is props, all from `roomprops_structures` through `roombuild.structures`: plank
walls with the open windows left as gaps (the shuttered one is wall), Doors front, back and
in both partitions (E opens them, enemies never do), one-way decks for the upstairs floor,
the attic floor and the porch, a ladder up through the hatch, and a slate roof laid along
both pitches - walkable, so the way in over the roof is a real one.

The furniture the sheet draws is clutter (`roombuild.clutter`, Props.Decor): the kitchen
table with a mug, candle and bottle on it, the stool, the shelf of jars, both bunks, the
sacks upstairs - walked through, knocked flying by a shot.

The floors are solid, wall-thick FloorPlanks (`roombuild.structures`): the only ways up are
the hatch over the ladder from the kitchen side and a second hatch and ladder this module
adds, from the east room up into the attic. `furnish` adds the rest of what
a lived-in house has: pans and herbs on the kitchen wall, pictures and a notice by the
bunks, tools by the hatch, a ham hung up, a chest and books in the attic.

Not exported: the stove and its flue, the porch roof and post, the woodpile. The ledge
west and the cave are terrain.

The back wall (`backwall`, drawn by backwalls.py) is the inside of the house: boards up to
the eave and on into the gable, wainscot under a rail on both storeys, a beam behind each
floor, studs and a king post, and a window in three of the rooms with the cave behind it.
"""
from roombuild import structures as B
from roombuild import clutter as C

ORIGIN = (0, 0)
ATTIC_HATCH = 222      # sheet x of the hatch up into the attic, just east of the partition


def hooks(add, mod):
    h = B.hooks(add, mod)
    h.pop("shed_roof", None)        # the porch roof stays sheet-only (its beam is in the back wall)
    h.update(C.hooks(add))
    ox, oy = ORIGIN
    # a bed is wider than the sheet's bunk: keep it between the partition and the east wall
    lo, hi = ox + mod.INNER_DN + 5, ox + mod.HX1 - mod.WALL

    def bunk(x, floor, tiers=2, w=26):
        half = C.size("Bed")[0] / 2.0
        C.stand(add, "Bed", max(lo + half, min(x + w / 2.0, hi - half)), floor)
    h["bunk"] = bunk

    # the floors are wall-thick now (FloorPlank, 6px) where the sheet drew 3-4px decks:
    # a lamp the sheet hangs just under one hangs from the plank's underside instead
    undersides = {oy + mod.MID + 4: oy + mod.MID + B.FLOOR_T, oy + mod.EAVE + 7: oy + mod.EAVE + 4 + B.FLOOR_T}

    def warm_lamp(x, y, drop=6, *a, **k):
        y = undersides.get(y, y)
        drop = max(4, int(drop))
        add("Lantern", x + 0.5, y + drop + 5, rope=(x, y, y + drop))
    h["warm_lamp"] = warm_lamp
    return h


def furnish(add, mod, ox, oy):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    # the attic floor is solid now, so the attic gets a hatch and a ladder of its own, up
    # from the east room upstairs (the sheet's way in was through the whole floor)
    mod.trapdoor(X(ATTIC_HATCH), X(ATTIC_HATCH) + 17, Y(mod.EAVE) + 4)
    mod.ladder_up(X(ATTIC_HATCH) + 9, Y(mod.EAVE) + 4, Y(mod.MID))
    B.finish(add)
    fl, md, ev = Y(mod.FLOOR), Y(mod.MID) + 1, Y(mod.EAVE) + 4

    # kitchen: what hangs over the stove, a pot and a bucket on the floor
    C.hang(add, "Pan", X(146), Y(250))
    C.hang(add, "Herbs", X(160), Y(248))
    C.hang(add, "Herbs", X(167), Y(249))
    C.stand(add, "Pot", X(132), fl)
    C.stand(add, "Kettle", X(141), fl)
    C.stand(add, "Bucket", X(214), fl)
    # bunk room: a notice over one bed, a picture over the other, a chest between
    C.hang(add, "Notice", X(250), Y(262))
    C.hang(add, "Picture", X(325), Y(256))
    C.stand(add, "Chest", X(296), fl)
    # upstairs west: a shelf of books and a candle, a saw on the wall
    C.shelf(add, X(160), Y(214), ["BookRow", "Candlestick", "BookRow"], seed=4)
    C.hang(add, "Saw", X(197), Y(200))
    C.stand(add, "Basket", X(127), md)
    # upstairs east: tools by the attic ladder, a ham hung up, a jug by the keg
    C.hang(add, "Pickaxe", X(248), Y(202))
    C.hang(add, "Shovel", X(259), Y(200))
    C.hang(add, "Ham", X(294), Y(192))
    C.stand(add, "Jug", X(340), md)
    # the attic: a chest, books, a bucket under the ridge
    C.stand(add, "Chest", X(248), ev)
    C.stand(add, "BookStack", X(198), ev)
    C.stand(add, "Bedroll", X(160), ev)


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
