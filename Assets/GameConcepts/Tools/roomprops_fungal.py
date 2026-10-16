"""Room props, part 8: the fungal deep - what the mushroom rooms (S47 on) are built round.

The mine's rooms are loaded with kegs, bells, logs and nets; these are the same verbs
grown instead of made:

* HUNG - a spore pod and a cluster of sacs that burst into fire (Explosive, like a keg),
  a mass of caps grown down from the roof, a cocoon with someone in it, and the cult's
  lights: a glow-bulb in a twig cage and a censer of smouldering spore. Each hangs by an
  `Eye` (ANCHORS) on a Hazards/Rope set up by the room, so it swings, and a cut rope drops
  it on whoever is under it.
* LOOSE - puffballs that roll and go up, rotten logs crusted with brackets, a fallen cap,
  a sack and a keg of spore dust, a crate and a barrow of the crop.
* THE CULT'S THINGS - Props.Decor clutter: baskets, stools, a cap table, a grow rack,
  strings of drying caps, jars of glowing spore, skulls sprouting, candles in a cap, and
  the idol they pray to.
* HOUSES - what the cult builds with, in the timber's sizes so roombuild.structures lays
  it the same way (its KIT): stem slabs for walls and floors, a cap slice for a hatch lid,
  cap shingles for a roof, a door of cap flesh; a bed and a shelf to furnish them.
* BRACKETS - shelf fungus big enough to stand on, grown out of the wall: a static
  one-way deck (Props.OneWayPlatform), the way up a fungal shaft.

Built by `roomprops.py`; read its docstring for what the entries mean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402,F401
from roomprops_hung import eye  # noqa: E402
from roomprops_flora import (dome, ell, stem, bent, strand, speckle, GC_RAMP, GV_RAMP, GY_RAMP,  # noqa: E402
                             GA_RAMP, GSTEM_RAMP, STEM_RAMP, CAP_RAMP, GILL, MOSS_RAMP, FMOSS_RAMP,
                             ROOT_RAMP, PUFF_RAMP, RED_RAMP, SPOT)

TITLE = "THE FUNGAL DEEP"
SEED = 8800

# ── palette ──────────────────────────────────────────────────────────────────
FLESH_RAMP = ((52, 34, 46), (82, 54, 70), (116, 80, 96), (150, 112, 122))    # pod and cap flesh
SAC_RAMP = ((60, 46, 64), (92, 72, 96), (128, 104, 128), (170, 150, 168))     # spore sacs
MYC_RAMP = ((96, 92, 84), (132, 128, 116), (168, 162, 146), (198, 192, 174))  # mycelium, white rot
ROT_RAMP = ((42, 34, 30), (64, 52, 42), (88, 72, 54), (112, 94, 70))          # rotten wood
BONE_RAMP = ((110, 104, 86), (146, 140, 116), (180, 172, 146), (206, 200, 176))
WAX_RAMP = ((150, 136, 104), (186, 172, 132), (216, 206, 168))
VEIN = GV_RAMP[2]
DUST = (150, 140, 110)
SACK_RAMP = (SACK_D, SACK, SACK_L)
SOIL_C = (44, 36, 30)


def pod_body(cx, top, rx, ry, ramp, veins=True):
    """An egg-shaped pod hanging from its top: narrow at the stalk, fat at the bottom."""
    for y in range(int(top), int(top + 2 * ry) + 1):
        t = (y - top) / (2.0 * ry)
        hw = rx * math.sin(math.pi * min(1.0, t * 0.95 + 0.05)) * (0.55 + 0.45 * t)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            dshade(x, y, 0.85 - 0.5 * (x - cx + hw) / max(1.0, 2 * hw) - 0.25 * t, ramp)
    if veins:
        for k in range(3):
            x0 = cx - rx * 0.4 + k * rx * 0.4
            for y in range(int(top + ry * 0.4), int(top + 2 * ry) - 1, 1):
                x = int(round(x0 + 1.2 * math.sin(y * 0.7 + k)))
                if AT(x, y) != KEY:
                    P(x, y, VEIN if (y + k) % 3 else GV_RAMP[3])


def threads(x0, y0, x1, y1, n, ramp=MYC_RAMP):
    """White-rot threads across what is drawn there."""
    for _ in range(n):
        x, y = x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)
        for k in range(int(3 + rnd() * 6)):
            if AT(int(x), int(y)) != KEY:
                P(int(x), int(y), ramp[2] if k % 2 else ramp[1])
            x += rnd() * 2 - 1
            y += rnd() * 1.4 - 0.4


# ═══════════════════════════════════════════════════════════════════════════
#  HUNG
# ═══════════════════════════════════════════════════════════════════════════
def spore_pod():
    """A spore pod as big as a man's chest, veined violet, ready to burst."""
    eye(6.5, 0, 2.5, ROOT_RAMP)
    R(6, 5, 7, 7, ROOT_RAMP[1])
    pod_body(7, 7, 7, 10, SAC_RAMP)
    P(4, 12, SAC_RAMP[3])
    P(5, 11, SAC_RAMP[3])
    R(5, 27, 8, 27, SAC_RAMP[0])


