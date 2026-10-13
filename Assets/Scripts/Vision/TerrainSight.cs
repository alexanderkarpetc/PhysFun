using System.Collections.Generic;
using Phys.Pixels;
using Phys.Terrain;
using Props;
using Unity.Collections;
using Unity.Profiling;
using UnityEngine;

namespace Vision
{
    /// <summary>
    /// Answers "does something here block sight" from the pixels that are actually drawn: a
    /// point is solid when a piece of standing terrain has an opaque pixel under it, or a shut
    /// door covers it. Nothing else counts - not crates, ropes, bodies or loose rocks.
    ///
    /// Not a physics query on purpose. Colliders cannot tell a wall from a prop without walking
    /// every hit, and a ray stepped past a prop sunk into rock starts inside the rock and sees
    /// through it. The pixels have neither problem.
    ///
    /// Rays ask this tens of thousands of times a frame, so the answer is kept as one flat
    /// byte map over the whole floor, a cell per <see cref="Resolution"/> units (two terrain
    /// pixels), and a check is one array read. The map is repainted only where terrain
    /// changed: a piece appearing or going (<see cref="TerrainBody.StandingVersion"/>), or its
    /// pixels being dug or burnt (the registry record's Version), a bounded amount per frame.
    /// A native copy of it (<see cref="Map"/>) is what the fog's ray jobs read; it is only
    /// written here, on the main thread, while no job is running.
    /// </summary>
    public sealed class TerrainSight
    {
        /// <summary>Map cell side, world units. Two terrain pixels at 40 per unit.</summary>
        public static float Resolution = 0.05f;

        /// <summary>Map cells repainted per frame at most, once the floor is built.</summary>
        public static int RepaintBudget = 16000;

        /// <summary>Seconds between looks for doors, and for pieces whose sprite was swapped.</summary>
        public static float SlowCheckInterval = 0.5f;

        private static readonly ProfilerMarker s_sync = new("Fog.Map.Sync");
        private static readonly ProfilerMarker s_build = new("Fog.Map.Build");
        private static readonly ProfilerMarker s_repaint = new("Fog.Map.Repaint");

        private const float Margin = 4f;
        private const float HashCell = 4f;

        private sealed class Piece
        {
            public TerrainBody Body;
            public PixelSpriteRegistry.Record Rec;
            public int Version;
            public RectInt Area;          // map cells it covers
            public int Stamp, Seen;
            // World point to texture pixel: px = Ax*x + Bx*y + Cx, py = Ay*x + By*y + Cy.
            public float Ax, Bx, Cx, Ay, By, Cy;
        }

        private byte[] _solid;
        private NativeArray<byte> _native;
        private int _w, _h;
        private Vector2 _origin;
        private float _res = 0.05f;

        /// <summary>Changes whenever the map is rebuilt and anything sized to it must follow.</summary>
        public int MapId { get; private set; }
        public bool HasMap => _native.IsCreated && _w > 0 && _h > 0;
        public NativeArray<byte> Map => _native;
        public int Width => _w;
        public int Height => _h;
        public Vector2 Origin => _origin;
        public float CellSize => _res;

        private readonly Dictionary<TerrainBody, Piece> _pieces = new();
        private readonly List<Piece> _pieceList = new();
        private readonly Dictionary<long, List<Piece>> _hash = new();
        private readonly List<RectInt> _dirty = new();
        private readonly List<Piece> _scratch = new();
        private int _version = -1;
        private int _stamp;
        private bool _needFull = true;

        private readonly List<Door> _doors = new();
        private readonly List<Rect> _doorRects = new();
        private float _nextSlowCheck;

        /// <summary>Drop the map; the next refresh builds it from scratch.</summary>
        public void Reset()
        {
            _pieces.Clear();
            _pieceList.Clear();
            _hash.Clear();
            _dirty.Clear();
            _version = -1;
            _needFull = true;
        }

