"""Room concept 02 - THE DRYING LOFT.

One room, drawn at game scale. The toy is fire, and the room is its fuel:
three timber lofts stacked up the west half, stock drying on every one of them, and
a slab of roof in the east half that has already parted from the rock and is standing
on four stulls. Fire climbs, so whatever burns low takes the floors above it with it.

The enemies are placed to start the clock rather than wait for the player to: gapers
on the floor and the top loft, which you can deal with at leisure; pyros, who light
the lofts whether you want them lit or not; a reaper in the propped chamber, under the
slab. The two ways out pull against each other: exit A is off the top loft, so it goes
when the lofts go, and exit B is plugged with ice, so it only opens once something hot
has been near it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from roomkit import *  # noqa: F403,E402

FLOOR = 344
L1, L2, L3 = 276, 206, 130
SLAB = 230                              # underside of the propped roof
BARK = (92, 70, 48)
SACK = (70, 64, 54)
SMOKE = (70, 66, 64)


# ── local props ─────────────────────────────────────────────────────────────
def deck(x0, x1, y, holes=()):
    """Plank floor, 3px, with the gaps a ladder comes up through."""
    for x in range(int(x0), int(x1) + 1):
        if any(a <= x <= b for a, b in holes):
            continue
        rect(x, y, x, y + 3, WOOD if (x // 11) % 2 else WOOD_L if x % 11 == 0 else WOOD)
        px(x, y, WOOD_L)
        px(x, y + 3, WOOD_D)


def post(x, y0, y1, charred=False):
    beam(x, y0, y1, 3, CHAR if charred else WOOD, (60, 50, 44) if charred else WOOD_L)


def lumber(x, floor, w, rows, c=WOOD, lit=WOOD_L):
    """Stacked boards on stickers - the stock that is drying, i.e. the fuel."""
    y = floor - 1
    for r in range(rows):
        rect(x, y - 2, x + w, y - 1, c)
        rect(x, y - 2, x + w, y - 2, lit)
        for sx in range(int(x) + 3, int(x + w), 14):
            px(sx, y, WOOD_D)
        y -= 3


def coal_sack(x, floor):
    rect(x + 1, floor - 9, x + 10, floor - 1, SACK)
    rect(x, floor - 6, x + 11, floor - 2, SACK)
    rect(x + 3, floor - 11, x + 8, floor - 10, (52, 48, 42))
    rect(x + 1, floor - 9, x + 10, floor - 9, (98, 90, 76))
    px(x + 5, floor - 12, (52, 48, 42))


def keg(x, floor):
    rect(x, floor - 11, x + 8, floor - 1, WOOD)
    rect(x + 1, floor - 12, x + 7, floor - 12, WOOD_L)
    rect(x, floor - 9, x + 8, floor - 9, MET_D)
    rect(x, floor - 3, x + 8, floor - 3, MET_D)
    px(x + 4, floor - 6, INK)


def fuse(points, lit_at=None):
    """FuseCord: dotted line along its run, spark where it is burning."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)))
        for i in range(n + 1):
            if i % 3 == 2:
                continue
            px(ax + (bx - ax) * i / max(n, 1), ay + (by - ay) * i / max(n, 1), (150, 120, 70))
    if lit_at:
        disc(lit_at[0], lit_at[1], 1.5, F_HOT)
        sparks(lit_at[0], lit_at[1], 10, 8)
        glow(lit_at[0], lit_at[1], 10, F_MID, 0.4)


def brazier(cx, floor):
    rect(cx - 1, floor - 8, cx + 1, floor - 1, MET_D)
    rect(cx - 5, floor - 12, cx + 5, floor - 9, MET)
    rect(cx - 5, floor - 12, cx + 5, floor - 12, MET_L)
    fire_patch(cx - 4, floor - 18, cx + 4, floor - 12, 10, 1.2)
    glow(cx, floor - 14, 26, F_MID, 0.3)


def pulley(cx, cy, r=5):
    rect(cx - 1, cy - 12, cx + 1, cy - r, MET_D)
    disc(cx, cy, r, MET)
    ring(cx, cy, r, MET_L)
    disc(cx, cy, 1.4, MET_D)


