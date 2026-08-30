# Concept sheets

Level concepts are drawn from code so they can be edited, diffed and regenerated —
move a room 4px left and re-run, instead of repainting a png by hand.

```bash
python Assets/GameConcepts/Tools/build.py            # render everything
python Assets/GameConcepts/Tools/build.py coldvault  # render one sheet
```

Output lands in `Assets/GameConcepts/LevelConcept_*.png` (1600x900 = 400x225 native,
upscaled x4 nearest). Pure stdlib, no pip install, no Unity involvement.

## Layout of the tools

| file | what it is |
|---|---|
| `conceptkit.py` | everything shared: palette, primitives, the label font, the props library |
| `levels/*.py` | one scene per level — only what that level contains |
| `build.py` | renders every scene |
| `icons.py` | the 32x32 object icons — see **Object icons** below |


`conceptkit` is the part that should grow. If a new sheet needs a prop that another
sheet could plausibly want (a belt, a gear, a door, a barrel), it belongs in the kit;
if it only makes sense for that one level (a headframe, a frozen mech), keep it local
to the scene file. That split is what keeps a new sheet down to an afternoon's worth
of describing rooms rather than rewriting a renderer.

## Object icons

```bash
python Assets/GameConcepts/Tools/icons.py
```

Writes 55 icons to `Assets/GameConcepts/Icons/Icon_<Name>.png` (**transparent background**,
upscaled x4). Most are 32x32 native, but an icon may declare its own size as a fourth
element of its catalogue entry - `("BlastDoors", "BLAST DOORS", blast_doors, (28, 48))` -
because a door is twice as tall as it is wide and a length of roadway is wider than it is
tall, and squeezing either into the square is what makes it look compressed. The contact
sheet lays mixed sizes out left to right and wraps. and two labelled contact sheets,
`Assets/GameConcepts/IconSheet_Objects.png` and `IconSheet_Lab.png`. Same palette as the level sheets, so an icon
and the thing it stands for on a concept sheet look like the same game.

Six of them are objects the project already has — `Hazards/Conveyor`, `Hazards/Grinder`,
`BridgeBuilder2D`, `StaticObjects/spinning_plank`, `Player/Telekinesis`, `Phys/Fire`. The
other 24 are proposals, and the bar for being on the sheet was that the existing systems
can already express it: a hinge, a kinematic mover, a joint with a break force, a flammable
body, or terrain that loses its support.

| group | icons |
|---|---|
| in the project now | conveyor, grinder, rope bridge, spinning plank, telekinesis, fire |
| machines | winch drum, cage lift, counterweight, piston press, pile driver, saw on a rail |
| hazards | wrecking ball, hung boulder, spike bed, runaway cart, vent/updraft, magnet coil |
| structure | pit prop, timber crib, breakable wall, trapdoor, ore chute, ladder |
| triggers | lever, pressure plate, valve wheel |
| fire and powder | powder keg, fuse line, brazier |
| carried and thrown | boulder, explosive crate, explosive barrel, coal sack |
| track and rolling stock | rail track, mine cart, lab cart — the track is its own icon, the carts sit on nothing |
| lab: power and heat | muffle furnace, dynamo, battery bank, transformer, arc lamp, spark gap (Wimshurst) |
| lab: pressure and gas | gas cylinders, gauges + relief valve, air manifold |
| lab: control | knife-switch board, electromagnet, alarm bell + interlock lamps |
| lab: carried | battery cell, hand magnet |
| lab: containment | blast shield, blast doors, airlock pair, sample cores |

The lab set is for underground laboratory sections - an assay lab, an explosives testing
gallery, or a deep physics lab bored off a haulage level, all of which are real things to
find in a mine. It stays dry on purpose: no beakers or vats, because there is no liquid
simulation - the equivalents are powders, gas, vacuum and hot solids.

A group wider than six wraps onto another row, so a catalogue is not capped by the sheet.
Adding one is a draw function plus a line in `ICONS` or `LAB_ICONS` (each catalogue gets
its own sheet through `build_sheet`). Two things the format needs:

