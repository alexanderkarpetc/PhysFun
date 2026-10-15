using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// The back wall: a <see cref="TerrainMap"/> drawn behind the terrain - planks behind a
    /// house's rooms, dark rock behind a cave - so the air has something behind it instead of
    /// the camera's clear colour. Starbound and Terraria build their houses the same way: blocks
    /// in front, a wall layer behind that nothing collides with. The wall is what makes a frame
    /// read as a room.
    ///
    /// It is only a picture. No bodies, no colliders, sight passes through it and nothing digs
    /// it, so a chunk is never patched: it is made once from the map when the camera comes near
    /// and dropped again when the camera is far away. Each tile is darkened once, the first time
    /// it is used (<see cref="shade"/>, <see cref="haze"/>). That is what keeps it behind the
    /// terrain to the eye - the same tile at full brightness reads as solid.
    ///
    /// Cell 0 is no wall: the clear colour shows there, as before.
    /// </summary>
    public sealed class TerrainBackdrop : MonoBehaviour
    {
        [SerializeField] private TerrainMap map;

        [Tooltip("Brightness the wall's tiles are drawn at, against the same tile as terrain.")]
        [SerializeField, Range(0f, 1f)] private float shade = 0.62f;

        [Tooltip("Colour the wall fades towards - the cave's own dark.")]
        [SerializeField] private Color hazeColor = new(0.07f, 0.08f, 0.10f, 1f);

        [Tooltip("How far the wall fades towards the haze colour.")]
        [SerializeField, Range(0f, 1f)] private float haze = 0.22f;

        [Tooltip("Behind the terrain (-1) and everything in front of it.")]
        [SerializeField] private int sortingOrder = -50;

        [Tooltip("Chunk side in cells. Nothing is ever patched, so these can be big.")]
        [SerializeField] private int chunkPixels = 128;

        /// <summary>World units past the edge of the camera's view that are built.</summary>
        public static float BuildMargin = 6f;

        /// <summary>World units past the edge of the view beyond which a chunk is dropped.
        /// Wider than <see cref="BuildMargin"/>, so walking back and forth does not churn.</summary>
        public static float DropMargin = 16f;

        /// <summary>Milliseconds a frame may spend filling chunks.</summary>
        public static float BudgetMs = 1.5f;

        private sealed class Chunk
        {
            public GameObject Go;
            public Texture2D Tex;
            public Color32[] Pixels;
            public int Width, Height;
        }

        private TerrainTiler.Tile[] _tiles;
        private byte[] _cells;
        private int _w, _h, _cols, _rows;
        private float _ppu;
        private Vector2 _origin;
        private sbyte[] _state;                     // per chunk: 0 not looked at, -1 empty, 1 built
        private readonly Dictionary<int, Chunk> _chunks = new();
        private readonly Stack<Chunk> _spare = new();   // full-size chunks dropped, kept for reuse
        private readonly List<int> _drop = new();
        private float _nextSweep;

        private static readonly ProfilerMarker s_fill = new("Backdrop.Chunk.Fill");

        public TerrainMap Map => map;

        public void SetMap(TerrainMap value)
        {
            Clear();
            map = value;
            _cells = null;
        }

        private bool Ready()
        {
            if (_cells != null) return true;
            if (!map) return false;

            _cells = map.Cells;
            _w = map.Width;
            _h = map.Height;
            _ppu = map.PixelsPerUnit;
            _origin = map.Origin;
            chunkPixels = Mathf.Max(16, chunkPixels);
            _cols = (_w + chunkPixels - 1) / chunkPixels;
            _rows = (_h + chunkPixels - 1) / chunkPixels;
            _state = new sbyte[_cols * _rows];

            var palette = map.Palette;
            _tiles = new TerrainTiler.Tile[palette.Count];
            var tint = (Color32)hazeColor;
            float k = shade * (1f - haze);
            float hr = tint.r * haze, hg = tint.g * haze, hb = tint.b * haze;
            for (int i = 0; i < palette.Count; i++)
                _tiles[i] = TerrainTiler.Load(palette[i].tile).Recolored(c => new Color32(
                    (byte)Mathf.Min(255f, c.r * k + hr),
                    (byte)Mathf.Min(255f, c.g * k + hg),
                    (byte)Mathf.Min(255f, c.b * k + hb), 255));
            return true;
        }

        private void LateUpdate()
        {
            var cam = Camera.main;
            if (!cam || !Ready()) return;

            float hh = cam.orthographic ? cam.orthographicSize : 12f;
            float hw = hh * cam.aspect;
            Vector2 c = cam.transform.position;

            // Nearest first: the chunks under the view, then the margin round it.
            long deadline = System.Diagnostics.Stopwatch.GetTimestamp() +
                            (long)(BudgetMs * 0.001 * System.Diagnostics.Stopwatch.Frequency);
            if (!BuildRange(c, hw, hh, 0f, long.MaxValue)) return;
            BuildRange(c, hw, hh, BuildMargin, deadline);

            if (Time.unscaledTime >= _nextSweep)
            {
                _nextSweep = Time.unscaledTime + 0.5f;
                DropOutside(c, hw + DropMargin, hh + DropMargin);
            }
        }

        /// <summary>Build every chunk within <paramref name="margin"/> of the view. False when
        /// the time ran out first.</summary>
        private bool BuildRange(Vector2 c, float hw, float hh, float margin, long deadline)
        {
            Vector2 lo = (Vector2)transform.InverseTransformPoint(c - new Vector2(hw + margin, hh + margin)) - _origin;
            Vector2 hi = (Vector2)transform.InverseTransformPoint(c + new Vector2(hw + margin, hh + margin)) - _origin;
            float k = _ppu / chunkPixels;
            int x0 = Mathf.Max(0, Mathf.FloorToInt(lo.x * k)), x1 = Mathf.Min(_cols - 1, Mathf.FloorToInt(hi.x * k));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(lo.y * k)), y1 = Mathf.Min(_rows - 1, Mathf.FloorToInt(hi.y * k));

            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                int i = y * _cols + x;
                if (_state[i] != 0) continue;
                if (System.Diagnostics.Stopwatch.GetTimestamp() > deadline) return false;
                Build(x, y);
            }
            return true;
        }

        private void DropOutside(Vector2 c, float hw, float hh)
        {
            Vector2 lo = (Vector2)transform.InverseTransformPoint(c - new Vector2(hw, hh)) - _origin;
            Vector2 hi = (Vector2)transform.InverseTransformPoint(c + new Vector2(hw, hh)) - _origin;
            float k = _ppu / chunkPixels;
            int x0 = Mathf.FloorToInt(lo.x * k), x1 = Mathf.FloorToInt(hi.x * k);
            int y0 = Mathf.FloorToInt(lo.y * k), y1 = Mathf.FloorToInt(hi.y * k);

            _drop.Clear();
            foreach (var i in _chunks.Keys)
            {
                int x = i % _cols, y = i / _cols;
                if (x < x0 || x > x1 || y < y0 || y > y1) _drop.Add(i);
            }
            foreach (var i in _drop)
            {
                var chunk = _chunks[i];
                _chunks.Remove(i);
                _state[i] = 0;
                Retire(chunk);
            }
        }

        private void Build(int cx, int cy)
        {
            int i = cy * _cols + cx;
            int px0 = cx * chunkPixels, py0 = cy * chunkPixels;
            int cw = Mathf.Min(chunkPixels, _w - px0), ch = Mathf.Min(chunkPixels, _h - py0);

            var chunk = Take(cw, ch);
            if (!Fill(chunk, px0, py0))
            {
                _state[i] = -1;
                Retire(chunk);
                return;
            }

            chunk.Tex.SetPixels32(chunk.Pixels);
            chunk.Tex.Apply(false, false);
            chunk.Go.transform.localPosition = new Vector3(
                _origin.x + (px0 + cw * 0.5f) / _ppu,
                _origin.y + (py0 + ch * 0.5f) / _ppu, 0f);
            chunk.Go.name = $"Back_{cx}_{cy}";
            chunk.Go.SetActive(true);
            _chunks[i] = chunk;
            _state[i] = 1;
        }

        /// <summary>Paint a chunk's pixels from the map. False when it has no wall at all.</summary>
        private bool Fill(Chunk chunk, int px0, int py0)
        {
            using var _ = s_fill.Auto();
            var pixels = chunk.Pixels;
            int count = _tiles.Length, w = chunk.Width;
            bool any = false;
            for (int y = 0; y < chunk.Height; y++)
            {
                int row = (py0 + y) * _w + px0, dst = y * w, gy = py0 + y;
                int x = 0;
                while (x < w)
                {
                    int id = _cells[row + x];
                    int end = x + 1;
                    while (end < w && _cells[row + end] == id) end++;
                    if (id == 0 || id > count) System.Array.Clear(pixels, dst + x, end - x);
                    else
                    {
                        _tiles[id - 1].CopyRun(pixels, dst + x, px0 + x, gy, end - x);
                        any = true;
                    }
                    x = end;
                }
            }
            return any;
        }

        private Chunk Take(int cw, int ch)
        {
            if (cw == chunkPixels && ch == chunkPixels && _spare.Count > 0) return _spare.Pop();

            var tex = new Texture2D(cw, ch, TextureFormat.ARGB32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
            };
            var sprite = Sprite.Create(tex, new Rect(0, 0, cw, ch), new Vector2(0.5f, 0.5f), _ppu, 0,
                                       SpriteMeshType.FullRect, Vector4.zero, generateFallbackPhysicsShape: false);
            var go = new GameObject("Back");
            go.SetActive(false);
            go.layer = gameObject.layer;
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = sortingOrder;
            return new Chunk { Go = go, Tex = tex, Pixels = new Color32[cw * ch], Width = cw, Height = ch };
        }

        private void Retire(Chunk chunk)
        {
            if (chunk.Width == chunkPixels && chunk.Height == chunkPixels && _spare.Count < 64)
            {
                chunk.Go.SetActive(false);
                _spare.Push(chunk);
                return;
            }
            Kill(chunk);
        }

        private static void Kill(Chunk chunk)
        {
            var sprite = chunk.Go ? chunk.Go.GetComponent<SpriteRenderer>().sprite : null;
            if (chunk.Go) Destroy(chunk.Go);
            if (sprite) Destroy(sprite);
            if (chunk.Tex) Destroy(chunk.Tex);
        }

        private void Clear()
        {
            foreach (var chunk in _chunks.Values) Kill(chunk);
            foreach (var chunk in _spare) Kill(chunk);
            _chunks.Clear();
            _spare.Clear();
            if (_state != null) System.Array.Clear(_state, 0, _state.Length);
        }

        private void OnDestroy() => Clear();
    }
}
