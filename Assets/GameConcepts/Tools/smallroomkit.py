"""Small rooms: the kit the S-series sheets and the floor stitch are drawn with.

A small room is roughly 300-460 game pixels a side - about one screen across - and is
meant to be joined to others into one terrain, Enter the Gungeon style, rather than
loaded on its own. So on top of roomkit it has:

* sockets - the short passages from a room's air to its template edge that a generator
  joins rooms by (L/R at a floor line, T/B at a centre line). A socket nobody joins is
  left as rock;
* the shell - each room keeps ~SHELL px of its own rock round its air, and the rest of
  its template box is fill: the same Default rock as between rooms, under a colder tile;
* `lay`, which paints fill, rooms, stubs and corridors and then furnishes the rooms;
* `room_sheet`, one room on its own sheet with every socket open.

A room is a dict:

    {"name": "THE HOPPER", "w": 380, "h": 420,
     "shapes": [([cave_mask shapes in local coords], rough), ...],
     "sockets": {"T1": ("T", x, depth), "L1": ("L", floor_y, depth), ...},
     "edit": optional fn(air, ox, oy) -> air      (cut plinths, flatten floors),
     "furnish": fn(ox, oy, air)                    (props and enemies, sheet coords)}

`depth` is how far in from the template edge a socket's stub starts, i.e. where it
meets the room's own air.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from roomkit import *  # noqa: F403,E402

AIR = CAVE
LAMP = (255, 214, 140)
FILL = (41, 44, 54)          # the fill: Default rock under its own, colder tile
FILL_D = (30, 32, 40)
FILL_M = (53, 57, 69)
FILL_L = (76, 81, 97)
SOCKET = (121, 201, 213)     # socket markers
PLUG = (150, 160, 180)
ORE = (138, 112, 64)
KEG = (96, 62, 40)
KEG_L = (134, 92, 58)
COPPER = (168, 102, 62)
COPPER_L = (214, 146, 96)

SHELL = 20                   # how much of its own rock a room keeps round its air


# ─────────────────────────────────────────────────────────────────────────────
#  Sockets
# ─────────────────────────────────────────────────────────────────────────────
def stub(side, pos, depth, w, h):
    """The short passage from inside a room to its template edge that a socket is.
    L/R: `pos` is the floor line; T/B: `pos` is the centre line. `depth` is how far in
    from the edge it starts, i.e. where it meets the room's own air."""
    if side == "L":
        return ("tube", [(depth, pos - 15), (-8, pos - 15)], 15)
    if side == "R":
        return ("tube", [(w - depth, pos - 15), (w + 8, pos - 15)], 15)
    if side == "T":
        return ("tube", [(pos, depth), (pos, -8)], 13)
    return ("tube", [(pos, h - depth), (pos, h + 8)], 13)


def socket_point(room, sid, ox, oy):
    """Where a socket meets the template edge, in sheet coordinates (floor for L/R)."""
    side, pos, _ = room["sockets"][sid]
    w, h = room["w"], room["h"]
    return {"L": (ox, oy + pos), "R": (ox + w, oy + pos),
            "T": (ox + pos, oy), "B": (ox + pos, oy + h)}[side]


def shift(sh, ox, oy):
    if sh[0] == "blob":
        return ("blob", sh[1] + ox, sh[2] + oy, sh[3], sh[4])
    return ("tube", [(x + ox, y + oy) for x, y in sh[1]], sh[2])


def room_masks(room, ox, oy):
    """(air of the room itself, {socket id: air of that socket's stub}), in sheet
    coordinates, both clipped to the template box."""
    w, h = room["w"], room["h"]

    def clip(m):
        return {(x, y) for (x, y) in m if ox <= x < ox + w and oy <= y < oy + h}

    air = set()
    for shapes, rough in room["shapes"]:
        air |= cave_mask([shift(s, ox, oy) for s in shapes], rough=rough, top=0)
    if room.get("edit"):
        air = room["edit"](air, ox, oy)
    stubs = {}
    for sid, (side, pos, depth) in room["sockets"].items():
        stubs[sid] = clip(cave_mask([shift(stub(side, pos, depth, w, h), ox, oy)],
                                    rough=0.05, top=0)) - air
    return clip(air), stubs


