"""Turn small-room concepts into room prefabs for the floor builder.

    python Assets/GameConcepts/Tools/export_rooms.py                 # the default set
    python Assets/GameConcepts/Tools/export_rooms.py small_06_crib    # one room
    python Assets/GameConcepts/Tools/export_rooms.py --force ...      # overwrite existing

For each room this writes, under Assets/Rooms/:

* Maps/<Name>_Map.asset - the room's TerrainMap at 40 cells per unit (a concept pixel is a
  20-PPU sprite pixel, so two cells). Air is the concept's air with every socket stub open;
  the room keeps its shell of `rock`; the rest of its box is the fill tile. What the room
  is built round - timber, a loose slab, a boulder, an ore heap - goes in as terrain of the
  right material (see EXTRAS), so fire and the support pass work on it.
* Room_<Name>.prefab - a Room with that map, a TerrainBuilder child to see and paint it, a
  RoomSocket per concept socket, an entry, and the concept's enemies and kegs as prefab
  instances (enemies mapped onto the prefabs that exist, see ENEMIES).

and Floor.asset, a FloorRecipe listing them, if there is none yet.

It is a starting point, not a pipeline: an existing prefab or map is left alone unless
--force is given, because rooms are finished by hand in Unity. Guids and file ids are
derived from names, so a forced re-export keeps every reference to the room intact.
"""
import hashlib
import importlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smallroomkit as K  # noqa: E402
import propexport as PE  # noqa: E402
from roomkit import _load as R_load, _foot_row as R_foot, _CHARS as R_CHARS  # noqa: E402

ASSETS = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ASSETS, "Rooms")
PPU = 40
CELLS = 2                  # cells per concept pixel

DEFAULT = ["small_01_hopper", "small_02_drift", "small_06_crib", "small_17_boulderrun"]

# script guids
G_ROOM = "cc0403d229671b0498596a79ff78b02f"
G_ENTRY = "5f1fe1e0e28e8964bb02160093856c61"
G_SOCKET = "14074ffb884a4e04991986843c5b9484"
G_RECIPE = "91ea44979a630e34ca283054159bae0c"
G_MAP = "d1bd63cc6a214d94ab7e19d4204b43aa"
G_BUILDER = "09c0888d1dce440ea1c472960f2491a2"

# palette: material key -> (tile, PhysMaterialId)
MATERIALS = {
    "rock": ("rock", 0),
    "fill": ("rock_hard", 0),
    "wood": ("wood", 1),
    "slab": ("rock_alt", 0),
    "gravel": ("gravel", 0),
    "steel": ("steel", 3),
    "boulder": ("templerock", 0),
    "brick": ("templebrick", 0),
    "firebrick": ("brick", 0),
    "coal": ("coal", 0),
}

# concept sprite -> prefab under Resources/Prefabs/Enemies (closest thing that exists)
ENEMIES = {
    "Gaper": "Gaper", "Ghast": "Ghast", "Minespider": "Minespider", "Reaper": "Reaper",
    "Sentinel": "Sentinel", "RiotBrute": "Swat", "Grenadier": "SoldierArmed", "Pyro": "Shotgunner",
    "BloodMage": "Wizard", "WizBogcap": "Bogcap", "WizBonecrown": "Bonecrown",
    "WizCrimson": "Crimson", "WizDeepminer": "Deepminer", "WizGoldhood": "Goldhood",
    "WizHollowhood": "Hollowhood", "WizMaskwraith": "Maskwraith", "WizRamskull": "Ramskull",
}
BARREL = "Hazards/ExplosiveBarrel"
ROPE = "Hazards/Rope"
G_DAMAGEABLE = "baa9384630d24df0977c63474029daee"  # Common/Damageable
HUNG_LINK = 1.0         # kg a link of a rope a prop hangs from
HUNG_LOAD = 60.0        # kg at most a hung prop weighs, per rope (a bell is a tonne by area)


def prop_mass(prefab):
    t = open(os.path.join(ASSETS, "Resources", "Prefabs", "Props", prefab + ".prefab"), encoding="utf-8").read()
    return float(t.split("m_Mass: ")[1].split()[0])
G_ROPE2D = "354d5a79391726947894a3cca5cc16e5"      # Props/Rope2D
G_BRIDGE = "1276b41eb86147aa816dfa8b19a81a02"      # Spawners/BridgeBuilder2D
G_FUSE = "f1a0ab60ff6834642af8ee11fbd989a0"        # Phys/Explosions/FuseCord


def anchor_halfwidth(prefab):
    """Half the width of a prop's sprite, world units - where a plank's hinges go."""
    t = open(os.path.join(ASSETS, "Resources", "Prefabs", "Props", prefab + ".prefab"), encoding="utf-8").read()
    return float(t.split("m_Size: {x: ")[1].split(",")[0]) / 2.0


def script_guid(rel):
    """A script's guid from the .meta Unity wrote for it - never one made up here."""
    meta = os.path.join(ASSETS, rel + ".meta")
    if not os.path.exists(meta):
        raise SystemExit("%s has no .meta yet: let the Unity editor import it, then run again" % rel)
    return open(meta).read().split("guid: ")[1].split()[0]


def guid(name):
    return hashlib.md5(("physfun-rooms/" + name).encode()).hexdigest()


def fid(*parts):
    return int(hashlib.md5("/".join(parts).encode()).hexdigest()[:15], 16)


# ─────────────────────────────────────────────────────────────────────────────
#  The room at concept scale
# ─────────────────────────────────────────────────────────────────────────────
class Grid:
    """Material per concept pixel, local coords (x right, y down)."""

    def __init__(self, w, h, air, shell):
        self.w, self.h, self.air = w, h, air
        self.m = {}
        for y in range(h):
            for x in range(w):
                self.m[(x, y)] = None if (x, y) in air else "rock" if (x, y) in shell else "fill"

    def set(self, x, y, mat):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.m[(x, y)] = mat

    def rect(self, x0, y0, x1, y1, mat, only_air=False):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                if not only_air or (x, y) in self.air:
                    self.set(x, y, mat)

    def floor(self, x, y_from):
        y = int(y_from)
        while y < self.h and (int(x), y) in self.air:
            y += 1
        return y

    def ceil(self, x, y_from):
        y = int(y_from)
        while y > 0 and (int(x), y) in self.air:
            y -= 1
        return y


