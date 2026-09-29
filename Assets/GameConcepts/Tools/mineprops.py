"""Mine props - the collidable objects of the mine, drawn at game scale.

    python Assets/GameConcepts/Tools/mineprops.py

Writes `Assets/GameConcepts/Icons/Mine/Icon_<Name>.png` (transparent, x4) and one contact
sheet, `Assets/GameConcepts/Icons/IconSheet_Mine.png`, with the hooded hero standing at the head
of every row for scale.

This is the second pass at object art. The first (`icons.py`, now in `Icons/Legacy/`) squeezed every object into a
32x32 square with motion arrows, which made a lamp as big as a locomotive. These are drawn
the size they are in the game instead - one pixel is one 20-PPU sprite pixel, the same
scale as `Characters/Char_*.png` - so an ore tub is a little wider than a man is and a
stick of dynamite is a few pixels long.

Everything here is a thing the player collides with: a support, a car, a load, a machine.
Two rules follow from that, the same as for the first set:

* **Draw what is solid.** A container is drawn as the U it is - walls and a floor with the
  top open - so a tub, a kibble or a barrow can actually have something put in it. A
  side plate filling the middle would be a solid block in this engine.
* **Holes are holes.** The bolt holes in a girder, the axle eye of a cable reel and the
  throat of the crusher are keyed out, because a rope goes through the first and ore
  goes through the last.

Look: the characters' grim Noita palette, not the brighter icon palette. Three or four
muted tones per material, light from the top left, ordered dither between tones instead
of a smooth ramp, a scatter of grime over anything iron, and no arrows.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from roomkit import *  # noqa: F403,E402  (conceptkit plus hero())

OUT_DIR = os.path.join("Icons", "Mine")

# ── palette: drawn from the Noita 32, darker and dirtier than the icon set ──────────
IRON_D, IRON, IRON_M, IRON_L, IRON_XL = (40, 42, 46), (67, 67, 67), (89, 97, 100), (135, 135, 135), (187, 187, 187)
RUST_D, RUST, RUST_L = (66, 50, 42), (101, 76, 60), (131, 96, 70)
TIM_D, TIM, TIM_M, TIM_L = (58, 46, 35), (96, 76, 54), (120, 97, 68), (149, 134, 101)
SACK_D, SACK, SACK_L = (81, 72, 54), (101, 91, 81), (145, 131, 118)
ORE_G, ORE_GL, GOLD, GOLD_L = (107, 142, 127), (180, 202, 141), (165, 157, 108), (223, 232, 192)
PAINT_R, PAINT_RL = (131, 59, 59), (160, 72, 64)
OLIVE_D, OLIVE, OLIVE_L = (62, 70, 44), (86, 98, 56), (116, 128, 70)
STRIPE = (176, 160, 74)
CABLE = (30, 32, 36)

IRON_RAMP = (IRON_D, IRON, IRON_M, IRON_L)
TIM_RAMP = (TIM_D, TIM, TIM_M, TIM_L)
ROCK_RAMP = (ROCK_D, ROCK, ROCK_M, ROCK_L)

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

# the offset every helper adds, so one draw function renders its own file or a sheet cell
_OX = _OY = 0


def R(x0, y0, x1, y1, c):
    rect(_OX + x0, _OY + y0, _OX + x1, _OY + y1, c)


def P(x, y, c):
    px(_OX + x, _OY + y, c)


def LN(x0, y0, x1, y1, c):
    line(_OX + x0, _OY + y0, _OX + x1, _OY + y1, c)


def DC(cx, cy, r, c):
    disc(_OX + cx, _OY + cy, r, c)


def RG(cx, cy, r, c):
    ring(_OX + cx, _OY + cy, r, c)


def AT(x, y):
    return at(_OX + x, _OY + y)


def hole(x, y):
    """Key a pixel back out - a real opening, not a dark spot."""
    px(_OX + x, _OY + y, KEY)


# ── shading ─────────────────────────────────────────────────────────────────
def dshade(x, y, t, ramp):
    """Pick from a dark->light ramp with ordered dither, so a tone change is a
    checkered seam rather than a gradient."""
    t = max(0.0, min(1.0, t))
    v = t * (len(ramp) - 1)
    i = int(v)
    if v - i > BAYER[y % 4][x % 4] / 16.0:
        i += 1
    P(x, y, ramp[min(i, len(ramp) - 1)])


def box(x0, y0, x1, y1, dark, base, lit):
    R(x0, y0, x1, y1, base)
    R(x0, y0, x1, y0, lit)
    R(x0, y0, x0, y1, lit)
    R(x0, y1, x1, y1, dark)
    R(x1, y0, x1, y1, dark)


def log_v(x0, y0, x1, y1, ramp=TIM_RAMP, grain=TIM_D):
    """A round timber standing up: lit down its left side, grain streaks down its length."""
    w = max(x1 - x0, 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0) / w
            dshade(x, y, 0.95 - 0.9 * u, ramp)
    for _ in range((y1 - y0) // 3):
        x = x0 + 1 + int(rnd() * max(w - 1, 1))
        y = y0 + int(rnd() * (y1 - y0 - 2))
        R(x, y, x, y + 1 + int(rnd() * 2), grain)


def log_h(x0, y0, x1, y1, ramp=TIM_RAMP, grain=TIM_D, ends=True):
    """A round timber lying down: lit along its top, end grain showing at the cut ends."""
    h = max(y1 - y0, 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dshade(x, y, 0.95 - 0.9 * (y - y0) / h, ramp)
    for _ in range((x1 - x0) // 4):
        x = x0 + int(rnd() * (x1 - x0 - 2))
        y = y0 + 1 + int(rnd() * max(h - 1, 1))
        R(x, y, x + 1 + int(rnd() * 2), y, grain)
    if ends:
        for x in (x0, x1):
            R(x, y0, x, y1, TIM_M)
            P(x, y0 + h // 2, TIM_L)


def grime(x0, y0, x1, y1, n, colours, on=None):
    """Scatter dirt over pixels that are already drawn - never over the background, so the
    silhouette stays exactly what the collider is."""
    for _ in range(n):
        x = x0 + int(rnd() * (x1 - x0 + 1))
        y = y0 + int(rnd() * (y1 - y0 + 1))
        c = AT(x, y)
        if c != KEY and (on is None or c in on):
            P(x, y, pick(colours))


def stripes(x0, y0, x1, y1, period=2):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            P(x, y, STRIPE if ((x + y) // period) % 2 == 0 else INK)


def wheel(cx, cy, r):
    DC(cx, cy, r, IRON_D)
    RG(cx, cy, r, IRON)
    P(int(cx), int(cy), IRON_L)
    P(int(cx - r * 0.5), int(cy - r * 0.6), IRON_M)


def tpl(x, y, rows, pal):
    """Paint a hand-pixelled template; '.' is left alone."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.':
                P(x + i, y + j, pal[ch])


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPORTS - the things holding the roof up; knock one out and the support pass runs
# ═══════════════════════════════════════════════════════════════════════════
def stull():
    """A post jammed between floor and roof: headboard on top, wedges driven in under it,
    a footblock under the foot. The wedges are the weak point - fire or a hit there."""
    log_h(0, 0, 11, 2)                                     # headboard, pressed to the roof
    R(3, 3, 8, 3, TIM_M)                                   # wedges
    P(3, 3, TIM_L)
    P(8, 3, TIM_D)
    log_v(4, 4, 7, 29)                                     # the post
    P(6, 11, TIM_D)                                        # a knot and a split
    P(5, 12, TIM_D)
    LN(6, 17, 6, 22, TIM_D)
    P(5, 23, TIM_D)
    box(1, 30, 10, 31, TIM_D, TIM, TIM_M)                  # footblock


def timber_crib():
    """Cross-laid timbers, alternately end-on and side-on, rock packed in the middle. The
    ends are what burns first; the packing is what falls out."""
    for k in range(6):
        y1 = 23 - 4 * k
        y0 = y1 - 3
        if k % 2:                                          # side-on log, full length
            log_h(0, y0, 23, y1)
        else:                                              # two logs end-on, packing between
            for cx in (2, 21):
                DC(cx, y0 + 1.5, 2.2, TIM_D)
                DC(cx, y0 + 1.5, 1.3, TIM_M)
                P(cx, y0 + 1, TIM_L)
            for y in range(y0, y1 + 1):
                for x in range(5, 19):
                    dshade(x, y, 0.35 + 0.4 * rnd() - 0.1 * (y - y0), ROCK_RAMP)
    grime(0, 0, 23, 23, 14, (TIM_D, (46, 38, 30)), on=TIM_RAMP)


