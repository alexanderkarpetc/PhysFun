"""Concept 20 - THE CRIBWORKS.

One chamber, one problem: the roof is a single slab of rock the crew undercut and then
had to hold up, and what they held it up with was stacked timber. Six crib towers, an
enormous dead weight sitting on them, and a working haulage level running along the top
of the slab because the ore was up there anyway.

The support pass makes this level play itself. Every crib is a load path the player can
see, count and remove, and the sixth one is already gone - the slab above it has dropped
as far as its neighbours will let it, and the crack running out of that corner is the
level telling you what the rest of the sequence looks like.

No surface, no labels: the towers and the crack carry it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SLAB_TOP, SLAB_BOT = 48, 74      # the dead weight, in canvas rows
LAMP_TINT = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def rock_teeth(x0, x1, y, n=12, c=ROCK_M, tip=ROCK_L):
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 3 + int(rnd() * 7)
        for k in range(ln):
            half = max((ln - k) // 4, 0)
            rect(x - half, y + k, x + half, y + k, c if k < ln - 1 else tip)


def crib(x, base, top, w=24, crushed=False, leaning=0):
    """Stacked timber crib: alternating courses seen from the side, so every other
    course is two end-grain blocks and the one between is a beam across them."""
    if crushed:
        top = base - (base - top) * 0.28                  # what is left of it
    y = base
    course = 0
    while y > top:
        lean = int(leaning * (base - y) / max(base - top, 1))
        if course % 2:
            rect(x + lean, y - 3, x + w + lean, y, WOOD)
            rect(x + lean, y - 3, x + w + lean, y - 3, WOOD_L)
            rect(x + lean, y, x + w + lean, y, WOOD_D)
        else:
            for bx in (x + lean, x + w - 6 + lean):
                rect(bx, y - 3, bx + 6, y, WOOD_D)
                rect(bx, y - 3, bx + 6, y - 3, WOOD)
                rect(bx + 2, y - 2, bx + 3, y - 1, WOOD_L)
        y -= 4
        course += 1
    if crushed:
        for _ in range(34):                               # timber splayed out sideways
            sx = x - 14 + rnd() * (w + 28)
            sy = base - rnd() * (base - top + 8)
            rect(sx, sy, sx + 3 + rnd() * 8, sy + 1, pick([WOOD_D, WOOD, CHAR]))
        for _ in range(24):
            px(x - 12 + rnd() * (w + 24), base - rnd() * 8, pick([ROCK_M, DIRT, WOOD_D]))


def wedge(x, y, w=8, side=1):
    """Driven between the crib head and the slab. Knock it out and the load shifts."""
    for i in range(4):
        rect(x + (i if side > 0 else 0), y + i, x + w - (i if side < 0 else 0), y + i,
             WOOD_L if i == 0 else WOOD)
    px(x + w // 2, y, MET_XL)


def jack(x, base, h=16):
    """Screw jack: the crew's answer when a crib settles."""
    rect(x, base - 3, x + 8, base, MET_D)
    rect(x, base - 3, x + 8, base - 3, MET_L)
    rect(x + 3, base - h, x + 5, base - 3, MET)
    for yy in range(int(base - h) + 1, int(base) - 3, 2):
        rect(x + 2, yy, x + 6, yy, MET_L, 0.8)
    rect(x + 1, base - h - 2, x + 7, base - h, MET_D)
    rect(x + 1, base - h - 2, x + 7, base - h - 2, MET_L)