def spore_sacs():
    """Three sacs off one stalk, the middle one heaviest."""
    eye(6.5, 0, 2.5, ROOT_RAMP)
    R(6, 5, 7, 8, ROOT_RAMP[1])
    R(3, 8, 10, 8, ROOT_RAMP[1])
    pod_body(3, 9, 3, 4, SAC_RAMP, veins=False)
    pod_body(7, 9, 4, 6, SAC_RAMP)
    pod_body(11, 9, 2.6, 4, SAC_RAMP, veins=False)


def hanging_caps():
    """A mass of caps grown down from the roof - heavy as a man, and over someone's head.
    Each hangs on its own stalk off one knot, its cap's round side down."""
    eye(14.5, 0, 2.5, ROOT_RAMP)
    for x in range(10, 20):                                   # the knot the stalks grow from
        for y in range(5, 10):
            dshade(x, y, 0.75 - 0.04 * x - 0.04 * y, ROOT_RAMP)
    caps = ((5, 15, 4.5), (24, 13, 4.5), (11, 19, 4.0), (19, 22, 5.0), (14, 11, 3.0))
    for cx, base, r in caps:                                  # stalks, two wide
        x0, y0 = 14 + (cx - 14) * 0.3, 8
        n = max(1, base - y0)
        for k in range(n + 1):
            t = k / float(n)
            x = int(round(x0 + (cx - x0) * t))
            y = int(round(y0 + (base - y0) * t))
            dshade(x, y, 0.8, STEM_RAMP)
            dshade(x + 1, y, 0.35, STEM_RAMP)
    for cx, base, r in caps:                                  # caps, gills up, dome down
        for y in range(int(base), int(base + r) + 1):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = (x - cx - 0.5) / r, (y - base) / (r * 0.85)
                if dx * dx + dy * dy <= 1.0:
                    dshade(x, y, 0.95 - 0.55 * dy - 0.2 * dx, FLESH_RAMP)
        R(int(cx - r + 1), int(base), int(cx + r), int(base), GILL)
        P(int(cx - r * 0.3), int(base + r * 0.5), FLESH_RAMP[3])


def cocoon():
    """A man wrapped in mycelium and hung up to be eaten. His boots stick out."""
    eye(6.5, 0, 2.5, ROOT_RAMP)
    R(6, 5, 7, 7, MYC_RAMP[1])
    for y in range(7, 27):
        t = (y - 7) / 20.0
        hw = 2 + 3.2 * math.sin(math.pi * min(1.0, 0.15 + t * 0.85))
        for x in range(int(7 - hw), int(7 + hw) + 1):
            dshade(x, y, 0.85 - 0.4 * (x - 7 + hw) / (2 * hw) - 0.1 * t, MYC_RAMP)
    for y in range(9, 26, 3):                                 # the wraps
        for x in range(2, 13):
            if AT(x, y) != KEY:
                P(x, y, MYC_RAMP[0])
    R(5, 27, 6, 29, ROT_RAMP[0])                              # boots
    R(8, 27, 9, 29, ROT_RAMP[0])
    R(5, 29, 6, 29, ROT_RAMP[1])
    R(8, 29, 9, 29, ROT_RAMP[1])
    R(6, 27, 8, 27, MYC_RAMP[1])
    P(6, 11, BONE_RAMP[0])                                    # a face pressed through
    P(8, 11, BONE_RAMP[0])
    P(7, 13, BONE_RAMP[0])


def glow_lantern():
    """The cult's lamp: a glowing bulb fungus grown in a cage of bent twigs."""
    eye(4, 0, 2, ROOT_RAMP)
    R(3, 4, 5, 4, ROOT_RAMP[1])
    for x0, x1 in ((1, 7),):
        for y in range(5, 14):
            P(x0, y, ROOT_RAMP[1])
            P(x1, y, ROOT_RAMP[0])
    R(1, 5, 7, 5, ROOT_RAMP[2])
    R(1, 14, 7, 14, ROOT_RAMP[1])
    ell(4, 9.5, 2.4, 3.6, GC_RAMP, lit=1.1)
    P(4, 8, GC_RAMP[3])
    P(3, 9, GC_RAMP[3])
    P(4, 7, (220, 250, 244))


def fungal_censer():
    """A censer of smouldering spore on three cords, glowing violet through its holes."""
    eye(4, 0, 2, IRON_RAMP)
    LN(4, 4, 1, 8, ROOT_RAMP[1])
    LN(4, 4, 7, 8, ROOT_RAMP[1])
    for y in range(8, 14):
        hw = 3 if y < 12 else 2
        for x in range(4 - hw, 5 + hw):
            dshade(x, y, 0.6 - 0.08 * x, IRON_RAMP)
    for x, y in ((2, 10), (4, 11), (6, 10)):
        P(x, y, GV_RAMP[3])
    R(1, 8, 7, 8, IRON_RAMP[3])


