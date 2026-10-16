using System.Collections.Generic;
using Phys.Terrain;
using UnityEngine;

namespace Rooms
{
    /// <summary>What a stretch of corridor is like: it picks the moss on the rock and what
    /// grows there (<see cref="CorridorFlora"/>).</summary>
    public enum CaveMood
    {
        Green,      // moss, grass, ferns, brown mushrooms
        Fungal,     // purple moss and glowing mushrooms
        Dry,        // dead grass, thorns, roots
    }

    /// <summary>What a floor recipe asks its corridors to be: one mood throughout, or Mixed.</summary>
    public enum CorridorMood
    {
        Mixed,
        Green,
        Fungal,
        Dry,
    }

    /// <summary>
    /// Cuts a floor's corridors into its map and dresses them: what <see cref="FloorBuilder"/>
    /// does between stamping the rooms and building the terrain.
    ///
    /// <list type="bullet">
    /// <item><see cref="Carve"/> - the corridor bore swept along each route as before (a box
    /// standing on every point: a flat floor where it runs level, a shaft where it climbs),
    /// then lumps cut above that floor so ceilings and shaft walls are not ruled lines, and
    /// now and then a small cave opened at a bend. Nothing is ever filled, and nothing is cut
    /// under a route's floor, so a corridor is never harder to walk than its bore.</item>
    /// <item><see cref="Ladders"/> - where a route climbs at least a set height, a ladder from
    /// the ground under the shaft to the floor it comes up to.</item>
    /// <item><see cref="Dress"/> - moss, root mat and fungal crust on the corridors' floors,
    /// ceilings and walls (tiles, so they are dug and burnt like rock), a band of growth along
    /// the foot of the back wall and roots hanging down it.</item>
    /// </list>
    /// Rooms are left as they were made: no lump, cave or tile reaches into a room's rectangle.
    /// The work is kept to the blocks a corridor was cut in (<see cref="Blocks"/>), never the
    /// whole map.
    /// </summary>
    public sealed class CorridorCarver
    {
        public const int BlockCells = 32;

        /// <summary>Furthest, world units, a ladder reaches down for ground.</summary>
        public static float LadderDrop = 10f;
        /// <summary>Least distance between two corridor caves, world units.</summary>
        public static float CaveSpacing = 7f;

        private readonly byte[] _cells;
        private readonly int _w, _h;
        private readonly Rect _bounds;
        private readonly float _ppu;
        private readonly Rect[] _rooms;
        private readonly Vector2 _o1, _o2, _o3, _mood1, _mood2;
        private readonly CorridorMood _mood;

        /// <summary>Blocks of <see cref="BlockCells"/> cells something was cut in.</summary>
        public readonly HashSet<Vector2Int> Blocks = new();

        public int Width => _w;
        public int Height => _h;
        public float Ppu => _ppu;
        public Rect Bounds => _bounds;