def slab(x0, x1, y0, y1, sag_at=None):
    """The dead weight: one mass of rock, lighter than the country rock around it and
    parted from it top and bottom, so it reads as a block resting on the cribs rather
    than as more of the same wall."""
    rect(x0, y0 - 1, x1, y0 - 1, INK)                     # parting above
    rect(x0, y0, x1, y1, (84, 92, 104))                   # lighter than the country rock
    for _ in range((x1 - x0) * 3):                        # coarse grain, and plenty of it
        gx = x0 + rnd() * (x1 - x0)
        gy = y0 + rnd() * (y1 - y0)
        rect(gx, gy, gx + 1 + rnd() * 4, gy, ROCK_L if chance(0.55) else ROCK, 0.75)
    rect(x0, y0, x1, y0 + 2, ROCK_L)                      # lit top bed
    rect(x0, y1 - 3, x1, y1 - 1, ROCK)                    # shadowed underside
    rect(x0, y1, x1, y1, INK)                             # parting below - it is sitting on wood
    for _ in range(7):                                    # bedding planes
        yy = y0 + 4 + rnd() * (y1 - y0 - 7)
        x = x0
        while x < x1:
            ln = 12 + rnd() * 34
            rect(x, yy, x + ln, yy, ROCK, 0.55)
            x += ln + 8 + rnd() * 18
    if sag_at:                                            # the corner that has dropped
        cx, drop = sag_at
        for x in range(int(cx - 46), int(cx + 46)):
            t = abs(x - cx) / 46
            d = int(drop * (1 - t) ** 1.4)
            rect(x, y1, x, y1 + d, ROCK_M)
            px(x, y1 + d, ROCK_D)
        jx, jy = cx - 52, y0 + 2                          # one jagged crack, not a hatch
        while jx < cx + 40:
            nx = jx + 4 + rnd() * 5
            ny = min(max(jy + (rnd() - 0.35) * 9, y0 + 1), y1 - 2)
            line(jx, jy, nx, ny, INK, 0.85)
            line(jx, jy + 1, nx, ny + 1, ROCK_D, 0.5)
            jx, jy = nx, ny
        for _ in range(20):
            px(cx - 46 + rnd() * 92, y1 + rnd() * 7, pick([ROCK_D, ROCK_M, DIRT]), 0.8)


