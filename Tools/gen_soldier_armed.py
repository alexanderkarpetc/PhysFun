"""
Builds a gun-less copy of the Soldier and a prefab that carries one of the
separate weapon sprites instead.

Reads Assets/Sprites/Enemies/soldier.aseprite, drops every pixel that belongs to
the baked-in rifle, and writes:

  Assets/Resources/Animations/Enemies/SoldierArmed/soldier_body.png   (+ .meta)
  Assets/Resources/Animations/Enemies/SoldierArmed/SoldierBodyIdle|Walk|Shoot.anim
  Assets/Resources/Animations/Enemies/SoldierArmed/SoldierBodyAnimator.controller
  Assets/Resources/Prefabs/Enemies/SoldierArmed.prefab
  Assets/Resources/Ragdolls/soldier_armed/                 (corpse, same treatment)

The prefab carries a WeaponHolder pointing at one of the WeaponDefinition assets
gen_weapon_sprites.py writes, so the gun is a single field on the root object and
can be swapped on a scene instance without entering play mode.

soldier.aseprite and the old SoldierAnimator are never touched.  The weapon is a
child of View so it flips with the body; its per-frame offset is keyed in the
clips so it rides the walk/idle bob instead of floating.  The corpse gets the
same rifle-free parts sheet plus the weapon as a sixth, unhinged piece, so the
gun tumbles away from the body instead of vanishing with it.

    python Tools/gen_soldier_armed.py [weapon]      # any name in gen_weapon_sprites.GUNS
"""
import hashlib
import os
import struct
import sys
import zlib

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_weapon_sprites import GUNS, guid_for as weapon_guid  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, 'Assets', 'Sprites', 'Enemies', 'soldier.aseprite')
ANIM_DIR = os.path.join(ROOT, 'Assets', 'Resources', 'Animations', 'Enemies', 'SoldierArmed')
PREFAB = os.path.join(ROOT, 'Assets', 'Resources', 'Prefabs', 'Enemies', 'SoldierArmed.prefab')
# Snapshot of the stock soldier corpse. It lives here rather than in Assets
# because the armed version replaced it there and the originals were cleaned up.
RAG_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'soldier_ragdoll_src')
RAG_DIR = os.path.join(ROOT, 'Assets', 'Resources', 'Ragdolls', 'soldier_armed')

# What the stock soldier corpse is wired with; everything here gets swapped for a
# freshly generated id so the two ragdolls never share an asset.
OLD_PARTS_GUID = '977098cb67ed1864a98c7303577eea82'
OLD_DEF_GUID = '486d55fff93cb5c468b1c627d0e0c90c'
OLD_RAGDOLL_GUID = 'eb0ac9f1557752f48a9d1360813d012c'
RAG_ROOT_TR = 1593549879951695390

PPU = 20
COLS = 8
FPS = 10.0
HAND = (10, 13)   # trigger hand, in canvas pixels of the reference frame (y down)
TAGS = [('Idle', 0, 4), ('Walk', 5, 10), ('Shoot', 11, 15)]

# The olive/grey shades the rifle is drawn with. Nothing else on the sprite uses them.
GUN_COLORS = {(88, 94, 77, 255), (118, 133, 94, 255), (100, 110, 83, 255),
              (137, 153, 111, 255), (60, 71, 72, 255), (132, 137, 125, 255),
              (111, 114, 106, 255)}


# ----------------------------------------------------------------- aseprite --
def read_aseprite(path):
    d = open(path, 'rb').read()
    _, _, nframes, w, h, _ = struct.unpack_from('<IHHHHH', d, 0)
    off, frames = 128, []
    for _ in range(nframes):
        fbytes, _, oldn, _dur, newn = struct.unpack_from('<IHHH2xI', d, off)
        img, co = Image.new('RGBA', (w, h)), off + 16
        for _ in range(newn or oldn):
            csize, ctype = struct.unpack_from('<IH', d, co)
            if ctype == 0x2005:                                    # cel
                _li, x, y, _op, celtype = struct.unpack_from('<HhhBH', d, co + 6)
                if celtype == 2:                                   # zlib image
                    cw, ch = struct.unpack_from('<HH', d, co + 22)
                    px = zlib.decompress(d[co + 26:co + csize])
                    img.alpha_composite(Image.frombytes('RGBA', (cw, ch), px), (x, y))
            co += csize
        frames.append(img)
        off += fbytes
    return frames, w, h


def strip_gun(img):
    """Returns (image without the rifle, top-left of the rifle's bounding box)."""
    out = img.copy()
    p = out.load()
    gun = [(x, y) for y in range(out.height) for x in range(out.width)
           if p[x, y] in GUN_COLORS]
    for x, y in gun:
        p[x, y] = (0, 0, 0, 0)
    if not gun:
        return out, None
    return out, (min(x for x, _ in gun), min(y for _, y in gun))


