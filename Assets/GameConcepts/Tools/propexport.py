"""Turn a drawn prop into a game asset: a native-size sprite and a ready prefab.

Shared by `roomprops.py` (and anything after it that draws objects meant to be placed in
a room rather than looked at on a sheet). For a canvas drawn on KEY it writes

* `Assets/Sprites/Props/<Sub>/<Name>.png` - 1x, real alpha, and its .meta: Sprite, point
  filter, uncompressed, readable (the fire and the eraser edit the pixels), 20 pixels per
  unit, centre pivot - the importer settings of `Resources/SpawnImages/explosive_barrel.png`;
* `Assets/Resources/Prefabs/Props/<Name>.prefab` - SpriteRenderer, Rigidbody2D,
  PolygonCollider2D, MaterialView, the way `Hazards/ExplosiveBarrel` and SpriteFactory build
  a body. The collider is traced here from the same pixels, as closed loops round the
  opaque ones, so it sits on the art from the first frame; PixelSpriteRegistry retraces it
  itself once fire or the eraser start taking pixels away. The mass is the one
  MassRecalculator would give it: area x 100 x the material's density.

The png is written before its .meta in the same call (see the note on Unity reimporting
in the project memory: a .meta that lands first is thrown away), and every guid is derived
from the asset's name, so a re-run rewrites the files in place and keeps every reference.
"""
import hashlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixelfix import write_png  # noqa: E402

ASSETS = os.path.abspath(os.path.join(HERE, "..", ".."))
PPU = 20

G_MATERIAL_VIEW = "a8ce2ccf2ebd0f8469081b913f4833c9"
G_EXPLOSIVE = "1556ec25a253236488aa80bb20b65987"

# PhysMaterialId -> density, as in Materials/MaterialLibrary.cs
DEFAULT, WOOD, ICE, METAL = 0, 1, 2, 3
DENSITY = {DEFAULT: 1.0, WOOD: 0.6, ICE: 0.92, METAL: 2.6}


def guid(key):
    return hashlib.md5(("physfun-props/" + key).encode()).hexdigest()


def fid(*parts):
    return int(hashlib.md5("/".join(parts).encode()).hexdigest()[:15], 16)


# ─────────────────────────────────────────────────────────────────────────────
#  Outline
# ─────────────────────────────────────────────────────────────────────────────
def trace(solid, w, h):
    """Closed loops round the solid cells, in pixel-corner coordinates with y up.

    Every boundary edge is directed so the solid cell is on its left; loops are chained
    from those, and where two diagonal cells meet at a corner the walk turns left (back round the cell it came along), so a
    diagonal contact is two loops rather than one figure-eight."""
    def s(x, y):
        return 0 <= x < w and 0 <= y < h and solid[y][x]

    out = {}                                   # start corner -> [end corners]
    for y in range(h):
        for x in range(w):
            if not solid[y][x]:
                continue
            # image row y covers corners (y-up) from H-1-y to H-y
            yb, yt = h - 1 - y, h - y
            if not s(x, y + 1):                # below is empty: bottom edge, left to right
                out.setdefault((x, yb), []).append((x + 1, yb))
            if not s(x + 1, y):                # right
                out.setdefault((x + 1, yb), []).append((x + 1, yt))
            if not s(x, y - 1):                # top, right to left
                out.setdefault((x + 1, yt), []).append((x, yt))
            if not s(x - 1, y):                # left
                out.setdefault((x, yt), []).append((x, yb))

    loops = []
    while out:
        start = next(iter(out))
        loop = [start]
        prev, cur = None, start
        while True:
            nexts = out[cur]
            if len(nexts) == 1 or prev is None:
                nxt = nexts[0]
            else:                              # saddle: turn back round the same cell
                dx, dy = cur[0] - prev[0], cur[1] - prev[1]
                left = (cur[0] - dy, cur[1] + dx)
                nxt = left if left in nexts else nexts[0]
            nexts.remove(nxt)
            if not nexts:
                del out[cur]
            prev, cur = cur, nxt
            if cur == start:
                break
            loop.append(cur)
        loops.append(loop)
    return loops


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1.0
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - x0) - dx * (pts[i][1] - y0)) / n
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:idx + 1], eps)[:-1] + _rdp(pts[idx:], eps)


