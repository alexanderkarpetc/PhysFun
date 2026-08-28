"""Concept 18 - THE PENDULUM WORKS.

A hall where the mine broke rock by swinging weight at it. Every hazard is stored
kinetic energy on a chain: the pivots are still driven from the gear loft, the balls
still swing, and the walls they have already been through are the level's geometry.

Nothing here needs a trigger. The room is a clock, and the player has to cross it
between ticks - or cut a chain and spend the mass on the wall of their choosing.

No surface, no labels: the arcs do the talking.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

LAMP_TINT = (255, 214, 140)
STEEL = (168, 176, 190)


# ── local props ─────────────────────────────────────────────────────────────
def rock_teeth(x0, x1, y, n=12, c=ROCK_M, tip=ROCK_L):
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 3 + int(rnd() * 7)
        for k in range(ln):
            half = max((ln - k) // 4, 0)
            rect(x - half, y + k, x + half, y + k, c if k < ln - 1 else tip)


def pivot(x, y, w=12):
    """Trunnion bearing in the roof steel - the thing a chain is worth cutting at."""
    rect(x - w // 2, y - 3, x + w // 2, y, MET_D)
    rect(x - w // 2, y - 3, x + w // 2, y - 3, MET_L)
    disc(x, y + 1, 3, MET)
    ring(x, y + 1, 3, MET_XL)
    px(x, y + 1, INK)


def pendulum(x, y, length, angle, r=8, swept=1, cut=False):
    """Weight on a chain, drawn at `angle` from straight down, with the arc it owns.

    `swept` is the half-width of the swing in radians — the dotted arc is the part of
    the room the player cannot be standing in. `cut` drops the chain slack instead.
    """
    for t in range(30):                                  # the arc it owns, as dots
        aa = -swept + 2 * swept * t / 29
        px(x + math.sin(aa) * length, y + math.cos(aa) * length, STEEL, 0.22)
    for a in (-swept, swept):                            # ticks at the ends of the swing
        gx = x + math.sin(a) * length
        gy = y + math.cos(a) * length
        line(gx + math.sin(a) * 3, gy + math.cos(a) * 3,
             gx + math.sin(a) * (r + 2), gy + math.cos(a) * (r + 2), STEEL, 0.30)

    bx = x + math.sin(angle) * length
    by = y + math.cos(angle) * length
    if cut:
        for i in range(int(length) + 8):                 # chain gone slack, folded up
            t = i / (length + 8)
            px(x + math.sin(t * 3.4) * 9, y + i, MET_L if i % 3 else MET_D, 0.9)
        by = y + length + 8
        bx = x + math.sin(3.4) * 9
    else:
        steps = int(length)
        for i in range(steps):
            t = i / steps
            px(x + math.sin(angle) * length * t, y + math.cos(angle) * length * t,
               MET_L if i % 3 else MET_D)
            px(x + math.sin(angle) * length * t + 1,
               y + math.cos(angle) * length * t, MET_D, 0.6)

    disc(bx, by, r, MET)                                 # the weight
    disc(bx, by, r - 2, MET_D)
    ring(bx, by, r, MET_XL)
    disc(bx - r * 0.35, by - r * 0.35, r * 0.3, MET_L, 0.8)
    for i in range(int(r)):                              # motion smear off the leading face
        px(bx - math.sin(angle) * (r + 2 + i), by - 2 + rnd() * 4, STEEL, 0.25)
    return bx, by


def impact_crater(cx, y, w=30, depth=8):
    """Where a weight has already been. Terrain simply is not there any more."""
    for x in range(int(cx - w / 2), int(cx + w / 2) + 1):
        t = (x - (cx - w / 2)) / max(w, 1)
        d = int(depth * (1 - (2 * t - 1) ** 2))
        rect(x, y - d, x, y, CAVE)
        px(x, y - d, ROCK_L, 0.7)
    for _ in range(22):
        px(cx - w / 2 + rnd() * w, y - depth - rnd() * 6, pick([ROCK_M, ROCK_D, DIRT_L]), 0.8)


def smashed_wall(x, y0, y1, side=1):
    """A wall the works have punched through: stubs top and bottom, nothing between."""
    for y in range(int(y0), int(y1)):
        if 0.3 < (y - y0) / max(y1 - y0, 1) < 0.75:
            continue
        rect(x, y, x + 5 * side, y, ROCK_M if chance(0.6) else ROCK_D)
    for _ in range(20):
        px(x + side * rnd() * 16, y0 + (y1 - y0) * (0.3 + rnd() * 0.45),
           pick([ROCK_M, ROCK_D]), 0.7)


def drive_wheel(cx, cy, r=12):
    gear(cx, cy, r, teeth=11)
    for i in range(3):
        ring(cx, cy, r - 3 - i * 3, MET_D)


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


def build():
    new_canvas(400, 225, seed=51804)
    cw, ch = canvas_size()

    # ── rock, edge to edge ─────────────────────────────────────────────────
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=22)
    for _ in range(42):
        rect(rnd() * cw, rnd() * 16, rnd() * cw + 6, rnd() * 16 + 1, ROCK_D, 0.5)

    ROOMS = [
        (18, 34, 252, 152),     # the swing hall
        (262, 16, 392, 74),     # gear loft
        (262, 96, 392, 154),    # gallery the works broke into
        (14, 172, 302, 214),    # lower workings
        (312, 168, 392, 212),   # exit adit
        (246, 40, 268, 64),     # hall -> loft
        (246, 112, 270, 138),   # hall -> broken gallery
        (60, 148, 88, 176),     # hall -> lower workings
        (222, 148, 252, 176),   # hall -> lower workings, east
        (296, 150, 322, 180),   # gallery -> adit
    ]
    carve_all(ROOMS)

    # ── 1  the hall: roof steel, pivots, three weights ─────────────────────
    floor_slab(18, 252, 146, 5, ROCK_D, ROCK_L)
    rock_teeth(22, 248, 36, 14)
    rect(20, 40, 250, 41, MET_D)                          # roof girder the pivots hang on
    rect(20, 40, 250, 40, MET_L)
    for gx in range(28, 248, 24):                         # girder web
        line(gx, 42, gx + 12, 48, MET_D, 0.7)
        line(gx + 12, 42, gx, 48, MET_D, 0.7)
    for pvx in (72, 148, 214):
        pivot(pvx, 42)
    pendulum(72, 44, 74, 0.45, 9, swept=0.6)
    pendulum(148, 44, 86, 0.42, 11, swept=0.5)
    pendulum(214, 44, 62, 0.0, 7, swept=0.7, cut=True)    # this one is already down
    impact_crater(104, 146, 34, 9)
    impact_crater(190, 146, 26, 7)
    catwalk(18, 62, 108, drop=9)
    ladder(52, 108, 146)
    player(24, 96)
    binny(36, 88)
    tk_beam(30, 100, 62, 92)
    rect(56, 88, 68, 94, ROCK_M)                          # a rock held as a shield
    rect(56, 88, 68, 88, ROCK_L)
    humanoid(120, 134, MET_L, RED, face_right=False)      # crew keeping to the dead zones
    humanoid(168, 134, DIRT_L, GREEN, face_right=False)
    ragdoll(146, 128)
    rubble(90, 138, 210, 145, 54, (ROCK_M, ROCK_D, MET_D))
    scrap_pile(226, 145, 26, 10, (MET_D, MET, ROCK_M, DIRT))
    for lx in (40, 128, 236):
        lamp(lx, 42, drop=6, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.24)
    for _ in range(20):                                   # rock dust the swings kick up
        disc(24 + rnd() * 224, 100 + rnd() * 44, 1 + rnd() * 3, (140, 138, 132), 0.10)

    # ── 2  gear loft that still drives it all ──────────────────────────────
    floor_slab(262, 392, 66, 4, ROCK_D, ROCK_L)
    rock_teeth(266, 388, 18, 12)
    drive_wheel(300, 44, 12)
    drive_wheel(340, 34, 8)
    gear(366, 48, 9, teeth=9)
    line(300, 44, 340, 34, WOOD_D)                        # belt train
    line(300, 45, 340, 35, WOOD)
    line(340, 34, 366, 48, WOOD_D)
    for cx in (272, 286):                                 # cables through the wall to the pivots
        line(cx, 56, 246, 46, MET_L, 0.8)
    pipe_run(264, 388, 20)
    humanoid(316, 54, MET_L, DIRT_L)
    crate(376, 58)
    lamp(280, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.28)
    lamp(360, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    sparks(340, 34, 12, 14)

    # ── 3  the gallery a weight opened by accident ─────────────────────────
    smashed_wall(252, 100, 150, 1)
    floor_slab(262, 392, 148, 5, ROCK_D, ROCK_L)
    rock_teeth(266, 388, 98, 12)
    impact_crater(288, 148, 30, 10)
    for _ in range(40):                                   # the wall, now scattered
        px(268 + rnd() * 70, 128 + rnd() * 20, pick([ROCK_M, ROCK_D, DIRT]), 0.85)
    plank(264, 100, 390, 102, 2)
    for pxx in (312, 348, 380):
        pit_prop(pxx, 102, 148, cracked=(pxx == 348))
    rails(300, 388, 146, broken=(330, 344))
    cart(356, 137, tipped=True)
    ragdoll(300, 138, RED_L)
    humanoid(332, 136, DIRT_L, RED, face_right=False)
    tracer(334, 140, 300, 142)
    lamp(324, 102, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    lamp(376, 102, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.22)
    binny(280, 136)

    # ── 4  lower workings, where everything the hall breaks ends up ────────
    floor_slab(14, 302, 208, 5, DIRT_D, DIRT)
    rock_teeth(18, 298, 174, 14)
    plank(16, 176, 300, 176, 2)
    for pxx in (24, 96, 168, 240, 288):
        pit_prop(pxx, 177, 208, cracked=(pxx in (96, 240)))
    rails(18, 298, 206, broken=(120, 140))
    cart(48, 197)
    cart(206, 197, tipped=True)
    grate(112, 152, 178)                                  # debris drops through here
    for _ in range(34):
        px(114 + rnd() * 36, 182 + rnd() * 24, pick([ROCK_M, ROCK_D, MET_D]), 0.8)
    scrap_pile(140, 207, 60, 14, (MET_D, MET, ROCK_M, DIRT, WOOD_D))
    humanoid(78, 196, MET_L, GREEN, face_right=False)
    humanoid(262, 196, DIRT_L, RED, face_right=False)
    ragdoll(196, 192)
    for lx in (60, 224):
        lamp(lx, 177, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.24)

    # ── 5  exit adit ──────────────────────────────────────────────────────
    floor_slab(312, 392, 206, 5, DIRT_D, DIRT)
    rock_teeth(316, 388, 170, 8)
    rails(314, 388, 204)
    plank(314, 182, 390, 184, 2)
    for pxx in (326, 366):
        pit_prop(pxx, 184, 206)
    door(354, 178, 26, 28)
    glow(367, 192, 20, PALE_G, 0.16)
    lamp(330, 172, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)

    vignette()
    return save(out_path("LevelConcept_PendulumWorks.png"))


if __name__ == "__main__":
    build()
