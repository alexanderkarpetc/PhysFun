"""The fungal deep: what the mushroom rooms (S47 on) are drawn with, on top of housekit.

A fungal room is a small room like any other (smallroomkit), with three differences:

* **Its props are the game's own art.** `prop()` and `hang()` paste the prop's sprite from
  `Sprites/Props/Rooms` (roomprops_fungal, roomprops_flora, the hung and loose parts) onto
  the sheet at game scale, and the same calls are `PROP_HOOKS` for `export_rooms.py`, so the
  prefab instance lands exactly where the sheet shows it - a hung one on a Hazards/Rope
  from the roof to its Eye. `bracket()` is a shelf-fungus deck (one-way, static) grown out
  of a wall; `sprinkle()` strews flora props along a floor.
* **Giant mushrooms are terrain.** `giant_shroom()` is a stem of `stem` and a cap of `cap`
  (fungaltiles; both burn like wood). The cap stands on nothing but its stem, so burn or
  blow the stem and the support pass drops the cap on whoever is under it - the fungal
  rooms' boulder. `myc_mound()` is a heap of `mycel`. Both are recorded on the sheet pass
  and written into the map by `terrain_extras` (export_rooms calls it).
* **Its rock is fungal.** `TILES` swaps the room's rock and fill for fungal_rock and
  fungal_hard, `BACK_ROCK` puts back_mycelium behind the cave, and `fungal_sheet()` repaints
  the sheet's rock in the same colours so the concept reads as the biome it is.

A room sheet does `from fungalkit import *` and sets `TILES`, `BACK_ROCK`, `PROP_HOOKS` and
`terrain_extras` from here (the star import brings them).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from housekit import *  # noqa: F403,E402
import png as _png  # noqa: E402
import conceptkit as _ck  # noqa: E402

PROPS = os.path.abspath(os.path.join(HERE, "..", "..", "Sprites", "Props", "Rooms"))

TILES = {"rock": ("fungal_rock", 0), "fill": ("fungal_hard", 0)}
BACK_ROCK = "back_mycelium"

# sheet colours of the biome (the concept's rock is repainted in these)
F_ROCK, F_ROCK_D, F_ROCK_M, F_ROCK_L = (58, 46, 62), (40, 31, 44), (72, 58, 76), (98, 80, 104)
F_FILL, F_FILL_D, F_FILL_M, F_FILL_L = (36, 30, 40), (26, 22, 30), (46, 38, 50), (64, 54, 70)
CAP_C, CAP_L, CAP_D = (116, 80, 96), (150, 112, 124), (82, 54, 70)
GILL = (44, 36, 32)
GLOWCAP, GLOWCAP_L = (70, 140, 150), (140, 214, 210)
STEEL_C, STEEL_L, STEEL_D = (96, 104, 110), (150, 158, 160), (58, 62, 68)
BRICK_C, BRICK_L, BRICK_D = (120, 82, 60), (156, 112, 80), (78, 52, 40)
STEM_C, STEM_L, STEM_D = (148, 140, 116), (178, 170, 142), (118, 110, 92)
MYC_C, MYC_L = (60, 48, 44), (138, 132, 116)
TINDER, TINDER_L = (112, 98, 70), (156, 140, 100)
GLOW_V, GLOW_C = (170, 130, 220), (120, 210, 214)

_RECOLOR = {ROCK: F_ROCK, ROCK_D: F_ROCK_D, ROCK_M: F_ROCK_M, ROCK_L: F_ROCK_L}

# Eye of every hung prop, pixels from its top-left (the parts' ANCHORS)
_EYES = {}
for _part in ("roomprops_fungal", "roomprops_hung"):
    try:
        _EYES.update({k: v["Eye"] for k, v in __import__(_part).ANCHORS.items() if "Eye" in v})
    except Exception:  # noqa: BLE001 - a part that will not import just has no hung props here
        pass

_cache = {}
_terrain = []          # ("shroom", cx, floor, h, r, lean) / ("mound", cx, floor, rx, ry), sheet coords


def _img(name):
    if name not in _cache:
        _cache[name] = _png.load(os.path.join(PROPS, name + ".png"))
    return _cache[name]


def _paste(name, x0, y0):
    w, h, pix = _img(name)
    for j in range(h):
        for i in range(w):
            p = pix[j][i]
            if len(p) == 4 and p[3] < 128:
                continue
            px(x0 + i, y0 + j, p[:3])


def size(name):
    w, h, _ = _img(name)
    return w, h


# ─────────────────────────────────────────────────────────────────────────────
#  Props
# ─────────────────────────────────────────────────────────────────────────────
def prop(name, cx, y, at="floor"):
    """A prop's sprite centred on cx: standing on `y` (at="floor"), hanging from it
    ("ceil"), or centred on it ("centre")."""
    w, h = size(name)
    x0 = int(round(cx - w / 2.0))
    y0 = {"floor": y - h, "ceil": y, "centre": int(round(y - h / 2.0))}[at]
    _paste(name, x0, y0)


def hang(name, cx, roof, drop):
    """A hung prop on a rope from the roof at (cx, roof), its Eye `drop` below it."""
    ex, ey = _EYES.get(name, (size(name)[0] / 2.0, 0))
    rope([(cx, roof), (cx, roof + drop)])
    _paste(name, int(round(cx - ex)), int(round(roof + drop - ey)))


def bracket(x, y, side="L", glow=False):
    """A shelf-fungus deck grown out of a wall: its top (the floor) at y, its wall end at
    x - on the left of it for side "L", on the right for "R"."""
    name = "BracketDeck" + ("Glow" if glow else "") + ("R" if side == "R" else "")
    w, _ = size(name)
    _paste(name, x if side == "L" else x - w + 1, y)


FLOOR_GROWTH = ("GlowCaps", "FungalMoss", "GlowSpindles", "Toadstool", "PaleSprouts", "GlowBell",
                "InkCap", "ToadstoolCluster", "MossTuft", "CoralFungus", "Puffballs")


def sprinkle(m, x0, x1, y_ref, n, kinds=FLOOR_GROWTH, gap=10):
    """Up to n flora props along the floor under y_ref between x0 and x1, each where the
    floor under its whole width is flat and nothing else stands."""
    placed = []
    tries = 0
    while len(placed) < n and tries < n * 8:
        tries += 1
        name = pick(kinds)
        w, h = size(name)
        cx = int(x0 + rnd() * (x1 - x0))
        fy = floor_at(m, cx, y_ref)
        if any(abs(floor_at(m, cx + d, y_ref) - fy) > 1 for d in (-w // 2 + 1, w // 2 - 1)):
            continue
        if any((cx + dx, fy - h - 1 + dy) not in m for dx in (-w // 2, 0, w // 2) for dy in (0, h // 2)):
            continue
        if any(abs(cx - p) < gap for p in placed):
            continue
        prop(name, cx, fy)
        placed.append(cx)


# ─────────────────────────────────────────────────────────────────────────────
#  Terrain: giant mushrooms and mycelium heaps
# ─────────────────────────────────────────────────────────────────────────────
def _shroom_cells(cx, floor, h, r, lean=0):
    """(stem cells, cap cells) of a giant mushroom, sheet coords."""
    stem_c, cap_c = set(), set()
    top = floor - h
    for y in range(top, floor):
        t = (floor - y) / float(h)
        x = cx + lean * t * t
        hw = 3 + (2 if y > floor - 6 else 0) + (1 if y > floor - 3 else 0)
        for xx in range(int(x - hw), int(x + hw) + 1):
            stem_c.add((xx, y))
    capx = cx + lean
    for y in range(int(top - r * 0.55), top + 3):
        for x in range(int(capx - r) - 1, int(capx + r) + 2):
            dx, dy = (x - capx) / r, (y - top - 2) / (r * 0.55)
            if dy <= 0 and dx * dx + dy * dy <= 1.0:
                cap_c.add((x, y))
            elif 0 < dy and y <= top + 2 and abs(dx) <= 1.0:
                cap_c.add((x, y))
    return stem_c - cap_c, cap_c


def giant_shroom(cx, floor, h, r, lean=0, cap="cap"):
    """A giant mushroom grown out of the floor at cx: a stem h tall (leaning `lean` px by
    its top) under a cap r wide each way. Terrain - see the module doc. cap="glowcap" is
    the glowing kind (its light is props: GillGlow under it)."""
    _terrain.append(("shroom", cx, floor, h, r, lean, cap))
    stem_c, cap_c = _shroom_cells(cx, floor, h, r, lean)
    for (x, y) in stem_c:
        px(x, y, STEM_L if (x - cx - lean) < -1 else STEM_D if (x - cx - lean) > 2 else STEM_C)
    top = floor - h
    lit, base = (GLOWCAP_L, GLOWCAP) if cap == "glowcap" else (CAP_L, CAP_C)
    for (x, y) in cap_c:
        px(x, y, lit if y < top - r * 0.3 else base)
    for x in range(int(cx + lean - r) + 1, int(cx + lean + r)):
        if x % 2 == 0:
            px(x, top + 2, CAP_D)
    for k in range(int(r * 0.5)):                              # pale spots
        a = rnd() * math.pi
        px(cx + lean + math.cos(a) * r * 0.7 * rnd(), top - 1 - math.sin(a) * r * 0.4 * rnd(), STEM_L)


def _hanging_shroom_cells(cx, roof, h, r):
    """(stem, cap) cells of a mushroom grown down from the roof: the stem from `roof` down
    to roof + h, the cap a bowl hung on its end - flat on top (a floor), round underneath."""
    stem_c, cap_c = set(), set()
    top = roof + h
    for y in range(int(roof) - 2, top):
        hw = 3 + (2 if y < roof + 5 else 0)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            stem_c.add((x, y))
    depth = r * 0.5
    for y in range(top, int(top + depth) + 1):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = (x - cx) / r, (y - top) / depth
            if dx * dx + dy * dy <= 1.0:
                cap_c.add((x, y))
    return stem_c - cap_c, cap_c


def hanging_shroom(cx, roof, h, r):
    """A giant mushroom grown down out of the roof: its cap hangs h below, flat side up -
    a floor to build on, over whatever is below it. It hangs on its stem alone; burn that
    and the cap comes down with everything on it. Terrain, like giant_shroom."""
    _terrain.append(("hanging", cx, roof, h, r))
    stem_c, cap_c = _hanging_shroom_cells(cx, roof, h, r)
    for (x, y) in stem_c:
        px(x, y, STEM_L if (x - cx) < -1 else STEM_D if (x - cx) > 2 else STEM_C)
    top = roof + h
    for (x, y) in cap_c:
        px(x, y, CAP_L if y == top else CAP_C if y < top + r * 0.3 else CAP_D)
    for x in range(int(cx - r) + 2, int(cx + r) - 1, 3):
        px(x, top + int(r * 0.5) - 1 - abs(x - cx) // 12, GILL)


def hanging_top(roof, h):
    """The floor line on a hanging_shroom's cap: stand things on this."""
    return roof + h


