"""Concept 23 - THE ASSAY BLOCK.

The third kind of maze, and the only one somebody built on purpose: the company's old
assay and strongroom block, dropped whole into a cavern so that every gram of ore leaving
the mine had to be walked through it. Thirty-six masonry cells, doorways where the plan
allowed one, floor hatches where it did not, and one strongroom at the middle of it.

That makes it the one maze on these sheets whose walls are worth attacking. They are
courses of block, not rock, and two of them are already down - the plan the guards patrol
and the plan the player is going to leave behind are different plans.

No surface, no labels.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

COLS, ROWS = 9, 4
X0, Y0 = 24, 30
PITCH_X, PITCH_Y = 39, 44
VAULT = (4, 2)                   # the cell that is worth the walk

LAMP_TINT = (255, 214, 140)


def cell_box(cell):
    i, j = cell
    x = X0 + i * PITCH_X
    y = Y0 + j * PITCH_Y
    return x, y, x + PITCH_X, y + PITCH_Y


# ── local props ─────────────────────────────────────────────────────────────
def scales(x, base):
    """Assay balance: the reason the block exists, and a nice thing to throw."""
    rect(x - 6, base, x + 6, base + 1, MET_D)
    rect(x - 1, base - 12, x, base, MET_L)
    rect(x - 8, base - 12, x + 8, base - 12, MET_L)
    for sx in (x - 8, x + 7):
        for k in range(3):
            px(sx, base - 11 + k, MET_D)
        rect(sx - 2, base - 8, sx + 2, base - 7, MET)
    disc(x, base - 13, 1.4, MET_XL)


def ore_bin(x, base, w=16, h=9):
    rect(x, base - h, x + w, base, MET_D)
    rect(x, base - h, x + w, base - h, MET_L)
    rect(x + 1, base - h + 1, x + w - 1, base - h + 3, (58, 46, 34))
    for _ in range(12):
        px(x + 2 + rnd() * (w - 3), base - h - 1 + rnd() * 3,
           pick([GREEN_L, PALE_G, DIRT_L, MET_L]))


def strongbox(x, base):
    rect(x, base - 12, x + 16, base, MET_D)
    rect(x, base - 12, x + 16, base - 12, MET_L)
    frame(x, base - 12, x + 16, base, MET)
    disc(x + 8, base - 6, 3, MET_L)
    ring(x + 8, base - 6, 3, MET_XL)
    for _ in range(8):                                     # what is in it, spilling out
        px(x + 2 + rnd() * 13, base - 14 + rnd() * 3, pick([PALE_G, GREEN_L, MET_XL]))


def build():
    new_canvas(400, 225, seed=52309)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=22)
    for _ in range(40):
        rect(rnd() * cw, rnd() * 12, rnd() * cw + 6, rnd() * 12 + 1, ROCK_D, 0.5)

    # ── one cavern, with the block dropped into it ──────────────────────────
    carve(8, 10, 392, 218, rough=3)
    rock_teeth(12, 388, 12, 22)
    floor_slab(8, 392, 214, 4, ROCK_D, ROCK_L)
    rubble(10, 210, 390, 214, 60, (ROCK_M, ROCK_D, DIRT))
    for lx in (60, 200, 340):                              # the cavern's own lights
        lamp(lx, 12, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.18)

    links = maze_links(COLS, ROWS, braid=0.3)
    ends = maze_dead_ends(links)

    # ── the shell, the walls, the doorways and the hatches ─────────────────
    masonry_block(links, cell_box, COLS, ROWS, wall=3, door_h=20, hatch=13,
                  breaches=(((2, 1), 'E'), ((6, 3), 'E')))
    for cell in sorted(links):                             # a sconce on some blank walls
        x0, y0, x1, y1 = cell_box(cell)
        if (cell[0] + 1, cell[1]) not in links[cell] and chance(0.3):
            sconce(x1 - 4, y0 + 14, -1)

    # ── what is in the cells ───────────────────────────────────────────────
    for k, cell in enumerate(sorted(links)):
        x0, y0, x1, y1 = cell_box(cell)
        fx, fy = x0 + 4, y1 - 4                            # standing room
        if cell == VAULT:
            continue
        r = k % 7
        if r == 0:
            ore_bin(fx + 4, fy, 18, 9)
            ore_bin(fx + 24, fy, 12, 7)
        elif r == 1:
            scales(fx + 16, fy)
            crate(fx + 26, fy - 8, 7)
        elif r == 2:
            crate(fx + 4, fy - 8); crate(fx + 14, fy - 7, 7, False)
            barrel(fx + 26, fy - 8, WOOD, WOOD_L, MET_L)
        elif r == 3:
            humanoid(fx + 12, fy - 12, MET_L, RED, face_right=chance(0.5))
            sconce(x0 + 6, y0 + 14, 1)
        elif r == 4:
            scrap_pile(fx + 2, fy, 30, 9, (STONE_D, STONE, DIRT, ROCK_M))
        elif r == 5:
            lamp(x0 + PITCH_X // 2, y0 + 4, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT,
                 r=20, strength=0.26)
            humanoid(fx + 20, fy - 12, DIRT_L, GREEN, face_right=False)
        else:
            for _ in range(14):                            # ore trodden into the floor
                ox, oy = fx + rnd() * (PITCH_X - 8), fy - rnd() * 3
                rect(ox, oy, ox + 1 + rnd() * 2, oy, pick([GREEN_L, PALE_G, DIRT_L]), 0.85)
        if cell in ends and chance(0.7):                    # dead ends get the guards
            humanoid(fx + 24, fy - 12, MET_L, RED, face_right=False)

    # ── the strongroom ─────────────────────────────────────────────────────
    vx0, vy0, vx1, vy1 = cell_box(VAULT)
    masonry(vx0 + 2, vy0 + 2, vx1 - 2, vy1 - 2)            # solid, then hollowed
    rect(vx0 + 6, vy0 + 6, vx1 - 6, vy1 - 6, CAVE)
    frame(vx0 + 6, vy0 + 6, vx1 - 6, vy1 - 6, STONE_D)
    floor_slab(vx0 + 6, vx1 - 6, vy1 - 10, 3, STONE_D, STONE_L)
    door(vx0 + 12, vy1 - 32, 18, 22)
    glow(vx0 + 21, vy1 - 20, 24, PALE_G, 0.20)
    strongbox(vx0 + 10, vy1 - 11)
    ore_bin(vx0 + 26, vy1 - 11, 10, 7)
    sconce(vx0 + 8, vy0 + 14, 1)

    # ── the two who matter, working the breach ─────────────────────────────
    ex0, ey0, ex1, ey1 = cell_box((2, 1))
    player(ex0 + 10, ey1 - 16)
    binny(ex0 + 22, ey1 - 24)
    tk_beam(ex0 + 14, ey1 - 12, ex1 - 6, ey1 - 22)
    rect(ex1 - 12, ey1 - 26, ex1 + 2, ey1 - 20, STONE)     # a block, held, mid-throw
    rect(ex1 - 12, ey1 - 26, ex1 + 2, ey1 - 26, STONE_L)

    # ── guards who have noticed, and one who did not ───────────────────────
    gx0, gy0, gx1, gy1 = cell_box((3, 1))
    humanoid(gx0 + 8, gy1 - 16, MET_L, RED, face_right=False)
    tracer(gx0 + 8, gy1 - 12, ex1 - 4, ey1 - 12)
    rx0, ry0, rx1, ry1 = cell_box((5, 2))
    ragdoll(rx0 + 14, ry1 - 14, RED_L)
    rx0, ry0, rx1, ry1 = cell_box((7, 0))
    ragdoll(rx0 + 10, ry1 - 14)

    # ── the way in: a hoist through the cavern roof ────────────────────────
    for y in range(10, Y0 - 4):
        px(24, y, MET_L if y % 3 else MET_D)
    rect(18, Y0 - 10, 32, Y0 - 6, MET_D)
    rect(18, Y0 - 10, 32, Y0 - 10, MET_L)
    crate(20, Y0 - 20, 7)

    vignette()
    return save(out_path("LevelConcept_AssayBlock.png"))


if __name__ == "__main__":
    build()
