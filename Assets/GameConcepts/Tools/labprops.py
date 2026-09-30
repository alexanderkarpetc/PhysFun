"""Lab props - the underground laboratory's collidable objects, at game scale.

    python Assets/GameConcepts/Tools/labprops.py

Writes `Assets/GameConcepts/Icons/Lab/Icon_<Name>.png` (transparent, x4) and the contact
sheet `Assets/GameConcepts/Icons/IconSheet_Lab.png`. The same kit and the same rules as
`mineprops.py` - one pixel is one 20-PPU sprite pixel, every object is one body, a
container is the U it is, a real opening is keyed out - so the lab reads as a room bored
off the same haulage level rather than a different game.

It stays dry on purpose, like the first lab set: no beakers, vats or tanks of anything,
because there is no liquid simulation. The lab's dangers are the ones the engine has -
electricity (ArcField), gas and vacuum, hot solids, magnets, and blast.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mineprops as mp  # noqa: E402
from mineprops import *  # noqa: F403,E402  (the helpers, palette and ramps)

OUT_DIR = os.path.join("Icons", "Lab")

# ── the lab's own materials, on top of the mine's iron, timber and rust ─────────────
COP_D, COP, COP_L, COP_XL = (92, 62, 44), (131, 96, 70), (170, 124, 84), (205, 160, 110)
CER_D, CER, CER_L = (110, 104, 92), (165, 157, 140), (201, 204, 190)
SLATE_D, SLATE, SLATE_L = (38, 40, 48), (56, 60, 70), (78, 84, 96)
BRICK_D, BRICK, BRICK_L = (78, 48, 40), (110, 66, 50), (138, 88, 64)
SAFE_D, SAFE, SAFE_L = (44, 52, 50), (66, 78, 74), (96, 110, 104)
LAMP_G, LAMP_R, LAMP_A = (159, 187, 83), (180, 80, 70), F_MID
SCOPE = (40, 60, 52)

COP_RAMP = (COP_D, COP, COP_L, COP_XL)
CER_RAMP = (CER_D, CER, CER_L)
BRICK_RAMP = (BRICK_D, BRICK, BRICK_L)
POLISH = (IRON, IRON_M, IRON_L, IRON_XL)
OLIVE_RAMP = (OLIVE_D, OLIVE, OLIVE_L)
RED_RAMP = (RUST_D, PAINT_R, PAINT_RL)


def dial(cx, cy, r=2.2, needle=(1, -1)):
    """A meter face: pale disc, dark rim, a needle off the centre."""
    DC(cx, cy, r, CER_L)
    RG(cx, cy, r, IRON_D)
    P(int(cx), int(cy), INK)
    P(int(cx) + needle[0], int(cy) + needle[1], INK)


def cylinder(x, y0, y1, ramp, band=CER_L):
    """A gas bottle standing up, 5px wide: valve on the neck, rounded shoulder, a pale
    band under it for the label."""
    R(x + 1, y0, x + 3, y0, IRON_M)                        # handwheel
    P(x + 2, y0 + 1, IRON_L)                               # valve
    for y in range(y0 + 2, y1 + 1):
        for i in range(5):
            if y == y0 + 2 and i in (0, 4):
                continue                                   # the shoulder
            dshade(x + i, y, 0.95 - 0.22 * i, ramp)
    R(x, y0 + 4, x + 4, y0 + 4, band)
    P(x + 4, y0 + 4, CER_D)


# ═══════════════════════════════════════════════════════════════════════════
#  POWER AND FIELDS - what the lab runs on, and what arcs
# ═══════════════════════════════════════════════════════════════════════════
def dynamo():
    """A belt-driven dynamo on its bedplate: field frame, copper commutator, pulley. It
    turns when the line shaft does, and the terminals on top are live."""
    box(0, 15, 27, 17, IRON_D, IRON, IRON_M)               # bedplate
    R(4, 13, 6, 14, IRON_D)                                # feet
    R(14, 13, 16, 14, IRON_D)
    log_h(3, 3, 18, 12, IRON_RAMP, IRON_D, ends=False)     # field frame
    for x in (6, 9, 12, 15):                               # vent slots
        R(x, 6, x, 9, IRON_D)
    box(7, 1, 13, 2, IRON_D, IRON_M, IRON_L)               # terminal box
    P(9, 0, COP_L)
    P(12, 0, COP_L)
    P(10, 10, GOLD)                                        # maker's plate
    P(11, 10, GOLD)
    log_h(19, 5, 22, 10, COP_RAMP, COP_D, ends=False)      # commutator
    for y in range(5, 11, 2):
        P(20, y, COP_D)
        P(22, y, COP_D)
    P(20, 4, IRON_L)                                       # brushes
    P(21, 11, IRON_L)
    R(23, 7, 24, 8, IRON_L)                                # shaft
    R(23, 9, 24, 14, IRON_D)                               # bearing pedestal
    box(25, 4, 27, 11, IRON_D, IRON_M, IRON_L)             # pulley
    grime(0, 1, 27, 17, 20, (RUST, RUST_D), on=IRON_RAMP)


def battery_bank():
    """A timber rack of accumulator cells, strapped in series. Each cell is its own body,
    so a knocked shelf spills them - still charged."""
    log_v(0, 0, 1, 19)                                     # posts
    log_v(28, 0, 29, 19)
    box(0, 8, 29, 9, TIM_D, TIM, TIM_M)                    # shelves
    box(0, 18, 29, 19, TIM_D, TIM, TIM_M)
    for top in (3, 13):
        for k, x in enumerate((3, 9, 15, 21)):
            box(x, top, x + 4, top + 4, SLATE_D, SLATE, SLATE_L)
            P(x + 1, top - 1, COP_L)                       # + and -
            P(x + 3, top - 1, IRON_L)
            P(x + 2, top + 3, CER if k % 2 else STRIPE)
            if k < 3:                                      # the strap to the next cell
                R(x + 3, top - 2, x + 7, top - 2, IRON_M)
    R(24, 1, 24, 2, CABLE)                                 # the lead off the end
    R(25, 1, 27, 1, CABLE)


def transformer():
    """A step-up transformer: finned tank, three porcelain bushings on the lid, a striped
    warning plate. The ArcField source - metal near it gets the arc."""
    box(1, 23, 18, 25, IRON_D, IRON, IRON_M)               # skid
    for y in range(8, 23):                                 # tank
        for x in range(3, 17):
            dshade(x, y, 0.9 - 0.06 * (x - 3), OLIVE_RAMP)
    for y in range(9, 22, 2):                              # cooling fins
        R(0, y, 2, y, IRON_M)
        R(17, y, 19, y, IRON_D)
    box(2, 6, 17, 7, IRON_D, IRON_M, IRON_L)               # lid
    for x in (5, 9, 13):                                   # bushings, ribbed
        for y in range(0, 6):
            if y % 2:
                R(x - 1, y, x + 2, y, CER)
                P(x + 2, y, CER_D)
            else:
                R(x, y, x + 1, y, CER_L if y else COP_L)
    R(7, 13, 12, 17, STRIPE)                               # the warning plate
    for x, y in ((10, 14), (9, 15), (10, 15), (9, 16)):
        P(x, y, INK)
    grime(0, 6, 19, 25, 20, (RUST, RUST_D, OLIVE_D), on=IRON_RAMP + OLIVE_RAMP)


def switchboard():
    """A slate switchboard on iron legs: three knife switches (one thrown open), a row of
    fuses, two meters, two lamps. Every blade is a copper collider and a live one."""
    log_h(0, 0, 25, 1)                                     # timber header
    box(0, 2, 25, 26, SLATE_D, SLATE, SLATE_L)             # the slab
    R(1, 27, 2, 29, IRON_D)                                # legs
    R(23, 27, 24, 29, IRON_D)
    for k, x in enumerate((4, 11, 18)):
        box(x, 4, x + 2, 5, CER_D, CER, CER_L)             # jaws
        box(x, 11, x + 2, 12, CER_D, CER, CER_L)           # hinge block
        if k == 1:                                         # this one is open
            R(x + 1, 13, x + 1, 18, COP_L)
            P(x + 1, 19, INK)
        else:
            R(x + 1, 6, x + 1, 10, COP_L)
            P(x + 1, 3, INK)
    for x in (4, 8, 15, 19):                               # fuses
        box(x, 15, x + 2, 17, CER_D, CER, CER_L)
        P(x + 1, 16, COP)
    dial(7, 22)
    dial(18, 22, needle=(-1, -1))
    P(12, 22, LAMP_R)
    P(13, 24, LAMP_G)


def tesla_coil():
    """A resonant coil: cabinet, flat primary, tall copper secondary, polished toroid on
    top. The tallest arc source in the lab - it reaches whatever is closest and metal."""
    box(1, 34, 16, 41, IRON_D, IRON, IRON_M)               # cabinet
    for x in range(4, 14, 3):
        R(x, 37, x, 39, IRON_D)
    R(0, 32, 17, 32, COP_L)                                # primary, edge-on
    R(1, 33, 16, 33, COP_D)
    R(5, 31, 12, 31, CER_D)                                # former, bottom and top
    R(5, 10, 12, 10, CER_D)
    for y in range(11, 31):                                # secondary windings
        for x in range(6, 12):
            dshade(x, y, 0.95 - 0.13 * (x - 6) - (0.22 if y % 2 else 0), COP_RAMP)
    R(8, 8, 9, 9, IRON_M)                                  # stem
    for y in range(2, 8):                                  # toroid, side-on
        for x in range(18):
            ends = min(x, 17 - x)
            if ends >= 2 or (ends == 1 and 3 <= y <= 6) or (ends == 0 and 4 <= y <= 5):
                dshade(x, y, 1.0 - 0.17 * (y - 2), POLISH)
    P(3, 3, IRON_XL)


def van_de_graaff():
    """An electrostatic generator: a belt in an insulating column charging a polished
    sphere. Walk past it with iron in hand and find out."""
    box(1, 33, 12, 37, IRON_D, IRON, IRON_M)               # base
    P(3, 35, IRON_L)
    for y in range(12, 33):                                # column
        for x in range(5, 9):
            dshade(x, y, 0.9 - 0.25 * (x - 5), CER_RAMP)
    for y in (20, 28):
        R(5, y, 8, y, CER_D)
    sdisc(7, 6.5, 6.5, POLISH, base=0.6)                   # sphere
    P(4, 3, IRON_XL)
    P(5, 3, IRON_XL)
    P(4, 4, IRON_XL)


# ═══════════════════════════════════════════════════════════════════════════
#  HEAT, GAS AND VACUUM
# ═══════════════════════════════════════════════════════════════════════════
def muffle_furnace():
    """The assay furnace: a brick body in an iron frame, door with a glowing spy hole,
    flue off the back. The outside is hot enough to light timber that touches it."""
    R(2, 24, 3, 27, IRON_D)                                # legs
    R(22, 24, 23, 27, IRON_D)
    box(1, 22, 24, 23, IRON_D, IRON, IRON_M)               # base plate
    for y in range(6, 22):                                 # brickwork
        for x in range(1, 25):
            if y % 3 == 0 or (x + ((y // 3) % 2) * 3) % 6 == 0:
                P(x, y, BRICK_D)
            else:
                dshade(x, y, 0.85 - 0.02 * y - 0.01 * x, BRICK_RAMP)
    R(1, 6, 1, 21, IRON_M)                                 # corner angles
    R(24, 6, 24, 21, IRON_D)
    box(0, 4, 25, 5, IRON_D, IRON_M, IRON_L)               # top plate
    box(19, 0, 22, 3, IRON_D, IRON, IRON_M)                # flue
    P(20, 1, IRON_L)
    box(7, 10, 18, 18, IRON_D, IRON, IRON_M)               # door
    R(11, 13, 14, 14, F_MID)                               # spy hole
    P(12, 13, F_HOT)
    P(13, 13, F_HOT)
    R(8, 19, 17, 19, F_COOL)                               # heat at the door gap
    R(19, 13, 20, 14, IRON_L)                              # latch
    dial(4, 9, 1.6)                                        # pyrometer
    grime(0, 4, 25, 23, 16, (IRON_D, RUST_D), on=IRON_RAMP)


def fume_hood():
    """A fume hood on its cabinet: the working space is a pocket open at the front, under
    a steel sash that is half down, with a burner on the slate and the duct overhead.
    What burns in there draws up the duct; what is shut in there stays in."""
    box(0, 22, 27, 35, IRON_D, IRON, IRON_M)               # cabinet
    R(13, 24, 13, 34, IRON_D)
    P(11, 28, IRON_L)
    P(15, 28, IRON_L)
    box(0, 20, 27, 21, SLATE_D, SLATE, SLATE_L)            # work surface
    box(24, 8, 27, 19, IRON_D, IRON, IRON_M)               # back wall
    box(0, 4, 27, 7, IRON_D, IRON_M, IRON_L)               # hood
    box(18, 0, 22, 3, IRON_D, IRON_M, IRON_L)              # duct
    box(0, 8, 1, 12, IRON_D, IRON_M, IRON_L)               # the sash, half down
    stripes(0, 12, 1, 12, 1)
    R(8, 8, 15, 8, CER_L)                                  # lamp under the hood
    R(8, 18, 11, 19, IRON_D)                               # burner
    R(9, 15, 10, 17, IRON_M)
    P(9, 14, F_MID)
    grime(0, 0, 27, 35, 20, (RUST, RUST_D), on=IRON_RAMP)


def gas_rack():
    """Three bottles chained in a rack - fuel, oxygen, inert. Shoot a valve off and that
    bottle leaves the rack; the others are still chained to it."""
    box(0, 26, 25, 27, IRON_D, IRON, IRON_M)               # base
    R(0, 6, 1, 25, IRON_M)                                 # posts
    R(24, 6, 25, 25, IRON_D)
    for x, ramp in ((4, OLIVE_RAMP), (11, RED_RAMP), (18, IRON_RAMP)):
        cylinder(x, 2, 25, ramp)
    R(0, 9, 25, 9, IRON_M)                                 # restraint bar
    for x in range(26):                                    # and the chain
        P(x, 15, IRON_L if x % 2 else IRON_D)
    grime(0, 2, 25, 27, 20, (RUST, RUST_D), on=IRON_RAMP + OLIVE_RAMP + RED_RAMP)


def gas_cylinder():
    """One loose bottle with its tulip cap on. Knock the cap and the valve off and it is
    a rocket with no steering."""
    box(1, 0, 5, 3, IRON_D, IRON_M, IRON_L)                # cap
    hole(3, 1)
    for y in range(4, 21):
        for i in range(5):
            if y == 4 and i in (0, 4):
                continue
            dshade(1 + i, y, 0.95 - 0.22 * i, RED_RAMP)
    R(1, 6, 5, 6, CER_L)
    R(0, 21, 6, 21, IRON_D)                                # foot ring
    grime(1, 4, 5, 20, 8, (RUST_D, RUST), on=RED_RAMP)


def vacuum_bell():
    """A steel vacuum bell on a thick table, porthole in the dome, pump underneath. Sealed
    shut, it is a heavy lump; pumped down and cracked open, the room rushes in."""
    R(3, 19, 4, 23, IRON_D)                                # legs
    R(17, 19, 18, 23, IRON_D)
    box(7, 19, 14, 22, OLIVE_D, OLIVE, OLIVE_L)            # pump
    box(0, 17, 21, 18, IRON_D, IRON_M, IRON_L)             # table
    for y in range(3, 17):                                 # dome
        for x in range(3, 19):
            if ((x - 10.5) / 7.6) ** 2 + ((y - 16.5) / 13.6) ** 2 <= 1:
                dshade(x, y, 0.95 - 0.06 * (x - 3) - 0.02 * y, POLISH)
    R(2, 16, 19, 16, IRON_M)                               # flange
    R(10, 1, 11, 2, IRON_M)                                # lifting eye
    DC(10.5, 10, 2.4, SLATE_D)                             # porthole
    RG(10.5, 10, 2.4, IRON_L)
    P(9, 9, CER_L)
    R(20, 13, 20, 15, IRON_M)                              # gauge on its stem
    box(19, 10, 21, 12, IRON_D, CER_L, CER_L)
    P(20, 11, INK)


def pipe_manifold():
    """A gas header on two legs with three valved drops. Each valve wheel is a trigger;
    each drop is a jet when opened, and the header is one long fuse when it leaks."""
    R(1, 6, 2, 17, IRON_D)                                 # legs
    R(29, 6, 30, 17, IRON_D)
    R(0, 17, 3, 17, IRON_D)
    R(28, 17, 31, 17, IRON_D)
    log_h(0, 3, 31, 5, IRON_RAMP, IRON_D, ends=False)      # header
    for x in (0, 10, 21, 31):                              # flanges
        R(x, 2, x, 6, IRON_L if x < 20 else IRON_M)
    stripes(12, 3, 16, 5, 1)
    for x in (5, 15, 26):                                  # drops
        R(x, 6, x, 14, IRON_M)
        R(x + 1, 6, x + 1, 14, IRON_D)
        box(x - 1, 8, x + 2, 10, IRON_D, IRON, IRON_M)     # valve body
        R(x - 2, 7, x + 3, 7, PAINT_RL)                    # its wheel
        R(x - 1, 15, x + 2, 15, IRON_L)                    # outlet flange
    R(20, 1, 20, 2, IRON_M)                                # gauge
    R(19, 0, 21, 0, CER_L)
    grime(0, 2, 31, 17, 16, (RUST, RUST_D), on=IRON_RAMP)


# ═══════════════════════════════════════════════════════════════════════════
#  BENCH AND INSTRUMENTS
# ═══════════════════════════════════════════════════════════════════════════
def workbench():
    """A timber bench with a drawer, a shelf and a vice. A floor at waist height, cover
    to crouch behind, and fuel."""
    for x0, x1 in ((0, 9), (10, 19), (20, 29)):            # top
        box(x0, 3, x1, 5, TIM_D, TIM_M, TIM_L)
    log_v(1, 6, 2, 15)                                     # legs
    log_v(27, 6, 28, 15)
    box(1, 11, 28, 12, TIM_D, TIM, TIM_M)                  # shelf
    box(8, 6, 20, 8, TIM_D, TIM, TIM_M)                    # drawer
    P(14, 7, IRON_L)
    box(23, 0, 27, 2, IRON_D, IRON, IRON_M)                # vice
    R(28, 1, 29, 1, IRON_L)
    P(29, 0, IRON_L)
    P(25, 1, IRON_D)


def assay_balance():
    """The assay balance in its case: slate base, timber frame, a beam on a copper pillar
    and a pan on each end. Put the weight on the pan and the beam goes over."""
    box(0, 13, 17, 15, SLATE_D, SLATE, SLATE_L)            # base
    box(0, 0, 17, 1, TIM_D, TIM, TIM_M)                    # case frame
    R(0, 2, 0, 12, TIM_M)
    R(17, 2, 17, 12, TIM_D)
    R(8, 5, 8, 12, COP_L)                                  # pillar
    R(9, 5, 9, 12, COP)
    R(8, 3, 9, 3, COP_XL)                                  # knife edge
    R(3, 4, 14, 4, COP_L)                                  # beam
    R(3, 5, 3, 8, IRON_M)                                  # hangers
    R(14, 5, 14, 8, IRON_M)
    R(1, 9, 5, 9, COP)                                     # pans
    R(12, 9, 16, 9, COP)
    P(2, 8, IRON_L)                                        # a weight on one
    P(1, 8, COP_D)
    P(5, 8, COP_D)
    P(12, 8, COP_D)
    P(16, 8, COP_D)


def instrument_rack():
    """A tall instrument cabinet on castors: meters, a row of lamps, knobs, a scope. Heavy,
    top-heavy, and it rolls."""
    box(0, 0, 15, 28, IRON_D, IRON, IRON_M)
    R(1, 9, 14, 9, IRON_D)
    R(1, 18, 14, 18, IRON_D)
    dial(4.5, 4.5, 2.3)
    dial(11, 4.5, 2.3, needle=(-1, -1))
    for x, c in ((3, LAMP_G), (6, LAMP_A), (9, LAMP_R), (12, IRON_D)):
        P(x, 12, c)
    for x in (3, 7, 11):                                   # knobs
        box(x, 14, x + 1, 15, IRON_D, IRON_L, IRON_L)
    box(3, 20, 12, 25, SLATE_D, SCOPE, SCOPE)              # scope
    for x in range(4, 12):
        P(x, 22 + int(round(math.sin(x * 1.1) * 1.4)), LAMP_G)
    for x in range(2, 14, 2):                              # vents
        P(x, 27, IRON_D)
    R(1, 29, 14, 29, IRON_D)
    wheel(3, 30.4, 1.5)
    wheel(12, 30.4, 1.5)


def centrifuge():
    """A floor centrifuge: enamelled housing, hinged lid, a small control panel. The rotor
    inside is a kinematic body at speed - open the lid while it runs and it leaves."""
    box(0, 16, 19, 17, IRON_D, IRON, IRON_M)               # feet
    for y in range(4, 16):                                 # housing
        for x in range(1, 19):
            if (x in (1, 18)) and y in (4, 15):
                continue
            dshade(x, y, 0.95 - 0.04 * (x - 1) - 0.02 * y, CER_RAMP)
    box(3, 1, 16, 3, IRON_D, IRON_M, IRON_L)               # lid
    stripes(3, 3, 16, 3, 1)
    P(17, 3, IRON_D)                                       # hinge
    P(2, 3, IRON_L)                                        # latch
    box(4, 8, 10, 12, SLATE_D, SLATE, SLATE_L)             # panel
    P(6, 10, CER_L)
    P(9, 9, LAMP_G)
    R(13, 9, 16, 9, CER_D)                                 # vents
    R(13, 11, 16, 11, CER_D)


def core_rack():
    """The core library: a timber rack of drill cores, three to a shelf. Labelled, dated,
    and just as happy to be thrown."""
    log_v(0, 0, 1, 21)                                     # posts
    log_v(26, 0, 27, 21)
    box(0, 0, 27, 1, TIM_D, TIM, TIM_M)
    rock_ramps = (ROCK_RAMP, (DIRT_D, DIRT, DIRT_L), (STONE_D, STONE, STONE_L))
    for s, shelf in enumerate((6, 13, 20)):
        box(0, shelf, 27, shelf + 1, TIM_D, TIM, TIM_M)
        for k, x in enumerate((3, 11, 19)):
            if s == 1 and k == 1:
                continue                                   # one out on loan
            ramp = rock_ramps[(s + k) % 3]
            for y in range(shelf - 3, shelf):
                for i in range(6):
                    if i == 5 and y != shelf - 2:
                        continue                           # rounded end
                    dshade(x + i, y, 0.9 - 0.3 * (y - shelf + 3), ramp)
            P(x, shelf - 2, CER_L)                         # the label


def lab_trolley():
    """A two-tier steel trolley with a lipped top tray, a push handle and castors. The
    tray is a container - the lab's answer to the ore tub."""
    box(1, 5, 18, 6, IRON_D, IRON_M, IRON_L)               # tray
    R(1, 3, 2, 4, IRON_M)                                  # lips
    R(17, 3, 18, 4, IRON_D)
    R(19, 1, 19, 6, IRON_M)                                # handle
    R(19, 0, 21, 0, TIM_L)
    R(2, 7, 2, 14, IRON)                                   # legs
    R(17, 7, 17, 14, IRON_D)
    box(2, 11, 17, 12, IRON_D, IRON, IRON_M)               # lower shelf
    wheel(3, 16, 1.6)
    wheel(16, 16, 1.6)


