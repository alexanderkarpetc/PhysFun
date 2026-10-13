"""S43 THE SWITCHBACK, assembled.

Everything built in the cave is props from `roomprops_structures`, laid by
`roombuild.structures`, not terrain:

* each deck is a row of DeckPlanks - static, one-way (Props.OneWayPlatform), let into the
  rock at both ends;
* each bulkhead is a stack of WallPlanks, from the door's lintel up to the deck above (or
  the roof). Terrain would not do: terrain only stays up while it touches rock, and a
  bulkhead between two decks touches none;
* each door is a Door, 1px clear of the lintel and the deck: E opens it, E shuts it, and
  enemies never do;
* each ladder is a Ladder instance from the deck it comes up through down to the floor
  below, with its `_height` set to fit.

The cave, its teeth and the rock the decks are let into are terrain. Furniture on the sheet
(the table, the bunk, the sack) is not exported; crates and kegs are, by the shared hooks.
"""
from roombuild import structures as B

ORIGIN = (0, 0)


def hooks(add, mod):
    return B.hooks(add, mod)


def furnish(add, mod, ox, oy):
    B.finish(add)


def _entry():
    import levels.small_43_switchback as m
    return (110, m.LEVELS[0])


ENTRY_AT = _entry()
