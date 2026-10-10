"""S04 THE BELFRY, assembled.

The bell hangs on its one chain from the yoke under the timber headbeam: a Rope2D held
long-range (it does not stretch) under a Tether2D, so a round through the chain drops the
bell the whole height of the shaft onto the kegs and whoever is at the foot. The headbeam,
its wedges, the yoke and the boards out over the ledge lips are terrain; the beam is
wedged into the dome's walls, so it holds - burn it out and the bell comes down with it.
"""

ENTRY = "L2"            # the foot, west side: the one place not under a thrower


def hooks(add, mod):
    def bell(cx, top, lip):
        # the chain ties on under the yoke (the sheet's chain starts at BEAM_Y + 8)
        roof = top - mod.BELL_TOP + mod.BEAM_Y + 8
        add("Bell", cx + 0.5, top + 23, rope=(cx, roof, top - 11))

    def heavy_chain(x, y0, y1):
        pass                                    # the bell's own rope is the chain

    return {"bell": bell, "heavy_chain": heavy_chain}


def extras(g, mod):
    y = mod.BEAM_Y
    g.rect(52, y, 248, y + 4, "wood")                       # headbeam, wall to wall
    for wx in (53, 241):                                    # the wedges at its ends
        g.rect(wx, y - 3, wx + 6, y - 1, "wood")
    x = mod.BELL_X
    g.rect(x - 6, y + 5, x + 6, y + 7, "steel")             # the yoke the chain hangs from
    for side, fy, lip in mod.LEDGES:                        # boards out over each ledge lip
        x0, x1 = (lip - 2, lip + 12) if side == "L" else (lip - 12, lip + 2)
        for bx in range(x0, x1, 6):
            g.rect(bx, fy - 2, bx + 4, fy - 1, "wood")
