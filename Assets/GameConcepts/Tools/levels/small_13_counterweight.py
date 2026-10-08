"""Small room S13 - THE COUNTERWEIGHT.

A tall oval shaft with one timber sheave hung off its roof. One rope runs over it: on
the west side a lift deck with two of them riding it, docked at the west shelf; on the
east side an iron counterweight, hauled right up under the roof. Straight under the
weight, on the shaft floor, is where the rest of them stand - next to the powder.

Cut the rope anywhere and both ends go: the deck drops down the shaft with its riders,
and the weight comes down on whoever is under it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S13"

ROPE = (150, 130, 96)
ROPE_D = (104, 88, 62)

SHAFT = (180, 228, 145, 196)
FLOOR = 398
WHEEL = (180, 74, 28)               # sheave centre and radius
DECK_Y, DECK_X0, DECK_X1 = 262, 118, 186
WEIGHT_Y = 112                      # top of the counterweight
# rock left standing in the oval: shelves you stand on, bulges that break the curve
SHELVES = [(52, 284, 66, 22),       # the dock shelf, level with the deck (L1)
           (318, 184, 42, 18),      # east shelf (R1)
           (322, 362, 40, 22),      # low east shelf (R2)
           (28, 150, 30, 24),       # bulges
           (342, 268, 26, 34),
           (40, 360, 30, 26),
           (44, 214, 30, 14),       # small west ledge under the lamp
           (96, 420, 40, 30)]       # mound by the floor hole


def cw_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR:
            continue
        if any(((lx - cx) / rx) ** 2 + ((ly - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in SHELVES):
            continue
        out.add((x, y))
    return out


def rope(pts, c=ROPE):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        line(ax, ay, bx, by, c)
        line(ax + 1, ay, bx + 1, by, ROPE_D, 0.6)


def sheave(cx, cy, r):
    """Timber sheave in an iron tyre, the rope lying in its top half."""
    disc(cx, cy, r, MET_D)
    disc(cx, cy, r - 2, WOOD_D)
    disc(cx, cy, r - 4, WOOD)
    for i in range(6):
        a = i * math.pi / 3 + 0.3
        line(cx + math.cos(a) * 4, cy + math.sin(a) * 4,
             cx + math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3), WOOD_D)
    for i in range(48):
        a = i * 2 * math.pi / 48
        if math.sin(a) < 0.15:
            px(cx + math.cos(a) * (r - 1), cy + math.sin(a) * (r - 1), MET_L)
    disc(cx, cy, 4, MET)
    disc(cx, cy, 1.6, MET_XL)
    for i in range(0, 61):                       # the rope over the top
        a = math.pi + i * math.pi / 60
        px(cx + math.cos(a) * (r + 1), cy + math.sin(a) * (r + 1), ROPE)


def hanger(cx, roof, cy):
    """Iron fork from a roof plate down to the axle."""
    rect(cx - 9, roof, cx + 9, roof + 3, MET_D)
    rect(cx - 9, roof + 3, cx + 9, roof + 3, MET)
    for bx in (cx - 6, cx + 6):
        px(bx, roof + 1, MET_XL)
    rect(cx - 2, roof + 4, cx + 2, cy, MET)
    rect(cx - 2, roof + 4, cx - 2, cy, MET_L)


def deck(x0, x1, y):
    """Lift deck: timber planks on two iron straps, bridle to one ring."""
    rect(x0, y, x1, y + 4, WOOD)
    rect(x0, y, x1, y, WOOD_L)
    rect(x0, y + 4, x1, y + 4, WOOD_D)
    for x in range(x0 + 7, x1, 8):
        px(x, y + 2, WOOD_D)
    for bx in (x0 + 2, x1 - 4):
        rect(bx, y - 1, bx + 2, y + 6, MET_D)
    for bx in (x0 + 14, x1 - 16):
        rect(bx, y + 5, bx + 2, y + 8, WOOD_D)


def counterweight(cx, y):
    """A cast iron block on a shackle: solid, and much heavier than it looks."""
    rect(cx - 1, y, cx + 1, y + 5, MET_L)
    ring(cx, y + 6, 2.5, MET_L)
    rect(cx - 6, y + 9, cx + 6, y + 11, MET)
    rect(cx - 12, y + 12, cx + 12, y + 46, MET_D)
    rect(cx - 12, y + 12, cx + 12, y + 12, MET_L)
    rect(cx - 12, y + 12, cx - 12, y + 46, MET)
    rect(cx + 12, y + 12, cx + 12, y + 46, INK)
    rect(cx - 12, y + 46, cx + 12, y + 46, INK)
    for yy in (y + 22, y + 34):
        rect(cx - 11, yy, cx + 11, yy, (40, 40, 42))
        rect(cx - 11, yy + 1, cx + 11, yy + 1, MET)
    for bx, by in ((cx - 9, y + 15), (cx + 8, y + 15), (cx - 9, y + 42), (cx + 8, y + 42)):
        px(bx, by, MET_XL)
    rect(cx - 7, y + 27, cx + 7, y + 30, HAZARD)
    for i in range(0, 15, 4):
        rect(cx - 7 + i, y + 27, cx - 6 + i, y + 30, INK)


def drop_guide(x, y0, y1, c=(200, 205, 215)):
    """Where something will fall: a faint dotted plumb line."""
    for y in range(int(y0), int(y1), 5):
        px(x, y, c, 0.35)
        px(x, y + 1, c, 0.2)


def cw_furnish(ox, oy, m):
    teeth(m, ox + 50, ox + 310, oy + 120, 22)
    wx, wy, wr = WHEEL
    roof = ceil_at(m, ox + wx, oy + wy) + 1
    rope_l, rope_r = ox + wx - wr - 1, ox + wx + wr + 1

    # the weight first, so the rope is drawn over its stirrup
    counterweight(rope_r, oy + WEIGHT_Y)
    rope([(rope_r, oy + wy), (rope_r, oy + WEIGHT_Y)])
    drop_guide(rope_r, oy + WEIGHT_Y + 50, oy + FLOOR - 26)

    # the deck: bridle to a ring, one rope up to the wheel
    dx0, dx1 = ox + DECK_X0, ox + DECK_X1
    ring_y = oy + DECK_Y - 48
    rope([(rope_l, oy + wy), (rope_l, ring_y)])
    ring(rope_l, ring_y + 2, 2.2, MET_L)
    rope([(rope_l, ring_y + 4), (dx0 + 3, oy + DECK_Y - 1)])
    rope([(rope_l, ring_y + 4), (dx1 - 3, oy + DECK_Y - 1)])
    deck(dx0, dx1, oy + DECK_Y)
    drop_guide(ox + 152, oy + DECK_Y + 12, oy + FLOOR - 4)

    hanger(ox + wx, roof, oy + wy)
    sheave(ox + wx, oy + wy, wr)
    rect(ox + wx - 2, roof + 4, ox + wx + 2, oy + wy - 5, MET)
    disc(ox + wx, oy + wy, 2, MET_XL)

    # lamps
    lamp(ox + 124, ceil_at(m, ox + 124, oy + 120) + 1, drop=10, bulb=LAMP, tint=LAMP, r=90, strength=0.15)
    lamp(ox + 256, ceil_at(m, ox + 256, oy + 120) + 1, drop=16, bulb=LAMP, tint=LAMP, r=80, strength=0.14)

    # the dock shelf: crates and a coil of spare rope, the riders' way off
    f = floor_at(m, ox + 60, oy + 240)
    crate_g(ox + 64, f)
    crate_g(ox + 78, f, 9)
    for k in range(3):
        ring(ox + 100, f - 4, 4 - k, ROPE if k % 2 else ROPE_D)
    stand("WizDeepminer", ox + 136, oy + DECK_Y)
    stand("Gaper", ox + 166, oy + DECK_Y, flip=True)

    # under the weight: the shaft floor, the powder, and who is standing on it
    fy = oy + FLOOR
    for i, kx in enumerate((222, 232, 227)):
        keg(ox + kx, fy - (11 if i == 2 else 0))
    scrap_pile(ox + 150, fy, 24, 5, colors=(MET_D, DIRT, ROCK_M, DIRT_D, WOOD_D))
    stand("RiotBrute", ox + 206, fy)
    stand("Pyro", ox + 186, fy)
    corpse(ox + 252, floor_at(m, ox + 252, oy + 380))

    # an idle hook off the roof, and a ladder between the east shelves
    hx = ox + 72
    chain(hx, ceil_at(m, hx, oy + 150) + 1, oy + 176)
    rect(hx - 1, oy + 176, hx + 2, oy + 178, MET)
    px(hx + 3, oy + 179, MET_L)
    px(hx + 3, oy + 180, MET_L)
    px(hx + 2, oy + 181, MET_L)
    ladder(ox + 290, oy + 168, floor_at(m, ox + 293, oy + 300), w=6, step=6, c=WOOD_L, rail=WOOD_D)
    fl = floor_at(m, ox + 56, oy + 180)
    stand("Minespider", ox + 52, fl)

    # east shelves
    f1 = floor_at(m, ox + 300, oy + 150)
    stand("Grenadier", ox + 300, f1, flip=True)
    lamp(ox + 312, ceil_at(m, ox + 312, f1 - 10) + 1, drop=4, bulb=LAMP, tint=LAMP, r=40, strength=0.13)
    f2 = floor_at(m, ox + 310, oy + 320)
    crate_g(ox + 316, f2)
    stand("WizHollowhood", ox + 296, f2, flip=True)


ROOM = {
    "name": "THE COUNTERWEIGHT", "w": 360, "h": 440,
    "shapes": [([("blob",) + SHAFT], 0.07)],
    "sockets": {"T1": ("T", 92, 84), "T2": ("T", 272, 84),
                "L1": ("L", DECK_Y, 44), "R1": ("R", 166, 52),
                "R2": ("R", 340, 60), "B1": ("B", 136, 48)},
    "edit": cw_edit,
    "furnish": cw_furnish,
}


SHEET = {
    "seed": 71301,
    "callouts": [
        ("1 ONE ROPE OVER ONE WHEEL", (190, -50), (180, 74)),
        ("2 CUT: THE DECK DROPS", (-130, 326), (150, 268)),
        ("3 ...AND THE WEIGHT LANDS HERE", (176, 460), (214, 386)),
    ],
    "beats": [
        ("TWO RIDE THE DECK, TWO STAND UNDER THE WEIGHT", (170, 180, 195)),
        ("THE KEGS UNDER IT MAKE THE LANDING WORSE", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
