"""Room props, part 6: clutter - what a lived-in room is full of. Bottles, jugs, pots and
mugs for the tables and shelves, books on end, and what hangs on the wall: a picture, the
tools, a pan, herbs drying.

Every one of them is Props.Decor (extra "decor", or "wall" for what hangs on the back wall):
asleep, a static body the player and the enemies walk straight through; a round, a blast,
fire or something falling on it wakes it into an ordinary loose prop. So a room can be
filled with this without filling it up. See Scripts/Props/Decor.cs.

Built by `roomprops.py`; read its docstring for what the entries mean.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402,F401

TITLE = "CLUTTER"
SEED = 9900

GLASS_D, GLASS, GLASS_L = (30, 46, 36), (48, 72, 54), (92, 124, 96)
AMBER_D, AMBER, AMBER_L = (66, 44, 28), (96, 64, 36), (146, 106, 64)
CLAY_D, CLAY, CLAY_L = (80, 48, 36), (118, 72, 50), (154, 100, 70)
PAPER_D, PAPER = (120, 112, 90), (168, 158, 130)
HERB_D, HERB, HERB_L = (52, 64, 38), (76, 92, 50), (104, 118, 64)
MEAT_D, MEAT, MEAT_L = (86, 42, 38), (118, 60, 50), (148, 86, 66)
WAX_C, WAX_L = (186, 170, 130), (222, 210, 170)
CANVAS_D, CANVAS = (34, 38, 36), (52, 58, 52)
BOOK_SPINES = ((86, 40, 38), (44, 58, 70), (70, 76, 44), (92, 70, 40), (58, 44, 66))

CLAY_RAMP = (CLAY_D, CLAY, CLAY_L)
GLASS_RAMP = (GLASS_D, GLASS, GLASS_L)
AMBER_RAMP = (AMBER_D, AMBER, AMBER_L)


def vessel(profile, ramp, top=0, lit=0.75):
    """A turned shape - bottle, jug, jar - from its half-widths, row by row from the top,
    lit from the left."""
    cx = max(profile)
    for j, hw in enumerate(profile):
        for x in range(cx - hw, cx + hw + (1 if hw else 1)):
            t = lit - 0.6 * (x - (cx - hw)) / max(1, 2 * hw)
            dshade(x, top + j, t, ramp)


# ═══════════════════════════════════════════════════════════════════════════
#  ON TABLES AND SHELVES
# ═══════════════════════════════════════════════════════════════════════════
def bottle():
    """A green glass bottle, corked."""
    vessel([0, 0, 0, 1, 1, 2, 2, 2, 2, 2], GLASS_RAMP, top=0)
    P(2, 0, RUST_L)
    P(1, 5, GLASS_L)
    P(1, 6, GLASS_L)


def bottle_brown():
    """A squat brown bottle."""
    vessel([0, 0, 1, 2, 2, 2, 2, 2], AMBER_RAMP, top=0)
    P(2, 0, TIM_M)
    P(1, 4, AMBER_L)


def jug():
    """A clay jug with its handle out to the east."""
    vessel([1, 1, 2, 3, 3, 3, 2, 2], CLAY_RAMP, top=0)
    R(1, 0, 5, 0, CLAY_L)
    P(7, 2, CLAY_D)
    P(7, 3, CLAY_D)
    P(7, 4, CLAY_D)
    P(6, 5, CLAY_D)


def jar():
    """A lidded clay jar."""
    R(1, 0, 4, 0, TIM_M)
    R(0, 1, 5, 1, TIM_D)
    vessel([2, 3, 3, 3, 2], CLAY_RAMP, top=2)


def mug():
    """A tin mug."""
    for y in range(0, 4):
        for x in range(0, 4):
            dshade(x, y, 0.8 - 0.2 * x, IRON_RAMP)
    P(4, 1, IRON_D)
    P(4, 2, IRON_D)
    R(0, 0, 3, 0, IRON_L)


def plate():
    """A pewter plate, on its edge against the wall."""
    for y in range(0, 7):
        for x in range(0, 3):
            d = abs(y - 3)
            if d <= 3 - (1 if x == 0 or x == 2 else 0) or (x == 1):
                dshade(x, y, 0.85 - 0.15 * x - 0.05 * y, IRON_RAMP)


def pot():
    """An iron cooking pot with two lugs."""
    R(1, 0, 7, 0, IRON_L)
    for y in range(1, 6):
        for x in range(1, 8):
            dshade(x, y, 0.65 - 0.06 * x - 0.05 * y, IRON_RAMP)
    R(2, 6, 6, 6, IRON_D)
    P(0, 1, IRON_D)
    P(8, 1, IRON_D)


def kettle():
    """A black kettle, spout to the east."""
    R(2, 0, 4, 0, IRON_M)
    R(1, 1, 5, 1, IRON_D)
    for y in range(2, 7):
        for x in range(0, 7):
            dshade(x, y, 0.55 - 0.05 * x, IRON_RAMP)
    P(7, 3, IRON)
    P(8, 2, IRON)


def candlestick():
    """A candle in an iron holder, lit: its flame is a Lighting.LightSource2D."""
    P(1, 0, F_HOT)
    P(1, 1, F_MID)
    R(1, 2, 1, 6, WAX_C)
    P(1, 2, WAX_L)
    R(0, 7, 2, 7, IRON_M)
    R(0, 8, 2, 8, IRON_D)


def bucket():
    """A wooden bucket, iron hooped."""
    R(0, 0, 7, 0, TIM_L)
    for y in range(1, 8):
        inset = 0 if y < 4 else 1 if y < 7 else 1
        for x in range(inset, 8 - inset):
            dshade(x, y, 0.8 - 0.07 * x, TIM_RAMP)
    R(0, 2, 7, 2, IRON_M)
    R(1, 6, 6, 6, IRON_M)


def basket():
    """A wicker basket of something."""
    R(1, 0, 8, 0, SACK_L)
    R(0, 1, 9, 1, SACK)
    for y in range(2, 7):
        for x in range(0 + (y == 6), 10 - (y == 6)):
            P(x, y, TIM_M if (x + y) % 2 else TIM)
    R(1, 7, 8, 7, TIM_D)


def book_row():
    """Five books on end, as they stand on a shelf."""
    hs = (8, 7, 8, 6, 7)
    x = 0
    for k, h in enumerate(hs):
        c = BOOK_SPINES[k % len(BOOK_SPINES)]
        lit = tuple(min(255, v + 26) for v in c)
        for y in range(8 - h, 8):
            P(x, y, lit)
            P(x + 1, y, c)
        P(x + 1, 8 - h + 2, (150, 132, 90))                  # a band on the spine
        x += 2


def shelf():
    """A plank shelf on two iron brackets, screwed to the back wall: what the jars and
    books on it stand on. It is clutter too - shoot it and it comes down with them."""
    for x in range(0, 26):
        dshade(x, 0, 0.95, TIM_RAMP)
        dshade(x, 1, 0.4, TIM_RAMP)
    for bx in (3, 21):
        P(bx, 2, IRON_M)
        P(bx + 1, 2, IRON_M)
        P(bx + 1, 3, IRON_D)
        P(bx + 1, 4, IRON_D)


# ═══════════════════════════════════════════════════════════════════════════
#  ON THE WALL
# ═══════════════════════════════════════════════════════════════════════════
def picture():
    """A small framed picture - hills under a dark sky."""
    R(0, 0, 11, 9, TIM_D)
    R(0, 0, 11, 0, TIM_M)
    R(0, 0, 0, 9, TIM_M)
    R(1, 1, 10, 8, CANVAS_D)
    for x in range(1, 11):
        h = 6 - int(2 * abs((x - 4) / 5.0) ** 0.7)
        for y in range(h, 9):
            P(x, y, CANVAS if y > h else OLIVE_D)
    P(8, 3, (150, 140, 110))                                  # a moon


def pickaxe():
    """A pick hung head-up on a nail."""
    R(1, 0, 9, 0, IRON_M)
    R(0, 1, 10, 1, IRON)
    P(0, 2, IRON_D)
    P(10, 2, IRON_D)
    for y in range(2, 14):
        dshade(5, y, 0.8, TIM_RAMP)
        dshade(6, y, 0.3, TIM_RAMP)


def shovel():
    """A shovel, blade down."""
    for y in range(0, 10):
        dshade(2, y, 0.8, TIM_RAMP)
    R(1, 0, 3, 0, TIM_D)
    for y in range(10, 16):
        for x in range(0, 5):
            if not (y == 15 and x in (0, 4)):
                dshade(x, y, 0.75 - 0.12 * x, IRON_RAMP)


def saw():
    """A hand saw, handle west."""
    R(0, 0, 3, 4, TIM)
    R(0, 0, 3, 0, TIM_M)
    P(1, 2, TIM_D)
    P(2, 2, TIM_D)
    for x in range(4, 18):
        P(x, 1, IRON_L)
        P(x, 2, IRON_M)
        if x < 17:
            P(x, 3, IRON if x % 2 else IRON_D)


def pan():
    """A frying pan on a nail, by its handle."""
    for y in range(0, 6):
        P(4, y, IRON_D)
    for y in range(6, 14):
        for x in range(0, 9):
            d = (x - 4) ** 2 / 20.0 + (y - 10) ** 2 / 16.0
            if d <= 1.0:
                dshade(x, y, 0.6 - 0.05 * x - 0.03 * y, IRON_RAMP)


def herbs():
    """Herbs hung to dry, tied at the stems."""
    R(2, 0, 4, 1, SACK_L)
    for k, x in enumerate((0, 1, 2, 3, 4, 5, 6)):
        top = 2
        length = 6 + (k * 5) % 4
        for y in range(top, top + length):
            P(x, y, (HERB_D, HERB, HERB_L)[(x + y) % 3])
    for x in range(1, 6):
        P(x, 2, HERB_D)


def ham():
    """A ham and a string of sausages off one hook."""
    P(3, 0, IRON_M)
    P(3, 1, SACK_L)
    for y in range(2, 11):
        w = min(3, 1 + (y - 2) // 2)
        for x in range(3 - w, 4 + w):
            dshade(x, y, 0.8 - 0.1 * (x - 3 + w), (MEAT_D, MEAT, MEAT_L))
    R(2, 11, 4, 11, MEAT_D)
    for k in range(3):                                        # sausages down the side
        P(7, 2 + k * 3, MEAT)
        P(7, 3 + k * 3, MEAT_D)
        P(7, 4 + k * 3, SACK)
    P(6, 2, SACK)
    P(5, 2, MEAT)


def notice():
    """A sheet of paper nailed up, written over."""
    R(0, 0, 6, 8, PAPER)
    R(6, 1, 6, 8, PAPER_D)
    R(0, 8, 6, 8, PAPER_D)
    P(3, 0, IRON_D)
    for y in (2, 4, 6):
        for x in range(1, 5 - (y == 6)):
            P(x, y, (70, 64, 52) if (x + y) % 3 else PAPER_D)


GROUPS = [
    ("ON TABLES AND SHELVES", [
        ("Bottle", "BOTTLE", bottle, (5, 10), DEFAULT, "decor"),
        ("BottleBrown", "BOTTLE", bottle_brown, (5, 8), DEFAULT, "decor"),
        ("Jug", "JUG", jug, (8, 8), DEFAULT, "decor"),
        ("Jar", "JAR", jar, (7, 7), DEFAULT, "decor"),
        ("Mug", "MUG", mug, (5, 4), METAL, "decor"),
        ("Plate", "PLATE", plate, (3, 7), METAL, "decor"),
        ("Pot", "POT", pot, (9, 7), METAL, "decor"),
        ("Kettle", "KETTLE", kettle, (9, 7), METAL, "decor"),
        ("Candlestick", "CANDLE", candlestick, (3, 9), METAL, "decor"),
        ("Bucket", "BUCKET", bucket, (8, 8), WOOD, "decor"),
        ("Basket", "BASKET", basket, (10, 8), WOOD, "decor"),
        ("BookRow", "BOOKS", book_row, (10, 8), WOOD, "decor"),
        ("Shelf", "SHELF", shelf, (26, 5), WOOD, "wall"),
    ]),
    ("ON THE WALL", [
        ("Picture", "PICTURE", picture, (12, 10), WOOD, "wall"),
        ("Pickaxe", "PICK", pickaxe, (11, 14), METAL, "wall"),
        ("Shovel", "SHOVEL", shovel, (5, 16), METAL, "wall"),
        ("Saw", "SAW", saw, (18, 5), METAL, "wall"),
        ("Pan", "PAN", pan, (9, 14), METAL, "wall"),
        ("Herbs", "HERBS", herbs, (7, 11), WOOD, "wall"),
        ("Ham", "HAM", ham, (8, 12), WOOD, "wall"),
        ("Notice", "NOTICE", notice, (7, 9), WOOD, "wall"),
    ]),
]

# what gives light, and from where (pixels from the top-left) - see roomprops.py
LIGHTS = {
    "Candlestick": dict(at=(1, 0.5), color=(1.0, 0.8, 0.5), intensity=0.7, radius=4.0, flicker=0.18),
}
