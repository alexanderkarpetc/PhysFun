"""S46 MINERS' ROW, assembled.

The three huts are props from `roombuild.structures`: plank walls (the open windows left as
gaps, the powder shed's shuttered one as wall), a Door on the uphill side of each and one in
hut 3's partition, and a lean-to roof of RoofPlanks along each hut's single pitch.

The timber steps down each drop are terrain (`wood`): the treads, and a stringer under them
from the lip of the shelf above to the floor of the one below - it touches rock at both
ends, so the support pass holds it, and burns or cuts like any timber. The sheet's posts
under the treads are left out: they would fence off the foot of the drop.

Not exported: the lamp posts, the table, stool, bunk and shelf (lamps and interiors are only
on the sheet).

The back wall (`backwall`, drawn by backwalls.py): each hut's inside boarded up under its
lean-to, wainscot under a rail, the wall plate, a window onto the cave, a post behind hut
3's partition; out in the cave, a mine's timber set on the top and bottom shelves.
"""
from roombuild import structures as B

ORIGIN = (0, 0)


def hooks(add, mod):
    return B.hooks(add, mod)


def furnish(add, mod, ox, oy):
    B.finish(add)


def _line(g, x0, y0, x1, y1, mat, thick=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        g.rect(x, y, x, y + thick - 1, mat)


def extras(g, mod):
    for i in range(len(mod.SHELVES) - 1):
        x = mod.SHELVES[i][1] - 2
        y0, y1 = mod.SHELVES[i][2], mod.SHELVES[i + 1][2]
        last = None
        for k in range(mod.STEPS):
            sx, sy = mod.step_at(x, y0, y1, k)
            g.rect(sx, sy, sx + mod.STEP_RUN, sy + 1, "wood", only_air=True)
            last = (sx + mod.STEP_RUN, sy + 1)
        # the stringer, lip to floor, under the treads
        first = mod.step_at(x, y0, y1, 0)
        _line(g, first[0], first[1] + 2, last[0], y1, "wood", thick=3)


def backwall(b, mod):
    for i, (hx0, hx1, h) in enumerate(mod.HUTS):
        fl = mod.SHELVES[i][2]
        top = fl - h
        hi, lo = top - 8 + 4, top - 1 + 4                 # the roof's underside, high end west
        b.under_roof(hx0, hx1, lambda x: hi + (lo - hi) * (x - hx0) / (hx1 - hx0), fl - 1)
        b.wainscot(hx0, hx1, fl, h=12)
        b.beam(hx0, top + 2, hx1, top + 6)                # the wall plate
        if i == 2:
            mid = hx0 + 42
            b.beam(mid - 1, top + 6, mid + 5, fl - 1)     # behind the partition
            b.window(mid + 12, top + 12, mid + 26, top + 24)
        else:
            wx = (hx0 + hx1) // 2 + (8 if i == 0 else 0)
            b.window(wx - 7, top + 12, wx + 7, top + 24)
    # the lamp post at the head of each flight of steps, with the arm its lantern hangs from
    for i in range(2):
        x = mod.SHELVES[i][1] - 2
        y0 = mod.SHELVES[i][2]
        b.beam(x - 16, y0 - 36, x - 13, y0 - 1)
        b.beam(x - 16, y0 - 38, x - 10, y0 - 35)
    b.timber_set(132, 162, mod.SHELVES[0][2], 40)
    b.timber_set(318, 350, mod.SHELVES[2][2], 42)
