"""Room concept 03 - THE SORTING PLANT (big room).

Twice the linear size of rooms 01-02: ~3.6 x 3 screens. The toy is the belt. Six
conveyors, two on each side hung off the roof and one set into the floor on each
side of the pit, and every one of them ends in the same place - the grinder at the
bottom of the room. Whatever lands on a belt is on its way there; the only question
the room asks is whether it is them or you.

The room delivers its own waves: the first comes down the intake chute onto the top
belt and rides in; the second climbs out of the ducts onto the catwalks; the third is
riot brutes, too heavy to throw, so the answer to them is the lever in the cabin that
turns a belt round under their feet. The grinder pays out in scrap - the bin under it
is where Binny eats.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

CEIL = 70
FLOOR = 700
RUBBER = (44, 44, 48)
LAMP = (255, 214, 140)
SLATE = (54, 60, 56)


# ── local props ─────────────────────────────────────────────────────────────
def belt(x0, x1, y, d, hang=()):
    """Conveyor at game scale: rubber on top, a deep frame under it, drums at both ends
    and chevrons pointing the way it drags. Hung from the roof on rods - (x, top) pairs
    where the roof above is a rock tooth rather than the ceiling line."""
    for h in hang:
        hx, top = h if isinstance(h, tuple) else (h, CEIL)
        rect(hx, top, hx + 1, y - 1, MET_D)
        px(hx, top, MET_L)
        rect(hx - 3, y - 3, hx + 4, y - 1, MET)
    rect(x0, y + 3, x1, y + 10, MET_D)
    rect(x0, y + 3, x1, y + 3, MET)
    rect(x0, y + 10, x1, y + 10, (36, 36, 38))
    for x in range(int(x0) + 8, int(x1) - 6, 12):
        disc(x, y + 6, 1.6, MET)
        px(x, y + 5, MET_L)
    rect(x0, y, x1, y + 2, RUBBER)
    rect(x0, y, x1, y, MET_L)
    for x in range(int(x0) + 10, int(x1) - 8, 18):
        px(x, y, GREEN_L)                                    # a '>' pointing along d
        px(x + d, y + 1, GREEN_L)
        px(x, y + 2, GREEN_L)
    for ex in (x0 + 5, x1 - 5):
        disc(ex, y + 5, 5.5, MET)
        ring(ex, y + 5, 5.5, MET_L)
        disc(ex, y + 5, 1.6, MET_D)
    # the end it tips off: a short lip and a few things already falling
    tip = x1 if d > 0 else x0
    for i in range(4):
        px(tip + d * (3 + i), y + 10 + i * 7, pick([MET_L, DIRT_L, RED]), 0.8)


def catwalk_deck(x0, x1, y):
    rect(x0, y, x1, y + 3, MET)
    rect(x0, y, x1, y, MET_XL)
    rect(x0, y + 3, x1, y + 3, MET_D)
    for x in range(int(x0) + 3, int(x1), 9):
        px(x, y + 2, MET_D)


def chute(x0, x1, y0, y1):
    """Intake chute through the roof: steel liner both sides, ore dust spilling."""
    rect(x0 - 3, y0, x0 - 1, y1, MET_D)
    rect(x1 + 1, y0, x1 + 3, y1, MET_D)
    rect(x0 - 3, y0, x0 - 3, y1, MET_L)
    for y in range(int(y0), int(y1), 6):
        rect(x0 - 3, y, x0 - 1, y, MET)
        rect(x1 + 1, y, x1 + 3, y, MET)
    for _ in range(40):
        px(x0 + rnd() * (x1 - x0), y1 + rnd() * 100, pick([DIRT_L, DIRT, ROCK_L]), 0.6)


def grinder_pit(x0, x1, top, bottom):
    """The pit every belt ends in: a steel funnel, two meshing wheels, and under them
    the bin that catches what comes out."""
    for t in range(4):                                       # funnel plates
        line(x0, top + t, x0 + 58, top + 40 + t, MET)
        line(x1, top + t, x1 - 58, top + 40 + t, MET)
    line(x0, top, x0 + 58, top + 40, MET_L)
    line(x1, top, x1 - 58, top + 40, MET_L)
    cx = (x0 + x1) // 2
    gear(cx - 17, top + 58, 16, teeth=12, c=MET, lit=MET_XL, hub=MET_D)
    gear(cx + 17, top + 58, 16, teeth=12, c=MET, lit=MET_XL, hub=MET_D)
    for _ in range(40):                                      # what is going through
        px(cx - 30 + rnd() * 60, top + 40 + rnd() * 26, pick([RED, RED_L, MET_L, DIRT_L]), 0.85)
    rect(cx - 36, bottom - 16, cx + 36, bottom - 1, MET_D)   # the scrap bin
    rect(cx - 36, bottom - 16, cx + 36, bottom - 16, MET_L)
    rect(cx - 34, bottom - 14, cx + 34, bottom - 10, (58, 46, 34))
    for _ in range(50):
        px(cx - 33 + rnd() * 66, bottom - 16 + rnd() * 5, pick([MET_L, MET, WOOD, RED, HAZARD]))
    glyph("scrap", cx, bottom - 26)


def cabin(x0, x1, y0, floor):
    """Control cabin: steel box on the wall, open on the gantry side, three levers -
    one per reversible belt."""
    rect(x0, y0, x1, y0 + 4, MET_D)                          # roof
    rect(x0, y0, x1, y0, MET_L)
    rect(x0, y0, x0 + 4, floor - 34, MET_D)                  # west wall, open below: the way in
    rect(x0, floor, x1, floor + 4, MET_D)                    # floor
    rect(x0, floor, x1, floor, MET_L)
    px_ = x0 + 30
    rect(px_, floor - 30, px_ + 44, floor - 1, SLATE)        # lever desk
    rect(px_, floor - 30, px_ + 44, floor - 30, MET_L)
    for k, (lab, up) in enumerate((("L", True), ("R", False), ("F", True))):
        lx = px_ + 8 + k * 14
        rect(lx - 2, floor - 30, lx + 2, floor - 28, MET_D)
        line(lx, floor - 30, lx + (4 if up else -4), floor - 44, MET_L)
        disc(lx + (4 if up else -4), floor - 45, 1.8, RED_L if up else GREEN_L)
        text(lx - 1, floor - 24, lab, HAZARD, shadow=False)
    disc(x0 + 20, y0 + 10, 2, RED_L)
    glow(x0 + 20, y0 + 10, 12, RED_L, 0.3)
    lamp((x0 + x1) // 2, y0 + 5, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.2)


def press(cx, belt_y, top):
    """Piston press over the floor belt. Time it, or ride under it."""
    for px_ in (cx - 26, cx + 22):
        rect(px_, top, px_ + 4, belt_y - 1, MET_D)
        rect(px_, top, px_, belt_y - 1, MET_L)
    rect(cx - 30, top - 6, cx + 30, top, MET)
    rect(cx - 30, top - 6, cx + 30, top - 6, MET_XL)
    rect(cx - 4, top + 1, cx + 4, top + 40, MET_L)          # rod
    rect(cx - 18, top + 40, cx + 18, top + 54, MET)          # head, halfway down
    rect(cx - 18, top + 54, cx + 18, top + 55, MET_XL)
    for k in range(6):
        rect(cx - 16 + k * 6, top + 43, cx - 13 + k * 6, top + 51, HAZARD if k % 2 else INK)
    for _ in range(12):
        px(cx - 20 + rnd() * 40, belt_y - 2 - rnd() * 3, RED, 0.8)


def magnet_crane(x0, x1, rail_y, tx, mag_y):
    rect(x0, rail_y, x1, rail_y + 3, MET_D)
    rect(x0, rail_y, x1, rail_y, MET_L)
    for bx in range(int(x0) + 10, int(x1), 60):
        rect(bx, CEIL, bx + 1, rail_y, MET_D)
    rect(tx - 12, rail_y + 4, tx + 12, rail_y + 11, MET)
    rect(tx - 12, rail_y + 4, tx + 12, rail_y + 4, MET_L)
    line(tx, rail_y + 12, tx, mag_y - 6, MET_L)
    line(tx + 1, rail_y + 12, tx + 1, mag_y - 6, MET_D)
    rect(tx - 16, mag_y - 6, tx + 16, mag_y + 2, MET_D)      # the magnet
    rect(tx - 16, mag_y - 6, tx + 16, mag_y - 6, MET_L)
    for k in range(5):
        rect(tx - 14 + k * 6, mag_y - 4, tx - 11 + k * 6, mag_y + 1, (184, 148, 120))
    for k in range(3):                                       # field lines
        line(tx - 14 + k * 14, mag_y + 3, tx - 14 + k * 14, mag_y + 8, CYAN, 0.5)
    # held: a mine tub, upside-up, full of scrap
    cy = mag_y + 8
    rect(tx - 20, cy, tx + 20, cy + 16, MET)
    rect(tx - 20, cy, tx + 20, cy, MET_XL)
    rect(tx - 18, cy + 2, tx + 18, cy + 5, (58, 46, 34))
    rect(tx - 20, cy + 16, tx + 20, cy + 17, MET_D)
    for wx in (tx - 12, tx + 12):
        disc(wx, cy + 20, 3.5, INK)
        disc(wx, cy + 20, 1.5, MET_L)
    glow(tx, mag_y, 26, CYAN, 0.14)


def spinning_plank(cx, cy, length, angle):
    """StaticObjects/spinning_plank: a board on a hub, turning. The only footing over
    the pit up high - and it bats whatever falls onto it."""
    dx, dy = math.cos(angle) * length / 2, math.sin(angle) * length / 2
    for t in range(-2, 3):
        nx, ny = -math.sin(angle) * t * 0.7, math.cos(angle) * t * 0.7
        line(cx - dx + nx, cy - dy + ny, cx + dx + nx, cy + dy + ny,
             WOOD if abs(t) < 2 else WOOD_D)
    line(cx - dx, cy - dy - 2, cx + dx, cy + dy - 2, WOOD_L)
    disc(cx, cy, 4, MET_D)
    disc(cx, cy, 2, MET_L)
    for k in range(3):                                       # motion arcs
        a = angle + 0.35 + k * 0.12
        px(cx + math.cos(a) * (length / 2 + 3), cy + math.sin(a) * (length / 2 + 3), PALE_G, 0.5)
        px(cx - math.cos(a) * (length / 2 + 3), cy - math.sin(a) * (length / 2 + 3), PALE_G, 0.5)


def grille(x, y0, y1):
    """Duct grille in a wall. Thin bars: shoot it out."""
    rect(x, y0, x + 6, y1, CAVE)
    for yy in range(int(y0), int(y1) + 1, 4):
        rect(x, yy, x + 6, yy, MET_L)
    frame(x, y0, x + 6, y1, MET_D)


def drive(x, y, d):
    """Drive motor bolted to a belt's head end: housing, flywheel, a belt to the drum."""
    hx = x - 22 if d < 0 else x + 6
    rect(hx, y - 16, hx + 16, y - 4, (70, 82, 78))
    rect(hx, y - 16, hx + 16, y - 16, (110, 124, 118))
    for k in range(3):
        rect(hx + 3, y - 13 + k * 3, hx + 13, y - 13 + k * 3, (44, 52, 50))
    ring(hx + 8, y - 22, 6, MET_L)
    disc(hx + 8, y - 22, 1.5, MET_D)
    line(hx + 8, y - 16, x, y + 2, INK)
    disc(hx + 14, y - 14, 1, GREEN_L)


