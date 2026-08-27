"""Concept 11 - THE TEMPLE VAULT.

Something older than the machinery, dug into by it. Straight lines and columns instead of
pipes and belts — and the columns are the level: templebrick is heavy, it holds up the nave,
and the support pass does not care that a column is beautiful.

The reward for wrecking the place is the fastest route through it, which is the trade the
level keeps offering: every shortcut costs a piece of the room you are standing in.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 42
STONE = (132, 122, 100)
STONE_L = (178, 166, 138)
STONE_D = (82, 76, 62)
GOLD = (214, 176, 84)
GOLD_L = (255, 226, 140)


def relief(x0, x1, y, h=10):
    """Carved band. Reads as authored stonework rather than rock at a glance."""
    rect(x0, y, x1, y + h, STONE)
    rect(x0, y, x1, y, STONE_L)
    rect(x0, y + h, x1, y + h, STONE_D)
    for x in range(int(x0) + 3, int(x1) - 3, 8):
        rect(x, y + 2, x + 4, y + h - 2, STONE_D, 0.5)
        px(x + 2, y + h // 2, GOLD)


def brazier_stand(x, y):
    rect(x - 1, y, x + 5, y + 12, STONE)
    rect(x - 4, y - 4, x + 8, y, STONE_L)
    fire_patch(x - 4, y - 10, x + 8, y - 1, 12, 1.3)
    glow(x + 2, y - 6, 28, F_MID, 0.30)
    embers(x - 3, y - 18, x + 7, y - 8, 10)


def idol(x, base, h=30):
    rect(x - 8, base - h, x + 8, base, STONE)
    rect(x - 8, base - h, x - 8, base, STONE_L)
    rect(x - 6, base - h + 4, x + 6, base - h + 14, STONE_D)
    disc(x, base - h - 6, 7, STONE)
    ring(x, base - h - 6, 7, STONE_L)
    px(x - 3, base - h - 7, GOLD_L)
    px(x + 3, base - h - 7, GOLD_L)
    glow(x, base - h - 6, 20, GOLD, 0.16)


def hoard(x0, x1, y, n=40):
    for _ in range(n):
        hx = x0 + rnd() * (x1 - x0)
        hy = y - rnd() * 8
        rect(hx, hy, hx + 1 + rnd() * 3, hy + 1, pick([GOLD, GOLD_L, (180, 150, 70)]))
    glow((x0 + x1) / 2, y - 2, (x1 - x0) * 0.5, GOLD, 0.20)


def build():
    new_canvas(400, 225, seed=1111)

    sky(SURF, hi=(118, 108, 96), lo=(74, 68, 62), smog=7)
    for _ in range(50):
        px(rnd() * W, rnd() * SURF, (196, 178, 146), 0.16)
    rock_mass(SURF, base=(70, 66, 60), dark=(46, 44, 40), mid=(92, 88, 80),
              soil=(84, 74, 56), soil_lit=(142, 126, 94))

    ROOMS = [
        (8, 58, 206, 124),      # the nave
        (8, 140, 150, 196),     # crypt
        (30, 116, 76, 148),     # nave -> crypt
        (212, 54, 330, 120),    # collapsed transept
        (196, 78, 218, 100),    # nave -> transept
        (150, 140, 300, 200),   # processional
        (236, 112, 274, 148),   # transept -> processional
        (306, 56, 392, 132),    # the vault
        (300, 138, 392, 200),   # exit stair
        (286, 96, 312, 118),    # transept -> vault
    ]
    carve_all(ROOMS, air=(22, 22, 24), lip=(86, 82, 72))

    # ── surface: the dig that found it ──────────────────────────────────────
    scrap_pile(10, SURF, 60, 11, (DIRT, DIRT_D, STONE_D, ROCK_M))
    scrap_pile(300, SURF, 70, 12, (DIRT, DIRT_D, STONE_D, ROCK_M))
    relief(120, 240, SURF - 12, 10)
    beam(104, SURF - 26, SURF, 3)
    beam(246, SURF - 26, SURF, 3)
    rect(100, SURF - 28, 250, SURF - 26, WOOD_L)
    player(150, SURF - 12)
    binny(166, SURF - 22, eye=GOLD_L)
    humanoid(268, SURF - 12, DIRT_L, RED, face_right=False)

    # ── 1  the nave ─────────────────────────────────────────────────────────
    floor_slab(8, 206, 120, 4, (48, 46, 42), (112, 106, 92))
    relief(10, 204, 58, 8)
    for cx in (34, 78, 122, 166):
        column(cx, 68, 120, 8)
    for cx in (56, 100, 144):
        arch(cx, 70, 40, 12, STONE, STONE_L)
    brazier_stand(24, 108)
    brazier_stand(190, 108)
    humanoid(96, 108, STONE_L, GOLD, face_right=False)      # temple guard
    humanoid(150, 108, STONE_L, GOLD, face_right=False)
    player(60, 108)
    tk_beam(67, 112, 100, 100, GOLD_L)
    rubble(12, 114, 202, 119, 34, (STONE_D, STONE, DIRT))
    for _ in range(9):                                       # dust in the beams
        px(20 + rnd() * 180, 62 + rnd() * 50, (200, 186, 150), 0.30)

    # ── 2  crypt ────────────────────────────────────────────────────────────
    floor_slab(8, 150, 192, 4, (48, 46, 42), (112, 106, 92))
    for i, sx in enumerate(range(16, 140, 26)):              # slab tombs, one open
        rect(sx, 178, sx + 20, 190, STONE)
        rect(sx, 178, sx + 20, 178, STONE_L)
        if i == 2:
            rect(sx + 2, 176, sx + 22, 178, STONE_D)
            for k in range(6):
                px(sx + 4 + k * 3, 182 + int(rnd() * 4), (40, 40, 44))
    column(60, 148, 178, 7)
    column(112, 148, 178, 7)
    ragdoll(92, 170)
    humanoid(130, 166, ICE_L, PURPLE, face_right=False)
    lamp(84, 142, bulb=GOLD_L, tint=GOLD, r=20, strength=0.20)
    hoard(20, 44, 176, 18)

    # ── 3  collapsed transept ───────────────────────────────────────────────
    floor_slab(212, 330, 116, 4, (48, 46, 42), (112, 106, 92))
    for cx, broken in ((228, False), (266, True), (304, False)):
        if broken:
            column(cx, 92, 116, 8)                           # snapped off at head height
            for _ in range(12):
                bx = cx - 10 + rnd() * 28
                rect(bx, 100 + rnd() * 14, bx + 4, 102 + rnd() * 14, STONE_D)
        else:
            column(cx, 62, 116, 8)
    arch(248, 64, 46, 14, STONE, STONE_L, broken=True)
    for _ in range(16):                                      # roof already coming in
        fx = 216 + rnd() * 108
        rect(fx, 58 + rnd() * 24, fx + 4, 60 + rnd() * 24, ROCK_M)
    rubble(214, 108, 326, 115, 40, (STONE_D, ROCK_M, DIRT))
    humanoid(292, 104, STONE_L, GOLD, face_right=False)
    brazier_stand(222, 104)

    # ── 4  processional ─────────────────────────────────────────────────────
    floor_slab(150, 300, 196, 4, (48, 46, 42), (112, 106, 92))
    relief(152, 298, 142, 9)
    for cx in (170, 210, 250, 286):
        column(cx, 152, 196, 7)
    for i in range(6):                                       # steps up to the vault
        rect(266 + i * 6, 190 - i * 6, 300, 192 - i * 6, STONE)
        rect(266 + i * 6, 190 - i * 6, 300, 190 - i * 6, STONE_L)
    idol(196, 194, 28)
    humanoid(236, 184, STONE_L, GOLD)
    player(160, 184)
    binny(176, 168, eye=GOLD_L)
    hoard(216, 240, 192, 26)

    # ── 5  the vault ────────────────────────────────────────────────────────
    floor_slab(306, 392, 128, 4, (48, 46, 42), (112, 106, 92))
    relief(308, 390, 60, 8)
    column(320, 72, 128, 8)
    column(372, 72, 128, 8)
    idol(346, 126, 34)
    hoard(312, 386, 124, 60)
    glow(346, 100, 44, GOLD, 0.22)
    for _ in range(20):
        px(310 + rnd() * 78, 74 + rnd() * 46, GOLD_L, 0.4)
    humanoid(314, 116, STONE_L, GOLD)

    # ── 6  exit stair ───────────────────────────────────────────────────────
    floor_slab(300, 392, 196, 4, (48, 46, 42), (112, 106, 92))
    stairs(304, 190, 8, 9, 6, STONE_D, STONE_L)
    door(352, 150, 30, 30, STONE, GOLD_L, STONE_D)
    glow(367, 165, 24, GOLD, 0.18)
    brazier_stand(316, 176)

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 11:  THE TEMPLE VAULT")
    callout(6, 24, "1 THE DIG - SPAWN", 152, 38)
    callout(112, 22, "2 THE NAVE - COLUMNS HOLD THE ROOF", 78, 90)
    callout(280, 26, "5 THE VAULT - TAKE IT AND RUN", 346, 100)
    callout(6, 128, "3 CRYPT - SOMETHING WAS LET OUT", 60, 176)
    callout(212, 40, "4 TRANSEPT - ONE COLUMN ALREADY GONE", 266, 96)
    callout(164, 208, "6 PROCESSIONAL - GUARDED", 210, 176)
    callout(300, 212, "7 EXIT STAIR", 356, 168)
    legend(6, 188, [
        ("BEATS", CYAN),
        ("STONE IS HEAVY AND LOAD-BEARING", (170, 180, 195)),
        ("EVERY SHORTCUT COSTS A ROOM", (200, 150, 90)),
        ("GOAL: LOOT THE VAULT, GET OUT", GREEN_L),
    ], width=148)

    return save(out_path("LevelConcept_TempleVault.png"))


if __name__ == "__main__":
    build()
