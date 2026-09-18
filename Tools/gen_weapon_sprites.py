from PIL import Image

STL_L=(178,184,194,255); STL_M=(122,129,142,255); STL_D=(72,78,90,255)
POL_L=(96,99,110,255);   POL_M=(66,69,79,255);    POL_D=(46,48,57,255)
WD_L=(158,108,64,255);   WD_M=(126,83,48,255);    WD_D=(88,56,32,255)

class C:
    def __init__(s,w,h,grip):
        s.w,s.h,s.grip=w,h,grip
        s.im=Image.new('RGBA',(w,h),(0,0,0,0)); s.p=s.im.load()
    def r(s,x0,y0,x1,y1,c):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if 0<=x<s.w and 0<=y<s.h: s.p[x,y]=c
    def px(s,x,y,c): s.r(x,y,x,y,c)

def glock():
    # grip = trigger-hand pixel
    c=C(6,6,(1,3))
    c.r(1,0,5,0,STL_L)      # slide top
    c.r(1,1,5,1,STL_M)      # slide body
    c.px(1,0,STL_D)         # rear sight
    c.px(5,1,STL_D)         # muzzle
    c.r(1,2,4,2,STL_D)      # frame / dust cover
    c.px(4,3,STL_D)         # front of trigger guard
    c.r(1,3,2,3,POL_M)      # grip
    c.r(0,4,1,4,POL_M)
    c.r(0,5,1,5,POL_D)      # magazine floorplate
    return c

def uzi():
    c=C(9,8,(3,4))
    c.r(1,0,5,0,POL_L)      # receiver top
    c.r(1,1,5,2,POL_M)      # receiver body
    c.r(1,3,5,3,POL_D)      # receiver bottom
    c.px(4,1,STL_D)         # ejection port
    c.px(2,0,STL_L)         # top charging handle
    c.r(6,1,8,1,STL_M)      # barrel
    c.r(6,2,7,2,STL_D)      # barrel shadow
    c.px(8,1,STL_D)         # muzzle
    c.r(3,4,4,6,POL_M)      # grip + magazine
    c.r(3,4,3,6,POL_L)      # front highlight
    c.r(3,7,4,7,POL_D)      # floorplate
    return c

def m4():
    c=C(13,8,(4,4))
    c.r(4,0,6,0,STL_D)      # carry handle
    c.r(0,1,1,1,POL_L)      # stock
    c.r(0,2,1,2,POL_M)
    c.r(0,3,1,3,POL_D)
    c.r(2,1,7,1,STL_M)      # upper receiver
    c.r(2,2,7,2,STL_M)
    c.r(2,3,7,3,STL_D)
    c.px(2,1,STL_L)         # charging handle
    c.px(6,2,STL_L)         # forward assist
    c.r(8,1,10,1,POL_L)     # handguard
    c.r(8,2,10,2,POL_M)
    c.r(8,3,10,3,POL_D)
    c.r(11,0,11,1,STL_D)    # front sight post
    c.r(11,2,12,2,STL_M)    # barrel
    c.px(12,2,STL_D)        # flash hider
    c.r(6,4,7,6,POL_M)      # magazine
    c.r(6,4,6,6,POL_L)
    c.r(6,7,7,7,POL_D)
    c.r(4,4,5,4,POL_M)      # pistol grip
    c.r(3,5,4,5,POL_M)
    c.r(3,6,4,6,POL_D)
    return c

def ak():
    c=C(13,8,(4,4))
    c.r(0,1,2,1,WD_L)       # wooden stock
    c.r(0,2,2,2,WD_M)
    c.r(0,3,2,3,WD_D)
    c.r(3,1,7,1,STL_L)      # dust cover
    c.r(3,2,7,2,STL_M)
    c.r(3,3,7,3,STL_D)
    c.px(6,2,STL_D)         # ejection port
    c.r(8,0,10,0,STL_D)     # gas tube
    c.r(8,1,10,1,WD_L)      # handguard
    c.r(8,2,10,2,WD_M)
    c.r(8,3,10,3,WD_D)
    c.r(11,0,11,1,STL_D)    # gas block / front sight
    c.r(11,2,12,2,STL_M)    # barrel
    c.px(12,2,STL_D)        # muzzle brake
    c.r(6,4,7,4,POL_M)      # banana magazine
    c.px(6,4,POL_L)
    c.r(7,5,8,5,POL_M)
    c.r(7,6,8,6,POL_D)
    c.r(4,4,5,4,WD_M)       # pistol grip
    c.r(3,5,4,5,WD_M)
    c.r(3,6,4,6,WD_D)
    return c

GUNS={'glock':glock(),'uzi':uzi(),'m4':m4(),'ak47':ak()}

# ---------------------------------------------------------------- export ----
import hashlib, os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'Assets', 'Resources', 'Sprites', 'Weapons')
PPU = 20   # same as the enemy sprites

META = """fileFormatVersion: 2
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
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 0
  alignment: 9
  spritePivot: {{x: {px}, y: {py}}}
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
    sprites: []
    outline: []
    customData: 
    physicsShape: []
    bones: []
    spriteID: 5e97eb03825dee720800000000000000
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
    secondaryTextures: []
    nameFileIdTable: {{}}
  mipmapLimitGroupName: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

FOLDER_META = "fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"


def guid_for(key):
    return hashlib.md5(('physfun/weapons/' + key).encode()).hexdigest()


def export():
    out = os.path.normpath(OUT_DIR)
    os.makedirs(out, exist_ok=True)
    fm = out + '.meta'
    if not os.path.exists(fm):
        open(fm, 'w').write(FOLDER_META.format(guid=guid_for('folder')))
    for name, g in GUNS.items():
        png = os.path.join(out, name + '.png')
        g.im.save(png)
        gx, gy = g.grip
        open(png + '.meta', 'w').write(META.format(
            guid=guid_for(name),
            px=round((gx + 0.5) / g.w, 6),
            py=round((g.h - gy - 0.5) / g.h, 6),
            ppu=PPU))
        print('%-6s %2dx%-2d grip=%s -> %s' % (name, g.w, g.h, g.grip, png))


if __name__ == '__main__':
    export()
