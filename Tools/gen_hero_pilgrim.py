"""
The pilgrim - the player hero (concept 4C in Assets/GameConcepts/Characters): a kasa
straw hat, a pale robe with a sash, and a ring staff whose head glows cyan, the
telekinesis colour.

Body frames are assembled from parts rather than drawn one by one - hat, body, legs,
hand - so every animation is the same man and a palette tweak lands everywhere. Same
frame as the enemies: 20x22 at PPU 20, facing right, feet on row 18, 10 fps.

The staff is not in those frames. It is a sprite of its own on a `Staff` child of View,
pivoted at the grip: the clips key its position to the hand every frame (and swap in the
bright-ring sprite where the body glows), and `StaffAim` turns it toward the cursor on
top of whatever the body is doing. So aiming runs in parallel with Idle, Walk and flight
instead of being an animation of its own.

Animations: Idle, Walk, WalkBack (moving away from where he looks), Levitate (thrust
held) and Fall.

    python Tools/gen_hero_pilgrim.py [--preview]

writes

  Assets/Resources/Animations/Player/Pilgrim/pilgrim.png        (+ .meta, one sprite per frame)
  Assets/Resources/Animations/Player/Pilgrim/staff.png          (+ .meta, normal / bright ring)
  Assets/Resources/Animations/Player/Pilgrim/Pilgrim<Anim>.anim (+ .meta)
  Assets/Resources/Animations/Player/Pilgrim/PilgrimAnimator.controller
  Assets/GameConcepts/Characters/HeroPilgrim_Anims.png / .gif   (only with --preview)

and wires Player.prefab: the Animator's controller, View's resting sprite, and the Staff
node under View (added on the first run). The controller keeps the trigger-per-state
shape PlayerMovement drives, plus the Speed float that scales the stride. Ids are hashed
from names, so a rerun rewrites the same assets in place.
"""
import hashlib
import os
import re

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CONCEPTS = os.path.join(ROOT, 'Assets', 'GameConcepts', 'Characters')

W, H = 20, 22
FPS = 10

GLOW = (121, 201, 213)
GLOW_L = (194, 252, 243)
PAL = {
    'h': (128, 108, 70), 'H': (160, 136, 90), 'd': (78, 62, 42),       # straw hat
    'k': (12, 13, 16), 'e': GLOW, 'E': GLOW_L, 's': (140, 116, 96),     # face, glow, skin
    'c': (126, 120, 104), 'C': (160, 154, 136), 'b': (96, 60, 46),      # robe, sash
    'w': (96, 74, 50),                                                  # staff wood
    'n': (78, 74, 80), 'N': (52, 50, 56),                               # near / far leg
    't': (124, 104, 70), 'T': (92, 78, 54),                             # near / far sandal
}

# ─────────────────────────────────────────────────────────────── parts ──
# Grids are placed with their first row at the given row of the frame.
HAT = [                     # rows 2-5
    "..........H.........",
    "........hHHHH.......",
    "......hhHHHHHHh.....",
    "....hhhhhhhhhhhhh...",
]
BODY = [                    # rows 6-14
    "........kkek........",
    "........kssss.......",
    ".......cCCCCC.......",
    "......cCCCCbCc......",
    "......cCCCbCCCc.....",
    "......cCCbCCCc......",
    "......cCbCCCCc......",
    ".......cCCCCCc......",
    ".......cCCcCCc......",
]
# Robe hem variants (replace the last body row) - the cloth moves with the gait/air.
HEM = {
    'still': ".......cCCcCCc......",
    'swing': "......cCCcCCc.......",
    'flare': "......cCCcCCcc......",
    'flare2': ".....ccCCcCCcc......",
    'billow': ".....cc.cCCc.cc.....",
}

# Legs, rows 15-18. n/t = near leg, N/T = far leg (darker).
LEGS = {
    'stand':    ["........NN.nn.......",
                 "........NN.nn.......",
                 "........NN.nn.......",
                 "........TT.tt......."],
    'dangle':   ["........NN.nn.......",
                 ".........N..n.......",
                 ".........N..n.......",
                 ".........T...t......"],
    'dangle2':  ["........NN.nn.......",
                 "........N...n.......",
                 ".........N..n.......",
                 ".........T..t......."],
    'spread':   ["........NN..nn......",
                 ".......NN....nn.....",
                 ".......N......n.....",
                 ".......T......t....."],
}


