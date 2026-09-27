"""Room concept 08 - THE FROZEN THROAT (big room).

~3.6 x 3 screens at game scale; replaces the layered Icefall (05) as the ice room.
Nothing here is a storey. The whole sheet is glacier, and the room is what melt and
time have hollowed out of it: one throat winding from the top of the sheet to a grotto
at the bottom, and off it a string of bubbles at every height - joined by slanted
tubes, a crawl, a dead-end slot - so every route between two places is a different
shape from every other one.

The toy is still PhysMaterial.Ice (brittle, shears in slabs, split drawn first), and
here it is used on the throat: a tongue of ice hangs off its neck at the top, and
anything sheared up there falls the whole height of the room, through both bridges.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

ICE_BANDS = ((60, 90, 102), (70, 102, 114), (80, 114, 126))
ICE_AIR = (18, 26, 32)
COLD = (150, 205, 226)
LAMP = (255, 214, 140)


def ice_at(x, y):
    return ICE_BANDS[int((y + 0.18 * x + 7 * math.sin(x * 0.011)) / 9) % 3]


def glacier(bed):
    """Ice over everything down to the bedrock line `bed(x)`, with bubbles in it."""
    cw, ch = canvas_size()
    for x in range(cw):
        b = int(bed(x))
        for y in range(46, b):
            px(x, y, ice_at(x, y))
            if chance(0.007):
                px(x, y, ICE_L)
        for k in range(4):
            px(x, b + k, pick([(58, 60, 58), DIRT, ROCK_L]))


def split(points, c=ICE_XL):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay + 1, bx, by + 1, (40, 60, 70))
        line(ax, ay, bx, by, c)


def jag(x0, y0, x1, y1, n=8, amp=4):
    pts = []
    for i in range(n + 1):
        t = i / n
        o = 0 if i in (0, n) else (rnd() - 0.5) * 2 * amp
        horiz = abs(x1 - x0) >= abs(y1 - y0)
        pts.append((x0 + (x1 - x0) * t + (0 if horiz else o), y0 + (y1 - y0) * t + (o if horiz else 0)))
    return pts


def ice_blob(cx, cy, rx, ry):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                px(x, y, ice_at(x, y))
    for x in range(int(cx - rx), int(cx + rx) + 1):
        dy = ry * math.sqrt(max(0, 1 - ((x - cx) / rx) ** 2))
        px(x, cy + dy, ICE_L)


def tongue(cx, top, rx, ry):
    """The tongue: a lobe of clear ice hanging into the throat off a neck. Clearer and
    lighter than the glacier round it, so it reads as a thing and not as more wall. The
    split across the neck is already drawn - one more round and it goes."""
    clear = ((96, 129, 140), (110, 146, 158), (124, 160, 170))
    for y in range(int(top) - 14, int(top + 24)):
        w = 12 + max(0, y - top) * 0.5
        for x in range(int(cx - w), int(cx + w) + 1):
            px(x, y, clear[int((y + 0.3 * x) / 7) % 3])
    for y in range(int(top + 20), int(top + 24 + ry * 2) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x - cx) / rx) ** 2 + ((y - top - 24 - ry) / ry) ** 2
            if d <= 1:
                px(x, y, ICE_L if d > 0.86 else clear[int((y + 0.3 * x) / 7) % 3])
    for _ in range(30):
        px(cx - rx * 0.6 + rnd() * rx * 1.2, top + 30 + rnd() * ry * 1.6, ICE_XL, 0.7)
    split(jag(cx - 16, top + 12, cx + 16, top + 14, 5, 2))
    icicles(int(cx - rx + 8), int(cx + rx - 8), int(top + 24 + ry * 2 - 3), 14, ICE_L, ICE_XL)
    glow(cx, top + 24 + ry, rx * 1.6, COLD, 0.16)


def ice_bridge(x0, x1, y):
    for x in range(int(x0), int(x1) + 1):
        rect(x, y, x, y + 6, ice_at(x, y))
    rect(x0, y, x1, y, ICE_L)
    split(jag((x0 + x1) / 2, y, (x0 + x1) / 2 + 3, y + 6, 2, 1))
    icicles(int(x0) + 2, int(x1) - 2, int(y) + 7, 8, ICE_L, ICE_XL)


def ice_column(x, y0, y1, w=22):
    for y in range(int(y0), int(y1) + 1):
        t = abs((y - (y0 + y1) / 2) / ((y1 - y0) / 2))
        half = w / 2 * (0.55 + 0.45 * t * t)                 # waisted: thin in the middle
        rect(x - half, y, x + half, y, ice_at(x, y))
        px(x - half, y, ICE_L)
    split(jag(x - 8, (y0 + y1) / 2 - 4, x + 8, (y0 + y1) / 2 + 2, 3, 2))


def crystal(cx, base, h=14, w=6, c=CYAN, dark=(34, 62, 70), lit=ICE_XL):
    for i in range(h):
        t = i / h
        half = max(int(w * (1 - t) / 2), 0)
        rect(cx - half, base - i, cx + half, base - i, dark if i % 5 == 4 else c, 0.55 + 0.45 * (1 - t))
    line(cx, base - h + 1, cx - w // 2, base, lit, 0.7)
    glow(cx, base - h // 2, h * 1.4, c, 0.22)


def frozen_giant(x, y):
    """A machine three times the size of a sentinel, stood in the ice where it stopped.
    Its chest is the cache; the ice in front of it is the lid."""
    body = (74, 82, 86)
    rect(x + 20, y + 30, x + 92, y + 110, body)              # torso
    rect(x + 20, y + 30, x + 92, y + 30, (110, 120, 124))
    rect(x + 34, y + 44, x + 78, y + 80, (44, 50, 54))       # chest hatch
    frame(x + 34, y + 44, x + 78, y + 80, HAZARD)
    rect(x + 40, y + 6, x + 72, y + 30, body)                # head
    rect(x + 46, y + 14, x + 66, y + 20, (30, 34, 38))
    px(x + 60, y + 17, RED_L)
    rect(x + 92, y + 44, x + 132, y + 58, body)              # arm: a cannon
    rect(x + 120, y + 46, x + 140, y + 56, (52, 56, 60))
    rect(x + 28, y + 110, x + 44, y + 170, body)             # legs
    rect(x + 68, y + 110, x + 84, y + 170, body)
    rect(x + 22, y + 164, x + 50, y + 172, (52, 56, 60))
    rect(x + 62, y + 164, x + 90, y + 172, (52, 56, 60))
    for yy in range(int(y), int(y) + 175):                   # glaze it into the ice
        for xx in range(int(x), int(x) + 145):
            if at(xx, yy) != ICE_AIR:
                px(xx, yy, ICE_BANDS[1], 0.42)
    glyph("scrap", x + 56, y + 62)


def frozen_body(x, y):
    rect(x, y, x + 12, y + 3, (99, 104, 101))
    rect(x - 3, y + 1, x, y + 3, DIRT_L)
    line(x + 12, y + 3, x + 18, y + 6, INK)
    rect(x - 5, y - 3, x + 20, y + 9, ICE_BANDS[1], 0.45)


def build():
    new_canvas(1600, 900, seed=11417)
    label_scale(3)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=90)
    glacier(lambda x: 792 - 30 * math.sin(x / 210.0) - 14 * math.sin(x / 61.0))
    for cx, cy, rx, ry in ((560, 150, 40, 28), (1000, 380, 34, 24), (240, 400, 30, 20),
                           (1180, 620, 44, 26), (460, 720, 50, 30)):
        rock_blob(cx, cy, rx, ry)                            # boulders the ice carried in

    m = cave_mask([
        ("tube", [(0, 170), (90, 172)], 22),                              # entry
        ("blob", 190, 160, 120, 66),                                      # entry bubble
        ("tube", [(760, 46), (735, 150), (795, 270), (745, 390), (820, 510), (790, 620)], 52),
        ("blob", 800, 690, 270, 85),                                      # the grotto
        ("blob", 400, 320, 110, 62),                                      # L1
        ("tube", [(260, 200), (330, 280)], 18),
        ("tube", [(500, 300), (700, 250)], 18),                           # L1 -> throat, uphill
        ("blob", 300, 560, 160, 95),                                      # L2, the giant's cave
        ("tube", [(380, 370), (340, 480)], 12),                           # the crawl
        ("tube", [(440, 610), (570, 680)], 20),
        ("blob", 1110, 200, 150, 72),                                     # R1 crystals
        ("tube", [(830, 250), (975, 215)], 20),
        ("blob", 1320, 430, 180, 115),                                    # R2 the cathedral
        ("tube", [(1170, 262), (1250, 340)], 22),
        ("tube", [(860, 470), (1150, 450)], 24),
        ("tube", [(1330, 320), (1350, 150)], 10),                         # dead-end slot
        ("blob", 1450, 690, 120, 68),                                     # R3, exit B
        ("tube", [(1370, 530), (1440, 630)], 20),
        ("tube", [(1060, 700), (1340, 700)], 20),
        ("tube", [(1540, 716), (1600, 716)], 20),
        ("tube", [(1250, 175), (1600, 130)], 22),                         # exit A
        ("blob", 600, 470, 40, 30),                                       # ghast roost
        ("tube", [(640, 470), (760, 450)], 12),
    ])
    carve_mask(m, air=ICE_AIR, lip=(40, 56, 66), floor_lit=ICE_L, floor_c=ICE, ceil=(48, 74, 86))

    # ── light: cold everywhere, a lamp where people were ────────────────────
    for cx, cy, r in ((760, 300, 220), (800, 690, 260), (1320, 430, 200), (1110, 200, 160),
                      (300, 560, 180), (400, 320, 120)):
        glow(cx, cy, r, COLD, 0.09)
    for lx, ly in ((190, 100), (1450, 632)):
        lamp(lx, ly, drop=6, bulb=LAMP, tint=LAMP, r=100, strength=0.2)

    # ── the throat ──────────────────────────────────────────────────────────
    tongue(770, 96, 44, 50)
    ice_bridge(700, 850, 338)
    ice_bridge(750, 880, 566)
    for y, x0, x1 in ((180, 690, 790), (420, 700, 800)):
        icicles(x0, x1, y, 10, ICE_L, ICE_XL)

    # ── rooms off it ────────────────────────────────────────────────────────
    frozen_giant(20, 440)                                    # in L2's west wall
    for cx, sc in ((1010, 1.0), (1060, 1.6), (1120, 0.8), (1170, 2.0), (1225, 1.1), (1260, 0.7)):
        base = floor_at(m, cx, 180)
        crystal(cx, base, int(22 * sc), int(10 * sc))
        crystal(cx - int(7 * sc), base, int(13 * sc), int(6 * sc))
        crystal(cx + int(8 * sc), base, int(15 * sc), int(6 * sc))
    for cx in (1060, 1150, 1210):                            # and off the roof
        top = ceil_at(m, cx, 180) + 1
        for i in range(int(16)):
            half = max(0, (16 - i) // 4)
            rect(cx - half, top + i, cx + half, top + i, CYAN, 0.8)
        glow(cx, top + 8, 20, CYAN, 0.2)
    for cx in (1240, 1320, 1410):                            # the cathedral's columns
        ice_column(cx, ceil_at(m, cx, 440), floor_at(m, cx, 440))
    for k in range(5):
        x = 1180 + k * 60
        crystal(x, floor_at(m, x, 450), 10, 5, (120, 170, 190))
    frozen_body(1336, 190)
    frozen_body(620, 730)
    frozen_body(930, 752)
    reward_pedestal(800, floor_at(m, 800, 700), "heart", ghost=True)

    # ── characters ──────────────────────────────────────────────────────────
    hazard_slab(4, floor_at(m, 8, 160) - 30, 6, 29)
    ey = floor_at(m, 150, 160)
    hero(150, ey)
    binny_half(176, ey - 60)
    sprite("Ghast", 750, 440, flip=True)
    sprite("Ghast", 590, 452)
    stand("Minespider", 360, floor_at(m, 360, 320))
    stand("Minespider", 440, floor_at(m, 440, 320), flip=True)
    stand("Grenadier", 1120, floor_at(m, 1120, 200), flip=True)
    stand("WizHollowhood", 1280, floor_at(m, 1280, 440), flip=True)
    stand("Sentinel", 1380, floor_at(m, 1380, 440), flip=True)
    stand("Reaper", 900, floor_at(m, 900, 700), flip=True)
    stand("RiotBrute", 1480, floor_at(m, 1480, 690), flip=True)
    exit_door(1584, floor_at(m, 1580, 120), "gun")
    exit_door(1584, floor_at(m, 1580, 700), "skull")

    for x, y, t in ((744, 420, "W1"), (584, 432, "W1"), (354, floor_at(m, 360, 320) - 30, "W1"),
                    (434, floor_at(m, 440, 320) - 30, "W1"), (1114, floor_at(m, 1120, 200) - 36, "W2"),
                    (1274, floor_at(m, 1280, 440) - 36, "W2"), (1374, floor_at(m, 1380, 440) - 38, "W2"),
                    (894, floor_at(m, 900, 700) - 36, "W3"), (1474, floor_at(m, 1480, 690) - 36, "W3")):
        wave_tag(x, y, t, {"W1": PALE_G, "W2": F_MID, "W3": RED_L}[t])

    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(4, 60)
    vignette(0.3)
    btitle_bar("PHYSFUN - ROOM CONCEPT 08:  THE FROZEN THROAT",
               "BIG ROOM / ~3.6 X 3 SCREENS / GAME SCALE")
    bcallout(20, 330, "1 IN FROM THE WEST", 150, ey - 10)
    bcallout(870, 90, "2 THE THROAT: TOP TO BOTTOM, ONE DROP", 770, 300)
    bcallout(330, 60, "3 SHEAR THE TONGUE'S NECK", 760, 112)
    bcallout(520, 400, "4 ICE BRIDGES", 770, 340)
    bcallout(20, 700, "5 FROZEN GIANT: CUT IT OUT", 110, 560)
    bcallout(1340, 56, "6 CRYSTAL CAVE", 1110, 190)
    bcallout(1040, 580, "7 COLUMNS HOLD THE ROOF", 1320, 470)
    bcallout(20, 400, "8 A CRAWL, NOT A DOOR", 360, 420)
    bcallout(1100, 768, "9 PEDESTAL ON CLEAR", 800, 740)
    blegend(20, 822, [
        ("BEATS", CYAN),
        ("NO STOREYS: A THROAT, AND BUBBLES OFF IT", (170, 180, 195)),
        ("W1 IN THE AIR  W2 IN THE SIDE CAVES  W3 AT THE BOTTOM", F_MID),
    ], 700)
    glyph_key(1180, 796)
    return save(out_path("RoomConcept_FrozenThroat.png"), scale=2)


if __name__ == "__main__":
    build()
