"""S59 THE BURROWS, assembled.

The homes are pockets dug in the rock (the sheet's air); their fronts are props laid by
`roombuild.structures` from the fungal set - StemWall slabs with the windows left open, a
CapDoor in each doorway. The cap arch over each door is only on the sheet. The ladder
down the cellar shaft is a Props/Ladder. The back wall inside each home is stem slabs
(BACK_HOUSES), the rest the fungal room's own.
"""
from roombuild import structures as B

ORIGIN = (0, 0)


def hooks(add, mod):
    return B.hooks(add, mod)


def furnish(add, mod, ox, oy):
    B.finish(add)
