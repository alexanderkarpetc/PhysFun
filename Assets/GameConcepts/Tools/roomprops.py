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
`STATIC = {"TeslaCoil"}` makes those prefabs' bodies static (bolted down, still metal,
still burnt and carved), and extra "arc" adds an ArcEmitter whose tip is ANCHORS' "Tip".
`DAMPING = {"Name": 3.0}` sets a prefab's angular damping, extra "oneway" adds a
Props.OneWayPlatform, "door" a Props.Door, "decor" / "wall" a Props.Decor (clutter, walked
through until something hits it; "wall" hangs on the back wall), and `AFTER = [fn]` runs exporters for assets that are not bodies
(the ladder in `roomprops_structures`). `LIGHTS = {"Name": dict(at=(x, y), color=(r, g, b),
intensity=, radius=, flicker=)}` gives a prop a Lighting.LightSource2D whose light comes
from `at` (pixels from the top-left: the flame, the coals) - a lamp that swings swings
its light, and one shot down takes it with it. `SORTING_ORDER = -2` draws every prop of a
part at that sorting order (the cave plants go behind the characters, ladders and terrain).
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

PARTS = ["roomprops_hung", "roomprops_machines", "roomprops_dwellings", "roomprops_rooms",
         "roomprops_structures", "roomprops_decor", "roomprops_flora"]
ICON_DIR = os.path.join("Icons", "Rooms")
SPRITE_DIR = "Sprites/Props/Rooms"
PREFAB_DIR = "Resources/Prefabs/Props"


G_DAMAGEABLE = "baa9384630d24df0977c63474029daee"   # Common/Damageable
G_FUSE = "f1a0ab60ff6834642af8ee11fbd989a0"        # Phys/Explosions/FuseCord


def _explosive(radius=2.0, damage=60, fireball=120):
    """The ExplosiveBarrel's Explosive, read from its prefab and scaled down a little - set
    off by a hit (OnDamage) rather than on death, with a Damageable for hits to land on, so
    a round, a hard knock or a fall sets it off. Fire sets it off through the short fuse on
    top (see FUSE): a flame on the fuse lights it, and it burns down into the charge."""
    path = os.path.join(PE.ASSETS, "Resources", "Prefabs", "Hazards", "ExplosiveBarrel.prefab")
    text = open(path, encoding="utf-8").read()
    block = text.split("Assembly-CSharp::Phys.Explosions.Explosive\n")[1].split("--- !u!")[0]
    for key, val in (("radius", radius), ("damage", damage), ("fireball", fireball)):
        block = re.sub(r"(?m)^(    %s: ).*$" % key, r"\g<1>%s" % val, block, count=1)
    block = re.sub(r"(?m)^  trigger: .*$", "  trigger: 3", block, count=1)       # OnDamage
    hp = ("  maxHealth: 100000\n  targetLayers:\n    serializedVersion: 2\n    m_Bits: 4294967295\n"
          "  deathKick: 0\n  config: {fileID: 0}\n  takesPhysicsDamage: 1\n  showDamageNumbers: 0\n"
          "  bleeds: 0\n  bloodColor: {r: 0, g: 0, b: 0, a: 0}\n")
    return [(PE.G_EXPLOSIVE, "Assembly-CSharp::Phys.Explosions.Explosive", block),
            (G_DAMAGEABLE, "Assembly-CSharp::Common.Damageable", hp)]


# The fuse an explosive prop carries: from a free end 0.3 above its top, down onto it.
FUSE = [(G_FUSE, "Assembly-CSharp::Phys.Explosions.FuseCord",
         "  points:\n  - {x: 0, y: 0.3}\n  - {x: 0, y: 0}\n  pixelsPerUnit: 20\n  burnSpeed: 0.2\n"
         "  litByFire: 1\n  targets: []\n  triggerRadius: 0.25\n  lightOnStart: 0\n"
         "  removeWhenSpent: 1\n")]


def _script_guid(rel):
    """A script's guid, read from the .meta Unity wrote for it (never made up here: a guid
    invented before Unity sees the script is one it throws away)."""
    meta = os.path.join(PE.ASSETS, rel + ".meta")
    if not os.path.exists(meta):
        return None
    return open(meta).read().split("guid: ")[1].split()[0]


def _arc():
    """An ArcEmitter (Scripts/Phys/Electricity): throws a bolt at the nearest metal now and
    then. Its tip is set per prop from ANCHORS["Tip"]; the rest keep the script's defaults."""
    g = _script_guid("Scripts/Phys/Electricity/ArcEmitter.cs")
    if not g:
        print("  !! ArcEmitter.cs has no .meta yet (Unity has not imported it): "
              "written without the emitter - run this again once it has")
        return None
    return [(g, "Assembly-CSharp::Phys.Electricity.ArcEmitter", "{tip}")]


