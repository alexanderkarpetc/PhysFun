"""Concept 17 - THE HOLLOW COLUMN.

The vertical one, and nothing but rock around it: a single hoist shaft bored through
the whole sheet, with galleries hanging off it at four heights. The shaft is the level's
only fast route down and it is full of mass that is already moving - a cage on a rope,
a counterweight going the other way, and whatever the loading belt has just pushed over
the edge.

Read it top to bottom: everything that leaves a gallery ends up on the heap at the
bottom, sooner or later, and so does the player.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SX0, SX1 = 168, 232        # the shaft's walls, referenced by half the scene
LAMP_TINT = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def rock_teeth(x0, x1, y, n=12, c=ROCK_M, tip=ROCK_L):
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 3 + int(rnd() * 7)
        for k in range(ln):
            half = max((ln - k) // 4, 0)
            rect(x - half, y + k, x + half, y + k, c if k < ln - 1 else tip)


def shaft_lining(x0, x1, y0, y1, ring_step=23):
    """Steel-lined bore: side plates, ring frames, and a lit inner edge so the drop
    still reads as depth rather than as a black stripe."""
    rect(x0, y0, x0 + 2, y1, MET_D)
    rect(x1 - 2, y0, x1, y1, MET_D)
    rect(x0 + 2, y0, x0 + 2, y1, MET_L, 0.7)
    rect(x1 - 2, y0, x1 - 2, y1, MET, 0.7)
    for y in range(int(y0) + 8, int(y1), ring_step):     # ring frames, not full floors
        for xs in (x0, x1 - 13):
            rect(xs, y, xs + 13, y + 1, MET_D)
            rect(xs, y, xs + 13, y, MET, 0.8)
        rect(x0 + 13, y, x1 - 13, y, MET_D, 0.35)
    for y in range(int(y0), int(y1), 5):                 # guide timbers
        px(x0 + 6, y, WOOD_D)
        px(x1 - 6, y, WOOD_D)


def rope(x, y0, y1, c=MET_L):
    for y in range(int(y0), int(y1)):
        px(x, y, c if y % 3 else MET_D)


def cage(x, y, w=22, h=16, riders=True):
    rect(x, y, x + w, y + h, MET)
    frame(x, y, x + w, y + h, MET_XL)
    rect(x + 2, y + 2, x + w - 2, y + h - 2, (28, 32, 38))
    for gx in range(int(x) + 3, int(x + w) - 2, 3):      # mesh sides
        rect(gx, y + 2, gx, y + h - 2, MET_L, 0.6)
    rect(x - 2, y - 3, x + w + 2, y - 1, MET_D)          # bonnet
    rect(x - 2, y - 3, x + w + 2, y - 3, MET_L)
    if riders:
        player(x + 3, y + 3)
        humanoid(x + 12, y + 4, DIRT_L, RED, face_right=False)


def counterweight(x, y, w=12, h=22):
    rect(x, y, x + w, y + h, MET_D)
    rect(x, y, x, y + h, MET_L)
    rect(x, y, x + w, y, MET_L)
    for i in range(1, 4):                                # stacked slabs
        rect(x, y + h * i // 4, x + w, y + h * i // 4, MET, 0.9)
    for i in range(5):                                   # motion streaks upward
        px(x + 2 + i * 2, y - 4 - i * 3, MET_L, 0.4)


def winch(cx, cy, r=13):
    """Drum, brake band and gear train. The one machine the whole shaft hangs on."""
    disc(cx, cy, r, MET)
    ring(cx, cy, r, MET_XL)
    for i in range(6):                                   # rope courses on the drum
        ring(cx, cy, r - 2 - i * 2, MET_D)
    disc(cx, cy, 3, MET_D)
    gear(cx + r + 9, cy + 4, 8, teeth=9)
    gear(cx + r + 22, cy - 4, 6, teeth=7)
    rect(cx - r - 4, cy + r + 1, cx + r + 4, cy + r + 4, MET_D)   # bed
    rect(cx - r - 4, cy + r + 1, cx + r + 4, cy + r + 1, MET_L)
    for lx in (cx - r - 2, cx + r):                      # brake linkage
        rect(lx, cy + r - 2, lx + 1, cy + r + 1, MET_L)
    sparks(cx + r + 9, cy + 4, 8, 12)


def broken_catwalk(x0, x1, y, break_at=None):
    """Crossing that used to reach the shaft. Where it stops, the drop starts."""
    for x in range(int(x0), int(x1) + 1):
        if break_at and break_at[0] <= x <= break_at[1]:
            continue
        px(x, y, MET_L)
        px(x, y + 1, MET_D)
    for x in range(int(x0) + 4, int(x1) - 2, 16):
        if break_at and break_at[0] <= x <= break_at[1]:
            continue
        rect(x, y + 2, x, y + 8, MET_D)
    if break_at:                                          # torn plate, hanging
        line(break_at[0] - 1, y, break_at[0] + 4, y + 6, MET_D)
        line(break_at[1] + 1, y, break_at[1] - 3, y + 5, MET_D)


def pit_prop(x, y0, y1, cracked=False, gone=False):
    if gone:
        rect(x, y1 - 4, x + 3, y1, WOOD_D)
        for i in range(6):
            px(x + int(rnd() * 4), y1 - 6 - int(rnd() * 4), WOOD_D)
        return
    beam(x, y0, y1)
    rect(x - 3, y0, x + 6, y0 + 1, WOOD_L)
    if cracked:
        for k in range(5):
            px(x + (k % 3), y0 + 6 + k * 2, CHAR)


def sag(x0, x1, y, depth=4):
    for x in range(int(x0), int(x1) + 1):
        t = (x - x0) / max(x1 - x0, 1)
        d = int(depth * (1 - (2 * t - 1) ** 2))
        rect(x, y, x, y + d, ROCK_M)
        px(x, y + d, ROCK_L)
    for _ in range(12):
        cx = x0 + rnd() * (x1 - x0)
        cy = y - 2 - rnd() * 8
        line(cx, cy, cx + 3 - rnd() * 6, cy - 3, ROCK_D, 0.8)


def falling_crate(x, y, s=8, wood=True):
    crate(x, y, s, wood)
    for i in range(4):
        px(x + 1 + int(rnd() * s), y - 4 - i * 3, DIRT_L, 0.45)


def falling_chunk(x, y, s=4):
    rect(x, y, x + s, y + s - 1, ROCK_M)
    rect(x, y, x + s, y, ROCK_L)
    for i in range(3):
        px(x + int(rnd() * s), y - 3 - i * 2, DIRT_L, 0.5)


def build():
    new_canvas(400, 225, seed=51703)
    cw, ch = canvas_size()

    # ── rock everywhere; the sheet never leaves it ──────────────────────────
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=24)
    for _ in range(44):
        rect(rnd() * cw, rnd() * 16, rnd() * cw + 6, rnd() * 16 + 1, ROCK_D, 0.5)

    ROOMS = [
        (SX0, 4, SX1, 220),     # the shaft
        (10, 18, 162, 60),      # loading gallery
        (10, 82, 158, 124),     # timbered gallery
        (12, 152, 156, 210),    # the heap at the bottom
        (240, 12, 392, 68),     # winch house
        (244, 88, 392, 134),    # belt landing
        (250, 160, 392, 208),   # exit adit
        (156, 30, 172, 52),     # gallery -> shaft
        (150, 96, 172, 118),    # gallery -> shaft
        (150, 178, 172, 202),   # heap -> shaft
        (228, 30, 246, 56),     # shaft -> winch house
        (228, 100, 250, 126),   # shaft -> landing
        (228, 176, 254, 200),   # shaft -> adit
    ]
    carve_all(ROOMS)

    # ── 1  the shaft itself ────────────────────────────────────────────────
    shaft_lining(SX0, SX1, 4, 220)
    rope(178, 4, 62)
    rope(180, 4, 62)
    rope(220, 4, 118)
    cage(172, 62, 22, 16)
    counterweight(214, 118)
    for y in range(20, 216, 26):                          # shaft lamps down the wall
        lamp(SX0 + 5, y, drop=2, bulb=LAMP_TINT, tint=LAMP_TINT, r=16, strength=0.22)
    falling_crate(196, 96, 8)
    falling_crate(188, 148, 7, False)
    for _ in range(9):
        falling_chunk(SX0 + 6 + rnd() * 50, 90 + rnd() * 110, 2)
    binny(200, 78)
    for cx in (188, 226):                                 # slack chain down the bore
        chain(cx, 6, 218)
    for _ in range(14):                                   # loose cargo mid-fall
        px(SX0 + 6 + rnd() * 52, 20 + rnd() * 190, pick([MET_L, WOOD_L, DIRT_L]), 0.8)
    for _ in range(18):                                   # dust hanging in the bore
        disc(SX0 + 4 + rnd() * 56, 8 + rnd() * 208, 1 + rnd() * 2.5, (140, 138, 132), 0.10)

    # ── 2  loading gallery: the belt that feeds the drop ───────────────────
    floor_slab(10, 168, 54, 4, ROCK_D, ROCK_L)
    rock_teeth(14, 158, 20, 12)
    conveyor(16, 178, 40, direction=1)                    # tips its load into the bore
    for _ in range(20):
        px(18 + rnd() * 136, 37 + rnd() * 3, pick([MET_L, DIRT_L, WOOD_L]))
    crate(120, 32); crate(130, 31, 7, False)
    pipe_run(12, 156, 22)
    scrap_pile(16, 53, 30, 9)
    humanoid(58, 42, MET_L, GREEN, face_right=False)
    humanoid(104, 42, DIRT_L, DIRT_L)
    barrel(88, 47); barrel(96, 47)
    lamp(40, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    lamp(132, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    ladder(148, 44, 54)

    # ── 3  timbered gallery, catwalk torn off at the shaft ─────────────────
    floor_slab(10, 162, 118, 5, DIRT_D, DIRT)
    sag(58, 116, 84, 5)
    for pxx, cracked, gone in ((16, False, False), (44, True, False), (72, False, True),
                               (100, True, False), (132, False, False)):
        pit_prop(pxx, 85, 118, cracked, gone)
    plank(12, 84, 156, 84, 2)
    broken_catwalk(96, 170, 104, break_at=(136, 152))
    rails(14, 148, 116, broken=(64, 82))
    cart(24, 107)
    humanoid(84, 106, DIRT_L, RED, face_right=False)
    humanoid(118, 106, MET_L, WOOD_L, face_right=False)
    tk_beam(122, 110, 148, 100)
    rect(144, 96, 154, 102, ROCK_M)
    rect(144, 96, 154, 96, ROCK_L)
    falling_chunk(70, 92, 6)
    rubble(58, 112, 116, 117, 36, (ROCK_M, ROCK_D, DIRT))
    for lx in (32, 108):
        lamp(lx, 85, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)

    # ── 4  winch house ────────────────────────────────────────────────────
    floor_slab(240, 392, 62, 4, ROCK_D, ROCK_L)
    rock_teeth(244, 388, 14, 12)
    winch(300, 40, 13)
    line(268, 34, 234, 22, MET_L)                         # rope out to the head sheave
    line(268, 35, 234, 23, MET_D)
    disc(232, 20, 4, MET)
    ring(232, 20, 4, MET_XL)
    pipe_run(242, 388, 16)
    cable(244, 24, 300, 26, 4)
    humanoid(258, 50, MET_L, DIRT_L)                      # winchman
    crate(356, 54); crate(366, 53, 7, False)
    scrap_pile(340, 61, 34, 8)
    lamp(268, 17, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.28)
    lamp(360, 17, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)

    # ── 5  belt landing ───────────────────────────────────────────────────
    floor_slab(244, 392, 128, 4, ROCK_D, ROCK_L)
    rock_teeth(248, 388, 90, 12)
    conveyor(252, 386, 112, direction=-1)
    for _ in range(18):
        px(254 + rnd() * 128, 109 + rnd() * 3, pick([DIRT_L, MET_L, GREEN_L]))
    gear(268, 122, 8, teeth=8)                            # tail pulley, unguarded
    grate(300, 340, 124)
    plank(246, 92, 388, 94, 2)
    crate(320, 120); crate(330, 119, 7, False)
    humanoid(352, 116, DIRT_L, GREEN, face_right=False)
    ragdoll(290, 116)
    lamp(300, 93, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    for cx in (262, 356):
        chain(cx, 94, 106)

    # ── 6  the heap: everything the shaft has ever dropped ────────────────
    floor_slab(12, 168, 204, 5, DIRT_D, DIRT)
    rock_teeth(16, 152, 154, 12)
    scrap_pile(16, 203, 132, 26, (MET_D, MET, WOOD_D, DIRT, ROCK_M, MET_L))
    for i in range(7):                                    # recognisable wreckage in it
        crate(24 + i * 18, 190 - int(rnd() * 6), 7, i % 2 == 0)
    cart(96, 192, tipped=True)
    ragdoll(64, 184)
    ragdoll(126, 188, RED_L)
    rubble(14, 196, 166, 204, 60, (MET_D, DIRT, ROCK_M))
    for pxx in (20, 140):
        pit_prop(pxx, 158, 204, cracked=True)
    plank(14, 157, 154, 157, 2)
    lamp(78, 158, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=24, strength=0.24)
    glow(90, 196, 40, LAMP_TINT, 0.10)

    # ── 7  exit adit ──────────────────────────────────────────────────────
    floor_slab(250, 392, 202, 5, DIRT_D, DIRT)
    rock_teeth(254, 388, 162, 10)
    rails(252, 388, 200)
    cart(272, 191)
    plank(252, 176, 390, 178, 2)
    for pxx in (266, 310, 350):
        pit_prop(pxx, 178, 202)
    door(356, 174, 26, 28)
    glow(369, 188, 20, PALE_G, 0.16)
    spikes(300, 178, 200, 1)
    lamp(288, 163, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)

    vignette()
    return save(out_path("LevelConcept_HollowColumn.png"))


if __name__ == "__main__":
    build()
