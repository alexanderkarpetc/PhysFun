"""Concept 03 - THE DEEP CUT.

A mine that is one bad decision away from falling on you. Everything here is built
around TerrainSupportSystem: the galleries are held up by wooden pit props, and a
prop is a physics object like any other — burn it, shoot it, or telekinesis it out
of the way and the roof above comes down as real terrain, on whoever is under it.

The level never asks for a collapse. It just puts the miners under the sagging bay.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 44
LAMP_TINT = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def rails(x0, x1, y, ties=8, broken=None):
    """Mine track. `broken` is an (x0, x1) span where the rail is simply gone."""
    for x in range(int(x0), int(x1)):
        if broken and broken[0] <= x <= broken[1]:
            continue
        px(x, y, MET_XL)
        px(x, y + 1, MET)
    for x in range(int(x0), int(x1), ties):
        if broken and broken[0] <= x <= broken[1]:
            continue
        rect(x, y + 2, x + 4, y + 3, WOOD_D)


def minecart(x, y, tipped=False):
    rect(x, y, x + 13, y + 7, MET)
    rect(x, y, x + 13, y, MET_XL)
    rect(x + 1, y + 1, x + 12, y + 3, (58, 46, 34))
    for _ in range(9):                                   # ore heaped over the rim
        px(x + 2 + int(rnd() * 10), y - 1 + int(rnd() * 3), pick([DIRT_L, GREEN_L, MET_L]))
    rect(x, y + 7, x + 13, y + 8, MET_D)
    for wx in (x + 3, x + 10):
        disc(wx, y + 9, 2, INK)
        disc(wx, y + 9, 1, MET_L)
    if tipped:
        for i in range(14):                              # spilled load
            px(x + 14 + i, y + 9 - int(rnd() * 3), pick([DIRT_L, DIRT, GREEN_L]))


def pit_prop(x, y0, y1, cracked=False, gone=False):
    """A timber holding up the roof. Gone = the bay above it is already sagging."""
    if gone:
        rect(x, y1 - 4, x + 3, y1, WOOD_D)               # stump left in the floor
        for i in range(6):
            px(x + int(rnd() * 4), y1 - 6 - int(rnd() * 4), WOOD_D)
        return
    beam(x, y0, y1)
    rect(x - 3, y0, x + 6, y0 + 1, WOOD_L)               # head board
    if cracked:
        for k in range(5):
            px(x + (k % 3), y0 + 6 + k * 2, CHAR)


def sag(x0, x1, y, depth=4):
    """Ceiling bowing down between two props, with the hairline cracks that say so."""
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
    for i in range(4):                                   # dust trail upward
        px(x + int(rnd() * s), y - 3 - i * 2, DIRT_L, 0.5)


def crystal(cx, base, h=14, w=6, c=CYAN, dark=(34, 62, 70), lit=ICE_XL):
    """Faceted cluster growing off the floor - reads as a shape, not a blob."""
    for i in range(h):
        t = i / h
        half = max(int(w * (1 - t) / 2), 0)
        rect(cx - half, base - i, cx + half, base - i, dark if i % 5 == 4 else c,
             0.55 + 0.45 * (1 - t))
    line(cx, base - h + 1, cx - w // 2, base, lit, 0.7)
    line(cx, base - h + 1, cx + w // 2, base, dark, 0.9)
    glow(cx, base - h // 2, h, c, 0.20)


def crystal_cluster(cx, base, scale=1.0):
    crystal(cx, base, int(16 * scale), int(7 * scale))
    crystal(cx - int(6 * scale), base, int(10 * scale), int(5 * scale))
    crystal(cx + int(7 * scale), base, int(12 * scale), int(5 * scale))


def gas(x0, y0, x1, y1, n=90):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), 1 + rnd() * 3,
             pick([(96, 130, 72), (128, 160, 88)]), 0.16)


def ore_vein(x0, y0, x1, y1, n=40, colors=(GREEN_L, PALE_G, CYAN)):
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        y = y0 + rnd() * (y1 - y0)
        rect(x, y, x + 1 + rnd() * 2, y, pick(list(colors)), 0.9)


def build():
    new_canvas(400, 225, seed=90210)

    # ── dusk over the pit head ──────────────────────────────────────────────
    sky(SURF, hi=(126, 108, 104), lo=(74, 66, 72), smog=7)
    for _ in range(40):
        px(rnd() * W, rnd() * (SURF - 6), (200, 180, 150), 0.25)
    rock_mass(SURF, soil=DIRT, soil_lit=DIRT_L)

    ROOMS = [
        (48, 48, 74, 196),      # main shaft
        (8, 92, 190, 126),      # upper gallery
        (74, 140, 250, 178),    # haulage level
        (16, 184, 130, 214),    # flooded sump
        (188, 118, 262, 146),   # ramp between levels
        (244, 116, 336, 172),   # gas pocket
        (258, 56, 392, 116),    # crystal cavern
        (330, 172, 392, 212),   # ore chute / exit
        (176, 96, 214, 122),    # gallery -> ramp
        (120, 172, 160, 190),   # haulage -> sump
    ]
    carve_all(ROOMS)

    # ── surface: headframe, spoil heaps, hoist house ────────────────────────
    scrap_pile(4, SURF, 40, 10, (DIRT, DIRT_D, DIRT_L, ROCK_M))
    scrap_pile(140, SURF, 70, 12, (DIRT, DIRT_D, DIRT_L, ROCK_M))
    scrap_pile(300, SURF, 60, 9, (DIRT, DIRT_D, DIRT_L, ROCK_M))
    beam(44, SURF - 34, SURF, 3)                          # headframe legs
    beam(74, SURF - 34, SURF, 3)
    line(44, SURF - 34, 61, SURF - 44, WOOD)              # A-frame
    line(78, SURF - 34, 61, SURF - 44, WOOD)
    rect(52, SURF - 46, 70, SURF - 44, WOOD_L)
    line(50, SURF - 6, 72, SURF - 30, WOOD_D)             # bracing
    line(72, SURF - 6, 50, SURF - 30, WOOD_D)
    disc(61, SURF - 48, 4, MET)                           # sheave wheel
    ring(61, SURF - 48, 4, MET_XL)
    line(61, SURF - 44, 61, 66, MET_L)                    # hoist rope
    rect(90, SURF - 14, 122, SURF, (62, 58, 62))          # hoist house
    rect(90, SURF - 14, 122, SURF - 14, (92, 86, 88))
    rect(96, SURF - 10, 102, SURF - 5, LAMP_TINT)
    glow(99, SURF - 8, 14, LAMP_TINT, 0.25)
    rails(122, 210, SURF - 1, broken=(168, 176))
    minecart(150, SURF - 10, tipped=True)
    humanoid(196, SURF - 12, DIRT_L, WOOD_L, face_right=False)
    rect(40, SURF - 3, 82, SURF - 1, MET_D)               # shaft collar
    rect(40, SURF - 3, 82, SURF - 3, MET_L)

    # ── 1  the cage, coming down the shaft ──────────────────────────────────
    rect(48, 48, 49, 196, MET_D)
    rect(73, 48, 74, 196, MET_D)
    for y in range(52, 196, 12):                          # shaft guides
        rect(50, y, 72, y, ROCK_D, 0.6)
    rect(52, 66, 70, 80, MET)                             # cage
    frame(52, 66, 70, 80, MET_XL)
    rect(54, 68, 68, 78, (28, 32, 38))
    for x in range(55, 68, 3):
        rect(x, 68, x, 78, MET_L, 0.7)
    player(56, 68)
    binny(60, 84)
    lamp(61, 62, drop=2, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.30)
    for _ in range(10):
        falling_chunk(50 + rnd() * 20, 100 + rnd() * 80, 2)

    # ── 2  upper gallery: the props that hold the roof ──────────────────────
    floor_slab(8, 190, 122, 4, DIRT_D, DIRT)
    sag(96, 150, 96, 5)                                   # bay whose prop is gone
    for pxx, cracked, gone in ((16, False, False), (40, False, False), (64, True, False),
                               (92, True, False), (120, False, True), (150, True, False),
                               (176, False, False)):
        pit_prop(pxx, 97, 122, cracked, gone)
    plank(10, 96, 188, 96, 2)                             # lagging along the roof
    rails(10, 188, 120, broken=(112, 130))
    minecart(28, 111)
    ore_vein(10, 100, 60, 118, 26, (GREEN_L, PALE_G))
    humanoid(104, 110, DIRT_L, WOOD_L)                    # miners under the sag
    humanoid(134, 110, MET_L, WOOD_L, face_right=False)
    humanoid(160, 110, DIRT_L, RED, face_right=False)
    tracer(133, 115, 112, 116)
    for lx in (34, 78, 158):
        lamp(lx, 97, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    falling_chunk(118, 104, 5)
    falling_chunk(126, 112, 3)
    rubble(96, 116, 150, 121, 40, (ROCK_M, ROCK_D, DIRT))

    # ── 3  haulage level ────────────────────────────────────────────────────
    floor_slab(74, 250, 174, 4, DIRT_D, DIRT)
    rails(78, 248, 172, broken=(150, 170))
    minecart(96, 163)
    minecart(206, 163)
    for pxx in (86, 128, 190, 232):
        pit_prop(pxx, 146, 174, cracked=(pxx == 128))
    plank(76, 145, 248, 145, 2)
    ore_vein(200, 148, 248, 170, 30)
    humanoid(176, 162, MET_L, GREEN, face_right=False)
    humanoid(222, 162, DIRT_L, RED, face_right=False)
    crate(112, 166); crate(142, 166, 7, False)
    lamp(110, 146, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    lamp(212, 146, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.26)
    ragdoll(158, 158)
    rubble(148, 168, 176, 173, 30, (ROCK_M, DIRT, ROCK_D))

    # ── 4  flooded sump ─────────────────────────────────────────────────────
    water(16, 202, 130, 214)
    glow(72, 204, 40, (70, 120, 140), 0.20)
    plank(20, 200, 96, 200, 2)                            # walkway, half sunk
    for pxx in (34, 62, 88):
        beam(pxx, 200, 210, 2, WOOD_D, WOOD)
    ragdoll(102, 197)
    for _ in range(18):
        px(18 + rnd() * 110, 200 + rnd() * 3, ICE_L, 0.35)
    crate(24, 192); crate(46, 192)

    # ── 5  gas pocket ───────────────────────────────────────────────────────
    floor_slab(244, 336, 168, 4, DIRT_D, DIRT)
    gas(246, 120, 334, 168)
    for _ in range(20):                                   # seeping cracks in the floor
        gx = 248 + rnd() * 84
        line(gx, 168, gx, 162 - rnd() * 6, (140, 176, 96), 0.4)
    barrel(268, 160, GREEN, GREEN_L, PALE_G)
    barrel(276, 160, GREEN, GREEN_L, PALE_G)
    crate(300, 160, 7, False)
    lamp(292, 120, drop=8, bulb=F_HOT, tint=F_MID, r=22, strength=0.30)  # naked flame
    humanoid(318, 156, MET_L, GREEN, face_right=False)
    pipe_run(246, 334, 122)

    # ── 6  crystal cavern ───────────────────────────────────────────────────
    floor_slab(258, 392, 112, 4, DIRT_D, DIRT)
    for cx, sc in ((276, 1.3), (310, 1.0), (348, 1.4), (382, 1.0)):
        crystal_cluster(cx, 111, sc)
    for cx, h, w in ((292, 16, 8), (330, 12, 6), (366, 20, 9)):      # roof-hung spars
        for i in range(h):
            half = max(int(w * (1 - i / h) / 2), 0)
            rect(cx - half, 60 + i, cx + half, 60 + i, (34, 62, 70) if i % 5 == 4 else CYAN,
                 0.55 + 0.45 * (1 - i / h))
        line(cx, 60 + h - 1, cx - w // 2, 60, ICE_XL, 0.6)
        glow(cx, 60 + h // 2, h + 4, CYAN, 0.18)
    ore_vein(262, 96, 390, 110, 16, (CYAN, ICE_L))
    icicles(262, 388, 60, 16, ICE, ICE_L)                 # crystal spikes off the roof
    for rx in (286, 356):                                 # rope down from the roof
        for y in range(60, 110, 3):
            px(rx, y, WOOD_L)
            px(rx + 1, y + 1, WOOD_D)
    humanoid(318, 100, MET_L, CYAN, face_right=False)
    crate(268, 104); crate(276, 104)
    binny(348, 96)

    # ── 7  ore chute out ────────────────────────────────────────────────────
    floor_slab(330, 392, 208, 4, DIRT_D, DIRT)
    for i in range(5):                                    # chute plates
        rect(334 + i * 2, 176 + i * 6, 392, 178 + i * 6, MET_D)
        rect(334 + i * 2, 176 + i * 6, 392, 176 + i * 6, MET_L)
    door(352, 182, 30, 26)
    glow(367, 195, 22, PALE_G, 0.16)
    for _ in range(26):
        px(336 + rnd() * 54, 178 + rnd() * 30, pick([DIRT_L, GREEN_L, MET_L]), 0.8)

    vignette()

    # ── sheet furniture ─────────────────────────────────────────────────────
    title_bar("PHYSFUN - LEVEL CONCEPT 03:  THE DEEP CUT")
    callout(8, 24, "1 PIT HEAD - CAGE DESCENT", 61, 40)
    callout(150, 22, "2 SAGGING BAY - ONE PROP MISSING", 122, 98)
    callout(300, 26, "6 CRYSTAL CAVERN", 340, 84)
    callout(6, 74, "3 TIMBERED GALLERY - CUT THE PROPS,", 40, 100)
    tag(6, 82, "  THE ROOF IS A PHYSICS OBJECT")
    callout(238, 178, "5 GAS POCKET - NO FLAME", 292, 150)
    callout(150, 130, "4 HAULAGE - RIDE THE CART", 206, 162)
    callout(300, 216, "7 ORE CHUTE EXIT", 360, 196)
    callout(6, 196, "8 FLOODED SUMP - SNUFFS FIRE", 60, 204)
    legend(146, 190, [
        ("BEATS", CYAN),
        ("SUPPORT > COLLAPSE > CRUSH", (170, 180, 195)),
        ("GAS + FLAME = ROOM GONE", (200, 150, 90)),
        ("GOAL: DROP THE ROOF, WALK OUT", GREEN_L),
    ], width=124)

    return save(out_path("LevelConcept_DeepCut.png"))


if __name__ == "__main__":
    build()
