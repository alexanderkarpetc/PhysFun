"""Object icons - one 32x32 pixel icon per interactive object, drawn from code.

    python Assets/GameConcepts/Tools/icons.py

Writes `Assets/GameConcepts/Icons/Icon_<Name>.png` (32x32 native, x4 = 128, transparent
background) plus one labelled contact sheet, `IconSheet_Objects.png`, for picking from.

The first six are things the project already has - Hazards/Conveyor, Hazards/Grinder,
BridgeBuilder2D, spinning_plank, Player/Telekinesis and Phys/Fire. The rest are proposals:
each one is a thing the existing systems can already express (a hinge, a kinematic mover,
a joint with a break force, a flammable body, terrain that loses its support), so an icon
here is a level-design suggestion rather than an engineering one.

Icons are drawn on a colour-keyed canvas and get a one-pixel dark outline, which is what
keeps them readable at 32px over both the dark editor and a light palette window.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conceptkit import *  # noqa: F403,E402

S = 32                     # icon side, native pixels
OUT_DIR = "Icons"

# offset the drawing helpers below add to everything, so one draw function can render
# into its own icon canvas or into a cell of the contact sheet
_OX = _OY = 0


def R(x0, y0, x1, y1, c, a=1.0):
    rect(_OX + x0, _OY + y0, _OX + x1, _OY + y1, c, a)


def P(x, y, c, a=1.0):
    px(_OX + x, _OY + y, c, a)


def LN(x0, y0, x1, y1, c, a=1.0):
    line(_OX + x0, _OY + y0, _OX + x1, _OY + y1, c, a)


def DC(cx, cy, r, c, a=1.0):
    disc(_OX + cx, _OY + cy, r, c, a)


def RG(cx, cy, r, c):
    ring(_OX + cx, _OY + cy, r, c)


def FR(x0, y0, x1, y1, c):
    frame(_OX + x0, _OY + y0, _OX + x1, _OY + y1, c)


# ── shared icon parts ───────────────────────────────────────────────────────
def plate(x0, y0, x1, y1, c=MET, lit=MET_L, dark=MET_D):
    R(x0, y0, x1, y1, c)
    R(x0, y0, x1, y0, lit)
    R(x0, y1, x1, y1, dark)


def post(x, y0, y1, w=2, c=WOOD, lit=WOOD_L):
    R(x, y0, x + w, y1, c)
    R(x, y0, x, y1, lit)


def toothed(cx, cy, r, teeth=8, c=MET, lit=MET_XL):
    DC(cx, cy, r, c)
    RG(cx, cy, r, lit)
    DC(cx, cy, r * 0.34, MET_D)
    for i in range(teeth):
        a = i * 2 * math.pi / teeth
        DC(cx + math.cos(a) * (r + 1.4), cy + math.sin(a) * (r + 1.4), 1.4, MET_L)


def rope(x0, y0, x1, y1, c=MET_L, dark=MET_D):
    steps = max(int(max(abs(x1 - x0), abs(y1 - y0))), 1)
    for i in range(steps + 1):
        t = i / steps
        P(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c if i % 3 else dark)


def cord(x0, y0, x1, y1, c=WOOD_L, dark=WOOD_D):
    rope(x0, y0, x1, y1, c, dark)


def arrow(x, y, dx, dy, c=CYAN):
    """Motion hint. Used sparingly - only where the icon would otherwise be a still life."""
    LN(x, y, x + dx, y + dy, c)
    hx, hy = x + dx, y + dy
    nx, ny = (-1 if dx > 0 else 1), (-1 if dy > 0 else 1)
    P(hx + nx * (1 if dx else 0) + (0 if dx else 1), hy + (0 if dy else -1) + ny * (1 if dy else 0), c)
    P(hx + nx * (1 if dx else 0) - (0 if dx else 1), hy + (0 if dy else 1) + ny * (1 if dy else 0), c)


def spark_burst(x, y, n=6, c=F_HOT):
    for k in range(n):
        a = k * 2 * math.pi / n + 0.3
        P(x + math.cos(a) * 3, y + math.sin(a) * 3, c)


def ground(y=27, x0=2, x1=29, c=ROCK, lit=ROCK_L):
    R(x0, y, x1, 29, c)
    R(x0, y, x1, y, lit)


# ── 1-6  what the project already has ───────────────────────────────────────
def conveyor():
    plate(3, 14, 28, 18, MET, MET_L, MET_D)
    for x in range(6, 26, 5):                              # chevrons, pointing the way
        for k in range(3):
            P(x + k, 15 + abs(k - 1), GREEN_L)
    for cx in (5, 26):
        DC(cx, 16, 3, MET)
        RG(cx, 16, 3, MET_XL)
    for x in (9, 16, 23):                                  # legs
        R(x, 19, x + 1, 26, MET_D)
    ground()
    R(11, 9, 20, 13, ROCK_M)                               # cargo it is dragging
    R(11, 9, 20, 9, ROCK_L)
    arrow(21, 11, 5, 0)


def grinder():
    toothed(16, 16, 9, 10)
    for k in range(4):                                     # spokes
        a = k * math.pi / 4 + 0.4
        LN(16, 16, 16 + math.cos(a) * 6, 16 + math.sin(a) * 6, MET_D)
    spark_burst(24, 9, 5)
    arrow(9, 5, 8, 2, CYAN)
    R(13, 26, 19, 28, MET_D)                               # mount
    R(13, 26, 19, 26, MET_L)


def rope_bridge():
    for x in (1, 25):                                      # the ledges it is slung between
        R(x, 10, x + 5, 15, ROCK)
        R(x, 10, x + 5, 10, ROCK_L)
        R(x, 15, x + 5, 15, ROCK_D)
    pts = []
    for i in range(21):
        t = i / 20
        pts.append((int(5 + 22 * t), int(13 + 7 * math.sin(math.pi * t))))
    for i, (x, y) in enumerate(pts):                       # the carrying ropes
        P(x, y - 2, WOOD_L if i % 3 else WOOD_D)
        P(x, y + 4, WOOD_D)
    for i, (x, y) in enumerate(pts):                       # the deck, with a hole in it
        if 8 <= i <= 12:
            continue
        R(x, y, x, y + 3, WOOD if i % 2 else WOOD_L)
    for k in range(3):                                     # the planks that went
        x, y = pts[9 + k]
        R(x - 1, y + 7 + k * 5, x + 1, y + 8 + k * 5, WOOD_D)
        P(x, y + 7 + k * 5, WOOD)
    for i in (0, 20):                                      # anchor irons
        x, y = pts[i]
        R(x - 1, y - 3, x + 2, y, MET_D)
        R(x - 1, y - 3, x + 2, y - 3, MET_L)


def spinning_plank():
    a = -0.5
    for k in range(-11, 12):                               # the plank, on the turn
        x, y = 16 + math.cos(a) * k, 16 + math.sin(a) * k
        R(x, y, x, y + 2, WOOD)
        P(x, y, WOOD_L)
    DC(16, 16, 3, MET)
    RG(16, 16, 3, MET_XL)
    P(16, 16, INK)
    for k in range(9):                                     # the arc it sweeps
        aa = 0.4 + k * 0.22
        P(16 + math.cos(aa) * 13, 16 + math.sin(aa) * 13, CYAN, 0.75)
    R(14, 26, 18, 28, MET_D)


def telekinesis():
    R(4, 16, 8, 19, DIRT_L)                                # the hand
    R(4, 16, 8, 16, PALE_G)
    R(8, 17, 10, 17, DIRT_L)
    for k in range(7):                                     # the beam
        P(11 + k * 2, 16 - k // 3, CYAN, 0.85)
    R(20, 9, 27, 15, ROCK_M)                               # the held rock
    R(20, 9, 27, 9, ROCK_L)
    RG(23, 12, 7, CYAN)
    for k in range(4):
        a = k * math.pi / 2 + 0.5
        P(23 + math.cos(a) * 9, 12 + math.sin(a) * 9, CYAN, 0.6)


def fire():
    R(4, 23, 28, 27, WOOD)                                 # the flammable thing
    R(4, 23, 28, 23, WOOD_L)
    R(4, 26, 28, 27, CHAR)
    for x in (7, 13, 22):
        P(x, 22, CHAR)
    body = ((6, 20, 24, 22), (7, 17, 22, 19), (9, 14, 20, 16),
            (10, 11, 17, 13), (12, 8, 16, 10), (13, 5, 15, 7))
    for k, (x0, y0, x1, y1) in enumerate(body):            # the flame, leaning as it goes
        lean = k // 2
        R(x0 + lean, y0, x1 + lean, y1, F_COOL if k == 0 else F_MID)
    R(9, 18, 15, 21, F_MID)                                # the hot core
    R(11, 14, 15, 19, F_HOT)
    R(13, 10, 15, 13, F_HOT)
    for x, y in ((21, 12), (23, 8), (9, 9), (19, 4)):      # embers off the top
        P(x, y, F_MID)
    P(17, 3, F_HOT)


# ── 7-12  machines ──────────────────────────────────────────────────────────
def winch_drum():
    DC(13, 14, 8, MET)
    RG(13, 14, 8, MET_XL)
    for i in range(3):
        RG(13, 14, 6 - i * 2, WOOD_D if i % 2 else WOOD)
    DC(13, 14, 2, MET_D)
    rope(21, 14, 27, 26)                                   # the rope off it
    R(24, 26, 29, 28, MET)                                 # and the load
    R(24, 26, 29, 26, MET_L)
    R(6, 23, 20, 25, MET_D)                                # bed
    R(6, 23, 20, 23, MET_L)
    R(8, 25, 9, 28, MET_D)
    R(17, 25, 18, 28, MET_D)


def cage_lift():
    rope(16, 2, 16, 9)
    R(8, 9, 24, 11, MET_D)                                 # bonnet
    R(8, 9, 24, 9, MET_L)
    R(8, 11, 24, 25, MET)
    FR(8, 11, 24, 25, MET_XL)
    R(10, 13, 22, 23, CAVE)
    for x in range(11, 23, 3):                             # mesh
        R(x, 13, x, 23, MET_L, 0.7)
    R(8, 25, 24, 26, MET_D)
    arrow(27, 20, 0, -8)


def counterweight():
    DC(16, 6, 4, MET)                                      # the sheave
    RG(16, 6, 4, MET_XL)
    rope(12, 7, 8, 20)
    rope(20, 7, 24, 16)
    R(4, 20, 13, 22, WOOD)                                 # platform one side
    R(4, 20, 13, 20, WOOD_L)
    R(4, 22, 5, 24, WOOD_D)
    R(12, 22, 13, 24, WOOD_D)
    R(21, 16, 27, 24, MET_D)                               # weight the other
    R(21, 16, 27, 16, MET_L)
    for k in range(2):
        R(21, 19 + k * 3, 27, 19 + k * 3, MET, 0.8)
    arrow(29, 14, 0, 6)


def piston_press():
    R(3, 4, 29, 8, MET)                                    # the ram
    R(3, 4, 29, 4, MET_L)
    R(3, 8, 29, 9, MET_D)
    R(14, 1, 18, 4, MET_L)                                 # rod
    R(3, 22, 29, 26, MET)                                  # the anvil
    R(3, 22, 29, 22, MET_L)
    for x in (5, 16, 27):                                  # guide columns
        R(x, 9, x + 1, 22, MET_D)
    R(10, 16, 22, 21, ROCK_M)                              # what is between them
    R(10, 16, 22, 16, ROCK_L)
    for x in (11, 15, 20):
        LN(x, 16, x + 2, 21, ROCK_D)
    arrow(24, 12, 0, 6)


def pile_driver():
    R(6, 2, 26, 4, MET_D)                                  # head frame
    for x in (7, 24):
        R(x, 4, x + 1, 26, MET_D)
    R(15, 4, 17, 13, MET_L)                                # stem
    R(11, 13, 21, 20, MET)                                 # the hammer
    R(11, 13, 21, 13, MET_XL)
    R(11, 19, 21, 20, MET_D)
    R(5, 24, 27, 27, WOOD_D)                               # the mortar it falls into
    R(5, 24, 27, 24, WOOD)
    for x in (8, 13, 19, 24):
        P(x, 23, DIRT_L)
    arrow(25, 15, 0, 6)


def saw_track():
    R(2, 8, 29, 10, MET_D)                                 # the rail it runs on
    R(2, 8, 29, 8, MET_L)
    R(14, 10, 18, 13, MET)                                 # carriage
    toothed(16, 19, 7, 12)
    for k in range(3):
        P(23 + k, 15 - k, F_HOT)
    ground()
    R(6, 24, 13, 27, WOOD)                                 # stock on the bed
    R(6, 24, 13, 24, WOOD_L)
    arrow(24, 9, 5, 0)


# ── 13-18  hazards ──────────────────────────────────────────────────────────
def wrecking_ball():
    R(10, 2, 22, 4, MET_D)                                 # pivot beam
    R(10, 2, 22, 2, MET_L)
    DC(16, 4, 2, MET)
    rope(16, 5, 22, 17)
    DC(23, 21, 6, MET)
    DC(23, 21, 4, MET_D)
    RG(23, 21, 6, MET_XL)
    for k in range(9):                                     # the arc it owns
        a = 0.55 + k * 0.13
        P(16 + math.sin(a) * 17, 4 + math.cos(a) * 17, CYAN, 0.7)
    for k in range(4):                                     # the smear off its face
        P(15 - k, 20 + k % 2, MET_L, 0.5)


def suspended_boulder():
    R(6, 2, 26, 4, ROCK_D)
    rope(16, 4, 16, 10)
    DC(16, 17, 7, ROCK_M)
    DC(14, 15, 4, ROCK)
    RG(16, 17, 7, ROCK_L)
    for x, y in ((13, 14), (19, 19), (16, 21)):
        P(x, y, ROCK_D)
    LN(13, 6, 19, 10, F_MID)                               # the cut worth making
    LN(13, 10, 19, 6, F_MID)
    P(16, 8, F_HOT)
    ground()
    for x in (8, 12, 21, 25):                              # what is under it
        P(x, 26, DIRT_L)


def spike_bed():
    ground(24)
    R(3, 21, 29, 24, MET_D)
    R(3, 21, 29, 21, MET)
    for x in range(4, 28, 4):                              # the spikes
        for k in range(5):
            R(x + k // 2, 20 - k, x + 3 - k // 2, 20 - k, MET_XL if k > 2 else MET_L)
    P(11, 12, RED_L)
    P(19, 10, RED_L)
    P(15, 14, RED_L)


def runaway_cart():
    R(2, 24, 29, 25, MET_XL)                               # the rail
    for x in range(3, 28, 6):
        R(x, 26, x + 3, 27, WOOD_D)
    R(9, 12, 25, 21, MET)                                  # the car
    R(9, 12, 25, 12, MET_XL)
    R(10, 13, 24, 15, (58, 46, 34))
    for k in range(7):
        P(11 + k * 2, 11, pick([DIRT_L, GREEN_L, ROCK_L]))
    R(9, 21, 25, 22, MET_D)
    for cx in (13, 22):
        DC(cx, 23, 2, INK)
        DC(cx, 23, 1, MET_L)
    for k in range(4):                                     # going, and not stopping
        LN(8 - k, 13 + k * 2, 2 + k, 13 + k * 2, CYAN if k < 2 else (70, 118, 128))


def steam_vent():
    ground(26)
    R(7, 22, 25, 26, MET_D)                                # the vent box
    R(7, 22, 25, 22, MET_L)
    for x in range(9, 25, 3):
        R(x, 22, x + 1, 26, MET, 0.9)
    puff = ((214, 230, 238), (168, 190, 202), (120, 140, 154))
    for k in range(10):                                    # the jet, cooling as it rises
        y = 21 - k * 2
        DC(16 + (k % 2) * 2 - 1, y, 1.4 + k * 0.32, puff[min(k // 4, 2)])
    R(9, 4, 23, 10, WOOD)                                  # what it is holding up
    R(9, 4, 23, 4, WOOD_L)
    R(9, 9, 23, 10, WOOD_D)
    LN(11, 4, 21, 10, WOOD_L)
    arrow(28, 20, 0, -9, CYAN)


def magnet_coil():
    R(6, 3, 26, 7, MET_D)                                  # the coil block
    R(6, 3, 26, 3, MET_L)
    for x in range(7, 26, 3):
        R(x, 7, x + 1, 10, (140, 100, 60))                 # windings
    R(6, 10, 26, 12, MET)
    for k in range(3):                                     # field
        RG(16, 12, 6 + k * 4, CYAN)
    R(13, 20, 19, 24, MET_L)                               # the steel it has
    R(13, 20, 19, 20, MET_XL)
    arrow(22, 22, 0, -6)
    ground()


# ── 19-24  structure ────────────────────────────────────────────────────────
def pit_prop():
    R(2, 2, 29, 8, ROCK_M)                                 # the roof it holds
    R(2, 2, 29, 2, ROCK_L)
    for x in (7, 15, 23):
        LN(x, 8, x + 2, 4, ROCK_D)
    R(11, 8, 12, 10, WOOD_L)                               # head board
    R(9, 8, 21, 10, WOOD_L)
    post(14, 10, 26, 3)
    for k in range(4):                                     # it is not coping
        P(14 + k % 3, 13 + k * 3, CHAR)
    ground()


def timber_crib():
    y = 26
    while y > 8:
        if (y // 3) % 2:
            R(9, y - 2, 23, y, WOOD)
            R(9, y - 2, 23, y - 2, WOOD_L)
        else:
            for bx in (9, 19):
                R(bx, y - 2, bx + 4, y, WOOD_D)
                R(bx, y - 2, bx + 4, y - 2, WOOD)
        y -= 3
    R(4, 2, 29, 6, ROCK_M)                                 # the load on top
    R(4, 2, 29, 2, ROCK_L)
    R(9, 6, 23, 7, WOOD_L)
    ground()


def breakable_wall():
    for y in range(4, 27, 4):                              # coursed block
        R(4, y, 27, y + 3, STONE)
        R(4, y, 27, y, STONE_L)
        R(4, y + 3, 27, y + 3, STONE_D)
        off = 0 if (y // 4) % 2 else 3
        for x in range(4 + off, 27, 6):
            R(x, y, x, y + 3, STONE_D, 0.6)
    for _ in range(26):                                    # the hole in it
        px_, py_ = 12 + rnd() * 10, 10 + rnd() * 11
        P(px_, py_, CAVE)
    for _ in range(8):
        P(9 + rnd() * 16, 8 + rnd() * 16, STONE_D)
    for x, y in ((10, 22), (21, 8), (23, 21)):
        P(x, y, CHAR)


def trapdoor():
    R(2, 11, 29, 15, ROCK)                                 # the floor it is cut into
    R(2, 11, 29, 11, ROCK_L)
    R(2, 15, 29, 16, ROCK_D)
    R(8, 11, 21, 16, CAVE)                                 # the opening
    R(8, 16, 21, 28, CAVE)                                 # and the drop under it
    R(8, 11, 21, 11, ROCK_D)
    for k in range(10):                                    # the leaf, hanging open
        x, y = 20 + k * 0.5, 16 + k
        R(x, y, x + 3, y + 1, WOOD)
        P(x, y, WOOD_L)
        P(x + 3, y + 1, WOOD_D)
    for k in (2, 6):                                       # its boards
        x, y = 20 + k * 0.5, 16 + k
        R(x, y, x + 3, y, WOOD_D)
    R(19, 14, 22, 17, MET_L)                               # hinge
    P(20, 15, INK)
    R(6, 12, 9, 14, MET_D)                                 # latch, tripped
    P(7, 11, MET_XL)
    for k in range(3):                                     # something on its way down
        P(12 + k, 20 + k * 3, DIRT_L)
    R(11, 25, 15, 27, ROCK_M)
    R(11, 25, 15, 25, ROCK_L)


def ore_chute():
    for k in range(12):                                    # the chute, on the slope
        x, y = 4 + k * 2, 6 + k
        R(x, y, x + 1, y + 1, MET_D)
        P(x, y, MET_L)
        R(x + 7, y - 2, x + 8, y - 1, MET_D)
    for k in range(7):                                     # ore in it
        P(9 + k * 2, 10 + k, pick([GREEN_L, DIRT_L, PALE_G]))
    R(24, 18, 28, 26, MET)                                 # the gate at the bottom
    R(24, 18, 28, 18, MET_L)
    R(21, 25, 29, 27, MET_D)
    for x in (23, 26):
        P(x, 28, GREEN_L)
    ground()


def ladder():
    for x in (9, 21):
        R(x, 3, x + 1, 28, WOOD)
        R(x, 3, x, 28, WOOD_L)
    for y in range(6, 27, 5):
        R(9, y, 22, y + 1, WOOD_D)
        R(9, y, 22, y, WOOD)


# ── 25-27  triggers ─────────────────────────────────────────────────────────
def lever():
    ground()
    R(10, 22, 22, 26, MET_D)                               # base
    R(10, 22, 22, 22, MET_L)
    DC(16, 22, 2, MET)
    for k in range(14):                                    # the arm, thrown over
        x, y = 16 + k * 0.7, 22 - k
        P(x, y, MET_L)
        P(x + 1, y, MET_D)
    DC(26, 8, 2.4, RED_L)
    RG(26, 8, 2.4, MET_XL)
    for k in range(5):                                     # the throw
        a = 1.0 + k * 0.2
        P(16 + math.cos(a) * 15, 22 - math.sin(a) * 15, CYAN, 0.6)


def pressure_plate():
    ground(26)
    R(5, 21, 27, 24, MET)                                  # the plate
    R(5, 21, 27, 21, MET_XL)
    R(5, 24, 27, 25, MET_D)
    for x in (8, 16, 24):                                  # springs under it
        for k in range(3):
            R(x - 1, 25 + k % 2, x + 1, 25 + k % 2, MET_L, 0.8)
    R(11, 12, 21, 19, ROCK_M)                              # the mass that trips it
    R(11, 12, 21, 12, ROCK_L)
    arrow(24, 14, 0, 5)


def valve_wheel():
    R(2, 18, 29, 22, MET_D)                                # the pipe
    R(2, 18, 29, 18, MET_L)
    R(12, 14, 20, 18, MET)
    R(12, 14, 20, 14, MET_L)
    RG(16, 8, 6, MET_XL)
    RG(16, 8, 5, MET)
    for k in range(4):                                     # spokes
        a = k * math.pi / 2 + 0.4
        LN(16, 8, 16 + math.cos(a) * 5, 8 + math.sin(a) * 5, MET_L)
    DC(16, 8, 1.6, MET_D)
    R(15, 12, 17, 14, MET_L)
    for k in range(4):
        P(23 + k, 6 - k // 2, CYAN, 0.7)


# ── 28-30  fire and powder ──────────────────────────────────────────────────
def powder_keg():
    R(9, 9, 23, 27, WOOD)                                  # the keg
    R(9, 9, 9, 27, WOOD_L)
    R(23, 9, 23, 27, WOOD_D)
    R(9, 9, 23, 9, WOOD_L)
    for y in (13, 22):
        R(9, y, 23, y + 1, MET_L)
    R(14, 6, 18, 9, MET_D)                                 # bung
    cord(16, 6, 24, 2)
    spark_burst(25, 2, 5)
    P(25, 2, F_HOT)
    for k in range(3):
        P(12 + k * 4, 17 + k % 2, CHAR)


def fuse_line():
    for x in range(3, 29):                                 # the cord, tacked to a wall
        y = 18 + int(2 * math.sin(x / 4.0))
        P(x, y, WOOD_L if x % 3 else WOOD_D)
        if x % 8 == 0:
            R(x - 1, y - 1, x, y + 1, MET_D)
    bx = 19
    by = 18 + int(2 * math.sin(bx / 4.0))
    DC(bx, by, 2.4, F_MID)                                 # the spark travelling it
    P(bx, by, F_HOT)
    for k in range(5):
        P(bx + 2 + k, by - 1 - k // 2, F_MID, 0.7 - k * 0.1)
    for k in range(4):
        P(bx - 3 - k * 2, by + 1, CHAR)
    R(24, 22, 29, 28, WOOD)                                # what it runs to
    R(24, 22, 29, 22, WOOD_L)
    R(24, 25, 29, 25, MET_L)


def brazier():
    R(9, 14, 23, 20, MET)                                  # the bowl
    R(9, 14, 23, 14, MET_L)
    R(9, 20, 23, 21, MET_D)
    for x in (11, 16, 21):                                 # legs
        LN(x, 21, x + (16 - x) // 4, 27, MET_D)
    R(11, 25, 21, 27, MET_D)
    for k in range(3):                                     # the fire in it
        w = 6 - k * 2
        R(16 - w, 12 - k * 3, 16 + w, 14 - k * 3, F_COOL if k == 0 else F_MID)
    R(14, 4, 18, 9, F_MID)
    R(15, 2, 17, 7, F_HOT)
    for x, y in ((10, 8), (22, 6), (13, 3)):
        P(x, y, F_MID)


# ── control, and the things that run on rails ───────────────────────────────
def knife_switch_board():
    R(3, 2, 28, 27, (52, 46, 48))                          # the slate panel
    R(3, 2, 28, 2, (86, 80, 80))
    R(3, 27, 28, 27, (26, 24, 26))
    R(5, 5, 26, 6, BRASS)                                  # bus bar across the top
    R(5, 5, 26, 5, BRASS_L)
    R(5, 18, 26, 19, BRASS)                                # and the one along the bottom
    for k in range(4):
        x = 6 + k * 6
        R(x, 6, x + 2, 8, BRASS_L)                         # contacts, top and bottom
        R(x, 16, x + 2, 18, BRASS_L)
        if k == 2:                                         # this one is open
            for j in range(8):                             # the blade, thrown up
                R(x + 1 + j, 15 - j, x + 2 + j, 15 - j, MET_XL)
            R(x + 8, 6, x + 10, 8, WOOD)                   # insulated handle
            P(x + 9, 5, WOOD_L)
            P(x + 1, 14, F_HOT)                            # and arcing as it broke
            P(x + 2, 12, F_MID)
        else:
            R(x, 8, x + 2, 16, MET_XL)
            R(x + 1, 9, x + 1, 15, MET_L)
            R(x, 8, x + 2, 8, MET)
    for k in range(3):                                     # fuse carriers under the bus
        x = 7 + k * 7
        R(x, 21, x + 5, 25, WOOD_D)
        R(x, 21, x + 5, 21, WOOD)
        R(x + 1, 22, x + 4, 23, BRASS_L)
        P(x + 2, 24, BRASS)
    for k in range(4):                                     # cables leaving the board
        LN(8 + k * 5, 27, 8 + k * 5, 29, MET_D)


def electromagnet():
    R(12, 1, 20, 3, MET_D)                                 # hanger
    R(12, 1, 20, 1, MET_L)
    R(15, 0, 17, 1, MET_D)
    R(5, 3, 27, 8, MET)                                    # the horseshoe: yoke...
    R(5, 3, 27, 3, MET_L)
    for x in (5, 22):                                      # ...and its two limbs
        R(x, 8, x + 5, 19, MET)
        R(x, 8, x, 19, MET_L)
        R(x + 5, 8, x + 5, 19, MET_D)
    for k in range(4):                                     # windings, proud of the limbs
        y = 9 + k * 3
        R(3, y, 12, y + 1, COPPER if k % 2 else BRASS)
        R(20, y, 29, y + 1, COPPER if k % 2 else BRASS)
        R(3, y, 12, y, BRASS_L)
        R(20, y, 29, y, BRASS_L)
    for x in (5, 22):                                      # pole faces
        R(x, 19, x + 5, 21, MET_XL)
    R(6, 22, 26, 25, MET_L)                                # the steel plate it has taken
    R(6, 22, 26, 22, MET_XL)
    R(6, 25, 26, 26, MET_D)
    for k in range(3):                                     # field, only where it acts
        for j in range(7):
            a = 0.3 + j * 0.4
            P(16 + math.cos(a) * (8 + k * 3), 21 + math.sin(a) * (4 + k * 2), CYAN)
    P(2, 27, MET_L)                                        # and one more bolt on its way
    P(4, 28, MET_L)
    P(29, 27, MET_L)


def alarm_panel():
    R(4, 11, 27, 27, (74, 68, 64))                         # the panel
    R(4, 11, 27, 11, (108, 100, 94))
    R(4, 27, 27, 27, (34, 32, 32))
    R(6, 13, 25, 25, (52, 48, 46))
    DC(16, 6, 5, BRASS)                                    # the bell
    DC(16, 6, 4, BRASS_L)
    R(11, 6, 21, 8, BRASS)
    R(11, 8, 21, 9, (120, 92, 46))
    R(15, 1, 17, 2, MET_D)                                 # yoke
    DC(21, 9, 1.6, MET_L)                                  # striker
    for k in range(3):                                     # ringing, to the sides only
        for j in range(3):
            a = 2.5 + j * 0.35
            P(16 + math.cos(a) * (7 + k * 3), 6 + math.sin(a) * (7 + k * 3), PALE_G)
            P(16 - math.cos(a) * (7 + k * 3), 6 + math.sin(a) * (7 + k * 3), PALE_G)
    for cx, lit in ((11, True), (21, False)):              # the interlock lamps
        DC(cx, 17, 4, MET_D)
        DC(cx, 17, 3, RED_L if lit else (58, 78, 58))
        RG(cx, 17, 4, MET_XL)
        if lit:
            DC(cx, 17, 1.6, F_HOT)
            for k in range(4):
                a = k * math.pi / 2 + 0.4
                P(cx + math.cos(a) * 6, 17 + math.sin(a) * 6, F_MID)
        else:
            P(cx - 1, 16, (86, 108, 86))
    R(8, 22, 24, 24, (30, 32, 36))                         # label plate
    R(8, 22, 24, 22, (86, 92, 100))
    for k in range(5):
        P(10 + k * 3, 23, PALE_G)
    for x in (7, 24):                                      # conduit
        R(x, 27, x + 1, 29, MET_D)


def cart_wheel(cx, cy, r=3):
    DC(cx, cy, r, MET_D)
    RG(cx, cy, r, MET_XL)
    DC(cx, cy, 1.2, MET_L)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        P(cx + math.cos(a) * (r - 1), cy + math.sin(a) * (r - 1), MET)


def mine_cart():
    """Empty on purpose: the tub is a container, and whatever it is carrying is a separate
    object that goes in it. So what the icon has to show is the opening."""
    R(3, 4, 32, 4, MET_XL)                                 # the rim you would load over
    R(3, 5, 32, 11, (28, 31, 36))                          # and the empty inside of it
    R(4, 5, 4, 10, MET_D)                                  # the far wall, catching a little
    R(31, 5, 31, 10, MET_D)                                # light down each end
    R(4, 10, 31, 11, MET_D)                                # the floor of the tub
    R(4, 10, 31, 10, (44, 48, 54))
    R(3, 12, 32, 20, MET)                                  # the near wall
    R(3, 12, 32, 12, MET_L)
    R(3, 20, 32, 22, MET_D)
    R(3, 22, 32, 22, MET_L)
    for x in (9, 17, 25):                                  # strakes
        R(x, 12, x + 1, 20, MET_L)
        P(x, 21, MET_XL)
    for x in range(5, 31, 4):                              # rivets along the rim
        P(x, 13, MET_XL)
    R(0, 12, 3, 15, MET_D)                                 # tipping hinge, one end
    P(1, 13, MET_L)
    R(32, 12, 35, 15, MET_D)                               # coupling hook, the other
    P(35, 13, MET_L)
    for cx in (9, 26):                                     # wheels under it
        R(cx - 2, 22, cx + 2, 24, MET_D)
        cart_wheel(cx, 25, 3)


def lab_cart():
    """The same idea in the lab: a flat trolley with nothing on it, tie-downs empty,
    waiting for whatever the level wants carried."""
    R(3, 9, 36, 12, MET_L)                                 # the deck
    R(3, 9, 36, 9, MET_XL)
    R(3, 12, 36, 14, MET_D)
    for x in range(6, 35, 5):                              # its planking
        P(x, 10, MET)
        P(x, 11, MET_D)
    for x in (5, 34):                                      # a lip at each end
        R(x, 5, x + 1, 9, MET)
        R(x, 5, x + 1, 5, MET_XL)
    for x in (12, 27):                                     # tie-down loops, nothing in them
        R(x, 6, x + 1, 9, BRASS)
        R(x, 6, x + 3, 6, BRASS_L)
        R(x + 3, 6, x + 3, 9, BRASS)
    R(0, 2, 2, 12, MET_D)                                  # push handle
    R(0, 1, 5, 2, MET_L)
    for cx in (10, 29):                                    # wheels, small and castored
        R(cx - 2, 14, cx + 2, 16, MET_D)
        cart_wheel(cx, 18, 3)
    R(20, 14, 24, 16, MET_D)                               # the brake, on one axle
    P(22, 17, MET_XL)


def rail_track():
    """The road itself: ballast, sleepers, rail, a joint, and a gap where it stops."""
    for _ in range(80):                                    # ballast
        P(2 + rnd() * 27, 21 + rnd() * 7, pick([ROCK_M, ROCK_D, DIRT, DIRT_D]))
    R(2, 27, 29, 28, ROCK_D)
    for k in range(5):                                     # sleepers
        x = 2 + k * 6
        R(x, 21, x + 4, 24, WOOD_D)
        R(x, 21, x + 4, 21, WOOD)
        P(x + 1, 22, WOOD_L)
    for k in range(5):                                     # chairs holding the rail
        x = 2 + k * 6
        R(x + 1, 19, x + 3, 20, MET_D)
    R(2, 16, 20, 18, MET)                                  # the rail
    R(2, 16, 20, 16, MET_XL)
    R(2, 18, 20, 18, MET_D)
    R(24, 16, 29, 18, MET)                                 # the length past the gap
    R(24, 16, 29, 16, MET_XL)
    R(19, 15, 21, 19, MET_D)                               # fishplate at the joint
    P(20, 16, MET_XL)
    P(20, 18, MET_XL)
    for k in range(3):                                     # the gap, and what is in it
        P(22 + k, 19 + k % 2, ROCK_L)
    for k in range(7):                                     # spillage along the road
        P(4 + k * 3, 15, pick([DIRT_L, GREEN_L, ROCK_L]))


# ── carryables: the things that go in the cart, the hand, or the beam ───────
def boulder():
    """Irregular on purpose - a circle reads as a ball, and a ball reads as something
    that rolls forever. This is mass you lift, drop and get under."""
    DC(13, 13, 9, ROCK)                                    # the lump, built from three
    DC(19, 15, 7, ROCK)                                    # overlapping masses so the
    DC(11, 18, 6, ROCK)                                    # silhouette is not a disc
    for cx, cy, r in ((13, 13, 9), (19, 15, 7), (11, 18, 6)):
        RG(cx, cy, r, ROCK_M)
    DC(11, 10, 4, ROCK_M)                                  # the lit shoulder
    DC(10, 9, 2, ROCK_L)
    for x, y in ((20, 20), (23, 16), (16, 22)):            # and the shaded underside
        DC(x, y, 3, ROCK_D)
    for a, b, c, d in ((9, 14, 15, 11), (14, 17, 20, 14), (12, 20, 17, 19)):
        LN(a, b, c, d, ROCK_D)                             # bedding, so it reads as rock
    for _ in range(10):
        P(6 + rnd() * 18, 6 + rnd() * 16, pick([ROCK_M, ROCK_D, ROCK_L]))
    for k in range(4):                                     # chips knocked off the bottom
        P(4 + k * 6, 23, ROCK_D)
    P(21, 9, PALE_G)                                       # a little ore in it
    P(8, 16, GREEN_L)


def explosive_crate():
    """A case of cartridges with the lid off, because what is in it is the point. Crate
    first, hazard second - it should read as something you can pick up and stack."""
    R(1, 9, 24, 23, WOOD)                                  # the case
    R(1, 9, 24, 9, WOOD_L)
    R(1, 23, 24, 24, WOOD_D)
    for y in (14, 19):                                     # boards
        R(1, y, 24, y, WOOD_D)
    for x in (1, 23):                                      # corner irons
        R(x, 9, x + 1, 24, MET_D)
        P(x, 10, MET_L)
        P(x, 22, MET_L)
    LN(2, 22, 23, 10, WOOD_L)                              # diagonal brace
    R(2, 8, 23, 9, WOOD_D)                                 # the rim it was nailed to
    for k in range(4):                                     # cartridges standing in it
        x = 4 + k * 5
        R(x, 3, x + 3, 9, (176, 142, 74))
        R(x, 3, x + 3, 3, PALE_G)
        R(x, 6, x + 3, 6, (128, 96, 50))
        for c in range(2):                                 # each with its pigtail of fuse
            P(x + 2 + c, 2 - c, WOOD_L)
    R(20, 1, 26, 8, WOOD_D)                                # the lid, leaned against the end
    R(20, 1, 26, 1, WOOD)
    LN(20, 8, 26, 2, WOOD)
    for k in range(3):                                     # the stencil on the side
        R(7 + k * 4, 20, 9 + k * 4, 22, F_MID)
    P(11, 16, F_HOT)


def explosive_barrel():
    """Bigger than the keg, and inert until something lights it: no fuse burning here,
    just staves, hoops and a band that tells you what is inside."""
    for k in range(24):                                    # staves, bulged at the waist
        y = 3 + k
        bulge = int(2 * math.sin(math.pi * k / 23.0))
        R(2 - bulge, y, 19 + bulge, y, WOOD)
        P(2 - bulge, y, WOOD_L)
        P(19 + bulge, y, WOOD_D)
    for x in range(4, 19, 4):                              # the joints between them
        R(x, 4, x, 26, WOOD_D)
    for y in (7, 22):                                      # hoops
        R(0, y, 21, y + 1, MET_L)
        R(0, y + 1, 21, y + 1, MET_D)
    R(2, 3, 19, 4, WOOD_L)                                 # the head
    R(2, 26, 19, 27, WOOD_D)
    R(8, 1, 13, 3, MET_D)                                  # bung
    P(10, 0, MET_L)
    R(0, 13, 21, 17, F_COOL)                               # the hazard band round the waist
    for x in range(1, 21, 4):
        R(x, 13, x + 1, 17, F_MID)
    P(10, 15, F_HOT)


def coal_sack():
    """Hessian, tied at the neck, heavy at the bottom. Fuel you carry - and a cloud of
    dust if it splits."""
    for k in range(18):                                    # the body, wider as it settles
        y = 9 + k
        w = 3 + int(8 * math.sin(math.pi * (k + 3) / 24.0))
        R(11 - w, y, 11 + w, y, DIRT)
        P(11 - w, y, DIRT_L)
        P(11 + w, y, DIRT_D)
    R(3, 25, 19, 27, DIRT_D)                               # where it sits
    for a, b, c, d in ((6, 14, 9, 20), (14, 13, 12, 21), (8, 22, 15, 23)):
        LN(a, b, c, d, DIRT_D)                             # folds in the cloth
    R(8, 5, 14, 9, DIRT)                                   # the neck
    R(8, 5, 14, 5, DIRT_L)
    for k in range(3):                                     # the cord round it
        R(7, 6 + k, 15, 6 + k, WOOD_D if k == 1 else WOOD)
    for x, y in ((9, 3), (12, 2), (14, 4), (10, 1)):       # coal showing at the top
        R(x, y, x + 2, y + 2, CHAR)
        P(x, y, ROCK_D)
    for k in range(5):                                     # and dust round the foot
        P(2 + k * 4, 27, CHAR)


def battery_cell():
    """One cell out of the bank: glass, plates, two brass posts and a handle. Portable
    power for one machine, once."""
    R(3, 6, 15, 27, GLASS)                                 # the jar
    R(3, 6, 3, 27, GLASS_L)
    R(15, 6, 15, 27, (78, 104, 112))
    R(4, 8, 14, 26, (44, 62, 70))                          # its dark interior
    for x in range(5, 14, 3):                              # the plates, hanging in it
        R(x, 9, x + 1, 24, MET_L)
        P(x, 9, MET_XL)
    R(3, 5, 15, 7, MET_D)                                  # the lid
    R(3, 5, 15, 5, MET_L)
    R(3, 27, 15, 28, MET_D)
    for x in (5, 12):                                      # terminals
        R(x, 2, x + 2, 5, BRASS)
        R(x, 2, x + 2, 2, BRASS_L)
    for k in range(4):                                     # and a spark across them
        P(8 + k, 1 + (k % 2), CYAN if k % 2 else F_HOT)
    LN(2, 12, 0, 16, MET_D)                                # carrying strap
    LN(16, 12, 17, 16, MET_D)


def hand_magnet():
    """A horseshoe in the hand: painted limbs, bright pole faces, and steel already stuck
    to it. Picks up metal without spending telekinesis on it."""
    R(2, 2, 21, 8, RED_L)                                  # the bend across the top
    R(2, 2, 21, 2, (208, 108, 96))
    R(2, 8, 21, 8, (120, 54, 52))
    for x in (2, 15):                                      # the two limbs
        R(x, 8, x + 6, 19, RED_L)
        R(x, 8, x, 19, (208, 108, 96))
        R(x + 6, 8, x + 6, 19, (120, 54, 52))
        R(x, 19, x + 6, 22, MET_XL)                        # pole faces
        R(x, 22, x + 6, 22, MET)
    R(9, 9, 14, 23, KEY)                                   # the gap between them, open
    R(5, 24, 18, 26, MET_L)                                # the steel it has picked up
    R(5, 24, 18, 24, MET_XL)
    R(5, 26, 18, 27, MET_D)
    for k in range(3):                                     # field, where it is working
        for j in range(5):
            a = 0.4 + j * 0.55
            P(11 + math.cos(a) * (6 + k * 2), 22 + math.sin(a) * (2 + k * 2), CYAN)
    P(22, 27, MET_L)                                       # one more bolt on its way in
    P(0, 26, MET_L)


# ── the catalogue ───────────────────────────────────────────────────────────
# ── cradles: the wood-and-iron stands a load is set into and lashed down ────
def cradle(c=WOOD, lit=WOOD_L, dark=WOOD_D, y=23, bed=2, horn=12):
    """The shape the whole group is built on - a flat bed with both ends splayed up and
    out, so a load rolls to the middle and a lashing over the horns pulls it down."""
    R(9, y - bed + 1, 22, y, c)                            # the bed
    R(9, y - bed + 1, 22, y - bed + 1, lit)
    R(9, y + 1, 22, y + 1, dark)
    for k in range(2):                                     # the two splayed horns
        LN(9 + k, y, 4 + k, horn, lit if k else c)
        LN(22 - k, y, 27 - k, horn, lit if k else c)


def tie(x, y, c=MET_XL, r=WOOD_L, rd=WOOD_D):
    """The iron band at a horn with a rope loop through it - where a lashing gets made
    off. Two of these are what say `tie something on` rather than `shelf`."""
    R(x - 1, y, x + 1, y, c)
    P(x, y - 1, r)
    P(x - 1, y - 2, r)
    P(x + 1, y - 2, rd)
    P(x, y - 3, r)


def timber_cradle():
    cradle()
    for x in (12, 16, 20):                                 # the boards read across it
        R(x, 22, x, 23, WOOD_D, 0.6)
    for x in (10, 19):                                     # skids under the bed
        R(x, 24, x + 3, 25, WOOD_D)
        R(x, 24, x + 3, 24, WOOD)
    tie(4, 12)
    tie(27, 12)


def iron_cradle():
    cradle(MET_D, MET_L, MET_D)
    for x in range(11, 22, 3):                             # rivets down the bed
        P(x, 22, MET_XL)
    for y in (15, 18):                                     # and up the horns
        P(4 + (23 - y), y, MET_XL)
        P(27 - (23 - y), y, MET_XL)
    for x in (11, 19):                                     # short feet
        R(x, 24, x + 1, 26, MET_D)
        R(x, 24, x + 1, 24, MET_L)
    tie(4, 12, MET_XL, MET_L, MET_D)
    tie(27, 12, MET_XL, MET_L, MET_D)


def banded_cradle():
    cradle()
    for x in (12, 16, 20):
        R(x, 22, x, 23, WOOD_D, 0.6)
    for k in range(2):                                     # iron straps up both horns
        LN(8 - k, 21 - k * 5, 6 - k, 17 - k * 5, MET_L)
        LN(23 + k, 21 - k * 5, 25 + k, 17 - k * 5, MET_L)
    for x, y in ((7, 19), (24, 19), (5, 14), (26, 14)):
        P(x, y, MET_XL)
    R(8, 24, 23, 25, MET_D)                                # the iron skid it stands on
    R(8, 24, 23, 24, MET_L)
    R(9, 21, 22, 21, MET, 0.7)                             # a plate lining the bed
    tie(4, 12)
    tie(27, 12)


def lashed_load():
    cradle()
    DC(16, 19, 5, ROCK_M)                                  # the load dropped in
    RG(16, 19, 5, ROCK_L)
    for x, y in ((14, 17), (18, 20), (15, 21)):
        P(x, y, ROCK_D)
    LN(5, 13, 11, 15, DIRT_L)                              # the lashing over the top
    LN(11, 15, 21, 15, DIRT_L)
    LN(21, 15, 26, 13, DIRT_L)
    for x in (8, 13, 18, 24):
        P(x, 14 if x in (8, 24) else 15, DIRT)
    R(15, 15, 17, 16, DIRT_L)                              # the knot pulling it down
    P(16, 17, DIRT)
    for x in (10, 19):
        R(x, 24, x + 3, 25, WOOD_D)
    tie(4, 12)
    tie(27, 12)


def slung_cradle():
    RG(16, 4, 2, MET_XL)                                   # the ring it hangs from
    P(16, 6, MET_D)
    rope(16, 6, 5, 14)                                     # the two legs of the sling
    rope(16, 6, 26, 14)
    cradle(WOOD, WOOD_L, WOOD_D, y=26, horn=15)
    for x in (12, 16, 20):
        R(x, 25, x, 26, WOOD_D, 0.6)
    R(12, 19, 20, 24, MET_D)                               # a case of something in it
    R(12, 19, 20, 19, MET_L)
    for k in range(2):
        R(12, 21 + k * 2, 20, 21 + k * 2, MET, 0.8)
    tie(5, 15, MET_XL, MET_L, MET_D)
    tie(26, 15, MET_XL, MET_L, MET_D)


def cradle_stand():
    cradle(WOOD, WOOD_L, WOOD_D, y=18, horn=7)
    for x in (12, 16, 20):
        R(x, 17, x, 18, WOOD_D, 0.6)
    R(9, 19, 22, 19, MET_L)                                # iron shoe under the bed
    for x in (10, 20):                                     # the trestle it stands on
        post(x, 20, 27, 2, WOOD_D, WOOD)
    R(11, 23, 21, 24, WOOD_D)                              # the tie between the legs
    R(11, 23, 21, 23, WOOD)
    tie(4, 7)
    tie(27, 7)


ICONS = [
    ("IN THE PROJECT NOW", [
        ("Conveyor", "CONVEYOR", conveyor),
        ("Grinder", "GRINDER", grinder),
        ("RopeBridge", "ROPE BRIDGE", rope_bridge),
        ("SpinningPlank", "SPIN PLANK", spinning_plank),
        ("Telekinesis", "TELEKINESIS", telekinesis),
        ("Fire", "FIRE", fire),
    ]),
    ("MACHINES", [
        ("WinchDrum", "WINCH DRUM", winch_drum),
        ("CageLift", "CAGE LIFT", cage_lift),
        ("Counterweight", "COUNTERWEIGHT", counterweight),
        ("PistonPress", "PISTON PRESS", piston_press),
        ("PileDriver", "PILE DRIVER", pile_driver),
        ("SawTrack", "SAW ON RAIL", saw_track),
    ]),
    ("HAZARDS", [
        ("WreckingBall", "WRECKING BALL", wrecking_ball),
        ("SuspendedBoulder", "HUNG BOULDER", suspended_boulder),
        ("SpikeBed", "SPIKE BED", spike_bed),
        ("RunawayCart", "RUNAWAY CART", runaway_cart),
        ("SteamVent", "VENT / UPDRAFT", steam_vent),
        ("MagnetCoil", "MAGNET COIL", magnet_coil),
    ]),
    ("STRUCTURE", [
        ("PitProp", "PIT PROP", pit_prop),
        ("TimberCrib", "TIMBER CRIB", timber_crib),
        ("BreakableWall", "BREAK WALL", breakable_wall),
        ("Trapdoor", "TRAPDOOR", trapdoor),
        ("OreChute", "ORE CHUTE", ore_chute),
        ("Ladder", "LADDER", ladder),
    ]),
    ("TRIGGERS", [
        ("Lever", "LEVER", lever),
        ("PressurePlate", "PRESS PLATE", pressure_plate),
        ("ValveWheel", "VALVE WHEEL", valve_wheel),
    ]),
    ("FIRE AND POWDER", [
        ("PowderKeg", "POWDER KEG", powder_keg),
        ("FuseLine", "FUSE LINE", fuse_line),
        ("Brazier", "BRAZIER", brazier),
    ]),
    ("CARRIED AND THROWN", [
        ("Boulder", "BOULDER", boulder, (28, 26)),
        ("ExplosiveCrate", "EXPLOSIVE CRATE", explosive_crate, (28, 25)),
        ("ExplosiveBarrel", "EXPLOSIVE BARREL", explosive_barrel, (22, 29)),
        ("CoalSack", "COAL SACK", coal_sack, (23, 29)),
    ]),
    ("TRACK AND ROLLING STOCK", [
        ("RailTrack", "RAIL TRACK", rail_track),
        ("MineCart", "MINE CART", mine_cart, (36, 30)),
        ("LabCart", "LAB CART", lab_cart, (40, 23)),
    ]),
    ("CRADLES AND SLINGS", [
        ("TimberCradle", "TIMBER CRADLE", timber_cradle),
        ("IronCradle", "IRON CRADLE", iron_cradle),
        ("BandedCradle", "BANDED CRADLE", banded_cradle),
        ("LashedLoad", "LASHED LOAD", lashed_load),
        ("SlungCradle", "SLUNG CRADLE", slung_cradle),
        ("CradleStand", "CRADLE ON TRESTLE", cradle_stand),
    ]),
]




# ── laboratory: power and heat ──────────────────────────────────────────────
BRASS = (168, 132, 66)
BRASS_L = (214, 178, 96)
COPPER = (156, 96, 52)
BRICK = (104, 68, 56)
BRICK_L = (140, 96, 76)
GLASS = (118, 150, 158)
GLASS_L = (176, 208, 214)


def muffle_furnace():
    R(4, 8, 27, 27, BRICK)                                 # the brick shell
    R(4, 8, 27, 8, BRICK_L)
    R(4, 27, 27, 27, (70, 48, 40))
    for y in range(11, 27, 4):                             # courses
        R(5, y, 26, y, (74, 50, 42))
    R(11, 4, 15, 8, MET_D)                                 # flue
    R(11, 4, 15, 4, MET_L)
    for k in range(4):
        P(12 + k % 2, 3 - k, (120, 112, 106))
    R(9, 15, 22, 24, INK)                                  # the mouth
    R(10, 17, 21, 23, F_COOL)
    R(11, 19, 20, 23, F_MID)
    R(13, 21, 18, 23, F_HOT)
    for x in (12, 16, 20):
        P(x, 14, F_MID)
    R(7, 12, 24, 13, MET_D)                                # door hinge bar
    P(6, 12, MET_L)
    P(25, 12, MET_L)


def dynamo():
    R(3, 24, 29, 27, MET_D)                                # bed plate
    R(3, 24, 29, 24, MET_L)
    for x in (6, 25):
        R(x, 27, x + 1, 28, MET_D)
    R(9, 4, 24, 7, MET)                                    # the yoke over the top
    R(9, 4, 24, 4, MET_L)
    for x in (9, 21):                                      # pole pieces, wound
        R(x, 7, x + 3, 21, MET_D)
        for k in range(5):
            R(x - 1, 8 + k * 2, x + 4, 9 + k * 2, COPPER if k % 2 else BRASS)
        R(x, 21, x + 3, 23, MET)
    DC(16, 15, 5, BRASS)                                   # the armature between them
    RG(16, 15, 5, BRASS_L)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        LN(16, 15, 16 + math.cos(a) * 4, 15 + math.sin(a) * 4, COPPER)
    DC(16, 15, 1.6, MET_D)
    DC(16, 22, 2.4, MET_L)                                 # commutator and brushes
    R(13, 21, 15, 23, MET_D)
    R(17, 21, 19, 23, MET_D)
    P(19, 20, F_HOT)
    P(21, 19, F_MID)
    DC(5, 15, 3, MET)                                      # drive pulley, belt off the side
    RG(5, 15, 3, MET_XL)
    LN(2, 12, 5, 12, WOOD_D)
    LN(2, 18, 5, 18, WOOD_D)


def battery_bank():
    R(2, 6, 29, 8, WOOD_D)                                 # the rack
    R(2, 6, 29, 6, WOOD)
    R(2, 26, 29, 28, WOOD_D)
    R(2, 26, 29, 26, WOOD)
    for k in range(4):                                     # glass cells
        x = 4 + k * 6
        R(x, 10, x + 4, 25, GLASS)
        R(x, 10, x, 25, GLASS_L)
        R(x + 1, 12, x + 3, 24, (60, 84, 92))
        for py_ in range(13, 24, 3):                       # the plates inside
            R(x + 1, py_, x + 3, py_, MET_L)
        R(x, 9, x + 4, 10, MET_D)                          # terminals
        P(x + 1, 8, BRASS_L)
        P(x + 3, 8, BRASS_L)
    for k in range(3):                                     # link bars
        x = 5 + k * 6
        R(x, 8, x + 5, 8, BRASS)
    x = 4 + 3 * 6                                          # the cracked one
    LN(x, 13, x + 4, 22, INK)
    LN(x + 3, 12, x + 1, 20, INK)
    P(x + 2, 26, (60, 84, 92))


def transformer():
    for y in (5, 23):                                      # core yokes
        R(7, y, 25, y + 3, MET)
        R(7, y, 25, y, MET_L)
    for x in (7, 22):                                      # core limbs
        R(x, 8, x + 3, 23, MET)
        R(x, 8, x, 23, MET_L)
    for y in range(9, 23, 3):                              # laminations
        R(7, y, 10, y, MET_D)
        R(22, y, 25, y, MET_D)
    for x in (5, 20):                                      # the windings, proud of the core
        R(x, 10, x + 7, 21, COPPER)
        for k in range(4):
            R(x, 11 + k * 3, x + 7, 11 + k * 3, BRASS)
        R(x, 10, x + 7, 10, BRASS_L)
        R(x, 21, x + 7, 21, (110, 66, 36))
    R(9, 1, 11, 5, BRASS)                                  # terminals
    R(21, 1, 23, 5, BRASS)
    P(10, 0, BRASS_L)
    P(22, 0, BRASS_L)
    for k in range(6):                                     # arcing across them
        P(11 + k * 2, 1 + (k % 2), CYAN if k % 2 else F_HOT)
    R(12, 26, 20, 28, MET_D)


def arc_lamp():
    R(8, 2, 24, 5, MET_D)                                  # the hood
    R(8, 2, 24, 2, MET_L)
    LN(8, 5, 11, 8, MET_D)
    LN(24, 5, 21, 8, MET_D)
    R(10, 8, 22, 10, MET)                                  # the mechanism box
    R(10, 8, 22, 8, MET_L)
    R(15, 10, 17, 14, MET_D)                               # holders and carbons
    R(15, 14, 16, 16, CHAR)
    R(15, 19, 16, 21, CHAR)
    R(14, 21, 18, 24, MET_D)
    DC(16, 17, 2.6, F_HOT)                                 # the arc itself
    RG(16, 17, 4, F_MID)
    for k in range(6):                                     # hard, short rays
        a = k * math.pi / 3 + 0.4
        LN(16 + math.cos(a) * 5, 17 + math.sin(a) * 5,
           16 + math.cos(a) * 8, 17 + math.sin(a) * 8, F_MID)
    R(15, 24, 17, 27, MET)                                 # column and feet
    R(11, 27, 21, 28, MET_D)
    R(11, 27, 21, 27, MET_L)
    for k in range(3):                                     # the flex up to the mains
        P(25 + (k % 2), 4 - k, MET_D)


def wimshurst():
    R(4, 26, 28, 28, WOOD_D)                               # the base
    R(4, 26, 28, 26, WOOD)
    for x in (8, 22):                                      # the frame
        R(x, 14, x + 1, 26, WOOD_D)
        P(x, 14, WOOD)
    RG(16, 16, 9, GLASS_L)                                 # the disc, edge lit
    RG(16, 16, 8, GLASS)
    for k in range(8):                                     # brass sectors on it
        a = k * math.pi / 4 + 0.2
        R(16 + math.cos(a) * 5, 16 + math.sin(a) * 5,
          16 + math.cos(a) * 6 + 1, 16 + math.sin(a) * 6, BRASS)
        P(16 + math.cos(a) * 5, 16 + math.sin(a) * 5, BRASS_L)
    DC(16, 16, 2, MET_D)
    RG(16, 16, 2, MET_L)
    for cx in (12, 20):                                    # the spark gap, over the top
        LN(cx, 12, cx, 7, MET_D)
        R(cx - 1, 12, cx + 1, 13, MET_L)
        DC(cx, 6, 2, BRASS)
        RG(cx, 6, 2, BRASS_L)
    for k in range(5):                                     # arcing across the gap
        P(14 + k, 6 - (k % 2), F_HOT if k % 2 else CYAN)
    for x in (2, 27):                                      # leyden jars
        R(x, 20, x + 3, 26, GLASS)
        R(x, 20, x, 26, GLASS_L)
        R(x, 19, x + 3, 20, MET_L)
        P(x + 1, 18, BRASS_L)
    DC(25, 17, 2, MET_L)                                   # the crank
    LN(25, 17, 28, 20, MET_L)
    P(28, 21, WOOD)


# ── laboratory: pressure and gas ────────────────────────────────────────────
def gas_cylinders():
    for k in range(3):                                     # three in the rack
        x = 5 + k * 7
        body = (74, 92, 104) if k != 1 else (96, 78, 74)
        R(x, 9, x + 4, 25, body)
        R(x, 9, x, 25, MET_L)
        DC(x + 2, 9, 2.4, body)
        R(x + 1, 5, x + 3, 7, BRASS)                       # valve
        P(x + 2, 4, BRASS_L)
        R(x, 20, x + 4, 20, MET_D)
    R(3, 13, 27, 15, MET_D)                                # the strap holding them
    R(3, 13, 27, 13, MET_L)
    R(24, 20, 29, 24, (74, 92, 104))                       # one loose on the floor
    R(24, 20, 29, 20, MET_L)
    R(22, 21, 24, 23, BRASS)
    for k in range(5):                                     # and going somewhere
        P(21 - k * 2, 22 + (k % 2), (200, 216, 224) if k < 3 else (140, 158, 170))
    ground()


def pressure_gauges():
    R(2, 22, 29, 26, MET)                                  # the manifold it is all on
    R(2, 22, 29, 22, MET_L)
    R(2, 26, 29, 27, MET_D)
    for cx, r, ang in ((8, 6, -2.3), (24, 4, -0.6)):       # two dials, reading differently
        DC(cx, 12, r, MET_D)
        DC(cx, 12, r - 1, (226, 222, 204))
        RG(cx, 12, r, MET_XL)
        for k in range(8):
            a = k * math.pi / 4
            P(cx + math.cos(a) * (r - 2), 12 + math.sin(a) * (r - 2), MET_D)
        LN(cx, 12, cx + math.cos(ang) * (r - 2), 12 + math.sin(ang) * (r - 2), RED_L)
        P(cx, 12, INK)
        R(cx - 1, 12 + r, cx + 1, 22, MET)                 # its stalk
    R(15, 12, 18, 22, MET)                                 # the relief valve
    R(15, 12, 15, 22, MET_L)
    for k in range(4):                                     # its spring
        R(13, 11 - k * 2, 20, 11 - k * 2, MET_L)
        P(13, 10 - k * 2, MET_D)
    R(14, 2, 19, 4, MET_D)                                 # the cap, lifting
    R(14, 2, 19, 2, MET_L)
    for k in range(3):
        P(16 + (k % 2), 1 - k, (200, 216, 224))


def air_manifold():
    R(2, 14, 29, 18, MET)                                  # the main
    R(2, 14, 29, 14, MET_L)
    R(2, 18, 29, 19, MET_D)
    for x in (8, 17, 24):                                  # flanges
        R(x - 2, 13, x + 3, 13, MET_D)
        R(x - 2, 19, x + 3, 19, MET_D)
    for x in (8, 17):                                      # two branches, shut
        R(x, 9, x + 1, 14, MET)
        P(x, 9, MET_L)
        RG(x, 7, 2, BRASS_L)
        P(x, 7, BRASS)
    R(24, 9, 25, 14, MET)                                  # the third, open
    RG(24, 7, 2, BRASS_L)
    P(24, 7, BRASS)
    for k in range(8):                                     # its hose, off and whipping
        x, y = 25 + int(2 * math.sin(k / 1.3)), 5 - k
        if y < 1:
            break
        R(x, y, x + 1, y, WOOD_D)
        P(x, y, WOOD)
    for k in range(4):                                     # the jet out of the end
        P(28 - k, 1 + k // 2, (214, 230, 238) if k < 2 else (150, 170, 182))
    DC(6, 24, 4, MET_D)                                    # gauge hung under the main
    DC(6, 24, 3, (226, 222, 204))
    LN(6, 24, 8, 22, RED_L)
    P(6, 24, INK)
    R(5, 19, 7, 21, MET)
    for x in (15, 26):                                     # wall brackets
        R(x, 19, x + 2, 27, MET_D)
        R(x, 27, x + 2, 27, MET_L)


# ── laboratory: containment ─────────────────────────────────────────────────
def blast_shield():
    R(2, 4, 29, 26, MET_D)                                 # the frame
    R(2, 4, 29, 5, MET_L)
    R(6, 8, 25, 22, GLASS)                                 # laminated glass
    R(6, 8, 25, 8, GLASS_L)
    for k in range(3):                                     # laminations, seen edge-on
        R(6, 9 + k, 25, 9 + k, (96, 128, 138))
    for k in range(4):                                     # reflection streaks
        LN(9 + k * 5, 21, 14 + k * 5, 9, GLASS_L)
    sx, sy = 17, 15                                        # and a star crack in it
    for k in range(7):
        a = k * 0.9
        LN(sx, sy, sx + math.cos(a) * (3 + k % 3), sy + math.sin(a) * (3 + k % 3), MET_XL)
    DC(sx, sy, 1.4, MET_XL)
    for x in (4, 27):                                      # bolts
        for y in (7, 15, 23):
            P(x, y, MET_XL)
    R(2, 26, 29, 28, MET)
    R(2, 26, 29, 26, MET_L)


def hatched_rock(x0, y0, x1, y1, step=4):
    """Solid rock, with the diagonal hatch the game's terrain reads by."""
    R(x0, y0, x1, y1, ROCK_M)
    for d in range(int(x0 - (y1 - y0)) - 1, int(x1) + 1, step):
        for k in range(int(y1 - y0) + 1):
            x, y = d + k, y0 + k
            if x0 <= x <= x1:
                P(x, y, ROCK_D)


