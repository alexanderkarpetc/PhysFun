"""Room concept 09 - THE FALLEN TOWER (big room).

~3.6 x 3 screens at game scale. A cult's bell tower stood on the surface over this
cavern until the roof gave; it came down through the hole it made and broke in three.
The base still stands, leaning. The middle section lies at 28 degrees from a single
steel girder up to the hole, and is the way out. The belfry lies on its side on the
floor with the bell rolled out of it, and the spire is stuck point-down in the rubble.

So the room is one building at three angles: in the base a floor is a floor, in the
middle it is a ramp, and in the belfry it is a wall and the walls are floors. The cult
moved back in anyway. Everything is masonry, which fractures, and the middle section
is still settling on its girder.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

TW = 120                                   # tower width
BRONZE = (150, 112, 62)
BRONZE_L = (196, 156, 92)
BRONZE_D = (96, 70, 40)
CANDLE = (255, 214, 140)
DAY = (190, 200, 214)


# ── the tower, drawn upright in local coords and pasted at an angle ─────────
def section(h, floors, door_at=None, belfry=False, spire=False, broken_top=True,
            broken_bottom=True, shelves=(), crypt=None):
    def draw():
        w = TW
        masonry(0, 0, 11, h - 1)                          # walls
        masonry(w - 12, 0, w - 1, h - 1)
        for fy in floors:                                 # floors, with a stair hole
            masonry(12, fy, w - 13, fy + 7)
            rect(w - 42, fy, w - 22, fy + 7, KEY)
        for fy0, fy1 in zip([0] + list(floors), list(floors) + [h]):
            for k in range(0, 10):                        # a stair up to the hole above
                sx = w - 30 - k * 7
                sy = fy1 - 4 - k * ((fy1 - fy0 - 10) / 10)
                if fy0 + 8 < sy < fy1 - 2:
                    rect(sx, sy, sx + 6, sy + 1, WOOD)
        for fy0, fy1 in zip([0] + list(floors), list(floors) + [h]):
            for wx in (0, w - 12):                        # slit windows
                my = (fy0 + fy1) // 2
                if fy1 - fy0 > 30:
                    rect(wx + 4, my - 8, wx + 7, my + 6, KEY)
        if door_at is not None:
            rect(0, door_at - 34, 11, door_at - 1, KEY)
            rect(0, door_at - 36, 13, door_at - 34, STONE_L)
        for sx, fy in shelves:                            # the cult moved back in
            rect(sx, fy - 20, sx + 22, fy - 1, WOOD_D)
            for k in range(3):
                rect(sx + 1, fy - 19 + k * 6, sx + 21, fy - 19 + k * 6, WOOD)
                for b in range(0, 20, 3):
                    rect(sx + 1 + b, fy - 18 + k * 6, sx + 2 + b, fy - 15 + k * 6,
                         pick([RED, GREEN, BLUE, DIRT_L, PURPLE]))
        if crypt:
            y0, y1 = crypt
            masonry(12, y0, w - 13, y0 + 7)
            masonry(12, y1, w - 13, y1 + 7)
            rect(40, y0 + 14, 80, y1 - 4, STONE_D)       # the sarcophagus
            rect(40, y0 + 14, 80, y0 + 16, STONE_L)
            rect(52, y0 + 20, 68, y1 - 10, (44, 40, 36))
        if belfry:
            for ax in (18, 70):                           # arched openings
                rect(ax + 4, 18, ax + 30, 64, KEY)
            rect(0, 0, w - 1, 10, STONE)
            rect(0, 0, w - 1, 0, STONE_L)
            rect(16, 12, w - 17, 15, WOOD_D)              # the bell beam, bell gone
        if spire:
            for y in range(0, 60):
                half = (w / 2) * y / 60
                rect(w / 2 - half, y, w / 2 + half, y, STONE_D if (y // 6) % 2 else STONE)
            rect(w / 2 - 1, 0, w / 2 + 1, 4, BRONZE_L)
        for edge, on in ((0, broken_top and not spire and not belfry), (h - 1, broken_bottom)):
            if on:                                        # a snapped end, not a cut one
                for x in range(w):
                    d = int(4 + rnd() * 16)
                    for k in range(d):
                        yy = edge + k if edge == 0 else edge - k
                        px(x, yy, KEY)
    return draw


def bell_local():
    """The bell on its own canvas, mouth down; pasted on its side where it rolled."""
    for y in range(0, 50):
        t = y / 50
        half = 12 + 18 * t ** 2.2
        rect(29 - half, y + 4, 29 + half, y + 4, BRONZE)
        px(29 - half, y + 4, BRONZE_L)
        px(29 + half, y + 4, BRONZE_D)
    rect(0, 50, 58, 55, BRONZE_D)
    rect(0, 50, 58, 50, BRONZE_L)
    rect(25, 0, 33, 5, BRONZE_D)
    for k in range(3):
        rect(10, 34 + k * 4, 48, 34 + k * 4, BRONZE_L)


def girder(x0, y0, x1, y1):
    for t in range(-3, 4):
        line(x0 + t, y0, x1 + t, y1, MET if abs(t) < 3 else MET_D)
    line(x0 - 3, y0, x1 - 3, y1, MET_L)
    rect(x0 - 12, y0 - 2, x0 + 12, y0, MET_D)
    for k in range(6):
        t = k / 6
        px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, MET_XL)


def daylight(x, top, bottom, w):
    for y in range(int(top), int(bottom)):
        t = (y - top) / (bottom - top)
        half = w * (0.5 + t * 0.9)
        rect(x - half, y, x + half, y, DAY, 0.07 * (1 - t))
    for _ in range(60):
        px(x - w + rnd() * w * 2, top + rnd() * (bottom - top), DAY, 0.4)


def candle(x, y):
    rect(x, y - 4, x + 1, y - 1, (199, 190, 160))
    px(x, y - 6, CANDLE)
    glow(x, y - 6, 16, CANDLE, 0.3)


def rubble_heap(m, cx, w, h, floor):
    for x in range(int(cx - w), int(cx + w)):
        d = abs(x - cx) / w
        ys = floor - h * (1 - d * d) - rnd() * 4
        for y in range(int(ys), int(floor) + 30):
            if (x, y) in m:
                px(x, y, pick([STONE, STONE_D, ROCK_M, STONE_L, DIRT]))
            elif y > floor:
                break
    for _ in range(int(w)):
        x = cx - w + rnd() * 2 * w
        d = abs(x - cx) / w
        y = floor - h * (1 - d * d) - 2
        rect(x, y - 3, x + 4 + rnd() * 5, y, pick([STONE, STONE_L, STONE_D]))


def build():
    new_canvas(1600, 900, seed=77031)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)

    m = cave_mask([
        ("blob", 800, 480, 650, 300),                        # the cavern
        ("tube", [(770, 46), (745, 120), (765, 200)], 46),   # the hole it came through
        ("tube", [(790, 120), (900, 100), (1000, 112)], 18), # side passage off the hole: exit A
        ("tube", [(0, 440), (120, 452), (210, 470)], 24),    # entry
        ("tube", [(1420, 520), (1600, 500)], 24),            # exit B
        ("blob", 250, 250, 110, 50),                         # high gallery, west
        ("blob", 1330, 730, 130, 46),                        # the spire's pocket
    ])
    carve_mask(m)
    for (x0, x1, y) in ((200, 700, 196), (830, 1400, 196), (160, 360, 204)):
        rock_teeth(x0, x1, y, int((x1 - x0) / 10))
    daylight(765, 46, 700, 40)

    floor_y = floor_at(m, 800, 700)
    # ── the three pieces and the spire ──────────────────────────────────────
    A_h, A_c, A_a = 300, (330, floor_at(m, 330, 700) - 146), -0.10
    to_a = draw_rotated(TW, A_h, section(A_h, (70, 150, 226), door_at=A_h - 8,
                                          shelves=((20, 150), (30, 226)), broken_bottom=False),
                        A_c[0], A_c[1], A_a)
    B_h, B_c, B_a = 440, (668, 372), 0.494
    to_b = draw_rotated(TW, B_h, section(B_h, (80, 170, 260, 350), shelves=((22, 170),)),
                        B_c[0], B_c[1], B_a)
    C_h, C_c, C_a = 260, (1080, floor_y - 66), 1.72
    to_c = draw_rotated(TW, C_h, section(C_h, (100, 190), belfry=True, broken_bottom=True,
                                          crypt=(110, 180)),
                        C_c[0], C_c[1], C_a)
    D_h = 120
    sp = (1350, floor_at(m, 1350, 700) - 52)
    draw_rotated(TW, D_h, section(D_h, (), spire=True, broken_top=False), sp[0], sp[1], math.pi - 0.18)
    draw_rotated(58, 58, bell_local, 1236, floor_y - 30, math.pi / 2 + 0.1)

    bot = to_b(TW / 2, B_h)
    girder(bot[0] - 40, floor_at(m, bot[0] - 40, 600), bot[0] + 4, bot[1] - 2)
    rubble_heap(m, 330, 140, 40, floor_at(m, 330, 700))
    rubble_heap(m, 560, 90, 26, floor_at(m, 560, 700))
    rubble_heap(m, 1350, 90, 20, floor_at(m, 1350, 740))
    rubble_heap(m, 900, 60, 12, floor_y)

    # ── a camp on a shelf off the east wall, chains off the roof ────────────
    rock_blob(1420, 470, 100, 16, clip=(0, 0, 1600, 486))
    camp = 456
    rect(1330, camp - 2, 1500, camp, ROCK_L)
    for k in range(3):                                   # bedrolls
        rect(1350 + k * 30, camp - 4, 1372 + k * 30, camp - 1, pick([RED, PURPLE, DIRT]))
    rect(1440, camp - 10, 1446, camp - 1, MET_D)         # brazier
    fire_patch(1436, camp - 18, 1450, camp - 10, 12, 1.2)
    glow(1443, camp - 14, 40, F_MID, 0.3)
    for k in range(4):
        candle(1470 + k * 6, camp)
    for cx_, drop in ((1120, 180), (1210, 260), (1290, 140)):
        top = ceil_at(m, cx_, 400) + 1
        chain(cx_, top, top + drop)
        rect(cx_ - 5, top + drop, cx_ + 6, top + drop + 8, pick([BRONZE_D, MET_D]))
    stand("WizRamskull", 1400, camp, flip=True)

    # ── the cult, back in residence ─────────────────────────────────────────
    for lx, ly in ((60, 150), (40, 226), (60, 70)):
        wx, wy = to_a(lx, ly)
        candle(int(wx), int(wy))
    for lx, ly in ((40, 170), (60, 260)):
        wx, wy = to_b(lx, ly)
        candle(int(wx), int(wy))
    for x in (200, 240, 290):
        candle(x, floor_at(m, x, 250))
    ax, ay = to_a(60, 150)
    stand("WizBonecrown", int(ax), int(ay))
    bx, by = to_b(50, 260)
    stand("WizRamskull", int(bx), int(by), flip=True)
    cx, cy = to_c(TW - 12, 150)
    stand("WizHollowhood", int(cx), int(cy) - 1)
    tx, ty = to_b(60, 80)
    stand("BloodMage", int(tx), int(ty), flip=True)
    stand("Reaper", 1180, floor_y, flip=True)
    stand("Gaper", 480, floor_at(m, 480, 700))
    stand("Gaper", 820, floor_y, flip=True)
    stand("Minespider", 250, floor_at(m, 250, 250))
    stand("Minespider", 1400, floor_at(m, 1400, 740), flip=True)
    corpse(620, floor_at(m, 620, 700))
    crypt = to_c(60, 145)

    # ── ways in and out ─────────────────────────────────────────────────────
    ey = floor_at(m, 60, 440)
    doorway(4, ey)
    hero(60, ey)
    binny_half(86, ey - 60)
    doorway(1014, floor_at(m, 1000, 100))
    doorway(1584, floor_at(m, 1580, 500))


    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(4, 330)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 09:  THE FALLEN TOWER",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(20, 600, "1 IN FROM THE WEST", 60, ey - 10)
    bcallout(860, 56, "2 IT CAME THROUGH THE ROOF", 770, 150)
    bcallout(20, 780, "3 ONE GIRDER HOLDS THE MIDDLE", bot[0] - 16, bot[1] + 60)
    bcallout(40, 100, "4 IN HERE A FLOOR IS A RAMP", int(to_b(60, 170)[0]), int(to_b(60, 170)[1]))
    bcallout(1180, 150, "5 THE BELFRY, ON ITS SIDE", int(to_c(60, 40)[0]), int(to_c(60, 40)[1]))
    bcallout(1180, 560, "6 THE BELL ROLLS", 1236, floor_y - 30)
    bcallout(1450, 620, "7 SPIRE", 1350, sp[1])
    bcallout(560, 790, "8 A CRYPT ON ITS SIDE", int(crypt[0]), int(crypt[1]))
    bcallout(1200, 60, "9 EXIT A: UP THE TOWER", 1010, 96)
    blegend(20, 822, [
        ("BEATS", CYAN),
        ("ONE BUILDING AT THREE ANGLES, STILL SETTLING", (170, 180, 195)),
        ("IN THE RUBBLE, A WIZARD PER PIECE, ONE AT THE TOP", F_MID),
    ], 660)
    return save(out_path("RoomConcept_FallenTower.png"), scale=2)


if __name__ == "__main__":
    build()
