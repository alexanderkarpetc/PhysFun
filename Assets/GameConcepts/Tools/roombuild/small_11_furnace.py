"""S11 THE FURNACE, assembled.

The furnace is firebrick terrain - walls, dome, the flue up the middle with its open
channel, iron ties - round a fire box that is air, with a coal bed, the muffle standing in
it, and a FireSource in its lower half putting out flames for as long as the room exists.
The box is closed but for the two stoke holes low in its sides, so the fire only reaches
the room through those: what sits by a hole, or is knocked into one, goes up.

Everything over it is timber terrain, as the sheet draws it: the charging deck round the
flue head (with the flue coming up through it), its two outer posts and their braces, the
gangways to the wall ledges and their props, the headframe with its sheave, the stulls
under the ledges. The two inner posts and the ladder stand in front of the furnace on the
sheet - where every pixel collides they would stand inside its walls and fire box - so
they are left out, and the braces stop at the brickwork. The coal sacks are props, the
skip of coal hangs off the sheave on a rope, the stock pile is end-on logs.
"""
import math

ORIGIN = (0, 0)
ENTRY = "L1"
_rec = {"furnace": None, "deck": [], "beams": [], "braces": [], "ramps": [], "heaps": [],
        "stulls": [], "sheave": None}


def hooks(add, mod):
    ox, oy = ORIGIN
    for k, v in _rec.items():
        if isinstance(v, list):
            v.clear()
        else:
            _rec[k] = None

    def furnace(cx, floor):
        _rec["furnace"] = (cx - ox, floor - oy)
        top = floor - 58
        by1 = floor - 7
        # the fire bed: flames out of the lower box, over the coal
        add.component("FireSource", "Scripts/Phys/Fire/FireSource.cs", cx + 0.5, by1 - 9,
                      "  _size: {x: 3, y: 0.5}\n  _rate: 40\n  _heat: 70\n  _smokeRate: 3\n")
        return top - 112

    def deck(x0, x1, y, posts=()):
        _rec["deck"].append((x0 - ox, x1 - ox, y - oy))

    def beam(x, y0, y1, w=3, c=None, lit=None):
        _rec["beams"].append((x - ox, y0 - oy, y1 - oy, w))

    def brace(x0, y0, x1, y1):
        _rec["braces"].append((x0 - ox, y0 - oy, x1 - ox, y1 - oy))

    def ramp(x0, y0, x1, y1):
        _rec["ramps"].append((x0 - ox, y0 - oy, x1 - ox, y1 - oy))

    def coal_heap(x, floor, w, h):
        _rec["heaps"].append((x - ox, floor - oy, w, h))

    def stull(x, y0, y1):
        _rec["stulls"].append((x - ox, y0 - oy, y1 - oy))

    def ring(cx, cy, r, c=None):
        if r >= 4.5:                              # the sheave: the skip of coal hangs off it
            _rec["sheave"] = (cx - ox, cy - oy)
            x = cx + 5
            add("HoistBucket", x + 0.5, cy + 64, rope=(x, cy + 6, cy + 60))
        else:                                     # the stock pile: logs end-on
            add("LogEnd", cx + 0.5, cy + 0.5, scale=(2 * r + 1) / 12.0)

    def noop(*a, **k):
        pass

    return {"furnace": furnace, "deck": deck, "beam": beam, "brace": brace, "ramp": ramp,
            "coal_heap": coal_heap, "stull": stull, "ring": ring, "ladder": noop,
            "smoke": noop, "embers": noop, "fire_patch": noop}


def _line(g, x0, y0, x1, y1, mat, keep=None):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
        if keep is None or keep(x, y):
            g.set(x, y, mat)


