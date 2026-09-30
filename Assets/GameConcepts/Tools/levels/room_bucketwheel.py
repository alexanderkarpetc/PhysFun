"""Room concept 07 - THE BUCKET WHEEL (big room).

~3.6 x 3 screens at game scale, and not a storey in it. The room is round because the
thing in it is round: a bucket-wheel excavator that dug its way into the cavern and
was left running. Twelve buckets on a 20-unit wheel turn clockwise through the room -
scoop at the bottom, lift up the west side, tip at the top onto a belt that runs up
the boom into the machine house. Everything about the room's geography changes with
the wheel's angle: a bucket is a lift, a platform, a hazard and a way to the niche.

The rest is cave, cut as shapes rather than floors: a slanted crawl from the entry to
a grotto, the pit under the wheel, a bowl for the machine house, and the spoil heap
the house has been tipping into a chamber below it for longer than anyone was here.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

WC = (720, 490)            # wheel centre
WR = 205                   # rim radius
P0, P1 = (720, 490), (1170, 300)
LAMP = (255, 214, 140)
RUBBER = (44, 44, 48)


def rock_fill(x0, y0, x1, y1):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            r = rnd()
            px(x, y, ROCK_D if r < 0.13 else ROCK_M if r < 0.2 else ROCK)


def polar(theta, r):
    return WC[0] + math.cos(theta) * r, WC[1] + math.sin(theta) * r


# ── the wheel ───────────────────────────────────────────────────────────────
def bucket_local():
    """One bucket, drawn opening-up; draw_rotated turns it to face out of the rim.
    Big on purpose: on a machine like this a bucket is a room you can stand in."""
    rect(2, 8, 5, 37, MET)                                   # side plates
    rect(46, 8, 49, 37, MET_D)
    rect(2, 33, 49, 37, MET)                                 # back plate, against the rim
    rect(6, 10, 45, 32, (58, 46, 34))
    rect(2, 8, 2, 37, MET_L)
    for k in range(7):                                       # teeth on the lip
        rect(4 + k * 7, 2, 6 + k * 7, 7, MET_XL)
    rect(2, 7, 49, 8, MET_XL)
    for _ in range(26):
        px(8 + rnd() * 36, 12 + rnd() * 18, pick([DIRT_L, ROCK_L, DIRT, DIRT_D]))


def wheel():
    cx, cy = WC
    for y in range(cy - WR - 2, cy + WR + 3):                # rim and inner ring
        for x in range(cx - WR - 2, cx + WR + 3):
            d = math.hypot(x - cx, y - cy)
            if WR - 9 <= d <= WR:
                px(x, y, MET_L if d > WR - 1.5 else MET_D if d < WR - 7.5 else MET)
            elif 108 <= d <= 114:
                px(x, y, MET if d > 109 else MET_D)
    for k in range(10):                                      # spokes
        a = k * math.tau / 10 + 0.1
        for t in range(-1, 2):
            nx, ny = -math.sin(a) * t, math.cos(a) * t
            line(cx + math.cos(a) * 34 + nx, cy + math.sin(a) * 34 + ny,
                 cx + math.cos(a) * (WR - 8) + nx, cy + math.sin(a) * (WR - 8) + ny,
                 MET_L if t < 0 else MET)
        line(*polar(a, WR - 30), *polar(a + math.tau / 10, WR - 30), MET_D)
    disc(cx, cy, 34, MET_D)
    ring(cx, cy, 34, MET_L)
    disc(cx, cy, 12, MET)
    ring(cx, cy, 12, MET_XL)
    for k in range(8):
        a = k * math.tau / 8
        disc(cx + math.cos(a) * 24, cy + math.sin(a) * 24, 2, MET_L)
    for k in range(12):                                      # buckets
        th = k * math.tau / 12 + 0.12
        bx, by = polar(th, WR + 16)
        draw_rotated(52, 38, bucket_local, bx, by, math.atan2(math.cos(th), -math.sin(th)))
    for k in range(16):                                      # clockwise, dotted
        th = math.radians(196 + k * 4)
        if k % 2 == 0:
            px(*polar(th, WR + 34), PALE_G)
    ax, ay = polar(math.radians(262), WR + 34)
    for k in range(4):
        px(ax - k, ay - k, PALE_G)
        px(ax - k, ay + k, PALE_G)


def boom():
    """Lattice boom from the hub up to the house: two chords, a zigzag web, a belt on
    top running up to the house. It is also the only bridge across the room."""
    dx, dy = P1[0] - P0[0], P1[1] - P0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux                                         # perpendicular...
    if ny < 0:
        nx, ny = -nx, -ny                                    # ...pointing down
    top = [(P0[0] - nx * 14, P0[1] - ny * 14), (P1[0] - nx * 14, P1[1] - ny * 14)]
    bot = [(P0[0] + nx * 14, P0[1] + ny * 14), (P1[0] + nx * 14, P1[1] + ny * 14)]
    for k in range(3):
        line(top[0][0], top[0][1] + k, top[1][0], top[1][1] + k, MET_L if k == 0 else MET)
        line(bot[0][0], bot[0][1] + k, bot[1][0], bot[1][1] + k, MET if k == 0 else MET_D)
    n = int(L / 26)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a = (top[0][0] + (top[1][0] - top[0][0]) * t0, top[0][1] + (top[1][1] - top[0][1]) * t0)
        b = (bot[0][0] + (bot[1][0] - bot[0][0]) * (t0 + t1) / 2,
             bot[0][1] + (bot[1][1] - bot[0][1]) * (t0 + t1) / 2)
        c = (top[0][0] + (top[1][0] - top[0][0]) * t1, top[0][1] + (top[1][1] - top[0][1]) * t1)
        line(*a, *b, MET_D)
        line(*b, *c, MET_D)
    # belt on the top chord, from the tipping chute up to the house
    t_start = 0.22
    for i in range(int(L * (1 - t_start))):
        t = t_start + i / L
        x = top[0][0] + (top[1][0] - top[0][0]) * t
        y = top[0][1] + (top[1][1] - top[0][1]) * t - 2
        px(x, y, RUBBER)
        px(x, y - 1, MET_L if i % 14 else GREEN_L)
    return top


def machine_house(x0, x1, y0, deck):
    """The excavator's house: steel shell, cab on the front corner, machinery inside,
    crawler tracks under it."""
    rect(x0, y0, x1, y0 + 4, MET)                            # roof
    rect(x0, y0, x1, y0, MET_XL)
    rect(x1 - 4, y0, x1, deck, MET)                          # back wall
    rect(x0, y0, x0 + 4, deck - 40, MET)                     # front wall, open below: the boom comes in
    rect(x0, deck, x1, deck + 5, MET_D)                      # deck
    rect(x0, deck, x1, deck, MET_L)
    rect(x0 + 70, y0 + 4, x0 + 74, y0 + 60, MET_D)           # cab bulkhead
    rect(x0, y0 + 60, x0 + 74, y0 + 64, MET_D)               # cab floor
    rect(x0 + 10, y0 + 36, x0 + 50, y0 + 59, (54, 60, 56))   # the controls
    rect(x0 + 10, y0 + 36, x0 + 50, y0 + 36, MET_L)
    for k, up in enumerate((True, False, True)):
        lx = x0 + 18 + k * 12
        line(lx, y0 + 36, lx + (4 if up else -4), y0 + 24, MET_L)
        disc(lx + (4 if up else -4), y0 + 23, 1.8, GREEN_L if up else RED_L)
    disc(x0 + 150, deck - 30, 22, MET)                       # winding drum
    ring(x0 + 150, deck - 30, 22, MET_L)
    disc(x0 + 150, deck - 30, 5, MET_D)
    gear(x0 + 200, deck - 24, 16, teeth=12, c=MET, lit=MET_XL, hub=MET_D)
    rect(x0 + 90, y0 + 90, x1 - 10, y0 + 94, MET_D)          # mezzanine over the machinery
    rect(x0 + 90, y0 + 90, x1 - 10, y0 + 90, MET_L)
    ladder(x1 - 24, y0 + 94, deck - 1, w=8, step=7)
    ladder(x1 - 24, y0 + 6, y0 + 89, w=8, step=7)
    # crawler tracks
    ty0, ty1 = deck + 6, deck + 42
    rect(x0 + 10, ty0, x1 - 10, ty1, (40, 40, 44))
    rect(x0 + 10, ty0, x1 - 10, ty0 + 2, MET_D)
    for x in range(int(x0) + 14, int(x1) - 12, 7):
        rect(x, ty0, x + 3, ty0 + 3, MET)
        rect(x, ty1 - 3, x + 3, ty1, MET)
    for x in range(int(x0) + 30, int(x1) - 20, 34):
        disc(x, (ty0 + ty1) // 2, 11, MET)
        ring(x, (ty0 + ty1) // 2, 11, MET_L)
        disc(x, (ty0 + ty1) // 2, 3, MET_D)
    for fx in (x0 + 20, x1 - 30):                            # floodlights
        lamp(fx, y0 + 6, drop=4, bulb=LAMP, tint=LAMP, r=120, strength=0.2)


def counterweight(ax, ay, bx, by):
    line(ax, ay, bx, by, MET)
    line(ax, ay + 12, bx, by + 6, MET)
    for i in range(6):
        t = i / 6
        line(ax + (bx - ax) * t, ay + (by - ay) * t, ax + (bx - ax) * (t + 1 / 12),
             ay + 12 + (by + 6 - ay - 12) * (t + 1 / 12), MET_D)
    chain(bx - 4, by + 6, by + 30)
    rect(bx - 22, by + 30, bx + 10, by + 70, MET_D)
    rect(bx - 22, by + 30, bx + 10, by + 30, MET_L)
    for k in range(4):
        rect(bx - 20, by + 36 + k * 9, bx + 8, by + 36 + k * 9, MET)
    text(bx - 16, by + 52, "40T", HAZARD, shadow=False)


def spoil_heap(m, x_top, y_top, floor, w):
    """What the house has been tipping: a scree cone under the chute, slumped against
    the east wall, filling only air - so it takes the shape of the chamber it is in."""
    cw, _ = canvas_size()
    wob = [rnd() for _ in range(64)]
    for x in range(int(x_top - w), cw):
        d = max(0.0, x_top - x) / w                          # east of the chute it is banked to the wall
        ys = y_top + (floor - y_top) * min(1.0, d ** 1.5) + 6 * wob[x % 64] - 3
        for y in range(int(ys), int(floor) + 40):
            if (x, y) in m:
                px(x, y, pick([DIRT, DIRT_D, DIRT_L, ROCK_M, DIRT]))
    for _ in range(40):                                      # stones rolling down it
        x = x_top - rnd() * w
        d = abs(x - x_top) / w
        y = y_top + (floor - y_top) * min(1.0, d ** 1.5) - 3
        disc(x, y, 1.5 + rnd() * 2, pick([ROCK_M, ROCK_L]))


def chute(x0, y0, x1, y1):
    for k in range(4):
        line(x0, y0 + k, x1, y1 + k, MET if k else MET_L)
    line(x0 + 8, y0 - 6, x1 + 8, y1 - 6, MET_D)
    for _ in range(30):
        t = rnd()
        px(x0 + (x1 - x0) * t + 2, y0 + (y1 - y0) * t - 2 - rnd() * 3, pick([DIRT_L, DIRT]))


def build():
    new_canvas(1600, 900, seed=5150)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)

    m = cave_mask([
        ("blob", 720, 490, 300, 270),                         # the wheel's cavern
        ("blob", 1310, 275, 265, 125),                        # the bowl the house sits in
        ("tube", [(950, 390), (1080, 320)], 60),              # boom's way between them
        ("tube", [(0, 470), (140, 452), (280, 500), (440, 478)], 26),   # entry
        ("blob", 230, 250, 150, 85),                          # grotto
        ("tube", [(200, 318), (160, 448)], 18),               # slanted crawl entry -> grotto
        ("tube", [(360, 300), (470, 350)], 20),               # grotto -> cavern
        ("blob", 560, 238, 40, 20),                           # the niche only a bucket reaches
        ("tube", [(520, 736), (330, 758), (0, 758)], 22),     # out through the pit
        ("blob", 1300, 632, 250, 130),                        # spoil chamber
    ])
    carve_mask(m)
    rock_fill(1045, 376, 1578, 402)                           # the bowl's floor under the tracks
    floor_slab(1060, 1570, 370, 6)
    m2 = cave_mask([
        ("tube", [(1488, 372), (1506, 490)], 22),             # the chute's hole down to the heap
        ("tube", [(1470, 176), (1600, 146)], 20),             # exit A
    ])
    carve_mask(m2)
    m |= m2
    rock_blob(930, 720, 110, 64)                              # the face the wheel is cutting
    rock_blob(470, 700, 60, 50)
    for (x0, x1, y) in ((440, 1000, 226), (1060, 1560, 156), (90, 370, 170), (1060, 1540, 506)):
        rock_teeth(x0, x1, y, int((x1 - x0) / 10))

    # ── light ───────────────────────────────────────────────────────────────
    for lx, ly, r in ((120, 452, 90), (230, 172, 110), (1300, 510, 130), (560, 222, 50)):
        lamp(lx, ly, drop=4, bulb=LAMP, tint=LAMP, r=r, strength=0.22)
    glow(720, 490, 280, (160, 170, 190), 0.07)

    # ── the machine ─────────────────────────────────────────────────────────
    wheel()
    top = boom()
    chute(820, 300, 870, 402)                                 # the tip at the top of the turn
    machine_house(1160, 1430, 170, 328)
    counterweight(1430, 196, 1552, 172)
    chute(1432, 318, 1496, 470)
    spoil_heap(m, 1500, 486, 764, 300)

    # ── the pit: what the wheel digs, and what it has already dug ───────────
    fy = floor_at(m, 620, 600)
    rubble(520, fy - 3, 900, fy, 120, (DIRT, DIRT_L, ROCK_M, RED))
    stand("Gaper", 620, floor_at(m, 620, 620))
    stand("Gaper", 790, floor_at(m, 790, 640), flip=True)
    bx, by = polar(math.pi + 0.12 + 0.0, WR + 9)
    stand("Gaper", int(bx) - 4, int(by) + 8, flip=True)       # already in a bucket, going up
    corpse(700, floor_at(m, 700, 650))

    # ── grotto, entry ───────────────────────────────────────────────────────
    stand("Minespider", 200, floor_at(m, 200, 250))
    stand("Minespider", 300, floor_at(m, 300, 250), flip=True)
    scrap_pile(120, floor_at(m, 150, 250), 70, 10)
    doorway(4, floor_at(m, 10, 440))
    ey = floor_at(m, 70, 440)
    hero(70, ey)
    binny_half(96, ey - 60)
    scrap_pile(560, floor_at(m, 560, 225) - 8, 40, 8)

    # ── the boom and the house ──────────────────────────────────────────────
    gx, gy = top[0][0] + (top[1][0] - top[0][0]) * 0.55, top[0][1] + (top[1][1] - top[0][1]) * 0.55
    stand("Grenadier", int(gx), int(gy) - 3, flip=True)
    gx, gy = top[0][0] + (top[1][0] - top[0][0]) * 0.8, top[0][1] + (top[1][1] - top[0][1]) * 0.8
    stand("Grenadier", int(gx), int(gy) - 3, flip=True)
    stand("Sentinel", 1196, 230, flip=True)
    stand("RiotBrute", 1300, 328, flip=True)
    stand("Pyro", 1440, floor_at(m, 1440, 560), flip=True)
    doorway(1584, floor_at(m, 1580, 130))
    doorway(10, floor_at(m, 16, 740))


    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(4, 300)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 07:  THE BUCKET WHEEL",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(20, 580, "1 IN FROM THE WEST", 70, ey - 10)
    bcallout(60, 90, "2 THE WHEEL TURNS: BUCKETS ARE LIFTS", 500, 470)
    bcallout(700, 790, "3 TEETH: THE PIT GETS SCOOPED", 770, 712)
    bcallout(880, 150, "4 BOOM: A BRIDGE WITH A BELT", 960, 382)
    bcallout(1240, 90, "5 CAB: STOP, START, REVERSE", 1196, 214)
    bcallout(1100, 440, "6 SPOIL CHUTE", 1470, 410)
    bcallout(1290, 468, "7 CUT THE COUNTERWEIGHT", 1540, 236)
    bcallout(390, 160, "8 RIDE A BUCKET UP", 560, 250)
    bcallout(60, 690, "9 OUT THROUGH THE PIT", 20, 740)
    blegend(20, 822, [
        ("BEATS", CYAN),
        ("THE ROOM IS ONE MACHINE, AND IT TURNS", (170, 180, 195)),
        ("IN THE PIT, ON THE BOOM, IN THE CAB", F_MID),
    ], 660)
    return save(out_path("RoomConcept_BucketWheel.png"), scale=2)


if __name__ == "__main__":
    build()