# ═══════════════════════════════════════════════════════════════════════════
#  MAGNETS
# ═══════════════════════════════════════════════════════════════════════════
def lift_magnet():
    """A lifting magnet on its chains: the flat drum with ribs round it, pole face below,
    cable off the top. Switched on it picks up iron from below - including you."""
    for y in range(0, 8):                                  # chain
        P(10, y, IRON_L if y % 2 else IRON_D)
        P(11, y, IRON_D if y % 2 else IRON_M)
    LN(10, 8, 3, 12, IRON_M)                               # slings
    LN(11, 8, 18, 12, IRON)
    R(3, 12, 18, 12, IRON_M)
    box(1, 13, 20, 19, IRON_D, IRON, IRON_M)               # body
    stripes(1, 15, 20, 16, 2)
    for x in (4, 8, 13, 17):                               # ribs
        R(x, 13, x, 14, IRON_D)
        R(x, 17, x, 18, IRON_D)
    R(2, 20, 19, 20, IRON_M)                               # pole face
    R(8, 20, 13, 20, IRON_L)
    for x, y in ((19, 11), (20, 10), (20, 9), (21, 8), (21, 7)):
        P(x, y, CABLE)                                     # power cable
    grime(1, 12, 20, 20, 14, (RUST, RUST_D), on=IRON_RAMP)


