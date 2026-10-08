"""Small room S36 - THE MENAGERIE.

A low oval hall where the cult keeps what it catches: iron cages stacked two high on
rock shelves off both walls, and more hung on chains from the roof - Minespiders, a
Gaper, and one Ghast in the big cage in the middle. The keepers walk the floor between
them with prods and buckets. Break a cage - shoot the bars, or the chain it hangs on -
and what was inside goes for whoever is nearest, keeper or you.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S36"

FLOOR = 292
W_SHELF = 204            # west shelf top
E_SHELF = 186            # east shelf top
RUST = (104, 74, 58)
STRAW = (150, 128, 76)
STRAW_D = (104, 88, 52)


def zoo_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > FLOOR and 40 < lx < 380:
            continue
        if lx < 104 + 8 * math.sin(ly * 0.2) and ly >= W_SHELF and ly < 262 - (lx - 30) * 0.4:
            continue                                         # west shelf
        if lx > 324 - 6 * math.sin(ly * 0.23) and ly >= E_SHELF and ly < 240 + (lx - 390) * 0.5:
            continue                                         # east shelf
        out.add((x, y))
    return out


def iron_cage(x0, bottom, w, h, beast=None, flip=False, bent=None, gap=None):
    """A keeper's cage side-on: a floor plate, a roof plate with a lifting eye, bars every
    3px drawn over whatever is inside. `bent` = a bar index already sprung."""
    top = bottom - h
    rect(x0, top + 2, x0 + w, bottom - 3, (22, 24, 28))           # shadow behind the bars
    for k in range(6):                                            # straw on the floor plate
        px(x0 + 2 + rnd() * (w - 4), bottom - 3, pick([STRAW, STRAW_D]))
    if beast:
        stand(beast, x0 + w // 2, bottom - 2, flip=flip)
    rect(x0 - 1, bottom - 2, x0 + w + 1, bottom, MET_D)
    rect(x0 - 1, bottom - 2, x0 + w + 1, bottom - 2, MET)
    rect(x0 - 1, top, x0 + w + 1, top + 2, MET_D)
    rect(x0 - 1, top, x0 + w + 1, top, MET_L)
    rect(x0, top + h // 2, x0 + w, top + h // 2, MET_D, 0.8)        # a band halfway
    for i, x in enumerate(range(x0, x0 + w + 1, 3)):
        if gap and gap[0] <= i <= gap[1]:
            continue
        if bent is not None and i == bent:
            for y in range(top + 3, bottom - 2):
                d = int(3 * math.sin((y - top) / h * math.pi))
                px(x - d, y, MET_L)
            continue
        rect(x, top + 3, x, bottom - 3, MET if i % 2 else RUST)
        px(x, top + 3 + int(rnd() * (h - 6)), MET_L)
    rect(x0 + w // 2 - 1, top - 3, x0 + w // 2 + 1, top - 1, MET_D)   # lifting eye
    px(x0 + w // 2, top - 2, INK)


def hung(cx, roof, drop, w, h, beast, flip=False, bent=None, gap=None):
    top = roof + drop
    chain(cx, roof, top - 2)
    iron_cage(cx - w // 2, top + h, w, h, beast, flip, bent, gap)
    return top + h


def bucket(x, floor):
    rect(x, floor - 6, x + 5, floor - 1, MET)
    rect(x, floor - 6, x + 5, floor - 6, MET_L)
    rect(x + 1, floor - 5, x + 4, floor - 5, RED)
    line(x, floor - 6, x + 2, floor - 9, MET_D)
    line(x + 5, floor - 6, x + 3, floor - 9, MET_D)


def prod(x, floor, lean=7):
    """Keeper's pole leaned on something: shaft and an iron hook."""
    line(x, floor - 1, x + lean, floor - 22, WOOD_D)
    rect(x + lean - 1, floor - 25, x + lean + 1, floor - 22, MET_L)
    px(x + lean + 2, floor - 24, MET_L)


def bones(cx, floor, n=8):
    for _ in range(n):
        x = cx + (rnd() - 0.5) * 18
        rect(x, floor - 1, x + 2 + rnd() * 3, floor - 1, (190, 184, 160))
    px(cx, floor - 2, (190, 184, 160))
    disc(cx + 4, floor - 2, 1.5, (190, 184, 160))


