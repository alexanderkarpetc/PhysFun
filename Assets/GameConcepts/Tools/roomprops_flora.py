"""Room props, part 7: what grows in the corridors - mushrooms (glowing and not), moss,
grass, ferns, bushes, roots and vines. Rooms.CorridorFlora strews them along the floor,
ceiling and walls of every corridor a floor cuts (Scripts/Rooms/CorridorFlora.cs), picking
by the spot and by the corridor's mood (green, fungal or dry).

All of it is Props.Decor: asleep and walked through until a round, a blast or fire wakes
it - extra "decor" for what stands on the floor, "wall" for what hangs from the ceiling or
grows out of a wall, which needs nothing under it. The glowing ones carry a dim, cold
Lighting.LightSource2D (LIGHTS below), so a fungal corridor is never quite dark.

Orientation is what the placer expects:
* floor growth stands on the bottom row of its canvas;
* ceiling growth hangs from the top row;
* wall growth sticks out of the left column (a wall on the right gets it mirrored).

Built by `roomprops.py`; read its docstring for what the entries mean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402,F401

TITLE = "CAVE GROWTH"
SEED = 7700
SORTING_ORDER = -2          # behind characters, ladders and the terrain's edge

# ── palette: muted, a little cold; only the glowing ones are allowed any colour ──────
CAP_RAMP = ((54, 38, 30), (82, 58, 42), (110, 80, 56), (140, 106, 74))
STEM_RAMP = ((92, 86, 72), (124, 116, 96), (156, 148, 122), (184, 176, 146))
GILL = (44, 36, 32)
RED_RAMP = ((66, 30, 30), (96, 42, 36), (124, 58, 44), (150, 80, 58))
SPOT = (168, 158, 130)
INK_RAMP = ((70, 66, 64), (112, 108, 102), (150, 146, 136), (178, 174, 162))
INK_DRIP = (40, 36, 44)
PUFF_RAMP = ((96, 88, 70), (128, 118, 92), (156, 146, 114), (182, 172, 138))
CORAL_RAMP = ((100, 62, 40), (132, 86, 52), (160, 112, 68), (186, 140, 90))
MOREL_RAMP = ((50, 38, 28), (78, 60, 42), (104, 82, 56), (128, 104, 72))

GC_RAMP = ((32, 70, 82), (54, 120, 132), (96, 184, 188), (176, 236, 228))      # cyan
GY_RAMP = ((58, 78, 36), (104, 140, 52), (164, 200, 92), (222, 240, 160))      # sulphur green
GV_RAMP = ((56, 36, 82), (92, 60, 130), (144, 106, 190), (210, 182, 240))      # violet
GA_RAMP = ((96, 56, 26), (152, 98, 40), (210, 156, 72), (246, 214, 140))       # amber
GSTEM_RAMP = ((44, 48, 58), (66, 74, 84), (94, 104, 112), (126, 136, 140))

MOSS_RAMP = ((34, 44, 28), (52, 66, 34), (74, 90, 44), (100, 114, 58))
FMOSS_RAMP = ((44, 32, 48), (66, 46, 66), (90, 64, 86), (118, 88, 110))        # fungal moss
LEAF_RAMP = ((32, 44, 32), (48, 64, 40), (68, 86, 50), (94, 110, 62))
DRY_RAMP = ((70, 62, 40), (98, 88, 56), (128, 116, 74), (156, 144, 96))
TWIG_RAMP = ((44, 34, 28), (66, 52, 40), (90, 72, 52), (112, 92, 66))
ROOT_RAMP = ((46, 36, 28), (70, 54, 38), (96, 76, 52), (122, 100, 70))
PALE_RAMP = ((110, 112, 88), (144, 144, 112), (176, 174, 138), (204, 202, 168))
BERRY, BERRY_L = (104, 34, 38), (146, 58, 52)
SOIL = (44, 36, 30)


# ═══════════════════════════════════════════════════════════════════════════
#  Shapes
# ═══════════════════════════════════════════════════════════════════════════
def dome(cx, base, rx, ry, ramp, lit=0.8):
    """A mushroom cap: the top half of an ellipse standing on row `base`, lit top left."""
    for y in range(base - int(math.ceil(ry)), base + 1):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = (x - cx) / rx, (y - base) / max(0.5, ry)
            if dx * dx + dy * dy <= 1.0:
                dshade(x, y, lit - 0.35 * (dx + 1.0) - 0.3 * (dy + 1.0) + 0.3, ramp)


def ell(cx, cy, rx, ry, ramp, lit=0.75):
    """A filled ellipse, lit top left."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = (x - cx) / max(0.5, rx), (y - cy) / max(0.5, ry)
            if dx * dx + dy * dy <= 1.0:
                dshade(x, y, lit - 0.3 * dx - 0.35 * dy, ramp)


