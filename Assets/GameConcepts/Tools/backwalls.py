"""Back walls: what is drawn behind a room's terrain, the way Starbound and Terraria put a
wall layer behind their blocks. Nothing collides with it - in game it is a TerrainBackdrop,
the room's back map stamped into the floor's (Rooms/FloorBuilder.cs) and drawn darkened
behind the terrain.

    python Assets/GameConcepts/Tools/backwalls.py tiles                    # the wall tiles
    python Assets/GameConcepts/Tools/backwalls.py small_44_bunkhouse       # one room
    python Assets/GameConcepts/Tools/backwalls.py --force small_44_bunkhouse

`tiles` draws the wall materials into Resources/Sprites/Materials/back_*.png, two cells a
pixel like the props (a 20-PPU sprite pixel is two terrain cells):

* back_planks - upright boards, the WallPlank prop's boards with staggered end joints;
* back_boards - boards laid flat, for wainscot under a rail;
* back_beam / back_post - a timber's grain lengthwise / upright, with no edges of its own,
  so a beam of any size cut from it lines up; the edges are back_shadow lines drawn round it;
* back_shadow - the dark of timber in shadow: outlines, gaps, the line under a rail.

A room writes Rooms/Maps/<Name>_Back.asset, the same size and origin as its map, and points
the Room in Room_<Name>.prefab at it. Every cell of the room that is not fill gets the
room's own rock (`ROCK`), so the cave has a cave behind it; then the room's roombuild
module, if it has `backwall(b, mod)`, draws its walls over that with the Brush below, in the
sheet's room coords (x right, y down, one sheet pixel = 2x2 cells). The map is left alone
when it exists, unless --force: like a room, a back wall may be finished by hand.
"""
import importlib
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixelfix import write_png  # noqa: E402
import export_rooms as X  # noqa: E402

MATERIALS = os.path.join(X.ASSETS, "Resources", "Sprites", "Materials")
FILL = "rock_hard"
ROCK = "rock"

TIM_D, TIM, TIM_M, TIM_L = (58, 46, 35), (96, 76, 54), (120, 97, 68), (149, 134, 101)
NAIL = (89, 97, 100)
BEAM_D, BEAM, BEAM_L = (86, 62, 42), (112, 82, 55), (136, 104, 70)
SHADOW, SHADOW_D = (40, 32, 25), (30, 24, 19)


# ─────────────────────────────────────────────────────────────────────────────
#  Tiles
# ─────────────────────────────────────────────────────────────────────────────
def save_tile(name, art):
    """`art` is rows of RGB at sprite scale; written x2, so a pixel is 2x2 cells."""
    rows = []
    for r in art:
        row = []
        for c in r:
            row += [tuple(c) + (255,)] * 2
        rows += [row, list(row)]
    path = os.path.join(MATERIALS, name + ".png")
    write_png(path, rows)
    print("  wrote", os.path.relpath(path, X.ASSETS))


def grid(w, h, c):
    return [[c] * w for _ in range(h)]


