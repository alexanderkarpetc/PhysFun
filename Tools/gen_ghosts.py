"""
Eight ghost enemies picked from Assets/GameConcepts/Characters/GhostConcepts.png -
Phantom, Howler, Skulls, Maw, Weaver, Watcher, Stinger, Leech - as animated sprites.

Each one is drawn with the primitives of the concept sheet (Assets/GameConcepts/Tools/
ghosts.py), but parameterised, so a frame is the same ghost with its jaw a bit wider or
its claws further out rather than a fresh drawing. Every ghost gets the enemy tag set:

    Idle   4 frames   hovering in place, a pixel of bob
    Walk   6 frames   flying - the body shears forward, the tail streams back
    Shoot  3 frames   its attack: wind-up, strike, recover (each ghost its own)
    Death  4 frames   comes apart into dust that drifts up

Idle / Walk / Shoot keep the names the other enemies use, so these drop into the same
controller setup when they get behaviour. 10 fps, PPU 20, facing right.

    python Tools/gen_ghosts.py [--preview DIR]

writes Assets/Sprites/Enemies/Ghosts/ghost_<name>.aseprite (+ .meta) and, with
--preview, a sheet and a gif of every animation into DIR.
"""
import math
import os
import random
import struct
import sys
import zlib

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'Assets', 'GameConcepts', 'Tools'))
from ghosts import Canvas, PAL, GLOWING, BAYER, SKULL, shade_px  # noqa: E402

OUT = os.path.join(ROOT, 'Assets', 'Sprites', 'Enemies', 'Ghosts')
FPS = 10
MS = 1000 // FPS
COUNTS = (('Idle', 4), ('Walk', 6), ('Shoot', 3), ('Death', 4))
MARGIN = 3          # room around the body for bob, lean and lunges


# ────────────────────────────────────────────────────────────── motion ──
def bob(i, n):
    """A pixel of hover, as a smooth wave sampled on n frames."""
    return int(round(math.sin(2 * math.pi * i / n)))


def shear(g, amount):
    """Lean into flight: rows above the middle slide forward, rows below slide back."""
    h = len(g)
    mid = h / 2.0
    out = []
    for y, row in enumerate(g):
        s = int(round(amount * (mid - y) / mid))
        if s > 0:
            row = ['.'] * s + row[:-s]
        elif s < 0:
            row = row[-s:] + ['.'] * (-s)
        out.append(row)
    return out


def place(g, w, h, dx=0, dy=0):
    """Body grid centred on the frame canvas, offset by (dx, dy)."""
    out = [['.'] * w for _ in range(h)]
    ox, oy = (w - len(g[0])) // 2 + dx, (h - len(g)) // 2 + dy
    for y, row in enumerate(g):
        for x, ch in enumerate(row):
            if ch != '.' and 0 <= x + ox < w and 0 <= y + oy < h:
                out[y + oy][x + ox] = ch
    return out


