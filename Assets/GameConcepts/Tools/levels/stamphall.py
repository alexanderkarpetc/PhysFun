"""Concept 26 - THE STAMP HALL.

Third of the big-cell blocks, and the loudest: the mill where ore stops being rock. Each
bay holds a battery of stamps - iron heads on stems, lifted by cams off the line shaft and
dropped into a mortar box - fed by chutes through the cap of the block and emptied onto a
belt that runs out through the wall slots at the bottom.

A stamp battery is the clearest hazard on any of these sheets: four heads, each one up or
down, each one a column of the bay you cannot occupy. Cut a cam and a stamp stops; cut the
drive and a whole row does. Bay (3, 1) shows what happens when a stem lets go instead.

No surface, no labels. The dust is doing most of the atmosphere.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

COLS, ROWS = 5, 3
X0, Y0 = 22, 28
PITCH_X, PITCH_Y = 70, 60
DRIVE = (4, 1)                   # the bay with the flywheel in it
WRECKED = (3, 1)                 # the battery that threw a stem
LAMP_TINT = (255, 214, 140)
ORE = (159, 187, 83)


def cell_box(cell):
    i, j = cell
    x = X0 + i * PITCH_X
    y = Y0 + j * PITCH_Y
    return x, y, x + PITCH_X, y + PITCH_Y


# ── local props - the ones only a stamp mill has ─────────────────────────────
def mortar(x, base, w=34):
    """The box the stamps fall into: iron-shod timber, and always overfull."""
    rect(x, base - 8, x + w, base, WOOD_D)
    rect(x, base - 8, x + w, base - 8, WOOD)
    rect(x, base - 3, x + w, base - 3, MET_D)
    rect(x - 1, base - 9, x + w + 1, base - 8, MET_L)
    for _ in range(int(w / 2)):
        ox = x + 2 + rnd() * (w - 4)
        rect(ox, base - 10 + rnd() * 2, ox + 1 + rnd() * 2, base - 9, pick([ORE, DIRT_L, ROCK_L]))


def stamp_battery(x, base, n=4, cam_y=None, broken=False):
    """n stems in a guide frame, heads at different heights so the battery reads as
    something mid-cycle rather than a row of posts."""
    top = cam_y if cam_y is not None else base - 40
    span = (n - 1) * 8
    rect(x - 3, top, x + span + 3, top + 2, MET_D)         # guide frame
    rect(x - 3, top, x + span + 3, top, MET_L)
    rect(x - 3, base - 18, x + span + 3, base - 17, MET_D)  # lower guide
    for bx in (x - 3, x + span + 3):
        rect(bx, top, bx + 1, base - 17, MET_D)
    for k in range(n):
        sx = x + k * 8
        lift = (3, 12, 6, 16, 9)[k % 5]
        if broken and k == 2:
            continue
        head_y = base - 10 - lift
        rect(sx, top + 2, sx + 1, head_y, MET_L)           # stem
        rect(sx - 2, head_y, sx + 3, head_y + 8, MET)      # head
        rect(sx - 2, head_y, sx + 3, head_y, MET_XL)
        rect(sx - 2, head_y + 7, sx + 3, head_y + 8, MET_D)
        if lift < 5:                                        # the one that just landed
            for _ in range(8):
                px(sx - 4 + rnd() * 10, base - 10 + rnd() * 2, pick([DIRT_L, ORE]), 0.8)
            disc(sx, base - 9, 5, (150, 144, 128), 0.10)
    mortar(x - 6, base, span + 12)


def cam_shaft(x0, x1, y, n=5):
    """The shaft that lifts the stems: a line shaft with cams keyed onto it."""
    rect(x0, y, x1, y + 1, MET_D)
    rect(x0, y, x1, y, MET_L)
    for k in range(n):
        cx = x0 + 8 + k * max(int((x1 - x0 - 12) / max(n - 1, 1)), 6)
        a = k * 1.1
        disc(cx, y + 1, 3, MET)
        ring(cx, y + 1, 3, MET_XL)
        px(cx + int(math.cos(a) * 2), y + 1 + int(math.sin(a) * 2), MET_D)


def ore_chute(x, y0, y1, w=9, tilt=0):
    """Feed from the cavern roof, through the cap of the block, into the mortar."""
    for i in range(int(y1 - y0)):
        t = i / max(y1 - y0, 1)
        sx = x + tilt * t
        rect(sx, y0 + i, sx + 1, y0 + i, MET_D)
        rect(sx + w, y0 + i, sx + w + 1, y0 + i, MET_D)
        px(sx, y0 + i, MET_L)
    for _ in range(7):
        px(x + 2 + rnd() * (w - 3) + tilt * rnd(), y0 + rnd() * (y1 - y0),
           pick([ROCK_L, DIRT_L, ORE]))


def flywheel(cx, cy, r=16):
    disc(cx, cy, r, MET)
    ring(cx, cy, r, MET_XL)
    ring(cx, cy, r - 2, MET_D)
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        line(cx, cy, cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2), MET_D, 0.85)
    disc(cx, cy, 3, MET_D)
    ring(cx, cy, 3, MET_L)
    glow(cx, cy, r + 10, (150, 170, 190), 0.10)


def dust_hang(x0, y0, x1, y1, n=22):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), 1 + rnd() * 3.5,
             (152, 146, 132), 0.11)


def thrown_stem(x, y, dx, dy):
    """A stem that came out of its guides, and where it stopped."""
    line(x, y, x + dx, y + dy, MET_L)
    line(x + 1, y, x + 1 + dx, y + dy, MET_D)
    rect(x + dx - 2, y + dy, x + dx + 3, y + dy + 8, MET)
    rect(x + dx - 2, y + dy, x + dx + 3, y + dy, MET_XL)
    for _ in range(14):
        px(x + dx - 6 + rnd() * 14, y + dy + 6 + rnd() * 4, pick([STONE_D, ROCK_M, MET_D]))


def build():
    new_canvas(400, 225, seed=52612)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=22)
    for _ in range(40):
        rect(rnd() * cw, rnd() * 12, rnd() * cw + 6, rnd() * 12 + 1, ROCK_D, 0.5)

    carve(8, 8, 392, 218, rough=3)
    rock_teeth(12, 388, 10, 22)
    floor_slab(8, 392, 214, 4, ROCK_D, ROCK_L)
    rubble(10, 210, 390, 214, 50, (ROCK_M, ROCK_D, DIRT))
    for lx in (46, 190, 340):
        lamp(lx, 10, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.20)

    links = maze_links(COLS, ROWS, braid=0.35)
    ends = maze_dead_ends(links)

    masonry_block(links, cell_box, COLS, ROWS, wall=4, door_h=24, hatch=15,
                  breaches=(((1, 2), 'E'), ((2, 0), 'S')), door_shut=0.3)

    # ── the drive: one cam shaft per row, through every wall ───────────────
    for j in range(ROWS):
        y = Y0 + j * PITCH_Y + 10
        for i in range(COLS - 1):
            wall_slot(X0 + (i + 1) * PITCH_X - 4, y - 1, 6, 5)
        cam_shaft(X0 + 2, X0 + COLS * PITCH_X - 2, y, 9)

    # ── the feed: chutes down from the cavern roof into the top row ────────
    for i in (0, 2, 4):
        x = X0 + i * PITCH_X + 30
        ore_chute(x, 12, Y0 + 6, 9, tilt=2)
        for _ in range(9):
            px(x + 2 + rnd() * 8, 14 + rnd() * 12, pick([ROCK_L, ORE, DIRT_L]), 0.8)

    # ── the bays ──────────────────────────────────────────────────────────
    for k, cell in enumerate(sorted(links)):
        x0, y0, x1, y1 = cell_box(cell)
        fl = y1 - 4
        cam_y = y0 + 10
        if cell in (DRIVE, WRECKED):
            continue
        if cell[1] == ROWS - 1:                              # bottom row stands on a
            fl -= 11                                         # plinth, over the belt
            masonry(x0 + 6, fl, x1 - 8, y1 - 4)
        r = k % 4
        if r == 0:
            stamp_battery(x0 + 12, fl, 4, cam_y + 2)
            crate(x0 + 52, fl - 8, 7)
            humanoid(x0 + 60, fl - 12, MET_L, DIRT_L, face_right=False)
        elif r == 1:
            stamp_battery(x0 + 10, fl, 5, cam_y + 2)
            barrel(x0 + 58, fl - 8, WOOD, WOOD_L, MET_L)
        elif r == 2:
            stamp_battery(x0 + 34, fl, 4, cam_y + 2)
            plank(x0 + 4, fl - 24, x0 + 28, fl - 24, 2)      # sorting stage
            ladder(x0 + 6, fl - 22, fl - 4, w=4, step=6)
            humanoid(x0 + 14, fl - 36, DIRT_L, GREEN, face_right=False)
            for _ in range(10):
                ox, oy = x0 + 6 + rnd() * 20, fl - 26 + rnd() * 2
                rect(ox, oy, ox + 1 + rnd() * 2, oy, pick([ORE, PALE_G]), 0.9)
        else:
            stamp_battery(x0 + 16, fl, 3, cam_y + 2)
            gear(x1 - 16, fl - 12, 9, teeth=9)
            scrap_pile(x0 + 44, fl, 18, 7, (ROCK_M, DIRT, MET_D))
        if cell in ends and chance(0.6):
            humanoid(x0 + 6, fl - 12, MET_L, RED)
        dust_hang(x0 + 5, y0 + 12, x1 - 6, fl - 2, 18)
        for _ in range(14):                                  # crushed ore on the floor
            ox, oy = x0 + 6 + rnd() * (PITCH_X - 14), fl - rnd() * 2
            rect(ox, oy, ox + 1 + rnd() * 2, oy, pick([DIRT_L, ORE, ROCK_L]), 0.75)

    # ── the belt out, along the bottom row and through the shell ──────────
    by = Y0 + 2 * PITCH_Y + PITCH_Y - 9
    for i in range(COLS - 1):
        wall_slot(X0 + (i + 1) * PITCH_X - 4, by - 1, 6, 6)
    conveyor(X0 + 3, X0 + COLS * PITCH_X - 3, by, direction=1)
    for _ in range(60):
        px(X0 + 6 + rnd() * (COLS * PITCH_X - 12), by - 2 + rnd() * 2,
           pick([DIRT_L, ORE, ROCK_L]))

    # ── the drive bay: flywheel, and the belt up to the shafts ───────────
    dx0, dy0, dx1, dy1 = cell_box(DRIVE)
    fl = dy1 - 4
    flywheel(dx0 + 34, fl - 20, 16)
    rect(dx0 + 30, fl - 4, dx0 + 38, fl, MET_D)              # bed
    rect(dx0 + 30, fl - 4, dx0 + 38, fl - 4, MET_L)
    rect(dx0 + 33, fl - 20, dx0 + 35, fl - 4, MET)           # column
    gear(dx0 + 12, fl - 14, 10, teeth=10)
    line(dx0 + 20, fl - 22, dx0 + 34, fl - 32, WOOD_D)       # belt to the row above
    line(dx0 + 21, fl - 21, dx0 + 35, fl - 31, WOOD)
    line(dx0 + 34, dy0 + 12, dx0 + 34, fl - 34, WOOD_D)
    humanoid(dx0 + 56, fl - 12, MET_L, GREEN, face_right=False)
    sconce(dx1 - 6, dy0 + 26, -1)
    dust_hang(dx0 + 6, dy0 + 14, dx1 - 6, fl - 2, 14)

    # ── the battery that threw a stem ────────────────────────────────────
    wx0, wy0, wx1, wy1 = cell_box(WRECKED)
    fl = wy1 - 4
    stamp_battery(wx0 + 12, fl, 4, wy0 + 12, broken=True)
    thrown_stem(wx0 + 28, wy0 + 20, 22, 22)
    for _ in range(26):
        px(wx0 + 8 + rnd() * 56, wy0 + 16 + rnd() * 34, pick([STONE_D, MET_D, ROCK_M]), 0.8)
    breach(wx1 - 8, wy0 + 20, wx1 - 2, fl)                   # it went through the wall
    ragdoll(wx0 + 44, fl - 22, RED_L)
    ragdoll(wx0 + 16, fl - 12)
    dust_hang(wx0 + 5, wy0 + 12, wx1 - 6, fl - 2, 26)

    # ── the two who matter, one bay along ───────────────────────────────
    px0, py0, px1, py1 = cell_box((2, 1))
    fl = py1 - 4
    player(px0 + 8, fl - 16)
    binny(px0 + 20, fl - 28)
    tk_beam(px0 + 12, fl - 12, px0 + 42, fl - 26)
    rect(px0 + 38, fl - 32, px0 + 50, fl - 24, ROCK_M)       # a rock, held over the mortar
    rect(px0 + 38, fl - 32, px0 + 50, fl - 32, ROCK_L)

    # ── the way in ──────────────────────────────────────────────────────
    for y in range(8, Y0 - 4):
        px(360, y, MET_L if y % 3 else MET_D)
    rect(354, Y0 - 10, 368, Y0 - 6, MET_D)
    rect(354, Y0 - 10, 368, Y0 - 10, MET_L)
    crate(356, Y0 - 20, 7)

    vignette()
    return save(out_path("LevelConcept_StampHall.png"))


if __name__ == "__main__":
    build()
