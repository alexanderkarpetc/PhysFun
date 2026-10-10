"""S03 THE COIL DOME, assembled.

Everything metal in the dome has to be a body of its own: a terrain chunk takes the
material most of its cells are, so a steel strip laid on rock would be rock as far as the
arc is concerned. So the coil, the dynamo, both grates and the floor plate are props
(roomprops_rooms), and only the duckboards - wood, which is the point of them - are terrain.

The coil is an ArcEmitter: a bolt every couple of seconds at the nearest thing that
conducts. The grates hang on two ropes each, so an arc into one takes everybody on it.
"""

# The grates are shorter than the sheet's (72 px, not 128): where each one's west end goes,
# from the sheet's, west grate first as the sheet draws them. West: under the sentinel and
# clear of the T1 shaft, so both ropes tie to rock. East: under the crimson mage, its west
# rope clear of the cage that hangs at x 300.
SHIFT = [20, 36]
LUGS = (8, 63)                     # HungGrate's EyeL / EyeR, pixels from its west end
GRATE_W = 72

# Start on the duckboards. L1/R1 are the grates (metal, swinging, next to the coil) and L2
# is the steel plate - the one safe floor in the room is the timber east half.
ENTRY = "R2"


def hooks(add, mod):
    grates = iter(SHIFT)

    def tesla(cx, base):
        # sprite: toroid at the top, cabinet foot's last row on the plinth (base - 1)
        add("TeslaCoil", cx + 0.5, base - 32.5)

    def hung_grate(x0, x1, y, chains, roof):
        # sprite: lugs rows 0-3, the bar rows 4-6 with its top on y
        x0 += next(grates)
        add("HungGrate", x0 + GRATE_W / 2.0, y - 0.5,
            ropes=[(a, x0 + k, roof(x0 + k)) for a, k in (("EyeL", LUGS[0]), ("EyeR", LUGS[1]))])

    return {"tesla": tesla, "hung_grate": hung_grate}


def furnish(add, mod, ox, oy):
    """The dynamo and the floor plate are drawn inline in dome_furnish, not by a helper."""
    fy = oy + mod.DOME_FLOOR
    add("Dynamo", ox + 252 + 12.5, fy - 18 + 8)
    add("FloorPlate", ox + 50 + 65.5, fy - 1.5)


def extras(g, mod):
    f = mod.DOME_FLOOR
    for x in range(244, 372, 7):                             # duckboards, east half
        g.rect(x, f - 2, x + 5, f - 1, "wood")