def _grown_house_cells(x0, x1, floor, h, ridge, doors, windows, wall=4, roof=4, shed=None):
    """(wall cells, roof cells, inside cells) of a house grown rather than built: walls of
    stem `wall` thick from the floor up h, a roof of cap `roof` thick over them - pitched
    to a ridge `ridge` high, or a lean-to when shed="L"/"R" names its high side. `doors` =
    "L"/"R" walls with a doorway (30 high) at the foot; `windows` = [(side, y top, y bottom)]."""
    walls, roofc, inside = set(), set(), set()
    eave = floor - h
    for x in range(x0, x1 + 1):
        for y in range(eave, floor):
            if x < x0 + wall or x > x1 - wall:
                side = "L" if x < x0 + wall else "R"
                if side in doors and y >= floor - 30:
                    continue
                if any(ws == side and wy0 <= y <= wy1 for ws, wy0, wy1 in windows):
                    continue
                walls.add((x, y))
            else:
                inside.add((x, y))
    cx, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0 + 3
    for x in range(x0 - 3, x1 + 4):
        if shed == "L":
            top = eave - ridge * (x1 + 3 - x) / float(x1 - x0 + 6)
        elif shed == "R":
            top = eave - ridge * (x - x0 + 3) / float(x1 - x0 + 6)
        else:
            top = eave - ridge * max(0.0, 1 - abs(x - cx) / half)
        for k in range(roof):
            roofc.add((x, int(round(top)) + k))
        if x0 + wall <= x <= x1 - wall:                       # the attic air under the roof
            for y in range(int(round(top)) + roof, eave):
                inside.add((x, y))
    return walls, roofc - walls, inside - walls - roofc


