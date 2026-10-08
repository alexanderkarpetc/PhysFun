"""Small room S34 - THE COLONNADE.

What is left of a hall somebody built in the rock: a paved floor, a row of five tall stone
columns, and the barrel vault they carry, arch after arch, up to the cave roof. The west
end has already gone - its arch is on the floor, and the first column, cracked at the
foot, leans with its capital on the next. The rest stand, some cracked. The row runs east
into a raw apse. Shoot one column through and it falls into the next, and that one into
the next: the row goes down like dominoes, and the vault with it, on whoever stands
between them.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S34"

FLOOR = 250
COL_W = 12
COLS = (76, 132, 188, 244, 300)      # left edge of each shaft
SPRING = 140                         # top of the capitals, where the arches start
RISE = 26
PERCH = 166


def colo_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > FLOOR:
            continue
        if lx < 60 and PERCH < ly < PERCH + 50:
            continue
        out.add((x, y))
    return out


def stone_px(x, y, base=STONE):
    """Coursed block, pixel by pixel: 6px courses, joints staggered every 14."""
    c = base
    if y % 6 == 0:
        c = STONE_D
    elif (x + (7 if (y // 6) % 2 else 0)) % 14 == 0:
        c = STONE_D
    elif chance(0.08):
        c = STONE_L if chance(0.3) else (110, 103, 88)
    px(x, y, c)


def column_shape(x, base, top, cracked=0):
    """A column: plinth, a shaft of drums with fluting, a capital wider than the shaft."""
    rect(x - 4, base - 5, x + COL_W + 4, base - 1, STONE)          # plinth
    rect(x - 4, base - 5, x + COL_W + 4, base - 5, STONE_L)
    rect(x - 4, base - 1, x + COL_W + 4, base - 1, STONE_D)
    rect(x, top + 7, x + COL_W, base - 6, STONE)
    for fx in (x + 3, x + 6, x + 9):                               # flutes
        rect(fx, top + 9, fx, base - 8, (110, 103, 88))
    rect(x, top + 7, x, base - 6, STONE_L)
    rect(x + COL_W, top + 7, x + COL_W, base - 6, STONE_D)
    for y in range(top + 20, base - 8, 15):                        # drum joints
        rect(x, y, x + COL_W, y, STONE_D)
    rect(x - 4, top, x + COL_W + 4, top + 3, STONE)                 # abacus
    rect(x - 4, top, x + COL_W + 4, top, STONE_L)
    rect(x - 2, top + 4, x + COL_W + 2, top + 6, STONE)              # echinus
    rect(x - 2, top + 6, x + COL_W + 2, top + 6, STONE_D)
    if cracked:
        cy = top + 30 + (cracked * 23) % 50
        cx = x + 1
        for i in range(COL_W + 3):
            px(cx + i, cy + (i % 3) - (i // 4), INK)
        px(cx + 4, cy + 3, INK)
        px(cx + 5, cy + 4, INK)


def colo_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fy = Y(FLOOR) + 1

    teeth(m, X(20), X(70), Y(150), 5)
    teeth(m, X(330), X(420), Y(150), 8)
    rock_blob(X(14) + 10, Y(PERCH) + 8, 24, 8, rough=0.2)

    # the paving
    for x in range(X(30), X(350)):
        for y in range(fy, fy + 5):
            stone_px(x, y, (112, 105, 90))
        px(x, fy, STONE_L)

    # the vault: from each bay's intrados up to the cave roof, and solid over the capitals
    def intrados(lx):
        for i in range(1, len(COLS) - 1 + 1):
            if i >= len(COLS):
                break
            a, b = COLS[i - 1] + COL_W + 4, COLS[i] - 4
            if a <= lx <= b and i > 1:
                c, r = (a + b) / 2.0, (b - a) / 2.0
                t = (lx - c) / r
                return SPRING - RISE * math.sqrt(max(0.0, 1 - t * t))
        return SPRING
    v0, v1 = COLS[1] - 4, COLS[-1] + COL_W + 6
    for lx in range(v0, v1):
        yb = intrados(lx)
        top = ceil_at(m, X(lx), Y(SPRING - RISE - 4))
        for y in range(top, int(Y(yb)) + 1):
            stone_px(X(lx), y)
    for i in range(2, len(COLS)):                                  # arch rings and voussoirs
        a, b = COLS[i - 1] + COL_W + 4, COLS[i] - 4
        c, r = (a + b) / 2.0, (b - a) / 2.0
        for k in range(0, 181, 2):
            ang = math.radians(k)
            for d in range(0, 6):
                xx = c - math.cos(ang) * (r + d * 0.4)
                yy = SPRING - math.sin(ang) * (RISE + d)
                px(X(xx), Y(yy), STONE_L if d == 0 else STONE)
            if k % 18 == 0:
                for d in range(0, 7):
                    px(X(c - math.cos(ang) * (r + d * 0.4)), Y(SPRING - math.sin(ang) * (RISE + d)), STONE_D)
    # the broken east end of the vault: courses stepping back into the raw rock
    for k in range(6):
        lx = v1 + k * 3
        top = ceil_at(m, X(lx), Y(SPRING - 30))
        for y in range(top, Y(SPRING - 6 - k * 6)):
            stone_px(X(lx), y)
            stone_px(X(lx) + 1, y)
            stone_px(X(lx) + 2, y)
    # what is left of the vault either side of the standing bays: spandrel still stuck
    # to the roof, broken off ragged underneath (T1 drops in through the gap)
    for (a, b) in ((44, 90), (118, COLS[1] - 4), (v1 + 10, 364)):
        for lx in range(a, b):
            top = ceil_at(m, X(lx), Y(SPRING - 10))
            bot = Y(SPRING - 16) - int(6 * abs(math.sin(lx * 0.7)) + 5 * abs(math.sin(lx * 0.23)))
            if lx < 60 or lx > 344:
                bot -= (60 - lx if lx < 60 else (lx - 344) * 2)
            for y in range(top, bot):
                stone_px(X(lx), y)
            if bot > top:
                px(X(lx), bot, STONE_D)
                if chance(0.15):
                    px(X(lx), bot + 1 + int(rnd() * 4), STONE_D, 0.6)    # dust off it

    # the stub of the fallen west arch, hanging off the second column's springer
    for k in range(0, 50, 2):
        ang = math.radians(180 - k)
        a, b = COLS[0] + COL_W + 4, COLS[1] - 4
        c, r = (a + b) / 2.0, (b - a) / 2.0
        for d in range(0, 6):
            px(X(c - math.cos(ang) * (r + d * 0.4)), Y(SPRING - math.sin(ang) * (RISE + d)), STONE if d else STONE_L)
    for y in range(SPRING - 14, SPRING):
        stone_px(X(COLS[1] - 4), Y(y))

    # columns: the upright four, cracked here and there
    for i, cx in enumerate(COLS[1:], 1):
        column_shape(X(cx), fy, Y(SPRING), cracked=(i if i in (2, 4) else 0))
    # chips off the fourth: a missing bite out of the shaft
    rect(X(COLS[3] + COL_W - 3), Y(200), X(COLS[3] + COL_W), Y(206), CAVE)
    px(X(COLS[3] + COL_W - 4), Y(203), INK)

    # the first column, cracked at the foot, pivoted on its east corner onto the next
    h = FLOOR - SPRING
    cw, ch = COL_W + 12, h + 8
    pivot = (COL_W + 6 + 4, ch - 1)
    ang = math.asin((COLS[1] - (COLS[0] + COL_W + 4)) / float(h))
    sa, ca = math.sin(ang), math.cos(ang)
    dx, dy = pivot[0] - cw / 2.0, pivot[1] - ch / 2.0
    pxw, pyw = X(COLS[0] + COL_W + 4), fy - 1
    ccx = pxw - (ca * dx - sa * dy)
    ccy = pyw - (sa * dx + ca * dy)
    draw_rotated(cw, ch, lambda: column_shape(6, ch, ch - h, cracked=0), ccx, ccy, ang)
    for i in range(8):                                             # the crushed west foot
        px(X(COLS[0] - 2 + i), fy - 1 - (i % 3 == 0), pick([STONE_D, STONE, INK]))
    for i in range(6):
        px(X(COLS[0] + 4 + i), fy - 6 - i, INK)

    # what came down already: voussoirs and a drum on the floor, dust
    for (lx, w_, h_) in ((96, 9, 5), (108, 7, 6), (118, 10, 4), (44, 8, 5), (60, 6, 4)):
        rect(X(lx), fy - h_, X(lx + w_), fy - 1, STONE)
        rect(X(lx), fy - h_, X(lx + w_), fy - h_, STONE_L)
        rect(X(lx + w_), fy - h_, X(lx + w_), fy - 1, STONE_D)
    rubble(X(36), fy - 4, X(128), fy - 1, n=60, colors=(STONE, STONE_D, ROCK_M, STONE_L))
    rect(X(214), fy - 11, X(236), fy - 1, STONE)                    # a fallen drum, on its side
    rect(X(214), fy - 11, X(236), fy - 11, STONE_L)
    for fx in (218, 223, 228, 233):
        rect(X(fx), fy - 10, X(fx), fy - 2, (110, 103, 88))
    rect(X(214), fy - 11, X(214), fy - 1, STONE_D)

    # cressets on chains from the vault crowns
    for i in (2, 4):
        a, b = COLS[i - 1] + COL_W + 4, COLS[i] - 4
        c = (a + b) // 2
        chain(X(c), Y(SPRING - RISE) + 1, Y(SPRING - 4))
        rect(X(c - 3), Y(SPRING - 4), X(c + 3), Y(SPRING - 2), MET_D)
        glow(X(c), Y(SPRING - 6), 46, F_MID, 0.16)
        px(X(c), Y(SPRING - 5), F_HOT)
        px(X(c - 1), Y(SPRING - 6), F_MID)
        px(X(c + 1), Y(SPRING - 6), F_MID)

    # the crew between the columns, the apse at the end of the row
    stand("Gaper", X(160), fy, flip=True)
    stand("WizMaskwraith", X(208), fy, flip=True)
    stand("RiotBrute", X(272), fy, flip=True)
    stand("Gaper", X(330), fy, flip=True)
    af = floor_at(m, X(384), Y(220))
    stand("BloodMage", X(380), af, flip=True)
    for (bx, n) in ((360, 7), (400, 5)):                             # bones heaped in the apse
        scrap_pile(X(bx) - 8, af, 18, n, colors=((200, 196, 178), (160, 156, 140), STONE_D))
    for k, cx in enumerate((350, 366, 396, 410)):                    # candles
        cfl = floor_at(m, X(cx), Y(230))
        rect(X(cx), cfl - 4, X(cx), cfl - 1, (210, 200, 170))
        px(X(cx), cfl - 5, F_HOT)
        glow(X(cx), cfl - 5, 12, F_MID, 0.12)
    sx = X(440)
    while (sx, Y(186)) not in m:
        sx -= 1
    rock_blob(sx - 6, Y(186) + 6, 22, 7, rough=0.2)
    stand("WizBonecrown", sx - 12, Y(186), flip=True)
    stand("Sentinel", X(30), Y(PERCH) + 1)
    stand("Grenadier", X(28), fy, flip=False)


ROOM = {
    "name": "THE COLONNADE", "w": 440, "h": 320,
    "shapes": [([("blob", 192, 172, 178, 94)], 0.07),             # the hall
               ([("blob", 380, 176, 40, 76),                       # the apse
                 ("blob", 36, PERCH - 10, 30, 18),                 # a perch in the west wall
                 ("blob", 40, 236, 36, 18)], 0.12)],               # the west way in
    "sockets": {"T1": ("T", 104, 94), "T2": ("T", 384, 104),
                "L1": ("L", FLOOR, 26), "L2": ("L", PERCH, 10), "R1": ("R", FLOOR, 24)},
    "edit": colo_edit,
    "furnish": colo_furnish,
}


SHEET = {
    "seed": 73401,
    "callouts": [
        ("1 LEANS ON THE NEXT", (-120, 60), (110, 170)),
        ("2 SHOOT ONE, THE ROW GOES DOWN", (180, 334), (250, 200)),
        ("3 CRACKED DRUMS", (426, 112), (306, 212)),
    ],
    "beats": [
        ("EACH COLUMN FALLS INTO THE NEXT, AND THE VAULT COMES WITH THEM", (170, 180, 195)),
        ("THE CREW STAND BETWEEN THE COLUMNS, THE BLOOD MAGE IN THE APSE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
