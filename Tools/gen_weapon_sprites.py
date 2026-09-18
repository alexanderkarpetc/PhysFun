from PIL import Image

STL_L=(178,184,194,255); STL_M=(122,129,142,255); STL_D=(72,78,90,255)
POL_L=(112,116,128,255); POL_M=(80,84,95,255);    POL_D=(56,59,69,255)
WD_L=(158,108,64,255);   WD_M=(126,83,48,255);    WD_D=(88,56,32,255)

# Energy weapons run on a darker chassis than the ballistics so the glow reads.
BLK_L=(78,82,96,255);    BLK_M=(52,55,68,255);    BLK_D=(32,34,44,255)
CYN_L=(168,246,250,255); CYN_M=(64,206,214,255);  CYN_D=(28,118,138,255)
VIO_L=(206,164,255,255); VIO_M=(152,88,224,255);  VIO_D=(86,44,138,255)

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
    c=C(8,8,(3,4))
    c.r(1,0,5,0,POL_L)      # receiver top
    c.r(1,1,5,1,POL_M)      # receiver body
    c.r(1,2,5,2,POL_M)
    c.r(1,3,5,3,POL_D)      # receiver bottom
    c.px(2,0,STL_L)         # top charging handle
    c.r(4,1,5,1,STL_D)      # ejection port
    c.r(6,1,7,1,STL_M)      # barrel
    c.px(7,1,STL_D)         # muzzle
    c.px(6,2,POL_D)         # barrel shoulder
    c.r(3,4,4,6,POL_M)      # grip + magazine
    c.r(3,4,3,6,POL_L)      # front highlight
    c.r(3,7,4,7,POL_D)      # floorplate
    return c

def mp5():
    # One unbroken bore line from buttplate to muzzle ties the stock, receiver
    # and handguard together; the grip and magazine hang off it with a gap
    # between them so neither reads as one brick.
    c=C(9,8,(2,4))
    c.r(2,1,6,1,POL_L)      # receiver top
    c.r(0,2,8,2,POL_M)      # stock / receiver / handguard
    c.r(2,3,8,3,POL_D)      # underside
    c.px(1,1,POL_D)         # buttplate
    c.px(1,3,POL_D)
    c.px(5,0,STL_D)         # rear drum sight
    c.px(8,0,STL_D)         # front sight
    c.px(4,2,STL_D)         # ejection port
    c.r(5,4,6,5,POL_M)      # magazine, angled forward
    c.px(5,4,POL_L)
    c.px(6,6,POL_D)
    c.r(2,4,3,4,POL_M)      # pistol grip
    c.r(2,5,3,5,POL_M)
    c.r(2,6,3,6,POL_D)
    return c

def shotgun():
    c=C(11,7,(3,4))
    c.r(3,1,10,1,STL_M)     # barrel
    c.px(10,1,STL_D)        # muzzle
    c.r(6,2,9,2,STL_D)      # magazine tube under the barrel
    c.r(0,1,2,1,WD_L)       # stock
    c.r(0,2,2,2,WD_M)
    c.r(0,3,2,3,WD_D)
    c.r(3,2,5,2,STL_M)      # receiver
    c.r(3,3,5,3,STL_D)
    c.px(5,3,STL_D)         # trigger
    c.r(6,3,8,3,WD_M)       # pump forend
    c.r(6,4,8,4,WD_D)
    c.r(3,4,4,4,WD_M)       # grip
    c.r(2,5,3,5,WD_M)
    c.r(2,6,3,6,WD_D)
    return c

