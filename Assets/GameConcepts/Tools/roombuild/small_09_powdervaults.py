"""S09 THE POWDER VAULTS, assembled.

Four barrel vaults stepped down the drift, their masonry templebrick terrain - six px of
it round every bay, as the sheet draws it - so a blast in a bay takes its arch and the
support pass brings down what was resting on it. Every bay has its stack of powder kegs
(the Keg prop, explosive), and one FuseCord runs the length of the row: from its free end
at the west pier it dips onto the top keg of each stack and climbs to the next pier, and
its tail hangs over the last step into the sump. Light it anywhere - a flame on the cord
is enough - and the burn carries bay to bay, setting each stack off as it passes.

The stulls in the spoil crawl under the row are timber terrain. The keg sling over the
sump is left out: its two kegs lie in the sump instead.
"""
ORIGIN = (0, 0)
ENTRY = "L2"             # the spoil crawl: L1 is the first bay, on top of its kegs
BURN_SPEED = 1.0         # units a second - the row burns in about 20 s
MASONRY = 6              # px of brick round every bay
_stulls = []


def hooks(add, mod):
    ox, oy = ORIGIN
    _stulls.clear()

    def stull(x, y0, y1):
        _stulls.append((x - ox, y0 - oy, y1 - oy))

    def cord(points):
        pass                                    # the FuseCord is laid in furnish, in one piece

    def chain(*a, **k):
        pass

    return {"stull": stull, "cord": cord, "chain": chain}


def furnish(add, mod, ox, oy):
    E, F, S = mod.EDGES, mod.FLOORS, mod.SPRING
    stacks = ((24, (4, 3, 2)), (104, (5, 4, 2)), (186, (3, 2)), (252, (4, 3, 2, 1)))
    pins = [(E[0] + 3, F[0] - S + 4)] + [(E[i + 1], F[min(i + 1, 3)] - S + 3) for i in range(4)]
    path = [pins[0]]
    for i, (sx, rows) in enumerate(stacks):
        tx = sx + int((len(rows) - 1) * 4.5) + 4
        ty = F[i] - len(rows) * 11
        path += [(tx, ty), pins[i + 1]]                     # down onto the stack, up to the pier
    lx, ly = pins[-1]
    path += [(lx + 6, ly + 14), (lx + 7, F[3] + 6), (lx + 9, F[3] + 30)]   # the tail, into the sump
    add.fuse([(ox + x, oy + y) for x, y in path], BURN_SPEED)


def extras(g, mod):
    E, F = mod.EDGES, mod.FLOORS
    bays = {(x, y) for (x, y) in g.air if x < E[-1] - 1 and y < F[-1] + 2}
    ring = set(bays)
    for _ in range(MASONRY):
        ring |= {(x + dx, y + dy) for (x, y) in ring for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for (x, y) in ring - g.air:
        if x < E[-1] + 4 and 0 <= y < g.h and 0 <= x < g.w:
            g.set(x, y, "brick")
    for x, y0, y1 in _stulls:
        g.rect(x, y0, x + 3, y1, "wood")
        g.rect(x - 4, y0, x + 7, y0 + 2, "wood")
    _part_the_row(g, mod)


CRACKS = (13, 317)      # x of the two cracks that part the row from the drift's rock


def _part_the_row(g, mod):
    """Cut the whole row - its floors, the step faces, the bricks under the bays - loose from
    the rock round it, so that it stands on the two stulls in the crawl and nothing else.
    Above the floors the bays are one air from end to end, so a crack down each end, from
    the floor to the crawl, is all it takes. The support pass does the rest: take out both
    stulls and the row drops into the crawl, kegs and all."""
    E, F = mod.EDGES, mod.FLOORS
    for cx in CRACKS:
        bay = max(0, min(3, max(i for i in range(4) if E[i] <= cx) if cx >= E[0] else 0))
        y = F[bay]                                           # from the floor of the end bay down:
        while y < g.h and g.m.get((cx, y)) is None:          # past any air under it (the tube)
            y += 1
        while y < g.h and g.m.get((cx, y)) is not None:      # and through the rock to the crawl
            g.set(cx, y, None)
            y += 1
    # check it is loose: the solid under the second bay, flooded, must not reach the edge
    seed = (128, mod.FLOORS[1] + 8)
    seen, stack = {seed}, [seed]
    while stack:
        x, y = stack.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n in seen or not (0 <= n[0] < g.w and 0 <= n[1] < g.h):
                continue
            if g.m.get(n) is None or g.m.get(n) == "wood":
                continue
            seen.add(n)
            stack.append(n)
    edge = any(x <= 0 or x >= g.w - 1 or y >= g.h - 1 or y <= 0 for x, y in seen)
    print("  the row: %d cells, %s" % (len(seen), "STILL ATTACHED to the room's rock" if edge
                                         else "loose - held by the stulls only"))