def shell(air, ox, oy, w, h):
    """Rock the room keeps: every template pixel within ~SHELL of its air (two-pass
    chamfer distance), with a wobbling edge so the join to the fill is not a contour."""
    INF = 10 ** 6
    d = [[INF] * w for _ in range(h)]
    for (x, y) in air:
        d[y - oy][x - ox] = 0
    for y in range(h):
        row, up = d[y], d[y - 1] if y else None
        for x in range(w):
            v = row[x]
            if x and row[x - 1] + 3 < v:
                v = row[x - 1] + 3
            if up:
                if up[x] + 3 < v:
                    v = up[x] + 3
                if x and up[x - 1] + 4 < v:
                    v = up[x - 1] + 4
                if x + 1 < w and up[x + 1] + 4 < v:
                    v = up[x + 1] + 4
            row[x] = v
    for y in range(h - 1, -1, -1):
        row, dn = d[y], d[y + 1] if y + 1 < h else None
        for x in range(w - 1, -1, -1):
            v = row[x]
            if x + 1 < w and row[x + 1] + 3 < v:
                v = row[x + 1] + 3
            if dn:
                if dn[x] + 3 < v:
                    v = dn[x] + 3
                if x + 1 < w and dn[x + 1] + 4 < v:
                    v = dn[x + 1] + 4
                if x and dn[x - 1] + 4 < v:
                    v = dn[x - 1] + 4
            row[x] = v
    out = set()
    for y in range(h):
        for x in range(w):
            r = SHELL + 6 * math.sin(x * 0.047 + 1.3) * math.cos(y * 0.039) + 3 * math.sin((x + y) * 0.13)
            if 0 < d[y][x] <= r * 3:
                out.add((x + ox, y + oy))
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  Painting the ground
# ─────────────────────────────────────────────────────────────────────────────
def paint_fill():
    """Whole sheet in fill: Default rock, cold tile, cracked on a slant so it reads as
    one mass rather than as more room."""
    cw, ch = canvas_size()
    rect(0, 0, cw - 1, ch - 1, FILL)
    for y in range(ch):
        for x in range(cw):
            r = rnd()
            if r < 0.12:
                px(x, y, FILL_D)
            elif r < 0.19:
                px(x, y, FILL_M)
    for _ in range(cw * ch // 2600):
        x, y = rnd() * cw, rnd() * ch
        n = 6 + int(rnd() * 22)
        for i in range(n):
            px(x + i, y + i * 0.35, FILL_D if chance(0.7) else INK, 0.8)


def paint_rock(cells):
    for (x, y) in cells:
        r = rnd()
        px(x, y, ROCK_D if r < 0.13 else ROCK_M if r < 0.2 else ROCK)


def carve_all_air(air, rock):
    """Air with a lit floor edge and a dark ceiling lip - in the room's rock colours
    where the edge is room rock, in the fill's where it is fill."""
    for p in air:
        px(p[0], p[1], AIR)
    for (x, y) in air:
        mine = (x, y) in rock or (x, y + 1) in rock or (x, y - 1) in rock
        if (x, y - 1) not in air:
            px(x, y, CAVE_L, 0.5)
            px(x, y - 1, ROCK_D if mine else FILL_D)
        if (x, y + 1) not in air:
            px(x, y + 1, ROCK_L if mine else FILL_L)
            if (x, y + 2) not in air:
                px(x, y + 2, ROCK_M if mine else FILL_M)


def dashed_edge(cells, c=PLUG, a=0.75):
    for (x, y) in cells:
        if (x + y) % 4 < 2:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in cells:
                px(x, y, c, a)
                break


def dashed_box(x0, y0, x1, y1, c=(110, 122, 140)):
    for x in range(x0, x1 + 1, 8):
        rect(x, y0, min(x + 3, x1), y0, c, 0.7)
        rect(x, y1, min(x + 3, x1), y1, c, 0.7)
    for y in range(y0, y1 + 1, 8):
        rect(x0, y, x0, min(y + 3, y1), c, 0.7)
        rect(x1, y, x1, min(y + 3, y1), c, 0.7)


# ─────────────────────────────────────────────────────────────────────────────
#  Props local to these rooms
# ─────────────────────────────────────────────────────────────────────────────
def keg(x, floor):
    """Powder keg, 9x11: staves, two iron hoops and a red stencil band."""
    rect(x + 1, floor - 11, x + 7, floor - 1, KEG)
    rect(x, floor - 9, x + 8, floor - 3, KEG)
    rect(x + 1, floor - 11, x + 7, floor - 11, KEG_L)
    for yy in (floor - 9, floor - 3):
        rect(x, yy, x + 8, yy, MET_D)
    rect(x + 2, floor - 7, x + 6, floor - 5, RED_L)
    px(x + 2, floor - 10, KEG_L)


def crate_g(x, floor, s=12):
    rect(x, floor - s, x + s, floor - 1, WOOD)
    frame(x, floor - s, x + s, floor - 1, WOOD_D)
    line(x, floor - s, x + s, floor - 1, WOOD_D)
    rect(x + 1, floor - s, x + s - 1, floor - s, WOOD_L)


def tub_cart():
    """Ore tub on its wheels, drawn upright on a 32x20 canvas for draw_rotated."""
    rect(2, 3, 29, 13, MET)
    rect(2, 3, 29, 3, MET_XL)
    rect(3, 4, 28, 6, (58, 46, 34))
    for i in range(14):
        disc(5 + i * 1.7, 3 - (i % 3), 1.6, pick([ORE, DIRT_L, ROCK_L]))
    rect(2, 12, 29, 14, MET_D)
    for wx in (8, 23):
        disc(wx, 16, 3.2, INK)
        disc(wx, 16, 1.4, MET_L)


def tesla(cx, base):
    """ArcField source: a copper coil on a slate foot under an iron toroid."""
    rect(cx - 9, base - 6, cx + 9, base - 1, (60, 64, 70))
    rect(cx - 9, base - 6, cx + 9, base - 6, MET_L)
    for y in range(base - 46, base - 6):
        rect(cx - 5, y, cx + 5, y, COPPER if y % 2 else COPPER_L)
    rect(cx - 1, base - 52, cx + 1, base - 46, MET_D)
    for y in range(-6, 7):
        half = int(17 * math.sqrt(max(0.0, 1 - (y / 6.5) ** 2)))
        rect(cx - half, base - 58 + y, cx + half, base - 58 + y, MET if y > -3 else MET_L)
    glow(cx, base - 58, 70, CYAN, 0.18)


def hung_grate(x0, x1, y, chains, roof):
    """A steel grate walkway on chains - the only floor at that height, and metal."""
    rect(x0, y, x1, y + 2, MET_D)
    rect(x0, y, x1, y, MET_L)
    for x in range(int(x0) + 2, int(x1), 4):
        px(x, y + 1, INK)
    for cx in chains:
        chain(cx, roof(cx), y)


def cage(cx, top, bottom, roof):
    chain(cx, roof, top)
    rect(cx - 9, top, cx + 9, top + 1, MET_D)
    rect(cx - 9, bottom, cx + 9, bottom + 1, MET_D)
    for x in range(cx - 9, cx + 10, 4):
        rect(x, top, x, bottom, MET)
    rect(cx - 5, bottom - 3, cx + 4, bottom - 1, (150, 146, 128))   # what is left in it
    px(cx + 5, bottom - 4, (150, 146, 128))


def stull(x, y0, y1):
    """Timber post roof to floor, with a headboard - burnable, and holding something."""
    beam(x, y0, y1, 3, WOOD, WOOD_L)
    rect(x - 4, y0, x + 7, y0 + 2, WOOD_D)


def teeth(m, x0, x1, yref, n=10, rock=True):
    """Rock hanging off a curved roof: short tapered points, so a carve edge stops
    reading as a drawn line."""
    for _ in range(n):
        x = int(x0 + rnd() * (x1 - x0))
        top = ceil_at(m, x, yref) + 1
        ln = 3 + int(rnd() * 8)
        for i in range(ln):
            half = max(0, int((ln - i) / 3))
            rect(x - half, top + i, x + half, top + i, ROCK_M if rock else FILL_M)
        px(x, top + ln - 1, ROCK_L if rock else FILL_L)



# ─────────────────────────────────────────────────────────────────────────────
#  Laying rooms down
# ─────────────────────────────────────────────────────────────────────────────
def lay(placed, used, corridors, ladders=()):
    """Paint fill, rooms, the stubs of used sockets and the corridors, then furnish.
    `placed` = [(room, ox, oy)], `used` = {(room name, socket id)} or None for all open.
    Returns (air, {(name, sid): stub cells}) so the sheet can label what it wants."""
    paint_fill()
    air, rock, plugs, info = set(), set(), {}, []
    for room, ox, oy in placed:
        a, stubs = room_masks(room, ox, oy)
        open_ = set(a)
        for sid, cells in stubs.items():
            if used is None or (room["name"], sid) in used:
                open_ |= cells
            else:
                plugs[(room["name"], sid)] = cells
        r = shell(open_, ox, oy, room["w"], room["h"])
        paint_rock(r)
        rock |= r
        air |= open_
        info.append((room, ox, oy))
    for pts, r in corridors:
        air |= cave_mask([("tube", pts, r)], rough=0.06, top=0)
    carve_all_air(air, rock)
    for cells in plugs.values():
        dashed_edge(cells)
    for x, y0, y1 in ladders:
        ladder(x - 3, y0, y1, w=6, step=6)
    for room, ox, oy in info:
        room["furnish"](ox, oy, air)
    return air, plugs


def socket_tags(room, ox, oy):
    """Socket ids at the template edge, in the marker colour, with a tick on the edge."""
    for sid, (side, pos, _) in room["sockets"].items():
        x, y = socket_point(room, sid, ox, oy)
        if side in "LR":
            rect(x - 1, y - 30, x, y, SOCKET)
            tx = x - btext_w(sid) - 8 if side == "L" else x + 8
            btag(tx, y - 24, sid, SOCKET)
        else:
            rect(x - 13, y - 1, x + 13, y, SOCKET)
            ty = y - 26 if side == "T" else y + 10
            btag(x - btext_w(sid) // 2, ty, sid, SOCKET)



# ─────────────────────────────────────────────────────────────────────────────
#  One room, one sheet
# ─────────────────────────────────────────────────────────────────────────────
SMALL_DIR = os.path.abspath(os.path.join(HERE, "..", "Rooms"))


def small_path(name):
    os.makedirs(SMALL_DIR, exist_ok=True)
    return os.path.join(SMALL_DIR, name)


def room_sheet(room, code, callouts, beats, seed):
    """One small room on its own sheet, every socket open and tagged.

    `callouts` = [(text, (label x, label y), (anchor x, anchor y))], both in the room's
    local coordinates (labels may sit outside the template, in the margin).
    `beats` = [(line, colour)], under a BEATS header at the foot of the sheet."""
    w, h = room["w"], room["h"]
    cw, ch = max(640, w + 260), h + 240
    new_canvas(cw, ch, seed=seed)
    label_scale(2)
    ox, oy = (cw - w) // 2, 84
    lay([(room, ox, oy)], None, [])
    dashed_box(ox, oy, ox + w - 1, oy + h - 1)
    vignette(0.25)
    socket_tags(room, ox, oy)
    btitle_bar("PHYSFUN - SMALL ROOM %s:  %s" % (code, room["name"]),
               "%dX%d / GAME SCALE" % (w, h))
    for text, (lx, ly), (ax, ay) in callouts:
        bcallout(ox + lx, oy + ly, text, ox + ax, oy + ay)
    blegend(16, oy + h + 54, [("BEATS", CYAN)] + list(beats), cw - 40)
    slug = "".join(p.capitalize() for p in room["name"].replace("THE ", "").split())
    return save(small_path("RoomConcept_%s_%s.png" % (code, slug)), scale=2)

