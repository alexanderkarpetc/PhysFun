"""Room concept 04 - THE CHASM (big room).

Twice the linear size of rooms 01-02: ~3.6 x 3 screens. The toy is the rope. A cult
has hung its whole temple over a drop: rope bridges between two rock pinnacles, timber
cradles slung from the roof on single rings, a cage lift on a counterweight, a boulder
on a chain, a wrecking ball that nobody stopped. Everything that holds anyone up in
this room is a rope, and every rope can be cut - so the room is fought by cutting
under people rather than shooting at them.

Wave 1 is ghasts, which fly and do not care about any of it - the one wave that makes
you look up. Wave 2 is three wizards, each on a cradle or a pinnacle top, i.e. each
standing on one rope. Wave 3 is the blood mage on the far pinnacle, whose bridge is
the one with a boulder over it. The bottom is where everything cut ends up; it is
also the long way round to exit B, and the only way to the cache in the pinnacle foot.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

CEIL = 64
BOTTOM = 770
ROPE = (150, 130, 96)
ROPE_D = (104, 88, 62)
BONE = (199, 190, 160)
CANDLE = (255, 214, 140)


# ── local props ─────────────────────────────────────────────────────────────
def pinnacle(cx, top, bottom, w_top, w_bot):
    """A rock column standing out of the chasm floor: tapered, rough-sided, lit on
    top and down its west face."""
    edge_l = edge_r = 0
    for y in range(int(top), int(bottom) + 1):
        t = (y - top) / max(bottom - top, 1)
        half = w_top / 2 + (w_bot - w_top) / 2 * t ** 1.6
        edge_l = max(-4, min(4, edge_l + pick([-1, 0, 0, 1])))
        edge_r = max(-4, min(4, edge_r + pick([-1, 0, 0, 1])))
        x0, x1 = int(cx - half + edge_l), int(cx + half + edge_r)
        for x in range(x0, x1 + 1):
            r = rnd()
            px(x, y, ROCK_D if r < 0.13 else ROCK_M if r < 0.2 else ROCK)
        px(x0, y, ROCK_L)
        px(x1, y, ROCK_D)
        if y == int(top):
            rect(x0, y, x1, y, ROCK_L)
            rect(x0, y + 1, x1, y + 1, ROCK_M)
    for _ in range(int((bottom - top) / 14)):                # strata
        y = top + 10 + rnd() * (bottom - top - 12)
        t = (y - top) / max(bottom - top, 1)
        half = w_top / 2 + (w_bot - w_top) / 2 * t ** 1.6
        rect(cx - half + 3, y, cx + half - 3, y, ROCK_D, 0.6)


def catenary(x0, y0, x1, y1, sag, t):
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)


def rope_bridge(x0, y0, x1, y1, sag):
    """BridgeBuilder2D: planks on a sagging rope, seen edge-on. No hand rope - it would
    be a solid line at head height."""
    n = int(abs(x1 - x0) / 7)
    for i in range(n):
        ax, ay = catenary(x0, y0, x1, y1, sag, i / n)
        rect(ax, ay, ax + 5, ay + 2, WOOD if i % 3 else WOOD_L)
        px(ax, ay + 2, WOOD_D)
    for i in range(int(abs(x1 - x0))):
        ax, ay = catenary(x0, y0, x1, y1, sag, i / abs(x1 - x0))
        px(ax, ay + 3, ROPE_D)
    for x, y in ((x0, y0), (x1, y1)):                        # anchor stakes
        rect(x - 1, y - 6, x + 1, y + 2, WOOD_D)


def broken_bridge(x, y, length, lean=0.25):
    """The half of a cut bridge still tied on: planks hanging straight down the rock."""
    for i in range(int(length / 7)):
        t = i * 7
        ax = x - math.sin(lean * (t / length)) * t * 0.4
        rect(ax - 2, y + t, ax, y + t + 5, WOOD if i % 3 else WOOD_L)
        px(ax + 1, y + t + 2, ROPE_D)
    rect(x - 1, y - 6, x + 1, y + 2, WOOD_D)


def rope(points, c=ROPE):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay, bx, by, c)


def anchor(x, y):
    """Ring bolt in the roof - where every rope in the room is tied off."""
    ring(x, y + 3, 2.5, MET_L)
    rect(x, y - 2, x, y, MET_D)


def cradle(x0, x1, y, top):
    """Timber cradle slung on one ring: two ropes up to a ring, one rope to the roof.
    Cut the one rope and the whole platform goes."""
    cx = (x0 + x1) // 2
    ring_y = y - 40
    anchor(cx, top)
    rope([(cx, top + 5), (cx, ring_y)])
    ring(cx, ring_y + 2, 2, MET_L)
    rope([(cx, ring_y + 3), (x0 + 2, y)])
    rope([(cx, ring_y + 3), (x1 - 2, y)])
    rect(x0, y, x1, y + 4, WOOD)
    rect(x0, y, x1, y, WOOD_L)
    rect(x0, y + 4, x1, y + 4, WOOD_D)
    for bx in (x0 + 4, x1 - 6):
        rect(bx, y + 5, bx + 2, y + 8, WOOD_D)


def cage_lift(pulley_x, top, cage_y, weight_y):
    """Cage on a rope over a roof pulley, counterweight on the other side. Cut either
    side and both ends do something."""
    anchor(pulley_x, top)
    disc(pulley_x, top + 12, 7, MET)
    ring(pulley_x, top + 12, 7, MET_L)
    disc(pulley_x, top + 12, 2, MET_D)
    lx, rx = pulley_x - 7, pulley_x + 7
    rope([(lx, top + 12), (lx, cage_y)])
    rope([(rx, top + 12), (rx, weight_y)])
    cx0, cx1 = lx - 13, lx + 13                               # cage
    rect(cx0, cage_y, cx1, cage_y + 2, MET)
    rect(cx0, cage_y + 30, cx1, cage_y + 32, MET)
    for x in range(int(cx0), int(cx1) + 1, 4):
        rect(x, cage_y + 3, x, cage_y + 29, MET_L)
    rect(cx0, cage_y, cx1, cage_y, MET_XL)
    rect(rx - 7, weight_y, rx + 7, weight_y + 22, MET_D)     # counterweight
    rect(rx - 7, weight_y, rx + 7, weight_y, MET_L)
    for k in range(4):
        rect(rx - 6, weight_y + 4 + k * 5, rx + 6, weight_y + 4 + k * 5, MET)


def hung_boulder(x, top, y, r=18):
    anchor(x, top)
    chain(x, top + 5, y - r - 4)
    ring(x, y - r - 2, 2.5, MET_L)
    line(x, y - r - 2, x - r + 2, y - 6, MET_L)
    line(x, y - r - 2, x + r - 2, y - 6, MET_L)
    disc(x, y, r, ROCK_M)
    disc(x - 4, y - 4, r - 7, ROCK_L)
    disc(x + 3, y + 3, r - 6, ROCK_M)
    for _ in range(30):
        a = rnd() * math.tau
        d = rnd() * r
        px(x + math.cos(a) * d, y + math.sin(a) * d, pick([ROCK_D, ROCK]))
    rect(x - r, y - 1, x + r, y, MET_D)                      # the sling band


def wrecking_ball(ax, ay, angle, length, r=15):
    anchor(ax, ay)
    bx, by = ax + math.sin(angle) * length, ay + math.cos(angle) * length
    n = int(length / 3)
    for i in range(n):
        t = i / n
        px(ax + (bx - ax) * t, ay + (by - ay) * t, MET_L if i % 2 else MET_D)
    disc(bx, by, r, MET_D)
    disc(bx - 4, by - 4, r - 6, MET)
    px(bx - 6, by - 7, MET_XL)
    for k in range(1, 9):                                    # swing arc, dotted
        a = angle + k * 0.07
        if k % 2:
            px(ax + math.sin(a) * length, ay + math.cos(a) * length, PALE_G, 0.6)
    return bx, by


def shrine(cx, floor):
    """Cult altar on a pinnacle top: two standing stones, a slab, candles."""
    for sx in (cx - 22, cx + 16):
        rect(sx, floor - 26, sx + 6, floor - 1, STONE)
        rect(sx, floor - 26, sx + 6, floor - 26, STONE_L)
        rect(sx + 6, floor - 26, sx + 6, floor - 1, STONE_D)
    rect(cx - 26, floor - 30, cx + 26, floor - 27, STONE_L)
    for k in range(5):
        x = cx - 12 + k * 6
        rect(x, floor - 5, x + 1, floor - 1, BONE)
        px(x, floor - 7, CANDLE)
        glow(x, floor - 7, 8, CANDLE, 0.35)
    for _ in range(10):
        px(cx - 20 + rnd() * 40, floor - 1, RED, 0.8)


def bones(x0, x1, y, n=40):
    for _ in range(n):
        x = x0 + rnd() * (x1 - x0)
        if chance(0.2):
            rect(x, y - 3, x + 3, y - 1, BONE)                # skull
            px(x + 1, y - 2, INK)
        else:
            line(x, y - 1, x + 3 + rnd() * 5, y - 1 - rnd() * 3, BONE)


def spike_bed(x0, x1, y):
    for x in range(int(x0), int(x1), 5):
        for k in range(6):
            half = (6 - k) // 3
            rect(x + 2 - half, y - k, x + 2 + half, y - k, MET_XL if k > 3 else MET_L)
    rect(x0, y + 1, x1, y + 2, MET_D)


def wreck(x, y):
    """A cage that came down: bent frame lying on its side."""
    rect(x, y - 16, x + 30, y - 15, MET)
    rect(x, y - 2, x + 30, y - 1, MET)
    for k in range(0, 31, 4):
        line(x + k, y - 14, x + k + 3, y - 3, MET_L)


def gibbet(x, top, y):
    """Cult gibbet: a small cage on a chain with what is left in it. Another rope."""
    anchor(x, top)
    chain(x, top + 5, y)
    rect(x - 7, y, x + 7, y + 1, MET)
    rect(x - 7, y + 22, x + 7, y + 23, MET)
    for bx in range(x - 7, x + 8, 3):
        rect(bx, y + 2, bx, y + 21, MET_L)
    rect(x - 2, y + 16, x + 2, y + 18, BONE)
    px(x - 1, y + 17, INK)
    line(x - 4, y + 21, x + 3, y + 19, BONE)


def rubble_plug(x0, y0, x1, y1):
    """Loose rock stopping up a cave mouth - reads as rubble, not wall: blast it."""
    for _ in range(int((x1 - x0) * (y1 - y0) / 6)):
        bx, by = x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)
        rect(bx, by, bx + 1 + rnd() * 4, by + 1 + rnd() * 3, pick([ROCK_M, ROCK_L, ROCK, DIRT]))


def build():
    new_canvas(1600, 900, seed=66613)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)

    carve_all([
        (300, CEIL, 1300, BOTTOM),       # the chasm
        (14, 180, 300, 262),             # entry cave, west cliff
        (230, 262, 272, 560),            # crack down the west cliff
        (40, 560, 300, 700),             # low west cave: the long way round starts
        (300, 690, 1300, BOTTOM),        # (chasm floor, so the caves join it)
        (1300, 170, 1590, 252),          # exit A cave, east cliff, high
        (1300, 610, 1590, 700),          # exit B cave, east cliff, low
        (1300, 690, 1360, BOTTOM - 10),  # ramp up from the chasm floor into B
        (956, 700, 1016, BOTTOM),        # cache in the east pinnacle's foot
    ], rough=3)
    # the walls are not straight: bulges and shelves, and teeth off the roof
    for cx, cy, rx, ry in ((310, 140, 30, 60), (300, 420, 26, 90),
                           (1290, 120, 30, 50), (1296, 420, 30, 120), (1280, 560, 20, 30),
                           (560, 60, 90, 20), (1080, 58, 110, 22)):
        rock_blob(cx, cy, rx, ry)
    rock_teeth(320, 1290, CEIL + 2, 90)
    rock_teeth(20, 296, 182, 20)
    rock_teeth(1304, 1586, 172, 20)
    rock_teeth(44, 296, 562, 18)
    rock_teeth(1304, 1586, 612, 18)

    floor_slab(14, 300, 262, 6)
    floor_slab(40, 300, 700, 6)
    floor_slab(1300, 1590, 252, 6)
    floor_slab(1360, 1590, 700, 6)
    floor_slab(300, 1360, BOTTOM, 6, DIRT_D, DIRT)
    floor_slab(956, 1016, BOTTOM, 6, DIRT_D, DIRT)

    # ── the pinnacles ───────────────────────────────────────────────────────
    pinnacle(610, 330, BOTTOM, 90, 180)
    pinnacle(990, 290, BOTTOM, 96, 200)
    # re-open the cache after the pinnacle filled it, and plug its mouth
    carve(962, 704, 1012, BOTTOM - 1, rough=1)
    floor_slab(962, 1012, BOTTOM, 4, DIRT_D, DIRT)
    rubble_plug(1010, 712, 1030, BOTTOM - 1)

    # ── light ───────────────────────────────────────────────────────────────
    for lx, ly, r in ((100, 186, 100), (220, 186, 80), (140, 566, 100), (1440, 176, 110),
                      (1460, 616, 100)):
        lamp(lx, ly, drop=6, bulb=CANDLE, tint=CANDLE, r=r, strength=0.22)
    for sx, sy in ((304, 250), (560, 324), (660, 324), (940, 284), (1040, 284), (1296, 240),
                   (330, 690), (1270, 690), (720, 760), (880, 760)):
        sconce(sx, sy - 8, 1 if sx < 800 else -1)
    glow(800, 420, 300, (120, 110, 150), 0.06)

    # ── bridges ─────────────────────────────────────────────────────────────
    rope_bridge(300, 262, 566, 330, 34)                     # west cliff -> pinnacle 1
    broken_bridge(656, 330, 150, lean=-0.4)                 # pinnacle 1 -> 2, cut
    broken_bridge(942, 290, 110, lean=0.4)
    rope_bridge(1036, 290, 1300, 252, 30)                   # pinnacle 2 -> exit A

    # ── things on ropes ─────────────────────────────────────────────────────
    cage_lift(440, CEIL, 520, 180)
    wrecking_ball(800, CEIL, -0.12, 330)
    cradle(670, 750, 600, CEIL)
    cradle(1110, 1200, 470, CEIL)
    cradle(340, 410, 420, CEIL)
    hung_boulder(1150, CEIL, 190, 18)
    gibbet(520, CEIL, 170)
    gibbet(1060, CEIL, 120)
    gibbet(1230, CEIL, 520)
    ladder(1330, 700, BOTTOM - 1, w=8, step=7)             # up out of the chasm into B

    # ── the bottom: everything that was cut ─────────────────────────────────
    spike_bed(690, 900, BOTTOM - 1)
    bones(320, 1290, BOTTOM, 120)
    wreck(420, BOTTOM)
    for k in range(8):
        plank(480 + k * 60 + rnd() * 20, BOTTOM - 3 - rnd() * 3,
              500 + k * 60 + rnd() * 20, BOTTOM - 1 - rnd() * 4, 2)
    for _ in range(20):
        px(300 + rnd() * 1000, BOTTOM - 1, RED, 0.7)
    disc(1150, BOTTOM - 16, 16, ROCK_M)                     # a boulder that already came down
    disc(1146, BOTTOM - 20, 9, ROCK_L)

    # ── the long way round ──────────────────────────────────────────────────
    rope([(250, 262), (252, 560)], ROPE)                    # knotted rope down the crack
    for y in range(270, 560, 12):
        rect(250, y, 252, y + 1, ROPE_D)
    for k in range(4):
        crate(60 + k * 14, 687, 12)
    scrap_pile(160, 700, 80, 10)

    # ── characters ──────────────────────────────────────────────────────────
    hazard_slab(14, 262 - 30, 6, 29)
    rect(12, 262 - 33, 22, 262 - 31, MET_D)
    disc(17, 262 - 37, 1.5, RED_L)
    glow(17, 262 - 37, 7, RED_L, 0.4)
    hero(70, 262)
    binny_half(96, 262 - 60)

    sprite("Ghast", 470, 280)                               # W1: they fly
    sprite("Ghast", 820, 180, flip=True)
    sprite("Ghast", 1180, 330, flip=True)
    stand("WizHollowhood", 710, 600, flip=True)             # W2: one per rope
    stand("WizRamskull", 1150, 470, flip=True)
    stand("WizBonecrown", 580, 330)
    shrine(990, 290)
    stand("BloodMage", 1000, 290, flip=True)                # W3
    stand("Gaper", 520, BOTTOM)
    stand("Gaper", 1220, BOTTOM, flip=True)
    stand("Minespider", 180, 700)
    reward_pedestal(640, 330, "gun", ghost=True)
    reward_pedestal(986, BOTTOM, "scrap")

    exit_door(1584, 252, "gear")
    exit_door(1584, 700, "heart")

    for x, y, t in ((474, 262, "W1"), (824, 162, "W1"), (1184, 312, "W1"),
                    (704, 562, "W2"), (1144, 432, "W2"), (572, 292, "W2"),
                    (994, 250, "W3"), (514, BOTTOM - 36, "W1"), (1214, BOTTOM - 36, "W1")):
        wave_tag(x, y, t, {"W1": PALE_G, "W2": F_MID, "W3": RED_L}[t])

    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(14, 120)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 04:  THE CHASM",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(20, 300, "1 IN HIGH, WEST", 24, 250)
    bcallout(460, 96, "2 BRIDGES: CUT ONE, IT HANGS", 420, 300)
    bcallout(20, 120, "3 CAGE LIFT + COUNTERWEIGHT", 432, 540)
    bcallout(1330, 90, "4 BOULDER ON A CHAIN", 1160, 190)
    bcallout(640, 240, "5 NOBODY STOPPED THE BALL", 770, 390)
    bcallout(20, 400, "6 CRADLES: ONE ROPE EACH", 374, 420)
    bcallout(1330, 330, "7 PEDESTAL, ON CLEAR", 640, 300)
    bcallout(1330, 470, "8 WHAT YOU CUT", 1200, BOTTOM - 10)
    bcallout(20, 740, "9 THE LONG WAY ROUND", 250, 600)
    bcallout(1330, 540, "10 RUBBLE: CACHE", 1022, 740)
    blegend(20, 822, [
        ("BEATS", CYAN),
        ("EVERYTHING HANGS, EVERYTHING CUTS: CUT UNDER THEM", (170, 180, 195)),
        ("W1 GHASTS  W2 A WIZARD PER ROPE  W3 BLOOD MAGE", F_MID),
    ], 640)
    glyph_key(1180, 796)
    return save(out_path("RoomConcept_Chasm.png"), scale=2)


if __name__ == "__main__":
    build()