def stem(x0, x1, y0, y1, ramp, lit=0.85):
    """An upright stalk, lit down its left side."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dshade(x, y, lit - 0.5 * (x - x0) / max(1, x1 - x0 + 1), ramp)


def bent(x, y0, y1, lean, ramp, width=1):
    """A thin stalk from (x, y1) up to row y0, leaning `lean` pixels by the top."""
    for y in range(y0, y1 + 1):
        t = (y1 - y) / max(1, y1 - y0)
        cx = x + int(round(lean * t * t))
        for k in range(width):
            dshade(cx + k, y, 0.7 - 0.3 * k, ramp)


def blade(x0, y0, x1, y1, ramp):
    """A line shaded from dark at its foot (x0, y0) to light at its tip."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        t = i / n
        dshade(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), 0.15 + 0.75 * t, ramp)


def clump(x0, x1, top, base, ramp, rough=0.35):
    """A mound of moss or leaves from row `base` up to about row `top`, ragged on top."""
    w = x1 - x0
    for x in range(x0, x1 + 1):
        u = (x - x0) / max(1, w)
        hgt = (base - top) * math.sqrt(max(0.0, 1.0 - (2 * u - 1) ** 2))
        hgt *= 1.0 - rough * rnd()
        for y in range(base - int(round(hgt)), base + 1):
            t = 0.85 - 0.6 * (y - (base - hgt)) / max(1.0, hgt) - 0.15 * u
            dshade(x, y, t, ramp)


def strand(x, y0, length, ramp, sway=0.0, phase=0.0):
    """Something hanging from row y0: a moss strand, a root, a vine."""
    for k in range(length):
        dx = int(round(sway * math.sin(phase + k * 0.45)))
        dshade(x + dx, y0 + k, 0.75 - 0.5 * k / max(1, length), ramp)


