"""Concept 22 - THE VEIN RUNS.

The other kind of maze: nobody laid this one out, they just followed the ore. Every run
is a bore chasing a vein, so the tunnels arrive at each other at whatever angle the rock
allowed, and the junctions are wherever two crews met by accident.

Where the drifts of [21] are square and legible, this is round, sloped and disorienting -
no floor is flat for more than a few metres, half the connections are steep enough to
need a rope, and the branch you want looks exactly like the four that dead-end on a face.
The ore in the walls is the only wayfinding the level gives you.

No surface, no labels.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

COLS, ROWS = 8, 5
LAMP_TINT = (255, 214, 140)
ORE = (159, 187, 83)


# ── boring, and the passes that make a bore read as a tunnel ────────────────
def bore(x0, y0, x1, y1, r0=7, r1=None):
    """Carve a round tunnel along a line. Radius wanders a little, which is the whole
    difference between a bore chasing ore and a corridor."""
    steps = max(int(max(abs(x1 - x0), abs(y1 - y0))), 1)
    for i in range(steps + 1):
        t = i / steps
        r = r0 + ((r1 if r1 else r0) - r0) * t
        disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r * (0.82 + 0.34 * rnd()), CAVE)


def chamber(cx, cy, r=14):
    disc(cx, cy, r, CAVE)
    for _ in range(10):
        disc(cx + (rnd() - 0.5) * r, cy + (rnd() - 0.5) * r, r * 0.5, CAVE)


def dress_walls(ore_chance=0.14):
    """One pass over the canvas: light the top edge of every tunnel, silt the bottom
    edge, and seed ore where the wall is freshly cut. Collected first, painted after,
    so a lit pixel does not make the pixel under it think it is an edge too."""
    cw, ch = canvas_size()
    lips, floors, seams = [], [], []
    for y in range(1, ch - 1):
        for x in range(cw):
            if at(x, y) != CAVE:
                continue
            if at(x, y - 1) != CAVE:
                lips.append((x, y))
                if chance(ore_chance):
                    seams.append((x, y))
            if at(x, y + 1) != CAVE:
                floors.append((x, y))
                if chance(ore_chance * 0.6):
                    seams.append((x, y))
    for x, y in lips:
        px(x, y, ROCK_L, 0.5)
        if chance(0.35):
            px(x, y + 1, ROCK_M, 0.35)
    for x, y in floors:
        px(x, y, DIRT if chance(0.6) else DIRT_D)
        px(x, y - 1, DIRT_L if chance(0.35) else DIRT_D, 0.7)
    for x, y in seams:
        rect(x, y, x + rnd() * 2, y, pick([ORE, PALE_G, MET_L]), 0.9)


# ── local props ─────────────────────────────────────────────────────────────
def ore_face(cx, cy, ang, h=13):
    """A dead end: the vein the run was chasing, and the tools left against it."""
    dx, dy = math.cos(ang), math.sin(ang)
    for k in range(h):
        t = k / h
        rect(cx + dx * k - 2, cy + dy * k - 2, cx + dx * k + 2, cy + dy * k + 2,
             ROCK_M, 0.8 * (1 - t * 0.4))
    for _ in range(14):                                  # the vein, in the face
        t = rnd() * h
        ox, oy = cx + dx * t, cy + dy * t + (rnd() - 0.5) * 6
        rect(ox, oy, ox + 1 + rnd() * 2, oy, pick([ORE, PALE_G]), 0.9)
    for _ in range(8):
        line(cx + dx * 3, cy + dy * 3 + rnd() * 6 - 3,
             cx + dx * 8, cy + dy * 8 + rnd() * 6 - 3, ROCK_L, 0.4)


def rope_run(x0, y0, x1, y1):
    """Steep enough that the crew rigged it. Also the fast way down."""
    steps = max(int(max(abs(x1 - x0), abs(y1 - y0))), 1)
    for i in range(steps):
        t = i / steps
        px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, WOOD_L if i % 4 else WOOD_D)
    for i in range(0, steps, 7):                          # knots
        t = i / steps
        disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.2, WOOD)


def stull(cx, cy, w=16):
    """A stull: one timber wedged across a round bore, and a plank floor on top of it."""
    rect(cx - w // 2, cy, cx + w // 2, cy + 1, WOOD_D)
    rect(cx - w // 2, cy, cx + w // 2, cy, WOOD_L)
    for bx in (cx - w // 2 + 1, cx + w // 2 - 2):
        rect(bx, cy + 2, bx + 1, cy + 5, WOOD_D)


def timber_chock(cx, cy):
    for k in range(3):
        rect(cx - 5 + k, cy - k * 2, cx + 5 - k, cy - k * 2 + 1, WOOD if k % 2 else WOOD_D)


def dust(x, y, r=14, n=14):
    for _ in range(n):
        disc(x + (rnd() - 0.5) * r * 2, y + (rnd() - 0.5) * r, 1 + rnd() * 3,
             (146, 140, 126), 0.11)


def build():
    new_canvas(400, 225, seed=52208)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=26)
    for _ in range(46):
        rect(rnd() * cw, rnd() * 16, rnd() * cw + 6, rnd() * 16 + 1, ROCK_D, 0.5)
    for _ in range(30):                                   # ore showing in the solid rock
        x, y = rnd() * cw, rnd() * ch
        for _ in range(5):
            ox, oy = x + rnd() * 10, y + rnd() * 8
            rect(ox, oy, ox + 1 + rnd() * 2, oy, ORE if chance(0.6) else PALE_G, 0.35)

    # ── the maze, as a set of nodes joined by bores ─────────────────────────
    links = maze_links(COLS, ROWS, braid=0.55)
    node = {}
    for j in range(ROWS):
        for i in range(COLS):
            node[(i, j)] = (26 + i * 50 + (rnd() - 0.5) * 18,
                            26 + j * 46 + (rnd() - 0.5) * 16)

    bores = []
    for cell in sorted(links):
        x0, y0 = node[cell]
        for n in sorted(links[cell]):
            if n < cell:
                continue
            x1, y1 = node[n]
            r = 5 + rnd() * 2
            mx = (x0 + x1) / 2 + (rnd() - 0.5) * 16       # bores bend on the way
            my = (y0 + y1) / 2 + (rnd() - 0.5) * 12
            bore(x0, y0, mx, my, r, 4 + rnd() * 2)
            bore(mx, my, x1, y1, 4 + rnd() * 2, r)
            bores.append((cell, n, (x0, y0), (mx, my), (x1, y1)))

    for cell in sorted(links):                            # false leads off the main runs
        if not chance(0.45):
            continue
        x0, y0 = node[cell]
        ang = rnd() * 6.28
        ln = 12 + rnd() * 16
        bore(x0, y0, x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln, 5, 3)

    hubs = [c for c in sorted(links) if len(links[c]) >= 3]
    for c in hubs:
        chamber(node[c][0], node[c][1], 10 + rnd() * 3)

    dress_walls()

    # ── dead ends: the faces the runs died on ──────────────────────────────
    ends = maze_dead_ends(links)
    for k, cell in enumerate(ends):
        cx, cy = node[cell]
        other = sorted(links[cell])[0]
        ang = math.atan2(cy - node[other][1], cx - node[other][0])
        ore_face(cx, cy, ang, 12)
        if k % 3 == 0:
            humanoid(cx - 3, cy - 4, DIRT_L, RED, face_right=chance(0.5))
        elif k % 3 == 1:
            timber_chock(cx, cy + 5)
            crate(cx - 8, cy - 3, 6)
        else:
            scrap_pile(cx - 9, cy + 5, 18, 6, (DIRT, DIRT_D, DIRT_L, ROCK_M))

    # ── hubs: the only places you can stand still ─────────────────────────
    for k, cell in enumerate(hubs):
        cx, cy = node[cell]
        stull(cx, cy + 6, 20)
        lamp(cx + (rnd() - 0.5) * 10, cy - 11, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT,
             r=20, strength=0.26)
        if k % 4 == 0:
            cart(cx - 6, cy - 3)
        elif k % 4 == 1:
            crate(cx - 9, cy + 1); crate(cx + 1, cy + 1, 6, False)
            humanoid(cx - 2, cy - 6, MET_L, GREEN, face_right=False)
        elif k % 4 == 2:
            barrel(cx - 3, cy - 1, WOOD, WOOD_L, MET_L)
            humanoid(cx + 4, cy - 6, DIRT_L, DIRT_L, face_right=False)
        else:
            spoil = (DIRT, DIRT_D, DIRT_L, ROCK_M)
            scrap_pile(cx - 10, cy + 5, 20, 7, spoil)
        dust(cx, cy, 14, 10)

    # ── every node gets something, so no run is featureless ───────────────
    for k, cell in enumerate(sorted(links)):
        if cell in hubs or cell in ends:
            continue
        cx, cy = node[cell]
        pick_n = k % 6
        if pick_n == 0:
            lamp(cx, cy - 7, drop=2, bulb=LAMP_TINT, tint=LAMP_TINT, r=16, strength=0.24)
        elif pick_n == 1:
            timber_chock(cx + 4, cy + 4)
            crate(cx - 8, cy - 1, 6)
        elif pick_n == 2:
            humanoid(cx - 3, cy - 5, pick([MET_L, DIRT_L]), pick([RED, GREEN, DIRT_L]),
                     face_right=chance(0.5))
        elif pick_n == 3:
            scrap_pile(cx - 8, cy + 4, 16, 5, (DIRT, DIRT_D, DIRT_L, ROCK_M))
        elif pick_n == 4:
            stull(cx, cy + 4, 14)
        else:
            for _ in range(10):                            # ore worth stopping for
                ox, oy = cx - 8 + rnd() * 16, cy - 6 + rnd() * 12
                rect(ox, oy, ox + 1 + rnd() * 2, oy, pick([ORE, PALE_G]), 0.9)

    # ── ropes and ladders on the steep links ──────────────────────────────
    for _, _, a, m, b in bores:
        if abs(b[1] - a[1]) < 24 or abs(b[0] - a[0]) > 30:
            continue                                      # only the steep ones get rigged
        if chance(0.6):
            rope_run(a[0], a[1] - 3, m[0], m[1])          # rigged along the actual bore
            rope_run(m[0], m[1], b[0], b[1] - 3)
        elif abs(a[0] - b[0]) < 9 and abs(m[0] - (a[0] + b[0]) / 2) < 5:
            top, bot = (a, b) if a[1] < b[1] else (b, a)
            ladder(m[0] - 2, top[1] + 3, bot[1] - 3, w=4, step=6)
        else:
            rope_run(a[0], a[1] - 3, m[0], m[1])
            rope_run(m[0], m[1], b[0], b[1] - 3)

    # ── the two who matter, in the biggest hub ────────────────────────────
    if hubs:
        hx, hy = node[max(hubs, key=lambda c: len(links[c]))]
        player(hx - 8, hy - 6)
        binny(hx + 4, hy - 12)
        tk_beam(hx - 2, hy - 2, hx + 22, hy - 10)
        rect(hx + 16, hy - 14, hx + 28, hy - 8, ROCK_M)
        rect(hx + 16, hy - 14, hx + 28, hy - 14, ROCK_L)

    # ── things that have gone wrong in here already ───────────────────────
    fcx, fcy = node[(4, 1)]
    fire_patch(fcx - 8, fcy + 1, fcx + 8, fcy + 7, 18, 1.3)
    embers(fcx - 12, fcy - 8, fcx + 12, fcy + 7, 26)
    glow(fcx, fcy + 3, 24, F_MID, 0.24)
    timber_chock(fcx - 12, fcy + 6)

    rcx, rcy = node[(2, 2)]
    for _ in range(40):                                   # a run that has run in on itself
        px(rcx - 14 + rnd() * 28, rcy - 8 + rnd() * 18, pick([ROCK_M, ROCK_D, DIRT]))
    dust(rcx, rcy, 16, 14)

    for cell in ((5, 0), (1, 3), (6, 2)):
        cx, cy = node[cell]
        ragdoll(cx - 2, cy - 1, RED_L)
    t0 = node[(3, 3)]
    tracer(t0[0] + 10, t0[1] - 2, t0[0] - 18, t0[1] + 2)

    # ── the way in, and the way out ──────────────────────────────────────
    ix, iy = node[(0, 0)]
    for y in range(0, int(iy) - 6):
        px(ix, y, MET_L if y % 3 else MET_D)
    disc(ix, iy - 6, 3, MET)
    ring(ix, iy - 6, 3, MET_XL)
    ex, ey = node[(6, 3)]
    door(ex - 4, ey - 12, 22, 22)
    glow(ex + 7, ey - 1, 20, PALE_G, 0.16)

    vignette()
    return save(out_path("LevelConcept_VeinRuns.png"))


if __name__ == "__main__":
    build()
