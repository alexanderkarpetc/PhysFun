"""Room props, part 3: what the nests, chapels and houses are furnished with.

The loose and moving things of S29-S39: the spiders' sacs, cocoons and silk, the chapel's
banners, pews and candle racks, the paternoster's cars and sprocket, the warehouse racks
and what is on them, the sunken house's furniture, the colonnade's drums, the clock's
brass wheels and its weight, and the trench's bags, boards, wire and barricade. Built by
`roomprops.py`; read its docstring for what the entries mean. The bodies part 1 already
has (crates, drums, stakes, skulls, logs) are used from there, not drawn again.

Two things about every-pixel-collides that shape these drawings:

* The outside outline is solid too, so a gap that opens to the outside closes up by a
  pixel on each side. Gaps you are meant to see through (under a table, between candles,
  between tatters) are 3-4px wide so a real gap is left; gaps closed all round (a cage, a
  wheel between its spokes, a ladder between its rungs) keep what they are drawn with.
* A diagonal one pixel wide is two bodies touching at a corner. Threads, braces and
  hangers are drawn with `ln4`, which steps square, so they hold their ends together.

The clock wheels and the sprockets turn, so they follow `wheels.py`: lit from their own
centre, features repeating round it, the bore keyed out for the arbor.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402
from roomprops_hung import eye, ball, BONE, BONE_L, BONE_D, WAX, WAX_L, EMBER, RUST_RAMP  # noqa: E402,F401

TITLE = "NESTS, CHAPELS AND HOUSES"
SEED = 9500

SILK_D, SILK, SILK_L = (104, 102, 92), (150, 146, 130), (186, 182, 164)
SAC_D, SAC, SAC_L = (104, 96, 70), (152, 144, 112), (196, 188, 152)
GRUB = (88, 104, 60)
BOOT_D, BOOT = (40, 36, 32), (64, 56, 48)
OX_D, OX, OX_L = (70, 30, 32), (106, 48, 48), (140, 68, 60)              # oxblood cloth
VI_D, VI, VI_L = (40, 38, 62), (64, 62, 96), (90, 88, 124)               # dull violet cloth
SIGIL = (176, 160, 112)
GRAIN_D, GRAIN, GRAIN_L = (104, 88, 64), (142, 122, 88), (172, 152, 112)
BAG_D, BAG, BAG_L = (82, 72, 52), (118, 104, 76), (150, 134, 100)
KEG_D, KEG, KEG_L = (62, 40, 26), (92, 60, 38), (128, 88, 56)
BED_D, BED, BED_L = (66, 42, 46), (94, 60, 64), (126, 88, 90)
LINEN_D, LINEN = (118, 110, 92), (156, 148, 124)
TILE_D, TILE, TILE_L = (78, 46, 38), (110, 64, 52), (146, 92, 70)
BLK_D, BLK, BLK_F, BLK_L = (74, 68, 57), (122, 114, 96), (104, 97, 83), (160, 150, 128)
BRASS_D, BRASS_M, BRASS, BRASS_L = (78, 58, 36), (108, 82, 50), (136, 104, 62), (176, 140, 88)
STRAP = (70, 66, 60)
WIRE_D, WIRE, WIRE_L = (70, 70, 68), (112, 110, 104), (160, 158, 150)
PAGES = (184, 174, 146)
BOOKS = ((OX, OX_L), (VI, VI_L), ((80, 92, 54), (106, 120, 70)), ((112, 90, 62), (146, 120, 84)))

SILK_RAMP = (SILK_D, SILK, SILK_L)
SAC_RAMP = (SAC_D, SAC, SAC_L)
OX_RAMP = (OX_D, OX, OX_L)
VI_RAMP = (VI_D, VI, VI_L)
GRAIN_RAMP = (GRAIN_D, GRAIN, GRAIN_L)
BAG_RAMP = (BAG_D, BAG, BAG_L)
KEG_RAMP = (KEG_D, KEG, KEG_L)
BED_RAMP = (BED_D, BED, BED_L)
TILE_RAMP = (TILE_D, TILE, TILE_L)
BLK_RAMP = (BLK_D, BLK_F, BLK, BLK_L)
BRASS_RAMP = (BRASS_D, BRASS_M, BRASS, BRASS_L)


def ln4(x0, y0, x1, y1, c):
    """A line that steps square: every pixel shares an edge with the next, so a thread
    or a brace one pixel wide is one body, not a chain of corners."""
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    px_, py_ = x0, y0
    P(x0, y0, c)
    for i in range(1, n + 1):
        x = int(round(x0 + (x1 - x0) * i / float(n)))
        y = int(round(y0 + (y1 - y0) * i / float(n)))
        if x != px_ and y != py_:
            P(x, py_, c)
        P(x, y, c)
        px_, py_ = x, y


def eye_at(cx, top, r):
    """Where `eye(cx, top, r)` puts the middle of its hole, for the prefab's anchor."""
    return (cx + 1.0, top + r + 0.5)