        public CorridorCarver(byte[] cells, int w, int h, Rect bounds, float ppu, Rect[] rooms, int seed,
                              CorridorMood mood = CorridorMood.Mixed)
        {
            _mood = mood;
            _cells = cells;
            _w = w;
            _h = h;
            _bounds = bounds;
            _ppu = ppu;
            _rooms = rooms;
            var rng = new System.Random(seed * 7919 + 17);
            Vector2 Offset() => new((float)rng.NextDouble() * 900f, (float)rng.NextDouble() * 900f);
            _o1 = Offset();
            _o2 = Offset();
            _o3 = Offset();
            _mood1 = Offset();
            _mood2 = Offset();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Cells
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Open at cell (x, y). Off the map counts as rock.</summary>
        public bool Air(int x, int y) => x >= 0 && y >= 0 && x < _w && y < _h && _cells[y * _w + x] == 0;

        public int CellX(float wx) => Mathf.FloorToInt((wx - _bounds.xMin) * _ppu);
        public int CellY(float wy) => Mathf.FloorToInt((wy - _bounds.yMin) * _ppu);
        public float WorldX(int x) => _bounds.xMin + (x + 0.5f) / _ppu;
        /// <summary>World height of the bottom edge of row y.</summary>
        public float EdgeY(int y) => _bounds.yMin + y / _ppu;

        public bool InRoom(Vector2 p, float pad = 0f)
        {
            foreach (var r in _rooms)
                if (p.x > r.xMin - pad && p.x < r.xMax + pad && p.y > r.yMin - pad && p.y < r.yMax + pad)
                    return true;
            return false;
        }

        private bool TouchesRoom(Rect box, float pad)
        {
            foreach (var r in _rooms)
                if (box.xMax > r.xMin - pad && box.xMin < r.xMax + pad &&
                    box.yMax > r.yMin - pad && box.yMin < r.yMax + pad)
                    return true;
            return false;
        }

        /// <summary>The blocks something was cut in, in a fixed order (a seed gives the same floor).</summary>
        public List<Vector2Int> SortedBlocks()
        {
            var list = new List<Vector2Int>(Blocks);
            list.Sort((a, b) => a.y != b.y ? a.y.CompareTo(b.y) : a.x.CompareTo(b.x));
            return list;
        }

        /// <summary>Whether any room's rectangle reaches into block b - if not, nothing in it
        /// needs a room test.</summary>
        public bool BlockTouchesRoom(Vector2Int b)
        {
            float size = BlockCells / _ppu;
            var box = new Rect(_bounds.xMin + b.x * size, _bounds.yMin + b.y * size, size, size);
            return TouchesRoom(box, 0.05f);
        }

        private void Touch(int x0, int y0, int x1, int y1)
        {
            for (int by = Mathf.Max(0, y0) / BlockCells; by <= Mathf.Min(_h - 1, y1) / BlockCells; by++)
            for (int bx = Mathf.Max(0, x0) / BlockCells; bx <= Mathf.Min(_w - 1, x1) / BlockCells; bx++)
                Blocks.Add(new Vector2Int(bx, by));
        }

        public CaveMood MoodAt(Vector2 p)
        {
            switch (_mood)
            {
                case CorridorMood.Green: return CaveMood.Green;
                case CorridorMood.Fungal: return CaveMood.Fungal;
                case CorridorMood.Dry: return CaveMood.Dry;
            }
            if (Mathf.PerlinNoise(_mood1.x + p.x * 0.03f, _mood1.y + p.y * 0.03f) > 0.56f) return CaveMood.Fungal;
            if (Mathf.PerlinNoise(_mood2.x + p.x * 0.04f, _mood2.y + p.y * 0.04f) > 0.6f) return CaveMood.Dry;
            return CaveMood.Green;
        }

        /// <summary>Patchiness, 0..1, for whatever wants it - tiles (in cells), plant clumps
        /// (in world units); `freq` is per whichever of the two it is given.</summary>
        public float Patch(float x, float y, float freq) => Mathf.PerlinNoise(_o3.x + x * freq, _o3.y + y * freq);

        // ─────────────────────────────────────────────────────────────────────────
        // Carving
        // ─────────────────────────────────────────────────────────────────────────

        public void Carve(FloorLayout plan, float bore, float lumps, float chambers, System.Random rng)
        {
            float half = bore * 0.5f;
            foreach (var route in plan.Corridors)
                for (int k = 1; k < route.Count; k++)
                {
                    Box(route[k - 1], route[k], bore);
                    if (lumps > 0f) Lumps(route[k - 1], route[k], half, lumps);
                }

            if (chambers <= 0f) return;
            var caves = new List<Vector2>();
            foreach (var route in plan.Corridors)
                // not the legs at either end: they are the sockets' own short runs
                for (int k = 3; k < route.Count - 3; k++)
                {
                    var c = route[k];
                    if (rng.NextDouble() >= chambers) continue;
                    bool near = false;
                    foreach (var o in caves)
                        if ((o - c).sqrMagnitude < CaveSpacing * CaveSpacing) { near = true; break; }
                    if (near) continue;
                    if (Cave(c, rng)) caves.Add(c);
                }
        }

        /// <summary>A box `bore` wide and `bore` tall standing on each point from a to b.
        /// Level runs get a flat floor at the route's height; climbs get a shaft centred on it.</summary>
        private void Box(Vector2 a, Vector2 b, float bore)
        {
            float len = Vector2.Distance(a, b);
            int steps = Mathf.Max(1, Mathf.CeilToInt(len * _ppu / 4f));
            float half = bore * 0.5f;
            for (int i = 0; i <= steps; i++)
            {
                var p = Vector2.Lerp(a, b, i / (float)steps);
                int x0 = Mathf.Max(0, CellX(p.x - half));
                int x1 = Mathf.Min(_w - 1, Mathf.CeilToInt((p.x + half - _bounds.xMin) * _ppu) - 1);
                int y0 = Mathf.Max(0, CellY(p.y));
                int y1 = Mathf.Min(_h - 1, Mathf.CeilToInt((p.y + bore - _bounds.yMin) * _ppu) - 1);
                for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                    _cells[y * _w + x] = 0;
                Touch(x0, y0, x1, y1);
            }
        }

        /// <summary>Discs of noisy radius along the bore's centre line, cut only above the
        /// segment's floor: domed, uneven ceilings, bulging shaft walls.</summary>
        private void Lumps(Vector2 a, Vector2 b, float half, float lumps)
        {
            float floor = Mathf.Min(a.y, b.y);
            float len = Vector2.Distance(a, b);
            int steps = Mathf.Max(1, Mathf.CeilToInt(len / 0.3f));
            for (int i = 0; i <= steps; i++)
            {
                var c = Vector2.Lerp(a, b, i / (float)steps) + new Vector2(0f, half);
                float n = 0.7f * Mathf.PerlinNoise(_o1.x + c.x * 0.45f, _o1.y + c.y * 0.45f)
                        + 0.3f * Mathf.PerlinNoise(_o2.x + c.x * 1.4f, _o2.y + c.y * 1.4f);
                n = Mathf.Clamp01((n - 0.3f) / 0.45f);
                Disc(c, half * (1f + lumps * n), floor);
            }
        }

        private void Disc(Vector2 c, float r, float floor)
        {
            var box = new Rect(c.x - r, Mathf.Max(floor, c.y - r), 2f * r, c.y + r - Mathf.Max(floor, c.y - r));
            bool check = TouchesRoom(box, 0.4f);
            int x0 = Mathf.Max(1, CellX(box.xMin)), x1 = Mathf.Min(_w - 2, CellX(box.xMax));
            int y0 = Mathf.Max(1, CellY(box.yMin)), y1 = Mathf.Min(_h - 2, CellY(box.yMax));
            float r2 = r * r * _ppu * _ppu;
            float cx = (c.x - _bounds.xMin) * _ppu, cy = (c.y - _bounds.yMin) * _ppu;
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                float dx = x + 0.5f - cx, dy = y + 0.5f - cy;
                if (dx * dx + dy * dy > r2) continue;
                if (check && InRoom(new Vector2(WorldX(x), EdgeY(y) + 0.5f / _ppu), 0.4f)) continue;
                _cells[y * _w + x] = 0;
            }
            Touch(x0, y0, x1, y1);
        }