def close_gun_gap(stripped, original):
    """Reconnect the forearm to the torso where the rifle used to bridge them.

    The soldier is drawn with the gun crossing his chest, so on most frames the
    torso stops at one side of it and the forward arm picks up on the other.
    Take the gun out and those two are no longer touching: a two-pixel hole
    opens mid-body, and no held weapon reliably covers it — a pistol is nowhere
    near it and even a rifle only fills one of the two rows.

    Only pixels the strip removed are candidates, so the gap between the legs —
    which was never gun — is left alone.
    """
    p, q = stripped.load(), original.load()
    for y in range(stripped.height):
        for x in range(stripped.width):
            if p[x, y][3] or not q[x, y][3]:
                continue
            left = next((p[i, y] for i in range(x - 1, -1, -1) if p[i, y][3]), None)
            right = next((p[i, y] for i in range(x + 1, stripped.width) if p[i, y][3]), None)
            if left and right:
                p[x, y] = left


# ---------------------------------------------------------------------- ids --
def guid(key):
    return hashlib.md5(('physfun/soldier-armed/' + key).encode()).hexdigest()


def file_id(key):
    """A stable, positive 32-bit id, the way Unity writes sprite internal ids."""
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def sprite_id(key):
    return hashlib.md5(('sprite/' + key).encode()).hexdigest()[:16] + '0800000000000000'


NATIVE_META = ('fileFormatVersion: 2\nguid: {guid}\nNativeFormatImporter:\n'
               '  externalObjects: {{}}\n  mainObjectFileID: {main}\n  userData: \n'
               '  assetBundleName: \n  assetBundleVariant: \n')
FOLDER_META = ('fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n'
               '  externalObjects: {{}}\n  userData: \n  assetBundleName: \n'
               '  assetBundleVariant: \n')


# ------------------------------------------------------------------ texture --
SPRITE_ENTRY = """    - serializedVersion: 2
      name: {name}
      rect:
        serializedVersion: 2
        x: {x}
        y: {y}
        width: {w}
        height: {h}
      alignment: 9
      pivot: {{x: 0.5, y: 0}}
      border: {{x: 0, y: 0, z: 0, w: 0}}
      outline: []
      physicsShape: []
      tessellationDetail: -1
      bones: []
      spriteID: {sid}
      internalID: {iid}
      vertices: []
      indices:
      edges: []
      weights: []"""


def sheet_meta(sprites, tex_guid):
    entries, mapping, table = [], [], []
    for name, rect, iid, sid in sprites:
        entries.append(SPRITE_ENTRY.format(name=name, x=rect[0], y=rect[1],
                                           w=rect[2], h=rect[3], sid=sid, iid=iid))
        mapping.append('  - first:\n      213: {iid}\n    second: {name}'.format(
            iid=iid, name=name))
        table.append('      {name}: {iid}'.format(name=name, iid=iid))
    return TEXTURE_META.format(guid=tex_guid, mapping='\n'.join(mapping),
                               entries='\n'.join(entries), table='\n'.join(table),
                               ppu=PPU)


TEXTURE_META = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable:
{mapping}
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 0
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 2
  spriteExtrude: 1
  spriteMeshType: 0
  alignment: 9
  spritePivot: {{x: 0.5, y: 0}}
  spritePixelsToUnits: {ppu}
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 0
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings:
  - serializedVersion: 4
    buildTarget: DefaultTexturePlatform
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 0
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
  spriteSheet:
    serializedVersion: 2
    sprites:
{entries}
    outline: []
    customData:
    physicsShape: []
    bones: []
    spriteID:
    internalID: 0
    vertices: []
    indices:
    edges: []
    weights: []
    secondaryTextures: []
    nameFileIdTable:
{table}
  mipmapLimitGroupName:
  pSDRemoveMatte: 0
  userData:
  assetBundleName:
  assetBundleVariant:
"""


# -------------------------------------------------------------------- clips --
POS_KEY = """      - serializedVersion: 3
        time: {t}
        value: {{x: {x}, y: {y}, z: 0}}
        inSlope: {{x: Infinity, y: Infinity, z: Infinity}}
        outSlope: {{x: Infinity, y: Infinity, z: Infinity}}
        tangentMode: 103
        weightedMode: 0
        inWeight: {{x: 0.33333334, y: 0.33333334, z: 0.33333334}}
        outWeight: {{x: 0.33333334, y: 0.33333334, z: 0.33333334}}"""

CLIP = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  serializedVersion: 7
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves: []
  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:
  - curve:
      serializedVersion: 2
      m_Curve:
{pos}
      m_PreInfinity: 2
      m_PostInfinity: 2
      m_RotationOrder: 4
    path: Weapon
  m_ScaleCurves: []
  m_FloatCurves: []
  m_PPtrCurves:
  - serializedVersion: 2
    curve:
{pptr}
    attribute: m_Sprite
    path:
    classID: 212
    script: {{fileID: 0}}
    flags: 2
  m_SampleRate: 60
  m_WrapMode: 0
  m_Bounds:
    m_Center: {{x: 0, y: 0, z: 0}}
    m_Extent: {{x: 0, y: 0, z: 0}}
  m_ClipBindingConstant:
    genericBindings:
    - serializedVersion: 2
      path: 0
      attribute: 0
      script: {{fileID: 0}}
      typeID: 212
      customType: 23
      isPPtrCurve: 1
      isIntCurve: 0
      isSerializeReferenceCurve: 0
    - serializedVersion: 2
      path: 1855955664
      attribute: 1
      script: {{fileID: 0}}
      typeID: 4
      customType: 0
      isPPtrCurve: 0
      isIntCurve: 0
      isSerializeReferenceCurve: 0
    pptrCurveMapping:
{mapping}
  m_AnimationClipSettings:
    serializedVersion: 2
    m_AdditiveReferencePoseClip: {{fileID: 0}}
    m_AdditiveReferencePoseTime: 0
    m_StartTime: 0
    m_StopTime: {stop}
    m_OrientationOffsetY: 0
    m_Level: 0
    m_CycleOffset: 0
    m_HasAdditiveReferencePose: 0
    m_LoopTime: 1
    m_LoopBlend: 0
    m_LoopBlendOrientation: 0
    m_LoopBlendPositionY: 0
    m_LoopBlendPositionXZ: 0
    m_KeepOriginalOrientation: 0
    m_KeepOriginalPositionY: 1
    m_KeepOriginalPositionXZ: 0
    m_HeightFromFeet: 0
    m_Mirror: 0
  m_EditorCurves: []
  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events: []
"""


def clip(name, keys, tex_guid):
    """keys: list of (sprite internalID, weapon local x, weapon local y)."""
    pptr, mapping, pos = [], [], []
    for i, (iid, wx, wy) in enumerate(keys):
        t = round(i / FPS, 7)
        ref = '{{fileID: {iid}, guid: {g}, type: 3}}'.format(iid=iid, g=tex_guid)
        pptr.append('    - time: {t}\n      value: {ref}'.format(t=t, ref=ref))
        mapping.append('    - ' + ref)
        pos.append(POS_KEY.format(t=t, x=round(wx, 6), y=round(wy, 6)))
    return CLIP.format(name=name, pos='\n'.join(pos), pptr='\n'.join(pptr),
                       mapping='\n'.join(mapping), stop=round(len(keys) / FPS, 7))


# --------------------------------------------------------------- controller --
CONTROLLER = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!91 &9100000
AnimatorController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  serializedVersion: 5
  m_AnimatorParameters:
  - m_Name: Idle
    m_Type: 9
    m_DefaultFloat: 0
    m_DefaultInt: 0
    m_DefaultBool: 0
    m_Controller: {{fileID: 9100000}}
  - m_Name: Walk
    m_Type: 9
    m_DefaultFloat: 0
    m_DefaultInt: 0
    m_DefaultBool: 0
    m_Controller: {{fileID: 9100000}}
  - m_Name: Shoot
    m_Type: 9
    m_DefaultFloat: 0
    m_DefaultInt: 0
    m_DefaultBool: 0
    m_Controller: {{fileID: 9100000}}
  m_AnimatorLayers:
  - serializedVersion: 5
    m_Name: Base Layer
    m_StateMachine: {{fileID: 1107000}}
    m_Mask: {{fileID: 0}}
    m_Motions: []
    m_Behaviours: []
    m_BlendingMode: 0
    m_SyncedLayerIndex: -1
    m_DefaultWeight: 0
    m_IKPass: 0
    m_SyncedLayerAffectsTiming: 0
    m_Controller: {{fileID: 9100000}}