def magnet_yoke():
    """A test electromagnet: an iron C with a copper coil on each arm and an air gap
    between the poles. The gap is a pocket open to the room; iron that comes near it
    ends up in it."""
    box(0, 23, 23, 25, IRON_D, IRON, IRON_M)               # plinth
    for y in range(2, 23):                                 # the C
        for x in range(0, 22):
            back = x <= 5
            arm = y <= 6 or y >= 17
            pole = 16 <= x and (7 <= y <= 9 or 14 <= y <= 16)
            if back or arm or pole:
                dshade(x, y, 0.9 - 0.03 * x - 0.015 * y, IRON_RAMP)
    for y0, y1 in ((1, 8), (15, 22)):                      # coils
        for y in range(y0, y1 + 1):
            for x in range(7, 14):
                dshade(x, y, 0.95 - 0.07 * (x - 7) - (0.25 if y % 2 else 0), COP_RAMP)
    stripes(20, 7, 21, 9, 1)                               # pole tips
    stripes(20, 14, 21, 16, 1)
    grime(0, 2, 23, 25, 16, (RUST, RUST_D), on=IRON_RAMP)


def hand_magnet():
    """A horseshoe magnet, red with bright pole tips. Carried, it drags loose iron to the
    player; thrown, it sticks to whatever steel it hits."""
    tpl(0, 0, [
        ".LLLLLLLWW",
        "LRRRRRRRWW",
        "RRD.......",
        "RD........",
        "RRD.......",
        "LRRRRRRRWW",
        ".DDDDDDDWW",
    ], {'L': PAINT_RL, 'R': PAINT_R, 'D': RUST_D, 'W': IRON_L})