def speckle(x0, y0, x1, y1, c, p):
    """Scatter `c` over pixels already drawn."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if AT(x, y) != KEY and chance(p):
                P(x, y, c)


# ═══════════════════════════════════════════════════════════════════════════
#  MUSHROOMS
# ═══════════════════════════════════════════════════════════════════════════
def toadstool():
    """A brown toadstool."""
    stem(4, 5, 5, 10, STEM_RAMP)
    dome(4.5, 4, 3.6, 3, CAP_RAMP)
    R(2, 5, 7, 5, GILL)


def toadstool_cluster():
    """Three toadstools off one foot."""
    R(2, 11, 11, 11, SOIL)
    stem(2, 3, 7, 10, STEM_RAMP)
    dome(2.5, 6, 2.2, 2, CAP_RAMP)
    stem(6, 7, 3, 10, STEM_RAMP)
    dome(6.5, 2, 3.2, 2, CAP_RAMP)
    R(4, 3, 9, 3, GILL)
    stem(10, 10, 8, 10, STEM_RAMP)
    dome(10.5, 7, 1.8, 1.5, CAP_RAMP)


def ink_cap():
    """A shaggy ink cap, tall and pale, its rim melting to black."""
    stem(3, 3, 10, 14, STEM_RAMP)
    for y in range(1, 10):
        hw = 1 if y < 3 else 2
        for x in range(3 - hw, 4 + hw):
            dshade(x, y, 0.9 - 0.18 * (x - 3 + hw) - 0.02 * y, INK_RAMP)
        if y % 3 == 1:
            P(3 + hw - 1, y, INK_RAMP[0])
    R(1, 9, 5, 9, INK_DRIP)
    P(1, 10, INK_DRIP)
    P(5, 10, INK_DRIP)
    P(4, 11, INK_DRIP)


def puffballs():
    """Puffballs in a row, the big one split at the top."""
    R(2, 9, 12, 9, SOIL)
    ell(4, 6, 3, 3, PUFF_RAMP)
    ell(9, 7, 2.2, 2.2, PUFF_RAMP)
    ell(12, 8, 1.2, 1.2, PUFF_RAMP)
    P(4, 3, PUFF_RAMP[0])
    P(5, 4, PUFF_RAMP[0])
    P(3, 4, PUFF_RAMP[3])


def red_cap():
    """A dull red cap with pale flecks - poison, by the look."""
    stem(4, 5, 6, 11, STEM_RAMP)
    R(3, 9, 6, 9, STEM_RAMP[1])                               # the ring
    dome(4.5, 5, 4.2, 4, RED_RAMP)
    R(1, 6, 8, 6, GILL)
    for x, y in ((3, 2), (6, 3), (2, 4), (5, 1), (7, 5)):
        P(x, y, SPOT)


def tall_stalk():
    """A bonnet on a long thin stalk."""
    bent(3, 4, 17, 1, STEM_RAMP)
    dome(4, 3, 2.2, 2.5, CAP_RAMP, lit=0.65)


def giant_mushroom():
    """A mushroom bigger than a man is wide - the cap a flat brown table."""
    for y in range(9, 26):
        sw = 3 if y < 22 else 4 if y < 24 else 5
        for x in range(11 - sw, 12 + sw):
            dshade(x, y, 0.85 - 0.6 * (x - 11 + sw) / (2 * sw), STEM_RAMP)
    R(5, 25, 17, 25, SOIL)
    dome(11, 8, 10.4, 7, CAP_RAMP)
    R(1, 9, 21, 9, GILL)
    for x in range(2, 21, 2):
        P(x, 10, GILL)
    speckle(2, 2, 20, 8, CAP_RAMP[0], 0.08)


def coral_fungus():
    """Coral fungus: a pale orange tangle of branches."""
    R(3, 10, 8, 10, CORAL_RAMP[0])
    for x0, x1, top in ((5, 5, 2), (3, 3, 4), (8, 8, 3), (6, 7, 5), (2, 2, 6), (9, 9, 6)):
        for x in range(x0, x1 + 1):
            for y in range(top, 10):
                dshade(x, y, 0.85 - 0.04 * y, CORAL_RAMP)
    for x in range(3, 9):
        for y in range(7, 10):
            dshade(x, y, 0.55 - 0.05 * (y - 7), CORAL_RAMP)
    for x, y in ((4, 3), (6, 4), (7, 2), (2, 5), (9, 5)):
        P(x, y, CORAL_RAMP[3])


def morel():
    """A morel: a pitted cone on a fat white foot."""
    stem(2, 4, 8, 11, STEM_RAMP)
    for y in range(1, 8):
        hw = 1 if y < 3 else 2
        for x in range(3 - hw, 4 + hw):
            dshade(x, y, 0.85 - 0.15 * (x - 3 + hw), MOREL_RAMP)
            if (x + y * 2) % 3 == 0:
                P(x, y, MOREL_RAMP[0])


# ── glowing ──────────────────────────────────────────────────────────────────
def glow_caps():
    """A spread of little cyan caps: the light of a fungal corridor."""
    R(1, 8, 11, 8, SOIL)
    for x, top, r in ((2, 5, 1.6), (5, 3, 2.2), (9, 4, 2), (11, 6, 1.2)):
        stem(x, x, top + 1, 7, GSTEM_RAMP)
        dome(x + 0.5 if r > 1.5 else x, top, r, max(1.2, r * 0.8), GC_RAMP, lit=1.0)
    P(5, 2, GC_RAMP[3])
    P(9, 3, GC_RAMP[3])


def glow_stalks():
    """Thin stalks with a glowing bead on every tip."""
    R(2, 15, 9, 15, SOIL)
    for x, top, lean in ((3, 3, -1), (5, 1, 0), (7, 4, 1), (9, 6, 1), (4, 7, -2)):
        bent(x, top + 1, 14, lean, GSTEM_RAMP)
        tx = x + lean
        P(tx, top, GY_RAMP[3])
        P(tx - 1, top, GY_RAMP[2])
        P(tx, top - 1, GY_RAMP[2])


def glow_bell():
    """A violet bell-cap, its skirt glowing from inside."""
    stem(4, 5, 7, 12, GSTEM_RAMP)
    for y in range(1, 8):
        hw = int(1 + (y - 1) * 0.6)
        for x in range(5 - hw, 5 + hw):
            dshade(x, y, 1.0 - 0.12 * abs(x - 4) - 0.03 * y, GV_RAMP)
    R(1, 8, 8, 8, GV_RAMP[2])
    P(1, 8, GV_RAMP[1])
    P(8, 8, GV_RAMP[1])
    P(3, 6, GV_RAMP[3])
    P(6, 6, GV_RAMP[3])


def glow_giant():
    """A big glowing cap, cyan under its rim, freckled with light."""
    for y in range(8, 22):
        sw = 2 if y < 19 else 3
        for x in range(9 - sw, 10 + sw):
            dshade(x, y, 0.75 - 0.5 * (x - 9 + sw) / (2 * sw), GSTEM_RAMP)
    R(4, 21, 14, 21, SOIL)
    dome(9, 7, 8.4, 6, GC_RAMP, lit=0.75)
    R(1, 8, 17, 8, GC_RAMP[2])
    for x in range(2, 17, 3):
        P(x, 9, GC_RAMP[3])
    for x, y in ((5, 3), (9, 2), (12, 4), (7, 5), (14, 6)):
        P(x, y, GC_RAMP[3])


def glow_puffs():
    """Amber spore-balls on short stalks, smouldering."""
    R(1, 10, 10, 10, SOIL)
    for x, top, r in ((3, 4, 1.6), (7, 2, 2.0), (9, 6, 1.1)):
        stem(x, x, int(top + r), 9, GSTEM_RAMP)
        ell(x, top, r, r, GA_RAMP, lit=1.0)
    P(7, 1, GA_RAMP[3])
    P(2, 3, GA_RAMP[3])


def glow_spindles():
    """Fairy fingers: pale spikes that glow green-white at the tips."""
    R(1, 10, 8, 10, SOIL)
    for x, top in ((2, 5), (3, 2), (5, 1), (6, 4), (8, 6)):
        for y in range(top, 10):
            dshade(x, y, 1.0 - 0.07 * (y - top), GY_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  PLANTS
# ═══════════════════════════════════════════════════════════════════════════
def moss_clump():
    """A low cushion of moss."""
    clump(1, 13, 0, 4, MOSS_RAMP)
    speckle(1, 1, 13, 4, MOSS_RAMP[3], 0.07)


def moss_tuft():
    """A small tuft of moss."""
    clump(1, 7, 0, 3, MOSS_RAMP, rough=0.25)


def fungal_moss():
    """A cushion of the purple stuff that grows where the mushrooms glow."""
    clump(1, 12, 0, 4, FMOSS_RAMP)
    speckle(1, 1, 12, 4, GV_RAMP[2], 0.05)


def grass_tuft():
    """A tuft of dark cave grass."""
    R(2, 6, 9, 6, SOIL)
    for x0, x1, y1 in ((2, 0, 1), (4, 3, 0), (5, 6, 1), (6, 9, 2), (8, 10, 3), (3, 1, 3), (7, 7, 0)):
        blade(x0 + 1, 6, x1 + 1, y1, LEAF_RAMP)


def dry_grass():
    """Dead grass gone the colour of straw."""
    R(2, 6, 10, 6, SOIL)
    for x0, x1, y1 in ((2, 1, 1), (4, 4, 0), (6, 8, 1), (8, 11, 3), (9, 9, 2), (3, 0, 3), (7, 6, 0)):
        blade(x0 + 1, 6, x1 + 1, y1, DRY_RAMP)


def fern():
    """A fern, its fronds arching out both ways."""
    R(6, 10, 8, 10, SOIL)
    for side in (-1, 1):
        for k, (reach, rise) in enumerate(((6, 7), (4, 9), (2, 6))):
            x0, y0 = 7, 10
            for i in range(reach * 2 + 1):
                t = i / (reach * 2.0)
                x = int(round(x0 + side * reach * t))
                y = int(round(y0 - rise * math.sin(t * math.pi * 0.8)))
                dshade(x, y, 0.35 + 0.5 * t, LEAF_RAMP)
                if i % 2 == 0 and i > 1:                     # leaflets under the frond
                    dshade(x, y + 1, 0.3 + 0.3 * t, LEAF_RAMP)
    P(7, 0, LEAF_RAMP[3])


def thorn_bush():
    """A dry thorn bush, all twigs and spikes."""
    R(5, 11, 11, 11, SOIL)
    for x0, y0, x1, y1 in ((8, 11, 2, 3), (8, 11, 14, 2), (8, 11, 8, 0), (7, 10, 1, 8),
                           (9, 10, 15, 7), (8, 6, 4, 1), (8, 6, 12, 1), (5, 7, 3, 4), (11, 7, 13, 4)):
        LN(x0, y0, x1, y1, TWIG_RAMP[1])
    for _ in range(26):
        x, y = int(1 + rnd() * 15), int(rnd() * 10)
        if AT(x, y) != KEY:
            P(x + (1 if chance(0.5) else -1), y, TWIG_RAMP[0])
    speckle(0, 0, 16, 10, TWIG_RAMP[3], 0.15)


def shrub():
    """A leafy, dark green shrub."""
    R(7, 12, 10, 12, SOIL)
    stem(8, 9, 9, 12, TWIG_RAMP)
    ell(5, 7, 4, 3.5, LEAF_RAMP)
    ell(12, 6.5, 4.5, 4, LEAF_RAMP)
    ell(8.5, 4, 4, 3.5, LEAF_RAMP, lit=0.9)
    speckle(1, 1, 16, 10, LEAF_RAMP[0], 0.12)
    speckle(1, 1, 12, 6, LEAF_RAMP[3], 0.06)


def berry_bush():
    """A low bush with a few dull red berries on it."""
    R(6, 10, 9, 10, SOIL)
    ell(4.5, 6.5, 3.5, 3, LEAF_RAMP)
    ell(10, 6, 3.8, 3.5, LEAF_RAMP)
    ell(7.5, 4, 3, 2.6, LEAF_RAMP, lit=0.9)
    R(6, 8, 9, 9, TWIG_RAMP[1])
    for x, y in ((3, 6), (6, 3), (10, 5), (12, 7), (8, 7), (5, 8)):
        P(x, y, BERRY_L)
        P(x + 1, y + 1, BERRY)


def dead_shrub():
    """A dead shrub, bare twigs."""
    R(5, 10, 8, 10, SOIL)
    for x0, y0, x1, y1 in ((6, 10, 6, 3), (6, 7, 2, 2), (6, 6, 10, 1), (6, 8, 11, 6),
                           (4, 4, 3, 1), (8, 3, 9, 0), (3, 4, 1, 4)):
        LN(x0, y0, x1, y1, TWIG_RAMP[2])
    speckle(0, 0, 11, 9, TWIG_RAMP[0], 0.3)


def pale_sprouts():
    """Blanched sprouts that never saw the sun."""
    R(1, 7, 8, 7, SOIL)
    for x, top, lean in ((2, 3, -1), (4, 1, 0), (6, 2, 1), (7, 4, 1), (3, 5, 0)):
        bent(x, top + 1, 6, lean, PALE_RAMP)
        tx = x + lean
        P(tx, top, PALE_RAMP[3])
        P(tx + (1 if lean >= 0 else -1), top, PALE_RAMP[2])


def root_knot():
    """A knot of root breaking out of the floor and back in."""
    for k in range(12):
        t = k / 11.0
        y = int(round(8 - 6 * math.sin(t * math.pi)))
        for d in range(3):
            dshade(1 + k, y + d, 0.8 - 0.25 * d, ROOT_RAMP)
    for k in range(6):
        t = k / 5.0
        y = int(round(8 - 3 * math.sin(t * math.pi)))
        dshade(7 + k, y, 0.6, ROOT_RAMP)
        dshade(7 + k, y + 1, 0.3, ROOT_RAMP)
    R(0, 9, 13, 9, SOIL)


def cave_lily():
    """A pale cave lily: broad leaves and one hanging white flower."""
    R(4, 12, 8, 12, SOIL)
    for side in (-1, 1):
        for i in range(7):
            x = 6 + side * i
            y = 11 - int(round(3 * math.sin(i / 6.0 * math.pi * 0.9)))
            dshade(x, y, 0.3 + 0.08 * i, LEAF_RAMP)
            dshade(x, y + 1, 0.2, LEAF_RAMP)
    bent(6, 2, 11, 2, LEAF_RAMP)
    for x, y in ((8, 2), (9, 3), (9, 4), (8, 4), (10, 4), (9, 5)):
        dshade(x, y, 0.9 - 0.1 * (y - 2), PALE_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  HANGING (from the ceiling)
# ═══════════════════════════════════════════════════════════════════════════
def hang_moss():
    """Long beards of moss off the ceiling."""
    R(0, 0, 11, 0, MOSS_RAMP[1])
    for x in range(0, 12):
        n = int(3 + 12 * rnd() * (1.0 - abs(x - 5.5) / 7.0))
        strand(x, 0, n, MOSS_RAMP, sway=0.6 * rnd(), phase=x)


def hang_moss_short():
    """A short fringe of moss."""
    R(0, 0, 9, 1, MOSS_RAMP[1])
    for x in range(0, 10):
        strand(x, 1, int(2 + 5 * rnd()), MOSS_RAMP)


def hang_fungal():
    """A fringe of the purple moss with little lights in it."""
    R(0, 0, 9, 1, FMOSS_RAMP[1])
    for x in range(0, 10):
        strand(x, 1, int(2 + 7 * rnd()), FMOSS_RAMP)
    for x in (2, 6, 8):
        y = 2
        while AT(x, y + 1) != KEY:
            y += 1
        P(x, y, GV_RAMP[3])


def hang_roots():
    """A tangle of roots come through the ceiling."""
    R(1, 0, 12, 0, ROOT_RAMP[1])
    R(4, 1, 9, 1, ROOT_RAMP[0])
    for x, n, sway in ((2, 9, 1.0), (4, 16, 1.4), (6, 6, 0.6), (7, 12, 1.0), (9, 14, 1.2), (11, 7, 0.8)):
        strand(x, 1, n, ROOT_RAMP, sway=sway, phase=x * 0.7)
    for x in (4, 9):                                          # the thick ones are two wide at the top
        strand(x + 1, 1, 5, ROOT_RAMP, sway=0.5, phase=x * 0.7)


def hang_roots_thin():
    """A few thin root hairs."""
    R(2, 0, 5, 0, ROOT_RAMP[1])
    for x, n in ((2, 6), (3, 10), (4, 7), (5, 4)):
        strand(x, 0, n, ROOT_RAMP, sway=0.8, phase=x)


def vines():
    """Vines hanging long, leaves along them."""
    R(0, 0, 6, 0, LEAF_RAMP[1])
    for x, n, ph in ((1, 20, 0.0), (3, 14, 1.3), (5, 22, 2.1)):
        for k in range(n):
            dx = int(round(0.8 * math.sin(ph + k * 0.35)))
            dshade(x + dx, k, 0.5, LEAF_RAMP)
            if k % 3 == 2:
                dshade(x + dx + (1 if k % 2 else -1), k, 0.85, LEAF_RAMP)


def glow_drops():
    """Glow-worm threads: sticky lines with a bead of light at each end."""
    R(0, 0, 8, 0, GSTEM_RAMP[1])
    for x, n in ((1, 9), (3, 14), (5, 7), (7, 12)):
        for k in range(1, n):
            P(x, k, GSTEM_RAMP[2] if k % 2 else GSTEM_RAMP[1])
        P(x, n, GC_RAMP[3])
        P(x, n - 1, GC_RAMP[2])
        P(x, n // 2, GC_RAMP[2])


def hang_glow_caps():
    """Glowing caps growing upside down off the ceiling."""
    R(0, 0, 10, 1, SOIL)
    for x, n, r in ((2, 3, 1.6), (5, 5, 2.2), (8, 2, 1.6)):
        stem(x, x, 2, n + 1, GSTEM_RAMP)
        for y in range(n + 1, n + 1 + int(math.ceil(r))):
            for xx in range(int(x - r), int(x + r) + 1):
                dx, dy = (xx - x) / r, (y - (n + 1)) / r
                if dx * dx + dy * dy <= 1.0:
                    dshade(xx, y, 0.95 - 0.3 * dy - 0.15 * dx, GC_RAMP)
    P(5, 7, GC_RAMP[3])


# ═══════════════════════════════════════════════════════════════════════════
#  ON THE WALL (growing out of the left column)
# ═══════════════════════════════════════════════════════════════════════════
def bracket_fungus():
    """Shelf fungus, three brackets up the wall."""
    R(0, 0, 0, 12, CAP_RAMP[0])
    for y0, reach in ((1, 4), (5, 6), (9, 5)):
        for x in range(0, reach + 1):
            dshade(x, y0, 0.9 - 0.06 * x, CAP_RAMP)
            if x < reach:
                dshade(x, y0 + 1, 0.5 - 0.05 * x, CAP_RAMP)
            if x < reach - 1:
                P(x, y0 + 2, GILL)
        P(reach, y0, CAP_RAMP[3])


def bracket_glow():
    """Shelf fungus that glows sulphur green under its lip."""
    R(0, 0, 0, 10, GSTEM_RAMP[0])
    for y0, reach in ((1, 5), (6, 4)):
        for x in range(0, reach + 1):
            dshade(x, y0, 0.55 - 0.05 * x, GSTEM_RAMP)
            if x < reach:
                dshade(x, y0 + 1, 0.85, GY_RAMP)
            if x < reach - 1:
                P(x, y0 + 2, GY_RAMP[3] if x % 2 else GY_RAMP[2])


def wall_moss():
    """Moss hanging down a wall's face."""
    for y in range(0, 14):
        reach = int(1 + 3 * math.sin(y / 13.0 * math.pi) * (0.6 + 0.4 * rnd()))
        for x in range(0, reach + 1):
            dshade(x, y, 0.8 - 0.15 * x, MOSS_RAMP)
    for x, n in ((1, 3), (2, 5), (3, 2)):
        strand(x, 13, n, MOSS_RAMP)


