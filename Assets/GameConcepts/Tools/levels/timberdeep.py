"""Concept 16 - TIMBER DEEP.

The mine's own sawmill, sunk below the workings so the pit props never see daylight.
Everything structural down here is also fuel: the roof is held up by the same stock
the saws are cutting, and MaterialLibrary.Wood burns. One fire in the log store is
both the way through the level and the reason the level lands on you.

No surface, no labels — the read is warm wood against cold rock, and the ember ramp
marking where it has already started.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

LAMP_TINT = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def rock_teeth(x0, x1, y, n=12, c=ROCK_M, tip=ROCK_L):
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0))
        ln = 3 + int(rnd() * 7)
        for k in range(ln):
            half = max((ln - k) // 4, 0)
            rect(x - half, y + k, x + half, y + k, c if k < ln - 1 else tip)


def log_stack(x, base, cols=5, rows=3, r=3, burn=0):
    """Round stock seen end-on. Stacked, so a support failure rolls the whole face."""
    for row in range(rows):
        for col in range(cols):
            cx = x + col * (r * 2 + 1) + (r if row % 2 else 0)
            cy = base - r - row * (r * 2 - 1)
            disc(cx, cy, r, WOOD)
            disc(cx, cy, r - 1, WOOD_D)
            ring(cx, cy, r, WOOD_L)
            px(cx, cy, WOOD_L)
    if burn:
        top = base - rows * (r * 2 - 1) - r
        fire_patch(x + 2, top - 2, x + burn, top + 5, 14, 1.2)
        embers(x, top - 10, x + burn, base - 2, 24)
        for _ in range(10):                              # char creeping down the face
            px(x + rnd() * burn, top + 4 + rnd() * (base - top - 4), CHAR, 0.8)


def plank_stack(x, base, w=22, layers=5, burn=False):
    for i in range(layers):
        yy = base - i * 3
        rect(x, yy - 1, x + w, yy, WOOD if i % 2 else WOOD_L)
        rect(x, yy, x + w, yy, WOOD_D)
    if burn:
        for _ in range(10):
            px(x + rnd() * w, base - rnd() * layers * 3, pick([F_MID, F_COOL]), 0.9)


def saw_bench(x, y, w=34, blade=8):
    """Bench with a circular blade proud of the table - Hazards/Grinder, in a shop."""
    rect(x, y, x + w, y + 3, MET_D)
    rect(x, y, x + w, y, MET_L)
    for lx in (x + 3, x + w - 4):
        rect(lx, y + 4, lx + 1, y + 12, MET_D)
    gear(x + w // 2, y - 1, blade, teeth=14, c=MET_L, lit=MET_XL, hub=MET_D)
    sparks(x + w // 2 + blade - 2, y - 2, 10, 10)
    for _ in range(8):                                   # sawdust off the cut
        px(x + w // 2 + blade + rnd() * 8, y + 1 + rnd() * 5, pick([WOOD_L, DIRT_L]), 0.8)
    rect(x + 4, y - 2, x + w // 2 - blade - 1, y - 1, WOOD)   # stock on the table


def line_shaft(x0, x1, y, drops=()):
    """Ceiling shaft with pulleys - what tells you the saws are all one machine."""
    rect(x0, y, x1, y + 1, MET_D)
    rect(x0, y, x1, y, MET_L)
    for x in range(int(x0) + 8, int(x1) - 4, 22):
        disc(x, y + 3, 2.4, MET)
        ring(x, y + 3, 2.4, MET_XL)
        rect(x - 1, y + 1, x + 1, y + 1, MET_D)
    for bx, by in drops:                                 # belt down to a bench
        line(bx - 1, y + 3, bx - 1, by, WOOD_D)
        line(bx + 1, y + 3, bx + 1, by, WOOD)


def pit_prop(x, y0, y1, cracked=False, gone=False, burning=False):
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
    if burning:
        rect(x, y1 - 12, x + 3, y1, CHAR)
        fire_patch(x - 2, y1 - 16, x + 5, y1 - 2, 18, 1.3)
        embers(x - 3, y1 - 26, x + 6, y1 - 10, 20)


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


def kiln(x, y, w=40, h=26):
    """Charring oven: brick shell, a mouth full of ember, char raked out in front."""
    rect(x, y, x + w, y + h, (86, 62, 52))
    frame(x, y, x + w, y + h, (120, 90, 72))
    for yy in range(int(y) + 3, int(y + h), 5):           # courses
        rect(x + 1, yy, x + w - 1, yy, (66, 48, 40))
    mx0, mx1 = x + w // 2 - 7, x + w // 2 + 7
    rect(mx0, y + h - 12, mx1, y + h - 1, INK)
    fire_patch(mx0 + 1, y + h - 11, mx1 - 1, y + h - 2, 22, 1.5)
    glow((mx0 + mx1) / 2, y + h - 6, 26, F_MID, 0.30)
    rect(x + w // 2 - 2, y - 5, x + w // 2 + 2, y, MET_D)  # flue
    steam_plume(x + w // 2, y - 6, 14, 26, (120, 110, 104))
    for _ in range(24):                                   # raked char
        px(mx0 - 12 + rnd() * 34, y + h + rnd() * 3, pick([CHAR, F_COOL, (52, 44, 40)]))


def build():
    new_canvas(400, 225, seed=51602)

    # ── solid rock, top to bottom ───────────────────────────────────────────
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=20)
    for _ in range(40):
        rect(rnd() * W, rnd() * 18, rnd() * W + 6, rnd() * 18 + 1, ROCK_D, 0.5)

    ROOMS = [
        (8, 12, 186, 60),       # log store
        (14, 74, 246, 136),     # saw floor
        (256, 16, 392, 88),     # prop gallery
        (40, 150, 296, 208),    # kiln floor
        (306, 148, 392, 202),   # exit adit
        (150, 54, 178, 80),     # log drop to the saws
        (240, 60, 268, 92),     # gallery -> saw floor
        (60, 130, 92, 156),     # saw floor -> kiln
        (216, 130, 250, 156),   # saw floor -> kiln, east
        (288, 156, 314, 190),   # kiln -> adit
    ]
    carve_all(ROOMS)

    # ── 1  log store ────────────────────────────────────────────────────────
    floor_slab(8, 186, 54, 4, ROCK_D, ROCK_L)
    rock_teeth(12, 182, 14, 14)
    log_stack(16, 53, 6, 3, 3)
    log_stack(70, 53, 5, 3, 3, burn=30)                  # the stack already going
    log_stack(130, 53, 4, 2, 3)
    line(10, 20, 184, 20, MET_D)                         # gantry rail
    line(10, 21, 184, 21, MET_L)
    for cx in (52, 118, 166):
        chain(cx, 22, 34)
    rect(160, 34, 174, 40, MET)                          # grab, holding a log
    rect(160, 34, 174, 34, MET_L)
    disc(178, 44, 3, WOOD)
    ring(178, 44, 3, WOOD_L)
    humanoid(112, 42, MET_L, DIRT_L, face_right=False)
    humanoid(150, 42, DIRT_L, RED, face_right=False)
    lamp(36, 15, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    lamp(140, 15, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)
    glow(88, 44, 34, F_MID, 0.22)

    # ── 2  the drop, with a log on the way down ─────────────────────────────
    for i in range(4):
        rect(152 + i, 58 + i * 5, 176 - i, 59 + i * 5, WOOD_D)
    disc(164, 70, 3, WOOD)
    ring(164, 70, 3, WOOD_L)

    # ── 3  saw floor ────────────────────────────────────────────────────────
    floor_slab(14, 246, 130, 5, ROCK_D, ROCK_L)
    rock_teeth(18, 242, 76, 16)
    line_shaft(16, 244, 80, drops=((60, 106), (140, 100), (206, 106)))
    saw_bench(44, 118, 34, 8)
    saw_bench(124, 112, 30, 7)
    saw_bench(190, 118, 32, 8)
    plank_stack(18, 129, 20, 6)
    plank_stack(96, 129, 22, 5, burn=True)
    plank_stack(228, 129, 16, 4)
    for _ in range(30):                                  # sawdust drift on the floor
        px(20 + rnd() * 220, 126 + rnd() * 4, pick([WOOD_L, DIRT_L]), 0.7)
    conveyor(160, 224, 96, direction=1, chevron=WOOD_L)  # off-cuts leaving the shop
    for _ in range(16):
        rect(162 + rnd() * 58, 93 + rnd() * 2, 164 + rnd() * 6, 94 + rnd() * 2, WOOD)
    fire_patch(96, 118, 118, 128, 20, 1.4)
    embers(90, 104, 124, 128, 30)
    glow(107, 122, 30, F_MID, 0.24)
    humanoid(66, 118, MET_L, GREEN, face_right=False)
    humanoid(148, 118, DIRT_L, WOOD_L)
    player(166, 118)
    binny(178, 110)
    tk_beam(172, 122, 196, 108)                          # a plank held mid-air
    rect(190, 106, 206, 108, WOOD)
    rect(190, 106, 206, 106, WOOD_L)
    ragdoll(216, 114)
    for lx in (30, 168, 236):
        lamp(lx, 76, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.26)

    # ── 4  prop gallery - stock in place, holding the roof ──────────────────
    floor_slab(256, 392, 84, 4, DIRT_D, DIRT)
    sag(300, 352, 20, 6)
    for pxx, cracked, gone, burning in ((262, False, False, False), (286, True, False, False),
                                        (312, False, True, False), (336, True, False, True),
                                        (364, False, False, False), (386, False, False, False)):
        pit_prop(pxx, 21, 84, cracked, gone, burning)
    plank(258, 20, 390, 20, 2)
    plank_stack(266, 82, 18, 4)
    log_stack(356, 83, 3, 2, 3)
    falling_chunk(310, 30, 6)
    falling_chunk(318, 44, 4)
    rubble(300, 78, 352, 83, 34, (ROCK_M, ROCK_D, DIRT))
    humanoid(288, 72, DIRT_L, RED, face_right=False)
    humanoid(370, 72, MET_L, DIRT_L, face_right=False)
    tracer(368, 76, 344, 74)
    lamp(274, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    lamp(380, 21, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.24)
    for ax, bx in ((262, 286), (336, 364)):              # cross-bracing between props
        line(ax + 3, 40, bx, 62, WOOD_D)
        line(ax + 3, 62, bx, 40, WOOD_D)
    plank(258, 52, 312, 52, 2)                           # staging shelf, half loaded
    plank_stack(276, 51, 16, 3)
    for cx in (298, 350):
        chain(cx, 22, 34)
    cable(258, 26, 330, 28, 4)
    cable(330, 28, 390, 25, 4)
    crate(320, 76); crate(330, 76, 7, False)
    rock_teeth(258, 300, 21, 8)
    for _ in range(18):
        px(258 + rnd() * 132, 78 + rnd() * 5, pick([WOOD_L, DIRT_L, CHAR]), 0.7)

    # ── 5  kiln floor ──────────────────────────────────────────────────────
    floor_slab(40, 296, 202, 5, DIRT_D, DIRT)
    rock_teeth(44, 292, 152, 14)
    kiln(64, 176, 40, 26)
    kiln(176, 176, 40, 26)
    plank(42, 154, 294, 154, 2)
    for pxx in (52, 130, 240, 286):
        pit_prop(pxx, 155, 202, cracked=(pxx == 130))
    for _ in range(40):                                  # char and cinder underfoot
        px(46 + rnd() * 246, 198 + rnd() * 4, pick([CHAR, (52, 44, 40), F_COOL]), 0.85)
    plank_stack(140, 201, 24, 5)
    log_stack(226, 201, 3, 2, 3)
    barrel(120, 195, WOOD, WOOD_L, MET_L)
    barrel(128, 195, WOOD, WOOD_L, MET_L)
    crate(252, 195); crate(262, 195, 7, False)
    humanoid(112, 190, MET_L, RED)
    humanoid(232, 190, DIRT_L, GREEN, face_right=False)
    ragdoll(160, 186)
    embers(60, 170, 220, 200, 40)
    lamp(150, 155, drop=4, bulb=LAMP_TINT, tint=LAMP_TINT, r=20, strength=0.22)
    binny(276, 188)

    # ── 6  exit adit ───────────────────────────────────────────────────────
    floor_slab(306, 392, 196, 5, DIRT_D, DIRT)
    rock_teeth(310, 388, 150, 10)
    plank(308, 172, 390, 176, 2)
    for pxx in (322, 356):
        beam(pxx, 176, 196, 2, WOOD_D, WOOD)
    rails(310, 388, 194)
    cart(330, 185)
    door(360, 168, 26, 28)
    glow(373, 182, 20, PALE_G, 0.16)
    lamp(330, 152, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.24)

    vignette()
    return save(out_path("LevelConcept_TimberDeep.png"))


if __name__ == "__main__":
    build()