def winch(cx, floor):
    """Winch2D: drum on an A-frame, crank on the side. Unwind it, or cut the rope."""
    line(cx - 10, floor - 1, cx - 2, floor - 18, WOOD_D)
    line(cx + 10, floor - 1, cx + 2, floor - 18, WOOD_D)
    line(cx - 9, floor - 1, cx - 1, floor - 18, WOOD)
    line(cx + 9, floor - 1, cx + 1, floor - 18, WOOD)
    disc(cx, floor - 18, 6, WOOD)
    ring(cx, floor - 18, 6, WOOD_L)
    for k in range(3):
        ring(cx, floor - 18, 5 - k, (150, 130, 96) if k % 2 == 0 else WOOD_D)
    line(cx, floor - 18, cx + 7, floor - 25, MET_L)
    rect(cx + 7, floor - 26, cx + 9, floor - 25, WOOD_L)


def rope(points, c=(150, 130, 96)):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        line(ax, ay, bx, by, c)


def log_bundle(cx, top):
    """Four logs in two chain slings, hung off one hook. The biggest thing in the room
    that falls through three floors."""
    rect(cx - 1, top - 4, cx + 1, top, MET_L)
    line(cx, top, cx - 28, top + 8, MET_L)
    line(cx, top, cx + 28, top + 8, MET_L)
    logs = [(cx - 36, top + 8), (cx - 34, top + 16), (cx - 38, top + 24), (cx - 32, top + 32)]
    for lx, ly in logs:
        rect(lx, ly, lx + 70, ly + 6, BARK)
        rect(lx, ly, lx + 70, ly, WOOD_L)
        rect(lx, ly + 6, lx + 70, ly + 6, WOOD_D)
        rect(lx + 70, ly, lx + 71, ly + 6, (190, 160, 110))           # sawn end
        px(lx + 71, ly + 3, WOOD_D)
        for _ in range(8):
            px(lx + rnd() * 68, ly + 1 + rnd() * 5, WOOD_D)
    for bx in (cx - 24, cx + 22):
        for y in range(top + 8, top + 39, 2):
            px(bx, y, MET_L)
            px(bx + 1, y + 1, MET_D)


def stull(x, y0, y1, burning=False):
    """Timber standing under the slab, head board and foot block. TerrainSupport
    counts these; take enough away and the slab is terrain on the floor."""
    beam(x, y0 + 2, y1 - 2, 4, CHAR if burning else WOOD, (70, 50, 40) if burning else WOOD_L)
    rect(x - 4, y0, x + 8, y0 + 2, WOOD_L)
    rect(x - 2, y1 - 2, x + 6, y1 - 1, WOOD_D)
    if burning:
        fire_patch(x - 3, y0 + 30, x + 7, y0 + 70, 18, 1.4)
        embers(x - 8, y0 + 10, x + 12, y0 + 60, 30)
        glow(x + 2, y0 + 50, 30, F_MID, 0.3)


def slab_crack(x0, x1, y):
    """The seam where the slab has already let go of the roof. Without it the slab is
    just more ceiling - with it, it is a weight."""
    yy = y
    for x in range(int(x0), int(x1) + 1):
        if chance(0.3):
            yy += pick([-1, 1])
            yy = max(y - 3, min(y + 3, yy))
        rect(x, yy, x, yy + 1, CAVE)
        px(x, yy + 2, ROCK_L, 0.6)
    for _ in range(18):
        cx = x0 + rnd() * (x1 - x0)
        line(cx, y + 3, cx + (rnd() - 0.5) * 8, y + 10 + rnd() * 14, ROCK_D, 0.9)


def plank_wall(x, y0, y1):
    """Boarded-up partition. Wood, so it is a door you open with fire."""
    for k in range(3):
        rect(x + k * 3, y0, x + k * 3 + 2, y1, WOOD if k % 2 else WOOD_D)
        px(x + k * 3 + 1, y0 + 6, MET_L)
        px(x + k * 3 + 1, y1 - 6, MET_L)
    rect(x - 1, y0 + 12, x + 9, y0 + 14, WOOD_L)
    rect(x - 1, y1 - 16, x + 9, y1 - 14, WOOD_L)


