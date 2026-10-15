"""Room props, part 1: things that hang and things that lie about.

Bells, cages, buckets, counterweights and lamps-on-chains from S01-S14 and S28, and the
loose stuff nearly every room has a few of - logs, sacks, crates, drums, tubs, bones,
boulders. Built by `roomprops.py`; read its docstring for what the entries mean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402

TITLE = "HUNG AND LOOSE"
SEED = 9100

BRONZE_D, BRONZE, BRONZE_M, BRONZE_L = (50, 45, 37), (86, 78, 64), (110, 99, 78), (150, 134, 98)
BONE_D, BONE, BONE_L = (110, 104, 88), (158, 150, 128), (196, 190, 168)
STONE_D, STONE, STONE_M, STONE_L = (52, 54, 58), (78, 80, 84), (100, 101, 93), (128, 126, 114)
COAL_D, COAL = (24, 24, 26), (44, 44, 46)
WAX, WAX_L = (186, 170, 130), (222, 210, 170)
EMBER = (232, 150, 70)

BRONZE_RAMP = (BRONZE_D, BRONZE, BRONZE_M, BRONZE_L)
BONE_RAMP = (BONE_D, BONE, BONE_L)
STONE_RAMP = (STONE_D, STONE, STONE_M, STONE_L)
SACK_RAMP = (SACK_D, SACK, SACK_L)
RUST_RAMP = (RUST_D, RUST, RUST_L)


def eye(cx, top, r=3.0, ramp=IRON_RAMP):
    """A lifting eye: a ring with its hole keyed out, for a rope or a hook."""
    for y in range(int(top), int(top + 2 * r) + 1):
        for x in range(int(cx - r), int(cx + r) + 2):
            d = math.hypot(x - cx - 0.5, y - top - r)
            if r - 1.6 <= d <= r + 0.4:
                dshade(x, y, 0.8 - 0.4 * (x - cx) / r - 0.3 * (y - top) / r, ramp)
    for y in range(int(top), int(top + 2 * r) + 1):
        for x in range(int(cx - r), int(cx + r) + 2):
            if math.hypot(x - cx - 0.5, y - top - r) < r - 1.6:
                hole(x, y)


def ball(cx, cy, r, ramp, lit=0.6):
    """A shaded sphere or disc, lit from the top left."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r * r:
                t = lit - 0.45 * (dx + dy) / (2 * r) - 0.25 * math.hypot(dx, dy) / r
                dshade(x, y, t, ramp)


# ═══════════════════════════════════════════════════════════════════════════
#  HUNG
# ═══════════════════════════════════════════════════════════════════════════
def bell():
    """S04's bell, side-on and a little from below: a solid bronze body with the mouth
    showing as an arch at the bottom, so it is open underneath - drop it on someone and
    they are under it - but still reads as a bell, not a tent. The clapper hangs in the
    mouth from the roof of the arch."""
    cx = 28
    eye(cx - 0.5, 0, 3.5, BRONZE_RAMP)
    for y in range(7, 11):                                  # crown block
        for x in range(cx - 7, cx + 7):
            dshade(x, y, 0.85 - 0.6 * (x - cx + 7) / 14, BRONZE_RAMP)
    top, lip = 11, 64
    depth = 15                                              # how far up the mouth goes

    def half(y):
        t = (y - top) / float(lip - top)
        return 10 + 9 * t ** 2.2 + (6 * ((t - 0.72) / 0.28) ** 1.6 if t > 0.72 else 0)

    mouth = half(lip) - 8

    def in_mouth(x, y, grow=0.0):
        d = abs(x + 0.5 - cx)
        wall = 6.5 - grow                                   # the wall never thins below this
        return ((d / (mouth + grow)) ** 2 + ((lip + 1 - y) / (depth + grow)) ** 2 < 1
                and d < half(y) - wall)

    for y in range(top, lip + 1):
        hw = half(y)
        t = (y - top) / float(lip - top)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if in_mouth(x, y):
                continue
            u = (x - cx) / hw
            if in_mouth(x, y, 1.6):                         # the inside of the lip, in shadow
                P(x, y, BRONZE_D)
                continue
            # round body: lit a third of the way in from the west edge, dark at the east
            dshade(x, y, 0.85 - 1.1 * abs(u + 0.35) - 0.12 * t, BRONZE_RAMP)
    for y in (top + 4, int(top + (lip - top) * 0.55), lip - 5):      # cast bands
        hw = half(y)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if AT(x, y) != KEY and not in_mouth(x, y, 1.6):
                P(x, y, BRONZE_D if (x - cx) > -hw + 2 else BRONZE_M)
    for y in range(lip - 2, lip + 1):                       # the lip, a rolled edge
        hw = half(lip) + 0.5
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not in_mouth(x, y, 1.6):
                dshade(x, y, 0.55 - 0.4 * (x - cx) / hw, BRONZE_RAMP)
    R(cx - 1, lip - depth, cx, lip - 7, IRON)               # clapper rod from the arch roof
    P(cx - 1, lip - depth + 3, IRON_M)
    ball(cx - 0.5, lip - 4, 3.4, IRON_RAMP, 0.5)
    grime(0, top, 56, lip + 1, 70, (BRONZE_D, (70, 84, 74), (60, 70, 62)), on=BRONZE_RAMP)