--- !u!1107 &1107000
AnimatorStateMachine:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Base Layer
  m_ChildStates:
  - serializedVersion: 1
    m_State: {{fileID: 1102000}}
    m_Position: {{x: 200, y: 0, z: 0}}
  - serializedVersion: 1
    m_State: {{fileID: 1102001}}
    m_Position: {{x: 235, y: 65, z: 0}}
  - serializedVersion: 1
    m_State: {{fileID: 1102002}}
    m_Position: {{x: 270, y: 130, z: 0}}
  - serializedVersion: 1
    m_State: {{fileID: 1102003}}
    m_Position: {{x: 305, y: 195, z: 0}}
  m_ChildStateMachines: []
  m_AnyStateTransitions:
  - {{fileID: 1101001}}
  - {{fileID: 1101002}}
  - {{fileID: 1101003}}
  m_EntryTransitions: []
  m_StateMachineTransitions: {{}}
  m_StateMachineBehaviours: []
  m_AnyStatePosition: {{x: 50, y: 20, z: 0}}
  m_EntryPosition: {{x: 50, y: 120, z: 0}}
  m_ExitPosition: {{x: 800, y: 120, z: 0}}
  m_ParentStateMachinePosition: {{x: 800, y: 20, z: 0}}
  m_DefaultState: {{fileID: 1102000}}
{states}{transitions}"""

STATE = """--- !u!1102 &{fid}
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {{x: 50, y: 50, z: 0}}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {motion}
  m_Tag:
  m_SpeedParameter:
  m_MirrorParameter:
  m_CycleOffsetParameter:
  m_TimeParameter:
"""

TRANSITION = """--- !u!1101 &{fid}
AnimatorStateTransition:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name:
  m_Conditions:
  - m_ConditionMode: 1
    m_ConditionEvent: {param}
    m_EventTreshold: 0
  m_DstStateMachine: {{fileID: 0}}
  m_DstState: {{fileID: {dst}}}
  m_Solo: 0
  m_Mute: 0
  m_IsExit: 0
  serializedVersion: 3
  m_TransitionDuration: 0
  m_TransitionOffset: 0
  m_ExitTime: 0.75
  m_HasExitTime: 0
  m_HasFixedDuration: 1
  m_InterruptionSource: 0
  m_OrderedInterruption: 1
  m_CanTransitionToSelf: 0
"""


def controller(name, clip_guids):
    states = [STATE.format(fid=1102000, name='Empty', motion='{fileID: 0}')]
    transitions = []
    for i, (tag, _a, _b) in enumerate(TAGS):
        motion = '{{fileID: 7400000, guid: {g}, type: 2}}'.format(g=clip_guids[tag])
        states.append(STATE.format(fid=1102001 + i, name=tag, motion=motion))
        transitions.append(TRANSITION.format(fid=1101001 + i, param=tag, dst=1102001 + i))
    return CONTROLLER.format(name=name, states=''.join(states),
                             transitions=''.join(transitions))


# ------------------------------------------------------------------- prefab --
# Weapon is an empty node whose position the clips key; Sprite hangs under it and
# carries the renderer, so WeaponHolder's per-weapon hold offset is not fighting
# the animator for the same transform.
WEAPON_GO = 6100000001
WEAPON_TR = 6100000002
SPRITE_GO = 6100000011
SPRITE_TR = 6100000012
SPRITE_SR = 6100000013
HOLDER = 6100000021
LASER_GO = 6100000031
LASER_TR = 6100000032
LASER_SR = 6100000033
VIEW_TR = 1653403570204640222
ROOT_GO = 8666127740443770330

# Assets/Scripts/Weapons/WeaponHolder.cs.meta
HOLDER_SCRIPT_GUID = 'e39068af5be3b6f8bea416bdbda84e25'
# Assets/Resources/Prefabs/Weapons/Bullet.prefab.meta
BULLET_PREFAB_GUID = '288beb9111df540a0d8976502d5ef229'


WEAPON_BLOCK = """--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {tr}}}
  m_Layer: 8
  m_Name: Weapon
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
  m_LocalPosition: {{x: {px}, y: {py}, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {{fileID: {str}}}
  m_Father: {{fileID: {view}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!1 &{sgo}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {str}}}
  - component: {{fileID: {sr}}}
  m_Layer: 8
  m_Name: Sprite
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &{str}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {sgo}}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: {tr}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!212 &{sr}
SpriteRenderer:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {sgo}}}
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
  m_SortingOrder: 1
  m_MaskInteraction: 0
  m_Sprite: {{fileID: 0}}
  m_Color: {{r: 1, g: 1, b: 1, a: 1}}
  m_FlipX: 0
  m_FlipY: 0
  m_DrawMode: 0
  m_Size: {{x: 1, y: 1}}
  m_AdaptiveModeThreshold: 0.5
  m_SpriteTileMode: 0
  m_WasSpriteAssigned: 0
  m_SpriteSortPoint: 0
"""


HOLDER_BLOCK = """--- !u!114 &{holder}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {root}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: Assembly-CSharp::Weapons.WeaponHolder
  weapon: {{fileID: 11400000, guid: {asset}, type: 2}}
  view: {{fileID: {sr}}}
  arm: {{fileID: {tr}}}
  laser: {{fileID: {laser}}}
  projectilePrefab: {{fileID: 6300000000000000006, guid: {bullet}, type: 3}}
  shooter: {{fileID: 837572233467329222}}
