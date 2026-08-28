"""Concept 25 - THE WINDING HOUSE.

The same built maze again, same doubled cell, but this block is a machine. Three line
shafts run the width of it through slots in every wall, and each bay takes its drive off
the shaft above it: winding drums, gear trains, and the brakes that are the only thing
between a drum and the rope on it.

Big bays are what let the machinery be the level. A drum is a wheel the player can free,
a gear train is a wall of moving teeth, and the shaft head bay is a hole straight through
all three floors with a rope in it - the fastest route down here, and a moving one.

Bay (3, 1) is what a drum looks like after its brake let go.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

COLS, ROWS = 5, 3
X0, Y0 = 22, 28
PITCH_X, PITCH_Y = 70, 60
SHAFT_HEAD = (1, 0)             # the bay the rope goes down through
RUNAWAY = (3, 1)                # the bay whose brake let go
LAMP_TINT = (255, 214, 140)


def cell_box(cell):
    i, j = cell
    x = X0 + i * PITCH_X
    y = Y0 + j * PITCH_Y
    return x, y, x + PITCH_X, y + PITCH_Y


# ── local props - the ones only a winding house has ──────────────────────────
def drum(cx, cy, r=12, wound=True, broken=False):
    """Winding drum: flanged wheel, rope courses on the barrel, and a spoke pattern so
    it reads as a thing that turns rather than a disc."""
    disc(cx, cy, r, MET)
    ring(cx, cy, r, MET_XL)
    ring(cx, cy, r - 1, MET_D)
    if wound:
        for i in range(int(r / 3)):
            ring(cx, cy, r - 3 - i * 3, WOOD_D if i % 2 else WOOD)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        line(cx, cy, cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2), MET_D, 0.8)
    disc(cx, cy, 2.4, MET_D)
    ring(cx, cy, 2.4, MET_L)
    if broken:
        for k in range(9):                                # flange gone, spokes bent
            a = rnd() * 6.28
            line(cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6,
                 cx + math.cos(a) * (r + 5), cy + math.sin(a) * (r + 5), MET_D)
        sparks(cx + r - 2, cy - 2, 12, 14)


def pedestal(cx, base, top, w=7):
    """Bearing stand. Without one, a drum reads as a wheel floating in a dark room."""
    rect(cx - w // 2, top, cx + w // 2, base, MET_D)
    rect(cx - w // 2, top, cx - w // 2, base, MET)
    rect(cx - w // 2 - 2, base - 2, cx + w // 2 + 2, base, MET_D)     # foot
    rect(cx - w // 2 - 2, base - 2, cx + w // 2 + 2, base - 2, MET_L)
    rect(cx - w // 2 - 1, top, cx + w // 2 + 1, top + 1, MET_L)       # cap / bearing
    for k in range(2):                                                # hold-down bolts
        px(cx - w // 2 - 1 + k * (w + 2), base - 1, MET_XL)


def mounted_drum(cx, cy, r, floor, wound=True, broken=False, released=False):
    """A drum as installed: stand, wheel, band, weight."""
    pedestal(cx, floor, cy)
    drum(cx, cy, r, wound=wound, broken=broken)
    brake_band(cx, cy, r, released=released)


def brake_band(cx, cy, r=12, released=False):
    """The band round the drum and the weight that pulls it tight. Released, the weight
    is on the floor and the drum is somebody else's problem."""
    for k in range(14):
        a = -1.1 + k * 0.16
        px(cx + math.cos(a) * (r + 2), cy + math.sin(a) * (r + 2), MET_XL)
    lx = cx + r + 3
    if released:
        rect(lx, cy + r + 4, lx + 5, cy + r + 8, MET_D)
        rect(lx, cy + r + 4, lx + 5, cy + r + 4, MET_L)
        line(cx + r + 2, cy + 2, lx + 2, cy + r + 3, MET_D)
    else:
        rect(lx - 1, cy - 2, lx + 1, cy + 14, MET_D)      # pull rod
        rect(lx - 3, cy + 14, lx + 3, cy + 19, MET)       # the weight
        rect(lx - 3, cy + 14, lx + 3, cy + 14, MET_L)


def gear_train(x, y, n=3):
    r = 9
    for k in range(n):
        gear(x + k * (r * 2 - 1), y + (k % 2) * 5, r - (k % 2) * 2, teeth=9 - (k % 2))


def lever_bank(x, base, n=4):
    """The control frame. Somebody stands here and decides which drum is turning."""
    rect(x - 2, base, x + n * 6 + 2, base + 1, MET_D)
    for k in range(n):
        lx = x + k * 6
        rect(lx, base - 12, lx + 1, base, MET_L)
        disc(lx, base - 13, 1.4, RED_L if k % 2 else MET_XL)
    rect(x - 2, base - 4, x + n * 6 + 2, base - 4, MET_D, 0.7)


