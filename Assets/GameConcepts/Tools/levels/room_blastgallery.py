"""Room concept 06 - THE BLASTING GALLERY (big room).

~3.6 x 3 screens at game scale. A working face at the east end, drilled and charged,
wired back down the drift to a plunger in the shot-firer's hut where you come in; a
powder magazine over your head; a test bay of masonry walls; and a fuse main - a
FuseCord, litByFire - threaded through every chamber to roof charges over the face.

The toy is the blast, and the room is built so that the player is never the only one
who can set it off. Grenadiers throw near the magazine. Pyros light cord without
meaning to (FuseCord catches from fire), so the main is usually burning before long
and the room has a clock. Exit B is behind the face: the way out is to blow the face,
ideally with the brutes standing at it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

FLOOR = 700
LAMP = (255, 214, 140)
CORD = (176, 140, 87)            # FuseCord.cordColor
CORD_D = (115, 84, 48)           # FuseCord.cordShade
WIRE = (180, 80, 70)
SANDBAG = (130, 118, 90)


# ── local props ─────────────────────────────────────────────────────────────
def cord(points):
    """FuseCord laid along a wall: two-tone cord, pinned every so often."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)))
        for i in range(n + 1):
            x = ax + (bx - ax) * i / max(n, 1)
            y = ay + (by - ay) * i / max(n, 1)
            px(x, y, CORD)
            px(x, y + 1, CORD_D)
            if i % 24 == 0:
                px(x, y - 1, MET_L)


def burning(x0, x1, y):
    """A run of cord lit in the middle: charcoal between two sparks, one going each
    way. Cord lit from fire does not pick a direction."""
    rect(x0, y, x1, y + 1, CHAR)
    for sx in (x0, x1):
        disc(sx, y, 2, F_HOT)
        sparks(sx, y, 18, 12)
        glow(sx, y, 20, F_MID, 0.45)
    for k in range(10):
        disc((x0 + x1) / 2 + (rnd() - 0.5) * 20, y - 4 - k * 3, 2 + k * 0.4, (80, 76, 72), 0.18)


def wire(points):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay, bx, by, WIRE)
        line(ax, ay + 1, bx, by + 1, (40, 30, 30))


def plunger(x, floor):
    """Shot-firer's exploder: a box with a T-handle. Push it and the face goes."""
    rect(x, floor - 16, x + 20, floor - 1, WOOD)
    rect(x, floor - 16, x + 20, floor - 16, WOOD_L)
    rect(x + 2, floor - 13, x + 18, floor - 4, WOOD_D)
    text(x + 4, floor - 12, "TNT", HAZARD, shadow=False)
    rect(x + 9, floor - 30, x + 11, floor - 17, MET_L)
    rect(x + 2, floor - 32, x + 18, floor - 30, MET)
    disc(x + 22, floor - 6, 1.5, WIRE)


def keg(x, floor):
    rect(x, floor - 11, x + 8, floor - 1, WOOD)
    rect(x + 1, floor - 12, x + 7, floor - 12, WOOD_L)
    rect(x, floor - 9, x + 8, floor - 9, MET_D)
    rect(x, floor - 3, x + 8, floor - 3, MET_D)
    px(x + 4, floor - 6, INK)


def keg_stack(x, floor, cols, rows):
    for r in range(rows):
        for c in range(cols - r):
            keg(x + c * 10 + r * 5, floor - r * 12)