# ═══════════════════════════════════════════════════════════════════════════
#  CONTAINMENT
# ═══════════════════════════════════════════════════════════════════════════
def blast_shield():
    """A wheeled blast shield: a thick plate braced from behind, with an armoured glass
    block let into it rather than a slot - a slot through the plate would cut it in two.
    Cover you can push, and the only thing in the test gallery that stops a fragment."""
    for y in range(0, 20):                                 # plate
        for x in range(10, 15):
            dshade(x, y, 0.9 - 0.18 * (x - 10), IRON_RAMP)
    stripes(10, 0, 14, 2, 1)
    R(11, 6, 13, 7, SLATE_D)                               # the glass block
    P(11, 6, CER)
    for y in (4, 12, 17):                                  # bolts
        P(11, y, IRON_L)
        P(13, y, IRON_L)
    LN(14, 5, 19, 19, IRON_D)                              # braces
    LN(15, 5, 20, 19, IRON)
    R(21, 8, 21, 18, IRON_M)                               # push handle
    R(20, 8, 21, 8, TIM_L)
    box(4, 19, 21, 21, IRON_D, IRON, IRON_M)               # carriage
    wheel(7, 22.3, 1.7)
    wheel(18, 22.3, 1.7)
    grime(4, 0, 21, 21, 18, (RUST, RUST_D), on=IRON_RAMP)


