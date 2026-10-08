"""Every small room on one sheet, for picking which ones stay.

Finds every `levels/small_NN_*.py`, lays the rooms out in rows at game scale with every
socket open, and tags each with its code and name. No callouts - the per-room sheets
carry those; this one is for comparing shapes and density side by side.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from smallroomkit import *  # noqa: F403,E402

ROW_W = 2400
GAP_X, GAP_Y = 70, 110


def rooms():
    d = os.path.join(HERE, "levels")
    out = []
    for f in sorted(os.listdir(d)):
        if f.startswith("small_") and f[6:8].isdigit() and f.endswith(".py"):
            m = importlib.import_module("levels." + f[:-3])
            out.append((m.CODE, m.ROOM))
    return out


def layout(items):
    """Greedy rows: (code, room, ox, oy) for each, and the canvas height."""
    placed, x, y, row_h = [], GAP_X, 70, 0
    for code, room in items:
        if x + room["w"] > ROW_W - GAP_X and x > GAP_X:
            x, y, row_h = GAP_X, y + row_h + GAP_Y, 0
        placed.append((code, room, x, y))
        x += room["w"] + GAP_X
        row_h = max(row_h, room["h"])
    return placed, y + row_h + GAP_Y


def build():
    items = rooms()
    placed, height = layout(items)
    new_canvas(ROW_W, height, seed=70000)
    label_scale(2)
    lay([(room, ox, oy) for _, room, ox, oy in placed], None, [])
    for _, room, ox, oy in placed:
        dashed_box(ox, oy, ox + room["w"] - 1, oy + room["h"] - 1)
    for code, room, ox, oy in placed:
        btag(ox + 4, oy + room["h"] + 30, "%s  %s" % (code, room["name"]), PALE_G)
    btitle_bar("PHYSFUN - SMALL ROOMS:  ALL %d" % len(placed), "GAME SCALE / EVERY SOCKET OPEN")
    return save(out_path("RoomConcept_SmallIndex.png"), scale=1)


if __name__ == "__main__":
    build()
