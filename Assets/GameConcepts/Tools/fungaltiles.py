"""Tiles of the fungal deep: the rock, soil and flesh the mushroom rooms (S47 on) are made
of, and their back walls. Written to Resources/Sprites/Materials like every terrain tile,
two cells a pixel (`backwalls.save_tile`), and seamless - every feature wraps.

    python Assets/GameConcepts/Tools/fungaltiles.py

* fungal_rock  - the rooms' own rock: dark slate gone violet, flecked with spore;
* fungal_hard  - the fill between them on a fungal floor: the same, colder and darker;
* mycelium     - soil shot through with white threads (floors, mounds);
* fungal_cap   - the flesh of a giant cap (terrain that burns: built as wood);
* fungal_stem  - a giant stem, fibres running up it;
* fungal_glowcap - the cap of a glowing giant (Terraria's): built as wood, lit by props;
* back_mycelium - back wall: rock netted over with threads;
* back_caps     - back wall: a crust of small caps, for a grown wall behind a shrine;
* back_stem     - back wall inside a house: stem slabs on end;
* back_gills    - back wall under a cap roof: its gills.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from backwalls import save_tile  # noqa: E402


def grid(w, h, c):
    return [[c] * w for _ in range(h)]


def speckle(a, rnd, colours, p):
    h, w = len(a), len(a[0])
    for y in range(h):
        for x in range(w):
            r = rnd.random()
            acc = 0.0
            for c, q in zip(colours, p):
                acc += q
                if r < acc:
                    a[y][x] = c
                    break


def blobs(a, rnd, n, r0, r1, c, edge=None):
    """Soft round patches, wrapping round the tile's edges."""
    h, w = len(a), len(a[0])
    for _ in range(n):
        cx, cy, r = rnd.random() * w, rnd.random() * h, r0 + rnd.random() * (r1 - r0)
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, y - cy)
                if d <= r - 0.6:
                    a[y % h][x % w] = c
                elif edge and d <= r + 0.4:
                    a[y % h][x % w] = edge


def walk_threads(a, rnd, n, length, c, c2=None):
    """Thin wandering threads, wrapping."""
    h, w = len(a), len(a[0])
    for _ in range(n):
        x, y = rnd.random() * w, rnd.random() * h
        ang = rnd.random() * 6.28
        for k in range(length):
            a[int(y) % h][int(x) % w] = c2 if (c2 and k % 4 == 0) else c
            ang += (rnd.random() - 0.5) * 0.9
            x += math.cos(ang)
            y += math.sin(ang)


def fungal_rock(dark=False):
    rnd = random.Random(471 if not dark else 473)
    k = 0.78 if dark else 1.0
    base = tuple(int(v * k) for v in (54, 44, 58))
    a = grid(24, 24, base)
    speckle(a, rnd, [tuple(int(v * k) for v in c) for c in ((40, 32, 44), (66, 54, 70), (30, 24, 34))],
            (0.18, 0.12, 0.06))
    blobs(a, rnd, 5, 1.5, 3.2, tuple(int(v * k) for v in (46, 38, 50)), tuple(int(v * k) for v in (36, 28, 40)))
    for _ in range(9 if not dark else 4):                       # spore flecks
        x, y = rnd.randrange(24), rnd.randrange(24)
        a[y][x] = tuple(int(v * k) for v in (120, 98, 132))
    return a


def mycelium():
    rnd = random.Random(481)
    a = grid(24, 24, (48, 38, 36))
    speckle(a, rnd, ((38, 30, 30), (60, 48, 42), (30, 24, 24)), (0.2, 0.12, 0.05))
    walk_threads(a, rnd, 5, 18, (96, 90, 78), (140, 134, 116))
    return a


def fungal_cap():
    rnd = random.Random(491)
    a = grid(32, 16, (112, 76, 92))
    speckle(a, rnd, ((96, 64, 80), (128, 90, 104), (84, 56, 70)), (0.25, 0.15, 0.06))
    blobs(a, rnd, 6, 1.4, 3.0, (140, 104, 116), (124, 88, 102))
    return a


def fungal_stem():
    rnd = random.Random(501)
    a = grid(16, 32, (148, 140, 116))
    for x in range(16):
        tone = (134, 126, 104) if x % 4 == 0 else (160, 152, 126) if x % 4 == 2 else None
        for y in range(32):
            if tone and rnd.random() < 0.8:
                a[y][x] = tone
    speckle(a, rnd, ((120, 112, 94),), (0.05,))
    return a


def back_mycelium():
    rnd = random.Random(511)
    a = grid(32, 32, (46, 38, 50))
    speckle(a, rnd, ((36, 30, 40), (56, 46, 60)), (0.18, 0.1))
    walk_threads(a, rnd, 8, 24, (84, 80, 78), (118, 114, 104))
    return a


def back_caps():
    rnd = random.Random(521)
    a = grid(24, 24, (44, 34, 44))
    speckle(a, rnd, ((34, 26, 34), (54, 42, 54)), (0.2, 0.1))
    for _ in range(14):                                         # little caps, lit on top
        cx, cy = rnd.randrange(24), rnd.randrange(24)
        r = 1 + rnd.randrange(2)
        for dx in range(-r, r + 1):
            a[cy % 24][(cx + dx) % 24] = (110, 76, 92)
            a[(cy - 1) % 24][(cx + dx) % 24] = (138, 100, 114) if abs(dx) < r else (110, 76, 92)
        a[(cy + 1) % 24][cx % 24] = (140, 132, 110)
    return a


def back_stem():
    """Inside a house: slabs of stem stood on end, a seam every six."""
    rnd = random.Random(531)
    a = grid(24, 36, (140, 132, 108))
    for x in range(24):
        for y in range(36):
            if x % 6 == 0:
                a[y][x] = (164, 156, 128)
            elif x % 6 == 5:
                a[y][x] = (100, 94, 76)
            elif (x * 3 + y // 4) % 5 == 0:
                a[y][x] = (124, 116, 96)
        j = (x // 6 * 13 + 7) % 36                     # end joints, staggered
        a[j][x] = (100, 94, 76)
    speckle(a, rnd, ((118, 110, 92),), (0.04,))
    return a


def back_gills():
    """Under a cap roof: the gills, fine ridges running across."""
    a = grid(32, 8, (96, 64, 78))
    for y in range(8):
        for x in range(32):
            if x % 2 == 0:
                a[y][x] = (72, 46, 58) if y % 4 else (60, 38, 48)
            elif y == 0:
                a[y][x] = (118, 82, 96)
    return a


def fungal_glowcap():
    """The flesh of a glowing cap: pale cyan, brighter spots (the light itself is props)."""
    rnd = random.Random(541)
    a = grid(32, 16, (70, 140, 150))
    speckle(a, rnd, ((56, 118, 128), (92, 170, 176), (48, 100, 112)), (0.25, 0.15, 0.06))
    blobs(a, rnd, 6, 1.2, 2.6, (140, 214, 210), (104, 186, 188))
    return a


def write_all():
    save_tile("fungal_rock", fungal_rock())
    save_tile("fungal_hard", fungal_rock(dark=True))
    save_tile("mycelium", mycelium())
    save_tile("fungal_cap", fungal_cap())
    save_tile("fungal_stem", fungal_stem())
    save_tile("back_mycelium", back_mycelium())
    save_tile("back_caps", back_caps())
    save_tile("back_stem", back_stem())
    save_tile("back_gills", back_gills())
    save_tile("fungal_glowcap", fungal_glowcap())


if __name__ == "__main__":
    write_all()