def grown_house(x0, x1, floor, h, ridge, doors=("L", "R"), windows=(), shed=None):
    """A house of the cult's grown out of stem and cap: walls, doorways, windows and a
    roof, all terrain - it burns, it can be dug through, and it stands on whatever it was
    grown on (a hanging cap, a ledge) and comes down with it. No doors to open: its
    doorways are arches."""
    _terrain.append(("house", x0, x1, floor, h, ridge, tuple(doors), tuple(windows), shed))
    walls, roofc, inside = _grown_house_cells(x0, x1, floor, h, ridge, doors, windows, shed=shed)
    for (x, y) in inside:
        px(x, y, (70, 58, 96), 0.14)
    for (x, y) in walls:
        px(x, y, STEM_L if (x - x0) % 4 == 0 else STEM_D if y % 12 == 0 else STEM_C)
    for (x, y) in roofc:
        px(x, y, CAP_L if (x, y - 1) not in roofc else CAP_D if (x, y + 1) not in roofc else CAP_C)


def slab(x0, y0, x1, y1, mat="stem"):
    """A block of terrain: a stilt, a floor slab, a beam - stem by default (burns); "steel"
    for a beam nothing digs, "brick" for masonry a blast will open."""
    _terrain.append(("slab", x0, y0, x1, y1, mat))
    c, lit, dark = {"stem": (STEM_C, STEM_L, STEM_D), "steel": (STEEL_C, STEEL_L, STEEL_D),
                    "brick": (BRICK_C, BRICK_L, BRICK_D)}.get(mat, (CAP_C, CAP_L, CAP_D))
    rect(x0, y0, x1, y1, c)
    rect(x0, y0, x1, y0, lit)
    rect(x0, y0, x0, y1, lit)
    rect(x1, y0, x1, y1, dark)