def flame_jet(x0, y0, x1, y1, n=60):
    """Pyro's spray: a widening cone of flame particles."""
    for _ in range(n):
        t = rnd()
        spread = 2 + t * 10
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + (rnd() - 0.5) * spread
        disc(x, y, 0.8 + t * 1.6, F_HOT if t < 0.3 else pick([F_MID, F_HOT, F_COOL]), 0.85)
    glow((x0 + x1) / 2, (y0 + y1) / 2, 30, F_MID, 0.25)


def saw_bench(x, floor):
    """Bench saw: a trestle table with the blade proud of the top. Still spinning."""
    rect(x, floor - 16, x + 44, floor - 13, WOOD)
    rect(x, floor - 16, x + 44, floor - 16, WOOD_L)
    for lx in (x + 3, x + 39):
        line(lx, floor - 13, lx - 3, floor - 1, WOOD_D)
        line(lx, floor - 13, lx + 3, floor - 1, WOOD_D)
    gear(x + 22, floor - 17, 7, teeth=12, c=MET_L, lit=MET_XL, hub=MET_D)
    rect(x + 12, floor - 13, x + 32, floor - 13, WOOD_D)
    for _ in range(14):
        px(x + 26 + rnd() * 18, floor - 1 - rnd() * 3, (190, 160, 110), 0.8)


def smoke(x0, y0, x1, y1, n=90):
    for _ in range(n):
        disc(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0), 2 + rnd() * 5, SMOKE, 0.14)