        public void Refresh()
        {
            if (_version != TerrainBody.StandingVersion) Sync();

            if (Time.unscaledTime >= _nextSlowCheck)
            {
                _nextSlowCheck = Time.unscaledTime + SlowCheckInterval;
                SlowCheck();
            }

            if (_needFull)
            {
                Build();
                return;
            }

            for (int i = 0; i < _pieceList.Count; i++)
            {
                var p = _pieceList[i];
                if (p.Rec.Version == p.Version) continue;
                p.Version = p.Rec.Version;
                _dirty.Add(p.Area);
            }

            Repaint(RepaintBudget);
        }

        public bool Solid(Vector2 p)
        {
            if (_doorRects.Count > 0 && InDoor(p)) return true;
            if (_solid == null) return false;
            float x = (p.x - _origin.x) / _res, y = (p.y - _origin.y) / _res;
            return x >= 0f && y >= 0f && x < _w && y < _h && _solid[(int)y * _w + (int)x] != 0;
        }

        public int DoorCount => _doors.Count;

        /// <summary>The <paramref name="i"/>th door found shut at the last look, if it still is.</summary>
        public bool ShutDoor(int i, out Rect rect)
        {
            rect = _doorRects[i];
            return _doors[i] && !_doors[i].IsOpen;
        }

        public void Dispose()
        {
            if (_native.IsCreated) _native.Dispose();
            _w = _h = 0;
        }