def terrain_jamb(y0, y1, mouth_x0, mouth_x1, top=True, x0=1, x1=30):
    """A wedge of terrain narrowing to the mouth of a doorway. Every pixel of it is solid,
    which is the whole reason a door has to be the thing that fills the gap."""
    span = y1 - y0
    for k in range(span + 1):
        t = k / max(span, 1)
        if not top:
            t = 1 - t
        a = x0 + (mouth_x0 - x0) * t
        b = x1 - (x1 - mouth_x1) * t
        y = y0 + k
        R(a, y, b, y, ROCK_M)
        P(a, y, ROCK_L)
        P(b, y, ROCK_D)
    for d in range(int(x0 - span) - 1, int(x1) + 1, 4):    # the hatch through it
        for k in range(span + 1):
            t = k / max(span, 1)
            tt = t if top else 1 - t
            y, x = y0 + k, d + k
            if x0 + (mouth_x0 - x0) * tt <= x <= x1 - (x1 - mouth_x1) * tt:
                P(x, y, ROCK_D)


def hazard_slab(x0, y0, x1, y1, rib_every=13):
    """The moving part: a steel slab with diagonal hazard stripes, which is what reads as
    *door* at this size. Ribs break the stripes up so it does not shimmer."""
    R(x0, y0, x1, y1, MET)
    R(x0, y0, x1, y0, MET_XL)
    R(x0, y1, x1, y1, MET_D)
    R(x0, y0, x0, y1, MET_L)
    R(x1, y0, x1, y1, MET_D)
    for d in range(int(x0 - (y1 - y0)) - 2, int(x1) + 2, 5):
        for k in range(int(y1 - y0) + 1):
            x, y = d + k, y0 + k
            if x0 < x < x1 and y0 < y < y1:
                P(x, y, F_MID)
                if x + 1 < x1:
                    P(x + 1, y, F_MID)
    for y in range(int(y0) + rib_every, int(y1) - 2, rib_every):
        R(x0, y, x1, y + 1, MET_D)
        R(x0, y, x1, y, MET)


