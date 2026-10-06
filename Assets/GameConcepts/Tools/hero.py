"""Main hero candidates, replacing the borrowed Noita player sprite.

Each candidate is a 20x22 frame at PPU 20, facing right, feet on row 18 - the same
frame as `Characters/Char_*.png`, so it drops into `roomkit.stand()` and the ragdoll
cutter (head / torso / two legs) as-is. Look follows the enemy sprites: muted palette,
dithered shading. What sets the hero apart from the enemies is one colour: enemies glow
red, the hero glows cyan - the telekinesis colour (`tk_beam`).

Two silhouettes were picked from a sheet of sixteen bare shapes - the wide conical
kasa hat and the stage magician (top hat, cape, cane). Each gets four dressings here;
the outline stays, the costume changes.

    python hero.py

writes `Characters/Char_Hero_<Name>.png` (native) and `Characters/HeroConcept.png`
(the labelled sheet, x4).
"""
import os

from conceptkit import *  # noqa: F401,F403
import conceptkit as ck
from pixelfix import write_png

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "Characters"))

GLOW = (121, 201, 213)     # CYAN - the hero's colour, shared by every candidate
GLOW_L = (194, 252, 243)   # ICE_XL - hot core
EDGE = (24, 23, 24)

BASE = {'o': EDGE, 'e': GLOW, 'E': GLOW_L, 'k': (12, 13, 16)}