def dissolve(g, k, n, seed, lights=GLOWING, dust='g'):
    """Death frame k of n: the body breaks up from the edges in, what is left drifts
    upward, and loose grains rise off it. Eyes go out on the last frame."""
    rnd = random.Random(seed + k)
    h, w = len(g), len(g[0])
    t = (k + 1) / float(n)
    out = [['.'] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            ch = g[y][x]
            if ch == '.':
                continue
            if ch in lights:
                if k < n - 1:
                    out[max(0, y - k)][x] = ch
                continue
            if BAYER[y % 4][x % 4] + rnd.random() * 4 >= t * 20:
                out[max(0, y - k)][x] = ch
            elif rnd.random() < 0.18:
                out[max(0, y - k - 2 - rnd.randint(0, 2))][x] = dust
    return out


# ────────────────────────────────────────────────────────────── ghosts ──
# Each builder draws the body for one pose. Parameters: `t` is the frame's phase
# (0..1) for anything that sways, `a` the attack amount (0 rest, 1 full strike).

def phantom(t=0.0, a=0.0, fly=False):
    c = Canvas(27, 26, 2)
    c.poly([(9, 3), (13, 2), (15, 6), (13, 13), (10, 18), (7, 13)], 'K')
    c.blob(13, 4, 3, 3, 'K')
    c.spikes('K', 22, 200, 80, (1, 3), 2)
    sway = int(round(math.sin(t * 2 * math.pi)))
    if a <= 0:
        hand = (17 + (0 if not fly else -2), 17 + sway)
        c.path([(12, 8), (16, 12 + sway // 2), hand], 'K')
        c.claw(hand[0], hand[1], 80, 3, 4)
    elif a < 0.5:
        # wind-up: the long arm goes up over the head
        c.path([(12, 8), (16, 5), (17, 2)], 'K')
        c.claw(17, 2, -70, 3, 4)
    elif a > 0.9:
        # the rake: arm thrown forward and down, fingers spread wide
        c.path([(12, 8), (17, 10), (21, 13)], 'K')
        c.path([(13, 8), (18, 10)], 'j')
        c.claw(21, 13, 25, 4, 5, spread=18)
    else:
        # follow-through: the arm swings on past and hangs low
        c.path([(12, 8), (16, 13), (19, 18)], 'K')
        c.claw(19, 18, 70, 3, 4)
    c.path([(9, 8), (6 - (2 if fly else 0), 13), (6 - (3 if fly else 0), 18 + sway)], 'j')
    c.claw(6 - (3 if fly else 0), 18 + sway, 100, 3, 3, 'd')
    back = 3 if fly else 0
    c.path([(10, 18), (9 - back, 22)], 'K')
    c.path([(12, 17), (13 - back, 22)], 'K')
    blink = 0.7 < t < 0.8 and not fly and a == 0
    for (x, y) in ((13, 3), (15, 3), (13, 5), (15, 5)):
        c.put(x, y, 'k' if blink else 'w')
    c.fade(20)
    return c.g


def howler(t=0.0, a=0.0, fly=False):
    c = Canvas(18, 30, 4)
    c.poly([(5, 2), (12, 1), (15, 6), (14, 14), (12, 21), (8, 25), (4, 16), (3, 7)], 'K')
    jaw = 19 + int(round(math.sin(t * 2 * math.pi))) + int(round(a * 6))
    c.poly([(7, 9), (12, 9), (12, jaw), (9, jaw + 3), (7, jaw - 1)], 'k')
    for y in range(10, jaw, 2):
        c.put(7, y, 'B')
        c.put(12, y, 'B')
    c.teeth(7, 12, 9)
    c.eye(7, 5)
    c.eye(12, 5)
    if a > 0.5:                                   # the scream lights the sockets up
        for (x, y) in ((6, 5), (8, 5), (11, 5), (13, 5)):
            c.put(x, y, 'r')
    c.spikes('K', 16, 110 + (40 if fly else 0), 60, (1, 4), 4)
    c.fade(21 + int(round(a * 2)))
    return c.g


def skulls(t=0.0, a=0.0, fly=False):
    c = Canvas(30, 24, 8)
    for k, (x, y, s) in enumerate(((1, 9, 81), (10, 2, 82), (18, 10, 83))):
        dy = int(round(math.sin((t + k / 3.0) * 2 * math.pi)))
        dx = int(round(a * (3 + k)))
        x, y = x + dx, y + 1 + dy
        c.stamp(SKULL, x, y)
        gap = 1 + int(round(a * 2))
        c.teeth(x + 3, x + 6, y + 6 + gap)
        r = random.Random(s)
        px, py = x + 1, y + 4
        for j in range(6 + (3 if fly else 0) + int(a * 3)):
            px -= 1
            py += r.choice((0, 1))
            c.put(px, py, 'v')
            c.put(px, py + 1, 'V' if j < 2 else 'v')
    return c.g


def maw(t=0.0, a=0.0, fly=False):
    c = Canvas(30, 24, 9)
    c.blob(13, 12, 11, 9, 'K', 0.3)
    breathe = int(round(math.sin(t * 2 * math.pi)))
    top, bot = 8 - int(round(a * 2)), 16 + breathe + int(round(a * 3))
    c.poly([(4, top + 1), (23, top - 1), (24, bot), (6, bot + 1)], 'o')
    c.teeth(4, 23, top)
    c.teeth(5, 23, bot, up=True)
    reach = 21 + int(round(a * 7))
    c.path([(10, (top + bot) // 2 + 1), (16, (top + bot) // 2), (reach, (top + bot) // 2 + 1)], 'O', 2)
    blink = 0.45 < t < 0.55 and a == 0
    for (x, y) in ((8, 4), (12, 3), (16, 4), (19, 5)):
        c.eye(x, y - int(round(a)))
        if blink and x in (12, 19):
            c.put(x, y, 'k')
    c.spikes('K', 24, 180, 100 if not fly else 60, (1, 4), 9)
    c.fade_back(5 + (3 if fly else 0))
    return c.g


def weaver(t=0.0, a=0.0, fly=False):
    c = Canvas(30, 24, 13)
    c.blob(14, 7, 6, 4.5, 'K', 0.2)
    c.blob(19, 6, 3, 2.5, 'K')
    c.eye(19, 5)
    c.eye(21, 6)
    c.teeth(18, 22, 8)
    r = random.Random(13)
    for i in range(7):
        x0 = 9 + i * 2
        out = r.choice((-4, -3, 3, 4))
        # legs paddle in flight, twitch at rest, the front pair stabs on attack
        ph = math.sin((t + i * 0.37) * 2 * math.pi)
        kx = x0 + out + int(round(ph * (2 if fly else 1)))
        ky = 11 + r.randint(0, 3)
        fx = kx + (1 if kx > x0 else -1)
        fy = 20
        if a > 0 and i >= 5:
            kx, ky = x0 + 4, 3 + int(round((1 - a) * 4))
            fx, fy = x0 + 8, 10 - int(round(a * 3))
        c.path([(x0, 10), (kx, ky), (fx, fy)], 'd')
        c.put(fx, fy + 1, 'B')
    c.spikes('K', 14, 270, 70, (1, 3), 13)
    return c.g


def watcher(t=0.0, a=0.0, fly=False):
    c = Canvas(26, 28, 14)
    c.blob(12, 9, 8, 7, 'K', 0.35)
    c.blob(13, 9, 4.5 + a, 4 + a, 'w')
    look = int(round(math.sin(t * 2 * math.pi) * 1.4)) if a == 0 else 2
    c.blob(14 + look, 9, 2.4 - a, 2.4 - a, 'r')
    c.put(14 + look, 9, 'k')
    if a < 0.5:
        c.put(15 + look, 9, 'k')
    if a >= 0.5:
        for k in range(3, 10):
            c.put(17 + k, 9, 'R' if k % 2 else 'r')
    for (p, q) in (((10, 8), (12, 7)), ((16, 12), (17, 13)), ((11, 12), (10, 13))):
        c.path([p, q], 'O')
    r = random.Random(14)
    for i in range(6):
        x = 6 + i * 2 + r.randint(0, 1)
        pts = [(x, 15)]
        for k in range(4):
            sway = int(round(math.sin((t + i * 0.2 + k * 0.15) * 2 * math.pi)))
            pts.append((pts[-1][0] + sway - (1 if fly else 0), pts[-1][1] + 2))
        c.path(pts, 'K')
        c.put(pts[-1][0], pts[-1][1] + 1, 'd')
    c.spikes('K', 16, 270, 120, (1, 3), 14)
    return c.g


def stinger(t=0.0, a=0.0, fly=False):
    c = Canvas(24, 30, 22)
    squeeze = int(round(math.sin(t * 2 * math.pi) * (1.5 if fly else 1)))
    c.poly([(3 + squeeze, 9), (6, 3), (14, 2), (17 - squeeze, 8), (16 - squeeze, 10), (4 + squeeze, 10)], 'v')
    c.blob(10, 5, 6 - squeeze * 0.5, 4, 'v')
    c.eye(12, 5)
    r = random.Random(22)
    for x in range(4, 17, 2):
        pts = [(x, 10)]
        n = r.randint(5, 8)
        for k in range(n):
            wave = math.sin((t + x * 0.05 + k * 0.12) * 2 * math.pi)
            dx = r.choice((-1, 0, 0, 1)) + int(round(wave * 0.6))
            if a > 0:                              # strands whip forward
                dx += int(round(a * 1.5))
            pts.append((pts[-1][0] + dx, pts[-1][1] + 2 - (1 if a > 0.7 and k > 2 else 0)))
        c.path(pts, 'V' if x % 4 else 'v')
        c.put(pts[-1][0] + 1, pts[-1][1], 'B')
        c.put(pts[-1][0] + 1, pts[-1][1] - 1, 'B')
    return c.g


def leech(t=0.0, a=0.0, fly=False):
    c = Canvas(34, 20, 25)
    speed = 2 if fly else 1
    lunge = int(round(a * 4))
    pts = [(2, 14), (6, 12), (10, 13), (14, 10), (18, 9), (22, 7)]
    for k, ((x, y), rad) in enumerate(zip(pts, (1.2, 1.6, 2, 2.4, 2.8, 3.2))):
        wave = int(round(math.sin((t * speed + k * 0.22) * 2 * math.pi) * 1.2))
        c.blob(x + lunge * k / 5.0, y + wave, rad + 0.5, rad, 'j')
    hx = 24 + lunge
    c.blob(hx, 7, 4.5, 4.5, 'j')
    ring = 3 + a
    c.blob(hx + 1, 7, ring, ring, 'o')
    c.blob(hx + 1.5, 7, 1.5 + a, 1.5 + a, 'k')
    for ang in range(0, 360, 40):
        c.put(hx + 1 + math.cos(math.radians(ang)) * ring, 7 + math.sin(math.radians(ang)) * ring, 'B')
    c.put(hx - 3, 4, 'R')
    c.fade_back(10)
    return c.g


GHOSTS = [
    ('phantom', phantom),
    ('howler', howler),
    ('skulls', skulls),
    ('maw', maw),
    ('weaver', weaver),
    ('watcher', watcher),
    ('stinger', stinger),
    ('leech', leech),
]


def frames_for(fn, seed):
    """All frames of one ghost as letter grids on one canvas size, tag by tag."""
    raw = {
        'Idle': [(fn(t=i / 4.0), bob(i, 4), 0) for i in range(4)],
        'Walk': [(fn(t=i / 6.0, fly=True), bob(i, 6), 2) for i in range(6)],
        # wind-up, strike, follow-through
        'Shoot': [(fn(t=0.0, a=a), 0, 0) for a in (0.4, 1.0, 0.7)],
    }
    bw = max(len(g[0]) for v in raw.values() for g, _, _ in v)
    bh = max(len(g) for v in raw.values() for g, _, _ in v)
    w, h = bw + 2 * MARGIN, bh + 2 * MARGIN
    tags = {}
    for name, items in raw.items():
        out = []
        for g, dy, lean in items:
            if lean:
                g = shear(g, lean)
            out.append(place(g, w, h, 0, dy))
        tags[name] = out
    base = tags['Idle'][0]
    tags['Death'] = [dissolve(base, k, 4, seed) for k in range(4)]
    return tags, w, h


def to_rgba(g, pal=None):
    """Ghosts go through the cast's shading; hand-shaded sprites (`gen_mages.py`) pass
    their own palette and map straight across."""
    if pal is not None:
        img = Image.new('RGBA', (len(g[0]), len(g)))
        p = img.load()
        for y, row in enumerate(g):
            for x, ch in enumerate(row):
                if ch != '.':
                    p[x, y] = pal[ch] + (255,)
        return img
    pix = shade_px(g)
    img = Image.new('RGBA', (len(g[0]), len(g)))
    p = img.load()
    for y, row in enumerate(pix):
        for x, c in enumerate(row):
            if c:
                p[x, y] = c + (255,)
    return img


# ──────────────────────────────────────────────────────────── aseprite ──
def _string(s):
    b = s.encode('utf-8')
    return struct.pack('<H', len(b)) + b


def _chunk(kind, data):
    return struct.pack('<IH', len(data) + 6, kind) + data


TAG_COLORS = {'Idle': (0, 0, 0), 'Walk': (96, 160, 96), 'Shoot': (200, 80, 64), 'Death': (110, 110, 160)}


def write_aseprite(path, images, tags):
    """One RGBA layer, one compressed cel per frame, the tag ranges on frame 0 - the
    same shape as the hand-made enemy files, which is what Unity's importer expects."""
    w, h = images[0].size
    frames = []
    for i, img in enumerate(images):
        chunks = []
        if i == 0:
            layer = struct.pack('<HHHHHHB3x', 3, 0, 0, 0, 0, 0, 255) + _string('Layer 1')
            chunks.append(_chunk(0x2004, layer))
            body = struct.pack('<H8x', len(tags))
            for name, a, b in tags:
                r, g, bl = TAG_COLORS.get(name, (0, 0, 0))
                # Death plays once; everything else loops (0 = forever in Aseprite's repeat field)
                repeat = 1 if name == 'Death' else 0
                body += struct.pack('<HHBH6xBBBx', a, b, 0, repeat, r, g, bl) + _string(name)
            chunks.append(_chunk(0x2018, body))
        cel = struct.pack('<HhhBHh5xHH', 0, 0, 0, 255, 2, 0, w, h) + zlib.compress(img.tobytes())
        chunks.append(_chunk(0x2005, cel))
        data = b''.join(chunks)
        head = struct.pack('<IHHH2xI', 16 + len(data), 0xF1FA, len(chunks), MS, len(chunks))
        frames.append(head + data)
    body = b''.join(frames)
    header = struct.pack('<IHHHHHIHII', 128 + len(body), 0xA5E0, len(images), w, h, 32, 1, MS, 0, 0)
    header += struct.pack('<B3xHBBhhHH', 0, 0, 1, 1, 0, 0, 16, 16)
    header += b'\0' * (128 - len(header))
    with open(path, 'wb') as f:
        f.write(header + body)


def write_meta(path, guid, w, h):
    """Importer settings copied from the other enemies (PPU 20, bottom-centre pivot,
    clips generated per tag); Unity fills in the per-frame sprite data on import."""
    src = open(os.path.join(ROOT, 'Assets', 'Sprites', 'Enemies', 'gaper.aseprite.meta'),
               encoding='utf-8').read()
    head = src[:src.index('  animatedSpriteImportData:')]
    head = head.replace('guid: 99578b370e2144ef93450ae049d06e31', 'guid: ' + guid, 1)
    tail = ('  animatedSpriteImportData: []\n  spriteSheetImportData: []\n  tileSetImportData: []\n'
            '  asepriteLayers: []\n  tileSets: []\n  platformSettings: []\n'
            '  generatePhysicsShape: 0\n  secondarySpriteTextures: []\n  spritePackingTag: \n'
            '  canvasSize: {x: %d, y: %d}\n  previousTextureSize: {x: 0, y: 0}\n' % (w, h))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head + tail)


def guid(key):
    import hashlib
    return hashlib.md5(('physfun/ghosts/' + key).encode()).hexdigest()


# ───────────────────────────────────────────────────────────── preview ──
def preview(all_frames, outdir):
    scale, pad, label = 4, 8, 70
    rows = []
    for name, (tags, w, h, pal) in all_frames:
        rows.append((name, tags, w, h, pal))
    cw = max(r[2] for r in rows) * scale
    ch = max(r[3] for r in rows) * scale
    ncol = sum(n for _, n in COUNTS)
    sheet = Image.new('RGBA', (label + ncol * (cw + 2) + len(COUNTS) * pad, len(rows) * (ch + pad) + 20),
                      (26, 30, 35, 255))
    d = ImageDraw.Draw(sheet)
    x = label
    for tag, n in COUNTS:
        d.text((x, 4), tag, fill=(223, 232, 192))
        x += n * (cw + 2) + pad
    for r, (name, tags, w, h, pal) in enumerate(rows):
        y = 20 + r * (ch + pad)
        d.text((6, y + ch // 2 - 6), name, fill=(223, 232, 192))
        x = label
        for tag, n in COUNTS:
            for g in tags[tag]:
                d.rectangle((x, y, x + cw - 1, y + ch - 1), fill=(53, 62, 70))
                img = to_rgba(g, pal).resize((w * scale, h * scale), Image.NEAREST)
                sheet.alpha_composite(img, (x + (cw - w * scale) // 2, y + (ch - h * scale) // 2))
                x += cw + 2
            x += pad
    sheet.save(os.path.join(outdir, 'ghost_anims.png'))

    # gif: every ghost, cycling Idle -> Walk -> Shoot -> Death
    seq = [(tag, k) for tag, n in COUNTS for rep in range(2 if tag in ('Idle', 'Walk') else 1)
           for k in range(n)]
    gifs = []
    for tag, k in seq:
        g = Image.new('RGBA', (len(rows) * (cw + pad) + pad, ch + 30), (53, 62, 70, 255))
        gd = ImageDraw.Draw(g)
        gd.text((pad, 4), tag, fill=(223, 232, 192))
        for i, (name, tags, w, h, pal) in enumerate(rows):
            img = to_rgba(tags[tag][k], pal).resize((w * scale, h * scale), Image.NEAREST)
            gx = pad + i * (cw + pad)
            g.alpha_composite(img, (gx + (cw - w * scale) // 2, 22 + (ch - h * scale) // 2))
        gifs.append(g.convert('RGB'))
    gifs[0].save(os.path.join(outdir, 'ghost_anims.gif'), save_all=True, append_images=gifs[1:],
                 duration=MS, loop=0)


# ──────────────────────────────────────────────────────────────── main ──
def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(OUT + '.meta'):
        with open(OUT + '.meta', 'w', newline='\n') as f:
            f.write('fileFormatVersion: 2\nguid: %s\nfolderAsset: yes\nDefaultImporter:\n'
                    '  externalObjects: {}\n  userData: \n  assetBundleName: \n'
                    '  assetBundleVariant: \n' % guid('folder'))
    made = []
    jobs = [(name, lambda fn=fn, k=k: frames_for(fn, 100 + k) + (None,))
            for k, (name, fn) in enumerate(GHOSTS)]
    for name, job in jobs:
        tags, w, h, pal = job()
        images, ranges, at = [], [], 0
        for tag, n in COUNTS:
            images += [to_rgba(g, pal) for g in tags[tag]]
            ranges.append((tag, at, at + n - 1))
            at += n
        path = os.path.join(OUT, 'ghost_%s.aseprite' % name)
        write_aseprite(path, images, ranges)
        if not os.path.exists(path + '.meta'):
            write_meta(path + '.meta', guid(name), w, h)
        made.append((name, (tags, w, h, pal)))
        print('%-8s %2dx%-2d %d frames -> %s' % (name, w, h, len(images), path))
    if '--preview' in sys.argv:
        outdir = sys.argv[sys.argv.index('--preview') + 1]
        preview(made, outdir)
        print('preview  %s' % outdir)


if __name__ == '__main__':
    main()
