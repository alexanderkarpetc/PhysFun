"""Room props, part 2: the machines and the cargo they move.

The crane, the magnet and what it carries from S12 and S20; the gas bottles of S25; the
cage lift and its brake from S18; S19's stamp and S20's swing jaw; the wheels that turn -
S22's sprocket, S21's table and crank, the windlasses of S23/S27/S28; S26's idol in the
three pieces it breaks into; S27's trebuchet; S24's scales; S22's hooks and what hangs on
them. Built by `roomprops.py`; read its docstring for what the entries mean.

Things that turn round an axle (sprocket, reel, crank, windlass drum) are lit from their
own centre, not from the top left, and keep their bore open, so they read the same at
any angle (see `wheels.py`). The idol is drawn once as the concept's 72x200 figure and
cut along the two cracks, so the three pieces stack back into it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from mineprops import BAYER  # noqa: E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402
from roomprops_hung import (eye, ball, BRONZE_RAMP, BONE_RAMP, STONE_RAMP,  # noqa: E402
                            BONE_D, BONE, BONE_L, STONE_D, STONE, STONE_M, STONE_L,
                            COAL_D, COAL, EMBER, RUST_RAMP, SACK_RAMP)

BRONZE_D, BRONZE, BRONZE_M, BRONZE_L = BRONZE_RAMP

TITLE = "MACHINES AND CARGO"
SEED = 9300

COP_D, COP, COP_L = (96, 56, 38), (140, 84, 52), (176, 112, 66)
PAINT_D = (88, 44, 42)
ROPE_L, ROPE_D = (150, 132, 96), (100, 82, 56)
MEAT_XD, MEAT_D, MEAT, MEAT_L = (52, 26, 26), (78, 36, 34), (112, 50, 46), (136, 66, 58)
FAT, FAT_D = (164, 144, 118), (128, 108, 86)

COP_RAMP = (COP_D, COP, COP_L)
RED_RAMP = (PAINT_D, PAINT_R, PAINT_RL)
POLISH = (IRON, IRON_M, IRON_L, IRON_XL)
MEAT_RAMP = (MEAT_D, MEAT, MEAT_L)


def ln4(x0, y0, x1, y1, c):
    """A line that steps in x or in y, never both, so a 1px stroke is still one body.
    `c` is a colour or a function (x, y) -> colour."""
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x1 >= x0 else -1), (1 if y1 >= y0 else -1)
    ix = iy = 0
    x, y = x0, y0
    while True:
        P(x, y, c(x, y) if callable(c) else c)
        if ix >= dx and iy >= dy:
            return
        if iy >= dy or (ix < dx and (0.5 + ix) / max(dx, 1) < (0.5 + iy) / max(dy, 1)):
            x += sx
            ix += 1
        else:
            y += sy
            iy += 1


def bore(cx, cy, r=1.0):
    """Key out an axle bore round a centre given in pixel indices."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if math.hypot(x - cx, y - cy) <= r + 0.01:
                hole(x, y)


def rope_wound(x, y, cx, cy):
    """Rope turns on a drum face, seen end-on: concentric strands."""
    d = math.hypot(x - cx, y - cy)
    k = int(d * 1.6) % 3
    return (ROPE_L, SACK_L, ROPE_D)[k]