def bunker(x0, x1, top, bottom, gate_x):
    """Ore bunker on legs: a steel box that tips rock onto the belt under it every few
    seconds. Mass in the middle of the room, and something to stand on."""
    for lx in (x0 + 4, x1 - 8):
        rect(lx, bottom, lx + 4, FLOOR - 11, MET_D)
        px(lx, bottom, MET_L)
    rect(x0, top, x1, bottom - 12, MET)
    rect(x0, top, x1, top, MET_XL)
    rect(x0, top, x0, bottom - 12, MET_L)
    for y in range(int(top) + 10, int(bottom) - 12, 12):
        rect(x0, y, x1, y, MET_D)
    for i in range(12):                                      # tapered throat
        rect(x0 + i * 2, bottom - 12 + i, x1 - i * 2, bottom - 12 + i, MET_D)
    rect(x0 + 2, top - 6, x1 - 2, top - 1, DIRT)             # heaped ore
    for _ in range(40):
        px(x0 + 2 + rnd() * (x1 - x0 - 4), top - 8 + rnd() * 7, pick([DIRT_L, ROCK_L, GREEN_L]))
    rect(gate_x - 6, bottom, gate_x + 6, bottom + 3, HAZARD)
    for _ in range(26):
        px(gate_x - 4 + rnd() * 8, bottom + 4 + rnd() * (FLOOR - bottom - 14),
           pick([DIRT_L, ROCK_L, DIRT]), 0.8)


