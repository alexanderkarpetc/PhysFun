"""S08 THE GRINDER WELL, assembled.

The floor is a funnel lined with steel, and in its throat two Hazards/Grinder wheels turn
in (the west clockwise, the east anticlockwise) with a 4 px nip between them, set to eat:
what slides down the steel is dragged into the nip and carved away at the teeth until it
is small enough to drop through, into the pit under the wheels. Living things are hurt
there instead, until they are corpses, and then eaten the same way.

Changed from the sheet after play: the belts are gone (they read as nothing in the room),
the wheels are smaller with a nip (meshed, as drawn, they were a shelf things lay on; with
a wide one everything fell through whole), the funnel and the wheel chamber are lined in
steel, the rock shelves over the slopes are gone, and the bin is a pit.
"""
PPU = 20.0
ORIGIN = (0, 0)

GRINDER = "Hazards/Grinder"
G_GRINDER = 6301000000000000006
GEAR_R = 20.0           # the Grinder's sprite: 2 units across, so r 20 px to the teeth
WHEEL_R = 12            # px, teeth included
NIP = 4                 # px between the wheels' teeth: nothing passes whole
CHAMBER = (171, 352, 229, 392)     # the wheels' chamber: no gap down the side of a wheel
PIT = (184, 392, 216, 428)         # under the nip, down past the bin
LINING = 3              # px of steel under the funnel's surface


def hooks(add, mod):
    def belt(x0, x1, top, d):
        pass

    def grinder(cx, cy, r):
        off = WHEEL_R + NIP / 2.0
        for side in (-1, 1):
            # turning in: the west wheel's inner edge goes down (clockwise, negative)
            add.place(GRINDER, cx + side * off + 0.5, cy + 0.5, scale=WHEEL_R / GEAR_R, name="Wheel",
                      mods=[(G_GRINDER, "spin", "-220" if side < 0 else "220"),
                            (G_GRINDER, "eats", "1")])

    def lip_plates(bx, by):
        pass

    def rock_blob(*a, **k):
        pass                                     # no shelves or lumps over the chute: they only snag

    return {"belt": belt, "grinder": grinder, "lip_plates": lip_plates, "rock_blob": rock_blob}


def furnish(add, mod, ox, oy):
    """The skip over the throat is drawn inline on the sheet."""
    cx = ox + mod.CX + 20
    add("HoistBucket", cx + 0.5, oy + 214 + 6, rope=(cx, None, oy + 214 - 6))


def extras(g, mod):
    x0, y0, x1, y1 = CHAMBER
    g.rect(x0, y0, x1, y1, None)                            # the wheels' chamber
    px0, py0, px1, py1 = PIT
    g.rect(px0, py0, px1, py1, None)                        # the pit under the nip

    # steel: down both slopes of the funnel - laid on the funnel line itself, the stones and
    # gravel the sheet scatters on the slope cleared off it, so the lining is one clean chute
    for lx in range(20, 381):
        if x0 <= lx <= x1:
            continue
        top = int(mod.funnel(lx)) + 1
        if top > 392 or not g.m.get((lx, top)):
            continue                                        # past the slope's ends: under a ledge
        for y in range(top - 18, top):
            if g.m.get((lx, y)) and g.m.get((lx, y - 1)) is None:
                g.set(lx, y, None)                          # a stone sat on the slope
        for k in range(LINING):
            if g.m.get((lx, top + k)):
                g.set(lx, top + k, "steel")
    for y in range(y0 - 2, y1 + 1):
        for x in list(range(x0 - LINING, x0)) + list(range(x1 + 1, x1 + 1 + LINING)):
            if g.m.get((x, y)):
                g.set(x, y, "steel")
    for x in range(x0 - LINING, x1 + LINING + 1):           # the chamber's floor, either side of the pit
        for k in range(LINING):
            if g.m.get((x, y1 + 1 + k)) and not (px0 <= x <= px1):
                g.set(x, y1 + 1 + k, "steel")
    for y in range(py0, py1 + 1):
        for x in list(range(px0 - LINING, px0)) + list(range(px1 + 1, px1 + 1 + LINING)):
            if g.m.get((x, y)):
                g.set(x, y, "steel")


# Not on the slope: steel all the way down now, and it ends in the wheels. The west ledge
# the belt used to run along.
ENTRY_AT = (60, 150)
