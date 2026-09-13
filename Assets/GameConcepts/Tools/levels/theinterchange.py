"""Concept 30 - THE INTERCHANGE.

A deep tube station with the power still on. The level is one long platform hall:
street stair, ticket hall, escalator barrel down, and a running tunnel through the
whole sheet with two dead cars parked on it.

The car is the point. It is a twenty-tonne body on four wheels standing on a rail
that runs off both ends of the level, and everything else here - the brake shoe, the
grade, the buffer stop, the crowd on the platform - exists to decide where it stops.
The conductor rail is the second system: it is live, it is at ankle height, and every
metal thing the player can lift is a bridge across it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 34
LAMP_TINT = (214, 228, 255)


def build():
    new_canvas(400, 225, seed=30301)
    cw, ch = canvas_size()

    # -- street above --------------------------------------------------------
    sky(SURF, hi=(96, 104, 124), lo=(62, 68, 82), smog=8)
    rock_mass(SURF, soil=DIRT, soil_lit=DIRT_L)
    for _ in range(30):
        px(rnd() * cw, rnd() * (SURF - 8), (190, 200, 220), 0.20)

    ROOMS = [
        (44, 28, 78, 68),        # street stair
        (12, 66, 142, 106),      # ticket hall
        (12, 122, 86, 154),      # relay room
        (44, 104, 58, 124),      # ladder shaft down to the relay room
        (274, 62, 392, 102),     # fan plant
        (352, 100, 374, 162),    # vent shaft
        (8, 158, 392, 212),      # platform hall + running tunnel
    ]
    for i in range(15):                                  # escalator barrel, stepped
        t = i / 14
        ex = 118 + 112 * t
        ey = 104 + 84 * t
        ROOMS.append((ex - 4, ey - 30, ex + 20, ey + 8))
    carve_all(ROOMS)

    # -- surface: entrance canopy, railings, a street that has stopped -------
    rect(0, SURF - 2, cw - 1, SURF - 1, (74, 76, 80))
    rect(0, SURF - 2, cw - 1, SURF - 2, (108, 112, 116))
    rect(36, SURF - 16, 92, SURF - 13, MET_D)            # canopy
    rect(36, SURF - 16, 92, SURF - 16, MET_L)
    beam(38, SURF - 13, SURF - 2, 2, MET_D, MET)
    beam(88, SURF - 13, SURF - 2, 2, MET_D, MET)
    sign_board(52, SURF - 26)
    for rx in (40, 80):                                  # railings round the stair mouth
        rect(rx, SURF - 10, rx + 1, SURF - 2, MET)
    rect(40, SURF - 10, 81, SURF - 9, MET_L)
    stairs(46, SURF + 22, 6, 5, 4, (58, 62, 66), (110, 116, 120))
    humanoid(104, SURF - 13, MET_L, BLUE_L, face_right=False)
    humanoid(140, SURF - 13, DIRT_L, RED)
    scrap_pile(150, SURF - 1, 34, 7, (MET_D, MET, DIRT, RED))
    for x in (210, 300):                                 # street grilles over the works
        grate(x, x + 26, SURF - 2)
    lamp(120, SURF - 20, drop=4, bulb=LAMP_TINT, tint=(200, 214, 255), r=18, strength=0.20)

    # -- 1  ticket hall ------------------------------------------------------
    floor_slab(12, 142, 102, 4, (44, 48, 54), (104, 110, 118))
    tiled_wall(14, 76, 140, 101, band_y=88)
    tube_lining(12, 142, 68, ribs=24)
    for tx in (66, 82, 98, 114):
        turnstile(tx, 102)
    sign_board(20, 78, 30)
    crate(126, 95)
    barrel(136, 94, MET, MET_L, MET_XL)
    humanoid(30, 91, MET_L, GREEN, face_right=False)
    humanoid(44, 91, DIRT_L, BLUE_L)
    lamp(38, 70, drop=3, bulb=LAMP_TINT, tint=(200, 214, 255), r=20, strength=0.22)
    lamp(110, 70, drop=3, bulb=LAMP_TINT, tint=(200, 214, 255), r=20, strength=0.22)

    # -- 2  relay room under the hall ----------------------------------------
    floor_slab(12, 86, 150, 4, (44, 48, 54), (104, 110, 118))
    ladder(46, 106, 150, 6, 8)
    for bx in (20, 40, 60):                              # battery bank / switch cubicles
        tank(bx, 132, 14, 16, MET, MET_L, MET_D, 2)
        rect(bx + 3, 130, bx + 11, 131, MET_XL)
    cable_rack(14, 84, 124)
    for i in range(4):                                   # knife-switch board
        rect(70 + i * 3, 136, 70 + i * 3, 142, MET_XL)
        px(70 + i * 3, 135, F_MID if i == 1 else PALE_G)
    glow(74, 138, 16, F_MID, 0.16)
    binny(30, 140)

    # -- 3  escalator barrel -------------------------------------------------
    for i in range(120):                                 # lit soffit + skirt of the barrel
        t = i / 119
        bx = 116 + 116 * t
        by = 104 + 84 * t
        rect(bx, by - 30, bx, by - 28, MET_D)
        px(bx, by - 30, MET_L)
        px(bx, by + 8, (96, 100, 106))
    escalator(118, 104, 230, 188)
    escalator(126, 118, 238, 202, tread=6, rail=False)   # the second flight, stopped
    for i in range(5):
        t = i / 4
        lamp(122 + 112 * t, 104 + 84 * t - 26, drop=3, bulb=LAMP_TINT,
             tint=(200, 214, 255), r=16, strength=0.18)
    cable_rack(118, 236, 90)
    humanoid(168, 138, MET_L, RED, face_right=False)
    player(196, 158)
    crate(214, 176, 7)

    # -- 4  fan plant and the vent shaft into the hall -----------------------
    floor_slab(274, 392, 98, 4, (44, 48, 54), (104, 110, 118))
    fan(300, 82, 12)
    rect(286, 66, 316, 68, MET_D)
    pipe_run(316, 390, 72)
    tank(330, 78, 18, 20, MET, MET_L, MET_D, 3)
    valve(360, 86)
    cable_rack(276, 390, 62, 2)
    humanoid(268, 87, MET_L, GREEN)
    for y in range(104, 158, 6):                         # draught down the shaft
        px(356 + int(rnd() * 16), y, BLUE_L, 0.30)
        px(356 + int(rnd() * 16), y + 2, BLUE_XL, 0.18)
    grate(352, 374, 158)

    # -- 5  the platform hall ------------------------------------------------
    floor_slab(8, 392, 206, 5, (40, 42, 46), (96, 100, 106))     # track bed
    tube_lining(8, 392, 158)
    tiled_wall(198, 172, 392, 186, band_y=178)
    rect(198, 186, 392, 188, STONE_D)
    rect(198, 188, 392, 206, STONE)                              # raised platform
    rect(198, 188, 392, 188, STONE_L)
    rect(198, 188, 200, 206, STONE_D)
    for x in range(202, 392, 6):                                 # tactile edge strip
        rect(x, 189, x + 3, 190, (198, 164, 60), 0.85)
    rails(12, 390, 204)
    live_rail(12, 390, 199, arc_at=176)
    train_car(258, 176, 118, 26, nose=True, doors=(30, 74))
    train_car(24, 176, 96, 26, nose=False, doors=(22, 58), lit_windows=False, rolling=True)
    buffer_stop(9, 204)
    for lx in (40, 110, 180, 250, 320):
        lamp(lx, 162, drop=3, bulb=LAMP_TINT, tint=(200, 214, 255), r=22, strength=0.20)
    sign_board(232, 166, 34)
    sign_board(330, 166, 30)
    humanoid(268, 194, MET_L, RED, face_right=False)             # crowd on the platform
    humanoid(292, 194, DIRT_L, GREEN, face_right=False)
    humanoid(348, 194, MET_L, BLUE_L, face_right=False)
    ragdoll(160, 198)
    crate(214, 198)
    crate(226, 198, 7, False)
    barrel(240, 196, GREEN, GREEN_L, PALE_G)
    rubble(120, 200, 176, 205, 30, (MET_D, ROCK_M, DIRT))
    scrap_pile(130, 205, 30, 5, (MET_D, MET, RED, DIRT))
    binny(210, 178)
    tk_beam(212, 182, 240, 196)

    vignette()

    # -- sheet furniture -----------------------------------------------------
    title_bar("PHYSFUN - LEVEL CONCEPT 30:  THE INTERCHANGE")
    callout(6, 24, "1 STREET STAIR - THE WAY IN", 60, 40)
    callout(6, 56, "2 TICKET HALL - TURNSTILES ARE LEVERS", 84, 96)
    callout(6, 108, "3 RELAY ROOM - CUT THE RAIL POWER", 62, 132)
    callout(150, 130, "4 ESCALATOR - A CONVEYOR ON A SLOPE", 190, 152)
    callout(238, 112, "5 FAN PLANT - DRAUGHT DOWN SHAFT", 358, 130)
    callout(96, 150, "6 DEAD CAR, NO BRAKE - 20 TONNES ROLLING", 60, 182)
    callout(116, 216, "7 LIVE RAIL AT ANKLE HEIGHT", 176, 200)
    callout(262, 216, "8 BUFFER STOP AT THE FAR END", 14, 200)
    legend(250, 22, [
        ("BEATS", CYAN),
        ("ROLLING MASS > EVERYTHING", (170, 180, 195)),
        ("METAL ACROSS THE RAIL = ARC", (140, 200, 210)),
        ("GOAL: SEND THE CAR DOWN THE TUNNEL", GREEN_L),
    ], width=138)

    return save(out_path("LevelConcept_TheInterchange.png"))


if __name__ == "__main__":
    build()
