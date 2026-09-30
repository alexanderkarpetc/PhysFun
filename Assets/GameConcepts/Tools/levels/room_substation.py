"""Room concept 01 - THE SUBSTATION.

One room, drawn at game scale. The toy is ArcField: a transformer in the
middle of the room throws an arc at the nearest metal inside its reach, every few
seconds, and does not care whose metal it is. So the room is sorted by material -
a steel gantry and a steel floor grate that carry the arc, a timber scaffold that
does not - and every setpiece in it is a way of choosing where the next arc lands.

The enemies are all in the room when you walk in, and they are placed by the same
rule: grenadiers up on the gantry, riot brutes on the grate - their steel shields make
them lightning rods walking towards you - and one sentinel on the scaffold, where the
arcs cannot reach it. What you do about any of that is up to you; by the time the banks
are on the floor and the gas rack has gone off it is a different room.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

FLOOR = 340
GANTRY = 166
DECK = 196
LAMP = (255, 214, 140)
PORCELAIN = (180, 172, 150)
PORCELAIN_D = (120, 110, 95)
COPPER = (184, 148, 120)
SLATE = (54, 60, 56)


# ── local props ─────────────────────────────────────────────────────────────
def grate_floor(x0, x1, y, broken=None):
    """Steel grating over the cable trench. Conducts - that is the point of it."""
    for x in range(int(x0), int(x1) + 1):
        if broken and broken[0] <= x <= broken[1]:
            continue
        rect(x, y, x, y + 3, MET_D)
        px(x, y, MET_L)
        if x % 5 == 0:
            rect(x, y + 1, x, y + 2, CAVE)


def gantry(x0, x1, y, hangers):
    """Steel walkway hung on chains from the roof. No handrail: a rail would be a
    solid bar at waist height, and this game collides with every pixel."""
    rect(x0, y, x1, y + 3, MET)
    rect(x0, y, x1, y, MET_XL)
    rect(x0, y + 3, x1, y + 3, MET_D)
    for x in range(int(x0) + 3, int(x1), 9):
        px(x, y + 2, MET_D)
    for hx, top in hangers:
        chain(hx, top, y)
        rect(hx - 1, y - 1, hx + 2, y, MET_D)


def insulator(x, y0, y1):
    """Porcelain bushing: stacked sheds, alternating light and dark."""
    for y in range(int(y0), int(y1) + 1):
        half = 3 if (y - y0) % 4 < 2 else 2
        rect(x - half, y, x + half, y, PORCELAIN if (y - y0) % 4 < 2 else PORCELAIN_D)


def transformer(x0, x1, top, floor):
    rect(x0 - 10, floor - 16, x1 + 10, floor - 1, STONE_D)          # plinth
    rect(x0 - 10, floor - 16, x1 + 10, floor - 16, STONE_L)
    rect(x0, top + 22, x1, floor - 17, MET)                         # tank
    rect(x0, top + 22, x0, floor - 17, MET_L)
    rect(x1, top + 22, x1, floor - 17, MET_D)
    for x in range(int(x0) + 6, int(x1) - 3, 5):                    # cooling fins
        rect(x, top + 30, x + 1, floor - 22, MET_D)
        px(x, top + 30, MET_L)
    rect(x0 - 3, top + 18, x1 + 3, top + 22, MET_D)                 # lid
    rect(x0 - 3, top + 18, x1 + 3, top + 18, MET_L)
    rect(x0 + 8, top + 36, x0 + 26, top + 48, (30, 34, 40))         # rating plate
    frame(x0 + 8, top + 36, x0 + 26, top + 48, MET_L)
    for k in range(3):
        rect(x0 + 11, top + 39 + k * 3, x0 + 23, top + 39 + k * 3, HAZARD, 0.7)
    lx, rx = x0 + 18, x1 - 18
    insulator(lx, top, top + 17)
    insulator(rx, top, top + 17)
    # horn gap on top: two rods leaning out, the arc climbs between them
    line(lx, top, lx - 10, top - 26, MET_XL)
    line(rx, top, rx + 10, top - 26, MET_XL)
    for k in range(4):
        t = k / 3
        y = top - 4 - t * 20
        arc(lx - t * 8, y, rx + t * 8, y, jag=3, seg=6, fork=0.0)
    glow((lx + rx) / 2, top - 14, 50, CYAN, 0.18)


def battery_bank(cx, top, bottom):
    """A rack of cells hung on one chain. Shoot the chain."""
    chain(cx, top, bottom - 18)
    line(cx - 10, bottom - 16, cx, bottom - 20, MET_L)
    line(cx + 11, bottom - 16, cx + 1, bottom - 20, MET_L)
    rect(cx - 13, bottom - 16, cx + 14, bottom, MET_D)
    rect(cx - 13, bottom - 16, cx + 14, bottom - 16, MET_L)
    for k in range(5):
        x = cx - 11 + k * 5
        rect(x, bottom - 13, x + 3, bottom - 2, (40, 46, 50))
        rect(x, bottom - 13, x + 3, bottom - 12, pick([RED_L, GREEN_L, HAZARD]))
    glow(cx, bottom - 8, 14, CYAN, 0.1)


def switchboard(x, floor):
    """Two knife switches on a slate panel: G for the gantry, F for the floor."""
    top = floor - 44
    rect(x + 4, floor - 8, x + 8, floor - 1, MET_D)
    rect(x + 22, floor - 8, x + 26, floor - 1, MET_D)
    rect(x, top, x + 30, floor - 8, SLATE)
    frame(x, top, x + 30, floor - 8, MET_D)
    rect(x, top, x + 30, top, MET_L)
    # G - open (blade up), F - open (blade up). The player throws them.
    for k, (sx, lab) in enumerate(((x + 8, "G"), (x + 21, "F"))):
        rect(sx - 2, top + 20, sx + 2, top + 22, MET_L)                 # hinge
        line(sx, top + 20, sx - 1, top + 7, COPPER)
        line(sx + 1, top + 20, sx, top + 7, COPPER)
        rect(sx - 3, top + 5, sx + 3, top + 6, WOOD)                     # handle
        rect(sx - 2, top + 28, sx + 2, top + 30, MET)                    # jaws
        text(sx - 1, top + 31, lab, HAZARD, shadow=False)
    disc(x + 15, top + 3, 1.2, RED_L)
    glow(x + 15, top + 3, 5, RED_L, 0.4)


def gas_rack(x, floor, n=4):
    """Pressurised bottles against the wall. One arc in here and the wall behind is
    gone - which is the way into the cache."""
    rect(x - 2, floor - 26, x + n * 10, floor - 25, MET_D)             # restraint bar
    for k in range(n):
        bx = x + k * 10
        c = [GREEN, RED, MET_L, GREEN][k % 4]
        rect(bx, floor - 32, bx + 7, floor - 1, c)
        rect(bx, floor - 32, bx, floor - 1, tuple(min(255, v + 30) for v in c))
        rect(bx + 1, floor - 35, bx + 6, floor - 33, c)
        rect(bx + 2, floor - 38, bx + 5, floor - 36, MET_D)             # valve cap
        rect(bx, floor - 18, bx + 7, floor - 17, PALE_G, 0.6)            # band
    rect(x - 2, floor - 26, x + n * 10, floor - 26, MET_L)


def scaffold(x0, x1, deck, floor, posts):
    """Timber: the only floor in the room the arc will not jump to."""
    for x in posts:
        beam(x, deck + 3, floor - 1, 3)
    for a, b in zip(posts, posts[1:]):                                 # cross braces
        line(a + 3, deck + 6, b, floor - 6, WOOD_D)
    rect(x0, deck, x1, deck + 3, WOOD)
    rect(x0, deck, x1, deck, WOOD_L)
    rect(x0, deck + 3, x1, deck + 3, WOOD_D)
    for x in range(int(x0) + 8, int(x1), 12):
        px(x, deck + 1, WOOD_D)


def cable_bundle(x0, x1, y):
    for k, c in enumerate(((30, 30, 34), (62, 46, 40), (40, 44, 58))):
        for x in range(int(x0), int(x1)):
            px(x, y + k * 2 + int(1.5 * math.sin(x * 0.07 + k)), c)


def cable_spool(cx, floor, r=12):
    """Wooden cable drum. Wood, so the arc ignores it; round, so it rolls."""
    cy = floor - r - 1
    disc(cx, cy, r, WOOD)
    ring(cx, cy, r, WOOD_L)
    disc(cx, cy, r - 4, (40, 44, 58))
    for k in range(3):
        ring(cx, cy, r - 5 - k, (62, 46, 40) if k % 2 else (40, 44, 58))
    disc(cx, cy, 2, WOOD_D)
    line(cx + r - 5, cy - 2, cx + r + 6, floor - 1, (40, 44, 58))


def crane(x0, x1, rail_y, tx, hook_y):
    """Overhead crane: rail on brackets, trolley, chain, and a laminated steel core on
    the hook. The heaviest metal in the room, parked right over the floor."""
    rect(x0, rail_y, x1, rail_y + 2, MET_D)
    rect(x0, rail_y, x1, rail_y, MET_L)
    for bx in range(int(x0) + 6, int(x1), 40):
        rect(bx, rail_y - 8, bx + 1, rail_y, MET_D)
    rect(tx - 8, rail_y + 3, tx + 8, rail_y + 8, MET)
    rect(tx - 8, rail_y + 3, tx + 8, rail_y + 3, MET_L)
    disc(tx - 5, rail_y + 2, 1.5, MET_XL)
    disc(tx + 5, rail_y + 2, 1.5, MET_XL)
    chain(tx, rail_y + 9, hook_y)
    ring(tx, hook_y + 2, 2.5, MET_L)
    line(tx - 1, hook_y + 4, tx - 12, hook_y + 10, MET_L)
    line(tx + 1, hook_y + 4, tx + 12, hook_y + 10, MET_L)
    rect(tx - 14, hook_y + 10, tx + 14, hook_y + 26, MET)
    rect(tx - 14, hook_y + 10, tx + 14, hook_y + 10, MET_XL)
    for y in range(int(hook_y) + 12, int(hook_y) + 26, 2):
        rect(tx - 13, y, tx + 13, y, MET_D)


def locker(x, floor, h=26, open_=False):
    rect(x, floor - h, x + 10, floor - 1, (70, 82, 78))
    rect(x, floor - h, x + 10, floor - h, (110, 124, 118))
    rect(x + 5, floor - h, x + 5, floor - 1, (44, 52, 50))
    for k in range(3):
        rect(x + 2, floor - h + 3 + k, x + 3, floor - h + 3 + k, (44, 52, 50))
        rect(x + 7, floor - h + 3 + k, x + 8, floor - h + 3 + k, (44, 52, 50))


def scorch(x0, x1, y, n=40):
    for _ in range(n):
        px(x0 + rnd() * (x1 - x0), y + (rnd() - 0.5) * 4, pick([CHAR, (44, 40, 38)]), 0.8)


def lob(x0, y0, x1, y1, peak=40, c=F_MID):
    """A grenade's arc, dotted."""
    for i in range(0, 21):
        t = i / 20
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t - peak * 4 * t * (1 - t)
        px(x, y, c, 0.9 if i % 2 else 0.4)
    disc(x1, y1, 2, MET_D)
    px(x1, y1 - 2, F_HOT)