def extras(g, mod):
    cx, F = _rec["furnace"]
    x0, x1, top = cx - 46, cx + 46, F - 58
    bx0, bx1, by0, by1 = x0 + 8, x1 - 8, top - 4, F - 7
    fy_top = top - 112

    def in_furnace(x, y):
        return x0 - 2 <= x <= x1 + 2 and y >= top - 17

    # the furnace: walls, dome, then the box and the stoke holes cut out of them
    g.rect(x0, top, x1, F - 1, "firebrick")
    for i in range(-46, 47):
        dy = int(16 * math.sqrt(max(0.0, 1 - (i / 46.0) ** 2)))
        g.rect(cx + i, top - dy, cx + i, top, "firebrick")
    g.rect(bx0, by0, bx1, by1, None)
    for hx in (x0, x1 - 7):
        g.rect(hx, F - 26, hx + 7, F - 8, None)
    g.rect(bx0, by1 - 4, bx1, by1, "coal")                       # the coal bed
    g.rect(cx - 16, by1 - 26, cx + 16, by1 - 5, "brick")        # the muffle, standing in it
    for xx in (x0 - 2, x1 + 1):                                  # iron ties up the corners,
        g.rect(xx, top - 2, xx + 1, F - 27, "steel")             # stopping over the stoke holes
        g.rect(xx, F - 7, xx + 1, F - 1, "steel")
    for yy in (top + 6, F - 12):                                 # and across the face, on brick
        for x in range(x0 - 2, x1 + 3):
            for y in (yy, yy + 1):
                if g.m.get((x, y)) in ("firebrick", "steel"):
                    g.set(x, y, "steel")
    # the flue, its channel open at the top, its bands
    g.rect(cx - 9, fy_top, cx + 9, top - 14, "firebrick")
    g.rect(cx - 3, fy_top, cx + 3, top - 14, None)
    for yy in range(fy_top + 10, top - 14, 24):
        for x in list(range(cx - 11, cx - 3)) + list(range(cx + 4, cx + 12)):
            g.rect(x, yy, x, yy + 1, "steel")

    # timber
    for dx0, dx1, y in _rec["deck"]:                             # the deck, the flue through it
        for x in range(int(dx0), int(dx1) + 1):
            if abs(x - cx) > 9:
                g.rect(x, y, x, y + 3, "wood")
    for x, y0, y1, w in _rec["beams"]:
        if x0 - 2 <= x <= x1 + 2 and y1 >= top - 17:
            continue                                             # the inner posts: in the furnace
        g.rect(x, y0, x + w - 1, y1, "wood")
    for ax, ay, bx, by in _rec["braces"]:
        keep = lambda x, y: not in_furnace(x, y)
        _line(g, ax, ay, bx, by, "wood", keep)
        _line(g, ax + 1, ay, bx + 1, by, "wood", keep)
    for ax, ay, bx, by in _rec["ramps"]:
        for t in range(3):
            _line(g, ax, ay + t, bx, by + t, "wood")
    for x, y0, y1 in _rec["stulls"]:
        g.rect(x, y0, x + 3, y1, "wood")
        g.rect(x - 4, y0, x + 7, y0 + 2, "wood")
    # the headframe: two legs off the deck to a crown pinned under the roof, the sheave
    if _rec["sheave"]:
        sx, sy = _rec["sheave"]
        crown = sy - 8
        dy = _rec["deck"][0][2]
        for lx in (cx - 44, cx + 42):
            for k in range(3):
                _line(g, lx + k, dy - 1, cx + (lx - cx) * 0.25 + k, crown + 2, "wood")
        g.rect(cx - 30, crown, cx + 30, crown + 3, "wood")
        for y in range(sy - 5, sy + 6):
            for x in range(sx - 5, sx + 6):
                if (x - sx) ** 2 + (y - sy) ** 2 <= 25:
                    g.set(x, y, "steel")
    # the coal heap by the west stoke hole (the one on the floor; the skip's is the prop's)
    for x, floor, w, h in _rec["heaps"]:
        if abs(floor - F) > 2:
            continue
        for i in range(w):
            t = abs(i - w / 2.0) / (w / 2.0)
            g.rect(x + i, floor - int(h * (1 - t * t)), x + i, floor - 1, "coal")
