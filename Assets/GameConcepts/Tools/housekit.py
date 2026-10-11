"""Built things inside small rooms: houses, huts, a keep, bulkheads - the parts S41-S46
share.

Everything here is drawn as what the player collides with (see the door rule in the
README): a wall is the planks or the courses themselves, a floor is a deck you stand on,
and a door is the slab that fills the gap. In the game a door is a Props.Door: E opens
it, and only the player does, so a house closes people in without anything having to lock.

There is no back wall in this engine, so the inside of a house is the cave's own air.
What makes it read as a room is the frame round it and a warm lamp in it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smallroomkit import *  # noqa: F403,E402

ROPE = (150, 130, 96)
ROPE_D = (104, 88, 62)
CLOTH = (96, 62, 66)
CLOTH_L = (130, 92, 96)
SLATE = (112, 66, 54)
SLATE_L = (150, 94, 72)
SOOT = (30, 26, 25)
EMBER = (226, 120, 54)
SACK = (148, 128, 92)
SACK_L = (178, 158, 116)
SACK_D = (108, 92, 66)


def rope(points, c=ROPE):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay, bx, by, c)
        line(ax + 1, ay, bx + 1, by, ROPE_D)


def cleat(x, y):
    """Where a rope is made fast: an iron horn bolted to the floor, the rope wound on it."""
    rect(x - 4, y - 2, x + 4, y - 1, MET_D)
    rect(x - 4, y - 2, x + 4, y - 2, MET_L)
    rect(x - 1, y - 5, x + 1, y - 3, MET)
    for k in range(3):
        rect(x - 3 + k, y - 5 + k, x + 3 - k, y - 5 + k, ROPE)


def pulley(x, y, r=3):
    disc(x, y, r, MET_D)
    ring(x, y, r, MET_L)
    px(x, y, MET_XL)


def plank_wall(x0, y0, x1, y1):
    """Upright boards side-on: the wall of a hut, burnable and cut by any blade."""
    rect(x0, y0, x1, y1, WOOD)
    rect(x0, y0, x0, y1, WOOD_L)
    rect(x1, y0, x1, y1, WOOD_D)
    for y in range(int(y0) + 6, int(y1), 9):
        rect(x0, y, x1, y, WOOD_D, 0.6)
    for _ in range(int(y1 - y0) // 4):
        px(x0 + rnd() * (x1 - x0 + 1), y0 + rnd() * (y1 - y0), WOOD_L, 0.3)


def post(x, y0, y1, w=3):
    rect(x, y0, x + w, y1, WOOD)
    rect(x, y0, x, y1, WOOD_L)
    rect(x + w, y0, x + w, y1, WOOD_D)


def deck(x0, x1, y, thick=4, joists=True):
    """A plank floor side-on, top at y: what everything upstairs stands on, and the
    one thing between the people upstairs and the people down."""
    rect(x0, y, x1, y + thick - 1, WOOD)
    rect(x0, y, x1, y, WOOD_L)
    rect(x0, y + thick - 1, x1, y + thick - 1, WOOD_D)
    for x in range(int(x0) + 3, int(x1), 11):
        px(x, y + 1, WOOD_D)
    if joists:
        for x in range(int(x0) + 4, int(x1) - 2, 22):
            rect(x, y + thick, x + 2, y + thick + 2, WOOD_D)


def flap_door(x, top, h=30, w=4, swung=0):
    """A plank leaf on a pin at the lintel, filling the doorway. Shut, it is a slab
    with a diagonal brace (the brace is what says door and not more wall). `swung`
    draws it pushed open by that many pixels at the foot."""
    rect(x - 2, top - 3, x + w + 2, top - 1, WOOD_D)
    rect(x - 2, top - 3, x + w + 2, top - 3, WOOD_L)
    pin = (x + w // 2, top - 1)
    disc(pin[0], pin[1], 1, MET_XL)
    if swung:
        line(pin[0], pin[1] + 1, pin[0] + swung, top + h - 2, WOOD)
        line(pin[0] - 1, pin[1] + 1, pin[0] + swung - 1, top + h - 2, WOOD_D)
        line(pin[0] + 1, pin[1] + 1, pin[0] + swung + 1, top + h - 2, WOOD_L)
        return
    rect(x, top, x + w, top + h - 1, WOOD_D)
    rect(x, top, x + w, top + 1, WOOD)
    rect(x, top + h - 2, x + w, top + h - 1, WOOD)
    for k in range(h - 4):
        px(x + (k * (w + 1)) // (h - 4), top + 2 + k, WOOD_L)
    px(x + w, top + h // 2, MET_XL)


def trapdoor(x0, x1, y, open_=False):
    """A flap in a deck: hinged at its west end, shut flush with the floor or stood up."""
    disc(x0, y + 1, 1, MET_XL)
    if open_:
        rect(x0, y - (x1 - x0), x0 + 2, y, WOOD)
        rect(x0, y - (x1 - x0), x0, y, WOOD_L)
        return
    rect(x0, y, x1, y + 2, WOOD)
    rect(x0, y, x1, y, WOOD_L)
    line(x0 + 2, y + 2, x1 - 2, y, WOOD_D)


def window(x0, y0, x1, y1, shutter=False):
    """A hole in a wall with a sill under it. Open, it is a sight line both ways; a
    shutter is a slab on the outside that fills it."""
    rect(x0, y0, x1, y1, CAVE)
    rect(x0 - 1, y1 + 1, x1 + 1, y1 + 2, STONE_L)
    if shutter:
        rect(x0, y0, x1, y1, WOOD_D)
        for y in range(int(y0) + 2, int(y1), 3):
            rect(x0, y, x1, y, WOOD)


def ladder_up(x, y0, y1):
    ladder(x - 3, y0, y1, w=6, step=6, c=WOOD_L, rail=WOOD_D)


def pitched_roof(x0, x1, eave, ridge_h, c=SLATE, lit=SLATE_L, thick=6):
    """Two pitches over a house, eave at y = eave, ridge ridge_h higher, overhanging."""
    cx = (x0 + x1) / 2.0
    half = (x1 - x0) / 2.0
    for x in range(int(x0) - 4, int(x1) + 5):
        t = min(abs(x - cx) / half, 1.08)
        top = eave - ridge_h * (1 - t)
        for d in range(thick):
            px(x, top + d, lit if d == 0 else c if (x // 4 + d) % 3 else SOOT)


def shed_roof(x0, x1, y_hi, y_lo, thick=4):
    """A lean-to: one pitch, high end west."""
    for x in range(int(x0) - 3, int(x1) + 4):
        t = (x - x0) / float(x1 - x0)
        top = y_hi + (y_lo - y_hi) * t
        for d in range(thick):
            px(x, top + d, WOOD_L if d == 0 else WOOD if d < thick - 1 else WOOD_D)


def stove(x, floor, flue_to=None):
    """Iron stove with a fire in it and a flue up through whatever is overhead."""
    rect(x, floor - 12, x + 12, floor - 1, MET_D)
    rect(x, floor - 12, x + 12, floor - 12, MET_L)
    rect(x + 3, floor - 8, x + 9, floor - 3, SOOT)
    rect(x + 4, floor - 5, x + 8, floor - 3, EMBER)
    glow(x + 6, floor - 5, 26, F_MID, 0.22)
    if flue_to is not None:
        rect(x + 4, flue_to, x + 7, floor - 13, MET_D)
        rect(x + 4, flue_to, x + 4, floor - 13, MET_L)


def bunk(x, floor, tiers=2, w=26):
    for t in range(tiers):
        y = floor - 4 - t * 16
        rect(x, y, x + w, y + 2, WOOD)
        rect(x + 1, y - 2, x + w - 1, y - 1, CLOTH)
        rect(x + 1, y - 2, x + w - 1, y - 2, CLOTH_L)
    post(x, floor - 4 - (tiers - 1) * 16 - 6, floor - 1, 1)
    post(x + w - 1, floor - 4 - (tiers - 1) * 16 - 6, floor - 1, 1)


def table(x, floor, w=18):
    rect(x, floor - 9, x + w, floor - 8, WOOD_L)
    rect(x + 1, floor - 7, x + w - 1, floor - 7, WOOD_D)
    rect(x + 1, floor - 7, x + 2, floor - 1, WOOD_D)
    rect(x + w - 2, floor - 7, x + w - 1, floor - 1, WOOD_D)


def stool(x, floor):
    rect(x, floor - 6, x + 5, floor - 5, WOOD)
    rect(x, floor - 4, x, floor - 1, WOOD_D)
    rect(x + 5, floor - 4, x + 5, floor - 1, WOOD_D)


def sack(x, floor, w=10):
    rect(x + 1, floor - 7, x + w - 1, floor - 1, SACK)
    rect(x, floor - 5, x + w, floor - 2, SACK)
    rect(x + 1, floor - 7, x + w - 1, floor - 7, SACK_L)
    rect(x + 1, floor - 1, x + w - 1, floor - 1, SACK_D)
    rect(x + w // 2 - 1, floor - 9, x + w // 2 + 1, floor - 8, SACK_D)


def shelf(x, y, w=20, n=4):
    rect(x, y, x + w, y + 1, WOOD)
    rect(x, y + 2, x + 1, y + 4, WOOD_D)
    for k in range(n):
        rect(x + 2 + k * 5, y - 4, x + 4 + k * 5, y - 1, pick([MET_L, RED, GREEN, DIRT_L, STONE]))


def warm_lamp(x, y, drop=6, r=44, strength=0.16):
    lamp(x, y, drop=drop, bulb=LAMP, tint=LAMP, r=r, strength=strength)


def interior(x0, y0, x1, y1, a=0.10):
    """Lamplight shut in by walls: a faint warm wash over the inside of a room, so a
    house reads as rooms and not as a frame stood in the cave."""
    rect(x0, y0, x1, y1, (120, 84, 50), a)


def stone_slab(x0, x1, y, thick=5):
    """A stone floor in a masonry building."""
    masonry(x0, y, x1, y + thick - 1, course=thick)


def arrow_slit(x, y, w, h=9):
    """A narrow cut through a stone wall: you see out of it, and are shot through it."""
    rect(x, y, x + w, y + h, CAVE)
    rect(x, y + h + 1, x + w, y + h + 1, STONE_L)
