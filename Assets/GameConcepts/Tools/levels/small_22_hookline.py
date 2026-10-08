"""Small room S22 - THE HOOK LINE.

A long, low butchery. Under the roof an endless chain runs round two sprockets, one at
each end of the hall, and from trolleys on its lower run hang meat hooks with carcasses
on them, moving east the whole time; the upper run brings the empty hooks back west.
Under the line the crew work at the blocks, a gut trench down the middle of the floor.
The line does not care what is on a hook: hang an enemy on it - or knock one into the
hooks - and it carries him the length of the hall and round the sprocket with the meat.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S22"

FLOOR = 222
SPR_W, SPR_E, SPR_Y, SPR_R = 70, 392, 114, 16
TOP_RUN, LOW_RUN = SPR_Y - SPR_R, SPR_Y + SPR_R
TRENCH = (196, 290)                  # gut trench across the middle of the floor
MEAT = (112, 50, 46)
MEAT_D = (78, 36, 34)
FAT = (176, 150, 124)
BONE = (196, 186, 160)


def hook_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if lx < 40:
            f = 252                                        # west nook, a step down
        elif lx > 408:
            f = 204 - 2 * math.sin(lx * 0.3)               # east alcove, a step up
        elif TRENCH[0] < lx < TRENCH[1]:
            f = FLOOR + 30 * math.sqrt(max(0.0, 1 - ((lx - 243) / 47.0) ** 2))
        else:
            f = FLOOR + 2 * math.sin(lx * 0.07)
        if ly < f:
            out.add((x, y))
    return out


def sprocket(cx, cy, r):
    disc(cx, cy, r, MET_D)
    ring(cx, cy, r, MET_L)
    for k in range(12):
        a = k * math.pi / 6
        disc(cx + math.cos(a) * (r + 1.5), cy + math.sin(a) * (r + 1.5), 1.4, MET)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        line(cx, cy, cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2), MET)
    disc(cx, cy, 4, MET)
    disc(cx, cy, 1.6, INK)


def chain_run(x0, x1, y):
    for x in range(int(x0), int(x1) + 1):
        px(x, y, MET_L if x % 3 else MET_D)
        px(x, y + 1, MET_D if x % 3 else MET)


def trolley(x, y):
    rect(x - 2, y, x + 2, y + 2, MET_D)
    rect(x - 2, y, x + 2, y, MET_L)


def hook(x, y, ln=8):
    """A meat hook off a trolley on the chain: a stem and an open S, point up."""
    trolley(x, y)
    rect(x, y + 3, x, y + ln, MET_L)
    px(x - 1, y + ln + 1, MET_L)
    px(x - 1, y + ln + 2, MET_L)
    px(x, y + ln + 3, MET_L)
    px(x + 1, y + ln + 2, MET_XL)
    px(x + 1, y + ln + 1, MET_XL)
    return y + ln + 3


def carcass(x, top, ln=36, sway=0):
    """A side of meat hung by the hock: a narrow shank on the hook, the haunch, a waist,
    then the opened ribcage - fat down the back, the cavity dark with the ribs across
    it - tapering to the neck at the bottom."""
    prof = ((0.0, 1.0), (0.12, 1.2), (0.3, 5.5), (0.45, 4.2), (0.55, 4.0), (0.72, 5.2),
            (0.9, 3.4), (1.0, 1.5))
    for i in range(ln):
        t = i / (ln - 1)
        for (t0, h0), (t1, h1) in zip(prof, prof[1:]):
            if t0 <= t <= t1:
                half = h0 + (h1 - h0) * (t - t0) / (t1 - t0)
                break
        cx = x + sway * t
        l, r = cx - half, cx + half * 0.8
        rect(l, top + i, r, top + i, MEAT)
        rect(l, top + i, l + 1, top + i, FAT if t > 0.12 else MEAT_D)
        px(r, top + i, MEAT_D)
        if t > 0.5 and t < 0.92:                                  # the opened cavity
            rect(cx, top + i, r - 1, top + i, (62, 28, 28))
            if i % 3 == 0:
                line(cx - 1, top + i, r - 1, top + i + 1, BONE)
        elif 0.18 < t < 0.4 and i % 4 == 0:
            px(cx - 1 + int(rnd() * 3), top + i, FAT, 0.6)
    rect(x - 1, top - 2, x + 1, top, BONE)                          # the hock bone, over the hook


def hung_body(name, x, top):
    """An enemy hung by his feet from a hook: the sprite turned over, gone grey."""
    draw_rotated(24, 26, lambda: sprite(name, 2, 2, tint=((80, 84, 86), 0.3)), x, top + 9, math.pi + 0.12)
    line(x - 1, top - 1, x + 1, top + 4, MET_L)                    # the hook through the boots
    for k in range(3):
        px(x - 2 + k * 2, top + 24 + k * 3, RED, 0.8)


def block(x, floor):
    """Butcher's block: a timber stump, scored top, a cleaver bitten into it."""
    rect(x, floor - 10, x + 14, floor - 1, WOOD)
    rect(x, floor - 10, x + 14, floor - 10, WOOD_L)
    rect(x + 14, floor - 10, x + 14, floor - 1, WOOD_D)
    for k in range(3):
        px(x + 3 + k * 4, floor - 10, RED)
    rect(x + 9, floor - 16, x + 10, floor - 10, MET_L)            # the cleaver
    rect(x + 6, floor - 18, x + 11, floor - 15, MET_XL)
    rect(x + 6, floor - 18, x + 7, floor - 15, MET)
    rect(x + 2, floor - 12, x + 7, floor - 11, MEAT)