def m4():
    c=C(11,8,(3,4))
    c.r(3,0,5,0,STL_D)      # carry handle
    c.r(0,1,1,1,POL_L)      # stock
    c.r(0,2,1,2,POL_M)
    c.r(0,3,1,3,POL_D)
    c.r(2,1,6,1,STL_M)      # upper receiver
    c.r(2,2,6,2,STL_M)
    c.r(2,3,6,3,STL_D)
    c.px(2,1,STL_L)         # charging handle
    c.px(5,2,STL_L)         # forward assist
    c.r(7,1,8,1,POL_L)      # handguard
    c.r(7,2,8,2,POL_M)
    c.r(7,3,8,3,POL_D)
    c.r(9,0,9,1,STL_D)      # front sight post
    c.r(9,2,10,2,STL_M)     # barrel
    c.px(10,2,STL_D)        # flash hider
    c.r(5,4,6,6,POL_M)      # magazine
    c.r(5,4,5,6,POL_L)
    c.r(5,7,6,7,POL_D)
    c.r(3,4,4,4,POL_M)      # pistol grip
    c.r(2,5,3,5,POL_M)
    c.r(2,6,3,6,POL_D)
    return c

def ak():
    c=C(11,8,(3,4))
    c.r(0,1,2,1,WD_L)       # wooden stock
    c.r(0,2,2,2,WD_M)
    c.r(0,3,2,3,WD_D)
    c.r(3,1,6,1,STL_L)      # dust cover
    c.r(3,2,6,2,STL_M)
    c.r(3,3,6,3,STL_D)
    c.px(5,2,STL_D)         # ejection port
    c.r(7,0,8,0,STL_D)      # gas tube
    c.r(7,1,8,1,WD_L)       # handguard
    c.r(7,2,8,2,WD_M)
    c.r(7,3,8,3,WD_D)
    c.r(9,0,9,1,STL_D)      # gas block / front sight
    c.r(9,2,10,2,STL_M)     # barrel
    c.px(10,2,STL_D)        # muzzle brake
    c.r(5,4,6,4,POL_M)      # banana magazine
    c.px(5,4,POL_L)
    c.r(6,5,7,5,POL_M)
    c.r(6,6,7,6,POL_D)
    c.r(3,4,4,4,WD_M)       # pistol grip
    c.r(2,5,3,5,WD_M)
    c.r(2,6,3,6,WD_D)
    return c

def sniper():
    c=C(12,8,(3,4))
    c.r(4,0,8,0,STL_L)      # scope tube, bright over a dark shadow so the
    c.r(4,1,8,1,STL_D)      # glass reads as a scope and not as a carry handle
    c.px(4,0,STL_M)         # ocular bell
    c.r(0,2,2,2,WD_L)       # wooden stock
    c.r(0,3,2,3,WD_M)
    c.r(0,4,2,4,WD_D)
    c.r(3,2,7,2,STL_M)      # receiver
    c.r(3,3,7,3,STL_D)
    c.px(6,3,STL_M)         # bolt handle
    c.r(8,2,11,2,STL_M)     # barrel
    c.px(11,2,STL_D)        # muzzle
    c.r(8,3,9,3,WD_M)       # forend
    c.px(5,4,POL_D)         # box magazine
    c.r(3,4,4,4,WD_M)       # grip
    c.r(3,5,4,5,WD_M)
    c.r(3,6,4,6,WD_D)
    return c

# ------------------------------------------------------------ energy guns ----
def laserpistol():
    c=C(7,6,(1,3))
    c.r(1,0,5,0,BLK_M)      # slide
    c.r(1,1,4,1,BLK_L)
    c.r(2,1,4,1,VIO_M)      # charge window
    c.px(3,1,VIO_L)
    c.r(5,1,6,1,BLK_D)      # emitter housing
    c.px(6,1,VIO_L)         # lens
    c.r(1,2,4,2,BLK_D)      # frame
    c.px(4,3,BLK_D)         # trigger guard
    c.r(0,3,1,3,BLK_M)      # grip
    c.px(1,4,VIO_D)         # cell window
    c.px(0,4,BLK_M)
    c.r(0,5,1,5,BLK_D)      # cell floor
    return c