# The staff, drawn ring-up. The pivot is the grip, a third of the way up the shaft, so
# most of it reaches toward the cursor and a short butt trails behind the hand.
STAFF = {
    'normal': [".....",
               "..e..",
               ".eEe.",
               ".ewe."] + ["..w.."] * 13,
    'bright': ["..e..",
               ".eEe.",
               "eEEEe",
               ".ewe."] + ["..w.."] * 13,
}
STAFF_W, STAFF_H = 5, 17
GRIP = (2, 12)              # staff pixel the hand closes on


class Frame:
    """One body pose. `hand` is where the staff's grip goes this frame; `glow` 2 lights
    the ring up."""

    def __init__(self, legs='stand', body_dy=0, hat_dy=0, hem='still', hand=(14, 10),
                 glow=1, wisps=(), legs_top=15):
        self.legs, self.body_dy, self.hat_dy, self.hem = legs, body_dy, hat_dy, hem
        self.legs_top = legs_top
        self.hand, self.glow, self.wisps = hand, glow, wisps


def line(x0, y0, x1, y1):
    pts, dx, dy = [], abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def render(f):
    grid = [['.'] * W for _ in range(H)]

    def put(x, y, ch):
        if 0 <= x < W and 0 <= y < H and ch != '.':
            grid[y][x] = ch

    def place(rows, top, dx=0):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                put(i + dx, top + j, ch)

    place(LEGS[f.legs] if isinstance(f.legs, str) else f.legs, f.legs_top)
    body = BODY[:-1] + [HEM[f.hem]]
    place(body, 6 + f.body_dy)
    place(HAT, 2 + f.body_dy + f.hat_dy)

    hx, hy = f.hand
    put(hx - 1, hy, 'c')          # sleeve
    put(hx, hy, 's')              # the fist the staff sits in
    for x, y, ch in f.wisps:
        put(x, y, ch)
    return grid


def shade(img):
    """Same light as the rest of the cast: lift top edges, sink bottom ones, and a
    sparse ordered dither into the lower half. Glow pixels stay as drawn."""
    p = img.load()
    out = img.copy()
    q = out.load()
    keep = {GLOW, GLOW_L, PAL['w']}     # the staff is a 1px line; shading would dash it
    w, h = img.size

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and p[x, y][3] > 0

    def mul(c, k):
        return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)

    for y in range(h):
        for x in range(w):
            c = p[x, y]
            if not c[3] or c[:3] in keep:
                continue
            if not solid(x, y - 1):
                q[x, y] = mul(c, 1.14)
            elif not solid(x, y + 1) or not solid(x + 1, y) and y > 8:
                q[x, y] = mul(c, 0.82)
            elif y > 11 and (x + y) % 2 == 0 and (x * 7 + y * 3) % 5 < 2:
                q[x, y] = mul(c, 0.88)
    return out


def to_image(grid):
    img = Image.new('RGBA', (len(grid[0]), len(grid)))
    p = img.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != '.':
                p[x, y] = PAL[ch] + (255,)
    return shade(img)


# ─────────────────────────────────────────────────────────── animations ──
FAR_HIP, NEAR_HIP = 8, 10


def stride_legs(near, far, top=15):
    """Legs for one walk pose, rows `top`..18. `near` / `far` are (foot x, lifted): each
    leg is a 2px line from its hip on the top row to the foot - on row 18 when planted,
    a row up when swinging through. Far leg first, so the near one covers it where they
    cross."""
    rows = 19 - top
    grid = [['.'] * W for _ in range(rows)]
    for hip, (fx, lifted), leg, foot in ((FAR_HIP, far, 'N', 'T'), (NEAR_HIP, near, 'n', 't')):
        sole = rows - 2 if lifted else rows - 1
        for x, y in line(hip, 0, fx, sole - 1):
            grid[y][x] = grid[y][x + 1] = leg
        grid[sole][fx] = grid[sole][fx + 1] = foot
    return [''.join(r) for r in grid]