        /// <summary>A small cave on a bend: a ragged dome on the corridor's floor, the floor
        /// itself left flat. False if it would come near a room or the floor's edge.</summary>
        private bool Cave(Vector2 at, System.Random rng)
        {
            float rx = Mathf.Lerp(1.8f, 3.2f, (float)rng.NextDouble());
            float ry = Mathf.Lerp(1.3f, 2.3f, (float)rng.NextDouble());
            var c = new Vector2(at.x, at.y + ry * 0.35f);
            var box = new Rect(c.x - rx * 1.2f, at.y, rx * 2.4f, ry * 1.6f);
            if (TouchesRoom(box, 1f)) return false;
            if (box.xMin < _bounds.xMin + 1.5f || box.xMax > _bounds.xMax - 1.5f || box.yMax > _bounds.yMax - 1.5f)
                return false;

            int x0 = CellX(box.xMin), x1 = CellX(box.xMax);
            int y0 = CellY(at.y), y1 = CellY(box.yMax);
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                float wx = WorldX(x), wy = EdgeY(y) + 0.5f / _ppu;
                float dx = (wx - c.x) / rx, dy = (wy - c.y) / ry;
                float edge = 0.8f + 0.45f * Mathf.PerlinNoise(_o2.x + wx * 0.9f, _o2.y + wy * 0.9f);
                if (dx * dx + dy * dy <= edge) _cells[y * _w + x] = 0;
            }
            Touch(x0, y0, x1, y1);
            return true;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Ladders
        // ─────────────────────────────────────────────────────────────────────────

        public struct LadderSpot
        {
            public float X, Top, Bottom;
        }