def blast_door():
    """The test gallery's door as an object: the drive housing and the striped slab that
    hangs from it into the opening. Closed, the slab is in the gap; open, it is up in the
    housing and gone - there is no panel to draw."""
    box(0, 0, 15, 5, IRON_D, IRON, IRON_M)                 # housing
    for x in (3, 7, 11):
        P(x, 2, IRON_L)
    R(7, 6, 7, 7, IRON_L)                                  # chain
    R(8, 6, 8, 7, IRON_D)
    box(2, 8, 13, 40, IRON_D, IRON_M, IRON_L)              # slab
    stripes(3, 9, 12, 39, 3)
    for y in range(16, 40, 8):                             # ribs
        R(2, y, 13, y, IRON_D)
    R(2, 41, 13, 41, IRON_D)                               # shoe


def faraday_cage():
    """A Faraday cage on porcelain feet: arched roof, a meshed wall, a test sphere on an
    insulator inside, strapped to earth. Arcs stop at the mesh - stand inside and the
    transformer cannot reach you; stand on the mesh and it can."""
    R(1, 28, 3, 29, CER)                                   # insulator feet
    R(24, 28, 26, 29, CER)
    box(0, 26, 27, 27, IRON_D, IRON, IRON_M)               # floor
    R(0, 3, 1, 25, IRON_M)                                 # posts
    R(26, 3, 27, 25, IRON_D)
    R(0, 3, 27, 4, IRON_M)                                 # eaves
    for x in range(28):                                    # arched roof and its ribs
        y = int(3 - 3 * math.sin(math.pi * x / 27))
        P(x, y, IRON_L)
        if x % 3 == 0:
            R(x, y, x, 2, IRON_D)
    R(23, 5, 23, 25, IRON_M)                               # meshed wall
    for y in range(5, 26, 3):
        R(23, y, 25, y, IRON_L)
    R(12, 18, 14, 25, CER)                                 # insulator
    R(14, 18, 14, 25, CER_D)
    sdisc(13, 15, 3, POLISH)                               # test sphere
    R(2, 25, 5, 25, COP_L)                                 # earth strap