def walk_frames():
    """Six frames, two steps. The planted foot slides back 2px a frame (that is the
    ground going by) and the free one swings forward 2px a frame, so no frame jumps.
    The body rides a pixel higher while the free leg passes under it and the legs show
    that extra row - lowest on the wide contact frames, highest mid-step, as in a real
    gait. The staff's grip rides the hand."""
    near = [(12, 0), (10, 0), (8, 0), (6, 0), (8, 1), (10, 1)]
    far = [(6, 0), (8, 1), (10, 1), (12, 0), (10, 0), (8, 0)]
    dy = [0, -1, 0, 0, -1, 0]
    hem = ['swing', 'still', 'still', 'swing', 'still', 'still']
    return [Frame(legs=stride_legs(n, f, 15 + d), legs_top=15 + d, body_dy=d, hem=m,
                  hand=(14, 10 + d))
            for n, f, d, m in zip(near, far, dy, hem)]


def levitate_frames():
    under = [
        [(9, 19, 'e'), (12, 20, 'e'), (10, 21, 'e')],
        [(10, 19, 'E'), (13, 19, 'e'), (9, 21, 'e')],
        [(9, 20, 'e'), (12, 19, 'e'), (11, 21, 'e')],
        [(10, 20, 'e'), (13, 21, 'e'), (12, 19, 'E')],
    ]
    legs = ['dangle', 'dangle2', 'dangle', 'dangle2']
    hem = ['flare', 'flare2', 'flare', 'flare2']
    return [Frame(legs=l, hem=m, glow=2 if i % 2 == 0 else 1, wisps=u)
            for i, (l, m, u) in enumerate(zip(legs, hem, under))]


ANIMS = [
    ('Idle', [Frame(), Frame(), Frame(body_dy=1, hand=(14, 11), glow=2), Frame(body_dy=1, hand=(14, 11))]),
    ('Walk', walk_frames()),
    ('WalkBack', list(reversed(walk_frames()))),
    ('Levitate', levitate_frames()),
    ('Fall', [
        Frame(legs='spread', hat_dy=-1, hem='billow', hand=(14, 8)),
        Frame(legs='spread', hat_dy=-2, hem='flare2', hand=(14, 8)),
        Frame(legs='spread', hat_dy=-1, hem='billow', hand=(14, 8)),
    ]),
]


# ────────────────────────────────────────────────────────────── preview ──
def staff_images():
    return {k: to_image([list(r) for r in rows]) for k, rows in STAFF.items()}


def with_staff(body, frame, staff, degrees, scale):
    """Body plus the staff turned `degrees` from upright (positive leans it forward),
    gripped at this frame's hand - what StaffAim does in the game. Staff behind body."""
    big = body.resize((W * scale, H * scale), Image.NEAREST)
    img = staff['bright' if frame.glow >= 2 else 'normal']
    s = img.resize((STAFF_W * scale, STAFF_H * scale), Image.NEAREST)
    # centre the grip on a square big enough for any angle before turning it, or the
    # rotation clips the ring off against the narrow strip
    side = 2 * STAFF_H * scale
    sq = Image.new('RGBA', (side, side))
    sq.alpha_composite(s, (int(side / 2 - (GRIP[0] + 0.5) * scale), int(side / 2 - (GRIP[1] + 0.5) * scale)))
    gx = gy = side / 2
    rot = sq.rotate(-degrees, resample=Image.NEAREST, center=(gx, gy), expand=False)
    pad = STAFF_H * scale
    canvas = Image.new('RGBA', (W * scale + 2 * pad, H * scale + 2 * pad))
    hx, hy = (frame.hand[0] + 0.5) * scale + pad, (frame.hand[1] + 0.5) * scale + pad
    canvas.alpha_composite(rot, (int(hx - gx), int(hy - gy)))
    canvas.alpha_composite(big, (pad, pad))
    return canvas.crop((pad - MX_L * scale, pad - MY_T * scale,
                        pad + (W + MX_R) * scale, pad + H * scale))


# Preview cells reach past the 20x22 frame: the staff sticks out of it when aimed.
MX_L, MX_R, MY_T = 2, 8, 6


