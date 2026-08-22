# Generating enemy sprites that match the Noita art

Working notes from the first pass at generating our own 16×22 enemies with Retro Diffusion,
so the next attempt does not rediscover the same dead ends. Everything here is measured off
the actual files, not guessed.

## What the target actually looks like

Measured across `data/enemies_gfx` of the unpacked Noita data:

| sheet | unique colours (whole sheet) |
|---|---|
| assassin | 6 |
| zombie | 6 |
| coward | 18 |
| 12 enemy sheets combined | 115 |

That is the single most important number. A generated sprite that carries 30+ colours reads as
"from a different game" no matter how good the drawing is — Noita works in flat fills with a
hard edge between tones, not soft ramps. Aim for **≤ 20 colours on a 16×22 sprite**.

Frame geometry: coward is 16×22 with the entity origin at (8, 16). Most humanoids sit in the
16–19 × 16–22 range.

## Retro Diffusion settings that worked

- **Model: RD Fast.** Cheapest, and at this size the expensive models do not buy much.
- **Art style: Low Resolution.** The only preset in the list actually aimed at tiny sprites.
- **Width/Height: 16 × 22.** The minimum the tool allows is 16×16, so our size is right at the
  bottom of its comfort zone — see "known limits" below.
- **Remove Background: on.** This is what produces real alpha. Asking for a transparent
  background in the prompt does nothing.
- **Palette: off.** Forcing a palette wrecked the generation. Recolour in post instead (below).
- **Tiling: off.** That is for seamless textures.
- **Image Count: 4.** All four are paid for whether you look at them or not — always download
  every variant of a batch, not just the one the UI enlarges. Several times the thumbnail we
  ignored was better than the one we opened.
- **Seed:** leave Random while exploring. Once a pose and silhouette land, pin that seed and
  change one phrase at a time — otherwise you cannot tell whether a prompt edit helped or the
  dice just rolled differently.

## Prompt lessons

**Negations do not work and often backfire.** Text encoders handle "no X" poorly, and
`no dithering, no gradient, no background` measurably made things worse. If the tool grows a
negative-prompt field, that is where such phrases belong. In the positive prompt, ask for what
you want instead: `flat shading`, `limited palette of 6 flat colors`, `high contrast`.

**Never say "black".** `hard black outline` turned a whole batch into unreadable near-black
blobs. On a 16×22 sprite the outline is a large share of the pixels, so the word dominates.
Say `dark outline`, or describe the lit side instead.

**Spell out the silhouette.** At this size readability comes from negative space, and the model
will happily fuse head, arms and torso into one column. Phrases that helped:
`strict side view profile`, `facing right`, `full body`, `narrow waist`, `visible neck`,
`one arm extended forward`, `clear gap between arm and body`, `thin separated legs mid stride`.

**Robes and hoods are a trap.** They merge everything into a sack. Lanky, clothed characters
with visible boots and a coat read far better.

Best prompt of the session (19 colours, good contrast, clean alpha — `scavenger_raw.png`):

```
side view, small hunched cultist, hooded robe, thin legs, facing right, full body,
flat shading, limited palette of 6 flat colors, light grey robe with tan trim,
high contrast, legs apart, arm held away from body
```

Next thing to try, combining that colour result with the separated limbs we got later:

```
side view, thin scavenger man wearing ragged coat and heavy boots, facing right,
full body, mid stride walking, one arm extended forward, clear gap between arm and body,
narrow waist, visible neck, flat shading, limited palette of 6 flat colors,
grey coat, dark boots, pale face, high contrast
```

## Post-processing

**The export is an 8× upscale.** Retro Diffusion generates at the requested 16×22 and hands you
a 128×176 png — clean nearest-neighbour, no partial alpha. `tools/pixelfix.py::detect_scale`
finds the factor by looking for the largest integer block size where every block is one flat
colour, and `downscale` recovers the native grid. Lossless; do not resample.

**Recolouring: use a luminance ramp, not nearest colour.** Mapping each pixel to its nearest
Noita colour collapsed 33 colours into 1 — the generated browns have no neighbour anywhere in
Noita's grey-blue-green palette, so everything snapped to the same swatch. What works instead:
take each pixel's relative brightness inside the sprite, quantise it into ~5 steps, and place
those steps along a ramp taken from Noita's palette. Shading survives, hue changes, and the
colour count drops to Noita levels as a side effect. 5 steps looks right; 7 starts to smudge.

The Noita palette splits into hue families, sorted by luminance:

| family | colours | darkest → lightest |
|---|---|---|
| blue | 34 | `#060E0F` → `#C2FCF3` |
| grey | 33 | `#33312D` → `#FFFFFF` |
| green | 19 | `#383D28` → `#E0FFE7` |
| olive | 18 | `#373028` → `#F7E787` |
| red | 11 | `#4F2323` → `#B1A79E` |

Grey is the closest to the general Noita mood; olive is warmer and works for organic creatures.

The 32 most common colours, also in `noita_palette_32.png` (32×1, one pixel per colour, which is
the format palette pickers usually want):

```
#878787 #99B1C7 #6E7E8D #C9CCDF #636363 #DFE8C0 #474E5A #6D8233
#918376 #6B8E7F #A59D6C #9FBB53 #655B51 #833B3B #514836 #4E5C68
#434343 #8A94A9 #BBBBBB #939FB7 #958665 #889BAF #596171 #353E46
#596364 #C7D792 #60818C #938D64 #92A4B6 #79C9D5 #474B6F #B4CA8D
```

## What the ragdoll pipeline needs from a sprite

A generated sprite is only half the job — to leave a corpse it has to be cuttable into parts
(see `Assets/Scripts/Editor/Noita/`, menu `PhysFun ▸ Noita Ragdolls`). That means the silhouette
must have a **visible neck notch and a gap between arm and torso**, otherwise there is nothing
to cut along and the corpse degenerates into "head, blob, two feet". None of the sprites here
clear that bar yet without hand editing; carving a neck and detaching an arm is a ten-pixel
edit, not a redraw.

Also worth knowing: for a creature that is not from Noita there is no `_uv_src` marker sheet, so
per-frame death poses cannot be derived — such a corpse always spawns in its rest pose unless
the poses are authored some other way.

## Known limits

16×22 is at the bottom of what these models can do; every batch trades one quality for another
(colour count vs silhouette vs pose). If we commit to generated art, **generating at 32×44 and
scaling the enemies up in game is far less painful** than fighting for a hit at Noita's size.

## Files here

| file | what it is |
|---|---|
| `scavenger_raw.png` | best generation, 19 colours, native 16×22 |
| `scavenger_grey/olive.png` | same, recoloured onto the Noita ramps |
| `cultist_*.png` | first usable generation, 33 colours — kept for comparison |
| `shade_*.png` | the near-black one; unusable raw, readable after the ramp |
| `noita_palette_32.png` | 32×1 palette image |
| `noita_palette_preview.png` | the same palette as visible swatches |
| `_compare_sheet.png` | coward next to the generations, 8×, for eyeballing |
| `tools/png.py` | dependency-free png reader (handles Noita's palette + colour-key files) |
| `tools/pixelfix.py` | scale detection, downscale, ramp recolour, png writer |
