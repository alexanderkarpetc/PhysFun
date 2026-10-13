"""Room props, part 5: what built rooms are put together from - decks, plank walls, flap
doors and ladders. Not one room's: any room with a house, a keep or a set of decks in it
(S43-S46 so far) is laid out of these, a piece per few pixels, by its roombuild module.

* DeckPlank - 20x4 of timber floor. Static (let into the rock or nailed to the next one)
  and a Props.OneWayPlatform: come up through it from below, stand on it, hold S to drop.
  Laid end to end into a deck; it fills its canvas, so the row reads as one floor.
* WallPlank - 6x12 of upright boards, static, solid. Stacked into a bulkhead or a hut wall.
  Built rooms make walls of these rather than of terrain because terrain only stays up if
  it touches rock, and a bulkhead between two decks touches none.
* Door - 6x30 plank leaf filling a doorway, kinematic, with a Props.Door: the player opens
  it with E (it swings away from them, shown edge-on against the far face of the wall) and
  shuts it with E. Enemies never open one; shut, it blocks them and their sight lines.
* IronDoor - the same Door, in iron: for masonry (the keep). Metal, so it conducts.
* RoofPlank - 20x5 of slate on a board, static and solid, laid along a roof's pitch at
  its angle: you can walk up a roof and stand on its ridge.
* Ladder - not a body at all: a tiled sprite and a Props.Ladder, sized per instance
  (`_height`). See LADDER below and Props/Ladder.cs for why it has no collider.

Built by `roomprops.py`; read its docstring for what the entries mean.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
import propexport as PE  # noqa: E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402,F401
from pixelfix import write_png  # noqa: E402

TITLE = "BUILT ROOMS"
SEED = 9800

DECK_W, DECK_H = 20, 4
WALL_W, WALL_H = 6, 12
DOOR_W, DOOR_H = 6, 30
ROOF_W, ROOF_H = 20, 5
SLATE_D, SLATE, SLATE_L = (74, 42, 36), (112, 66, 54), (150, 94, 72)
LADDER_W, LADDER_STEP = 8, 6


def deck_plank():
    """A length of plank floor edge-on: lit top, the board, nails, a dark underside. It
    fills its canvas so a row of them is one floor with a joint every 20px."""
    for x in range(DECK_W):
        P(x, 0, TIM_L if x % 7 else TIM_M)
        P(x, 1, TIM)
        P(x, 2, TIM if x % 9 else TIM_M)
        P(x, 3, TIM_D)
    P(0, 1, TIM_D)
    P(0, 2, TIM_D)
    for x in (3, 13):
        P(x, 1, IRON_M)


def wall_plank():
    """Upright boards: a lit edge, the board face, a dark edge, a joint at the foot."""
    for y in range(WALL_H):
        P(0, y, TIM_L)
        for x in range(1, WALL_W - 1):
            P(x, y, TIM if (x + y // 3) % 4 else TIM_M)
        P(WALL_W - 1, y, TIM_D)
    for x in range(WALL_W):
        P(x, WALL_H - 1, TIM_D)
    P(2, 3, IRON_M)


def iron_door():
    """The keep's door: an iron leaf edge-on - plate, a rivet line top and bottom, a lit
    edge on the side the light comes from, rust in the dark half."""
    for y in range(DOOR_H):
        for x in range(DOOR_W):
            P(x, y, IRON if (x + y // 2) % 4 else IRON_M)
        P(0, y, IRON_L)
        P(DOOR_W - 1, y, IRON_D)
    for y in (1, 9, 20, DOOR_H - 2):
        for x in range(1, DOOR_W - 1):
            P(x, y, IRON_D if x % 2 else IRON_XL)
    for k in range(10):
        P(1 + (k * 3) % (DOOR_W - 2), 12 + (k * 7) % 14, RUST if k % 2 else RUST_D)
    P(DOOR_W - 2, DOOR_H // 2, IRON_XL)


def door():
    """A plank leaf: dark boards, a rail top and bottom, a brace corner to corner (the
    brace is what says door), an iron strap round the hinge pin at the top."""
    for y in range(DOOR_H):
        for x in range(DOOR_W):
            P(x, y, TIM_D if (x + y) % 5 else TIM)
    for y in (0, 1, DOOR_H - 2, DOOR_H - 1):
        for x in range(DOOR_W):
            P(x, y, TIM_M if y in (0, DOOR_H - 2) else TIM)
    for k in range(DOOR_H - 4):
        P(int(k * (DOOR_W - 1) / (DOOR_H - 5)), 2 + k, TIM_L)
    for x in range(DOOR_W):
        P(x, 2, IRON_M)
    P(DOOR_W // 2, 1, IRON_L)
    P(DOOR_W - 1, DOOR_H // 2, IRON_L)


def roof_plank():
    """Slates on a board, edge-on: a lit top course, two courses of tile with the joints
    staggered, the board under them."""
    for x in range(ROOF_W):
        P(x, 0, SLATE_L if x % 5 else SLATE)
        P(x, 1, SLATE if x % 5 != 2 else SLATE_D)
        P(x, 2, SLATE if x % 5 != 4 else SLATE_D)
        P(x, 3, SLATE_D)
        P(x, 4, TIM_D if x % 6 else TIM)


def ladder_tile():
    """One rung of a ladder: two rails and the rung across them, repeated by the tiling."""
    for y in range(LADDER_STEP):
        P(0, y, TIM_M)
        P(1, y, TIM_D)
        P(LADDER_W - 2, y, TIM_M)
        P(LADDER_W - 1, y, TIM_D)
    for x in range(1, LADDER_W - 1):
        P(x, 1, TIM_L)
        P(x, 2, TIM_D)


GROUPS = [
    ("DECKS, WALLS, DOORS", [
        ("DeckPlank", "DECK PLANK", deck_plank, (DECK_W, DECK_H), WOOD, "oneway"),
        ("WallPlank", "WALL PLANK", wall_plank, (WALL_W, WALL_H), WOOD, None),
        ("Door", "DOOR", door, (DOOR_W, DOOR_H), WOOD, "door"),
        ("IronDoor", "IRON DOOR", iron_door, (DOOR_W, DOOR_H), METAL, "door"),
        ("RoofPlank", "ROOF PLANK", roof_plank, (ROOF_W, ROOF_H), DEFAULT, None),
    ]),
]

STATIC = {"DeckPlank", "WallPlank", "RoofPlank"}
KINEMATIC = {"Door", "IronDoor"}


# ─────────────────────────────────────────────────────────────────────────────
#  The ladder: a tiled sprite and a Props.Ladder, no body
# ─────────────────────────────────────────────────────────────────────────────
LADDER_PREFAB = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {tr}}}
  - component: {{fileID: {sr}}}
  - component: {{fileID: {lc}}}
  m_Layer: 0
  m_Name: Ladder
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &{tr}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!212 &{sr}
SpriteRenderer:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_CastShadows: 0
  m_ReceiveShadows: 0
  m_DynamicOccludee: 1
  m_StaticShadowCaster: 0
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 0
  m_RayTraceProcedural: 0
  m_RayTracingAccelStructBuildFlagsOverride: 0
  m_RayTracingAccelStructBuildFlags: 1
  m_SmallMeshCulling: 1
  m_ForceMeshLod: -1
  m_MeshLodSelectionBias: 0
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:
  - {{fileID: 10754, guid: 0000000000000000f000000000000000, type: 0}}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {{fileID: 0}}
  m_ProbeAnchor: {{fileID: 0}}
  m_LightProbeVolumeOverride: {{fileID: 0}}
  m_ScaleInLightmap: 1
  m_ReceiveGI: 1
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 0
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {{fileID: 0}}
  m_GlobalIlluminationMeshLod: 0
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: -1
  m_MaskInteraction: 0
  m_Sprite: {{fileID: 21300000, guid: {tex}, type: 3}}
  m_Color: {{r: 1, g: 1, b: 1, a: 1}}
  m_FlipX: 0
  m_FlipY: 0
  m_DrawMode: 2
  m_Size: {{x: {w}, y: 2}}
  m_AdaptiveModeThreshold: 0.5
  m_SpriteTileMode: 0
  m_WasSpriteAssigned: 1
  m_SpriteSortPoint: 0
--- !u!114 &{lc}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Props.Ladder
  _height: 2
  _reach: 0.2
"""


