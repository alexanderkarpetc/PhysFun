"""Room props, part 4: what one room needs and no other does, added as each room is
assembled from its sheet (`export_rooms.py`, one room at a time). A group per room.

Built by `roomprops.py`; read its docstring for what the entries mean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mineprops import *  # noqa: F403,E402
from propexport import DEFAULT, WOOD, METAL  # noqa: E402,F401
from roomprops_hung import eye, ball  # noqa: E402
from roomprops_machines import COP_RAMP, POLISH  # noqa: E402  # noqa: E402

TITLE = "ROOM BY ROOM"
SEED = 9700


# ═══════════════════════════════════════════════════════════════════════════
#  S03 THE COIL DOME
# ═══════════════════════════════════════════════════════════════════════════
def tesla_coil():
    """The coil on the dome's plinth, at the sheet's size: an iron foot, the flat primary
    edge-on, a tall copper secondary and a polished toroid. Bolted down (static) and an
    ArcEmitter - every couple of seconds a bolt from the toroid to the nearest metal."""
    for y in range(1, 13):                                 # toroid, side-on
        for x in range(1, 36):
            dx, dy = (x - 18) / 17.2, (y - 6.5) / 5.8
            if dx * dx + dy * dy <= 1:
                dshade(x, y, 0.95 - 0.5 * (y - 1) / 11 - 0.15 * abs(dx), POLISH)
    R(4, 3, 9, 3, IRON_XL)                                 # the shine along its top
    R(16, 13, 20, 15, IRON_M)                              # stem
    for y in range(16, 56):                                # the secondary, wound copper
        for x in range(13, 24):
            dshade(x, y, 0.95 - 0.07 * (x - 13) - (0.25 if y % 2 else 0), COP_RAMP)
    R(12, 16, 24, 16, IRON_M)                              # former caps
    R(12, 55, 24, 55, IRON_M)
    R(6, 56, 30, 56, COP_RAMP[2])                          # primary, edge-on
    R(7, 57, 29, 57, COP_RAMP[0])
    box(8, 58, 28, 64, IRON_D, IRON, IRON_M)               # cabinet foot
    for x in (11, 15, 21, 25):
        R(x, 60, x, 62, IRON_D)
    grime(8, 56, 28, 64, 14, (RUST, RUST_D), on=IRON_RAMP)


def hung_grate():
    """A steel grate walkway as it hangs off the dome's walls: a flat bar with the slots
    of the grating showing in its face, a lug near each end for the ropes. Short - about
    three men long - so it is a perch to stand on, not a floor across the room."""
    for cx in GRATE_LUGS:
        eye(cx, 0, 2.0)
    for x in range(GRATE_W):
        P(x, 4, IRON_L)
        P(x, 5, IRON_M if x % 4 else IRON_D)
        P(x, 6, IRON_D)
    for x in range(2, GRATE_W - 1, 4):
        P(x, 5, INK)
    grime(0, 4, GRATE_W - 1, 6, 24, (RUST, RUST_D), on=IRON_RAMP)


GRATE_W = 72
GRATE_LUGS = (8, 63)


def floor_plate():
    """The steel plate down the west half of the dome's floor: what makes that half a
    conductor. Loose - a hard enough blast lifts it."""
    for x in range(131):
        P(x, 0, IRON_L)
        P(x, 1, IRON_M)
        P(x, 2, IRON_D)
    for x in range(6, 130, 21):                            # plate seams and bolt heads
        P(x, 1, IRON_D)
        P(x + 2, 1, IRON_XL)
    grime(0, 0, 130, 2, 50, (RUST, RUST_D, RUST_L), on=IRON_RAMP)


def dynamo():
    """The dynamo that feeds the coil: an iron case, the copper armature end showing, the
    cable gland. Bolted to the floor, and metal - the nearest thing to the coil's foot."""
    box(0, 2, 24, 15, IRON_D, IRON, IRON_M)
    R(2, 0, 6, 1, IRON_M)                                  # lifting lug
    R(18, 0, 22, 1, IRON_M)
    for y in range(4, 15):
        for x in range(7, 18):
            d = math.hypot(x - 12, y - 9)
            if d <= 5:
                dshade(x, y, 0.9 - 0.12 * d, COP_RAMP)
    for y in range(7, 12):
        for x in range(10, 15):
            if math.hypot(x - 12, y - 9) <= 2:
                P(x, y, IRON_D)
    P(12, 9, IRON_L)
    for y in (5, 9, 13):                                   # cooling fins
        R(1, y, 4, y, IRON_D)
        R(20, y, 23, y, IRON_D)
    grime(0, 2, 24, 15, 16, (RUST, RUST_D), on=IRON_RAMP)



