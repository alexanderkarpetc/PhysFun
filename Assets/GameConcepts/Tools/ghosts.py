"""Ghost enemy concepts: thirty spectres, after Noita's (data/enemies_gfx: ghost, phantom,
wraith and wraith_arm, ethereal_being, greed_ghost, the skulls).

The rule set that keeps them hostile rather than cute - the first pass broke every one
of these and read as a row of mascots:

* Dark bodies. Near-black void with only a cold rim of light on the top edge; nothing
  pale and round.
* Eyes are pinpoints: one or two hot pixels sunk in a dark socket, slanted when there
  are two. Never white circles with pupils.
* Teeth, claws, hooks. If there is a mouth it is open and jagged; if there are hands
  they are long bone fingers reaching forward.
* Leaning in. Everything faces right, toward the player, head pushed forward, the body
  tearing into spikes and dissolving into an ordered dither behind and below it.

Cyan stays the hero's; enemy glow is ember red, with pale glints and lamp gold as the
only other lights.

Sprites are drawn on their own small canvas with a few primitives (blobs, polygons,
spikes, claws, teeth), shaded with the cast's light, and laid out on one labelled sheet.

    python ghosts.py

writes `Characters/GhostConcepts.png`.
"""
import math
import os
import random

from conceptkit import *  # noqa: F401,F403
import conceptkit as ck

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "Characters"))

PAL = {
    'k': (12, 10, 16), 'K': (28, 22, 34), 'j': (44, 36, 52), 'J': (64, 54, 74),   # void
    'g': (52, 54, 62), 'G': (78, 82, 92),                                          # ash
    'r': (176, 34, 30), 'R': (255, 112, 80), 'w': (226, 220, 232),                 # eyes
    'b': (150, 140, 116), 'B': (192, 184, 160), 'd': (96, 86, 70),                 # bone
    'o': (64, 20, 24), 'O': (104, 32, 34),                                         # blood
    'v': (52, 36, 66), 'V': (82, 60, 104),                                         # violet
    'm': (52, 70, 52), 'M': (82, 106, 76),                                         # rot
    'y': (214, 160, 64), 'Y': (255, 222, 140),                                     # lamp, gold
    'c': (70, 70, 76), 'C': (116, 116, 122),                                       # iron
    'u': (90, 60, 42), 'h': (110, 92, 60),                                         # rope, straw
    'n': (130, 130, 134), 'N': (80, 80, 86),                                       # static
}
GLOWING = set('rRwyY')
BONE = set('bBd')


