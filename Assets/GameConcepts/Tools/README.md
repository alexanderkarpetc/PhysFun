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
- **Look at the png.** Every one of these sheets needed two or three passes purely on
  composition; the code being right is not the same as the picture reading right.

### Sheets keep their labels — except where a sheet is asked to drop them

`LevelConcept_DeepCut.png` is the reference: title bar, numbered callouts on leader lines,
BEATS legend in a corner. The callouts are the part that carries the design intent, so a
new sheet ends with `vignette()` and then the sheet furniture, never without it.

Sheets 15-20 are the deliberate exception, drawn to order: no title bar, no callouts, no
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