def hanging_cage():
    """A cage on a chain: bail ring, domed cap, bars with two rungs, a floor. Bars with
    gaps, so a shot goes through and whatever is inside can be hit; one body."""
    eye(9.5, 0, 2.5)
    for y in range(5, 8):                                   # cap
        hw = 4 + (y - 5) * 3
        for x in range(10 - hw, 10 + hw + 1):
            dshade(x, y, 0.8 - 0.5 * (x - 10 + hw) / (2 * hw), IRON_RAMP)
    for x in range(1, 20, 3):                               # bars
        for y in range(8, 27):
            P(x, y, IRON_M if x < 10 else IRON)
        P(x, 8, IRON_L)
    for y in (13, 21):                                      # rungs
        R(1, y, 19, y, IRON_D)
    box(0, 27, 20, 28, IRON_D, IRON, IRON_M)                # floor
    grime(0, 5, 20, 28, 24, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def gibbet():
    """S14's gibbet: a cage the shape of the man in it, and what is left of him. The
    bones are wired to the hoops, so the whole thing comes down as one."""
    eye(7.5, 0, 2.5)
    R(7, 5, 8, 6, IRON_M)
    # hoops, body-shaped: head, shoulders, waist, knees
    hoops = [(7, 4), (10, 6), (16, 5), (22, 4), (26, 3)]
    for y, hw in hoops:
        R(8 - hw, y, 7 + hw, y, IRON_D if y > 7 else IRON_M)
    for side in (-1, 1):                                    # the straps between hoops
        for (y0, w0), (y1, w1) in zip(hoops, hoops[1:]):
            for y in range(y0, y1 + 1):
                hw = w0 + (w1 - w0) * (y - y0) / float(y1 - y0)
                x = int(7.5 + side * (hw + 0.5) - (1 if side > 0 else 0))
                P(x, y, IRON_M if side < 0 else IRON)
    R(5, 7, 10, 7, IRON)
    # the skull, hanging forward in the head hoop
    tpl(5, 7, [
        ".bBb.",
        "bBBBd",
        "BoBod",
        ".bBd.",
        "..d..",
    ], {'b': BONE_L, 'B': BONE, 'd': BONE_D, 'o': INK})
    for y in range(12, 22):                                 # spine and ribs
        P(7, y, BONE)
        if y in (12, 14, 16):
            R(4, y, 11, y, BONE_D)
            P(4, y, BONE)
            P(11, y, BONE_D)
    R(5, 21, 10, 22, BONE_D)                                # pelvis on the waist hoop
    P(6, 21, BONE_L)
    for x in (6, 9):                                        # legs down to the knee hoop
        for y in range(23, 27):
            P(x, y, BONE if x == 6 else BONE_D)
    grime(0, 4, 15, 27, 18, (RUST, RUST_D), on=IRON_RAMP)


def hoist_bucket():
    """The ore bucket on the hoist chain (S01, S08, S19): a tapered iron U with a rolled
    rim and a bail arched over it, open at the top so ore goes in and tips out."""
    for x in range(1, 18):                                  # the bail, a half hoop
        y = int(round(6 - 6 * math.sqrt(max(0.0, 1 - ((x - 9) / 8.0) ** 2))))
        P(x, y, IRON_L if x < 9 else IRON_M)
        if x in (1, 17):
            R(x, y, x, 6, IRON_M)
    for y in range(6, 16):
        k = (y - 6) // 4                                    # sides step in as they go down
        for i in range(3):
            dshade(k + i, y, 0.85 - 0.12 * i - 0.02 * y, IRON_RAMP)
            dshade(18 - k - i, y, 0.42 - 0.08 * i - 0.02 * y, IRON_RAMP)
    for y in (14, 15):                                      # the floor
        for x in range(2, 17):
            dshade(x, y, 0.55 - 0.02 * x - 0.15 * (y - 14), IRON_RAMP)
    R(0, 6, 3, 6, IRON_XL)                                  # rolled rim
    R(15, 6, 18, 6, IRON_L)
    for y in (9, 12):                                       # hoops
        k = (y - 6) // 4
        R(k, y, k + 2, y, IRON_D)
        R(16 - k, y, 18 - k, y, IRON_D)
    grime(0, 6, 18, 15, 22, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def counterweight():
    """S13's counterweight: cast slabs on a tie rod, an eye on top, hazard paint on the
    bottom slab. The heaviest thing in the room for its size."""
    eye(12, 0, 3.5)
    R(11, 7, 13, 9, IRON_M)                                 # tie rod head
    slabs = [(10, 18), (19, 27), (28, 36), (37, 46)]
    for k, (y0, y1) in enumerate(slabs):
        for y in range(y0, y1 + 1):
            for x in range(0, 25):
                dshade(x, y, 0.8 - 0.55 * x / 24 - 0.25 * (y - y0) / (y1 - y0), IRON_RAMP)
        R(0, y1, 24, y1, IRON_D)
        R(0, y0, 24, y0, IRON_L if k == 0 else IRON_M)
        P(12, y0 + 3, IRON_D)                               # the rod through it
        P(12, y0 + 4, IRON_XL)
    stripes(1, 40, 23, 45, 3)
    grime(0, 10, 24, 46, 60, (RUST, RUST_D, IRON_D), on=IRON_RAMP)


def candle_crown():
    """S14's candle crown: an iron hoop seen edge-on, spikes under it, candle stubs and a
    few bones wired along the top, and an eye for the chain. Falls, and the candles go
    with it."""
    eye(12, 0, 2.5)
    LN(4, 8, 11, 5, IRON_M)                                 # the three hangers to the eye
    LN(20, 8, 13, 5, IRON)
    R(12, 5, 12, 7, IRON_M)
    for x in range(0, 25):                                  # hoop
        dshade(x, 8, 0.85 - 0.5 * x / 24, IRON_RAMP)
        dshade(x, 9, 0.5 - 0.4 * x / 24, IRON_RAMP)
    for x in range(1, 25, 4):                               # spikes
        P(x, 10, IRON_D)
    P(1, 11, IRON_D)
    P(23, 11, IRON_D)
    for x, h in ((2, 3), (7, 2), (17, 3), (22, 2)):         # candles
        R(x, 8 - h, x, 7, WAX)
        P(x, 8 - h, WAX_L)
    R(9, 7, 15, 7, BONE)                                    # a long bone along the top
    P(9, 6, BONE_L)
    P(15, 6, BONE_D)
    grime(0, 8, 24, 10, 6, (RUST,), on=IRON_RAMP)


def censer():
    """S26's censer: a small iron pot on its chain, lid pierced, coals showing."""
    eye(3.5, 0, 2.0)
    R(3, 4, 4, 4, IRON_M)
    tpl(0, 5, [
        "..LML...",
        ".LMoMMD.",
        "LMMMMMMD",
        "MeMMeMMD",
        "LMMMMMMD",
        ".MMMMMD.",
        "..DDDD..",
    ], {'L': IRON_L, 'M': IRON, 'D': IRON_D, 'o': IRON_XL, 'e': EMBER})


def wrecking_ball():
    """S28's wrecking ball: a riveted iron sphere under a forged eye."""
    eye(14, 0, 4.0)
    R(12, 8, 16, 9, IRON)                                   # boss
    R(12, 8, 16, 8, IRON_L)
    ball(14.5, 21.5, 13.2, IRON_RAMP, 0.62)
    for a in range(0, 360, 40):                             # a band of rivets
        r = a * math.pi / 180
        x = 14.5 + math.cos(r) * 13.0 * 0.95
        y = 21.5 + math.sin(r) * 3.0
        P(int(x), int(y), IRON_XL if x < 14 else IRON_M)
    for x in range(2, 28):
        y = int(21.5 + 3.4 * math.sqrt(max(0, 1 - ((x - 14.5) / 13.2) ** 2)))
        if AT(x, y) != KEY:
            P(x, y, IRON_D)
    grime(1, 9, 28, 34, 50, (RUST, RUST_D, IRON_D), on=IRON_RAMP)


def lift_deck():
    """S13's lift deck: planks on two iron stringers, an eye at each end for the ropes."""
    for cx in (3, 65):
        eye(cx, 0, 2.5)
        R(cx - 1, 5, cx + 1, 5, IRON_M)
    for x in range(0, 69):                                  # planks
        seam = x % 9 == 8
        for y in range(6, 9):
            dshade(x, y, 0.85 - 0.25 * (y - 6), TIM_RAMP)
        if seam:
            R(x, 6, x, 8, TIM_D)
    R(0, 9, 68, 9, IRON_D)                                  # stringer
    for x in (2, 3, 4, 64, 65, 66, 34):                     # straps
        R(x, 6, x, 9, IRON if x != 34 else IRON_M)
    for x in (12, 25, 43, 56):
        P(x, 7, TIM_D)
    grime(0, 6, 68, 9, 30, (TIM_D, RUST_D), on=TIM_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  LOOSE
# ═══════════════════════════════════════════════════════════════════════════
def _log(w, h):
    log_h(0, 0, w - 1, h - 1)
    for x in (0, w - 1):                                    # end grain rings
        for y in range(1, h - 1):
            P(x, y, TIM_M if y % 2 else TIM_L)
    P(w // 3, 1, TIM_D)                                     # a knot or two
    P(w // 3 + 1, 1, TIM_D)
    P(2 * w // 3, h - 3, TIM_D)


def log_long():
    """S05's sawlog, 88 long - the stock the sawpit cuts, and a roller when it gets loose."""
    _log(88, 10)


def log_short():
    _log(44, 9)


def log_end():
    """A log seen end-on (S23's chute is full of them): rings, a crack, bark round it.
    A disc, so it rolls."""
    cx = cy = 5.5
    for y in range(12):
        for x in range(12):
            d = math.hypot(x - cx, y - cy)
            if d <= 5.8:
                if d > 4.6:
                    dshade(x, y, 0.4 - 0.3 * (x + y - 11) / 11, (TIM_D, TIM))
                else:
                    ring_ = int(d) % 2
                    P(x, y, (128, 104, 72) if ring_ else (148, 124, 88))
    P(5, 5, TIM_D)
    LN(6, 6, 9, 8, TIM_D)


def coal_sack():
    """S11's coal sack: tied at the neck, slumped, coal showing at the tear. It burns."""
    tpl(0, 0, [
        "....aab.....",
        "....bbd.....",
        ".....rR.....",
        "...abbbbd...",
        "..abbbbbbd..",
        ".abbabbbbbd.",
        ".abbbbbbbbd.",
        "abbbbbbcCbbd",
        "abbbbbcCcbbd",
        "abbbbbbbbbdd",
        "abbbbbbbbbdd",
        ".bbbbbbbbdd.",
        "..ddddddddd.",
    ], {'a': SACK_L, 'b': SACK, 'd': SACK_D, 'r': TIM_L, 'R': TIM_M, 'c': COAL, 'C': COAL_D})
    grime(0, 3, 11, 12, 14, (SACK_D, COAL), on=(SACK,))


def crate():
    """A plank crate with a cross brace, the kind every room has one or two of."""
    for y in range(0, 13):
        for x in range(0, 13):
            dshade(x, y, 0.75 - 0.35 * (x + y) / 24, TIM_RAMP)
    for y in (3, 7, 11):
        R(1, y, 11, y, TIM_D)
    box(0, 0, 12, 12, TIM_D, TIM, TIM_L)
    LN(1, 11, 11, 1, TIM_M)
    LN(1, 12, 12, 1, TIM_D)
    for x, y in ((1, 1), (11, 1), (1, 11), (11, 11)):
        P(x, y, IRON_M)


def _drum(body):
    for y in range(0, 14):
        for x in range(0, 11):
            dshade(x, y, 0.85 - 0.7 * x / 10, body)
    R(0, 0, 10, 0, body[-1])
    for y in (0, 4, 9, 13):                                 # rolling hoops
        R(0, y, 10, y, body[0] if y in (4, 9) else body[1])
    P(7, 1, IRON_D)                                         # bung
    grime(0, 0, 10, 13, 14, (RUST_D, RUST), on=body)


def oil_drum():
    """S12/S20's drum, rusted out. Rolls, stacks, and the magnet takes it."""
    _drum(RUST_RAMP)


def oil_drum_green():
    _drum((OLIVE_D, OLIVE, OLIVE_L))


def ore_tub():
    """The ore tub the rooms park on their rails (S02, S21): an open U on its wheels."""
    for y in range(0, 13):
        for x in (0, 1, 2):
            dshade(x, y, 0.85 - 0.03 * y, IRON_RAMP)
        for x in (25, 26, 27):
            dshade(x, y, 0.42 - 0.02 * y, IRON_RAMP)
    for y in (11, 12, 13):
        for x in range(0, 28):
            dshade(x, y, 0.55 - 0.012 * x - 0.1 * (y - 11), IRON_RAMP)
    R(0, 0, 2, 0, IRON_XL)
    R(25, 0, 27, 0, IRON_L)
    for y in (4, 8):
        P(1, y, IRON_L)
        P(26, y, IRON_M)
    R(3, 14, 24, 14, IRON_D)                                # chassis
    for wx in (6, 21):                                      # wheels, fused to the axle boxes
        ball(wx, 16, 2.8, IRON_RAMP, 0.4)
        P(wx, 16, IRON_L)
    grime(0, 0, 27, 14, 30, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def skull():
    tpl(0, 0, [
        ".bBb.",
        "bBBBd",
        "BoBod",
        "bBBBd",
        ".dbd.",
    ], {'b': BONE_L, 'B': BONE, 'd': BONE_D, 'o': INK})


def long_bone():
    tpl(0, 0, [
        "bB......Bb",
        "BBBBBBBBBd",
        "Bd......dd",
    ], {'b': BONE_L, 'B': BONE, 'd': BONE_D})


def stake():
    """A sharpened stake with an iron tip (S07, S24, S39)."""
    R(1, 0, 1, 2, IRON_L)
    P(2, 1, IRON_M)
    R(1, 3, 2, 3, IRON)
    log_v(0, 4, 2, 15)


def _boulder(r):
    c = r + 0.5
    for y in range(int(2 * r) + 2):
        for x in range(int(2 * r) + 2):
            a = math.atan2(y - c, x - c)
            rr = r * (1 + 0.05 * math.sin(a * 3 + 0.7) + 0.04 * math.sin(a * 7))
            d = math.hypot(x - c, y - c)
            if d <= rr:
                t = 0.62 - 0.4 * ((x - c) + (y - c)) / (2 * r) - 0.2 * d / r
                dshade(x, y, t, STONE_RAMP)
    for _ in range(int(r)):                                 # cracks and lichen
        x, y = int(c + (rnd() - 0.5) * r * 1.2), int(c + (rnd() - 0.5) * r * 1.2)
        if AT(x, y) != KEY:
            P(x, y, pick((STONE_D, (88, 98, 80), STONE_D)))
    grime(0, 0, int(2 * r) + 1, int(2 * r) + 1, int(r * 2), (STONE_D, STONE_M), on=STONE_RAMP)


def boulder_big():
    """S17's boulder: the one that rolls the bowl. A body, so it can roll at all."""
    _boulder(17)


def boulder_mid():
    _boulder(11.5)


def boulder_small():
    _boulder(8.5)


GROUPS = [
    ("HUNG", [
        ("Bell", "BELL", bell, (57, 68), METAL, None),
        ("HangingCage", "CAGE", hanging_cage, (21, 30), METAL, None),
        ("Gibbet", "GIBBET", gibbet, (16, 28), METAL, None),
        ("HoistBucket", "HOIST BUCKET", hoist_bucket, (19, 16), METAL, None),
        ("Counterweight", "COUNTERWEIGHT", counterweight, (25, 47), METAL, None),
        ("CandleCrown", "CANDLE CROWN", candle_crown, (25, 12), METAL, None),
        ("Censer", "CENSER", censer, (8, 12), METAL, None),
        ("WreckingBall", "WRECKING BALL", wrecking_ball, (30, 36), METAL, None),
        ("LiftDeck", "LIFT DECK", lift_deck, (69, 11), WOOD, None),
        ("Lantern", "LANTERN", lantern, (7, 12), METAL, None),
    ]),
    ("LOOSE", [
        ("LogLong", "LOG", log_long, (88, 10), WOOD, None),
        ("LogShort", "SHORT LOG", log_short, (44, 9), WOOD, None),
        ("LogEnd", "LOG END-ON", log_end, (12, 12), WOOD, None),
        ("CoalSack", "COAL SACK", coal_sack, (12, 13), WOOD, None),
        ("Crate", "CRATE", crate, (13, 13), WOOD, None),
        ("OilDrum", "DRUM", oil_drum, (11, 14), METAL, None),
        ("OilDrumGreen", "DRUM", oil_drum_green, (11, 14), METAL, None),
        ("OreTub", "ORE TUB", ore_tub, (28, 19), METAL, None),
        ("Skull", "SKULL", skull, (5, 5), DEFAULT, None),
        ("LongBone", "BONE", long_bone, (10, 3), DEFAULT, None),
        ("Stake", "STAKE", stake, (3, 16), WOOD, None),
        ("BoulderBig", "BOULDER", boulder_big, (36, 36), DEFAULT, None),
        ("BoulderMid", "BOULDER", boulder_mid, (25, 25), DEFAULT, None),
        ("BoulderSmall", "BOULDER", boulder_small, (19, 19), DEFAULT, None),
    ]),
]

# where each hung prop's rope ties on: the middle of its eye, pixels from the top-left
ANCHORS = {
    "Bell": {"Eye": (28, 3.5)},
    "HangingCage": {"Eye": (10, 2.5)},
    "Gibbet": {"Eye": (8, 2.5)},
    "HoistBucket": {"Eye": (9.5, 0.5)},
    "Counterweight": {"Eye": (12.5, 3.5)},
    "CandleCrown": {"Eye": (12.5, 2.5)},
    "Censer": {"Eye": (4, 2)},
    "Lantern": {"Eye": (3.5, 1)},
    "WreckingBall": {"Eye": (14.5, 4)},
    "LiftDeck": {"EyeL": (3.5, 2.5), "EyeR": (65.5, 2.5)},
}

# what gives light, and from where (pixels from the top-left) - see roomprops.py
LIGHTS = {
    "Lantern": dict(at=(3.5, 8.5), color=(1.0, 0.72, 0.42), intensity=1.6, radius=7.5, flicker=0.08),
    "CandleCrown": dict(at=(12.5, 3), color=(1.0, 0.78, 0.5), intensity=0.9, radius=6.0, flicker=0.15),
    "Censer": dict(at=(4, 7), color=(1.0, 0.45, 0.2), intensity=0.5, radius=3.0, flicker=0.2),
}