def _living_cells(cx, floor, hw, h, r):
    """(stem, cap) cells of a living mushroom: a stem 2*hw wide, flaring at its foot."""
    stem_c, cap_c = set(), set()
    top = floor - h
    for y in range(top, floor):
        flare = max(0, 10 - (floor - y)) * 0.8
        for x in range(int(cx - hw - flare), int(cx + hw + flare) + 1):
            stem_c.add((x, y))
    ry = r * 0.55
    for y in range(int(top - ry), top + 8):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = (x - cx) / r, (y - top - 2) / ry
            if (dy <= 0 and dx * dx + dy * dy <= 1.0) or (0 < dy and y <= top + 7 and abs(dx) <= 1.0 - 0.15 * (y - top)):
                cap_c.add((x, y))
    return stem_c - cap_c, cap_c


def living_shroom(cx, floor, hw, h, r, holes):
    """A mushroom big enough to live in, the way Terraria's living trees are: a stem of
    terrain 2*hw wide and a cap of r, with `holes` = [(x0, y0, x1, y1)] carved out of them -
    rooms, the shafts and hatches between them, windows, a door at the foot. Its walls and
    floors are what is left: stem and cap, burning."""
    _terrain.append(("living", cx, floor, hw, h, r, tuple(tuple(hh) for hh in holes)))
    stem_c, cap_c = _living_cells(cx, floor, hw, h, r)
    for (x, y) in stem_c:
        px(x, y, STEM_L if x - cx < -hw + 2 else STEM_D if x - cx > hw - 2 else STEM_C)
    top = floor - h
    for (x, y) in cap_c:
        px(x, y, CAP_L if (x, y - 1) not in cap_c else CAP_D if y > top + 2 else CAP_C)
    for x0, y0, x1, y1 in holes:
        rect(x0, y0, x1, y1, AIR)
        rect(x0, y0, x1, y1, (70, 58, 96), 0.12)