def pal(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


# The two picked silhouettes, kept as the reference every dressing is checked against.
KASA_SIL = [
    "....................",
    "....................",
    "..........#.........",
    "........#####.......",
    "......#########.....",
    "....#############...",
    "........##e#........",
    "........####........",
    ".......######.......",
    "......########......",
    "......########.#....",
    "......#########.....",
    "......########......",
    ".......######.......",
    ".......######.......",
    "........#..#........",
    "........#..#........",
    "........#..#........",
    ".......##.##........",
]
STAGE_SIL = [
    "....................",
    "....................",
    "........####........",
    "........####........",
    "........####........",
    ".......######.......",
    "........###e........",
    "........####........",
    ".......######.......",
    "......########......",
    ".....##########.....",
    ".....##.####.#.#....",
    ".....#..####...#....",
    "....##..####...#....",
    "....#...####...#....",
    "........#..#...#....",
    "........#..#...#....",
    "........#..#...#....",
    ".......##.##...#....",
]
SIL_PAL = pal(**{'#': (22, 22, 26)})

# ─────────────────────────────────────────────────────────────────────────────
#  KASA HAT - the wanderer under a wide straw cone. The brim hides the face, so
#  the eye glowing in its shadow is the whole expression.
# ─────────────────────────────────────────────────────────────────────────────
STRAW = dict(h=(128, 108, 70), H=(160, 136, 90), d=(78, 62, 42), s=(140, 116, 96),
             t=(124, 104, 70), n=(50, 48, 54), p=(118, 122, 126))

RONIN = [
    "....................",
    "....................",
    "..........H.........",
    "........hHHHH.......",
    "......hhHHHHHHh.....",
    "....hhdddddddhhh....",
    "........kkek........",
    "........ksss........",
    ".......gGGGGs.......",
    "......gGGgGGGg......",
    "......gGGgGGGgs.....",
    "......rrrrrrrrs..p..",
    "......gGGGgGGg...e..",
    ".......gGGgGGg......",
    ".......nnnnnn.......",
    "........nn.nn.......",
    "........nn.nn.......",
    "........nn.nn.......",
    "........tt.tt.......",
]
RONIN_PAL = pal(g=(44, 48, 64), G=(62, 68, 88), r=(120, 52, 44), **STRAW)

VEILED = [
    "....................",
    "....................",
    "..........H.........",
    "........hHHHH.......",
    "......hhHHHHHHh.....",
    "....hhhhhhhhhhhhh...",
    ".....vVvvvvvvvVv....",
    ".....vvvVvvvevvv....",
    ".....vVvvvvVvvvv....",
    ".....v.vgGGGGv.v....",
    "......gGGgGGGg......",
    "......gGGgGGGgss....",
    "......gGGgGGGg..e...",
    "......gGGGgGGg......",
    ".......gGGgGGg......",
    "........nn.nn.......",
    "........nn.nn.......",
    "........nn.nn.......",
    "........tt.tt.......",
]
VEILED_PAL = pal(v=(46, 50, 54), V=(64, 70, 74), g=(70, 78, 70), G=(92, 102, 90), **STRAW)

PILGRIM = [
    "...............e....",
    "..............eEe...",
    "..........H...ese...",
    "........hHHHH..w....",
    "......hhHHHHHHhw....",
    "....hhhhhhhhhhhwh...",
    "........kkek...w....",
    "........kssss..w....",
    ".......cCCCCC..w....",
    "......cCCCCbCc.w....",
    "......cCCCbCCCsw....",
    "......cCCbCCCc.w....",
    "......cCbCCCCc.w....",
    ".......cCCCCCc.w....",
    ".......cCCcCCc.w....",
    "........nn.nn..w....",
    "........nn.nn..w....",
    "........nn.nn..w....",
    "........tt.tt..w....",
]
PILGRIM_PAL = pal(c=(126, 120, 104), C=(160, 154, 136), b=(96, 60, 46), w=(96, 74, 50),
                  **STRAW)

MINO = [
    "....................",
    "....................",
    "..........H.........",
    "........hHHHH.......",
    "......hhHHHHHHh.....",
    "....hhhhhhhhhhhhh...",
    "........kkek........",
    "........kkkk........",
    ".......MmMmMm.......",
    "......mMmMmMm.......",
    "......mMmMmMmMs.....",
    "......mMmMmMmM.e....",
    ".....MmMmMmMmMm.....",
    ".....MmMmMmMmMm.....",
    ".....M.M.m.M.m.M....",
    "........nn.nn.......",
    "........nn.nn.......",
    "........nn.nn.......",
    "........tt.tt.......",
]
MINO_PAL = pal(m=(104, 86, 56), M=(138, 116, 76), **STRAW)

# ─────────────────────────────────────────────────────────────────────────────
#  STAGE MAGE - "mage" taken literally: a conjurer. Top hat, cape, cane; the
#  trick is that nothing he does is a trick.
# ─────────────────────────────────────────────────────────────────────────────
HAT = dict(h=(30, 30, 36), H=(50, 50, 58), S=(170, 150, 132), s=(132, 114, 100),
           w=(190, 186, 176), n=(150, 150, 146), l=(34, 34, 40), b=(22, 22, 24))

SHOWMAN = [
    "....................",
    "....................",
    "........hHHh........",
    "........hHHh........",
    "........rrrr........",
    ".......hhhhhh.......",
    "........SSSe........",
    "........SSSs........",
    ".......cCwrC........",
    "......cCCwwCc.......",
    ".....cCCCwwCCc......",
    ".....cr.CCCCcwnn....",
    ".....cr.CCCC...j....",
    "....cr..CCCC...j....",
    "....c...cCCc...j....",
    "........ll.l...j....",
    "........l..l...j....",
    "........l..l...j....",
    ".......bb.bb...j....",
]
SHOWMAN_PAL = pal(c=(28, 28, 34), C=(44, 44, 54), r=(130, 46, 42), j=(70, 50, 36),
                  **HAT)

RAGGED = [
    "....................",
    "....................",
    ".........hHh........",
    "........hHHHh.......",
    "........hhHHh.......",
    ".......hhhhhh.......",
    "........sSSe........",
    "........sSSs........",
    ".......cCxCCc.......",
    "......cCCxCCc.......",
    ".....cCcCCCCCc......",
    ".....c..CCxCcSj.....",
    ".....c..CCCC...j....",
    "....c...CCxC...j....",
    "....c...cCCc..j.....",
    "........ll.l...j....",
    "........l..l...j....",
    "........l..l...j....",
    ".......bb.bb...j....",
]
RAGGED_PAL = pal(c=(58, 52, 46), C=(82, 74, 64), x=(110, 60, 50), j=(86, 66, 44),
                 **dict(HAT, h=(46, 42, 40), H=(70, 64, 58)))

MASKED = [
    "....................",
    "....................",
    "........hHHh........",
    "........hHHh........",
    "........hHHh........",
    ".......hhhhhh.......",
    "........SwweE.......",
    "........SSSs........",
    "......cc.ww.cc......",
    "......cCCwwCCc......",
    ".....cCCCCCCCc..e...",
    ".....cv.CCCCcwnEe...",
    ".....cv.CCCC...j....",
    "....cv..CCCC...j....",
    "....c...cCCc...j....",
    "........ll.l...j....",
    "........l..l...j....",
    "........l..l...j....",
    ".......bb.bb...j....",
]
MASKED_PAL = pal(c=(36, 40, 50), C=(54, 60, 74), v=(70, 90, 110), j=(30, 30, 36),
                 **HAT)

RINGMASTER = [
    "....................",
    "....................",
    "........hHHh........",
    "........hHHh........",
    "........nnnn........",
    ".......hhhhhh.......",
    "........SSSe........",
    "........SSSs........",
    ".......cCwCC........",
    "......cCnwnCc.......",
    ".....cCCCwCCCc..qq..",
    ".....cC.CnCCcwj.qe..",
    ".....cC.CCCC..j.....",
    "....cC..CnCC........",
    "....c...cCCc........",
    "........ll.l........",
    "........l..l........",
    "........l..l........",
    ".......bb.bb........",
]
RINGMASTER_PAL = pal(c=(80, 34, 34), C=(108, 48, 46), j=(28, 28, 32),
                     q=(196, 190, 176), **dict(HAT, n=(156, 128, 74)))

GROUPS = [
    ("4 KASA HAT", KASA_SIL, [
        ("Ronin", RONIN, RONIN_PAL, "RONIN"),
        ("Veiled", VEILED, VEILED_PAL, "VEIL"),
        ("Pilgrim", PILGRIM, PILGRIM_PAL, "RING STAFF"),
        ("Mino", MINO, MINO_PAL, "STRAW CAPE"),
    ]),
    ("12 STAGE MAGE", STAGE_SIL, [
        ("Showman", SHOWMAN, SHOWMAN_PAL, "SHOWMAN"),
        ("Ragged", RAGGED, RAGGED_PAL, "FALLEN"),
        ("Masked", MASKED, MASKED_PAL, "MASK, ORB"),
        ("Ringmaster", RINGMASTER, RINGMASTER_PAL, "CARDS FLY"),
    ]),
]


def frame20(name, grid):
    """Pad a grid to the 20x22 frame; a row longer than 20 is a drawing mistake."""
    rows = []
    for j, row in enumerate(grid):
        assert len(row) <= 20, "%s row %d: %d cols" % (name, j, len(row))
        rows.append(row.ljust(20, '.'))
    assert len(rows) <= 22, "%s: %d rows" % (name, len(rows))
    return rows + ["." * 20] * (22 - len(rows))


def pixels(name, grid, pal_):
    out = []
    for row in frame20(name, grid):
        r = []
        for ch in row:
            if ch == '.':
                r.append((0, 0, 0, 0))
            elif ch == '#':
                c = pal_[ch]
                r.append((c[0], c[1], c[2], 255))
            else:
                c = pal_[ch]
                r.append((c[0], c[1], c[2], 255))
        out.append(r)
    return shade(out)


def shade(pix):
    """Light from the top left, as on the rest of the cast: lift the top edge of every
    part, sink the bottom edge, and scatter an ordered dither into the lower half so
    fills read as cloth rather than flat plates. Glow and outline pixels are left as
    drawn."""
    h, w = len(pix), len(pix[0])
    keep = {GLOW, GLOW_L, EDGE}

    def solid(i, j):
        return 0 <= i < w and 0 <= j < h and pix[j][i][3] > 0

    def mul(p, f):
        return tuple(max(0, min(255, int(v * f))) for v in p[:3]) + (255,)

    out = [row[:] for row in pix]
    for j in range(h):
        for i in range(w):
            p = pix[j][i]
            if not p[3] or p[:3] in keep:
                continue
            if not solid(i, j - 1):
                out[j][i] = mul(p, 1.14)
            elif not solid(i, j + 1) or not solid(i + 1, j) and j > 8:
                out[j][i] = mul(p, 0.82)
            elif j > 11 and (i + j) % 2 == 0 and (i * 7 + j * 3) % 5 < 2:
                out[j][i] = mul(p, 0.88)
            elif j <= 11 and (i + j) % 4 == 0 and (i * 5 + j) % 3 == 0:
                out[j][i] = mul(p, 1.08)
    return out


def draw(pix, x, y, s=1):
    for j, row in enumerate(pix):
        for i, p in enumerate(row):
            if len(p) < 4 or p[3] >= 128:
                ck.rect(x + i * s, y + j * s, x + i * s + s - 1, y + j * s + s - 1, p[:3])


def glows(pix, x, y, s):
    for j, row in enumerate(pix):
        for i, p in enumerate(row):
            if p[3] and p[:3] in (GLOW, GLOW_L):
                glow(x + i * s + s // 2, y + j * s + s // 2, 3 * s + 1, GLOW, 0.18)


def main():
    new_canvas(400, 262, seed=77)
    W, H = canvas_size()
    for y in range(H):
        for x in range(W):
            if rnd() < 0.08:
                px(x, y, CAVE)

    pw, ph, gap = 61, 66, 4
    lineup = []
    for g, (title, sil, items) in enumerate(GROUPS):
        gy = 20 + g * 92
        text(4, gy, title, PALE_G)
        # the picked silhouette first, on paper, then the four dressings
        x0, y0 = 4, gy + 8
        rect(x0, y0, x0 + pw - 1, y0 + ph, (196, 198, 188))
        draw(pixels("sil", sil, SIL_PAL), x0, y0 + 4, 3)
        text(x0 + 1, y0 + ph + 4, "SILHOUETTE", (150, 165, 185))
        for k, (name, grid, pal_, note) in enumerate(items):
            pix = pixels(name, grid, pal_)
            path = os.path.join(CHARS, "Char_Hero_%s.png" % name)
            write_png(path, pix)
            print("wrote", path)
            num = "%s%s" % (title.split()[0], "ABCD"[k])
            lineup.append((num, pix))

            x0 = 4 + (k + 1) * (pw + gap) + 6
            rect(x0, y0, x0 + pw - 1, y0 + ph, CAVE_L)
            frame(x0, y0, x0 + pw - 1, y0 + ph, (58, 66, 76))
            glows(pix, x0, y0 + 4, 3)
            draw(pix, x0, y0 + 4, 3)
            tag(x0 + pw - 4 - text_w(num), y0 + ph - 8, num, PALE_G)
            text(x0 + 1, y0 + ph + 4, note, LABEL)

    # lineup at 2x next to a soldier: the hero has to read among the cast at a glance
    floor = 250
    text(4, 204, "LINEUP 2X", PALE_G)
    rect(0, floor, W - 1, H - 1, ROCK_D)
    rect(0, floor, W - 1, floor, ROCK_L)
    import roomkit
    _, _, soldier = roomkit._load(os.path.join(CHARS, "Char_Grenadier.png"))
    order = [(None, soldier)] + lineup
    for i, (num, pix) in enumerate(order):
        pix = [[p if len(p) == 4 else p + (255,) for p in row] for row in pix]
        foot = max(j for j, row in enumerate(pix) if any(p[3] >= 128 for p in row))
        x = 10 + i * 42
        if num:
            glows(pix, x, floor - (foot + 1) * 2, 2)
        draw(pix, x, floor - (foot + 1) * 2, 2)
        if num:
            text(x + 16, floor + 4, num, (150, 165, 185), shadow=False)

    title_bar("HERO - KASA HAT / STAGE MAGE", "4 DRESSINGS EACH / 20X22")
    save(os.path.join(CHARS, "HeroConcept.png"), scale=4)


if __name__ == "__main__":
    main()
