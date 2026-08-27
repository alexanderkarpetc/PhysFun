"""Concept 05 - THE SUNKEN DEPOT.

A logistics depot that lost its pumps. Water is the level: it snuffs fire, it slows
everything moving through it, and it floats anything wooden — which is the point, because
the way up is a crate you have to sink, or a crate you have to let rise.

The pump house at the far end drops the water line by a floor. Nothing else in the level
changes; the same rooms simply become reachable, which is cheaper than building two levels
and reads as a bigger change than it is.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 46
WATER = (44, 84, 104)
WATER_L = (120, 176, 196)


def build():
    new_canvas(400, 225, seed=5150)

    # ── rain over a drowned yard ────────────────────────────────────────────
    sky(SURF, hi=(104, 118, 132), lo=(66, 78, 92), smog=8)
    for _ in range(180):
        x, y = rnd() * W, rnd() * (SURF + 4)
        line(x, y, x - 1, y + 3, (170, 190, 205), 0.30)
    for hx, hy in ((14, 22), (250, 18)):
        rect(hx, hy, hx + 60, SURF, (58, 66, 78))
        rect(hx, hy, hx + 60, hy, (84, 94, 108))
        for x in range(hx + 4, hx + 56, 9):
            rect(x, hy + 6, x + 4, hy + 12, (38, 44, 54))

    rock_mass(SURF, base=(56, 66, 78), dark=(36, 44, 54), mid=(76, 88, 102),
              soil=(70, 78, 84), soil_lit=(112, 126, 138))

    ROOMS = [
        (8, 60, 190, 116),      # loading hall
        (8, 128, 210, 186),     # flooded floor
        (150, 108, 196, 136),   # hall -> flooded floor
        (204, 62, 320, 120),    # crane bay
        (206, 128, 306, 190),   # sump
        (300, 60, 392, 124),    # pump house
        (300, 130, 392, 196),   # outfall / exit
        (186, 84, 212, 104),    # hall -> crane bay
        (296, 96, 316, 120),    # crane bay -> pumps
    ]
    carve_all(ROOMS, air=(22, 28, 34), lip=(66, 82, 96))

    # ── surface: quay, cranes, spillway ─────────────────────────────────────
    rect(0, SURF - 4, 120, SURF - 2, MET_D)
    rect(0, SURF - 4, 120, SURF - 4, MET_L)
    beam(96, SURF - 30, SURF - 4, 3, (66, 76, 88), MET_L)          # gantry leg
    beam(150, SURF - 30, SURF - 4, 3, (66, 76, 88), MET_L)
    rect(92, SURF - 33, 156, SURF - 30, (78, 90, 102))
    line(124, SURF - 30, 124, SURF - 12, MET_L)
    rect(120, SURF - 12, 130, SURF - 7, MET)                       # hook block
    liquid_pool(160, SURF - 6, 260, SURF, WATER, WATER_L)
    crate(168, SURF - 12); crate(182, SURF - 11)                   # floating
    player(60, SURF - 12, coat=(56, 78, 96), cuff=BLUE_L)
    binny(74, SURF - 22, thruster=(120, 190, 210))
    humanoid(214, SURF - 12, MET_L, BLUE, face_right=False)

    # ── 1  loading hall, dry but leaking ────────────────────────────────────
    floor_slab(8, 190, 112, 4, (40, 48, 58), (100, 118, 132))
    conveyor(20, 130, 100, 1)
    crate(36, 92); crate(60, 92, 7, False); crate(104, 92)
    catwalk(16, 96, 76, drop=8, posts=14)
    humanoid(30, 65, MET_L, GREEN)
    humanoid(58, 65, DIRT_L, GREEN)
    tracer(41, 70, 82, 98)
    for lx in (46, 132):
        lamp(lx, 62, bulb=PALE_G, r=22, strength=0.22)
    for cx in (150, 176):                                          # water coming through
        for y in range(64, 110, 3):
            px(cx, y, WATER_L, 0.5)
        disc(cx, 110, 3, WATER_L, 0.35)
    rubble(120, 104, 188, 111, 26, ((60, 72, 84), MET_D, DIRT))

    # ── 2  the flooded floor ────────────────────────────────────────────────
    floor_slab(8, 210, 182, 4, (40, 48, 58), (100, 118, 132))
    liquid_pool(8, 152, 210, 182, WATER, WATER_L)
    for _ in range(16):                                            # things adrift
        fx = 14 + rnd() * 180
        rect(fx, 149, fx + 3 + rnd() * 4, 151, pick([WOOD, MET_D, DIRT_L]), 0.85)
    crate(46, 144); crate(58, 143); crate(120, 145)                # floating, walkable
    ragdoll(150, 146, WATER_L)
    catwalk(90, 200, 134, drop=6, posts=18)                        # walkway above the line
    chain(104, 136, 148); chain(168, 136, 150)
    humanoid(78, 138, ICE_L, BLUE, face_right=False)               # wading, slowed
    player(126, 133, coat=(56, 78, 96), cuff=BLUE_L)
    tk_beam(133, 137, 120, 146, CYAN)
    icicles(10, 208, 130, 12, (70, 96, 110), WATER_L)              # drips off the roof

    # ── 3  crane bay ────────────────────────────────────────────────────────
    floor_slab(204, 320, 116, 4, (40, 48, 58), (100, 118, 132))
    rect(206, 64, 318, 66, (66, 76, 88))
    line(240, 66, 240, 92, MET_L)
    rect(232, 92, 250, 98, MET)                                    # magnet block
    glow(241, 98, 22, CYAN, 0.20)
    for _ in range(12):                                            # scrap stuck to it
        px(230 + rnd() * 22, 99 + rnd() * 4, pick([MET_L, MET_D]))
    tank(266, 88, 18, 26)
    valve(276, 84)
    crate(212, 108); crate(224, 108, 7, False)
    humanoid(288, 104, MET_L, RED, face_right=False)
    lamp(258, 68, bulb=PALE_G, r=20, strength=0.20)
    cable(206, 70, 318, 74, 6)

    # ── 4  the sump ─────────────────────────────────────────────────────────
    floor_slab(206, 306, 186, 4, (40, 48, 58), (100, 118, 132))
    liquid_pool(206, 150, 306, 186, tuple(int(v * 0.8) for v in WATER), WATER_L)
    grate(232, 280, 148)
    chain(250, 132, 148)
    for _ in range(9):
        px(212 + rnd() * 90, 152 + rnd() * 20, WATER_L, 0.4)
    ragdoll(268, 154, WATER_L)
    conveyor(214, 296, 140, -1)                                    # feed belt, half drowned

    # ── 5  pump house ───────────────────────────────────────────────────────
    floor_slab(300, 392, 120, 4, (40, 48, 58), (100, 118, 132))
    tank(316, 74, 22, 40)
    tank(348, 78, 20, 36)
    valve(327, 70, 5); valve(358, 74, 5)
    pipe_run(302, 390, 64, c=(58, 68, 80), lit=MET_L)
    for py in (100, 108):
        rect(302, py, 316, py + 3, MET)
        rect(302, py, 316, py, MET_L)
    steam_plume(340, 70, 16, 26)
    rect(372, 96, 388, 116, MET_D)                                 # control panel
    rect(374, 100, 386, 106, CYAN, 0.8)
    glow(380, 103, 16, CYAN, 0.26)
    humanoid(306, 108, MET_L, GREEN)
    binny(354, 104, thruster=(120, 190, 210))

    # ── 6  outfall ──────────────────────────────────────────────────────────
    floor_slab(300, 392, 192, 4, (40, 48, 58), (100, 118, 132))
    rect(300, 132, 316, 190, MET_D)
    for y in range(136, 188, 8):
        rect(300, y, 316, y + 1, MET)
    liquid_pool(316, 168, 392, 192, WATER, WATER_L)
    for _ in range(30):                                            # the flow out
        fx = 318 + rnd() * 40
        line(fx, 168 - rnd() * 20, fx + 4, 168, WATER_L, 0.35)
    door(348, 138, 30, 26)
    glow(363, 151, 22, PALE_G, 0.16)

    vignette()

    # ── sheet furniture ─────────────────────────────────────────────────────
    title_bar("PHYSFUN - LEVEL CONCEPT 05:  THE SUNKEN DEPOT")
    callout(6, 24, "1 QUAY - SPAWN", 62, 40)
    callout(120, 22, "2 LOADING HALL - IT IS LEAKING", 152, 88)
    callout(250, 26, "5 PUMP HOUSE - DROPS THE WATER LINE", 330, 92)
    callout(6, 120, "3 FLOODED FLOOR - CRATES FLOAT, FIRE DOES NOT", 60, 156)
    callout(204, 54, "4 CRANE BAY - MAGNET DROPS THE LOAD", 241, 96)
    callout(150, 208, "6 SUMP - THE GRATE GIVES", 256, 150)
    callout(300, 206, "7 OUTFALL EXIT", 350, 176)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("WATER SLOWS YOU AND KILLS FIRE", (170, 180, 195)),
        ("WOOD FLOATS - RIDE IT OR SINK IT", (170, 180, 195)),
        ("GOAL: DRAIN A FLOOR, WALK OUT", GREEN_L),
    ], width=142)

    return save(out_path("LevelConcept_SunkenDepot.png"))


if __name__ == "__main__":
    build()
