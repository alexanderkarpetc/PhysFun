"""Concept 07 - THE FUNGAL SINK.

The one level that is alive. No machinery, no straight lines: a sinkhole the forest fell
into, lit by the fungus rather than by lamps, with spore clouds hanging in the still air.

Spores are the mechanic. They drift, they are flammable, and a cloud that catches goes off
as a flat sheet of flame rather than a fireball — so fire here is a decision about the whole
room, not a tool you point at something. The caps themselves are soft platforms: they hold,
they sag, and they burn away faster than wood.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 40
MOSS = (72, 104, 58)
MOSS_L = (126, 168, 84)
FLESH = (168, 104, 118)
BIOLUM = (140, 240, 190)


def root(x0, y0, x1, y1, thick=3, c=(96, 74, 52), lit=(140, 112, 78)):
    """A root breaking through the roof — organic version of a pit prop, and it burns."""
    steps = max(int(abs(y1 - y0)), 2)
    px_prev = x0
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t + math.sin(t * 6) * 4
        y = y0 + (y1 - y0) * t
        rect(x, y, x + thick, y + 1, c)
        px(x, y, lit)
        px_prev = x
    return px_prev


def gill_shelf(x0, x1, y, c=FLESH, lit=(240, 230, 200)):
    """Walkable cap. Drawn thin and sagging so it never reads as rock."""
    span = x1 - x0
    for i in range(int(span) + 1):
        t = i / max(span, 1)
        d = int(3 * (1 - (2 * t - 1) ** 2))
        rect(x0 + i, y + d, x0 + i, y + d + 3, c)
        px(x0 + i, y + d, lit)
    glow((x0 + x1) / 2, y + 4, span * 0.45, BIOLUM, 0.12)


def build():
    new_canvas(400, 225, seed=7007)

    # ── forest floor above the hole ─────────────────────────────────────────
    sky(SURF, hi=(96, 112, 96), lo=(58, 70, 62), smog=6)
    for _ in range(40):
        px(rnd() * W, rnd() * SURF, (150, 190, 140), 0.18)
    rock_mass(SURF, base=(58, 64, 56), dark=(38, 44, 38), mid=(78, 88, 72),
              soil=(70, 82, 50), soil_lit=MOSS_L)
    for x in range(W):                                       # grass fringe
        if chance(0.5):
            rect(x, SURF - 1 - int(rnd() * 3), x, SURF, MOSS_L)

    ROOMS = [
        (60, 44, 150, 96),      # the sinkhole itself
        (8, 96, 210, 168),      # main chamber
        (10, 168, 150, 206),    # spore basin
        (198, 88, 300, 150),    # gallery of caps
        (196, 150, 290, 202),   # rot pool
        (296, 60, 392, 140),    # the mother cap
        (300, 146, 392, 202),   # exit burrow
        (150, 120, 204, 146),   # chamber -> gallery
        (286, 110, 306, 134),   # gallery -> mother
    ]
    carve_all(ROOMS, air=(22, 28, 26), lip=(70, 86, 66))

    # ── surface + the hole ──────────────────────────────────────────────────
    for tx in (20, 178, 320):                                # dead trunks leaning in
        beam(tx, SURF - 26, SURF, 4, (86, 70, 50), (128, 104, 72))
        for k in range(5):
            line(tx + 2, SURF - 26 + k * 2, tx + 12 + k * 3, SURF - 32 + k, (86, 70, 50))
    player(96, SURF - 12, coat=(60, 84, 70), cuff=MOSS_L)
    binny(112, SURF - 22, eye=BIOLUM, thruster=BIOLUM)
    for _ in range(30):                                      # rim crumbling in
        px(62 + rnd() * 86, 44 + rnd() * 50, MOSS, 0.5)
    root(84, 44, 96, 100, 3)
    root(126, 46, 112, 104, 3)

    # ── 1  main chamber ─────────────────────────────────────────────────────
    floor_slab(8, 210, 164, 4, (44, 52, 44), (96, 116, 84))
    spore_cloud(12, 108, 205, 162, 90)
    for mx, base, h, cap in ((36, 164, 20, 26), (72, 164, 14, 18), (150, 164, 24, 30),
                             (186, 164, 12, 16)):
        mushroom(mx, base, h, cap)
    gill_shelf(52, 116, 132)
    gill_shelf(120, 190, 118)
    for x0, y0, x1, y1 in ((20, 96, 30, 140), (168, 96, 176, 128)):
        root(x0, y0, x1, y1, 3)
    humanoid(88, 152, MOSS_L, FLESH, face_right=False)       # something that lives here
    humanoid(164, 106, ICE_L, MOSS, face_right=False)
    player(126, 106, coat=(60, 84, 70), cuff=MOSS_L)
    tk_beam(133, 110, 152, 138, BIOLUM)
    for gx, gy in ((44, 118), (108, 150), (196, 120)):       # glowing clusters
        disc(gx, gy, 3, BIOLUM, 0.8)
        glow(gx, gy, 20, BIOLUM, 0.22)
    ragdoll(178, 156, MOSS_L)

    # ── 2  spore basin ──────────────────────────────────────────────────────
    floor_slab(10, 150, 202, 4, (44, 52, 44), (96, 116, 84))
    liquid_pool(12, 186, 148, 202, (58, 84, 52), (128, 176, 96))
    spore_cloud(12, 170, 148, 196, 70, (190, 220, 140))
    for mx in (34, 66, 104):
        mushroom(mx, 186, 10, 14, (200, 210, 180), (120, 150, 90))
    embers(60, 172, 92, 186, 14)                             # someone lit it once
    glow(76, 180, 26, F_MID, 0.20)
    crate(120, 178)

    # ── 3  gallery of caps ──────────────────────────────────────────────────
    floor_slab(198, 300, 146, 4, (44, 52, 44), (96, 116, 84))
    for i, (gx0, gx1, gy) in enumerate(((202, 250, 132), (238, 292, 118), (208, 258, 104))):
        gill_shelf(gx0, gx1, gy)
    for mx, h, cap in ((214, 16, 22), (264, 20, 26)):
        mushroom(mx, 146, h, cap)
    spore_cloud(200, 92, 298, 144, 60)
    humanoid(272, 136, MOSS_L, FLESH, face_right=False)
    humanoid(226, 94, ICE_L, MOSS)
    disc(246, 100, 3, BIOLUM, 0.8)
    glow(246, 100, 22, BIOLUM, 0.20)

    # ── 4  rot pool ─────────────────────────────────────────────────────────
    floor_slab(196, 290, 198, 4, (44, 52, 44), (96, 116, 84))
    liquid_pool(198, 178, 288, 198, (66, 62, 40), (150, 150, 80))
    for _ in range(24):
        bx = 200 + rnd() * 84
        disc(bx, 178 - rnd() * 2, 1 + rnd() * 2, (170, 180, 100), 0.5)
    ragdoll(240, 172, (150, 150, 80))
    root(210, 150, 220, 178, 3)
    root(262, 150, 254, 176, 3)

    # ── 5  the mother cap ───────────────────────────────────────────────────
    floor_slab(296, 392, 136, 4, (44, 52, 44), (96, 116, 84))
    mushroom(344, 136, 44, 76, (216, 206, 186), (176, 96, 112))
    glow(344, 96, 54, BIOLUM, 0.24)
    for sx in (312, 326, 362, 378):                          # children
        mushroom(sx, 136, 12 + int(rnd() * 8), 16 + int(rnd() * 8))
    spore_cloud(298, 64, 390, 134, 80, (190, 230, 160))
    for _ in range(24):                                      # spore fall
        px(300 + rnd() * 88, 66 + rnd() * 66, (210, 250, 190), 0.5)
    humanoid(306, 126, MOSS_L, FLESH)
    binny(370, 112, eye=BIOLUM, thruster=BIOLUM)

    # ── 6  exit burrow ──────────────────────────────────────────────────────
    floor_slab(300, 392, 198, 4, (44, 52, 44), (96, 116, 84))
    for i in range(6):                                       # the burrow narrows
        rect(302 + i * 3, 150 + i * 4, 392, 152 + i * 4, (54, 64, 52))
    door(348, 160, 30, 30, (86, 96, 78), MOSS_L, (40, 48, 40))
    glow(363, 175, 24, BIOLUM, 0.18)
    for mx in (312, 330):
        mushroom(mx, 198, 10, 14)

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 07:  THE FUNGAL SINK")
    callout(6, 24, "1 SINKHOLE - SPAWN, DROP IN", 96, 50)
    callout(150, 22, "2 MAIN CHAMBER - CAPS ARE SOFT PLATFORMS", 150, 128)
    callout(280, 30, "5 MOTHER CAP - ONE BIG FUSE", 344, 96)
    callout(6, 84, "3 SPORE BASIN - FLAMMABLE AIR", 76, 180)
    callout(196, 76, "4 CAP GALLERY - CLIMB, DO NOT BURN", 246, 118)
    callout(196, 210, "6 ROT POOL - DISSOLVES", 244, 186)
    callout(300, 212, "7 EXIT BURROW", 352, 178)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("SPORES DRIFT, THEN THEY CATCH", (170, 180, 195)),
        ("FIRE IS A ROOM DECISION HERE", (200, 150, 90)),
        ("GOAL: CROSS WITHOUT LIGHTING IT", GREEN_L),
    ], width=140)

    return save(out_path("LevelConcept_FungalSink.png"))


if __name__ == "__main__":
    build()
