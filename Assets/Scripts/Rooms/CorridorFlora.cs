using System.Collections.Generic;
using Lighting;
using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// Strews the corridors of a floor with growth: mushrooms (some of them glowing), moss,
    /// grass, ferns, bushes and roots on the floors; moss, roots, vines and glow-worm threads
    /// off the ceilings; shelf fungus and moss on the walls. The props are drawn by
    /// GameConcepts/Tools/roomprops_flora.py and are all Props.Decor, so none of it is in
    /// anyone's way until it is shot, blown up or set alight.
    ///
    /// Spots are read off the carved cells (<see cref="CorridorCarver"/>): a floor spot needs
    /// rock under the whole width of the plant and air over its height, a ceiling spot rock
    /// over its width and room under it to walk, a wall spot rock beside it top to bottom.
    /// What grows where is by the corridor's <see cref="CaveMood"/>, in clumps (a noise field
    /// thins it and thickens it), never in a room and never over a ladder.
    /// </summary>
    public static class CorridorFlora
    {
        /// <summary>Plants per world unit of floor, ceiling and wall, at density 1.</summary>
        public static float FloorRate = 1.7f, CeilingRate = 0.7f, WallRate = 0.35f;
        /// <summary>How far, world units, the art is sunk into what it grows from.</summary>
        public static float Sink = 0.05f;
        /// <summary>Head room a ceiling plant leaves under it, world units.</summary>
        public static float HangClearance = 0.6f;

        private const string Folder = "Prefabs/Props/";

        private enum Spot { Floor, Ceiling, Wall }

        private sealed class Kind
        {
            public GameObject Prefab;
            public Vector2 Size;
            public bool Glows;
        }

        private sealed class Table
        {
            public readonly List<(Kind kind, float weight)> Items = new();
            public float Total;

            public Kind Pick(System.Random rng)
            {
                float r = (float)rng.NextDouble() * Total;
                foreach (var (k, w) in Items)
                {
                    r -= w;
                    if (r <= 0f) return k;
                }
                return Items.Count > 0 ? Items[Items.Count - 1].kind : null;
            }
        }

        // what grows where - name, weight
        private static readonly (string, float)[] GreenFloor =
        {
            ("MossClump", 6), ("MossTuft", 6), ("GrassTuft", 6), ("Fern", 4), ("Shrub", 2), ("BerryBush", 2),
            ("Toadstool", 3), ("ToadstoolCluster", 2), ("TallStalk", 2), ("InkCap", 1), ("Morel", 1),
            ("RedCap", 1), ("CaveLily", 2), ("RootKnot", 1.5f), ("Puffballs", 2), ("GiantMushroom", 0.4f),
            ("GlowCaps", 1), ("GlowSpindles", 0.8f),
        };
        private static readonly (string, float)[] FungalFloor =
        {
            ("FungalMoss", 6), ("GlowCaps", 5), ("GlowStalks", 3), ("GlowBell", 3), ("GlowPuffs", 2),
            ("GlowSpindles", 3), ("GlowGiant", 0.6f), ("Toadstool", 2), ("ToadstoolCluster", 2), ("InkCap", 2),
            ("CoralFungus", 2), ("Puffballs", 2), ("TallStalk", 2), ("RedCap", 1), ("Morel", 1),
            ("PaleSprouts", 2), ("GiantMushroom", 0.5f), ("MossTuft", 2),
        };
        private static readonly (string, float)[] DryFloor =
        {
            ("DryGrass", 6), ("DeadShrub", 3), ("ThornBush", 3), ("RootKnot", 3), ("PaleSprouts", 2),
            ("Puffballs", 1), ("Toadstool", 1), ("MossTuft", 1), ("CoralFungus", 1), ("GlowSpindles", 0.5f),
        };
        private static readonly (string, float)[] GreenCeiling =
        {
            ("HangMoss", 4), ("HangMossShort", 5), ("HangRoots", 3), ("HangRootsThin", 3), ("Vines", 3),
            ("GlowDrops", 1),
        };
        private static readonly (string, float)[] FungalCeiling =
        {
            ("HangFungal", 4), ("HangGlowCaps", 3), ("GlowDrops", 3), ("HangRootsThin", 2), ("HangMossShort", 1),
        };
        private static readonly (string, float)[] DryCeiling =
        {
            ("HangRoots", 4), ("HangRootsThin", 5), ("HangMossShort", 1),
        };
        private static readonly (string, float)[] GreenWall =
        {
            ("WallMoss", 4), ("WallFern", 3), ("BracketFungus", 3), ("BracketGlow", 0.5f),
        };
        private static readonly (string, float)[] FungalWall =
        {
            ("BracketGlow", 3), ("WallGlowCaps", 3), ("BracketFungus", 2), ("WallMoss", 1),
        };
        private static readonly (string, float)[] DryWall =
        {
            ("BracketFungus", 2), ("WallMoss", 0.5f),
        };

        private static Table[,] _tables;            // [mood, spot]
        private static readonly HashSet<string> Missing = new();

        private static Table[,] Tables()
        {
            if (_tables != null) return _tables;
            var cache = new Dictionary<string, Kind>();
            Table Make((string, float)[] list)
            {
                var t = new Table();
                foreach (var (name, w) in list)
                {
                    if (!cache.TryGetValue(name, out var k))
                    {
                        var go = Resources.Load<GameObject>(Folder + name);
                        var sr = go ? go.GetComponent<SpriteRenderer>() : null;
                        k = go && sr && sr.sprite
                            ? new Kind { Prefab = go, Size = sr.sprite.bounds.size, Glows = go.GetComponent<LightSource2D>() }
                            : null;
                        cache[name] = k;
                        if (k == null && Missing.Add(name))
                            Debug.LogWarning($"CorridorFlora: no prop at Resources/{Folder}{name} - run roomprops.py roomprops_flora.");
                    }
                    if (k == null) continue;
                    t.Items.Add((k, w));
                    t.Total += w;
                }
                return t;
            }
            _tables = new Table[3, 3];
            _tables[(int)CaveMood.Green, (int)Spot.Floor] = Make(GreenFloor);
            _tables[(int)CaveMood.Fungal, (int)Spot.Floor] = Make(FungalFloor);
            _tables[(int)CaveMood.Dry, (int)Spot.Floor] = Make(DryFloor);
            _tables[(int)CaveMood.Green, (int)Spot.Ceiling] = Make(GreenCeiling);
            _tables[(int)CaveMood.Fungal, (int)Spot.Ceiling] = Make(FungalCeiling);
            _tables[(int)CaveMood.Dry, (int)Spot.Ceiling] = Make(DryCeiling);
            _tables[(int)CaveMood.Green, (int)Spot.Wall] = Make(GreenWall);
            _tables[(int)CaveMood.Fungal, (int)Spot.Wall] = Make(FungalWall);
            _tables[(int)CaveMood.Dry, (int)Spot.Wall] = Make(DryWall);
            return _tables;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            _tables = null;
            Missing.Clear();
        }

        // ─────────────────────────────────────────────────────────────────────────

        private sealed class Ctx
        {
            public CorridorCarver C;
            public Transform Parent;
            public List<CorridorCarver.LadderSpot> Ladders;
            public System.Random Rng;
            public readonly HashSet<long> Taken = new();
            public int Placed, Glowing;
        }

        public static void Grow(CorridorCarver carver, Transform parent, List<CorridorCarver.LadderSpot> ladders,
                                float density, int seed)
        {
            if (density <= 0f) return;
            var tables = Tables();
            var x = new Ctx { C = carver, Parent = parent, Ladders = ladders, Rng = new System.Random(seed * 31 + 5) };
            float ppu = carver.Ppu;
            float floorP = FloorRate * density / ppu, ceilP = CeilingRate * density / ppu, wallP = WallRate * density / ppu;

            foreach (var blk in carver.SortedBlocks())
            {
                bool check = carver.BlockTouchesRoom(blk);
                int bx = blk.x * CorridorCarver.BlockCells, by = blk.y * CorridorCarver.BlockCells;
                int x0 = Mathf.Max(1, bx), x1 = Mathf.Min(carver.Width - 2, bx + CorridorCarver.BlockCells - 1);
                int y0 = Mathf.Max(1, by), y1 = Mathf.Min(carver.Height - 2, by + CorridorCarver.BlockCells - 1);
                for (int cy = y0; cy <= y1; cy++)
                for (int cx = x0; cx <= x1; cx++)
                {
                    if (!carver.Air(cx, cy)) continue;
                    bool floor = !carver.Air(cx, cy - 1), ceiling = !carver.Air(cx, cy + 1);
                    bool left = !carver.Air(cx - 1, cy), right = !carver.Air(cx + 1, cy);
                    if (!floor && !ceiling && !left && !right) continue;

                    var p = new Vector2(carver.WorldX(cx), carver.EdgeY(cy));
                    if (check && carver.InRoom(p, 0.1f)) continue;
                    // clumps: thick here, bare there
                    float clump = 0.25f + 1.6f * carver.Patch(p.x, p.y, 0.5f) * carver.Patch(p.x + 40f, p.y, 0.13f) * 2f;
                    int mood = (int)carver.MoodAt(p);

                    if (floor && x.Rng.NextDouble() < floorP * clump)
                        TryFloor(x, tables[mood, (int)Spot.Floor].Pick(x.Rng), cx, cy);
                    if (ceiling && x.Rng.NextDouble() < ceilP * clump)
                        TryCeiling(x, tables[mood, (int)Spot.Ceiling].Pick(x.Rng), cx, cy);
                    if ((left || right) && !floor && !ceiling && x.Rng.NextDouble() < wallP * clump)
                        TryWall(x, tables[mood, (int)Spot.Wall].Pick(x.Rng), cx, cy, left);
                }
            }
            Debug.Log($"CorridorFlora: {x.Placed} plants in the corridors, {x.Glowing} of them glowing.");
        }

        // ─────────────────────────────────────────────────────────────────────────

        private static void TryFloor(Ctx x, Kind k, int cx, int cy)
        {
            if (k == null) return;
            var c = x.C;
            float ppu = c.Ppu;
            int halfW = Mathf.Max(1, Mathf.RoundToInt(k.Size.x * 0.5f * ppu * 0.7f));
            // rock under both edges and the middle, all at about this height
            foreach (int dx in new[] { -halfW, 0, halfW })
                if (!SurfaceNear(c, cx + dx, cy, +1)) return;
            // air over the whole plant
            int top = cy + Mathf.CeilToInt((k.Size.y + 0.1f) * ppu);
            for (int y = cy; y <= top; y += 4)
                if (!c.Air(cx, y)) return;
            for (int y = cy + 4; y <= top; y += 4)             // the edges may stand a step higher
                if (!c.Air(cx - halfW, y) || !c.Air(cx + halfW, y)) return;

            float wx = c.WorldX(cx), wy = c.EdgeY(cy);
            if (OnLadder(x, wx, k.Size.x * 0.5f, wy, wy + k.Size.y)) return;
            if (!Claim(x, 0, wy, wx, k.Size.x)) return;
            Place(x, k, new Vector2(wx, wy + k.Size.y * 0.5f - Sink), x.Rng.NextDouble() < 0.5);
        }

        private static void TryCeiling(Ctx x, Kind k, int cx, int cy)
        {
            if (k == null) return;
            var c = x.C;
            float ppu = c.Ppu;
            int halfW = Mathf.Max(1, Mathf.RoundToInt(k.Size.x * 0.5f * ppu * 0.6f));
            foreach (int dx in new[] { -halfW, 0, halfW })
                if (!SurfaceNear(c, cx + dx, cy, -1)) return;
            int bottom = cy - Mathf.CeilToInt((k.Size.y + HangClearance) * ppu);
            for (int y = cy; y >= bottom; y -= 4)
                if (!c.Air(cx, y)) return;

            float wx = c.WorldX(cx), wy = c.EdgeY(cy + 1);
            if (OnLadder(x, wx, k.Size.x * 0.5f, wy - k.Size.y, wy)) return;
            if (!Claim(x, 1, wy, wx, k.Size.x)) return;
            Place(x, k, new Vector2(wx, wy - k.Size.y * 0.5f + Sink), x.Rng.NextDouble() < 0.5);
        }

        private static void TryWall(Ctx x, Kind k, int cx, int cy, bool wallOnLeft)
        {
            if (k == null) return;
            var c = x.C;
            float ppu = c.Ppu;
            int side = wallOnLeft ? -1 : 1;                     // towards the wall
            int halfH = Mathf.Max(1, Mathf.RoundToInt(k.Size.y * 0.5f * ppu * 0.8f));
            int reach = Mathf.CeilToInt(k.Size.x * ppu);
            // rock beside it top to bottom (within three cells), air where it sticks out
            foreach (int dy in new[] { -halfH, 0, halfH })
            {
                bool rock = false;
                for (int s = 1; s <= 3 && !rock; s++) rock = !c.Air(cx + side * s, cy + dy);
                if (!rock || !c.Air(cx - side * reach, cy + dy)) return;
            }
            // not right down on the floor or up against the ceiling
            for (int dy = halfH + 2; dy <= halfH + Mathf.CeilToInt(0.25f * ppu); dy += 2)
                if (!c.Air(cx - side, cy - dy) || !c.Air(cx - side, cy + dy)) return;

            float wallX = c.WorldX(cx) + side * 0.5f / ppu;
            float wy = c.EdgeY(cy);
            float wx = wallX - side * (k.Size.x * 0.5f - Sink);
            if (OnLadder(x, wx, k.Size.x * 0.5f, wy - k.Size.y * 0.5f, wy + k.Size.y * 0.5f)) return;
            if (!Claim(x, 2, wallX, wy, k.Size.y)) return;
            // drawn growing out of a wall on its left; a wall on the right gets it mirrored
            Place(x, k, new Vector2(wx, wy), !wallOnLeft);
        }

        /// <summary>Rock just past (cx, cy) the way <paramref name="dir"/> says (+1: under,
        /// -1: over), give or take three cells of unevenness.</summary>
        private static bool SurfaceNear(CorridorCarver c, int cx, int cy, int dir)
        {
            for (int k = -3; k <= 3; k++)
            {
                int y = cy + k;
                if (c.Air(cx, y) && !c.Air(cx, y - dir)) return true;
            }
            return false;
        }

        private static bool OnLadder(Ctx x, float wx, float halfW, float y0, float y1)
        {
            foreach (var l in x.Ladders)
                if (Mathf.Abs(l.X - wx) < halfW + 0.3f && y1 > l.Bottom - 0.1f && y0 < l.Top)
                    return true;
            return false;
        }

        /// <summary>
        /// Room along the surface it grows from: slots of 0.2 units along the line `line`
        /// (a floor's or ceiling's height, a wall's x) of surface kind `kind`, as many as most
        /// of the plant's width. Neighbours may overlap at their edges - a clump, not a row.
        /// </summary>
        private static bool Claim(Ctx x, int kind, float line, float along, float width)
        {
            const float slot = 0.2f;
            long key = ((long)(Mathf.FloorToInt(line / slot) + 100000) * 4 + kind) * 1000003L;
            int a = Mathf.FloorToInt((along - width * 0.3f) / slot), b = Mathf.FloorToInt((along + width * 0.3f) / slot);
            int mid = Mathf.FloorToInt(along / slot);
            if (x.Taken.Contains(key + mid)) return false;
            if (x.Taken.Contains(key + a) && x.Taken.Contains(key + b)) return false;
            for (int i = a; i <= b; i++) x.Taken.Add(key + i);
            return true;
        }

        private static void Place(Ctx x, Kind k, Vector2 at, bool mirror)
        {
            var go = Object.Instantiate(k.Prefab, at, Quaternion.identity, x.Parent);
            go.name = k.Prefab.name;
            if (mirror) go.transform.localScale = new Vector3(-1f, 1f, 1f);
            if (!k.Glows)
            {
                // a little darker or lighter each, so a clump of one kind is not a stamp
                var sr = go.GetComponent<SpriteRenderer>();
                float v = 0.8f + 0.2f * (float)x.Rng.NextDouble();
                if (sr) sr.color = new Color(v, v, v, 1f);
            }
            else x.Glowing++;
            x.Placed++;
        }
    }
}
