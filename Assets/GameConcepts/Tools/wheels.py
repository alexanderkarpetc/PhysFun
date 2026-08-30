"""Pulley wheel sprites for Props/PulleyWheel2D - drawn from code, three finishes.

    python Assets/GameConcepts/Tools/wheels.py            # all three
    python Assets/GameConcepts/Tools/wheels.py wood       # just one
    python Assets/GameConcepts/Tools/wheels.py --preview  # + an x4 contact sheet

Writes `Assets/Sprites/Props/PulleyWheel_<Kind>.png`, 80x80 native with real alpha,
same footprint and importer settings as `Sprites/Hazards/Gear.png` (point filter,
40 pixels per unit, centre pivot) - so at scale 1 the wheel is a disc of radius ~0.98
world units and a CircleCollider2D of radius 0.975 sits exactly on the drawn rim.

Everything a sprite carries has to survive being spun, which is the one rule this file
follows throughout: the light is radial, not directional, and every feature repeats
around the wheel (5 spokes, 4 straps, 4 holes). A wheel lit from the top-left flickers
as it turns; one lit from its own centre does not. The features are there so the spin
reads at all - a flat disc turning looks like a flat disc standing still.

Sizes in pixels from the centre, shared by all three:

    39      outer edge of the flange (the outline pass eats the last pixel of it)
    33..39  flange face
    29..33  rope groove, the dark band the cable sits in
    11..29  web - spokes, planks or plate, whatever the finish is made of
    5..11   hub boss
    0..5    bore, left transparent so the pin behind it shows through
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "PixelArt", "tools"))
from pixelfix import write_png, upscale  # noqa: E402

S = 80                      # sprite side, native pixels
C = S / 2.0                 # centre, in pixel-corner coordinates
R_OUT = 39.0                # outer edge of the flange
R_GROOVE = 33.0             # flange face ends, groove begins
R_WEB = 29.0                # groove ends, web begins
R_HUB = 11.0                # web ends, hub boss begins
R_BORE = 5.0                # bore for the pin

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "Sprites", "Props")

# ── palettes ────────────────────────────────────────────────────────────────
# Noita's swatches (see PixelArt/NOTES.md): flat fills, hard edges, <= 6 tones a sprite.
PLAIN = dict(ink=(51, 49, 45), dark=(67, 67, 67), mid=(135, 135, 135),
             lit=(187, 187, 187), iron=(99, 99, 99))
WOOD = dict(ink=(55, 48, 40), dark=(81, 72, 54), mid=(149, 134, 101),
            lit=(165, 157, 108), iron=(89, 97, 113), iron_d=(71, 78, 90))
METAL = dict(ink=(53, 62, 70), dark=(71, 78, 90), mid=(110, 126, 141),
             lit=(138, 148, 169), hi=(201, 204, 223))

HOLE = None                 # what a draw function returns for "nothing here"


# ── the three finishes ──────────────────────────────────────────────────────
# Each takes a pixel's polar position and returns a colour, or HOLE for transparent.
# `a` is the angle in radians, `r` the distance from the centre in pixels.

def plain(r, a, p=PLAIN):
    """A plain cast disc: flange, groove, four lightening holes, hub."""
    if r > R_OUT:
        return HOLE
    if r > R_GROOVE:
        return p["lit"] if r < R_GROOVE + 2 else p["mid"]
    if r > R_WEB:
        return p["dark"]                     # the groove the rope runs in
    if r < R_BORE:
        return HOLE
    if r < R_HUB:
        return p["mid"] if r > R_HUB - 3 else p["lit"]

    # four holes through the web, on the diagonals - the only thing that says "turning"
    for k in range(4):
        th = math.pi / 4 + k * math.pi / 2
        dx, dy = r * math.cos(a) - 20 * math.cos(th), r * math.sin(a) - 20 * math.sin(th)
        d = math.hypot(dx, dy)
        if d < 5.5:
            return HOLE
        if d < 7.0:
            return p["dark"]                 # the web thickens around each hole
    return p["mid"]


def wood(r, a, p=WOOD):
    """Laminated timber sheave in an iron tyre, four straps across the face."""
    if r > R_OUT:
        return HOLE
    if r > R_GROOVE:                          # iron tyre shrunk onto the rim
        return p["iron"] if r < R_GROOVE + 2.5 else p["iron_d"]
    if r > R_WEB:
        return p["iron_d"]
    if r < R_BORE:
        return HOLE
    if r < R_HUB:
        return p["iron"] if r > R_HUB - 3 else p["iron_d"]

    x, y = r * math.cos(a), r * math.sin(a)

    # four iron straps bolted across the face, at 45 degrees to the seams
    for k in range(4):
        th = math.pi / 4 + k * math.pi / 2
        along = x * math.cos(th) + y * math.sin(th)
        across = -x * math.sin(th) + y * math.cos(th)
        if along > 0 and abs(across) < 3.0:
            return p["iron"] if across < -1.0 else p["iron_d"]

    # annual rings, struck off-centre so the grain looks grown rather than machined
    ring = math.hypot(x + 7, y - 4) % 9.0
    if ring < 1.8:
        return p["dark"]
    return p["lit"] if ring < 5.0 else p["mid"]


def metal(r, a, p=METAL):
    """Five-spoke steel sheave, riveted flange, holes right through the web."""
    if r > R_OUT:
        return HOLE
    if r > R_GROOVE:
        # rivets around the flange, one per spoke plus one between
        for k in range(10):
            th = k * math.pi / 5
            d = math.hypot(r * math.cos(a) - 36 * math.cos(th),
                           r * math.sin(a) - 36 * math.sin(th))
            if d < 1.8:
                return p["hi"] if d < 1.0 else p["dark"]
        return p["lit"] if r < R_GROOVE + 2 else p["mid"]
    if r > R_WEB:
        return p["dark"]
    if r < R_BORE:
        return HOLE
    if r < R_HUB:
        return p["mid"] if r > R_HUB - 3 else p["lit"]

    # five spokes; between them the web is cut away
    step = 2 * math.pi / 5
    off = (a % step)
    off = off - step if off > step / 2 else off        # signed offset from the spoke
    half = 3.2 + r * 0.06                              # spokes flare towards the rim
    if abs(off) * r > half and R_HUB + 2 < r < R_WEB - 2:
        return HOLE
    if off * r > half - 1.6:
        return p["lit"]                                # leading edge of every spoke
    if off * r < -(half - 1.6):
        return p["dark"]                               # trailing edge
    return p["mid"]


KINDS = {"plain": (plain, PLAIN), "wood": (wood, WOOD), "metal": (metal, METAL)}


# ── rendering ───────────────────────────────────────────────────────────────
def render(draw, palette):
    """Rasterise one wheel, then walk the edges and lay a one-pixel dark outline.

    The outline is done as a pass over the finished image rather than drawn in, so
    the holes through the web get the same edge the silhouette does for free.
    """
    rows = []
    for y in range(S):
        row = []
        for x in range(S):
            dx, dy = x + 0.5 - C, y + 0.5 - C
            c = draw(math.hypot(dx, dy), math.atan2(dy, dx))
            row.append((0, 0, 0, 0) if c is HOLE else c + (255,))
        rows.append(row)

    ink = palette["ink"] + (255,)
    edge = []
    for y in range(S):
        for x in range(S):
            if rows[y][x][3] == 0:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if not (0 <= nx < S and 0 <= ny < S) or rows[ny][nx][3] == 0:
                    edge.append((x, y))
                    break
    for x, y in edge:
        rows[y][x] = ink
    return rows


def build(names=None, preview=False):
    names = names or sorted(KINDS)
    os.makedirs(OUT_DIR, exist_ok=True)
    sheets = []
    for name in names:
        draw, palette = KINDS[name]
        rows = render(draw, palette)
        path = os.path.join(OUT_DIR, "PulleyWheel_%s.png" % name.capitalize())
        write_png(path, rows)
        colours = {p for row in rows for p in row if p[3]}
        print("%-28s %dx%d, %d colours" % (os.path.basename(path), S, S, len(colours)))
        sheets.append(rows)

    if preview:
        pad = 8
        w = len(sheets) * (S + pad) + pad
        sheet = [[(24, 26, 30, 255)] * w for _ in range((S + 2 * pad))]
        for i, rows in enumerate(sheets):
            ox = pad + i * (S + pad)
            for y, row in enumerate(rows):
                for x, p in enumerate(row):
                    if p[3]:
                        sheet[pad + y][ox + x] = p
        out = os.path.join(os.path.dirname(OUT_DIR), "..", "GameConcepts",
                           "PulleyWheels.png")
        write_png(out, upscale(sheet, 4))
        print("preview: %s" % out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    build(args or None, preview="--preview" in sys.argv)
