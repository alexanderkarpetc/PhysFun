"""
Five walking mages redrawn from the user's concepts (Assets/GameConcepts/Tools/
hooded_mages.py) - Crimson, Bogcap, Maskwraith, Deepminer, Goldhood - animated with the
tag set the other wizards (wiz_bonecrown, wiz_hollowhood, wiz_ramskull) use:

    Idle   4 frames   standing, a breath, the lights flicker
    Walk   6 frames   a real stride: legs redrawn every frame, body up on the passing step
    Shoot  3 frames   the cast: weapon or claw raised, swung, magic flaring at its tip

No death animation - like every walking enemy they go down as a ragdoll.

The sprites are fixed hand-placed grids, so the animation works on parts of them. Each
mage has a leg spec: which letters below which row are legs (they are erased), where
the two hips sit, and what the legs and feet are drawn in. A frame is the body shifted
by its bob, with fresh legs drawn underneath on the same evenly-spaced stride the
pilgrim uses (Tools/gen_hero_pilgrim.py) - the planted foot slides back a pixel a frame
while the free one swings through - so nothing jumps between frames. The cast turns the
weapon arm about its shoulder, as the box/pivot spec says, and flares on release.

10 fps, PPU 20, facing right. Writes Assets/Sprites/Enemies/wiz_<name>.aseprite (+ .meta)
next to the other wizards.

    python Tools/gen_mages.py [--preview DIR]
"""
import math
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'Assets', 'GameConcepts', 'Tools'))
from gen_ghosts import write_aseprite, write_meta, to_rgba, MS  # noqa: E402
from hooded_mages import SPRITES  # noqa: E402

OUT = os.path.join(ROOT, 'Assets', 'Sprites', 'Enemies')
COUNTS = (('Idle', 4), ('Walk', 6), ('Shoot', 3))
PAD_L, PAD_R, PAD_T = 3, 5, 3       # room for the cast to reach and flare


# Per mage:
#   legs    letters that are legs below `top`; erased and redrawn every frame
#   top     the hip row; legs run from here to the bottom of the grid (+ `extra` rows)
#   hips    far and near hip x
#   leg     far / near leg letter, foot letter, foot width, leg width
#   arm     box (x0, y0, x1, y1) of the casting arm/weapon, `pivot` its shoulder
#   flare   (glow letter, core letter) of its magic
#   flicker letter pairs swapped on the idle breath
#   hem     first row of the robe/coat bottom that sways with the stride
#   neck    first row below the head, where the corpse is cut between head and torso
MAGES = {
    'crimson': dict(legs='w', top=22, hips=(5, 11), leg=('k', 'K', 'w', 3, 1),
                    arm=(15, 12, 21, 20), pivot=(15, 16), flare=('O', 'R'),
                    flicker=[('R', 'P')], hem=19, neck=13),
    'bogcap': dict(legs='', top=19, hips=(8, 11), leg=('r', 'R', 'r', 2, 1), extra=1,
                   arm=(16, 12, 21, 21), pivot=(16, 13), flare=('s', 'S'),
                   flicker=[('s', 'S')], hem=17, neck=12),
    'maskwraith': dict(legs='', top=22, hips=(7, 11), leg=('k', 'k', 'V', 2, 1), extra=1,
                       arm=(16, 11, 23, 15), pivot=(16, 13), flare=('W', 'R'),
                       flicker=[], hem=18, neck=10),
    'deepminer': dict(legs='cCk', top=18, hips=(5, 9), leg=('c', 'C', 'k', 3, 2),
                      arm=(12, 10, 21, 14), pivot=(12, 13), flare=('y', 'Y'),
                      flicker=[('y', 'Y')], hem=15, neck=11),
    'goldhood': dict(legs='kaw', top=21, hips=(5, 9), leg=('k', 'a', 'w', 3, 1),
                     arm=(13, 14, 20, 18), pivot=(13, 15), flare=('Y', 'e'),
                     flicker=[], hem=18, neck=13),
}

# Foot offsets from the hip, frame by frame, as (dx, lifted): the planted foot slides
# back a pixel a frame, the free one swings through a row up. The far leg runs the same
# cycle three frames later.
NEAR = [(2, 0), (1, 0), (0, 0), (-1, 0), (0, 1), (1, 1)]
FAR = NEAR[3:] + NEAR[:3]
BOB = [0, -1, 0, 0, -1, 0]          # up on the passing steps
SWAY = [1, 0, -1, -1, 0, 1]         # the hem follows the forward leg


