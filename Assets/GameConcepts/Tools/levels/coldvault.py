"""Concept 04 - THE COLD VAULT.

The counterweight to the Scrapworks: there, fire was the danger; here it is the only
tool that works. Ice is terrain — you walk on it — until something warm touches it,
and then the floor is gone and so is whatever was standing on it. Every ice shelf in
this level is drawn thin enough that the player can see it is temporary.

Fire is scarce on purpose: a hand-carried brazier, and whatever wood the player is
willing to burn. The guardian at the end cannot be shot out of its ice, only melted.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 48
FROST = (206, 232, 240)
DEEP = (30, 48, 60)


# ── local props ─────────────────────────────────────────────────────────────
def snow_drift(x, base, w, h):
    for i in range(w * 2):
        t = i / (w * 2)
        d = int(h * (1 - (2 * t - 1) ** 2))
        sx = x + int(t * w)
        rect(sx, base - d, sx, base, FROST)
        px(sx, base - d, (255, 255, 255))


def snowfall(y1, n=160):
    for _ in range(n):
        px(rnd() * W, rnd() * y1, FROST, 0.15 + rnd() * 0.35)


def ice_shelf(x0, x1, y, thick=3, cracked=False):
    """A walkable ledge of ice. Thin, lit along the top, dark underneath."""
    rect(x0, y, x1, y + thick, ICE, 0.92)
    rect(x0, y, x1, y, ICE_XL)
    rect(x0, y + thick, x1, y + thick, DEEP)
    if cracked:
        for _ in range(int((x1 - x0) / 8) + 2):
            cx = x0 + rnd() * (x1 - x0)
            line(cx, y, cx + 2 - rnd() * 4, y + thick, DEEP, 0.85)
    icicles(x0, x1, y + thick, int((x1 - x0) / 12) + 2)


def brazier(x, y, lit=True):
    rect(x, y, x + 7, y + 4, MET_D)
    rect(x, y, x + 7, y, MET_L)
    for k in range(3):
        rect(x + 1 + k * 2, y + 5, x + 1 + k * 2, y + 8, MET_D)
    if lit:
        fire_patch(x, y - 5, x + 7, y + 2, 14, 1.2)
        glow(x + 3, y - 2, 26, F_MID, 0.34)
        embers(x, y - 14, x + 7, y - 4, 12)


def steam(x0, y0, x1, y1, n=60):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), 1 + rnd() * 3,
             pick([(190, 210, 220), (150, 176, 190)]), 0.15)


def vent(x, y, w=8, up=True):
    rect(x, y, x + w, y + 2, MET_D)
    rect(x, y, x + w, y, MET_L)
    d = -1 if up else 1
    steam(x, y + d * 20, x + w, y, 34)


def frozen_mech(x, y):
    """A roboguard entombed mid-stride. Reads as a threat that is not awake yet."""
    rect(x + 4, y, x + 18, y + 12, MET)            # hull
    rect(x + 4, y, x + 18, y, MET_XL)
    rect(x + 6, y + 3, x + 16, y + 8, (26, 34, 42))
    rect(x + 7, y + 5, x + 9, y + 6, RED_L)        # optics, still on
    rect(x + 13, y + 5, x + 15, y + 6, RED_L)
    glow(x + 11, y + 6, 12, RED_L, 0.18)
    rect(x, y + 6, x + 4, y + 8, MET_L)            # arms
    rect(x + 18, y + 5, x + 24, y + 7, MET_L)
    rect(x + 22, y + 3, x + 26, y + 9, MET)        # weapon block
    rect(x + 6, y + 12, x + 8, y + 20, MET_D)      # legs
    rect(x + 14, y + 12, x + 16, y + 20, MET_D)
    rect(x + 4, y + 20, x + 10, y + 22, MET_L)
    rect(x + 12, y + 20, x + 18, y + 22, MET_L)
    rect(x - 4, y - 6, x + 30, y + 26, ICE, 0.42)  # the ice around it
    frame(x - 4, y - 6, x + 30, y + 26, ICE_L)
    line(x - 2, y - 4, x + 12, y + 24, ICE_XL, 0.35)
    line(x + 28, y - 2, x + 10, y + 24, ICE_XL, 0.25)


def build():
    new_canvas(400, 225, seed=4711)

    # ── whiteout sky ────────────────────────────────────────────────────────
    sky(SURF, hi=(178, 196, 208), lo=(120, 140, 156), smog=6)
    for x in range(W):                                    # far ridge line
        h = 12 + int(6 * (1 + math.sin(x / 26.0)) + rnd() * 3)
        rect(x, SURF - h, x, SURF, (108, 128, 144))
        px(x, SURF - h, (168, 190, 202))
    rock_mass(SURF, base=(64, 78, 92), dark=(44, 55, 66), mid=(86, 102, 118),
              soil=(120, 142, 158), soil_lit=FROST)

    ROOMS = [
        (8, 66, 180, 118),      # intake hall
        (8, 130, 204, 190),     # ice cavern
        (150, 108, 190, 138),   # hall -> cavern
        (206, 118, 312, 180),   # thaw plant
        (196, 146, 214, 172),   # cavern -> plant
        (300, 72, 392, 150),    # vault chamber
        (300, 152, 392, 206),   # exit lock
        (280, 108, 306, 132),   # plant -> vault
        (172, 60, 300, 100),    # frozen duct along the top
    ]
    carve_all(ROOMS, air=(20, 26, 32), lip=(72, 92, 108))

    # ── surface: intake yard under snow ─────────────────────────────────────
    snow_drift(0, SURF, 60, 9)
    snow_drift(96, SURF, 70, 11)
    snow_drift(250, SURF, 90, 8)
    for hx, hy in ((32, 26), (232, 22)):                  # buried sheds
        rect(hx, hy, hx + 46, SURF, (72, 84, 96))
        rect(hx, hy, hx + 46, hy, (110, 130, 146))
        rect(hx, hy - 2, hx + 46, hy - 1, FROST)
        for x in range(hx + 3, hx + 43, 8):
            rect(x, hy + 5, x + 4, hy + 10, (40, 50, 60))
    for px_ in (86, 190):                                 # frozen pipe runs
        pipe_run(px_, px_ + 70, SURF - 8, c=(60, 72, 84), lit=ICE_L)
        icicles(px_, px_ + 70, SURF - 5, 10)
    beam(150, SURF - 30, SURF, 3, (74, 88, 100), ICE_L)   # iced-up gantry
    rect(120, SURF - 32, 182, SURF - 30, (74, 88, 100))
    icicles(120, 182, SURF - 29, 14)
    rect(60, SURF - 6, 96, SURF - 4, MET_D)               # hatch down
    rect(60, SURF - 6, 96, SURF - 6, MET_L)
    player(66, SURF - 12, coat=(64, 84, 104), cuff=ICE_L)
    binny(78, SURF - 22, eye=ICE_XL, thruster=ICE_L)
    humanoid(206, SURF - 12, ICE_L, BLUE, face_right=False)
    humanoid(280, SURF - 12, BLUE_L, ICE, face_right=False)

    # ── 1  intake hall: the belt stopped years ago ──────────────────────────
    floor_slab(8, 180, 114, 4, (40, 50, 60), (96, 118, 132))
    conveyor(20, 150, 104, 1, chevron=ICE_L)
    for bx in (34, 58, 96, 124):                          # cargo frozen to the belt
        ice_block(bx, 92, 9, 10)
    icicles(10, 178, 70, 22)
    rect(8, 66, 180, 69, (52, 66, 78), 0.6)               # frost on the ceiling
    humanoid(160, 102, ICE_L, CYAN, face_right=False)     # icer, guarding the belt
    tk_beam(166, 106, 140, 96, ICE_XL)                    # its freeze cone
    crate(64, 106); crate(88, 106, 7, False)
    vent(112, 114, 10, up=True)
    lamp(46, 68, bulb=ICE_XL, tint=(180, 220, 235), r=20, strength=0.18)
    lamp(132, 68, bulb=ICE_XL, tint=(180, 220, 235), r=20, strength=0.18)
    ladder(160, 116, 136, 6, 8, ICE_L, (60, 72, 84))

    # ── 2  ice cavern: shelves over open water ──────────────────────────────
    water(10, 178, 202, 188, DEEP, (86, 140, 160))
    rect(10, 183, 202, 188, (18, 30, 40), 0.7)            # it gets darker fast
    for wx in range(12, 200, 7):
        rect(wx, 178, wx + 3, 178, (120, 176, 196), 0.55)
    glow(100, 180, 66, (70, 130, 156), 0.24)
    ice_shelf(14, 78, 146, 3, cracked=True)
    ice_shelf(96, 158, 160, 3)
    ice_shelf(40, 96, 172, 4, cracked=True)
    ice_shelf(168, 202, 150, 3)
    icicles(10, 200, 132, 26)
    for cx, cy, r in ((60, 138, 5), (130, 154, 4), (176, 144, 6)):
        disc(cx, cy, r, ICE, 0.5)
        ring(cx, cy, r, ICE_L)
    player(120, 149, coat=(64, 84, 104), cuff=ICE_L)      # mid-run over thin ice
    tk_beam(127, 153, 150, 140, ICE_XL)
    binny(104, 132, eye=ICE_XL, thruster=ICE_L)
    humanoid(52, 161, ICE_L, CYAN)                        # icers hold the low route
    humanoid(84, 133, BLUE_L, CYAN)
    ragdoll(150, 166, ICE_XL)
    for _ in range(14):                                   # shards on the water
        sx = 12 + rnd() * 186
        rect(sx, 177, sx + 2 + rnd() * 3, 178, ICE_L, 0.8)
    brazier(24, 142)                                      # the one fire you start with
    crate(30, 166); crate(58, 166)

    # ── 3  thaw plant: fire on tap, if you can move it ─────────────────────
    floor_slab(206, 312, 176, 4, (40, 50, 60), (96, 118, 132))
    steam(208, 120, 310, 176, 70)
    pipe_run(208, 308, 122, c=(60, 72, 84), lit=MET_L)
    for vx in (222, 252, 284):
        vent(vx, 168, 10, up=True)
    brazier(232, 160)
    brazier(268, 160)
    glow(250, 158, 46, F_MID, 0.20)
    ice_shelf(206, 250, 140, 3, cracked=True)             # shelf right over the heat
    icicles(206, 306, 126, 12)
    crate(292, 168); crate(300, 168, 7, False)
    humanoid(296, 156, ICE_L, RED, face_right=False)
    barrel(214, 168, MET, MET_L, RED_L)
    rubble(208, 172, 306, 176, 26, ((60, 72, 84), ICE, MET_D))

    # ── 4  the vault: a guardian in the ice ─────────────────────────────────
    floor_slab(296, 392, 146, 4, (40, 50, 60), (96, 118, 132))
    glow(344, 104, 54, (60, 130, 160), 0.26)
    for cx in (304, 318, 384):                            # frozen cascade behind it
        rect(cx, 74, cx + 5, 146, ICE, 0.26)
        rect(cx, 74, cx, 146, ICE_L, 0.34)
    rect(324, 138, 372, 146, (46, 58, 70))                # pedestal
    rect(324, 138, 372, 138, (96, 118, 132))
    frozen_mech(330, 112)
    icicles(302, 390, 76, 20)
    ice_block(304, 126, 12, 18)
    ice_block(374, 124, 14, 20)
    for cx, cy in ((312, 92), (382, 88)):                 # thaw consoles, still powered
        rect(cx, cy, cx + 6, cy + 8, (40, 52, 64))
        rect(cx + 1, cy + 1, cx + 5, cy + 4, CYAN, 0.8)
        glow(cx + 3, cy + 3, 12, CYAN, 0.22)
    rubble(298, 142, 390, 146, 24, (ICE, MET_D, (96, 118, 132)))

    # ── 5  exit lock, heated ────────────────────────────────────────────────
    floor_slab(300, 392, 202, 4, (40, 50, 60), (96, 118, 132))
    door(344, 166, 32, 32, MET, F_MID, MET_D)
    glow(360, 182, 30, F_MID, 0.24)
    for vx in (308, 322):
        vent(vx, 198, 8, up=True)
    pipe_run(302, 342, 158, c=(60, 72, 84), lit=F_MID)
    for _ in range(20):
        px(302 + rnd() * 38, 160 + rnd() * 3, F_MID, 0.5)
    plank(302, 196, 340, 196, 2, burn=True)

    snowfall(SURF + 4, 150)
    vignette(0.5)

    # ── sheet furniture ─────────────────────────────────────────────────────
    title_bar("PHYSFUN - LEVEL CONCEPT 04:  THE COLD VAULT")
    callout(6, 24, "1 INTAKE YARD - SPAWN", 70, 42)
    callout(120, 22, "2 DEAD BELT - CARGO FROZEN ON", 96, 96)
    callout(250, 26, "6 THE VAULT - MELT, DO NOT SHOOT", 340, 118)
    callout(6, 122, "3 ICE SHELVES - THIN, LIT, TEMPORARY", 60, 152)
    callout(206, 100, "4 THAW PLANT - CARRY THE FIRE", 250, 160)
    callout(208, 196, "5 BLACK WATER - DO NOT FALL", 150, 182)
    callout(300, 214, "7 HEATED LOCK", 348, 196)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("FIRE IS THE KEY, NOT THE THREAT", (170, 180, 195)),
        ("ICE IS TERRAIN UNTIL IT IS NOT", (170, 180, 195)),
        ("GOAL: THAW THE GUARDIAN OUT", GREEN_L),
    ], width=146)

    return save(out_path("LevelConcept_ColdVault.png"))


if __name__ == "__main__":
    build()
