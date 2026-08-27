"""Concept 13 - THE VENT SHAFTS.

Air is the level. The fans are still running somewhere below, so the ducts have a current:
updraft columns you fall up rather than down, cross-draughts that push a thrown object off
line, and — the part that matters — a draught that carries fire.

Light a filter at the bottom of a shaft and the flame arrives at the top before the player
does. That is the whole level: a fire you start deliberately, in a place you have already
decided not to be.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *  # noqa: F403,E402

SURF = 40
DUCT = (92, 98, 108)
DUCT_D = (52, 56, 64)
DRAFT = (176, 200, 214)


def duct_run(x0, y0, x1, y1, w=16, vertical=False):
    """Sheet-metal duct with ribs. Ribs are what stop it reading as a corridor."""
    if vertical:
        rect(x0, y0, x0 + w, y1, (30, 34, 40))
        rect(x0, y0, x0, y1, DUCT)
        rect(x0 + w, y0, x0 + w, y1, DUCT_D)
        for y in range(int(y0), int(y1), 12):
            rect(x0 - 1, y, x0 + w + 1, y + 1, DUCT)
    else:
        rect(x0, y0, x1, y0 + w, (30, 34, 40))
        rect(x0, y0, x1, y0, DUCT)
        rect(x0, y0 + w, x1, y0 + w, DUCT_D)
        for x in range(int(x0), int(x1), 12):
            rect(x, y0 - 1, x + 1, y0 + w + 1, DUCT)


def draft(x0, y0, x1, y1, up=True, n=26, c=DRAFT):
    """Arrows of moving air. Drawn as streaks with a head, so direction reads instantly."""
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        y = y0 + rnd() * (y1 - y0)
        ln = 4 + rnd() * 7
        if up:
            line(x, y, x, y - ln, c, 0.30)
            px(x - 1, y - ln + 1, c, 0.35)
            px(x + 1, y - ln + 1, c, 0.35)
        else:
            line(x, y, x + ln, y, c, 0.30)
            px(x + ln - 1, y - 1, c, 0.35)
            px(x + ln - 1, y + 1, c, 0.35)


def filter_panel(x, y, w=26, h=14, burning=False):
    rect(x, y, x + w, y + h, (78, 74, 58))
    frame(x, y, x + w, y + h, MET_L)
    for i in range(int(h // 3)):
        rect(x + 1, y + 1 + i * 3, x + w - 1, y + 2 + i * 3, (54, 52, 40))
    if burning:
        fire_patch(x, y - 4, x + w, y + h, 16, 1.4)
        glow(x + w / 2, y + h / 2, 30, F_MID, 0.32)
        embers(x, y - 20, x + w, y - 2, 16)


def build():
    new_canvas(400, 225, seed=1313)

    sky(SURF, hi=(126, 134, 146), lo=(80, 88, 100), smog=6)
    for hx, hy, w in ((10, 16, 90), (270, 20, 100)):
        rect(hx, hy, hx + w, SURF, (58, 62, 72))
        rect(hx, hy, hx + w, hy, (86, 92, 104))
        for x in range(hx + 6, hx + w - 6, 12):
            rect(x, hy + 6, x + 6, hy + 12, (38, 42, 50))
    for cx in (140, 200):                                       # extract cowls on the roof
        rect(cx, SURF - 16, cx + 22, SURF, (66, 72, 82))
        rect(cx - 2, SURF - 20, cx + 24, SURF - 16, (94, 100, 112))
        steam_plume(cx + 11, SURF - 22, 16, 22)

    rock_mass(SURF, base=(62, 66, 74), dark=(42, 46, 54), mid=(84, 90, 100),
              soil=(76, 78, 74), soil_lit=(128, 132, 126))

    ROOMS = [
        (130, 44, 220, 96),     # plenum under the cowls
        (16, 100, 200, 150),    # cross gallery
        (140, 92, 200, 108),    # plenum -> gallery
        (34, 150, 88, 210),     # updraft shaft
        (16, 196, 200, 216),    # sump duct
        (210, 96, 320, 160),    # fan room
        (196, 118, 214, 140),   # gallery -> fan room
        (206, 166, 330, 212),   # filter bank
        (240, 154, 280, 172),   # fan room -> filters
        (326, 60, 392, 208),    # riser to the exit
        (312, 120, 332, 142),   # fan room -> riser
    ]
    carve_all(ROOMS, air=(20, 24, 30), lip=(78, 84, 96))

    # ── surface ─────────────────────────────────────────────────────────────
    rect(96, SURF - 4, 136, SURF - 2, MET_D)
    rect(96, SURF - 4, 136, SURF - 4, MET_L)
    player(106, SURF - 12)
    binny(120, SURF - 22)
    humanoid(250, SURF - 12, MET_L, RED, face_right=False)
    scrap_pile(300, SURF, 60, 10, (MET_D, MET, DIRT))

    # ── 1  plenum ───────────────────────────────────────────────────────────
    floor_slab(130, 220, 92, 4, (44, 48, 56), (104, 110, 120))
    duct_run(140, 44, 0, 92, 18, vertical=True)
    duct_run(190, 44, 0, 92, 18, vertical=True)
    draft(134, 90, 216, 50, up=True, n=30)
    grate(150, 186, 68)
    humanoid(206, 80, ICE_L, BLUE, face_right=False)
    crate(160, 84)
    lamp(174, 46, bulb=PALE_G, r=18, strength=0.18)

    # ── 2  cross gallery ────────────────────────────────────────────────────
    floor_slab(16, 200, 146, 4, (44, 48, 56), (104, 110, 120))
    duct_run(16, 104, 196, 0, 16)
    draft(24, 118, 190, 132, up=False, n=28)
    catwalk(20, 194, 138, drop=6, posts=18)
    humanoid(56, 133, MET_L, GREEN)
    humanoid(150, 133, DIRT_L, GREEN, face_right=False)
    tracer(63, 138, 142, 138)
    player(96, 133)
    tk_beam(103, 137, 138, 130, CYAN)                          # throw drifts with the draught
    crate(36, 138, 7, False); crate(174, 138)
    for lx in (44, 168):
        lamp(lx, 102, bulb=PALE_G, r=18, strength=0.18)

    # ── 3  updraft shaft ────────────────────────────────────────────────────
    duct_run(36, 150, 0, 208, 48, vertical=True)
    draft(40, 206, 82, 156, up=True, n=34, c=(200, 220, 230))
    for i, y in enumerate(range(160, 204, 14)):                # ledges you do not need
        x0 = 38 if i % 2 else 66
        rect(x0, y, x0 + 18, y + 3, MET_D)
        rect(x0, y, x0 + 18, y, MET_L)
    player(56, 172)
    binny(44, 156)
    embers(40, 176, 84, 206, 20)                               # the fire is already coming up
    glow(60, 200, 34, F_MID, 0.24)

    # ── 4  fan room ─────────────────────────────────────────────────────────
    floor_slab(210, 320, 156, 4, (44, 48, 56), (104, 110, 120))
    for fx, fy, r in ((240, 124, 16), (288, 128, 12)):
        fan(fx, fy, r)
        glow(fx, fy, r + 14, (150, 180, 200), 0.14)
    draft(214, 150, 318, 110, up=True, n=22)
    duct_run(210, 100, 318, 0, 14)
    humanoid(216, 144, MET_L, RED, face_right=False)
    valve(306, 146, 5)
    rubble(212, 150, 316, 155, 24, (MET_D, DIRT, (70, 74, 84)))

    # ── 5  filter bank ──────────────────────────────────────────────────────
    floor_slab(206, 330, 208, 4, (44, 48, 56), (104, 110, 120))
    for i, fx in enumerate((212, 248, 284)):
        filter_panel(fx, 182, 28, 20, burning=i == 1)
    duct_run(206, 170, 328, 0, 10)
    draft(210, 200, 326, 178, up=True, n=18, c=(220, 190, 150))
    humanoid(312, 194, ICE_L, RED, face_right=False)
    crate(318, 196, 7, False)
    embers(240, 160, 290, 182, 22)

    # ── 6  riser to the exit ────────────────────────────────────────────────
    duct_run(340, 60, 0, 206, 44, vertical=True)
    draft(344, 204, 382, 66, up=True, n=30)
    for i, y in enumerate(range(72, 200, 16)):
        x0 = 342 if i % 2 else 366
        rect(x0, y, x0 + 16, y + 3, MET_D)
        rect(x0, y, x0 + 16, y, MET_L)
    fan(362, 190, 14)
    door(348, 66, 28, 26)
    glow(362, 79, 22, PALE_G, 0.16)
    binny(356, 120)

    vignette()

    title_bar("PHYSFUN - LEVEL CONCEPT 13:  THE VENT SHAFTS")
    callout(6, 24, "1 ROOF HATCH - SPAWN", 112, 38)
    callout(258, 24, "6 RISER - THE WAY UP", 362, 100)
    callout(6, 62, "2 PLENUM - AIR MOVES, SO DO YOU", 174, 70)
    callout(6, 88, "3 CROSS GALLERY - THROWS DRIFT", 110, 124)
    callout(96, 160, "4 UPDRAFT - FALL UPWARD", 60, 180)
    callout(206, 104, "5 FAN ROOM - KILL THE DRAUGHT", 240, 124)
    callout(150, 216, "7 FILTER BANK - LIGHT IT AND LEAVE", 262, 192)
    legend(206, 58, [
        ("BEATS", CYAN),
        ("THE DRAUGHT CARRIES FIRE", (170, 180, 195)),
        ("AIM UPWIND OR MISS", (200, 150, 90)),
        ("GOAL: BURN BELOW, CLIMB ABOVE", GREEN_L),
    ], width=130)

    return save(out_path("LevelConcept_VentShafts.png"))


if __name__ == "__main__":
    build()