def line_shaft_run(x0, x1, y, pulleys=18):
    rect(x0, y, x1, y + 1, MET_D)
    rect(x0, y, x1, y, MET_L)
    for x in range(int(x0) + 8, int(x1) - 4, pulleys):
        disc(x, y + 3, 2.4, MET)
        ring(x, y + 3, 2.4, MET_XL)
        rect(x - 1, y + 1, x + 1, y + 1, MET_D)


def belt_drop(x, y0, y1, lean=0):
    """Flat belt from the line shaft down to whatever this bay drives."""
    line(x, y0, x + lean, y1, WOOD_D)
    line(x + 2, y0, x + 2 + lean, y1, WOOD)


def whipped_rope(x0, y0, pts):
    """Rope that let go, drawn as the curve it took. Reads as speed, and as a warning."""
    x, y = x0, y0
    for dx, dy in pts:
        line(x, y, x + dx, y + dy, MET_L, 0.9)
        line(x, y + 1, x + dx, y + dy + 1, MET_D, 0.7)
        x, y = x + dx, y + dy


def cage(x, y, w=18, h=14):
    rect(x, y, x + w, y + h, MET)
    frame(x, y, x + w, y + h, MET_XL)
    rect(x + 2, y + 2, x + w - 2, y + h - 2, (28, 32, 38))
    for gx in range(int(x) + 3, int(x + w) - 2, 3):
        rect(gx, y + 2, gx, y + h - 2, MET_L, 0.6)
    rect(x - 2, y - 3, x + w + 2, y - 1, MET_D)
    rect(x - 2, y - 3, x + w + 2, y - 3, MET_L)


def oil_can(x, base):
    rect(x, base - 6, x + 5, base, MET_D)
    rect(x, base - 6, x + 5, base - 6, MET_L)
    line(x + 5, base - 5, x + 9, base - 8, MET_L)


