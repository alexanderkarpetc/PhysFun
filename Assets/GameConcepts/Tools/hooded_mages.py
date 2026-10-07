"""Five hooded mages redrawn from the user's large concept paintings at our sprite size.

The sources were ~60px-tall pixel paintings; a straight downscale kept the silhouettes
and lost everything that made them who they are (the sickle, the eyes, the mask, the
skull), so these are hand-placed at 21-24px with the source beside them. What each one
keeps:

* crimson     - red band across a pointed hood, two red eyes in the dark, a bone sickle
* bogcap      - drooping cap crusted with glowing spores, root arms, two green eyes
* maskwraith  - pointed bone mask with one red eye, flared purple collar, a raking claw
* deepminer   - rusted helmet, a skull with a burning socket, a glowing heart, a pick
* goldhood    - hood with a curled tip, gold-trimmed rags, one yellow eye

All face right, like the rest of the cast; the crimson one and the goldhood were
mirrored from their sources to do so. They walk, like the other wizards - the grids are
the standing pose, `Tools/gen_mages.py` animates them.

    python hooded_mages.py

writes `Characters/Char_Wiz<Name>.png` at native size.
"""
import os

from pixelfix import write_png

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "Characters"))

SPRITES = {}

SPRITES['crimson'] = (dict(
    k=(10, 6, 10), K=(32, 20, 26), j=(52, 30, 38), J=(74, 46, 54),
    o=(90, 16, 32), O=(140, 26, 48), P=(180, 52, 70), R=(255, 60, 66),
    b=(170, 152, 124), B=(214, 198, 168), d=(104, 88, 70), u=(84, 56, 36), w=(70, 50, 38)), [
    "......K...............",
    "......KK..............",
    ".....KjK..............",
    ".....KjjK.............",
    "....KjjJjK............",
    "....KjjJjjK...........",
    "...KjjjjJjjK..........",
    "...oOOOPPOOoK.........",
    "..oOOOOOOOOPOK........",
    ".o.oKjjjKkkkOK........",
    "o..KjjjKkkRkRK........",
    "...KjjjKkkkkkK........",
    "..oKjjjjKkkkK.........",
    ".oOKKjjjjKKKjK...BBb..",
    "oO.KjjOjjjjjjjK.B...b.",
    "o.KjjjOOjjjjJjjKu....b",
    "..KjjOOjjdbdbjjbu....b",
    ".bKjjOjjjjbjjjjKb...d.",
    "bdKjjOOjjjBjjjjK...dO.",
    "b.KjjjOjjjjjjOjK..O...",
    "..KjjjOOjjjjOOjK......",
    "..KjjjjOjjjjOjjjK.....",
    "..KjOjjOjjjOjjOjK.....",
    "..K.Oj.Oj.jO.j.O......",
    "....ww......ww........",
    "...www.....www........",
])

SPRITES['bogcap'] = (dict(
    k=(8, 8, 8), h=(70, 58, 38), H=(118, 100, 70), I=(156, 138, 100),
    g=(44, 52, 30), G=(78, 90, 52), M=(110, 124, 72),
    s=(150, 196, 56), S=(214, 240, 110), r=(70, 52, 34), R=(104, 80, 52)), [
    "...............hH.....",
    "..............hHh.....",
    "........hHsHHHHh......",
    "......hHSsHHIHh.s.....",
    ".....hsSsHHIHHHh.s....",
    "....hHsHHHIHHsSHh.....",
    "...hHHHHHIHHHsSsHh....",
    "..hsHHHHHHHHHHHsHHh...",
    ".hHHhhhhhhhhhhhhhHHh..",
    "..s.hkkkkkkkkkh.h.....",
    "....kkSkkkSkkk..s.....",
    ".....GkkkkkkkkG.......",
    "....GgkkkkkkkgGgs.....",
    "...rGgGkkkkGgGgGr.....",
    "..rRgGMgkkgMGgGgRr....",
    ".rR.gGMggggMGgGg.Rr...",
    "rR..ggGMggMGggGg..Rr..",
    "r...gGgGggGgGgGg...rR.",
    "s...gg.GggG.gGgg....r.",
    "Ss..g..Gg.G..gg....sS.",
    ".s.....G..G...g....s..",
    ".......g..g...g.......",
    "......g...g....g......",
    "......g..........g....",
])

