"""S41 THE HONEYCOMB, assembled.

The rope that ties the pockets together is real. The CargoNet over the crew in the east
pocket hangs on a Hazards/Rope under a Tether2D, pinned at the crossbar of the sheave frame
in the north pocket: from there it runs down through a bore in the rock between them. Shoot
or cut the length of it in the north pocket and the net drops in the east one. The bore is
carved out of the map here, a little wider than the rope so its links hang free.

The frame is terrain (`wood`) standing on the north pocket's floor. The plank plug in the
tube from the store to the east pocket is a stack of WallPlanks, the ladder up the drop
shaft a Ladder - both from `roombuild.structures`.
"""
from roombuild import structures as B

ORIGIN = (0, 0)
_rec = {"frame": [], "bore": []}


def hooks(add, mod):
    ox, oy = ORIGIN
    for k in _rec:
        _rec[k].clear()
    hk = B.hooks(add, mod)
    pin = {}

    def sheave_frame(x, floor):
        _rec["frame"].append((x - ox, floor - oy))
        _rec["bore"].append((x - ox, floor - oy))
        pin["at"] = (x, floor - mod.FRAME_H + 3)

    def cargo_net(cx, top, w=30, h=22):
        px_, py_ = pin["at"]
        add("CargoNet", cx + 0.5, top + 13, rope=(px_, py_, top + 2))

    hk.update({"sheave_frame": sheave_frame, "cargo_net": cargo_net})
    return hk


def furnish(add, mod, ox, oy):
    B.finish(add)


def extras(g, mod):
    for x, floor in _rec["frame"]:
        top = floor - mod.FRAME_H
        for dx in (-7, 6):
            g.rect(x + dx, top, x + dx + 1, floor - 1, "wood")
        g.rect(x - 8, top - 2, x + 8, top, "wood")
    for x, floor in _rec["bore"]:
        # down through the north pocket's floor and the rock under it, into the east pocket
        y = floor
        while y < g.h and (y < floor + 4 or (x, y) not in g.air):
            g.rect(x - 2, y, x + 2, y, None)
            y += 1
