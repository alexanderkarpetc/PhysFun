"""Small room S16 - THE SPINNER.

A round chamber with one long timber beam on an iron hub in its middle, turning - a
kinematic thing nobody switched off. The ledges are cut round the wall just outside its
reach: the high ones are safe, because whoever stands on them stands away from the hub;
on the low ones and the floor's middle, heads stick up into the circle and the beam
takes them. Two of them ride the beam itself, and get thrown off its end.

Nothing to switch. Ride it, stand where its tip passes and let it fling the room at you,
or put a blast into the hub and stop it where it stands.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402

CODE = "S16"

CH = (200, 200, 176, 172)
HUB = (200, 196)
ARM = 132                       # hub to beam tip
THICK = 8
ANGLE = 0.30                    # radians; the east end is down
FLOOR = 344
SWEEP = (200, 205, 215)
LEDGES = [(26, 146, 40, 16),    # west high (L2) - out of reach
          (374, 126, 48, 16),   # east high (R2) - out of reach
          (14, 212, 46, 14),    # west, hub height
          (388, 222, 42, 14),   # east, hub height
          (40, 316, 74, 16),    # west low (L1) - heads in the circle
          (360, 316, 74, 16),   # east low (R1)
          (200, 26, 46, 22),    # roof boss
          (136, 352, 26, 12),   # spoil against the bowl's sides
          (262, 354, 22, 14)]


def sp_edit(air, ox, oy):
    out = set()
    for (x, y) in air:
        lx, ly = x - ox, y - oy
        if ly >= FLOOR:
            continue
        if any(((lx - cx) / rx) ** 2 + ((ly - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in LEDGES):
            continue
        out.add((x, y))
    return out


def beam_canvas():
    """The spinner beam, upright on its own canvas: 268 x 10, hub at the centre."""
    n = 2 * ARM + 4
    rect(0, 1, n - 1, THICK, WOOD)
    rect(0, 1, n - 1, 1, WOOD_L)
    rect(0, THICK, n - 1, THICK, WOOD_D)
    for x in range(5, n - 5, 11):
        px(x, 3 + (x // 11) % 4, WOOD_D)
    for x in range(14, n - 10, 30):                          # iron bands
        rect(x, 0, x + 2, THICK + 1, MET_D)
        rect(x, 0, x + 2, 0, MET_L)
    for x0 in (0, n - 6):                                    # shod tips
        rect(x0, 0, x0 + 5, THICK + 1, MET)
        rect(x0, 0, x0 + 5, 0, MET_XL)


def beam_top(u):
    """World point on the beam's top face, `u` along it from the hub (local coords)."""
    ca, sa = math.cos(ANGLE), math.sin(ANGLE)
    t = THICK / 2 + 1
    return HUB[0] + u * ca + sa * t, HUB[1] + u * sa - ca * t


