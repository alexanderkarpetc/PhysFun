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


`conceptkit` is the part that should grow. If a new sheet needs a prop that another
sheet could plausibly want (a belt, a gear, a door, a barrel), it belongs in the kit;
if it only makes sense for that one level (a headframe, a frozen mech), keep it local
to the scene file. That split is what keeps a new sheet down to an afternoon's worth
of describing rooms rather than rewriting a renderer.

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