def arcgun():
    # Two prongs with the arc jumping between them; the coils behind wind up.
    c=C(9,8,(2,4))
    c.r(1,1,6,1,BLK_L)      # body top
    c.r(1,2,6,2,BLK_M)
    c.r(1,3,6,3,BLK_D)
    c.r(4,1,5,1,VIO_M)      # coil rings
    c.px(4,2,VIO_L)
    c.r(7,0,7,3,BLK_D)      # emitter head
    c.px(8,0,BLK_D)         # prong tips
    c.px(8,3,BLK_D)
    c.px(8,1,CYN_L)         # arc jumping between them
    c.px(8,2,CYN_M)
    c.r(2,4,3,4,BLK_M)      # grip
    c.r(2,5,3,5,BLK_M)
    c.r(2,6,3,6,BLK_D)
    c.r(4,4,5,5,VIO_M)      # capacitor pack
    c.px(4,4,VIO_L)
    c.r(4,6,5,6,VIO_D)
    return c

def plasmarifle():
    c=C(11,8,(3,4))
    c.r(4,0,7,0,CYN_D)      # plasma tank
    c.r(5,0,6,0,CYN_M)
    c.px(5,0,CYN_L)
    c.r(2,1,8,1,BLK_L)      # receiver
    c.r(2,2,8,2,BLK_M)
    c.r(2,3,8,3,BLK_D)
    c.r(5,3,7,3,CYN_D)      # vent slots
    c.r(0,2,1,2,BLK_M)      # stock
    c.r(0,3,1,3,BLK_D)
    c.r(9,1,10,1,BLK_D)     # emitter shroud
    c.r(9,3,10,3,BLK_D)
    c.px(9,2,CYN_M)         # bore
    c.px(10,2,CYN_L)
    c.r(3,4,4,4,BLK_M)      # grip
    c.r(2,5,3,5,BLK_M)
    c.r(2,6,3,6,BLK_D)
    c.r(5,4,6,5,BLK_M)      # cell magazine
    c.r(5,4,5,5,CYN_D)      # charge strip down its side
    c.px(5,4,CYN_M)
    c.r(5,6,6,6,BLK_D)
    return c

def railgun():
    # The rail itself is the read: a checkered cell strip running the length of
    # it, bracketed by a dark housing.
    c=C(12,8,(3,4))
    c.r(4,0,11,0,BLK_D)     # rail housing, top
    c.r(4,3,10,3,BLK_D)     # rail housing, bottom
    for x in range(5,11):   # energy cells
        c.px(x,1,CYN_L if x%2 else CYN_D)
        c.px(x,2,CYN_D if x%2 else CYN_L)
    c.r(11,1,11,2,CYN_L)    # muzzle
    c.r(1,1,4,1,BLK_L)      # receiver
    c.r(1,2,4,2,BLK_M)
    c.r(1,3,3,3,BLK_M)
    c.r(0,2,1,2,BLK_M)      # stock
    c.r(0,3,1,3,BLK_D)
    c.r(3,4,4,4,BLK_M)      # grip
    c.r(2,5,3,5,BLK_M)
    c.r(2,6,3,6,BLK_D)
    c.px(5,4,CYN_D)         # capacitor under the rail
    c.px(6,4,CYN_M)
    return c

def voidcannon():
    c=C(11,8,(3,4))
    c.r(1,1,7,1,BLK_L)      # heavy body
    c.r(1,2,7,2,BLK_M)
    c.r(1,3,7,3,BLK_D)
    c.r(4,2,5,2,VIO_M)      # core
    c.px(4,2,VIO_L)
    c.px(4,1,VIO_D)
    c.r(0,2,1,2,BLK_M)      # stock
    c.r(0,3,1,3,BLK_D)
    c.r(8,0,10,0,BLK_D)     # muzzle bell
    c.r(8,1,10,1,BLK_M)
    c.r(8,2,10,2,VIO_M)
    c.px(10,2,VIO_L)
    c.r(8,3,10,3,BLK_D)
    c.r(3,4,4,4,BLK_M)      # grip
    c.r(2,5,3,5,BLK_M)
    c.r(2,6,3,6,BLK_D)
    c.r(5,4,6,4,VIO_D)      # underslung cell
    c.r(5,5,6,5,VIO_M)
    c.r(5,6,6,6,VIO_D)
    return c

