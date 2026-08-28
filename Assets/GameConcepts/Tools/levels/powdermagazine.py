"""Concept 24 - THE POWDER MAGAZINE.

The Assay Block's plan at double the cell size, and this time every room is full of the
one material the engine treats as a decision: powder. Fifteen vaulted bays, blast doors
in the openings, hatches between floors, and a fuse main threaded through wall slots from
bay to bay so the whole magazine can be fired from one place.

The bays are big enough to fight in, which is the point of the bigger cell - a stack of
barrels is cover, a thrown barrel is a delivery system, and the masonry between two bays
is thinner than the rock everywhere else on these sheets.

The north-west corner has already gone off once. Note where the sconces are, and are not.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

COLS, ROWS = 5, 3
X0, Y0 = 22, 28
PITCH_X, PITCH_Y = 70, 60
MAIN_STORE = (2, 1)              # the bay the fuse main runs to
BURNT = (0, 0)                   # the bay that has already been fired
LAMP_TINT = (255, 214, 140)
FUSE = (168, 140, 96)


def cell_box(cell):
    i, j = cell
    x = X0 + i * PITCH_X
    y = Y0 + j * PITCH_Y
    return x, y, x + PITCH_X, y + PITCH_Y


# ── local props - the ones only a magazine has ───────────────────────────────
def powder_stack(x, base, cols=4, rows=3, burnt=False):
    """Kegs stacked on their sides, seen end-on - circles, so they read as barrels and
    not as crates at this size. Cover, ammunition, and the reason nobody down here is
    carrying a lamp."""
    body = CHAR if burnt else WOOD
    hoop = (60, 52, 48) if burnt else MET_L
    lit = (52, 46, 44) if burnt else WOOD_L
    r = 4
    for row in range(rows):
        for c in range(cols):
            cx = x + c * (r * 2 + 1) + (r if row % 2 else 0)
            cy = base - r - 1 - row * (r * 2 - 1)
            disc(cx, cy, r, body)
            disc(cx, cy, r - 2, WOOD_D if not burnt else CHAR)
            ring(cx, cy, r, lit)
            rect(cx - r + 1, cy - 1, cx + r - 1, cy - 1, hoop, 0.8)   # hoop
            px(cx - 1, cy - r + 1, lit)
            if burnt and chance(0.4):
                px(cx, cy, F_COOL)
    rect(x - 2, base, x + cols * (r * 2 + 1), base + 1, WOOD_D)       # dunnage
    for k in range(cols):                                             # chocks
        px(x + k * (r * 2 + 1) + r, base - 1, WOOD_D)


def sand_bin(x, base, w=18, h=10):
    """Sand, for the fire that is not supposed to happen."""
    rect(x, base - h, x + w, base, WOOD_D)
    rect(x, base - h, x + w, base - h, WOOD)
    rect(x + 1, base - h + 2, x + w - 1, base - 1, DIRT)
    rect(x + 1, base - h + 2, x + w - 1, base - h + 2, DIRT_L)
    for _ in range(6):
        px(x + 2 + rnd() * (w - 3), base - h + 1 + rnd() * 2, DIRT_L)
    rect(x + w // 2 - 1, base - h - 4, x + w // 2, base - h, MET_D)   # scoop handle


def fuse(points, c=FUSE):
    """The fuse main. Runs along the springing of the vault, through a slot in every
    wall it meets, and into the bay that fires the rest."""
    for k in range(len(points) - 1):
        x0, y0 = points[k]
        x1, y1 = points[k + 1]
        steps = max(int(max(abs(x1 - x0), abs(y1 - y0))), 1)
        for i in range(steps + 1):
            t = i / steps
            px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + (1 if (i // 3) % 2 else 0),
               c if i % 4 else WOOD_D)
    for x, y in points[1:-1]:                              # a tie at every bend
        rect(x - 1, y - 1, x + 1, y + 1, MET_D)


def vault_rib(x0, x1, y):
    """Brick ribs across the ceiling of a bay - the giveaway that a room is built,
    not carved, once the walls are out of shot."""
    for x in range(int(x0), int(x1), 11):
        rect(x, y, x + 5, y + 1, STONE_D)
        rect(x, y, x + 5, y, STONE_L)


def scorched(x0, y0, x1, y1):
    """What one bay going off leaves: charred courses, spalled block, embers still in it."""
    for _ in range(150):
        x = x0 + rnd() * (x1 - x0)
        y = y0 + rnd() * (y1 - y0)
        px(x, y, pick([CHAR, (40, 34, 32), STONE_D]), 0.85)
    for _ in range(26):
        bx = x0 + rnd() * (x1 - x0)
        by = y1 - 2 - rnd() * 8
        rect(bx, by, bx + 2 + rnd() * 5, by + 1, pick([STONE_D, CHAR, ROCK_M]))
    embers(x0 + 4, y0 + 6, x1 - 4, y1 - 3, 34)
    fire_patch(x0 + 10, y1 - 14, x0 + 34, y1 - 4, 16, 1.2)
    glow((x0 + x1) / 2, y1 - 10, 34, F_MID, 0.22)


def mezzanine(x0, x1, y, ladder_at=None):
    """A plank staging halfway up a bay, because the bays are now tall enough to want one."""
    plank(x0, y, x1, y, 2)
    for bx in (x0 + 4, (x0 + x1) // 2, x1 - 5):
        rect(bx, y + 2, bx + 1, y + 9, WOOD_D)
    if ladder_at is not None:
        ladder(ladder_at, y + 2, y + 24, w=4, step=6)


def build():
    new_canvas(400, 225, seed=52410)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=22)
    for _ in range(40):
        rect(rnd() * cw, rnd() * 12, rnd() * cw + 6, rnd() * 12 + 1, ROCK_D, 0.5)

    # ── the cavern the magazine sits in ────────────────────────────────────
    carve(8, 10, 392, 218, rough=3)
    rock_teeth(12, 388, 12, 22)
    floor_slab(8, 392, 214, 4, ROCK_D, ROCK_L)
    rubble(10, 210, 390, 214, 60, (ROCK_M, ROCK_D, DIRT))
    for lx in (52, 200, 348):                              # lamps, kept outside the block
        lamp(lx, 12, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=28, strength=0.20)

    links = maze_links(COLS, ROWS, braid=0.3)
    ends = maze_dead_ends(links)

    masonry_block(links, cell_box, COLS, ROWS, wall=4, door_h=24, hatch=15,
                  breaches=(((0, 0), 'E'), ((3, 2), 'E')), door_shut=0.6)

    # ── the fuse main, bay to bay, through the walls ───────────────────────
    for j in range(ROWS):
        y = Y0 + j * PITCH_Y + 12
        for i in range(COLS - 1):
            x = X0 + (i + 1) * PITCH_X - 3
            wall_slot(x, y - 2, 5, 5)
        fuse([(X0 + 2, y), (X0 + COLS * PITCH_X - 2, y)])
    mx0, my0, mx1, my1 = cell_box(MAIN_STORE)
    fuse([(mx0 + 6, Y0 + 12), (mx0 + 6, my0 + 12), (mx0 + 6, my1 - 30),
          (mx0 + 22, my1 - 30)])

    # ── the bays ──────────────────────────────────────────────────────────
    for k, cell in enumerate(sorted(links)):
        x0, y0, x1, y1 = cell_box(cell)
        fl = y1 - 4                                        # the floor of the bay
        vault_rib(x0 + 4, x1 - 6, y0 + 3)
        if cell == BURNT or cell == MAIN_STORE:
            continue
        r = k % 5
        if r == 0:
            powder_stack(x0 + 8, fl, 4, 3)
            sand_bin(x0 + 42, fl, 16, 9)
        elif r == 1:
            powder_stack(x0 + 6, fl, 3, 2)
            mezzanine(x0 + 30, x1 - 6, fl - 26, ladder_at=x0 + 34)
            crate(x0 + 40, fl - 34, 7)
            barrel(x0 + 52, fl - 35, WOOD, WOOD_L, MET_L)
        elif r == 2:
            crate(x0 + 8, fl - 8); crate(x0 + 18, fl - 7, 7, False)
            powder_stack(x0 + 32, fl, 3, 3)
            humanoid(x0 + 56, fl - 12, MET_L, RED, face_right=False)
        elif r == 3:
            mezzanine(x0 + 6, x1 - 26, fl - 26, ladder_at=x0 + 10)
            powder_stack(x0 + 8, fl - 27, 3, 1)
            sand_bin(x0 + 40, fl, 18, 10)
            humanoid(x0 + 20, fl - 12, DIRT_L, GREEN)
        else:
            powder_stack(x0 + 10, fl, 5, 4)
            crate(x0 + 50, fl - 8, 7)
        if cell in ends and chance(0.7):
            humanoid(x0 + 48, fl - 12, MET_L, DIRT_L, face_right=False)

    # ── the bay that has already gone off ─────────────────────────────────
    bx0, by0, bx1, by1 = cell_box(BURNT)
    scorched(bx0 + 4, by0 + 4, bx1 - 6, by1 - 4)
    powder_stack(bx0 + 34, by1 - 4, 3, 2, burnt=True)
    ragdoll(bx0 + 16, by1 - 20, RED_L)
    ragdoll(bx0 + 44, by1 - 16)
    sconce(bx1 + 6, by0 + 20, 1)                           # the one that was left lit

    # ── the main store: everything the fuse main runs to ──────────────────
    powder_stack(mx0 + 6, my1 - 4, 6, 5)
    powder_stack(mx0 + 8, my1 - 48, 4, 1)
    sand_bin(mx0 + 54, my1 - 4, 12, 8)
    for _ in range(20):                                    # spilled powder underfoot
        ox, oy = mx0 + 6 + rnd() * 56, my1 - 6 + rnd() * 3
        rect(ox, oy, ox + 1 + rnd() * 2, oy, CHAR, 0.8)
    humanoid(mx0 + 50, my1 - 16, DIRT_L, RED, face_right=False)

    # ── the two who matter, in the breach off the burnt bay ───────────────
    ex0, ey0, ex1, ey1 = cell_box((1, 0))
    player(ex0 + 8, ey1 - 16)
    binny(ex0 + 22, ey1 - 26)
    tk_beam(ex0 + 12, ey1 - 12, ex0 + 44, ey1 - 24)
    rect(ex0 + 40, ey1 - 30, ex0 + 46, ey1 - 22, WOOD)     # a barrel, held, on its way
    rect(ex0 + 40, ey1 - 27, ex0 + 46, ey1 - 27, MET_L)
    px(ex0 + 43, ey1 - 29, PALE_G)

    # ── the guard who has noticed ────────────────────────────────────────
    gx0, gy0, gx1, gy1 = cell_box((1, 1))
    humanoid(gx0 + 30, gy1 - 16, MET_L, RED)
    tracer(gx0 + 34, gy1 - 12, gx0 + 60, gy1 - 14)
    ragdoll(gx1 - 20, gy1 - 14, RED_L)

    # ── the way in ───────────────────────────────────────────────────────
    for y in range(10, Y0 - 4):
        px(30, y, MET_L if y % 3 else MET_D)
    rect(24, Y0 - 10, 38, Y0 - 6, MET_D)
    rect(24, Y0 - 10, 38, Y0 - 10, MET_L)
    crate(26, Y0 - 20, 7)

    vignette()
    return save(out_path("LevelConcept_PowderMagazine.png"))


if __name__ == "__main__":
    build()
