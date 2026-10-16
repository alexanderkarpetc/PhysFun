"""What built rooms share when they are assembled: the housekit draw calls a sheet makes,
turned into the props from `roomprops_structures`.

    from roombuild import structures as B

    def hooks(add, mod):
        return B.hooks(add, mod)

    def furnish(add, mod, ox, oy):
        B.finish(add)

* deck(...)        -> a floor of FloorPlanks (static, solid both ways, wall-thick), laid in
                      finish() round the hatches in it, flush with both ends of every run;
* plank_wall(...)  -> a stack of WallPlanks, held back until finish() so that the windows a
                      sheet cuts into a wall afterwards are left open in it;
* window(...)      -> a gap in the wall it is in (a shuttered one stays wall);
* flap_door(...)   -> a Door (E opens it), 1px clear of the lintel and the floor;
* ladder_up(...)   -> a Ladder from the deck it comes up through to the floor below;
* pitched_roof(...)-> RoofPlanks laid up both pitches at their angle, walkable;
* shed_roof(...)   -> the same along a lean-to's single pitch;
* trapdoor(...)    -> a hatch: a gap in the floor with a DeckPlank lid over it, thin and
                      one-way, so a ladder comes up through it and you stand on it at the
                      top. A ladder that comes up through a floor with no trapdoor over it
                      gets one of its own (HATCH wide). The hatch is the only way through
                      a floor: it is wall-thick everywhere else.

Walls, decks and roofs are props rather than terrain because terrain only stays up while it
touches rock, and a house stands on the cave floor touching nothing but itself.
"""
import math

DECK = 20          # DeckPlank / FloorPlank length, px
FLOOR_T = 6        # FloorPlank thickness
HATCH = 16         # the gap a ladder gets in a floor with no trapdoor over it
WALL = 12          # WallPlank height, px
ROOF = 20          # RoofPlank length, px
ROOF_T = 5         # and thickness

_walls = []        # (x0, y0, x1, y1) in sheet coords, waiting for finish()
_gaps = []         # window openings, the same
_decks = []        # (x0, x1, y) floors, laid in finish() round the hatches
_hatches = []      # (x0, x1, y) gaps in them
_ladders = []      # (x, top y) ladders, which need a hatch over them

# What a house is built of: the timber set (roomprops_structures), or another of the same
# sizes - `use_kit(FUNGAL)` for the cult's houses of stem and cap (roomprops_fungal).
TIMBER = dict(wall="WallPlank", floor="FloorPlank", deck="DeckPlank", door="Door", roof="RoofPlank")
FUNGAL = dict(wall="StemWall", floor="StemFloor", deck="CapDeck", door="CapDoor", roof="CapRoof")
KIT = dict(TIMBER)


def use_kit(kit):
    """Build the next room's houses of `kit` (a dict like TIMBER)."""
    KIT.clear()
    KIT.update(kit)


def hooks(add, mod):
    import roomprops_structures as S
    use_kit(getattr(mod, "HOUSE_KIT", TIMBER))
    ids = S.ladder_ids()
    _walls.clear()
    _gaps.clear()
    _decks.clear()
    _hatches.clear()
    _ladders.clear()

    def deck(x0, x1, y, thick=4, joists=True):
        _decks.append((x0, x1, y))

    def plank_wall(x0, y0, x1, y1):
        _walls.append((x0, y0, x1, y1))

    def window(x0, y0, x1, y1, shutter=False):
        if not shutter:
            _gaps.append((x0, y0, x1, y1))

    def flap_door(x, top, h=30, w=4, swung=0):
        add(KIT["door"], x + (w + 1) / 2.0, top + 14)

    def ladder_up(x, y0, y1):
        _ladders.append((x, y0))
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
                add(KIT["roof"], xa + ux * t, ya + uy * t + ROOF_T / 2.0, angle=ang)

    def shed_roof(x0, x1, y_hi, y_lo, thick=4):
        _plank_line(add, x0 - 3, y_hi, x1 + 3, y_lo)

    def trapdoor(x0, x1, y, open_=False):
        # a hatch left open would drop you back down the ladder you just climbed
        _hatches.append((x0, x1, y))
        add(KIT["deck"], (x0 + x1 + 1) / 2.0, y + 2)

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
        add(KIT["roof"], xa + ux * t, ya + uy * t + ROOF_T / 2.0, angle=ang)


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


def _lay(add, a, b, y):
    """FloorPlanks over a..b (inclusive), flush with both ends: the last one overlaps the
    one before it rather than sticking out past a wall or into a hatch."""
    n = int(math.ceil((b - a + 1) / float(DECK)))
    for k in range(n):
        add(KIT["floor"], min(a + DECK * (k + 0.5), b + 1 - DECK / 2.0), y + FLOOR_T / 2.0)


def _lay_floors(add):
    """Every floor, solid, with a gap at each hatch in it; a ladder coming up through a
    floor where nobody put a trapdoor gets a hatch of its own."""
    for x0, x1, y in _decks:
        holes = [(hx0, hx1) for hx0, hx1, hy in _hatches if abs(hy - y) <= 2 and hx1 >= x0 - 2 and hx0 <= x1 + 2]
        for lx, ly in _ladders:
            if abs(ly - y) > 2 or not x0 - 2 <= lx <= x1 + 2:
                continue
            if any(hx0 - 2 <= lx <= hx1 + 2 for hx0, hx1 in holes):
                continue
            hx0, hx1 = lx - HATCH // 2, lx + HATCH // 2 - 1
            holes.append((hx0, hx1))
            add(KIT["deck"], (hx0 + hx1 + 1) / 2.0, y + 2)
        holes.sort()
        a = x0
        for hx0, hx1 in holes:
            if hx0 - 1 >= a:
                _lay(add, a, hx0 - 1, y)
            a = hx1 + 1
        if x1 >= a:
            _lay(add, a, x1, y)


def finish(add):
    """Lay the floors round their hatches, and the walls, now that every window cut into
    them is known. Each run is stacked
    from its foot; the top plank is set flush with the run's top, overlapping the one
    under it, so a plank never sticks out into a window or a doorway. A run shorter than
    one plank keeps its foot and pokes up into the gap above it - never down into a door."""
    _lay_floors(add)
    for x0, y0, x1, y1 in _walls:
        cx = (x0 + x1 + 1) / 2.0
        for a, b in _open_runs(x0, y0, x1, y1):
            h = b - a + 1
            n = int(math.ceil(h / float(WALL)))
            for k in range(n):
                cy = b + 1 - WALL * (k + 0.5)
                if k == n - 1 and h >= WALL:
                    cy = max(cy, a + WALL / 2.0)
                add(KIT["wall"], cx, cy)