def preview(save=True):
    scale, pad = 6, 10
    cols = max(len(fr) for _, fr in ANIMS)
    label_w = 90
    fh = (H + MY_T) * scale
    fw = (W + MX_L + MX_R) * scale
    staff = staff_images()
    rendered = {name: [to_image(render(f)) for f in frames] for name, frames in ANIMS}
    sheet = Image.new('RGBA', (label_w + cols * (fw + pad), len(ANIMS) * (fh + pad) + pad),
                      (26, 30, 35, 255))
    d = ImageDraw.Draw(sheet)
    for r, (name, frames) in enumerate(ANIMS):
        y = pad + r * (fh + pad)
        d.text((8, y + fh // 2 - 6), '%s (%d)' % (name, len(frames)), fill=(223, 232, 192))
        for c, (f, img) in enumerate(zip(frames, rendered[name])):
            x = label_w + c * (fw + pad)
            d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=(38, 44, 52))
            d.line((x, y + (19 + MY_T) * scale, x + fw - 1, y + (19 + MY_T) * scale), fill=(70, 78, 90))
            sheet.alpha_composite(with_staff(img, f, staff, 25, scale), (x, y))
    if not save:
        return rendered, staff
    sheet.save(os.path.join(CONCEPTS, 'HeroPilgrim_Anims.png'))

    # every animation side by side while the staff sweeps from overhead to low forward,
    # the way it follows a cursor moved around in front of him
    n = 24
    gif_frames = []
    for t in range(n):
        aim = 75 * (1 - abs((t % n) / (n / 2.0) - 1)) - 10        # -10..65 and back
        g = Image.new('RGBA', (len(ANIMS) * (fw + pad) + pad, fh + 2 * pad + 14),
                      (26, 30, 35, 255))
        gd = ImageDraw.Draw(g)
        for k, (name, frames) in enumerate(ANIMS):
            fr = rendered[name]
            x = pad + k * (fw + pad)
            gd.text((x, 4), name, fill=(223, 232, 192))
            gd.line((x, 18 + (19 + MY_T) * scale, x + fw - 1, 18 + (19 + MY_T) * scale), fill=(70, 78, 90))
            i = t % len(fr)
            g.alpha_composite(with_staff(fr[i], frames[i], staff, aim, scale), (x, 18))
        gif_frames.append(g.convert('RGB'))
    gif_frames[0].save(os.path.join(CONCEPTS, 'HeroPilgrim_Anims.gif'), save_all=True,
                       append_images=gif_frames[1:], duration=1000 // FPS, loop=0)
    return rendered, staff


# ────────────────────────────────────────────────────────────── assets ──
OUT = os.path.join(ROOT, 'Assets', 'Resources', 'Animations', 'Player', 'Pilgrim')
PREFAB = os.path.join(ROOT, 'Assets', 'Resources', 'Prefabs', 'Player.prefab')
PPU = 20
COLS = 8
# Player.prefab: the Animator on the root, View's transform and SpriteRenderer.
ANIMATOR_ID = '9013860082252455183'
VIEW_TR_ID = '7200395927289935388'
VIEW_SR_ID = '6865162776936784293'
VIEW_LAYER = 7
# The Staff node this script adds under View.
STAFF_GO, STAFF_TR, STAFF_SR, STAFF_AIM = 6300000001, 6300000002, 6300000003, 6300000004
STAFF_AIM_GUID = '08b69042be9feb7e990bf9ce397267d3'      # Assets/Scripts/Player/StaffAim.cs
# Clip binding paths are CRC32s of the path string.
PATH_VIEW = 1590625456          # "View"
PATH_STAFF = 2784195988         # "View/Staff"


def guid(key):
    return hashlib.md5(('physfun/hero-pilgrim/' + key).encode()).hexdigest()


def file_id(key):
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def sprite_id(key):
    return hashlib.md5(('sprite/' + key).encode()).hexdigest()[:16] + '0800000000000000'


NATIVE_META = ('fileFormatVersion: 2\nguid: {guid}\nNativeFormatImporter:\n'
               '  externalObjects: {{}}\n  mainObjectFileID: {main}\n  userData: \n'
               '  assetBundleName: \n  assetBundleVariant: \n')
FOLDER_META = ('fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n'
               '  externalObjects: {{}}\n  userData: \n  assetBundleName: \n'
               '  assetBundleVariant: \n')

# Centre pivot on the 20x22 frame puts the feet (bottom of row 18) 8px under the pivot -
# the same drop the old 16px Noita frames had under their centre pivot, so View keeps its
# offset and the feet still meet the ground check.
SPRITE_ENTRY = """    - serializedVersion: 2
      name: {name}
      rect:
        serializedVersion: 2
        x: {x}
        y: {y}
        width: {w}
        height: {h}
      alignment: 9
      pivot: {{x: {px}, y: {py}}}
      border: {{x: 0, y: 0, z: 0, w: 0}}
      customData:
      outline: []
      physicsShape: []
      tessellationDetail: 0
      bones: []
      spriteID: {sid}
      internalID: {iid}
      vertices: []
      indices:
      edges: []
      weights: []"""

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
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
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
    path: View/Staff
  m_ScaleCurves: []
  m_FloatCurves: []
  m_PPtrCurves:
  - serializedVersion: 2
    curve:
{body}
    attribute: m_Sprite
    path: View
    classID: 212
    script: {{fileID: 0}}
    flags: 2
  - serializedVersion: 2
    curve:
{staff}
    attribute: m_Sprite
    path: View/Staff
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
      path: {path_view}
      attribute: 0
      script: {{fileID: 0}}
      typeID: 212
      customType: 23
      isPPtrCurve: 1
      isIntCurve: 0
      isSerializeReferenceCurve: 0
    - serializedVersion: 2
      path: {path_staff}
      attribute: 0
      script: {{fileID: 0}}
      typeID: 212
      customType: 23
      isPPtrCurve: 1
      isIntCurve: 0
      isSerializeReferenceCurve: 0
    - serializedVersion: 2
      path: {path_staff}
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

# Stepped position key: the grip jumps with the frame instead of gliding between them.
POS_KEY = """      - serializedVersion: 3
        time: {t}
        value: {{x: {x}, y: {y}, z: 0}}
        inSlope: {{x: Infinity, y: Infinity, z: Infinity}}
        outSlope: {{x: Infinity, y: Infinity, z: Infinity}}
        tangentMode: 103
        weightedMode: 0
        inWeight: {{x: 0.33333334, y: 0.33333334, z: 0.33333334}}
        outWeight: {{x: 0.33333334, y: 0.33333334, z: 0.33333334}}"""


def hand_local(hand):
    """A frame pixel's centre in View's space: the body sprite's pivot is the centre of
    the 20x22 frame, y up."""
    hx, hy = hand
    return round((hx + 0.5 - W / 2.0) / PPU, 6), round((H / 2.0 - hy - 0.5) / PPU, 6)


def clip(name, frames, body_iids, tex_guid, staff_refs):
    """One key per frame for the body sprite, the staff sprite and the staff's grip, plus
    the last of each held to the end so the final frame gets its full 1/FPS."""
    body = ['{{fileID: {i}, guid: {g}, type: 3}}'.format(i=i, g=tex_guid) for i in body_iids]
    staff = [staff_refs['bright' if f.glow >= 2 else 'normal'] for f in frames]
    grip = [hand_local(f.hand) for f in frames]
    n = len(frames)
    times = [round(k / FPS, 7) for k in range(n)] + [round(n / FPS, 7)]
    body, staff, grip = body + body[-1:], staff + staff[-1:], grip + grip[-1:]

    def pptr(refs):
        return '\n'.join('    - time: {t}\n      value: {r}'.format(t=t, r=r) for t, r in zip(times, refs))

    pos = '\n'.join(POS_KEY.format(t=t, x=x, y=y) for t, (x, y) in zip(times, grip))
    mapping = ['    - ' + r for r in list(dict.fromkeys(body)) + list(dict.fromkeys(staff))]
    return CLIP.format(name=name, body=pptr(body), staff=pptr(staff), pos=pos,
                       mapping='\n'.join(mapping), stop=round(n / FPS, 7),
                       path_view=PATH_VIEW, path_staff=PATH_STAFF)


CONTROLLER_HEAD = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!91 &9100000
AnimatorController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: PilgrimAnimator
  serializedVersion: 5
  m_AnimatorParameters:
{params}
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
{children}
  m_ChildStateMachines: []
  m_AnyStateTransitions:
{any}
  m_EntryTransitions: []
  m_StateMachineTransitions: {{}}
  m_StateMachineBehaviours: []
  m_AnyStatePosition: {{x: 100, y: 180, z: 0}}
  m_EntryPosition: {{x: 100, y: 60, z: 0}}
  m_ExitPosition: {{x: 800, y: 120, z: 0}}
  m_ParentStateMachinePosition: {{x: 800, y: 20, z: 0}}
  m_DefaultState: {{fileID: 1102001}}
"""

PARAM = """  - m_Name: {name}
    m_Type: {type}
    m_DefaultFloat: {default}
    m_DefaultInt: 0
    m_DefaultBool: 0
    m_Controller: {{fileID: 9100000}}"""

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
  m_SpeedParameterActive: {speed_on}
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {{fileID: 7400000, guid: {clip}, type: 2}}
  m_Tag:
  m_SpeedParameter: {speed}
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

# Walking cycles follow the ground speed; everything else plays at its own pace.
STRIDE = {'Walk', 'WalkBack'}


def controller(clip_guids):
    names = [n for n, _ in ANIMS]
    params = [PARAM.format(name=n, type=9, default=0) for n in names]
    params.append(PARAM.format(name='Speed', type=1, default=1))
    children, anys, blocks = [], [], []
    for i, n in enumerate(names):
        sid, tid = 1102001 + i, 1101001 + i
        children.append('  - serializedVersion: 1\n    m_State: {fileID: %d}\n'
                        '    m_Position: {x: 400, y: %d, z: 0}' % (sid, 60 + 70 * i))
        anys.append('  - {fileID: %d}' % tid)
        blocks.append(STATE.format(fid=sid, name=n, clip=clip_guids[n],
                                   speed_on=1 if n in STRIDE else 0,
                                   speed='Speed' if n in STRIDE else ''))
        blocks.append(TRANSITION.format(fid=tid, param=n, dst=sid))
    return CONTROLLER_HEAD.format(params='\n'.join(params), children='\n'.join(children),
                                  any='\n'.join(anys)) + ''.join(blocks)


STAFF_NODE = """--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {tr}}}
  - component: {{fileID: {sr}}}
  - component: {{fileID: {aim}}}
  m_Layer: {layer}
  m_Name: Staff
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
  m_Father: {{fileID: {view}}}
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
  m_Sprite: {sprite}
  m_Color: {{r: 1, g: 1, b: 1, a: 1}}
  m_FlipX: 0
  m_FlipY: 0
  m_DrawMode: 0
  m_Size: {{x: 0.25, y: 0.85}}
  m_AdaptiveModeThreshold: 0.5
  m_SpriteTileMode: 0
  m_WasSpriteAssigned: 1
  m_SpriteSortPoint: 0