# ═══════════════════════════════════════════════════════════════════════════
#  S05 THE SAWPIT
# ═══════════════════════════════════════════════════════════════════════════
SAW_CX, SAW_HUB = 23, 68          # the carriage's centre column and its arbour row
SAW_R = 16                        # blade radius to the gullets, teeth 2 more


def saw_carriage():
    """The swing saw's carriage, everything but the blade: two wheels that ride the rail's
    bottom flange, the carriage box with its motor, the two flat bars down to the arbour,
    and the striped guard over the top of where the blade turns. Kinematic and a
    RailShuttle: it runs the rail end to end, and drops when there is no rail over it."""
    cx, hub = SAW_CX, SAW_HUB
    for wx in (cx - 7, cx + 7):                            # wheels, axle eyes open
        ball(wx + 0.5, 3.5, 3.2, IRON_RAMP, 0.45)
        P(wx, 3, IRON_L)
    for y in range(7, 18):                                 # carriage box
        for x in range(cx - 12, cx + 13):
            dshade(x, y, 0.75 - 0.4 * (x - cx + 12) / 24 - 0.02 * (y - 7), IRON_RAMP)
    R(cx - 12, 7, cx + 12, 7, IRON_L)
    R(cx - 12, 17, cx + 12, 17, IRON_D)
    for y in range(9, 16):                                 # the motor, copper end on
        for x in range(cx + 2, cx + 11):
            d = math.hypot(x - cx - 6, y - 12)
            if d <= 3.6:
                dshade(x, y, 0.95 - 0.2 * d, COP_RAMP)
    P(cx + 6, 12, IRON_D)
    for bx in (cx - 5, cx + 3):                            # the flat bars to the arbour
        for y in range(18, hub - 1):
            P(bx, y, IRON_L)
            P(bx + 1, y, IRON_M)
            P(bx + 2, y, IRON)
    for y in range(26, hub - 4, 14):                       # cross braces between them
        R(cx - 3, y, cx + 2, y, IRON_D)
    for y in range(18, hub - 1):                           # the belt, motor to arbour
        x = cx + 6 - int(4 * (y - 18) / (hub - 18))
        if AT(x, y) == KEY:
            P(x, y, (60, 52, 46))
    for y in range(hub - 3, hub + 4):                      # arbour boss
        for x in range(cx - 3, cx + 4):
            if math.hypot(x - cx, y - hub) <= 3.3:
                dshade(x, y, 0.8 - 0.1 * (x - cx + y - hub), IRON_RAMP)
    hole(cx, hub)
    for y in range(hub - SAW_R - 7, hub + 1):              # the guard over the top half
        for x in range(cx - SAW_R - 7, cx + SAW_R + 8):
            d = math.hypot(x - cx, y - hub)
            if SAW_R + 4 <= d <= SAW_R + 6 and y <= hub - 1:
                a = math.atan2(hub - y, x - cx)
                band = int(a / (math.pi / 8)) % 2
                P(x, y, STRIPE if band == 0 and d < SAW_R + 5.5 else IRON_D)
    grime(cx - 12, 7, cx + 12, hub, 30, (RUST, RUST_D), on=IRON_RAMP)