- **Draw through the `R`/`P`/`LN`/`DC` wrappers, not the kit's own primitives.** They add
  the current offset, which is what lets the same function render both its own icon file
  and its cell of the contact sheet.
- **Carryables are drawn empty-handed and container-shaped.** The tub, the trolley and the
  crate are containers; what goes in them is a separate icon. That is why the carts are
  empty and the explosive crate has its lid off - an item's second job is being the thing
  in the cart, and a cart of kegs should not need its own artwork.
- **Every pixel collides, so draw what is solid.** Most 2D games can draw a door as a
  panel facing the camera because the panel lives in a background layer that nothing
  collides with. This game has no such layer - if a pixel is there, it stops you. A door
  is therefore the slab that fills the gap between roof and floor: closed means the pixels
  are in the opening, open means they are gone into a recess. Hazard stripes are what say
  *door* rather than *wall*; a handle and a panelled leaf say nothing at this size and are
  wrong besides. The same test applies to everything else on these sheets: if the art sits
  in a space the player has to walk through, it had better be something they cannot walk
  through.
- **Do not blend against the background.** Icons are drawn on `KEY` (magenta), which
  `save_keyed` turns into alpha 0. `px` deliberately ignores the alpha argument when the
  destination is `KEY` — blending there is how magenta fringes end up in the art. Where you
  want a soft edge, pick a darker colour instead of a lower alpha.

In Unity these want **Point (no filter)** sampling, **no compression**, and for UI use
Sprite (2D and UI); at 4x they can also be dropped in a scene at 20 PPU and stay crisp.

## Mazes

`maze_links(cols, rows, braid=...)` returns `{cell: {neighbour, ...}}` for a maze
generated on the sheet's own `rnd()` — so the layout is part of what the canvas seed
fixes, and a maze sheet still diffs like any other. `braid` re-opens that fraction of
dead ends into loops (0 = a perfect maze, ~0.5 = somewhere you can be chased).
`maze_dead_ends(links)` and `maze_runs(links, horizontal=True, least=3)` are the two
queries the sheets actually place art with: put the working faces and the guards at the
dead ends, and the track, the belt and the sightlines down the straight runs.

`masonry_block(links, cell_box, cols, rows, ...)` draws the built version of a maze for
you: shell, a wall on every edge the maze does not link, a doorway with an `iron_door` on
every edge it does, and a floor hatch with a ladder where the link runs down. `breaches`
names edges as `(cell, 'E')` / `(cell, 'S')` and draws those already broken. It leaves the
cells empty on purpose — furnishing them is the whole scene. `masonry`, `breach`,
`iron_door`, `sconce`, `wall_slot` and `rock_teeth` live in the kit alongside it, and
`STONE`/`STONE_L`/`STONE_D` are the laid-block colours, as against `ROCK_*` country rock.

Cell size is the dial that changes what a block sheet can hold. Sheet 23 runs 9x4 cells at
39x44 and the cells take one prop each; sheets 24-26 run 5x3 at 70x60 — roughly double —
and a bay then has room for machinery, a mezzanine, cover and a fight. Bigger cells also
want something threaded through every wall (`wall_slot` plus a fuse, a line shaft, a cam
shaft) or the bays read as unrelated rooms that happen to share a wall.

The three maze sheets draw the same data three ways — square drifts (21), round bores
following a vein (22), and masonry walls where a link is *absent* (23). That last one is
the trick worth remembering: draw the walls, not the corridors, and the same generator
gives you a built labyrinth instead of a dug one.

## Writing a new sheet

Copy the shape below into `levels/<name>.py`. Everything after `carve_all` is just
placing props at coordinates.

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conceptkit import *

SURF = 50

