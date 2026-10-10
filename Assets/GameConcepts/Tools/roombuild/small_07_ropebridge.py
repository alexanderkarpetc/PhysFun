"""S07 THE ROPE BRIDGE, assembled.

The bridge is a BridgeBuilder2D that builds itself when the room wakes: 18 timber planks
hinged end to end across the chasm, with nothing pinning its ends - it hangs from four
ropes alone, each under a Tether2D so a round parts it: one off each lip's tie-off post to
the end plank, and the two hangers off the ring bolt in the vault to the planks at 0.3 and
0.7 along. Cut an end rope and that end swings down into the chasm, the hangers with it;
cut everything and the bridge, and whoever is on it, goes onto the stakes. The planks burn.

The posts, the ring bolt and the stakes on the chasm floor are terrain.
"""

ORIGIN = (0, 0)
_rec = {"posts": [], "bolt": [], "stakes": []}
PLANKS = 18


def hooks(add, mod):
    ox, oy = ORIGIN
    for k in _rec:
        _rec[k].clear()

    def rope_bridge(bx, by):
        x0, y0, x1, y1 = mod.BRIDGE
        # the deck, from end plank to end plank, along the straight line between the lips
        add.bridge(bx + x0, by + y0 + 1, bx + x1, by + y1 + 1, PLANKS,
                   [("west", 0.0), ("east", 1.0), ("hang_w", 0.3), ("hang_e", 0.7)])
        # the end ropes, post top to the end plank, as the sheet draws them
        add.rope("west", bx + x0 - 5, by + mod.WEST_FLOOR - 8, bx + x0, by + y0 + 1)
        add.rope("east", bx + x1 + 5, by + mod.EAST_FLOOR - 8, bx + x1, by + y1 + 1)

    def ring_bolt(x, y):
        _rec["bolt"].append((x - ox, y - oy))
        for key, t in (("hang_w", 0.3), ("hang_e", 0.7)):
            px_, py_ = mod.catenary(t)
            add.rope(key, x, y + 6, ox + px_ + 2, oy + py_)

    def post(x, floor, side):
        _rec["posts"].append((x - ox, floor - oy))

    def stake_bed(x0, x1, y):
        # the sheet's own draws from the shared random stream, kept in the same order
        for x in range(int(x0), int(x1), 5):
            h = 8 + int(mod.rnd() * 8)
            lean = (mod.rnd() - 0.5) * 6
            _rec["stakes"].append((x - ox, y - oy, h, lean))

    def noop(*a, **k):
        pass

    def deck(t):
        # the bridge is built straight, lip to lip, and only sags as far as it can - so the
        # gaper on the planks and the hangers go to the deck line, not the sheet's curve
        x0, y0, x1, y1 = mod.BRIDGE
        return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t

    return {"rope_bridge": rope_bridge, "ring_bolt": ring_bolt, "post": post,
            "stake_bed": stake_bed, "hanging_wreck": noop, "catenary": deck}


def furnish(add, mod, ox, oy):
    pass


ENTRY_AT = None


def _line(g, x0, y0, x1, y1, mat):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
        g.rect(x, y, x, y, mat)


def extras(g, mod):
    for x, floor in _rec["posts"]:                           # tie-off posts, driven into the lip
        g.rect(x - 1, floor - 12, x + 2, floor + 4, "wood")
    for x, y in _rec["bolt"]:                                # the ring bolt in the vault
        g.rect(x - 2, y - 2, x + 2, y + 5, "steel")
    for x, y, h, lean in _rec["stakes"]:                     # sharpened stakes on the chasm floor
        _line(g, x, y - 1, x + lean, y - h, "wood")
        _line(g, x + 1, y - 1, x + 1 + lean, y - h, "wood")


def _entry():
    import levels.small_07_ropebridge as m
    return (60, m.west_floor(60))


ENTRY_AT = _entry()