"""

LASER_BLOCK = """--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {tr}}}
  - component: {{fileID: {sr}}}
  m_Layer: 8
  m_Name: Laser
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
  m_Father: {{fileID: {root}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!212 &{sr}
SpriteRenderer:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 0
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
  m_SortingOrder: 3
  m_MaskInteraction: 0
  m_Sprite: {{fileID: 21300000, guid: {sprite}, type: 3}}
  m_Color: {{r: 1, g: 0.3, b: 0.25, a: 0.55}}
  m_FlipX: 0
  m_FlipY: 0
  m_DrawMode: 0
  m_Size: {{x: 1, y: 1}}
  m_AdaptiveModeThreshold: 0.5
  m_SpriteTileMode: 0
  m_WasSpriteAssigned: 1
  m_SpriteSortPoint: 0
"""

def build_prefab(body_sprite_ref, controller_guid, weapon, weapon_pos, ragdoll_guid):
    # The armed prefab replaced the stock Soldier, so its untouched YAML lives
    # here rather than in Assets — everything it references still exists.
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'soldier_prefab.template'), encoding='utf-8').read()
    # body sprite + animator controller
    src = src.replace(
        'm_Sprite: {fileID: -2559116770277906535, guid: aa8d14077ffc6904d907266a841a3d92, type: 3}',
        'm_Sprite: ' + body_sprite_ref)
    src = src.replace('m_Controller: {fileID: 9100000, guid: 33b868bf9d9d24549aaa2c0158bb55a3, type: 2}',
                      'm_Controller: {{fileID: 9100000, guid: {g}, type: 2}}'.format(g=controller_guid))
    src = src.replace('  m_Name: Soldier\n', '  m_Name: SoldierArmed\n')
    src = src.replace(
        'ragdollPrefab: {fileID: 7583020597788532137, guid: %s, type: 3}' % OLD_RAGDOLL_GUID,
        'ragdollPrefab: {fileID: 7583020597788532137, guid: %s, type: 3}' % ragdoll_guid)
    # hang the weapon off View
    src = src.replace('  m_Children: []\n  m_Father: {fileID: 7099991138952253097}\n'
                      '  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}\n'
                      '--- !u!212 &1052722090386138420',
                      '  m_Children:\n  - {{fileID: {tr}}}\n'
                      '  m_Father: {{fileID: 7099991138952253097}}\n'
                      '  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}\n'
                      '--- !u!212 &1052722090386138420'.format(tr=WEAPON_TR))
    # RegularEnemyController aims and fires through the holder, so it needs to know it.
    src = src.replace(
        '  _eye: {fileID: 7723626924655959891}\n',
        '  _eye: {fileID: 7723626924655959891}\n  _weapon: {fileID: %d}\n' % HOLDER, 1)
    # WeaponHolder goes on the root, next to the controller, so the gun is one
    # field on the object you click rather than three nodes down.
    src = src.replace(
        '  - component: {fileID: 8077373476292324551}\n',
        '  - component: {fileID: 8077373476292324551}\n'
        '  - component: {fileID: %d}\n' % HOLDER, 1)
    # The beam hangs off the root, not off View: it is positioned in world space and a
    # mirrored parent would flip the stretch out from under it.
    src = src.replace(
        '  - {fileID: 2696194240902440409}\n',
        '  - {fileID: 2696194240902440409}\n  - {fileID: %d}\n' % LASER_TR, 1)
    src += LASER_BLOCK.format(go=LASER_GO, tr=LASER_TR, sr=LASER_SR, root=7099991138952253097,
                              sprite=weapon_guid('laser_pixel'))
    src += HOLDER_BLOCK.format(holder=HOLDER, root=ROOT_GO,
                               script=HOLDER_SCRIPT_GUID,
                               asset=weapon_guid('asset/' + weapon), sr=SPRITE_SR,
                               tr=WEAPON_TR, bullet=BULLET_PREFAB_GUID,
                               laser=LASER_SR)
    src += WEAPON_BLOCK.format(go=WEAPON_GO, tr=WEAPON_TR, sgo=SPRITE_GO,
                               str=SPRITE_TR, sr=SPRITE_SR, view=VIEW_TR,
                               px=round(weapon_pos[0], 6), py=round(weapon_pos[1], 6))
    return src


# -------------------------------------------------------------------- corpse --
# Where the pieces sit on the 32x32 part sheet: (left, top, width, height).
TORSO_RECT = (0, 0, 9, 10)
ARM_RECT = (19, 0, 6, 8)

SLEEVE_L = (138, 122, 122, 255)
SLEEVE_M = (104, 91, 91, 255)
GLOVE = (73, 66, 66, 255)

# A forearm hanging off the shoulder hinge, which the definition puts at the
# sprite's (0.5, 2.5). Columns and rows are local to the 6x8 arm cell.
ARM_PIXELS = [((0, 2), SLEEVE_L), ((1, 2), SLEEVE_M),
              ((0, 3), SLEEVE_L), ((1, 3), SLEEVE_M),
              ((1, 4), SLEEVE_L), ((2, 4), SLEEVE_M),
              ((1, 5), SLEEVE_L), ((2, 5), SLEEVE_M),
              ((2, 6), GLOVE)]


def close_holes(img, rect):
    """Refill pixels the rifle had covered that are enclosed by body on both sides.

    Scoped to one piece: the parts sit side by side on the sheet, and a sweep over
    the whole thing would bridge one limb into the next.
    """
    ax, ay, w, h = rect
    p = img.load()
    for y in range(ay, ay + h):
        for x in range(ax + 1, ax + w - 1):
            if p[x, y][3]:
                continue
            left = next((p[i, y] for i in range(x - 1, ax - 1, -1) if p[i, y][3]), None)
            right = next((p[i, y] for i in range(x + 1, ax + w) if p[i, y][3]), None)
            if left and right:
                p[x, y] = left


def draw_arm(img, rect):
    p = img.load()
    ax, ay, w, h = rect
    for x in range(w):
        for y in range(h):
            p[ax + x, ay + y] = (0, 0, 0, 0)
    for (cx, cy), color in ARM_PIXELS:
        p[ax + cx, ay + cy] = color


RAG_GO = 6200000001
RAG_TR = 6200000002
RAG_SR = 6200000003
RAG_RB = 6200000004
RAG_COL = 6200000005

RAG_WEAPON_BLOCK = """--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {tr}}}
  - component: {{fileID: {sr}}}
  - component: {{fileID: {rb}}}
  - component: {{fileID: {col}}}
  m_Layer: 0
  m_Name: weapon
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
  m_LocalPosition: {{x: {px}, y: {py}, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: {root}}}
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
  m_SortingOrder: 5
  m_MaskInteraction: 0
  m_Sprite: {{fileID: 21300000, guid: {wguid}, type: 3}}
  m_Color: {{r: 1, g: 1, b: 1, a: 1}}
  m_FlipX: 0
  m_FlipY: 0
  m_DrawMode: 0
  m_Size: {{x: 1, y: 1}}
  m_AdaptiveModeThreshold: 0.5
  m_SpriteTileMode: 0
  m_WasSpriteAssigned: 1
  m_SpriteSortPoint: 0
