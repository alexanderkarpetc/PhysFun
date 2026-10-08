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
    open_ = set(a)
    for cells in stubs.values():
        open_ |= cells
    shell = K.shell(open_, ox, oy, w, h)

    # Run the furnish pass to learn where the enemies and kegs stand.
    spawns = []
    mod.stand = lambda name, cx, floor, flip=False, tint=None: spawns.append(("enemy", name, cx - ox, floor - oy))
    mod.keg = lambda x, floor: spawns.append(("barrel", None, x + 4.5 - ox, floor - oy))
    room["furnish"](ox, oy, open_)

    air = {(x - ox, y - oy) for (x, y) in open_}
    shell = {(x - ox, y - oy) for (x, y) in shell}
    return Grid(w, h, air, shell), spawns


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


class Prefab:
    def __init__(self, name):
        self.name = name
        self.docs = []

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

    def instance(self, key, src_rel, name, parent_t, pos):
        """A nested prefab instance of Resources/Prefabs/<src_rel>.prefab."""
        path = os.path.join(ASSETS, "Resources", "Prefabs", src_rel + ".prefab")
        src = open(path + ".meta").read().split("guid: ")[1].split()[0]
        rgo, rt = prefab_root(path)
        pid, sid = fid(self.name, key, "pi"), fid(self.name, key, "st")
        mods = [(rt, "m_LocalPosition.x", "%.4f" % pos[0]), (rt, "m_LocalPosition.y", "%.4f" % pos[1]),
                (rt, "m_LocalPosition.z", "0"), (rt, "m_LocalRotation.w", "1"),
                (rt, "m_LocalRotation.x", "0"), (rt, "m_LocalRotation.y", "0"),
                (rt, "m_LocalRotation.z", "0"), (rgo, "m_Name", name)]
        m = "".join(f"""    - target: {{fileID: {t}, guid: {src}, type: 3}}
      propertyPath: {p}
      value: {v}
      objectReference: {{fileID: 0}}
""" for t, p, v in mods)
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
    for sid, (side, pos, depth) in room["sockets"].items():
        if side in "LR":
            at = local(0 if side == "L" else w, pos)
            size = 1.5
            if entry is None:
                inward = (depth * U + 0.9) * (1 if side == "L" else -1)
                entry = ((at[0] + inward, at[1]), side == "L")
        else:
            at = local(pos, 0 if side == "T" else h)
            size = 1.3
        p.go("socket/" + sid, sid, sockets_t, at,
             [(G_SOCKET, f"  _side: {side_index[side]}\n  _size: {size}\n  _depth: {depth * U:.4f}\n")])
    if entry:
        p.go("entry", "Entry", root_t, entry[0],
             [(G_ENTRY, f"  _id: start\n  _faceRight: {1 if entry[1] else 0}\n")])

    enemies_t, _ = p.go("enemies", "Enemies", root_t, (0, 0), [])
    props_t, _ = p.go("props", "Props", root_t, (0, 0), [])
    for i, (kind, who, x, floor) in enumerate(spawns):
        fx, fy = local(x, floor)
        if kind == "enemy":
            src = ENEMIES.get(who)
            if not src:
                print("  no prefab for", who)
                continue
            p.instance("e%d" % i, "Enemies/" + src, src, enemies_t, (fx, fy + 0.1))
        else:
            p.instance("b%d" % i, BARREL, "ExplosiveBarrel", props_t, (fx, fy + 0.4))

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