def hook_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = lambda lx, ly=FLOOR - 20: floor_at(m, X(lx), Y(ly))

    teeth(m, X(110), X(370), Y(80), 22)
    teeth(m, X(20), X(110), Y(150), 6)
    for x, y, d, rx, ry in ((14, 170, -1, 12, 9), (446, 160, 1, 12, 8)):
        x0 = ox + x
        while (x0, oy + y) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), oy + y, rx, ry, rough=0.25)

    # the line: two sprockets on brackets bolted into the roof, chain round them
    for sx in (SPR_W, SPR_E):
        top = ceil_at(m, X(sx), Y(SPR_Y)) + 1
        rect(X(sx) - 2, top, X(sx) + 2, Y(SPR_Y), MET_D)
        rect(X(sx) - 2, top, X(sx) - 2, Y(SPR_Y), MET)
        line(X(sx) - 12, top, X(sx), Y(SPR_Y) - 8, MET_D)
        line(X(sx) + 12, top, X(sx), Y(SPR_Y) - 8, MET_D)
    for sx in (SPR_W, SPR_E):
        sprocket(X(sx), Y(SPR_Y), SPR_R)
    chain_run(X(SPR_W), X(SPR_E), Y(TOP_RUN) - 1)
    chain_run(X(SPR_W), X(SPR_E), Y(LOW_RUN))
    for x in range(SPR_W + 40, SPR_E - 20, 52):                     # guide rail hangers
        top = ceil_at(m, X(x), Y(TOP_RUN) - 4) + 1
        line(X(x), top, X(x), Y(TOP_RUN) - 3, MET_D)
    for k in range(3):                                              # which way it runs
        for x in (150, 250, 330):
            px(X(x + k), Y(LOW_RUN) + 3 + (k % 2), PALE_G, 0.8)
            px(X(x + 20 - k), Y(TOP_RUN) - 4 - (k % 2), PALE_G, 0.6)
    # the drive: a gearbox on the east bracket, belted to an engine in the east alcove
    ex, ey = X(430), Y(204)
    rect(ex - 12, ey - 20, ex + 10, ey - 1, MET)
    rect(ex - 12, ey - 20, ex + 10, ey - 20, MET_L)
    rect(ex - 12, ey - 6, ex + 10, ey - 1, MET_D)
    disc(ex, ey - 26, 8, MET_D)
    ring(ex, ey - 26, 8, MET_L)
    disc(ex, ey - 26, 2, MET_XL)
    line(ex - 6, ey - 32, X(SPR_E) + 4, Y(SPR_Y) - 5, (60, 52, 42))
    line(ex + 4, ey - 19, X(SPR_E) + 6, Y(SPR_Y) + 5, (60, 52, 42))
    rect(ex + 6, ey - 34, ex + 8, ey - 20, MET_D)                   # exhaust stack
    steam_plume(ex + 7, ey - 36, r=10, n=14, c=(120, 120, 120))
    stand("Pyro", X(414), Y(204))

    # hooks on the lower run, loaded; empties going back on the upper
    loads = {104: "meat", 132: "meat", 160: "body", 188: "meat", 216: "empty", 244: "meat",
             272: "meat", 300: "body2", 328: "meat", 356: "meat"}
    for lx, what in loads.items():
        tip = hook(X(lx), Y(LOW_RUN) + 2, ln=9 if what != "empty" else 6)
        if what == "meat":
            carcass(X(lx), tip - 1, ln=34 + (lx % 3) * 3, sway=(lx % 5) - 2)
        elif what == "body":
            hung_body("Grenadier", X(lx), tip - 3)
        elif what == "body2":
            hung_body("Gaper", X(lx), tip - 3)
    for lx in range(96, 380, 28):
        hook(X(lx), Y(TOP_RUN) + 2, ln=5)
    # one going round the west sprocket, swung out on the turn
    hook(X(SPR_W) - SPR_R - 3, Y(SPR_Y) - 2, ln=6)

    # under the line: the blocks, the trench and the crew
    f = Y(FLOOR)
    block(X(96), fl(96))
    block(X(312), fl(312))
    block(X(362), fl(362))
    stand("WizBonecrown", X(124), fl(124), flip=True)
    stand("Reaper", X(166), fl(166))
    stand("RiotBrute", X(336), fl(336))
    stand("Gaper", X(384), fl(384), flip=True)
    stand("Ghast", X(300), fl(300), flip=True)
    # the gut trench: bones and offal in the bottom, a plank across it
    tb = fl(243, FLOOR + 4)
    for _ in range(60):
        x = 214 + rnd() * 58
        y = tb - 1 - rnd() * 7 * (1 - abs(x - 243) / 32.0)
        if (int(X(x)), int(y)) in m:
            px(X(x), y, pick([BONE, BONE, MEAT_D, MEAT, DIRT]))
    for k in range(4):
        line(X(222 + k * 13), tb - 2 - k % 2, X(228 + k * 13), tb - 6 + k % 2, BONE)
    plank(X(TRENCH[0] - 6), f - 2, X(TRENCH[1] + 6), f - 2, thick=3)
    stand("Minespider", X(250), tb)
    # a tub of trimmings and a bone heap in the west nook
    nk = Y(252)
    scrap_pile(X(8), nk, 30, 9, colors=(BONE, BONE, MEAT_D, DIRT, FAT))
    draw_rotated(32, 20, tub_cart, X(58), fl(58) - 10, 0)
    for k in range(6):
        px(X(48 + k * 3), fl(58) - 18, pick([BONE, MEAT]))
    # salt kegs and a crate stack by the east blocks; a hide rack off the west wall
    keg(X(276), fl(276))
    keg(X(286), fl(286))
    crate_g(X(196) - 14, fl(186))
    for k in range(3):
        rect(X(56) + k * 7, Y(150), X(56) + k * 7 + 4, Y(168), (98, 74, 58))
        rect(X(56) + k * 7, Y(150), X(56) + k * 7 + 4, Y(150), (130, 100, 76))
    wx = X(56)
    while (wx, Y(150)) in m:
        wx -= 1
    rect(wx, Y(148), X(78), Y(149), WOOD_D)
    for x in (200, 290):
        lamp(X(x), ceil_at(m, X(x), Y(TOP_RUN)) + 1, drop=46, bulb=LAMP, tint=LAMP, r=80, strength=0.15)
    lamp(X(24), ceil_at(m, X(24), Y(230)) + 1, drop=4, bulb=LAMP, tint=LAMP, r=40, strength=0.12)
    for _ in range(18):                                            # what drips off the line
        x = 100 + rnd() * 270
        px(X(x), f - 1, RED, 0.7)