def skip(x0, x1, floor):
    """Steel skip full of rejects - cover, and a platform."""
    rect(x0, floor - 26, x1, floor - 5, (70, 82, 78))
    rect(x0, floor - 26, x1, floor - 26, (110, 124, 118))
    rect(x0 + 4, floor - 4, x0 + 10, floor - 1, MET_D)
    rect(x1 - 10, floor - 4, x1 - 4, floor - 1, MET_D)
    for k in range(0, int(x1 - x0) - 6, 14):
        rect(x0 + 5 + k, floor - 22, x0 + 6 + k, floor - 9, (44, 52, 50))
    scrap_pile(x0 + 2, floor - 26, int(x1 - x0) - 4, 8)




def hole(x0, y0, x1, y1):
    """A way through the rock between two chambers - a ladder shaft or a drop."""
    carve(x0, y0, x1, y1, rough=1)


def build():
    new_canvas(1600, 900, seed=31337)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)

    # Chambers, not a hall: half of a Noita screen is rock, and a room this size carved
    # as one box is mostly air. Each chamber holds one machine; the belts and the
    # ladder shafts are what join them, and all of them drain into the well.
    carve_all([
        (40, 130, 640, 214),             # A  intake gallery - L1
        (180, 46, 232, 134),             # chute through the roof into A
        (540, 214, 700, 350),            # B  L2, stepping down into the well
        (690, 84, 910, FLOOR),           # C  the well, over the grinder
        (650, 420, 950, FLOOR),          #    ...widening at the bottom
        (40, 300, 520, 470),             # D  west chamber - catwalk, cache wall
        (14, 560, 700, FLOOR),           # E  west floor - F1 and the press
        (1000, 110, 1584, 330),          # F  cabin chamber - R1, the magnet
        (940, 400, 1560, 520),           # G  east chamber - R2
        (940, 580, 1590, FLOOR),         # H  east floor - F2, bunker, pedestal
        (700, FLOOR, 900, 800),          #    the grinder pit
        (4, 376, 42, 444),               #    cache behind the grille
    ], rough=3)
    hole(56, 210, 86, 304)               # A -> D ladder
    hole(446, 466, 478, 564)             # D -> E ladder
    hole(1070, 326, 1150, 404)           # F -> G: R1 tips through here
    hole(1516, 326, 1548, 404)           # F -> G ladder
    hole(1486, 516, 1518, 584)           # G -> H ladder
    hole(900, 430, 950, 520)             # G opens onto the well
    for x0, x1, y in ((40, 640, 132), (540, 700, 216), (690, 910, 86), (40, 520, 302),
                      (14, 700, 562), (1000, 1584, 112), (940, 1560, 402), (940, 1590, 582)):
        rock_teeth(x0, x1, y, int((x1 - x0) / 12))
    rock_blob(1400, FLOOR, 84, 56, clip=(0, 0, 1600, FLOOR))  # mound the pedestal stands on
    rock_blob(200, FLOOR, 60, 14, clip=(0, 0, 1600, FLOOR))
    rock_blob(300, 470, 50, 12, clip=(0, 0, 1600, 470))
    rock_blob(1250, 520, 70, 16, clip=(0, 0, 1600, 520))

    floor_slab(40, 560, 214, 6)
    floor_slab(540, 700, 350, 6)
    floor_slab(40, 446, 470, 6)
    floor_slab(478, 520, 470, 6)
    floor_slab(14, 700, FLOOR, 6)
    floor_slab(900, 1590, FLOOR, 6)
    floor_slab(1000, 1070, 330, 6)
    floor_slab(1150, 1516, 330, 6)
    floor_slab(1548, 1584, 330, 6)
    floor_slab(950, 1486, 520, 6)
    floor_slab(1518, 1560, 520, 6)
    floor_slab(700, 900, 800, 4)
    floor_slab(4, 42, 444, 4)
    floor_slab(1500, 1584, 230, 4)

    # ── light: one or two lamps per chamber, the pit lit from inside ────────
    for lx, ly, r in ((140, 138, 110), (420, 138, 110), (620, 222, 80), (160, 308, 100),
                      (400, 308, 90), (120, 568, 110), (560, 568, 110), (800, 92, 120),
                      (1100, 118, 110), (1260, 118, 100), (1100, 408, 100), (1380, 408, 110),
                      (1060, 588, 100), (1300, 588, 110)):
        lamp(lx, ly, drop=6, bulb=LAMP, tint=LAMP, r=r, strength=0.22)
    glow(800, FLOOR + 30, 170, F_MID, 0.14)

    # ── A  intake: the chute and L1 ─────────────────────────────────────────
    chute(180, 232, 46, 134)
    belt(100, 560, 202, +1)                                  # L1, set on the gallery floor
    drive(100, 202, -1)
    pipe_run(260, 540, 142)
    for k in range(3):
        crate(360 + k * 40, 190, 11)
    stand("Gaper", 206, 110)
    stand("Gaper", 300, 202)
    stand("Gaper", 470, 202)
    ladder(64, 214, 469, w=8, step=7)

    # ── B  L2 into the well ─────────────────────────────────────────────────
    belt(560, 760, 330, +1, hang=((580, 216), (690, 216)))
    drive(560, 330, -1)
    stand("Gaper", 640, 330)
    rubble(540, 346, 700, 350, 30, (ROCK_M, DIRT, MET_D))

    # ── C  the well ─────────────────────────────────────────────────────────
    grinder_pit(700, 900, FLOOR, 800)
    spinning_plank(800, 560, 96, -0.35)
    for _ in range(40):                                      # the fall into the pit
        px(740 + rnd() * 120, 340 + rnd() * 350, pick([MET_L, DIRT_L, RED]), 0.5)
    pipe_run(690, 910, 96)
    for y in range(120, 400, 40):                            # old rungs up the well wall
        rect(692, y, 700, y + 1, MET_D)

    # ── D  west chamber ─────────────────────────────────────────────────────
    catwalk_deck(120, 420, 400)
    for hx in (140, 300, 410):
        chain(hx, 304, 400)
    crate(360, 387, 12)
    stand("Minespider", 250, 400, flip=True)
    stand("Gaper", 300, 460)
    corpse(200, 470)
    grille(38, 386, 440)
    reward_pedestal(22, 444, "heart")
    ladder(454, 470, 559, w=8, step=7)

    # ── E  west floor: F1 and the press ─────────────────────────────────────
    hazard_slab(14, FLOOR - 30, 6, 29)
    rect(12, FLOOR - 33, 22, FLOOR - 31, MET_D)
    disc(17, FLOOR - 37, 1.5, RED_L)
    glow(17, FLOOR - 37, 7, RED_L, 0.4)
    hero(60, FLOOR)
    binny_half(86, FLOOR - 60)
    scrap_pile(140, FLOOR - 12, 90, 12)
    for k in range(3):
        crate(250 + k * 14, FLOOR - 13, 12)
    crate(262, FLOOR - 25, 11)
    belt(300, 698, FLOOR - 8, +1)                            # F1 -> pit
    press(480, FLOOR - 8, 598)
    barrel(600, FLOOR - 23, RED, RED_L, HAZARD, w=10, h=14)  # riding F1 in
    stand("Minespider", 380, FLOOR - 8)
    corpse(560, FLOOR - 8)

    # ── F  cabin chamber: R1 and the magnet ─────────────────────────────────
    cabin(1320, 1500, 110, 230)
    belt(1150, 1480, 290, -1, hang=((1170, 114), 1300, (1470, 234)))
    drive(1480, 290, +1)
    magnet_crane(1010, 1140, 124, 1060, 244)
    stand("Grenadier", 1420, 230, flip=True)
    stand("Gaper", 1260, 290, flip=True)
    ladder(1528, 234, 403, w=8, step=7)
    scrap_pile(1010, 318, 50, 10)

    # ── G  east chamber: R2 onto the well ───────────────────────────────────
    belt(900, 1180, 430, -1, hang=((920, 404), 1040, 1160))
    drive(1180, 430, +1)
    stand("RiotBrute", 1000, 430, flip=True)                  # riding to the pit
    stand("Minespider", 1300, 520, flip=True)
    stand("Minespider", 1400, 520, flip=True)
    barrel(1440, 506, MET, MET_L, HAZARD, w=9, h=13)
    crate(1340, 507, 12)
    ladder(1498, 520, 583, w=8, step=7)

    # ── H  east floor: F2, the bunker, the mound ────────────────────────────
    belt(902, 1300, FLOOR - 8, -1)                           # F2 -> pit
    bunker(1010, 1110, 612, 652, 1060)
    stand("RiotBrute", 1200, FLOOR - 8, flip=True)
    reward_pedestal(1400, 648, "gun", ghost=True)
    scrap_pile(1500, FLOOR - 10, 60, 10)
    exit_door(1574, 230, "skull")
    exit_door(1580, FLOOR, "gear")

    for x, y, t in ((200, 70, "W1"), (294, 164, "W1"), (464, 164, "W1"), (634, 292, "W1"),
                    (294, 424, "W1"), (244, 364, "W2"), (374, FLOOR - 44, "W2"),
                    (1294, 484, "W2"), (1394, 484, "W2"), (994, 386, "W3"),
                    (1192, FLOOR - 52, "W3"), (1414, 188, "W3"), (1254, 252, "W1")):
        wave_tag(x, y, t, {"W1": PALE_G, "W2": F_MID, "W3": RED_L}[t])

    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(14, 460)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 03:  THE SORTING PLANT",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(120, 506, "1 IN, AND THE DOOR SEALS", 20, 660)
    bcallout(260, 58, "2 WAVE 1 COMES DOWN THE CHUTE", 206, 96)
    bcallout(890, 58, "3 EVERY BELT ENDS IN THE GRINDER", 800, 150)
    bcallout(1040, 350, "4 LEVERS TURN A BELT ROUND", 1374, 186)
    bcallout(960, 760, "5 GRINDER PAYS SCRAP: FEED BINNY", 830, 776)
    bcallout(80, 740, "6 THE FLOOR MOVES TOO", 360, 700)
    bcallout(520, 606, "7 PRESS", 480, 612)
    bcallout(1340, 66, "8 MAGNET: A FULL TUB", 1060, 250)
    bcallout(960, 540, "9 SPINNING PLANK", 830, 552)
    bcallout(60, 250, "10 GRILLE: CACHE", 40, 400)
    bcallout(1200, 548, "11 PEDESTAL ON CLEAR", 1400, 600)
    blegend(20, 820, [
        ("BEATS", CYAN),
        ("A BELT DECIDES WHERE THINGS END UP", (170, 180, 195)),
        ("W1 ON THE CHUTE  W2 FROM THE DUCTS  W3 TOO HEAVY TO THROW", F_MID),
    ], 700)
    glyph_key(1180, 796)
    return save(out_path("RoomConcept_SortingPlant.png"), scale=2)


if __name__ == "__main__":
    build()
