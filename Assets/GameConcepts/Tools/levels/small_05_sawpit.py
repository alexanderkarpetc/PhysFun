"""Small room S05 - THE SAWPIT.

A long low cut with a steel rail bolted under the roof from end to end and a swing saw
on a trolley running along it, its blade at chest height. Timber stock is stacked at
both ends, logs lie on trestles under the rail, and in the middle the floor drops into
the old saw pit, a trench with a log across it. Gapers working. The saw does not stop:
it runs the rail end to end, and whatever is on its line is stock.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S05"

FLOOR = 214
RAIL_Y = 104
RAIL_X0, RAIL_X1 = 34, 428
SAW_X = 286                     # where the trolley is in this frame
HUB_Y = 184
BLADE_R = 16
PIT = (196, 266)                # the trench, x span
SAWDUST = (176, 150, 104)
SAWDUST_D = (130, 108, 74)


def sawpit_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR and not (PIT[0] <= lx <= PIT[1]):
            continue
        if ly >= 138 and ((lx - 4) / 70.0) ** 2 + ((ly - 146) / 34.0) ** 2 < 1:
            continue                                         # the stock shelf, west wall
        if ly >= 162 and ((lx - 462) / 48.0) ** 2 + ((ly - 174) / 30.0) ** 2 < 1:
            continue                                         # a lower one, east wall
        out.add((x, y))
    return out


def rail(x0, x1, y):
    """An I-beam under the roof: top flange, web, bottom flange the wheels run on."""
    rect(x0, y, x1, y + 1, MET_D)
    rect(x0, y + 2, x1, y + 3, MET)
    rect(x0, y + 4, x1, y + 5, MET_D)
    rect(x0, y + 4, x1, y + 4, MET_L)
    for x in range(int(x0) + 4, int(x1), 12):
        px(x, y + 2, MET_D)
    for bx in (x0, x1 - 3):                                 # end stops
        rect(bx, y + 6, bx + 3, y + 12, HAZARD)
        rect(bx, y + 6, bx + 3, y + 6, MET_D)


def hanger(x, roof_y, rail_y):
    rect(x, roof_y, x + 1, rail_y - 1, MET_D)
    px(x, roof_y, MET_L)
    rect(x - 2, roof_y, x + 3, roof_y + 1, MET)


def blade(cx, cy, r):
    """The disc with its teeth proud of the rim and a guard over the top half."""
    disc(cx, cy, r, MET)
    disc(cx, cy, r - 3, MET_L)
    disc(cx, cy, r - 6, MET)
    for i in range(24):
        a = i * 2 * math.pi / 24
        x, y = cx + math.cos(a) * (r + 1), cy + math.sin(a) * (r + 1)
        px(x, y, MET_XL)
        px(cx + math.cos(a + 0.08) * (r + 2), cy + math.sin(a + 0.08) * (r + 2), MET_XL)
    disc(cx, cy, 3, MET_D)
    px(cx, cy, MET_XL)
    for i in range(3):                                       # spin lines
        a0 = i * 2.1
        for k in range(10):
            a = a0 + k * 0.08
            px(cx + math.cos(a) * (r - 4), cy + math.sin(a) * (r - 4), MET_XL, 0.6)
    for k in range(40):                                      # the guard over the top
        a = math.pi + k * math.pi / 40
        for t in range(3):
            px(cx + math.cos(a) * (r + 4 + t), cy + math.sin(a) * (r + 4 + t),
               HAZARD if (k // 5) % 2 == 0 and t < 2 else MET_D)


def trolley(x, rail_y, hub_y):
    """Two wheels on the bottom flange, a carriage, a frame down to the arbour, and the
    belt from the motor on the carriage to the blade."""
    for wx in (x - 7, x + 7):
        disc(wx, rail_y + 3, 3.2, MET_D)
        ring(wx, rail_y + 3, 3.2, MET_L)
    rect(x - 12, rail_y + 7, x + 12, rail_y + 17, MET_D)
    rect(x - 12, rail_y + 7, x + 12, rail_y + 7, MET_L)
    rect(x - 10, rail_y + 9, x + 10, rail_y + 15, (78, 74, 64))
    disc(x + 6, rail_y + 12, 3.5, COPPER)                    # the motor
    disc(x + 6, rail_y + 12, 1.4, MET_D)
    for dx in (-5, 3):                                       # the frame, two flat bars
        rect(x + dx, rail_y + 18, x + dx + 2, hub_y - 2, MET)
        rect(x + dx, rail_y + 18, x + dx, hub_y - 2, MET_L)
    for y in range(rail_y + 26, hub_y - 4, 14):
        line(x - 5, y, x + 5, y + 7, MET_D)
    line(x + 6, rail_y + 15, x + 2, hub_y, INK)              # belt
    line(x + 7, rail_y + 15, x + 3, hub_y, (60, 52, 46))


def motion(x, y, d, n=4):
    """Chevrons along the rail showing the run, both ways."""
    for i in range(n):
        cx = x + i * 7 * d
        for k in range(4):
            px(cx - k * d, y - k, CYAN, 0.7)
            px(cx - k * d, y + k, CYAN, 0.7)


def log(x0, x1, y, r=4):
    """A log lying along the room: bark top and bottom, a cut end-grain face at x1."""
    rect(x0, y - r, x1, y + r, WOOD_D)
    rect(x0, y - r + 1, x1, y + r - 2, WOOD)
    rect(x0, y - r + 1, x1, y - r + 1, WOOD_L)
    for x in range(int(x0) + 3, int(x1), 9):
        px(x, y, WOOD_D)
    disc(x1, y, r, WOOD_L)
    ring(x1, y, r, WOOD_D)
    px(x1, y, WOOD_D)


def trestle(x, floor, h=10):
    line(x - 4, floor - 1, x, floor - h, WOOD_D)
    line(x + 4, floor - 1, x, floor - h, WOOD_D)
    rect(x - 5, floor - h, x + 5, floor - h + 1, WOOD)


def log_stack(x, base, cols=5, rows=3, r=4):
    for row in range(rows):
        for col in range(cols - row):
            cx = x + col * (r * 2 + 1) + row * (r + 1)
            cy = base - r - 1 - row * (r * 2 - 1)
            disc(cx, cy, r, WOOD)
            disc(cx, cy, r - 1.5, WOOD_L)
            ring(cx, cy, r, WOOD_D)
            px(cx, cy, WOOD_D)


def plank_stack(x, base, w=26, layers=6):
    for i in range(layers):
        yy = base - 1 - i * 3
        rect(x + (i % 2), yy - 2, x + w - (i % 3), yy, WOOD if i % 2 else WOOD_L)
        rect(x + (i % 2), yy, x + w - (i % 3), yy, WOOD_D)
    rect(x + 3, base - layers * 3 - 1, x + 4, base - 1, WOOD_D)         # sticks between


def sawdust(x0, x1, floor, h=3):
    for x in range(int(x0), int(x1)):
        t = (x - x0) / max(x1 - x0, 1)
        top = floor - 1 - int(h * math.sin(math.pi * t))
        rect(x, top, x, floor - 1, SAWDUST if (x + top) % 3 else SAWDUST_D)


def wall_shelf(m, x, y, d, rx, ry):
    """Rock grown out of the nearest wall (d = -1 west, 1 east) or roof (d = 0), found
    by scanning out through the air, so it is always attached."""
    if d:
        while (x, y) in m:
            x += d
        rock_blob(x - d * (rx // 3), y, rx, ry, rough=0.25)
    else:
        y = ceil_at(m, x, y)
        rock_blob(x, y + ry // 3, rx, ry, rough=0.3)


def sawpit_furnish(ox, oy, m):
    fy = oy + FLOOR
    teeth(m, ox + 40, ox + 420, oy + 120, 22)
    for x, y, d, rx, ry in ((60, 186, -1, 10, 7), (400, 122, 1, 14, 8), (300, 70, 0, 18, 8),
                            (150, 100, 0, 22, 7)):
        wall_shelf(m, ox + x, oy + y, d, rx, ry)

    # the rail and its hangers - roof is uneven, so every rod is its own length
    ry = oy + RAIL_Y
    for hx in range(RAIL_X0 + 10, RAIL_X1, 42):
        hanger(ox + hx, ceil_at(m, ox + hx, ry - 2) + 1, ry)
    rail(ox + RAIL_X0, ox + RAIL_X1, ry)
    lamp(ox + 130, ceil_at(m, ox + 130, ry - 2) + 1, drop=14, bulb=LAMP, tint=LAMP, r=80, strength=0.13)
    lamp(ox + 370, ceil_at(m, ox + 370, ry - 2) + 1, drop=14, bulb=LAMP, tint=LAMP, r=80, strength=0.13)

    # timber stock: logs at the west end on a rock shelf, planks at the east
    log_stack(ox + 18, oy + 138, cols=5, rows=3)
    stand("WizDeepminer", ox + 64, oy + 138)
    stand("Grenadier", ox + 430, oy + 162, flip=True)
    crate_g(ox + 440, oy + 162, 10)
    log_stack(ox + 22, fy, cols=4, rows=3)
    plank_stack(ox + 394, fy, 30, 7)
    plank_stack(ox + 400, fy - 22, 22, 4)
    sawdust(ox + 60, ox + 120, fy, 3)
    sawdust(ox + 300, ox + 360, fy, 4)

    # logs on trestles under the rail - the saw's own line
    for tx in (96, 150):
        trestle(ox + tx, fy, 11)
    log(ox + 86, ox + 168, fy - 15)
    for tx in (330, 372):
        trestle(ox + tx, fy, 11)
    log(ox + 316, ox + 384, fy - 15)

    # the saw pit: a log across the trench on bearers, the two-man saw through it
    rect(ox + PIT[0] - 4, fy - 2, ox + PIT[0] + 6, fy - 1, WOOD_D)
    rect(ox + PIT[1] - 6, fy - 2, ox + PIT[1] + 4, fy - 1, WOOD_D)
    log(ox + PIT[0] - 6, ox + PIT[1] + 6, fy - 7, r=5)
    rect(ox + 230, fy - 26, ox + 231, fy + 20, MET_L)        # pit saw, top handle to bottom
    rect(ox + 226, fy - 27, ox + 235, fy - 26, WOOD)
    rect(ox + 226, fy + 20, ox + 235, fy + 21, WOOD)
    pf = floor_at(m, ox + 244, fy + 2)
    sawdust(ox + PIT[0] + 6, ox + PIT[1] - 6, pf, 5)
    stand("Gaper", ox + 244, pf, flip=True)
    stand("Gaper", ox + 212, fy - 12)

    # the saw itself, mid-run, east-bound
    trolley(ox + SAW_X, ry, oy + HUB_Y)
    blade(ox + SAW_X, oy + HUB_Y, BLADE_R)
    motion(ox + SAW_X + 22, ry + 12, 1)
    motion(ox + SAW_X - 22, ry + 12, -1)
    for _ in range(40):                                      # sawdust off the front of it
        a = -0.6 + rnd() * 1.2
        d = BLADE_R + 2 + rnd() * 18
        px(ox + SAW_X + math.cos(a) * d, oy + HUB_Y + 4 + math.sin(a) * d * 0.6,
           pick([SAWDUST, SAWDUST_D, WOOD_L]), 0.85)
    sparks(ox + SAW_X - BLADE_R, oy + HUB_Y + 6, 8, 6)

    # who is working
    stand("Gaper", ox + 120, fy)
    stand("RiotBrute", ox + 348, fy, flip=True)
    stand("Gaper", ox + 400, fy - 21, flip=True)
    corpse(ox + 268 + 14, fy)


ROOM = {
    "name": "THE SAWPIT", "w": 460, "h": 300,
    "shapes": [([("blob", 150, 162, 140, 66),
                 ("blob", 326, 150, 122, 74),
                 ("blob", 236, 92, 64, 30)], 0.10),            # the vault over the pit
               ([("blob", 231, 234, 38, 26)], 0.08)],          # the saw pit
    "sockets": {"T1": ("T", 96, 108), "T2": ("T", 250, 70),
                "L1": ("L", 138, 26), "L2": ("L", FLOOR, 30),
                "R1": ("R", FLOOR, 22), "B1": ("B", 231, 50)},
    "edit": sawpit_edit,
    "furnish": sawpit_furnish,
}


SHEET = {
    "seed": 70505,
    "callouts": [
        ("1 SAW ON A ROOF RAIL", (330, -50), (SAW_X + 10, RAIL_Y + 4)),
        ("2 BLADE AT CHEST HEIGHT", (290, 320), (SAW_X, HUB_Y + BLADE_R)),
        ("3 THE OLD SAW PIT", (-100, 320), (231, 262)),
    ],
    "beats": [
        ("THE SAW RUNS THE RAIL END TO END: ON ITS LINE IS STOCK", (170, 180, 195)),
        ("GAPERS FEED IT, DUCK IN THE PIT, OR CUT THE RAIL", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