SPRITES['maskwraith'] = (dict(
    k=(10, 8, 12), v=(54, 34, 58), V=(96, 64, 100), W=(140, 100, 140),
    m=(150, 132, 108), M=(198, 182, 152), n=(96, 76, 58),
    u=(110, 70, 40), b=(204, 194, 164), R=(255, 50, 50)), [
    "..........k.............",
    "..........n.............",
    ".........nmk............",
    ".........mMn............",
    "........nmkMn...........",
    "........mMkmn...........",
    "...vv..nmMmMmn..........",
    "..vVWv.nmMMRmn.v........",
    "..vVWVvnmMmmnvVv........",
    "...vVWVvnmmnvVWv........",
    "...vVVWvknnkvWVv........",
    "..vVVVvkkuukkvVv....k.k.",
    "..vVVvkkbkkbkkvVk..knk.k",
    ".vVVvvkkkbbkkkkvVnnmkk.k",
    ".vVvvkkkkbkkkkvvnmnk.k..",
    "vVVvkkkukbkukkkvVk..k...",
    "vVvVkkkkkbkkkkvVv.......",
    "vVvvVkkkkbkkkvVvVv......",
    ".vvVvkkkkbkkkvVvVv......",
    "vVvVvvkkbbbkkvvVvv......",
    "..vVvVkkkbkkvVvVvVv.....",
    ".vVv.VvkkkkvVvVv.Vv.....",
    "vV..vVvvkkkvvV.vV..v....",
    "v...vv.vk.kv.v..v.......",
    "...v...v...v..v.........",
])

SPRITES['deepminer'] = (dict(
    k=(12, 10, 10), c=(40, 36, 34), C=(66, 60, 54), D=(96, 88, 78),
    q=(110, 56, 28), Q=(156, 86, 42), b=(178, 164, 134), B=(214, 200, 170),
    d=(110, 96, 76), R=(255, 70, 40), y=(220, 110, 36), Y=(255, 200, 90), u=(90, 60, 40)), [
    ".......qqqq...........",
    ".....qQQqQqq..........",
    "....qQQQqQQQq.........",
    "....qQkQQQqQQq........",
    "..qqqqqqqqqqqqqq......",
    "....kbBBBbbk..qq......",
    "...kbBkkkBBbk.........",
    "...kbkkRkBBdk.........",
    "...kbBkkkBddk.........",
    "....kbdBdbdk..........",
    "....kdbdbdk.....QQ....",
    "...cCCkddkCc...q..Q...",
    "..cCDCCkCCCCc.u....q..",
    "..cCDCyYyCCCbu.....q..",
    ".cCDCCyYCCCcbb........",
    ".cDCCCkCCCc...........",
    ".cCC.cCCCc............",
    ".b.c.cCcCc............",
    ".bd.cCC.CCc...........",
    "....cCc..Cc...........",
    "....kk...kk...........",
    "...kkk..kkk...........",
])

SPRITES['goldhood'] = (dict(
    k=(8, 6, 6), a=(48, 44, 40), A=(86, 80, 70), Z=(122, 114, 98),
    y=(130, 96, 36), Y=(190, 150, 60), G=(240, 200, 90), e=(255, 236, 140), w=(60, 48, 30)), [
    "..k..................",
    "..ka.................",
    "...kaa...............",
    "....aAa..............",
    "....aAAa.............",
    "...aAAZAa............",
    "...aAZZAAa...........",
    "..aAAZAAAa...........",
    "...aAAZAAYa..........",
    "...aAZAAYkka.........",
    "..aAAZAYkkeka........",
    "..aAAAAYkkkk.k.......",
    "..aAAAAAYkkk.k.......",
    ".aAAAYYYYYa..........",
    ".aAYAAAAAAYa.........",
    "aAAYAAyAAAAYaAA......",
    "aAYAAAyAAAAAYa.AZ....",
    "aAYAAAAyAAAAyAA.k.k.k",
    ".aYAAAyAAAAAyAa.k.k..",
    ".aYAAAyAAAAAyAa......",
    ".a.YAa.yAAA.yAa......",
    ".y..a..y.a...a.y.....",
    ".G...ka..ka...G......",
    ".....k...k...........",
    "....kw..kw...........",
    "...www.www...........",
])



def rows_of(name):
    pal, grid = SPRITES[name]
    w = max(len(r) for r in grid)
    return [[pal[ch] + (255,) if ch != '.' else (0, 0, 0, 0) for ch in r.ljust(w, '.')]
            for r in grid]


def main():
    for name in SPRITES:
        path = os.path.join(CHARS, "Char_Wiz%s.png" % name.capitalize())
        write_png(path, rows_of(name))
        print("wrote", path)


if __name__ == "__main__":
    main()