def blast_doors():
    """Drawn tall, because a door is tall: 28x48 rather than squeezed into the square.
    Closed, the slab is the pixels in the gap; open, they are up in the recess over the
    head and the way through is simply empty."""
    terrain_jamb(0, 13, 9, 18, True, 0, 27)                # roof, narrowing to the mouth
    terrain_jamb(34, 47, 9, 18, False, 0, 27)              # floor, doing the same
    for x in (8, 19):                                      # the guides the slab runs in
        R(x, 8, x, 37, MET_D)
        P(x, 8, MET_L)
        for y in range(11, 36, 6):
            P(x, y, MET)
    R(9, 6, 18, 10, MET_D)                                 # the recess it lifts into
    R(9, 6, 18, 6, MET)
    for x in range(10, 18, 3):
        P(x, 9, MET_L)
    hazard_slab(9, 11, 18, 35, 11)                         # the slab, down and shut
    R(9, 35, 18, 36, MET_D)                                # its shoe, on the sill
    P(10, 12, MET_XL)
    P(17, 34, MET_D)
    for k in range(3):                                     # chain to the counterweight
        P(13, 5 - k, MET_L)
        P(14, 4 - k, MET_D)


def airlock():
    """Wide rather than square, because it is a length of roadway with two doors in it:
    the first lifted into its recess so the way is open, the second down and shut. Never
    both open, which is the whole mechanism."""
    hatched_rock(0, 0, 59, 10)                             # roof
    R(0, 10, 59, 10, ROCK_D)
    R(0, 0, 59, 0, ROCK_L)
    hatched_rock(0, 29, 59, 39)                            # floor
    R(0, 29, 59, 29, ROCK_L)
    for x0 in (12, 38):                                    # guides and recess for each slab
        for x in (x0 - 1, x0 + 10):
            R(x, 8, x, 30, MET_D)
            for y in range(12, 29, 5):
                P(x, y, MET)
        R(x0 - 1, 5, x0 + 10, 9, MET_D)
        R(x0 - 1, 5, x0 + 10, 5, MET)
    hazard_slab(12, 6, 22, 13, 9)                          # first slab: up, way open
    R(12, 13, 22, 14, MET_D)
    for k in range(5):                                     # air moving through the gap
        P(24 + k * 2, 17 + k, CYAN)
    for k in range(4):                                     # and boots on the floor
        P(16 + k * 4, 28, DIRT_L)
    hazard_slab(38, 9, 48, 28, 9)                          # second slab: down, shut
    R(38, 28, 48, 29, MET_D)
    for k in range(3):                                     # its chain, taking the weight
        P(43, 4 - k, MET_L)
        P(44, 3 - k, MET_D)
    DC(30, 15, 3, MET_D)                                   # the interlock, on the wall
    DC(30, 15, 2, RED_L)
    P(30, 15, F_HOT)
    R(30, 11, 30, 13, MET_D)
    DC(30, 21, 2, MET_D)
    DC(30, 21, 1.2, (58, 78, 58))
    R(30, 18, 30, 19, MET_D)


