"""Small room S38 - THE CLOCKWORK.

A tall cave with a clock's going train set into its walls: four brass wheels, each in
its own round niche cut in the rock, meshing one into the next from the floor to the
roof and turning slowly, driven by an iron weight on a chain off the top wheel's arbor.
Their teeth and spokes are platforms - stand on one and it carries you round and up to
the next - and where two wheels mesh they pinch whatever is between the teeth. Ride
the wheels up, and feed the enemies on them into the mesh.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S38"

BRASS = (138, 106, 62)
BRASS_L = (182, 146, 90)
BRASS_D = (88, 66, 40)
ARROW = (196, 186, 140)
FLOOR = 418

# the train: (name, cx, cy, r, teeth, spokes, phase, turn) - turn +1 clockwise on screen
A = ("A", 86, 336, 66, 22, 6, 0.0, -1)
B = ("B", 160, 248, 44, 15, 5, 0.0, 1)
C = ("C", 250, 194, 56, 19, 6, 0.0, -1)
D = ("D", 120, 180, 30, 10, 4, 0.0, -1)


def place(base, r, other_r, deg):
    """Centre of a wheel of radius `other_r` meshing with `base` at angle `deg`."""
    d = r + other_r + 6
    a = math.radians(deg)
    return base[0] + d * math.cos(a), base[1] + d * math.sin(a)


# put the wheels exactly in mesh, each off the one below it
_bx, _by = place((A[1], A[2]), A[3], B[3], -52)
B = ("B", _bx, _by, 44, 15, 5, 0.18, 1)
_cx, _cy = place((B[1], B[2]), B[3], C[3], -26)
C = ("C", _cx, _cy, 56, 19, 6, 0.0, -1)
_dx, _dy = place((B[1], B[2]), B[3], D[3], -128)
D = ("D", _dx, _dy, 30, 10, 4, 0.4, -1)
WHEELS = (A, B, C, D)


def wheel(cx, cy, r, n, spokes, phase):
    """A clock wheel side-on: a toothed brass rim, crossed spokes, an iron arbor. Inside
    the rim between the spokes is air - a spoke is a beam you can stand on."""
    R = r + 7
    pitch = 2 * math.pi / n
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > R:
                continue
            a = math.atan2(dy, dx)
            c = None
            if d > r:                                         # teeth, tapered
                f = ((a - phase) / pitch) % 1.0
                half = 0.26 - 0.10 * (d - r) / 7.0
                if abs(f - 0.5) < half:
                    c = BRASS_L if d > R - 1.5 else BRASS
            elif d > r - 6:                                   # the rim
                c = BRASS_L if d > r - 1.2 else BRASS_D if d < r - 4.8 else BRASS
                if dy > 0 and d > r - 1.2:
                    c = BRASS
            elif d < 11:                                      # boss and arbor
                c = MET_L if d < 3.5 else INK if d < 4.5 else BRASS_D if d > 9.5 else BRASS
            else:
                for k in range(spokes):
                    sa = phase + k * 2 * math.pi / spokes
                    along = dx * math.cos(sa) + dy * math.sin(sa)
                    across = -dx * math.sin(sa) + dy * math.cos(sa)
                    if along > 0 and abs(across) < 3.0:
                        c = BRASS_L if across < -2.0 else BRASS_D if across > 2.0 else BRASS
                        break
            if c:
                px(x, y, c)
    for k in range(spokes):                                   # rivets where spokes meet the rim
        sa = phase + k * 2 * math.pi / spokes
        px(cx + math.cos(sa) * (r - 3), cy + math.sin(sa) * (r - 3), MET_L)


def turn_arrow(cx, cy, r, turn, at, span=0.9):
    """Which way it goes: a dotted arc just off the teeth with a head on it."""
    rr = r + 12
    n = 14
    for i in range(n):
        if i % 2:
            continue
        a = at + turn * span * i / n
        px(cx + math.cos(a) * rr, cy + math.sin(a) * rr, ARROW, 0.75)
    a = at + turn * span
    hx, hy = cx + math.cos(a) * rr, cy + math.sin(a) * rr
    tx, ty = -math.sin(a) * turn, math.cos(a) * turn       # direction of travel
    nx, ny = math.cos(a), math.sin(a)
    for k in range(4):
        px(hx - tx * k + nx * k * 0.8, hy - ty * k + ny * k * 0.8, ARROW, 0.9)
        px(hx - tx * k - nx * k * 0.8, hy - ty * k - ny * k * 0.8, ARROW, 0.9)


def clock_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly > FLOOR:
            continue
        if lx > 300 + 4 * math.sin(ly * 0.3) and 292 <= ly < 306 + (lx - 300) * 0.4:
            continue                                         # east shelf, under the weight
        out.add((x, y))
    return out


def clock_furnish(ox, oy, m):
    X = lambda lx: ox + lx
    Y = lambda ly: oy + ly
    fl = Y(FLOOR)
    teeth(m, X(250), X(330), Y(110), 6)
    teeth(m, X(180), X(350), Y(300), 10)

    # the niches: a dark ring of cut rock round each wheel, so they read as set in
    for (_, cx, cy, r, *_rest) in WHEELS:
        for k in range(180):
            a = k * 2 * math.pi / 180
            x, y = X(cx) + math.cos(a) * (r + 12), Y(cy) + math.sin(a) * (r + 12)
            if (int(x), int(y)) not in m:
                continue
            px(x, y, CAVE_L, 0.8)

    for (_, cx, cy, r, n, sp, ph, _t) in WHEELS:
        wheel(X(cx), Y(cy), r, n, sp, ph)
    # iron arbors back into the rock: a bearing plate behind each boss
    for (_, cx, cy, r, *_rest) in WHEELS:
        ring(X(cx), Y(cy), 12, MET_D)

    # the weight: chain off C's arbor drum, down to an iron bob over the east shelf
    cx, cy = X(C[1]), Y(C[2])
    disc(cx, cy, 6, MET_D)
    chain(cx + 6, cy + 2, Y(286) - 22)
    wx = cx + 6
    rect(wx - 8, Y(286) - 22, wx + 9, Y(286) - 2, MET_D)
    rect(wx - 8, Y(286) - 22, wx + 9, Y(286) - 22, MET_L)
    rect(wx - 6, Y(286) - 14, wx + 7, Y(286) - 12, MET)

    # direction arrows, and the pinch at each mesh
    turn_arrow(X(A[1]), Y(A[2]), A[3], A[7], 0.6)
    turn_arrow(X(B[1]), Y(B[2]), B[3], B[7], 1.2)
    turn_arrow(X(C[1]), Y(C[2]), C[3], C[7], 0.3)
    turn_arrow(X(D[1]), Y(D[2]), D[3], D[7], 3.6)
    for p, q in ((A, B), (B, C), (B, D)):
        ux, uy = q[1] - p[1], q[2] - p[2]
        d = math.hypot(ux, uy)
        mx, my = X(p[1] + ux / d * (p[3] + 3)), Y(p[2] + uy / d * (p[3] + 3))
        for k in range(12):
            px(mx + (rnd() - 0.5) * 10, my + (rnd() - 0.3) * 12, pick([RED, RED_L, RED]), 0.85)
        glow(mx, my, 10, RED_L, 0.12)
    # what the A-B mesh has already had
    ux, uy = B[1] - A[1], B[2] - A[2]
    d = math.hypot(ux, uy)
    mx, my = X(A[1] + ux / d * (A[3] + 3)), Y(A[2] + uy / d * (A[3] + 3))
    rect(mx - 3, my - 2, mx + 3, my + 1, (99, 104, 101))
    for k in range(8):
        px(mx - 2 + k * 0.6, my + 3 + k * 4, RED, 0.8)            # down the rock under it

    # riders: on a spoke, on a top tooth, on the rim
    stand("Reaper", X(A[1] + 38), Y(A[2]) - 3, flip=True)       # on A's level spoke
    stand("WizBonecrown", X(B[1]) - 2, Y(B[2] - B[3] - 6))
    stand("Gaper", X(C[1] - 26), Y(C[2] - C[3] + 4) - 2)
    stand("Pyro", X(D[1]), Y(D[2] - D[3] - 6), flip=True)

    # the floor: the train's foot, scrap from the wheels, what they dropped
    stand("RiotBrute", X(196), fl, flip=True)
    stand("Minespider", X(262), fl)
    stand("WizDeepminer", X(316), Y(292), flip=True)              # on the east shelf
    corpse(X(160), fl)
    for k in range(10):                                          # broken teeth on the floor
        x = X(150 + rnd() * 160)
        rect(x, fl - 2, x + 2, fl - 1, pick([BRASS, BRASS_D, BRASS_L]))
    scrap_pile(X(276), fl, 26, 5, colors=(BRASS_D, MET_D, BRASS, ROCK_M))
    wheel(X(322), fl - 21, 14, 8, 4, 0.3)                        # a spare, leaned on the wall
    crate_g(X(300), fl, 12)
    crate_g(X(302), fl - 13, 10)
    stand("Ghast", X(236), Y(352), flip=True)                    # drifting in the hall
    glow(X(236), Y(342), 26, (150, 200, 170), 0.10)
    for lx in (230, 312):
        lamp(X(lx), ceil_at(m, X(lx), Y(140)) + 1, drop=8, bulb=LAMP, tint=LAMP, r=70, strength=0.15)
    lamp(X(206), ceil_at(m, X(206), Y(380)) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.12)
    # a ladder off the west ledge down onto A's rim, for the winders
    ladder(X(30) - 3, Y(212), Y(262), w=6, step=6)
    stand("Grenadier", X(40), Y(212))


ROOM = {
    "name": "THE CLOCKWORK", "w": 360, "h": 450,
    "shapes": [([("blob", 250, 352, 104, 72),            # the hall at the train's foot
                 ("blob", 286, 116, 44, 34),             # the roof pocket over C
                 ("blob", 112, 128, 30, 26),             # and over D
                 ("blob", 286, 272, 50, 22)], 0.08),     # the weight's bay
               ([("blob", A[1], A[2], A[3] + 13, A[3] + 13),
                 ("blob", B[1], B[2], B[3] + 13, B[3] + 13),
                 ("blob", C[1], C[2], C[3] + 13, C[3] + 13),
                 ("blob", D[1], D[2], D[3] + 13, D[3] + 13)], 0.015),
               ([("blob", 50, 196, 46, 22)], 0.1)],          # the west ledge
    "sockets": {"T1": ("T", 110, 112), "T2": ("T", 290, 92),
                "L1": ("L", 212, 20), "R1": ("R", 292, 30),
                "R2": ("R", FLOOR, 40), "B1": ("B", 236, 30)},
    "edit": clock_edit,
    "furnish": clock_furnish,
}


SHEET = {
    "seed": 73801,
    "callouts": [
        ("1 FOUR WHEELS IN MESH, TURNING", (230, -50), (250, 150)),
        ("2 RIDE A SPOKE UP", (-125, 470), (120, 330)),
        ("3 THE MESH PINCHES", (254, 470), (136, 280)),
        ("4 WEIGHT DRIVE", (370, 330), (262, 270)),
    ],
    "beats": [
        ("TEETH AND SPOKES CARRY YOU UP THE WALL, WHEEL TO WHEEL", (170, 180, 195)),
        ("SHOVE THEM OFF THEIR SPOKE INTO THE MESH, OR CUT THE WEIGHT", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