def _light(spec, w, h):
    """A Lighting.LightSource2D for a prop that gives light, from its LIGHTS entry."""
    g = _script_guid("Scripts/Lighting/LightSource2D.cs")
    if not g:
        print("  !! LightSource2D.cs has no .meta yet: written without its light")
        return []
    x, y = spec["at"]
    r, g_, b = spec.get("color", (1.0, 0.74, 0.45))
    fields = ("  color: {r: %s, g: %s, b: %s, a: 1}\n  intensity: %s\n  radius: %s\n"
              "  flicker: %s\n  flickerSpeed: %s\n  offset: {x: %.4f, y: %.4f}\n"
              % (r, g_, b, spec.get("intensity", 1.0), spec.get("radius", 6.0),
                 spec.get("flicker", 0.12), spec.get("flickerSpeed", 7.0),
                 (x - w / 2.0) / PE.PPU, (h / 2.0 - y) / PE.PPU))
    return [(g, "Assembly-CSharp::Lighting.LightSource2D", fields)]


def _script(rel, cls):
    """A component of one of the game's scripts with its own defaults - for the per-room
    machines (RailShuttle, SawBlade); a room sets what differs on its instance."""
    def make():
        g = _script_guid(rel)
        if not g:
            print("  !! %s has no .meta yet (Unity has not imported it): "
                  "written without it - run this again once it has" % rel)
            return None
        return [(g, "Assembly-CSharp::" + cls, "")]
    return make


def _decor(on_wall):
    """Props.Decor: clutter, asleep (static, walked through) until something hits it.
    "wall" is clutter hung on the back wall, which needs nothing under it."""
    def make():
        g = _script_guid("Scripts/Props/Decor.cs")
        if not g:
            print("  !! Decor.cs has no .meta yet (Unity has not imported it): "
                  "written without it - run this again once it has")
            return None
        return [(g, "Assembly-CSharp::Props.Decor", "  onWall: %d\n  knock: 1.2\n" % on_wall)]
    return make


EXTRAS = {None: lambda: None, "explosive": _explosive, "arc": _arc,
          "decor": _decor(0), "wall": _decor(1),
          "shuttle": _script("Scripts/Hazards/RailShuttle.cs", "Hazards.RailShuttle"),
          "saw": _script("Scripts/Hazards/SawBlade.cs", "Hazards.SawBlade"),
          "oneway": _script("Scripts/Props/OneWayPlatform.cs", "Props.OneWayPlatform"),
          "door": _script("Scripts/Props/Door.cs", "Props.Door")}


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
    static = getattr(mod, "STATIC", set())
    kinematic = getattr(mod, "KINEMATIC", set())
    triggers = getattr(mod, "TRIGGER", set())
    damping = getattr(mod, "DAMPING", {})
    lights = getattr(mod, "LIGHTS", {})
    sorting = getattr(mod, "SORTING_ORDER", 0)
    for g, (group, items) in enumerate(mod.GROUPS):
        for i, (name, label, fn, (w, h), material, extra) in enumerate(items):
            new_canvas(w, h, seed=seed0 + g * 101 + i * 7, bg=KEY)
            mp.draw_one(fn)
            outline_outside(w, h)
            rows = [[(0, 0, 0, 0) if c == KEY else (c[0], c[1], c[2], 255) for c in row]
                    for row in snapshot()]
            n = islands(rows)
            comps = EXTRAS[extra]()
            if comps and "{tip}" in comps[0][2]:                  # the emitter's tip, local units
                tx, ty = anchors[name]["Tip"]
                # no ignite: it fires every couple of seconds into metal something is tied to,
                # and a room that burns its own ropes down before anyone walks in is no room
                comps = [(g_, c_, "  _tip: {x: %.4f, y: %.4f}\n  _profile:\n    igniteChancePercent: 0\n"
                          % ((tx - w / 2.0) / PE.PPU, (h / 2.0 - ty) / PE.PPU))
                         for g_, c_, _f in comps]
            if name in lights:
                comps = (comps or []) + _light(lights[name], w, h)
            anc, kids = anchors.get(name), None
            if extra == "explosive":                              # its fuse, on its top
                anc = dict(anc or {}, Fuse=(w / 2.0, 0.0))
                kids = {"Fuse": FUSE}
            path, loops, mass = PE.export(name, rows, SPRITE_DIR, PREFAB_DIR, material, comps,
                                          anchors=anc, child_components=kids, body_type=2 if name in static else 1 if name in kinematic else 0,
                                          trigger=name in triggers,
                                          angular_damping=damping.get(name, 0.05), sorting_order=sorting)
            warn = "" if n == 1 else "   <-- %d bodies, should be one" % n
            print("  %-18s %3dx%-3d %s  mass %7.2f  %d loop(s)%s"
                  % (name, w, h, ("default", "wood", "ice", "metal")[material], mass, loops, warn))
    for after in getattr(mod, "AFTER", ()):                    # assets that are not bodies
        after()
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