--- !u!50 &{rb}
Rigidbody2D:
  serializedVersion: 5
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_BodyType: 0
  m_Simulated: 1
  m_UseFullKinematicContacts: 0
  m_UseAutoMass: 0
  m_Mass: 3
  m_LinearDamping: 0
  m_AngularDamping: 0.4
  m_GravityScale: 1
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_Interpolate: 1
  m_SleepingMode: 1
  m_CollisionDetection: 1
  m_Constraints: 0
--- !u!60 &{col}
PolygonCollider2D:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  serializedVersion: 3
  m_Density: 1
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_ForceSendLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_ForceReceiveLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_ContactCaptureLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_CallbackLayers:
    serializedVersion: 2
    m_Bits: 4294967295
  m_IsTrigger: 0
  m_UsedByEffector: 0
  m_CompositeOperation: 0
  m_CompositeOrder: 0
  m_Offset: {{x: 0, y: 0}}
  m_SpriteTilingProperty:
    border: {{x: 0, y: 0, z: 0, w: 0}}
    pivot: {{x: 0.5, y: 0.5}}
    oldSize: {{x: 1, y: 1}}
    newSize: {{x: 1, y: 1}}
    adaptiveTilingThreshold: 0.5
    drawMode: 0
    adaptiveTiling: 0
  m_AutoTiling: 0
  m_Points:
    m_Paths:
    - - {{x: {x0}, y: {y0}}}
      - {{x: {x1}, y: {y0}}}
      - {{x: {x1}, y: {y1}}}
      - {{x: {x0}, y: {y1}}}
  m_UseDelaunayMesh: 1
"""

DEF_PART = """  - name: weapon
    sprite: {{fileID: 21300000, guid: {wguid}, type: 3}}
    parent: -1
    pivotPx: {{x: {hx}, y: {hy}}}
    anchorPx: {{x: {hx}, y: {hy}}}
    useLimits: 0
    limitLow: -55
    limitHigh: 55
    uvColor:
      serializedVersion: 2
      rgba: 0