        /// <summary>
        /// A ladder up every climb of at least <paramref name="minClimb"/>: from the ground
        /// under the shaft (found by looking down the shaft's centre, so one that drops into a
        /// room through its ceiling reaches the room's floor) to the floor the shaft comes up
        /// to - for a corridor that comes up through a room's floor, through the socket's stub
        /// to the room's own floor.
        /// </summary>
        public List<LadderSpot> Ladders(FloorLayout plan, IReadOnlyList<FloorLayout.RoomShape> shapes, float minClimb)
        {
            var spots = new List<LadderSpot>();
            for (int i = 0; i < plan.Corridors.Count && i < plan.Links.Count; i++)
            {
                var route = plan.Corridors[i];
                var link = plan.Links[i];
                var sa = shapes[link.A].Sockets[link.SocketA];
                var sb = shapes[link.B].Sockets[link.SocketB];
                for (int k = 1; k < route.Count; k++)
                {
                    Vector2 a = route[k - 1], b = route[k];
                    if (Mathf.Abs(a.x - b.x) > 0.01f) continue;
                    int hiIndex = a.y > b.y ? k - 1 : k;
                    float top = Mathf.Max(a.y, b.y);
                    if (hiIndex == 0 && sa.Side == SocketSide.Bottom) top += sa.Depth;
                    if (hiIndex == route.Count - 1 && sb.Side == SocketSide.Bottom) top += sb.Depth;

                    float bottom = Ground(a.x, Mathf.Min(a.y, b.y));
                    if (top - bottom < minClimb) continue;
                    Add(spots, new LadderSpot { X = a.x, Top = top + 0.05f, Bottom = bottom });
                }
            }
            return spots;
        }

        /// <summary>Top of the first rock under (x, y), no further than LadderDrop.</summary>
        private float Ground(float x, float y)
        {
            int cx = CellX(x), cy = CellY(y);
            int stop = Mathf.Max(0, cy - Mathf.CeilToInt(LadderDrop * _ppu));
            while (cy > stop && Air(cx, cy)) cy--;
            return Air(cx, cy) ? y : EdgeY(cy + 1);
        }

