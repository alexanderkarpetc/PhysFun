"""Concept 12 - THE MAGNET HALL.

The level that argues with your telekinesis. Ceiling magnets take everything ferrous away
from you on their cycle: the crate you were holding, the guard's rifle, the girder you were
standing on. Wood and stone are the only things that stay where you put them, which quietly
teaches the player to re-read the whole game's material list.

Fighting the field is the wrong answer and the level says so early — the first magnet
catches something huge and holds it overhead for as long as the player watches.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 44
COIL = (168, 128, 62)
FIELD = (120, 190, 220)


def magnet(x, y, w=34, on=True):
    """Ceiling coil. Field lines only when live, so a dead one reads as safe at a glance."""
    rect(x, y, x + w, y + 10, MET_D)
    rect(x, y, x + w, y, MET_L)
    for i in range(4):
        rect(x + 3 + i * (w // 4), y + 2, x + 5 + i * (w // 4), y + 9, COIL)
    rect(x + 4, y + 10, x + w - 4, y + 13, MET)
    if not on:
        return
    for k in range(4):
        r = 10 + k * 7
        for a in range(10):
            ang = math.pi * (0.1 + a * 0.09)
            px(x + w / 2 + math.cos(ang) * r * 1.4, y + 13 + math.sin(ang) * r,
               FIELD, 0.30 - k * 0.05)
    glow(x + w / 2, y + 16, 30, FIELD, 0.22)


def girder(x, y, w=34, h=5, angle=0):
    if angle == 0:
        rect(x, y, x + w, y + h, MET)
        rect(x, y, x + w, y, MET_L)
        for k in range(int(w // 8)):
            line(x + k * 8, y + h, x + k * 8 + 8, y, MET_D, 0.6)
    else:
        for k in range(int(w)):
            rect(x + k, y + int(k * angle), x + k, y + int(k * angle) + h, MET)
            px(x + k, y + int(k * angle), MET_L)


def lifted(x, y, n=18):
    """Loose metal on its way up — the picture of the field being on."""
    for _ in range(n):
        lx = x + (rnd() - 0.5) * 40
        ly = y - rnd() * 30
        rect(lx, ly, lx + 1 + rnd() * 3, ly + 1, pick([MET_L, MET, MET_XL]), 0.9)


def build():
    new_canvas(400, 225, seed=1212)

    sky(SURF, hi=(108, 116, 130), lo=(68, 76, 90), smog=7)
    for hx, hy, w in ((20, 18, 76), (230, 14, 96)):
        rect(hx, hy, hx + w, SURF, (56, 60, 70))
        rect(hx, hy, hx + w, hy, (84, 90, 102))
        for x in range(hx + 5, hx + w - 6, 11):
            rect(x, hy + 6, x + 5, hy + 12, (36, 40, 48))
    rock_mass(SURF, base=(60, 62, 70), dark=(40, 42, 50), mid=(82, 86, 96),
              soil=(76, 72, 62), soil_lit=(130, 124, 104))

    ROOMS = [
        (8, 58, 230, 128),      # the main hall
        (8, 146, 190, 202),     # the floor of scrap
        (44, 122, 96, 152),     # hall -> scrap floor
        (236, 56, 340, 122),    # coil room
        (224, 80, 242, 100),    # hall -> coil room
        (196, 150, 320, 204),   # rail store
        (250, 116, 290, 156),   # coil room -> rail store
        (346, 58, 392, 200),    # exit shaft
        (316, 168, 350, 192),   # rail store -> exit
    ]
    carve_all(ROOMS, air=(20, 24, 30), lip=(76, 82, 94))

    # ── surface ─────────────────────────────────────────────────────────────
    rect(0, SURF - 4, 130, SURF - 2, MET_D)
    rect(0, SURF - 4, 130, SURF - 4, MET_L)
    scrap_pile(140, SURF, 80, 13, (MET_D, MET, MET_L, RUST_LIKE := (120, 76, 52)))
    player(44, SURF - 12)
    binny(58, SURF - 22)
    humanoid(206, SURF - 12, MET_L, RED, face_right=False)
    cable(10, SURF - 20, 130, SURF - 18, 5)

    # ── 1  the main hall ────────────────────────────────────────────────────
    floor_slab(8, 230, 124, 4, (44, 46, 54), (104, 110, 122))
    for i, mx in enumerate((24, 92, 160)):
        magnet(mx, 60, 34, on=i != 1)
    girder(40, 96, 40)
    girder(120, 88, 46)
    girder(178, 104, 40, 5, 0.12)                              # one already yanked crooked
    lifted(110, 92, 22)
    crate(64, 116); crate(140, 116)                            # wood: stays put
    humanoid(62, 112, MET_L, GREEN)
    humanoid(196, 112, DIRT_L, GREEN, face_right=False)
    tracer(69, 117, 186, 116)
    player(112, 78)                                            # riding a lifted girder
    tk_beam(119, 82, 150, 96, CYAN)
    for lx in (56, 200):
        lamp(lx, 58, bulb=PALE_G, r=20, strength=0.20)
    rubble(12, 118, 226, 123, 34, (MET_D, MET, DIRT))

    # ── 2  the floor of scrap ───────────────────────────────────────────────
    floor_slab(8, 190, 198, 4, (44, 46, 54), (104, 110, 122))
    scrap_pile(12, 198, 170, 22, (MET_D, MET, MET_L, (120, 76, 52), DIRT))
    magnet(60, 148, 34, on=True)
    lifted(77, 176, 26)
    girder(112, 178, 44)
    humanoid(150, 186, ICE_L, RED, face_right=False)
    ragdoll(96, 182)
    crate(24, 188, 7, False)
    lamp(140, 148, bulb=PALE_G, r=18, strength=0.18)

    # ── 3  coil room ────────────────────────────────────────────────────────
    floor_slab(236, 340, 118, 4, (44, 46, 54), (104, 110, 122))
    for i, cx in enumerate((250, 282, 314)):
        rect(cx, 74, cx + 18, 114, MET_D)
        rect(cx, 74, cx + 18, 74, MET_L)
        for k in range(5):
            rect(cx + 2, 78 + k * 7, cx + 16, 80 + k * 7, COIL)
        if i == 1:
            glow(cx + 9, 94, 30, FIELD, 0.26)
            sparks(cx + 9, 76, 12, 14, FIELD)
    cable(238, 62, 338, 66, 6)
    pipe_run(238, 338, 58, c=(56, 60, 70), lit=MET_L)
    humanoid(244, 106, MET_L, BLUE, face_right=False)
    binny(320, 96)
    valve(332, 100, 5)

    # ── 4  rail store ───────────────────────────────────────────────────────
    floor_slab(196, 320, 200, 4, (44, 46, 54), (104, 110, 122))
    for i in range(4):                                          # stock racked in rows
        girder(204, 166 + i * 9, 100)
    magnet(240, 152, 34, on=False)                              # dead coil above the rack
    humanoid(300, 188, MET_L, RED, face_right=False)
    crate(212, 190); crate(230, 190, 7, False)
    lifted(268, 168, 12)
    lamp(288, 154, bulb=PALE_G, r=18, strength=0.18)

    # ── 5  exit shaft ───────────────────────────────────────────────────────
    floor_slab(346, 392, 196, 4, (44, 46, 54), (104, 110, 122))
    ladder(360, 64, 190, 8, 10)
    for y in range(70, 190, 40):
        magnet(352, y, 36, on=y == 110)
    door(352, 162, 30, 30)
    glow(367, 177, 22, PALE_G, 0.16)
    lifted(372, 140, 10)

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 12:  THE MAGNET HALL")
    callout(6, 24, "1 SUBSTATION - SPAWN", 44, 40)
    callout(120, 22, "2 MAIN HALL - THE CEILING TAKES METAL", 110, 76)
    callout(258, 30, "4 COIL ROOM - CUT THE POWER", 292, 92)
    callout(6, 134, "3 SCRAP FLOOR - IT ALL WANTS TO GO UP", 77, 176)
    callout(196, 136, "5 RAIL STORE - DEAD COIL, SAFE ROOM", 240, 170)
    callout(230, 212, "6 EXIT SHAFT - RIDE THE PULSE", 366, 150)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("MAGNETS OVERRULE TELEKINESIS", (170, 180, 195)),
        ("WOOD AND STONE STAY PUT", (200, 150, 90)),
        ("GOAL: KILL THE COILS, CLIMB OUT", GREEN_L),
    ], width=146)

    return save(out_path("LevelConcept_MagnetHall.png"))


if __name__ == "__main__":
    build()