def build():
    new_canvas(400, 225, seed=1234)     # fixed seed -> a re-run is byte-identical
    sky(SURF)
    rock_mass(SURF)                     # solid ground with strata + topsoil
    carve_all([                         # rooms are hollowed out of it, in reading order
        (8, 70, 180, 120),              # x0, y0, x1, y1
        (200, 130, 320, 190),
    ])

    floor_slab(8, 180, 116)             # a lit floor line under each room
    conveyor(20, 150, 104)
    crate(64, 106)
    humanoid(160, 102, MET_L, GREEN, face_right=False)
    player(66, 100); binny(78, 90)

    vignette()
    title_bar("PHYSFUN - LEVEL CONCEPT 05:  THE NAME")
    callout(6, 26, "1 WHAT THIS ROOM TEACHES", 70, 100)
    legend(6, 190, [
        ("BEATS", CYAN),
        ("ONE LINE PER MECHANIC", (170, 180, 195)),
        ("GOAL: THE WIN CONDITION", GREEN_L),
    ])
    return save(out_path("LevelConcept_TheName.png"))

if __name__ == "__main__":
    build()
```

### Sheets with a spine

16, 17 and 27-29 are the ones the art director keeps coming back to, and they have one
thing in common: a single continuous element crossing the whole sheet, with the rooms hung
off it. A shaft (17), a line shaft through a sawmill (16), an incline (27), the dip of an
ore body (28), a ropeway (29). Two rules that fall out of it:

- **Give the spine its own function, sampled everywhere.** `slope_at(x)` /
  `hanging(x)` / `foot(x)` return the spine's geometry at any x, and every prop on it is
  placed by calling that rather than by hand-tuned coordinates — which is what makes a
  diagonal or a curve cheap enough to draw a hundred props along.
- **A void needs a lit edge to read as a void.** A carve alone is a black shape the same
  value as everything else; what sells it is a bright line under the roof and a `floor_slab`
  -style sill at the bottom. The Great Stope was unreadable until both were in.

### Things learned the hard way

- **Contrast first.** If the rock is as dark as the carved air, every room merges
  into one black blob. `rock_mass(..., base=..., mid=...)` should be clearly lighter
  than the `carve(air=...)` colour.
- **Rooms want floors.** `carve` alone gives a hole; `floor_slab` is what makes it
  read as a place someone stands.
- **The label font is 3x5 and the plates are opaque for a reason.** Check the render
  before shipping: a label plate silently covering a hazard is the most common defect.
  `M`, `N` and `W` are wider glyphs because at 3px they read as `H`, `K` and `V`.
- **Keep callouts out of the art.** Put them on rock, not on the thing they point at,
  and let the leader line do the work.
- **Sheet furniture last.** `vignette()` before `title_bar`/`callout`/`legend`, or the
  darkening eats the text.
- **Never use bare `W` / `H` in a scene.** A scene does `from conceptkit import *`, which
  copies those two by value at import time — when they are still `0` — so `range(W)` in a
  scene silently draws nothing and `slab(0, W - 1, ...)` draws an empty rect. Call
  `canvas_size()` instead: `cw, ch = canvas_size()`. Sheets 02-14 predate this note and
  still read the bare globals in a few places (`coldvault` and `fungalsink` lose a ridge
  line and a grass fringe to it); worth fixing next time one of them is edited.
- **Look at the png.** Every one of these sheets needed two or three passes purely on
  composition; the code being right is not the same as the picture reading right.

### Sheets keep their labels — except where a sheet is asked to drop them

`LevelConcept_DeepCut.png` is the reference: title bar, numbered callouts on leader lines,
BEATS legend in a corner. The callouts are the part that carries the design intent, so a
new sheet ends with `vignette()` and then the sheet furniture, never without it.

Sheets 15 on are the deliberate exception, drawn to order: no title bar, no callouts, no
legend, and no surface layer either — the whole sheet is underground. Two things follow
from that:

- **No `sky()`, and no topsoil band.** `rock_mass(0, soil=ROCK, soil_lit=ROCK_M)` fills the
  canvas edge to edge with stone; passing rock colours as the soil is what stops row 0 from
  reading as a strip of dirt with nothing above it.
- **The art has to say what the callout used to.** Without text, a room only reads if its
  silhouette does: circles chew, chevrons drag, timber holds, ember means it has already
  started. Ceilings get `rock_teeth()` so a carve line does not read as a drawn box, and
  every room wants enough props that the air in it looks occupied rather than empty.

## Existing sheets

| sheet | pitch |
|---|---|
| 02 `scrapworks.py` | industrial opener — telekinesis, then fire, then belt hazards; fill Binny to open the vault |
| 03 `deepcut.py` | a mine held up by wooden props — TerrainSupportSystem as the whole level |
| 04 `coldvault.py` | fire as the key instead of the threat; ice is terrain until it is not |
| 05 `sunkendepot.py` | water kills fire, floats wood, slows everything; drain a floor to open the map |
| 06 `boilerrow.py` | stored pressure as the player's demolition kit — aim at the room, not the guard |
| 07 `fungalsink.py` | the living level: spore clouds are flammable air, caps are soft platforms |
| 08 `railyard.py` | five-tonne cars parked on grades; every one is a held brake |
| 09 `sortingtower.py` | the vertical one — chutes are the fast route and always slightly lethal |
| 10 `acidworks.py` | acid deletes terrain over seconds; the map changes behind you |
| 11 `templevault.py` | stone ruins where every shortcut costs the room you are standing in |
| 12 `magnethall.py` | ceiling coils overrule telekinesis; only wood and stone stay put |
| 13 `ventshafts.py` | air is the level — updrafts, drifting throws, and a draught that carries fire |
| 14 `slagfoundry.py` | a working foundry that has no idea you are in it |
| 15 `quarryteeth.py` | crusher plant, no surface — belts feed meshing wheels, timber holds the west end |
| 16 `timberdeep.py` | the mine's own sawmill: the roof is held up by the stock the saws are cutting |
| 17 `hollowcolumn.py` | one hoist shaft through the whole sheet; everything dropped down it lands on one heap |
| 18 `pendulumworks.py` | weight on chains — the room is a clock, and each arc is floor you cannot use |
| 19 `thewarren.py` | fifty small dirt tunnels; the shortest route between two of them is a wall |
| 20 `cribworks.py` | one slab of roof on six timber cribs — a countable load path per tower |
| 21 `theknot.py` | a real maze of square drifts; faces at the dead ends, track down the straights |
| 22 `veinruns.py` | the same maze bored round and sloped, following ore — ropes, stulls, false leads |
| 23 `assayblock.py` | a masonry labyrinth in a cavern: the only maze here whose walls are worth attacking |
| 24 `powdermagazine.py` | same block, double cells: fifteen powder bays and a fuse main through every wall |
| 25 `windinghouse.py` | the block as a machine — line shafts, winding drums, brakes, and a shaft head through all three floors |
| 26 `stamphall.py` | stamp batteries in every bay, fed by chutes and emptied onto one belt out |
| 27 `theincline.py` | one rope-haulage incline corner to corner, with every room hung off it |
| 28 `thegreatstope.py` | a single slanted void; stulls, staging and ore passes are the only floors in it |
| 29 `thespan.py` | a chasm crossed by a ropeway on two rock pinnacles — buckets, a footbridge, or the long way round |

## Pulley wheel sprites

```bash
python Assets/GameConcepts/Tools/wheels.py            # all three
python Assets/GameConcepts/Tools/wheels.py wood       # just one
python Assets/GameConcepts/Tools/wheels.py --preview  # + PulleyWheels.png, x4, for eyeballing
```

Unlike everything else here these are **game sprites, not concept art**: `wheels.py` writes
80x80 native pngs with real alpha to `Assets/Sprites/Props/PulleyWheel_<Plain|Wood|Metal>.png`,
importer settings cloned from `Sprites/Hazards/Gear.png` (point filter, 40 pixels per unit,
centre pivot). Drop one on a `PulleyWheel2D` and give the `CircleCollider2D` radius `0.975`
and it sits on the drawn rim.

The wheels spin, so the light is radial rather than directional and every feature repeats
around the disc - a wheel lit from the top-left strobes as it turns. The three finishes are
a plain cast disc with four lightening holes, a timber sheave in an iron tyre, and a
five-spoke steel sheave with the web cut right through.