# ───────────────────────────────────────────────────────────── grid ops ──
def grid_of(name):
    pal, rows = SPRITES[name]
    w = max(len(r) for r in rows)
    return [list(r.ljust(w, '.')) for r in rows], pal


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def split(name):
    """The body without its legs, padded onto the frame canvas, plus the frame size."""
    spec = MAGES[name]
    g, pal = grid_of(name)
    h0, w0 = len(g), len(g[0])
    h = PAD_T + h0 + spec.get('extra', 0)
    w = PAD_L + w0 + PAD_R
    body = blank(w, h)
    for y in range(h0):
        for x in range(w0):
            ch = g[y][x]
            if ch == '.' or (y > spec['top'] and ch in spec['legs']):
                continue
            body[y + PAD_T][x + PAD_L] = ch
    return body, pal, w, h


def shifted(g, dy):
    h, w = len(g), len(g[0])
    out = blank(w, h)
    for y in range(h):
        for x in range(w):
            if g[y][x] != '.' and 0 <= y + dy < h:
                out[y + dy][x] = g[y][x]
    return out


def draw_legs(canvas, spec, near, far, dy):
    """Two legs from the hips (on the hip row, raised by the bob) to the feet on the
    bottom row - or a row up for the swinging one."""
    h = len(canvas)
    top = spec['top'] + PAD_T + dy
    bottom = h - 1
    far_l, near_l, foot, fw, lw = spec['leg']
    for hip, (dx, lifted), leg in ((spec['hips'][0], far, far_l), (spec['hips'][1], near, near_l)):
        hx = hip + PAD_L
        fx = hx + dx
        sole = bottom - lifted
        n = max(1, sole - 1 - top)
        for i in range(n + 1):
            x = int(round(hx + (fx - hx) * i / float(n)))
            for k in range(lw):
                canvas[top + i][x + k] = leg
        for k in range(fw):
            canvas[sole][fx - (fw - 2) + k if fw > 2 else fx + k] = foot


def overlay(base, top):
    out = [row[:] for row in base]
    for y, row in enumerate(top):
        for x, ch in enumerate(row):
            if ch != '.':
                out[y][x] = ch
    return out


def sway(g, from_row, s):
    """Slide every row from `from_row` down by `s` pixels sideways: the robe bottom
    swinging with the step while the shoulders stay put."""
    out = [row[:] for row in g]
    for y in range(max(0, from_row), len(g)):
        row = g[y]
        if s > 0:
            out[y] = ['.'] * s + row[:-s]
        elif s < 0:
            out[y] = row[-s:] + ['.'] * (-s)
    return out


def swap(g, pairs):
    m = {}
    for a, b in pairs:
        m[a], m[b] = b, a
    return [[m.get(ch, ch) for ch in row] for row in g]


def swing(g, box, pivot, degrees):
    """Turn the pixels inside `box` about `pivot`; returns the grid and the arm tip."""
    x0, y0, x1, y1 = box
    px, py = pivot
    h, w = len(g), len(g[0])
    arm = {(x, y): g[y][x] for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
           if 0 <= y < h and 0 <= x < w and g[y][x] != '.'}
    out = [row[:] for row in g]
    for (x, y) in arm:
        out[y][x] = '.'
    a = math.radians(degrees)
    ca, sa = math.cos(a), math.sin(a)
    for y in range(h):
        for x in range(w):
            dx, dy = x - px, y - py
            key = (int(round(px + dx * ca + dy * sa)), int(round(py - dx * sa + dy * ca)))
            if key in arm:
                out[y][x] = arm[key]
    tip = max(arm, key=lambda q: (q[0] - px) ** 2 + (q[1] - py) ** 2)
    tdx, tdy = tip[0] - px, tip[1] - py
    return out, (int(round(px + tdx * ca - tdy * sa)), int(round(py + tdx * sa + tdy * ca)))