        private bool InDoor(Vector2 p)
        {
            for (int i = 0; i < _doorRects.Count; i++)
                if (_doorRects[i].Contains(p) && _doors[i] && !_doors[i].IsOpen) return true;
            return false;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Which pieces exist
        // ─────────────────────────────────────────────────────────────────────────

        private void Sync()
        {
            using var _ = s_sync.Auto();
            _version = TerrainBody.StandingVersion;
            _stamp++;

            foreach (var body in TerrainBody.Standing)
            {
                if (!body) continue;
                if (_pieces.TryGetValue(body, out var p))
                {
                    p.Stamp = _stamp;
                    continue;
                }

                p = MakePiece(body);
                if (p == null) continue;
                p.Stamp = _stamp;
                _pieces.Add(body, p);
                _pieceList.Add(p);
                if (_needFull) continue;

                // A piece past the edge of the map just goes unpainted there: rebuilding the
                // whole map for it would cost far more than the sliver of sight it is worth.
                Place(p);
                HashAdd(p);
                _dirty.Add(p.Area);
            }

            for (int i = _pieceList.Count - 1; i >= 0; i--)
            {
                var p = _pieceList[i];
                if (p.Stamp == _stamp) continue;
                _pieceList.RemoveAt(i);
                _pieces.Remove(p.Body);
                if (_needFull) continue;
                HashRemove(p);
                _dirty.Add(p.Area);
            }
        }

        private Piece MakePiece(TerrainBody body)
        {
            var go = body.gameObject;
            var registry = PixelSpriteRegistry.Instance;
            if (!registry.TryGet(go, out var rec)) rec = registry.Get(go);
            if (rec == null || rec.Pixels == null) return null;

            var p = new Piece { Body = body };
            Bind(p, rec);
            return p;
        }

        private static void Bind(Piece p, PixelSpriteRegistry.Record rec)
        {
            p.Rec = rec;
            p.Version = rec.Version;

            // world -> local (sprite units) -> texture pixels
            var m = p.Body.transform.worldToLocalMatrix;
            float ppu = rec.Ppu;
            p.Ax = m.m00 * ppu; p.Bx = m.m01 * ppu; p.Cx = m.m03 * ppu + rec.PivotPx.x;
            p.Ay = m.m10 * ppu; p.By = m.m11 * ppu; p.Cy = m.m13 * ppu + rec.PivotPx.y;
        }

        /// <summary>
        /// Doors, and pieces whose record was replaced (the cracker swaps sprites) - neither
        /// says when it changes, so they are looked at now and then.
        /// </summary>
        private void SlowCheck()
        {
            _doors.Clear();
            _doorRects.Clear();
            foreach (var door in Object.FindObjectsByType<Door>(FindObjectsSortMode.None))
            {
                if (door.IsOpen) continue;
                var col = door.GetComponent<Collider2D>();
                if (!col || !col.enabled) continue;
                var b = col.bounds;
                _doors.Add(door);
                _doorRects.Add(new Rect(b.min.x, b.min.y, b.size.x, b.size.y));
            }

            if (_needFull) return;
            var registry = PixelSpriteRegistry.Instance;
            for (int i = 0; i < _pieceList.Count; i++)
            {
                var p = _pieceList[i];
                if (!p.Body || !registry.TryGet(p.Body.gameObject, out var rec) || rec == p.Rec) continue;
                Bind(p, rec);
                _dirty.Add(p.Area);
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // The map
        // ─────────────────────────────────────────────────────────────────────────

        private void Build()
        {
            using var _ = s_build.Auto();
            _needFull = false;
            _dirty.Clear();
            _hash.Clear();
            _res = Mathf.Max(0.01f, Resolution);

            MapId++;
            if (_pieceList.Count == 0)
            {
                _solid = null;
                Dispose();
                return;
            }

            var min = new Vector2(float.MaxValue, float.MaxValue);
            var max = new Vector2(float.MinValue, float.MinValue);
            foreach (var p in _pieceList)
            {
                var b = PieceBounds(p);
                min = Vector2.Min(min, b.min);
                max = Vector2.Max(max, b.max);
            }
            min -= Vector2.one * Margin;
            max += Vector2.one * Margin;

            _origin = min;
            _w = Mathf.CeilToInt((max.x - min.x) / _res);
            _h = Mathf.CeilToInt((max.y - min.y) / _res);
            if (_solid == null || _solid.Length < _w * _h) _solid = new byte[_w * _h];
            else System.Array.Clear(_solid, 0, _w * _h);

            foreach (var p in _pieceList)
            {
                Place(p);
                HashAdd(p);
                p.Version = p.Rec.Version;
                Paint(p, p.Area);
            }

            int n = _w * _h;
            if (_native.IsCreated && _native.Length != n) _native.Dispose();
            if (!_native.IsCreated) _native = new NativeArray<byte>(n, Allocator.Persistent, NativeArrayOptions.UninitializedMemory);
            NativeArray<byte>.Copy(_solid, 0, _native, 0, n);
        }

        private void Repaint(int budget)
        {
            if (_dirty.Count == 0 || _solid == null || !_native.IsCreated) return;
            using var _ = s_repaint.Auto();
            int done = 0;
            while (_dirty.Count > 0 && done < budget)
            {
                var r = _dirty[_dirty.Count - 1];
                _dirty.RemoveAt(_dirty.Count - 1);
                r = Clip(r);
                if (r.width <= 0 || r.height <= 0) continue;

                for (int y = r.yMin; y < r.yMax; y++)
                    System.Array.Clear(_solid, y * _w + r.xMin, r.width);

                Gather(r);
                foreach (var p in _scratch) Paint(p, r);
                for (int y = r.yMin; y < r.yMax; y++)
                    NativeArray<byte>.Copy(_solid, y * _w + r.xMin, _native, y * _w + r.xMin, r.width);
                done += r.width * r.height;
            }
        }

        /// <summary>Write <paramref name="p"/>'s opaque pixels into the map, inside <paramref name="clip"/>.</summary>
        private void Paint(Piece p, RectInt clip)
        {
            int x0 = Mathf.Max(clip.xMin, p.Area.xMin), x1 = Mathf.Min(clip.xMax, p.Area.xMax);
            int y0 = Mathf.Max(clip.yMin, p.Area.yMin), y1 = Mathf.Min(clip.yMax, p.Area.yMax);
            if (x0 >= x1 || y0 >= y1) return;

            var px = p.Rec.Pixels;
            int tw = p.Rec.Width, th = p.Rec.Height;
            float res = _res;

            for (int y = y0; y < y1; y++)
            {
                float wy = _origin.y + (y + 0.5f) * res;
                float wx = _origin.x + (x0 + 0.5f) * res;
                float u = p.Ax * wx + p.Bx * wy + p.Cx, v = p.Ay * wx + p.By * wy + p.Cy;
                float du = p.Ax * res, dv = p.Ay * res;
                int row = y * _w;

                for (int x = x0; x < x1; x++, u += du, v += dv)
                {
                    if (u < 0f || v < 0f) continue;
                    int iu = (int)u, iv = (int)v;
                    if (iu >= tw || iv >= th) continue;
                    if (px[iv * tw + iu].a != 0) _solid[row + x] = 1;
                }
            }
        }

        private static Bounds PieceBounds(Piece p)
        {
            var sr = p.Body ? p.Body.GetComponent<SpriteRenderer>() : null;
            return sr ? sr.bounds : new Bounds(p.Body ? p.Body.transform.position : Vector3.zero, Vector3.zero);
        }

        private void Place(Piece p)
        {
            var b = PieceBounds(p);
            int x0 = Mathf.FloorToInt((b.min.x - _origin.x) / _res);
            int y0 = Mathf.FloorToInt((b.min.y - _origin.y) / _res);
            int x1 = Mathf.CeilToInt((b.max.x - _origin.x) / _res);
            int y1 = Mathf.CeilToInt((b.max.y - _origin.y) / _res);
            p.Area = new RectInt(x0, y0, x1 - x0, y1 - y0);
        }

        private RectInt Clip(RectInt r)
        {
            int x0 = Mathf.Max(0, r.xMin), y0 = Mathf.Max(0, r.yMin);
            int x1 = Mathf.Min(_w, r.xMax), y1 = Mathf.Min(_h, r.yMax);
            return new RectInt(x0, y0, x1 - x0, y1 - y0);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Which pieces cover a region
        // ─────────────────────────────────────────────────────────────────────────

        private void HashRange(RectInt area, out int hx0, out int hy0, out int hx1, out int hy1)
        {
            float k = _res / HashCell;
            hx0 = Mathf.FloorToInt(area.xMin * k);
            hy0 = Mathf.FloorToInt(area.yMin * k);
            hx1 = Mathf.FloorToInt((area.xMax - 1) * k);
            hy1 = Mathf.FloorToInt((area.yMax - 1) * k);
        }

        private void HashAdd(Piece p)
        {
            HashRange(p.Area, out int hx0, out int hy0, out int hx1, out int hy1);
            for (int y = hy0; y <= hy1; y++)
            for (int x = hx0; x <= hx1; x++)
            {
                long key = Key(x, y);
                if (!_hash.TryGetValue(key, out var list)) _hash[key] = list = new List<Piece>(4);
                list.Add(p);
            }
        }

        private void HashRemove(Piece p)
        {
            HashRange(p.Area, out int hx0, out int hy0, out int hx1, out int hy1);
            for (int y = hy0; y <= hy1; y++)
            for (int x = hx0; x <= hx1; x++)
                if (_hash.TryGetValue(Key(x, y), out var list)) list.Remove(p);
        }

        private void Gather(RectInt r)
        {
            _scratch.Clear();
            _stamp++;
            HashRange(r, out int hx0, out int hy0, out int hx1, out int hy1);
            for (int y = hy0; y <= hy1; y++)
            for (int x = hx0; x <= hx1; x++)
            {
                if (!_hash.TryGetValue(Key(x, y), out var list)) continue;
                foreach (var p in list)
                {
                    if (p.Seen == _stamp) continue;
                    p.Seen = _stamp;
                    _scratch.Add(p);
                }
            }
        }

        private static long Key(int x, int y) => ((long)x << 32) | (uint)y;
    }
}