def build():
    new_canvas(800, 450, seed=4417)
    cw, ch = canvas_size()
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=40)

    carve_all([
        (70, 92, 690, FLOOR),          # the hall
        (230, 50, 520, 110),           # roof dome over the transformer
        (26, 122, 90, GANTRY),         # upper-left alcove: exit A, off the gantry
        (686, 142, 772, DECK),         # upper-right alcove: exit B, off the scaffold
        (18, 282, 80, FLOOR),          # entry
        (704, 270, 772, FLOOR),        # the cache behind the masonry
        (150, FLOOR, 560, 368),        # cable trench under the grate - crawlable
    ], rough=3)
    rock_teeth(90, 690, 94, 40)
    rock_teeth(240, 510, 52, 20)
    rock_teeth(30, 88, 124, 6)
    rock_teeth(690, 770, 144, 8)

    # ── floors ──────────────────────────────────────────────────────────────
    floor_slab(18, 150, FLOOR, 6)
    floor_slab(560, 772, FLOOR, 6)
    floor_slab(150, 560, 368, 5)
    floor_slab(26, 90, GANTRY, 4)
    floor_slab(686, 772, DECK, 4)
    cable_bundle(152, 558, 360)
    for x in (220, 330, 470):
        sparks(x, 358, 10, 14, CYAN)
    grate_floor(150, 560, FLOOR, broken=(282, 306))
    rect(536, FLOOR, 556, FLOOR + 3, CAVE)                          # lifted panel at the far end
    rect(538, FLOOR - 8, 556, FLOOR - 6, MET_D)
    rect(538, FLOOR - 8, 556, FLOOR - 8, MET_L)

    # ── ceiling services ────────────────────────────────────────────────────
    pipe_run(92, 228, 100)
    pipe_run(522, 686, 98)
    pipe_run(92, 228, 106, c=(62, 46, 40), lit=(110, 80, 62))
    cable(236, 60, 360, 70, sag=10, c=(40, 44, 58))
    cable(420, 70, 516, 60, sag=12, c=(40, 44, 58))
    scorch(300, 470, 56, 60)
    scorch(340, 450, FLOOR + 1, 30)

    # ── lighting ────────────────────────────────────────────────────────────
    for lx in (120, 610):
        lamp(lx, 95, drop=8, bulb=LAMP, tint=LAMP, r=60, strength=0.2)
    for lx in (46, 726):
        lamp(lx, 124, drop=4, bulb=LAMP, tint=LAMP, r=30, strength=0.2)

    # ── 1  the way in ───────────────────────────────────────────────────────
    doorway(18, FLOOR)
    hero(48, FLOOR)
    binny_half(58, FLOOR - 58)

    # ── 2  the gantry, and a way out off the end of it ──────────────────────
    gantry(88, 300, GANTRY, [(120, 94), (200, 94), (280, 94)])
    ladder(96, GANTRY + 4, FLOOR - 1, w=8, step=7)
    doorway(30, GANTRY)
    stand("Grenadier", 176, GANTRY, flip=True)
    stand("Grenadier", 236, GANTRY, flip=True)
    lob(230, GANTRY - 14, 118, FLOOR - 4, peak=30)
    cable(150, 318, 300, GANTRY + 2, sag=40, c=(40, 44, 58))            # G feed

    # ── 3  switchboard ──────────────────────────────────────────────────────
    switchboard(120, FLOOR)
    cable(150, 322, 190, FLOOR + 6, sag=4, c=(40, 44, 58))              # F feed

    # ── 4  transformer ──────────────────────────────────────────────────────
    transformer(345, 435, 250, FLOOR)

    # ── 5  battery banks over the floor ─────────────────────────────────────
    battery_bank(240, 60, 214)
    arc(372, 236, 252, 208, jag=7, seg=9)                               # nearest metal

    # ── 6  grate + trench; the brutes on it ─────────────────────────────────
    stand("RiotBrute", 480, FLOOR, flip=True)
    stand("RiotBrute", 530, FLOOR, flip=True)
    arc(418, 238, 474, 326, jag=6, seg=8)                               # to the shield
    glow(478, 326, 16, CYAN, 0.3)
    stand("Minespider", 294, FLOOR + 6)                                 # out of the trench
    stand("Minespider", 262, FLOOR, flip=True)
    corpse(210, FLOOR)

    # ── floor clutter: cover, most of it metal, i.e. more arc targets ───────
    crate(234, FLOOR - 13, 12)
    crate(236, FLOOR - 24, 10)
    locker(158, FLOOR)
    locker(169, FLOOR, open_=True)
    cable_spool(456, FLOOR)
    barrel(548, FLOOR - 15, MET, MET_L, HAZARD, w=9, h=14)
    rubble(60, FLOOR - 2, 150, FLOOR, 40, (ROCK_M, ROCK_D, MET_D))
    rubble(560, FLOOR - 2, 700, FLOOR, 40, (ROCK_M, ROCK_D, MET_D))

    # ── crane over the right half ───────────────────────────────────────────
    crane(470, 686, 112, 536, 160)

    # ── 7  timber scaffold; the sentinel up on it ───────────────────────────
    scaffold(566, 690, DECK, FLOOR, [572, 616, 660])
    ladder(640, DECK + 4, FLOOR - 1, w=8, step=7)
    stand("Sentinel", 606, DECK, flip=True)
    doorway(764, DECK)

    # ── 8  gas rack, masonry, a store behind it ─────────────────────────────
    gas_rack(574, FLOOR, 4)                         # under the scaffold, against the posts
    masonry(688, 266, 704, FLOOR - 1)
    for k in range(3):
        crate(716 + k * 16, FLOOR - 13, 12)


    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(14, 104)
    vignette(0.35)
    btitle_bar("PHYSFUN - ROOM CONCEPT 01:  THE SUBSTATION",
               "ONE ROOM / GAME SCALE")
    bcallout(34, 256, "1 IN", 22, 300)
    bcallout(104, 50, "2 STEEL GANTRY ON CHAINS", 200, 120)
    bcallout(56, 206, "3 SWITCHES: G / F", 134, 300)
    bcallout(560, 52, "4 ARCS TO NEAREST METAL", 420, 232)
    bcallout(560, 76, "5 DROP THE BANK OR THE CORE", 536, 150)
    bcallout(384, 382, "6 LIVE ON F", 420, 356)
    bcallout(620, 124, "7 WOOD: ARCS SKIP IT", 650, 198)
    bcallout(598, 250, "8 GAS RACK, THIN WALL", 700, 290)
    blegend(22, 378, [
        ("BEATS", CYAN),
        ("METAL CARRIES THE ARC, WOOD DOES NOT", (170, 180, 195)),
        ("GANTRY, SHIELDS, ONE UP ON THE WOOD", F_MID),
    ], 342)
    return save(out_path("RoomConcept_Substation.png"), scale=2)


if __name__ == "__main__":
    build()
