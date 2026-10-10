"""Draw an exported room the way it was written, to check it against its sheet before
anyone presses Play.

    python Assets/GameConcepts/Tools/preview_room.py CoilDome            # Assets/Rooms/Room_CoilDome
    python Assets/GameConcepts/Tools/preview_room.py CoilDome --dir D    # a room exported to D

Reads `Room_<Name>.prefab` and its map - not the sheet - so what comes out is what the
game gets: the terrain cell by cell in its material tiles (40 cells a unit, two a sheet
pixel), every prop prefab instance's own sprite where the instance stands (scaled and
turned), the enemies (drawn with their concept sprite), ropes as lines from their pinned
end to the anchor they tie to, PropJoints as rings, sockets and the entry as marks.
Writes `Tools/room_previews/<Name>.png` at the project root - outside Assets, so Unity
does not import it - x2 again, so a sheet pixel is 4.
"""
import glob
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png import load  # noqa: E402
from pixelfix import write_png  # noqa: E402

ASSETS = os.path.abspath(os.path.join(HERE, "..", ".."))
CPU = 40                      # map cells per unit
AIR = (18, 20, 26)
FILL_TINT = 0.55              # the fill is drawn darker than the room's own rock

CHARS = {"Swat": "RiotBrute", "SoldierArmed": "Grenadier", "Shotgunner": "Pyro", "Wizard": "BloodMage",
         "Bogcap": "WizBogcap", "Bonecrown": "WizBonecrown", "Crimson": "WizCrimson",
         "Deepminer": "WizDeepminer", "Goldhood": "WizGoldhood", "Hollowhood": "WizHollowhood",
         "Maskwraith": "WizMaskwraith", "Ramskull": "WizRamskull"}


def guid_index():
    idx = {}
    for meta in glob.glob(os.path.join(ASSETS, "Resources", "Prefabs", "**", "*.prefab.meta"), recursive=True):
        g = open(meta).read().split("guid: ")[1].split()[0]
        idx[g] = meta[:-5]
    return idx


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


_tex = {}


def tile_px(tile, x, y):
    if tile not in _tex:
        p = os.path.join(ASSETS, "Resources", "Sprites", "Materials", tile + ".png")
        _tex[tile] = load(p) if os.path.exists(p) else (1, 1, [[(255, 0, 255, 255)]])
    w, h, pix = _tex[tile]
    c = pix[(h - 1 - y) % h][x % w]
    return c[:3]


def parse_prefab(path):
    """[(source prefab path, name, x, y, angle, scale, mods dict)] for every nested
    instance, and [(x, y)] for every PropJoint, sockets and the entry."""
    t = open(path, encoding="utf-8").read()
    idx = guid_index()
    out, marks = [], []
    for block in t.split("--- !u!")[1:]:
        if block.startswith("1001 "):
            src = re.search(r"m_SourcePrefab: \{fileID: \d+, guid: (\w+)", block).group(1)
            mods = {}
            for m in re.finditer(r"propertyPath: (\S+)\n\s+value: ?(.*)\n\s+objectReference: \{fileID: (\d+)", block):
                mods[m.group(1)] = m.group(2).strip()
            x, y = float(mods.get("m_LocalPosition.x", 0)), float(mods.get("m_LocalPosition.y", 0))
            qz, qw = float(mods.get("m_LocalRotation.z", 0)), float(mods.get("m_LocalRotation.w", 1))
            ang = math.degrees(2 * math.atan2(qz, qw))
            sc = float(mods.get("m_LocalScale.x", 1))
            out.append((idx.get(src), mods.get("m_Name", "?"), x, y, ang, sc, mods))
    # plain transforms: sockets, entry, joints (by their component's class)
    gos = {}
    for block in t.split("--- !u!")[1:]:
        head = block.split("\n")[0]
        if block.startswith("1 &"):
            gos[head.split("&")[1].strip()] = re.search(r"m_Name: (.*)", block).group(1).strip()
    for block in t.split("--- !u!")[1:]:
        if block.startswith("4 &") and "stripped" not in block.split("\n")[0]:
            go = re.search(r"m_GameObject: \{fileID: (\d+)", block).group(1)
            p = re.search(r"m_LocalPosition: \{x: ([-\d.]+), y: ([-\d.]+)", block)
            name = gos.get(go, "")
            marks.append((name, float(p.group(1)), float(p.group(2))))
    return out, marks


def sprite_of(prefab_path):
    """The png a prefab's SpriteRenderer shows, found through its guid."""
    t = open(prefab_path, encoding="utf-8").read()
    m = re.search(r"m_Sprite: \{fileID: \d+, guid: (\w+)", t)
    if not m:
        return None
    for meta in glob.glob(os.path.join(ASSETS, "Sprites", "**", "*.png.meta"), recursive=True) + \
            glob.glob(os.path.join(ASSETS, "Resources", "**", "*.png.meta"), recursive=True):
        if m.group(1) in open(meta).read():
            return meta[:-5]
    return None