def build():
    new_canvas(400, 225, seed=52511)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=22)
    for _ in range(40):
        rect(rnd() * cw, rnd() * 12, rnd() * cw + 6, rnd() * 12 + 1, ROCK_D, 0.5)

    carve(8, 10, 392, 218, rough=3)
    rock_teeth(12, 388, 12, 22)
    floor_slab(8, 392, 214, 4, ROCK_D, ROCK_L)
    rubble(10, 210, 390, 214, 50, (ROCK_M, ROCK_D, DIRT))
    for lx in (60, 210, 350):
        lamp(lx, 12, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=28, strength=0.20)

    links = maze_links(COLS, ROWS, braid=0.35)
    ends = maze_dead_ends(links)

    masonry_block(links, cell_box, COLS, ROWS, wall=4, door_h=24, hatch=15,
                  breaches=(((2, 2), 'E'), ((0, 1), 'S')), door_shut=0.35)

    # ── three line shafts, straight through every wall on the row ──────────
    for j in range(ROWS):
        y = Y0 + j * PITCH_Y + 9
        for i in range(COLS - 1):
            wall_slot(X0 + (i + 1) * PITCH_X - 4, y - 1, 6, 5)
        line_shaft_run(X0 + 2, X0 + COLS * PITCH_X - 2, y)

    # ── the bays ──────────────────────────────────────────────────────────
    for k, cell in enumerate(sorted(links)):
        x0, y0, x1, y1 = cell_box(cell)
        fl = y1 - 4
        shaft_y = y0 + 9
        if cell in (SHAFT_HEAD, RUNAWAY):
            continue
        r = k % 5
        if r == 0:
            mounted_drum(x0 + 22, fl - 14, 12, fl)
            belt_drop(x0 + 20, shaft_y + 4, fl - 26)
            lever_bank(x0 + 46, fl, 4)
            humanoid(x0 + 54, fl - 12, MET_L, DIRT_L, face_right=False)
        elif r == 1:
            gear_train(x0 + 14, fl - 16, 3)
            belt_drop(x0 + 14, shaft_y + 4, fl - 24, lean=2)
            crate(x0 + 52, fl - 8, 7)
            oil_can(x0 + 44, fl)
        elif r == 2:
            plank(x0 + 4, fl - 26, x1 - 26, fl - 26, 2)     # control platform
            for bx in (x0 + 8, x0 + 30):
                rect(bx, fl - 24, bx + 1, fl - 16, WOOD_D)
            ladder(x0 + 6, fl - 24, fl - 4, w=4, step=6)
            lever_bank(x0 + 16, fl - 27, 5)
            humanoid(x0 + 30, fl - 39, MET_L, GREEN, face_right=False)
            mounted_drum(x1 - 20, fl - 12, 10, fl)
            belt_drop(x1 - 22, shaft_y + 4, fl - 22)
        elif r == 3:
            mounted_drum(x0 + 18, fl - 13, 11, fl)
            mounted_drum(x0 + 46, fl - 11, 9, fl, wound=False)
            belt_drop(x0 + 16, shaft_y + 4, fl - 24)
            belt_drop(x0 + 44, shaft_y + 4, fl - 20, lean=-2)
            sparks(x0 + 46, fl - 20, 10, 12)
        else:
            gear_train(x0 + 10, fl - 14, 2)
            barrel(x0 + 40, fl - 8, MET, MET_L, MET_XL)
            barrel(x0 + 48, fl - 8, MET, MET_L, MET_XL)
            oil_can(x0 + 58, fl)
            humanoid(x0 + 30, fl - 12, DIRT_L, RED)
        if cell in ends and chance(0.6):
            humanoid(x0 + 60, fl - 12, MET_L, RED, face_right=False)
        for _ in range(12):                                # oil and swarf on the floor
            ox, oy = x0 + 6 + rnd() * (PITCH_X - 14), fl - rnd() * 2
            rect(ox, oy, ox + 1 + rnd() * 2, oy, pick([MET_D, CHAR, MET]), 0.7)

    # ── the shaft head: a hole through all three floors, with a rope in it ─
    sx0, sy0, sx1, sy1 = cell_box(SHAFT_HEAD)
    hx = sx0 + 34
    for j in range(ROWS):                                  # cut the floors out
        _, _, _, fy = cell_box((SHAFT_HEAD[0], j))
        rect(hx - 11, fy - 3, hx + 11, fy + 4, CAVE)
        rect(hx - 12, fy - 3, hx - 12, fy + 4, STONE_D)
        rect(hx + 12, fy - 3, hx + 12, fy + 4, STONE_D)
    rect(hx - 11, Y0 + 2 * PITCH_Y + 4, hx + 11, 213, CAVE)
    for wx, lit in ((hx - 13, MET_L), (hx + 11, MET)):     # lined, top to bottom
        rect(wx, sy0 + 14, wx + 2, 213, MET_D)
        rect(wx, sy0 + 14, wx, 213, lit, 0.8)
    for y in range(sy0 + 18, 210, 6):                      # guide timbers
        px(hx - 9, y, WOOD_D)
        px(hx + 9, y, WOOD_D)
    for y in range(sy0 + 26, 210, 22):                     # ring frames
        rect(hx - 11, y, hx - 5, y, MET, 0.7)
        rect(hx + 5, y, hx + 11, y, MET, 0.7)
    mounted_drum(sx0 + 14, sy0 + 30, 12, sy1 - 4)
    belt_drop(sx0 + 12, sy0 + 13, sy0 + 18)
    disc(hx, sy0 + 20, 4, MET)                             # head sheave
    ring(hx, sy0 + 20, 4, MET_XL)
    line(sx0 + 14, sy0 + 30, hx, sy0 + 20, MET_L)
    for y in range(sy0 + 24, 206):                         # the rope, all the way down
        px(hx, y, MET_L if y % 3 else MET_D)
    cage(hx - 9, Y0 + 2 * PITCH_Y + 12, 18, 14)
    player(hx - 6, Y0 + 2 * PITCH_Y + 15)
    binny(hx + 4, Y0 + 2 * PITCH_Y + 30)
    lamp(sx0 + 56, sy0 + 12, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    humanoid(sx0 + 58, sy1 - 16, DIRT_L, GREEN, face_right=False)

    # ── the bay whose brake let go ────────────────────────────────────────
    rx0, ry0, rx1, ry1 = cell_box(RUNAWAY)
    fl = ry1 - 4
    mounted_drum(rx0 + 24, fl - 14, 12, fl, wound=False, broken=True, released=True)
    belt_drop(rx0 + 22, ry0 + 13, fl - 26)
    whipped_rope(rx0 + 34, fl - 20, [(12, -8), (10, 9), (12, -6), (8, 7)])
    for _ in range(30):                                    # what the rope did to the bay
        px(rx0 + 8 + rnd() * 56, ry0 + 14 + rnd() * 34, pick([MET_D, STONE_D, MET]), 0.8)
    ragdoll(rx0 + 44, fl - 24, RED_L)
    ragdoll(rx0 + 12, fl - 14)
    scrap_pile(rx0 + 40, fl, 24, 9, (MET_D, MET, STONE_D, ROCK_M))
    sconce(rx1 - 6, ry0 + 24, -1)
    tk_beam(rx0 + 30, fl - 10, rx0 + 6, fl - 22)

    # ── the way in ───────────────────────────────────────────────────────
    for y in range(10, Y0 - 4):
        px(300, y, MET_L if y % 3 else MET_D)
    rect(294, Y0 - 10, 308, Y0 - 6, MET_D)
    rect(294, Y0 - 10, 308, Y0 - 10, MET_L)
    crate(296, Y0 - 20, 7)

    vignette()
    return save(out_path("LevelConcept_WindingHouse.png"))


if __name__ == "__main__":
    build()