def boom_crate(x, floor, s=14):
    rect(x, floor - s, x + s, floor - 1, RED)
    frame(x, floor - s, x + s, floor - 1, (90, 40, 40))
    rect(x + 2, floor - s // 2 - 1, x + s - 2, floor - s // 2 + 1, HAZARD)


def blast_shield(x, floor, h=40):
    """Steel plate on two feet: cover you can push, and that a blast will push too."""
    rect(x, floor - h, x + 5, floor - 4, MET)
    rect(x, floor - h, x, floor - 4, MET_XL)
    rect(x + 5, floor - h, x + 5, floor - 4, MET_D)
    for k in range(3):
        px(x + 2, floor - h + 6 + k * 12, MET_D)
    rect(x - 8, floor - 3, x + 13, floor - 1, MET_D)
    line(x + 5, floor - 20, x + 13, floor - 3, MET_D)


def sandbags(x, floor, n=4, rows=2):
    for r in range(rows):
        for k in range(n - r):
            bx = x + k * 12 + r * 6
            by = floor - 6 - r * 6
            rect(bx, by, bx + 11, by + 5, SANDBAG)
            rect(bx, by, bx + 11, by, (170, 156, 120))
            px(bx, by + 5, DIRT_D)


def test_wall(x, floor, h=40, breached=False):
    if breached:
        masonry(x, floor - 8, x + 14, floor - 1)
        for _ in range(40):
            bx = x - 30 + rnd() * 80
            rect(bx, floor - 2 - rnd() * 3, bx + 2 + rnd() * 4, floor - 1, pick([STONE, STONE_D, STONE_L]))
        return
    masonry(x, floor - h, x + 14, floor - 1)


def dummy(x, floor):
    """Straw test dummy on a post - what the range was shooting before you arrived."""
    rect(x + 3, floor - 22, x + 4, floor - 1, WOOD_D)
    rect(x, floor - 22, x + 7, floor - 10, (170, 150, 96))
    rect(x + 1, floor - 28, x + 6, floor - 23, (170, 150, 96))
    rect(x - 3, floor - 18, x + 10, floor - 17, WOOD)


def minecart_barrels(x, floor):
    rect(x, floor - 22, x + 40, floor - 10, MET)
    rect(x, floor - 22, x + 40, floor - 22, MET_XL)
    rect(x, floor - 10, x + 40, floor - 9, MET_D)
    for wx in (x + 8, x + 32):
        disc(wx, floor - 6, 4, INK)
        disc(wx, floor - 6, 1.5, MET_L)
    for k in range(3):
        bx = x + 3 + k * 12
        barrel(bx, floor - 38, RED, RED_L, HAZARD, w=10, h=15)
    rect(x - 3, floor - 30, x - 2, floor - 16, MET_D)       # the chock: kick it out
    rect(x - 7, floor - 5, x - 1, floor - 1, WOOD_D)


def charged_face(x0, x1, y0, y1):
    """The working face, drilled and charged, seen in section: the rock plug between the
    chamber and exit B, holes bored into it, a charge at the back of each, and a leg wire
    out of every collar, bunched into the lead back to the plunger."""
    for y in range(int(y0), int(y1) + 1):                    # the face itself, lit
        px(x0, y, ROCK_L)
        px(x0 + 1, y, ROCK_M)
    for y in range(int(y0) + 8, int(y1) - 4, 16):            # hazard paint down the face
        rect(x0 - 1, y, x0, y + 5, HAZARD)
    lead = (x0 - 10, y1 - 8)
    for k, y in enumerate(range(int(y0) + 16, int(y1) - 10, 22)):
        depth = 26 + (k % 3) * 5
        rect(x0 + 1, y, x0 + depth, y + 1, INK)               # the hole
        rect(x0 + depth - 6, y - 1, x0 + depth, y + 2, RED)   # the charge at its back
        px(x0 + depth - 3, y, HAZARD)
        line(x0, y, lead[0], lead[1], HAZARD, 0.7)            # leg wire out of the collar
    disc(lead[0], lead[1], 2, HAZARD)
    return lead


def drill_rig(x, floor):
    """Drill carriage on the rails: a boom and a feed pointing at the face."""
    rect(x, floor - 20, x + 44, floor - 10, (70, 82, 78))
    rect(x, floor - 20, x + 44, floor - 20, (110, 124, 118))
    for wx in (x + 8, x + 36):
        disc(wx, floor - 6, 4, INK)
        disc(wx, floor - 6, 1.5, MET_L)
    line(x + 40, floor - 20, x + 70, floor - 56, MET_L)
    line(x + 41, floor - 20, x + 71, floor - 56, MET_D)
    rect(x + 64, floor - 60, x + 100, floor - 56, MET)       # feed beam
    rect(x + 100, floor - 59, x + 108, floor - 57, MET_XL)   # the steel
    rect(x + 4, floor - 34, x + 22, floor - 21, (44, 52, 50))
    rect(x + 4, floor - 34, x + 22, floor - 34, (110, 124, 118))


def vent_duct(x0, x1, y):
    rect(x0, y, x1, y + 8, (90, 96, 88))
    rect(x0, y, x1, y, (130, 138, 126))
    for x in range(int(x0), int(x1), 20):
        rect(x, y, x + 1, y + 8, (60, 64, 58))
        rect(x, y - 6, x, y - 1, MET_D)


def gas_rack(x, floor, n=5):
    rect(x - 2, floor - 26, x + n * 10, floor - 25, MET_D)
    for k in range(n):
        bx = x + k * 10
        c = [GREEN, RED, MET_L, GREEN, RED][k % 5]
        rect(bx, floor - 32, bx + 7, floor - 1, c)
        rect(bx, floor - 32, bx, floor - 1, tuple(min(255, v + 30) for v in c))
        rect(bx + 1, floor - 35, bx + 6, floor - 33, c)
        rect(bx + 2, floor - 38, bx + 5, floor - 36, MET_D)
        rect(bx, floor - 18, bx + 7, floor - 17, PALE_G, 0.6)
    rect(x - 2, floor - 26, x + n * 10, floor - 26, MET_L)


def roof_charge(x, y):
    """A pack taped to the roof with the main run through it."""
    rect(x - 5, y + 2, x + 5, y + 9, RED)
    rect(x - 5, y + 5, x + 5, y + 5, HAZARD)
    rect(x - 1, y, x + 1, y + 1, MET_D)


def warning_lamp(x, y):
    rect(x - 1, y - 4, x + 1, y, MET_D)
    disc(x, y + 3, 2.5, RED_L)
    glow(x, y + 3, 26, RED_L, 0.28)


def build():
    new_canvas(1600, 900, seed=24107)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)

    carve_all([
        (14, 580, 330, FLOOR),           # A  shot-firer's hut + entry
        (330, 560, 1150, FLOOR),         # B  the drift
        (1150, 400, 1480, FLOOR),        # E  the face chamber
        (1522, 620, 1590, FLOOR),        #    exit B, behind the face
        (60, 300, 520, 460),             # C  the magazine
        (560, 250, 1000, 470),           # D  the test bay
        (1050, 120, 1560, 300),          # F  upper gallery: gas store, exit A
        (1556, 222, 1590, 300),          #    exit A alcove
        (780, 470, 842, 504),            #    cache under the crater
    ], rough=3)
    carve(80, 456, 110, 584, rough=1)                        # A -> C ladder
    carve(516, 412, 566, 460, rough=1)                       # C -> D
    carve(996, 252, 1054, 300, rough=1)                      # D -> F
    carve(1380, 296, 1412, 404, rough=1)                     # F -> E ladder
    for x0, x1, y in ((18, 326, 582), (334, 1146, 562), (1154, 1476, 402), (64, 516, 302),
                      (564, 996, 252), (1054, 1556, 122)):
        rock_teeth(x0, x1, y, int((x1 - x0) / 12))
    rock_blob(1100, FLOOR, 40, 10, clip=(0, 0, 1600, FLOOR))

    floor_slab(14, 1480, FLOOR, 6)
    floor_slab(1522, 1590, FLOOR, 6)
    floor_slab(60, 80, 460, 6)
    floor_slab(110, 516, 460, 6)
    floor_slab(560, 780, 470, 6)
    floor_slab(842, 1000, 470, 6)
    floor_slab(1050, 1380, 300, 6)
    floor_slab(1412, 1590, 300, 6)
    floor_slab(780, 842, 504, 4)

    # ── light ───────────────────────────────────────────────────────────────
    for lx, ly, r in ((120, 586, 100), (260, 586, 80), (480, 566, 110), (760, 566, 110),
                      (1000, 566, 100), (1300, 406, 120), (180, 306, 110), (400, 306, 100),
                      (660, 256, 100), (900, 256, 100), (1150, 126, 100), (1420, 126, 110)):
        lamp(lx, ly, drop=6, bulb=LAMP, tint=LAMP, r=r, strength=0.22)
    for wx, wy in ((340, 566), (1160, 408), (70, 306), (570, 256)):
        warning_lamp(wx, wy)

    # ── A  the hut ──────────────────────────────────────────────────────────
    doorway(14, FLOOR)
    hero(60, FLOOR)
    binny_half(86, FLOOR - 60)
    plunger(190, FLOOR)
    sandbags(230, FLOOR, 5, 3)
    ladder(88, 460, 583, w=8, step=7)
    rect(140, 620, 170, 640, (36, 42, 52))                   # the shot board on the wall
    frame(140, 620, 170, 640, MET_L)
    for k in range(3):
        rect(144, 624 + k * 5, 166, 625 + k * 5, PALE_G, 0.6)

    # ── B  the drift ────────────────────────────────────────────────────────
    rails(340, 1470, FLOOR - 4, ties=9)
    minecart_barrels(420, FLOOR - 4)
    blast_shield(600, FLOOR)
    blast_shield(880, FLOOR)
    sandbags(960, FLOOR, 4, 2)
    for k in range(3):
        boom_crate(700 + k * 16, FLOOR)
    boom_crate(708, FLOOR - 14)
    stand("Grenadier", 620, FLOOR, flip=True)
    stand("Grenadier", 900, FLOOR, flip=True)
    corpse(780, FLOOR)

    # ── C  the magazine ─────────────────────────────────────────────────────
    keg_stack(130, 460, 7, 4)
    keg_stack(330, 460, 6, 3)
    for k in range(3):
        boom_crate(430 + k * 16, 460)
    hazard_slab(500, 420, 8, 39)                             # blast door, shut
    rect(516, 404, 524, 410, MET_D)
    stand("Pyro", 280, 460)                                  # a pyro. in the magazine.

    # ── D  the test bay ─────────────────────────────────────────────────────
    test_wall(660, 470)
    test_wall(810, 470, breached=True)
    test_wall(920, 470)
    dummy(700, 470)
    dummy(960, 470)
    for _ in range(60):
        px(760 + rnd() * 110, 468 + rnd() * 3, CHAR)
    for _ in range(40):
        px(760 + rnd() * 110, 300 + rnd() * 160, (80, 76, 72), 0.3)
    stand("Pyro", 610, 470)
    scrap_pile(810, 496, 40, 8)
    blast_shield(580, 470, 36)

    # ── the fuse main, burning ──────────────────────────────────────────────
    main = [(470, 456), (540, 456), (566, 440), (570, 262), (990, 262), (1060, 296),
            (1396, 296), (1396, 410), (1470, 410)]
    cord(main)
    burning(640, 700, 262)
    for x in (720, 850, 950):
        line(x, 262, x, 440, CORD, 0.8)                     # branches to the wall charges
    for rx in (1220, 1300, 1380):
        roof_charge(rx, 402)
    cord([(1396, 406), (1180, 406)])

    # ── E  the face ─────────────────────────────────────────────────────────
    lead = charged_face(1480, 1522, 420, 698)
    drill_rig(1330, FLOOR - 4)
    vent_duct(1160, 1470, 430)
    catwalk = (1384, 1476, 560)
    rect(catwalk[0], catwalk[2], catwalk[1], catwalk[2] + 3, WOOD)
    rect(catwalk[0], catwalk[2], catwalk[1], catwalk[2], WOOD_L)
    for bx in (1388, 1470):
        beam(bx, catwalk[2] + 3, FLOOR - 5, 3)
    ladder(1440, 564, FLOOR - 5, w=7, step=7, c=WOOD_L, rail=WOOD_D)
    stand("Grenadier", 1420, 560, flip=True)
    scrap_pile(1240, FLOOR - 8, 50, 16, (ROCK_M, ROCK_L, ROCK_D, DIRT))
    wire([lead, (1470, 692), (240, 692), (212, 690)])
    stand("RiotBrute", 1300, FLOOR, flip=True)
    stand("RiotBrute", 1460, FLOOR, flip=True)
    sandbags(1250, FLOOR, 4, 2)
    ladder(1392, 300, 403, w=8, step=7)
    rubble(1400, FLOOR - 3, 1478, FLOOR, 50, (ROCK_M, ROCK_L, DIRT))

    # ── F  gas store, exit A ────────────────────────────────────────────────
    gas_rack(1120, 300, 6)
    gas_rack(1250, 300, 4)
    stand("Grenadier", 1460, 300, flip=True)
    crate(1500, 287, 12)
    doorway(1584, 300)
    doorway(1584, FLOOR)


    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(14, 462)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 06:  THE BLASTING GALLERY",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(40, 740, "1 THE PLUNGER: WIRED TO THE FACE", 200, 676)
    bcallout(700, 740, "2 BLOW THE FACE AND EXIT B OPENS", 1490, 560)
    bcallout(40, 240, "3 THE MAGAZINE, AND A PYRO IN IT", 280, 420)
    bcallout(600, 190, "4 FUSE MAIN, LIT BOTH WAYS", 670, 262)
    bcallout(600, 510, "5 TEST WALLS", 670, 440)
    bcallout(340, 510, "6 SHIELDS", 602, 664)
    bcallout(1160, 70, "9 GAS STORE", 1180, 272)
    bcallout(40, 530, "7 BARREL CART: KICK THE CHOCK", 418, 674)
    bcallout(1100, 340, "8 ROOF CHARGES", 1300, 406)
    bcallout(880, 510, "10 CRATER: WHAT IT BURIED", 812, 490)
    blegend(20, 822, [
        ("BEATS", CYAN),
        ("NEVER THE ONLY ONE HOLDING THE MATCH", (170, 180, 195)),
        ("GRENADES, PYROS LIGHT THE MAIN, BRUTES AT THE FACE", F_MID),
    ], 660)
    return save(out_path("RoomConcept_BlastGallery.png"), scale=2)


if __name__ == "__main__":
    build()