def simplify(loop, eps=0.5):
    """Drop collinear corners, then Douglas-Peucker the staircase, split at the two corners
    farthest apart so the closed loop keeps its extremes."""
    pts = [p for i, p in enumerate(loop)
           if (loop[i - 1][0] - p[0]) * (loop[(i + 1) % len(loop)][1] - p[1])
           != (loop[i - 1][1] - p[1]) * (loop[(i + 1) % len(loop)][0] - p[0])]
    if len(pts) <= 4:
        return pts
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    a = _rdp(pts[:far + 1], eps)
    b = _rdp(pts[far:] + [pts[0]], eps)
    res = a[:-1] + b[:-1]
    return res if len(res) >= 3 else pts


def area(loop):
    return sum(loop[i - 1][0] * p[1] - p[0] * loop[i - 1][1] for i, p in enumerate(loop)) / 2.0


# ─────────────────────────────────────────────────────────────────────────────
#  Files
# ─────────────────────────────────────────────────────────────────────────────
TEXTURE_META = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
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
  isReadable: 1
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
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: {ppu}
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 1
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
    maxTextureSize: 256
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
  - serializedVersion: 4
    buildTarget: Standalone
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
    sprites: []
    outline: []
    customData:
    physicsShape: []
    bones: []
    spriteID: {sid}
    internalID: 0
    vertices: []
    indices:
    edges: []
    weights: []
    secondaryTextures: []
    spriteCustomMetadata:
      entries: []
    nameFileIdTable: {{}}
  mipmapLimitGroupName:
  pSDRemoveMatte: 0
  userData:
  assetBundleName:
  assetBundleVariant:
"""

FOLDER_META = """fileFormatVersion: 2
guid: {guid}
folderAsset: yes
DefaultImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""

PREFAB_META = """fileFormatVersion: 2
guid: {guid}
PrefabImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""

LAYERS = """    serializedVersion: 2
    m_Bits: {bits}"""


def _layers(bits):
    return LAYERS.format(bits=bits)


def ensure_dir(rel):
    """Make Assets/<rel>, giving each new folder its .meta after the folder exists."""
    path = ASSETS
    for part in rel.replace("\\", "/").split("/"):
        path = os.path.join(path, part)
        if not os.path.isdir(path):
            os.makedirs(path)
            with open(path + ".meta", "w", newline="\n") as f:
                f.write(FOLDER_META.format(guid=guid("folder/" + os.path.relpath(path, ASSETS))))
    return path


def write_text(path, text):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != text:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def anchor_id(name, anchor):
    """File id of an anchor child's Transform inside the prop prefab - what a room
    references when it ties a rope to that point of a prop instance."""
    return fid("prop", name, "anchor", anchor, "t")


def export(name, rows, sprite_dir, prefab_dir, material, extra=None, angular_damping=0.05,
           sorting_order=0, anchors=None, body_type=0, trigger=False, child_components=None):
    """rows: [[(r, g, b, a)]] top to bottom. `extra` is a list of (script guid, editor
    class, field yaml) MonoBehaviours to add (an Explosive, say). `anchors` maps a child's
    name to a point in pixels (x right, y down from the top-left corner): an empty child
    is put there, e.g. "Eye" where a hung prop's rope ties on. `body_type` is the
    Rigidbody2D's: 0 dynamic, 1 kinematic, 2 static (a coil bolted to its plinth).
    Returns the prefab path."""
    h, w = len(rows), len(rows[0])
    sdir = ensure_dir(sprite_dir)
    pdir = ensure_dir(prefab_dir)
    png = os.path.join(sdir, name + ".png")
    tex_guid = guid("sprite/" + name)
    write_png(png, rows)
    sid = hashlib.md5(("spriteid/" + name).encode()).hexdigest()[:16] + "0800000000000000"
    write_text(png + ".meta", TEXTURE_META.format(guid=tex_guid, ppu=PPU, sid=sid))

    solid = [[px[3] > 0 for px in row] for row in rows]
    loops = [simplify(l) for l in trace(solid, w, h)]
    loops = [l for l in loops if len(l) >= 3]
    # outer loops are counter-clockwise (positive area), holes clockwise
    total = sum(area(l) for l in loops)
    mass = max(0.01, total / (PPU * PPU) * 100.0 * DENSITY[material])
    cx, cy = w / 2.0, h / 2.0
    paths = ""
    for l in loops:
        paths += "    - " + "\n      ".join(
            "- {x: %s, y: %s}" % (_num((x - cx) / PPU), _num((y - cy) / PPU)) for x, y in l) + "\n"

    go, tr, sr, rb, col, mv = (fid("prop", name, k) for k in ("go", "t", "sr", "rb", "col", "mv"))
    comps = [tr, sr, rb, col, mv]
    extras = []
    for i, (script, cls, fields) in enumerate(extra or []):
        cid = fid("prop", name, "x%d" % i)
        comps.append(cid)
        extras.append(f"""--- !u!114 &{cid}
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
  m_EditorClassIdentifier: {cls}
{fields}""")
    comp_txt = "".join("  - component: {fileID: %d}\n" % c for c in comps)
    kids, kid_docs = [], []
    for aname, (ax, ay) in (anchors or {}).items():
        ag, at_ = fid("prop", name, "anchor", aname, "go"), anchor_id(name, aname)
        kids.append(at_)
        kcomps = (child_components or {}).get(aname, [])
        kcids = [fid("prop", name, "anchor", aname, "c%d" % ci) for ci in range(len(kcomps))]
        kcomp_txt = "".join("  - component: {fileID: %d}\n" % c for c in kcids)
        for kc, (script, cls, fields) in zip(kcids, kcomps):
            kid_docs.append(f"""--- !u!114 &{kc}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {ag}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: {cls}
{fields}""")
        kid_docs.append(f"""--- !u!1 &{ag}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {at_}}}
{kcomp_txt}  m_Layer: 0
  m_Name: {aname}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &{at_}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {ag}}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: {_num((ax - cx) / PPU)}, y: {_num((cy - ay) / PPU)}, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: {tr}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
