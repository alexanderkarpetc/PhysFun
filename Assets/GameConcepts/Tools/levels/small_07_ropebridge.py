"""Small room S07 - THE ROPE BRIDGE.

Two chambers either side of a chasm that splits the floor right down to a bed of
sharpened stakes. A plank bridge on two ropes crosses it, tied off to a post on each
lip and held up in the middle by one hanger rope off a ring bolt in the vault. The
west lip is higher than the east, so the bridge runs downhill. Enemies hold both ends
and one is on the planks. Cut a rope and the bridge, and whoever is on it, goes down.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S07"

WEST_FLOOR, EAST_FLOOR = 184, 204
BOTTOM = 330
NICHE_FLOOR = 122
BRIDGE = (172, WEST_FLOOR - 2, 294, EAST_FLOOR - 2)     # x0, y0, x1, y1
SAG = 16
ROPE = (150, 130, 96)
ROPE_D = (104, 88, 62)
BONE = (199, 190, 160)


def west_floor(lx):
    """Uneven floor, flat for the last stretch to the lip so the post has footing."""
    return WEST_FLOOR + (0 if lx > 140 else int(3 * math.sin(lx * 0.08) + 2 * math.sin(lx * 0.21)))


def east_floor(lx):
    return EAST_FLOOR + (0 if lx < 320 else int(3 * math.sin(lx * 0.06 + 1) + 2 * math.sin(lx * 0.19)))


def bridge_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if lx < 176 and ly >= west_floor(lx):
            continue
        if lx > 290 and ly >= east_floor(lx):
            continue
        if ly >= BOTTOM:
            continue
        if ly >= NICHE_FLOOR and ((lx - 470) / 92.0) ** 2 + ((ly - 134) / 14.0) ** 2 < 1:
            continue
        out.add((x, y))
    return out


def catenary(t):
    x0, y0, x1, y1 = BRIDGE
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + SAG * 4 * t * (1 - t)


def rope_bridge(ox, oy):
    """Planks on a sagging rope, seen edge-on, with the rope under them."""
    x0, _, x1, _ = BRIDGE
    n = int((x1 - x0) / 7)
    for i in range(n):
        ax, ay = catenary(i / n)
        rect(ox + ax, oy + ay, ox + ax + 5, oy + ay + 2, WOOD if i % 3 else WOOD_L)
        px(ox + ax, oy + ay + 2, WOOD_D)
    for i in range(x1 - x0 + 1):
        ax, ay = catenary(i / (x1 - x0))
        px(ox + ax, oy + ay + 3, ROPE_D)


def post(x, floor, side):
    """Tie-off post on a lip: a stake driven in, the rope wrapped round it."""
    rect(x - 1, floor - 12, x + 2, floor + 4, WOOD)
    rect(x - 1, floor - 12, x - 1, floor + 4, WOOD_L)
    for k in range(3):
        rect(x - 2, floor - 9 + k * 2, x + 3, floor - 9 + k * 2, ROPE)


def ring_bolt(x, y):
    ring(x, y + 3, 2.5, MET_L)
    rect(x, y - 2, x, y, MET_D)


def stake_bed(x0, x1, y):
    """Sharpened timber stakes in the chasm floor, leaning every way."""
    for x in range(int(x0), int(x1), 5):
        h = 8 + int(rnd() * 8)
        lean = (rnd() - 0.5) * 6
        line(x, y - 1, x + lean, y - h, WOOD_D)
        line(x + 1, y - 1, x + 1 + lean, y - h, WOOD)
        px(x + lean, y - h - 1, MET_XL)


def bones(x0, x1, y, n=30):
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        if chance(0.5):
            rect(x, y - 2, x + 3 + rnd() * 4, y - 2, BONE)
        else:
            px(x, y - 2 - rnd() * 2, BONE)


def hanging_wreck(x, y, length):
    """The last bridge, cut: planks hanging down the west wall from its old post."""
    for i in range(int(length / 7)):
        t = i * 7
        ax = x + math.sin(t * 0.07) * 2
        rect(ax - 2, y + t, ax, y + t + 5, WOOD if i % 3 else WOOD_L)
        px(ax + 1, y + t + 2, ROPE_D)
    rect(x - 1, y - 6, x + 1, y + 2, WOOD_D)


def wall_shelf(m, x, y, d, rx, ry):
    while (x, y) in m:
        x += d
    rock_blob(x - d * (rx // 3), y, rx, ry, rough=0.25)


def bridge_furnish(ox, oy, m):
    teeth(m, ox + 20, ox + 440, oy + 150, 26)
    for x, y, d, rx, ry in ((232, 240, -1, 14, 8), (232, 280, 1, 12, 7), (232, 214, 1, 10, 6),
                            (100, 120, -1, 12, 8), (300, 140, 1, 10, 6)):
        wall_shelf(m, ox + x, oy + y, d, rx, ry)

    # the bridge, its posts and the one hanger rope off the vault
    x0, y0, x1, y1 = BRIDGE
    post(ox + x0 - 6, oy + WEST_FLOOR, 1)
    post(ox + x1 + 6, oy + EAST_FLOOR, -1)
    line(ox + x0 - 5, oy + WEST_FLOOR - 8, ox + x0, oy + y0 + 3, ROPE)
    line(ox + x1 + 5, oy + EAST_FLOOR - 8, ox + x1, oy + y1 + 3, ROPE)
    rope_bridge(ox, oy)
    mx, my = catenary(0.5)
    top = ceil_at(m, ox + mx, oy + 140) + 1
    ring_bolt(ox + mx, top)
    for t in (0.3, 0.7):
        bx, by = catenary(t)
        line(ox + mx, top + 6, ox + bx + 2, oy + by, ROPE)
    lamp(ox + mx - 30, ceil_at(m, ox + mx - 30, oy + 140) + 1, drop=10, bulb=LAMP, tint=LAMP, r=70, strength=0.12)

    # the chasm: the last bridge down the west wall, stakes and what fell on them
    hanging_wreck(ox + 180, oy + WEST_FLOOR + 6, 64)
    bot = oy + BOTTOM
    stake_bed(ox + 194, ox + 276, bot)
    bones(ox + 190, ox + 280, bot, 34)
    corpse(ox + 214, bot, c=(110, 104, 92))
    scrap_pile(ox + 248, bot, 18, 4, colors=(WOOD_D, WOOD, ROCK_M))
    glow(ox + 232, bot - 20, 60, (170, 80, 60), 0.08)

    # west chamber
    wf = oy + WEST_FLOOR
    fl = lambda x: floor_at(m, ox + x, wf - 12)
    crate_g(ox + 30, fl(36))
    crate_g(ox + 34, fl(36) - 13, 10)
    keg(ox + 46, fl(50))
    lamp(ox + 110, ceil_at(m, ox + 110, wf - 10) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)
    stand("Reaper", ox + 120, fl(120))
    stand("Gaper", ox + 150, fl(150))
    stand("Pyro", ox + 74, fl(74))

    # on the planks
    gx, gy = catenary(0.42)
    stand("Gaper", ox + gx, oy + gy, flip=True)

    # east chamber and its niche
    ef = oy + EAST_FLOOR
    fe = lambda x: floor_at(m, ox + x, ef - 12)
    stand("RiotBrute", ox + 318, fe(318), flip=True)
    stand("WizMaskwraith", ox + 360, fe(360), flip=True)
    scrap_pile(ox + 392, fe(400), 30, 6, colors=(MET_D, DIRT, ROCK_M, WOOD_D))
    keg(ox + 428, fe(432))
    keg(ox + 437, fe(441))
    lamp(ox + 380, ceil_at(m, ox + 380, ef - 10) + 1, drop=6, bulb=LAMP, tint=LAMP, r=60, strength=0.14)
    stand("Grenadier", ox + 412, oy + NICHE_FLOOR, flip=True)


ROOM = {
    "name": "THE ROPE BRIDGE", "w": 460, "h": 360,
    "shapes": [([("blob", 96, 146, 98, 56),                    # west chamber
                 ("blob", 364, 160, 98, 64),                   # east chamber
                 ("blob", 232, 128, 76, 52)], 0.10),           # the vault over the chasm
               ([("tube", [(234, 160), (226, 250), (236, 322)], 50)], 0.08),   # the chasm
               ([("blob", 420, 106, 34, 18)], 0.12)],          # the east niche
    "sockets": {"T1": ("T", 70, 104), "T2": ("T", 300, 96),
                "L1": ("L", WEST_FLOOR, 14), "R1": ("R", EAST_FLOOR, 14),
                "R2": ("R", NICHE_FLOOR, 16), "B1": ("B", 232, 40)},
    "edit": bridge_edit,
    "furnish": bridge_furnish,
}


SHEET = {
    "seed": 70707,
    "callouts": [
        ("1 PLANKS ON TWO ROPES", (-120, 250), (172, 186)),
        ("2 ONE HANGER OFF THE VAULT", (250, -50), (233, 100)),
        ("3 STAKES AT THE BOTTOM", (290, 300), (262, 320)),
    ],
    "beats": [
        ("CUT A ROPE: THE BRIDGE AND WHO IS ON IT GO DOWN", (170, 180, 195)),
        ("BOTH LIPS HELD, A GAPER HALFWAY ACROSS", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