def specimen_safe():
    """A specimen safe: painted steel, dial and handle, brass plate. The heaviest small
    thing in the lab, and it is locked."""
    R(1, 17, 3, 17, IRON_D)                                # feet
    R(12, 17, 14, 17, IRON_D)
    box(0, 0, 15, 16, SAFE_D, SAFE, SAFE_L)
    for y in range(2, 15):                                 # door
        R(2, y, 2, y, SAFE_D)
        R(13, y, 13, y, SAFE_D)
    R(2, 2, 13, 2, SAFE_D)
    R(2, 14, 13, 14, SAFE_D)
    R(1, 4, 1, 5, IRON_L)                                  # hinges
    R(1, 11, 1, 12, IRON_L)
    DC(6, 7, 2.2, IRON_L)                                  # dial
    RG(6, 7, 2.2, IRON_D)
    P(6, 7, IRON_D)
    P(6, 5, GOLD)
    R(9, 7, 11, 7, IRON_L)                                 # handle
    R(10, 6, 10, 9, IRON_L)
    R(5, 12, 10, 12, GOLD)                                 # brass plate
    grime(0, 0, 15, 16, 14, (SAFE_D, RUST_D), on=(SAFE, SAFE_L))


# ═══════════════════════════════════════════════════════════════════════════
#  CARRIED
# ═══════════════════════════════════════════════════════════════════════════
def battery_cell():
    """One accumulator cell with a rope handle. Carry it to a dead machine, or drop it
    into an arc and watch it go."""
    R(3, 0, 4, 0, SACK_L)                                  # handle
    P(3, 1, SACK)
    P(4, 1, SACK)
    P(1, 1, COP_L)                                         # terminals
    P(6, 1, IRON_L)
    R(0, 2, 7, 2, IRON_D)                                  # lid
    box(0, 3, 7, 10, SLATE_D, SLATE, SLATE_L)
    R(1, 6, 6, 6, STRIPE)
    P(1, 4, PAINT_RL)
    P(6, 4, CER)