--- !u!114 &{aim}
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
  m_EditorClassIdentifier: Assembly-CSharp::Player.StaffAim
  follow: 20
"""


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def build(rendered, staff_imgs):
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(OUT + '.meta'):
        write(OUT + '.meta', FOLDER_META.format(guid=guid('folder')))

    # sprite sheet: every frame of every animation, COLS to a row
    order = [(n, k) for n, _ in ANIMS for k in range(len(rendered[n]))]
    rows = (len(order) + COLS - 1) // COLS
    sheet = Image.new('RGBA', (COLS * W, rows * H))
    sprites, iid_of = [], {}
    for idx, (n, k) in enumerate(order):
        col, row = idx % COLS, idx // COLS
        sheet.alpha_composite(rendered[n][k], (col * W, row * H))
        name = 'pilgrim_%s_%d' % (n, k)
        iid = file_id('pilgrim/' + name)
        iid_of[(n, k)] = iid
        sprites.append(SPRITE_ENTRY.format(name=name, x=col * W, y=(rows - 1 - row) * H,
                                           w=W, h=H, sid=sprite_id(name), iid=iid,
                                           px=0.5, py=0.5))
    png = os.path.join(OUT, 'pilgrim.png')
    sheet.save(png)
    tex_guid = guid('pilgrim.png')
    names = ['pilgrim_%s_%d' % nk for nk in order]
    mapping = '\n'.join('  - first:\n      213: %d\n    second: %s' % (iid_of[nk], nm)
                        for nk, nm in zip(order, names))
    table = '\n'.join('      %s: %d' % (nm, iid_of[nk]) for nk, nm in zip(order, names))
    write(png + '.meta', TEXTURE_META.format(guid=tex_guid, mapping=mapping,
                                             entries='\n'.join(sprites), table=table, ppu=PPU))

    # staff: two sprites side by side, both pivoted on the grip
    staff_png = os.path.join(OUT, 'staff.png')
    kinds = list(STAFF)
    strip = Image.new('RGBA', (STAFF_W * len(kinds), STAFF_H))
    staff_refs, entries, smap, stable = {}, [], [], []
    staff_guid = guid('staff.png')
    for k, kind in enumerate(kinds):
        strip.alpha_composite(staff_imgs[kind], (k * STAFF_W, 0))
        name = 'staff_' + kind
        iid = file_id('pilgrim/' + name)
        staff_refs[kind] = '{fileID: %d, guid: %s, type: 3}' % (iid, staff_guid)
        entries.append(SPRITE_ENTRY.format(
            name=name, x=k * STAFF_W, y=0, w=STAFF_W, h=STAFF_H, sid=sprite_id(name), iid=iid,
            px=round((GRIP[0] + 0.5) / STAFF_W, 6), py=round((STAFF_H - GRIP[1] - 0.5) / STAFF_H, 6)))
        smap.append('  - first:\n      213: %d\n    second: %s' % (iid, name))
        stable.append('      %s: %d' % (name, iid))
    strip.save(staff_png)
    write(staff_png + '.meta', TEXTURE_META.format(guid=staff_guid, mapping='\n'.join(smap),
                                                   entries='\n'.join(entries),
                                                   table='\n'.join(stable), ppu=PPU))

    # clips for what is in ANIMS, and nothing left over from animations that were dropped
    keep = {'Pilgrim%s.anim' % n for n, _ in ANIMS}
    for old in os.listdir(OUT):
        if old.endswith('.anim') and old not in keep:
            os.remove(os.path.join(OUT, old))
            if os.path.exists(os.path.join(OUT, old + '.meta')):
                os.remove(os.path.join(OUT, old + '.meta'))
    clip_guids = {}
    for n, frames in ANIMS:
        name = 'Pilgrim' + n
        path = os.path.join(OUT, name + '.anim')
        write(path, clip(name, frames, [iid_of[(n, k)] for k in range(len(frames))], tex_guid,
                         staff_refs))
        clip_guids[n] = guid(name)
        write(path + '.meta', NATIVE_META.format(guid=clip_guids[n], main=7400000))

    ctrl = os.path.join(OUT, 'PilgrimAnimator.controller')
    ctrl_guid = guid('PilgrimAnimator')
    write(ctrl, controller(clip_guids))
    write(ctrl + '.meta', NATIVE_META.format(guid=ctrl_guid, main=9100000))

    # point the player at it: the Animator's controller and View's resting sprite
    src = open(PREFAB, encoding='utf-8').read()
    first = '{fileID: %d, guid: %s, type: 3}' % (iid_of[('Idle', 0)], tex_guid)

    def patch(doc_id, field, value):
        nonlocal src
        m = re.search(r'--- !u!\d+ &%s\n.*?(?=\n--- |\Z)' % doc_id, src, re.S)
        doc = re.sub(r'(\n  %s: )\{[^}]*\}' % field, lambda mm: mm.group(1) + value, m.group(0), 1)
        src = src[:m.start()] + doc + src[m.end():]

    patch(ANIMATOR_ID, 'm_Controller', '{fileID: 9100000, guid: %s, type: 2}' % ctrl_guid)
    patch(VIEW_SR_ID, 'm_Sprite', first)

    # the Staff node under View, added once; later runs only refresh its sprite and grip
    gx, gy = hand_local(ANIMS[0][1][0].hand)
    if '&%d\n' % STAFF_GO not in src:
        m = re.search(r'--- !u!4 &%s\n.*?(?=\n--- |\Z)' % VIEW_TR_ID, src, re.S)
        doc = m.group(0).replace('  m_Children: []\n', '  m_Children:\n  - {fileID: %d}\n' % STAFF_TR, 1)
        src = src[:m.start()] + doc + src[m.end():]
        if not src.endswith('\n'):
            src += '\n'
        src += STAFF_NODE.format(go=STAFF_GO, tr=STAFF_TR, sr=STAFF_SR, aim=STAFF_AIM,
                                 layer=VIEW_LAYER, view=VIEW_TR_ID, px=gx, py=gy,
                                 sprite=staff_refs['normal'], script=STAFF_AIM_GUID)
    else:
        patch(STAFF_SR, 'm_Sprite', staff_refs['normal'])
    with open(PREFAB, 'w', encoding='utf-8', newline='') as f:
        f.write(src)
    print('sheet       %dx%d, %d frames -> %s' % (sheet.width, sheet.height, len(order), png))
    print('controller  %s' % ctrl)
    print('prefab      %s' % PREFAB)


if __name__ == '__main__':
    import sys
    want = '--preview' in sys.argv[1:]
    build(*preview(save=want))
    if want:
        print('preview     %s' % os.path.join(CONCEPTS, 'HeroPilgrim_Anims.png'))
