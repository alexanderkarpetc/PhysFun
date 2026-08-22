"""Take a Retro Diffusion export, recover its native pixel grid, and optionally remap it
onto the palette pulled from Noita's enemy sheets."""
import sys, os, glob, struct, zlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import load


def write_png(path, rows):
    h = len(rows)
    w = len(rows[0])
    raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in rows)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(raw, 9))
    out += chunk(b"IEND", b"")
    open(path, "wb").write(out)


def detect_scale(w, h, px):
    """Largest integer factor whose blocks are all one flat colour."""
    for s in range(min(w, h), 1, -1):
        if w % s or h % s:
            continue
        ok = True
        for by in range(0, h, s):
            for bx in range(0, w, s):
                first = px[by][bx]
                for y in range(by, by + s):
                    for x in range(bx, bx + s):
                        if px[y][x] != first:
                            ok = False
                            break
                    if not ok: break
                if not ok: break
            if not ok: break
        if ok:
            return s
    return 1


def downscale(px, w, h, s):
    return [[px[y * s][x * s] for x in range(w // s)] for y in range(h // s)]


# perceptual-ish distance: weighted RGB is close enough to Lab at these palette sizes
def dist(a, b):
    rm = (a[0] + b[0]) / 2.0
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return (2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db


def remap(rows, palette):
    cache = {}
    out = []
    for row in rows:
        r = []
        for p in row:
            if p[3] == 0:
                r.append((0, 0, 0, 0))
                continue
            key = p[:3]
            if key not in cache:
                cache[key] = min(palette, key=lambda c: dist(key, c))
            r.append(cache[key] + (p[3],))
        out.append(r)
    return out


def upscale(rows, s):
    return [[p for p in row for _ in range(s)] for row in rows for _ in range(s)]


def paste(canvas, rows, ox, oy):
    for y, row in enumerate(rows):
        for x, p in enumerate(row):
            if p[3] == 0:
                continue
            canvas[oy + y][ox + x] = p