def crucible():
    """A fireclay crucible, still hot. A small container: it holds a charge of ore or
    powder, and it lights what it is set down on."""
    for y in range(0, 4):                                  # walls, flared at the top
        R(0, y, 1, y, CER_L if y < 2 else CER)
        R(6, y, 7, y, CER_D)
    for y in range(4, 7):
        R(1, y, 2, y, CER)
        R(5, y, 6, y, CER_D)
    R(2, 6, 5, 7, CER_D)                                   # floor
    P(2, 4, F_COOL)                                        # heat in the walls
    P(5, 5, F_COOL)
    P(3, 6, F_MID)


def sample_canister():
    """A sealed sample canister with a carry ring and a hazard band. What is in it is the
    question the lab exists to answer - do not open it near the furnace."""
    R(2, 0, 4, 0, IRON_M)                                  # ring
    P(2, 1, IRON_M)
    P(4, 1, IRON_D)
    box(0, 2, 6, 3, IRON_D, IRON_M, IRON_L)                # lid
    P(2, 3, IRON_D)
    P(4, 3, IRON_D)
    log_v(1, 4, 5, 9, IRON_RAMP, IRON_D)                   # body
    R(1, 6, 5, 7, STRIPE)
    P(3, 6, INK)
    P(3, 7, INK)
    R(0, 10, 6, 10, IRON_D)                                # base