def build():
    new_canvas(400, 225, seed=52006)
    cw, ch = canvas_size()

    # ── rock to every edge ─────────────────────────────────────────────────
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=20)
    for _ in range(40):
        rect(rnd() * cw, rnd() * 14, rnd() * cw + 6, rnd() * 14 + 1, ROCK_D, 0.5)

    ROOMS = [
        (10, 16, 390, 44),      # haulage on top of the slab
        (12, 75, 388, 178),     # the undercut chamber, right up to the slab
        (16, 192, 236, 216),    # sub-drift below
        (250, 190, 392, 216),   # exit adit
        (352, 44, 380, 80),     # the hole the slab's dropped corner has opened
        (36, 176, 62, 196),     # chamber -> sub-drift
        (196, 176, 224, 196),   # chamber -> sub-drift, east
        (228, 194, 256, 214),   # sub-drift -> adit
    ]
    carve_all(ROOMS)

    # ── 1  the slab ────────────────────────────────────────────────────────
    slab(0, cw - 1, SLAB_TOP, SLAB_BOT, sag_at=(352, 9))

    carve(352, 44, 380, 84, rough=3)                      # the corner's drop, punched through
    for _ in range(18):
        px(352 + rnd() * 28, 46 + rnd() * 36, pick([ROCK_M, ROCK_D, DIRT]), 0.8)

    # ── 2  haulage running along the top of it ─────────────────────────────
    floor_slab(10, 390, 40, 4, ROCK_D, ROCK_L)
    rock_teeth(14, 386, 18, 16)
    rails(14, 386, 38, broken=(330, 350))
    cart(60, 29)
    cart(150, 29)
    cart(300, 29, tipped=True)
    for pxx in (30, 108, 190, 268, 340):
        beam(pxx, 20, 40, 2, WOOD_D, WOOD)
        rect(pxx - 3, 20, pxx + 5, 21, WOOD_L)
    pipe_run(12, 386, 20)
    humanoid(94, 28, MET_L, DIRT_L)
    humanoid(232, 28, DIRT_L, RED, face_right=False)
    humanoid(322, 28, MET_L, GREEN, face_right=False)
    scrap_pile(200, 39, 30, 8, (ROCK_M, DIRT, MET_D))
    for lx in (48, 168, 286, 372):
        lamp(lx, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    for _ in range(24):                                   # ore spilled along the track
        px(16 + rnd() * 366, 36 + rnd() * 3, pick([DIRT_L, GREEN_L, ROCK_L]), 0.8)

    # ── 3  the chamber: six load paths, one of them gone ───────────────────
    floor_slab(12, 388, 172, 6, ROCK_D, ROCK_L)
    CRIBS = [
        (26, 172, 71, 28, False, 0),
        (92, 172, 71, 26, False, 0),
        (156, 172, 71, 28, False, 0),
        (220, 172, 71, 26, False, 3),                     # this one has started to lean
        (284, 172, 71, 28, False, 0),
        (340, 172, 71, 26, True, 0),                      # and this one is finished
    ]
    for x, base, top, w, crushed, lean in CRIBS:
        crib(x, base, top, w, crushed, lean)
        if not crushed:
            wedge(x + 2, top - 4, w - 4, 1 if x % 2 else -1)
            for _ in range(7):                            # crush dust where it bears
                px(x - 2 + rnd() * (w + 4), top - 6 + rnd() * 3, DIRT_L, 0.6)
    jack(66, 172, 18)
    jack(200, 172, 18)
    jack(316, 172, 20)
    for _ in range(30):                                   # rock dust standing in the room
        disc(16 + rnd() * 368, 90 + rnd() * 80, 1 + rnd() * 3, (150, 146, 138), 0.10)
    rubble(300, 158, 388, 171, 60, (ROCK_M, ROCK_D, DIRT))
    scrap_pile(352, 171, 34, 16, (ROCK_M, ROCK_D, WOOD_D, DIRT))
    for lx in (60, 142, 262):
        lamp(lx, 78, drop=6, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.24)
    plank(14, 120, 120, 122, 2)                           # staging between two cribs
    plank(160, 118, 250, 116, 2)
    catwalk(120, 162, 120, drop=10)
    ladder(140, 122, 170, w=4, step=7)
    player(120, 108)
    binny(134, 100)
    tk_beam(126, 112, 158, 104)
    rect(152, 100, 168, 106, WOOD)                        # a crib timber pulled out
    rect(152, 100, 168, 100, WOOD_L)
    humanoid(84, 160, MET_L, GREEN, face_right=False)     # crew re-wedging number two
    humanoid(214, 160, DIRT_L, RED, face_right=False)
    humanoid(268, 160, DIRT_L, DIRT_L)
    ragdoll(320, 152, RED_L)
    tracer(216, 164, 190, 166)
    crate(46, 164); crate(56, 163, 7, False)
    barrel(180, 165, WOOD, WOOD_L, MET_L); barrel(188, 165, WOOD, WOOD_L, MET_L)
    for _ in range(22):                                   # off-cuts and chocks underfoot
        rect(20 + rnd() * 340, 168 + rnd() * 4, 24 + rnd() * 340, 169 + rnd() * 4, WOOD_D)

    # ── 4  sub-drift under the floor ───────────────────────────────────────
    floor_slab(16, 236, 210, 5, DIRT_D, DIRT)
    rock_teeth(20, 232, 194, 10)
    rails(18, 234, 208)
    cart(70, 199)
    plank(18, 194, 234, 194, 2)
    for pxx in (30, 108, 186):                            # timber under the sub-drift too
        beam(pxx, 195, 210, 2, WOOD_D, WOOD)
        rect(pxx - 3, 195, pxx + 5, 196, WOOD_L)
    humanoid(140, 198, MET_L, DIRT_L, face_right=False)
    lamp(96, 194, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=18, strength=0.22)
    lamp(198, 194, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=18, strength=0.22)
    binny(212, 198)

    # ── 5  exit adit ──────────────────────────────────────────────────────
    floor_slab(250, 392, 210, 5, DIRT_D, DIRT)
    rock_teeth(254, 388, 192, 8)
    rails(252, 388, 208)
    plank(252, 192, 390, 194, 2)
    door(352, 184, 26, 26)
    glow(365, 197, 20, PALE_G, 0.16)
    lamp(290, 192, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=18, strength=0.22)

    vignette()
    return save(out_path("LevelConcept_Cribworks.png"))


if __name__ == "__main__":
    build()
