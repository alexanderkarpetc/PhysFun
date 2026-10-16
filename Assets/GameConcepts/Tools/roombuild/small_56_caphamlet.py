"""S56 THE CAP HAMLET, assembled.

The houses are props laid by `roombuild.structures` from the fungal set (the sheet's
HOUSE_KIT): StemWall walls with the open windows left as gaps (the shuttered one is wall),
a CapDoor in each doorway, StemFloor storeys with a CapDeck hatch over every ladder. The
mushrooms they are built against are terrain (fungalkit's giant_shroom: stem and cap, both
burning) - each cap is its house's roof and stands on its stem alone.

The back wall inside each house is stem slabs from the cap's underside to the floor
(fungalkit.house_back); out in the cave it is the fungal room's own (back_mycelium, with
crusts of caps behind the yard).
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
    for name, (x0, x1) in mod.HOUSES.items():
        sx = mod.SHROOMS[name][0]
        lo, hi = min(x0, sx), max(x1, sx)
        F.house_back(b, lo, mod.under(name), hi, mod.FLOOR - 1)