def sweep_circle(cx, cy, r):
    for i in range(0, 720, 2):
        if (i // 2) % 4 == 3:
            continue
        a = math.radians(i / 2)
        px(cx + math.cos(a) * r, cy + math.sin(a) * r, SWEEP, 0.5)
    for a0 in (math.radians(-60), math.radians(120)):        # which way it turns
        for k in range(10):
            a = a0 + k * 0.025
            px(cx + math.cos(a) * (r + 4), cy + math.sin(a) * (r + 4), SWEEP, 0.7)
        a = a0 + 0.25
        tx, ty = cx + math.cos(a) * (r + 4), cy + math.sin(a) * (r + 4)
        dx, dy = -math.sin(a), math.cos(a)
        for s in (-1, 1):
            line(tx, ty, tx - dx * 4 + s * math.cos(a) * 3, ty - dy * 4 + s * math.sin(a) * 3, SWEEP, 0.8)


def ghost_beam(cx, cy, angle, n=3):
    """Where the beam was a moment ago: faint after-images trailing its turn."""
    for k in range(1, n + 1):
        a = angle - k * 0.12
        for s in (-1, 1):
            for r in range(30, ARM, 2):
                px(cx + s * math.cos(a) * r, cy + s * math.sin(a) * r, WOOD_L, 0.3 / k)
                px(cx + s * math.cos(a) * r + 1, cy + s * math.sin(a) * r, WOOD, 0.2 / k)


def hub(cx, cy):
    gear(cx, cy, 15, teeth=10, c=MET_D, lit=MET, hub=MET_D)
    disc(cx, cy, 8, MET)
    ring(cx, cy, 8, MET_XL)
    disc(cx, cy, 3, MET_D)
    for i in range(6):
        a = i * math.pi / 3 + ANGLE
        px(cx + math.cos(a) * 6, cy + math.sin(a) * 6, MET_XL)


def flung_crate():
    crate_g(1, 11, 10)


def sp_furnish(ox, oy, m):
    teeth(m, ox + 40, ox + 360, oy + 120, 24)
    hx, hy = ox + HUB[0], oy + HUB[1]
    sweep_circle(hx, hy, ARM + 4)
    ghost_beam(hx, hy, ANGLE)

    # lamps tucked high, out of the circle
    for lx in (160, 240):
        lamp(ox + lx, ceil_at(m, ox + lx, oy + 80) + 1, drop=4, bulb=LAMP, tint=LAMP, r=80, strength=0.14)

    # the floor's middle, where the tip scrapes past: gouges, splinters, the last one
    fy = oy + FLOOR
    for i in range(-24, 25, 6):
        line(ox + 200 + i, fy, ox + 200 + i + 4, fy + 2, INK)
    scrap_pile(ox + 150, fy, 22, 4, colors=(WOOD_D, WOOD, MET_D, DIRT))
    corpse(ox + 238, fy)
    keg(ox + 268, fy)

    # the beam, its hub, and who is on it
    draw_rotated(2 * ARM + 4, THICK + 2, beam_canvas, hx, hy, ANGLE)
    hub(hx, hy)
    gx, gy = beam_top(-44)
    stand("Gaper", ox + gx, oy + gy)
    sx, sy = beam_top(96)
    stand("Minespider", ox + sx, oy + sy, flip=True)

    # something already thrown off the high end, and grit off the tip
    draw_rotated(14, 14, flung_crate, ox + 86, oy + 70, -0.6)
    for k in range(5):
        line(ox + 96 + k * 4, oy + 76 + k * 3, ox + 104 + k * 4, oy + 80 + k * 3, SWEEP, 0.25)
    tx, ty = beam_top(ARM)
    for _ in range(14):
        px(ox + tx + rnd() * 16, oy + ty + 6 + rnd() * 10, pick([WOOD_L, ROCK_L, DIRT_L]), 0.8)

    # the ring of ledges
    f = floor_at(m, ox + 54, oy + 112)
    stand("Grenadier", ox + 54, f)
    f = floor_at(m, ox + 340, oy + 96)
    stand("WizRamskull", ox + 340, f, flip=True)
    f = floor_at(m, ox + 40, oy + 186)
    crate_g(ox + 34, f, 10)
    crate_g(ox + 26, f, 8)
    f = floor_at(m, ox + 106, oy + 270)
    stand("RiotBrute", ox + 100, f)
    f = floor_at(m, ox + 296, oy + 270)
    stand("Sentinel", ox + 298, f, flip=True)
    f = floor_at(m, ox + 370, oy + 180)
    keg(ox + 366, f)


ROOM = {
    "name": "THE SPINNER", "w": 400, "h": 400,
    "shapes": [([("blob",) + CH], 0.06)],
    "sockets": {"T1": ("T", 120, 56), "T2": ("T", 284, 56),
                "L2": ("L", 130, 50), "R2": ("R", 110, 64),
                "L1": ("L", 300, 56), "R1": ("R", 300, 56)},
    "edit": sp_edit,
    "furnish": sp_furnish,
}


SHEET = {
    "seed": 71601,
    "callouts": [
        ("1 A BEAM ON A HUB, TURNING", (190, -50), (200, 196)),
        ("2 LOW LEDGES ARE IN ITS REACH", (-120, 420), (100, 290)),
        ("3 HIGH LEDGES ARE NOT", (300, 40), (344, 108)),
    ],
    "beats": [
        ("RIDE IT, OR STAND WHERE THE TIP PASSES AND LET IT SWEEP", (170, 180, 195)),
        ("TWO RIDE THE BEAM, TWO WAIT ON THE LOW LEDGES", F_MID),
    ],
}


def build():
    return room_sheet(ROOM, CODE, **SHEET)


if __name__ == "__main__":
    build()