def zoo_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR)
    roof = lambda lx: ceil_at(m, X(lx), Y(160)) + 1

    teeth(m, X(60), X(370), Y(140), 22)
    # rock knuckles off the walls, so the oval is not a drawn line
    for lx, ly, d, rx, ry in ((40, 150, -1, 12, 9), (392, 250, 1, 12, 10), (60, 276, -1, 14, 8)):
        x0, y0 = X(lx), Y(ly)
        while (x0, y0) in m:
            x0 += d
        rock_blob(x0 - d * (rx // 3), y0, rx, ry, rough=0.25)

    # straw across the floor and the shelves
    for lx in range(48, 376):
        for base in (fl,):
            if chance(0.35):
                px(X(lx), base - 1, pick([STRAW, STRAW_D, DIRT_L]))
    for lx in range(36, 100):
        if chance(0.4):
            px(X(lx), Y(W_SHELF) - 1, pick([STRAW, STRAW_D]))

    # the west shelf: two cages, stacked
    ws = Y(W_SHELF)
    iron_cage(X(46), ws, 26, 28, "Minespider")
    iron_cage(X(46), ws - 29, 26, 28, "Minespider", flip=True)
    iron_cage(X(76), ws, 22, 24, None)
    bones(X(86), ws - 3, 4)
    # the east shelf: two stacked and one on its own
    es = Y(E_SHELF)
    iron_cage(X(340), es, 26, 28, "Gaper", flip=True)
    iron_cage(X(340), es - 29, 26, 28, "Minespider", flip=True)
    lamp(X(358), roof(358), drop=4, bulb=LAMP, tint=LAMP, r=50, strength=0.13)

    # the roof: the Ghast in the big cage in the middle, spiders either side of it
    big_bot = hung(X(206), roof(206), 70, 34, 36, "Ghast", flip=True)
    hung(X(146), roof(146), 46, 24, 26, "Minespider")
    hung(X(266), roof(266), 34, 24, 26, "Minespider", flip=True, gap=(3, 5))
    hung(X(306), roof(306), 18, 20, 22, "Minespider", flip=True)
    hung(X(116), roof(116), 22, 20, 22, None)
    # what the sprung cage is letting out: a spider on its thread, coming down
    sy = roof(266) + 34 + 26
    rect(X(262), sy, X(262), sy + 40, (200, 200, 190), 0.6)
    stand("Minespider", X(262), sy + 62, flip=True)
    lamp(X(184), roof(184), drop=12, bulb=LAMP, tint=LAMP, r=110, strength=0.16)
    lamp(X(300), roof(300), drop=20, bulb=LAMP, tint=LAMP, r=70, strength=0.12)
    glow(X(210), big_bot - 16, 30, (150, 200, 170), 0.12)

    # on the floor: a cart cage being wheeled, the keepers, and the cage that already broke
    cx0 = 232
    iron_cage(X(cx0), fl - 6, 28, 26, "Minespider", flip=True)
    rect(X(cx0 - 2), fl - 7, X(cx0 + 30), fl - 6, WOOD_D)
    for wx in (cx0 + 4, cx0 + 24):
        disc(X(wx), fl - 3, 2.6, INK)
        disc(X(wx), fl - 3, 1, MET_L)
    line(X(cx0 + 30), fl - 7, X(cx0 + 40), fl - 16, WOOD_D)           # the handle
    stand("WizDeepminer", X(cx0 + 48), fl, flip=True)

    stand("RiotBrute", X(160), fl)
    stand("Reaper", X(298), fl, flip=True)
    prod(X(310), fl)
    iron_cage(X(322), fl, 24, 26, "Gaper", flip=True)            # a stack on the floor too
    iron_cage(X(322), fl - 27, 24, 24, "Minespider", flip=True)
    rect(X(318), fl - 9, X(321), fl - 1, WOOD_D)                  # a chock
    bucket(X(128), fl)
    bucket(X(196), fl)
    bones(X(102), fl, 10)

    # the broken one: on the floor by the west shelf, door sprung, its spider on a keeper
    bx = 112
    iron_cage(X(bx), fl, 24, 24, None, bent=2, gap=(4, 6))
    for k in range(4):                                            # its bars, on the floor
        line(X(bx + 28 + k * 5), fl - 1, X(bx + 34 + k * 5), fl - 3 - (k % 2), RUST)
    corpse(X(70), fl, c=(90, 70, 90))
    stand("Minespider", X(76), fl - 3, flip=True)

    # a keeper on the east shelf with a feed bucket
    stand("WizHollowhood", X(374), es, flip=True)
    bucket(X(386), es)
    # a winch on the west wall for lowering the roof cages
    wx, wy = X(36), Y(178)
    disc(wx + 6, wy, 4, MET_D)
    ring(wx + 6, wy, 4, MET_L)
    cable(wx + 6, wy - 4, X(116), roof(116) + 4, sag=3, c=MET_D)


ROOM = {
    "name": "THE MENAGERIE", "w": 420, "h": 360,
    "shapes": [([("blob", 210, 210, 186, 106)], 0.08),
               ([("blob", 76, 170, 54, 40),                # the west shelf's bay
                 ("blob", 356, 150, 50, 42)], 0.12)],      # the east shelf's bay
    "sockets": {"T1": ("T", 88, 120), "T2": ("T", 330, 104),
                "L1": ("L", W_SHELF - 58, 30), "R1": ("R", E_SHELF, 24),
                "L2": ("L", FLOOR, 66), "R2": ("R", FLOOR, 66)},
    "edit": zoo_edit,
    "furnish": zoo_furnish,
}


SHEET = {
    "seed": 73601,
    "callouts": [
        ("1 CAGES HUNG ON CHAINS", (250, -50), (206, 160)),
        ("2 STACKED ON THE SHELVES", (-125, 64), (58, 150)),
        ("3 BREAK ONE, IT GOES FOR THE NEAREST", (180, 380), (124, 280)),
    ],
    "beats": [
        ("SHOOT A CHAIN OR THE BARS: THE BEAST TAKES THE CLOSEST BODY", (170, 180, 195)),
        ("KEEPERS WALK THE FLOOR UNDER THE GHAST'S CAGE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
