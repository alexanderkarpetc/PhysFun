"""S06 THE CRIB, assembled.

The slab and the crib are terrain (export_rooms' extras_crib): the slab is rock_alt parted
from the roof, standing on the timber crib alone, so the support pass drops it on the camp
the moment the crib burns or is shot out.

The crib there is one solid block of timber; here it is cut into courses the way the sheet
draws it - a beam across, then two end blocks with the hollow between, and so on up - so the
hollows are real openings you can shoot or throw fire through, and it reads as a crib, not
a wall. The top rows, where the wedges are driven under the slab, stay solid.
"""

ENTRY = "L2"            # the floor, west of the camp: under the slab, as the sheet means


def hooks(add, mod):
    return {}


def furnish(add, mod, ox, oy):
    fy = oy + mod.FLOOR
    for bx in (100, 300):                                   # bedrolls, drawn inline on the sheet
        add("Bedroll", ox + bx + 7, fy - 2.5, scale=14 / 17.0)


COURSE = 5              # rows per course
END = 11                # width of an end block


def extras(g, mod):
    x0, x1 = mod.CRIB_X - 2, mod.CRIB_X + mod.CRIB_W + 2
    base = int(mod.mound_top(mod.CRIB_X + mod.CRIB_W // 2))   # the courses count up from here
    for x in range(x0, x1 + 1):
        if x - x0 < END or x1 - x < END:
            continue                                         # end blocks run the full height
        top = int(mod.slab_bottom(x)) + 1
        for y in range(top + 5, int(mod.mound_top(x))):
            if ((base - 1 - y) // COURSE) % 2 == 0:
                g.set(x, y, None)                            # the hollow behind the end blocks