# ═══════════════════════════════════════════════════════════════════════════
#  CRANE AND CARGO
# ═══════════════════════════════════════════════════════════════════════════
def lifting_magnet():
    """S12's lifting magnet: a flat iron pot, the copper coil band showing through the
    casing, the pole face under it and a forged eye on the yoke. Live, it takes anything
    iron off the floor - drums, girders, a Sentinel."""
    eye(23.5, 0, 3.0)
    for y in range(6, 9):                                   # the yoke, flaring to the pot
        hw = 4 + (y - 6) * 2
        for x in range(24 - hw, 25 + hw):
            dshade(x, y, 0.8 - 0.5 * (x - 24 + hw) / (2 * hw + 1), IRON_RAMP)
    for y in range(9, 17):                                  # the pot
        for x in range(2, 47):
            dshade(x, y, 0.62 - 0.45 * (x - 2) / 44 - 0.25 * (y - 9) / 8, IRON_RAMP)
    R(3, 9, 45, 9, IRON_L)
    hole(2, 9)
    hole(46, 9)
    R(3, 10, 45, 10, IRON_M)
    for y in range(11, 15):                                 # coil band: the turns run round
        for x in range(4, 45):                              # it, so side-on they lie flat
            t = (0.95, 0.55, 0.75, 0.3)[y - 11] - 0.3 * (x - 4) / 40
            dshade(x, y, t, COP_RAMP)
    for x in (4, 13, 24, 35, 44):                           # casing ribs over the coil
        R(x, 10, x, 15, IRON_D)
        P(x, 10, IRON_M)
    for y in range(17, 19):                                 # pole face, wider than the pot
        for x in range(0, 49):
            dshade(x, y, 0.7 - 0.5 * x / 48 - 0.2 * (y - 17), IRON_RAMP)
    R(0, 17, 48, 17, IRON_M)
    R(1, 19, 47, 19, IRON_D)
    R(18, 18, 30, 18, IRON_L)                               # the bright polished pole
    R(41, 7, 44, 8, IRON_D)                                 # terminal box for the cable
    P(41, 7, IRON_M)
    grime(0, 6, 48, 19, 60, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def crane_trolley():
    """S12's crab: two flanged wheels on top that ride the runway's bottom flange, the side
    plates, the rope drum between them and the hanger eye the block hangs from."""
    for x0 in (4, 19):                                      # hanger straps, axle to frame
        R(x0, 3, x0 + 2, 8, IRON)
        R(x0 + 2, 3, x0 + 2, 8, IRON_D)
    for wx in (5.5, 20.5):                                  # flanged wheels
        for y in range(0, 8):
            for x in range(int(wx) - 4, int(wx) + 5):
                d = math.hypot(x - wx, y - 3.5)
                if d <= 3.6:
                    t = 0.05 if d > 2.9 else 0.8 - 0.12 * d - 0.2 * (x - wx + y - 3.5) / 4
                    dshade(x, y, t, IRON_RAMP)
        P(int(wx), 3, IRON_XL)
        P(int(wx) + 1, 4, IRON_D)
    for y in range(8, 13):                                  # frame
        for x in range(0, 27):
            dshade(x, y, 0.6 - 0.4 * x / 26 - 0.15 * (y - 8) / 4, IRON_RAMP)
    R(0, 8, 26, 8, IRON_L)
    R(1, 12, 26, 12, IRON_D)
    for y in range(9, 12):                                  # rope drum, seen through the frame
        for x in range(4, 23):
            dshade(x, y, 0.8 - 0.3 * (y - 9), (ROPE_D, SACK, ROPE_L))
        for x in range(4 + y % 2, 23, 3):
            P(x, y, ROPE_D)
    R(3, 9, 3, 11, IRON_D)
    R(23, 9, 23, 11, IRON_D)
    R(11, 13, 15, 13, IRON_M)                               # clevis to the eye
    eye(12.5, 12, 2.4)
    grime(0, 4, 26, 13, 26, (RUST, RUST_D), on=IRON_RAMP)


def hook_block():
    """A hook block (S12, S20, S21, S28): eye on top, the sheave pinned between its cheek
    plates, and the hook under it, point up, open to the right. The throat is three wide:
    the outline pass closes anything narrower."""
    eye(3.5, 0, 2.5)
    tpl(0, 5, [
        ".LLMMMMD.",
        ".LMaaMMD.",
        ".LaeaMMD.",
        ".MMaMMDD.",
        "..DDDDD..",
        "...LD....",
        "...LD....",
        "...LD...L",
        "...LD...M",
        "...LMMMMD",
        "....DDDD.",
    ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D, 'a': IRON, 'e': IRON_XL})
    grime(1, 5, 7, 8, 5, (RUST, RUST_D), on=(IRON_M, IRON))


def _girder(w, holes):
    """A steel joist side-on: flanges, the web between, stiffeners, and the bolt holes
    through the web keyed out - for a rope or a hook - never through a flange."""
    for x in range(w):
        P(x, 0, IRON_L)
        P(x, 1, IRON_M)
        for y in (2, 3):
            dshade(x, y, 0.25 - 0.1 * (y - 2), IRON_RAMP)
        P(x, 4, IRON)
        P(x, 5, IRON_D)
    for x in range(7, w - 6, 7):                            # stiffeners
        if all(abs(x - hx) > 1 for hx in holes):
            R(x, 2, x, 3, IRON)
            P(x + 1, 2, IRON_D)
    R(0, 0, 0, 5, IRON_M)                                   # sawn ends
    R(w - 1, 0, w - 1, 5, IRON_D)
    grime(0, 0, w - 1, 5, w // 2, (RUST, RUST_D, RUST_L), on=IRON_RAMP)
    for x in holes:
        hole(x, 2)
        hole(x, 3)
        P(x - 1, 2, IRON_D)


def girder_long():
    """S12's girder, the one the magnet still has hold of."""
    _girder(63, (3, 17, 31, 45, 59))


def girder_short():
    """S20's scrap girder."""
    _girder(41, (3, 20, 37))


def steel_plate():
    """A plate off the scrap pile: flat, riveted along its length, one corner bent."""
    for y in range(0, 5):
        for x in range(0, 30):
            dshade(x, y, 0.7 - 0.25 * x / 29 - 0.4 * y / 4, IRON_RAMP)
    R(0, 0, 26, 0, IRON_L)
    R(0, 4, 29, 4, IRON_D)
    for x in (3, 10, 17, 24):
        P(x, 2, IRON_XL)
        P(x + 1, 3, IRON_D)
    hole(29, 0)                                             # the bent corner
    hole(28, 0)
    P(27, 0, IRON_M)
    P(29, 1, IRON_D)
    grime(0, 0, 29, 4, 22, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def cable_reel():
    """S12's cable reel, end-on. It rolls, so it is lit from its own middle: plank
    flange, iron tyre, bolt ring and the axle eye open through it."""
    cx = cy = 8.0
    for y in range(17):
        for x in range(17):
            d = math.hypot(x - cx, y - cy)
            if d > 8.3:
                continue
            if d > 7.2:
                P(x, y, IRON_D if d > 7.8 else IRON)        # iron tyre
                continue
            dshade(x, y, 0.75 - 0.5 * d / 7.2, TIM_RAMP)
    for k in range(4):                                      # plank seams, four ways round
        a = k * math.pi / 4
        for s in range(3, 8):
            for sgn in (-1, 1):
                x = int(round(cx + sgn * math.cos(a) * s))
                y = int(round(cy + sgn * math.sin(a) * s))
                P(x, y, TIM_D)
    for k in range(6):                                      # bolt ring
        a = k * math.pi / 3 + 0.5
        P(int(round(cx + math.cos(a) * 5.0)), int(round(cy + math.sin(a) * 5.0)), IRON_L)
    for y in range(4, 13):                                  # washer
        for x in range(4, 13):
            d = math.hypot(x - cx, y - cy)
            if d <= 2.6:
                P(x, y, IRON_M if d > 1.8 else IRON_L)
    bore(cx, cy, 1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  GAS ROOM
# ═══════════════════════════════════════════════════════════════════════════
def _bottle(c):
    """S25's bottle stood up: guard ring and brass valve on top, domed shoulder, the pale
    stencil band, the body lit down its left side, a dark foot ring."""
    ramp = (tuple(int(v * 0.55) for v in c), tuple(int(v * 0.8) for v in c), c,
            tuple(min(255, v + 30) for v in c))
    R(1, 0, 5, 0, IRON_M)                                   # the guard ring, edge-on
    P(1, 0, IRON_L)
    P(1, 1, IRON_M)
    P(5, 1, IRON_D)
    R(2, 1, 4, 3, BRONZE_M)                                 # valve
    P(2, 1, BRONZE_L)
    P(4, 2, BRONZE)
    P(5, 2, BRONZE_D)                                       # outlet
    R(2, 4, 4, 4, IRON)                                     # neck ring
    rows = [(5, 2, 4), (6, 1, 5), (7, 1, 5)]                # dome
    for y, a, b in rows:
        for x in range(a, b + 1):
            dshade(x, y, 0.9 - 0.25 * (x - a), ramp)
    for y in range(8, 38):
        for x in range(0, 7):
            dshade(x, y, 0.95 - 0.16 * x - 0.004 * y, ramp)
    for y in (13, 14):                                      # stencil band
        for x in range(0, 7):
            dshade(x, y, 0.9 - 0.12 * x, ((128, 122, 104), (156, 150, 128), (176, 170, 150)))
    for x in (2, 4):                                        # stencil marks
        P(x, 14, ramp[0])
    R(0, 36, 6, 36, IRON)
    R(0, 37, 6, 37, IRON_D)
    P(0, 36, IRON_M)
    grime(0, 5, 6, 35, 14, (ramp[0], RUST_D, RUST), on=ramp)


def gas_bottle():
    _bottle((70, 84, 96))


def gas_bottle_red():
    _bottle((110, 58, 50))


def gas_bottle_ochre():
    _bottle((128, 112, 60))


def gas_bottle_green():
    _bottle((78, 96, 70))


def bottle_trolley():
    """S25's bottle trolley: a flat iron deck, a stop at each end so a bottle laid on it
    stays, two wheels under it."""
    for y in (3, 4):
        for x in range(0, 27):
            dshade(x, y, 0.7 - 0.3 * x / 26 - 0.35 * (y - 3), IRON_RAMP)
    R(0, 3, 26, 3, IRON_M)
    for x0 in (0, 25):                                      # end stops
        R(x0, 1, x0 + 1, 2, IRON)
        P(x0, 1, IRON_L)
        P(x0 + 1, 2, IRON_D)
    R(0, 0, 1, 0, TIM_L)                                    # a stub of push handle
    for wx in (4.5, 21.5):
        R(int(wx) - 1, 5, int(wx) + 1, 5, IRON_D)           # axle box
        for y in range(4, 8):
            for x in range(int(wx) - 3, int(wx) + 4):
                d = math.hypot(x - wx, y - 5.5)
                if d <= 2.4:
                    P(x, y, IRON_D if d > 1.5 else IRON_M)
        P(int(wx), 5, IRON_L)
    grime(0, 1, 26, 4, 10, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  LIFTS AND BRAKES
# ═══════════════════════════════════════════════════════════════════════════
def cage_car():
    """S18's cage: eye and bonnet straps on top, a roof plate, round bars with gaps and a
    rung across them, a floor. Every bar collides and a shot goes through between them."""
    eye(13.5, 0, 2.6)
    R(13, 5, 15, 5, IRON_M)
    for k in range(2):                                      # bonnet straps
        ln4(2 + k, 9, 13 + k, 5, IRON_M if k == 0 else IRON)
        ln4(26 - k, 9, 15 - k, 5, IRON if k == 0 else IRON_D)
    for y in (9, 10, 11):                                   # roof
        for x in range(0, 29):
            dshade(x, y, 0.75 - 0.4 * x / 28 - 0.25 * (y - 9), IRON_RAMP)
    R(0, 9, 28, 9, IRON_L)
    for x in range(0, 29, 4):                               # bars
        for y in range(12, 37):
            P(x, y, IRON_L if x == 0 else IRON_D if x == 28 else IRON_M if x < 14 else IRON)
        P(x, 12, IRON_D)
    R(1, 24, 27, 24, IRON_D)                                # rung
    R(1, 23, 27, 23, IRON)
    for y in (37, 38, 39):                                  # floor
        for x in range(0, 29):
            dshade(x, y, 0.6 - 0.3 * x / 28 - 0.3 * (y - 37), IRON_RAMP)
    R(0, 37, 28, 37, IRON_M)
    R(1, 39, 27, 39, IRON_D)
    for x in (2, 26):
        P(x, 10, IRON_XL)
        P(x, 38, IRON_L)
    grime(0, 9, 28, 39, 40, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def brake_lever():
    """S18's band-brake lever: a squared timber with a striped iron weight on its free end
    and an iron boss at the pin end, the pivot bore open through it."""
    for y in range(4, 9):                                   # the lever
        for x in range(11, 42):
            dshade(x, y, 0.95 - 0.8 * (y - 4) / 4, TIM_RAMP)
    for _ in range(6):
        x = 13 + int(rnd() * 24)
        R(x, 6 + int(rnd() * 2), x + 1 + int(rnd() * 2), 6 + int(rnd() * 2), TIM_D)
    R(17, 4, 18, 8, IRON_D)                                 # strap round it
    P(17, 4, IRON_M)
    for y in range(1, 12):                                  # the weight
        for x in range(1, 13):
            dshade(x, y, 0.8 - 0.5 * x / 12 - 0.3 * y / 11, IRON_RAMP)
    stripes(2, 4, 11, 9, 2)
    R(1, 1, 12, 1, IRON_L)
    R(1, 2, 12, 2, IRON_M)
    R(1, 11, 12, 11, IRON_D)
    R(12, 1, 12, 11, IRON_D)
    R(1, 10, 11, 10, IRON)
    for y in range(2, 11):                                  # the pin boss, round the bore
        for x in range(37, 45):
            d = math.hypot(x - 40.5, y - 6.0)
            if d <= 3.9:
                dshade(x, y, 0.8 - 0.25 * (x - 37) / 7 - 0.3 * (y - 2) / 8, IRON_RAMP)
    bore(40.5, 6.0, 1.3)
    grime(1, 1, 44, 11, 30, (RUST, RUST_D), on=IRON_RAMP)


def stamp():
    """One of S19's stamps: the stem, the tappet collar the cam lifts it by, and the head
    and shoe at the bottom - which is what comes down on whatever is under it."""
    R(5, 1, 7, 1, IRON_M)                                   # stem cap
    for y in range(2, 60):                                  # stem
        P(5, y, IRON_L)
        P(6, y, IRON_M)
        P(7, y, IRON_D)
    for y in (20, 40):
        P(6, y, IRON)
    for y in range(13, 18):                                 # tappet collar
        for x in range(2, 11):
            dshade(x, y, 0.85 - 0.5 * (x - 2) / 8 - 0.2 * (y - 13) / 4, IRON_RAMP)
    R(2, 13, 10, 13, IRON_L)
    R(2, 17, 10, 17, IRON_D)
    R(4, 15, 4, 15, IRON_XL)                                # the gib key
    for y in range(57, 60):                                 # boss where stem meets head
        R(4, y, 8, y, IRON_M)
        P(8, y, IRON_D)
        P(4, y, IRON_L)
    for y in range(60, 78):                                 # head and shoe
        inset = 1 if y >= 76 else 0
        for x in range(0 + inset, 13 - inset):
            base = 0.8 - 0.65 * x / 12
            if y >= 72:                                     # the shoe, darker, worn
                base -= 0.25
            dshade(x, y, base, IRON_RAMP)
    R(0, 60, 12, 60, IRON_XL)
    R(0, 61, 12, 61, IRON_L)
    R(0, 66, 12, 67, IRON_D)                                # the band on the head
    R(0, 66, 0, 67, IRON_M)
    R(0, 71, 12, 71, INK)                                   # head / shoe joint
    R(1, 77, 11, 77, IRON_D)
    grime(0, 1, 12, 77, 50, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def swing_jaw():
    """S20's swing jaw: a thick plate on a pivot boss at the top, its crushing face (the
    left) cut into deep ridges, plain and darker behind."""
    for y in range(7, 75):                                  # the plate
        w = 7 if y < 66 else 6 if y < 71 else 5
        for x in range(1, w):
            dshade(x, y, 0.45 - 0.35 * (x - 1) / 5 - 0.1 * (y - 7) / 67, IRON_RAMP)
    for y in range(9, 72):                                  # the ridges across the face
        k = (y - 9) % 4
        if k == 0:
            R(0, y, 3, y, IRON_L)
            P(0, y, IRON_XL)
        elif k == 1:
            R(0, y, 3, y, IRON_M)
            P(4, y, IRON)
        elif k == 2:
            R(1, y, 3, y, IRON_D)
    R(5, 7, 5, 73, IRON_D)                                  # the back's edge
    R(1, 74, 4, 74, IRON_D)
    for y in range(0, 9):                                   # pivot boss
        for x in range(0, 7):
            d = math.hypot(x - 3, y - 3.5)
            if d <= 3.6:
                dshade(x, y, 0.85 - 0.6 * d / 3.6, IRON_RAMP)
    bore(3, 3.5, 1.2)
    grime(0, 7, 6, 74, 18, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  WHEELS
# ═══════════════════════════════════════════════════════════════════════════
def sprocket():
    """S22's chain sprocket: twelve teeth round a rim, five spokes, a hub, the bore open.
    It turns all the time, so it is lit from its middle and every feature repeats."""
    c = 18.5
    for y in range(38):
        for x in range(38):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            if d > 18.9:
                continue
            if d > 15.6:                                    # teeth
                k = round(a / (math.pi / 6))
                off = abs(a - k * math.pi / 6) * d
                if off <= 2.1 - 0.55 * (d - 15.6):
                    P(x, y, IRON_M if d < 17.4 else IRON_L)
                continue
            if d > 12.4:                                    # rim
                dshade(x, y, 0.15 + 0.5 * (1 - abs(d - 14.2) / 1.8), IRON_RAMP)
                continue
            if d > 4.6:                                     # spokes, open between
                best = min(abs(math.sin(a - (k * 2 * math.pi / 5 + 0.3))) * d
                           for k in range(5) if math.cos(a - (k * 2 * math.pi / 5 + 0.3)) > 0)
                if best <= 1.25:
                    dshade(x, y, 0.55 - 0.25 * (d - 4.6) / 8, IRON_RAMP)
                continue
            dshade(x, y, 0.85 - 0.5 * abs(d - 3.4) / 1.6, POLISH)   # hub
    for y in range(38):                                     # inner edge of the rim
        for x in range(38):
            if 12.4 < math.hypot(x - c, y - c) <= 13.2 and AT(x, y) != KEY:
                P(x, y, IRON_D)
    bore(c, c, 1.8)
    grime(0, 0, 37, 37, 40, (RUST, RUST_D), on=IRON_RAMP)


def turntable():
    """S21's turntable deck side-on: the rail on a timber deck on an iron girder, a red
    latch at each end that holds the tub, and the kingpin boss under the middle with its
    bore open."""
    for y in range(4, 10):                                  # kingpin boss
        for x in range(39, 50):
            d = math.hypot(x - 44, y - 6.5)
            if d <= 3.6:
                dshade(x, y, 0.8 - 0.6 * (d / 3.6) * (0.5 + 0.5 * (x - 39) / 10), IRON_RAMP)
    for x in range(4, 85):                                  # rail
        P(x, 1, IRON_XL if x % 11 else IRON_L)
        P(x, 2, IRON_M)
    for y in (3, 4, 5):                                     # deck
        for x in range(2, 87):
            dshade(x, y, 0.9 - 0.3 * (y - 3), TIM_RAMP)
    for x in range(6, 84, 7):                               # tie ends
        R(x, 4, x + 1, 5, TIM_D)
    for y in (6, 7):                                        # girder
        for x in range(1, 88):
            dshade(x, y, 0.45 - 0.3 * (y - 6) - 0.15 * x / 87, IRON_RAMP)
    for x in range(5, 85, 10):
        P(x, 6, IRON_L)
    for x0 in (0, 85):                                      # latches
        for y in range(0, 8):
            for x in range(x0, x0 + 4):
                dshade(x, y, 0.85 - 0.25 * (x - x0) - 0.06 * y, RED_RAMP)
        R(x0, 0, x0 + 3, 0, PAINT_RL)
        P(x0 + 1, 4, IRON_D)
    bore(44, 7, 1.0)
    grime(0, 0, 88, 9, 40, (RUST, RUST_D, TIM_D), on=IRON_RAMP + RED_RAMP)


def turntable_crank():
    """S21's crank: the pinion that walks the table's rim, its bore open, and the crank
    arm off it to a wooden grip. It turns, so the pinion is lit from its middle."""
    c = 8.5
    for y in range(18):
        for x in range(18):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            if d > 8.7:
                continue
            a = math.atan2(dy, dx)
            if d > 6.6:                                     # eight teeth, square-cut
                k = round(a / (2 * math.pi / 8))
                if abs(a - k * 2 * math.pi / 8) * d <= 1.3:
                    P(x, y, IRON_M if d < 7.8 else IRON_L)
                continue
            dshade(x, y, 0.35 + 0.45 * (1 - abs(d - 4.2) / 2.6), IRON_RAMP)
    for y in range(18):
        for x in range(18):
            d = math.hypot(x - c, y - c)
            if 2.4 <= d <= 3.2:                             # hub ring
                P(x, y, IRON_L)
    for k in range(3):                                      # the arm, a flat iron web
        ln4(10 + k, 11, 15 + k, 24, (IRON_L, IRON_M, IRON_D)[k])
    for y in range(23, 27):                                 # boss at the arm's end
        for x in range(14, 19):
            if math.hypot(x - 16, y - 24.5) <= 2.2:
                dshade(x, y, 0.8 - 0.4 * (x - 14) / 4, IRON_RAMP)
    for y in range(25, 29):                                 # the handle, out sideways
        for x in range(13, 22):
            if (x, y) in ((21, 25), (21, 28)):
                continue
            dshade(x, y, 0.95 - 0.7 * (y - 25) / 3, TIM_RAMP)
    P(16, 26, IRON_M)
    bore(c, c, 1.3)
    grime(0, 0, 21, 29, 14, (RUST, RUST_D), on=IRON_RAMP)


def windlass():
    """The hand windlass of S23, S27 and S28, end-on: a sill and two raked legs up to the
    bearing, the rope drum on it, the crank arm and its handle. The drum's bore is open."""
    for y in (15, 16):                                      # sill
        for x in range(0, 23):
            dshade(x, y, 0.85 - 0.6 * (y - 15) - 0.2 * x / 22, TIM_RAMP)
    for k in range(3):                                      # legs
        sh = lambda x, y, k=k: (TIM_L, TIM_M, TIM)[k]
        ln4(1 + k, 14, 7 + k, 8, sh)
        ln4(19 + k, 14, 13 + k, 8, lambda x, y, k=k: (TIM_M, TIM, TIM_D)[k])
    cx, cy = 11.0, 7.0
    for y in range(0, 14):                                  # drum: rope turns, iron flange
        for x in range(4, 19):
            d = math.hypot(x - cx, y - cy)
            if d <= 6.0:
                P(x, y, IRON_D if d > 5.2 else rope_wound(x, y, cx, cy) if d > 2.4 else
                  IRON_M if d > 1.5 else IRON_L)
    for k in range(4):                                      # flange bolts
        a = k * math.pi / 2 + 0.4
        P(int(round(cx + math.cos(a) * 5.6)), int(round(cy + math.sin(a) * 5.6)), IRON_M)
    for k in range(2):                                      # crank arm, up and out
        ln4(13, 4 + k, 19, 1 + k, IRON_L if k == 0 else IRON_D)
    R(19, 0, 21, 2, TIM_L)                                  # handle
    P(21, 2, TIM)
    P(21, 0, TIM_M)
    bore(cx, cy, 0.9)
    grime(0, 0, 22, 16, 14, (TIM_D, SACK_D), on=TIM_RAMP + (ROPE_L,))


# ═══════════════════════════════════════════════════════════════════════════
#  IDOL AND TREBUCHET
# ═══════════════════════════════════════════════════════════════════════════
IDOL_W, IDOL_H = 73, 200
ST_XD, ST_D, ST, ST_L = (44, 45, 43), (68, 69, 64), (100, 101, 93), (138, 137, 122)
MOSS, MOSS_D = (70, 82, 52), (52, 60, 40)
IDOL_ROPE, IDOL_ROPE_D = (128, 112, 80), (84, 70, 50)
ST_RAMP = (ST_XD, ST_D, ST, ST_L)


def _hash(x, y, s=0):
    v = (x * 73856093) ^ (y * 19349663) ^ (s * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


def _dpick(x, y, t, ramp):
    t = max(0.0, min(1.0, t))
    v = t * (len(ramp) - 1)
    i = int(v)
    if v - i > BAYER[y % 4][x % 4] / 16.0:
        i += 1
    return ramp[min(i, len(ramp) - 1)]


def _half_w(ly):
    """Silhouette of the idol, half-width by row (0 = hood peak) - S26's own."""
    if ly < 10:
        return 3 + ly * 1.2
    if ly < 56:
        t = (ly - 32) / 26.0
        return 17 * math.sqrt(max(0.0, 1 - t * t * 0.55))
    if ly < 74:
        return 16 + (ly - 56) * 0.85
    if ly < 128:
        return 31 - (ly - 74) * 0.08
    return 27 + (ly - 128) * 0.12


def _crack(k, x):
    """Where the idol breaks: neck (k=0, y~62) and waist (k=1, y~134)."""
    if k == 0:
        return 61 + int(round(0.9 * math.sin(x * 0.33) + 0.6 * math.sin(x * 0.9 + 0.5)))
    return 134 + int(round(2.0 * math.sin(x * 0.27 + 1.0) + 0.8 * math.sin(x * 0.8)))


def _idol():
    """The whole figure as {(x, y): colour}, drawn once, upright, 0 = hood peak."""
    cx = IDOL_W // 2
    img = {}

    def put(x, y, c):
        x, y = int(x), int(y)
        if (x, y) in img:
            img[(x, y)] = c

    for ly in range(IDOL_H):                                # the stone, lit from the west
        h = int(_half_w(ly))
        for x in range(cx - h, cx + h + 1):
            u = (x - cx + h) / float(2 * h)
            t = 0.8 - 0.55 * u - 0.1 * (ly / IDOL_H)
            img[(x, ly)] = _dpick(x, ly, t, ST_RAMP)
        img[(cx - h, ly)] = ST_L
        img[(cx + h, ly)] = ST_XD
    for (x, y) in list(img):                                # tooling, weather and moss
        r = _hash(x, y)
        if r < 0.03:
            put(x, y, ST_D)
        elif r < 0.045:
            put(x, y, ST_L if x < cx else ST)
        m = _hash(x // 3, y // 3, 7)
        if m < 0.08 and (y < 20 or 56 < y < 80 or _hash(x, y, 3) < 0.25):
            put(x, y, MOSS if _hash(x, y, 5) < 0.6 else MOSS_D)
    for y in range(18, 50):                                 # the hood's dark opening
        t = (y - 34) / 15.0
        hw = int(9 * math.sqrt(max(0.0, 1 - t * t)))
        for x in range(cx - hw, cx + hw + 1):
            put(x, y, COAL if abs(x - cx) < hw - 1 and 20 < y < 48 else ST_XD)
    for y in range(16, 52):                                 # the hood's edge
        t = (y - 34) / 17.0
        hw = int(11 * math.sqrt(max(0.0, 1 - t * t)))
        put(cx - hw, y, ST_L)
        put(cx + hw, y, ST_D)
    for ex in (cx - 3, cx + 3):                             # two dim embers for eyes
        put(ex, 33, (150, 78, 38))
        put(ex, 32, (92, 44, 26))
    for side in (-1, 1):                                    # sleeves in to the chest
        for i in range(30):
            x = cx + side * (26 - i * 0.55)
            for xx in range(int(min(x, x + side * 6)), int(max(x, x + side * 6)) + 1):
                put(xx, 76 + i, _dpick(xx, 76 + i, 0.55 if side < 0 else 0.3, ST_RAMP))
        for i in range(31):
            put(cx + side * (26 - i * 16 / 30.0), 76 + i, ST_XD)
    for y in range(88, 113):                                # the carved ring in the hands
        for x in range(cx - 12, cx + 13):
            d = math.hypot(x - cx, y - 100)
            if d <= 11:
                if d <= 5:
                    put(x, y, ST_XD)
                elif d > 10.1:
                    put(x, y, ST_L if x + y < cx + 100 else ST_D)
                else:
                    put(x, y, _dpick(x, y, 0.75 - 0.4 * (x - cx + y - 100) / 22.0, ST_RAMP))
    for side in (-1, 1):                                    # the hands gripping its sides
        for y in range(97, 105):
            for x in range(cx + side * 13 - 2, cx + side * 13 + 3):
                if abs(x - cx - side * 13) + abs(y - 101) > 4:
                    continue
                put(x, y, _dpick(x, y, 0.62 - 0.25 * side, ST_RAMP))
        for y in (99, 101, 103):                            # fingers
            for i in range(3):
                put(cx + side * (10 + i), y, ST_XD)
    for fx, k in ((-16, 0.06), (-6, -0.02), (5, 0.03), (15, 0.08)):    # robe folds
        for y in range(118, IDOL_H):
            put(cx + fx + (y - 118) * k, y, ST_D)
            if y % 3 == 0:
                put(cx + fx + 1 + (y - 118) * k, y, ST_L)
    for y in range(IDOL_H - 4, IDOL_H):                     # hem
        for x in range(cx - 30, cx + 31):
            put(x, y, ST_D if y > IDOL_H - 4 else ST)
    for y0 in (58, 70, 128):                                # the ropes round it
        h = int(_half_w(y0)) + 1
        for x in range(cx - h, cx + h + 1):
            yy = int(y0 + (x - cx) * 0.12)
            img[(x, yy)] = IDOL_ROPE if (x + yy) % 3 else ROPE_D
            img[(x, yy + 1)] = IDOL_ROPE_D
    return img


_IDOL = []


def _idol_piece(k):
    """Rows of the idol between cracks k-1 and k, cut on the crack lines and set 1px down
    from the canvas top. Returns (pixels, height)."""
    if not _IDOL:
        _IDOL.append(_idol())
    img = _IDOL[0]

    def piece_of(x, y):
        c0, c1 = _crack(0, x), _crack(1, x)
        if y < c0:
            return 0
        if c0 < y < c1:
            return 1
        if y > c1:
            return 2
        return -1

    mine = {p: c for p, c in img.items() if piece_of(*p) == k}
    top = min(y for (_x, y) in mine)
    bot = max(y for (_x, y) in mine)
    return mine, top, bot


def _idol_size(k):
    """Canvas for piece k: 1px over it and under it for the outline."""
    _m, top, bot = _idol_piece(k)
    return (IDOL_W, bot - top + 3)


def _draw_idol(k):
    mine, top, _bot = _idol_piece(k)
    y0 = top - 1
    for (x, y), c in mine.items():
        P(x, y - y0, c)
    if k:                                                   # the broken top face, raw stone
        for x in range(IDOL_W):
            ys = [y for (xx, y) in mine if xx == x]
            if ys:
                y = min(ys)
                P(x, y - y0, _dpick(x, y, 0.6 + 0.3 * _hash(x, y, 9), (ST_D, ST, ST_L)))
    if k < 2:                                               # and the broken underside, dark
        for x in range(IDOL_W):
            ys = [y for (xx, y) in mine if xx == x]
            if ys:
                P(x, max(ys) - y0, ST_XD)


def idol_head():
    """S26's idol from the hood peak to the neck crack: the hood, the dark opening and
    the two embers in it, the neck rope."""
    _draw_idol(0)


def idol_torso():
    """From the neck crack to the waist crack: the shoulders, the sleeves and the carved
    ring in the hands, the chest and waist ropes."""
    _draw_idol(1)


def idol_robe():
    """From the waist crack down to the ankles: the robe and its folds, the hem."""
    _draw_idol(2)


def trebuchet_arm():
    """S27's throwing arm: a long timber, thicker at the axle than at the tip, four iron
    bands, the pivot bore near the short end, a pin hole at that end for the counterweight,
    and the sling hook on the tip."""
    L = 141
    piv = 107
    for x in range(3, L):
        t = min(1.0, (x - 3) / float(piv - 3))
        top = 1 if t < 0.5 else 0
        bot = 3 if t < 0.25 else 4
        for y in range(top, bot + 1):
            dshade(x, y, 0.95 - 0.8 * (y - top) / max(bot - top, 1), TIM_RAMP)
    for _ in range(26):                                     # grain
        x = 6 + int(rnd() * (L - 12))
        R(x, 2 + int(rnd() * 2), x + 1 + int(rnd() * 3), 2 + int(rnd() * 2), TIM_D)
    for bx in (28, 55, 82, 128):                            # iron bands
        for y in range(0, 6):
            if AT(bx, y) != KEY:
                P(bx, y, IRON_M if y < 2 else IRON_D)
                P(bx + 1, y, IRON_D)
        P(bx, 0, IRON_L)
    R(3, 1, 6, 3, IRON)                                     # tip ferrule
    R(3, 1, 6, 1, IRON_L)
    R(0, 2, 2, 2, IRON_M)                                   # the sling hook
    P(0, 1, IRON_L)
    R(137, 0, 140, 4, IRON)                                 # end cap
    R(137, 0, 140, 0, IRON_L)
    R(140, 0, 140, 4, IRON_D)
    for y in range(0, 6):                                   # axle boss
        for x in range(piv - 4, piv + 6):
            d = math.hypot(x - (piv + 0.5), y - 2.5)
            if d <= 3.4:
                dshade(x, y, 0.8 - 0.6 * d / 3.4, IRON_RAMP)
    bore(piv + 0.5, 2.5, 0.8)
    hole(138, 2)                                            # hanger pin hole
    hole(139, 2)
    grime(0, 0, 140, 5, 30, (TIM_D, RUST_D), on=TIM_RAMP)


def trebuchet_box():
    """S27's counterweight: a U of planks with iron corner bands, heaped with rock, and the
    bail straps up to the eye it hangs by. The rock is drawn in, part of the one body."""
    eye(19.5, 0, 2.6)
    R(19, 5, 21, 6, IRON_M)
    for x in range(1, 40):                                  # the bail, a flat iron hoop
        u = (x - 20) / 19.0
        y = int(round(11.5 - 6.0 * math.sqrt(max(0.0, 1 - u * u))))
        P(x, y, IRON_L if x < 20 else IRON_M)
        P(x, y + 1, IRON_M if x < 20 else IRON_D)
        if x in (1, 39):
            R(x, y, x, 11, IRON_M)
    for x in range(5, 36):                                  # the rock, heaped
        u = (x - 20) / 15.5
        top = int(round(17 - 6 * (1 - u * u)))
        for y in range(top, 29):
            P(x, y, COAL_D)
    stones = []
    for _ in range(70):
        sx = 5 + rnd() * 30
        u = (sx - 20) / 15.5
        sy = 18 - 6 * (1 - u * u) + rnd() * 12
        stones.append((sx, sy, 1.1 + rnd() * 1.3))
    for sx, sy, r in sorted(stones, key=lambda s: s[1]):
        for y in range(int(sy - r), int(sy + r) + 1):
            for x in range(int(sx - r), int(sx + r) + 1):
                if math.hypot(x - sx, y - sy) <= r and AT(x, y) != KEY and 4 < x < 36:
                    dshade(x, y, 0.55 - 0.5 * ((x - sx) + (y - sy)) / (2 * r) - 0.2 * rnd(),
                           (COAL, STONE_D, STONE, STONE_M))
    for x0, x1 in ((1, 4), (36, 39)):                       # plank walls
        for y in range(11, 29):
            for x in range(x0, x1 + 1):
                dshade(x, y, 0.85 - 0.45 * (x - x0) / 3 - 0.2 * (y - 11) / 17, TIM_RAMP)
        for y in (16, 22):
            R(x0, y, x1, y, TIM_D)
    for y in range(29, 33):                                 # floor planks
        for x in range(1, 40):
            dshade(x, y, 0.7 - 0.3 * (y - 29) - 0.15 * x / 39, TIM_RAMP)
    for x in range(8, 36, 9):
        R(x, 29, x, 31, TIM_D)
    for x0, x1 in ((0, 4), (36, 40)):                       # iron corner bands
        R(x0, 11, x1, 12, IRON_M)
        R(x0, 11, x1, 11, IRON_L)
        R(x0, 30, x1, 32, IRON_D)
        R(x0, 30, x1, 30, IRON)
    grime(0, 11, 40, 32, 24, (TIM_D, RUST_D), on=TIM_RAMP)


def stone_shot():
    """S27's shot: a dressed stone, rounder than any boulder, a few chisel scars."""
    ball(6.0, 6.0, 5.6, STONE_RAMP, 0.62)
    for x, y in ((3, 4), (8, 3), (5, 8), (9, 7)):
        if AT(x, y) != KEY:
            P(x, y, STONE_D)
            P(x + 1, y, STONE_L if y < 6 else STONE)
    P(4, 3, STONE_L)
    P(3, 3, STONE_L)


def trigger_pin():
    """The trigger pin of S23 and S27: a pull ring and a tapered iron pin."""
    tpl(0, 0, [
        "LMMD.......",
        "L..MLLLMMMD",
        "M..DMMMMDD.",
        "MDDD.......",
    ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D})


# ═══════════════════════════════════════════════════════════════════════════
#  SCALES
# ═══════════════════════════════════════════════════════════════════════════
def balance_beam():
    """S24's balance beam: a riveted steel lattice girder, deep at the middle where the
    pin goes through it and tapering to the eyes at the ends that the pans hang from.
    The web is bars with real gaps between them."""
    W, c, cx = 233, 7, 116
    L = 112

    def half(x):
        return int(7 - 4 * min(1.0, abs(x - cx) / float(L)))

    for x in range(3, 230):                                 # outline of the girder, solid
        h = half(x)
        for y in range(c - h, c + h + 1):
            dshade(x, y, 0.6 - 0.25 * (y - c + h) / (2 * h), IRON_RAMP)
    panels = [10 + 9 * j for j in range(9)]                 # 10 .. 82 out from the pin
    for x in range(3, 230):                                 # cut the web open between bars
        if panels[0] < abs(x - cx) < panels[-1]:
            h = half(x)
            for y in range(c - h + 2, c + h - 1):
                hole(x, y)
    for side in (-1, 1):                                    # the lattice: zig-zag bars
        for j in range(len(panels) - 1):
            xa, xb = cx + side * panels[j], cx + side * panels[j + 1]
            ta, ba = c - half(xa) + 2, c + half(xa) - 2
            tb, bb = c - half(xb) + 2, c + half(xb) - 2
            ya, yb = (ta, bb) if j % 2 == 0 else (ba, tb)
            ln4(xa, ya, xb, yb, IRON_M)
            ln4(xa, ya + (1 if ya < yb else -1), xb - side, yb, IRON_D)
        for xv in (cx + side * panels[0], cx + side * panels[-1]):
            h = half(xv)
            R(xv, c - h, xv, c + h, IRON_M)
    for x in range(3, 230):                                 # chords
        h = half(x)
        P(x, c - h, IRON_L)
        P(x, c - h + 1, IRON_M)
        P(x, c + h - 1, IRON)
        P(x, c + h, IRON_D)
    for x in range(6, 228, 6):                              # rivets
        h = half(x)
        P(x, c - h + 1, IRON_XL)
        P(x, c + h - 1, IRON_M)
    for y in range(0, 15):                                  # the pin boss
        for x in range(cx - 8, cx + 9):
            d = math.hypot(x - cx, y - c)
            if d <= 7.2:
                P(x, y, IRON_D if d > 6.3 else IRON_L if d > 5.4 else
                  _dpick(x, y, 0.75 - 0.5 * d / 5.4, IRON_RAMP))
    bore(cx, c, 2.2)
    for ex in (3, 229):                                     # end eyes
        for y in range(2, 13):
            for x in range(ex - 4, ex + 5):
                d = math.hypot(x - ex, y - c)
                if d <= 3.6:
                    dshade(x, y, 0.85 - 0.6 * d / 3.6 - 0.15 * (y - 3) / 8, IRON_RAMP)
        bore(ex, c, 1.0)
    grime(0, 0, 232, 14, 120, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def scale_pan():
    """S24's pan: a shallow steel dish with rolled lips, a stiffening ring under it, and
    an eye on each lip for the bridle chains. Open on top - ore or the crew ride in it."""
    for cx in (2.0, 50.0):
        eye(cx - 0.5, 0, 2.2)
        R(int(cx) - 1, 4, int(cx) + 1, 6, IRON_M)           # lips
        P(int(cx) - 1, 4, IRON_L)
        P(int(cx) + 1, 6, IRON_D)
    for y in range(6, 9):                                   # the dish
        for x in range(1, 52):
            dshade(x, y, 0.75 - 0.35 * (y - 6) - 0.25 * x / 51, IRON_RAMP)
    R(1, 6, 51, 6, IRON_XL)
    R(2, 6, 50, 6, IRON_L)
    for x in range(5, 49, 7):
        P(x, 7, IRON_D)
    R(4, 9, 48, 9, IRON_D)                                  # ring under it
    R(4, 9, 8, 9, IRON)
    grime(0, 4, 52, 9, 24, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  MEAT LINE
# ═══════════════════════════════════════════════════════════════════════════
def meat_hook():
    """A hook off S22's line: the trolley wheel that runs on the chain, the stem, and the
    hook, point up, its throat wide enough to stay open under the outline."""
    tpl(0, 0, [
        "...LMD.",
        "..LMeMD",
        "..MMMDD",
        "...MDD.",
        "...LMD.",
        "....L..",
        "....M..",
        "....L..",
        "....M..",
        "....L..",
        "....MD.",
        "L...LD.",
        "M...MD.",
        "MD..MD.",
        ".MMMMD.",
    ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D, 'e': IRON_XL})


def carcass():
    """A side of meat off S22's hooks, hung by the hock: the bone knob over the hole the
    hook goes through, the shank, the haunch, then the opened ribs, fat down the back.
    Muted and dark - meat that has hung in a cave."""
    cx = 6
    prof = ((0.0, 1.6), (0.1, 1.6), (0.14, 1.2), (0.3, 5.0), (0.45, 4.0), (0.55, 3.8),
            (0.72, 4.8), (0.9, 3.2), (1.0, 1.4))
    top, ln = 2, 33
    for i in range(ln):
        t = i / float(ln - 1)
        for (t0, h0), (t1, h1) in zip(prof, prof[1:]):
            if t0 <= t <= t1:
                hw = h0 + (h1 - h0) * (t - t0) / (t1 - t0)
                break
        y = top + i
        l, r = int(round(cx - hw)), int(round(cx + hw * 0.85))
        for x in range(l, r + 1):
            u = (x - l) / float(max(r - l, 1))
            P(x, y, _dpick(x, y, 0.85 - 0.75 * u, MEAT_RAMP))
        if t > 0.12:                                        # fat down the back
            P(l, y, FAT if (y % 5) else FAT_D)
            if t > 0.25:
                P(l + 1, y, _dpick(l + 1, y, 0.6, (FAT_D, FAT)))
        P(r, y, MEAT_D)
        if 0.5 < t < 0.9:                                   # the opened cavity, ribs across
            for x in range(cx, r):
                P(x, y, MEAT_XD)
            if i % 3 == 0:
                R(cx - 1, y, r - 1, y, BONE_D)
                P(cx - 1, y, BONE)
    tpl(cx - 2, 0, [                                        # the hock bone
        ".bB.",
        "bBBd",
        ".Bd.",
    ], {'b': BONE_L, 'B': BONE, 'd': BONE_D})
    hole(cx, 4)                                             # where the hook goes through
    hole(cx, 5)
    grime(0, 6, 11, 34, 20, (MEAT_D, MEAT_XD, (90, 60, 50)), on=MEAT_RAMP)


GROUPS = [
    ("CRANE AND CARGO", [
        ("LiftingMagnet", "LIFTING MAGNET", lifting_magnet, (49, 20), METAL, None),
        ("CraneTrolley", "CRANE TROLLEY", crane_trolley, (27, 17), METAL, None),
        ("HookBlock", "HOOK BLOCK", hook_block, (9, 16), METAL, None),
        ("GirderLong", "GIRDER", girder_long, (63, 6), METAL, None),
        ("GirderShort", "GIRDER", girder_short, (41, 6), METAL, None),
        ("SteelPlate", "PLATE", steel_plate, (30, 5), METAL, None),
        ("CableReel", "CABLE REEL", cable_reel, (17, 17), WOOD, None),
    ]),
    ("GAS ROOM", [
        ("GasBottle", "BOTTLE", gas_bottle, (7, 38), METAL, "explosive"),
        ("GasBottleRed", "BOTTLE", gas_bottle_red, (7, 38), METAL, "explosive"),
        ("GasBottleOchre", "BOTTLE", gas_bottle_ochre, (7, 38), METAL, "explosive"),
        ("GasBottleGreen", "BOTTLE", gas_bottle_green, (7, 38), METAL, "explosive"),
        ("BottleTrolley", "BOTTLE TROLLEY", bottle_trolley, (27, 8), METAL, None),
    ]),
    ("LIFTS AND BRAKES", [
        ("CageCar", "CAGE", cage_car, (29, 40), METAL, None),
        ("BrakeLever", "BRAKE LEVER", brake_lever, (45, 13), WOOD, None),
        ("Stamp", "STAMP", stamp, (13, 78), METAL, None),
        ("SwingJaw", "SWING JAW", swing_jaw, (7, 75), METAL, None),
    ]),
    ("WHEELS", [
        ("Sprocket", "SPROCKET", sprocket, (38, 38), METAL, None),
        ("Turntable", "TURNTABLE", turntable, (89, 10), METAL, None),
        ("TurntableCrank", "CRANK", turntable_crank, (22, 30), METAL, None),
        ("Windlass", "WINDLASS", windlass, (23, 17), WOOD, None),
    ]),
    ("IDOL AND TREBUCHET", [
        ("IdolHead", "IDOL HEAD", idol_head, _idol_size(0), DEFAULT, None),
        ("IdolTorso", "IDOL TORSO", idol_torso, _idol_size(1), DEFAULT, None),
        ("IdolRobe", "IDOL ROBE", idol_robe, _idol_size(2), DEFAULT, None),
        ("TrebuchetArm", "TREBUCHET ARM", trebuchet_arm, (141, 6), WOOD, None),
        ("TrebuchetBox", "COUNTERWEIGHT", trebuchet_box, (41, 33), WOOD, None),
        ("StoneShot", "SHOT", stone_shot, (13, 13), DEFAULT, None),
        ("TriggerPin", "PIN", trigger_pin, (11, 4), METAL, None),
    ]),
    ("SCALES", [
        ("BalanceBeam", "BALANCE BEAM", balance_beam, (233, 15), METAL, None),
        ("ScalePan", "SCALE PAN", scale_pan, (53, 10), METAL, None),
    ]),
    ("MEAT LINE", [
        ("MeatHook", "MEAT HOOK", meat_hook, (7, 15), METAL, None),
        ("Carcass", "CARCASS", carcass, (12, 36), DEFAULT, None),
    ]),
]

# where ropes and pins go: the middle of each eye or bore, pixels from the top-left corner
ANCHORS = {
    "LiftingMagnet": {"Eye": (24.5, 3.5)},
    "CraneTrolley": {"Eye": (13.5, 14.9)},
    "HookBlock": {"Eye": (4.5, 3.0)},
    "CableReel": {"Pivot": (8.5, 8.5)},
    "CageCar": {"Eye": (14.5, 3.1)},
    "BrakeLever": {"Pivot": (41.0, 6.5)},
    "SwingJaw": {"Pivot": (3.5, 4.0)},
    "Sprocket": {"Pivot": (19.0, 19.0)},
    "Turntable": {"Pivot": (44.5, 7.5)},
    "TurntableCrank": {"Pivot": (9.0, 9.0)},
    "Windlass": {"Pivot": (11.5, 7.5)},
    "TrebuchetArm": {"Pivot": (108.0, 3.0), "Hanger": (139.0, 2.5), "Sling": (0.5, 1.5)},
    "TrebuchetBox": {"Eye": (20.5, 3.1)},
    "BalanceBeam": {"Pivot": (116.5, 7.5), "EyeL": (3.5, 7.5), "EyeR": (229.5, 7.5)},
    "ScalePan": {"EyeL": (2.5, 2.7), "EyeR": (50.5, 2.7)},
    "MeatHook": {"Eye": (4.5, 1.5)},
    "Carcass": {"Eye": (6.5, 5.0)},
}
