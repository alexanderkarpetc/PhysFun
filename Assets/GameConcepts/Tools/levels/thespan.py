"""Concept 29 - THE SPAN.

The hollow column turned on its side. One natural void the width of the sheet, two rock
pinnacles left standing in it because they were barren, a timber tower on top of each, and
a ropeway strung wall to wall carrying buckets of ore across the gap.

Everything the player wants is on the far side, and the level offers three ways over: the
buckets, the footbridge slung under them, or the long way round through the wall galleries.
Two of those three are ropes under tension, and there is nothing below them for a hundred
feet but the fan of everything that has already fallen.

No surface, no labels.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

LAMP_TINT = (255, 214, 140)
ORE = (159, 187, 83)
FLOOR = 200                      # the sill of the void


# ── local props ─────────────────────────────────────────────────────────────
def pinnacle(cx, top, base=FLOOR, half_top=9, half_base=26):
    """A column of rock the stope left standing. Tapered, lit down one side, and the
    only thing in the middle of the void that is not hanging from a rope."""
    for y in range(int(top), int(base) + 1):
        t = (y - top) / max(base - top, 1)
        half = int(half_top + (half_base - half_top) * t * t)
        rect(cx - half, y, cx + half, y, ROCK)
        px(cx - half, y, ROCK_L, 0.8)
        px(cx + half, y, ROCK_D)
        for _ in range(2):
            px(cx - half + rnd() * half * 2, y, ROCK_D if chance(0.6) else ROCK_M)
    for _ in range(30):                                    # strata across it
        y = top + rnd() * (base - top)
        t = (y - top) / max(base - top, 1)
        half = int(half_top + (half_base - half_top) * t * t)
        rect(cx - half + rnd() * 4, y, cx + half - rnd() * 6, y, ROCK_D, 0.5)
    rect(cx - half_top - 2, top - 2, cx + half_top + 2, top, ROCK_M)
    rect(cx - half_top - 2, top - 2, cx + half_top + 2, top - 2, ROCK_L)


def tower(cx, base, h=26, w=13):
    """Trestle on top of a pinnacle: legs, cross-braces, a saddle for the cable."""
    for lx in (cx - w // 2, cx + w // 2):
        rect(lx, base - h, lx + 1, base, WOOD)
        px(lx, base - h, WOOD_L)
    for k in range(3):                                     # bracing
        y0 = base - h + k * (h // 3)
        y1 = y0 + h // 3
        line(cx - w // 2, y0, cx + w // 2, y1, WOOD_D)
        line(cx + w // 2, y0, cx - w // 2, y1, WOOD_D)
        rect(cx - w // 2, y1, cx + w // 2, y1, WOOD)
    rect(cx - w // 2 - 3, base - h - 2, cx + w // 2 + 3, base - h, WOOD)
    rect(cx - w // 2 - 3, base - h - 2, cx + w // 2 + 3, base - h - 2, WOOD_L)
    disc(cx, base - h - 4, 3, MET)                         # saddle sheave
    ring(cx, base - h - 4, 3, MET_XL)
    return cx, base - h - 6


def anchor(x, y, side=1):
    """Cable anchor in the wall: a shoe bolted to rock, and the strain showing round it."""
    rect(x, y - 3, x + 6 * side, y + 3, MET_D)
    rect(x, y - 3, x + 6 * side, y - 3, MET_L)
    disc(x + 5 * side, y, 2, MET)
    ring(x + 5 * side, y, 2, MET_XL)
    for k in range(4):
        line(x, y - 3 + k * 2, x - 4 * side, y - 6 + k * 4, MET_D, 0.7)
    for _ in range(8):
        px(x - 6 * side + rnd() * 8 * side, y - 8 + rnd() * 16, ROCK_D, 0.7)


def cable_run(x0, y0, x1, y1, sag=8, c=MET_L):
    """A cable under load: a catenary, drawn as one, because a straight line reads as
    a pipe and the sag is the whole information."""
    pts = []
    steps = max(int(abs(x1 - x0)), 2)
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
        px(x, y, c if i % 4 else MET_D)
        pts.append((x, y))
    return pts


def bucket(pts, t, load=True, falling=False):
    """A bucket on the cable: hanger, carriage wheel, and the ore it is carrying."""
    x, y = pts[int(t * (len(pts) - 1))]
    if falling:
        x, y = x, y + 30 + rnd() * 20
        for i in range(5):
            px(x + 2 + rnd() * 6, y - 10 - i * 4, DIRT_L, 0.4)
    else:
        disc(x, y, 2, MET)                                 # carriage on the rope
        ring(x, y, 2, MET_XL)
        rect(x - 1, y + 2, x, y + 6, MET_D)
    rect(x - 5, y + 6, x + 5, y + 14, MET)
    rect(x - 5, y + 6, x + 5, y + 6, MET_XL)
    rect(x - 5, y + 13, x + 5, y + 14, MET_D)
    rect(x - 4, y + 7, x + 4, y + 8, (58, 46, 34))
    if load:
        for _ in range(7):
            px(x - 3 + rnd() * 7, y + 5 + rnd() * 3, pick([ORE, DIRT_L, ROCK_L]))


def footbridge(x0, y0, x1, y1, sag=14):
    """Planks on two ropes, slung under the ropeway. Sags more than the cable does."""
    top = []
    steps = max(int(abs(x1 - x0)), 2)
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
        top.append((x, y))
    for i, (x, y) in enumerate(top):                       # the walking ropes
        px(x, y, WOOD_L if i % 3 else WOOD_D)
        px(x, y + 1, WOOD_D)
    for i in range(0, len(top), 6):                        # planks
        x, y = top[i]
        rect(x - 2, y - 1, x + 2, y - 1, WOOD)
        px(x - 2, y - 1, WOOD_L)
    for i in range(0, len(top), 18):                       # hand ropes going up
        x, y = top[i]
        for k in range(8):
            px(x, y - 2 - k, WOOD_D if k % 2 else WOOD_L)


def debris_fan(x0, x1, y, h=16):
    """What the void has collected. Reads as depth: you can see where things land."""
    for _ in range((x1 - x0) * 4):
        x = x0 + rnd() * (x1 - x0)
        d = 1 - abs(x - (x0 + x1) / 2) / ((x1 - x0) / 1.6)
        yy = y - rnd() * h * max(d, 0.15)
        px(x, yy, pick([ROCK_M, ROCK_D, DIRT, MET_D, WOOD_D]))
    for _ in range(18):
        x = x0 + rnd() * (x1 - x0)
        rect(x, y - rnd() * 5, x + 2 + rnd() * 6, y - rnd() * 5 + 1, pick([MET_D, WOOD_D]))


def wrecked_bucket(x, y):
    for _ in range(24):
        px(x - 9 + rnd() * 20, y - 7 + rnd() * 9, pick([MET_D, MET, ROCK_M]))
    rect(x - 6, y - 3, x + 4, y, MET_D)
    rect(x - 6, y - 3, x + 4, y - 3, MET)
    for _ in range(10):
        px(x - 12 + rnd() * 26, y - 1, pick([ORE, DIRT_L]))


def gallery(x0, y0, x1, y1, side=1):
    """A wall gallery: floor, roof timber, a landing platform out over the drop."""
    floor_slab(x0, x1, y1 - 4, 4, ROCK_D, ROCK_L)
    rock_teeth(x0 + 3, x1 - 3, y0 + 2, 8)
    plank(x0 + 2, y0 + 4, x1 - 2, y0 + 4, 2)
    for pxx in range(int(x0) + 8, int(x1) - 4, 22):
        beam(pxx, y0 + 5, y1 - 4, 2, WOOD_D, WOOD)
    px_edge = x1 if side > 0 else x0
    catwalk(px_edge - 14 * side, px_edge + 8 * side, y1 - 6, drop=7)


def build():
    new_canvas(400, 225, seed=52915)
    cw, ch = canvas_size()

    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=26)
    for _ in range(44):
        rect(rnd() * cw, rnd() * 14, rnd() * cw + 6, rnd() * 14 + 1, ROCK_D, 0.5)

    # ── the void, and the galleries in its walls ───────────────────────────
    carve(22, 20, 378, 206, rough=4)
    rock_teeth(26, 374, 22, 30)
    for _ in range(26):                                    # the walls of it, streaked
        y = 24 + rnd() * 170
        rect(24, y, 24 + rnd() * 10, y, ROCK_D, 0.6)
        rect(374 - rnd() * 10, y, 374, y, ROCK_D, 0.6)

    for _ in range(14):                                    # the roof of the void, in use
        cx = 40 + rnd() * 320
        for k in range(int(3 + rnd() * 9)):
            px(cx, 24 + k, ROCK_M if k < 2 else ROCK_D)
    for cx in (120, 196, 300):                              # old rigging, still hanging
        chain(cx, 24, 24 + int(10 + rnd() * 16))
    for _ in range(20):
        disc(40 + rnd() * 320, 26 + rnd() * 40, 1 + rnd() * 3, (140, 138, 132), 0.08)

    GALLERIES = [
        (22, 32, 96, 76, 1),        # west upper
        (22, 118, 88, 162, 1),      # west lower
        (306, 44, 378, 88, -1),     # east upper
        (300, 136, 378, 180, -1),   # east lower
    ]
    for x0, y0, x1, y1, side in GALLERIES:
        carve(x0, y0, x1, y1, rough=2)
    for x0, y0, x1, y1, side in GALLERIES:
        gallery(x0, y0, x1, y1, side)

    # ── the two pinnacles, and the towers on them ─────────────────────────
    pinnacle(150, 96, FLOOR, 9, 28)
    pinnacle(258, 84, FLOOR, 8, 24)
    t1 = tower(150, 96, 26, 13)
    t2 = tower(258, 84, 28, 12)

    # ── the ropeway: wall, tower, tower, wall ─────────────────────────────
    anchor(96, 60, 1)
    anchor(306, 66, -1)
    span_a = cable_run(100, 60, t1[0], t1[1], 7)
    span_b = cable_run(t1[0], t1[1], t2[0], t2[1], 6)
    span_c = cable_run(t2[0], t2[1], 302, 66, 7)
    for pts, ts in ((span_a, (0.35, 0.72)), (span_b, (0.3, 0.66)), (span_c, (0.45,))):
        for t in ts:
            bucket(pts, t, load=chance(0.7))
    bucket(span_b, 0.9, load=True, falling=True)           # and one that came off

    for k in range(3):                                     # a cable that has parted
        line(302, 66 + k, 288, 96 + k * 3, MET_L if k == 1 else MET_D, 0.9)
    for y in range(96, 150, 4):
        px(288 - (y - 96) // 6, y, MET_L)
        px(289 - (y - 96) // 6, y + 1, MET_D)

    # ── the footbridge, slung under it ────────────────────────────────────
    footbridge(96, 128, 150, 118, 16)
    footbridge(150, 118, 258, 112, 22)
    footbridge(258, 112, 306, 150, 14)

    # ── the towers, staffed ───────────────────────────────────────────────
    for cx, base, h in ((150, 96, 26), (258, 84, 28)):
        plank(cx - 14, base - h + 2, cx + 14, base - h + 2, 2)
        humanoid(cx + 6, base - h - 10, MET_L, RED, face_right=False)
        lamp(cx - 10, base - h, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=22,
             strength=0.28)
        ladder(cx - 2, base - h + 4, base - 4, w=4, step=6)
        for _ in range(10):                                # ore spilled on the pinnacle
            px(cx - 12 + rnd() * 24, base - 1 - rnd() * 2, pick([ORE, DIRT_L]), 0.8)
    crate(140, 84, 7)
    barrel(268, 72, MET, MET_L, MET_XL)

    # ── the galleries, working ────────────────────────────────────────────
    x0, y0, x1, y1, _ = GALLERIES[0]
    rails(x0 + 4, x1 - 6, y1 - 6, broken=(70, 78))
    cart(34, y1 - 15)
    humanoid(64, y1 - 16, DIRT_L, GREEN, face_right=False)
    lamp(48, y0 + 5, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    scrap_pile(76, y1 - 6, 18, 7, (DIRT_L, DIRT, ROCK_M, ORE))   # ore heap at the landing

    x0, y0, x1, y1, _ = GALLERIES[1]
    player(38, y1 - 16)
    binny(52, y1 - 28)
    tk_beam(44, y1 - 12, 76, y1 - 24)
    rect(70, y1 - 30, 84, y1 - 22, ROCK_M)                 # a rock, held over the drop
    rect(70, y1 - 30, 84, y1 - 30, ROCK_L)
    humanoid(64, y1 - 16, MET_L, RED, face_right=False)
    lamp(40, y0 + 5, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)

    x0, y0, x1, y1, _ = GALLERIES[2]
    conveyor(x0 + 6, x1 - 4, y1 - 16, direction=-1)
    for _ in range(16):
        px(x0 + 8 + rnd() * 60, y1 - 19 + rnd() * 2, pick([ORE, DIRT_L, ROCK_L]))
    humanoid(x0 + 40, y1 - 16, DIRT_L, DIRT_L, face_right=False)
    lamp(x0 + 20, y0 + 5, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    crate(x1 - 20, y1 - 12, 7)

    x0, y0, x1, y1, _ = GALLERIES[3]
    rails(x0 + 4, x1 - 6, y1 - 6)
    cart(x0 + 16, y1 - 15)
    door(x1 - 30, y1 - 32, 24, 26)
    glow(x1 - 18, y1 - 18, 22, PALE_G, 0.16)
    humanoid(x0 + 44, y1 - 16, MET_L, RED, face_right=False)
    tracer(x0 + 46, y1 - 12, x0 + 12, y1 - 10)
    lamp(x0 + 30, y0 + 5, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)

    # ── the sill of the void: everything that has ever fallen ─────────────
    floor_slab(22, 378, FLOOR, 6, ROCK_D, ROCK_L)
    debris_fan(60, 340, FLOOR - 1, 18)
    wrecked_bucket(196, FLOOR - 2)
    wrecked_bucket(288, FLOOR - 2)
    ragdoll(214, FLOOR - 12, RED_L)
    ragdoll(120, FLOOR - 10)
    rails(26, 180, FLOOR - 2, broken=(120, 150))
    cart(60, FLOOR - 11, tipped=True)
    humanoid(160, FLOOR - 14, DIRT_L, RED, face_right=False)
    for _ in range(22):
        disc(60 + rnd() * 280, FLOOR - 30 + rnd() * 28, 1 + rnd() * 3.5,
             (146, 142, 132), 0.10)
    lamp(100, FLOOR - 34, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.20)
    lamp(320, FLOOR - 34, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.20)

    # ── the way in: a rope down the west wall ─────────────────────────────
    for y in range(22, 32):
        px(30, y, MET_L if y % 3 else MET_D)

    vignette()
    return save(out_path("LevelConcept_TheSpan.png"))


if __name__ == "__main__":
    build()