AIR_MARK = (1, 2, 3)
ROCK_COLOURS = {K.ROCK, K.ROCK_D, K.ROCK_M, K.ROCK_L, K.FILL, K.FILL_D, K.FILL_M, K.FILL_L}


def rasterise(mod):
    """Rebuild the room's air exactly as its sheet does - same canvas, same seed, the
    fill painted first so the noise lines up - then shift it to the room's own coords."""
    room = mod.ROOM
    w, h = room["w"], room["h"]
    cw, ch = max(640, w + 260), h + 240
    ox, oy = (cw - w) // 2, 84
    K.new_canvas(cw, ch, seed=mod.SHEET["seed"])
    K.label_scale(2)
    K.paint_fill()
    a, stubs = K.room_masks(room, ox, oy)
    for sid, cells in stubs.items():            # a stub that stops short of the room is a wall
        if not any((x + dx, y + dy) in a for (x, y) in cells
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            print("  !! socket %s does not reach the room's air - raise its depth" % sid)
    open_ = set(a)
    for cells in stubs.values():
        open_ |= cells
    shell = K.shell(open_, ox, oy, w, h)

    # Run the furnish pass to learn where the enemies, kegs and props are.
    spawns = []
    mod.stand = lambda name, cx, floor, flip=False, tint=None: spawns.append(("enemy", name, cx - ox, floor - oy))
    # a keg is the Keg prop (9x11, the sheet's own size, explosive); the four rooms exported
    # before it existed keep their ExplosiveBarrels until they are exported again
    mod.keg = lambda x, floor: add("Keg", x + 4.5, floor - 5.5)

    def placed(name, x, y, flip=False, tint=None):
        """An enemy pasted by its top-left (sprite()) rather than stood (stand()). Inside
        draw_rotated the coords are the little canvas's own - those land outside the room."""
        cw_, ch_, pix = R_load(os.path.join(R_CHARS, "Char_%s.png" % name))
        cx, floor = x + cw_ // 2 - ox, y + R_foot(ch_, pix) + 1 - oy
        if 0 <= cx < w and 0 <= floor < h:
            spawns.append(("enemy", name, cx, floor))
    mod.sprite = placed

    def add(prefab, cx, cy, scale=1.0, angle=0.0, rope=None, ropes=(), static=False,
            key=None, fields=None, mass=None):
        """rope=(x, roof y or None, eye y) is the old one-rope form; ropes=[(anchor, roof x,
        roof y or None)] ties each named anchor of the prop to the roof above that x.
        key names the instance for add.joint; fields = {component index: {field: value}}
        overrides the prefab's own components (index into its extras, 0 = the first);
        mass overrides its Rigidbody2D's."""
        hung = [("Eye", rope[0], rope[1])] if rope else []
        hung += list(ropes)
        r = [[a, x - ox, None if y is None else y - oy] for a, x, y in hung]
        spawns.append(("prop", prefab, cx - ox, cy - oy,
                       dict(scale=scale, angle=angle, ropes=r, static=static, key=key,
                            fields=fields or {}, mass=mass)))

    def joint(body, anchor, connected=None, kind=0, **fields):
        """A PropJoint at `anchor` of the prop keyed `body`, to the prop keyed `connected`
        (None = the world). kind 0 hinge, 1 slider, 2 fixed; fields are PropJoint's
        (_useMotor, _motorSpeed, ...)."""
        spawns.append(("joint", body, anchor, connected, dict(kind=kind, **fields)))
    add.joint = joint

    def rope(key, x0, y0, x1, y1):
        """A rope from (x0, y0) - pinned there - towards (x1, y1), its far end left for
        whatever ties it on at runtime (a bridge's hanger), under a Tether2D so it can be
        shot through. Sheet coords."""
        spawns.append(("rope", key, x0 - ox, y0 - oy, (x1 - ox, y1 - oy)))
    add.rope = rope

    def bridge(x0, y0, x1, y1, count, hangers, plank="BridgePlank"):
        """A BridgeBuilder2D built when the room wakes: `count` planks from (x0, y0) to
        (x1, y1), ends left loose, hung from ropes made with add.rope - hangers =
        [(rope key, 0..1 along the bridge)]. Sheet coords."""
        spawns.append(("bridge", plank, x0 - ox, y0 - oy, (x1 - ox, y1 - oy, count, list(hangers))))
    add.bridge = bridge

    def fuse(points, burn_speed=1.0):
        """A FuseCord along `points` (sheet coords, first = the free end), lit by fire."""
        spawns.append(("fuse", None, points[0][0] - ox, points[0][1] - oy,
                       dict(points=[(x - ox, y - oy) for x, y in points], speed=burn_speed)))
    add.fuse = fuse

    def place(rel, cx, cy, mods=(), angle=0.0, scale=1.0, name=None):
        """An instance of any prefab under Resources/Prefabs (a Conveyor, a Grinder), centred
        at (cx, cy) sheet coords, with mods = [(file id in that prefab, property path, value)]."""
        spawns.append(("inst", rel, cx - ox, cy - oy, dict(mods=list(mods), angle=angle,
                                                           scale=scale, name=name)))
    add.place = place

    def component(name, script_rel, cx, cy, fields=""):
        """A bare GameObject at (cx, cy) sheet coords carrying one of the game's scripts
        (a FireSource, say), its serialized fields given as YAML lines."""
        spawns.append(("comp", name, cx - ox, cy - oy, dict(script=script_rel, fields=fields)))
    add.component = component
    hooks = prop_hooks(add, mod)
    rb = room_module(mod)
    if rb and hasattr(rb, "hooks"):
        rb.ORIGIN = (ox, oy)                                 # sheet coords of the room's corner
        hooks.update({k: v for k, v in rb.hooks(add, mod).items() if hasattr(mod, k)})
    for fn, hook in hooks.items():
        setattr(mod, fn, hook)
    # Paint the air one colour no sheet uses, and switch the light off, so that afterwards
    # whatever the furnish pass drew in rock colours over the air - teeth off the roof,
    # shelves off the walls, mounds - can be told apart and turned into rock.
    for (x, y) in open_:
        K.px(x, y, AIR_MARK)
    mod.glow = lambda *a, **k: None
    # The furnish pass sees the room without its socket stubs: on the sheet every stub is
    # open, but in a floor an unused one is rock again, and a floor_at / ceil_at that runs
    # down a stub stands a gaper at the bottom of a hole that is about to be filled in, or
    # hangs a rod from the top of a corridor that may not be there.
    room["furnish"](ox, oy, set(a))
    if rb and hasattr(rb, "furnish"):                        # props the sheet draws inline
        rb.furnish(add, mod, ox, oy)

    grown = {(x, y) for (x, y) in open_ if K.at(x, y) in ROCK_COLOURS}
    open_ -= grown
    air = {(x - ox, y - oy) for (x, y) in open_}
    shell = {(x - ox, y - oy) for (x, y) in shell | grown}
    g = Grid(w, h, air, shell)
    for sp in spawns:                                        # no roof given: up to the rock above
        if sp[0] != "prop" or len(sp) < 5 or not isinstance(sp[4], dict) or "ropes" not in sp[4]:
            continue
        for r in sp[4]["ropes"]:
            if r[2] is None:
                r[2] = g.ceil(r[1], sp[3]) + 1
    return g, spawns


# ─────────────────────────────────────────────────────────────────────────────
#  Props: the sheet's draw calls, turned into prefab instances
# ─────────────────────────────────────────────────────────────────────────────
def room_module(mod):
    """`roombuild/<sheet>.py`, if the room has one: what is particular to assembling that
    room - `extras(g, mod)` for its structure as terrain, `hooks(add, mod)` for its own
    draw calls as props, `furnish(add, mod, ox, oy)` for props the sheet draws inline."""
    sheet = mod.__name__.split(".")[-1]
    try:
        return importlib.import_module("roombuild." + sheet)
    except ModuleNotFoundError as e:
        if e.name not in ("roombuild." + sheet, "roombuild"):
            raise
        return None


def anchor_local(prefab, anchor):
    """Where a prop prefab's anchor child sits, local units - read from the prefab."""
    path = os.path.join(ASSETS, "Resources", "Prefabs", "Props", prefab + ".prefab")
    text = open(path, encoding="utf-8").read()
    t = "--- !u!4 &%d\n" % PE.anchor_id(prefab, anchor)
    if t not in text:
        raise ValueError("%s has no anchor %s" % (prefab, anchor))
    block = text.split(t)[1]
    pos = block.split("m_LocalPosition: {x: ")[1]
    x = float(pos.split(",")[0])
    y = float(pos.split("y: ")[1].split(",")[0])
    return x, y


def prop_hooks(add, mod):
    """{draw function: replacement} for the furnish pass. Each replacement calls
    add(prefab under Resources/Prefabs/Props, centre x, centre y, scale=, angle=, rope=)
    in sheet coords, the centre being where the prop's sprite centre lands so that it
    covers what the sheet drew. rope=(x, roof y or None, eye y) hangs it on a Hazards/Rope
    from the roof (None = the rock straight above) down to the prefab's Eye child.

    The art is `roomprops.py`. Local helpers share names across sheets (S12's drum is an
    oil drum, S18's is the winch drum), so a hook names the sheets it is for."""
    sheet = mod.__name__.split(".")[-1]

    def only(*sheets):
        return sheet in sheets

    h = {}
    h["crate_g"] = lambda x, floor, s=12: add("Crate", x + s / 2.0, floor - s / 2.0, scale=(s + 1) / 13.0)
    # the cage sprite: eye 0-4, bars to 26, floor 27-28 on the sheet's `bottom`
    h["cage"] = lambda cx, top, bottom, roof: add("HangingCage", cx + 0.5, bottom - 12.5,
                                                   rope=(cx, roof, top - 4))
    if only("small_04_belfry"):
        h["bell"] = lambda cx, top, lip: add("Bell", cx + 0.5, top + 23, rope=(cx, None, top - 11))
    if only("small_11_furnace"):
        h["coal_sack"] = lambda x, floor: add("CoalSack", x + 6, floor - 6.5)
    if only("small_14_ossuary", "small_26_idol"):
        quiet = []

        def skull(x, y, flip=False):
            if not quiet:
                add("Skull", x + 2, y - 2)
        h["skull"] = skull
        # the skulls packed into niches and heaps are part of the bone, not 70 loose bodies
        for packed in ("fill_niche", "charnel_heap"):
            if hasattr(mod, packed):
                def wrapped(*a, _fn=getattr(mod, packed), **k):
                    quiet.append(1)
                    try:
                        return _fn(*a, **k)
                    finally:
                        quiet.pop()
                h[packed] = wrapped
    if only("small_14_ossuary"):
        h["gibbet"] = lambda x, roof, top: add("Gibbet", x + 0.5, top + 11, rope=(x, roof, top - 3))
    if only("small_26_idol"):
        h["censer"] = lambda x, roof, drop: add("Censer", x + 0.5, roof + drop + 1,
                                                rope=(x, roof, roof + drop - 4))
    if only("small_13_counterweight"):
        h["counterweight"] = lambda cx, y: add("Counterweight", cx + 0.5, y + 23.5, rope=(cx, None, y))
    if only("small_12_magnetcrane"):
        h["drum"] = lambda x, floor, c=None: add("OilDrum", x + 4, floor - 7)
    if only("small_20_scrapyard"):
        def drum_(x, floor, c=None, cl=None, lying=False):
            name = "OilDrumGreen" if c is not None and c[1] > c[0] else "OilDrum"
            if lying:
                add(name, x + 7, floor - 5.5, angle=90)
            else:
                add(name, x + 5, floor - 7)
        h["drum_"] = drum_
    if only("small_05_sawpit"):
        def log(x0, x1, y, r=4):
            ln = x1 - x0
            add("LogLong" if ln > 60 else "LogShort", (x0 + x1) / 2.0, y + 0.5,
                scale=ln / (88.0 if ln > 60 else 44.0))
        h["log"] = log
    if only("small_23_timberchute"):
        h["log_end"] = lambda cx, cy, r=5: add("LogEnd", cx + 0.5, cy + 0.5, scale=(2 * r + 1) / 12.0)
    if only("small_25_gasroom"):
        tints = {(110, 58, 50): "GasBottleRed", (128, 112, 60): "GasBottleOchre",
                 (78, 96, 70): "GasBottleGreen"}

        def bottle(cx, floor, h=34, c=(70, 84, 96), valve=True):
            add(tints.get(tuple(c), "GasBottle"), cx + 0.5, floor - (h + 4) / 2.0)
        h["bottle"] = bottle
    for name, fn in getattr(mod, "PROP_HOOKS", {}).items():   # a sheet may bring its own
        h[name] = lambda *a, _fn=fn, **k: _fn(add, *a, **k)
    return {k: v for k, v in h.items() if hasattr(mod, k)}


# ─────────────────────────────────────────────────────────────────────────────
#  What each room is built round, as terrain
# ─────────────────────────────────────────────────────────────────────────────
def extras_hopper(g, mod):
    # The ore heap in the bowl. It is kept 2px clear of the bowl's rock so that the gate
    # is the only thing holding it up - touching the bowl would count as support.
    def clear(x, y):
        return all((x + dx, y + dy) in g.air for dx in range(-2, 3) for dy in range(-2, 3)
                   if not (dy > 0 and 174 <= x + dx <= 206))   # ...except down into the throat
    for x in range(100, 282):
        top = int(166 + ((x - 190) / 88.0) ** 2 * 36)
        y = top
        while (x, y) in g.air and y < 213:
            if clear(x, y):
                g.set(x, y, "gravel")
            y += 1
    g.rect(166, 213, 214, 216, "wood")                       # the gate
    g.rect(188, 217, 191, 236, "wood")                       # its strut
    g.rect(182, 236, 197, 238, "wood")
    g.rect(92, 96, 291, 98, "wood")                          # plank walk under the roof
    for hx in (134, 172, 212, 250):                          # hangers, clear of the top sockets
        g.rect(hx, g.ceil(hx, 94), hx, 95, "wood")
    for sx in (82, 298):                                     # the pit's stulls
        top, bot = g.ceil(sx + 1, 330) + 1, g.floor(sx + 1, 330) - 1
        g.rect(sx, top, sx + 3, bot, "wood")
        g.rect(sx - 4, top, sx + 7, top + 2, "wood")


def extras_drift(g, mod):
    rail = mod.drift_rail_y
    for x in range(16, 424):
        y = int(rail(x))
        g.rect(x, y, x, y + 1, "steel")
        f = g.floor(x, y + 2)
        if f - (y + 2) <= 4:                                 # bed the rail where the floor is under it
            g.rect(x, y + 2, x, f - 1, "rock")
    bot = g.floor(139, 250)
    for lx in (122, 154):                                    # the trestle over the magazine
        g.rect(lx, int(rail(lx)) + 2, lx + 3, bot - 1, "wood")
    # the tub: a steel box riding 2px clear of the rail, held only by its chock
    s, c = math.sin(mod.SLOPE), math.cos(mod.SLOPE)
    bx, by = 46, rail(46) - 3
    for u in range(0, 30):
        for v in range(0, 12):
            g.set(bx + u * c + v * s, by + u * s - v * c, "steel")
    cx = bx + 30 * c
    cy = rail(cx)
    for i in range(7):                                       # chock wedge, rail to the tub's nose
        g.rect(cx, cy - 1 - i, cx + 7 - i, cy - 1 - i, "wood")
    f = g.floor(372, 330)                                    # barricade at the bottom
    for i, x in enumerate((364, 370, 376)):
        g.rect(x, f - 30 + i * 2, x + 4, f - 1, "wood")
    g.rect(358, f - 20, 384, f - 18, "wood")


def extras_crib(g, mod):
    for (x, y) in mod.SLAB:                                  # the parted roof slab
        g.set(x, y, "slab")
    x0, x1 = mod.CRIB_X - 2, mod.CRIB_X + mod.CRIB_W + 2
    for x in range(x0, x1 + 1):                              # the crib, slab to mound
        top = int(mod.slab_bottom(x)) + 1
        g.rect(x, top, x, g.floor(x, top) - 1, "wood")


def extras_boulderrun(g, mod):
    cx, cy, r = 88, 130, 17
    bottom = {}
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                g.set(x, y, "boulder")
                bottom[x] = max(bottom.get(x, 0), y)
    # a timber cradle under its downhill side: the only thing it touches
    for x in range(80, 101):
        if x in bottom:
            g.rect(x, bottom[x] + 1, x, g.floor(x, bottom[x] + 1) - 1, "wood")


EXTRAS = {
    "small_01_hopper": extras_hopper,
    "small_02_drift": extras_drift,
    "small_06_crib": extras_crib,
    "small_17_boulderrun": extras_boulderrun,
}


# ─────────────────────────────────────────────────────────────────────────────
#  Unity files
# ─────────────────────────────────────────────────────────────────────────────
def encode(cells):
    out = bytearray()
    i, n = 0, len(cells)
    while i < n:
        v = cells[i]
        run = 1
        while i + run < n and cells[i + run] == v and run < 65535:
            run += 1
        out += bytes((v, run & 0xFF, run >> 8))
        i += run
    return out.hex()


def write_map(name, g):
    keys = [k for k in MATERIALS if any(v == k for v in g.m.values())]
    index = {k: i + 1 for i, k in enumerate(keys)}
    W, H = g.w * CELLS, g.h * CELLS
    cells = bytearray(W * H)
    for cy in range(H):
        y = (H - 1 - cy) // CELLS
        row = cy * W
        for cx in range(W):
            v = g.m[(cx // CELLS, y)]
            cells[row + cx] = index[v] if v else 0
    palette = "".join("  - tile: %s\n    physMaterial: %d\n" % MATERIALS[k] for k in keys)
    asset = f"""%YAML 1.1
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
  m_Script: {{fileID: 11500000, guid: {G_MAP}, type: 3}}
  m_Name: {name}_Map
  m_EditorClassIdentifier: Assembly-CSharp::Phys.Terrain.TerrainMap
  pixelsPerUnit: {PPU}
  origin: {{x: 0, y: 0}}
  width: {W}
  height: {H}
  palette:
{palette}  encoded: {encode(cells)}
"""
    meta = f"""fileFormatVersion: 2
guid: {guid(name + '_Map.asset')}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 11400000
  userData:
  assetBundleName:
  assetBundleVariant:
"""
    return asset, meta


def prefab_root(path):
    """(root GameObject fileID, root Transform fileID) of a prefab file."""
    text = open(path, encoding="utf-8").read()
    for block in text.split("--- !u!")[1:]:
        if block.startswith("4 &") and "m_Father: {fileID: 0}" in block:
            tid = int(block[3:block.index("\n")].split()[0])
            go = int(block.split("m_GameObject: {fileID: ")[1].split("}")[0])
            return go, tid
    raise ValueError("no root transform in " + path)


def rope_component(path):
    """File id of the Rope2D on the rope prefab (the one MonoBehaviour with `points:`)."""
    text = open(path, encoding="utf-8").read()
    for block in text.split("--- !u!")[1:]:
        if block.startswith("114 &") and "\n  points:" in block:
            return int(block[5:block.index("\n")].split()[0])
    raise ValueError("no Rope2D in " + path)


class Prefab:
    def __init__(self, name):
        self.name = name
        self.docs = []
        self.strips = {}        # (instance, source file id) -> the one stripped object for it

    def go(self, key, name, parent_t, pos, components):
        """A GameObject with a Transform and the given MonoBehaviours (script guid, fields).
        Returns (transform id, [component ids])."""
        gid, tid = fid(self.name, key, "go"), fid(self.name, key, "t")
        cids = [fid(self.name, key, "c%d" % i) for i in range(len(components))]
        comps = "".join("  - component: {fileID: %d}\n" % c for c in [tid] + cids)
        self.docs.append(f"""--- !u!1 &{gid}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
{comps}  m_Layer: 0
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
""")
        self.docs.append(("T", tid, gid, parent_t, pos))
        for cid, (script, fields) in zip(cids, components):
            self.docs.append(f"""--- !u!114 &{cid}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {gid}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier:
{fields}""")
        return tid, cids

    def instance(self, key, src_rel, name, parent_t, pos, angle=0.0, scale=1.0, mods=(), refs=()):
        """A nested prefab instance of Resources/Prefabs/<src_rel>.prefab. `mods` are extra
        (target file id in the source, property path, value); `refs` are (target, path,
        file id in this prefab) object references. Returns (instance id, source guid)."""
        path = os.path.join(ASSETS, "Resources", "Prefabs", src_rel + ".prefab")
        src = open(path + ".meta").read().split("guid: ")[1].split()[0]
        rgo, rt = prefab_root(path)
        pid, sid = fid(self.name, key, "pi"), fid(self.name, key, "st")
        self.strips[(pid, rt)] = sid
        a = math.radians(angle) / 2
        base = [(rt, "m_LocalPosition.x", "%.4f" % pos[0]), (rt, "m_LocalPosition.y", "%.4f" % pos[1]),
                (rt, "m_LocalPosition.z", "0"), (rt, "m_LocalRotation.w", "%.6f" % math.cos(a)),
                (rt, "m_LocalRotation.x", "0"), (rt, "m_LocalRotation.y", "0"),
                (rt, "m_LocalRotation.z", "%.6f" % math.sin(a)), (rgo, "m_Name", name)]
        if angle:
            base.append((rt, "m_LocalEulerAnglesHint.z", "%g" % angle))
        if scale != 1.0:
            base += [(rt, "m_LocalScale.x", "%.4f" % scale), (rt, "m_LocalScale.y", "%.4f" % scale)]
        m = "".join(f"""    - target: {{fileID: {t}, guid: {src}, type: 3}}
      propertyPath: {p}
      value: {v}
      objectReference: {{fileID: 0}}
""" for t, p, v in base + list(mods))
        m += "".join(f"""    - target: {{fileID: {t}, guid: {src}, type: 3}}
      propertyPath: {p}
      value:
      objectReference: {{fileID: {r}}}
""" for t, p, r in refs)
        self.docs.append(f"""--- !u!1001 &{pid}
PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {{fileID: {parent_t}}}
    m_Modifications:
{m}    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents: []
  m_SourcePrefab: {{fileID: 100100000, guid: {src}, type: 3}}
--- !u!4 &{sid} stripped
Transform:
  m_CorrespondingSourceObject: {{fileID: {rt}, guid: {src}, type: 3}}
  m_PrefabInstance: {{fileID: {pid}}}
  m_PrefabAsset: {{fileID: 0}}
""")
        self.docs.append(("child", parent_t, sid))
        return pid, src

    def docs_add_component(self, tid, key, script, fields):
        """Put one more MonoBehaviour on the GameObject whose Transform is `tid` (made by go())."""
        gid = fid(self.name, key, "go")
        cid = fid(self.name, key, "extra")
        for i, d in enumerate(self.docs):
            if isinstance(d, str) and d.startswith("--- !u!1 &%d\n" % gid):
                self.docs[i] = d.replace("  m_Layer: 0\n", "  - component: {fileID: %d}\n  m_Layer: 0\n" % cid, 1)
                break
        self.docs.append(f"""--- !u!114 &{cid}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {gid}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier:
{fields}""")
        return cid

    def stripped(self, key, pid, src, source_fid):
        """A Transform inside a nested instance, so something in this prefab can point at it.
        Unity allows one stripped object per (instance, source object): a second one for the
        same pair is not resolved, and whatever points at it gets null - so reuse."""
        if (pid, source_fid) in self.strips:
            return self.strips[(pid, source_fid)]
        tid = fid(self.name, key, "strip")
        self.strips[(pid, source_fid)] = tid
        self.docs.append(f"""--- !u!4 &{tid} stripped
Transform:
  m_CorrespondingSourceObject: {{fileID: {source_fid}, guid: {src}, type: 3}}
  m_PrefabInstance: {{fileID: {pid}}}
  m_PrefabAsset: {{fileID: 0}}
""")
        return tid

    def stripped_component(self, key, pid, src, source_fid, type_id, type_name, script=None):
        """A component inside a nested instance (its Rigidbody2D, a script on it), so a
        component in this prefab can hold a reference to it."""
        if (pid, source_fid) in self.strips:
            return self.strips[(pid, source_fid)]
        cid = fid(self.name, key, "stripc")
        self.strips[(pid, source_fid)] = cid
        extra = ""
        if type_name == "MonoBehaviour":
            extra = f"""  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier:
"""
        self.docs.append(f"""--- !u!{type_id} &{cid} stripped
{type_name}:
  m_CorrespondingSourceObject: {{fileID: {source_fid}, guid: {src}, type: 3}}
  m_PrefabInstance: {{fileID: {pid}}}
  m_PrefabAsset: {{fileID: 0}}
{extra}""")
        return cid

    def text(self):
        children = {}
        for d in self.docs:
            if isinstance(d, tuple):
                if d[0] == "T" and d[3]:
                    children.setdefault(d[3], []).append(d[1])
                elif d[0] == "child":
                    children.setdefault(d[1], []).append(d[2])
        out = ["%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n"]
        for d in self.docs:
            if isinstance(d, str):
                out.append(d)
            elif d[0] == "T":
                _, tid, gid, parent, pos = d
                kids = children.get(tid, [])
                kid_txt = "\n" + "".join("  - {fileID: %d}\n" % k for k in kids) if kids else " []\n"
                out.append(f"""--- !u!4 &{tid}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {gid}}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: {pos[0]:.4f}, y: {pos[1]:.4f}, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:{kid_txt}  m_Father: {{fileID: {parent or 0}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
""")
        return "".join(out)


def build_prefab(name, mod, g, spawns):
    room = mod.ROOM
    w, h = room["w"], room["h"]
    U = 1.0 / 20                                       # concept px -> world units

    def local(x, y):
        return (x * U, (h - y) * U)

    p = Prefab(name)
    map_ref = "{fileID: 11400000, guid: %s, type: 2}" % guid(name + "_Map.asset")
    root_t, root_c = p.go("root", "Room_" + name, 0, (0, 0), [(G_ROOM, f"  _map: {map_ref}\n")])
    p.go("terrain", "Terrain", root_t, (0, 0), [(G_BUILDER, f"  map: {map_ref}\n  buildOnAwake: 1\n")])

    sockets_t, _ = p.go("sockets", "Sockets", root_t, (0, 0), [])
    side_index = {"L": 0, "R": 1, "T": 2, "B": 3}
    entry = None
    rb = room_module(mod)
    want = getattr(rb, "ENTRY", None)                        # a room module may pick the way in
    for sid, (side, pos, depth) in room["sockets"].items():
        if side in "LR":
            at = local(0 if side == "L" else w, pos)
            size = 1.5
            if entry is None and want in (None, sid):
                inward = (depth * U + 0.9) * (1 if side == "L" else -1)
                entry = ((at[0] + inward, at[1]), side == "L")
        else:
            at = local(pos, 0 if side == "T" else h)
            size = 1.3
        p.go("socket/" + sid, sid, sockets_t, at,
             [(G_SOCKET, f"  _side: {side_index[side]}\n  _size: {size}\n  _depth: {depth * U:.4f}\n")])
    at = getattr(rb, "ENTRY_AT", None)                     # or a point on the floor, local px
    if at:
        entry = (local(*at), at[0] < w / 2)
    if entry:
        p.go("entry", "Entry", root_t, entry[0],
             [(G_ENTRY, f"  _id: start\n  _faceRight: {1 if entry[1] else 0}\n")])

    enemies_t, _ = p.go("enemies", "Enemies", root_t, (0, 0), [])
    props_t, _ = p.go("props", "Props", root_t, (0, 0), [])
    keyed = {}
    for i, sp in enumerate(spawns):
        if sp[0] == "inst":
            _, rel, x, y, o = sp
            p.instance("i%d" % i, rel, o["name"] or os.path.basename(rel), props_t, local(x, y),
                       angle=o["angle"], scale=o["scale"], mods=o["mods"])
            continue
        if sp[0] == "comp":
            _, cname, x, y, o = sp
            p.go("c%d" % i, cname, props_t, local(x, y), [(script_guid(o["script"]), o["fields"])])
            continue
        if sp[0] == "fuse":
            _, _, x, y, o = sp
            a = local(x, y)
            pts = "".join("  - {x: %.4f, y: %.4f}\n" % (local(px_, py_)[0] - a[0], local(px_, py_)[1] - a[1])
                          for px_, py_ in o["points"])
            p.go("f%d" % i, "FuseCord", props_t, a, [(G_FUSE, (
                "  points:\n%s  pixelsPerUnit: 20\n  burnSpeed: %g\n  litByFire: 1\n"
                "  targets: []\n  triggerRadius: 0.25\n  lightOnStart: 0\n  removeWhenSpent: 1\n")
                % (pts, o["speed"]))])
            continue
        if sp[0] in ("joint", "rope", "bridge"):
            continue
        kind, who, x, floor = sp[:4]
        fx, fy = local(x, floor)
        if kind == "prop":
            opts = sp[4]
            mods = [(PE.fid("prop", who, "rb"), "m_BodyType", "2")] if opts["static"] else []
            if opts["mass"] is not None:
                mods.append((PE.fid("prop", who, "rb"), "m_Mass", "%g" % opts["mass"]))
            for ci, fl in opts["fields"].items():
                for fname, val in fl.items():
                    mods.append((PE.fid("prop", who, "x%d" % ci), fname, str(val)))
            if opts["ropes"]:
                # A rope holds what hangs on it only if the load is not hundreds of times a
                # link: the prop's own mass (area x density) can be a tonne, so a hung prop is
                # capped at HUNG_LOAD per rope it hangs from.
                cap = HUNG_LOAD * len(opts["ropes"])
                if prop_mass(who) > cap:
                    mods.append((PE.fid("prop", who, "rb"), "m_Mass", "%g" % cap))
            pid, src = p.instance("p%d" % i, "Props/" + who, who, props_t, (fx, fy),
                                  angle=opts["angle"], scale=opts["scale"], mods=mods)
            if opts["key"]:
                keyed[opts["key"]] = (i, pid, src, who, fx, fy, opts["scale"])
            g_tether = script_guid("Scripts/Props/Tether2D.cs")
            rope_c = rope_component(os.path.join(ASSETS, "Resources", "Prefabs", ROPE + ".prefab"))
            for k, (aname, rx, ry) in enumerate(opts["ropes"]):
                ax, ay = anchor_local(who, aname)
                eye = (fx + ax * opts["scale"], fy + ay * opts["scale"])
                top = (eye[0], local(rx, ry)[1])
                anchor = p.stripped("p%d/%s" % (i, aname), pid, src, PE.anchor_id(who, aname))
                # A Rope2D to look at, bend, collide and be cut; a Tether2D over it carrying the
                # weight on a distance joint a little shorter than the rope, so the links never
                # take the load and never stretch. The rope sits under the tether so a hit on
                # any link finds the tether's Damageable.
                key = "t%d_%d" % (i, k)
                tether_t, _ = p.go(key, who + "Rope", props_t, top, [
                    (g_tether, "  _rope: {fileID: %d}\n  _cutDamage: 5\n"
                               % fid(p.name, key + "/rope", "stripc")),
                    (G_DAMAGEABLE, "  maxHealth: 100000\n  targetLayers:\n    serializedVersion: 2\n"
                                   "    m_Bits: 0\n  deathKick: 0\n  config: {fileID: 0}\n"
                                   "  takesPhysicsDamage: 0\n  showDamageNumbers: 0\n  bleeds: 0\n"
                                   "  bloodColor: {r: 0, g: 0, b: 0, a: 0}\n")])
                rpid, rsrc = p.instance(key + "/r", ROPE, "Rope", tether_t, (0, 0), mods=[
                    (rope_c, "points.Array.size", "2"),
                    (rope_c, "points.Array.data[0].x", "0"), (rope_c, "points.Array.data[0].y", "0"),
                    (rope_c, "points.Array.data[1].x", "0"),
                    (rope_c, "points.Array.data[1].y", "%.4f" % (eye[1] - top[1])),
                    (rope_c, "pinStart", "1"), (rope_c, "pinEnd", "1"),    # pinEnd ties it to anchorB
                    # longRangeHold: no link further from the tie than its length along the
                    # rope, the load no further than the whole rope - so it cannot stretch
                    (rope_c, "longRangeHold", "1"),
                    (rope_c, "massPerSegment", "%g" % HUNG_LINK), (rope_c, "tensionIterations", "12"),
                    (rope_c, "maxTension", "0"), (rope_c, "breakable", "0")],
                    refs=[(rope_c, "anchorB", anchor)])
                p.stripped_component(key + "/rope", rpid, rsrc, rope_c, 114, "MonoBehaviour", G_ROPE2D)
            continue
        if kind == "enemy":
            src = ENEMIES.get(who)
            if not src:
                print("  no prefab for", who)
                continue
            p.instance("e%d" % i, "Enemies/" + src, src, enemies_t, (fx, fy + 0.1))
        else:
            p.instance("b%d" % i, BARREL, "ExplosiveBarrel", props_t, (fx, fy + 0.4))

    rope_c = rope_component(os.path.join(ASSETS, "Resources", "Prefabs", ROPE + ".prefab"))
    ropes = {}
    for i, sp in enumerate(spawns):
        if sp[0] != "rope":
            continue
        _, key, x0, y0, (x1, y1) = sp
        a, b = local(x0, y0), local(x1, y1)
        k = "rope/" + key
        tether_t, _ = p.go(k, "Rope_" + key, props_t, a, [
            (script_guid("Scripts/Props/Tether2D.cs"),
             "  _rope: {fileID: %d}\n  _cutDamage: 5\n" % fid(p.name, k + "/rope", "stripc")),
            (G_DAMAGEABLE, "  maxHealth: 100000\n  targetLayers:\n    serializedVersion: 2\n"
                           "    m_Bits: 0\n  deathKick: 0\n  config: {fileID: 0}\n"
                           "  takesPhysicsDamage: 0\n  showDamageNumbers: 0\n  bleeds: 0\n"
                           "  bloodColor: {r: 0, g: 0, b: 0, a: 0}\n")])
        rpid, rsrc = p.instance(k + "/r", ROPE, "Rope", tether_t, (0, 0), mods=[
            (rope_c, "points.Array.size", "2"),
            (rope_c, "points.Array.data[0].x", "0"), (rope_c, "points.Array.data[0].y", "0"),
            (rope_c, "points.Array.data[1].x", "%.4f" % (b[0] - a[0])),
            (rope_c, "points.Array.data[1].y", "%.4f" % (b[1] - a[1])),
            (rope_c, "pinStart", "1"), (rope_c, "pinEnd", "0"), (rope_c, "buildOnAwake", "0"),
            (rope_c, "longRangeHold", "1"), (rope_c, "massPerSegment", "%g" % HUNG_LINK)])
        ropes[key] = p.stripped_component(k + "/rope", rpid, rsrc, rope_c, 114, "MonoBehaviour", G_ROPE2D)
    for i, sp in enumerate(spawns):
        if sp[0] != "bridge":
            continue
        _, plank, x0, y0, (x1, y1, count, hangers) = sp
        k = "bridge%d" % i
        bt, _ = p.go(k, "Bridge", props_t, (0, 0), [])
        lt, _ = p.go(k + "/l", "LeftAnchor", bt, local(x0, y0), [])
        rt_, _ = p.go(k + "/r", "RightAnchor", bt, local(x1, y1), [])
        pg = open(os.path.join(ASSETS, "Resources", "Prefabs", "Props", plank + ".prefab.meta")).read()
        pguid = pg.split("guid: ")[1].split()[0]
        hy = "".join("  - rope: {fileID: %d}\n    at: %g\n" % (ropes[rk], t) for rk, t in hangers)
        half = anchor_halfwidth(plank)
        p.docs_add_component(bt, k, G_BRIDGE, (
            "  leftAnchor: {fileID: %d}\n  rightAnchor: {fileID: %d}\n"
            "  segmentPrefab: {fileID: %d, guid: %s, type: 3}\n"
            "  segmentCount: %d\n  autoSegmentLength: 1\n  segmentLength: 1\n"
            "  localAnchorA: {x: %.4f, y: 0}\n  localAnchorB: {x: %.4f, y: 0}\n"
            "  enableBreak: 1\n  breakForce: 15000\n  attachToWorldIfNoRB: 1\n  useFixedOnEnds: 0\n"
            "  useStabilizers: 0\n  stabilizerHeight: 2.5\n  stabilizerEvery: 2\n  stabilizerSlack: 0.2\n"
            "  segmentsRoot: {fileID: 0}\n  buildOnStart: 1\n  pinEnds: 0\n  hangers:\n%s"
            % (lt, rt_, PE.fid("prop", plank, "go"), pguid, count, -half, half, hy)))

    for i, sp in enumerate(spawns):
        if sp[0] != "joint":
            continue
        _, body, aname, conn, f = sp
        bi, bpid, bsrc, bwho, bx, by, bsc = keyed[body]
        ax, ay = anchor_local(bwho, aname)
        at = (bx + ax * bsc, by + ay * bsc)
        body_t = p.stripped("j%d/body" % i, bpid, bsrc, PE.fid("prop", bwho, "t"))
        conn_t = 0
        if conn:
            ci, cpid, csrc, cwho, *_ = keyed[conn]
            conn_t = p.stripped("j%d/conn" % i, cpid, csrc, PE.fid("prop", cwho, "t"))
        f = dict(f)
        kind = f.pop("kind")
        fields = "".join("  %s: %s\n" % kv for kv in f.items())
        p.go("j%d" % i, "Joint_" + bwho, props_t, at, [(script_guid("Scripts/Rooms/PropJoint.cs"),
             "  _body: {fileID: %d}\n  _connectedTo: {fileID: %d}\n  _kind: %d\n%s" % (body_t, conn_t, kind, fields))])

    meta = f"""fileFormatVersion: 2
guid: {guid('Room_' + name + '.prefab')}
PrefabImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""
    return p.text(), meta, root_c[0]


def write_recipe(rooms):
    refs = "".join("  - {fileID: %d, guid: %s, type: 3}\n" % (cid, guid("Room_" + n + ".prefab"))
                   for n, cid in rooms)
    asset = f"""%YAML 1.1
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
  m_Script: {{fileID: 11500000, guid: {G_RECIPE}, type: 3}}
  m_Name: Floor
  m_EditorClassIdentifier: Assembly-CSharp::Rooms.FloorRecipe
  _rooms:
{refs}  _roomCount: {len(rooms)}
  _startRoom: {{fileID: 0}}
  _fillTile: rock_hard
  _fillMaterial: 0
  _margin: 6
  _gap: 5
  _jitter: 0.35
  _extraLinks: 1
  _corridorSize: 1.6
"""
    meta = f"""fileFormatVersion: 2
guid: {guid('Floor.asset')}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 11400000
  userData:
  assetBundleName:
  assetBundleVariant:
"""
    return asset, meta


def put(path, text, force):
    if os.path.exists(path) and not force:
        print("  kept", os.path.relpath(path, ASSETS))
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  wrote", os.path.relpath(path, ASSETS))


def slug(mod):
    return "".join(p.capitalize() for p in mod.ROOM["name"].replace("THE ", "").split())


def main(argv):
    force = "--force" in argv
    names = [a for a in argv[1:] if not a.startswith("--")] or DEFAULT
    os.makedirs(os.path.join(OUT, "Maps"), exist_ok=True)
    done = []
    for n in names:
        mod = importlib.import_module("levels." + n)
        name = slug(mod)
        print(n, "->", name)
        g, spawns = rasterise(mod)
        if n in EXTRAS:
            EXTRAS[n](g, mod)
        rb = room_module(mod)
        if rb and hasattr(rb, "extras"):
            rb.extras(g, mod)
        asset, meta = write_map(name, g)
        put(os.path.join(OUT, "Maps", name + "_Map.asset"), asset, force)
        put(os.path.join(OUT, "Maps", name + "_Map.asset.meta"), meta, force)
        prefab, pmeta, room_cid = build_prefab(name, mod, g, spawns)
        put(os.path.join(OUT, "Room_" + name + ".prefab"), prefab, force)
        put(os.path.join(OUT, "Room_" + name + ".prefab.meta"), pmeta, force)
        done.append((name, room_cid))
    if names == DEFAULT:
        asset, meta = write_recipe(done)
        put(os.path.join(OUT, "Floor.asset"), asset, force)
        put(os.path.join(OUT, "Floor.asset.meta"), meta, force)


if __name__ == "__main__":
    main(sys.argv)
