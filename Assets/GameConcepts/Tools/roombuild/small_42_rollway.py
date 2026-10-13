"""S42 THE ROLLWAY, assembled.

The boulder is terrain - `boulder` (templerock) - the way S17's is: lifted 2px clear of the
track, so the only thing it touches is a timber cradle under its downhill side, which stands
on the track. The support pass holds the boulder up through the cradle; shoot, cut or burn
the cradle out and the boulder comes loose as one rolling body and takes the track the way
the sheet says - east along the top, down the drop, back west along the bottom into the
kegs in the low pocket.

The ladder up the west shaft is a Ladder from `roombuild.structures`.
"""
from roombuild import structures as B

ORIGIN = (0, 0)
LIFT = 2
_rec = {"boulder": []}


def hooks(add, mod):
    ox, oy = ORIGIN
    _rec["boulder"].clear()
    hk = B.hooks(add, mod)

    def boulder(cx, cy, r):
        _rec["boulder"].append((cx - ox, cy - oy, r))

    def chock(x, floor):
        pass                                       # the cradle in extras() is the chock

    hk.update({"boulder": boulder, "chock": chock})
    return hk


def furnish(add, mod, ox, oy):
    B.finish(add)


def extras(g, mod):
    for cx, cy, r in _rec["boulder"]:
        cy -= LIFT
        bottom = {}
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    g.set(x, y, "boulder")
                    bottom[x] = max(bottom.get(x, -1), y)
        # the cradle: timber from the boulder's underside down to the track, under its
        # downhill (east) half - the only thing it rests on
        for x in range(cx - 4, cx + r - 2):
            if x in bottom:
                g.rect(x, bottom[x] + 1, x, g.floor(x, bottom[x] + 1) - 1, "wood")
