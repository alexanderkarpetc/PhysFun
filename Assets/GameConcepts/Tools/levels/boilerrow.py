"""Concept 06 - BOILER ROW.

Everything in this level is under pressure and none of it is yours. Boilers are physics
objects with a lot of stored energy: shoot one, burn through its feed line, or drop
something heavy on it, and it takes out the wall behind it — which is usually the wall you
needed gone.

The design bet is that the player learns to aim at the room rather than at the enemies.
Guards patrol between the vessels precisely so that the cheap solution is also the loud one.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 42
BRASS = (150, 122, 68)
BRASS_L = (198, 172, 104)


def gauge(x, y, r=4):
    disc(x, y, r, (28, 32, 38))
    ring(x, y, r, BRASS_L)
    line(x, y, x + r * 0.7, y - r * 0.5, RED_L)
    px(x, y, PALE_G)


def boiler(x, y, w=26, h=34, hot=True):
    """Vessel plus firebox. The glow under it is the tell that it is live."""
    tank(x, y, w, h, MET, MET_L, MET_D, bands=3)
    rect(x + 2, y + h, x + w - 2, y + h + 6, MET_D)          # firebox
    if hot:
        rect(x + 4, y + h + 1, x + w - 4, y + h + 5, F_MID)
        rect(x + 6, y + h + 2, x + w - 6, y + h + 4, F_HOT)
        glow(x + w / 2, y + h + 4, 22, F_MID, 0.30)
    rect(x + w // 2 - 2, y - 6, x + w // 2 + 2, y, MET)      # stack
    gauge(x + 6, y + 8, 3)
    valve(x + w - 6, y + 6, 4, BRASS_L, BRASS)


def build():
    new_canvas(400, 225, seed=6006)

    sky(SURF, hi=(126, 116, 106), lo=(78, 74, 76), smog=9)
    for sx, top, w in ((22, 12, 7), (58, 20, 5), (326, 14, 8)):
        rect(sx, top, sx + w, SURF, (64, 66, 74))
        rect(sx, top, sx + w, top, (92, 94, 104))
        for i in range(14):
            disc(sx + w / 2 + (rnd() - 0.5) * 8, top - 2 - i * 2, 1.4 + i * 0.2,
                 (186, 180, 172), 0.12)
    rect(110, 24, 200, SURF, (60, 62, 70))
    rect(110, 24, 200, 24, (88, 90, 100))
    for x in range(114, 196, 8):
        rect(x, 28, x + 4, 34, (40, 42, 50))

    rock_mass(SURF, base=(62, 62, 68), dark=(42, 42, 48), mid=(84, 84, 92),
              soil=(74, 68, 58), soil_lit=(132, 120, 96))

    ROOMS = [
        (8, 56, 250, 118),      # boiler hall
        (8, 132, 170, 196),     # feedwater cellar
        (30, 110, 74, 140),     # hall -> cellar
        (188, 130, 300, 194),   # ash floor
        (164, 150, 196, 180),   # cellar -> ash floor
        (262, 54, 392, 122),    # governor room
        (306, 128, 392, 198),   # blowdown exit
        (240, 100, 272, 126),   # hall -> governor
        (286, 116, 320, 138),   # governor -> exit
    ]
    carve_all(ROOMS, air=(20, 22, 28), lip=(74, 76, 86))

    # ── surface ─────────────────────────────────────────────────────────────
    rect(0, SURF - 3, 108, SURF - 1, MET_D)
    rect(0, SURF - 3, 108, SURF - 3, MET_L)
    scrap_pile(210, SURF, 60, 12, (MET_D, MET, BRASS, DIRT))
    pipe_run(60, 210, SURF - 10, c=(60, 60, 68), lit=BRASS)
    player(40, SURF - 12)
    binny(54, SURF - 22)
    humanoid(232, SURF - 12, MET_L, RED, face_right=False)

    # ── 1  boiler hall ──────────────────────────────────────────────────────
    floor_slab(8, 250, 114, 4, (44, 44, 52), (104, 104, 116))
    pipe_run(10, 248, 60, c=(56, 56, 64), lit=BRASS)
    for i, bx in enumerate((22, 74, 126, 178)):
        boiler(bx, 72, 26, 34, hot=i != 2)
        for y in range(66, 72, 2):                                   # feed lines down
            rect(bx + 12, y, bx + 14, y + 1, BRASS)
    rect(126, 66, 152, 72, F_COOL, 0.5)                              # the cold one, cracked
    for k in range(6):
        px(130 + k * 3, 74 + k, CHAR)
    catwalk(12, 244, 66, drop=6, posts=16)
    humanoid(96, 100, MET_L, GREEN)
    humanoid(160, 100, DIRT_L, GREEN, face_right=False)
    tracer(103, 105, 150, 105)
    steam_plume(88, 68, 14, 20)
    steam_plume(192, 68, 12, 16)
    for lx in (56, 208):
        lamp(lx, 58, bulb=(255, 226, 150), tint=(255, 210, 140), r=22, strength=0.24)
    sparks(139, 78, 12, 14)

    # ── 2  feedwater cellar ─────────────────────────────────────────────────
    floor_slab(8, 170, 192, 4, (44, 44, 52), (104, 104, 116))
    liquid_pool(10, 168, 168, 192, (46, 78, 92), (118, 170, 190))
    for px_ in (16, 96):
        pipe_run(px_, px_ + 70, 138, c=(56, 56, 64), lit=BRASS)
    tank(30, 146, 20, 22, MET, BRASS_L, MET_D, bands=2)
    tank(60, 150, 18, 18, MET, BRASS_L, MET_D, bands=2)
    valve(40, 142, 5, BRASS_L, BRASS)
    crate(96, 158); crate(120, 158, 7, False)
    humanoid(140, 156, ICE_L, BLUE, face_right=False)
    ragdoll(86, 160)
    steam_plume(64, 146, 12, 18)
    lamp(112, 134, bulb=(255, 226, 150), tint=(255, 210, 140), r=18, strength=0.20)

    # ── 3  ash floor ────────────────────────────────────────────────────────
    floor_slab(188, 300, 190, 4, (44, 44, 52), (104, 104, 116))
    for _ in range(70):                                              # ash drifts
        ax = 192 + rnd() * 104
        ay = 176 + rnd() * 12
        rect(ax, ay, ax + 2 + rnd() * 4, ay + 1, pick([CHAR, (60, 56, 54), (86, 80, 76)]))
    for hx in (206, 250, 282):                                       # ash doors under the row
        rect(hx, 130, hx + 12, 138, MET_D)
        rect(hx + 2, 132, hx + 10, 136, F_COOL, 0.7)
        glow(hx + 6, 140, 20, F_COOL, 0.22)
    conveyor(196, 292, 168, 1, chevron=(180, 150, 90))
    humanoid(226, 156, MET_L, RED, face_right=False)
    crate(262, 158)
    embers(196, 150, 296, 176, 30)

    # ── 4  governor room ────────────────────────────────────────────────────
    floor_slab(262, 392, 118, 4, (44, 44, 52), (104, 104, 116))
    rect(300, 62, 384, 112, (50, 50, 58))
    frame(300, 62, 384, 112, MET_L)
    for i, gx in enumerate((312, 336, 360)):
        rect(gx, 70, gx + 14, 96, MET_D)
        rect(gx + 2, 74, gx + 12, 84, CYAN if i != 1 else RED_L, 0.85)
        gauge(gx + 7, 90, 4)
    glow(342, 82, 40, CYAN, 0.18)
    rect(268, 92, 292, 112, MET)                                     # governor flywheel housing
    disc(280, 100, 8, MET_D)
    ring(280, 100, 8, MET_XL)
    for a in range(3):
        ang = a * 2.1
        line(280, 100, 280 + math.cos(ang) * 7, 100 + math.sin(ang) * 7, MET_XL)
    humanoid(292, 104, MET_L, BLUE, face_right=False)
    pipe_run(264, 390, 58, c=(56, 56, 64), lit=BRASS)
    cable(266, 66, 388, 68, 5)

    # ── 5  blowdown exit ────────────────────────────────────────────────────
    floor_slab(306, 392, 194, 4, (44, 44, 52), (104, 104, 116))
    tank(314, 148, 22, 40)
    valve(325, 144, 5, BRASS_L, BRASS)
    steam_plume(325, 142, 20, 34)
    door(348, 156, 32, 34)
    glow(364, 173, 24, PALE_G, 0.16)
    for _ in range(14):
        px(310 + rnd() * 76, 188 + rnd() * 4, pick([CHAR, MET_D]))

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 06:  BOILER ROW")
    callout(6, 24, "1 SERVICE HATCH - SPAWN", 44, 38)
    callout(112, 22, "2 BOILER HALL - EVERY VESSEL IS A BOMB", 139, 76)
    callout(284, 26, "5 GOVERNOR - SHUT IT DOWN", 342, 78)
    callout(6, 122, "3 FEEDWATER CELLAR - CUT THE FEED,", 40, 148)
    tag(6, 130, "  THE ROW GOES CRITICAL")
    callout(176, 122, "4 ASH FLOOR - HOT DOORS", 250, 168)
    callout(300, 206, "6 BLOWDOWN EXIT", 350, 180)
    legend(6, 188, [
        ("BEATS", CYAN),
        ("PRESSURE IS YOUR DEMOLITION KIT", (170, 180, 195)),
        ("AIM AT THE ROOM, NOT THE GUARD", (200, 150, 90)),
        ("GOAL: BLOW A WALL, REACH THE VALVE", GREEN_L),
    ], width=152)

    return save(out_path("LevelConcept_BoilerRow.png"))


if __name__ == "__main__":
    build()