def main(argv):
    name = argv[1]
    d = argv[argv.index("--dir") + 1] if "--dir" in argv else os.path.join(ASSETS, "Rooms")
    W, H, tiles, cells = read_map(os.path.join(d, "Maps", name + "_Map.asset"))
    img = [[AIR] * W for _ in range(H)]
    for cy in range(H):
        for cx in range(W):
            v = cells[cy * W + cx]
            if v:
                c = tile_px(tiles[v - 1], cx, cy)
                if tiles[v - 1] == "rock_hard":
                    c = tuple(int(k * FILL_TINT) for k in c)
                img[H - 1 - cy][cx] = c

    def put(wx, wy, c):
        x, y = int(math.floor(wx * CPU)), H - 1 - int(math.floor(wy * CPU))
        if 0 <= x < W and 0 <= y < H:
            img[y][x] = c

    def line(a, b, c):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * CPU) + 1
        for i in range(n + 1):
            put(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, c)

    insts, marks = parse_prefab(os.path.join(d, "Room_" + name + ".prefab"))
    _sprites = {}
    for src, iname, x, y, ang, sc, mods in insts:
        if not src:
            continue
        base = os.path.basename(src)[:-7]
        if "Rope" in base:            # hung ropes sit under their Tether2D, drawn below
            continue
        if "/Enemies/" in src.replace("\\", "/"):
            ch = os.path.join(ASSETS, "GameConcepts", "Characters", "Char_%s.png" % CHARS.get(base, base))
            if os.path.exists(ch):
                w, h, pix = load(ch)
                foot = max(j for j in range(h) if any(len(q) == 4 and q[3] > 127 for q in pix[j]))
                for j in range(h):
                    for i in range(w):
                        q = pix[j][i]
                        if len(q) == 4 and q[3] > 127:
                            for a in range(2):
                                for b in range(2):
                                    put(x + (i - w / 2) / 20 + a / CPU, y - 0.1 + (foot - j) / 20 + b / CPU, q[:3])
            continue
        if "size.x" in mods:                     # a Conveyor: its belt is tiled to its size
            bw, bh = float(mods["size.x"]), float(mods["size.y"])
            for k in range(int(bh * CPU) + 1):
                line((x - bw / 2, y - bh / 2 + k / CPU), (x + bw / 2, y - bh / 2 + k / CPU),
                     (88, 92, 96) if k else (60, 62, 66))
            continue
        if src not in _sprites:
            sp = sprite_of(src)
            ppu_ = 20.0
            if sp:
                m = re.search(r"spritePixelsToUnits: ([\d.]+)", open(sp + ".meta").read())
                ppu_ = float(m.group(1)) if m else 20.0
            _sprites[src] = (load(sp), ppu_) if sp else None
        spr = _sprites[src]
        if not spr:
            continue
        (w, h, pix), ppu = spr
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        # walk the destination box, sample the sprite (nearest)
        ext = max(w, h) / ppu * sc * 0.75
        for py in range(int((y - ext) * CPU), int((y + ext) * CPU) + 1):
            for pxx in range(int((x - ext) * CPU), int((x + ext) * CPU) + 1):
                lx, ly = (pxx + 0.5) / CPU - x, (py + 0.5) / CPU - y
                u = (ca * lx + sa * ly) / sc
                v = (-sa * lx + ca * ly) / sc
                i, j = int(math.floor(u * ppu + w / 2)), int(math.floor(h / 2 - v * ppu))
                if 0 <= i < w and 0 <= j < h:
                    q = pix[j][i]
                    if len(q) == 4 and q[3] > 127:
                        put((pxx + 0.5) / CPU, (py + 0.5) / CPU, q[:3])

    # tethers: from the tie (the tether's own position) to the anchor it holds
    t = open(os.path.join(d, "Room_" + name + ".prefab"), encoding="utf-8").read()
    stripped = {}
    for m in re.finditer(r"--- !u!4 &(\d+) stripped\nTransform:\n  m_CorrespondingSourceObject: "
                         r"\{fileID: (\d+), guid: \w+, type: 3\}\n  m_PrefabInstance: \{fileID: (\d+)\}", t):
        stripped[m.group(1)] = (m.group(3), m.group(2))
    inst_at = {}
    gi = guid_index()
    for block in t.split("--- !u!")[1:]:
        if block.startswith("1001 "):
            pid = block.split("&")[1].split()[0]
            src = re.search(r"m_SourcePrefab: \{fileID: \d+, guid: (\w+)", block).group(1)
            mx = re.search(r"m_LocalPosition\.x\n\s+value: ([-\d.]+)", block)
            my = re.search(r"m_LocalPosition\.y\n\s+value: ([-\d.]+)", block)
            inst_at[pid] = (gi.get(src), float(mx.group(1)), float(my.group(1)))
    # every rope hangs under its tether (whose position is the tie on the roof) and is tied
    # by anchorB to a stripped anchor inside a prop instance
    t_pos = {}
    for block in t.split("--- !u!")[1:]:
        head = block.split("\n")[0]
        if block.startswith("4 &") and "stripped" not in head:
            q = re.search(r"m_LocalPosition: \{x: ([-\d.]+), y: ([-\d.]+)", block)
            t_pos[head.split("&")[1].strip()] = (float(q.group(1)), float(q.group(2)))
    for block in t.split("--- !u!")[1:]:
        if block.startswith("1001 ") and "points.Array.size" in block and "propertyPath: anchorB" not in block:
            # a rope tied at runtime (a bridge hanger): drawn along its own path
            parent = re.search(r"m_TransformParent: \{fileID: (\d+)\}", block).group(1)
            dx = float(re.search(r"points\.Array\.data\[1\]\.x\n\s+value: ([-\d.]+)", block).group(1))
            dy = float(re.search(r"points\.Array\.data\[1\]\.y\n\s+value: ([-\d.]+)", block).group(1))
            if parent in t_pos:
                a = t_pos[parent]
                line(a, (a[0] + dx, a[1] + dy), (158, 122, 71))
            continue
        if block.startswith("114 &") and "segmentPrefab:" in block:
            # a bridge built at runtime: its deck, anchor to anchor
            la = re.search(r"leftAnchor: \{fileID: (\d+)\}", block).group(1)
            ra = re.search(r"rightAnchor: \{fileID: (\d+)\}", block).group(1)
            if la in t_pos and ra in t_pos:
                (x0, y0), (x1, y1) = t_pos[la], t_pos[ra]
                for k in range(3):
                    line((x0, y0 - k / CPU), (x1, y1 - k / CPU), (149, 120, 80) if k else (96, 76, 54))
            continue
        if not block.startswith("1001 ") or "propertyPath: anchorB" not in block:
            continue
        parent = re.search(r"m_TransformParent: \{fileID: (\d+)\}", block).group(1)
        hook = re.search(r"propertyPath: anchorB\n\s+value: ?\n\s+objectReference: \{fileID: (\d+)\}", block).group(1)
        if parent not in t_pos or hook not in stripped:
            continue
        pid, sfid = stripped[hook]
        src, ix, iy = inst_at[pid]
        pt = open(src, encoding="utf-8").read().split("--- !u!4 &%s\n" % sfid)[1]
        q = re.search(r"m_LocalPosition: \{x: ([-\d.]+), y: ([-\d.]+)", pt)
        line(t_pos[parent], (ix + float(q.group(1)), iy + float(q.group(2))), (158, 122, 71))

    # fuse cords: their own path, from the GameObject they sit on
    go_t = {}
    for block in t.split("--- !u!")[1:]:
        if block.startswith("4 &") and "stripped" not in block.split("\n")[0]:
            g = re.search(r"m_GameObject: \{fileID: (\d+)", block).group(1)
            go_t[g] = block.split("&")[1].split()[0]
    for block in t.split("--- !u!")[1:]:
        if block.startswith("114 &") and "\n  burnSpeed:" in block:
            g = re.search(r"m_GameObject: \{fileID: (\d+)", block).group(1)
            base = t_pos.get(go_t.get(g), (0.0, 0.0))
            pts = [(base[0] + float(a), base[1] + float(b)) for a, b in
                   re.findall(r"  - \{x: ([-\d.]+), y: ([-\d.]+)\}", block.split("  points:")[1].split("pixelsPerUnit")[0])]
            for a, b in zip(pts, pts[1:]):
                line(a, b, (176, 140, 87))

    for mname, x, y in marks:
        if mname in ("L1", "L2", "R1", "R2", "T1", "T2", "B1", "B2"):
            for k in range(-6, 7):
                put(x + k / CPU, y, (121, 201, 213))
                put(x, y + k / CPU, (121, 201, 213))
        elif mname == "Entry":
            for k in range(0, 36):
                put(x, y + k / CPU, (159, 187, 83))
        elif mname.startswith("Joint"):
            for a in range(0, 360, 15):
                put(x + math.cos(math.radians(a)) * 0.15, y + math.sin(math.radians(a)) * 0.15, (240, 190, 80))

    big = []
    for row in img:
        r = []
        for c in row:
            r += [c + (255,)] * 2
        big += [r, r]
    od = os.path.abspath(os.path.join(ASSETS, "..", "Tools", "room_previews"))
    os.makedirs(od, exist_ok=True)
    out = os.path.join(od, name + ".png")
    write_png(out, big)
    print(out)


if __name__ == "__main__":
    main(sys.argv)
