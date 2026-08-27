"""Concept 09 - THE SORTING TOWER.

The vertical one. Every other sheet reads left to right; this one is a shaft you descend,
and the level's whole difficulty curve is the drop you are willing to take.

Chutes run the other way to the player: they carry cargo down fast and they will carry the
player down faster. The safe route is the slow one — belts, ladders, a cap of crates you
stack yourself — and the fast route is always available and always slightly lethal.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 34
AMBER = (255, 196, 90)


def chute(x0, y0, x1, y1, w=14, c=MET_D, lit=MET_L):
    """Angled slide. Two rails and a floor, so it reads as something cargo slides down."""
    line(x0, y0, x1, y1, c)
    line(x0, y0 + 1, x1, y1 + 1, lit)
    line(x0, y0 + w, x1, y1 + w, c)
    steps = max(int(abs(x1 - x0)), 2)
    for i in range(0, steps, 9):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        line(x, y, x, y + w, c, 0.45)


def sorter_arm(x, y, reach=18, c=MET_L):
    """The thing that shoves cargo off the belt — and off the player, given the chance."""
    rect(x - 2, y - 8, x + 2, y, MET_D)
    rect(x, y, x + reach, y + 3, c)
    rect(x + reach, y - 2, x + reach + 3, y + 5, MET)
    glow(x + reach, y + 1, 10, AMBER, 0.18)


def floor_plate(x0, x1, y, label_lamps=True):
    floor_slab(x0, x1, y, 4, (44, 46, 54), (104, 110, 122))
    if label_lamps:
        for lx in range(int(x0) + 20, int(x1) - 10, 60):
            lamp(lx, y - 44, bulb=AMBER, tint=(255, 200, 130), r=18, strength=0.18)


def build():
    new_canvas(400, 225, seed=9009)

    sky(SURF, hi=(120, 124, 138), lo=(78, 84, 98), smog=6)
    rect(120, 6, 300, SURF, (56, 60, 70))                     # the tower head above ground
    rect(120, 6, 300, 6, (86, 92, 104))
    for x in range(126, 296, 12):
        rect(x, 12, x + 6, 22, (38, 42, 50))
    for sx in (40, 340):
        rect(sx, 18, sx + 8, SURF, (60, 64, 74))
        rect(sx, 18, sx + 8, 18, (88, 94, 106))

    rock_mass(SURF, base=(60, 62, 70), dark=(40, 42, 50), mid=(82, 86, 96),
              soil=(72, 70, 66), soil_lit=(126, 122, 112))

    ROOMS = [
        (100, 40, 300, 78),     # intake floor
        (60, 84, 340, 122),     # sorting floor
        (40, 128, 360, 168),    # transfer floor
        (20, 174, 380, 212),    # dispatch floor
        (170, 74, 230, 90),     # intake -> sorting
        (86, 118, 140, 132),    # sorting -> transfer
        (280, 118, 330, 132),   # sorting -> transfer, far side
        (56, 164, 110, 178),    # transfer -> dispatch
        (300, 164, 350, 178),   # transfer -> dispatch, far side
    ]
    carve_all(ROOMS, air=(20, 22, 28), lip=(78, 82, 94))

    # ── surface ─────────────────────────────────────────────────────────────
    rect(150, SURF - 4, 250, SURF - 2, MET_D)
    rect(150, SURF - 4, 250, SURF - 4, MET_L)
    player(186, SURF - 12)
    binny(200, SURF - 22)
    humanoid(266, SURF - 12, MET_L, RED, face_right=False)
    scrap_pile(60, SURF, 60, 10, (MET_D, MET, DIRT))

    # ── 1  intake floor ─────────────────────────────────────────────────────
    floor_plate(100, 300, 74)
    conveyor(112, 288, 62, 1)
    for cx in (128, 168, 214, 258):
        crate(cx, 54, 7, cx % 3 == 0)
    sorter_arm(196, 50, 16)
    humanoid(120, 62, MET_L, GREEN)
    humanoid(272, 62, DIRT_L, GREEN, face_right=False)
    tracer(127, 67, 250, 68)
    chute(200, 76, 250, 90, 12)                               # the fast way down
    pipe_run(102, 298, 42, c=(56, 60, 70), lit=MET_L)

    # ── 2  sorting floor ────────────────────────────────────────────────────
    floor_plate(60, 340, 118)
    conveyor(70, 200, 106, 1)
    conveyor(210, 332, 106, -1)
    for i, sx in enumerate((124, 176, 244, 296)):
        sorter_arm(sx, 94, 16 if i % 2 else 22)
    for cx in (86, 150, 226, 310):
        crate(cx, 98, 7, cx % 2 == 0)
    chute(120, 120, 90, 132, 12)
    chute(300, 120, 328, 132, 12)
    player(206, 95)
    tk_beam(213, 99, 244, 96, CYAN)
    humanoid(96, 107, MET_L, RED, face_right=False)
    humanoid(320, 107, DIRT_L, RED, face_right=False)
    grate(200, 250, 118)
    lamp(160, 86, bulb=AMBER, tint=(255, 200, 130), r=22, strength=0.20)
    lamp(272, 86, bulb=AMBER, tint=(255, 200, 130), r=22, strength=0.20)

    # ── 3  transfer floor ───────────────────────────────────────────────────
    floor_plate(40, 360, 164)
    conveyor(52, 180, 150, -1)
    conveyor(196, 348, 150, 1)
    for cx in (64, 118, 232, 300):
        crate(cx, 142, 7, cx % 3 == 0)
    sorter_arm(160, 138, 20)
    chute(70, 166, 106, 178, 12)
    chute(330, 166, 306, 178, 12)
    catwalk(40, 358, 130, drop=6, posts=22)
    humanoid(140, 151, MET_L, GREEN)
    humanoid(276, 151, MET_L, GREEN, face_right=False)
    tracer(147, 156, 268, 156)
    ragdoll(212, 146)
    binny(196, 132)

    # ── 4  dispatch floor ───────────────────────────────────────────────────
    floor_plate(20, 380, 208, label_lamps=False)
    conveyor(32, 200, 196, 1)
    conveyor(214, 368, 196, 1)
    for cx in (44, 96, 148, 246, 300):
        crate(cx, 188, 7, cx % 2 == 0)
    gear(206, 200, 8)                                         # the transfer wheel
    humanoid(122, 193, DIRT_L, RED, face_right=False)
    door(340, 178, 30, 28)
    glow(355, 192, 22, PALE_G, 0.16)
    for lx in (72, 300):
        lamp(lx, 176, bulb=AMBER, tint=(255, 200, 130), r=18, strength=0.18)
    rubble(24, 202, 190, 207, 30, (MET_D, DIRT, (70, 74, 84)))

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 09:  THE SORTING TOWER")
    callout(6, 24, "1 TOWER HEAD - SPAWN", 190, 34)
    callout(252, 44, "2 INTAKE - RIDE THE CARGO IN", 240, 62)
    callout(6, 84, "3 SORTING FLOOR - ARMS SHOVE", 124, 96)
    callout(250, 92, "4 CHUTES - FAST AND LETHAL", 328, 128)
    callout(6, 140, "5 TRANSFER - BELTS RUN BOTH WAYS", 160, 150)
    callout(6, 214, "6 DISPATCH - LAST FLOOR", 100, 196)
    callout(268, 214, "7 SHIPPING DOOR", 344, 192)
    legend(6, 46, [
        ("BEATS", CYAN),
        ("THE LEVEL IS A DROP", (170, 180, 195)),
        ("SLOW IS SAFE, FAST IS CHEAP", (200, 150, 90)),
        ("GOAL: REACH THE FLOOR ALIVE", GREEN_L),
    ], width=118)

    return save(out_path("LevelConcept_SortingTower.png"))


if __name__ == "__main__":
    build()