ROOM = {
    "name": "THE HOOK LINE", "w": 460, "h": 276,
    "shapes": [([("blob", 230, 160, 216, 66),
                 ("tube", [(56, 116), (404, 116)], 34)], 0.07),
               ([("blob", 36, 226, 36, 30),                    # west nook, a step down
                 ("blob", 430, 176, 30, 34)], 0.12)],          # east alcove, a step up
    "sockets": {"T1": ("T", 150, 86), "T2": ("T", 320, 86),
                "L1": ("L", 252, 20), "R1": ("R", 204, 18),
                "B1": ("B", 243, 34)},
    "edit": hook_edit,
    "furnish": hook_furnish,
}


SHEET = {
    "seed": 72201,
    "callouts": [
        ("1 ENDLESS CHAIN ON TWO SPROCKETS", (-124, -50), (70, 98)),
        ("2 IT CARRIES ANY BODY HUNG ON IT", (230, -50), (300, 140)),
        ("3 THE GUT TRENCH", (330, 296), (243, 244)),
    ],
    "beats": [
        ("THE LINE NEVER STOPS: WHAT IS ON A HOOK GOES ROUND THE HALL", (170, 180, 195)),
        ("HOOK THEM ONTO IT, OR SHOOT A HOOK AND DROP THE MEAT ON THEM", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