def blob(cx, cy, rx, ry, ramp, lit=0.75):
    """A soft lump - a sac, a bundle, a bag - lit from the top left."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if u * u + v * v <= 1.0:
                dshade(x, y, lit - 0.35 * (u + v) - 0.2 * math.hypot(u, v), ramp)


# ═══════════════════════════════════════════════════════════════════════════
#  NEST - S29
# ═══════════════════════════════════════════════════════════════════════════
def _sac(cx, top, h=10, w=4.0):
    """A teardrop of silk: narrow where the thread goes in, full at the bottom, a few
    wraps of thread round it and the dark of the thing inside showing through."""
    for y in range(int(top), int(top + h)):
        u = (y + 0.5 - top) / h
        hw = w * math.sqrt(max(0.0, 1 - ((u - 0.6) / (0.62 if u < 0.6 else 0.42)) ** 2))
        for x in range(int(cx - hw - 1), int(cx + hw + 2)):
            dx = x + 0.5 - cx
            if abs(dx) <= hw:
                dshade(x, y, 0.78 - 0.32 * dx / max(hw, 1) - 0.3 * u, SAC_RAMP)
    for k in (0.35, 0.7):                                    # wraps of thread
        y = int(top + h * k)
        hw = w * 0.8
        ln4(cx - hw + 1, y, cx + hw - 1, y + 1, SAC_D)
    P(int(cx) - 1, int(top + h * 0.3), SAC_L)
    P(int(cx), int(top + h * 0.55), GRUB)                   # the thing inside


def egg_sac():
    """One egg sac on the knot of its thread. It hangs off the roof in bunches, lies on
    the floor where it dropped, and something is moving in it."""
    eye(3, 0, 2.5, SILK_RAMP)
    R(4, 5, 4, 7, SILK)
    _sac(4.5, 7, 10, 4.2)


def egg_cluster():
    """A bunch of sacs off one knot: threads of different lengths from the eye, a sac at
    the end of each, the long ones hanging between the short."""
    eye(11, 0, 2.5, SILK_RAMP)
    for (sx, st) in ((4.5, 8), (10.5, 15), (16.5, 9), (22.5, 14)):
        ln4(12, 5, sx, st, SILK)
    for (sx, st) in ((4.5, 8), (16.5, 9), (10.5, 15), (22.5, 14)):
        _sac(sx, st, 9, 3.4)


def _cocoon_body(x0, y0, w, h, along_x):
    """A wrapped body: an elongated bundle with the wraps going round it at a slant."""
    cx, cy = x0 + w / 2.0, y0 + h / 2.0
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            u, v = (x + 0.5 - cx) / (w / 2.0), (y + 0.5 - cy) / (h / 2.0)
            if u * u * (0.7 if along_x else 1) + v * v * (1 if along_x else 0.7) > 1.0:
                continue
            a = (x - y // 2) if along_x else (y - x // 2)
            t = 0.78 - 0.35 * (u + v) - 0.25 * math.hypot(u, v)
            if a % 4 == 0:
                P(x, y, SILK_D)
            elif a % 4 == 3 and t > 0.45:
                P(x, y, SILK_L)
            else:
                dshade(x, y, t, SILK_RAMP)


def cocoon_hung():
    """A miner the spiders have wrapped and hung: a long silk bundle on its thread, the
    wraps round it, a boot out of the bottom. Cut the thread and he comes down."""
    eye(4, 0, 2.5, SILK_RAMP)
    R(5, 5, 5, 6, SILK)
    _cocoon_body(1, 6, 10, 23, False)
    tpl(4, 28, ["Bb.", "BBb", "dBBB"], {'B': BOOT, 'b': BOOT, 'd': BOOT_D})


def cocoon_lying():
    """The same bundle, down: on the hammock, on the floor, on a shelf in a bubble."""
    _cocoon_body(0, 1, 23, 9, True)
    tpl(22, 3, ["bB.", "BBB", "BBb", "dd."], {'B': BOOT, 'b': BOOT, 'd': BOOT_D})


def _sag(x, x0, x1, y, sag):
    t = (x - x0) / float(x1 - x0)
    return y + sag * math.sin(math.pi * t)


def silk_net():
    """A panel of the hammock: three sagging strands laced across, a knot at each end
    where the next panel ties on. The hammock is a row of these, hinged: burn one and
    the net parts there. Spaces between the strands are holes - things fall through
    only if they are small."""
    for k, (y, sag) in enumerate(((1, 3), (5, 3), (9, 2))):
        prev = None
        for x in range(1, 27):
            yy = int(round(_sag(x, 1, 26, y, sag)))
            P(x, yy, SILK_L if k == 0 else SILK if k == 1 else SILK_D)
            if prev is not None and abs(prev - yy) > 0:
                R(x, min(prev, yy), x, max(prev, yy), SILK)
            prev = yy
    for x in range(4, 26, 5):                                # the lacing
        ya = int(round(_sag(x, 1, 26, 1, 3)))
        yb = int(round(_sag(x + 1, 1, 26, 9, 2)))
        ln4(x, ya, x + 1, yb, SILK_D)
    for x in (0, 27):                                        # knots at the ends
        R(x, 1, x, 9, SILK)
        P(x, 5, SILK_L)


def silk_curtain():
    """A strip of the curtain the spiders hang across a throat: strands roof to floor,
    laced. Hung from its top knot; burn it and the bubble behind is open."""
    eye(4, 0, 2.5, SILK_RAMP)
    R(1, 5, 9, 5, SILK)
    for k, x0 in enumerate((1, 5, 9)):
        prev = None
        for y in range(5, 40):
            xx = x0 + int(round(1.0 * math.sin(y * 0.22 + k)))
            P(xx, y, SILK if k != 1 else SILK_L)
            if prev is not None and prev != xx:
                P(prev, y, SILK_D)
            prev = xx
    for y in range(11, 39, 7):                               # the lacing
        ln4(1, y, 9, y + 2, SILK_D)


# ═══════════════════════════════════════════════════════════════════════════
#  CHAPEL - S30, S34
# ═══════════════════════════════════════════════════════════════════════════
def _banner(ramp, ln):
    """A cloth banner on its pole: an eye at each end of the pole for the two cords, the
    cloth hanging in folds, the cult's ring-and-eye sigil, the foot torn into tatters.
    Cloth burns, so it is wood to the game."""
    d, c, l = ramp
    for cx in (1, 14):
        eye(cx, 0, 2.5)
    for x in range(0, 19):                                   # the pole
        dshade(x, 5, 0.95, TIM_RAMP)
        dshade(x, 6, 0.35, TIM_RAMP)
    P(0, 5, TIM_M)
    P(18, 6, TIM_D)
    foot = 7 + ln
    for y in range(7, foot):
        for x in range(2, 17):
            fold = math.sin((x - 2) * 0.9 + y * 0.03)
            dshade(x, y, 0.55 + 0.25 * fold - 0.25 * (x - 2) / 14.0, ramp)
        P(2, y, l)
        P(16, y, d)
    R(2, 7, 16, 7, d)                                        # the hem round the pole
    for k, x in enumerate(range(2, 17, 4)):                  # tatters, 2 wide, 2 apart
        dd = 2 + (k * 7) % 5
        for y in range(foot, foot + dd):
            P(x, y, c)
            P(x + 1, y, d)
    sy = 7 + min(18, ln // 3)                                # the sigil: a ring with an eye
    for y in range(sy - 5, sy + 6):
        for x in range(4, 16):
            dd_ = math.hypot(x + 0.5 - 9.5, y + 0.5 - sy - 0.5)
            if 3.2 <= dd_ <= 4.3:
                P(x, y, SIGIL)
    P(9, sy, SIGIL)
    for yb in (10, foot - 7):
        R(5, yb, 13, yb, SIGIL)
    grime(2, 7, 17, foot + 5, ln // 2, (d,), on=(c,))


def banner_red():
    """S30's long banner, oxblood, off the vault on two cords."""
    _banner(OX_RAMP, 82)


def banner_violet():
    _banner(VI_RAMP, 76)


def banner_short():
    """The apse banner over the altar."""
    _banner(OX_RAMP, 30)


def pew():
    """A timber pew side-on, facing east: the back is the west end, the seat runs east
    to one leg, a stretcher low between. Kneel behind it, or burn it."""
    for y in range(1, 20):                                   # the back, down to the floor
        for x in (1, 2, 3):
            dshade(x, y, 0.9 - 0.25 * (x - 1), TIM_RAMP)
    R(1, 1, 3, 1, TIM_L)
    R(0, 2, 4, 2, TIM_M)                                     # book rail along its top
    for x in range(4, 27):                                   # seat
        dshade(x, 10, 0.95, TIM_RAMP)
        dshade(x, 11, 0.55, TIM_RAMP)
        dshade(x, 12, 0.15, TIM_RAMP)
    for y in range(13, 20):                                  # east leg
        dshade(23, y, 0.6, TIM_RAMP)
        dshade(24, y, 0.25, TIM_RAMP)
    R(4, 16, 22, 16, TIM_D)                                  # stretcher
    for x in (7, 15, 22):
        P(x, 10, TIM_D)
    grime(0, 1, 26, 19, 14, (TIM_D,), on=(TIM, TIM_M))


def lectern():
    """The preacher's lectern: a post on a foot under a sloped desk, high at the back and
    low to the reader, the book open on it. The book is part of it - it goes where the
    lectern goes."""
    R(1, 29, 12, 30, TIM_D)                                  # foot
    R(1, 29, 12, 29, TIM)
    for y in range(9, 29):                                   # post
        dshade(5, y, 0.9, TIM_RAMP)
        dshade(6, y, 0.6, TIM_RAMP)
        dshade(7, y, 0.2, TIM_RAMP)
    for x in range(1, 13):                                   # the desk, a wedge
        yt = int(round(3 + (x - 1) * 4 / 11.0))
        for y in range(yt, 9):
            dshade(x, y, 0.85 - 0.5 * (y - yt) / 6.0 - 0.25 * x / 12.0, TIM_RAMP)
        P(x, yt, TIM_L)
    R(1, 8, 12, 8, TIM_D)
    R(1, 3, 1, 8, TIM_M)
    for x in range(2, 12):                                   # the book, open on the slope
        yt = int(round(3 + (x - 1) * 4 / 11.0))
        if x in (2, 11):
            P(x, yt - 1, OX)
        elif x == 6:
            P(x, yt - 1, LINEN_D)
        else:
            P(x, yt - 1, PAGES)
            P(x, yt - 2, (212, 204, 178) if x < 6 else PAGES)
    R(11, 7, 11, 11, OX)                                     # the ribbon marker
    R(12, 9, 13, 11, KEY)