        /// <summary>Two corridors that climb the same shaft share one ladder.</summary>
        private static void Add(List<LadderSpot> spots, LadderSpot s)
        {
            for (int i = 0; i < spots.Count; i++)
            {
                var o = spots[i];
                if (Mathf.Abs(o.X - s.X) > 0.3f || o.Bottom > s.Top || s.Bottom > o.Top) continue;
                o.Top = Mathf.Max(o.Top, s.Top);
                o.Bottom = Mathf.Min(o.Bottom, s.Bottom);
                spots[i] = o;
                return;
            }
            spots.Add(s);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Dressing
        // ─────────────────────────────────────────────────────────────────────────

        private struct Palette
        {
            public byte Floor, FloorAlt, Ceiling, Wall, BackBand, BackRoot;
            public float FloorPatch, CeilingPatch, WallPatch, RootChance;
        }

        /// <summary>
        /// Paint the rock round the corridors: growth on floors (2-8 cells deep), ceilings and
        /// walls in patches, by mood; on the back wall a band of it along the foot and roots
        /// hanging from the ceiling. Only the fill's own tiles are painted - a room's timber or
        /// a corridor running past a room's masonry is left as it is.
        /// </summary>
        public void Dress(TerrainMap map, byte fill, TerrainMap back, byte backFill, Materials.PhysMaterialId material)
        {
            var moods = new Palette[3];
            byte T(TerrainMap m, string tile) => (byte)m.Require(tile, material);
            moods[(int)CaveMood.Green] = new Palette
            {
                Floor = T(map, "root_growth"), FloorAlt = T(map, "moss"), Ceiling = T(map, "moss"), Wall = T(map, "moss"),
                BackBand = back ? T(back, "root_growth") : (byte)0, BackRoot = back ? T(back, "root") : (byte)0,
                FloorPatch = 0.3f, CeilingPatch = 0.5f, WallPatch = 0.62f, RootChance = 0.28f,
            };
            moods[(int)CaveMood.Fungal] = new Palette
            {
                Floor = T(map, "moss_dark"), FloorAlt = T(map, "soil_lush_dark"), Ceiling = T(map, "moss_dark"),
                Wall = T(map, "moss_dark"),
                BackBand = back ? T(back, "moss_dark") : (byte)0, BackRoot = back ? T(back, "root") : (byte)0,
                FloorPatch = 0.3f, CeilingPatch = 0.42f, WallPatch = 0.55f, RootChance = 0.18f,
            };
            moods[(int)CaveMood.Dry] = new Palette
            {
                Floor = T(map, "earth"), FloorAlt = T(map, "soil_dead"), Ceiling = 0, Wall = 0,
                BackBand = back ? T(back, "soil") : (byte)0, BackRoot = back ? T(back, "root") : (byte)0,
                FloorPatch = 0.55f, CeilingPatch = 2f, WallPatch = 2f, RootChance = 0.35f,
            };

            var backCells = back ? back.Cells : null;
            foreach (var blk in SortedBlocks())
            {
                bool check = BlockTouchesRoom(blk);
                int bx0 = blk.x * BlockCells, by0 = blk.y * BlockCells;
                int bx1 = Mathf.Min(_w - 2, bx0 + BlockCells - 1), by1 = Mathf.Min(_h - 2, by0 + BlockCells - 1);
                for (int y = Mathf.Max(1, by0); y <= by1; y++)
                for (int x = Mathf.Max(1, bx0); x <= bx1; x++)
                {
                    int i = y * _w + x;
                    if (_cells[i] != 0) continue;
                    if (_cells[i - _w] == 0 && _cells[i + _w] == 0 && _cells[i - 1] == 0 && _cells[i + 1] == 0)
                        continue;                       // open all round: nothing to dress
                    var p = new Vector2(WorldX(x), EdgeY(y));
                    if (check && InRoom(p)) continue;
                    var pal = moods[(int)MoodAt(p)];

                    if (_cells[i - _w] != 0)
                    {
                        // floor: the rock under this air cell
                        if (Patch(x, 0f, 0.01f) > pal.FloorPatch)
                        {
                            int depth = 2 + (int)(6f * Patch(x, 3f, 0.05f));
                            byte tile = Patch(x, y, 0.02f) > 0.58f ? pal.FloorAlt : pal.Floor;
                            for (int k = 1; k <= depth && y - k >= 0; k++)
                                if (_cells[i - k * _w] == fill) _cells[i - k * _w] = tile;
                        }
                        if (backCells != null && pal.BackBand != 0 && Patch(x, 7f, 0.012f) > 0.38f)
                        {
                            int band = (int)(18f * Patch(x, 11f, 0.06f));
                            for (int k = 0; k < band && y + k < _h && _cells[i + k * _w] == 0; k++)
                                if (backCells[i + k * _w] == backFill) backCells[i + k * _w] = pal.BackBand;
                        }
                    }

                    if (_cells[i + _w] == fill && pal.Ceiling != 0 && Patch(x, 50f, 0.012f) > pal.CeilingPatch)
                    {
                        int depth = 1 + (int)(4f * Patch(x, 53f, 0.08f));
                        for (int k = 1; k <= depth && y + k < _h; k++)
                            if (_cells[i + k * _w] == fill) _cells[i + k * _w] = pal.Ceiling;
                    }
                    if (_cells[i + _w] != 0 && backCells != null && pal.BackRoot != 0)
                    {
                        // roots down the back wall from the ceiling, in clumps of columns
                        float r = Patch(x, 90f, 0.3f);
                        if (r > 1f - pal.RootChance)
                        {
                            int len = (int)(_ppu * 1.4f * Patch(x, 95f, 0.9f) * (r - (1f - pal.RootChance)) / pal.RootChance) + 6;
                            for (int k = 0; k < len && y - k >= 0 && _cells[i - k * _w] == 0; k++)
                                if (backCells[i - k * _w] == backFill) backCells[i - k * _w] = pal.BackRoot;
                        }
                    }

                    if (pal.Wall != 0 && Patch(x + 30f, y, 0.015f) > pal.WallPatch)
                    {
                        int depth = 1 + (int)(3f * Patch(x, y, 0.3f));
                        if (_cells[i - 1] == fill)
                            for (int k = 1; k <= depth && x - k >= 0; k++)
                                if (_cells[i - k] == fill) _cells[i - k] = pal.Wall;
                        if (_cells[i + 1] == fill)
                            for (int k = 1; k <= depth && x + k < _w; k++)
                                if (_cells[i + k] == fill) _cells[i + k] = pal.Wall;
                    }
                }
            }
        }
    }
}
