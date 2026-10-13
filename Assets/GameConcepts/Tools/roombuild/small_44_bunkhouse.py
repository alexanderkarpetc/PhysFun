"""S44 THE BUNKHOUSE, assembled.

The house is props, all from `roomprops_structures` through `roombuild.structures`: plank
walls with the open windows left as gaps (the shuttered one is wall), Doors front, back and
in both partitions (E opens them, enemies never do), one-way decks for the upstairs floor,
the attic floor and the porch, a ladder up through the hatch, and a slate roof laid along
both pitches - walkable, so the way in over the roof is a real one.

Not exported: the stove and its flue, the porch roof and post, the woodpile, the furniture
(lamps and interiors are only on the sheet). The ledge west and the cave are terrain.
"""
from roombuild import structures as B

ORIGIN = (0, 0)


def hooks(add, mod):
    return B.hooks(add, mod)


def furnish(add, mod, ox, oy):
    B.finish(add)