# ---------------------------------------------------------------- miniguns ----
BRS=(168,140,66,255)


def _minigun(body_l, body_m, body_d, frame, cell_l, cell_m, cell_d,
             pack_l, pack_d, checker):
    """Shared chassis: a four-row motor box at the back — one row deeper than
    any rifle here — feeding a shrouded barrel section, with the pack slung
    underneath. It keeps a rifle's height above the hand so it does not swallow
    the soldier's head; the bulk comes from depth and from the pack instead.

    Spun barrels read as a lit bundle pinched by dark clamp rings; the energy
    version swaps that for the cell checker off the reference.
    """
    c=C(12,7,(2,4))
    c.r(1,0,4,0,body_l)     # motor housing
    c.r(1,1,4,2,body_m)
    c.r(1,3,4,3,body_d)
    c.r(4,1,4,2,cell_d)     # drive port
    if checker:
        c.r(5,0,11,0,frame)     # shroud, top
        c.r(5,3,11,3,frame)     # shroud, bottom
        for x in range(5,12):
            c.px(x,1,cell_l if x%2 else cell_d)
            c.px(x,2,cell_d if x%2 else cell_l)
    else:
        # No shroud here — bare barrels, each row one of them, lit from above.
        c.r(5,0,11,0,cell_m)
        c.r(5,1,11,1,cell_l)
        c.r(5,2,11,2,cell_m)
        c.r(5,3,11,3,cell_d)
        c.r(8,0,8,3,cell_d)     # clamp ring
        c.r(11,0,11,3,cell_d)   # muzzle ends
    c.r(2,4,3,4,body_m)     # spade grip
    c.r(2,5,3,5,body_m)
    c.r(2,6,3,6,body_d)
    c.r(5,4,7,4,pack_l)     # ammo pack, slung under the shroud
    c.r(5,5,7,5,pack_d)
    c.px(5,4,pack_d)
    return c


def minigun():
    return _minigun(STL_L,STL_M,STL_D,BLK_D,STL_L,STL_M,STL_D,BRS,WD_D,
                    checker=False)


def energyminigun():
    return _minigun(BLK_L,BLK_M,BLK_D,BLK_D,CYN_L,CYN_M,CYN_D,VIO_M,VIO_D,
                    checker=True)


GUNS={'glock':glock(),'uzi':uzi(),'mp5':mp5(),'shotgun':shotgun(),
      'm4':m4(),'ak47':ak(),'sniper':sniper(),
      'laserpistol':laserpistol(),'arcgun':arcgun(),'plasmarifle':plasmarifle(),
      'railgun':railgun(),'voidcannon':voidcannon(),
      'minigun':minigun(),'energyminigun':energyminigun()}

# ------------------------------------------------------------ projectiles ----
# Tracers, drawn pointing right and brightest at the tip so the direction of
# travel reads even at four pixels. Pivoted on the middle: a shot then only has
# to be rotated to its heading.
def projectile_ballistic():
    c=C(4,1,(1,0))
    c.px(0,0,(190,140,50,255))
    c.px(1,0,(232,182,66,255))
    c.px(2,0,(255,220,110,255))
    c.px(3,0,(255,245,190,255))
    return c


def projectile_energy():
    c=C(4,2,(1,0))
    c.px(0,0,(40,160,180,255))
    c.px(1,0,(70,206,215,255))
    c.px(2,0,(150,240,246,255))
    c.px(3,0,(210,252,254,255))
    c.px(0,1,(26,120,140,255))
    c.px(1,1,(40,160,180,255))
    c.px(2,1,(70,206,215,255))
    c.px(3,1,(150,240,246,255))
    return c


PROJECTILES={'projectile_ballistic':projectile_ballistic(),
             'projectile_energy':projectile_energy()}