def build():
    new_canvas(800, 450, seed=7121)
    rock_mass(0, soil=ROCK, soil_lit=ROCK_M, strata=40)

    carve_all([
        (60, 74, 540, FLOOR),          # the tall half: lofts and the winch
        (540, 74, 740, 150),           # roof void above the slab (the gap it left)
        (540, SLAB, 740, FLOOR),       # propped chamber under the slab
        (22, 94, 64, L3),              # exit A alcove, level with the top loft
        (736, 288, 780, FLOOR),        # exit B alcove, behind the ice
        (16, 288, 60, FLOOR),          # cache behind the plank wall
        (384, FLOOR, 414, 380),        # the floor hatch you arrive through
    ], rough=3)
    rock_teeth(70, 540, 76, 34)
    rock_teeth(24, 62, 96, 4)
    slab_crack(540, 740, 152)          # slab = the rock between 152 and SLAB
    rect(540, SLAB - 2, 740, SLAB, ROCK_L, 0.5)

    # ── floors ──────────────────────────────────────────────────────────────
    floor_slab(16, 384, FLOOR, 6, DIRT_D, DIRT)
    floor_slab(414, 780, FLOOR, 6, DIRT_D, DIRT)
    floor_slab(22, 64, L3, 4, DIRT_D, DIRT)
    rubble(60, FLOOR - 2, 540, FLOOR, 90, (DIRT, DIRT_D, WOOD_D))

    # ── the lofts ───────────────────────────────────────────────────────────
    for x in (84, 164, 244, 324, 404):
        post(x, L3 if x <= 244 else L2, FLOOR - 1, charred=(x == 404))
    deck(80, 430, L1, holes=[(292, 306)])
    deck(80, 430, L2, holes=[(104, 118)])
    deck(62, 262, L3, holes=[(214, 228)])
    ladder(298, L1 + 4, FLOOR - 1, w=7, step=7, c=WOOD_L, rail=WOOD_D)
    ladder(110, L2 + 4, L1 - 1, w=7, step=7, c=WOOD_L, rail=WOOD_D)
    ladder(220, L3 + 4, L2 - 1, w=7, step=7, c=WOOD_L, rail=WOOD_D)

    lumber(126, L1, 60, 6)
    lumber(200, L1, 30, 3)
    for k in range(3):
        coal_sack(340 + k * 13, L1)
    coal_sack(346, L1 - 9)
    lumber(250, L2, 56, 5)
    lumber(90, L3, 60, 7)
    lumber(160, L3, 40, 4)
    for k in range(4):
        keg(150 + k * 10, L2)
    keg(155, L2 - 12)
    keg(165, L2 - 12)
    for k in range(4):
        coal_sack(440 + k * 12, FLOOR)
    lumber(430, FLOOR, 30, 4)

    # ── lighting ────────────────────────────────────────────────────────────
    for lx, ly in ((190, L3 + 2), (330, L2 + 4), (620, SLAB + 2)):
        lamp(lx, ly, drop=5, bulb=F_HOT, tint=(255, 214, 140), r=46, strength=0.2)

    # ── 1  in through the floor hatch ───────────────────────────────────────
    ladder(394, FLOOR - 2, 380, w=8, step=7)
    hero(400, FLOOR, face_right=False)
    binny_half(358, FLOOR - 44)

    # ── 3  fuse from the brazier to the keg shelf ───────────────────────────
    brazier(92, FLOOR)
    fuse([(96, FLOOR - 14), (70, FLOOR - 30), (68, L2 + 10), (140, L2 + 6), (150, L2 - 2)],
         lit_at=(69, 300))

    # ── 4  log bundle on the winch ──────────────────────────────────────────
    pulley(478, 88)
    rope([(470, FLOOR - 24), (473, 90)])
    rope([(483, 88), (484, 118)])
    log_bundle(484, 122)
    winch(470, FLOOR)

    # ── 5  the pyros, and the fire they have already started ───────────────
    stand("Pyro", 380, L2, flip=True)
    flame_jet(368, L2 - 10, 300, L2 - 4)
    fire_patch(262, L2 - 16, 310, L2 - 2, 40, 1.6)
    fire_patch(360, L1 - 20, 432, L1 + 2, 50, 1.8)
    fire_patch(400, L2 + 6, 410, L1, 24, 1.4)                      # climbing the post
    embers(250, L2 - 60, 440, L1, 120)
    smoke(250, 80, 540, 150, 120)
    glow(390, L1 - 20, 60, F_MID, 0.22)
    stand("Pyro", 510, FLOOR, flip=True)

    # ── gapers ──────────────────────────────────────────────────────────────
    saw_bench(176, FLOOR)
    stand("Gaper", 260, FLOOR, flip=False)
    stand("Gaper", 196, L3)
    corpse(330, FLOOR, (123, 126, 100))

    # ── 6  the slab on its stulls, the reaper under it ──────────────────────
    for sx, burning in ((556, False), (606, True), (660, False), (704, False)):
        stull(sx, SLAB, FLOOR, burning)
    stand("Reaper", 684, FLOOR, flip=True)

    # ── 7  ice plugging exit B ──────────────────────────────────────────────
    for j in range(5):
        for i in range(2):
            ice_block(716 + i * 10 - (j % 2) * 3, FLOOR - 12 - j * 11, 10, 10)
    icicles(712, 740, SLAB + 1, 6)
    doorway(760, FLOOR)

    # ── 8  a store behind the plank wall ────────────────────────────────────
    plank_wall(56, 290, FLOOR - 1)
    crate(22, FLOOR - 13, 12)
    crate(36, FLOOR - 13, 12)
    crate(28, FLOOR - 24, 10)

    # ── 9  exit A, off the top loft ─────────────────────────────────────────
    doorway(26, L3)


    # ── sheet furniture ─────────────────────────────────────────────────────
    screen_frame(300, 102)
    vignette(0.35)
    btitle_bar("PHYSFUN - ROOM CONCEPT 02:  THE DRYING LOFT",
               "ONE ROOM / GAME SCALE")
    bcallout(430, 396, "1 FROM BELOW", 404, 366)
    bcallout(250, 44, "2 THREE LOFTS, ALL FUEL", 236, 126)
    bcallout(84, 234, "3 FUSE TO THE KEGS", 70, 280)
    bcallout(560, 44, "4 CUT THE ROPE", 484, 104)
    bcallout(300, 232, "5 PYROS START THE CLOCK", 372, 196)
    bcallout(560, 176, "6 FOUR STULLS HOLD THE SLAB", 606, 236)
    bcallout(600, 262, "7 ICE PLUGS EXIT B", 722, 300)
    bcallout(84, 310, "8 BURNS OPEN", 58, 318)
    bcallout(84, 60, "9 EXIT A", 30, 92)
    blegend(22, 378, [
        ("BEATS", CYAN),
        ("EVERY FLOOR IS FUEL AND FIRE CLIMBS", (170, 180, 195)),
        ("GAPERS, PYROS, A REAPER UNDER THE SLAB", F_MID),
        ("FIRE OPENS B AND BURNS THE WAY TO A", GREEN_L),
    ], 342)
    return save(out_path("RoomConcept_DryingLoft.png"), scale=2)


if __name__ == "__main__":
    build()
