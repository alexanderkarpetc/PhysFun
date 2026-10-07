# Adding an enemy

Enemies are not built by hand in Unity. The art is a grid of letters in Python, a script
turns it into an animated `.aseprite`, and one editor menu turns that into a prefab, an
animator controller and, for walkers, a ragdoll. Change something by editing the source
and rerunning, never by editing the prefab: every rebuild overwrites it (guids are kept,
so scenes stay linked).

Worked examples to copy from:

| kind | art | animation | Unity build |
|---|---|---|---|
| walker (ragdoll on death) | `Assets/GameConcepts/Tools/hooded_mages.py` | `Tools/gen_mages.py` | `Editor/CastBuilder.cs` → *Build Hooded Mages* |
| flier (dissolves on death) | `Assets/GameConcepts/Tools/ghosts.py` | `Tools/gen_ghosts.py` | `Editor/GhostBuilder.cs` → *Build Ghosts* |

## 1. Draw it

One grid per enemy, a palette of letters, facing right, and only the standing pose. Rules
that keep it in the cast's style (they were all learned the hard way):

- grim and muted, not cartoony: dark bodies, 3-5 close tones, light from the top left
- eyes are one or two glowing pixels in a dark socket, never white circles
- enemy glow is red, yellow or green; cyan belongs to the hero
- walkers need two legs (a robe below the belt counts as two), or the corpse is a slab
- held weapons stay well short of the body's height

Run the art script to get `Characters/Char_<Name>.png` and check it next to the cast.

## 2. Animate it

Add the enemy to the generator (`MAGES` in gen_mages.py for a walker, `GHOSTS` in
gen_ghosts.py for a flier) and run it:

    python Tools/gen_mages.py --preview <scratch dir>
    python Tools/gen_ghosts.py --preview <scratch dir>

A walker's spec says which letters below which row are legs (they get redrawn each frame on
an even stride), where the hips are, the box and shoulder of its casting arm, and its
magic colour. A flier is a function of the frame's phase and attack amount.

Tags written: `Idle`, `Walk`, `Shoot` (plus `Death` for fliers), the names the controllers
fire as triggers. `--preview` drops a sheet and a gif somewhere outside the project: look
at it before going to Unity.

## 3. Cut the corpse (walkers only)

    python Tools/gen_mages.py --cuts

prints the `Cuts` rows and the `CastOffset` for every mage, read off the same frame the
ragdoll builder cuts. Paste them into a new `Member` in `CastBuilder.cs`, with health, walk
speed and magic colour. A `Magic` colour makes it cast `EnemyBolt` at the player; leave it
null for a walker that only walks.

## 4. Build it in Unity

**PhysFun → Enemies → Build …** for the group. That fixes the import settings, builds the
controller (one Any State trigger per tag), the prefab under
`Assets/Resources/Prefabs/Enemies/`, and the ragdoll under `Assets/Resources/Ragdolls/`.

Hulls are fitted to the body, not the sprite: `SoldierBuilder.CoreRect` keeps the rows
about half as wide as the widest and the columns that are mostly ink, so tendrils, trails
and weapons do not count. Walkers keep their full height; fliers get their root moved into
the middle of that core.

The prefab then shows up in **Tools → PhysFun → Object Placer**; drop it into a room under
its `Spawns` object.

## Shortcuts

- New art in an existing enemy: rerun step 2, then the menu. For a walker, rerun step 3
  too if the outline moved.
- Health, speed, damage, range: edit the row in the builder and rerun the menu, not the
  prefab.
- Behaviour: `Enemy/RegularEnemyController.cs` (walk, look, cast) and
  `Enemy/GhostController.cs` (hover, path round walls, lunge or spit). Both are shared, so
  a change there reaches every enemy that uses them.