# One pixel, stretched along x by the holder. Pivoted on its left edge so the
# scale that makes it reach is just the distance.
def laser_pixel():
    c=C(1,1,(0,0))
    c.px(0,0,(255,64,54,255))
    return c

LASER={'laser_pixel':laser_pixel()}


# ----------------------------------------------------------------- stats ----
# name -> (display, energy?, damage, rate, burst, cooldown, windUp, laser,
#          pellets, spread, speed, recoil, magazine, reload)
#
# rate is the cadence *inside* a burst; cooldown is the gap between bursts, and
# for a single-shot gun it is the fire rate. Speeds are deliberately slow — the
# rounds are meant to be watchable, and the arc is half the read.
STATS = {
    'glock':         ('Glock',          0,  6,  5.0,  1, 0.55, 0.0, 0, 1,  2.0, 13, 0.04,  17, 1.2),
    'uzi':           ('Uzi',            0,  4, 14.0,  3, 0.60, 0.0, 0, 1,  6.0, 12, 0.03,  32, 1.6),
    'mp5':           ('MP5',            0,  5, 13.0,  3, 0.50, 0.0, 0, 1,  4.0, 13, 0.035, 30, 1.7),
    'shotgun':       ('Shotgun',        0,  4,  1.0,  1, 1.10, 0.0, 0, 3, 14.0, 10, 0.25,   6, 2.6),
    'm4':            ('M4',             0,  7, 11.0, 14, 1.30, 0.0, 0, 1,  3.5, 15, 0.05,  30, 1.9),
    'ak47':          ('AK-47',          0,  9,  9.0, 12, 1.60, 0.0, 0, 1,  5.0, 14, 0.07,  30, 2.1),
    'sniper':        ('Sniper Rifle',   0, 28,  1.0,  1, 0.80, 1.8, 1, 1,  0.3, 24, 0.30,   5, 2.4),
    'minigun':       ('Minigun',        0,  5, 16.0, 40, 1.80, 1.2, 0, 1,  8.0, 14, 0.06, 150, 5.0),
    'laserpistol':   ('Laser Pistol',   1,  7,  5.0,  1, 0.40, 0.0, 0, 1,  0.0, 20, 0.02,  24, 1.1),
    'arcgun':        ('Arc Gun',        1,  3, 16.0,  8, 0.70, 0.0, 0, 1, 10.0, 11, 0.01,  60, 1.8),
    'plasmarifle':   ('Plasma Rifle',   1, 12,  6.0,  4, 0.90, 0.0, 0, 1,  2.0, 11, 0.08,  24, 2.0),
    'railgun':       ('Railgun',        1, 40,  1.0,  1, 1.80, 0.0, 0, 1,  0.0, 35, 0.40,   4, 2.8),
    'voidcannon':    ('Void Cannon',    1, 22,  1.0,  1, 1.40, 0.0, 0, 1,  6.0,  8, 0.30,   8, 2.5),
    'energyminigun': ('Energy Minigun', 1,  6, 18.0, 40, 1.60, 1.0, 0, 1,  7.0, 15, 0.05, 200, 4.5),
}


def muzzle_offset(g):
    """Tip of the barrel relative to the grip pivot, in local units.

    Taken from the art rather than typed per gun: the rightmost column that has
    any pixels is the muzzle, and the middle of that column's filled rows is the
    bore. Redraw a gun and the offset follows it.
    """
    p = g.im.load()
    for x in range(g.w - 1, -1, -1):
        rows = [y for y in range(g.h) if p[x, y][3]]
        if not rows:
            continue
        bore = (min(rows) + max(rows)) / 2.0
        return ((x + 0.5 - g.grip[0]) / PPU, (g.grip[1] - bore) / PPU)
    return (0.0, 0.0)


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


ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'Assets', 'Resources', 'Weapons')

# Assets/Scripts/Weapons/WeaponDefinition.cs.meta
DEFINITION_SCRIPT_GUID = '0c9b5183167f9c9e60ec1719c71d7aa7'

