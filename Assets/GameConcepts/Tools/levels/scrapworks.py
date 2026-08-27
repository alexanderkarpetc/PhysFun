"""Concept 02 - THE SCRAPWORKS.

Industrial opener. Teaches the three toys in order: telekinesis (throw the barrel
at the sniper), fire (wood burns, rock does not), and the belt hazards. Goal is a
delivery loop rather than a kill count — fill Binny, the vault opens.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 52


def build():
    new_canvas(400, 225, seed=1337)
    sky(SURF)

    # ── horizon: smelter row ────────────────────────────────────────────────
    def stack(x, top, w):
        rect(x, top, x + w, SURF, (66, 72, 84))
        rect(x, top, x + w, top, (86, 94, 108))
        rect(x + w, top + 2, x + w, SURF, (48, 53, 62))
        sx = x + w // 2
        for i in range(16):
            sx += -1 if chance(0.5) else 1
            disc(sx, top - 2 - i * 2, 1.4 + i * 0.22, (180, 188, 200), 0.13)

    stack(18, 20, 6); stack(40, 28, 4); stack(300, 24, 7); stack(330, 33, 5)
    for hx, hy in ((52, 38), (250, 34)):
        rect(hx, hy, hx + 44, SURF, (58, 64, 76))
        rect(hx, hy, hx + 44, hy, (80, 88, 102))
        for x in range(hx + 2, hx + 42, 7):
            rect(x, hy + 4, x + 3, hy + 8, (38, 43, 52))

    rock_mass(SURF)

    ROOMS = [
        (6, 100, 196, 146),     # conveyor hall
        (104, 56, 128, 104),    # entry shaft
        (46, 150, 158, 208),    # grinder pit
        (150, 150, 196, 176),   # pit -> furnace crawl
        (196, 146, 306, 210),   # furnace
        (198, 62, 300, 112),    # sniper gallery
        (296, 60, 396, 150),    # recycler hall
        (300, 150, 340, 210),   # lift chimney
        (180, 108, 206, 128),   # hall -> gallery link
        (296, 112, 320, 132),   # gallery -> recycler link
        (336, 150, 396, 200),   # exit vault
    ]
    carve_all(ROOMS)

    # ── 1  scrap yard ───────────────────────────────────────────────────────
    scrap_pile(6, SURF, 44, 14)
    scrap_pile(132, SURF, 60, 16)
    scrap_pile(210, SURF, 34, 10)

    tx, ty = 60, SURF - 11                       # wrecked truck
    rect(tx, ty, tx + 26, ty + 8, RED)
    rect(tx, ty, tx + 26, ty, RED_L)
    rect(tx + 18, ty - 6, tx + 26, ty, (96, 44, 44))
    rect(tx + 20, ty - 4, tx + 24, ty - 1, BLUE_L)
    rect(tx, ty + 8, tx + 26, ty + 9, MET_D)
    for wx in (tx + 5, tx + 21):
        disc(wx, ty + 10, 3, INK)
        disc(wx, ty + 10, 1.4, MET)

    beam(96, SURF - 26, SURF, 2)                 # winch scaffold over the shaft
    beam(126, SURF - 26, SURF, 2)
    rect(94, SURF - 28, 130, SURF - 26, WOOD_L)
    plank(96, SURF - 18, 128, SURF - 18)
    line(112, SURF - 26, 112, SURF - 6, MET_L)
    rect(109, SURF - 8, 115, SURF - 4, MET)
    rect(90, SURF - 3, 134, SURF - 1, MET_D)
    rect(90, SURF - 3, 134, SURF - 3, MET_L)

    player(100, SURF - 12)
    binny(112, SURF - 22)
    humanoid(206, SURF - 12, MET_L, GREEN, face_right=False)
    humanoid(224, SURF - 12, DIRT_L, RED, face_right=False)
    tracer(204, SURF - 7, 190, SURF - 5)

    # ── 2  winch shaft ──────────────────────────────────────────────────────
    rect(104, 56, 105, 104, MET_D)
    rect(127, 56, 128, 104, MET_D)
    ladder(106, 58, 104)
    plank(106, 74, 126, 76, 2)
    plank(106, 90, 120, 92, 2, burn=True)
    rubble(108, 60, 124, 102, 9, (DIRT_L,))

    # ── 3  conveyor hall ────────────────────────────────────────────────────
    floor_slab(6, 196, 142)
    conveyor(20, 120, 136, 1)
    conveyor(96, 190, 120, -1)
    crate(28, 128); crate(52, 128); crate(84, 128, 7, False)
    crate(140, 112); crate(166, 112)
    plank(104, 104, 96, 118, 2)                  # chute out of the shaft
    plank(112, 104, 120, 116, 2)
    catwalk(10, 62, 116, drop=6, posts=12)
    humanoid(30, 105, MET_L, GREEN)
    humanoid(48, 105, DIRT_L, GREEN)
    tracer(41, 110, 74, 126)
    lamp(76, 100); lamp(150, 100)
    rect(188, 120, 194, 142, MET)                # crate-fed gate
    for y in range(122, 142, 4):
        rect(188, y, 194, y, MET_D)
    rect(186, 118, 196, 120, MET_XL)

    # ── 4  grinder pit ──────────────────────────────────────────────────────
    floor_slab(46, 158, 200, 8, ROCK_D, ROCK_D)
    gear(104, 196, 9); gear(126, 198, 7); gear(148, 195, 10)
    for x in range(48, 158, 6):                  # rope bridge, already alight
        line(x, 158 + (2 if (x // 6) % 2 else 0), x + 6, 158 + (0 if (x // 6) % 2 else 2), WOOD_D)
    plank(48, 158, 156, 158, 2)
    fire_patch(92, 152, 132, 160)
    glow(112, 156, 26, F_MID, 0.30)
    ragdoll(140, 176)
    ragdoll(92, 182)
    spikes(47, 160, 200, 1)
    spikes(157, 160, 200, -1)

    # ── 5  furnace ──────────────────────────────────────────────────────────
    floor_slab(196, 306, 204, 6, ROCK_D, ROCK_D)
    glow(250, 190, 60, F_COOL, 0.42)
    glow(250, 196, 34, F_MID, 0.35)
    for sx in (214, 240, 268, 292):
        beam(sx, 160, 204)
        for _ in range(14):
            fy = 160 + int(rnd() * 44)
            rect(sx - 1, fy, sx + 4, fy + 1, pick([F_MID, F_COOL, F_HOT]), 0.85)
        embers(sx + 1, 150, sx + 4, 162, 10)
    plank(206, 178, 300, 178, 2, burn=True)
    plank(200, 196, 306, 196, 2, burn=True)
    embers(198, 150, 306, 208, 70)
    rect(196, 186, 202, 204, MET_D)              # furnace mouth
    rect(197, 190, 201, 200, F_MID)
    rect(198, 192, 200, 198, F_HOT)

    # ── 6  sniper gallery ───────────────────────────────────────────────────
    floor_slab(198, 300, 108)
    catwalk(210, 268, 92, drop=15)
    rect(272, 96, 292, 97, MET_D)
    line(268, 93, 274, 100, MET_D)
    humanoid(238, 81, MET_L, BLUE, face_right=False)
    line(236, 86, 196, 104, (200, 60, 60), 0.5)  # laser sight
    disc(196, 104, 1.4, RED_L)
    barrel(216, 100); barrel(224, 100)
    crate(252, 100); crate(260, 100); crate(256, 92)
    crate(282, 100, 7, False)
    rubble(200, 104, 296, 107)
    pipe_run(200, 298, 66)
    lamp(222, 69, r=18, strength=0.20); lamp(262, 69, r=18, strength=0.20)
    humanoid(276, 96, DIRT_L, RED, face_right=False)
    for cx in (204, 296):                        # hanging chain
        for y in range(64, 92, 3):
            px(cx, y, MET_L)
            px(cx + 1, y + 1, MET_D)

    # ── 7  recycler core ────────────────────────────────────────────────────
    floor_slab(296, 396, 146)
    rect(330, 74, 386, 144, MET_D)
    frame(330, 74, 386, 144, MET_L)
    rect(334, 78, 382, 118, (30, 34, 40))
    glow(358, 98, 30, CYAN, 0.30)
    disc(358, 98, 13, (24, 60, 66))
    ring(358, 98, 13, CYAN)
    ring(358, 98, 9, (70, 140, 150))
    disc(358, 98, 5, CYAN)
    disc(358, 98, 2.5, PALE_G)
    for _ in range(26):                          # scrap being swallowed
        import math
        a, rr = rnd() * 6.28, 15 + rnd() * 16
        px(358 + math.cos(a) * rr, 98 + math.sin(a) * rr * 0.8,
           pick([MET_L, GREEN_L, DIRT_L]), 0.9)
    for py in (124, 132):
        rect(300, py, 330, py + 4, MET)
        rect(300, py, 330, py, MET_L)
        for x in range(302, 328, 5):
            rect(x, py + 1, x, py + 3, MET_D)
    for cy in (70, 72):
        line(300, cy, 330, cy + 6, MET_D, 0.9)
    crate(304, 136); crate(313, 136, 7, False)
    rubble(300, 138, 326, 144, 18, (MET_D, GREEN, DIRT_L))

    # ── 8  vault + lift ─────────────────────────────────────────────────────
    door(346, 158)
    glow(363, 177, 26, PALE_G, 0.16)
    rect(300, 150, 302, 210, MET_D)
    rect(338, 150, 340, 210, MET_D)
    for fy in (166, 186, 204):
        line(304, fy, 336, fy + 4, MET_L, 0.9)
        line(304, fy + 4, 336, fy, MET_L, 0.9)
        disc(320, fy + 2, 2, MET_XL)
    rect(304, 152, 336, 154, MET)
    rect(304, 152, 336, 152, MET_XL)
    line(320, 154, 320, 210, MET_D)
    binny(314, 140)
    player(322, 141)

    vignette()

    # ── sheet furniture ─────────────────────────────────────────────────────
    title_bar("PHYSFUN - LEVEL CONCEPT 02:  THE SCRAPWORKS")
    callout(8, 26, "1 SCRAP YARD - SPAWN", 74, 44)
    callout(126, 26, "2 SHAFT - ROTTEN PLANKS", 116, 76)
    callout(258, 26, "7 RECYCLER CORE - FEED BINNY", 350, 84)
    callout(200, 56, "6 SNIPER GALLERY - THROW THE BARRELS", 232, 86)
    callout(6, 90, "3 CONVEYOR HALL - RIDE OR JAM THE BELT", 60, 136)
    callout(150, 158, "5 FURNACE - WOOD BURNS, ROCK DOES NOT", 214, 172)
    callout(6, 166, "4 GRINDER PIT - GEARS FLING CORPSES", 122, 192)
    callout(300, 216, "8 VAULT EXIT", 348, 198)
    legend(6, 186, [
        ("BEATS", CYAN),
        ("TELEKINESIS > FIRE > BELTS", (170, 180, 195)),
        ("TERRAIN CUTS - RAGDOLLS", (170, 180, 195)),
        ("GOAL: FILL BINNY, OPEN VAULT", GREEN_L),
    ])

    return save(out_path("LevelConcept_Scrapworks.png"))


if __name__ == "__main__":
    build()
