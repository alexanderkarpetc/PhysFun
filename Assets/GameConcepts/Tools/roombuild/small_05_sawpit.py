"""S05 THE SAWPIT, assembled.

The toy is the swing saw: a SawCarriage (kinematic, a RailShuttle) riding the roof rail end
to end, with a SawBlade hinged on its arbour and spun by the hinge's motor. The blade is a
trigger that carves the wood it overlaps and grinds what it catches, so whatever is on its
line - the logs on the trestles, the tops of both timber stacks, a gaper - is stock. Cut the
rail or its hangers out from over the wheels and the carriage drops, blade and all.

The rail, its hangers and end stops are steel terrain, the trestles and the pit's bearers
timber terrain. What the saw is meant to reach is loose, because the blade only carves
loose bodies: the logs on the trestles and across the pit, the log stacks (end-on logs),
the plank stacks.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomprops_rooms import SAW_HUB  # noqa: E402   rail to arbour on the carriage sprite

PPU = 20.0
# Changed from the sheet after the first play: the blade hangs 12 px higher than the
# sheet's (arbour 68 below the rail, not 80), so it clears the walkway and the logs on the
# trestles and takes what is stacked high; and the carriage runs between these two x (its
# centre, room px), short of the shelves at both ends, so it does not shove the west log
# stack or the east shelf's crate and grenadier off them.
RUN = (98, 392)
ENTRY_AT = (78, 214)          # the west floor past the log stack, the gaper's end
ORIGIN = (0, 0)               # set by export_rooms before hooks(): the room's corner on the sheet
_rec = {"rail": [], "hangers": [], "trestles": []}


def hooks(add, mod):
    ox, oy = ORIGIN
    for k in _rec:
        _rec[k].clear()

    # structure: recorded in the room's own coords for extras()
    def rail(x0, x1, y):
        _rec["rail"].append((x0 - ox, x1 - ox, y - oy))

    def hanger(x, roof_y, rail_y):
        _rec["hangers"].append((x - ox, roof_y - oy, rail_y - oy))

    def trestle(x, floor, h=10):
        _rec["trestles"].append((x - ox, floor - oy, h))

    # stock: loose, for the saw
    def log_stack(x, base, cols=5, rows=3, r=4):
        for row in range(rows):
            for col in range(cols - row):
                cx = x + col * (r * 2 + 1) + row * (r + 1)
                cy = base - r - 1 - row * (r * 2 - 1)
                add("LogEnd", cx + 0.5, cy + 0.5, scale=(2 * r + 1) / 12.0)

    def plank_stack(x, base, w=26, layers=6):
        sc = w / 30.0
        add("PlankStack", x + w / 2.0 + 0.5, base - 11 * sc, scale=sc)

    # the saw
    def trolley(x, rail_y, hub_y):
        x0, x1 = ox + RUN[0], ox + RUN[1]
        wheel_y = ((SAW_HUB + 5) / 2.0 - 3.5) / PPU
        # sprite: wheel row 0 on the rail, SAW_HUB + 5 rows tall
        add("SawCarriage", x + 0.5, rail_y + (SAW_HUB + 5) / 2.0, key="carriage",
            fields={0: {"_left": "%.3f" % ((x - x0) / PPU), "_right": "%.3f" % ((x1 - x) / PPU),
                        "_startEast": 1,
                        # the wheel probes, where the wheels are on this sprite (row 3.5, x +-7)
                        "_wheels.Array.data[0].x": "%.3f" % (-7 / PPU),
                        "_wheels.Array.data[0].y": "%.3f" % wheel_y,
                        "_wheels.Array.data[1].x": "%.3f" % (7 / PPU),
                        "_wheels.Array.data[1].y": "%.3f" % wheel_y}})

    def blade(cx, cy, r):
        # on the carriage's arbour, wherever the sheet drew it
        cy = oy + mod.RAIL_Y + SAW_HUB
        # a trigger, so its mass only turns it: kept light so the motor spins it up at once
        add("SawBlade", cx + 0.5, cy + 0.5, key="blade", mass=8)
        add.joint("blade", "Hub", "carriage", kind=0, _useMotor=1, _motorSpeed=-900,
                  _maxMotorTorque=4000)

    def noop(*a, **k):
        pass

    return {"rail": rail, "hanger": hanger, "trestle": trestle, "log_stack": log_stack,
            "plank_stack": plank_stack, "trolley": trolley, "blade": blade,
            "motion": noop, "sawdust": noop}


def _line(g, x0, y0, x1, y1, mat):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        g.rect(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n),
               round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), mat)


def extras(g, mod):
    for x0, x1, y in _rec["rail"]:
        g.rect(x0, y, x1, y + 5, "steel")
        for bx in (x0, x1 - 3):                              # end stops
            g.rect(bx, y + 6, bx + 3, y + 12, "steel")
    for x, roof_y, rail_y in _rec["hangers"]:
        g.rect(x, roof_y, x + 1, rail_y - 1, "steel")
        g.rect(x - 2, roof_y, x + 3, roof_y + 1, "steel")
    for x, floor, h in _rec["trestles"]:
        _line(g, x - 4, floor - 1, x, floor - h, "wood")
        _line(g, x + 4, floor - 1, x, floor - h, "wood")
        g.rect(x - 5, floor - h, x + 5, floor - h + 1, "wood")
    f = mod.FLOOR                                            # the pit's bearers
    g.rect(mod.PIT[0] - 4, f - 2, mod.PIT[0] + 6, f - 1, "wood")
    g.rect(mod.PIT[1] - 6, f - 2, mod.PIT[1] + 4, f - 1, "wood")
