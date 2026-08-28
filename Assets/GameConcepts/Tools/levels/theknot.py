"""Concept 21 - THE KNOT.

A working that was never planned: ten by five cells of drift, every junction a decision,
and no two routes the same length. The layout is a real maze - one generated on the
sheet's own seed rather than drawn by eye - and the level design is what has been left
at the ends of it: the dead ends hold the faces still being worked, the long straights
hold the track, and the loops are the only reason being chased through here is survivable.

The maze is also the fragile part. Every corner is a pillar, and every pillar is holding
the drift above it up.

No surface, no labels: the plan view is the read.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

COLS, ROWS = 10, 5
STEP_X, STEP_Y = 40, 44          # cell pitch
ORIGIN_X, ORIGIN_Y = 20, 24      # centre of cell (0, 0)
HALF_W, HALF_H = 15, 9           # a drift is 30 x 18
BORE = 6                         # half-width of a vertical squeeze
LAMP_TINT = (255, 214, 140)


def centre(cell):
    i, j = cell
    return ORIGIN_X + i * STEP_X, ORIGIN_Y + j * STEP_Y


# ── local props ─────────────────────────────────────────────────────────────
def rock_teeth(x0, x1, y, n=8, c=ROCK_M, tip=ROCK_L):
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 2 + int(rnd() * 5)
        for k in range(ln):
            half = max((ln - k) // 4, 0)
            rect(x - half, y + k, x + half, y + k, c if k < ln - 1 else tip)


def dig_face(x, y, side=1, h=12):
    """The end of a drift, still being worked."""
    for k in range(h):
        rect(x, y - k, x + side * (1 + int(rnd() * 3)), y - k, ROCK_M, 0.9)
    for _ in range(8):
        my = y - rnd() * h
        line(x, my, x + side * 3, my - 2, ROCK_L, 0.5)
    for _ in range(12):                                  # spoil at the foot of it
        px(x - side * rnd() * 10, y - rnd() * 3, pick([DIRT, DIRT_L, ROCK_M]))


def vein(x0, y0, x1, y1, n=18, colors=(GREEN_L, PALE_G, MET_L)):
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        y = y0 + rnd() * (y1 - y0)
        rect(x, y, x + 1 + rnd() * 2, y, pick(list(colors)), 0.9)


def set_timber(x0, x1, y0, y1, step=13):
    """Square-set: the drifts the crew decided to keep."""
    for x in range(int(x0), int(x1), step):
        beam(x, y0, y1, 2, WOOD_D, WOOD)
    rect(x0, y0, x1, y0 + 1, WOOD)
    rect(x0, y0, x1, y0, WOOD_L)


def pillar_crack(x, y0, y1):
    """The rock between two drifts, and the reason it will not stay there."""
    for _ in range(7):
        cy = y0 + rnd() * (y1 - y0)
        line(x, cy, x + 3 - rnd() * 6, cy + 4, ROCK_D, 0.8)
    for _ in range(5):
        px(x + rnd() * 4 - 2, y0 + rnd() * (y1 - y0), CHAR, 0.7)


def fallen_cell(cx, cy):
    """One cell of the maze that is no longer a route."""
    for _ in range(90):
        x = cx - HALF_W + rnd() * HALF_W * 2
        y = cy - HALF_H + rnd() * HALF_H * 2
        px(x, y, pick([ROCK_M, ROCK_D, DIRT, DIRT_D]))
    for _ in range(10):
        sx = cx - HALF_W + rnd() * HALF_W * 2
        sy = cy - HALF_H + rnd() * HALF_H * 2
        rect(sx, sy, sx + 2 + rnd() * 5, sy + 1, WOOD_D)
    for _ in range(12):
        disc(cx + (rnd() - 0.5) * 30, cy + (rnd() - 0.5) * 18, 1 + rnd() * 3,
             (150, 146, 138), 0.12)


def build():
    new_canvas(400, 225, seed=52107)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=24)
    for _ in range(40):
        rect(rnd() * cw, rnd() * 14, rnd() * cw + 6, rnd() * 14 + 1, ROCK_D, 0.5)

    # ── the maze, generated on this sheet's seed ────────────────────────────
    links = maze_links(COLS, ROWS, braid=0.22)

    rooms = []
    for cell in sorted(links):
        cx, cy = centre(cell)
        rooms.append((cx - HALF_W, cy - HALF_H, cx + HALF_W, cy + HALF_H))
    for cell in sorted(links):
        cx, cy = centre(cell)
        for n in sorted(links[cell]):
            nx, ny = centre(n)
            if n[0] > cell[0]:                            # east link, a low squeeze
                rooms.append((cx + HALF_W - 1, cy + HALF_H - 11, nx - HALF_W + 1, cy + HALF_H))
            elif n[1] > cell[1]:                          # link down to the next tier
                rooms.append((cx - BORE, cy + HALF_H - 1, cx + BORE, ny - HALF_H + 1))
    carve_all(rooms, rough=2)

    # ── every cell gets a floor, and most get a light ──────────────────────
    for cell in sorted(links):
        cx, cy = centre(cell)
        floor_slab(cx - HALF_W, cx + HALF_W, cy + HALF_H - 2, 3, ROCK_D, ROCK_L)
        rock_teeth(cx - HALF_W + 2, cx + HALF_W - 2, cy - HALF_H + 1, 5)
        if chance(0.5):
            lamp(cx + int((rnd() - 0.5) * 16), cy - HALF_H + 1, drop=3,
                 bulb=LAMP_TINT, tint=LAMP_TINT, r=16, strength=0.24)
        rubble(cx - HALF_W + 2, cy + HALF_H - 4, cx + HALF_W - 2, cy + HALF_H - 2,
               10 + int(rnd() * 14), (ROCK_M, ROCK_D, DIRT))
        if chance(0.3):                                  # spoil shovelled to one side
            scrap_pile(cx - 12 + int(rnd() * 20), cy + HALF_H - 3, 14, 5,
                       (DIRT, DIRT_D, DIRT_L, ROCK_M))
        if chance(0.25):
            vein(cx - HALF_W + 3, cy - HALF_H + 3, cx + HALF_W - 3, cy + HALF_H - 5, 10)

    # ── the pillars between drifts, cracked where they are carrying most ───
    for cell in sorted(links):
        cx, cy = centre(cell)
        if chance(0.35):
            pillar_crack(cx + HALF_W + 4, cy - HALF_H, cy + HALF_H)

    # ── dead ends: faces, ore, and the odd body ───────────────────────────
    ends = maze_dead_ends(links)
    for k, cell in enumerate(ends):
        cx, cy = centre(cell)
        side = -1 if cell[0] > COLS // 2 else 1
        dig_face(cx - side * (HALF_W - 2), cy + HALF_H - 3, side, 13)
        vein(cx - HALF_W + 3, cy - HALF_H + 3, cx + HALF_W - 3, cy + HALF_H - 4, 14)
        if k % 3 == 0:
            humanoid(cx - 4, cy - 1, DIRT_L, RED, face_right=side > 0)
        elif k % 3 == 1:
            scrap_pile(cx - 10, cy + HALF_H - 3, 20, 7, (DIRT, DIRT_D, DIRT_L, ROCK_M))
        else:
            crate(cx - 4, cy + HALF_H - 10)

    # ── the long straights: track, carts, and the one belt down here ───────
    runs = maze_runs(links, horizontal=True, least=3)
    for k, run in enumerate(runs):
        x0, y0 = centre(run[0])
        x1, _ = centre(run[-1])
        yy = y0 + HALF_H - 3
        if k % 3 == 2:
            conveyor(x0 - HALF_W + 3, x1 + HALF_W - 3, yy - 6, direction=1)
            for _ in range(int((x1 - x0) / 6)):
                px(x0 - 10 + rnd() * (x1 - x0 + 20), yy - 9 + rnd() * 2,
                   pick([DIRT_L, ROCK_L, GREEN_L]))
        else:
            rails(x0 - HALF_W + 3, x1 + HALF_W - 3, yy,
                  broken=(int(x0 + (x1 - x0) * 0.55), int(x0 + (x1 - x0) * 0.62)))
            cart(x0 + int((x1 - x0) * 0.3), yy - 9, tipped=(k % 2 == 1))
        if k % 2 == 0:
            set_timber(x0 - HALF_W + 2, x1 + HALF_W - 2, y0 - HALF_H + 1, yy)

    # ── vertical squeezes get a ladder ────────────────────────────────────
    for cell in sorted(links):
        cx, cy = centre(cell)
        for n in sorted(links[cell]):
            if n[1] > cell[1] and chance(0.7):
                ladder(cx - 2, cy + HALF_H - 2, centre(n)[1] - HALF_H + 2, w=4, step=6)

    # ── hazards, in the corridors where they hurt most ─────────────────────
    gx, gy = centre((4, 1))
    gear(gx + HALF_W + 6, gy + HALF_H - 6, 7, teeth=8)    # grinder in a squeeze
    fx, fy = centre((7, 3))
    fire_patch(fx - 8, fy + HALF_H - 9, fx + 10, fy + HALF_H - 3, 20, 1.3)
    embers(fx - 12, fy - 4, fx + 14, fy + HALF_H - 3, 26)
    glow(fx, fy + 3, 26, F_MID, 0.24)
    for pxx in (fx - 12, fx + 12):                        # timber that is next to go
        beam(pxx, fy - HALF_H + 2, fy + HALF_H - 3, 2, CHAR, WOOD_D)

    fallen_cell(*centre((6, 1)))                          # one cell simply gone
    fallen_cell(*centre((2, 4)))

    # ── the crew, and the two who matter ──────────────────────────────────
    px0, py0 = centre((0, 2))
    player(px0 - 4, py0 - 2)
    binny(px0 + 8, py0 - 6)
    tk_beam(px0, py0 + 2, px0 + 26, py0 - 4)
    rect(px0 + 20, py0 - 8, px0 + 32, py0 - 2, ROCK_M)
    rect(px0 + 20, py0 - 8, px0 + 32, py0 - 8, ROCK_L)

    for cell, coat, trim in (((3, 0), MET_L, GREEN), ((8, 0), DIRT_L, DIRT_L),
                             ((1, 1), DIRT_L, RED), ((9, 2), MET_L, RED),
                             ((5, 2), DIRT_L, GREEN), ((3, 3), MET_L, DIRT_L),
                             ((0, 4), DIRT_L, RED), ((6, 4), MET_L, GREEN),
                             ((8, 3), DIRT_L, RED)):
        cx, cy = centre(cell)
        humanoid(cx - 2, cy - 2, coat, trim, face_right=chance(0.5))

    for cell in ((5, 1), (4, 3), (7, 4)):
        cx, cy = centre(cell)
        ragdoll(cx - 2, cy + 1, RED_L)

    tcx, tcy = centre((9, 2))
    tracer(tcx - 4, tcy + 2, tcx - 34, tcy + 4)           # a shot down a long straight

    # ── the way out, bottom right, and the hoist in at top left ───────────
    ex, ey = centre((9, 4))
    door(ex - 4, ey - HALF_H + 1, 22, 17)
    glow(ex + 7, ey, 20, PALE_G, 0.16)
    hx, hy = centre((0, 0))
    for y in range(0, hy - HALF_H + 2):                    # the rope you came down
        px(hx, y, MET_L if y % 3 else MET_D)
    rect(hx - 8, hy - HALF_H + 2, hx + 8, hy - HALF_H + 4, MET_D)
    rect(hx - 8, hy - HALF_H + 2, hx + 8, hy - HALF_H + 2, MET_L)

    vignette()
    return save(out_path("LevelConcept_TheKnot.png"))


if __name__ == "__main__":
    build()