def screw_jack():
    """A steel prop: a screw in a tube, turned with a tommy bar. Stronger than timber,
    does not burn, and conducts."""
    log_h(0, 0, 9, 1)                                      # cap board it bears on
    box(1, 2, 8, 3, IRON_D, IRON, IRON_L)                  # head plate
    for y in range(4, 12):                                 # the screw
        c = IRON_L if y % 2 else IRON_D
        R(4, y, 5, y, c)
    box(2, 12, 7, 14, IRON_D, IRON_M, IRON_L)              # nut, with the bar through it
    R(0, 13, 9, 13, IRON_L)
    P(0, 13, IRON_M)
    log_v(3, 15, 6, 26, IRON_RAMP, IRON_D)                 # outer tube
    box(0, 27, 9, 29, IRON_D, IRON, IRON_M)                # foot plate
    grime(0, 2, 9, 29, 16, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def staging():
    """A timber stage to work the roof from. Planks on a ledger on posts, one bay braced:
    stand on it, under it, or burn a post and ride it down."""
    for x0, x1 in ((0, 9), (10, 20), (21, 31)):            # deck planks
        box(x0, 3, x1, 5, TIM_D, TIM_M, TIM_L)
    R(0, 6, 31, 6, TIM_D)                                  # ledger
    for x in (1, 15, 29):                                  # posts
        log_v(x, 7, x + 1, 19)
    LN(3, 8, 14, 18, TIM)                                  # braces
    LN(14, 8, 3, 18, TIM_D)
    LN(17, 8, 28, 16, TIM)
    for x in (4, 14, 25):                                  # nail heads
        P(x, 4, IRON_M)


# ═══════════════════════════════════════════════════════════════════════════
#  TRACK AND ROLLING STOCK
# ═══════════════════════════════════════════════════════════════════════════
def track_section():
    """A length of rail on its sleepers - the rail head is what the wheels ride and what
    the player walks on; the sleepers sit in the floor."""
    R(0, 0, 39, 0, IRON_L)                                 # rail head
    R(0, 1, 39, 1, IRON_M)
    R(1, 2, 38, 2, IRON_D)                                 # web
    R(0, 3, 39, 3, IRON)                                   # foot
    for x in range(1, 38, 8):                              # sleepers
        box(x, 4, x + 5, 5, TIM_D, TIM, TIM_M)
    for x in range(3, 38, 8):                              # spikes
        P(x, 3, IRON_L)
    grime(0, 0, 39, 3, 10, (RUST, RUST_D), on=(IRON, IRON_M, IRON_D))


def ore_tub():
    """The ore tub, drawn as the U it is: walls and a floor, top open, so whatever is
    thrown in stays in. Empty, because what goes in it is its own object."""
    for x0, x1, lit in ((1, 3, True), (20, 22, False)):    # walls
        for y in range(1, 12):
            for x in range(x0, x1 + 1):
                dshade(x, y, (0.75 if lit else 0.45) - 0.03 * y, IRON_RAMP)
    for y in range(9, 12):                                 # floor
        for x in range(4, 20):
            dshade(x, y, 0.5 - 0.1 * (y - 9), IRON_RAMP)
    R(0, 1, 3, 1, IRON_L)                                  # rolled rims, lipped outward
    R(20, 1, 23, 1, IRON_M)
    for y in (4, 7, 10):                                   # rivets
        P(2, y, IRON_L)
        P(21, y, IRON_M)
    R(3, 12, 20, 13, IRON_D)                               # chassis
    R(0, 12, 2, 12, IRON)                                  # couplers
    R(21, 12, 23, 12, IRON)
    P(0, 13, IRON_D)
    P(23, 13, IRON_D)
    wheel(7, 14, 2.5)
    wheel(16, 14, 2.5)
    grime(1, 1, 22, 12, 26, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def flatcar():
    """A flat for timber and rail - a deck with a stake at each end so a load can be
    lashed, or can slide off the ends when it is not."""
    log_v(1, 0, 2, 3)                                      # stakes
    log_v(23, 0, 24, 3)
    for x0, x1 in ((0, 8), (9, 16), (17, 25)):             # deck
        box(x0, 4, x1, 6, TIM_D, TIM_M, TIM_L)
    R(1, 7, 24, 7, IRON_D)                                 # frame
    R(0, 7, 0, 7, IRON)
    R(25, 7, 25, 7, IRON)
    wheel(6, 9, 2)
    wheel(19, 9, 2)
    grime(0, 4, 25, 6, 8, (TIM_D,), on=TIM_RAMP)


def battery_loco():
    """A battery loco: battery box forward, open cab at the back. Five tonnes that keeps
    going when the driver is dead, if the controller is left open."""
    box(2, 5, 20, 12, IRON_D, IRON, IRON_M)                # battery box
    for x in (8, 14):                                      # lid seams and lifting eyes
        R(x, 5, x, 12, IRON_D)
        P(x - 3, 4, IRON_M)
    P(17, 4, IRON_M)
    box(4, 7, 6, 9, IRON_D, (58, 60, 64), IRON_M)          # the stencilled plate
    P(5, 8, STRIPE)
    R(0, 7, 1, 9, IRON_D)                                  # headlamp
    P(0, 8, F_HOT)
    P(1, 8, F_MID)
    box(20, 1, 33, 2, IRON_D, IRON_M, IRON_L)              # cab roof
    R(21, 3, 21, 7, IRON)                                  # front post
    box(30, 3, 32, 12, IRON_D, IRON, IRON_M)               # back wall
    box(21, 8, 23, 12, IRON_D, IRON, IRON_M)               # control desk
    LN(24, 7, 25, 5, IRON_L)                               # controller handle
    P(25, 4, PAINT_RL)
    box(25, 9, 29, 10, TIM_D, TIM, TIM_M)                  # seat
    R(1, 13, 32, 14, IRON_D)                               # frame
    stripes(0, 12, 2, 14)                                  # buffer beams
    stripes(31, 12, 33, 14)
    wheel(7, 16, 3)
    wheel(26, 16, 3)
    R(7, 16, 26, 16, IRON_M)                               # side rod
    grime(2, 1, 32, 12, 30, (RUST, RUST_D, IRON_D), on=IRON_RAMP)


def track_buffer():
    """End of the line: a striped timber baulk on steel struts, bolted to the rail. Stops a
    tub; a loco at speed takes it with it."""
    R(0, 9, 13, 9, IRON_L)                                 # rail
    R(0, 10, 13, 10, IRON_D)
    box(1, 11, 5, 11, TIM_D, TIM, TIM_M)                   # sleepers
    box(9, 11, 13, 11, TIM_D, TIM, TIM_M)
    LN(8, 7, 2, 8, IRON_M)                                 # struts
    LN(9, 7, 4, 8, IRON)
    R(11, 7, 12, 8, IRON)
    box(8, 2, 13, 7, TIM_D, TIM, TIM_M)                    # baulk
    stripes(8, 2, 9, 7)                                    # its face
    P(11, 4, IRON_L)


# ═══════════════════════════════════════════════════════════════════════════
#  HAULAGE - what goes up and down the shafts
# ═══════════════════════════════════════════════════════════════════════════
def windlass():
    """A hand windlass over a shaft: rope drum on two posts, crank on the end. The sill is
    open in the middle - that gap is the shaft collar the rope goes down."""
    box(0, 18, 9, 19, TIM_D, TIM, TIM_M)                   # sill, both sides of the collar
    box(15, 18, 23, 19, TIM_D, TIM, TIM_M)
    log_v(2, 3, 3, 17)                                     # posts
    log_v(20, 3, 21, 17)
    LN(0, 17, 2, 12, TIM_D)                                # knee struts
    LN(23, 17, 21, 12, TIM_D)
    log_h(4, 5, 19, 10, ends=False)                        # drum
    for y in range(6, 10):                                 # rope wound on it
        for x in range(5, 19):
            if (x + y * 2) % 4 == 0:
                P(x, y, SACK_L)
            elif (x + y * 2) % 4 == 1:
                P(x, y, SACK)
    R(22, 7, 22, 12, IRON)                                 # crank
    P(22, 7, IRON_L)
    R(23, 12, 23, 13, TIM_L)
    for y in range(11, 20):                                # the rope, down the collar
        P(12, y, SACK_L if y % 3 else SACK_D)


def kibble():
    """A sinking bucket on its bail. Hollow, so it carries - men, rock, or a lit keg down a
    shaft to somebody who did not ask for it."""
    R(0, 3, 0, 9, IRON_M)                                  # bail: up from the lugs,
    R(15, 3, 15, 9, IRON_D)
    LN(0, 3, 6, 0, IRON_M)                                 # then in to the eye
    LN(15, 3, 9, 0, IRON)
    R(6, 0, 9, 0, IRON_L)
    for y in range(8, 18):                                 # walls, tapering a touch
        inset = 1 if y > 15 else 0
        for x in (1 + inset, 2 + inset, 3 + inset):
            dshade(x, y, 0.85 - 0.12 * (x - 1 - inset) - 0.02 * y, IRON_RAMP)
        for x in (12 - inset, 13 - inset, 14 - inset):
            dshade(x, y, 0.5 - 0.1 * (x - 12 + inset) - 0.02 * y, IRON_RAMP)
    for y in range(17, 20):                                # floor
        for x in range(3, 13):
            dshade(x, y, 0.45 - 0.12 * (y - 17), IRON_RAMP)
    R(1, 8, 3, 8, IRON_L)                                  # rolled rim and two hoops
    R(12, 8, 14, 8, IRON_M)
    for y in (11, 15):
        R(1, y, 3, y, IRON_D)
        R(12, y, 14, y, IRON_D)
    P(1, 9, IRON_XL)                                       # bail lugs
    P(14, 9, IRON_L)
    grime(1, 8, 14, 19, 16, (RUST, RUST_D), on=IRON_RAMP)


def ore_skip():
    """A shaft skip: tall box, sloped floor, a door at the low corner that opens when it
    tips. Open top, so it fills from a chute - or from a player dropping in."""
    LN(1, 5, 6, 0, IRON_M)                                 # bail straps and clevis
    LN(14, 5, 9, 0, IRON)
    R(6, 0, 9, 0, IRON_L)
    for y in range(5, 23):                                 # walls
        for x in (0, 1, 2):
            dshade(x, y, 0.8 - 0.02 * y, IRON_RAMP)
        for x in (13, 14, 15):
            dshade(x, y, 0.45 - 0.02 * y, IRON_RAMP)
    for k in range(10):                                    # sloped floor
        x = 3 + k
        y = 16 + k * 0.45
        R(x, int(y), x, 22, IRON)
        P(x, int(y), IRON_M)
    R(0, 23, 15, 23, IRON_D)
    box(13, 15, 15, 22, IRON_D, RUST, RUST_L)              # the door, hinged at the top
    P(14, 15, IRON_L)
    stripes(13, 21, 15, 22, 1)
    for y in (7, 11):                                      # rivets
        P(1, y, IRON_L)
        P(14, y, IRON_M)
    grime(0, 5, 15, 23, 22, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def hook_block():
    """A hook block on its chain. Hangs from a crane or a winch rope; the hook takes a
    sling, a kibble bail or a person's collar."""
    tpl(0, 0, [
        "...cc.....",
        "..c..C....",
        "...cC.....",
        "....c.....",
        "...cc.....",
        "..c..C....",
        "...cC.....",
        ".DDDDDDDD.",
        ".DLMMMMMD.",
        ".DMaaMMMD.",
        ".DMaoMMMD.",
        ".DMMMMMMD.",
        ".DDDDDDDD.",
        "....LM....",
        "....LM....",
        "....ML....",
        ".L...MM...",
        "LM....ML..",
        "ML....ML..",
        ".MM..MD...",
        "..MDDD....",
    ], {'c': IRON_L, 'C': IRON_D, 'D': IRON_D, 'M': IRON_M, 'L': IRON_L,
        'a': IRON, 'o': IRON_XL})
    grime(1, 7, 8, 12, 5, (RUST, RUST_D), on=(IRON_M,))


def ore_hopper():
    """An ore bin on timber legs: straight sides, then two sloped plates down to a throat,
    and a striped gate across the throat that a lever drops. Park a tub under it, or
    yourself."""
    log_v(1, 8, 2, 31)                                     # legs
    log_v(27, 8, 28, 31)
    LN(3, 26, 8, 20, TIM_D)                                # knee braces, clear of the throat
    LN(26, 26, 21, 20, TIM_D)
    for y in range(0, 9):                                  # straight upper sides
        for x in range(0, 4):
            dshade(x, y, 0.9 - 0.15 * x - 0.02 * y, IRON_RAMP)
        for x in range(26, 30):
            dshade(x, y, 0.55 - 0.1 * (x - 26) - 0.02 * y, IRON_RAMP)
    for i in range(10):                                    # sloped plates, 4px thick
        y = 9 + i
        xl = int(i * 0.95)
        xr = int(29 - i * 0.95)
        for k in range(4):
            dshade(xl + k, y, 0.85 - 0.15 * k, IRON_RAMP)
            dshade(xr - k, y, 0.5 - 0.1 * k, IRON_RAMP)
    for y in range(19, 22):                                # throat
        R(10, y, 12, y, IRON)
        R(17, y, 19, y, IRON_D)
    stripes(10, 22, 19, 23)                                # the gate, shut
    LN(19, 23, 23, 19, IRON_M)                             # its lever
    P(24, 18, PAINT_RL)
    R(0, 0, 3, 0, IRON_L)                                  # rim angles
    R(26, 0, 29, 0, IRON_M)
    for y in range(2, 18, 4):                              # rivets
        P(1 + max(0, int((y - 9) * 0.95)), y, IRON_XL)
        P(28 - max(0, int((y - 9) * 0.95)), y, IRON_L)
    grime(0, 0, 29, 23, 30, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  HEAVY AND LOOSE - dynamic bodies to throw, drop, stack and be crushed by
# ═══════════════════════════════════════════════════════════════════════════
def ore_chunk():
    """A lump of ore: country rock with a copper vein and a few flecks. Heavier than it
    looks, and the thing the grinder pays out for."""
    cx, cy, rx, ry = 5.5, 4.6, 5.6, 4.2
    for y in range(9):
        for x in range(12):
            a = math.atan2(y - cy, x - cx)
            rr = 1 + 0.16 * math.sin(a * 3 + 1.1) + 0.1 * math.sin(a * 5)
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= rr * rr:
                t = 0.55 - 0.35 * (x - cx) / rx - 0.45 * (y - cy) / ry
                dshade(x, y, t, ROCK_RAMP)
    for x, y, c in ((2, 6, ORE_G), (3, 5, ORE_G), (4, 5, ORE_GL), (5, 4, ORE_G),
                    (6, 3, ORE_G), (7, 3, ORE_GL), (8, 2, ORE_G), (6, 6, ORE_G)):
        if AT(x, y) != KEY:
            P(x, y, c)
    for x, y in ((9, 5), (3, 3), (7, 7)):
        if AT(x, y) != KEY:
            P(x, y, GOLD)
    P(4, 2, GOLD_L)


def ore_sack():
    """A tied sack of crushed ore. Soft enough to land on, heavy enough to hold a plate
    down, and it burns."""
    tpl(0, 0, [
        "....ab....",
        "...abbd...",
        "....dd....",
        "...rrRR...",
        "..abbbbd..",
        ".abbabbbd.",
        "abbbbbbbbd",
        "abbbccbbbd",
        "abbbbbbbdd",
        ".bbbbbbdd.",
        "..dddddd..",
    ], {'a': SACK_L, 'b': SACK, 'd': SACK_D, 'r': TIM_L, 'R': TIM_M, 'c': ORE_G})
    grime(0, 4, 9, 10, 10, (SACK_D, SACK_L), on=(SACK,))


def timber_bundle():
    """Three props lashed for carrying. Cut the lashing and they roll apart; light it and
    it is a bonfire on a flatcar."""
    log_h(0, 6, 27, 8)
    log_h(1, 3, 25, 5)
    log_h(4, 0, 22, 2)
    for x in (7, 19):                                      # lashings
        for y in range(0, 9):
            P(x, y, SACK_L if y % 2 else SACK)
            P(x + 1, y, SACK if y % 2 else SACK_D)


def girder():
    """A length of steel joist. The web is drilled at both ends - those are real holes,
    for a rope or a hook - and nothing on the sheet is heavier for its size."""
    R(0, 0, 31, 0, IRON_L)                                 # top flange
    R(0, 1, 31, 1, IRON_M)
    R(0, 2, 31, 3, IRON_D)                                 # web
    R(0, 4, 31, 4, IRON)                                   # bottom flange
    R(0, 5, 31, 5, IRON_D)
    for x in range(6, 28, 7):                              # stiffeners
        R(x, 2, x, 3, IRON)
    grime(0, 0, 31, 5, 30, (RUST, RUST_D, RUST_L), on=IRON_RAMP)
    for x in (2, 29):
        hole(x, 2)
        hole(x, 3)


def cable_reel():
    """A drum of power cable. Rolls - down a drift, off a flatcar, into the back of your
    legs - and the axle eye is open for a bar or a rope."""
    cx = cy = 8.5
    for y in range(18):
        for x in range(18):
            d = math.hypot(x - cx, y - cy)
            if d <= 8.6:
                t = 0.6 - 0.3 * (x - cx) / 8.6 - 0.35 * (y - cy) / 8.6
                dshade(x, y, t, TIM_RAMP)
    for x in (3, 6, 11, 14):                               # plank seams in the flange
        for y in range(18):
            if math.hypot(x - cx, y - cy) < 7.6:
                P(x, y, TIM_D)
    RG(cx, cy, 8.6, TIM_D)
    for k in range(6):                                     # bolt ring
        a = k * math.pi / 3 + 0.3
        P(int(cx + math.cos(a) * 5.2 + 0.5), int(cy + math.sin(a) * 5.2 + 0.5), IRON_L)
    DC(cx, cy, 2.6, IRON)                                  # the eye, with its washer
    RG(cx, cy, 2.6, IRON_D)
    P(7, 7, IRON_L)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if abs(dx) + abs(dy) < 2:
                hole(8 + dx, 8 + dy)
    for x, y in ((15, 3), (16, 2), (17, 2), (18, 1), (19, 1)):   # the cable's loose end
        P(x, y, CABLE)
    P(19, 0, IRON_M)


def anvil():
    """The mine smithy's anvil. It does one thing - fall on things - and does it well."""
    tpl(0, 0, [
        "..LLLLLLLLDL.",
        "LLMMMMMMMMMMD",
        ".LMMMMMMMMMD.",
        "...DMMMMMD...",
        "....MMMMD....",
        "...LMMMMMD...",
        "..LMMMMMMMD..",
        ".DDDDDDDDDDD.",
    ], {'L': IRON_L, 'M': IRON, 'D': IRON_D})
    grime(0, 1, 12, 7, 8, (IRON_D, IRON_M), on=(IRON,))


def tool_chest():
    """A steel tool chest, padlocked. Heavy, square, stacks; the lock is a shootable."""
    box(0, 2, 15, 9, OLIVE_D, OLIVE, OLIVE_L)
    R(0, 4, 15, 4, OLIVE_D)                                # lid seam
    R(6, 0, 9, 0, IRON_L)                                  # handle
    P(6, 1, IRON_M)
    P(9, 1, IRON_D)
    box(7, 5, 8, 7, IRON_D, IRON_M, IRON_L)                # hasp and lock
    for x, y in ((0, 2), (15, 2), (0, 9), (15, 9)):        # corner guards
        P(x, y, IRON_D)
    grime(0, 2, 15, 9, 18, (RUST, RUST_D, OLIVE_D, IRON_M), on=(OLIVE, OLIVE_L))


# ═══════════════════════════════════════════════════════════════════════════
#  CARRIED
# ═══════════════════════════════════════════════════════════════════════════
def wheelbarrow():
    """A barrow, as the tray it is: sloped walls, a floor, open top. One wheel, so it tips
    whenever it is not being held."""
    for k in range(2):                                     # tray walls
        LN(2 + k, 1, 4 + k, 7, IRON_M if k == 0 else IRON)
        LN(16 - k, 1, 13 - k, 7, IRON if k == 0 else IRON_D)
    R(4, 7, 13, 8, IRON)                                   # floor
    R(4, 8, 13, 8, IRON_D)
    R(1, 1, 3, 1, IRON_L)                                  # rim
    R(15, 1, 17, 1, IRON_M)
    LN(0, 4, 5, 9, TIM_M)                                  # handle
    P(0, 4, TIM_L)
    P(1, 4, TIM_L)
    R(5, 9, 5, 11, IRON_D)                                 # leg
    P(4, 11, IRON_D)
    LN(13, 8, 15, 9, IRON_D)                               # fork
    wheel(15, 9.5, 2.4)
    grime(1, 1, 17, 8, 10, (RUST, RUST_D), on=(IRON, IRON_M))


def powder_box():
    """A closed box of powder, lid nailed down. Treat as an explosive crate that has not
    been opened - it goes up the same."""
    box(0, 1, 11, 8, TIM_D, TIM, TIM_M)
    R(0, 0, 11, 0, TIM_L)                                  # lid edge
    R(0, 4, 11, 4, TIM_D)                                  # board seam
    for x, y in ((5, 2), (6, 2), (4, 3), (7, 3), (5, 5), (6, 5), (5, 6), (6, 6)):
        P(x, y, PAINT_R)                                   # the stencil
    P(5, 3, PAINT_RL)
    P(6, 3, PAINT_RL)
    for x in (1, 10):                                      # nails
        P(x, 1, IRON_M)
        P(x, 6, IRON_M)
    grime(0, 1, 11, 8, 8, (TIM_D,), on=(TIM,))


def dynamite_bundle():
    """Three sticks tied with twine, fuse curling off the end. Small enough to throw,
    which is the point."""
    tpl(0, 0, [
        ".......ff",
        "......f..",
        "aRtRRRtRf",
        "ardrrrdr.",
        "aRtRRRtR.",
        "ardrrrdr.",
        "aRtRRRtR.",
        "ardrrrdr.",
    ], {'a': GOLD, 'R': PAINT_RL, 'r': PAINT_R, 't': SACK_L, 'd': SACK_D, 'f': SACK})


def lantern():
    """A hung lamp on its hook. Small, swings, and breaking it is a fire."""
    tpl(0, 0, [
        "...h...",
        "..h.H..",
        "...H...",
        "...c...",
        "...C...",
        "..kKk..",
        ".kKKKk.",
        ".gyFyg.",
        ".gFWFg.",
        ".gyFyg.",
        ".kKKKk.",
        "..kkk..",
    ], {'h': IRON_L, 'H': IRON_D, 'c': IRON_M, 'C': IRON_D, 'k': IRON_D, 'K': IRON_M,
        'g': IRON, 'y': (140, 104, 58), 'F': F_MID, 'W': F_HOT})


# ═══════════════════════════════════════════════════════════════════════════
#  MACHINES
# ═══════════════════════════════════════════════════════════════════════════
def jaw_crusher():
    """A jaw crusher on its skid: a V throat between a fixed and a swing jaw, flywheel on
    the back. The throat is keyed out but it is a pocket, not a slot - a slot top to bottom
    would cut the frame into two separate bodies, so like the Grinder it eats what falls
    in and pays it out of the spout."""
    box(0, 25, 31, 27, TIM_D, TIM, TIM_M)                  # skid
    box(1, 6, 22, 24, IRON_D, IRON, IRON_M)                # frame
    R(1, 6, 22, 7, IRON_M)                                 # heavy top rail
    R(1, 6, 22, 6, IRON_L)
    for x in range(3, 22, 3):                              # rivet rows
        P(x, 9, IRON_L)
        P(x, 22, IRON_M)
    for y in range(6, 17):                                 # the throat, keyed out
        half = int(5 - (y - 6) * 0.45)
        for x in range(11 - half, 13 + half):
            hole(x, y)
        P(11 - half - 1, y, IRON_XL if y % 2 else IRON_M)  # fixed jaw, toothed
        P(13 + half, y, IRON_L if y % 2 else IRON_D)       # swing jaw
        P(13 + half + 1, y, IRON_D)
    for y in (17, 18):                                     # the bottom of the pocket
        hole(11, y)
        hole(12, y)
    R(10, 19, 13, 19, IRON_D)
    box(0, 18, 2, 20, IRON_D, IRON_M, IRON_L)              # the spout it pays out of
    R(0, 21, 0, 21, IRON_D)
    stripes(1, 4, 5, 5, 1)                                 # feed lips
    stripes(18, 4, 22, 5, 1)
    DC(25, 11, 6.4, IRON_D)                                # flywheel, over the back
    RG(25, 11, 6.4, IRON_M)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.4
        LN(25, 11, 25 + math.cos(a) * 5.4, 11 + math.sin(a) * 5.4, IRON)
    DC(25, 11, 1.4, IRON_L)
    P(25, 11, IRON_D)
    box(20, 15, 23, 24, IRON_D, IRON, IRON_M)              # bearing pedestal
    grime(1, 4, 31, 24, 34, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def rock_drill():
    """A jackleg drill standing on its air leg, steel forward. Knock the leg and it falls;
    leave it running and it walks."""
    LN(12, 9, 16, 15, IRON)                                # air leg, outer tube
    LN(13, 9, 17, 15, IRON_D)
    LN(16, 16, 19, 19, IRON_L)                             # inner tube
    P(17, 16, IRON_M)
    box(7, 3, 16, 8, IRON_D, IRON, IRON_M)                 # drill body
    for x in (10, 13):
        R(x, 3, x, 8, IRON_D)
    box(16, 4, 17, 7, IRON_D, IRON_M, IRON_L)              # backhead
    LN(17, 4, 20, 1, IRON_M)                               # handle
    R(20, 0, 21, 1, TIM_L)
    box(5, 4, 6, 7, IRON_D, IRON_M, IRON_L)                # chuck
    R(0, 5, 4, 6, IRON_L)                                  # drill steel
    R(0, 6, 4, 6, IRON_M)
    P(0, 4, IRON_XL)                                       # cross bit
    P(0, 7, IRON_XL)
    for x, y in ((17, 9), (18, 10), (19, 11), (20, 12), (20, 13), (21, 14),
                 (21, 15), (21, 16), (20, 17), (20, 18), (21, 19)):
        P(x, y, CABLE)                                     # air hose
    grime(5, 3, 17, 8, 10, (RUST, RUST_D), on=IRON_RAMP)


def sdisc(cx, cy, r, ramp=IRON_RAMP, base=0.55):
    """A disc lit from the top left, dithered - a wheel face, a drum end, a flange."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if math.hypot(x - cx, y - cy) <= r:
                dshade(x, y, base - 0.35 * (x - cx) / r - 0.4 * (y - cy) / r, ramp)


# ═══════════════════════════════════════════════════════════════════════════
#  MORE MACHINES
# ═══════════════════════════════════════════════════════════════════════════
def stamp_battery():
    """Three stamps in a timber frame, lifted by cams and dropped on the ore in the mortar
    box. Each stamp is its own kinematic body - one up, one falling, one down - and the
    mortar is open on top, so anything under a shoe gets the same as the ore."""
    log_v(0, 3, 2, 35)                                     # frame posts
    log_v(27, 3, 29, 35)
    log_h(0, 3, 29, 5)                                     # cap sill, the upper guide
    log_h(3, 19, 26, 20, ends=False)                       # lower guide
    R(3, 14, 26, 14, IRON_M)                               # camshaft
    R(3, 15, 26, 15, IRON_D)
    DC(28, 14.5, 2.6, IRON_D)                              # its pulley
    RG(28, 14.5, 2.6, IRON_M)
    for x in (3, 4, 25, 26):                               # mortar box: walls and floor
        R(x, 29, x, 35, IRON if x in (3, 4) else IRON_D)
    R(3, 29, 4, 29, IRON_L)
    R(25, 29, 26, 29, IRON_M)
    R(3, 34, 26, 35, IRON_D)
    R(5, 34, 24, 34, IRON)
    for x, lift in ((8, 0), (14, 4), (20, 2)):
        R(x - 1, 32, x + 2, 33, IRON_D)                    # the die it lands on
        R(x, 5 - lift, x, 27 - lift, IRON_L)               # stem
        R(x + 1, 5 - lift, x + 1, 27 - lift, IRON_M)
        box(x - 1, 12 - lift, x + 2, 13 - lift, IRON_D, IRON_M, IRON_L)   # tappet
        LN(x + 3, 14, x + 2, 14 - lift, IRON)              # the cam under it
        box(x - 1, 28 - lift, x + 2, 31 - lift, IRON_D, IRON, IRON_M)     # shoe
    log_h(0, 36, 29, 37)                                   # sill
    grime(0, 3, 29, 35, 30, (RUST, RUST_D, TIM_D), on=IRON_RAMP + TIM_RAMP)


def ball_mill():
    """A ball mill: a steel drum on two trunnions, turned by the ring gear round its middle.
    It is sealed - rock goes in the feed spout and comes out the far trunnion as grit -
    but the drum itself turns, so whatever stands on it walks."""
    box(0, 12, 5, 19, IRON_D, IRON, IRON_M)                # pedestals
    box(28, 12, 33, 19, IRON_D, IRON, IRON_M)
    log_h(5, 2, 28, 15, IRON_RAMP, IRON_D, ends=False)     # drum
    R(5, 2, 5, 15, IRON_D)
    R(28, 2, 28, 15, IRON_D)
    R(4, 4, 4, 13, IRON_M)                                 # heads
    R(29, 4, 29, 13, IRON_D)
    for x in (9, 13, 17, 25):                              # liner bolts
        for y in (5, 9, 13):
            P(x, y, IRON_L if y < 10 else IRON_M)
    for y in range(1, 17):                                 # ring gear
        P(20, y, IRON_L)
        P(21, y, IRON_D if y % 2 else IRON_M)
        P(22, y, IRON_D)
    R(20, 1, 22, 1, IRON_M)
    R(20, 16, 22, 16, IRON_D)
    sdisc(21, 18.4, 2.4)                                   # pinion
    box(0, 6, 3, 11, IRON_D, IRON, IRON_M)                 # feed trunnion and spout
    box(0, 1, 3, 5, IRON_D, IRON_M, IRON_L)
    box(30, 7, 33, 10, IRON_D, IRON, IRON_M)               # discharge trunnion
    box(0, 20, 33, 21, TIM_D, TIM, TIM_M)                  # base
    stripes(20, 20, 22, 21, 1)
    grime(0, 1, 33, 19, 30, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def chain_cutter():
    """A coal cutter: a low body on skids and a long jib with a chain of picks running
    round it. It saws a slot in the face - or in whatever the face has in front of it."""
    box(14, 2, 37, 10, IRON_D, IRON, IRON_M)               # body
    for x in (20, 27, 33):
        R(x, 2, x, 10, IRON_D)
    for x in range(28, 33, 2):                             # motor fins
        R(x, 4, x, 7, IRON_M)
    LN(34, 2, 36, 0, IRON_M)                               # handle
    R(36, 0, 37, 0, TIM_L)
    R(14, 11, 37, 11, IRON_D)                              # skids
    stripes(15, 8, 19, 9, 1)
    box(1, 5, 14, 8, IRON_D, IRON_M, IRON_L)               # jib
    for x in range(1, 14):                                 # the chain round it
        P(x, 5, IRON_L if x % 2 else IRON_D)
        P(x, 8, IRON_D if x % 2 else IRON_M)
        if x % 3 == 0:
            P(x, 4, IRON_XL)                               # picks
        if x % 3 == 1:
            P(x, 9, IRON_L)
    R(0, 6, 0, 7, IRON_M)                                  # rounded nose
    grime(14, 2, 37, 10, 16, (RUST, RUST_D), on=IRON_RAMP)


def belt_section():
    """A length of belt conveyor: tail pulley, idlers, head pulley, the return run under
    it. The belt top is the moving floor - like Hazards/Conveyor, but the mine's own."""
    sdisc(3, 4, 3)
    sdisc(36, 4, 3.2)
    for x in range(8, 34, 6):                              # idlers
        P(x, 3, IRON_L)
        P(x, 4, IRON_D)
        P(x - 1, 4, IRON)
        P(x + 1, 4, IRON)
    R(4, 5, 35, 5, IRON_D)                                 # stringer
    R(3, 1, 36, 1, (58, 60, 64))                           # belt, carrying side
    R(3, 2, 36, 2, CABLE)
    R(3, 7, 36, 7, CABLE)                                  # and the return run
    for x in (6, 32):                                      # legs
        R(x, 6, x + 1, 9, IRON)
        P(x, 6, IRON_M)
    P(36, 4, IRON_L)
    P(3, 4, IRON_L)
    grime(3, 1, 36, 2, 10, (IRON_D, SACK_D), on=((58, 60, 64), CABLE))


def air_receiver():
    """The compressed-air receiver the drills run off: a riveted tank on saddles with a
    gauge and a relief valve. Shoot it and the valve is not what goes."""
    for y in range(4, 14):
        for x in range(2, 32):
            inside = 7 <= x <= 26 or math.hypot(x - (7 if x < 7 else 26), y - 8.5) <= 5
            if inside:
                if 15 <= x <= 18:
                    dshade(x, y, 0.9 - 0.08 * (y - 4), (RUST_D, PAINT_R, PAINT_RL))
                else:
                    dshade(x, y, 0.9 - 0.08 * (y - 4), IRON_RAMP)
    for x in (11, 22):                                     # seams
        for y in range(4, 14):
            P(x, y, IRON_D)
            if y % 2:
                P(x + 1, y, IRON_L)
    R(10, 2, 10, 3, IRON_M)                                # gauge
    box(9, 0, 11, 1, IRON_D, IRON_XL, IRON_XL)
    P(11, 0, PAINT_R)
    R(24, 1, 25, 3, IRON_M)                                # relief valve
    P(24, 0, IRON_L)
    P(26, 1, STRIPE)
    for x0 in (7, 21):                                     # saddles
        R(x0, 13, x0 + 5, 15, IRON_D)
        R(x0 + 1, 16, x0 + 4, 17, IRON)
    box(0, 18, 33, 19, TIM_D, TIM, TIM_M)                  # skid
    grime(2, 4, 31, 17, 24, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def vent_fan():
    """The main fan in its duct, drawn edge-on: a bellmouth on the intake, the rotor seen
    side-on with its blades pitched, the motor behind it on struts, a diffuser flaring out
    of the far end. The duct is open both ends - the rotor and struts are what hold it
    together - and what it blows is air: loose bodies, gas, smoke and fire."""
    for x in range(5, 25):                                 # shell
        P(x, 3, IRON_L)
        P(x, 4, IRON_M)
        P(x, 17, IRON)
        P(x, 18, IRON_D)
    for x in range(0, 5):                                  # bellmouth
        d = (5 - x) ** 2 // 8
        P(x, 3 - d, IRON_L)
        P(x, 4 - d, IRON_M)
        P(x, 17 + d, IRON)
        P(x, 18 + d, IRON_D)
    for x in range(25, 30):                                # diffuser
        d = (x - 24) // 2
        P(x, 3 - d, IRON_M)
        P(x, 4 - d, IRON)
        P(x, 17 + d, IRON)
        P(x, 18 + d, IRON_D)
    box(9, 9, 12, 12, IRON_D, IRON_M, IRON_L)              # hub and nose
    R(8, 10, 8, 11, IRON_L)
    for y, xs, lit in ((8, (9, 10, 11), True), (7, (10, 11), True), (6, (11,), True),
                       (13, (10, 11, 12), False), (14, (10, 11), False), (15, (9,), False)):
        for i, x in enumerate(xs):                         # blades, pitched
            P(x, y, (IRON_L if lit else IRON_M) if i == 0 else (IRON_M if lit else IRON_D))
    R(13, 10, 13, 11, IRON_L)                              # shaft
    box(14, 7, 21, 14, IRON_D, IRON, IRON_M)               # motor
    for x in range(15, 21, 2):
        R(x, 8, x, 9, IRON_M)
    R(18, 5, 18, 6, IRON_D)                                # struts to the shell
    R(18, 15, 18, 16, IRON_D)
    stripes(8, 3, 13, 3, 1)
    R(7, 19, 8, 23, IRON)                                  # stand
    R(20, 19, 21, 23, IRON_D)
    box(5, 24, 23, 25, IRON_D, IRON, IRON_M)
    grime(0, 0, 29, 25, 24, (RUST, RUST_D), on=IRON_RAMP)


def hoist_drum():
    """The winding engine's drum, end on: a spoked flange on an A-frame, timber brake
    blocks on the right with the lever and its weight, and the rope running off the top
    to the headframe. Release the brake and whatever is on the rope comes back down."""
    for k in range(3):                                     # A-frame, behind the drum
        LN(5 + k, 26, 11 + k, 12, TIM_D if k == 2 else TIM)
        LN(27 - k, 26, 21 - k, 12, TIM_D if k == 0 else TIM)
    box(0, 26, 31, 27, TIM_D, TIM, TIM_M)                  # bedplate
    for i in range(17):                                    # the rope, off the top
        P(16 - i, 2 - i // 8, IRON_L if i % 3 else IRON_D)
    sdisc(16, 12, 10)
    RG(16, 12, 10, IRON_D)
    RG(16, 12, 8.6, IRON_M)
    for k in range(6):                                     # spokes, and the gaps between
        a = k * math.pi / 3 + 0.2
        LN(16, 12, 16 + math.cos(a) * 8, 12 + math.sin(a) * 8, IRON_D)
        b = a + math.pi / 6
        hx, hy = int(round(16 + math.cos(b) * 5)), int(round(12 + math.sin(b) * 5))
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            hole(hx + dx - 1, hy + dy - 1)
    DC(16, 12, 2, IRON_L)
    P(16, 12, IRON_D)
    for deg in range(-60, 61, 6):                          # brake blocks on the rim
        a = math.radians(deg)
        for r in (10.8, 11.8):
            P(int(round(16 + math.cos(a) * r)), int(round(12 + math.sin(a) * r)),
              TIM_M if r < 11 else TIM_D)
    R(29, 8, 30, 25, IRON)                                 # brake post
    P(29, 8, IRON_L)
    LN(29, 8, 24, 2, IRON_M)                               # lever
    box(21, 0, 24, 2, IRON_D, IRON, IRON_M)                # and its weight
    grime(6, 2, 30, 25, 24, (RUST, RUST_D), on=IRON_RAMP)


def slusher_winch():
    """A two-drum scraper winch. One rope drags the scraper out to the face, the other
    drags it back full - and anything in the way comes with it."""
    box(0, 10, 23, 13, IRON_D, IRON, IRON_M)               # frame
    for cx in (6, 15):                                     # drums
        sdisc(cx, 6, 4)
        RG(cx, 6, 4, IRON_D)
        P(cx, 6, IRON_L)
    box(19, 4, 23, 9, OLIVE_D, OLIVE, OLIVE_L)             # motor
    P(21, 6, OLIVE_D)
    R(10, 1, 10, 5, IRON_M)                                # clutch levers
    P(10, 0, PAINT_RL)
    R(11, 2, 11, 5, IRON_D)
    P(11, 1, STRIPE)
    for x in range(0, 3):                                  # ropes out to the scraper
        P(x, 6, IRON_L if x % 2 else IRON_D)
    for i in range(10):
        P(i, 2 - i // 5, IRON_L if i % 3 else IRON_D)
    grime(0, 2, 23, 13, 16, (RUST, RUST_D), on=IRON_RAMP)


def tippler():
    """A rotary tippler: a steel ring on rollers with a length of track through it and a
    striped clamp over the top. Run a tub in, turn the ring, and the tub empties - so does
    anybody riding it."""
    cx = cy = 13.5
    for y in range(28):
        for x in range(28):
            d = math.hypot(x - cx, y - cy)
            if 11 <= d <= 13.6:
                dshade(x, y, 0.55 - 0.35 * (x - cx) / 13.5 - 0.4 * (y - cy) / 13.5, IRON_RAMP)
    for k in range(8):                                     # rivets round the ring
        a = k * math.pi / 4 + 0.39
        P(int(cx + math.cos(a) * 12.3), int(cy + math.sin(a) * 12.3), IRON_L)
    for x in range(28):
        if math.hypot(x - cx, 19 - cy) <= 11.6:            # the track through it
            P(x, 19, IRON_L)
            P(x, 20, IRON)
            P(x, 21, IRON_D)
        if math.hypot(x - cx, 6.5 - cy) <= 11.6:           # the clamp beam
            for y in (6, 7):
                P(x, y, STRIPE if ((x + y) // 2) % 2 == 0 else INK)
    wheel(5, 25.5, 2)                                      # rollers
    wheel(22, 25.5, 2)
    R(0, 27, 27, 27, IRON_D)
    grime(0, 0, 27, 27, 20, (RUST, RUST_D), on=IRON_RAMP)


def jib_crane():
    """A pillar crane: a steel post, a tapering jib, a trolley and a hook on a chain. The
    jib slews on the post; the hook takes a kibble, a sling, a crate - or a body."""
    log_v(2, 2, 5, 28, IRON_RAMP, IRON_D)                  # post
    box(1, 0, 6, 2, IRON_D, IRON_M, IRON_L)                # cap
    box(1, 10, 6, 11, IRON_D, IRON_M, IRON_L)              # slewing collar
    box(0, 29, 8, 31, IRON_D, IRON, IRON_M)                # base
    P(1, 30, IRON_L)
    P(7, 30, IRON_L)

    def chord(x):                                          # the jib's lower edge
        return int(round(10 - (x - 5) * 5 / 26))
    R(6, 3, 31, 3, IRON_M)                                 # top chord
    R(6, 4, 31, 4, IRON_D)
    for x in range(6, 32):
        P(x, chord(x), IRON)
    for x in range(6, 30, 4):                              # lacing
        LN(x, 4, x + 2, chord(x + 2), IRON_D)
    box(19, 7, 23, 8, IRON_D, IRON_M, IRON_L)              # trolley
    for y in range(9, 20):                                 # chain
        P(21, y, IRON_L if y % 2 else IRON_D)
    tpl(20, 20, [
        "LM..",
        "LM..",
        ".MM.",
        "..MM",
        "L..M",
        "M..M",
        "MMMD",
    ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D})
    grime(0, 0, 31, 31, 16, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  SHAFT AND LANDING
# ═══════════════════════════════════════════════════════════════════════════
def man_cage():
    """The shaft cage: bonnet, floor, corner posts, open inside. The far gate is down (a
    grid of bars, so every bar is a collider and the gaps are gaps); the near one is
    folded up under the roof, which is the way in."""
    R(10, 0, 11, 1, IRON_L)                                # rope clevis
    for y in range(2, 4):                                  # bonnet
        R(10 - (y - 1) * 5, y, 11 + (y - 1) * 5, y, IRON_M if y == 2 else IRON)
    box(0, 4, 21, 5, IRON_D, IRON_M, IRON_L)
    R(0, 6, 1, 27, IRON)                                   # posts
    R(0, 6, 0, 27, IRON_M)
    R(20, 6, 21, 27, IRON_D)
    R(20, 6, 20, 27, IRON)
    box(0, 26, 21, 28, IRON_D, IRON, IRON_M)               # floor
    R(1, 29, 20, 29, IRON_D)
    R(17, 11, 19, 11, IRON_M)                              # far gate, down
    R(18, 12, 18, 25, IRON_M)
    for y in range(13, 26, 3):
        R(18, y, 19, y, IRON_L)
    R(2, 6, 2, 10, IRON_M)                                 # near gate, folded up
    for y in (6, 8, 10):
        R(2, y, 3, y, IRON_L)
    grime(0, 4, 21, 29, 18, (RUST, RUST_D), on=IRON_RAMP)


def landing_boom():
    """A striped boom across the shaft landing, pivoted on a post with its weight on the
    short end. Down, it is a bar at head height; up, the way is clear - one hinge."""
    log_v(2, 3, 4, 19, IRON_RAMP, IRON_D)                  # post
    box(0, 19, 7, 21, IRON_D, IRON, IRON_M)                # foot
    stripes(5, 4, 31, 5, 3)                                # the boom
    R(31, 4, 31, 5, IRON_D)
    box(0, 4, 2, 5, IRON_D, IRON, IRON_M)                  # short end
    box(0, 6, 1, 10, IRON_D, IRON, IRON_M)                 # its counterweight
    DC(3.5, 4.5, 1.6, IRON_L)                              # pivot
    P(3, 4, IRON_D)
    grime(0, 3, 7, 21, 8, (RUST, RUST_D), on=IRON_RAMP)


def chute():
    """A timber ore chute on two legs, iron-lined, with a striped flap across the low end.
    Things slide down it; drop the flap and they shoot off the end."""
    def top(x):
        return int(2 + x * 0.42)
    for x in range(32):
        y = top(x)
        P(x, y, IRON_M if x % 2 else IRON_L)               # liner
        for k in (1, 2):
            dshade(x, y + k, 0.8 - 0.3 * k, TIM_RAMP)
        if x % 8 == 7:
            P(x, y + 1, TIM_D)
            P(x, y + 2, TIM_D)
    stripes(30, top(30) - 4, 31, top(31) - 1, 1)           # flap
    log_v(6, top(7) + 3, 7, 21)                            # legs
    log_v(24, top(25) + 3, 25, 21)
    R(4, 21, 9, 21, TIM_D)
    R(22, 21, 27, 21, TIM_D)


def signal_bell():
    """The shaft signal: a bell on a wall bracket with its pull cord. One ring is stop,
    two is raise, three is lower - and anyone below hears it too."""
    box(0, 0, 1, 15, IRON_D, IRON, IRON_M)                 # wall plate
    R(2, 1, 6, 1, IRON_M)                                  # bracket
    P(6, 2, IRON_D)
    tpl(3, 3, [
        "..LLL..",
        ".LMMMD.",
        ".LMMMD.",
        ".LMMMD.",
        "LMMMMMD",
        "DDDDDDD",
    ], {'L': GOLD_L, 'M': GOLD, 'D': SACK_D})
    P(6, 9, IRON_D)                                        # clapper
    P(6, 10, IRON_L)
    for y in range(11, 15):                                # pull cord
        P(6, y, SACK_L if y % 2 else SACK)
    R(5, 15, 7, 15, TIM_L)


# ═══════════════════════════════════════════════════════════════════════════
#  MORE LOOSE
# ═══════════════════════════════════════════════════════════════════════════
def wheelset():
    """A spare wheelset off a tub. Rolls further than you would like, and on a grade it
    does not stop."""
    sdisc(5.5, 5.5, 5.5)
    RG(5.5, 5.5, 5.5, IRON_D)
    RG(5.5, 5.5, 4.4, IRON_M)
    for a in (0.4, 2.0, 3.5, 5.1):                         # lightening holes
        hole(int(round(5.5 + math.cos(a) * 2.8)), int(round(5.5 + math.sin(a) * 2.8)))
    DC(5.5, 5.5, 1.2, IRON_L)
    P(5, 5, IRON_D)


def carbide_drum():
    """A drum of lamp carbide, lid clamped. Heavy, rolls on its hoops, and the stencil is
    there because it burns."""
    log_v(0, 2, 10, 13, IRON_RAMP, IRON_D)
    for y in (5, 10):                                      # rolling hoops
        R(0, y - 1, 10, y - 1, IRON_L)
        R(0, y, 10, y, IRON_D)
    R(1, 0, 9, 0, IRON_M)                                  # lid and clamp ring
    R(0, 1, 10, 1, IRON_L)
    P(10, 0, IRON_D)
    for x, y in ((5, 6), (4, 7), (6, 7), (5, 8)):          # the stencil
        P(x, y, STRIPE)
    P(5, 7, PAINT_R)
    grime(0, 1, 10, 13, 16, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def chain_coil():
    """A heap of haulage chain. Pick up one end and the rest follows, link by link."""
    tpl(0, 0, [
        "...LDL.LDL....",
        "..LD.DLD.DL...",
        ".LDLMLDLMLDL..",
        "LD.DL.DL.DLDL.",
        "DLMLDLMLDLMLDL",
        ".DDDDDDDDDDDD.",
    ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D})
    grime(0, 0, 13, 5, 6, (RUST, RUST_D), on=(IRON_M, IRON_L))


def plunger_box():
    """The blasting machine: push the T-handle down and every charge on the line goes.
    Small, carryable, and the most dangerous thing on the sheet."""
    R(1, 0, 8, 0, TIM_L)                                   # T-handle
    R(1, 1, 8, 1, TIM_M)
    R(4, 2, 5, 5, IRON_L)                                  # rod
    R(5, 2, 5, 5, IRON_M)
    box(0, 6, 9, 13, TIM_D, TIM, TIM_M)                    # box
    R(0, 6, 9, 6, IRON_M)
    P(1, 5, IRON_L)                                        # terminals
    P(8, 5, IRON_L)
    R(2, 9, 7, 10, PAINT_R)                                # the band
    P(4, 9, STRIPE)
    P(5, 10, STRIPE)


# ═══════════════════════════════════════════════════════════════════════════
MINE_PROPS = [
    ("SUPPORTS", [
        ("Stull", "STULL", stull, (12, 32)),
        ("TimberCrib", "TIMBER CRIB", timber_crib, (24, 24)),
        ("ScrewJack", "SCREW JACK", screw_jack, (10, 30)),
        ("Staging", "STAGING", staging, (32, 20)),
    ]),
    ("TRACK AND ROLLING STOCK", [
        ("TrackSection", "TRACK", track_section, (40, 6)),
        ("OreTub", "ORE TUB", ore_tub, (24, 17)),
        ("Flatcar", "FLATCAR", flatcar, (26, 12)),
        ("BatteryLoco", "BATTERY LOCO", battery_loco, (34, 20)),
        ("TrackBuffer", "BUFFER STOP", track_buffer, (14, 12)),
        ("Tippler", "TIPPLER", tippler, (28, 28)),
        ("Wheelset", "WHEELSET", wheelset, (11, 11)),
    ]),
    ("HAULAGE", [
        ("Windlass", "WINDLASS", windlass, (24, 20)),
        ("Kibble", "KIBBLE", kibble, (16, 20)),
        ("OreSkip", "SKIP", ore_skip, (16, 24)),
        ("HookBlock", "HOOK BLOCK", hook_block, (10, 21)),
        ("OreHopper", "ORE HOPPER", ore_hopper, (30, 32)),
        ("JibCrane", "JIB CRANE", jib_crane, (32, 32)),
    ]),
    ("HEAVY AND LOOSE", [
        ("OreChunk", "ORE CHUNK", ore_chunk, (12, 9)),
        ("OreSack", "ORE SACK", ore_sack, (10, 11)),
        ("TimberBundle", "TIMBER BUNDLE", timber_bundle, (28, 9)),
        ("Girder", "GIRDER", girder, (32, 6)),
        ("CableReel", "CABLE REEL", cable_reel, (20, 18)),
        ("Anvil", "ANVIL", anvil, (13, 8)),
        ("ToolChest", "TOOL CHEST", tool_chest, (16, 10)),
        ("CarbideDrum", "CARBIDE DRUM", carbide_drum, (11, 14)),
        ("ChainCoil", "CHAIN", chain_coil, (14, 6)),
    ]),
    ("CARRIED", [
        ("Wheelbarrow", "BARROW", wheelbarrow, (20, 12)),
        ("PowderBox", "POWDER BOX", powder_box, (12, 9)),
        ("DynamiteBundle", "DYNAMITE", dynamite_bundle, (9, 8)),
        ("Lantern", "LANTERN", lantern, (7, 12)),
        ("PlungerBox", "BLASTING BOX", plunger_box, (10, 14)),
    ]),
    ("MACHINES", [
        ("JawCrusher", "JAW CRUSHER", jaw_crusher, (32, 28)),
        ("RockDrill", "ROCK DRILL", rock_drill, (22, 20)),
        ("StampBattery", "STAMP BATTERY", stamp_battery, (30, 38)),
        ("BallMill", "BALL MILL", ball_mill, (34, 22)),
        ("ChainCutter", "COAL CUTTER", chain_cutter, (38, 12)),
        ("BeltSection", "BELT", belt_section, (40, 10)),
    ]),
    ("POWER AND AIR", [
        ("AirReceiver", "AIR RECEIVER", air_receiver, (34, 20)),
        ("VentFan", "MAIN FAN", vent_fan, (30, 26)),
        ("HoistDrum", "HOIST DRUM", hoist_drum, (32, 28)),
        ("SlusherWinch", "SCRAPER WINCH", slusher_winch, (24, 14)),
    ]),
    ("SHAFT AND LANDING", [
        ("ManCage", "CAGE", man_cage, (22, 30)),
        ("LandingBoom", "LANDING BOOM", landing_boom, (32, 22)),
        ("Chute", "CHUTE", chute, (32, 22)),
        ("SignalBell", "SIGNAL BELL", signal_bell, (10, 16)),
    ]),
]


def draw_one(fn, ox=0, oy=0):
    global _OX, _OY
    _OX, _OY = ox, oy
    fn()
    _OX, _OY = 0, 0


def out_dir(sub=OUT_DIR):
    d = os.path.abspath(os.path.join(HERE, "..", sub))
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


SHEET_W, GAP, HERO_W = 400, 10, 16
HEAD_H, LABEL_H = 12, 11
FLOOR = (46, 50, 56)


def build_sheet(catalogue, sub, sheet_name, title, seed0):
    """Render every entry of a catalogue to `<sub>/Icon_<Name>.png` and lay them out on
    one contact sheet. Shared with `labprops.py`, which is the same thing for the lab."""
    d = out_dir(sub)
    shots = {}
    for g, (group, items) in enumerate(catalogue):
        for i, (name, label, fn, (w, h)) in enumerate(items):
            new_canvas(w, h, seed=seed0 + g * 101 + i * 7, bg=KEY)
            draw_one(fn)
            outline(0, 0, w - 1, h - 1)
            shots[name] = (snapshot(), w, h)
            save_keyed(os.path.join(d, "Icon_%s.png" % name), scale=4)

    # layout: one row per group (wrapping if it has to), everything standing on a floor
    # line, the hero at the head of each row so the scale is never in doubt
    rows, y = [], 22
    for group, items in catalogue:
        head_y = y
        y += HEAD_H
        line_, x = [], 10 + HERO_W + GAP
        for name, label, fn, (w, h) in items:
            cell = max(w, text_w(label))
            if x + cell > SHEET_W - 8 and line_:
                rows.append((group, head_y, y, line_))
                head_y = None
                y += max(max(p[3] for p in line_), 19) + LABEL_H + 6
                line_, x = [], 10 + HERO_W + GAP
            line_.append((name, label, x, h, cell))
            x += cell + GAP
        rows.append((group, head_y, y, line_))
        y += max(max(p[3] for p in line_), 19) + LABEL_H + 10
    height = y + 2

    new_canvas(SHEET_W, height, seed=991, bg=(22, 24, 28))
    cw, ch = canvas_size()
    for yy in range(ch):
        rect(0, yy, cw - 1, yy, (18 + yy // 30, 20 + yy // 30, 24 + yy // 26))
    text(8, 7, title, PALE_G)
    note = "GAME SCALE  /  EVERY PIXEL COLLIDES"
    tag(cw - 6 - text_w(note), 6, note, (150, 165, 185))
    for group, head_y, top, line_ in rows:
        if head_y is not None:
            rect(8, head_y, cw - 9, head_y, (60, 68, 80))
            text(8, head_y + 3, group, CYAN)
        tallest = max(max(p[3] for p in line_), 19)
        floor = top + tallest                              # the row's floor line
        rect(8, floor, cw - 9, floor, FLOOR)
        rect(8, floor + 1, cw - 9, floor + 1, (32, 35, 40))
        hero(10 + HERO_W // 2 - 1, floor)
        for name, label, x, h, cell in line_:
            rows_px, w, _ = shots[name]
            blit(rows_px, x + (cell - w) // 2, floor - h)
            text(x, floor + 4, label, LABEL, shadow=False)

    sheet = os.path.abspath(os.path.join(HERE, "..", sheet_name))
    save(sheet, scale=4)
    print("%d props -> %s" % (len(shots), d))
    return sheet


def build():
    return build_sheet(MINE_PROPS, OUT_DIR, os.path.join("Icons", "IconSheet_Mine.png"), "PHYSFUN - MINE OBJECTS", 8100)


if __name__ == "__main__":
    build()
