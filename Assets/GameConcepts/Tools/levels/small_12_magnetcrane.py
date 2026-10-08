"""Small room S12 - THE MAGNET CRANE.

A wide scrap hall with a steel runway beam hung under its roof end to end. On the beam
a trolley, and off the trolley, on two ropes, a lifting electromagnet - live, with a
load still on it: a girder, a fistful of scrap, and a Sentinel that walked under it.
Below, a pit full of scrap, and the metal enemies standing on it.

The toy is the magnet: run it along the beam and it takes anything metal off the floor
- scrap, drums, a RiotBrute - and cut it and everything on it comes down at once.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S12"

COIL = (168, 128, 62)
FIELD = (120, 190, 220)
RUST = (122, 74, 50)
BENCH_Y = 252          # the west bench, local
RAIL_Y = 122           # underside of the runway beam, local


def crane_edit(air, ox, oy):
    return {(x, y) for (x, y) in air if not (x - ox < 128 and y - oy >= BENCH_Y)}


def runway(x0, x1, y, roof):
    """Steel I-beam under the roof on hangers: flanges, web, rivets."""
    rect(x0, y - 7, x1, y, MET_D)
    rect(x0, y - 7, x1, y - 6, MET_L)
    rect(x0, y - 1, x1, y, MET)
    rect(x0, y - 5, x1, y - 2, (70, 70, 72))
    for x in range(int(x0) + 4, int(x1), 9):
        px(x, y - 4, MET_XL)
    for hx in range(int(x0) + 8, int(x1), 52):
        top = roof(hx)
        rect(hx - 1, top, hx + 1, y - 8, MET_D)
        rect(hx - 4, top, hx + 4, top + 1, MET)
    for ex in (x0, x1):                                    # end stops
        rect(ex - 2, y - 9, ex + 2, y + 4, MET_D)
        rect(ex - 2, y + 4, ex + 2, y + 4, HAZARD)


def trolley(cx, y):
    """Trolley on the beam's bottom flange: wheels either side, a rope drum under."""
    for wx in (cx - 8, cx + 8):
        disc(wx, y - 4, 3, MET_D)
        ring(wx, y - 4, 3, MET_L)
    rect(cx - 13, y + 1, cx + 13, y + 9, MET)
    rect(cx - 13, y + 1, cx + 13, y + 1, MET_XL)
    rect(cx - 9, y + 4, cx + 9, y + 7, RUST)
    for x in range(cx - 9, cx + 10, 2):
        px(x, y + 5, (90, 56, 40))


