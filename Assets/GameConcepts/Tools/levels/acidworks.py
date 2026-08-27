"""Concept 10 - THE ACID WORKS.

The level that edits itself. Acid is the only thing in the game that removes terrain
without the player asking: it eats through a floor over seconds, so a room you crossed once
is not the room you come back to.

That cuts both ways, and the level is laid out to make the player notice: the shortest route
runs over a floor thin enough that the drips beneath it are already through, and the vats you
tip to open a wall are the same vats that take the ground out from under the catwalk.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 46
ACID = (126, 176, 48)
ACID_L = (198, 240, 110)
ACID_D = (70, 100, 34)
STAIN = (98, 116, 52)


def drip(x, y0, y1, n=6):
    for i in range(n):
        t = i / n
        px(x, y0 + (y1 - y0) * t, ACID_L, 0.7 - t * 0.4)
    disc(x, y1, 1.4, ACID_L, 0.8)


def etched(x0, x1, y, depth=6):
    """Floor the acid has been working on. Half-eaten, and it shows."""
    for x in range(int(x0), int(x1)):
        if chance(0.35):
            d = 1 + int(rnd() * depth)
            rect(x, y, x, y + d, (24, 30, 24))
            px(x, y + d, STAIN)


def carboy(x, y, w=12, h=16):
    rect(x, y, x + w, y + h, (60, 74, 52))
    rect(x, y, x + w, y, (100, 122, 82))
    rect(x + 2, y + 5, x + w - 2, y + h - 2, ACID, 0.85)
    rect(x + 2, y + 5, x + w - 2, y + 5, ACID_L)
    rect(x + w // 2 - 2, y - 4, x + w // 2 + 2, y, MET_D)
    glow(x + w / 2, y + 9, 14, ACID_L, 0.20)


def build():
    new_canvas(400, 225, seed=1024)

    sky(SURF, hi=(104, 112, 96), lo=(66, 74, 66), smog=8)
    for hx, hy, w in ((16, 18, 74), (250, 22, 88)):
        rect(hx, hy, hx + w, SURF, (56, 62, 56))
        rect(hx, hy, hx + w, hy, (84, 92, 82))
        for x in range(hx + 5, hx + w - 6, 11):
            rect(x, hy + 6, x + 5, hy + 12, (36, 42, 38))
    for tx in (110, 210):                                       # vent stacks, weeping
        rect(tx, 10, tx + 6, SURF, (62, 68, 62))
        rect(tx, 10, tx + 6, 10, (92, 100, 90))
        drip(tx + 3, 16, SURF - 4, 10)

    rock_mass(SURF, base=(64, 68, 60), dark=(42, 46, 42), mid=(86, 92, 80),
              soil=(74, 76, 54), soil_lit=(128, 132, 88))

    ROOMS = [
        (8, 60, 200, 112),      # vat hall
        (8, 128, 168, 180),     # etched cellar
        (40, 104, 90, 134),     # hall -> cellar
        (206, 66, 320, 128),    # neutraliser bay
        (196, 88, 212, 106),    # hall -> bay
        (180, 136, 300, 196),   # the drip room
        (240, 122, 280, 144),   # bay -> drip room
        (312, 60, 392, 130),    # control platform
        (306, 134, 392, 200),   # exit lock
        (140, 172, 190, 198),   # cellar -> drip room
    ]
    carve_all(ROOMS, air=(20, 24, 22), lip=(74, 82, 70))

    # ── surface ─────────────────────────────────────────────────────────────
    rect(0, SURF - 4, 100, SURF - 2, MET_D)
    rect(0, SURF - 4, 100, SURF - 4, MET_L)
    carboy(64, SURF - 18)
    player(30, SURF - 12, coat=(58, 80, 62), cuff=ACID_L)
    binny(46, SURF - 22, eye=ACID_L, thruster=ACID_L)
    humanoid(230, SURF - 12, MET_L, ACID, face_right=False)
    scrap_pile(300, SURF, 60, 10, (MET_D, STAIN, MET, DIRT))

    # ── 1  vat hall ─────────────────────────────────────────────────────────
    floor_slab(8, 200, 108, 4, (44, 48, 44), (100, 110, 92))
    etched(24, 190, 108, 7)
    for vx in (20, 82, 144):
        vat(vx, 78, vx + 46, 106, ACID, ACID_L)
    catwalk(12, 196, 68, drop=8, posts=16)
    for cx in (58, 120):                                        # walkway planks over the vats
        plank(cx, cx + 34, 74, 3)
    humanoid(40, 56, MET_L, ACID, face_right=False)
    humanoid(160, 56, DIRT_L, ACID, face_right=False)
    tracer(47, 61, 150, 66)
    player(96, 63, coat=(58, 80, 62), cuff=ACID_L)
    tk_beam(103, 67, 128, 76, ACID_L)
    for lx in (66, 168):
        lamp(lx, 60, bulb=ACID_L, tint=(180, 230, 120), r=20, strength=0.20)
    steam_plume(104, 76, 14, 18, (170, 200, 130))

    # ── 2  etched cellar ────────────────────────────────────────────────────
    floor_slab(8, 168, 176, 4, (44, 48, 44), (100, 110, 92))
    liquid_pool(10, 160, 166, 176, ACID_D, ACID_L)
    etched(12, 164, 132, 8)
    for dx in (36, 78, 128):
        drip(dx, 134, 158, 8)
    carboy(96, 142); carboy(112, 144)
    crate(24, 148); crate(140, 148, 7, False)
    ragdoll(60, 150, ACID_L)
    humanoid(150, 148, ICE_L, ACID, face_right=False)
    glow(80, 164, 40, ACID_L, 0.18)

    # ── 3  neutraliser bay ──────────────────────────────────────────────────
    floor_slab(206, 320, 124, 4, (44, 48, 44), (100, 110, 92))
    tank(224, 82, 22, 36, MET, MET_L, MET_D, bands=3)
    tank(258, 86, 20, 32, MET, MET_L, MET_D, bands=2)
    valve(235, 78, 5); valve(268, 82, 5)
    pipe_run(208, 318, 70, c=(58, 64, 58), lit=MET_L)
    for py in (100, 108):
        rect(288, py, 318, py + 3, MET)
        rect(288, py, 318, py, MET_L)
    carboy(296, 104)
    humanoid(212, 112, MET_L, RED, face_right=False)
    steam_plume(246, 78, 16, 22, (200, 210, 190))
    lamp(284, 70, bulb=PALE_G, r=18, strength=0.18)

    # ── 4  the drip room ────────────────────────────────────────────────────
    floor_slab(180, 300, 192, 4, (44, 48, 44), (100, 110, 92))
    liquid_pool(182, 176, 298, 192, ACID_D, ACID_L)
    for dx in range(190, 296, 13):
        drip(dx, 140, 174, 7)
    plank(196, 258, 162, 4)                                     # walkway, being eaten
    for k in range(9):
        px(206 + k * 6, 162 + int(rnd() * 3), ACID_L, 0.7)
    etched(182, 296, 140, 6)
    player(224, 151, coat=(58, 80, 62), cuff=ACID_L)
    humanoid(272, 151, MOSS_L if False else ICE_L, ACID, face_right=False)
    ragdoll(250, 168, ACID_L)
    glow(240, 180, 44, ACID_L, 0.18)

    # ── 5  control platform ─────────────────────────────────────────────────
    floor_slab(312, 392, 126, 4, (44, 48, 44), (100, 110, 92))
    rect(332, 78, 386, 118, (48, 52, 50))
    frame(332, 78, 386, 118, MET_L)
    for i, gx in enumerate((340, 362)):
        rect(gx, 84, gx + 16, 100, MET_D)
        rect(gx + 2, 86, gx + 14, 94, ACID_L if i else CYAN, 0.85)
    glow(360, 92, 30, ACID_L, 0.18)
    valve(348, 108, 5); valve(370, 108, 5)
    humanoid(318, 114, MET_L, BLUE, face_right=False)
    binny(370, 108, eye=ACID_L, thruster=ACID_L)

    # ── 6  exit lock ────────────────────────────────────────────────────────
    floor_slab(306, 392, 196, 4, (44, 48, 44), (100, 110, 92))
    liquid_pool(308, 186, 340, 196, ACID_D, ACID_L)
    stairs(310, 190, 5, 8, 7)
    door(350, 152, 30, 30)
    glow(365, 167, 22, PALE_G, 0.16)
    etched(308, 344, 182, 5)

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 10:  THE ACID WORKS")
    callout(6, 24, "1 DECANT YARD - SPAWN", 34, 40)
    callout(114, 22, "2 VAT HALL - TIP ONE, OPEN A WALL", 104, 88)
    callout(290, 26, "5 CONTROL - NEUTRALISE", 358, 92)
    callout(6, 118, "3 ETCHED CELLAR - THE FLOOR IS THIN", 78, 150)
    callout(206, 56, "4 NEUTRALISER BAY", 246, 90)
    callout(162, 206, "6 DRIP ROOM - IT EATS THE WALKWAY", 226, 164)
    callout(300, 210, "7 EXIT LOCK", 356, 172)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("ACID DELETES TERRAIN, SLOWLY", (170, 180, 195)),
        ("THE MAP CHANGES BEHIND YOU", (200, 150, 90)),
        ("GOAL: CROSS BEFORE THE FLOOR GOES", GREEN_L),
    ], width=146)

    return save(out_path("LevelConcept_AcidWorks.png"))


if __name__ == "__main__":
    build()