def wall_fern():
    """A fern growing sideways out of a crack, its fronds arching and drooping."""
    R(0, 4, 0, 7, SOIL)
    for reach, lift, droop in ((11, 4, 3), (8, 1, 4), (6, 4, 0)):
        for i in range(reach + 1):
            t = i / float(reach)
            x = 1 + i
            y = int(round(6 - lift * math.sin(t * math.pi * 0.5) + droop * t * t))
            dshade(x, y, 0.3 + 0.55 * t, LEAF_RAMP)
            if 1 < i < reach and i % 2 == 0:
                dshade(x, y - 1, 0.75, LEAF_RAMP)
                dshade(x, y + 1, 0.25, LEAF_RAMP)


def wall_glow_caps():
    """Little cyan caps on short stems out of a wall, turned up to the light."""
    R(0, 1, 0, 11, SOIL)
    for y, reach, r in ((4, 3, 1.6), (8, 5, 2.0), (11, 3, 1.4)):
        R(1, y, reach, y, GSTEM_RAMP[2])
        P(reach, y - 1, GSTEM_RAMP[2])
        dome(reach, y - 2, r, max(1.0, r * 0.8), GC_RAMP, lit=1.0)


GROUPS = [
    ("MUSHROOMS", [
        ("Toadstool", "TOADSTOOL", toadstool, (10, 11), WOOD, "decor"),
        ("ToadstoolCluster", "CLUSTER", toadstool_cluster, (14, 12), WOOD, "decor"),
        ("InkCap", "INK CAP", ink_cap, (7, 15), WOOD, "decor"),
        ("Puffballs", "PUFFBALLS", puffballs, (15, 10), WOOD, "decor"),
        ("RedCap", "RED CAP", red_cap, (10, 12), WOOD, "decor"),
        ("TallStalk", "STALK", tall_stalk, (8, 18), WOOD, "decor"),
        ("GiantMushroom", "GIANT", giant_mushroom, (23, 26), WOOD, "decor"),
        ("CoralFungus", "CORAL", coral_fungus, (11, 11), WOOD, "decor"),
        ("Morel", "MOREL", morel, (7, 12), WOOD, "decor"),
    ]),
    ("GLOWING", [
        ("GlowCaps", "GLOW CAPS", glow_caps, (13, 9), WOOD, "decor"),
        ("GlowStalks", "GLOW STALKS", glow_stalks, (12, 16), WOOD, "decor"),
        ("GlowBell", "GLOW BELL", glow_bell, (10, 13), WOOD, "decor"),
        ("GlowGiant", "GLOW GIANT", glow_giant, (19, 22), WOOD, "decor"),
        ("GlowPuffs", "GLOW PUFFS", glow_puffs, (12, 11), WOOD, "decor"),
        ("GlowSpindles", "SPINDLES", glow_spindles, (10, 11), WOOD, "decor"),
    ]),
    ("PLANTS", [
        ("MossClump", "MOSS", moss_clump, (15, 5), WOOD, "decor"),
        ("MossTuft", "TUFT", moss_tuft, (9, 4), WOOD, "decor"),
        ("FungalMoss", "FUNGAL MOSS", fungal_moss, (14, 5), WOOD, "decor"),
        ("GrassTuft", "GRASS", grass_tuft, (13, 7), WOOD, "decor"),
        ("DryGrass", "DRY GRASS", dry_grass, (14, 7), WOOD, "decor"),
        ("Fern", "FERN", fern, (15, 11), WOOD, "decor"),
        ("ThornBush", "THORNS", thorn_bush, (17, 12), WOOD, "decor"),
        ("Shrub", "SHRUB", shrub, (18, 13), WOOD, "decor"),
        ("BerryBush", "BERRIES", berry_bush, (15, 11), WOOD, "decor"),
        ("DeadShrub", "DEAD SHRUB", dead_shrub, (13, 11), WOOD, "decor"),
        ("PaleSprouts", "SPROUTS", pale_sprouts, (10, 8), WOOD, "decor"),
        ("RootKnot", "ROOT", root_knot, (14, 10), WOOD, "decor"),
        ("CaveLily", "LILY", cave_lily, (13, 13), WOOD, "decor"),
    ]),
    ("HANGING", [
        ("HangMoss", "MOSS", hang_moss, (12, 16), WOOD, "wall"),
        ("HangMossShort", "FRINGE", hang_moss_short, (10, 8), WOOD, "wall"),
        ("HangFungal", "FUNGAL", hang_fungal, (10, 10), WOOD, "wall"),
        ("HangRoots", "ROOTS", hang_roots, (14, 18), WOOD, "wall"),
        ("HangRootsThin", "ROOT HAIR", hang_roots_thin, (8, 11), WOOD, "wall"),
        ("Vines", "VINES", vines, (7, 23), WOOD, "wall"),
        ("GlowDrops", "GLOW WORMS", glow_drops, (9, 15), WOOD, "wall"),
        ("HangGlowCaps", "GLOW CAPS", hang_glow_caps, (11, 9), WOOD, "wall"),
    ]),
    ("ON THE WALL", [
        ("BracketFungus", "BRACKET", bracket_fungus, (8, 13), WOOD, "wall"),
        ("BracketGlow", "GLOW BRACKET", bracket_glow, (7, 10), WOOD, "wall"),
        ("WallMoss", "WALL MOSS", wall_moss, (6, 19), WOOD, "wall"),
        ("WallFern", "WALL FERN", wall_fern, (13, 10), WOOD, "wall"),
        ("WallGlowCaps", "GLOW CAPS", wall_glow_caps, (9, 13), WOOD, "wall"),
    ]),
]

