"""Putting clutter (Props.Decor, roomprops_decor) and furniture into a room by where it
stands or hangs, rather than by its centre: `stand` on a floor, `hang` from a top edge.
Sizes come from the prop prefabs themselves, so a redrawn prop still lands right.

Sheet coords throughout, as `add` takes them: x right, y down, a floor is the first row of
ground under the thing (what the sheets' `floor` arguments are).

The sheet helpers it replaces (housekit's table, stool, shelf, bunk, sack) are in
`hooks(add)`: a room's roombuild module merges them into its own hooks to furnish the room
as the sheet drew it.
"""
import os
import random
import re

ASSETS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PPU = 20
_sizes = {}

SHELF_GOODS = ["Jar", "Bottle", "BottleBrown", "Jug", "Mug", "Jar", "Bottle"]


def size(prefab):
    """A prop's sprite size in sheet pixels."""
    if prefab not in _sizes:
        t = open(os.path.join(ASSETS, "Resources", "Prefabs", "Props", prefab + ".prefab"), encoding="utf-8").read()
        m = re.search(r"m_Size: \{x: ([\d.]+), y: ([\d.]+)\}", t)
        _sizes[prefab] = (round(float(m.group(1)) * PPU), round(float(m.group(2)) * PPU))
    return _sizes[prefab]


def stand(add, prefab, cx, floor):
    """Stood on a floor, centred on cx."""
    w, h = size(prefab)
    add(prefab, cx, floor - h / 2.0)


def hang(add, prefab, cx, top):
    """Hung on the back wall with its top edge at `top`."""
    w, h = size(prefab)
    add(prefab, cx, top + h / 2.0)


def shelf(add, x0, top, goods, seed=0):
    """A wall shelf whose plank top is at `top`, from x0, with `goods` stood along it."""
    w, _ = size("Shelf")
    hang(add, "Shelf", x0 + w / 2.0, top)
    rnd = random.Random(seed)
    x = x0 + 3
    for g in goods:
        gw, _ = size(g)
        if x + gw > x0 + w - 2:
            break
        stand(add, g, x + gw / 2.0, top)
        x += gw + rnd.randint(0, 2)


def table(add, x0, floor, things=()):
    """A table from x0 with `things` stood on its top."""
    w, h = size("Table")
    stand(add, "Table", x0 + w / 2.0, floor)
    top = floor - h + 1                                       # the plank top is the sprite's 2nd row
    x = x0 + 2
    for t in things:
        tw, _ = size(t)
        stand(add, t, x + tw / 2.0, top)
        x += tw + 2


def hooks(add):
    """The sheets' furniture as props: tables, stools, shelves, bunks and sacks."""
    n = [0]

    def table_(x, floor, w=18):
        table(add, x + (w - size("Table")[0]) / 2.0, floor, ("Mug", "Candlestick", "BottleBrown"))

    def stool_(x, floor):
        stand(add, "Chair", x + 3, floor)

    def shelf_(x, y, w=20, n_=4):
        n[0] += 1
        shelf(add, x + (w - size("Shelf")[0]) / 2.0, y, SHELF_GOODS[n[0] % 3:][:n_ + 1], seed=n[0])

    def bunk_(x, floor, tiers=2, w=26):
        stand(add, "Bed", x + w / 2.0, floor)

    def sack_(x, floor, w=10):
        stand(add, "GrainSack", x + w / 2.0, floor)

    return {"table": table_, "stool": stool_, "shelf": shelf_, "bunk": bunk_, "sack": sack_}