def magnet(cx, y, w=36):
    """The lifting magnet side-on: a flat iron drum, a coil band, the pole face under.
    Field lines only because it is live."""
    rect(cx - w // 2, y, cx + w // 2, y + 11, MET_D)
    rect(cx - w // 2, y, cx + w // 2, y, MET_L)
    rect(cx - w // 2 + 2, y + 3, cx + w // 2 - 2, y + 7, COIL)
    for x in range(cx - w // 2 + 3, cx + w // 2 - 2, 3):
        px(x, y + 5, (120, 90, 44))
    rect(cx - w // 2 - 2, y + 11, cx + w // 2 + 2, y + 13, MET)
    rect(cx - 5, y - 6, cx + 5, y - 1, MET_D)              # the yoke
    for k in range(4):
        r = 12 + k * 8
        for a in range(14):
            ang = math.pi * (0.08 + a * 0.06)
            px(cx + math.cos(ang) * r * 1.5, y + 14 + math.sin(ang) * r, FIELD, 0.32 - k * 0.06)
    glow(cx, y + 18, 40, FIELD, 0.2)


def girder(x, y, w, h=5):
    rect(x, y, x + w, y + h, MET)
    rect(x, y, x + w, y, MET_L)
    for k in range(int(w // 8)):
        line(x + k * 8, y + h, x + k * 8 + 8, y, MET_D, 0.7)


def drum(x, floor, c=RUST):
    rect(x, floor - 10, x + 7, floor - 1, c)
    rect(x, floor - 10, x + 7, floor - 10, (160, 104, 72))
    rect(x, floor - 6, x + 7, floor - 6, MET_D)


def heap(cx, base, w, h, m):
    """The scrap heap: a mound of junk filling the pit and standing above it."""
    cells = []
    for x in range(int(cx - w / 2), int(cx + w / 2)):
        t = abs(x - cx) / (w / 2.0)
        top = base - h * (1 - t * t) - 2 * math.sin(x * 0.7)
        y = int(top)
        while (x, y) in m:
            cells.append((x, y))
            y += 1
    for (x, y) in cells:
        r = rnd()
        px(x, y, MET_D if r < 0.3 else MET if r < 0.5 else RUST if r < 0.65 else ROCK_M if r < 0.8 else DIRT_D)
    for _ in range(40):
        x, y = pick(cells)
        rect(x, y, x + 1 + int(rnd() * 4), y + int(rnd() * 2), pick([MET_L, MET, RUST, MET_D]))
    tops = {}
    for (x, y) in cells:
        tops[x] = min(tops.get(x, 10 ** 6), y)
    for x, y in tops.items():
        px(x, y, MET_L if chance(0.5) else MET)
    return tops


def lifted(x, y, n=18):
    for _ in range(n):
        lx = x + (rnd() - 0.5) * 34
        ly = y + rnd() * 26
        rect(lx, ly, lx + 1 + rnd() * 3, ly + 1, pick([MET_L, MET, MET_XL, RUST]), 0.9)


def crane_furnish(ox, oy, m):
    teeth(m, ox + 40, ox + 430, oy + 140, 34)
    roof = lambda x: ceil_at(m, x, oy + RAIL_Y) + 1
    ry = oy + RAIL_Y
    rx0, rx1 = ox + 112, ox + 336
    runway(rx0, rx1, ry, roof)

    # the west bench: a stop block, a cable reel, what was dropped there
    bf = oy + BENCH_Y
    rect(ox + 118, bf, ox + 128, bf + 2, MET_D)
    rect(ox + 20, bf, ox + 128, bf, ROCK_L)
    disc(ox + 52, bf - 9, 8, MET_D)
    ring(ox + 52, bf - 9, 8, MET_L)
    disc(ox + 52, bf - 9, 3, RUST)
    rect(ox + 44, bf - 2, ox + 60, bf - 1, MET_D)
    girder(ox + 70, bf - 6, 40)
    drum(ox + 96, bf - 6)

    # the pit and its heap
    hb = floor_at(m, ox + 318, oy + 300)
    tops = heap(ox + 318, hb, 150, 64, m)
    draw_rotated(32, 20, tub_cart, ox + 286, tops.get(ox + 286, hb) - 4, -0.5)
    girder(ox + 330, tops.get(ox + 348, hb) - 4, 34)
    for dx in (360, 372):
        drum(ox + dx, tops.get(ox + dx + 4, hb) + 2)
    rock_blob(ox + 438, oy + 236, 14, 28, rough=0.3)

    # the trolley, the ropes, the magnet and what is on it
    tx = ox + 262
    trolley(tx, ry)
    my = oy + 196
    line(tx - 5, ry + 9, tx - 5, my - 6, MET_L)
    line(tx + 5, ry + 9, tx + 5, my - 6, MET_L)
    magnet(tx, my, 44)
    girder(tx - 32, my + 14, 62, 4)
    sprite("Sentinel", tx - 2, my + 18)
    lifted(tx + 20, my + 44, 26)
    for _ in range(14):
        rect(tx - 20 + rnd() * 36, my + 14 + rnd() * 3, tx - 18 + rnd() * 36, my + 15 + rnd() * 3,
             pick([MET, RUST, MET_L]))

    # the floor between bench and pit: a plate that was dropped and stuck, and the bits
    # that came off it
    rock_blob(ox + 44, oy + 204, 40, 9, rough=0.25)
    stand("WizHollowhood", ox + 58, oy + 196)
    ff = floor_at(m, ox + 150, oy + 240)
    def plate():
        rect(1, 1, 30, 5, MET)
        rect(1, 1, 30, 1, MET_L)
        for x in (5, 14, 23):
            px(x, 3, MET_XL)
    draw_rotated(32, 7, plate, ox + 146, ff - 9, -1.05)
    for _ in range(26):
        x = ox + 130 + rnd() * 100
        f = floor_at(m, x, oy + 240)
        rect(x, f - 1 - int(rnd() * 2), x + 1 + rnd() * 3, f - 1, pick([MET, MET_D, RUST, MET_L]))
    drum(ox + 214, floor_at(m, ox + 218, oy + 240))
    # the spare hook block parked at the west end of the beam
    chain(ox + 150, ry + 1, oy + 160)
    rect(ox + 146, oy + 160, ox + 154, oy + 166, MET)
    rect(ox + 146, oy + 160, ox + 154, oy + 160, MET_XL)
    line(ox + 150, oy + 167, ox + 150, oy + 172, MET_L)
    line(ox + 150, oy + 172, ox + 154, oy + 170, MET_L)

    # light: two lamps off the beam
    for lx in (ox + 100, ox + 390):
        lamp(lx, ry + 1, drop=6, bulb=LAMP, tint=LAMP, r=70, strength=0.14)

    stand("RiotBrute", ox + 318, tops.get(ox + 318, hb), flip=True)
    stand("Minespider", ox + 360, tops.get(ox + 360, hb) + 2, flip=True)
    stand("Sentinel", ox + 180, floor_at(m, ox + 180, oy + 220))
    stand("Grenadier", ox + 30, bf)
    stand("WizCrimson", ox + 420, floor_at(m, ox + 420, oy + 200), flip=True)


ROOM = {
    "name": "THE MAGNET CRANE", "w": 460, "h": 360,
    "shapes": [([("blob", 230, 200, 204, 100)], 0.1),            # the hall
               ([("blob", 80, 128, 34, 30),                       # bells in the roof
                 ("blob", 376, 124, 34, 30)], 0.12),
               ([("blob", 318, 290, 86, 42)], 0.12)],              # the scrap pit
    "sockets": {"T1": ("T", 80, 100), "T2": ("T", 376, 96),
                "L1": ("L", BENCH_Y, 30), "L2": ("L", 168, 44),
                "R1": ("R", 214, 36), "B1": ("B", 196, 58)},
    "edit": crane_edit,
    "furnish": crane_furnish,
}


SHEET = {
    "seed": 71201,
    "callouts": [
        ("1 RUNWAY BEAM ON HANGERS", (-120, -50), (160, 118)),
        ("2 LIVE MAGNET, LOAD STILL ON", (200, -50), (262, 204)),
        ("3 THE SCRAP PIT", (330, 380), (340, 300)),
    ],
    "beats": [
        ("THE MAGNET TAKES ANYTHING METAL, CUT IT AND IT ALL DROPS", (170, 180, 195)),
        ("SENTINEL AND RIOTBRUTE ARE METAL TOO", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
