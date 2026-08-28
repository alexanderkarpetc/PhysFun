"""Concept 19 - THE WARREN.

Not a hall in sight: fifty small dirt tunnels chewed through a soft seam, stacked five
deep and joined by whatever shaft the crew felt like sinking. The whole sheet is one
argument for destructible terrain - the shortest route between two rooms is usually a
wall, and the wall is dirt.

Which cuts both ways. Dirt is also what is holding the tunnel above yours up, and this
seam is riddled enough that one heavy dig walks a collapse three tiers down. The scar
in the middle of the sheet is what that looks like when it has already happened.

No surface, no labels; the honeycomb is the read.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

# A warmer, softer mass than the other sheets - this is a dirt seam, not stone.
SEAM_D = (44, 38, 30)
SEAM = (68, 59, 45)
SEAM_M = (92, 80, 60)
LAMP_TINT = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def dig_face(x, y, side=1, h=12):
    """The end of a tunnel that is still being worked: fresh face, pick marks, spoil."""
    for k in range(h):
        rect(x, y - k, x + side * (1 + int(rnd() * 3)), y - k, SEAM_M, 0.9)
    for _ in range(9):                                   # pick marks in the face
        my = y - rnd() * h
        line(x, my, x + side * 3, my - 2, DIRT_L, 0.55)
    for _ in range(14):                                  # spoil at the foot of it
        px(x - side * rnd() * 12, y - rnd() * 3, pick([DIRT, DIRT_L, SEAM_M]))


def roots(x0, x1, y, n=10):
    """Hair roots through the roof - the cheapest way to say 'this is soil'."""
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        ln = 2 + rnd() * 5
        for k in range(int(ln)):
            px(x + int((rnd() - 0.5) * 2), y + k, WOOD_D if chance(0.7) else WOOD)


def spoil(x, base, w=18, h=7):
    scrap_pile(x, base, w, h, (DIRT, DIRT_D, DIRT_L, SEAM_M))


def timbering(x0, x1, y0, y1, step=14):
    """Square-set timber: the tunnels the crew thought were worth keeping."""
    for x in range(int(x0), int(x1), step):
        beam(x, y0, y1, 2, WOOD_D, WOOD)
    rect(x0, y0, x1, y0 + 1, WOOD)
    rect(x0, y0, x1, y0, WOOD_L)


def plug(x, y0, y1, w=8):
    """Un-dug dirt between two tunnels - the wall the player is meant to remove."""
    rect(x, y0, x + w, y1, SEAM)
    rect(x, y0, x, y1, SEAM_M)
    for _ in range(w * 2):
        px(x + rnd() * w, y0 + rnd() * (y1 - y0), pick([SEAM_D, SEAM_M, DIRT]), 0.8)
    for _ in range(6):                                   # cracks: it is nearly through
        cy = y0 + rnd() * (y1 - y0)
        line(x, cy, x + w, cy + 2 - rnd() * 4, SEAM_D, 0.8)


def collapse_scar(cx, y0, y1, w=26):
    """A column of the warren that has already fallen into itself."""
    for y in range(int(y0), int(y1)):
        t = (y - y0) / max(y1 - y0, 1)
        half = int(w / 2 * (0.5 + t * 0.5))
        for x in range(cx - half, cx + half):
            if chance(0.55):
                px(x, y, pick([DIRT, DIRT_D, SEAM_M, DIRT_L]))
    for _ in range(16):                                  # dust still hanging in it
        disc(cx + (rnd() - 0.5) * w, y0 + rnd() * (y1 - y0), 1 + rnd() * 3,
             (168, 148, 118), 0.12)
    for _ in range(10):                                  # snapped timber in the column
        sy = y0 + rnd() * (y1 - y0)
        line(cx - w / 2 + rnd() * w, sy, cx - w / 2 + rnd() * w, sy + 4, WOOD_D)


def build():
    new_canvas(400, 225, seed=51905)
    cw, ch = canvas_size()

    # ── the seam: soft, warm, and solid to every edge ───────────────────────
    rock_mass(0, base=SEAM, dark=SEAM_D, mid=SEAM_M, soil=SEAM, soil_lit=SEAM_M, strata=26)
    for _ in range(60):                                  # gravel bands through the dirt
        yy = rnd() * ch
        x = rnd() * cw
        rect(x, yy, x + 6 + rnd() * 22, yy, ROCK_D if chance(0.5) else ROCK_M, 0.55)

    # ── the honeycomb ──────────────────────────────────────────────────────
    TUNNELS = [
        # tier 1
        (10, 14, 60, 32), (74, 16, 128, 34), (142, 14, 190, 32),
        (206, 16, 262, 34), (278, 14, 330, 32), (344, 16, 392, 34),
        # tier 2
        (8, 52, 52, 72), (66, 54, 120, 72), (134, 52, 184, 72),
        (200, 54, 250, 72), (264, 52, 318, 72), (332, 54, 392, 72),
        # tier 3 - the middle of the warren, with one room worth the name
        (14, 94, 68, 112), (82, 92, 138, 112), (150, 92, 244, 126),
        (258, 94, 306, 112), (320, 92, 392, 112),
        # tier 4
        (10, 136, 64, 154), (78, 134, 130, 154), (144, 138, 196, 158),
        (210, 136, 268, 154), (282, 134, 336, 154), (350, 138, 392, 158),
        # tier 5
        (12, 178, 80, 200), (96, 176, 160, 198), (176, 180, 250, 202),
        (266, 176, 330, 198), (344, 178, 392, 200),
        # the shafts and squeezes that join them
        (30, 30, 40, 56), (98, 32, 108, 56), (166, 28, 176, 56),
        (232, 32, 242, 58), (300, 30, 310, 56), (362, 32, 372, 58),
        (22, 70, 32, 96), (88, 70, 98, 94), (158, 70, 168, 96),
        (216, 70, 226, 96), (286, 70, 296, 96), (356, 70, 366, 94),
        (36, 110, 46, 138), (104, 110, 114, 136), (172, 124, 182, 140),
        (232, 124, 242, 138), (296, 110, 306, 136), (368, 110, 378, 140),
        (26, 152, 36, 180), (110, 152, 120, 178), (188, 156, 198, 182),
        (240, 152, 250, 180), (310, 152, 320, 178), (376, 156, 386, 180),
    ]
    carve_all(TUNNELS, rough=3)

    # ── the fall line: one column of the warren already gone ───────────────
    collapse_scar(232, 34, 136, 28)

    # ── tier by tier: floors, roots, lamps, spoil ──────────────────────────
    FLOORS = [
        (10, 60, 30), (74, 128, 32), (142, 190, 30), (206, 262, 32),
        (278, 330, 30), (344, 392, 32),
        (8, 52, 70), (66, 120, 70), (134, 184, 70), (200, 250, 70),
        (264, 318, 70), (332, 392, 70),
        (14, 68, 110), (82, 138, 110), (150, 244, 124), (258, 306, 110),
        (320, 392, 110),
        (10, 64, 152), (78, 130, 152), (144, 196, 156), (210, 268, 152),
        (282, 336, 152), (350, 392, 156),
        (12, 80, 198), (96, 160, 196), (176, 250, 200), (266, 330, 196),
        (344, 392, 198),
    ]
    for x0, x1, y in FLOORS:
        floor_slab(x0, x1, y, 3, SEAM_D, DIRT_L)

    for x0, y0, x1, y1 in TUNNELS[:28]:                  # roof roots in the rooms only
        roots(x0 + 3, x1 - 3, y0 + 1, max(int((x1 - x0) / 8), 3))

    for lx, ly in ((30, 15), (100, 17), (168, 15), (300, 15), (368, 17),
                   (26, 53), (94, 55), (160, 53), (226, 55), (292, 53), (360, 55),
                   (34, 95), (108, 93), (196, 93), (280, 95), (352, 93),
                   (30, 137), (100, 135), (168, 139), (236, 137), (304, 135), (370, 139),
                   (36, 179), (124, 177), (208, 181), (296, 177), (366, 179)):
        lamp(lx, ly, drop=3, bulb=LAMP_TINT, tint=LAMP_TINT, r=15, strength=0.24)

    # ── working faces, un-dug plugs, timbering ─────────────────────────────
    dig_face(58, 30, 1, 14)
    dig_face(120, 32, 1, 12)
    dig_face(146, 30, -1, 14)
    dig_face(322, 30, 1, 12)
    dig_face(50, 70, 1, 16)
    dig_face(316, 70, 1, 16)
    dig_face(60, 110, 1, 14)
    dig_face(190, 156, 1, 16)
    dig_face(78, 196, 1, 16)
    dig_face(326, 196, 1, 16)

    plug(60, 52, 72, 7)                                  # tier 2, two rooms apart
    plug(184, 52, 72, 8)
    plug(138, 92, 112, 9)                                # into the big chamber
    plug(244, 96, 124, 10)
    plug(64, 136, 154, 8)
    plug(160, 178, 198, 9)

    timbering(66, 118, 54, 72)
    timbering(210, 266, 136, 154)
    timbering(266, 328, 176, 198)

    spoil(14, 30, 22, 6); spoil(210, 32, 26, 7); spoil(346, 32, 24, 6)
    spoil(202, 70, 24, 7); spoil(334, 70, 26, 7)
    spoil(84, 110, 26, 8); spoil(322, 110, 30, 8)
    spoil(80, 152, 24, 7); spoil(352, 156, 26, 7)
    spoil(98, 196, 32, 9); spoil(268, 196, 28, 8)

    # ── ladders in the shafts ──────────────────────────────────────────────
    for lx, y0, y1 in ((31, 32, 55), (167, 30, 55), (301, 32, 55),
                       (23, 72, 95), (159, 72, 95), (287, 72, 95),
                       (37, 112, 137), (105, 112, 135), (297, 112, 135),
                       (27, 154, 179), (111, 154, 177), (311, 154, 177)):
        ladder(lx, y0, y1, w=4, step=6)

    # ── the middle chamber: the one place the warren opens up ──────────────
    timbering(152, 242, 94, 124, 18)
    plank(152, 108, 242, 108, 2)                          # a stage across it
    for pxx in (166, 200, 230):
        beam(pxx, 108, 124, 2, WOOD_D, WOOD)
    cart(206, 113)
    crate(158, 116); crate(168, 116, 7, False)
    barrel(180, 117, WOOD, WOOD_L, MET_L)
    player(190, 112)
    binny(178, 100)
    tk_beam(196, 116, 224, 104)
    rect(218, 100, 232, 106, SEAM_M)                      # a slab of dirt held mid-air
    rect(218, 100, 232, 100, DIRT_L)
    humanoid(154, 112, MET_L, GREEN, face_right=False)
    humanoid(236, 112, DIRT_L, RED, face_right=False)
    lamp(196, 93, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=26, strength=0.28)
    lamp(228, 93, drop=5, bulb=LAMP_TINT, tint=LAMP_TINT, r=22, strength=0.22)
    roots(152, 242, 93, 14)

    # ── crew, carts and casualties scattered through the honeycomb ─────────
    humanoid(20, 21, DIRT_L, DIRT_L)
    humanoid(88, 23, MET_L, RED, face_right=False)
    humanoid(288, 21, DIRT_L, GREEN)
    humanoid(76, 59, DIRT_L, RED, face_right=False)
    humanoid(272, 59, MET_L, DIRT_L)
    humanoid(340, 61, DIRT_L, GREEN, face_right=False)
    humanoid(20, 99, MET_L, RED)
    humanoid(266, 99, DIRT_L, DIRT_L, face_right=False)
    humanoid(18, 141, DIRT_L, GREEN)
    humanoid(120, 141, MET_L, RED, face_right=False)
    humanoid(292, 141, DIRT_L, DIRT_L, face_right=False)
    humanoid(20, 187, MET_L, GREEN)
    humanoid(140, 185, DIRT_L, RED, face_right=False)
    humanoid(300, 185, MET_L, DIRT_L, face_right=False)
    tracer(138, 189, 112, 191)
    tracer(118, 145, 96, 147)
    cart(40, 21); cart(304, 187); cart(120, 187, tipped=True)
    crate(240, 25); crate(360, 27, 7, False)
    crate(206, 145); crate(58, 191)
    ragdoll(212, 130, RED_L)                              # thrown clear of the scar
    ragdoll(246, 148)
    ragdoll(88, 191)

    # ── the scar again, on top, so it reads as the newest thing here ───────
    for _ in range(9):
        x = 220 + rnd() * 24
        y = 40 + rnd() * 90
        w = 3 + rnd() * 3
        rect(x, y, x + w, y + 2, SEAM_M)
        rect(x, y, x + w, y, DIRT_L)
    for _ in range(22):
        px(216 + rnd() * 32, 36 + rnd() * 100, pick([DIRT_L, SEAM_M]), 0.6)

    vignette()
    return save(out_path("LevelConcept_TheWarren.png"))


if __name__ == "__main__":
    build()
