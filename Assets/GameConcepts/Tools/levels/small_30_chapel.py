"""Small room S30 - THE CHAPEL.

A cult chapel cut into the rock: a nave with a pointed vault, dressed walls and carved
half-columns, opening east into a rough natural apse where the preacher stands at a
lectern on a stone dais. Cloth banners hang off the vault on cords, a ring chandelier of
candles hangs from the apex, candle racks stand along the walls right under the banners,
and the congregation kneels among timber pews. Fire is the toy: a candle lights a
banner, the banner's cord burns through, and it drops burning onto the pews.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S30"

NF = 284                        # nave floor
DAIS = 270
NX0, NX1 = 36, 290              # the nave's walls
SPRING = 190                    # where the vault springs off the walls
VR = 140                        # radius of each half of the pointed vault
APEX_X = (NX0 + NX1) // 2

CLOTH = [((112, 50, 50), (146, 70, 62), (74, 32, 34)),       # oxblood
         ((66, 64, 98), (92, 90, 128), (42, 40, 64))]        # dull violet
SIGIL = (186, 170, 120)
CANDLE = (206, 196, 160)
ROPE = (150, 128, 90)


def vault(lx):
    """Underside of the vault at lx: two arcs meeting in a point."""
    if lx <= APEX_X:
        c = NX0 + VR
    else:
        c = NX1 - VR
    return SPRING - math.sqrt(max(0.0, VR * VR - (lx - c) ** 2))


def chapel_edit(air, ox, oy):
    for lx in range(NX0, NX1 + 1):
        for ly in range(int(vault(lx)) + 1, NF):
            air.add((ox + lx, oy + ly))
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= NF:
            continue
        if lx >= NX1 + 8 and ly >= DAIS:
            continue                                         # the dais
        if lx >= NX1 and ly >= DAIS + 7:
            continue                                         # its step
        out.add((x, y))
    return out


def candle_rack(x, floor, w=16, rows=2):
    """Iron stand of candles, stepped."""
    rect(x, floor - 1, x + w, floor - 1, MET_D)
    for lx in (x + 1, x + w - 1):
        rect(lx, floor - 12 - rows * 4, lx, floor - 1, MET_D)
    for r in range(rows):
        y = floor - 10 - r * 5
        rect(x, y, x + w, y, MET)
        for cx in range(x + 1 + r, x + w, 3):
            h = 2 + int(rnd() * 3)
            rect(cx, y - h, cx, y - 1, CANDLE)
            px(cx, y - h - 1, F_HOT)
            px(cx, y - h - 2, F_MID, 0.6)
    glow(x + w / 2.0, floor - 18, 34, F_MID, 0.14)


def floor_candles(x0, x1, floor):
    for x in range(int(x0), int(x1), 3):
        h = 2 + int(rnd() * 6)
        rect(x, floor - h, x + 1, floor - 1, CANDLE)
        px(x, floor - h - 1, F_HOT)
    glow((x0 + x1) / 2.0, floor - 6, (x1 - x0) * 0.8 + 10, F_MID, 0.10)


def banner(x, roof, top, ln, pal, burning=False):
    """A cloth banner on a pole, hung off the vault on two cords: sigil, tattered foot."""
    c, cl, cd = pal
    w = 14
    for cx in (x - w // 2 + 1, x + w // 2 - 1):
        line(cx, top, x, roof, ROPE)
    rect(x - w // 2 - 2, top, x + w // 2 + 2, top + 1, WOOD_D)
    for yy in range(top + 2, top + ln):
        sway = int(1.5 * math.sin((yy - top) * 0.09))
        rect(x - w // 2 + sway, yy, x + w // 2 + sway, yy, c)
        px(x - w // 2 + sway, yy, cl)
        px(x + w // 2 + sway, yy, cd)
    for k in range(0, w + 1, 3):                             # tattered foot
        d = 2 + (k * 7) % 5
        rect(x - w // 2 + k, top + ln, x - w // 2 + k + 1, top + ln + d, c)
    # the sigil: a ring with an eye in it, the cult's mark
    sy = top + 18
    ring(x, sy, 4, SIGIL)
    px(x, sy, SIGIL)
    rect(x - 4, top + 4, x + 4, top + 4, SIGIL)
    rect(x - 4, top + ln - 8, x + 4, top + ln - 8, SIGIL)
    if burning:
        for i in range(16):                                  # the foot already going up
            fx = x - w // 2 + rnd() * w
            fy = top + ln + 4 - rnd() * 22
            disc(fx, fy, 1 + rnd() * 1.6, pick([F_HOT, F_MID, F_MID, F_COOL]), 0.9)
        for yy in range(top + ln - 26, top + ln - 16):
            px(x - w // 2 + rnd() * w, yy, CHAR, 0.7)
        embers(x - 14, top + ln - 50, x + 14, top + ln - 10, 26)
        glow(x, top + ln, 44, F_MID, 0.22)


def pew(x, floor, w=24):
    """A timber pew side-on, facing east: seat, back on the west end, two legs."""
    seat = floor - 8
    rect(x, seat, x + w, seat + 1, WOOD)
    rect(x, seat, x + w, seat, WOOD_L)
    rect(x, seat - 10, x + 2, floor - 1, WOOD_D)            # back
    rect(x, seat - 10, x + 2, seat - 10, WOOD_L)
    rect(x + w - 2, seat + 2, x + w - 1, floor - 1, WOOD_D)  # leg
    rect(x + 3, seat + 6, x + w - 3, seat + 6, WOOD_D)       # stretcher
    rect(x - 2, seat - 2, x + 6, seat - 2, WOOD)             # book rail of the pew behind


def lectern(x, floor):
    rect(x - 1, floor - 22, x + 2, floor - 1, WOOD)
    rect(x - 5, floor - 2, x + 6, floor - 1, WOOD_D)
    for i in range(6):                                       # slanted desk, book on it
        rect(x - 6 + i, floor - 26 + i, x + 3 + i, floor - 26 + i, WOOD_L if i == 0 else WOOD)
    rect(x - 5, floor - 30, x + 2, floor - 27, (150, 140, 112))
    rect(x - 5, floor - 30, x + 2, floor - 30, (200, 190, 160))


def chandelier(cx, roof, y):
    chain(cx, roof, y - 4)
    for side in (-1, 1):
        line(cx, y - 6, cx + side * 20, y, MET_D)
    for xx in range(-22, 23):                                 # the ring, side-on: a flat ellipse
        yy = y + 2.5 * math.sqrt(max(0.0, 1 - (xx / 22.0) ** 2))
        px(cx + xx, yy, MET)
        px(cx + xx, y - 2.5 * math.sqrt(max(0.0, 1 - (xx / 22.0) ** 2)), MET_D)
    for xx in range(-20, 21, 5):
        h = 4 + int(rnd() * 3)
        top = y - 1 - h
        rect(cx + xx, top, cx + xx, y - 1, CANDLE)
        px(cx + xx, top - 1, F_HOT)
        px(cx + xx, top - 2, F_MID, 0.6)
        for d in range(1 + int(rnd() * 4)):                  # wax dripping off
            px(cx + xx, y + 3 + d, CANDLE, 0.6)
    glow(cx, y - 4, 70, F_MID, 0.16)


def chapel_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    nf = Y(NF)

    # the dressing: a carved rib along the vault, half-columns on both walls
    for lx in range(NX0, NX1 + 1):
        v = Y(int(vault(lx)))
        px(X(lx), v - 2, ROCK_L, 0.7)
        px(X(lx), v - 3, ROCK_D)
        px(X(lx), v - 5, ROCK_L, 0.4)
    for wx in (NX0, NX1 - 6):
        column(X(wx), Y(SPRING - 10), nf - 1, w=6, c=ROCK_M, lit=ROCK_L, dark=ROCK_D)
    for k in range(3):                                       # coursing on the wall faces
        for wx, d in ((NX0 - 1, -1), (NX1 + 1, 1)):
            for yy in range(Y(SPRING) + 8 + k * 30, nf - 4, 90):
                rect(X(wx) + d * 6, yy, X(wx) + d, yy, ROCK_D, 0.6)

    # the apse: rough rock, the dais, the lectern and the altar
    teeth(m, X(NX1 + 20), X(366), Y(200), 8)
    rect(X(NX1), Y(DAIS + 7), X(NX1 + 7), nf - 1, ROCK_M)    # the step, dressed
    rect(X(NX1), Y(DAIS + 7), X(NX1 + 7), Y(DAIS + 7), ROCK_L)
    rect(X(NX1 + 8), Y(DAIS), X(360), Y(DAIS), ROCK_L)
    lectern(X(NX1 + 22), Y(DAIS))
    stand("WizBonecrown", X(NX1 + 34), Y(DAIS), flip=True)
    rect(X(334), Y(DAIS) - 16, X(358), Y(DAIS) - 1, STONE_D)  # altar block
    rect(X(334), Y(DAIS) - 16, X(358), Y(DAIS) - 16, STONE)
    rect(X(336), Y(DAIS) - 14, X(356), Y(DAIS) - 12, RED)
    floor_candles(X(336), X(356), Y(DAIS) - 16)
    rect(X(344), Y(DAIS) - 22, X(348), Y(DAIS) - 19, (176, 168, 140))   # a skull on it
    px(X(345), Y(DAIS) - 21, INK)
    px(X(347), Y(DAIS) - 21, INK)
    stand("BloodMage", X(368), Y(DAIS), flip=True)
    banner(X(346), ceil_at(m, X(346), Y(220)) + 1, Y(196), 30, CLOTH[0])
    floor_candles(X(NX1 - 22), X(NX1 - 2), nf)

    # banners off the vault, candle racks under them
    for i, (bx, foot, burning) in enumerate(((78, 244, False), (122, 236, True), (206, 240, False),
                                             (250, 246, False))):
        roof = Y(int(vault(bx)))
        banner(X(bx), roof, roof + 14, Y(foot) - roof - 14, CLOTH[i % 2], burning)
    for rx in (70, 116, 200, 244):
        candle_rack(X(rx), nf)

    # the chandelier from the apex
    chandelier(X(APEX_X), Y(int(vault(APEX_X))) + 1, Y(122))

    # the pews and the congregation, all facing east
    for k, px_ in enumerate((52, 92, 132, 172, 212)):
        pew(X(px_), nf)
    stand("WizCrimson", X(58), nf)
    stand("WizHollowhood", X(100), nf)
    stand("WizMaskwraith", X(150), nf)
    stand("WizGoldhood", X(180), nf)
    stand("WizRamskull", X(228), nf)
    for k in range(5):                                       # a scorch where one came down before
        px(X(140 + k * 3), nf - 1, CHAR)
    rect(X(98), nf - 3, X(112), nf - 1, CHAR)                # an old banner, burnt out on the floor
    for k in range(8):
        px(X(98 + k * 2), nf - 4, (90, 40, 40))


ROOM = {
    "name": "THE CHAPEL", "w": 380, "h": 340,
    "shapes": [([("blob", 322, 232, 50, 58)], 0.12),         # the apse
               ([("tube", [(4, 270), (40, 270)], 14)], 0.05)],  # the narthex, west door
    "sockets": {"T1": ("T", 90, 84), "T2": ("T", 250, 96),
                "L1": ("L", NF, 12), "R1": ("R", DAIS, 18),
                "B1": ("B", 20, 60)},
    "edit": chapel_edit,
    "furnish": chapel_furnish,
}


SHEET = {
    "seed": 73001,
    "callouts": [
        ("1 CANDLES UNDER THE BANNERS", (-124, 368), (124, 264)),
        ("2 CLOTH BURNS, CORDS LET GO", (-124, 40), (122, 180)),
        ("3 TIMBER PEWS", (240, 360), (180, 278)),
    ],
    "beats": [
        ("ONE CANDLE LIGHTS A BANNER, ITS CORDS BURN THROUGH, IT DROPS ON THE PEWS", (170, 180, 195)),
        ("THE CONGREGATION KNEELS IN THE PEWS, THE PREACHER STANDS ON THE DAIS", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
