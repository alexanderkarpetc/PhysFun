"""S45 THE KEEP, assembled.

The tower is terrain, not props: its masonry is `brick`, and unlike a timber house it can
be, because it stands on rock - the west wall and the battered foot on the cave floor, the
east wall built into the cave wall - and every floor slab is bonded into both walls. So the
support pass holds it up, and takes it down: blow the foot out and what it carried comes
with it. The slits and the doorway are left as gaps in the walls.

Props on top, from `roombuild.structures`: the IronDoor in the doorway (E opens it, enemies
never do), a ladder up through each hatch with a one-way DeckPlank lid over it - the floors
are stone, the hatch is the one plank in each - and the bridge to the battlement, a
BridgeBuilder2D of planks hung from two ropes: one off a timber post on the west ledge, one
off the west merlon. Cut either and that end drops.

Not exported: the brazier and the furniture (lamps and the interior are only on the sheet).
"""
from roombuild import structures as B

ORIGIN = (0, 0)
_rec = {"brick": [], "gap": [], "post": []}


def hooks(add, mod):
    ox, oy = ORIGIN
    for k in _rec:
        _rec[k].clear()
    hk = B.hooks(add, mod)

    def L(x, y):
        return x - ox, y - oy

    def masonry(x0, y0, x1, y1, course=5):
        _rec["brick"].append(L(x0, y0) + L(x1, y1))

    def stone_slab(x0, x1, y, thick=5):
        _rec["brick"].append(L(x0, y) + L(x1, y + thick - 1))

    def arrow_slit(x, y, w, h=9):
        _rec["gap"].append(L(x, y) + L(x + w, y + h))

    def iron_door(x, y, w=3, h=20, open_=False):
        _rec["gap"].append(L(x - 2, y - 1) + L(x + w + 2, y + h))
        add("IronDoor", x + w / 2.0 + 0.5, y + h / 2.0)

    def plank_bridge(x0, y0, x1, y1, sag):
        n = max(4, int(round(abs(x1 - x0) / 7.0)))
        add.bridge(x0, y0 + 1, x1, y1 + 1, n, [("ledge", 0.0), ("merlon", 1.0)])
        px_, py_ = x0 - 6, y0 + 1                                 # a post on the ledge's lip
        _rec["post"].append(L(px_, py_))
        add.rope("ledge", px_, py_ - 14, x0, y0 + 1)
        add.rope("merlon", x1 + 4, y1 - 10, x1, y1 + 1)

    hk.update({"masonry": masonry, "stone_slab": stone_slab, "arrow_slit": arrow_slit,
              "iron_door": iron_door, "plank_bridge": plank_bridge})
    return hk


def furnish(add, mod, ox, oy):
    B.finish(add)


def extras(g, mod):
    for x0, y0, x1, y1 in _rec["brick"]:
        g.rect(x0, y0, x1, y1, "brick")
    for x0, y0, x1, y1 in _rec["gap"]:
        g.rect(x0, y0, x1, y1, None)
    for x, y in _rec["post"]:
        g.rect(x - 1, y - 15, x + 2, y + 2, "wood")