""")
    kid_txt = ("\n" + "".join("  - {fileID: %d}\n" % k for k in kids)) if kids else " []\n"
    sw, sh = _num(w / PPU), _num(h / PPU)
    prefab = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
{comp_txt}  m_Layer: 0
  m_Name: {name}
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
  m_Children:{kid_txt}  m_Father: {{fileID: 0}}
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
  m_SortingOrder: {sorting_order}
  m_MaskInteraction: 0
  m_Sprite: {{fileID: 21300000, guid: {tex_guid}, type: 3}}
  m_Color: {{r: 1, g: 1, b: 1, a: 1}}
  m_FlipX: 0
  m_FlipY: 0
  m_DrawMode: 0
  m_Size: {{x: {sw}, y: {sh}}}
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
  m_BodyType: {body_type}
  m_Simulated: 1
  m_UseFullKinematicContacts: 0
  m_UseAutoMass: 0
  m_Mass: {_num(mass)}
  m_LinearDamping: 0
  m_AngularDamping: {angular_damping}
  m_GravityScale: 1
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
{_layers(0)}
  m_ExcludeLayers:
{_layers(0)}
  m_Interpolate: 0
  m_SleepingMode: 1
  m_CollisionDetection: 0
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
{_layers(0)}
  m_ExcludeLayers:
{_layers(0)}
  m_LayerOverridePriority: 0
  m_ForceSendLayers:
{_layers(4294967295)}
  m_ForceReceiveLayers:
{_layers(4294967295)}
  m_ContactCaptureLayers:
{_layers(4294967295)}
  m_CallbackLayers:
{_layers(4294967295)}
  m_IsTrigger: {1 if trigger else 0}
  m_UsedByEffector: 0
  m_CompositeOperation: 0
  m_CompositeOrder: 0
  m_Offset: {{x: 0, y: 0}}
  m_SpriteTilingProperty:
    border: {{x: 0, y: 0, z: 0, w: 0}}
    pivot: {{x: 0.5, y: 0.5}}
    oldSize: {{x: {sw}, y: {sh}}}
    newSize: {{x: {sw}, y: {sh}}}
    adaptiveTilingThreshold: 0.5
    drawMode: 0
    adaptiveTiling: 0
  m_AutoTiling: 0
  m_Points:
    m_Paths:
{paths}  m_UseDelaunayMesh: 0
--- !u!114 &{mv}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {G_MATERIAL_VIEW}, type: 3}}
  m_Name:
  m_EditorClassIdentifier: Assembly-CSharp::Materials.MaterialView
  materialId: {material}
""" + "".join(extras) + "".join(kid_docs)
    path = os.path.join(pdir, name + ".prefab")
    write_text(path, prefab)
    write_text(path + ".meta", PREFAB_META.format(guid=guid("prefab/" + name)))
    return path, len(loops), mass


def _num(v):
    s = "%.4f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
