"""Concept 14 - THE SLAG FOUNDRY.

The end of the scrap chain, and the loudest room in the game: molten metal runs in open
channels, ladles cross overhead on rails, and the casting floor is a grid of moulds that are
either empty holes or full of something that will kill you for touching it.

Nothing here needs a trap. The foundry is already doing its job; the level is about crossing
a working factory that has no idea you are in it, and about the one lever that tips a ladle
where you want it rather than where the schedule wants it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 42
SLAG = (255, 132, 40)
SLAG_HOT = (255, 236, 170)
SLAG_D = (168, 58, 18)
CRUST = (72, 44, 36)


def melt(x0, y0, x1, y1, crusted=True):
    """A run of molten metal. Crust on top, brightest in the middle, light spilling out."""
    rect(x0, y0, x1, y1, SLAG_D)
    rect(x0, y0 + 1, x1, y1 - 1, SLAG)
    rect(x0, (y0 + y1) // 2, x1, (y0 + y1) // 2, SLAG_HOT)
    if crusted:
        for x in range(int(x0), int(x1), 5):
            if chance(0.45):
                rect(x, y0, x + 2 + int(rnd() * 3), y0 + 1, CRUST)
    glow((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 0.5 + 14, SLAG, 0.30)
    embers(x0, y0 - 12, x1, y0, int((x1 - x0) / 6))


def ladle(x, y, r=11, pouring=False):
    disc(x, y, r, MET)
    ring(x, y, r, MET_XL)
    rect(x - r - 3, y - 2, x + r + 3, y, MET_D)              # trunnion bar
    rect(x - 2, y - r - 8, x + 2, y - r, MET_D)              # hanger
    disc(x, y - 2, r - 3, SLAG, 0.9)
    disc(x, y - 3, r - 6, SLAG_HOT, 0.9)
    glow(x, y, r + 16, SLAG, 0.26)
    if pouring:
        for k in range(22):
            px(x + r - 2 + (rnd() - 0.5) * 3, y + k, pick([SLAG, SLAG_HOT]), 0.9)
        glow(x + r, y + 22, 20, SLAG, 0.30)


def mould(x, y, w=22, full=False):
    rect(x, y, x + w, y + 12, MET_D)
    rect(x, y, x + w, y, MET_L)
    if full:
        rect(x + 2, y + 2, x + w - 2, y + 10, SLAG)
        rect(x + 3, y + 4, x + w - 3, y + 7, SLAG_HOT)
        glow(x + w / 2, y + 6, 20, SLAG, 0.26)
    else:
        rect(x + 2, y + 2, x + w - 2, y + 11, (24, 22, 24))


def build():
    new_canvas(400, 225, seed=1414)

    sky(SURF, hi=(128, 100, 88), lo=(80, 66, 62), smog=9)
    for sx, top, w in ((28, 8, 8), (66, 18, 6), (300, 12, 9)):
        rect(sx, top, sx + w, SURF, (66, 60, 60))
        rect(sx, top, sx + w, top, (94, 86, 84))
        for i in range(16):
            disc(sx + w / 2 + (rnd() - 0.5) * 9, top - 2 - i * 2, 1.4 + i * 0.22,
                 (200, 160, 130), 0.13)
    rect(120, 20, 240, SURF, (62, 58, 60))
    rect(120, 20, 240, 20, (92, 86, 86))
    for x in range(126, 236, 12):
        rect(x, 26, x + 6, 34, (176, 92, 40), 0.7)             # windows lit from inside
    glow(180, 34, 60, SLAG, 0.12)

    rock_mass(SURF, base=(66, 60, 58), dark=(44, 40, 40), mid=(88, 80, 76),
              soil=(80, 66, 52), soil_lit=(138, 114, 82))

    ROOMS = [
        (8, 58, 240, 122),      # casting floor
        (8, 140, 176, 200),     # tap cellar
        (30, 116, 84, 146),     # floor -> cellar
        (246, 54, 340, 118),    # crucible bay
        (232, 76, 250, 98),     # floor -> crucible
        (182, 146, 320, 204),   # slag channel
        (250, 112, 292, 152),   # crucible -> channel
        (346, 56, 392, 198),    # cooling stair / exit
        (314, 160, 350, 186),   # channel -> exit
    ]
    carve_all(ROOMS, air=(22, 20, 22), lip=(88, 78, 72))

    # ── surface ─────────────────────────────────────────────────────────────
    rect(0, SURF - 4, 116, SURF - 2, MET_D)
    rect(0, SURF - 4, 116, SURF - 4, MET_L)
    scrap_pile(250, SURF, 80, 13, (MET_D, MET, (120, 76, 52), DIRT))
    player(40, SURF - 12)
    binny(54, SURF - 22)
    humanoid(232, SURF - 12, MET_L, RED, face_right=False)

    # ── 1  casting floor ────────────────────────────────────────────────────
    floor_slab(8, 240, 118, 4, (46, 42, 44), (108, 100, 96))
    rect(10, 60, 238, 62, MET_D)                               # ladle rail
    rect(10, 60, 238, 60, MET_L)
    ladle(70, 78, 11, pouring=True)
    ladle(168, 76, 9)
    for i, mx in enumerate((24, 60, 100, 140, 180, 214)):
        mould(mx, 106, 22, full=i in (1, 4))
    humanoid(120, 106, MET_L, GREEN)
    humanoid(200, 106, DIRT_L, GREEN, face_right=False)
    tracer(127, 111, 194, 111)
    player(96, 106)
    tk_beam(103, 110, 130, 100, CYAN)
    embers(12, 64, 236, 104, 40)
    for lx in (44, 208):
        lamp(lx, 62, bulb=(255, 214, 150), tint=SLAG, r=20, strength=0.20)

    # ── 2  tap cellar ───────────────────────────────────────────────────────
    floor_slab(8, 176, 196, 4, (46, 42, 44), (108, 100, 96))
    melt(10, 186, 174, 194)
    for tx in (40, 96, 148):                                   # taps dripping into the run
        rect(tx, 150, tx + 8, 166, MET_D)
        rect(tx + 2, 166, tx + 6, 184, SLAG, 0.9)
        glow(tx + 4, 176, 22, SLAG, 0.26)
    plank(20, 90, 176, 4)                                      # a plank over molten metal
    crate(112, 172); crate(130, 172, 7, False)
    humanoid(158, 172, ICE_L, RED, face_right=False)
    ragdoll(70, 168, SLAG_HOT)
    steam_plume(120, 184, 16, 20, (200, 170, 150))

    # ── 3  crucible bay ─────────────────────────────────────────────────────
    floor_slab(246, 340, 114, 4, (46, 42, 44), (108, 100, 96))
    rect(272, 62, 316, 106, MET_D)                             # the crucible itself
    frame(272, 62, 316, 106, MET_L)
    rect(276, 66, 312, 74, SLAG)
    rect(278, 68, 310, 71, SLAG_HOT)
    glow(294, 76, 48, SLAG, 0.28)
    for k in range(4):
        rect(272, 78 + k * 8, 316, 79 + k * 8, MET)
    valve(324, 80, 5)
    rect(320, 84, 336, 106, MET_D)                             # the lever you came for
    rect(322, 88, 334, 94, CYAN, 0.85)
    glow(328, 91, 18, CYAN, 0.24)
    humanoid(252, 102, MET_L, BLUE, face_right=False)
    binny(258, 84)
    embers(248, 60, 338, 110, 26)

    # ── 4  slag channel ─────────────────────────────────────────────────────
    floor_slab(182, 320, 200, 4, (46, 42, 44), (108, 100, 96))
    melt(184, 188, 318, 198, crusted=True)
    for gx in range(190, 316, 26):                             # stepping plates over the run
        rect(gx, 184, gx + 12, 187, MET_D)
        rect(gx, 184, gx + 12, 184, MET_XL)
    ladle(240, 162, 10)
    rect(184, 148, 318, 150, MET_D)                            # overhead rail
    rect(184, 148, 318, 148, MET_L)
    humanoid(288, 176, MET_L, RED, face_right=False)
    player(200, 174)
    ragdoll(268, 180, SLAG_HOT)
    embers(184, 168, 318, 190, 30)

    # ── 5  cooling stair ────────────────────────────────────────────────────
    floor_slab(346, 392, 194, 4, (46, 42, 44), (108, 100, 96))
    stairs(348, 188, 8, 6, 16, MET_D, MET_L)
    for i, y in enumerate(range(72, 180, 26)):                 # cooling castings on racks
        rect(352, y, 386, y + 3, MET_D)
        rect(352, y, 386, y, MET_L)
        if i % 2 == 0:
            rect(356, y - 6, 378, y, SLAG_D)
            rect(358, y - 5, 376, y - 2, SLAG, 0.8)
            glow(367, y - 3, 20, SLAG, 0.18)
    door(352, 60, 30, 26)
    glow(367, 73, 22, PALE_G, 0.16)

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 14:  THE SLAG FOUNDRY")
    callout(6, 24, "1 CHARGE DECK - SPAWN", 44, 40)
    callout(120, 22, "2 CASTING FLOOR - LADLES ON A SCHEDULE", 70, 78)
    callout(258, 30, "4 CRUCIBLE - TIP IT YOURSELF", 328, 90)
    callout(6, 128, "3 TAP CELLAR - A PLANK OVER MOLTEN METAL", 56, 178)
    callout(184, 130, "5 SLAG CHANNEL - STEP PLATES ONLY", 250, 190)
    callout(240, 212, "6 COOLING STAIR - EXIT", 366, 120)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("THE FACTORY IGNORES YOU", (170, 180, 195)),
        ("MOLTEN METAL IS NOT FIRE - IT STAYS", (200, 150, 90)),
        ("GOAL: TIP A LADLE, WALK THE CRUST", GREEN_L),
    ], width=152)

    return save(out_path("LevelConcept_SlagFoundry.png"))


if __name__ == "__main__":
    build()