# ═══════════════════════════════════════════════════════════════════════════
#  LOOSE
# ═══════════════════════════════════════════════════════════════════════════
def puff_ball(cx, cy, r):
    ell(cx, cy, r, r * 0.92, PUFF_RAMP)
    for _ in range(int(r * r * 0.6)):                         # warts
        a, d = rnd() * 6.28, rnd() * r * 0.8
        x, y = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.9)
        if AT(x, y) != KEY:
            P(x, y, PUFF_RAMP[3] if y < cy else PUFF_RAMP[1])


def giant_puffball():
    """A puffball the size of a barrel, dry and full of spore: it rolls, and a shot or a
    flame sets it off like a keg."""
    puff_ball(11, 10, 10)
    R(8, 0, 12, 1, PUFF_RAMP[0])                              # the split crown
    P(10, 2, PUFF_RAMP[0])
    R(7, 19, 15, 19, PUFF_RAMP[0])


def puffball_small():
    """A small dry puffball - a grenade lying about."""
    puff_ball(6, 5.5, 5.4)
    P(6, 0, PUFF_RAMP[0])


def rot_log():
    """A rotten log furred with white rot and shelf fungus; it rolls, and it burns."""
    for x in range(0, 70):
        for y in range(2, 12):
            t = (y - 2) / 9.0
            dshade(x, y, 0.85 - 0.75 * t + 0.1 * math.sin(x * 0.4), ROT_RAMP)
    for x in range(0, 70, 7):                                 # bark furrows
        LN(x, 3, x + 4, 10, ROT_RAMP[0])
    R(0, 4, 1, 10, ROT_RAMP[3])                               # the cut end
    R(68, 4, 69, 10, ROT_RAMP[0])
    threads(4, 3, 66, 11, 9)
    for x, w in ((12, 6), (34, 8), (52, 5)):                  # brackets along the top
        for k in range(w):
            dshade(x + k, 1, 0.9, CAP_RAMP)
            dshade(x + k, 2, 0.5, CAP_RAMP)
        P(x - 1, 2, CAP_RAMP[0])
    for x in (24, 26, 44, 61):                                # little caps
        P(x, 1, FLESH_RAMP[2])
        P(x, 0, FLESH_RAMP[3])


def rot_log_short():
    """A length of rotten log."""
    for x in range(0, 36):
        for y in range(1, 11):
            t = (y - 1) / 9.0
            dshade(x, y, 0.85 - 0.75 * t + 0.1 * math.sin(x * 0.5), ROT_RAMP)
    for x in range(2, 36, 7):
        LN(x, 2, x + 3, 9, ROT_RAMP[0])
    R(0, 3, 1, 9, ROT_RAMP[3])
    threads(3, 2, 33, 10, 4)
    for k in range(6):
        dshade(14 + k, 0, 0.9, CAP_RAMP)
        dshade(14 + k, 1, 0.45, CAP_RAMP)


def fallen_cap():
    """The cap of a giant mushroom, come down: a slab of flesh, gills under it."""
    for x in range(0, 44):
        u = (x - 21.5) / 22.0
        top = int(round(2 + 9 * u * u))
        for y in range(top, 14):
            dshade(x, y, 0.85 - 0.35 * (y - top) / 12.0 - 0.15 * u, FLESH_RAMP)
    for x in range(1, 43, 2):
        R(x, 12, x, 13, GILL)
    for x, y in ((10, 6), (20, 3), (30, 5), (16, 8), (36, 8)):
        P(x, y, FLESH_RAMP[3])


def spore_sack():
    """A sack of spore dust, tied at the neck: burns like powder."""
    tpl(0, 0, [
        "....aab.....",
        "....bbd.....",
        ".....rR.....",
        "...abbbbd...",
        "..abbbbbbd..",
        ".abbabbbbbd.",
        ".abbbbbbbbd.",
        "abbbbbbvVbbd",
        "abbbbbvVvbbd",
        "abbbbbbbbbdd",
        "abbbbbbbbbdd",
        ".bbbbbbbbdd.",
        "..ddddddddd.",
    ], {'a': SACK_L, 'b': SACK, 'd': SACK_D, 'r': TIM_L, 'R': TIM_M, 'v': GV_RAMP[2], 'V': GV_RAMP[1]})
    for x, y in ((3, 6), (6, 4), (8, 9), (4, 10)):
        P(x, y, DUST)


def spore_keg():
    """A keg the cult packs spore into - their powder."""
    for y in range(0, 11):
        for x in range(1 if y in (0, 10) else 0, 8 if y in (0, 10) else 9):
            dshade(x, y, 0.75 - 0.06 * x, TIM_RAMP)
    R(0, 2, 8, 2, IRON_D)
    R(0, 8, 8, 8, IRON_D)
    R(2, 4, 6, 6, GV_RAMP[1])
    P(4, 5, GV_RAMP[3])
    R(1, 0, 7, 0, TIM_L)


def mushroom_crate():
    """A crate heaped with the crop."""
    for y in range(4, 17):
        for x in range(0, 14):
            dshade(x, y, 0.75 - 0.35 * (x + y) / 30, TIM_RAMP)
    box(0, 4, 13, 16, TIM_D, TIM, TIM_L)
    for y in (8, 12):
        R(1, y, 12, y, TIM_D)
    for cx, top, r in ((3, 3, 2.4), (7, 2, 3), (11, 3, 2.2)):
        dome(cx, top + 1, r, 2, CAP_RAMP)
    R(1, 4, 12, 4, GILL)