# ─────────────────────────────────────────────────────────── primitives ──
class Canvas:
    def __init__(self, w, h, seed=1):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]
        self.rnd = random.Random(seed)

    def put(self, x, y, ch):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch

    def at(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def blob(self, cx, cy, rx, ry, ch, rough=0.0):
        for y in range(self.h):
            for x in range(self.w):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1 + (self.rnd.uniform(-rough, rough) if rough else 0):
                    self.g[y][x] = ch

    def poly(self, pts, ch):
        n = len(pts)
        for y in range(self.h):
            xs = []
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 <= y + 0.5 < y1) or (y1 <= y + 0.5 < y0):
                    xs.append(x0 + (y + 0.5 - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                    self.put(x, y, ch)

    def line(self, x0, y0, x1, y1, ch, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / float(n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for k in range(w):
                self.put(x, y + k, ch)

    def path(self, pts, ch, w=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], ch, w)

    def stamp(self, rows, x, y):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != '.':
                    self.put(x + i, y + j, ch)

    def edge(self, ch):
        return [(x, y) for y in range(self.h) for x in range(self.w) if self.g[y][x] == ch
                and any(self.at(x + dx, y + dy) == '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]

    def spikes(self, ch, n, angle, spread, length, seed=0, src=None):
        """Torn cloth / bristles: rays out of the body edge, all leaning one way
        (`angle` in degrees, 180 = back, 90 = down)."""
        rnd = random.Random(seed)
        edge = self.edge(src or ch)
        a0 = math.radians(angle)
        cand = [(x, y) for x, y in edge
                if math.cos(a0) * (x - self.w / 2) + math.sin(a0) * (y - self.h / 2) > -2]
        cand = cand or edge
        for _ in range(n):
            x, y = rnd.choice(cand)
            a = a0 + math.radians(rnd.uniform(-spread, spread))
            ln = rnd.randint(*length)
            for k in range(1, ln + 1):
                self.put(x + math.cos(a) * k, y + math.sin(a) * k, ch)

    def claw(self, x, y, angle, fingers=3, length=4, ch='b', spread=22, curl=18):
        """Bone fingers fanning from (x, y), hooking down at the tips."""
        for f in range(fingers):
            a = math.radians(angle + (f - (fingers - 1) / 2.0) * spread)
            px, py = x, y
            for k in range(length):
                a += math.radians(curl / max(length, 1))
                px, py = px + math.cos(a), py + math.sin(a)
                self.put(px, py, ch if k < length - 1 else 'B')

    def teeth(self, x0, x1, y, up=False, ch='B'):
        for x in range(x0, x1 + 1):
            self.put(x, y, ch)
            if (x - x0) % 2 == 0:
                self.put(x, y + (-1 if up else 1), ch)

    def eye(self, x, y, socket=True):
        if socket:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if self.at(x + dx, y + dy) not in GLOWING:
                    self.put(x + dx, y + dy, 'k')
        self.put(x, y, 'R')

    def fade(self, start, axis='y', back=False):
        """Ordered-dither dissolve: from row (or column) `start` to the far edge the body
        thins out until nothing is left. Lights never fade."""
        size = self.h if axis == 'y' else self.w
        for y in range(self.h):
            for x in range(self.w):
                v = y if axis == 'y' else x
                if back:
                    v = start - v + start
                if v < start or self.g[y][x] == '.' or self.g[y][x] in GLOWING:
                    continue
                span = (size - start) if not back else start + 1
                t = (v - start + 1) / float(span + 1)
                if BAYER[y % 4][x % 4] < t * 18:
                    self.g[y][x] = '.'

    def fade_back(self, upto):
        """Dissolve toward the left edge (the trailing side) up to column `upto`."""
        for y in range(self.h):
            for x in range(upto):
                if self.g[y][x] == '.' or self.g[y][x] in GLOWING:
                    continue
                t = (upto - x) / float(upto + 1)
                if BAYER[y % 4][x % 4] < t * 18:
                    self.g[y][x] = '.'


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

SKULL = ["..bBBb.",
         ".bBBBBb",
         "bBkkBkk",
         "bBkRBkR",
         ".bBBdBb",
         "..dBdBd",
         "...d.d."]


# ──────────────────────────────────────────────────────────────── ghosts ──
def shade_():
    c = Canvas(28, 24, 1)
    c.blob(13, 11, 9, 7, 'K', 0.25)
    c.blob(19, 12, 5, 4, 'K', 0.2)
    c.spikes('K', 46, 180, 110, (2, 6), 1)
    c.poly([(16, 14), (25, 13), (23, 17), (17, 17)], 'k')
    c.teeth(17, 24, 14)
    c.teeth(18, 23, 16, up=True)
    c.eye(19, 10)
    c.eye(23, 9)
    return c


def phantom():
    c = Canvas(20, 26, 2)
    c.poly([(9, 3), (13, 2), (15, 6), (13, 13), (10, 18), (7, 13)], 'K')
    c.blob(13, 4, 3, 3, 'K')
    c.spikes('K', 22, 200, 80, (1, 3), 2)
    c.path([(12, 8), (16, 12), (17, 17)], 'K')
    c.claw(17, 17, 80, 3, 4)
    c.path([(9, 8), (6, 13), (6, 18)], 'j')
    c.claw(6, 18, 100, 3, 3, 'd')
    c.path([(10, 18), (9, 22)], 'K')
    c.path([(12, 17), (13, 22)], 'K')
    c.put(13, 3, 'w'); c.put(15, 3, 'w'); c.put(13, 5, 'w'); c.put(15, 5, 'w')
    c.fade(20)
    return c


def wraith():
    c = Canvas(30, 24, 3)
    c.poly([(16, 2), (22, 3), (24, 9), (21, 14), (8, 20), (2, 23), (6, 14), (12, 7)], 'K')
    c.blob(20, 6, 4, 4, 'K')
    c.blob(21, 7, 2, 2.5, 'k')
    c.eye(21, 6, False); c.eye(23, 7, False)
    c.spikes('K', 30, 160, 50, (2, 6), 3)
    c.path([(19, 11), (24, 12), (26, 13)], 'j')
    c.claw(26, 13, 20, 4, 4)
    c.fade_back(10)
    return c


def howler():
    c = Canvas(18, 28, 4)
    c.poly([(5, 2), (12, 1), (15, 6), (14, 14), (12, 21), (8, 25), (4, 16), (3, 7)], 'K')
    c.poly([(7, 9), (12, 9), (12, 19), (9, 22), (7, 18)], 'k')
    for y in range(10, 19, 2):
        c.put(7, y, 'B'); c.put(12, y, 'B')
    c.teeth(7, 12, 9)
    c.eye(7, 5); c.eye(12, 5)
    c.spikes('K', 16, 110, 60, (1, 4), 4)
    c.fade(20)
    return c


def grin():
    c = Canvas(26, 20, 5)
    c.blob(12, 10, 11, 7, 'j', 0.4)
    c.spikes('j', 30, 180, 90, (1, 5), 5)
    c.poly([(5, 10), (22, 8), (20, 13), (8, 14)], 'k')
    c.teeth(6, 21, 10)
    c.teeth(7, 20, 13, up=True)
    c.put(9, 5, 'R'); c.put(10, 5, 'r')
    c.put(17, 4, 'r'); c.put(18, 4, 'R')
    c.fade(14)
    return c


def husk_miner():
    c = Canvas(24, 26, 6)
    c.poly([(10, 6), (16, 6), (18, 12), (16, 18), (11, 20), (8, 14)], 'g')
    c.blob(15, 5, 3.5, 3, 'b')
    c.stamp(["..cCCCc..", ".cCCCCCc.", "ccccccccy"], 10, 0)
    c.put(14, 5, 'k'); c.put(17, 5, 'k'); c.put(14, 6, 'R'); c.put(17, 6, 'R')
    c.teeth(14, 18, 8)
    c.path([(16, 10), (20, 13)], 'g')
    c.path([(20, 13), (22, 9)], 'u', 1)
    c.stamp(["CCCc", "...C"], 19, 8)
    c.claw(20, 13, 60, 3, 3)
    c.spikes('g', 18, 120, 50, (2, 5), 6)
    c.fade(18)
    return c


def gaunt():
    c = Canvas(26, 26, 7)
    c.path([(6, 10), (12, 9), (17, 7)], 'j', 2)
    for i, x in enumerate(range(7, 15, 2)):
        c.path([(x, 9), (x - 1, 14 + i % 2)], 'b')
    c.path([(6, 10), (5, 15), (4, 22)], 'd')
    c.stamp(SKULL, 17, 2)
    c.teeth(20, 23, 8)
    c.path([(14, 9), (18, 13), (22, 15)], 'd')
    c.claw(22, 15, 15, 4, 4)
    c.path([(10, 10), (12, 15), (15, 18)], 'd')
    c.claw(15, 18, 40, 3, 3)
    c.spikes('j', 10, 160, 40, (2, 4), 7)
    c.fade(17)
    return c


def skull_swarm():
    c = Canvas(28, 22, 8)
    for (x, y, s) in ((1, 9, 81), (10, 2, 82), (18, 10, 83)):
        c.stamp(SKULL, x, y)
        c.teeth(x + 3, x + 6, y + 7)
        r = random.Random(s)
        px, py = x + 1, y + 4
        for k in range(6):
            px -= 1
            py += r.choice((0, 1))
            c.put(px, py, 'v')
            c.put(px, py + 1, 'V' if k < 2 else 'v')
    return c


def maw():
    c = Canvas(26, 22, 9)
    c.blob(13, 11, 11, 9, 'K', 0.3)
    c.poly([(4, 9), (23, 7), (24, 16), (6, 17)], 'o')
    c.teeth(4, 23, 8)
    c.teeth(5, 23, 16, up=True)
    c.path([(10, 13), (16, 12), (21, 13)], 'O', 2)
    for (x, y) in ((8, 3), (12, 2), (16, 3), (19, 4)):
        c.eye(x, y)
    c.spikes('K', 24, 180, 100, (1, 4), 9)
    c.fade_back(5)
    return c


def crawler():
    c = Canvas(30, 16, 10)
    c.poly([(2, 12), (12, 8), (22, 7), (25, 10), (20, 13), (8, 14)], 'K')
    c.blob(24, 8, 3.5, 3, 'K')
    c.eye(25, 8)
    c.teeth(23, 27, 10)
    for x in range(8, 21, 3):
        c.put(x, 7, 'd')
    c.path([(21, 11), (26, 13), (29, 14)], 'j')
    c.claw(28, 14, 10, 3, 2)
    c.path([(15, 12), (17, 15)], 'j')
    c.claw(17, 15, 0, 3, 2)
    c.fade_back(9)
    return c


def banshee():
    c = Canvas(26, 26, 11)
    c.poly([(14, 4), (19, 4), (20, 10), (17, 18), (10, 24), (8, 16)], 'g')
    c.blob(17, 6, 3.5, 4, 'G')
    for k in range(9):
        c.path([(15, 2 + k % 3), (6 - k % 3, 1 + k), (1, 3 + k * 2)], 'K')
    c.poly([(16, 7), (19, 7), (19, 13), (17, 12)], 'k')
    c.eye(16, 5, False); c.eye(19, 5, False)
    c.path([(19, 10), (23, 13)], 'g')
    c.claw(23, 13, 30, 4, 3)
    c.spikes('g', 14, 120, 40, (2, 5), 11)
    c.fade(18)
    return c


def hollow_king():
    c = Canvas(24, 26, 12)
    c.poly([(8, 8), (17, 8), (20, 16), (17, 24), (5, 24), (4, 15)], 'K')
    c.stamp(SKULL, 9, 3)
    c.stamp(["y.y.y.y", "yYyYyYy"], 9, 1)
    c.teeth(12, 15, 10)
    c.path([(17, 11), (21, 14)], 'K', 2)
    c.claw(21, 15, 50, 3, 3)
    c.spikes('K', 20, 100, 50, (2, 4), 12)
    c.fade(19)
    return c


def spider():
    c = Canvas(28, 22, 13)
    c.blob(14, 7, 6, 4.5, 'K', 0.2)
    c.blob(19, 6, 3, 2.5, 'K')
    c.eye(19, 5); c.eye(21, 6)
    c.teeth(18, 22, 8)
    r = random.Random(13)
    for i in range(7):
        x0 = 9 + i * 2
        knee = (x0 + r.choice((-4, -3, 3, 4)), 11 + r.randint(0, 3))
        c.path([(x0, 10), knee, (knee[0] + (1 if knee[0] > x0 else -1), 20)], 'd')
        c.put(knee[0] + (1 if knee[0] > x0 else -1), 21, 'B')
    c.spikes('K', 14, 270, 70, (1, 3), 13)
    return c


def eye_stalk():
    c = Canvas(24, 26, 14)
    c.blob(12, 9, 8, 7, 'K', 0.35)
    c.blob(13, 9, 4.5, 4, 'w')
    c.blob(14, 9, 2.4, 2.4, 'r')
    c.put(14, 9, 'k'); c.put(15, 9, 'k')
    for (a, b) in (((10, 8), (12, 7)), ((16, 11), (17, 12)), ((11, 11), (10, 12))):
        c.path([a, b], 'O')
    r = random.Random(14)
    for i in range(6):
        x = 6 + i * 2 + r.randint(0, 1)
        pts = [(x, 15)]
        for k in range(4):
            pts.append((pts[-1][0] + r.choice((-1, 0, 1)), pts[-1][1] + 2))
        c.path(pts, 'K')
        c.put(pts[-1][0], pts[-1][1] + 1, 'd')
    c.spikes('K', 16, 270, 120, (1, 3), 14)
    return c


def chained():
    c = Canvas(26, 26, 15)
    c.poly([(7, 6), (18, 5), (21, 12), (18, 20), (9, 22), (5, 14)], 'j')
    c.blob(16, 5, 4, 3.5, 'j')
    c.eye(15, 4); c.eye(18, 5)
    c.teeth(15, 19, 7)
    for (a, b) in (((6, 9), (20, 16)), ((19, 8), (6, 18))):
        c.path([a, b], 'c')
    c.blob(12, 13, 2, 2, 'r')
    c.put(12, 13, 'R')
    c.path([(19, 10), (23, 14), (24, 19)], 'C')
    c.stamp([".cc.", "cCCc", "cCCc", ".cc."], 22, 19)
    c.spikes('j', 16, 120, 50, (2, 4), 15)
    c.fade(20)
    return c


def pierced():
    c = Canvas(22, 26, 16)
    c.poly([(7, 5), (14, 4), (16, 11), (14, 19), (8, 22), (5, 13)], 'K')
    c.blob(13, 5, 3.5, 3, 'K')
    c.eye(13, 4); c.eye(16, 5)
    for (a, b) in (((2, 7), (19, 15)), ((10, 0), (11, 24)), ((18, 6), (3, 17))):
        c.line(a[0], a[1], b[0], b[1], 'C')
    c.path([(14, 10), (19, 12)], 'K')
    c.claw(19, 12, 30, 3, 3)
    c.spikes('K', 14, 120, 50, (2, 4), 16)
    c.fade(19)
    return c


def lantern_eater():
    c = Canvas(22, 26, 17)
    c.poly([(6, 6), (15, 5), (18, 12), (16, 21), (8, 23), (4, 14)], 'K')
    c.blob(14, 5, 4, 3.5, 'K')
    c.eye(14, 4); c.eye(17, 4)
    c.teeth(13, 18, 7)
    c.stamp(["cCCc", "cyYc", "cYYc", "cyYc", "cCCc"], 9, 11)
    c.path([(16, 9), (19, 14)], 'K')
    c.claw(19, 14, 60, 3, 3)
    c.spikes('K', 16, 120, 50, (2, 4), 17)
    c.fade(20)
    return c


def static():
    c = Canvas(18, 28, 18)
    c.poly([(6, 2), (12, 2), (14, 9), (13, 18), (11, 26), (6, 26), (4, 16), (4, 8)], 'N')
    r = random.Random(18)
    for y in range(c.h):
        for x in range(c.w):
            if c.g[y][x] == 'N':
                c.g[y][x] = r.choice('nNNkjN')
    for y in (5, 6):
        for x in range(5, 14):
            if c.g[y][x] != '.':
                c.g[y][x] = 'r'
    for y in (11, 17, 22):
        c.g[y] = c.g[y][3:] + ['.'] * 3
    c.path([(13, 10), (16, 14)], 'N')
    c.claw(16, 14, 70, 3, 3, 'n')
    c.fade(22)
    return c


def twin():
    c = Canvas(26, 24, 19)
    c.poly([(6, 9), (19, 8), (20, 15), (14, 22), (7, 19)], 'j')
    for (x, y) in ((6, 2), (15, 1)):
        c.stamp(SKULL, x, y)
        c.teeth(x + 3, x + 6, y + 7)
    c.path([(18, 12), (23, 14)], 'j')
    c.claw(23, 14, 30, 4, 3)
    c.spikes('j', 18, 120, 50, (2, 4), 19)
    c.fade(17)
    return c


def headless():
    c = Canvas(24, 26, 20)
    c.poly([(5, 6), (13, 5), (16, 12), (14, 20), (7, 23), (3, 14)], 'K')
    c.spikes('K', 10, 270, 30, (1, 3), 20, None)
    for k in range(4):
        c.put(9 + k % 2, 4 - k, 'o')
    c.path([(14, 8), (18, 6), (20, 3)], 'K')
    c.stamp(SKULL, 15, 0)
    c.teeth(18, 21, 7)
    c.spikes('K', 14, 120, 50, (2, 4), 21)
    c.fade(19)
    return c


def moth():
    c = Canvas(28, 20, 21)
    c.poly([(13, 7), (2, 1), (0, 8), (5, 13), (12, 11)], 'j')
    c.poly([(15, 7), (26, 1), (27, 8), (22, 13), (15, 11)], 'j')
    c.poly([(12, 11), (5, 16), (8, 19), (13, 14)], 'K')
    c.poly([(15, 11), (22, 16), (19, 19), (14, 14)], 'K')
    for (x, y) in ((6, 6), (21, 6)):
        c.stamp(["bBb", "kBk", ".d."], x - 1, y - 1)
    c.blob(13.5, 9, 1.5, 4, 'K')
    c.eye(13, 6, False); c.eye(15, 6, False)
    c.path([(13, 4), (11, 1)], 'd'); c.path([(15, 4), (17, 1)], 'd')
    c.claw(14, 12, 90, 2, 3, 'd', 40)
    return c


def jelly():
    c = Canvas(20, 28, 22)
    c.poly([(3, 9), (6, 3), (14, 2), (17, 8), (16, 10), (4, 10)], 'v')
    c.blob(10, 5, 6, 4, 'v')
    c.eye(12, 5)
    r = random.Random(22)
    for x in range(4, 17, 2):
        pts = [(x, 10)]
        for k in range(r.randint(5, 8)):
            pts.append((pts[-1][0] + r.choice((-1, 0, 0, 1)), pts[-1][1] + 2))
        c.path(pts, 'V' if x % 4 else 'v')
        c.put(pts[-1][0] + 1, pts[-1][1], 'B')
        c.put(pts[-1][0] + 1, pts[-1][1] - 1, 'B')
    return c


def weeper():
    c = Canvas(22, 26, 23)
    c.poly([(6, 6), (14, 4), (17, 11), (15, 20), (8, 23), (4, 14)], 'g')
    c.blob(14, 6, 4, 4, 'G')
    c.claw(17, 9, 250, 4, 4, 'b', 14)
    c.claw(12, 9, 290, 3, 3, 'd', 14)
    c.put(15, 6, 'R'); c.put(17, 7, 'R')
    c.spikes('g', 16, 120, 50, (2, 4), 23)
    c.fade(18)
    return c


def soul_cage():
    c = Canvas(20, 26, 24)
    c.blob(10, 6, 5, 4, 'K')
    c.stamp(SKULL, 7, 1)
    for i in range(5):
        y = 9 + i * 2
        c.path([(10, y), (4 + i % 2, y + 2)], 'b')
        c.path([(10, y), (16 - i % 2, y + 2)], 'b')
    c.line(10, 9, 10, 20, 'd')
    c.blob(10, 14, 2, 2, 'o')
    c.put(10, 14, 'R'); c.put(9, 14, 'r')
    c.spikes('K', 12, 90, 60, (2, 5), 24)
    c.fade(19)
    return c


def leech():
    c = Canvas(30, 18, 25)
    pts = [(2, 14), (6, 12), (10, 13), (14, 10), (18, 9), (22, 7)]
    for (x, y), r in zip(pts, (1.2, 1.6, 2, 2.4, 2.8, 3.2)):
        c.blob(x, y, r + 0.5, r, 'j')
    c.blob(24, 6, 4.5, 4.5, 'j')
    c.blob(25, 6, 3, 3, 'o')
    c.blob(25.5, 6, 1.5, 1.5, 'k')
    for a in range(0, 360, 40):
        c.put(25 + math.cos(math.radians(a)) * 3, 6 + math.sin(math.radians(a)) * 3, 'B')
    c.put(21, 3, 'R')
    c.fade_back(10)
    return c


def grasp():
    c = Canvas(30, 20, 26)
    c.poly([(0, 19), (3, 13), (12, 11), (24, 12), (29, 16), (29, 19)], 'K')
    r = random.Random(26)
    for x in (4, 10, 17, 23):
        top = r.randint(2, 6)
        c.path([(x, 13), (x + 1, top + 3)], 'd')
        c.claw(x + 1, top + 3, 260 + r.randint(-20, 20), 3, 3, 'b', 25, -10)
    for (x, y) in ((7, 15), (13, 14), (20, 15), (26, 16)):
        c.put(x, y, 'R')
    c.fade(17)
    return c


def coffin():
    c = Canvas(26, 22, 27)
    c.poly([(4, 3), (16, 2), (18, 8), (16, 20), (6, 21), (3, 9)], 'u')
    c.poly([(6, 5), (15, 4), (16, 9), (14, 18), (8, 19), (5, 10)], 'k')
    c.eye(9, 8); c.eye(12, 8)
    c.teeth(9, 13, 11)
    c.path([(16, 8), (20, 6), (23, 4)], 'd')
    c.claw(23, 4, -10, 4, 3)
    c.path([(16, 13), (20, 15), (23, 16)], 'd')
    c.claw(23, 16, 20, 4, 3)
    return c


def spine():
    c = Canvas(30, 18, 28)
    c.stamp(SKULL, 22, 2)
    c.teeth(25, 28, 9)
    c.stamp(["d.....d", ".d...d.", "..d.d.."], 22, 0)
    pts = [(22, 8), (18, 9), (14, 11), (10, 12), (6, 12), (3, 14)]
    for k, (x, y) in enumerate(pts):
        c.stamp(["bB", "dd"], x - 1, y)
        c.put(x, y - 1, 'd')
        c.put(x - 1, y + 2, 'd')
    c.put(1, 16, 'v'); c.put(0, 17, 'v')
    return c


def prospector():
    c = Canvas(26, 24, 29)
    c.stamp(["....cCCCCc......",
             "..cCCCCCCCCc.y...",
             ".cccccccccccccYY."], 4, 0)
    c.blob(10, 9, 7, 6, 'b')
    c.poly([(5, 7), (8, 7), (8, 10), (5, 10)], 'k')
    c.poly([(11, 7), (14, 7), (14, 10), (11, 10)], 'k')
    c.put(6, 8, 'y'); c.put(12, 8, 'y')
    c.poly([(5, 12), (16, 12), (15, 16), (6, 16)], 'k')
    c.teeth(5, 16, 12, ch='Y')
    c.teeth(6, 15, 15, up=True)
    c.path([(16, 14), (21, 16)], 'd')
    c.claw(21, 16, 30, 4, 3)
    c.stamp([".vv.vv.", "v..v..v"], 6, 17)
    return c


def echo():
    c = Canvas(26, 26, 30)
    c.stamp(["......h........",
             "....hjjjh.......",
             "..hjjjjjjjh.....",
             "hhhhhhhhhhhhhh.."], 3, 1)
    c.poly([(7, 5), (14, 5), (16, 12), (15, 20), (8, 22), (5, 13)], 'K')
    c.blob(11, 6, 2.5, 1.5, 'k')
    c.put(12, 6, 'R')
    c.path([(15, 9), (20, 5), (24, 1)], 'd')
    c.stamp([".r.", "r.r"], 23, 0)
    c.path([(14, 11), (19, 13)], 'K')
    c.claw(19, 13, 20, 4, 4)
    c.spikes('K', 20, 120, 60, (2, 5), 30)
    c.fade(19)
    return c


GHOSTS = [
    ("SHADE", shade_, "BRISTLES, A MAW"),
    ("PHANTOM", phantom, "ARMS TO THE KNEE"),
    ("WRAITH", wraith, "REACHES FIRST"),
    ("HOWLER", howler, "JAW TO THE CHEST"),
    ("GRIN", grin, "TEETH IN SMOKE"),
    ("HUSK", husk_miner, "MINER, STILL DIGS"),
    ("GAUNT", gaunt, "RIBS AND HOOKS"),
    ("SKULLS", skull_swarm, "THEY BITE"),
    ("MAW", maw, "EYES OVER A MOUTH"),
    ("CRAWLER", crawler, "LOW AND FAST"),
    ("BANSHEE", banshee, "HAIR IN THE WIND"),
    ("HOLLOW KING", hollow_king, "GOLD STILL ON"),
    ("WEAVER", spider, "BONE LEGS"),
    ("WATCHER", eye_stalk, "ONE BLOODSHOT EYE"),
    ("CHAINED", chained, "SWINGS ITS WEIGHT"),
    ("PIERCED", pierced, "NAILED, NOT DEAD"),
    ("GLUTTON", lantern_eater, "ATE THE LANTERN"),
    ("STATIC", static, "LAB SIGNAL"),
    ("TWIN", twin, "TWO SKULLS, ONE HUNGER"),
    ("HEADLESS", headless, "CARRIES ITS SKULL"),
    ("MOTH", moth, "SKULLS ON WINGS"),
    ("STINGER", jelly, "HOOKED STRANDS"),
    ("WEEPER", weeper, "PEEKS THROUGH"),
    ("SOUL CAGE", soul_cage, "HEART BEHIND RIBS"),
    ("LEECH", leech, "RING OF TEETH"),
    ("GRASP", grasp, "HANDS FROM THE FLOOR"),
    ("COFFIN", coffin, "LID WON'T HOLD"),
    ("SPINE", spine, "HORNED, HUNTING"),
    ("PROSPECTOR", prospector, "GOLD TEETH"),
    ("ECHO", echo, "A PILGRIM BEFORE"),
]


# ──────────────────────────────────────────────────────────────── render ──
# Cold rim on the lit (top / left) edge of the dark bodies, so a near-black ghost still
# cuts a silhouette against near-black rock.
VOID = set('kKjJgvVom')
RIM = (118, 108, 140)


def shade_px(g):
    """The cast's light, pushed harder for ghosts: a cold rim on the top edge, the
    underside sunk, a sparse dither through the lower half. Lights stay flat."""
    h, w = len(g), len(g[0])
    out = []

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and g[y][x] != '.'

    def mul(c, k):
        return tuple(max(0, min(255, int(v * k))) for v in c)

    for y in range(h):
        row = []
        for x in range(w):
            ch = g[y][x]
            if ch == '.':
                row.append(None)
                continue
            c = PAL[ch]
            if ch not in GLOWING:
                if ch in VOID and (not solid(x, y - 1) or not solid(x - 1, y)):
                    c = tuple((a + b) // 2 for a, b in zip(c, RIM))
                elif not solid(x, y - 1):
                    c = mul(c, 1.12)
                elif not solid(x, y + 1) or not solid(x + 1, y):
                    c = mul(c, 0.8)
                elif y > h // 2 and BAYER[y % 4][x % 4] < 3:
                    c = mul(c, 0.85)
            row.append(c)
        out.append(row)
    return out


def main():
    cols, cell, gap, top = 6, 100, 4, 22
    made = [(name, fn().g, note) for name, fn, note in GHOSTS]
    rows = (len(made) + cols - 1) // cols
    new_canvas(cols * (cell + gap) + gap, top + rows * (cell + 18) + 4, seed=5)
    W, H = canvas_size()
    for y in range(H):
        for x in range(W):
            if rnd() < 0.08:
                px(x, y, CAVE)

    for n, (name, g, note) in enumerate(made):
        x0 = gap + (n % cols) * (cell + gap)
        y0 = top + (n // cols) * (cell + 18)
        rect(x0, y0, x0 + cell - 1, y0 + cell - 1, ROCK)
        frame(x0, y0, x0 + cell - 1, y0 + cell - 1, (58, 66, 76))
        pix = shade_px(g)
        h, w = len(pix), len(pix[0])
        s = 3
        sx = x0 + (cell - w * s) // 2
        sy = y0 + 4 + (cell - 10 - h * s) // 2
        for j, row in enumerate(pix):
            for i, c in enumerate(row):
                if c and g[j][i] in 'rR':
                    glow(sx + i * s + 1, sy + j * s + 1, 7, PAL['r'], 0.14)
                elif c and g[j][i] in 'yY':
                    glow(sx + i * s + 1, sy + j * s + 1, 8, PAL['y'], 0.10)
        for j, row in enumerate(pix):
            for i, c in enumerate(row):
                if c:
                    rect(sx + i * s, sy + j * s, sx + i * s + s - 1, sy + j * s + s - 1, c)
        tag(x0 + 3, y0 + 3, "%02d" % (n + 1), PALE_G)
        dims = "%dX%d" % (w, h)
        text(x0 + cell - 3 - text_w(dims), y0 + cell - 8, dims, (90, 100, 115), shadow=False)
        text(x0 + 1, y0 + cell + 3, name, LABEL)
        text(x0 + 1, y0 + cell + 10, note, (150, 160, 172))

    title_bar("GHOSTS - 30 CONCEPTS", "AFTER NOITA / NATIVE PX, SHOWN 3X")
    save(os.path.join(CHARS, "GhostConcepts.png"), scale=3)


if __name__ == "__main__":
    main()
