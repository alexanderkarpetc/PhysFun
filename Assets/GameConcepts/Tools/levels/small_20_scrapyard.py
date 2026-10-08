"""Small room S20 - THE SCRAPYARD.

A rough cave the mine dumps its dead iron into: heaps of loose junk - girders, wheels,
drums, plates, a tub on its side - piled on a rock bowl, and in the east pocket a jaw
crusher still chewing, its swing jaw on a flywheel. Nothing here is fixed down, so for
telekinesis everything is ammo: pick it up, throw it, and whatever is thrown into the
jaws comes out the bottom as scrap.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S20"

RUST = (98, 64, 46)
RUST_L = (136, 92, 64)
JAW_TOP, JAW_BOT = 226, 298
FIXED = ((318, JAW_TOP), (340, JAW_BOT))     # fixed jaw, west side of the V
SWING = ((370, JAW_TOP), (350, JAW_BOT))     # swing jaw, east side
FLY = (392, 212, 15)


# ─────────────────────────────────────────────────────────────────────────────
#  Junk
# ─────────────────────────────────────────────────────────────────────────────
def girder_art(n):
    def draw():
        rect(0, 0, n - 1, 1, MET_L)
        rect(0, 5, n - 1, 6, MET_D)
        rect(0, 2, n - 1, 4, MET)
        for x in range(3, n - 3, 7):
            disc(x + 2, 3, 1, (40, 40, 42))
        for _ in range(n // 6):
            x = int(rnd() * n)
            rect(x, int(rnd() * 6), x + 1, int(rnd() * 6), RUST)
    return draw


def girder(cx, cy, n, angle):
    draw_rotated(n, 7, girder_art(n), cx, cy, angle)


def wheel(cx, cy, r, spokes=6):
    ring(cx, cy, r, MET_D)
    ring(cx, cy, r - 1, MET_L)
    ring(cx, cy, r - 2, MET_D)
    for k in range(spokes):
        a = k * 2 * math.pi / spokes + 0.2
        line(cx, cy, cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2), MET)
    disc(cx, cy, 2.2, MET_D)
    px(cx, cy, MET_XL)


def drum_(x, floor, c=RUST, cl=RUST_L, lying=False):
    if lying:
        rect(x, floor - 9, x + 13, floor - 1, c)
        rect(x, floor - 9, x + 13, floor - 9, cl)
        for xx in (x + 3, x + 10):
            rect(xx, floor - 9, xx, floor - 1, MET_D)
        disc(x + 13, floor - 5, 4, MET_D)
        disc(x + 13, floor - 5, 2, c)
        return
    rect(x, floor - 13, x + 9, floor - 1, c)
    rect(x, floor - 13, x + 9, floor - 13, cl)
    for yy in (floor - 10, floor - 4):
        rect(x, yy, x + 9, yy, MET_D)
    rect(x + 1, floor - 12, x + 1, floor - 2, cl)


def plate(x0, y0, x1, y1):
    line(x0, y0, x1, y1, MET_L)
    line(x0, y0 + 1, x1, y1 + 1, MET)
    line(x0, y0 + 2, x1, y1 + 2, MET_D)


def heap(m, cx, halfw, h, ref):
    """A lens of mixed junk on the floor - loose, every piece of it its own body."""
    for x in range(int(cx - halfw), int(cx + halfw) + 1):
        f = floor_at(m, x, ref)
        top = f - int(h * max(0.0, 1 - ((x - cx) / halfw) ** 2))
        for y in range(top, f):
            r = rnd()
            px(x, y, MET_D if r < 0.32 else MET if r < 0.47 else RUST if r < 0.57 else
               DIRT_D if r < 0.77 else (40, 40, 42) if r < 0.93 else MET_L)
        if top < f:
            px(x, top, MET_L if x % 4 else RUST_L)
    for _ in range(int(halfw * h / 18)):
        x = cx + (rnd() - 0.5) * halfw * 1.6
        f = floor_at(m, x, ref)
        top = f - h * max(0.0, 1 - ((x - cx) / halfw) ** 2)
        y = top + 2 + rnd() * max(1, f - top - 4)
        if chance(0.5):
            line(x - 3, y, x + 3, y - 1 + rnd() * 2, pick([MET_L, RUST_L, MET_XL]))
        else:
            ring(x, y, 2, pick([MET_L, RUST_L]))


def heap_top(m, cx, halfw, h, ref, x):
    f = floor_at(m, x, ref)
    return f - int(h * max(0.0, 1 - ((x - cx) / halfw) ** 2))


# ─────────────────────────────────────────────────────────────────────────────
#  The jaw crusher
# ─────────────────────────────────────────────────────────────────────────────
def jaw(p0, p1, side):
    """A jaw plate: a thick steel slab with its corrugated face toward the V."""
    (x0, y0), (x1, y1) = p0, p1
    for t in range(6):
        line(x0 + side * t, y0, x1 + side * t, y1, MET if t else MET_L)
    n = int(math.hypot(x1 - x0, y1 - y0) / 4)
    for i in range(n):
        u = i / n
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        px(x - side, y, MET_XL)
        px(x - side, y + 1, MET_XL)
        px(x - 2 * side, y + 1, MET_L)


def yard_edit(air, ox, oy):
    """The crusher housing: fill the east pocket with steel round the V, leaving the
    V and the discharge slot under it open."""
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if JAW_TOP - 4 <= ly <= JAW_BOT + 8 and 306 <= lx <= 404:
            u = (ly - JAW_TOP) / float(JAW_BOT - JAW_TOP)
            l = FIXED[0][0] + (FIXED[1][0] - FIXED[0][0]) * min(max(u, 0), 1)
            r = SWING[0][0] + (SWING[1][0] - SWING[0][0]) * min(max(u, 0), 1)
            if not (l + 6 <= lx <= r - 6 or (ly > JAW_BOT and 338 <= lx <= 352)):
                continue
        out.add((x, y))
    return out


def yard_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly

    teeth(m, X(100), X(300), Y(170), 20)
    teeth(m, X(20), X(110), Y(160), 6)
    teeth(m, X(270), X(370), Y(160), 8)

    # the crusher: housing, jaws, flywheel and pitman, a lip of plate round the mouth
    hx0, hx1 = X(306), X(404)
    for y in range(Y(JAW_TOP - 4), Y(JAW_BOT + 9)):
        for x in range(hx0, hx1 + 1):
            if (x, y) in m:
                continue
            dx, dy = (x - X(352)) / 56.0, (y - Y(262)) / 66.0
            if dx * dx + dy * dy <= 1.0:
                px(x, y, (64, 66, 70) if (x * 3 + y) % 11 else (52, 54, 58))
    for x in range(hx0 + 4, hx1 - 2, 12):
        for y in range(Y(JAW_TOP + 6), Y(JAW_BOT + 4), 12):
            dx, dy = (x - X(352)) / 52.0, (y - Y(262)) / 62.0
            if (x, y) not in m and dx * dx + dy * dy <= 1.0:
                disc(x, y, 1, MET_L)
    jaw((X(FIXED[0][0]), Y(FIXED[0][1])), (X(FIXED[1][0]), Y(FIXED[1][1])), -1)
    jaw((X(SWING[0][0]), Y(SWING[0][1])), (X(SWING[1][0]), Y(SWING[1][1])), 1)
    rect(X(300), Y(JAW_TOP - 6), X(321), Y(JAW_TOP - 4), MET_L)
    rect(X(367), Y(JAW_TOP - 6), X(404), Y(JAW_TOP - 4), MET_L)
    fx, fy, fr = FLY
    wheel(X(fx), Y(fy), fr, spokes=5)
    ring(X(fx), Y(fy), fr + 1, MET_D)
    ex, ey = X(fx) - 4, Y(fy) + 3                        # the eccentric
    disc(ex, ey, 3, MET_L)
    line(ex, ey, X(SWING[0][0] + 3), Y(JAW_TOP - 2), MET_XL)
    line(ex, ey + 1, X(SWING[0][0] + 3), Y(JAW_TOP - 1), MET_D)
    rect(X(fx - 3), Y(fy), X(fx + 3), Y(JAW_TOP - 7), MET_D)        # its bearing post
    # something half-chewed in the V, scrap coming out of the slot
    girder(X(344), Y(256), 22, 1.25)
    for k in range(9):
        px(X(342 + rnd() * 9), Y(JAW_BOT + 12 + k * 3), pick([MET_L, RUST_L, MET_D]))
    sparks(X(346), Y(268), n=10, spread=6)

    # heaps on the bowl floor: big in the west, smaller toward the crusher
    REF = Y(230)
    heap(m, X(120), 76, 60, REF)
    heap(m, X(240), 50, 30, REF)
    heap(m, X(60), 34, 10, Y(160))                      # in the west alcove
    hA = lambda x: heap_top(m, X(120), 76, 60, REF, X(x))
    hB = lambda x: heap_top(m, X(240), 50, 30, REF, X(x))
    hC = lambda x: heap_top(m, X(60), 34, 10, Y(160), X(x))

    # the big pieces on top of the heaps
    girder(X(92), hA(92) - 8, 50, -0.55)
    girder(X(150), hA(150) - 6, 40, 0.42)
    wheel(X(70), hA(70) - 9, 9)
    wheel(X(222), hB(222) - 7, 7)
    drum_(X(116), hA(120) + 1)
    drum_(X(254), hB(260) + 1, lying=True)
    drum_(X(196), hB(201) + 3, c=(70, 84, 60), cl=(98, 116, 80))
    plate(X(170), hA(170) - 2, X(194), hB(194) - 1)
    draw_rotated(32, 20, tub_cart, X(276), hB(276) - 4, 2.7)
    gear(X(86), hC(86) - 6, 6, teeth=7)
    crate_g(X(70), hC(76) + 1, 10)
    girder(X(296), Y(242), 34, -0.95)                   # leaning on the crusher's mouth
    keg(X(24), hC(28) + 1)
    # a roof trolley over the yard: a chain and a hook with a plate still on it
    rect(X(150), Y(150), X(234), Y(152), MET_D)
    rect(X(150), Y(150), X(234), Y(150), MET_L)
    for bx in (156, 206, 232):
        top = ceil_at(m, X(bx), Y(150)) + 1
        if top > Y(110):
            line(X(bx), top, X(bx), Y(149), MET_D)
    rect(X(214), Y(153), X(224), Y(157), MET)
    chain(X(219), Y(158), Y(192))
    line(X(219), Y(192), X(216), Y(196), MET_L)
    plate(X(206), Y(197), X(232), Y(201))

    # held: a wheel in the air with the pull round it, on its way to the brute
    hx, hy = X(176), Y(176)
    wheel(hx, hy, 8)
    for k in range(18):
        a = k * 2 * math.pi / 18
        px(hx + math.cos(a) * 12, hy + math.sin(a) * 12, CYAN, 0.7)
    glow(hx, hy, 18, CYAN, 0.18)
    tx, ty = X(132), hA(132) - 30
    for i in range(0, 16):
        t = i / 15.0
        x = hx + (tx - hx) * t
        y = hy - 16 * math.sin(math.pi * t) + (ty - hy) * t
        if i % 2 == 0 and i > 1:
            rect(x, y, x + 1, y, CYAN, 0.6)

    # who is in the yard
    stand("RiotBrute", X(132), hA(132))
    stand("Gaper", X(170), hA(170) - 1, flip=True)
    stand("BloodMage", X(236), hB(236), flip=True)
    stand("Reaper", X(92), hA(92) - 1)
    stand("WizMaskwraith", X(48), hC(48))
    stand("Ghast", X(312), Y(170), flip=True)

    lamp(X(120), ceil_at(m, X(120), Y(180)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=100, strength=0.15)
    lamp(X(344), ceil_at(m, X(344), Y(200)) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)


ROOM = {
    "name": "THE SCRAPYARD", "w": 420, "h": 380,
    "shapes": [([("blob", 200, 228, 168, 94)], 0.12),       # the yard
               ([("blob", 352, 266, 54, 60),                # the crusher pocket
                 ("blob", 64, 150, 50, 30),                 # west alcove
                 ("blob", 318, 156, 60, 34)], 0.10)],       # east shoulder
    "sockets": {"T1": ("T", 66, 124), "T2": ("T", 250, 140),
                "L1": ("L", 176, 20), "L2": ("L", 254, 40),
                "R1": ("R", 186, 46), "B1": ("B", 345, 52)},
    "edit": yard_edit,
    "furnish": yard_furnish,
}


SHEET = {
    "seed": 72001,
    "callouts": [
        ("1 JAW CRUSHER", (378, 398), (346, 262)),
        ("2 EVERYTHING LOOSE IS AMMO", (-120, 398), (100, 270)),
        ("3 FLYWHEEL", (428, 214), (392, 212)),
    ],
    "beats": [
        ("PICK IT UP, THROW IT: GIRDERS, WHEELS, DRUMS, THEM", (170, 180, 195)),
        ("WHAT GOES IN THE JAWS COMES OUT THE BOTTOM AS SCRAP", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
