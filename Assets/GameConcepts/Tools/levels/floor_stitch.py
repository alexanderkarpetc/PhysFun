"""Small rooms and a floor stitched out of them.

The question this answers is whether a floor reads well when it is put together from
small hand-made rooms the way Enter the Gungeon does it, instead of one room per screen
transition. Two sheets come out of it:

* RoomConcept_SmallRooms.png - three rooms of roughly 400x400 game pixels (about one
  screen across, a screen and a half tall), each with the sockets a generator could
  join it by: two on top, and the rest on the sides, so most pairs of rooms have a pair
  of sockets that face each other.
* RoomConcept_FloorStitch.png - the same three rooms laid into one terrain. Corridors
  are cut between the sockets that were chosen, every socket that was not is simply
  left as rock, and everything else is filled with the same Default rock under its own,
  darker tile, so the eye can tell the rooms from the fill while the physics cannot.

Each room is drawn by one function in local coordinates (0..w, 0..h) plus an origin, so
the two sheets draw exactly the same rooms. A room keeps a shell of its own rock round
its air; the rest of its template box is fill, the same as the space between rooms.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smallroomkit import *  # noqa: F403,E402
from levels.small_01_hopper import ROOM as HOPPER  # noqa: E402
from levels.small_02_drift import ROOM as DRIFT  # noqa: E402
from levels.small_03_dome import ROOM as DOME_ROOM  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
#  Sheet 1: the three rooms on their own, every socket open
# ─────────────────────────────────────────────────────────────────────────────
def build_rooms():
    new_canvas(1600, 800, seed=40417)
    label_scale(3)
    placed = [(HOPPER, 90, 120), (DRIFT, 560, 140), (DOME_ROOM, 1090, 120)]
    lay(placed, None, [])
    for room, ox, oy in placed:
        dashed_box(ox, oy, ox + room["w"] - 1, oy + room["h"] - 1)
    vignette(0.25)
    for letter, (room, ox, oy) in zip("ABC", placed):
        socket_tags(room, ox, oy)
        nx = ox + (170 if "B1" in room["sockets"] else 6)
        btag(nx, 562, "%s  %s  %dX%d" % (letter, room["name"], room["w"], room["h"]), PALE_G)

    btitle_bar("PHYSFUN - SMALL ROOMS:  THREE TO STITCH",
               "~1 X 1.6 SCREENS EACH / GAME SCALE")
    hx, hy = placed[0][1], placed[0][2]
    bcallout(30, 66, "1 ORE ON A TIMBER GATE", hx + 190, hy + 214)
    bcallout(hx + 200, 612, "2 THE PIT", hx + 300, hy + 360)
    dx, dy = placed[1][1], placed[1][2]
    bcallout(dx + 30, 66, "3 CART ON A CHOCK", dx + 62, dy + 112)
    bcallout(dx + 120, 612, "4 TRESTLE OVER THE KEGS", dx + 139, dy + 215)
    cx, cy = placed[2][1], placed[2][2]
    bcallout(cx + 200, 66, "5 COIL ARCS TO METAL", cx + 210, cy + 250)
    bcallout(cx + 160, 612, "6 GRATES ON CHAINS", cx + 360, cy + 226)

    blegend(30, 700, [
        ("BEATS", CYAN),
        ("ONE TOY PER ROOM, ENEMIES ALREADY IN IT", (170, 180, 195)),
        ("SOCKETS: TWO ON TOP, THE REST ON THE SIDES", SOCKET),
    ], 760)
    blegend(830, 700, [
        ("DASHED BOX = THE TEMPLATE", (170, 180, 195)),
        ("LIGHT ROCK = THE ROOM'S OWN, DARK = FILL", (170, 180, 195)),
        ("A SOCKET NOBODY USES IS LEFT AS ROCK", F_MID),
    ], 740)
    return save(out_path("RoomConcept_SmallRooms.png"), scale=2)


# ─────────────────────────────────────────────────────────────────────────────
#  Sheet 2: the three rooms stitched into one terrain
# ─────────────────────────────────────────────────────────────────────────────
def build_floor():
    new_canvas(1500, 1000, seed=51177)
    label_scale(3)
    A, B, C = (HOPPER, 80, 110), (DRIFT, 590, 70), (DOME_ROOM, 760, 545)
    placed = [A, B, C]

    def sp(room_t, sid):
        return socket_point(room_t[0], sid, room_t[1], room_t[2])

    a_l1, a_r1, a_r2 = sp(A, "L1"), sp(A, "R1"), sp(A, "R2")
    b_l1, b_b1, b_r1 = sp(B, "L1"), sp(B, "B1"), sp(B, "R1")
    c_t1, c_l2, c_r1 = sp(C, "T1"), sp(C, "L2"), sp(C, "R1")

    used = ({(A[0]["name"], s) for s in ("L1", "R1", "R2")}
            | {(B[0]["name"], s) for s in ("L1", "B1", "R1")}
            | {(C[0]["name"], s) for s in ("T1", "L2", "R1")})
    hall_y = b_b1[1] + 50
    corridors = [
        # in from the west, onto the bowl's lip
        ([(-20, a_l1[1] - 15), (40, a_l1[1] - 20), (a_l1[0] + 6, a_l1[1] - 15)], 15),
        # A -> B, climbing
        ([(a_r1[0] - 6, a_r1[1] - 15), (510, a_r1[1] - 15), (550, b_l1[1] - 4),
          (b_l1[0] + 6, b_l1[1] - 15)], 15),
        # B -> C: down a shaft, along a heading, down a shaft
        ([(b_b1[0], b_b1[1] - 6), (b_b1[0], hall_y)], 13),
        ([(b_b1[0], hall_y - 2), (c_t1[0], hall_y - 2)], 15),
        ([(c_t1[0], hall_y), (c_t1[0], c_t1[1] + 6)], 13),
        # A -> C the long way: out of the pit, winding down
        ([(a_r2[0] - 6, a_r2[1] - 15), (540, a_r2[1] - 10), (600, 600), (560, 720),
          (640, 850), (700, c_l2[1] - 18), (c_l2[0] + 6, c_l2[1] - 15)], 15),
        # out east, to the rest of the floor
        ([(b_r1[0] - 6, b_r1[1] - 15), (1150, b_r1[1] - 9), (1260, b_r1[1] + 6),
          (1520, b_r1[1] + 2)], 15),
        ([(c_r1[0] - 6, c_r1[1] - 15), (1300, c_r1[1] - 25), (1520, c_r1[1] - 20)], 15),
        # a pocket in the fill that no corridor reaches
        ([(280, 720), (340, 730)], 18),
    ]
    ladders = [(b_b1[0], b_b1[1] - 4, hall_y + 12), (c_t1[0], hall_y + 2, c_t1[1] + 90)]
    air, plugs = lay(placed, used, corridors, ladders)

    # the pocket: something worth digging to
    pf = floor_at(air, 310, 720)
    crate_g(296, pf)
    keg(312, pf)
    corpse(332, pf)

    # whoever is walking in
    hf = floor_at(air, 46, a_l1[1] - 20)
    stand("Hero_Pilgrim", 46, hf)
    binny_half(150, 196)

    vignette(0.25)
    btitle_bar("PHYSFUN - FLOOR CONCEPT:  THREE ROOMS, ONE TERRAIN",
               "STITCH / GAME SCALE")
    bcallout(20, 64, "1 IN FROM THE WEST", 46, hf - 12)
    bcallout(290, 64, "2 A TO B: CUT IN THE FILL", 500, a_r1[1] - 22)
    bcallout(930, 500, "3 B TO C: SHAFT, HEADING, SHAFT", 800, hall_y - 8)
    bcallout(120, 600, "4 A TO C THE LONG WAY: A LOOP", 590, 640)
    t1 = plugs[(B[0]["name"], "T1")]
    bcallout(1080, 120, "5 UNUSED SOCKETS: JUST ROCK", min(t1)[0] + 14, 100)
    bcallout(1100, 250, "6 FILL: DEFAULT ROCK, OWN TILE", 1250, 330)
    bcallout(1290, 366, "7 MORE ROOMS", 1460, b_r1[1] - 8)
    bcallout(1290, 830, "8 FLOOR EXIT", 1460, c_r1[1] - 32)
    bcallout(60, 800, "9 A POCKET NOBODY CUT TO", 300, 724)
    blegend(30, 890, [
        ("BEATS", CYAN),
        ("ROOMS + CORRIDORS + FILL = ONE TERRAIN", (170, 180, 195)),
        ("TWO WAYS A TO C; THE FILL DIGS, SLOWLY", F_MID),
    ], 560)
    return save(out_path("RoomConcept_FloorStitch.png"), scale=2)


def build():
    build_rooms()
    return build_floor()


if __name__ == "__main__":
    build()