# ═══════════════════════════════════════════════════════════════════════════
LAB_PROPS = [
    ("POWER AND FIELDS", [
        ("Dynamo", "DYNAMO", dynamo, (28, 18)),
        ("BatteryBank", "BATTERY BANK", battery_bank, (30, 20)),
        ("Transformer", "TRANSFORMER", transformer, (20, 26)),
        ("Switchboard", "SWITCHBOARD", switchboard, (26, 30)),
        ("TeslaCoil", "TESLA COIL", tesla_coil, (18, 42)),
        ("VanDeGraaff", "VAN DE GRAAFF", van_de_graaff, (14, 38)),
    ]),
    ("HEAT, GAS AND VACUUM", [
        ("MuffleFurnace", "MUFFLE FURNACE", muffle_furnace, (26, 28)),
        ("FumeHood", "FUME HOOD", fume_hood, (28, 36)),
        ("GasRack", "GAS RACK", gas_rack, (26, 28)),
        ("GasCylinder", "GAS BOTTLE", gas_cylinder, (7, 22)),
        ("VacuumBell", "VACUUM BELL", vacuum_bell, (22, 24)),
        ("PipeManifold", "GAS MANIFOLD", pipe_manifold, (32, 18)),
    ]),
    ("BENCH AND INSTRUMENTS", [
        ("Workbench", "WORKBENCH", workbench, (30, 16)),
        ("AssayBalance", "ASSAY BALANCE", assay_balance, (18, 16)),
        ("InstrumentRack", "INSTRUMENTS", instrument_rack, (16, 32)),
        ("Centrifuge", "CENTRIFUGE", centrifuge, (20, 18)),
        ("CoreRack", "CORE RACK", core_rack, (28, 22)),
        ("LabTrolley", "TROLLEY", lab_trolley, (22, 18)),
    ]),
    ("MAGNETS", [
        ("LiftMagnet", "LIFTING MAGNET", lift_magnet, (22, 21)),
        ("MagnetYoke", "TEST MAGNET", magnet_yoke, (24, 26)),
        ("HandMagnet", "HAND MAGNET", hand_magnet, (10, 7)),
    ]),
    ("CONTAINMENT", [
        ("BlastShield", "BLAST SHIELD", blast_shield, (22, 24)),
        ("BlastDoor", "BLAST DOOR", blast_door, (16, 42)),
        ("FaradayCage", "FARADAY CAGE", faraday_cage, (28, 30)),
        ("SpecimenSafe", "SPECIMEN SAFE", specimen_safe, (16, 18)),
    ]),
    ("CARRIED", [
        ("BatteryCell", "BATTERY CELL", battery_cell, (8, 11)),
        ("Crucible", "CRUCIBLE", crucible, (8, 8)),
        ("SampleCanister", "CANISTER", sample_canister, (7, 11)),
    ]),
]


def build():
    return mp.build_sheet(LAB_PROPS, OUT_DIR, os.path.join("Icons", "IconSheet_Lab.png"),
                          "PHYSFUN - LAB OBJECTS", 9100)


if __name__ == "__main__":
    build()