def saw_blade():
    """The blade: a steel disc, teeth proud of the rim, a polished ring, the arbour bore
    open in the middle. Lit from its own centre so it reads the same at any angle - it
    never stops turning."""
    c = 19
    for y in range(39):
        for x in range(39):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            if d <= SAW_R:
                ring_ = 0.75 if SAW_R - 3 <= d else 0.95 if SAW_R - 6 <= d <= SAW_R - 4 else 0.6
                dshade(x, y, ring_ - 0.25 * d / SAW_R, POLISH)
            elif d <= SAW_R + 2.2:
                a = math.atan2(dy, dx) % (2 * math.pi)
                tooth = (a / (2 * math.pi) * 24) % 1.0
                if tooth < 0.45 and d <= SAW_R + 0.8 + 1.6 * (1 - tooth / 0.45):
                    P(x, y, IRON_XL if tooth < 0.2 else IRON_L)
    for k in range(3):                                     # expansion slots, so it reads turning
        a = k * 2 * math.pi / 3 + 0.4
        for t in range(5, 11):
            P(int(round(c + math.cos(a) * t)), int(round(c + math.sin(a) * t)), IRON_D)
    for y in range(c - 3, c + 4):
        for x in range(c - 3, c + 4):
            d = math.hypot(x - c, y - c)
            if d <= 3.2:
                P(x, y, IRON_D if d > 1.6 else KEY)
    for y in range(c - 1, c + 2):
        for x in range(c - 1, c + 2):
            if math.hypot(x - c, y - c) <= 1.2:
                hole(x, y)


def plank_stack():
    """Sawn planks stacked flat with sticks between, the east end's stock. One body - the
    saw goes through it a layer at a time."""
    w, layers = 30, 7
    base = 21
    for i in range(layers):
        yy = base - 1 - i * 3
        x0, x1 = i % 2, w - (i % 3)
        for y in range(yy - 2, yy + 1):
            for x in range(x0, x1 + 1):
                dshade(x, y, 0.85 - 0.3 * (y - yy + 2) / 2 - 0.1 * (x / w), TIM_RAMP)
        R(x0, yy, x1, yy, TIM_D)
        P(x1, yy - 1, TIM_M)
    R(3, base - layers * 3, 4, base - 1, TIM_D)            # the sticks between the layers
    R(w - 6, base - layers * 3, w - 5, base - 1, TIM_D)


# ═══════════════════════════════════════════════════════════════════════════
#  S07 THE ROPE BRIDGE
# ═══════════════════════════════════════════════════════════════════════════
def bridge_plank():
    """One plank of a rope bridge, edge-on: the segment BridgeBuilder2D strings together.
    Timber, so a bridge burns plank by plank."""
    for x in range(7):
        P(x, 0, TIM_L if x % 3 else TIM_M)
        P(x, 1, TIM)
        P(x, 2, TIM_D)
    P(0, 1, TIM_D)
    P(6, 1, TIM_M)

GROUPS = [
    ("S03 THE COIL DOME", [
        ("TeslaCoil", "TESLA COIL", tesla_coil, (37, 65), METAL, "arc"),
        ("HungGrate", "HUNG GRATE", hung_grate, (GRATE_W, 7), METAL, None),
        ("FloorPlate", "FLOOR PLATE", floor_plate, (131, 3), METAL, None),
        ("Dynamo", "DYNAMO", dynamo, (25, 16), METAL, None),
    ]),
    ("S05 THE SAWPIT", [
        ("SawCarriage", "SAW CARRIAGE", saw_carriage, (47, SAW_HUB + 5), METAL, "shuttle"),
        ("SawBlade", "SAW BLADE", saw_blade, (39, 39), METAL, "saw"),
        ("PlankStack", "PLANK STACK", plank_stack, (32, 22), WOOD, None),
    ]),
    ("S07 THE ROPE BRIDGE", [
        ("BridgePlank", "BRIDGE PLANK", bridge_plank, (7, 3), WOOD, None),
    ]),
]

ANCHORS = {
    "TeslaCoil": {"Tip": (18, 6.5)},
    "HungGrate": {"EyeL": (GRATE_LUGS[0] + 0.5, 2), "EyeR": (GRATE_LUGS[1] + 0.5, 2)},
    "SawCarriage": {"Arbour": (SAW_CX + 0.5, SAW_HUB + 0.5)},
    "SawBlade": {"Hub": (19.5, 19.5)},
}

KINEMATIC = {"SawCarriage"}
TRIGGER = {"SawBlade"}

STATIC = {"TeslaCoil", "Dynamo"}
