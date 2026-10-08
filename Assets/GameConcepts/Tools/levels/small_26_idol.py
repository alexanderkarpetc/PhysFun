"""Small room S26 - THE IDOL.

A domed cave round one huge stone idol of the cult: a hooded figure with its hands on a
carved ring, three times the height of a man. It has cracked through at the ankles and
leans east, out over its own congregation, and is held up only by three ropes run back
west to rock anchors - one off the roof, one off the wall, one to a deadman in the floor.
The cultists pray at its feet regardless. Cut the ropes and it comes down across the
room, breaking at the cracks into head, chest and robe.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S26"

FLOOR = 342
BASE_X = 120                    # centre of the idol's feet
FEET_H = 20
LEAN = 0.23                     # radians east of upright
BW, BH = 72, 200                # the body, drawn upright on its own canvas
SHELF_Y = 226                   # the east perch

ST = (100, 101, 93)             # idol stone: greyer and greener than the country rock
ST_L = (138, 137, 122)
ST_D = (68, 69, 64)
ST_XD = (44, 45, 43)
MOSS = (70, 82, 52)
ROPE = (166, 144, 100)
ROPE_D = (100, 82, 56)
CANDLE = (206, 196, 160)


def idol_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR:
            continue
        if ((lx - 404) / 70.0) ** 2 + ((ly - SHELF_Y - 14) / 15.0) ** 2 < 1 and ly >= SHELF_Y:
            continue                                         # the east perch
        out.add((x, y))
    return out


def half_w(ly):
    """Silhouette of the idol, half-width by row (0 = hood peak)."""
    if ly < 10:
        return 3 + ly * 1.2
    if ly < 56:
        t = (ly - 32) / 26.0
        return 17 * math.sqrt(max(0.0, 1 - t * t * 0.55))
    if ly < 74:
        return 16 + (ly - 56) * 0.85
    if ly < 128:
        return 31 - (ly - 74) * 0.08
    return 27 + (ly - 128) * 0.12


def draw_body():
    """The idol from the ankles up, upright on a BW x BH keyed canvas."""
    cx = BW // 2
    for ly in range(BH):
        h = int(half_w(ly))
        if h <= 0:
            continue
        rect(cx - h, ly, cx + h, ly, ST)
        rect(cx - h, ly, cx - h + 2, ly, ST_L)          # candle light from below-west
        rect(cx + h - 4, ly, cx + h, ly, ST_D)
        px(cx + h, ly, ST_XD)
    for _ in range(420):                                 # tooling and weather
        x, y = int(rnd() * BW), int(rnd() * BH)
        if abs(x - cx) < half_w(y) - 1:
            px(x, y, pick([ST_D, ST_L, ST_D, MOSS]), 0.6)
    # hood: the dark opening, two pin-point eyes, the hood edge
    for y in range(18, 50):
        t = (y - 34) / 15.0
        hw = int(9 * math.sqrt(max(0.0, 1 - t * t)))
        rect(cx - hw, y, cx + hw, y, ST_XD)
    px(cx - 3, 33, F_MID)
    px(cx + 3, 33, F_MID)
    px(cx - 3, 32, F_COOL)
    px(cx + 3, 32, F_COOL)
    for y in range(16, 52):
        t = (y - 34) / 17.0
        hw = int(11 * math.sqrt(max(0.0, 1 - t * t)))
        px(cx - hw, y, ST_L)
        px(cx + hw, y, ST_D)
    # sleeves coming in to the chest, hands on the carved ring
    for side in (-1, 1):
        for i in range(30):
            x = cx + side * (26 - i * 0.55)
            y = 76 + i
            rect(min(x, x + side * 6), y, max(x, x + side * 6), y, ST_D if side > 0 else ST)
        line(cx + side * 26, 76, cx + side * 10, 106, ST_XD)
    disc(cx, 100, 11, ST)
    disc(cx, 100, 11, ST_D, 0.4)
    disc(cx, 100, 5, ST_XD)
    ring(cx, 100, 11, ST_L)
    for side in (-1, 1):
        rect(cx + side * 9 - 3, 104, cx + side * 9 + 3, 109, ST_L if side < 0 else ST)
    # robe folds
    for fx, k in ((-16, 0.06), (-6, -0.02), (5, 0.03), (15, 0.08)):
        for y in range(118, BH):
            px(cx + fx + (y - 118) * k, y, ST_D)
            if y % 3 == 0:
                px(cx + fx + 1 + (y - 118) * k, y, ST_L, 0.5)
    rect(cx - 30, BH - 4, cx + 30, BH - 1, ST_D)         # hem
    # the cracks it will break along: neck and waist
    for y0, amp in ((62, 2), (134, 3)):
        h = int(half_w(y0)) + 1
        for x in range(cx - h, cx + h + 1):
            y = y0 + int(amp * math.sin(x * 0.9) + amp * 0.6 * math.sin(x * 2.3))
            px(x, y, INK)
            px(x, y + 1, ST_XD)
    # ropes wrapped round it at neck, chest and waist
    for y0 in (58, 70, 128):
        h = int(half_w(y0)) + 1
        for x in range(cx - h, cx + h + 1):
            px(x, y0 + (x - cx) * 0.12, ROPE)
            px(x, y0 + 1 + (x - cx) * 0.12, ROPE_D)


def idol_feet(fx, fy):
    """The feet and the stump of the hem, left on the floor: they stay put."""
    rect(fx - 30, fy - FEET_H, fx + 30, fy - 1, ST)
    rect(fx - 30, fy - FEET_H, fx - 28, fy - 1, ST_L)
    rect(fx + 26, fy - FEET_H, fx + 30, fy - 1, ST_D)
    rect(fx - 36, fy - 6, fx + 36, fy - 1, ST_D)         # the toes, out from under
    rect(fx - 36, fy - 6, fx + 36, fy - 6, ST_L)
    for tx in range(fx - 34, fx + 34, 5):
        px(tx, fy - 4, ST_XD)
    # the crack through the ankles: a black wedge opening on the west side
    for x in range(fx - 30, fx + 31):
        y = fy - FEET_H + int(1.5 * math.sin(x * 1.3))
        px(x, y, INK)
        px(x, y - 1, INK)


def rope(x0, y0, x1, y1):
    line(x0, y0, x1, y1, ROPE)
    line(x0, y0 + 1, x1, y1 + 1, ROPE_D)


def ring_bolt(x, y):
    disc(x, y, 3.2, MET_D)
    ring(x, y, 3.2, MET_L)
    px(x, y, INK)


def candles(x0, x1, floor, step=5):
    for x in range(int(x0), int(x1), step):
        h = 3 + int(rnd() * 5)
        rect(x, floor - h, x + 1, floor - 1, CANDLE)
        px(x, floor - h - 1, F_HOT)
        px(x, floor - h - 2, F_MID, 0.7)
        rect(x - 1, floor - 1, x + 2, floor - 1, (180, 170, 140))    # drips
    glow((x0 + x1) / 2, floor - 6, max(24, (x1 - x0) * 0.8), F_MID, 0.10)


def skulls(x, floor, n=4):
    for i in range(n):
        sx = x + i * 5 - (i // 3) * 12
        sy = floor - 4 - (i // 3) * 4
        rect(sx, sy, sx + 4, sy + 3, (176, 168, 140))
        px(sx + 1, sy + 1, INK)
        px(sx + 3, sy + 1, INK)


def censer(x, roof, drop):
    chain(x, roof, roof + drop)
    y = roof + drop
    rect(x - 3, y, x + 4, y + 5, MET_D)
    rect(x - 3, y, x + 4, y, MET_L)
    px(x, y + 2, F_MID)
    for i in range(6):
        px(x + int(rnd() * 3) - 1, y - 2 - i * 2, (120, 120, 116), 0.5)
    glow(x, y + 3, 26, F_MID, 0.10)


def idol_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fy = Y(FLOOR)

    # a spur of roof rock over the east half, with the cult's cages off it
    rock_blob(X(262), Y(88), 38, 34, rough=0.18)
    rock_blob(X(284), Y(118), 16, 14, rough=0.2)
    teeth(m, X(150), X(390), Y(140), 18)
    teeth(m, X(40), X(130), Y(170), 6)
    for (x0, y0, ln) in ((250, 132, 9), (262, 134, 13), (276, 130, 7), (292, 140, 6)):
        for i in range(ln):
            hw = max(0, (ln - i) // 3)
            rect(X(x0) - hw, Y(y0) + i, X(x0) + hw, Y(y0) + i, ROCK_M)
    cage(X(244), Y(150), Y(172), Y(128))
    cage(X(272), Y(160), Y(186), Y(134))
    # the floor is not a line: rubble mounds and a low rise under the east
    for (cx_, rx, ry) in ((30, 22, 6), (150, 16, 4), (346, 40, 7), (230, 14, 3)):
        rock_blob(X(cx_), Y(FLOOR), rx, ry, rough=0.2, clip=(X(cx_ - rx - 4), Y(FLOOR - 20), X(cx_ + rx + 4), Y(FLOOR)))

    # the idol: feet on the floor, the rest leaning east off the crack
    pvx, pvy = X(BASE_X), fy - FEET_H
    ca, sa = math.cos(LEAN), math.sin(LEAN)
    cxw = pvx + sa * (BH / 2.0)
    cyw = pvy - ca * (BH / 2.0)
    to_world = draw_rotated(BW, BH, draw_body, cxw, cyw, LEAN)
    idol_feet(pvx, fy)
    for i in range(10):                                   # chips off the crack
        disc(pvx - 34 + rnd() * 70, fy - 2, 1 + rnd() * 1.5, pick([ST, ST_D, ST_L]))

    # the three ropes, back west to the anchors
    head = to_world(BW // 2 - 14, 58)
    chest = to_world(BW // 2 - 27, 70)
    waist = to_world(BW // 2 - 28, 128)
    roof_a = (X(104), ceil_at(m, X(104), Y(180)) + 4)
    wall_x = X(4)
    while (wall_x, Y(214)) not in m:
        wall_x += 1
    wall_a = (wall_x + 5, Y(214))
    stake = (X(44), fy)
    rock_blob(roof_a[0], roof_a[1] - 4, 10, 7, rough=0.2)
    rock_blob(wall_a[0] - 6, wall_a[1], 8, 10, rough=0.2)
    rope(head[0], head[1], roof_a[0], roof_a[1])
    rope(chest[0], chest[1], wall_a[0], wall_a[1])
    rope(waist[0], waist[1], stake[0] + 2, stake[1] - 16)
    ring_bolt(*roof_a)
    ring_bolt(*wall_a)
    beam(stake[0], stake[1] - 18, stake[1] - 1, 4, WOOD, WOOD_L)          # the deadman
    rect(stake[0] - 2, stake[1] - 18, stake[0] + 6, stake[1] - 17, WOOD_D)
    for i in range(3):                                    # turns of rope on the stake
        rect(stake[0], stake[1] - 15 + i * 2, stake[0] + 4, stake[1] - 15 + i * 2, ROPE)

    # the ladder they climbed to tie it, still leaning on its east flank
    top = to_world(BW // 2 + 30, 84)
    for t in (0, 7):
        line(X(212) + t, fy - 1, top[0] + t + 2, top[1], WOOD)
    for k in range(1, 9):
        f = k / 9.0
        x0_ = X(212) + (top[0] + 2 - X(212)) * f
        y0_ = fy - 1 + (top[1] - fy + 1) * f
        rect(x0_, y0_, x0_ + 7, y0_, WOOD_L)

    # the congregation at its feet, east, right where it will land
    candles(pvx + 40, pvx + 70, fy)
    candles(X(250), X(276), fy, 4)
    stand("WizCrimson", X(178), fy, flip=True)
    stand("WizMaskwraith", X(206), fy, flip=True)
    stand("WizBonecrown", X(236), fy, flip=True)
    stand("BloodMage", X(290), fy, flip=True)
    skulls(X(160), fy, 5)
    # the hand it lost already, on the floor: what it does when it falls
    hx, hy = X(318), fy
    rock_blob(hx, hy - 6, 18, 8, rough=0.15, base=ST, lit=ST_L, clip=(hx - 30, hy - 30, hx + 30, hy - 1))
    for k in range(4):
        rect(hx - 12 + k * 6, hy - 14, hx - 9 + k * 6, hy - 8, ST)
        px(hx - 12 + k * 6, hy - 14, ST_L)
    candles(hx - 14, hx + 10, hy - 14, 6)
    scrap_pile(X(350), fy, 22, 5, colors=(ST_D, ST, ROCK_M, ST_L))
    stand("Gaper", X(384), fy, flip=True)
    for bx in (258, 290):                                # prayer mats
        rect(X(bx) - 7, fy - 1, X(bx) + 7, fy - 1, RED)

    # the east perch and what keeps watch from it
    stand("Sentinel", X(392), Y(SHELF_Y), flip=True)
    candles(X(366), X(378), Y(SHELF_Y), 5)
    stand("Ghast", X(290), Y(196), flip=True)

    for cx_, drop in ((200, 34), (226, 18), (374, 22)):
        censer(X(cx_), ceil_at(m, X(cx_), Y(150)) + 1, drop)
    lamp(X(70), ceil_at(m, X(70), Y(260)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.12)
    glow(pvx + 30, fy - 30, 110, F_MID, 0.07)


ROOM = {
    "name": "THE IDOL", "w": 420, "h": 400,
    "shapes": [([("blob", 220, 214, 188, 150),               # the dome
                 ("blob", 220, 312, 204, 46)], 0.08),          # the floor, wall to wall
               ([("blob", 330, 92, 40, 28),                    # a chimney off the east roof
                 ("blob", 76, 116, 40, 26)], 0.14)],           # and one off the west
    "sockets": {"T1": ("T", 80, 98), "T2": ("T", 330, 70),
                "L1": ("L", FLOOR, 30), "R1": ("R", FLOOR, 22),
                "R2": ("R", SHELF_Y, 14)},
    "edit": idol_edit,
    "furnish": idol_furnish,
}


SHEET = {
    "seed": 72601,
    "callouts": [
        ("1 CRACKED AT THE ANKLES", (-124, 420), (122, 323)),
        ("2 THREE ROPES HOLD IT UP", (-124, 40), (66, 206)),
        ("3 IT FALLS ON THEM", (300, 420), (236, 330)),
    ],
    "beats": [
        ("CUT THE ROPES: THE IDOL FALLS EAST AND BREAKS IN THREE", (170, 180, 195)),
        ("THE CULT PRAYS RIGHT UNDER IT, THE SENTINEL WATCHES FROM THE PERCH", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