def sample_cores():
    R(3, 4, 29, 27, WOOD_D)                                # the rack
    R(3, 4, 29, 4, WOOD)
    for y in (11, 18, 25):
        R(3, y, 29, y + 1, WOOD)
        R(3, y, 29, y, WOOD_L)
    for row, y in enumerate((10, 17, 24)):                 # cores lying in it
        for k in range(3):
            x = 5 + k * 8
            if row == 2 and k == 1:
                continue
            stone = ROCK_M if (row + k) % 2 else DIRT
            lit = ROCK_L if (row + k) % 2 else DIRT_L
            R(x, y - 4, x + 6, y - 1, stone)
            R(x, y - 4, x + 6, y - 4, lit)
            DC(x + 6, y - 2, 1.6, stone)
            P(x + 1, y - 2, PALE_G)                        # the label
    R(13, 20, 16, 23, ROCK_M)                              # the broken one
    R(13, 20, 16, 20, ROCK_L)
    R(17, 21, 19, 23, ROCK_M)
    for k in range(4):
        P(13 + k * 2, 26, ROCK_D)


LAB_ICONS = [
    ("LAB - POWER AND HEAT", [
        ("MuffleFurnace", "MUFFLE FURNACE", muffle_furnace),
        ("Dynamo", "DYNAMO", dynamo),
        ("BatteryBank", "BATTERY BANK", battery_bank),
        ("Transformer", "TRANSFORMER", transformer),
        ("ArcLamp", "ARC LAMP", arc_lamp),
        ("Wimshurst", "SPARK GAP", wimshurst),
    ]),
    ("LAB - PRESSURE AND GAS", [
        ("GasCylinders", "GAS CYLINDERS", gas_cylinders),
        ("PressureGauges", "GAUGES / RELIEF", pressure_gauges),
        ("AirManifold", "AIR MANIFOLD", air_manifold),
    ]),
    ("LAB - CONTROL", [
        ("KnifeSwitchBoard", "SWITCHBOARD", knife_switch_board),
        ("Electromagnet", "ELECTROMAGNET", electromagnet),
        ("AlarmPanel", "ALARM / LAMPS", alarm_panel),
    ]),
    ("LAB - CARRIED", [
        ("BatteryCell", "BATTERY CELL", battery_cell, (18, 29)),
        ("HandMagnet", "HAND MAGNET", hand_magnet, (23, 29)),
    ]),
    ("LAB - CONTAINMENT", [
        ("BlastShield", "BLAST SHIELD", blast_shield),
        ("BlastDoors", "BLAST DOORS", blast_doors, (28, 48)),
        ("Airlock", "AIRLOCK PAIR", airlock, (60, 40)),
        ("SampleCores", "SAMPLE CORES", sample_cores),
    ]),
]