def candle_rack():
    """A stepped iron stand of candle stubs that stands along the wall under the
    banners. Stubs only: the flame is fire, not sprite."""
    R(0, 21, 17, 21, IRON_D)                                 # foot bar
    R(0, 20, 17, 20, IRON)
    for x in (1, 16):                                        # uprights
        R(x, 7, x, 20, IRON_M if x == 1 else IRON_D)
    for y, x0 in ((12, 1), (7, 3)):                          # two tiers
        R(0, y, 17, y, IRON)
        R(0, y, 17, y, IRON_M)
        R(0, y + 1, 17, y + 1, IRON_D)
        for cx in range(x0, 17, 4):
            h = 2 + int(rnd() * 3)
            R(cx, y - h, cx, y - 1, WAX)
            P(cx, y - h, WAX_L)
            P(cx, y - h - 1, IRON_D)                         # wick
            if chance(0.5):
                P(cx + 1, y - 1, WAX)                        # drip
    grime(0, 7, 17, 21, 6, (RUST, RUST_D), on=(IRON, IRON_M))


def ring_chandelier():
    """S30's ring of candles off the apex: an iron hoop seen edge-on (a flat ellipse,
    open in the middle), three hangers to the eye, candle stubs round the near rim, wax
    run off the bottom."""
    eye(22, 0, 2.5)
    cy, ry = 12.0, 3.5
    ln4(23, 5, 2, cy, IRON_M)
    ln4(23, 5, 44, cy, IRON)
    R(23, 5, 23, cy - ry, IRON_M)
    for x in range(1, 46):
        u = (x + 0.5 - 23.5) / 22.5
        k = math.sqrt(max(0.0, 1 - u * u))
        yt, yb = int(round(cy - ry * k)), int(round(cy + ry * k))
        dshade(x, yt, 0.6 - 0.3 * (u + 1) / 2, IRON_RAMP)                 # far side, in shadow
        dshade(x, yb, 0.95 - 0.4 * (u + 1) / 2, IRON_RAMP)                # near side, lit
        dshade(x, yb + 1, 0.3, IRON_RAMP)
        if yb - yt <= 1:
            R(x, yt, x, yb, IRON_M)
    for x in range(3, 45, 5):                                # candles on the near rim
        u = (x + 0.5 - 23.5) / 22.5
        yb = int(round(cy + ry * math.sqrt(max(0.0, 1 - u * u))))
        h = 3 + int(rnd() * 3)
        R(x, yb - h, x, yb - 1, WAX)
        P(x, yb - h, WAX_L)
        P(x, yb - h - 1, IRON_D)
        if chance(0.4):
            P(x, yb + 2, WAX)                                # wax run off the hoop
    grime(0, 6, 46, 16, 10, (RUST, RUST_D), on=IRON_RAMP)


def cresset():
    """S34's cresset off a vault crown: an iron basket of coals on its eye."""
    eye(3, 0, 2.5)
    R(4, 5, 4, 6, IRON_M)
    tpl(0, 7, [
        "MeMeMeMMD",
        "LMMMMMMMD",
        ".LMMMMMD.",
        "..DDDDD..",
    ], {'L': IRON_L, 'M': IRON, 'D': IRON_D, 'e': EMBER})
    P(0, 6, IRON_M)
    P(8, 6, IRON_D)
    P(2, 6, COAL_C)
    P(4, 6, COAL_C)
    P(6, 6, COAL_C)


COAL_C = (44, 44, 46)


# ═══════════════════════════════════════════════════════════════════════════
#  HAULAGE - S31, S32, S35
# ═══════════════════════════════════════════════════════════════════════════
def pater_car():
    """A paternoster car: a timber deck out from the chain-pin plate, an iron knee under
    it, a rail at the outer end so a rider is not thrown off at the top. The pin is a
    hole - the chain's pin goes through it, and the car hangs level off it."""
    for y in range(3, 19):                                   # the pin plate
        for x in (0, 1, 2):
            dshade(x, y, 0.8 - 0.25 * x - 0.01 * y, IRON_RAMP)
    R(0, 3, 2, 3, IRON_L)
    hole(1, 5)
    hole(1, 6)
    for x in range(3, 26):                                   # deck
        dshade(x, 7, 0.95, TIM_RAMP)
        dshade(x, 8, 0.5, TIM_RAMP)
        dshade(x, 9, 0.1, TIM_RAMP)
    for x in range(6, 26, 6):
        P(x, 8, TIM_D)
    for y in range(0, 7):                                    # end rail
        dshade(24, y, 0.75, TIM_RAMP)
        dshade(25, y, 0.25, TIM_RAMP)
    R(20, 0, 25, 0, TIM_M)
    R(20, 1, 23, 1, TIM_D)
    ln4(2, 16, 20, 10, IRON_M)                               # knee brace, two straps thick
    ln4(2, 17, 21, 10, IRON)
    P(1, 12, IRON_XL)                                        # bolts
    P(1, 16, IRON_XL)
    grime(0, 3, 25, 18, 14, (RUST, RUST_D), on=IRON_RAMP)


def _wheel(c, r_out, rim_in, hub, bore, spokes, teeth, ramp, tooth_h=2.0, phase=0.0,
           tooth_w=0.28, spoke_w=1.6):
    """A spinning wheel lit from its own centre: rim, teeth round the rim, straight
    spokes, a hub with its bore keyed out. Every tone depends only on distance from
    the centre or distance from a spoke's line - nothing on which way is up."""
    R_ = r_out + tooth_h
    n = len(ramp) - 1
    for y in range(int(c - R_) - 1, int(c + R_) + 2):
        for x in range(int(c - R_) - 1, int(c + R_) + 2):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            t = None
            if d > R_:
                continue
            if d > r_out:                                    # teeth
                if teeth:
                    f = ((a - phase) / (2 * math.pi / teeth)) % 1.0
                    if abs(f - 0.5) < tooth_w - 0.08 * (d - r_out) / tooth_h:
                        t = 0.85 - 0.3 * (d - r_out) / tooth_h
            elif d > rim_in:                                 # rim: lit lip outside, shadow in
                k = (d - rim_in) / (r_out - rim_in)
                t = 0.25 + 0.65 * k
                if d > r_out - 1.0:
                    t = 0.65
            elif d <= hub:                                   # hub
                if d <= bore:
                    continue
                t = 0.95 - 0.6 * (d - bore) / max(hub - bore, 1)
                if d > hub - 1.0:
                    t = 0.2
                if d < bore + 1.0:
                    P(x, y, INK)
                    continue
            else:                                            # spokes
                for s in range(spokes):
                    sa = phase + s * 2 * math.pi / spokes
                    along = dx * math.cos(sa) + dy * math.sin(sa)
                    across = -dx * math.sin(sa) + dy * math.cos(sa)
                    if along > 0 and abs(across) < spoke_w:
                        t = 0.8 - 0.55 * abs(across) / spoke_w
                        break
            if t is not None:
                dshade(x, y, t, ramp)
    return n


