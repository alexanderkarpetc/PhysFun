"""Small room S24 - THE SCALES.

A round room built round one giant balance: an iron beam on a pin, on an A-frame, on
a spire of rock left standing in the middle of the floor, a pan hung off each end on
chains. The west pan is loaded with ore and sits low over its pit; the east pan, light,
rides high by the east ledge - and the crew use it as a lift, so that is where they are
standing. Change the weight and the beam swings: shoot the ore off, or drop more on
the east pan, and it goes down into the east pit while the ore comes up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S24"

PIVOT = (210, 108)
ARM = 116                         # pivot to each end
TILT = 0.31                       # west end down
CHAIN_L = 118
PAN_W = 50
FLOOR = 312
LEDGE_W, LEDGE_E = 184, 192


def ends():
    c, s = math.cos(TILT), math.sin(TILT)
    return (PIVOT[0] - ARM * c, PIVOT[1] + ARM * s), (PIVOT[0] + ARM * c, PIVOT[1] - ARM * s)


def scales_edit(air, ox, oy):
    (wx, wy), (ex, ey) = ends()
    pw, pe = int(wy + CHAIN_L), int(ey + CHAIN_L)
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        in_w_pit = abs(lx - wx) < 36 and ly < 352 + 6 * math.sin(lx * 0.2)
        in_e_pit = abs(lx - ex) < 36 and ly < 372 + 6 * math.sin(lx * 0.17)
        if ly >= FLOOR + 2 * math.sin(lx * 0.09) and not (in_w_pit or in_e_pit):
            continue
        # the spire: rock left standing from the floor up to the A-frame's foot
        if ly > PIVOT[1] + 26 and abs(lx - PIVOT[0]) < 8 + (ly - PIVOT[1] - 26) * 0.05 + (ly - PIVOT[1] - 26) ** 2 * 0.0004 + 2 * math.sin(ly * 0.21):
            continue
        if lx < wx - PAN_W / 2 - 6 and LEDGE_W <= ly < LEDGE_W + 20 + (wx - PAN_W / 2 - 6 - lx) * 0.3:
            continue
        if lx > ex + PAN_W / 2 + 6 and LEDGE_E <= ly < LEDGE_E + 20 + (lx - ex - PAN_W / 2 - 6) * 0.3:
            continue
        out.add((x, y))
    return out


def chain_line(x0, y0, x1, y1):
    n = int(math.hypot(x1 - x0, y1 - y0) / 1.5)
    for i in range(n + 1):
        t = i / max(n, 1)
        px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, MET_L if (i // 2) % 2 else MET_D)


def beam_local():
    """The balance beam drawn level on a 260x20 canvas: a riveted iron girder, deeper at
    the middle, the pin boss at the centre and an eye at each end."""
    w, c = 260, 10
    L = ARM
    for x in range(130 - L, 130 + L + 1):
        d = abs(x - 130) / L
        half = int(7 - 4 * d)
        rect(x, c - half, x, c + half, MET)
        px(x, c - half, MET_XL)
        px(x, c + half, MET_D)
    for x in range(130 - L + 6, 130 + L - 4, 12):              # web lattice
        d = abs(x - 130) / L
        half = int(7 - 4 * d) - 1
        line(x, c - half, x + 6, c + half, MET_D)
        line(x + 6, c - half, x + 12, c + half, MET_D)
    for x in range(130 - L + 3, 130 + L - 2, 6):
        px(x, c - int(7 - 4 * abs(x - 130) / L) + 1, MET_XL)
    disc(130, c, 7, MET_D)
    ring(130, c, 7, MET_L)
    disc(130, c, 2.5, MET_XL)
    for e in (130 - L, 130 + L):
        disc(e, c, 3.5, MET_D)
        disc(e, c, 1.4, MET_XL)


def pan(cx, top):
    """A steel pan: shallow dish, rolled rim, a ring under it; the bridle chains meet
    above it at the hanger."""
    h = PAN_W // 2
    rect(cx - h, top, cx + h, top + 4, MET)
    rect(cx - h, top, cx + h, top, MET_XL)
    rect(cx - h + 2, top + 5, cx + h - 2, top + 6, MET_D)
    rect(cx - h - 1, top - 3, cx - h, top + 3, MET_L)          # rim lips
    rect(cx + h, top - 3, cx + h + 1, top + 3, MET_L)
    for k in range(cx - h + 4, cx + h - 3, 7):
        px(k, top + 2, MET_D)


def scales_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly: floor_at(m, X(lx), Y(ly))
    (wx, wy), (ex, ey) = ends()
    pw, pe = int(wy + CHAIN_L), int(ey + CHAIN_L)

    teeth(m, X(40), X(380), Y(80), 24)
    for x, y, d, rx, ry in ((14, 110, -1, 12, 9), (404, 120, 1, 13, 9), (20, 270, -1, 11, 8),
                            (402, 290, 1, 12, 8)):
        x0 = ox + x
        while (x0, oy + y) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), oy + y, rx, ry, rough=0.25)

    # the A-frame on the spire, and the pointer over its dial
    px_, py_ = X(PIVOT[0]), Y(PIVOT[1])
    st = Y(PIVOT[1] + 27)
    for s in (-1, 1):
        for t in range(3):
            line(px_ + s * (14 - t), st, px_, py_ + 2, MET_D if t == 2 else MET)
    rect(px_ - 16, st - 1, px_ + 16, st + 2, MET_D)
    rect(px_ - 16, st - 1, px_ + 16, st - 1, MET_L)
    for k in range(-5, 6):                                      # the dial: an arc of ticks
        a = -math.pi / 2 + k * 0.12
        r0, r1 = 30, 34 if k % 5 else 37
        line(px_ + math.cos(a) * r0, py_ + math.sin(a) * r0, px_ + math.cos(a) * r1,
             py_ + math.sin(a) * r1, PALE_G if k == 0 else MET_L)
    for k in range(-5, 6):
        a = -math.pi / 2 + k * 0.12
        px(px_ + math.cos(a) * 29, py_ + math.sin(a) * 29, MET_D)
    a = -math.pi / 2 - TILT                                     # the pointer swings with the beam
    line(px_, py_, px_ + math.cos(a) * 36, py_ + math.sin(a) * 36, RED_L)
    line(px_ + 1, py_, px_ + 1 + math.cos(a) * 34, py_ + math.sin(a) * 34, RED)

    # the beam, the bridles and the pans
    draw_rotated(260, 20, beam_local, px_, py_, -TILT)
    for (bx, by), ptop in (((wx, wy), pw), ((ex, ey), pe)):
        hy = Y(ptop) - 30
        chain_line(X(bx), Y(by) + 3, X(bx), hy)
        disc(X(bx), hy, 2, MET_L)
        chain_line(X(bx), hy, X(bx) - PAN_W // 2, Y(ptop) - 3)
        chain_line(X(bx), hy, X(bx) + PAN_W // 2, Y(ptop) - 3)
        pan(int(X(bx)), Y(ptop))

    # the west pan: heaped with ore
    top = Y(pw)
    for x in range(int(X(wx)) - 22, int(X(wx)) + 23):
        hgt = int(13 * (1 - ((x - X(wx)) / 23.0) ** 2) + 2 * math.sin(x * 0.9))
        for y in range(top - hgt, top):
            r = rnd()
            px(x, y, ORE if r < 0.18 else DIRT if r < 0.5 else ROCK_M if r < 0.8 else DIRT_D)
        px(x, top - hgt, DIRT_L)
    for _ in range(8):
        disc(X(wx) - 16 + rnd() * 32, top - 4 - rnd() * 6, 1.5 + rnd(), pick([ORE, ROCK_L]))

    # the east pan: the crew riding it up to the east ledge
    top = Y(pe)
    stand("RiotBrute", int(X(ex)) - 13, top)
    stand("WizMaskwraith", int(X(ex)) + 2, top, flip=True)
    stand("Gaper", int(X(ex)) + 16, top, flip=True)

    # the west ledge, where the ore is tipped in from; the east ledge the lift serves
    lw = Y(LEDGE_W)
    draw_rotated(32, 20, tub_cart, X(38), lw - 10, 0.0)
    for t in range(3):                                           # a tipping board off the ledge
        line(X(56), lw - 3 + t, X(int(wx) - 20), Y(pw) - 14 + t, WOOD if t < 2 else WOOD_D)
    for k in range(4):
        px(X(62 + k * 5), lw - 1 + k * 3, pick([ORE, DIRT_L]))
    stand("Grenadier", X(18), lw)
    le = Y(LEDGE_E)
    stand("WizRamskull", X(392), le, flip=True)
    rect(X(int(ex) + 33), le - 2, X(int(ex) + 40), le - 1, MET_D)   # a landing plate at the ledge lip
    lamp(X(380), ceil_at(m, X(380), le - 30) + 1, drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)

    # the floor: what is under each pan, and the crew round the spire
    for lx, name, flip in ((156, "Ghast", False), (262, "Pyro", True)):
        stand(name, X(lx), fl(lx, FLOOR - 20), flip=flip)
    bw = fl(int(wx), 330)
    scrap_pile(X(int(wx)) - 20, bw, 40, 6, colors=(ORE, DIRT, ROCK_M, DIRT_L))
    be = fl(int(ex), 340)
    for k in range(3):                                           # stakes in the east pit
        line(X(int(ex)) - 18 + k * 18, be - 1, X(int(ex)) - 16 + k * 18, be - 12, WOOD_D)
        px(X(int(ex)) - 16 + k * 18, be - 13, WOOD_L)
    corpse(X(int(ex)) - 8, be)
    lad_x = X(int(ex) + 20)
    while (lad_x, be - 30) in m:
        lad_x += 1
    ladder(lad_x - 8, Y(LEDGE_E), be - 1, w=6, step=6)               # down the pit wall from the ledge
    crate_g(X(140), fl(146, FLOOR - 20), 10)
    keg(X(270), fl(274, FLOOR - 20))
    lamp(X(130), ceil_at(m, X(130), Y(70)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=80, strength=0.15)
    lamp(X(290), ceil_at(m, X(290), Y(70)) + 1, drop=10, bulb=LAMP, tint=LAMP, r=80, strength=0.15)


ROOM = {
    "name": "THE SCALES", "w": 420, "h": 400,
    "shapes": [([("blob", 210, 196, 196, 150)], 0.07),
               ([("blob", 94, 334, 38, 26), ("blob", 322, 350, 40, 30)], 0.1)],
    "sockets": {"T1": ("T", 130, 70), "T2": ("T", 296, 70),
                "L1": ("L", LEDGE_W, 26), "R1": ("R", LEDGE_E, 26),
                "L2": ("L", FLOOR - 2, 70), "B1": ("B", 322, 40)},
    "edit": scales_edit,
    "furnish": scales_furnish,
}


SHEET = {
    "seed": 72401,
    "callouts": [
        ("1 ONE BEAM ON ONE PIN", (-118, -48), (180, 116)),
        ("2 ORE PAN, LOW", (-118, 236), (96, 252)),
        ("3 THE CREW RIDE THE LIGHT PAN", (190, -48), (334, 172)),
    ],
    "beats": [
        ("CHANGE THE WEIGHT AND THE BEAM SWINGS: ONE PAN DROPS, ONE RISES", (170, 180, 195)),
        ("SHOOT THE ORE OFF AND THE CREW GO DOWN INTO THE EAST PIT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