def flat(catalogue=None):
    """(group, name, label, fn, w, h) per icon. An entry may carry its own (w, h) as a
    fourth element: 32x32 suits most objects, but a door is twice as tall as it is wide
    and a length of roadway is wider than it is tall, and squeezing either into the square
    is what makes them look compressed."""
    out = []
    for group, items in (catalogue or ICONS):
        for item in items:
            name, label, fn = item[0], item[1], item[2]
            w, h = item[3] if len(item) > 3 else (S, S)
            out.append((group, name, label, fn, w, h))
    return out


def draw_one(fn, ox=0, oy=0, seed=7):
    global _OX, _OY
    _OX, _OY = ox, oy
    fn()
    _OX, _OY = 0, 0


def icons_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.abspath(os.path.join(here, "..", OUT_DIR))
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


SHEET_W = 394                  # the contact sheet's width, in native pixels
GAP, HEAD_H, LABEL_H = 9, 11, 12


def sheet_layout(catalogue):
    """Place icons of mixed sizes left to right, wrapping when the row runs out, and
    return the placements plus the height the sheet needs."""
    places = []
    y = 22
    for group, items in catalogue:
        heads = (group, y)
        y += HEAD_H
        x, line_h = 10, 0
        for item in flat([(group, items)]):
            _, name, label, fn, w, h = item
            cell = max(w, text_w(label))
            if x + cell > SHEET_W - 8 and line_h:          # wrap within the group
                y += line_h + LABEL_H + 4
                x, line_h = 10, 0
            places.append((heads, name, label, x, y, w, h))
            x += cell + GAP
            line_h = max(line_h, h)
        y += line_h + LABEL_H + 8
    return places, y + 2