def pater_sprocket():
    """The paternoster's sprocket: an iron rim with sixteen teeth for the chain, six
    spokes, a fat hub on its shaft. It turns, so it is lit from its middle."""
    _wheel(28.5, 24.5, 20.5, 5.5, 2.2, 6, 16, IRON_RAMP, tooth_h=3.5, tooth_w=0.3, spoke_w=1.5)
    for s in range(6):                                       # bolts where the spokes meet the rim
        a = s * math.pi / 3
        P(int(28.5 + math.cos(a) * 19), int(28.5 + math.sin(a) * 19), IRON_XL)
    grime(0, 0, 56, 56, 30, (RUST, RUST_D), on=IRON_RAMP)


def drive_flywheel():
    """The flywheel of the winding engine in S31's pit, belted to the bottom sprocket."""
    _wheel(15.0, 14.0, 10.5, 3.5, 1.5, 5, 0, IRON_RAMP, tooth_h=0.0, spoke_w=1.3)
    grime(0, 0, 29, 29, 14, (RUST, RUST_D), on=IRON_RAMP)


def _rack(h, bays):
    """A timber storage rack side-on: two uprights, a shelf at every bay, a cap on top
    and a knee in each corner. The bays are open - every shelf is a floor, and nothing
    crosses a bay to stop a load sliding off when the rack goes over."""
    W = 42
    base = h + 2
    for x0 in (1, 37):                                       # uprights
        for y in range(0, base + 1):
            for i in range(4):
                dshade(x0 + i, y, 0.95 - 0.27 * i, TIM_RAMP)
    shelf_ys = [int(round(3 + (base - 9) * k / float(bays))) for k in range(bays + 1)]
    for sy in shelf_ys:                                      # shelves, cap first
        for x in range(0, W):
            dshade(x, sy, 0.95, TIM_RAMP)
            dshade(x, sy + 1, 0.55, TIM_RAMP)
            dshade(x, sy + 2, 0.12, TIM_RAMP)
        for x in (3, 39):
            P(x, sy + 1, IRON_M)                             # bolt heads
    for sy in shelf_ys:                                      # knees under each shelf
        for i in range(3):
            R(5, sy + 3 + i, 7 - i, sy + 3 + i, TIM_D if i else TIM)
            R(34 + i, sy + 3 + i, 36, sy + 3 + i, TIM_D)
    for x0 in (1, 37):                                       # feet
        R(x0 - 1, base, x0 + 4, base, TIM_D)
    grime(0, 0, W - 1, base, h // 3, (TIM_D, (46, 38, 30)), on=TIM_RAMP)


def store_rack_tall():
    """S32's tall rack - four bays, 136 high. Load it with crates, sacks and kegs and
    knock it over: it falls into the next."""
    _rack(134, 4)


def store_rack():
    _rack(108, 3)


def store_rack_low():
    """The short rack under the low end of the warehouse roof."""
    _rack(78, 2)


def pallet():
    """A pallet: deck boards on three blocks, the gaps between are what a fork goes in."""
    for x in range(0, 34):
        dshade(x, 0, 0.95, TIM_RAMP)
        dshade(x, 1, 0.45, TIM_RAMP)
    for x in range(5, 34, 6):
        P(x, 0, TIM_D)
    for x0 in (0, 15, 31):
        for y in (2, 3):
            for x in range(x0, x0 + 3):
                dshade(x, y, 0.6 - 0.2 * (x - x0) - 0.15 * (y - 2), TIM_RAMP)


def grain_sack():
    """A tied grain sack, the warehouse's soft load. It burns."""
    tpl(0, 0, [
        "....dbd....",
        ".....d.....",
        "...abbbd...",
        "..abbbbbd..",
        ".abbabbbbd.",
        "abbbbbbbbbd",
        "abbbbbbbbdd",
        "abbbbbbbbdd",
        ".bbbbbbbdd.",
        "..ddddddd..",
    ], {'a': GRAIN_L, 'b': GRAIN, 'd': GRAIN_D})
    grime(0, 2, 10, 9, 10, (GRAIN_D, GRAIN_L), on=(GRAIN,))


def keg():
    """The powder keg every crew keeps one or two of (S31-S39): staves, two iron hoops,
    a red stencil band. It is powder."""
    tpl(0, 0, [
        ".abbbbbd.",
        "IIIIIIIII",
        "abbbbbbbd",
        "abrrrrrbd",
        "abrRRRrbd",
        "abrrrrrbd",
        "abbbbbbbd",
        "abbbbbbbd",
        "IIIIIIIII",
        ".abbbbbd.",
        "..ddddd..",
    ], {'a': KEG_L, 'b': KEG, 'd': KEG_D, 'I': IRON_D, 'r': PAINT_R, 'R': PAINT_RL})
    P(1, 1, IRON_M)
    P(4, 0, IRON_D)                                          # bung
    grime(0, 0, 8, 10, 8, (KEG_D, RUST_D), on=(KEG, KEG_L))


def ladder_trolley():
    """S32's ladder trolley: two iron rails with rungs between, hooks at the top that
    ride the rail along the rack fronts, a wheel under each rail at the foot. It stands
    on a slant; climb it, push it along, or unhook it."""
    for x0 in (1, 7):
        for y in range(3, 102):
            dshade(x0, y, 0.85, IRON_RAMP)
            dshade(x0 + 1, y, 0.3, IRON_RAMP)
        R(x0, 0, x0 + 3, 0, IRON_L)                          # hook over the rail
        R(x0 + 3, 1, x0 + 3, 2, IRON_M)
        R(x0, 1, x0 + 1, 2, IRON_M)
    for y in range(8, 100, 6):                               # rungs
        R(3, y, 6, y, IRON_L)
    for cx in (1.5, 7.5):                                    # wheels
        DC(cx + 0.5, 103, 2.2, IRON_D)
        P(int(cx), 103, IRON_L)
    grime(0, 0, 11, 105, 26, (RUST, RUST_D), on=IRON_RAMP)


def zip_trolley():
    """S35's hook trolley: two grooved wheels that ride on the cable, a cheek plate under
    them, a hanger and the bar you hold. Hooked over the line, it runs down it."""
    for x0 in (0, 8):
        tpl(x0, 0, [
            ".LLMM.",
            "LMDDMD",
            "LDooDD",
            "MDooDD",
            "MMDDDD",
            ".DDDD.",
        ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D, 'o': IRON_XL})
    for y in range(6, 9):                                    # cheek plate, the cable runs over it
        for x in range(1, 13):
            dshade(x, y, 0.7 - 0.4 * x / 12.0 - 0.1 * (y - 6), IRON_RAMP)
    R(1, 6, 12, 6, IRON_L)
    R(6, 5, 7, 5, IRON_M)
    P(3, 7, IRON_XL)
    P(10, 7, IRON_XL)
    R(6, 9, 7, 17, IRON_M)                                   # hanger
    R(6, 9, 6, 17, IRON_L)
    R(1, 18, 12, 19, IRON_D)                                 # the bar
    R(1, 18, 12, 18, IRON_XL)
    grime(0, 6, 13, 19, 6, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  HOUSE - S37, S33
# ═══════════════════════════════════════════════════════════════════════════
def wardrobe():
    """A wardrobe stood up: cornice, two panelled doors, a knob, two feet. Heavy, tall,
    and it goes over - S37 has one on its back already."""
    for y in range(3, 30):
        for x in range(1, 16):
            dshade(x, y, 0.75 - 0.5 * x / 15.0, TIM_RAMP)
    R(0, 1, 16, 2, TIM_M)                                    # cornice
    R(0, 1, 16, 1, TIM_L)
    R(1, 3, 15, 3, TIM_D)
    for x0, x1 in ((2, 7), (9, 14)):                         # door panels, sunk
        R(x0, 5, x1, 27, TIM_D)
        R(x0 + 1, 6, x1 - 1, 26, TIM)
        R(x0 + 1, 6, x0 + 1, 26, TIM_M)
        R(x0 + 1, 16, x1 - 1, 16, TIM_D)
    R(8, 4, 8, 28, TIM_D)                                    # the meeting stile
    P(7, 15, IRON_L)
    P(9, 15, IRON_L)
    R(1, 29, 15, 29, TIM_D)
    for x0 in (1, 13):                                       # feet
        R(x0, 30, x0 + 2, 31, TIM_D)
        P(x0, 30, TIM)
    grime(1, 3, 15, 29, 16, (TIM_D, (46, 38, 30)), on=(TIM, TIM_M))


def bed():
    """A bed side-on: headboard, footboard, the frame between, a mattress and a pillow,
    room under it. Upstairs in S37, slid down to the east wall."""
    for y in range(1, 17):                                   # headboard
        for x in (1, 2, 3):
            dshade(x, y, 0.85 - 0.25 * (x - 1), TIM_RAMP)
    R(0, 1, 4, 1, TIM_L)
    R(0, 2, 4, 2, TIM_M)
    for y in range(6, 17):                                   # footboard
        dshade(34, y, 0.7, TIM_RAMP)
        dshade(35, y, 0.25, TIM_RAMP)
    R(33, 6, 36, 6, TIM_L)
    for x in range(4, 34):                                   # frame rail
        dshade(x, 11, 0.7, TIM_RAMP)
        dshade(x, 12, 0.2, TIM_RAMP)
    for y in range(6, 11):                                   # mattress
        for x in range(4, 34):
            dshade(x, y, 0.85 - 0.12 * (y - 6) - 0.2 * x / 33.0, BED_RAMP)
    R(4, 6, 33, 6, BED_L)
    for x in range(16, 34, 6):                               # blanket folds
        ln4(x, 7, x + 2, 10, BED_D)
    for y in (4, 5, 6):                                      # pillow
        for x in range(5, 12):
            dshade(x, y, 0.9 - 0.3 * (y - 4), (LINEN_D, LINEN))
    P(5, 4, KEY)
    P(11, 4, KEY)
    grime(4, 6, 33, 10, 10, (BED_D,), on=(BED,))


def table():
    """A table: a plank top on an apron, a leg at each end, open under it."""
    for x in range(0, 19):
        dshade(x, 1, 0.95, TIM_RAMP)
        dshade(x, 2, 0.55, TIM_RAMP)
        dshade(x, 3, 0.15, TIM_RAMP)
    R(2, 4, 16, 4, TIM_D)
    for x0 in (2, 15):
        for y in range(5, 13):
            dshade(x0, y, 0.7, TIM_RAMP)
            dshade(x0 + 1, y, 0.25, TIM_RAMP)
    grime(0, 1, 18, 4, 5, (TIM_D,), on=(TIM, TIM_M))


def chair():
    """A chair side-on, facing east: back post and back leg in one, the seat, a front
    leg. Throw it."""
    for y in range(0, 13):                                   # back post
        dshade(1, y, 0.8, TIM_RAMP)
        dshade(2, y, 0.35, TIM_RAMP)
    R(0, 0, 3, 0, TIM_L)
    R(1, 3, 3, 3, TIM_M)                                     # back rail
    for x in range(1, 9):                                    # seat
        dshade(x, 6, 0.95, TIM_RAMP)
        dshade(x, 7, 0.3, TIM_RAMP)
    for y in range(8, 13):                                   # front leg
        dshade(7, y, 0.6, TIM_RAMP)
        dshade(8, y, 0.2, TIM_RAMP)
    R(3, 10, 6, 10, TIM_D)                                   # stretcher


def chest():
    """A strapped timber chest with a hasp. Upstairs in S37, and the camp in S33."""
    for y in range(1, 11):
        for x in range(0, 16):
            dshade(x, y, 0.8 - 0.35 * x / 15 - 0.02 * y, TIM_RAMP)
    R(0, 1, 15, 1, TIM_L)
    R(0, 4, 15, 4, TIM_D)                                    # lid seam
    for x in (2, 13):                                        # iron straps
        R(x, 1, x, 10, IRON)
        P(x, 1, IRON_L)
    R(7, 4, 8, 6, IRON_M)                                    # hasp
    P(7, 5, IRON_XL)
    R(0, 10, 15, 10, TIM_D)
    grime(0, 1, 15, 10, 12, (TIM_D, RUST_D), on=TIM_RAMP)


def book():
    """One book, lying shut: the cover and the page edge."""
    c, l = BOOKS[0]
    R(0, 1, 6, 1, l)
    R(0, 2, 5, 3, c)
    R(6, 2, 6, 3, PAGES)
    R(0, 3, 6, 3, OX_D)
    P(6, 2, (208, 198, 170))


def book_stack():
    """A pile of books, the shelf's worth that came down in S37. The pile is one body;
    a shot knocks single books off it."""
    y = 9
    for k, (w, off) in enumerate(((8, 0), (7, 1), (8, 0), (6, 1))):
        c, l = BOOKS[k % len(BOOKS)]
        R(off, y - 1, off + w - 1, y - 1, l)
        R(off, y, off + w - 1, y, c)
        R(off + w - 1, y - 1, off + w - 1, y, PAGES)
        P(off, y, c)
        y -= 2
    R(0, 9, 7, 9, (36, 32, 30))


def bedroll():
    """S33's bedroll: a rolled blanket, two ties, the roll showing at the end."""
    for y in range(1, 6):
        for x in range(1, 15):
            dshade(x, y, 0.85 - 0.18 * (y - 1), BED_RAMP)
    for x in (4, 11):
        R(x, 1, x, 5, TIM_D)
        P(x, 1, TIM)
    RG(14, 3, 2, BED_D)
    P(14, 3, BED_L)
    R(1, 1, 13, 1, BED_L)
    grime(1, 1, 14, 5, 6, (BED_D,), on=(BED,))


def hanging_sack():
    """S33's sack of stores, hung off the cradle on its rope: a loop to hang it by, the
    tied neck, the sack. Burn the rope and it drops on the camp."""
    eye(6, 0, 2.5, (GRAIN_D, (120, 104, 78), GRAIN_L))
    R(7, 5, 7, 6, GRAIN_D)
    tpl(0, 6, [
        "......ddd......",
        ".......d.......",
        "....aabbbd.....",
        "..abbbbbbbbd...",
        ".abbbabbbbbbd..",
        "abbbbbbbbbbbbd.",
        "abbbbbbbbbbbbd.",
        "abbbbbbbbbbbdd.",
        "abbbbbbbbbbbdd.",
        ".bbbbbbbbbbbdd.",
        "..dddddddddd...",
    ], {'a': GRAIN_L, 'b': GRAIN, 'd': GRAIN_D})
    grime(0, 8, 14, 16, 12, (GRAIN_D, GRAIN_L), on=(GRAIN,))


def slate():
    """A clay roof tile off S37's steep pitch: a few slide off when it is hit."""
    tpl(0, 0, [
        ".lllll",
        "lTTTTTd",
        "TTTTTdd",
    ], {'l': TILE_L, 'T': TILE, 'd': TILE_D})


def roof_beam():
    """A squared roof timber, the one that went off S37's east pitch and leans on the
    wall: long, heavy, a peg hole at each end."""
    for y in range(0, 5):
        for x in range(0, 72):
            dshade(x, y, 0.95 - 0.22 * y, TIM_RAMP)
    for x in (0, 71):                                        # end grain
        R(x, 0, x, 4, TIM_M)
        P(x, 2, TIM_L)
    for _ in range(16):                                      # grain
        x = 2 + int(rnd() * 66)
        y = 1 + int(rnd() * 3)
        R(x, y, x + 1 + int(rnd() * 3), y, TIM_D)
    hole(4, 2)
    hole(67, 2)
    grime(0, 0, 71, 4, 20, (TIM_D, (46, 38, 30)), on=TIM_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  COLONNADE - S34
# ═══════════════════════════════════════════════════════════════════════════
def _drums(x0, y0, y1, joint0=None):
    """A fluted column shaft, lit from the west."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x0 + 13):
            dshade(x, y, 0.82 - 0.55 * (x - x0) / 12.0, BLK_RAMP)
    for fx in (x0 + 3, x0 + 6, x0 + 9):                      # flutes
        R(fx, y0 + 1, fx, y1 - 1, BLK_F if fx < x0 + 9 else BLK_D)
    R(x0, y0, x0, y1, BLK_L)
    R(x0 + 12, y0, x0 + 12, y1, BLK_D)
    if joint0 is not None:
        for y in range(joint0, y1, 15):
            R(x0, y, x0 + 12, y, BLK_D)


def _capital(y):
    for x in range(0, 21):                                   # abacus
        for yy in range(y, y + 4):
            dshade(x, yy, 0.85 - 0.4 * x / 20.0 - 0.1 * (yy - y), BLK_RAMP)
    R(0, y, 20, y, BLK_L)
    for x in range(2, 19):                                   # echinus
        for yy in range(y + 4, y + 7):
            dshade(x, yy, 0.7 - 0.4 * x / 18.0 - 0.12 * (yy - y - 4), BLK_RAMP)
    R(2, y + 6, 18, y + 6, BLK_D)


def _plinth(y):
    for x in range(0, 21):
        for yy in range(y, y + 5):
            dshade(x, yy, 0.85 - 0.4 * x / 20.0 - 0.1 * (yy - y), BLK_RAMP)
    R(0, y, 20, y, BLK_L)
    R(0, y + 4, 20, y + 4, BLK_D)


def column_whole():
    """A whole column of S34's row: plinth, a shaft of drums, the capital. Standing, it
    holds the vault; shot through at the foot, it is a 110-pixel stone lever falling
    into the next one."""
    _capital(0)
    _drums(4, 7, 104, 20)
    _plinth(105)
    grime(0, 0, 20, 109, 40, (BLK_D, BLK_F, (96, 104, 86)), on=BLK_RAMP)


def column_capital():
    _capital(0)
    _drums(4, 7, 8)
    grime(0, 0, 20, 8, 6, (BLK_D,), on=BLK_RAMP)


def column_drum():
    """One drum of a column shaft - what the row breaks into, and what rolls."""
    _drums(0, 0, 14)
    R(0, 0, 12, 0, BLK_L)
    R(0, 14, 12, 14, BLK_D)
    grime(0, 0, 12, 14, 8, (BLK_D, BLK_F), on=BLK_RAMP)


def column_plinth():
    _drums(4, 0, 1)
    _plinth(2)


def voussoir():
    """An arch stone off the vault: a wedge, wider at the back, the face lit."""
    tpl(0, 0, [
        "lllllllll",
        "lBBBBBBBd",
        ".BBBBBBd.",
        ".lBBBBBd.",
        "..BBBBd..",
        "..ddddd..",
    ], {'l': BLK_L, 'B': BLK, 'd': BLK_D})
    P(3, 2, BLK_F)
    P(5, 3, BLK_F)


# ═══════════════════════════════════════════════════════════════════════════
#  CLOCKWORK - S38
# ═══════════════════════════════════════════════════════════════════════════
def _clock_wheel(r, teeth, spokes):
    """A brass clock wheel: tapered teeth, a rim, crossed spokes of flat bar, a boss on
    the arbor - the bore keyed out, the arbor is the room's. The spokes and the teeth
    are what you stand on, and the gaps between are air."""
    c = r + 8.0
    _wheel(c, float(r), r - 6.0, 10.5, 3.2, spokes, teeth, BRASS_RAMP, tooth_h=7.0,
           tooth_w=0.27, spoke_w=3.0)
    for s in range(spokes):                                  # rivets where the spokes meet the rim
        a = s * 2 * math.pi / spokes
        for rr in (r - 7.5, 12.5):
            P(int(c + math.cos(a) * rr), int(c + math.sin(a) * rr), IRON_L)
    grime(0, 0, int(2 * c), int(2 * c), r, (BRASS_D, (90, 96, 70)), on=BRASS_RAMP)


def clock_wheel_a():
    """The great wheel at the foot of the train: 22 teeth, six spokes."""
    _clock_wheel(66, 22, 6)


def clock_wheel_b():
    _clock_wheel(44, 15, 5)


def clock_wheel_c():
    """The top wheel, the one the weight's chain winds off."""
    _clock_wheel(56, 19, 6)


def clock_wheel_d():
    _clock_wheel(30, 10, 4)


def clock_wheel_spare():
    """The spare leaned against the wall by R2: it rolls."""
    _wheel(22.0, 14.0, 10.0, 5.5, 2.0, 4, 8, BRASS_RAMP, tooth_h=6.0, tooth_w=0.28,
           spoke_w=2.0)
    grime(0, 0, 43, 43, 10, (BRASS_D,), on=BRASS_RAMP)


def clock_weight():
    """The iron weight that drives the train, on its eye: cut its chain and the wheels
    stop - and it falls on the shelf under it."""
    eye(8, 0, 3.5)
    R(8, 7, 10, 8, IRON_M)
    for y in range(9, 29):
        for x in range(0, 19):
            dshade(x, y, 0.8 - 0.55 * x / 18.0 - 0.15 * (y - 8) / 20.0, IRON_RAMP)
    R(0, 9, 18, 9, IRON_L)
    R(0, 28, 18, 28, IRON_D)
    for y in (15, 16, 17):                                   # cast band
        R(1, y, 17, y, IRON_D if y == 17 else IRON if y == 16 else IRON_L)
    grime(0, 8, 18, 28, 16, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  TRENCH - S39
# ═══════════════════════════════════════════════════════════════════════════
def sandbag():
    """A sandbag: the brick of the parapet. Stack them, shoot them out, they slump."""
    tpl(0, 0, [
        ".aaaaaa.",
        "abbbbbbd",
        "abbdbbbd",
        ".dddddd.",
    ], {'a': BAG_L, 'b': BAG, 'd': BAG_D})


def revet_panel():
    """A height of trench revetment: boards laid one on another against the earth, held
    by a post. Shoot it out and the wall behind it comes in."""
    for y in range(3, 36):
        board = (y - 3) // 4
        for x in range(0, 3):
            dshade(x, y, 0.75 - 0.2 * x - (0.35 if (y - 3) % 4 == 3 else 0), TIM_RAMP)
        if (y - 3) % 4 == 0:
            P(0, y, TIM_L)
        if board % 3 == 1 and (y - 3) % 4 == 1:
            P(1, y, TIM_D)
    for y in range(0, 36):                                   # the post, earth side
        dshade(3, y, 0.3, TIM_RAMP)
    P(3, 0, TIM_M)
    for y in range(5, 36, 10):
        P(1, y, IRON_M)                                      # nails


def wire_coil():
    """A coil of barbed wire: loops overlapping along its length, barbs on them. Lay it
    out in front of a line; it rolls if it is pushed."""
    for k in range(4):
        cx = 5.0 + k * 4.0
        prev = None
        for i in range(48):
            a = i * 2 * math.pi / 48
            x, y = int(round(cx + 4.4 * math.cos(a))), int(round(6.0 + 5.0 * math.sin(a)))
            if prev is not None and x != prev[0] and y != prev[1]:
                P(x, prev[1], WIRE_D)
            P(x, y, WIRE_L if math.sin(a) < -0.3 and math.cos(a) < 0.3 else WIRE)
            prev = (x, y)
    for k in range(4):                                       # barbs, twisted on in pairs
        cx = 5 + k * 4
        for (bx, by) in ((cx + 2, 1), (cx - 2, 10)):
            if AT(bx, by) != KEY:
                P(bx, by, IRON_XL)
                P(bx + 1, by, WIRE_D)


def barricade():
    """S39's barricade: logs laid between two posts, a slit left between the top two to
    shoot through. The logs are pinned to the posts, so it goes over as one."""
    for k, y in enumerate((19, 15, 11, 3)):
        for yy in range(y, y + 4):
            for x in range(1, 26):
                dshade(x, yy, 0.95 - 0.27 * (yy - y), TIM_RAMP)
        RG(1.5, y + 1.5, 1.6, TIM_D)                         # end grain on the west end
        P(1, y + 1, TIM_L)
        R(25, y, 25, y + 3, TIM_M)
    for x0 in (5, 20):                                       # posts
        for y in range(0, 24):
            dshade(x0, y, 0.55, TIM_RAMP)
            dshade(x0 + 1, y, 0.12, TIM_RAMP)
        P(x0, 0, TIM_L)
    for y in (13, 21):
        P(5, y, IRON_M)
        P(20, y, IRON_M)
    grime(0, 0, 26, 23, 16, (TIM_D, (46, 38, 30)), on=TIM_RAMP)


def barricade_log():
    """A log off the barricade."""
    log_h(0, 0, 25, 3)
    RG(1.5, 1.5, 1.6, TIM_D)
    P(1, 1, TIM_L)


# ═══════════════════════════════════════════════════════════════════════════
#  MENAGERIE - S36
# ═══════════════════════════════════════════════════════════════════════════
STRAW, STRAW_D = (150, 128, 76), (104, 88, 52)
MEAT_D, MEAT = (74, 30, 30), (112, 46, 42)


def _cage(w, h, ox=0):
    """A keeper's cage side-on: a roof plate with its lifting eye, a floor plate with
    straw on it, bars every 3px between (2px gaps - a spider stays in, a shot goes
    through), a band round the middle. Empty: what is in it is its own body."""
    x0, top = ox + 1, 5
    bot = top + h
    eye(ox + w // 2 + 1, 0, 2.5)
    for y in range(top, top + 3):                            # roof plate
        for x in range(x0 - 1, x0 + w + 2):
            dshade(x, y, 0.85 - 0.35 * (x - x0) / w - 0.25 * (y - top), IRON_RAMP)
    for y in range(bot - 2, bot + 1):                        # floor plate
        for x in range(x0 - 1, x0 + w + 2):
            dshade(x, y, 0.6 - 0.3 * (x - x0) / w - 0.2 * (y - bot + 2), IRON_RAMP)
    for x in range(x0 + 1, x0 + w, 2):
        if chance(0.6):
            P(x, bot - 2, pick((STRAW, STRAW_D)))
    for i, x in enumerate(range(x0, x0 + w + 1, 3)):         # bars
        corner = i == 0 or x >= x0 + w - 1
        for y in range(top + 3, bot - 2):
            P(x, y, IRON_M if corner or i % 2 else RUST)
        P(x, top + 3 + int(rnd() * (h - 6)), IRON_L)
    R(x0, top + h // 2, x0 + w, top + h // 2, IRON_D)       # the band
    grime(ox, top, ox + w + 2, bot, w, (RUST, RUST_D, RUST_L), on=IRON_RAMP)
    return bot


def beast_cage():
    """S36's cage, the one stacked two high on the shelves."""
    _cage(27, 27)


def beast_cage_big():
    """The big cage hung in the middle of the hall, with the Ghast in it."""
    _cage(33, 35)


def beast_cage_small():
    _cage(21, 21)


def cage_cart():
    """A cage on a wheeled board with a push handle, the way the keepers move them: the
    cage is bolted to the board, so it is one body."""
    bot = _cage(27, 25)
    for x in range(0, 31):                                   # the board
        dshade(x, bot + 1, 0.85, TIM_RAMP)
        dshade(x, bot + 2, 0.25, TIM_RAMP)
    for wx in (5.5, 25.5):                                   # wheels on their axle blocks
        ball(wx, bot + 5.5, 2.6, IRON_RAMP, 0.45)
        P(int(wx), bot + 5, IRON_L)
    for k in range(2):                                       # the handle
        ln4(30, bot + 1 + k, 39, bot - 8 + k, TIM_M if k == 0 else TIM_D)
    R(38, bot - 9, 40, bot - 8, TIM_L)


def feed_bucket():
    """A keeper's bucket: a tapered iron U with a rolled rim, a hoop round it and a bail
    over it, and what the beasts get in the bottom of it."""
    prev = None
    for x in range(1, 10):                                   # the bail
        y = int(round(5 - 5 * math.sqrt(max(0.0, 1 - ((x - 5) / 4.0) ** 2))))
        y0 = y if prev is None else min(y, prev)
        R(x, y0, x, max(y, prev if prev is not None else y), IRON_M if x < 5 else IRON)
        prev = y
    R(1, 4, 1, 5, IRON_M)
    for y in range(5, 13):                                   # walls, stepping in
        k = (y - 5) // 4
        dshade(1 + k, y, 0.9, IRON_RAMP)
        dshade(2 + k, y, 0.55, IRON_RAMP)
        dshade(8 - k, y, 0.35, IRON_RAMP)
        dshade(9 - k, y, 0.15, IRON_RAMP)
    for x in range(2, 9):                                    # bottom
        dshade(x, 12, 0.4 - 0.03 * x, IRON_RAMP)
    R(0, 5, 3, 5, IRON_XL)                                   # rolled rim
    R(7, 5, 10, 5, IRON_L)
    for x in (1, 2, 8, 9):                                   # hoop
        P(x, 8, IRON_D)
    for x in range(4, 8):                                    # the feed, slopped in
        P(x, 11, pick((MEAT, MEAT_D, BONE_D)))
        if chance(0.5):
            P(x, 10, pick((MEAT, MEAT_D)))
    grime(0, 5, 10, 12, 6, (RUST, RUST_D), on=IRON_RAMP)


def keeper_pole():
    """A keeper's prod: an ash shaft with an iron hook at the end, to steer what is in a
    cage from outside it."""
    for y in range(5, 28):
        dshade(2, y, 0.85, TIM_RAMP)
        dshade(3, y, 0.3, TIM_RAMP)
    tpl(0, 0, [
        "LLLM.",
        "M...D",
        "D...D",
        "...MD",
        "..MD.",
    ], {'L': IRON_L, 'M': IRON_M, 'D': IRON_D})
    R(2, 21, 3, 22, TIM_D)                                   # grip binding
    R(2, 24, 3, 24, TIM_D)


GROUPS = [
    ("NEST", [
        ("EggSac", "EGG SAC", egg_sac, (10, 17), WOOD, None),
        ("EggCluster", "SAC CLUSTER", egg_cluster, (27, 24), WOOD, None),
        ("CocoonHung", "COCOON", cocoon_hung, (12, 32), WOOD, None),
        ("CocoonLying", "COCOON", cocoon_lying, (26, 11), WOOD, None),
        ("SilkNet", "SILK NET", silk_net, (28, 13), WOOD, None),
        ("SilkCurtain", "SILK CURTAIN", silk_curtain, (11, 41), WOOD, None),
    ]),
    ("CHAPEL", [
        ("BannerRed", "BANNER", banner_red, (19, 96), WOOD, None),
        ("BannerViolet", "BANNER", banner_violet, (19, 90), WOOD, None),
        ("BannerShort", "BANNER", banner_short, (19, 44), WOOD, None),
        ("Pew", "PEW", pew, (28, 21), WOOD, None),
        ("Lectern", "LECTERN", lectern, (14, 32), WOOD, None),
        ("CandleRack", "CANDLE RACK", candle_rack, (18, 22), METAL, None),
        ("RingChandelier", "RING CHANDELIER", ring_chandelier, (47, 18), METAL, None),
        ("Cresset", "CRESSET", cresset, (9, 11), METAL, None),
    ]),
    ("HAULAGE", [
        ("PaternosterCar", "PATERNOSTER CAR", pater_car, (27, 20), WOOD, None),
        ("PaternosterSprocket", "SPROCKET", pater_sprocket, (57, 57), METAL, None),
        ("DriveFlywheel", "FLYWHEEL", drive_flywheel, (30, 30), METAL, None),
        ("StoreRackTall", "RACK", store_rack_tall, (42, 137), WOOD, None),
        ("StoreRack", "RACK", store_rack, (42, 111), WOOD, None),
        ("StoreRackLow", "RACK", store_rack_low, (42, 81), WOOD, None),
        ("Pallet", "PALLET", pallet, (34, 4), WOOD, None),
        ("GrainSack", "SACK", grain_sack, (11, 10), WOOD, "decor"),
        ("Keg", "POWDER KEG", keg, (9, 11), WOOD, "explosive"),
        ("LadderTrolley", "LADDER TROLLEY", ladder_trolley, (12, 106), METAL, None),
        ("ZipTrolley", "HOOK TROLLEY", zip_trolley, (14, 21), METAL, None),
    ]),
    ("HOUSE", [
        ("Wardrobe", "WARDROBE", wardrobe, (17, 32), WOOD, "decor"),
        ("Bed", "BED", bed, (37, 17), WOOD, "decor"),
        ("Table", "TABLE", table, (19, 13), WOOD, "decor"),
        ("Chair", "CHAIR", chair, (10, 13), WOOD, "decor"),
        ("Chest", "CHEST", chest, (16, 11), WOOD, "decor"),
        ("Book", "BOOK", book, (7, 4), WOOD, "decor"),
        ("BookStack", "BOOKS", book_stack, (8, 10), WOOD, "decor"),
        ("Bedroll", "BEDROLL", bedroll, (17, 7), WOOD, "decor"),
        ("HangingSack", "HUNG SACK", hanging_sack, (15, 17), WOOD, None),
        ("Slate", "SLATE", slate, (7, 3), DEFAULT, None),
        ("RoofBeam", "ROOF BEAM", roof_beam, (72, 5), WOOD, None),
    ]),
    ("COLONNADE", [
        ("Column", "COLUMN", column_whole, (21, 110), DEFAULT, None),
        ("ColumnCapital", "CAPITAL", column_capital, (21, 9), DEFAULT, None),
        ("ColumnDrum", "DRUM", column_drum, (13, 15), DEFAULT, None),
        ("ColumnPlinth", "PLINTH", column_plinth, (21, 7), DEFAULT, None),
        ("Voussoir", "ARCH STONE", voussoir, (9, 6), DEFAULT, None),
    ]),
    ("MENAGERIE", [
        ("BeastCage", "BEAST CAGE", beast_cage, (30, 33), METAL, None),
        ("BeastCageBig", "BIG CAGE", beast_cage_big, (36, 41), METAL, None),
        ("BeastCageSmall", "SMALL CAGE", beast_cage_small, (24, 27), METAL, None),
        ("CageCart", "CAGE CART", cage_cart, (41, 39), METAL, None),
        ("FeedBucket", "FEED BUCKET", feed_bucket, (11, 13), METAL, None),
        ("KeeperPole", "KEEPER POLE", keeper_pole, (5, 28), WOOD, None),
    ]),
    ("CLOCKWORK", [
        ("ClockWheelA", "CLOCK WHEEL", clock_wheel_a, (148, 148), METAL, None),
        ("ClockWheelC", "CLOCK WHEEL", clock_wheel_c, (128, 128), METAL, None),
        ("ClockWheelB", "CLOCK WHEEL", clock_wheel_b, (104, 104), METAL, None),
        ("ClockWheelD", "CLOCK WHEEL", clock_wheel_d, (76, 76), METAL, None),
        ("ClockWheelSpare", "SPARE WHEEL", clock_wheel_spare, (44, 44), METAL, None),
        ("ClockWeight", "DRIVE WEIGHT", clock_weight, (19, 29), METAL, None),
    ]),
    ("TRENCH", [
        ("Sandbag", "SANDBAG", sandbag, (8, 4), DEFAULT, None),
        ("RevetPanel", "REVETMENT", revet_panel, (4, 36), WOOD, None),
        ("WireCoil", "WIRE COIL", wire_coil, (22, 12), METAL, None),
        ("Barricade", "BARRICADE", barricade, (27, 24), WOOD, None),
        ("BarricadeLog", "LOG", barricade_log, (26, 4), WOOD, None),
    ]),
]

# where a rope or a chain ties on (pixels from the top-left), for the prefab's anchors
ANCHORS = {
    "EggSac": {"Eye": eye_at(3, 0, 2.5)},
    "EggCluster": {"Eye": eye_at(11, 0, 2.5)},
    "CocoonHung": {"Eye": eye_at(4, 0, 2.5)},
    "SilkNet": {"West": (0.5, 5.5), "East": (27.5, 5.5)},
    "SilkCurtain": {"Eye": eye_at(4, 0, 2.5)},
    "BannerRed": {"EyeW": eye_at(1, 0, 2.5), "EyeE": eye_at(14, 0, 2.5)},
    "BannerViolet": {"EyeW": eye_at(1, 0, 2.5), "EyeE": eye_at(14, 0, 2.5)},
    "BannerShort": {"EyeW": eye_at(1, 0, 2.5), "EyeE": eye_at(14, 0, 2.5)},
    "RingChandelier": {"Eye": eye_at(22, 0, 2.5)},
    "Cresset": {"Eye": eye_at(3, 0, 2.5)},
    "PaternosterCar": {"Pin": (1.5, 6.0)},
    "PaternosterSprocket": {"Axle": (28.5, 28.5)},
    "DriveFlywheel": {"Axle": (15.0, 15.0)},
    "LadderTrolley": {"HookW": (3.0, 1.5), "HookE": (9.0, 1.5)},
    "ZipTrolley": {"Cable": (7.0, 5.0)},
    "HangingSack": {"Eye": eye_at(6, 0, 2.5)},
    "BeastCage": {"Eye": eye_at(14, 0, 2.5)},
    "BeastCageBig": {"Eye": eye_at(17, 0, 2.5)},
    "BeastCageSmall": {"Eye": eye_at(11, 0, 2.5)},
    "ClockWheelA": {"Axle": (74.0, 74.0)},
    "ClockWheelB": {"Axle": (52.0, 52.0)},
    "ClockWheelC": {"Axle": (64.0, 64.0)},
    "ClockWheelD": {"Axle": (38.0, 38.0)},
    "ClockWheelSpare": {"Axle": (22.0, 22.0)},
    "ClockWeight": {"Eye": eye_at(8, 0, 3.5)},
}

# what gives light, and from where (pixels from the top-left) - see roomprops.py
LIGHTS = {
    "Cresset": dict(at=(4.5, 7), color=(1.0, 0.6, 0.28), intensity=1.3, radius=7.0, flicker=0.2),
    "CandleRack": dict(at=(9, 6), color=(1.0, 0.8, 0.52), intensity=0.8, radius=5.0, flicker=0.15),
}