ASSET = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {script}, type: 3}}
  m_Name: {name}
  m_EditorClassIdentifier: Assembly-CSharp::Weapons.WeaponDefinition
  displayName: {display}
  kind: {kind}
  sprite: {{fileID: 21300000, guid: {sprite}, type: 3}}
  projectile: {{fileID: 21300000, guid: {projectile}, type: 3}}
  muzzleOffset: {{x: {mx}, y: {my}}}
  holdOffset: {{x: 0, y: 0}}
  sortingOrder: 1
  fire:
    damage: {damage}
    rate: {rate}
    burst: {burst}
    burstCooldown: {cooldown}
    windUp: {windup}
    laserSight: {laser}
    pellets: {pellets}
    spread: {spread}
    projectileSpeed: {speed}
    gravity: {gravity}
    recoil: {recoil}
    magazine: {magazine}
    reloadTime: {reload}
"""


def export():
    out = os.path.normpath(OUT_DIR)
    os.makedirs(out, exist_ok=True)
    fm = out + '.meta'
    if not os.path.exists(fm):
        open(fm, 'w').write(FOLDER_META.format(guid=guid_for('folder')))

    assets = os.path.normpath(ASSET_DIR)
    os.makedirs(assets, exist_ok=True)
    am = assets + '.meta'
    if not os.path.exists(am):
        open(am, 'w').write(FOLDER_META.format(guid=guid_for('asset-folder')))

    for name, g in PROJECTILES.items():
        png = os.path.join(out, name + '.png')
        g.im.save(png)
        open(png + '.meta', 'w').write(META.format(
            guid=guid_for(name), px=0.5, py=0.5, ppu=PPU))
        print('%-14s %2dx%-2d' % (name, g.w, g.h))

    for name, g in LASER.items():
        png = os.path.join(out, name + '.png')
        g.im.save(png)
        open(png + '.meta', 'w').write(META.format(
            guid=guid_for(name), px=0.0, py=0.5, ppu=PPU))
        print('%-14s %2dx%-2d' % (name, g.w, g.h))

    for name, g in GUNS.items():
        png = os.path.join(out, name + '.png')
        g.im.save(png)
        gx, gy = g.grip
        sprite_guid = guid_for(name)
        open(png + '.meta', 'w').write(META.format(
            guid=sprite_guid,
            px=round((gx + 0.5) / g.w, 6),
            py=round((g.h - gy - 0.5) / g.h, 6),
            ppu=PPU))

        (display, energy, dmg, rate, burst, cool, wind, laser,
         pel, spread, spd, rec, mag, rel) = STATS[name]
        # Same pull on every round. Well under real gravity because the rounds
        # are slow now: at full pull a pistol shot would fall short of the range
        # the soldier spots you at, so he would aim and never fire.
        grav = 0.35
        mx, my = muzzle_offset(g)
        asset = os.path.join(assets, name + '.asset')
        open(asset, 'w').write(ASSET.format(
            script=DEFINITION_SCRIPT_GUID, name=name, display=display,
            kind=1 if energy else 0, sprite=sprite_guid,
            projectile=guid_for('projectile_energy' if energy
                                else 'projectile_ballistic'),
            mx=round(mx, 6), my=round(my, 6),
            damage=dmg, rate=rate, burst=burst, pellets=pel, spread=spread,
            speed=spd, gravity=grav, recoil=rec, magazine=mag, reload=rel,
            cooldown=cool, windup=wind, laser=laser))
        open(asset + '.meta', 'w').write(
            'fileFormatVersion: 2\nguid: {g}\nNativeFormatImporter:\n'
            '  externalObjects: {{}}\n  mainObjectFileID: 11400000\n  userData: \n'
            '  assetBundleName: \n  assetBundleVariant: \n'
            .format(g=guid_for('asset/' + name)))

        print('%-14s %2dx%-2d grip=%s muzzle=(%+.3f,%+.3f)'
              % (name, g.w, g.h, g.grip, mx, my))


if __name__ == '__main__':
    export()