def myc_mound(cx, floor, rx, ry, mat="mycel"):
    """A heap of mycelium-shot soil on the floor. mat="tinder" is the dry kind, which
    burns like wood."""
    _terrain.append(("mound", cx, floor, rx, ry, mat))
    lit, base = (MYC_L, MYC_C) if mat == "mycel" else (TINDER_L, TINDER)
    for y in range(int(floor - ry), floor + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            dx, dy = (x - cx) / rx, (y - floor) / ry
            if dx * dx + dy * dy <= 1.0:
                px(x, y, lit if (x * 7 + y * 3) % 11 == 0 else base)


def _wall_shroom_cells(x0, y0, x1, y1, r):
    """(stem, cap) cells of a mushroom grown sideways out of a wall at (x0, y0), its stem
    running to (x1, y1) and its cap upright on the end."""
    stem_c, cap_c = set(), set()
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / float(n)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - 6 * math.sin(math.pi * t)
        hw = 4.5 - 1.5 * t
        for yy in range(int(y - hw), int(y + hw) + 1):
            for xx in range(int(x - hw), int(x + hw) + 1):
                stem_c.add((xx, yy))
    top = y1 - 2
    for y in range(int(top - r * 0.55), top + 3):
        for x in range(int(x1 - r) - 1, int(x1 + r) + 2):
            dx, dy = (x - x1) / r, (y - top - 2) / (r * 0.55)
            if (dy <= 0 and dx * dx + dy * dy <= 1.0) or (0 < dy and y <= top + 2 and abs(dx) <= 1.0):
                cap_c.add((x, y))
    return stem_c - cap_c, cap_c


def wall_shroom(x0, y0, x1, y1, r):
    """A giant mushroom grown sideways out of the rock at (x0, y0): its stem a walkway
    out to (x1, y1), where its cap stands. It hangs on its root alone - burn or blow
    that and the whole thing comes down."""
    _terrain.append(("wall", x0, y0, x1, y1, r))
    stem_c, cap_c = _wall_shroom_cells(x0, y0, x1, y1, r)
    for (x, y) in stem_c:
        px(x, y, STEM_L if (x + y) % 5 == 0 else STEM_C)
    for (x, y) in cap_c:
        px(x, y, CAP_L if y < y1 - 2 - r * 0.3 else CAP_C)


def room_origin(mod):
    """Where the sheet put the room's top-left - the same as smallroomkit.room_sheet."""
    w, h = mod.ROOM["w"], mod.ROOM["h"]
    return (max(640, w + 260) - w) // 2, 84


def terrain_extras(g, mod):
    """Write what giant_shroom and myc_mound recorded into the room's material grid, and a
    crust of mycelium on the room's floors. Called by export_rooms after the map is
    rasterised (the furnish pass that recorded them ran just before)."""
    ox, oy = room_origin(mod)
    for t in _terrain:
        if t[0] == "shroom":
            _, cx, floor, h, r, lean, capmat = t
            stem_c, cap_c = _shroom_cells(cx, floor, h, r, lean)
            for (x, y) in stem_c:
                g.set(x - ox, y - oy, "stem")
            for (x, y) in cap_c:
                g.set(x - ox, y - oy, capmat)
        elif t[0] == "slab":
            _, x0, y0, x1, y1, mat = t
            for y in range(int(y0), int(y1) + 1):
                for x in range(int(x0), int(x1) + 1):
                    g.set(x - ox, y - oy, mat)
        elif t[0] == "living":
            _, cx, floor, hw, h, r, holes = t
            stem_c, cap_c = _living_cells(cx, floor, hw, h, r)
            for (x, y) in stem_c:
                g.set(x - ox, y - oy, "stem")
            for (x, y) in cap_c:
                g.set(x - ox, y - oy, "cap")
            for x0, y0, x1, y1 in holes:
                for y in range(int(y0), int(y1) + 1):
                    for x in range(int(x0), int(x1) + 1):
                        g.set(x - ox, y - oy, None)
                        g.air.add((x - ox, y - oy))
        elif t[0] == "house":
            walls, roofc, inside = _grown_house_cells(*t[1:8], shed=t[8])
            for (x, y) in walls:
                g.set(x - ox, y - oy, "stem")
            for (x, y) in roofc:
                g.set(x - ox, y - oy, "cap")
            for (x, y) in inside:                             # a house grown into rock is hollow
                g.set(x - ox, y - oy, None)
                g.air.add((x - ox, y - oy))
        elif t[0] == "hanging":
            _, cx, roof, h, r = t
            stem_c, cap_c = _hanging_shroom_cells(cx, roof, h, r)
            for (x, y) in stem_c:
                g.set(x - ox, y - oy, "stem")
            for (x, y) in cap_c:
                g.set(x - ox, y - oy, "cap")
        elif t[0] == "wall":
            _, x0, y0, x1, y1, r = t
            stem_c, cap_c = _wall_shroom_cells(x0, y0, x1, y1, r)
            for (x, y) in stem_c:
                g.set(x - ox, y - oy, "stem")
            for (x, y) in cap_c:
                g.set(x - ox, y - oy, "cap")
        else:
            _, cx, floor, rx, ry, mat = t
            for y in range(int(floor - ry), floor + 1):
                for x in range(int(cx - rx), int(cx + rx) + 1):
                    dx, dy = (x - cx) / rx, (y - floor) / ry
                    if dx * dx + dy * dy <= 1.0:
                        g.set(x - ox, y - oy, mat)
    _terrain.clear()
    # mycelium a pixel or two deep under every floor of the room's own rock
    for (x, y) in list(g.air):
        if g.m.get((x, y + 1)) == "rock":
            depth = 1 + (x * 13 + y * 7) % 3
            for k in range(1, depth + 1):
                if g.m.get((x, y + k)) == "rock":
                    g.m[(x, y + k)] = "mycel"


def backwall(b, mod):
    """The back wall of a fungal room: back_mycelium behind the cave (BACK_ROCK), with
    crusts of small caps in patches. A sheet's own `BACK_PATCHES` = [(x0, y0, x1, y1)],
    room coords, puts them where it wants them (behind an altar, say); `BACK_HOUSES`, the
    same, boards the inside of a grown house with back_stem."""
    for x0, y0, x1, y1 in getattr(mod, "BACK_HOUSES", ()):     # inside a grown house
        b.rect(x0, y0, x1, y1, "back_stem")
    for x0, y0, x1, y1 in getattr(mod, "BACK_PATCHES", ()):
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rx, ry = max(1.0, (x1 - x0) / 2.0), max(1.0, (y1 - y0) / 2.0)
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                dx, dy = (x - cx) / rx, (y - cy) / ry
                if dx * dx + dy * dy <= 1.0 - 0.25 * math.sin(x * 0.7 + y * 0.4):
                    b.px(x, y, "back_caps")


# ─────────────────────────────────────────────────────────────────────────────
#  Houses: housekit's walls, floors, doors and roofs, in stem and cap
# ─────────────────────────────────────────────────────────────────────────────
# roombuild.structures lays these as the fungal set (StemWall, StemFloor, CapDeck, CapDoor,
# CapRoof) when the sheet says so; a fungal house room's roombuild module is the usual
# B.hooks / B.finish pair.
HOUSE_KIT = dict(wall="StemWall", floor="StemFloor", deck="CapDeck", door="CapDoor", roof="CapRoof")


def plank_wall(x0, y0, x1, y1):
    """A wall of stem slabs stood on end."""
    rect(x0, y0, x1, y1, STEM_C)
    rect(x0, y0, x0, y1, STEM_L)
    rect(x1, y0, x1, y1, STEM_D)
    for y in range(int(y0) + 11, int(y1), 12):
        rect(x0, y, x1, y, STEM_D, 0.7)


def deck(x0, x1, y, thick=4, joists=True):
    """A floor of stem slabs on a root joist, top at y."""
    rect(x0, y, x1, y + thick - 1, STEM_C)
    rect(x0, y, x1, y, STEM_L)
    rect(x0, y + thick - 1, x1, y + thick - 1, (84, 66, 46))
    if joists:
        for x in range(int(x0) + 4, int(x1) - 2, 22):
            rect(x, y + thick, x + 2, y + thick + 2, (70, 54, 38))


def flap_door(x, top, h=30, w=4, swung=0):
    """A door of cap flesh on a root frame, with its glowing knob."""
    rect(x - 2, top - 3, x + w + 2, top - 1, (70, 54, 38))
    rect(x, top, x + w, top + h - 1, CAP_C)
    rect(x, top, x, top + h - 1, CAP_L)
    rect(x + w, top, x + w, top + h - 1, CAP_D)
    for yy in (top + 1, top + 9, top + 20, top + h - 2):
        rect(x, yy, x + w, yy, (96, 76, 52))
    px(x + w - 1, top + h // 2, GLOW_C)


def trapdoor(x0, x1, y, open_=False):
    """A lid of cap over a hatch."""
    rect(x0, y, x1, y + 2, CAP_C)
    rect(x0, y, x1, y, CAP_L)


def pitched_roof(x0, x1, eave, ridge_h, c=None, lit=None, thick=6):
    """Two pitches of cap shingles over a house."""
    cx = (x0 + x1) / 2.0
    half = (x1 - x0) / 2.0
    for x in range(int(x0) - 4, int(x1) + 5):
        top = eave - ridge_h * max(0.0, 1 - abs(x - cx) / half)
        for k in range(thick):
            px(x, top + k, CAP_L if k == 0 else CAP_D if k == thick - 1 else CAP_C)


def house_back(b, x0, y0, x1, y1, gills_to=None):
    """The inside of a fungal house on its back wall: stem slabs from y0 to y1, and the
    gills of the cap over it from `gills_to` (the cap's underside) down to y0."""
    b.rect(x0, y0, x1, y1, "back_stem")
    if gills_to is not None and gills_to < y0:
        b.rect(x0, gills_to, x1, y0 - 1, "back_gills")


# ─────────────────────────────────────────────────────────────────────────────
#  Export hooks
# ─────────────────────────────────────────────────────────────────────────────
def _hook_prop(add, name, cx, y, at="floor"):
    w, h = size(name)
    x0 = int(round(cx - w / 2.0))
    y0 = {"floor": y - h, "ceil": y, "centre": int(round(y - h / 2.0))}[at]
    add(name, x0 + w / 2.0, y0 + h / 2.0)


def _hook_hang(add, name, cx, roof, drop):
    w, h = size(name)
    ex, ey = _EYES.get(name, (w / 2.0, 0))
    x0, y0 = int(round(cx - ex)), int(round(roof + drop - ey))
    add(name, x0 + w / 2.0, y0 + h / 2.0, rope=(x0 + ex, roof, y0 + ey))


def _hook_bracket(add, x, y, side="L", glow=False):
    name = "BracketDeck" + ("Glow" if glow else "") + ("R" if side == "R" else "")
    w, h = size(name)
    x0 = x if side == "L" else x - w + 1
    add(name, x0 + w / 2.0, y + h / 2.0)


def _hook_shroom(add, cx, floor, h, r, lean=0, cap="cap"):
    _terrain.append(("shroom", cx, floor, h, r, lean, cap))


def _hook_mound(add, cx, floor, rx, ry, mat="mycel"):
    _terrain.append(("mound", cx, floor, rx, ry, mat))


def _hook_slab(add, x0, y0, x1, y1, mat="stem"):
    _terrain.append(("slab", x0, y0, x1, y1, mat))


def _hook_living(add, cx, floor, hw, h, r, holes):
    _terrain.append(("living", cx, floor, hw, h, r, tuple(tuple(hh) for hh in holes)))


def _hook_house(add, x0, x1, floor, h, ridge, doors=("L", "R"), windows=(), shed=None):
    _terrain.append(("house", x0, x1, floor, h, ridge, tuple(doors), tuple(windows), shed))


def _hook_hanging(add, cx, roof, h, r):
    _terrain.append(("hanging", cx, roof, h, r))


def _hook_wall_shroom(add, x0, y0, x1, y1, r):
    _terrain.append(("wall", x0, y0, x1, y1, r))


def _hook_sprinkle(add, m, x0, x1, y_ref, n, kinds=FLOOR_GROWTH, gap=10):
    saved = globals()["prop"]
    globals()["prop"] = lambda name, cx, y, at="floor": _hook_prop(add, name, cx, y, at)
    try:
        sprinkle(m, x0, x1, y_ref, n, kinds, gap)
    finally:
        globals()["prop"] = saved


def _hook_ladder(add, x, y0, y1):
    """housekit's ladder_up as a Props/Ladder from y0 down to y1 (roombuild.structures)."""
    import roomprops_structures as S
    ids = S.ladder_ids()
    h = (y1 - y0) / 20.0
    add.place("Props/Ladder", x + 0.5, y0, mods=[
        (ids["lc"], "_height", "%.4f" % h), (ids["sr"], "m_Size.y", "%.4f" % h)])


PROP_HOOKS = {
    "ladder_up": _hook_ladder,
    "prop": _hook_prop,
    "hang": _hook_hang,
    "bracket": _hook_bracket,
    "giant_shroom": _hook_shroom,
    "myc_mound": _hook_mound,
    "wall_shroom": _hook_wall_shroom,
    "hanging_shroom": _hook_hanging,
    "grown_house": _hook_house,
    "slab": _hook_slab,
    "living_shroom": _hook_living,
    "sprinkle": _hook_sprinkle,
}


# ─────────────────────────────────────────────────────────────────────────────
#  The sheet
# ─────────────────────────────────────────────────────────────────────────────
def fungal_sheet(room, code, callouts, beats, seed):
    """smallroomkit.room_sheet, with the room's rock and the fill repainted in the biome's
    colours before the labels go on."""
    _terrain.clear()
    w, h = room["w"], room["h"]
    cw, ch = max(640, w + 260), h + 240
    new_canvas(cw, ch, seed=seed)
    label_scale(2)
    ox, oy = (cw - w) // 2, 84
    lay([(room, ox, oy)], None, [])
    fill_map = {FILL: F_FILL, FILL_D: F_FILL_D, FILL_M: F_FILL_M, FILL_L: F_FILL_L}
    buf = _ck.buf
    for y in range(ch):
        row = buf[y]
        for x in range(cw):
            c = row[x]
            if c in _RECOLOR:
                row[x] = _RECOLOR[c]
            elif c in fill_map:
                row[x] = fill_map[c]
    dashed_box(ox, oy, ox + w - 1, oy + h - 1)
    vignette(0.25)
    socket_tags(room, ox, oy)
    btitle_bar("PHYSFUN - FUNGAL ROOM %s:  %s" % (code, room["name"]), "%dX%d / GAME SCALE" % (w, h))
    for text, (lx, ly), (ax, ay) in callouts:
        bcallout(ox + lx, oy + ly, text, ox + ax, oy + ay)
    blegend(16, oy + h + 54, [("BEATS", CYAN)] + list(beats), cw - 40)
    slug = "".join(p.capitalize() for p in room["name"].replace("THE ", "").split())
    return save(small_path("RoomConcept_%s_%s.png" % (code, slug)), scale=2)
