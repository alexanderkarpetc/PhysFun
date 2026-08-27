"""Concept 15 - THE QUARRY TEETH.

A crusher plant cut into the rock, no surface at all: the sheet starts in stone and
ends in stone. Rock arrives on belts, falls down chutes into meshing grinder wheels,
and leaves as ore on the haulage below. Every hazard here is one the engine already
runs — Hazards/Conveyor drags mass sideways, Hazards/Grinder eats whatever the belt
hands it, and the whole west end is held up by pit props the support pass will drop.

Unlabelled by request: the art has to carry it, so the machinery reads by silhouette
(circles chew, chevrons drag, timber holds) rather than by callout.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

LAMP_TINT = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def rock_teeth(x0, x1, y, n=12, c=ROCK_M, tip=ROCK_L):
    """Stone hanging off a ceiling. Cheap, and it kills the flat carve line."""
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 3 + int(rnd() * 7)
        for k in range(ln):
            half = max((ln - k) // 4, 0)
            rect(x - half, y + k, x + half, y + k, c if k < ln - 1 else tip)


def chute(x, y0, y1, w=14, tilt=0):
    """Sloped plate pair that feeds the wheels. Tilt shifts the bottom sideways."""
    for i in range(int(y1 - y0)):
        t = i / max(y1 - y0, 1)
        sx = x + tilt * t
        rect(sx, y0 + i, sx + 1, y0 + i, MET_D)
        rect(sx + w, y0 + i, sx + w + 1, y0 + i, MET_D)
        px(sx, y0 + i, MET_L)
    for k in range(6):                                   # rock queued in the throat
        px(x + 3 + rnd() * (w - 5) + tilt * rnd(), y0 + rnd() * (y1 - y0),
           pick([ROCK_L, ROCK_M, DIRT_L]))


def crusher(cx, cy, r=13):
    """Two wheels turning into each other, with the bed plate and the dust they make."""
    gear(cx - r - 1, cy, r, teeth=10)
    gear(cx + r + 1, cy, r, teeth=10)
    rect(cx - r * 2 - 6, cy + r + 2, cx + r * 2 + 6, cy + r + 4, MET_D)
    rect(cx - r * 2 - 6, cy + r + 2, cx + r * 2 + 6, cy + r + 2, MET_L)
    for _ in range(26):                                  # crushed spray under the bite
        px(cx + (rnd() - 0.5) * r * 3, cy + r + 5 + rnd() * 6,
           pick([ROCK_L, DIRT_L, ROCK_M]), 0.8)
    for _ in range(30):                                  # dust cloud over it
        disc(cx + (rnd() - 0.5) * r * 4, cy - r - rnd() * 12, 1 + rnd() * 2.5,
             (150, 146, 138), 0.12)
    sparks(cx, cy - 2, 10, 14)


def screen_deck(x0, x1, y, decks=3):
    """Sizing screens: stacked grates, fines falling through each one."""
    for d in range(decks):
        yy = y + d * 7
        grate(x0 + d * 4, x1 - d * 4, yy)
        for _ in range(10):
            px(x0 + d * 4 + rnd() * (x1 - x0 - d * 8), yy + 2 + rnd() * 4,
               pick([DIRT_L, ROCK_L]), 0.7)
    rect(x0 - 2, y, x0 - 2, y + decks * 7, MET_D)
    rect(x1 + 2, y, x1 + 2, y + decks * 7, MET_D)


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
    for _ in range(14):
        cx = x0 + rnd() * (x1 - x0)
        cy = y - 2 - rnd() * 8
        line(cx, cy, cx + 3 - rnd() * 6, cy - 3, ROCK_D, 0.8)


def falling_chunk(x, y, s=4):
    rect(x, y, x + s, y + s - 1, ROCK_M)
    rect(x, y, x + s, y, ROCK_L)
    for i in range(4):
        px(x + int(rnd() * s), y - 3 - i * 2, DIRT_L, 0.5)


def ore_vein(x0, y0, x1, y1, n=30, colors=(GREEN_L, PALE_G, MET_L)):
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        y = y0 + rnd() * (y1 - y0)
        rect(x, y, x + 1 + rnd() * 2, y, pick(list(colors)), 0.9)


def drive_belt(x0, y0, x1, y1):
    """Flat leather belt between two pulleys - what makes the wheels look driven."""
    line(x0, y0, x1, y1, WOOD_D)
    line(x0, y0 + 1, x1, y1 + 1, WOOD)
    disc(x0, y0, 3, MET)
    ring(x0, y0, 3, MET_XL)
    disc(x1, y1, 3, MET)
    ring(x1, y1, 3, MET_XL)


def build():
    new_canvas(400, 225, seed=51501)

    # ── solid rock, edge to edge - no surface on this sheet ──────────────────
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=22)
    for _ in range(40):                                  # deeper mottle up top
        rect(rnd() * W, rnd() * 20, rnd() * W + 6, rnd() * 20 + 1, ROCK_D, 0.5)

    ROOMS = [
        (6, 14, 168, 52),       # feed gallery
        (24, 62, 208, 144),     # crusher hall
        (214, 26, 392, 104),    # screen house
        (196, 152, 392, 202),   # haulage out
        (6, 152, 178, 208),     # timbered west end
        (150, 16, 176, 70),     # feed chute shaft
        (200, 96, 232, 160),    # screen -> haulage drop
        (168, 132, 202, 160),   # hall -> haulage
        (8, 138, 40, 160),      # hall -> west end
        (330, 92, 366, 158),    # ore pass
    ]
    carve_all(ROOMS)

    # ── 1  feed gallery: rock comes in on the belt ──────────────────────────
    floor_slab(6, 168, 46, 4, ROCK_D, ROCK_L)
    rock_teeth(10, 164, 16, 14)
    conveyor(10, 148, 36, direction=1)
    for _ in range(34):                                  # feed on the belt
        px(12 + rnd() * 132, 33 + rnd() * 3, pick([ROCK_L, ROCK_M, DIRT_L]))
    cable(8, 20, 90, 22, 5)
    cable(90, 22, 166, 19, 5)
    lamp(44, 17, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.28)
    lamp(122, 17, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.28)
    humanoid(24, 34, MET_L, DIRT_L)
    crate(96, 38); crate(106, 38, 7, False)
    ore_vein(6, 24, 60, 44, 18)

    # ── 2  the chute, and the teeth at the bottom of it ─────────────────────
    chute(154, 46, 66, 14, tilt=-6)
    for _ in range(10):
        falling_chunk(150 - rnd() * 8, 50 + rnd() * 14, 2 + rnd() * 2)

    floor_slab(24, 208, 138, 5, ROCK_D, ROCK_L)
    rock_teeth(28, 204, 64, 16)
    crusher(120, 96, 13)
    crusher(64, 116, 8)
    drive_belt(96, 82, 148, 74)
    drive_belt(50, 104, 96, 86)
    catwalk(28, 110, 78, drop=9)
    catwalk(150, 206, 78, drop=9)
    ladder(112, 80, 118)
    ladder(190, 80, 136)
    for cx in (36, 148, 200):                            # hoist chains off the roof
        chain(cx, 66, 78)
    for _ in range(22):                                  # airborne dust in the hall
        disc(30 + rnd() * 174, 84 + rnd() * 50, 1 + rnd() * 3, (140, 138, 132), 0.10)
    scrap_pile(160, 137, 44, 12, (ROCK_M, ROCK_D, DIRT, MET_D))
    barrel(30, 130, MET, MET_L, MET_XL)
    barrel(38, 130, MET, MET_L, MET_XL)
    crate(48, 130); crate(58, 130, 7, False)
    humanoid(34, 68, DIRT_L, RED)                        # crew on the catwalk
    humanoid(88, 68, MET_L, GREEN, face_right=False)
    player(140, 126)
    binny(154, 118)
    tk_beam(146, 130, 172, 122)                          # dragging a rock clear
    rect(170, 118, 178, 126, ROCK_M)
    rect(170, 118, 178, 118, ROCK_L)
    rubble(26, 133, 206, 142, 60, (ROCK_M, ROCK_D, DIRT))
    for lx in (46, 176):
        lamp(lx, 64, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=24, strength=0.26)
    ragdoll(96, 128)

    # ── 3  screen house ────────────────────────────────────────────────────
    floor_slab(214, 392, 98, 4, ROCK_D, ROCK_L)
    rock_teeth(218, 388, 28, 16)
    screen_deck(240, 320, 44, 3)
    conveyor(236, 330, 78, direction=1)
    for _ in range(30):
        px(238 + rnd() * 90, 75 + rnd() * 3, pick([DIRT_L, ROCK_L, GREEN_L]))
    gear(348, 60, 11, teeth=9)                           # drive train up the east wall
    gear(374, 78, 8, teeth=7)
    drive_belt(348, 60, 374, 78)
    pipe_run(216, 388, 32)
    scrap_pile(222, 97, 28, 8, (MET_D, MET, DIRT, ROCK_M))
    crate(300, 90); crate(310, 90, 7, False)
    humanoid(268, 86, MET_L, DIRT_L, face_right=False)
    humanoid(332, 86, DIRT_L, GREEN)
    for cx in (244, 316):                                # screen hangers
        chain(cx, 30, 44)
    catwalk(216, 238, 62, drop=8)
    for _ in range(16):
        disc(220 + rnd() * 168, 46 + rnd() * 46, 1 + rnd() * 2.5, (140, 138, 132), 0.09)
    scrap_pile(352, 97, 36, 10, (ROCK_M, DIRT, MET_D, MET))
    lamp(252, 30, drop=6, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.28)
    lamp(344, 30, drop=6, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.28)
    ore_vein(216, 40, 240, 94, 14)

    # ── 4  ore pass down to the haulage ────────────────────────────────────
    chute(334, 100, 152, 26, tilt=4)
    for _ in range(8):
        falling_chunk(340 + rnd() * 14, 108 + rnd() * 34, 2)

    # ── 5  haulage out ─────────────────────────────────────────────────────
    floor_slab(196, 392, 196, 5, ROCK_D, ROCK_L)
    rock_teeth(200, 388, 154, 12)
    rails(202, 388, 194, broken=(300, 316))
    cart(220, 185)
    cart(268, 185, tipped=True)
    gear(324, 192, 9, teeth=8)                           # grinder straddling the track
    spikes(348, 160, 194, 1)
    plank(198, 156, 388, 158, 2)
    for pxx in (210, 250, 292, 356):
        pit_prop(pxx, 158, 196, cracked=(pxx == 292))
    humanoid(244, 184, MET_L, RED, face_right=False)
    lamp(232, 158, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    lamp(340, 158, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    door(366, 168, 24, 26)
    glow(378, 181, 20, PALE_G, 0.16)
    rubble(298, 190, 322, 195, 24, (ROCK_M, DIRT, MET_D))

    # ── 6  timbered west end - the part that is going to come down ─────────
    floor_slab(6, 178, 202, 5, DIRT_D, DIRT)
    sag(70, 132, 156, 6)
    for pxx, cracked, gone in ((14, False, False), (40, True, False), (66, True, False),
                               (96, False, True), (126, True, False), (156, False, False)):
        pit_prop(pxx, 157, 202, cracked, gone)
    plank(8, 156, 176, 156, 2)
    rails(10, 174, 200, broken=(88, 108))
    cart(30, 191)
    ore_vein(10, 162, 60, 198, 20)
    humanoid(78, 190, DIRT_L, WOOD_L)                    # crew under the sag
    humanoid(112, 190, MET_L, RED, face_right=False)
    tracer(110, 194, 84, 196)
    falling_chunk(94, 164, 6)
    falling_chunk(104, 174, 4)
    rubble(70, 196, 132, 201, 40, (ROCK_M, ROCK_D, DIRT))
    lamp(52, 157, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    lamp(146, 157, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    binny(20, 186)

    vignette()
    return save(out_path("LevelConcept_QuarryTeeth.png"))


if __name__ == "__main__":
    build()