def ladder_ids():
    """File ids inside Ladder.prefab, for a room that sets `_height` on an instance."""
    return {k: PE.fid("prop", "Ladder", k) for k in ("go", "t", "sr", "lc")}


def export_ladder():
    meta = os.path.join(PE.ASSETS, "Scripts", "Props", "Ladder.cs.meta")
    if not os.path.exists(meta):
        print("  !! Ladder.cs has no .meta yet (Unity has not imported it): Ladder not written")
        return
    script = open(meta).read().split("guid: ")[1].split()[0]
    new_canvas(LADDER_W, LADDER_STEP, seed=SEED, bg=KEY)
    ladder_tile()
    rows = [[(0, 0, 0, 0) if c == KEY else (c[0], c[1], c[2], 255) for c in row] for row in snapshot()]
    sdir = PE.ensure_dir("Sprites/Props/Rooms")
    png = os.path.join(sdir, "Ladder.png")
    tex = PE.guid("sprite/Ladder")
    write_png(png, rows)
    # full-rect mesh (tiling needs it), pivot at the top centre (the ladder hangs down
    # from its position), repeat wrap
    tm = PE.TEXTURE_META.format(guid=tex, ppu=PE.PPU,
                                sid=__import__("hashlib").md5(b"spriteid/Ladder").hexdigest()[:16] + "0800000000000000")
    tm = (tm.replace("spriteMeshType: 1", "spriteMeshType: 0")
            .replace("alignment: 0", "alignment: 2")
            .replace("spritePivot: {x: 0.5, y: 0.5}", "spritePivot: {x: 0.5, y: 1}")
            .replace("    wrapU: 1\n    wrapV: 1\n", "    wrapU: 0\n    wrapV: 0\n"))
    PE.write_text(png + ".meta", tm)
    ids = ladder_ids()
    pdir = PE.ensure_dir("Resources/Prefabs/Props")
    path = os.path.join(pdir, "Ladder.prefab")
    PE.write_text(path, LADDER_PREFAB.format(go=ids["go"], tr=ids["t"], sr=ids["sr"], lc=ids["lc"],
                                             tex=tex, w=PE._num(LADDER_W / PE.PPU), script=script))
    PE.write_text(path + ".meta", PE.PREFAB_META.format(guid=PE.guid("prefab/Ladder")))
    print("  %-18s %3dx%-3d tiled, no body" % ("Ladder", LADDER_W, LADDER_STEP))


AFTER = [export_ladder]