"""


def build_ragdoll(weapon, weapon_pos):
    """Rifle-free copy of the soldier corpse, with the weapon as a loose piece."""
    import re

    gun = GUNS[weapon]
    os.makedirs(RAG_DIR, exist_ok=True)
    folder_meta = RAG_DIR + '.meta'
    if not os.path.exists(folder_meta):
        open(folder_meta, 'w').write(FOLDER_META.format(guid=guid('ragdoll-folder')))

    # --- part sheet, minus the rifle ----------------------------------------
    # The corpse was cut around the drawn-in rifle, so taking it out leaves two
    # wounds: a gap through the chest where the gun crossed it, and an "arm"
    # piece that was almost entirely gun. Close the first, redraw the second.
    parts_png = os.path.join(RAG_DIR, 'soldier_armed_parts.png')
    sheet, _ = strip_gun(Image.open(os.path.join(RAG_SRC, 'soldier_parts.png')).convert('RGBA'))
    close_holes(sheet, TORSO_RECT)
    draw_arm(sheet, ARM_RECT)
    sheet.save(parts_png)

    meta = open(os.path.join(RAG_SRC, 'soldier_parts.png.meta'), encoding='utf-8').read()
    asset = open(os.path.join(RAG_SRC, 'soldier_ragdoll.asset'), encoding='utf-8').read()
    prefab = open(os.path.join(RAG_SRC, 'SoldierRagdoll.prefab'), encoding='utf-8').read()

    # Every id the three files share has to move together, or the corpse would
    # still be pointing at the armed soldier's sprites.
    swaps = {OLD_PARTS_GUID: guid('soldier_armed_parts.png'),
             OLD_DEF_GUID: guid('soldier_armed_ragdoll.asset'),
             OLD_RAGDOLL_GUID: guid('SoldierArmedRagdoll.prefab')}
    for old_sid in re.findall(r'spriteID: ([0-9a-f]{32})', meta):
        swaps[old_sid] = sprite_id('armed_parts/' + old_sid)
    for old_iid in re.findall(r'internalID: (-?\d+)', meta):
        if old_iid != '0':
            swaps[old_iid] = str(file_id('armed_parts/' + old_iid))

    def apply(text):
        for old, new in swaps.items():
            text = text.replace(old, new)
        return text

    meta, asset, prefab = apply(meta), apply(asset), apply(prefab)
    asset = asset.replace('m_Name: soldier_ragdoll', 'm_Name: soldier_armed_ragdoll')
    asset = asset.replace('creature: soldier', 'creature: soldier_armed')
    prefab = prefab.replace('m_Name: SoldierRagdoll', 'm_Name: SoldierArmedRagdoll')

    # --- the weapon as a sixth piece ----------------------------------------
    hx, hy = HAND
    asset = asset.replace('  poses:\n',
                          DEF_PART.format(wguid=weapon_guid(weapon), hx=hx, hy=hy) + '  poses:\n')
    asset = asset.replace('    - {x: 9, y: 17.5}\n    rotations:',
                          '    - {{x: 9, y: 17.5}}\n    - {{x: {hx}, y: {hy}}}\n    rotations:'
                          .format(hx=hx, hy=hy))
    asset = asset.replace('    - 0\n  defaultAnim: Frame', '    - 0\n    - 0\n  defaultAnim: Frame')

    prefab = prefab.replace('  - {fileID: 3791169322553385420}\n  m_Father: {fileID: 0}',
                            '  - {{fileID: {tr}}}\n  - {{fileID: 3791169322553385420}}\n'
                            '  m_Father: {{fileID: 0}}'.format(tr=RAG_TR))
    prefab = prefab.replace('  - {fileID: 4433179730501938759}\n  selfCollision: 0',
                            '  - {{fileID: 4433179730501938759}}\n  - {{fileID: {rb}}}\n'
                            '  selfCollision: 0'.format(rb=RAG_RB))
    # Collider box = the weapon sprite's own extents, measured from its grip pivot.
    gx, gy = gun.grip
    prefab += RAG_WEAPON_BLOCK.format(
        go=RAG_GO, tr=RAG_TR, sr=RAG_SR, rb=RAG_RB, col=RAG_COL, root=RAG_ROOT_TR,
        px=round(weapon_pos[0], 6), py=round(weapon_pos[1], 6), wguid=weapon_guid(weapon),
        x0=round(-(gx + 0.5) / PPU, 6), x1=round((gun.w - gx - 0.5) / PPU, 6),
        y0=round(-(gun.h - gy - 0.5) / PPU, 6), y1=round((gy + 0.5) / PPU, 6))

    open(parts_png + '.meta', 'w').write(meta)
    for name, text, main in (('soldier_armed_ragdoll.asset', asset, 11400000),
                             ('SoldierArmedRagdoll.prefab', prefab, None)):
        path = os.path.join(RAG_DIR, name)
        open(path, 'w').write(text)
        if main is None:
            open(path + '.meta', 'w').write(
                'fileFormatVersion: 2\nguid: {g}\nPrefabImporter:\n  externalObjects: {{}}\n'
                '  userData: \n  assetBundleName: \n  assetBundleVariant: \n'.format(g=swaps[OLD_RAGDOLL_GUID]))
        else:
            open(path + '.meta', 'w').write(
                NATIVE_META.format(guid=swaps[OLD_DEF_GUID], main=main))
    return swaps[OLD_RAGDOLL_GUID]


# --------------------------------------------------------------------- main --
def main(weapon='m4'):
    if weapon not in GUNS:
        raise SystemExit('unknown weapon %r, pick one of %s' % (weapon, list(GUNS)))
    gun = GUNS[weapon]

    frames, w, h = read_aseprite(SRC)
    bodies, anchors = [], []
    for img in frames:
        body, anchor = strip_gun(img)
        close_gun_gap(body, img)
        bodies.append(body)
        anchors.append(anchor)
    ref = anchors[0]

    # --- sprite sheet -------------------------------------------------------
    rows = (len(bodies) + COLS - 1) // COLS
    sheet = Image.new('RGBA', (COLS * w, rows * h))
    sprites = []
    for i, body in enumerate(bodies):
        col, row = i % COLS, i // COLS
        sheet.alpha_composite(body, (col * w, row * h))
        # Ragdoll.ApplySpritePose splits the showing sprite's name into animation
        # plus index, and the corpse's poses are baked under "Frame" — keep the
        # Aseprite importer's naming or a dying soldier finds no pose.
        name = 'Frame_%d' % i
        rect = (col * w, (rows - 1 - row) * h, w, h)     # Unity y counts from the bottom
        sprites.append((name, rect, file_id('soldier_body/%d' % i), sprite_id(name)))

    os.makedirs(ANIM_DIR, exist_ok=True)
    folder_meta = ANIM_DIR + '.meta'
    if not os.path.exists(folder_meta):
        open(folder_meta, 'w').write(FOLDER_META.format(guid=guid('folder')))
    png = os.path.join(ANIM_DIR, 'soldier_body.png')
    sheet.save(png)
    tex_guid = guid('soldier_body.png')
    open(png + '.meta', 'w').write(sheet_meta(sprites, tex_guid))

    # --- where the weapon sits, per frame -----------------------------------
    # The character sprite's pivot is the bottom centre of the 16x22 canvas; the
    # weapon sprite's pivot is its own grip pixel.  Both in units of 1/PPU.
    def weapon_local(i):
        dx = anchors[i][0] - ref[0] if anchors[i] else 0
        dy = anchors[i][1] - ref[1] if anchors[i] else 0
        cx = HAND[0] + dx + 0.5                       # canvas px, x from the left
        cy = h - (HAND[1] + dy) - 0.5                 # canvas px, y from the bottom
        return (cx - w / 2.0) / PPU, cy / PPU

    rest = weapon_local(0)

    # --- clips --------------------------------------------------------------
    clip_guids = {}
    for tag, first, last in TAGS:
        keys = [(sprites[i][2],) + weapon_local(i) for i in range(first, last + 1)]
        name = 'SoldierBody' + tag
        path = os.path.join(ANIM_DIR, name + '.anim')
        open(path, 'w').write(clip(name, keys, tex_guid))
        g = guid(name)
        clip_guids[tag] = g
        open(path + '.meta', 'w').write(NATIVE_META.format(guid=g, main=7400000))

    # --- controller ---------------------------------------------------------
    ctrl = os.path.join(ANIM_DIR, 'SoldierBodyAnimator.controller')
    open(ctrl, 'w').write(controller('SoldierBodyAnimator', clip_guids))
    ctrl_guid = guid('SoldierBodyAnimator')
    open(ctrl + '.meta', 'w').write(NATIVE_META.format(guid=ctrl_guid, main=9100000))

    # --- corpse -------------------------------------------------------------
    ragdoll_guid = build_ragdoll(weapon, rest)

    # --- prefab -------------------------------------------------------------
    body_ref = '{{fileID: {iid}, guid: {g}, type: 3}}'.format(iid=sprites[0][2], g=tex_guid)
    open(PREFAB, 'w').write(build_prefab(body_ref, ctrl_guid, weapon, rest, ragdoll_guid))
    open(PREFAB + '.meta', 'w').write(
        'fileFormatVersion: 2\nguid: {g}\nPrefabImporter:\n  externalObjects: {{}}\n'
        '  userData: \n  assetBundleName: \n  assetBundleVariant: \n'.format(g=guid('SoldierArmed.prefab')))

    print('body sheet  %dx%d, %d frames -> %s' % (sheet.width, sheet.height, len(sprites), png))
    print('weapon      %s, grip %s, rest pos (%.3f, %.3f)' % (weapon, gun.grip, rest[0], rest[1]))
    print('corpse      %s' % RAG_DIR)
    print('prefab      %s' % PREFAB)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'm4')
