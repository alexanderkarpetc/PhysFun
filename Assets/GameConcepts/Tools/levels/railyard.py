"""Concept 08 - THE RAIL YARD.

Underground marshalling yard. The level is built out of things that weigh five tonnes and
are already moving: loaded cars roll when you unchock them, the turntable spins whatever is
standing on it, and the hopper drops its load on whatever is standing under it.

Almost nothing here is a hazard by itself. A car parked on a level track is furniture; the
same car released on a grade is the most powerful thing in the game. The level is a set of
brakes waiting to be let off.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 44
RUST = (128, 78, 52)
SIGNAL = (220, 70, 60)


def flatcar(x, y, w=30, load=None):
    rect(x, y, x + w, y + 5, MET)
    rect(x, y, x + w, y, MET_L)
    rect(x, y + 5, x + w, y + 6, MET_D)
    for wx in (x + 5, x + w - 5):
        disc(wx, y + 8, 2.4, INK)
        disc(wx, y + 8, 1.2, MET_L)
    if load == "crates":
        crate(x + 4, y - 8); crate(x + 14, y - 8, 7, False)
    elif load == "pipe":
        for i in range(3):
            rect(x + 3, y - 4 - i * 3, x + w - 3, y - 3 - i * 3, MET_L)
    elif load == "ore":
        for _ in range(16):
            px(x + 3 + rnd() * (w - 6), y - 1 - rnd() * 4, pick([DIRT_L, GREEN_L, MET_L]))


def hopper(x, y, w=40, h=26):
    """Overhead bin. The chute mouth is drawn open, because a closed one has no threat."""
    rect(x, y, x + w, y + h, MET_D)
    rect(x, y, x + w, y, MET_L)
    for i in range(6):
        rect(x + 4 + i, y + h + i, x + w - 4 - i, y + h + i, MET_D)
    rect(x + w // 2 - 5, y + h + 6, x + w // 2 + 5, y + h + 8, MET)
    for _ in range(20):
        px(x + w / 2 + (rnd() - 0.5) * 10, y + h + 9 + rnd() * 8, pick([DIRT_L, DIRT, MET_D]))


def signal(x, y, red=True):
    rect(x, y, x + 1, y + 14, MET_D)
    rect(x - 3, y - 6, x + 4, y, MET)
    disc(x, y - 3, 2, SIGNAL if red else GREEN_L)
    glow(x, y - 3, 12, SIGNAL if red else GREEN_L, 0.24)


def build():
    new_canvas(400, 225, seed=8080)

    sky(SURF, hi=(112, 104, 108), lo=(70, 68, 76), smog=7)
    for hx, hy, w in ((10, 20, 70), (200, 16, 90)):
        rect(hx, hy, hx + w, SURF, (58, 58, 66))
        rect(hx, hy, hx + w, hy, (86, 86, 96))
        for x in range(hx + 5, hx + w - 5, 10):
            rect(x, hy + 6, x + 5, hy + 12, (38, 38, 46))
    rock_mass(SURF, base=(62, 60, 62), dark=(42, 40, 44), mid=(84, 82, 86),
              soil=(78, 66, 54), soil_lit=(136, 118, 92))

    ROOMS = [
        (8, 58, 260, 108),      # upper yard
        (8, 124, 220, 178),     # lower yard
        (60, 100, 104, 132),    # ramp down
        (232, 120, 340, 180),   # turntable pit
        (212, 150, 240, 176),   # lower yard -> turntable
        (272, 54, 392, 110),    # hopper road
        (330, 112, 392, 176),   # departure road / exit
        (250, 84, 284, 106),    # upper yard -> hopper road
        (96, 186, 268, 214),    # runaway sump
        (150, 170, 190, 196),   # lower yard -> sump
    ]
    carve_all(ROOMS, air=(20, 22, 26), lip=(76, 74, 80))

    # ── surface ─────────────────────────────────────────────────────────────
    rails(0, 200, SURF - 1)
    flatcar(96, SURF - 10, 30, "crates")
    signal(180, SURF - 16, red=True)
    player(40, SURF - 12)
    binny(54, SURF - 22)
    humanoid(232, SURF - 12, MET_L, RED, face_right=False)
    scrap_pile(280, SURF, 70, 12, (RUST, MET_D, MET, DIRT))

    # ── 1  upper yard ───────────────────────────────────────────────────────
    floor_slab(8, 260, 104, 4, (46, 44, 50), (108, 106, 114))
    rails(12, 256, 102, broken=(150, 162))
    flatcar(28, 92, 32, "pipe")
    flatcar(104, 92, 30, "ore")
    flatcar(196, 92, 28)
    for cx in (66, 140):                                        # chocks under the wheels
        rect(cx, 100, cx + 4, 102, WOOD)
    signal(172, 84, red=False)
    catwalk(10, 250, 62, drop=8, posts=18)
    humanoid(84, 70, MET_L, GREEN)
    humanoid(214, 70, DIRT_L, GREEN, face_right=False)
    tracer(91, 75, 190, 88)
    for lx in (48, 128, 224):
        lamp(lx, 58, bulb=(255, 226, 150), tint=(255, 214, 150), r=20, strength=0.22)
    cable(10, 66, 254, 68, 5)

    # ── 2  lower yard ───────────────────────────────────────────────────────
    floor_slab(8, 220, 174, 4, (46, 44, 50), (108, 106, 114))
    rails(12, 216, 172)
    flatcar(40, 162, 32, "crates")
    flatcar(120, 162, 30, "ore")
    for i in range(5):                                          # the grade, drawn as a wedge
        rect(150 + i * 14, 170 - i, 164 + i * 14, 172 - i, MET_D)
    player(96, 161)
    tk_beam(103, 165, 130, 160, CYAN)
    humanoid(180, 161, MET_L, RED, face_right=False)
    crate(24, 166); crate(200, 166, 7, False)
    hopper(96, 126, 40, 22)
    lamp(64, 128, bulb=(255, 226, 150), tint=(255, 214, 150), r=20, strength=0.22)
    ragdoll(168, 158)

    # ── 3  turntable pit ────────────────────────────────────────────────────
    floor_slab(232, 340, 176, 4, (46, 44, 50), (108, 106, 114))
    disc(286, 174, 30, (54, 52, 58))
    ring(286, 174, 30, MET_XL)
    ring(286, 174, 22, MET)
    rails(258, 316, 156)
    rect(284, 150, 288, 176, MET_D)                             # spindle
    disc(286, 152, 4, MET_L)
    for a in range(6):                                          # spokes under the deck
        ang = a * math.pi / 3
        line(286, 174, 286 + math.cos(ang) * 28, 174 + math.sin(ang) * 28, MET_D, 0.7)
    flatcar(262, 146, 30)
    humanoid(320, 160, DIRT_L, GREEN, face_right=False)
    lamp(300, 124, bulb=(255, 226, 150), tint=(255, 214, 150), r=20, strength=0.22)
    sparks(262, 156, 10, 12)

    # ── 4  hopper road ──────────────────────────────────────────────────────
    floor_slab(272, 392, 106, 4, (46, 44, 50), (108, 106, 114))
    rails(276, 388, 104)
    hopper(300, 58, 44, 26)
    flatcar(292, 94, 30, "ore")
    humanoid(356, 94, MET_L, RED, face_right=False)
    binny(340, 74)
    for _ in range(18):
        px(276 + rnd() * 112, 100 + rnd() * 4, pick([DIRT, DIRT_L, CHAR]))

    # ── 5  departure road ───────────────────────────────────────────────────
    floor_slab(330, 392, 172, 4, (46, 44, 50), (108, 106, 114))
    rails(334, 390, 170)
    signal(342, 152, red=False)
    door(352, 132, 30, 30)
    glow(367, 147, 22, PALE_G, 0.16)
    flatcar(334, 160, 26)

    # ── 6  runaway sump ─────────────────────────────────────────────────────
    floor_slab(96, 268, 210, 4, (46, 44, 50), (108, 106, 114))
    for i in range(7):                                          # buffer stop, already flattened
        rect(248 - i * 2, 196 + i, 264, 198 + i, RUST)
    flatcar(184, 200, 30)
    rect(184, 198, 214, 206, (70, 44, 34))                      # crumpled
    ragdoll(228, 200)
    ragdoll(148, 204)
    rubble(98, 202, 264, 210, 40, (RUST, MET_D, DIRT))
    liquid_pool(98, 208, 178, 213, (52, 60, 50), (110, 140, 100))

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 08:  THE RAIL YARD")
    callout(6, 24, "1 SURFACE SIDING - SPAWN", 40, 40)
    callout(124, 22, "2 UPPER YARD - CHOCKS, NOT BRAKES", 66, 100)
    callout(272, 30, "4 HOPPER ROAD - DROPS ON CUE", 322, 90)
    callout(6, 114, "3 LOWER YARD - LET ONE ROLL", 152, 166)
    callout(226, 114, "5 TURNTABLE - SPINS WHAT STANDS ON IT", 286, 168)
    callout(276, 196, "6 RUNAWAY SUMP - WHERE IT ENDS", 232, 202)
    callout(300, 210, "7 DEPARTURE ROAD", 356, 160)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("MASS IS THE WEAPON", (170, 180, 195)),
        ("EVERY CAR IS A HELD BRAKE", (200, 150, 90)),
        ("GOAL: DERAIL ONE INTO THE GATE", GREEN_L),
    ], width=126)

    return save(out_path("LevelConcept_RailYard.png"))


if __name__ == "__main__":
    build()
