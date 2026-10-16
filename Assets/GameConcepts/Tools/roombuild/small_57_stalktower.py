"""S57 THE STALK TOWER, assembled.

Like S56: the tower is props laid by `roombuild.structures` from the fungal set (StemWall
walls, CapDoor doors, StemFloor storeys either side of the stem with a CapDeck hatch over
each ladder); the mushroom it is built round is terrain, its cap the tower's roof standing
on its stem alone. The back wall inside is stem slabs from the cap down.
"""
from roombuild import structures as B
import fungalkit as F

ORIGIN = (0, 0)


def hooks(add, mod):
    return B.hooks(add, mod)


def furnish(add, mod, ox, oy):
    B.finish(add)


def backwall(b, mod):
    F.backwall(b, mod)
    F.house_back(b, mod.X0, mod.under(), mod.X1, mod.FLOOR - 1)