def mushroom_barrow():
    """A barrow of the crop, its wheel at the front."""
    for x in range(2, 22):                                    # the tray, open at the top
        P(x, 13, TIM_D)
        P(x, 12, TIM)
    for y in range(5, 13):
        P(2 + (12 - y) // 3, y, TIM_M)
        P(21 - (12 - y) // 4, y, TIM_D)
    for cx, top, r in ((7, 6, 3), (12, 5, 3.4), (17, 6, 2.6), (10, 9, 2.4), (15, 9, 2.6)):
        dome(cx, top + 2, r, 2.2, CAP_RAMP)
    LN(0, 10, 4, 12, TIM_M)                                   # handles
    LN(18, 13, 25, 12, TIM_M)
    for y in range(14, 19):                                   # wheel
        for x in range(19, 24):
            if (x - 21) ** 2 + (y - 16) ** 2 <= 5:
                P(x, y, IRON_D if (x - 21) ** 2 + (y - 16) ** 2 > 1 else IRON_M)
    R(5, 14, 5, 18, TIM_D)                                    # leg


# ═══════════════════════════════════════════════════════════════════════════
#  THE CULT'S THINGS (clutter)
# ═══════════════════════════════════════════════════════════════════════════
def crop_basket():
    """A wicker basket of picked caps."""
    for cx, r in ((3, 2.2), (6, 2.6), (8.5, 2)):
        dome(cx, 3, r, 2, CAP_RAMP)
    R(0, 3, 10, 3, SACK)
    for y in range(4, 9):
        for x in range(0 + (y == 8), 11 - (y == 8)):
            P(x, y, TIM_M if (x + y) % 2 else TIM)
    R(1, 9, 9, 9, TIM_D)


def cap_stool():
    """A stool sawn out of a giant mushroom's stem."""
    dome(4.5, 3, 4.6, 3, FLESH_RAMP)
    R(1, 4, 8, 4, GILL)
    stem(3, 6, 5, 9, STEM_RAMP)


def cap_table():
    """A table: a slice of giant cap on a stem."""
    for x in range(0, 22):
        dshade(x, 0, 0.95, FLESH_RAMP)
        dshade(x, 1, 0.6, FLESH_RAMP)
        dshade(x, 2, 0.3, FLESH_RAMP)
    for x in range(1, 21, 2):
        P(x, 3, GILL)
    stem(8, 13, 3, 11, STEM_RAMP)
    R(6, 11, 15, 11, STEM_RAMP[0])


def grow_rack():
    """A rack of logs stacked to grow the crop on, caps sprouting all along them."""
    for x in (0, 21):
        for y in range(0, 26):
            dshade(x, y, 0.8 if x == 0 else 0.3, TIM_RAMP)
    for y0 in (3, 11, 19):
        R(0, y0 + 4, 21, y0 + 4, TIM_D)
        for x in range(1, 21):
            for y in range(y0, y0 + 4):
                dshade(x, y, 0.75 - 0.15 * (y - y0), ROT_RAMP)
        for x in range(2, 20, 3):
            P(x, y0 - 1, FLESH_RAMP[3] if (x + y0) % 2 else CAP_RAMP[2])
            P(x, y0, CAP_RAMP[1])
    R(0, 25, 21, 25, TIM_D)


def drying_string():
    """Caps strung up to dry, nailed to the back wall at both ends."""
    for x in range(0, 24):
        y = int(round(1 + 3 * math.sin(math.pi * x / 23.0)))
        P(x, y, SACK_L)
        if 1 < x < 23 and x % 3 == 0:
            P(x, y + 1, SACK)
            dome(x, y + 4, 1.8, 1.6, CAP_RAMP)
            P(x, y + 5, GILL)
    P(0, 0, IRON_M)
    P(23, 0, IRON_M)


def spore_jars():
    """Jars of glowing spore on a board."""
    R(0, 9, 13, 9, TIM_D)
    R(0, 8, 13, 8, TIM_M)
    for x0, h, ramp in ((1, 6, GC_RAMP), (5, 5, GV_RAMP), (9, 7, GY_RAMP)):
        R(x0, 8 - h, x0 + 2, 8 - h, TIM_M)                     # cork
        for y in range(9 - h, 8):
            for x in range(x0, x0 + 3):
                P(x, y, ramp[2] if (x + y) % 2 else ramp[1])
        P(x0, 9 - h, ramp[3])


def skull_shrooms():
    """A skull with mushrooms come up through it."""
    tpl(0, 3, [
        ".bBBb.",
        "bBBBBd",
        "BoBBod",
        "BBBBBd",
        ".bddd.",
    ], {'b': BONE_RAMP[2], 'B': BONE_RAMP[1], 'd': BONE_RAMP[0], 'o': INK})
    for cx, top in ((1, 1), (4, 0), (6, 2)):
        P(cx, top + 2, STEM_RAMP[2])
        P(cx, top + 1, CAP_RAMP[2])
        P(cx - 1, top + 1, CAP_RAMP[1])


def cap_candles():
    """Candles stuck in a cut cap - the cult's altar lights."""
    dome(6, 9, 6, 3, FLESH_RAMP)
    R(0, 10, 12, 10, GILL)
    for x, h in ((3, 4), (6, 6), (9, 3)):
        R(x, 9 - h, x, 7, WAX_RAMP[1])
        P(x, 9 - h, WAX_RAMP[2])
        P(x, 8 - h, F_MID)
        P(x, 7 - h, F_HOT)


def fungal_idol():
    """What the cult prays to: a figure of root and cap, glowing at the heart."""
    for x in range(2, 15):                                    # the plinth of mycelium
        for y in range(22, 26):
            dshade(x, y, 0.7 - 0.03 * x, MYC_RAMP)
    for y in range(9, 22):                                    # the body, a twisted stem
        hw = 2 + (y - 9) // 6
        dx = int(round(math.sin(y * 0.5)))
        for x in range(8 - hw + dx, 9 + hw + dx):
            dshade(x, y, 0.75 - 0.1 * (x - 8 - dx), ROOT_RAMP)
    dome(8.5, 8, 7.5, 6, FLESH_RAMP)                          # the head, a cap
    R(1, 9, 15, 9, GILL)
    for x, y in ((5, 4), (9, 3), (12, 6), (7, 6)):
        P(x, y, GV_RAMP[3])
    ell(8, 15, 1.6, 2.2, GV_RAMP, lit=1.1)                    # the glowing heart
    for y in range(11, 22, 2):                                # arms of root
        P(4 + (y % 3), y, ROOT_RAMP[2])
        P(12 - (y % 3), y, ROOT_RAMP[1])


# ═══════════════════════════════════════════════════════════════════════════
#  BRACKETS (one-way decks grown out of the wall)
# ═══════════════════════════════════════════════════════════════════════════
BRACKET_W, BRACKET_H = 40, 7


def _bracket(mirror, glow):
    """Shelf fungus wide enough to stand on, grown out of the rock: a one-way deck. Drawn
    filling its canvas, so the top row is the floor; the wall end is the left one (the
    right one when mirrored - prefabs can't be flipped, so both are drawn)."""
    def X(x):
        return BRACKET_W - 1 - x if mirror else x
    for x in range(BRACKET_W):
        u = x / (BRACKET_W - 1.0)
        depth = int(round(BRACKET_H - 1 - 3 * u * u))
        for y in range(0, depth + 1):
            dshade(X(x), y, 0.95 - 0.55 * y / max(1, depth) - 0.1 * u, CAP_RAMP)
        if x % 3 == 1 and depth > 2:
            P(X(x), depth, GILL)
        if glow and 0 < x < BRACKET_W - 4 and depth > 1:
            P(X(x), depth, GY_RAMP[2] if x % 2 else GY_RAMP[3])
    for x in range(2, BRACKET_W - 2, 5):                      # growth rings on top
        P(X(x), 0, CAP_RAMP[3])
        P(X(x + 1), 1, CAP_RAMP[1])
    R(X(0), 0, X(0), BRACKET_H - 1, CAP_RAMP[0])


def bracket_deck():
    """Shelf fungus to stand on, its wall to the left: a one-way deck."""
    _bracket(False, False)


def bracket_deck_r():
    """The same, its wall to the right."""
    _bracket(True, False)


def bracket_deck_glow():
    """The kind that glows green under its lip, wall to the left."""
    _bracket(False, True)


def bracket_deck_glow_r():
    """The glowing kind, wall to the right."""
    _bracket(True, True)


# ═══════════════════════════════════════════════════════════════════════════
#  HOUSES - the cult builds like the miners do, in its own stuff
# ═══════════════════════════════════════════════════════════════════════════
# The same sizes as roomprops_structures' timber, so roombuild.structures lays these with
# the same code (its KIT names which set a house is built of).
H_DECK_W, H_DECK_H = 20, 4
H_FLOOR_W, H_FLOOR_H = 20, 6
H_WALL_W, H_WALL_H = 6, 12
H_DOOR_W, H_DOOR_H = 6, 30
H_ROOF_W, H_ROOF_H = 20, 5


def stem_wall():
    """Slabs of giant stem stood on end: fibres up the face, a lit edge, a dark seam."""
    for y in range(H_WALL_H):
        P(0, y, STEM_RAMP[3])
        for x in range(1, H_WALL_W - 1):
            P(x, y, STEM_RAMP[2] if (x * 3 + y // 4) % 5 else STEM_RAMP[1])
        P(H_WALL_W - 1, y, STEM_RAMP[0])
    for x in range(H_WALL_W):
        P(x, H_WALL_H - 1, STEM_RAMP[0])
    P(2, 4, MYC_RAMP[0])


def stem_floor():
    """A floor of stem slabs laid flat on a joist of root: as thick as a wall, solid both
    ways - the way up is a hatch."""
    for x in range(H_FLOOR_W):
        P(x, 0, STEM_RAMP[3] if x % 7 else STEM_RAMP[2])
        P(x, 1, STEM_RAMP[2])
        P(x, 2, STEM_RAMP[1] if x % 9 else STEM_RAMP[0])
        P(x, 3, STEM_RAMP[0])
        P(x, 4, ROOT_RAMP[2] if (x // 3) % 4 else ROOT_RAMP[1])
        P(x, 5, ROOT_RAMP[0])
    P(0, 1, STEM_RAMP[0])
    P(0, 2, STEM_RAMP[0])


def cap_deck():
    """A slice of cap, thin: the hatch lid over a ladder (one-way)."""
    for x in range(H_DECK_W):
        P(x, 0, FLESH_RAMP[3] if x % 6 else FLESH_RAMP[2])
        P(x, 1, FLESH_RAMP[2])
        P(x, 2, FLESH_RAMP[1])
        P(x, 3, GILL if x % 2 else FLESH_RAMP[0])


def cap_roof():
    """Shingles cut from a cap, edge-on: a lit top course, two courses of scale, the gills
    showing under them."""
    for x in range(H_ROOF_W):
        P(x, 0, FLESH_RAMP[3] if x % 4 else FLESH_RAMP[2])
        P(x, 1, FLESH_RAMP[2] if x % 4 != 2 else FLESH_RAMP[1])
        P(x, 2, FLESH_RAMP[2] if x % 4 != 0 else FLESH_RAMP[0])
        P(x, 3, FLESH_RAMP[1])
        P(x, 4, GILL if x % 2 else FLESH_RAMP[0])


def cap_door():
    """A door of cap flesh on a root frame: the leaf, a rail of root top and bottom, a
    glowing knob - edge-on in its doorway, like the plank door."""
    for y in range(H_DOOR_H):
        for x in range(H_DOOR_W):
            P(x, y, FLESH_RAMP[1] if (x + y) % 5 else FLESH_RAMP[2])
        P(0, y, FLESH_RAMP[3])
        P(H_DOOR_W - 1, y, FLESH_RAMP[0])
    for y in (0, 1, H_DOOR_H - 2, H_DOOR_H - 1):
        for x in range(H_DOOR_W):
            P(x, y, ROOT_RAMP[2] if y in (0, H_DOOR_H - 2) else ROOT_RAMP[1])
    for y in (9, 20):
        for x in range(1, H_DOOR_W - 1):
            P(x, y, ROOT_RAMP[1])
    P(H_DOOR_W - 2, H_DOOR_H // 2, GC_RAMP[3])
    P(H_DOOR_W - 2, H_DOOR_H // 2 + 1, GC_RAMP[2])


def mushroom_bed():
    """A bed: a mattress of cap flesh on a frame of root, a pillow of moss."""
    for x in range(0, 26):
        P(x, 3, FLESH_RAMP[3] if x % 5 else FLESH_RAMP[2])
        P(x, 4, FLESH_RAMP[2])
        P(x, 5, FLESH_RAMP[1])
    for x in range(1, 6):
        P(x, 2, MOSS_RAMP[2])
        P(x, 1, MOSS_RAMP[3] if x % 2 else MOSS_RAMP[2])
    for x in range(0, 26):
        P(x, 6, ROOT_RAMP[1])
    for x in (0, 1, 24, 25):
        for y in range(6, 9):
            P(x, y, ROOT_RAMP[0] if x % 2 else ROOT_RAMP[2])
    R(0, 0, 0, 5, ROOT_RAMP[2])
    R(25, 2, 25, 5, ROOT_RAMP[1])


def cap_shelf():
    """A shelf of bracket fungus grown on purpose out of the back wall, a jar and a cap on
    it - the cult's cupboard."""
    for x in range(0, 18):
        dshade(x, 3, 0.9, CAP_RAMP)
        dshade(x, 4, 0.45, CAP_RAMP)
        if 1 < x < 16 and x % 2:
            P(x, 5, GILL)
    R(2, 0, 4, 2, GC_RAMP[1])
    P(3, 0, GC_RAMP[3])
    dome(11, 2, 2.4, 2, FLESH_RAMP)


def root_chair():
    """A chair grown out of root: a twisted back, a seat of cap."""
    for y in range(0, 14):
        P(1 + (y % 3 == 0), y, ROOT_RAMP[2] if y % 2 else ROOT_RAMP[1])
    for x in range(1, 9):
        P(x, 8, FLESH_RAMP[3])
        P(x, 9, FLESH_RAMP[1])
    for y in range(10, 14):
        P(7, y, ROOT_RAMP[1])
        P(2, y, ROOT_RAMP[0])


def cap_cupboard():
    """A cupboard of cap flesh on root legs, its door a slice of cap with a glowing knob."""
    for y in range(1, 22):
        for x in range(0, 14):
            dshade(x, y, 0.75 - 0.03 * x - 0.01 * y, FLESH_RAMP)
    R(0, 0, 13, 0, FLESH_RAMP[3])
    R(0, 11, 13, 11, FLESH_RAMP[0])
    R(6, 2, 6, 21, FLESH_RAMP[0])
    P(5, 7, GC_RAMP[3])
    P(8, 7, GC_RAMP[3])
    P(5, 16, GC_RAMP[2])
    P(8, 16, GC_RAMP[2])
    for x in (1, 12):
        R(x, 22, x, 23, ROOT_RAMP[1])


def drying_rack():
    """A rack of root poles with caps strung along the bars to dry."""
    for x in (0, 17):
        R(x, 0, x, 19, ROOT_RAMP[1])
        P(x, 0, ROOT_RAMP[3])
    for y in (2, 9):
        R(0, y, 17, y, ROOT_RAMP[2])
        for x in range(2, 17, 3):
            P(x, y + 1, SACK)
            dome(x, y + 4, 1.6, 1.6, CAP_RAMP)
    LN(0, 19, 4, 15, ROOT_RAMP[0])
    LN(17, 19, 13, 15, ROOT_RAMP[0])


def glow_lamp_post():
    """A lamp of the cult's: a bulb fungus grown on top of a root post."""
    R(3, 9, 4, 27, ROOT_RAMP[1])
    R(3, 9, 3, 27, ROOT_RAMP[2])
    R(1, 27, 6, 27, ROOT_RAMP[0])
    ell(3.5, 4.5, 3.2, 4, GC_RAMP, lit=1.1)
    P(3, 3, (220, 250, 244))
    R(1, 8, 6, 8, ROOT_RAMP[2])


def planter_box():
    """A box of soil with the crop coming up in it, glowing."""
    for y in range(6, 12):
        for x in range(0, 20):
            dshade(x, y, 0.7 - 0.02 * x, TIM_RAMP)
    R(0, 6, 19, 6, TIM_L)
    R(1, 5, 18, 5, SOIL_C)
    for k, x in enumerate((3, 7, 11, 15)):
        stem(x, x, 2 + k % 2, 4, GSTEM_RAMP)
        P(x, 1 + k % 2, GC_RAMP[3] if k % 2 else GY_RAMP[3])
        P(x - 1, 2 + k % 2, GC_RAMP[2] if k % 2 else GY_RAMP[2])


def myc_rug():
    """A rug of woven mycelium, laid on the floor."""
    for x in range(0, 24):
        P(x, 0, MYC_RAMP[2] if x % 3 else MYC_RAMP[3])
        P(x, 1, MYC_RAMP[1] if (x // 2) % 2 else FLESH_RAMP[1])
    P(0, 1, MYC_RAMP[0])
    P(23, 1, MYC_RAMP[0])


def gill_glow():
    """The gills of a glowing giant, as a strip stuck under its cap: what lights it."""
    for x in range(0, 16):
        P(x, 0, GC_RAMP[1])
        P(x, 1, GC_RAMP[3] if x % 2 else GC_RAMP[2])
        if x % 3 == 1:
            P(x, 2, GC_RAMP[2])


GROUPS = [
    ("HUNG", [
        ("SporePod", "SPORE POD", spore_pod, (14, 28), WOOD, "explosive"),
        ("SporeSacs", "SPORE SACS", spore_sacs, (14, 20), WOOD, "explosive"),
        ("HangingCaps", "HANGING CAPS", hanging_caps, (31, 28), WOOD, None),
        ("Cocoon", "COCOON", cocoon, (14, 30), WOOD, None),
        ("GlowLantern", "GLOW LANTERN", glow_lantern, (9, 15), WOOD, None),
        ("FungalCenser", "CENSER", fungal_censer, (9, 14), METAL, None),
    ]),
    ("LOOSE", [
        ("GiantPuffball", "GIANT PUFFBALL", giant_puffball, (22, 20), WOOD, "explosive"),
        ("PuffballSmall", "PUFFBALL", puffball_small, (12, 11), WOOD, "explosive"),
        ("RotLog", "ROT LOG", rot_log, (70, 12), WOOD, None),
        ("RotLogShort", "ROT LOG", rot_log_short, (36, 11), WOOD, None),
        ("FallenCap", "FALLEN CAP", fallen_cap, (44, 14), WOOD, None),
        ("SporeSack", "SPORE SACK", spore_sack, (12, 13), WOOD, "explosive"),
        ("SporeKeg", "SPORE KEG", spore_keg, (9, 11), WOOD, "explosive"),
        ("MushroomCrate", "CROP CRATE", mushroom_crate, (14, 17), WOOD, None),
        ("MushroomBarrow", "BARROW", mushroom_barrow, (26, 19), WOOD, None),
    ]),
    ("THE CULT'S THINGS", [
        ("CropBasket", "BASKET", crop_basket, (11, 10), WOOD, "decor"),
        ("CapStool", "STOOL", cap_stool, (10, 10), WOOD, "decor"),
        ("CapTable", "CAP TABLE", cap_table, (22, 12), WOOD, "decor"),
        ("GrowRack", "GROW RACK", grow_rack, (22, 26), WOOD, "decor"),
        ("DryingString", "DRYING CAPS", drying_string, (24, 10), WOOD, "wall"),
        ("SporeJars", "SPORE JARS", spore_jars, (14, 10), WOOD, "decor"),
        ("SkullShrooms", "SKULL", skull_shrooms, (7, 8), DEFAULT, "decor"),
        ("CapCandles", "CANDLES", cap_candles, (13, 11), WOOD, "decor"),
        ("FungalIdol", "IDOL", fungal_idol, (17, 26), WOOD, "decor"),
    ]),
    ("HOUSES", [
        ("StemWall", "STEM WALL", stem_wall, (H_WALL_W, H_WALL_H), WOOD, None),
        ("StemFloor", "STEM FLOOR", stem_floor, (H_FLOOR_W, H_FLOOR_H), WOOD, None),
        ("CapDeck", "CAP DECK", cap_deck, (H_DECK_W, H_DECK_H), WOOD, "oneway"),
        ("CapRoof", "CAP ROOF", cap_roof, (H_ROOF_W, H_ROOF_H), WOOD, None),
        ("CapDoor", "CAP DOOR", cap_door, (H_DOOR_W, H_DOOR_H), WOOD, "door"),
        ("MushroomBed", "BED", mushroom_bed, (26, 9), WOOD, "decor"),
        ("CapShelf", "CAP SHELF", cap_shelf, (18, 6), WOOD, "wall"),
        ("RootChair", "ROOT CHAIR", root_chair, (10, 14), WOOD, "decor"),
        ("CapCupboard", "CUPBOARD", cap_cupboard, (14, 24), WOOD, "decor"),
        ("DryingRack", "DRYING RACK", drying_rack, (18, 20), WOOD, "decor"),
        ("GlowLampPost", "LAMP POST", glow_lamp_post, (8, 28), WOOD, "decor"),
        ("PlanterBox", "PLANTER", planter_box, (20, 12), WOOD, "decor"),
        ("MycelRug", "RUG", myc_rug, (24, 2), WOOD, "decor"),
        ("GillGlow", "GILL GLOW", gill_glow, (16, 3), WOOD, "wall"),
    ]),
    ("BRACKETS", [
        ("BracketDeck", "BRACKET DECK", bracket_deck, (BRACKET_W, BRACKET_H), WOOD, "oneway"),
        ("BracketDeckGlow", "GLOWING BRACKET", bracket_deck_glow, (BRACKET_W, BRACKET_H), WOOD, "oneway"),
        ("BracketDeckR", "BRACKET DECK R", bracket_deck_r, (BRACKET_W, BRACKET_H), WOOD, "oneway"),
        ("BracketDeckGlowR", "GLOWING BRACKET R", bracket_deck_glow_r, (BRACKET_W, BRACKET_H), WOOD, "oneway"),
    ]),
]

STATIC = {"BracketDeck", "BracketDeckGlow", "BracketDeckR", "BracketDeckGlowR",
          "StemWall", "StemFloor", "CapDeck", "CapRoof"}
KINEMATIC = {"CapDoor"}

ANCHORS = {
    "SporePod": {"Eye": (6.5, 2.5)},
    "SporeSacs": {"Eye": (6.5, 2.5)},
    "HangingCaps": {"Eye": (14.5, 2.5)},
    "Cocoon": {"Eye": (6.5, 2.5)},
    "GlowLantern": {"Eye": (4, 2)},
    "FungalCenser": {"Eye": (4, 2)},
}

_DIM = dict(flicker=0.05, flickerSpeed=0.8)
LIGHTS = {
    # the cult's lamp is their lantern: as bright as the mine's, but cold
    "GlowLantern": dict(at=(4, 9.5), color=(0.5, 0.92, 0.95), intensity=1.3, radius=7.0, flicker=0.06, flickerSpeed=1.2),
    "FungalCenser": dict(at=(4, 11), color=(0.72, 0.45, 1.0), intensity=0.6, radius=3.5, flicker=0.2),
    "SporePod": dict(at=(7, 18), color=(0.7, 0.5, 1.0), intensity=0.35, radius=2.4, **_DIM),
    "SporeJars": dict(at=(7, 5), color=(0.55, 0.85, 0.9), intensity=0.4, radius=2.6, **_DIM),
    "CapCandles": dict(at=(6, 3), color=(1.0, 0.8, 0.5), intensity=0.7, radius=4.0, flicker=0.18),
    "FungalIdol": dict(at=(8, 15), color=(0.72, 0.5, 1.0), intensity=0.8, radius=4.5, flicker=0.08, flickerSpeed=1.0),
    "BracketDeckGlow": dict(at=(18, 6), color=(0.7, 0.95, 0.45), intensity=0.4, radius=2.6, **_DIM),
    "GlowLampPost": dict(at=(3.5, 4.5), color=(0.5, 0.92, 0.95), intensity=1.0, radius=5.5, flicker=0.06, flickerSpeed=1.2),
    "GillGlow": dict(at=(8, 2), color=(0.45, 0.9, 0.95), intensity=0.9, radius=5.0, flicker=0.05, flickerSpeed=0.8),
    "PlanterBox": dict(at=(10, 2), color=(0.6, 0.95, 0.7), intensity=0.35, radius=2.4, **_DIM),
    "BracketDeckGlowR": dict(at=(22, 6), color=(0.7, 0.95, 0.45), intensity=0.4, radius=2.6, **_DIM),
}
