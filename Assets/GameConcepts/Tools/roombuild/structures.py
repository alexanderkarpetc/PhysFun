"""What built rooms share when they are assembled: the housekit draw calls a sheet makes,
turned into the props from `roomprops_structures`.

    from roombuild import structures as B

    def hooks(add, mod):
        return B.hooks(add, mod)

    def furnish(add, mod, ox, oy):
        B.finish(add)

* deck(...)        -> a row of DeckPlanks (static, one-way), centred so both ends run into
                      whatever the deck is let into;
* plank_wall(...)  -> a stack of WallPlanks, held back until finish() so that the windows a
                      sheet cuts into a wall afterwards are left open in it;
* window(...)      -> a gap in the wall it is in (a shuttered one stays wall);
* flap_door(...)   -> a Door (E opens it), 1px clear of the lintel and the floor;
* ladder_up(...)   -> a Ladder from the deck it comes up through to the floor below;
* pitched_roof(...)-> RoofPlanks laid up both pitches at their angle, walkable;
* shed_roof(...)   -> the same along a lean-to's single pitch;
* trapdoor(...)    -> a DeckPlank lid over the hatch: one-way like the decks, so a
                      ladder comes up through it and you stand on it at the top.

Walls, decks and roofs are props rather than terrain because terrain only stays up while it
touches rock, and a house stands on the cave floor touching nothing but itself.
"""
import math

DECK = 20          # DeckPlank length, px
WALL = 12          # WallPlank height, px
ROOF = 20          # RoofPlank length, px
ROOF_T = 5         # and thickness

_walls = []        # (x0, y0, x1, y1) in sheet coords, waiting for finish()
_gaps = []         # window openings, the same


def hooks(add, mod):
    import roomprops_structures as S
    ids = S.ladder_ids()
    _walls.clear()
    _gaps.clear()

    def deck(x0, x1, y, thick=4, joists=True):
        n = int(math.ceil((x1 - x0 + 1) / float(DECK)))
        start = (x0 + x1 + 1) / 2.0 - n * DECK / 2.0
        for k in range(n):
            add("DeckPlank", start + DECK * (k + 0.5), y + 2)

    def plank_wall(x0, y0, x1, y1):
        _walls.append((x0, y0, x1, y1))

    def window(x0, y0, x1, y1, shutter=False):
        if not shutter:
            _gaps.append((x0, y0, x1, y1))

    def flap_door(x, top, h=30, w=4, swung=0):
        add("Door", x + (w + 1) / 2.0, top + 14)

    def ladder_up(x, y0, y1):
        h = (y1 - y0) / 20.0
        add.place("Props/Ladder", x + 0.5, y0, mods=[
            (ids["lc"], "_height", "%.4f" % h), (ids["sr"], "m_Size.y", "%.4f" % h)])

    def pitched_roof(x0, x1, eave, ridge_h, c=None, lit=None, thick=6):
        cx = (x0 + x1) / 2.0
        for xa, xb in ((x0 - 4, cx), (x1 + 4, cx)):
            ya = eave - ridge_h * (1 - abs(xa - cx) / ((x1 - x0) / 2.0))
            yb = eave - ridge_h
            ln = math.hypot(xb - xa, yb - ya)
            n = int(math.ceil(ln / ROOF))
            ang = math.degrees(math.atan2(ya - yb, xb - xa))          # y is down on the sheet
            ux, uy = (xb - xa) / ln, (yb - ya) / ln
            for k in range(n):
                t = min(ln - ROOF / 2.0, ROOF * (k + 0.5))
                # the plank's top on the roof line: its centre half a thickness under it
                add("RoofPlank", xa + ux * t, ya + uy * t + ROOF_T / 2.0, angle=ang)

    def shed_roof(x0, x1, y_hi, y_lo, thick=4):
        _plank_line(add, x0 - 3, y_hi, x1 + 3, y_lo)

    def trapdoor(x0, x1, y, open_=False):
        # a hatch left open would drop you back down the ladder you just climbed
        add("DeckPlank", (x0 + x1 + 1) / 2.0, y + 2)

    return {"deck": deck, "plank_wall": plank_wall, "window": window, "flap_door": flap_door,
            "ladder_up": ladder_up, "pitched_roof": pitched_roof, "shed_roof": shed_roof, "trapdoor": trapdoor}


def _plank_line(add, xa, ya, xb, yb):
    """RoofPlanks from (xa, ya) to (xb, yb), sheet coords, their tops on the line."""
    ln = math.hypot(xb - xa, yb - ya)
    n = int(math.ceil(ln / ROOF))
    ang = math.degrees(math.atan2(ya - yb, xb - xa))
    ux, uy = (xb - xa) / ln, (yb - ya) / ln
    for k in range(n):
        t = min(ln - ROOF / 2.0, ROOF * (k + 0.5))
        add("RoofPlank", xa + ux * t, ya + uy * t + ROOF_T / 2.0, angle=ang)


def _open_runs(x0, y0, x1, y1):
    """The wall's height, top to bottom, minus the window gaps cut across it."""
    runs = [(y0, y1)]
    for gx0, gy0, gx1, gy1 in _gaps:
        if gx1 < x0 or gx0 > x1:
            continue
        nxt = []
        for a, b in runs:
            if gy1 < a or gy0 > b:
                nxt.append((a, b))
                continue
            if gy0 - 1 >= a:
                nxt.append((a, gy0 - 1))
            if gy1 + 1 <= b:
                nxt.append((gy1 + 1, b))
        runs = nxt
    return runs


def finish(add):
    """Lay the walls, now that every window cut into them is known. Each run is stacked
    from its foot; the top plank is set flush with the run's top, overlapping the one
    under it, so a plank never sticks out into a window or a doorway. A run shorter than
    one plank keeps its foot and pokes up into the gap above it - never down into a door."""
    for x0, y0, x1, y1 in _walls:
        cx = (x0 + x1 + 1) / 2.0
        for a, b in _open_runs(x0, y0, x1, y1):
            h = b - a + 1
            n = int(math.ceil(h / float(WALL)))
            for k in range(n):
                cy = b + 1 - WALL * (k + 0.5)
                if k == n - 1 and h >= WALL:
                    cy = max(cy, a + WALL / 2.0)
                add("WallPlank", cx, cy)