# Cold, dim and slow: a glow, not a lamp. `at` is where the light comes from, pixels
# from the top-left. A corridor full of these still loses to a lantern for the light
# budget (LightField.MaxLights ranks by intensity x radius).
_GLOW = dict(flicker=0.05, flickerSpeed=0.8)
_CYAN, _GREEN, _VIOLET, _AMBER = (0.45, 0.9, 0.95), (0.7, 0.95, 0.45), (0.7, 0.5, 1.0), (1.0, 0.7, 0.35)
LIGHTS = {
    "GlowCaps": dict(at=(6, 4), color=_CYAN, intensity=0.45, radius=2.6, **_GLOW),
    "GlowStalks": dict(at=(5, 3), color=_GREEN, intensity=0.4, radius=2.4, **_GLOW),
    "GlowBell": dict(at=(5, 6), color=_VIOLET, intensity=0.45, radius=2.6, **_GLOW),
    "GlowGiant": dict(at=(9, 7), color=_CYAN, intensity=0.6, radius=3.6, **_GLOW),
    "GlowPuffs": dict(at=(6, 4), color=_AMBER, intensity=0.4, radius=2.4, **_GLOW),
    "GlowSpindles": dict(at=(5, 3), color=_GREEN, intensity=0.35, radius=2.2, **_GLOW),
    "HangFungal": dict(at=(5, 6), color=_VIOLET, intensity=0.3, radius=2.0, **_GLOW),
    "GlowDrops": dict(at=(4, 10), color=_CYAN, intensity=0.35, radius=2.4, **_GLOW),
    "HangGlowCaps": dict(at=(5, 6), color=_CYAN, intensity=0.4, radius=2.4, **_GLOW),
    "BracketGlow": dict(at=(3, 4), color=_GREEN, intensity=0.35, radius=2.2, **_GLOW),
    "WallGlowCaps": dict(at=(5, 6), color=_CYAN, intensity=0.35, radius=2.2, **_GLOW),
}
