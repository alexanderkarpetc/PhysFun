"""Room props - the loose and moving objects the S-series small rooms are built round,
drawn at game scale and exported as game assets.

    python Assets/GameConcepts/Tools/roomprops.py                    # every part
    python Assets/GameConcepts/Tools/roomprops.py roomprops_hung     # one part

The small-room sheets (`levels/small_NN_*.py`) draw their bells, cages, gas bottles and
idols straight onto the room. `export_rooms.py` can turn the room's rock, timber and steel
into terrain, but a thing that has to fall, swing, roll or be thrown has to be a body of
its own, and until now there was no art for one. This is that art.

Each part is a module next to this one with a `GROUPS` list in the mineprops format plus
two more fields per entry:

    ("Bell", "BELL", bell, (57, 68), METAL, None),
     name    label  draw  size      material  extra ("explosive" or None)

For every entry this writes, through `propexport`:

* `Assets/Sprites/Props/Rooms/<Name>.png` - 1x, PPU 20, readable, point filter;
* `Assets/Resources/Prefabs/Props/<Name>.prefab` - SpriteRenderer + Rigidbody2D +
  PolygonCollider2D traced from the pixels + MaterialView (+ Explosive for "explosive");
* `Assets/GameConcepts/Icons/Rooms/Icon_<Name>.png` and one contact sheet per part,
  `Icons/IconSheet_Rooms_<Part>.png`, every row stood on a floor with the hero for scale.

Same rules as mineprops (read its docstring): one pixel is one 20-PPU sprite pixel, light
from the top left, ordered dither between tones, grime only over drawn pixels, every pixel
collides - so a cage is bars with gaps, a bell is the cup it is - and every prop is one
4-connected body. The script checks that last one and says so when a drawing breaks it.

Hanging things (a bell, a cage, a wrecking ball) are drawn with the eye or bail they hang
from, and without the chain: the chain is a Hazards/Rope set up in the room. A part can
give a module-level `ANCHORS = {"Bell": {"Eye": (x, y)}}` (pixels from the top-left) and
the prefab gets an empty child there - what `export_rooms.py` ties the rope's end to.
"""
import importlib
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mineprops as mp  # noqa: E402
from mineprops import *  # noqa: F403,E402
import propexport as PE  # noqa: E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402,F401

PARTS = ["roomprops_hung", "roomprops_machines", "roomprops_dwellings"]
ICON_DIR = os.path.join("Icons", "Rooms")
SPRITE_DIR = "Sprites/Props/Rooms"
PREFAB_DIR = "Resources/Prefabs/Props"


def _explosive(radius=2.0, damage=60, fireball=120):
    """The ExplosiveBarrel's Explosive, read from its prefab and scaled down a little."""
    path = os.path.join(PE.ASSETS, "Resources", "Prefabs", "Hazards", "ExplosiveBarrel.prefab")
    text = open(path, encoding="utf-8").read()
    block = text.split("Assembly-CSharp::Phys.Explosions.Explosive\n")[1].split("--- !u!")[0]
    for key, val in (("radius", radius), ("damage", damage), ("fireball", fireball)):
        block = re.sub(r"(?m)^(    %s: ).*$" % key, r"\g<1>%s" % val, block, count=1)
    return [(PE.G_EXPLOSIVE, "Assembly-CSharp::Phys.Explosions.Explosive", block)]


EXTRAS = {None: lambda: None, "explosive": _explosive}


def islands(rows):
    """How many 4-connected bodies a drawing is."""
    h, w = len(rows), len(rows[0])
    seen, n = set(), 0
    for y in range(h):
        for x in range(w):
            if rows[y][x][3] and (x, y) not in seen:
                n += 1
                stack = [(x, y)]
                seen.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and rows[ny][nx][3] and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
    return n


def outline_outside(w, h):
    """The kit's `outline`, but only round the outside. Inside a cage the gaps between bars
    are 2px, and ringing both sides of a gap fills it - the bars turn into a plate."""
    out, stack = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + \
        [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in out or not (0 <= x < w and 0 <= y < h) or at(x, y) != KEY:
            continue
        out.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    edge = [(x, y) for (x, y) in out
            if any(0 <= x + dx < w and 0 <= y + dy < h and at(x + dx, y + dy) not in (KEY, INK)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        px(x, y, INK)


def build_part(modname):
    mod = importlib.import_module(modname)
    seed0 = mod.SEED
    anchors = getattr(mod, "ANCHORS", {})
    for g, (group, items) in enumerate(mod.GROUPS):
        for i, (name, label, fn, (w, h), material, extra) in enumerate(items):
            new_canvas(w, h, seed=seed0 + g * 101 + i * 7, bg=KEY)
            mp.draw_one(fn)
            outline_outside(w, h)
            rows = [[(0, 0, 0, 0) if c == KEY else (c[0], c[1], c[2], 255) for c in row]
                    for row in snapshot()]
            n = islands(rows)
            path, loops, mass = PE.export(name, rows, SPRITE_DIR, PREFAB_DIR, material,
                                          EXTRAS[extra](), anchors=anchors.get(name))
            warn = "" if n == 1 else "   <-- %d bodies, should be one" % n
            print("  %-18s %3dx%-3d %s  mass %7.2f  %d loop(s)%s"
                  % (name, w, h, ("default", "wood", "ice", "metal")[material], mass, loops, warn))
    sheet_groups = [(group, [(n, l, f, s) for (n, l, f, s, _m, _e) in items])
                    for group, items in mod.GROUPS]
    part = modname.split("_", 1)[1].capitalize()
    # the sheet redraws every prop through mineprops' own outline; give it this one
    mp.outline = lambda x0, y0, x1, y1, *a, **k: outline_outside(x1 + 1, y1 + 1)
    return mp.build_sheet(sheet_groups, ICON_DIR, os.path.join("Icons", "IconSheet_Rooms_%s.png" % part),
                          "PHYSFUN - ROOM PROPS: " + mod.TITLE, seed0)


def main(argv):
    for modname in [a for a in argv[1:]] or PARTS:
        print(modname)
        build_part(modname)


if __name__ == "__main__":
    main(sys.argv)