def build_sheet(catalogue, sheet_name, title, seed0=6100, path=None):
    d = icons_dir()
    shots = {}
    for i, (group, name, label, fn, w, h) in enumerate(flat(catalogue)):
        new_canvas(w, h, seed=seed0 + i * 7, bg=KEY)
        draw_one(fn)
        outline(0, 0, w - 1, h - 1)
        shots[name] = snapshot()
        save_keyed(os.path.join(d, "Icon_%s.png" % name), scale=4)

    # ── the contact sheet ──────────────────────────────────────────────────
    places, height = sheet_layout(catalogue)
    new_canvas(SHEET_W, height, seed=990, bg=(22, 24, 28))
    cw, ch = canvas_size()
    for y in range(ch):                                    # a plain graded backdrop
        rect(0, y, cw - 1, y, (18 + y // 22, 20 + y // 22, 24 + y // 20))
    text(8, 7, title, PALE_G)
    note = "TRANSPARENT PNG  /  ICONS/ICON_NAME.PNG"
    tag(cw - 6 - text_w(note), 6, note, (150, 165, 185))

    drawn = set()
    for (group, gy), name, label, x, y, w, h in places:
        if group not in drawn:                             # the group's rule and title
            rect(8, gy, cw - 9, gy, (60, 68, 80))
            text(8, gy + 3, group, CYAN)
            drawn.add(group)
        rect(x - 2, y - 1, x + w + 1, y + h, (28, 31, 36))
        frame(x - 2, y - 1, x + w + 1, y + h, (44, 48, 56))
        blit(shots[name], x, y)
        text(x - 2, y + h + 3, label, LABEL, shadow=False)

    here = os.path.dirname(os.path.abspath(__file__))
    sheet = path or os.path.abspath(os.path.join(here, "..", sheet_name))
    save(sheet, scale=3)
    print("%d icons -> %s" % (len(flat(catalogue)), d))
    return sheet


def build():
    build_sheet(ICONS, "IconSheet_Objects.png", "PHYSFUN - INTERACTIVE OBJECTS", 6100)
    build_sheet(LAB_ICONS, "IconSheet_Lab.png", "PHYSFUN - LABORATORY OBJECTS", 7300)


if __name__ == "__main__":
    build()