def planks():
    """Four upright boards, 6 wide like the WallPlank prop: lit edge, face with a dithered
    grain, a dark gap; each board has its end joint at another height, nailed."""
    W, H = 24, 36
    a = grid(W, H, TIM)
    rnd = random.Random(31)
    for b in range(4):
        x0 = b * 6
        joint = (b * 13 + 5) % H
        for y in range(H):
            a[y][x0] = TIM_M
            for x in range(x0 + 1, x0 + 5):
                a[y][x] = TIM if (x + y // 3) % 4 else TIM_M
            a[y][x0 + 5] = TIM_D
        for x in range(x0 + 1, x0 + 5):                  # a streak of darker grain
            if rnd.random() < 0.5:
                y = rnd.randrange(H)
                for k in range(rnd.randint(3, 7)):
                    a[(y + k) % H][x] = TIM_D if k % 3 == 0 else a[(y + k) % H][x]
        for x in range(x0, x0 + 6):
            a[joint][x] = TIM_D
            a[(joint + 1) % H][x] = TIM_M if x < x0 + 5 else TIM_D
        a[(joint - 2) % H][x0 + 2] = NAIL
        a[(joint + 2) % H][x0 + 3] = NAIL
    return a


def boards():
    """Boards laid flat, 4 high: lit top, face, dark underside, staggered butt joints."""
    W, H = 36, 16
    a = grid(W, H, TIM)
    for b in range(4):
        y0 = b * 4
        joint = (b * 17 + 9) % W
        for x in range(W):
            a[y0][x] = TIM_M
            a[y0 + 1][x] = TIM if (x // 3 + b) % 5 else TIM_M
            a[y0 + 2][x] = TIM
            a[y0 + 3][x] = TIM_D
        for y in range(y0, y0 + 4):
            a[y][joint] = TIM_D
        a[y0 + 1][(joint + 2) % W] = NAIL
    return a


def beam(upright):
    """Squared timber: grain along its length, no edges of its own."""
    L, T = 24, 8
    rnd = random.Random(57 if upright else 53)
    a = grid(L, T, BEAM)
    for t in range(T):
        for l in range(L):
            a[t][l] = BEAM if (l // 4 + t * 3) % 7 else BEAM_L
    for _ in range(9):                                   # long streaks of grain
        t, l = rnd.randrange(T), rnd.randrange(L)
        for k in range(rnd.randint(4, 10)):
            a[t][(l + k) % L] = BEAM_D
    a[rnd.randrange(T)][rnd.randrange(L)] = SHADOW       # a knot
    if upright:
        a = [[a[t][l] for t in range(T)] for l in range(L)]
    return a


def shadow():
    a = grid(4, 4, SHADOW)
    a[1][2] = a[3][0] = SHADOW_D
    return a


def write_tiles():
    save_tile("back_planks", planks())
    save_tile("back_boards", boards())
    save_tile("back_beam", beam(False))
    save_tile("back_post", beam(True))
    save_tile("back_shadow", shadow())


# ─────────────────────────────────────────────────────────────────────────────
#  A room's back map
# ─────────────────────────────────────────────────────────────────────────────
class Brush:
    """Draws into a back map in sheet room coords: x right, y down, a sheet pixel 2x2 cells.
    Tiles are named as in Resources/Sprites/Materials; a tile's palette entry is made the
    first time it is used."""

    def __init__(self, w, h):
        self.W, self.H = w, h                            # cells
        self.cells = bytearray(w * h)
        self.tiles = []

    def index(self, tile):
        if tile is None:
            return 0
        if tile not in self.tiles:
            self.tiles.append(tile)
        return self.tiles.index(tile) + 1

    def px(self, x, y, tile):
        """One sheet pixel."""
        v = self.index(tile)
        x, y = int(x), int(y)
        for j in range(2):
            cy = self.H - 1 - (2 * y + j)
            if not 0 <= cy < self.H:
                continue
            for i in range(2):
                cx = 2 * x + i
                if 0 <= cx < self.W:
                    self.cells[cy * self.W + cx] = v

    def rect(self, x0, y0, x1, y1, tile):
        """Sheet pixels x0..x1, y0..y1, ends included."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, tile)

    def beam(self, x0, y0, x1, y1, edge="back_shadow"):
        """A timber across x0..x1 by y0..y1 with a dark line round it. Lengthwise grain if it
        is wider than tall, upright if not."""
        self.rect(x0, y0, x1, y1, edge)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1,
                  "back_beam" if x1 - x0 >= y1 - y0 else "back_post")

    def span(self, x, y0, y1, tile):
        for y in range(int(y0), int(y1) + 1):
            self.px(x, y, tile)

    # ── pieces a built room's wall is made of ──────────────────────────────
    def wainscot(self, x0, x1, floor, h=15):
        """Boards laid flat from the floor up `h`, under a rail."""
        self.rect(x0, floor - h, x1, floor - 1, "back_boards")
        self.beam(x0, floor - h - 4, x1, floor - h)

    def window(self, x0, y0, x1, y1, behind="rock"):
        """A window onto whatever is behind the wall (the cave): a timber frame round the
        opening x0..x1 by y0..y1, a cross, and the sill's shadow under it."""
        self.beam(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
        self.rect(x0, y0, x1, y1, behind)
        mx, my = (x0 + x1) // 2, (y0 + y1) // 2
        self.rect(mx, y0, mx + 1, y1, "back_post")
        self.rect(x0, my, x1, my + 1, "back_beam")
        self.rect(x0, y1 + 3, x1, y1 + 3, "back_shadow")

    def under_roof(self, x0, x1, top_at, bottom, tile="back_planks"):
        """Fill x0..x1 from the roof's underside, top_at(x), down to `bottom`."""
        for x in range(int(x0), int(x1) + 1):
            self.span(x, top_at(x), bottom, tile)

    def timber_set(self, x0, x1, floor, h):
        """A mine's support set against the rock: two legs and a cap."""
        self.beam(x0, floor - h, x0 + 4, floor - 1)
        self.beam(x1 - 4, floor - h, x1, floor - 1)
        self.beam(x0 - 3, floor - h - 5, x1 + 3, floor - h)


def read_map(path):
    t = open(path, encoding="utf-8").read()
    W = int(re.search(r"\n  width: (\d+)", t).group(1))
    H = int(re.search(r"\n  height: (\d+)", t).group(1))
    tiles = re.findall(r"- tile: (\S+)", t)
    data = bytes.fromhex(re.search(r"encoded: ([0-9a-f]*)", t).group(1))
    cells = bytearray()
    for i in range(0, len(data), 3):
        cells += bytes([data[i]]) * (data[i + 1] | data[i + 2] << 8)
    return W, H, tiles, cells


def map_asset(name, b):
    palette = "".join("  - tile: %s\n    physMaterial: 0\n" % t for t in b.tiles)
    return f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {X.G_MAP}, type: 3}}
  m_Name: {name}_Back
  m_EditorClassIdentifier: Assembly-CSharp::Phys.Terrain.TerrainMap
  pixelsPerUnit: {X.PPU}
  origin: {{x: 0, y: 0}}
  width: {b.W}
  height: {b.H}
  palette:
{palette}  encoded: {X.encode(b.cells)}
"""


META = """fileFormatVersion: 2
guid: {guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 11400000
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def link_prefab(name, guid):
    """Point the prefab's Room at the back map: its `_backMap` line, after `_map`."""
    path = os.path.join(X.OUT, "Room_" + name + ".prefab")
    t = open(path, encoding="utf-8").read()
    ref = "  _backMap: {fileID: 11400000, guid: %s, type: 2}\n" % guid
    if re.search(r"\n  _backMap: .*\n", t):
        t2 = re.sub(r"\n  _backMap: .*\n", "\n" + ref, t, count=1)
    else:
        t2 = re.sub(r"(\n  _map: \{fileID: 11400000, guid: \w+, type: 2\}\n)", r"\1" + ref.replace("\\", "\\\\"), t, count=1)
    if t2 == t and "_backMap: {fileID: 11400000, guid: %s" % guid not in t:
        raise SystemExit("Room_%s.prefab: no `_map:` line to put the back map after" % name)
    if t2 != t:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(t2)
        print("  linked", os.path.relpath(path, X.ASSETS))


def build_room(sheet, force):
    mod = importlib.import_module("levels." + sheet)
    name = X.slug(mod)
    print(sheet, "->", name)
    W, H, tiles, fore = read_map(os.path.join(X.OUT, "Maps", name + "_Map.asset"))
    b = Brush(W, H)

    # The cave: the room's rock behind everything that is not the fill round it.
    rock = b.index(ROCK)
    fill = tiles.index(FILL) + 1 if FILL in tiles else -1
    for i, v in enumerate(fore):
        if v != fill:
            b.cells[i] = rock

    rb = X.room_module(mod)
    if rb and hasattr(rb, "backwall"):
        rb.backwall(b, mod)
    else:
        print("  (roombuild has no backwall(): the cave only)")

    asset = os.path.join(X.OUT, "Maps", name + "_Back.asset")
    meta = asset + ".meta"
    if os.path.exists(asset) and not force:
        print("  kept", os.path.relpath(asset, X.ASSETS), "(--force to redraw)")
    else:
        with open(asset, "w", encoding="utf-8", newline="\n") as f:     # the asset before its meta
            f.write(map_asset(name, b))
        print("  wrote", os.path.relpath(asset, X.ASSETS))
    if os.path.exists(meta):
        guid = open(meta).read().split("guid: ")[1].split()[0]           # Unity's, if it has one
    else:
        guid = X.guid(name + "_Back.asset")
        with open(meta, "w", encoding="utf-8", newline="\n") as f:
            f.write(META.format(guid=guid))
        print("  wrote", os.path.relpath(meta, X.ASSETS))
    link_prefab(name, guid)
    return name


def main(argv):
    force = "--force" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return
    for a in args:
        if a == "tiles":
            write_tiles()
        else:
            build_room(a, force)


if __name__ == "__main__":
    main(sys.argv)