def flare(g, at, glow, core, size):
    """A burst of magic at the weapon tip: a core pixel, a cross of glow, and at full
    size the diagonals too."""
    x, y = at
    h, w = len(g), len(g[0])
    pts = [(0, 0, core)] + [(dx, dy, glow) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    if size > 1:
        pts += [(dx, dy, glow) for dx, dy in ((2, 0), (0, -2), (1, -1), (1, 1), (-1, -1))]
    for dx, dy, ch in pts:
        if 0 <= x + dx < w and 0 <= y + dy < h:
            g[y + dy][x + dx] = ch


# ─────────────────────────────────────────────────────────────── frames ──
def frames(name):
    spec = MAGES[name]
    body, pal, w, h = split(name)
    stand = ((0, 0), (0, 0))
    tags = {}

    idle = []
    for i, dy in enumerate((0, 0, 1, 1)):
        f = blank(w, h)
        draw_legs(f, spec, stand[0], stand[1], dy)
        b = shifted(body, dy)
        if i == 2 and spec['flicker']:
            b = swap(b, spec['flicker'])
        idle.append(overlay(f, b))
    tags['Idle'] = idle

    walk = []
    for i in range(6):
        f = blank(w, h)
        draw_legs(f, spec, NEAR[i], FAR[i], BOB[i])
        b = sway(shifted(body, BOB[i]), spec['hem'] + PAD_T + BOB[i], SWAY[i])
        walk.append(overlay(f, b))
    tags['Walk'] = walk

    pivot = (spec['pivot'][0] + PAD_L, spec['pivot'][1] + PAD_T)
    arm = (spec['arm'][0] + PAD_L, spec['arm'][1] + PAD_T,
           spec['arm'][2] + PAD_L, spec['arm'][3] + PAD_T)
    shoot = []
    for k, (deg, size) in enumerate(((-45, 1), (10, 2), (0, 1))):   # raise, release, hold
        f = blank(w, h)
        draw_legs(f, spec, stand[0], stand[1], 0)
        b, tip = swing(body, arm, pivot, deg)
        b = overlay(f, b)
        flare(b, tip, spec['flare'][0], spec['flare'][1], size)
        shoot.append(b)
    tags['Shoot'] = shoot
    return tags, w, h, pal


def corpse_cuts(name, tags, w, h):
    """The CastBuilder rows for this mage's ragdoll, read off Frame_0 (the first Idle frame,
    which is what SoldierRagdollBuilder cuts): head above the neck, the casting arm in its
    box, two legs below the hem split between the hips, the torso everything left over.
    Also where its bolt leaves from, as a local offset from the feet. Printed as C#."""
    spec = MAGES[name]
    neck = spec['neck'] + PAD_T
    hem = spec['hem'] + PAD_T
    x0, y0, x1, y1 = (spec['arm'][0] + PAD_L, spec['arm'][1] + PAD_T,
                      spec['arm'][2] + PAD_L, spec['arm'][3] + PAD_T)
    y0 = max(y0, neck)
    y1 = min(y1, hem - 1)
    split = (spec['hips'][0] + spec['hips'][1]) // 2 + PAD_L + 1
    hl, hr = spec['hips'][0] + PAD_L + 0.5, spec['hips'][1] + PAD_L + 0.5
    px, py = spec['pivot'][0] + PAD_L, spec['pivot'][1] + PAD_T
    torso = []
    if y0 > neck:
        torso.append((0, neck, w, y0 - neck))
    torso.append((0, y0, x0, y1 - y0 + 1))
    if y1 + 1 < hem:
        torso.append((0, y1 + 1, w, hem - y1 - 1))
    # the head hinges on the middle of the neck row as Frame_0 draws it
    frame0 = tags['Idle'][0]
    xs = [x for x, ch in enumerate(frame0[neck - 1]) if ch != '.' and x < x0]
    head_x = (min(xs) + max(xs)) / 2.0 + 0.5 if xs else w / 2.0
    rect = lambda r: 'new RectInt(%d, %d, %d, %d)' % r
    lines = ['new("torso", -1, Vector2.zero, 2, %s),' % ', '.join(rect(r) for r in torso),
             'new("leg_l", 0, new Vector2(%.1ff, %.1ff), 1, %s),' % (hl, hem - 0.5, rect((0, hem, split, h - hem))),
             'new("leg_r", 0, new Vector2(%.1ff, %.1ff), 0, %s),' % (hr, hem - 0.5, rect((split, hem, w - split, h - hem))),
             'new("head", 0, new Vector2(%.1ff, %.1ff), 4, %s),' % (head_x, neck - 0.5, rect((0, 0, w, neck))),
             'new("arm_r", 0, new Vector2(%.1ff, %.1ff), 3, %s),' % (px, py, rect((x0, y0, w - x0, y1 - y0 + 1)))]
    # the bolt leaves from where the flare blooms on the release frame
    _, tip = swing(split_body(name), arm_box(name), (px, py), 10)
    off = ((tip[0] + 0.5 - w / 2.0) / 20.0, (h - tip[1] - 0.5) / 20.0)
    return lines, off


def split_body(name):
    return split(name)[0]


def arm_box(name):
    a = MAGES[name]['arm']
    return (a[0] + PAD_L, a[1] + PAD_T, a[2] + PAD_L, a[3] + PAD_T)


def guid(key):
    import hashlib
    return hashlib.md5(('physfun/mages/' + key).encode()).hexdigest()


def preview(made, outdir):
    scale, pad = 5, 8
    cw = max(w for _, (_, w, _, _) in made) * scale
    ch = max(h for _, (_, _, h, _) in made) * scale
    sheet = Image.new('RGBA', (70 + 13 * (cw + 2) + 3 * pad, len(made) * (ch + pad) + 20),
                      (26, 30, 35, 255))
    d = ImageDraw.Draw(sheet)
    x = 70
    for tag, n in COUNTS:
        d.text((x, 4), tag, fill=(223, 232, 192))
        x += n * (cw + 2) + pad
    for r, (name, (tags, w, h, pal)) in enumerate(made):
        y = 20 + r * (ch + pad)
        d.text((6, y + ch // 2 - 6), name, fill=(223, 232, 192))
        x = 70
        for tag, n in COUNTS:
            for g in tags[tag]:
                d.rectangle((x, y, x + cw - 1, y + ch - 1), fill=(53, 62, 70))
                d.line((x, y + ch - (ch - h * scale) // 2, x + cw - 1, y + ch - (ch - h * scale) // 2),
                       fill=(89, 99, 113))
                img = to_rgba(g, pal).resize((w * scale, h * scale), Image.NEAREST)
                sheet.alpha_composite(img, (x + (cw - w * scale) // 2, y + (ch - h * scale) // 2))
                x += cw + 2
            x += pad
    sheet.save(os.path.join(outdir, 'mage_anims.png'))

    seq = [(tag, k) for tag, n in COUNTS for _ in range(2) for k in range(n)]
    gifs = []
    for tag, k in seq:
        g = Image.new('RGBA', (len(made) * (cw + pad) + pad, ch + 30), (53, 62, 70, 255))
        gd = ImageDraw.Draw(g)
        gd.text((pad, 4), tag, fill=(223, 232, 192))
        for i, (name, (tags, w, h, pal)) in enumerate(made):
            img = to_rgba(tags[tag][k], pal).resize((w * scale, h * scale), Image.NEAREST)
            gx = pad + i * (cw + pad)
            g.alpha_composite(img, (gx + (cw - w * scale) // 2, 22 + ch - h * scale))
            gd.line((gx, 22 + ch, gx + cw - 1, 22 + ch), fill=(89, 99, 113))
        gifs.append(g.convert('RGB'))
    gifs[0].save(os.path.join(outdir, 'mage_anims.gif'), save_all=True, append_images=gifs[1:],
                 duration=MS, loop=0)


def main():
    made = []
    for name in MAGES:
        tags, w, h, pal = frames(name)
        images, ranges, at = [], [], 0
        for tag, n in COUNTS:
            images += [to_rgba(g, pal) for g in tags[tag]]
            ranges.append((tag, at, at + n - 1))
            at += n
        path = os.path.join(OUT, 'wiz_%s.aseprite' % name)
        write_aseprite(path, images, ranges)
        if not os.path.exists(path + '.meta'):
            write_meta(path + '.meta', guid(name), w, h)
        made.append((name, (tags, w, h, pal)))
        print('%-10s %2dx%-2d %d frames -> %s' % (name, w, h, len(images), path))
    if '--cuts' in sys.argv:
        for name, (tags, w, h, pal) in made:
            lines, off = corpse_cuts(name, tags, w, h)
            print('// %s  %dx%d  cast offset (%.3f, %.3f)' % (name, w, h, off[0], off[1]))
            for ln in lines:
                print(ln)
    if '--preview' in sys.argv:
        outdir = sys.argv[sys.argv.index('--preview') + 1]
        preview(made, outdir)
        print('preview    %s' % outdir)


if __name__ == '__main__':
    main()
