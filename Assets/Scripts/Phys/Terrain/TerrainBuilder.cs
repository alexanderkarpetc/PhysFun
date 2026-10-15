using System.Collections.Generic;
using Materials;
using Phys.Pixels;
using Spawners;
using Unity.Profiling;
using UnityEngine;

namespace Phys.Terrain
{
    public enum TerrainShape
    {
        /// <summary>Solid below a noisy surface line — ground, hills, cave floors.</summary>
        Heightfield,
        Box,
        Ellipse,
    }

    /// <summary>One band of material, measured down from the surface of its feature.</summary>
    [System.Serializable]
    public sealed class TerrainStratum
    {
        [Tooltip("Texture name under Resources/Sprites/Materials (no folder, no extension).")]
        public string tile = "rock";

        [Tooltip("Physics material of chunks made mostly of this band — drives density and " +
                 "whether the terrain burns.")]
        public PhysMaterialId physMaterial = PhysMaterialId.Default;

        [Tooltip("How far below the surface this band reaches, in world units. 0 = all the way down.")]
        public float thickness;
    }

    /// <summary>One shape stamped into the terrain. Later features paint over earlier ones.</summary>
    [System.Serializable]
    public sealed class TerrainFeature
    {
        public string label = "feature";
        public TerrainShape shape = TerrainShape.Heightfield;

        [Tooltip("Bounds of the shape, in this object's local space.")]
        public Vector2 min;
        public Vector2 max;

        [Header("Heightfield")]
        [Tooltip("Average surface height above min.y.")]
        public float surfaceMean = 2f;
        public float surfaceAmplitude = 0.5f;
        public float surfaceFrequency = 0.15f;

        [Header("Ellipse")]
        [Tooltip("How much the outline is chewed up by noise. 0 = a clean ellipse.")]
        public float edgeNoise = 0.25f;

        public float noiseSeed;

        [Tooltip("Surface downwards. The last entry (or any with thickness 0) fills the rest.")]
        public TerrainStratum[] strata = { new TerrainStratum() };
    }

    /// <summary>
    /// Turns a terrain definition into destructible static bodies: one pixel mask is cut into
    /// chunk-sized sprite objects, each a static <see cref="TerrainBody"/> that every existing
    /// tool already understands — the eraser carves it, fire burns it where the material is
    /// flammable, and the cracker knocks shards out of it.
    ///
    /// The mask comes from a <see cref="TerrainMap"/> asset when one is assigned (that's what the
    /// Terrain Painter window edits), and otherwise from the procedural <see cref="features"/>
    /// list. Either way the chunks are a regenerated view, never saved data — <see cref="Build"/>
    /// recreates them from scratch and <see cref="RefreshArea"/> patches the ones an edit touched.
    ///
    /// Chunking is what keeps it affordable: an edit only re-uploads and re-traces the chunk it
    /// landed in, and the connected-component split scan only ever walks one chunk's texture.
    /// Chunks are stamped from a single shared mask, so their pixels line up exactly and the
    /// tiled art runs straight across the seams.
    /// </summary>
    public sealed class TerrainBuilder : MonoBehaviour
    {
        [Header("Source")]
        [Tooltip("Painted terrain. When set it replaces the procedural features below, and its " +
                 "resolution and region win over the ones here.")]
        [SerializeField] private TerrainMap map;

        [Header("Resolution")]
        [Tooltip("Mask cells per world unit, used only for the procedural features. " +
                 "40 matches the spawned props (20 PPU art at 0.5 scale).")]
        [SerializeField] private float pixelsPerUnit = 40f;

        [Tooltip("Chunk side in cells. Bigger = fewer colliders but pricier edits.")]
        [SerializeField] private int chunkPixels = 64;

        [Tooltip("Chunks with fewer solid cells than this are dropped instead of spawning a " +
                 "body that isn't worth its collider.")]
        [SerializeField] private int minChunkPixels = 24;

        [Header("Physics")]
        [SerializeField] private int simplifyLevel = 2;
        [SerializeField] private int sortingOrder = -1;

        [Tooltip("Layers that count as immovable ground. Terrain that can no longer reach one " +
                 "of these through neighbouring terrain falls down.")]
        [SerializeField] private string[] bedrockLayers = { "Untouchable" };

        [Header("Procedural fallback")]
        [SerializeField] private bool buildOnAwake = true;
        [SerializeField] private TerrainFeature[] features = DefaultFeatures();

        private sealed class Chunk
        {
            public GameObject Go;
            public Texture2D Tex;
            public Color32[] Pixels;
            public int Width, Height;
            public int Solid;   // opaque cells, as of the last refresh
        }

        // The mask currently on screen, whichever source it came from.
        private byte[] _cells;
        private int _cellsWidth, _cellsHeight;
        private float _cellsPerUnit;
        private Vector2 _origin;
        private readonly List<(TerrainTiler.Tile tile, PhysMaterialId material)> _palette = new();
        private readonly Dictionary<Vector2Int, Chunk> _chunks = new();
        private Transform _container;
        private int[] _counts;   // per-chunk palette histogram, reused across refreshes

        public TerrainMap Map => map;

        /// <summary>The region the map covers, in world space.</summary>
        public Rect WorldRect
        {
            get
            {
                Vector2 a = transform.TransformPoint(_origin);
                Vector2 b = transform.TransformPoint(_origin + new Vector2(_cellsWidth, _cellsHeight) / Mathf.Max(1f, _cellsPerUnit));
                return Rect.MinMaxRect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Streaming (play mode)
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Chunks within this many units of the player are built; past it the terrain
        /// is only cells in the map. Well beyond the camera and the fog's sight.</summary>
        public static float StreamRadius = 24f;

        /// <summary>Milliseconds a frame may spend building chunks that came into range.</summary>
        public static float StreamBudgetMs = 2f;

        /// <summary>How far the player moves before what is left is sorted by distance again.</summary>
        public static float ResortDistance = 3f;

        private static readonly List<TerrainBuilder> Streaming = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStreaming() => Streaming.Clear();

        private bool _stream;
        private Vector2 _focus;
        private Rect _mustBuild;
        private Vector2Int[] _queue;    // chunks not built yet, nearest first from _queueAt
        private float[] _keys;          // squared distance at the last sort; -1 when asked for
        private int _queueAt, _queueCount;
        private bool[] _built;          // per chunk
        private bool[] _wanted;         // per chunk: asked for ahead of its turn
        private sbyte[] _rock;          // per chunk: any solid cell in the map? 0 = not looked yet
        private int _cols, _rows;
        private Vector2 _sortedAt;
        private bool _resort;
        private Vector2 _chunkOrigin;   // world position of chunk (0, 0)'s corner
        private KeepInBuiltWorld _keeper;
        private float _chunkWorld;      // a chunk's side in world units

        /// <summary>
        /// Call before the builder wakes, in play mode, to stream the terrain instead of building
        /// all of it. Everything under <paramref name="mustBuild"/> and within
        /// <see cref="StreamRadius"/> of <paramref name="focus"/> (world) is built at once; after
        /// that, whatever comes within that radius of the player, a few chunks a frame. A floor is
        /// ten thousand chunks, and building them all held the first frame up for seconds. Noita
        /// does the same: only the world round the player is ever made real.
        ///
        /// Unbuilt terrain is still in the map, it just has no objects yet. Rooms over it sleep
        /// (<see cref="IsBuilt"/>, <see cref="Request"/>), and standing terrain leans on it
        /// (<see cref="TouchesUnbuilt"/>): it is rock, only not loaded.
        /// </summary>
        public void StreamFrom(Vector2 focus, Rect mustBuild)
        {
            _stream = true;
            _focus = focus;
            _mustBuild = mustBuild;
        }

        /// <summary>Is every chunk under <paramref name="worldRect"/> built?</summary>
        public static bool IsBuilt(Rect worldRect)
        {
            for (int i = Streaming.Count - 1; i >= 0; i--)
            {
                var b = Streaming[i];
                if (!b) { Streaming.RemoveAt(i); continue; }
                if (!b.AreaBuilt(worldRect)) return false;
            }
            return true;
        }

        /// <summary>Build the chunks under <paramref name="worldRect"/> ahead of their turn - a
        /// room the player is about to wake.</summary>
        public static void Request(Rect worldRect)
        {
            foreach (var b in Streaming)
                if (b) b.Want(worldRect);
        }

        /// <summary>
        /// Does <paramref name="worldBounds"/> reach rock that is not built yet? The support pass
        /// counts that as holding a piece up, the way the bedrock does: the unbuilt rock is
        /// there, it just cannot be dug or fall until it is built.
        /// </summary>
        public static bool TouchesUnbuilt(Bounds worldBounds)
        {
            if (Streaming.Count == 0) return false;
            var r = Rect.MinMaxRect(worldBounds.min.x - 0.05f, worldBounds.min.y - 0.05f,
                                    worldBounds.max.x + 0.05f, worldBounds.max.y + 0.05f);
            foreach (var b in Streaming)
                if (b && b.AreaTouchesUnbuiltRock(r)) return true;
            return false;
        }

        private bool ChunkRange(Rect worldRect, out int x0, out int y0, out int x1, out int y1)
        {
            // Standing terrain neither moves nor turns, so this is plain arithmetic - the support
            // pass asks it about every piece on every pass.
            float k = 1f / _chunkWorld;
            x0 = Mathf.Max(0, Mathf.FloorToInt((worldRect.xMin - _chunkOrigin.x) * k));
            x1 = Mathf.Min(_cols - 1, Mathf.FloorToInt((worldRect.xMax - _chunkOrigin.x) * k));
            y0 = Mathf.Max(0, Mathf.FloorToInt((worldRect.yMin - _chunkOrigin.y) * k));
            y1 = Mathf.Min(_rows - 1, Mathf.FloorToInt((worldRect.yMax - _chunkOrigin.y) * k));
            return x0 <= x1 && y0 <= y1;
        }

        /// <summary>Is the ground within half a unit of <paramref name="world"/> built?</summary>
        internal bool IsBuiltAround(Vector2 world) =>
            AreaBuilt(new Rect(world.x - 0.5f, world.y - 0.5f, 1f, 1f));

        private bool AreaBuilt(Rect worldRect)
        {
            if (_built == null || !ChunkRange(worldRect, out int x0, out int y0, out int x1, out int y1))
                return true;
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
                if (!_built[y * _cols + x]) return false;
            return true;
        }

        private bool AreaTouchesUnbuiltRock(Rect worldRect)
        {
            if (_built == null || !ChunkRange(worldRect, out int x0, out int y0, out int x1, out int y1))
                return false;
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
                if (!_built[y * _cols + x] && HasRock(x, y)) return true;
            return false;
        }

        private void Want(Rect worldRect)
        {
            if (_built == null || !ChunkRange(worldRect, out int x0, out int y0, out int x1, out int y1))
                return;
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                int i = y * _cols + x;
                if (_built[i] || _wanted[i]) continue;
                _wanted[i] = true;
                _resort = true;
            }
        }

        /// <summary>Any solid cell in this chunk's part of the map? Looked up once, lazily.</summary>
        private bool HasRock(int cx, int cy)
        {
            int i = cy * _cols + cx;
            if (_rock[i] == 0)
            {
                int px0 = cx * chunkPixels, py0 = cy * chunkPixels;
                int cw = Mathf.Min(chunkPixels, _cellsWidth - px0);
                int chh = Mathf.Min(chunkPixels, _cellsHeight - py0);
                int count = _palette.Count;
                _rock[i] = -1;
                for (int y = 0; y < chh && _rock[i] < 0; y++)
                {
                    int row = (py0 + y) * _cellsWidth + px0;
                    for (int x = 0; x < cw; x++)
                    {
                        int id = _cells[row + x];
                        if (id == 0 || id > count) continue;
                        _rock[i] = 1;
                        break;
                    }
                }
            }
            return _rock[i] > 0;
        }

        private void StartStreaming(int cols, int rows)
        {
            _cols = cols;
            _rows = rows;
            _queueCount = cols * rows;
            _queue = new Vector2Int[_queueCount];
            _keys = new float[_queueCount];
            _built = new bool[_queueCount];
            _wanted = new bool[_queueCount];
            _rock = new sbyte[_queueCount];
            _queueAt = 0;
            _chunkOrigin = transform.TransformPoint(_origin);
            _chunkWorld = Mathf.Max(1e-4f, chunkPixels / CellsPerWorldUnit);
            for (int cy = 0, i = 0; cy < rows; cy++)
            for (int cx = 0; cx < cols; cx++)
                _queue[i++] = new Vector2Int(cx, cy);

            Streaming.Add(this);
            if (_mustBuild.width > 0f && _mustBuild.height > 0f) Want(_mustBuild);

            _sortedAt = transform.InverseTransformPoint(_focus);
            SortQueue(_sortedAt);
            float r2 = StreamRadius * StreamRadius;
            while (_queueAt < _queueCount && _keys[_queueAt] <= r2) BuildNext();
            if (_queueAt >= _queueCount) EndStreaming();
        }

        /// <summary>Order what is left by distance from <paramref name="local"/>, nearest first,
        /// with whatever was asked for ahead of all of it.</summary>
        private void SortQueue(Vector2 local)
        {
            Vector2 f = local - _origin;
            float size = chunkPixels / _cellsPerUnit;
            for (int i = _queueAt; i < _queueCount; i++)
            {
                var c = _queue[i];
                if (_wanted[c.y * _cols + c.x])
                {
                    _keys[i] = -1f;
                    continue;
                }
                float dx = (c.x + 0.5f) * size - f.x, dy = (c.y + 0.5f) * size - f.y;
                _keys[i] = dx * dx + dy * dy;
            }
            System.Array.Sort(_keys, _queue, _queueAt, _queueCount - _queueAt);
        }

        private void BuildNext()
        {
            var c = _queue[_queueAt++];
            int i = c.y * _cols + c.x;
            RefreshChunk(c, rebuildCollider: true);
            _built[i] = true;
            _wanted[i] = false;
        }

        private void Update()
        {
            if (_queue == null) return;
            (_keeper ??= new KeepInBuiltWorld(this)).Tick();

            var player = App.Instance.PlayerTransform;
            Vector2 at = player ? (Vector2)transform.InverseTransformPoint(player.position) : _sortedAt;
            if (_resort || (at - _sortedAt).sqrMagnitude >= ResortDistance * ResortDistance)
            {
                _resort = false;
                _sortedAt = at;
                SortQueue(at);
            }

            // Nothing new in range: the player is standing still, or walking over built ground.
            float r2 = StreamRadius * StreamRadius;
            if (_queueAt >= _queueCount || _keys[_queueAt] > r2) return;

            long deadline = System.Diagnostics.Stopwatch.GetTimestamp() +
                            (long)(StreamBudgetMs * 0.001 * System.Diagnostics.Stopwatch.Frequency);
            do BuildNext();
            while (_queueAt < _queueCount && _keys[_queueAt] <= r2 &&
                   System.Diagnostics.Stopwatch.GetTimestamp() < deadline);

            if (_queueAt >= _queueCount) EndStreaming();
        }

        private void EndStreaming()
        {
            _keeper?.ReleaseAll();
            Streaming.Remove(this);
            _queue = null;
            _keys = null;
            _built = null;
            _wanted = null;
            _rock = null;
            _queueAt = _queueCount = 0;
        }

        private void OnDestroy() => EndStreaming();

        private static readonly ProfilerMarker s_build = new("Terrain.Build");
        private static readonly ProfilerMarker s_fill = new("Terrain.Chunk.Fill");
        private static readonly ProfilerMarker s_object = new("Terrain.Chunk.Object");
        private static readonly ProfilerMarker s_collider = new("Terrain.Chunk.Collider");
        private static readonly ProfilerMarker s_register = new("Terrain.Chunk.Register");

        /// <summary>Mask cells per world unit, accounting for this object's scale.</summary>
        public float CellsPerWorldUnit
        {
            get
            {
                float ppu = map ? map.PixelsPerUnit : Mathf.Max(1f, pixelsPerUnit);
                var s = transform.lossyScale;
                float scale = (Mathf.Abs(s.x) + Mathf.Abs(s.y)) * 0.5f;
                return scale > 1e-5f ? ppu / scale : ppu;
            }
        }

        private void Awake()
        {
            if (buildOnAwake) Build();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Authoring API (used by the Terrain Painter)
        // ─────────────────────────────────────────────────────────────────────────

        public void SetMap(TerrainMap value)
        {
            map = value;
        }

        /// <summary>Cell under a world point. Coordinates are written even when the point falls
        /// outside the map, so a brush straddling the edge can clamp and paint the rest.</summary>
        public bool WorldToCell(Vector3 world, out int px, out int py)
        {
            px = py = 0;
            if (!map) return false;
            return map.LocalToPixel(transform.InverseTransformPoint(world), out px, out py);
        }

        public Vector3 CellToWorld(int px, int py) =>
            map ? transform.TransformPoint(map.PixelToLocal(px, py)) : transform.position;

        /// <summary>
        /// Rebuild only the chunks covering <paramref name="cells"/> after the map was edited.
        /// Chunks that just became empty are dropped and ones that just became solid appear.
        /// Collider retracing is the expensive half, so a paint stroke can skip it until the
        /// mouse comes up.
        /// </summary>
        public void RefreshArea(RectInt cells, bool rebuildColliders)
        {
            if (!SyncSource()) { Build(); return; }

            // RectInt max bounds are exclusive.
            int x0 = Mathf.Clamp(cells.xMin, 0, _cellsWidth - 1);
            int x1 = Mathf.Clamp(cells.xMax - 1, 0, _cellsWidth - 1);
            int y0 = Mathf.Clamp(cells.yMin, 0, _cellsHeight - 1);
            int y1 = Mathf.Clamp(cells.yMax - 1, 0, _cellsHeight - 1);
            if (x1 < x0 || y1 < y0) return;

            for (int cy = y0 / chunkPixels; cy <= y1 / chunkPixels; cy++)
            for (int cx = x0 / chunkPixels; cx <= x1 / chunkPixels; cx++)
                RefreshChunk(new Vector2Int(cx, cy), rebuildColliders);
        }

        /// <summary>Stamp the procedural features into the assigned map, so painting can start
        /// from the generated layout instead of an empty canvas.</summary>
        public void BakeFeaturesIntoMap()
        {
            if (!map || features == null) return;

            var cells = map.Cells;
            foreach (var feature in features)
                Stamp(feature, map.LocalBounds, map.PixelsPerUnit, map.Width, map.Height, cells,
                      stratum => (byte)map.Require(stratum.tile, stratum.physMaterial));
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Build
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// True when this component lives in an open scene, which is the only place it can put
        /// the objects it generates. On a prefab asset Unity refuses the reparent, the container
        /// is left loose at the root of whatever scene happens to be open, and every build leaks
        /// another one — complete with colliders that nothing will ever update again.
        /// </summary>
        public bool CanGenerate => gameObject.scene.IsValid();

        [ContextMenu("Rebuild")]
        public void Build()
        {
            if (!CanGenerate)
            {
                Debug.LogWarning(
                    "TerrainBuilder: this is the prefab asset, not an object in the scene — " +
                    "nothing was built. Drag the prefab into the scene and work on that.", this);
                return;
            }

            using var _ = s_build.Auto();
            chunkPixels = Mathf.Max(8, chunkPixels);
            ApplyBedrockMask();
            ResetContainer();

            _palette.Clear();
            if (map) LoadFromMap();
            else if (!GenerateFromFeatures()) return;

            int cols = (_cellsWidth + chunkPixels - 1) / chunkPixels;
            int rows = (_cellsHeight + chunkPixels - 1) / chunkPixels;
            EndStreaming();
            if (_stream && Application.isPlaying) StartStreaming(cols, rows);
            else
                for (int cy = 0; cy < rows; cy++)
                for (int cx = 0; cx < cols; cx++)
                    RefreshChunk(new Vector2Int(cx, cy), rebuildCollider: true);
        }

        private void LoadFromMap()
        {
            _cells = map.Cells;
            _cellsWidth = map.Width;
            _cellsHeight = map.Height;
            _cellsPerUnit = map.PixelsPerUnit;
            _origin = map.Origin;
            SyncPalette();
        }

        /// <summary>
        /// Re-point the cached mask at the map's current buffer and pick up palette entries added
        /// since the last build. Painting appends to the palette as new tiles are used, and an undo
        /// replaces the cell array outright — without this, an incremental refresh would either
        /// ignore the new tile or patch a buffer nobody is editing anymore.
        /// Returns false when the map changed shape and only a full <see cref="Build"/> will do.
        /// </summary>
        private bool SyncSource()
        {
            if (_cells == null || !_container) return false;
            if (!map) return true;
            if (map.Width != _cellsWidth || map.Height != _cellsHeight) return false;
            if (!Mathf.Approximately(map.PixelsPerUnit, _cellsPerUnit)) return false;

            _cells = map.Cells;
            SyncPalette();
            return true;
        }

        private void SyncPalette()
        {
            var entries = map.Palette;
            for (int i = _palette.Count; i < entries.Count; i++)
                _palette.Add((TerrainTiler.Load(entries[i].tile), entries[i].physMaterial));
        }

        private bool GenerateFromFeatures()
        {
            // Scene YAML written without these fields still has to produce a map.
            if (features == null || features.Length == 0) features = DefaultFeatures();
            if (pixelsPerUnit <= 0f) pixelsPerUnit = 40f;

            var region = FeatureRegion();
            int w = Mathf.CeilToInt(region.width * pixelsPerUnit);
            int h = Mathf.CeilToInt(region.height * pixelsPerUnit);
            if (w <= 0 || h <= 0) return false;
            if ((long)w * h > 8_000_000L)
            {
                Debug.LogError($"TerrainBuilder: {w}x{h} cells is too much terrain — lower " +
                               "pixelsPerUnit or shrink the features.");
                return false;
            }

            _cells = new byte[w * h];
            _cellsWidth = w;
            _cellsHeight = h;
            _cellsPerUnit = pixelsPerUnit;
            _origin = region.min;

            foreach (var feature in features)
                Stamp(feature, region, pixelsPerUnit, w, h, _cells, RequireFeatureStratum);

            return true;
        }

        /// <summary>Palette slot for a stratum on the procedural path, where entries hold the
        /// loaded tile rather than its name.</summary>
        private byte RequireFeatureStratum(TerrainStratum stratum)
        {
            var tile = TerrainTiler.Load(stratum.tile);
            for (int i = 0; i < _palette.Count; i++)
                if (_palette[i].tile == tile && _palette[i].material == stratum.physMaterial)
                    return (byte)(i + 1);

            if (_palette.Count >= 254)
            {
                Debug.LogError("TerrainBuilder: more than 254 tile/material combinations.");
                return (byte)_palette.Count;
            }

            _palette.Add((tile, stratum.physMaterial));
            return (byte)_palette.Count;
        }

        private void ApplyBedrockMask()
        {
            int mask = 0;
            if (bedrockLayers == null) return;

            foreach (var name in bedrockLayers)
            {
                if (string.IsNullOrEmpty(name)) continue;
                int layer = LayerMask.NameToLayer(name);
                if (layer >= 0) mask |= 1 << layer;
            }
            if (mask != 0) TerrainSupportSystem.BedrockMask = mask;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Mask stamping (procedural features)
        // ─────────────────────────────────────────────────────────────────────────

        private Rect FeatureRegion()
        {
            Vector2 min = features[0].min;
            Vector2 max = features[0].max;
            foreach (var f in features)
            {
                min = Vector2.Min(min, f.min);
                max = Vector2.Max(max, f.max);
                if (f.shape == TerrainShape.Heightfield)
                    max.y = Mathf.Max(max.y, f.min.y + f.surfaceMean + f.surfaceAmplitude + 0.1f);
            }
            return new Rect(min, max - min);
        }

        private static void Stamp(TerrainFeature f, Rect region, float ppu, int w, int h,
                                  byte[] cells, System.Func<TerrainStratum, byte> idFor)
        {
            if (f == null) return;
            if (f.strata == null || f.strata.Length == 0)
                f.strata = new[] { new TerrainStratum() };

            var ids = new byte[f.strata.Length];
            for (int i = 0; i < f.strata.Length; i++) ids[i] = idFor(f.strata[i]);

            int x0 = Mathf.Clamp(Mathf.FloorToInt((f.min.x - region.xMin) * ppu), 0, w - 1);
            int x1 = Mathf.Clamp(Mathf.CeilToInt((f.max.x - region.xMin) * ppu), 0, w - 1);
            int y0 = Mathf.Clamp(Mathf.FloorToInt((f.min.y - region.yMin) * ppu), 0, h - 1);
            int y1 = Mathf.Clamp(Mathf.CeilToInt((f.max.y - region.yMin) * ppu), 0, h - 1);

            for (int px = x0; px <= x1; px++)
            {
                float wx = region.xMin + (px + 0.5f) / ppu;

                // Noise is expensive; the surface line only depends on x.
                float surface = f.shape == TerrainShape.Heightfield
                    ? f.min.y + SurfaceHeight(f, wx)
                    : 0f;

                // Strata are measured from the top of this column, so a grass cap follows the
                // shape of whatever it sits on instead of cutting straight across.
                int top = -1;
                for (int py = y1; py >= y0; py--)
                {
                    if (!IsSolid(f, wx, region.yMin + (py + 0.5f) / ppu, surface)) continue;
                    top = py;
                    break;
                }
                if (top < 0) continue;

                for (int py = y0; py <= top; py++)
                {
                    float wy = region.yMin + (py + 0.5f) / ppu;
                    if (!IsSolid(f, wx, wy, surface)) continue;
                    cells[py * w + px] = ids[StratumAt(f, (top - py) / ppu)];
                }
            }
        }

        private static int StratumAt(TerrainFeature f, float depth)
        {
            float reached = 0f;
            for (int i = 0; i < f.strata.Length - 1; i++)
            {
                float t = f.strata[i].thickness;
                if (t <= 0f) return i;          // an explicit "fills the rest"
                reached += t;
                if (depth < reached) return i;
            }
            return f.strata.Length - 1;
        }

        private static bool IsSolid(TerrainFeature f, float wx, float wy, float surface)
        {
            if (wx < f.min.x || wx > f.max.x || wy < f.min.y || wy > f.max.y) return false;

            switch (f.shape)
            {
                case TerrainShape.Box:
                    return true;

                case TerrainShape.Ellipse:
                {
                    Vector2 c = (f.min + f.max) * 0.5f;
                    Vector2 rad = (f.max - f.min) * 0.5f;
                    if (rad.x <= 0f || rad.y <= 0f) return false;
                    float nx = (wx - c.x) / rad.x;
                    float ny = (wy - c.y) / rad.y;
                    float limit = 1f + f.edgeNoise *
                        (Mathf.PerlinNoise(wx * 0.9f + f.noiseSeed, wy * 0.9f + f.noiseSeed) - 0.5f) * 2f;
                    return nx * nx + ny * ny <= Mathf.Max(0.05f, limit);
                }

                default:
                    return wy <= surface;
            }
        }

        /// <summary>Three octaves of value noise — enough for a ridge line that reads as rock.</summary>
        private static float SurfaceHeight(TerrainFeature f, float wx)
        {
            float sum = 0f, amp = 1f, norm = 0f, freq = Mathf.Max(0.001f, f.surfaceFrequency);
            for (int octave = 0; octave < 3; octave++)
            {
                sum += amp * (Mathf.PerlinNoise((wx + f.noiseSeed) * freq,
                                                f.noiseSeed * 0.37f + octave * 3.13f) - 0.5f) * 2f;
                norm += amp;
                amp *= 0.5f;
                freq *= 2.3f;
            }
            return f.surfaceMean + f.surfaceAmplitude * (sum / norm);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Chunks
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Bring one chunk in line with the mask: create it, drop it, or repaint it.</summary>
        private void RefreshChunk(Vector2Int coord, bool rebuildCollider)
        {
            int px0 = coord.x * chunkPixels;
            int py0 = coord.y * chunkPixels;
            if (px0 < 0 || py0 < 0 || px0 >= _cellsWidth || py0 >= _cellsHeight) return;

            int cw = Mathf.Min(chunkPixels, _cellsWidth - px0);
            int chh = Mathf.Min(chunkPixels, _cellsHeight - py0);

            if (_counts == null || _counts.Length < _palette.Count + 1)
                _counts = new int[_palette.Count + 1];
            else
                System.Array.Clear(_counts, 0, _counts.Length);

            // Counted a run at a time: a chunk is mostly a few long runs of one id.
            int solid = 0, dominant = 0, dominantCount = 0, paletteCount = _palette.Count;
            for (int y = 0; y < chh; y++)
            {
                int row = (py0 + y) * _cellsWidth + px0;
                int x = 0;
                while (x < cw)
                {
                    byte id = _cells[row + x];
                    int end = x + 1;
                    while (end < cw && _cells[row + end] == id) end++;
                    int run = end - x;
                    x = end;

                    if (id == 0 || id > paletteCount) continue;
                    solid += run;
                    if ((_counts[id] += run) <= dominantCount) continue;
                    dominantCount = _counts[id];
                    dominant = id;
                }
            }

            _chunks.TryGetValue(coord, out var chunk);

            if (solid < minChunkPixels || dominant == 0)
            {
                if (chunk == null) return;
                _chunks.Remove(coord);
                DestroyChunk(chunk);
                return;
            }

            if (chunk == null)
            {
                // Creating a chunk fills and uploads its texture on the way in — the collider
                // is traced from those pixels, so they can't be left undefined.
                chunk = CreateChunk(coord, px0, py0, cw, chh, solid);
                _chunks[coord] = chunk;
                rebuildCollider = true;
            }
            else
            {
                FillChunk(chunk, px0, py0);
                chunk.Tex.SetPixels32(chunk.Pixels);
                chunk.Tex.Apply(false, false);
            }

            // Collider first. Tagging the material can now attach components of its own, and a
            // chunk that never gets traced is a chunk the support pass cannot find a contact
            // for — which it reads as unsupported and drops.
            chunk.Solid = solid;
            if (rebuildCollider)
            {
                s_collider.Begin();
                RetraceCollider(chunk);
                s_collider.End();
            }
            MaterialView.Apply(chunk.Go, _palette[dominant - 1].material);
        }

        private void FillChunk(Chunk chunk, int px0, int py0)
        {
            using var _ = s_fill.Auto();
            var pixels = chunk.Pixels;
            int count = _palette.Count;
            int w = chunk.Width;
            for (int y = 0; y < chunk.Height; y++)
            {
                int row = (py0 + y) * _cellsWidth + px0;
                int dst = y * w;
                int gy = py0 + y;

                // Cells come in long runs of one id: each run is one block copy out of its tile.
                int x = 0;
                while (x < w)
                {
                    int id = _cells[row + x];
                    int end = x + 1;
                    while (end < w && _cells[row + end] == id) end++;

                    if (id == 0 || id > count) System.Array.Clear(pixels, dst + x, end - x);
                    else _palette[id - 1].tile.CopyRun(pixels, dst + x, px0 + x, gy, end - x);
                    x = end;
                }
            }
        }

        private Chunk CreateChunk(Vector2Int coord, int px0, int py0, int cw, int chh, int solid)
        {
            var tex = new Texture2D(cw, chh, TextureFormat.ARGB32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,

                // The texture has to carry the same flags as the object that renders it.
                // Without them the editor unloads it as an unused asset — on a script reload,
                // a scene save, the way into play mode — and leaves a chunk that still has its
                // collider but draws nothing at all.
                hideFlags = GeneratedHideFlags,
            };

            var chunk = new Chunk
            {
                Tex = tex,
                Pixels = new Color32[cw * chh],
                Width = cw,
                Height = chh,
            };

            FillChunk(chunk, px0, py0);

            s_object.Begin();
            tex.SetPixels32(chunk.Pixels);
            tex.Apply(false, false);

            var sprite = MakeSprite(tex, cw, chh, $"Chunk_{coord.x}_{coord.y}");
            sprite.hideFlags = GeneratedHideFlags;

            var go = new GameObject(sprite.name) { hideFlags = GeneratedHideFlags };
            chunk.Go = go;
            go.layer = gameObject.layer;
            go.transform.SetParent(_container, false);
            go.transform.localPosition = new Vector3(
                _origin.x + (px0 + cw * 0.5f) / _cellsPerUnit,
                _origin.y + (py0 + chh * 0.5f) / _cellsPerUnit,
                0f);

            // Body and collider before the renderer: a PolygonCollider2D added next to a sprite
            // traces an outline of it straight away, only to be replaced by RetraceCollider.
            var rb = go.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;
            go.AddComponent<PolygonCollider2D>();

            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = sortingOrder;
            s_object.End();

            if (Application.isPlaying)
            {
                // Hand the pixel tools the buffer we already have, instead of letting them
                // clone the texture the first time someone digs into this chunk.
                s_register.Begin();
                PixelSpriteRegistry.Instance.Adopt(go, tex, chunk.Pixels, solid);
                TerrainBody.Apply(go);
                s_register.End();
            }
            else
            {
                // Preview only: still tag it so the inspector shows what it would be.
                go.AddComponent<TerrainBody>();
            }

            return chunk;
        }

        /// <summary>
        /// A chunk's sprite, built over the whole texture rect. The mesh has to be
        /// <see cref="SpriteMeshType.FullRect"/>: a tight mesh is cut from the alpha the texture
        /// had when the sprite was made, so a chunk that is painted into later would keep
        /// rendering its original blob and drop everything added since.
        /// </summary>
        private Sprite MakeSprite(Texture2D tex, int cw, int chh, string name)
        {
            // No fallback physics shape: Unity would trace one from the alpha of every chunk,
            // and the collider is traced from the cells here anyway.
            var sprite = Sprite.Create(tex, new Rect(0, 0, cw, chh), new Vector2(0.5f, 0.5f),
                                       _cellsPerUnit, 0, SpriteMeshType.FullRect, Vector4.zero,
                                       generateFallbackPhysicsShape: false);
            sprite.name = name;
            sprite.hideFlags = GeneratedHideFlags;
            return sprite;
        }

        /// <summary>Re-trace the collider from the current pixels and re-derive mass.</summary>
        private void RetraceCollider(Chunk chunk)
        {
            var pivot = new Vector2(chunk.Width * 0.5f, chunk.Height * 0.5f);

            // Solid right through - most of a floor, the rock between rooms - is a rectangle,
            // and the cell count already says so without looking at a pixel.
            if (chunk.Solid == chunk.Width * chunk.Height)
            {
                PixelContour.ApplyRect(chunk.Go, chunk.Width, chunk.Height, _cellsPerUnit, pivot);
                return;
            }

            // Outlines come from the cell mask, not from Unity's sprite tracing — that runs at
            // a tolerance nobody controls and cuts corners across whole cells of solid ground.
            PixelContour.ApplyCollider(chunk.Go, chunk.Pixels, chunk.Width, chunk.Height,
                                       _cellsPerUnit,
                                       new Vector2(chunk.Width * 0.5f, chunk.Height * 0.5f),
                                       simplifyLevel);
        }

        private static void DestroyChunk(Chunk chunk)
        {
            var sprite = chunk.Go ? chunk.Go.GetComponent<SpriteRenderer>()?.sprite : null;

            if (chunk.Go) Kill(chunk.Go);
            if (sprite) Kill(sprite);
            if (chunk.Tex) Kill(chunk.Tex);
        }

        private static void Kill(Object o)
        {
            if (Application.isPlaying) Destroy(o);
            else DestroyImmediate(o);
        }

        /// <summary>
        /// Throw the generated chunks away. The editor calls this on the way into play mode:
        /// the preview objects are <see cref="HideFlags.DontSave"/>, which in Unity also means
        /// they survive the scene swap — but the textures they render do not, so left alone they
        /// come back as colliders with nothing drawn on them.
        /// </summary>
        public void ClearPreview()
        {
            foreach (var chunk in _chunks.Values) DestroyChunk(chunk);
            _chunks.Clear();

            // Sweep every container by name instead of trusting the cached reference or
            // Find(), which only ever returns the first match. The dictionary and the field
            // are wiped by a domain reload while the objects themselves live on, a resized map
            // leaves chunks of the old geometry behind, and a runtime Destroy does not take
            // effect until the end of the frame — so more than one of these can exist at once,
            // and anything missed is a chunk with a collider that nobody will ever update again.
            for (int i = transform.childCount - 1; i >= 0; i--)
            {
                var child = transform.GetChild(i);
                if (child.name == ContainerName) Kill(child.gameObject);
            }

            _container = null;
            _cells = null;   // forces a full rebuild rather than a patch of a dead view
        }

        private void ResetContainer()
        {
            ClearPreview();

            var holder = new GameObject(ContainerName) { hideFlags = GeneratedHideFlags };
            holder.layer = gameObject.layer;
            holder.transform.SetParent(transform, false);
            _container = holder.transform;
        }

        private const string ContainerName = "Chunks";

        /// <summary>
        /// Chunks live on textures that aren't assets, so a preview built from the inspector must
        /// not end up in the saved scene. In play mode they're plain objects.
        ///
        /// Deliberately not <see cref="HideFlags.DontSave"/>: that is these two flags plus
        /// <see cref="HideFlags.DontUnloadUnusedAsset"/>, and the extra one makes a GameObject
        /// survive a scene load — including the swap into play mode, where it comes back as a
        /// chunk whose texture did not survive with it. It also keeps the objects out of the
        /// Hierarchy, which means a straggler is invisible and cannot be deleted by hand.
        /// </summary>
        private static HideFlags GeneratedHideFlags =>
            Application.isPlaying
                ? HideFlags.None
                : HideFlags.DontSaveInEditor | HideFlags.DontSaveInBuild;

        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// The procedural sandbox layout, used when no map is assigned — and a decent starting
        /// point to bake into one: a layered ground bed across the play area, a brick tower rooted
        /// in it, a rock island held up by one thin pillar (dig the pillar out and the island comes
        /// down), and a wooden shelf off the left wall that can simply be set on fire.
        /// </summary>
        private static TerrainFeature[] DefaultFeatures() => new[]
        {
            // Painted first so the ground bed buries its lower half.
            new TerrainFeature
            {
                label = "island-pillar",
                shape = TerrainShape.Box,
                min = new Vector2(12.5f, -3.0f),
                max = new Vector2(13.5f, -0.2f),
                strata = new[] { new TerrainStratum { tile = "rock_hard" } },
            },
            new TerrainFeature
            {
                label = "ground",
                shape = TerrainShape.Heightfield,
                // Overlaps the floor and both side walls, which is what makes it bedrock.
                min = new Vector2(-14.6f, -4.35f),
                max = new Vector2(19.9f, -1.2f),
                surfaceMean = 2.35f,
                surfaceAmplitude = 0.55f,
                surfaceFrequency = 0.14f,
                noiseSeed = 11.3f,
                strata = new[]
                {
                    new TerrainStratum { tile = "soil_lush", thickness = 0.3f },
                    new TerrainStratum { tile = "soil", thickness = 0.9f },
                    new TerrainStratum { tile = "rock" },
                },
            },
            new TerrainFeature
            {
                label = "temple-tower",
                shape = TerrainShape.Box,
                min = new Vector2(3.6f, -3.0f),
                max = new Vector2(6.0f, 2.4f),
                strata = new[] { new TerrainStratum { tile = "templebrick" } },
            },
            new TerrainFeature
            {
                label = "island",
                shape = TerrainShape.Ellipse,
                min = new Vector2(8.7f, -0.6f),
                max = new Vector2(17.3f, 1.7f),
                edgeNoise = 0.28f,
                noiseSeed = 4.7f,
                strata = new[]
                {
                    new TerrainStratum { tile = "soil_lush", thickness = 0.28f },
                    new TerrainStratum { tile = "rock" },
                },
            },
            // A ledge of ice with air under it, held up only by the tower it grows out of.
            // It is the fracture model's test rig: a round into it opens a split you can watch
            // run, and whichever side of the split stops reaching the tower comes down.
            //
            // It reaches well inside the tower rather than just meeting its face. Support is
            // measured between the chunks' traced colliders, and those are simplified inwards,
            // so a join only a few cells wide is not a join by the time the support pass looks
            // at it — the ledge then reads as unsupported and scatters chunk by chunk the
            // moment play starts, before anything has touched it.
            new TerrainFeature
            {
                label = "ice-ledge",
                shape = TerrainShape.Box,
                min = new Vector2(1.1f, 1.55f),
                max = new Vector2(4.5f, 2.15f),
                strata = new[]
                {
                    new TerrainStratum { tile = "ice", physMaterial = PhysMaterialId.Ice },
                },
            },
            new TerrainFeature
            {
                label = "wood-shelf",
                shape = TerrainShape.Box,
                min = new Vector2(-14.6f, 0.15f),
                max = new Vector2(-8.2f, 0.8f),
                strata = new[]
                {
                    new TerrainStratum { tile = "wood", physMaterial = PhysMaterialId.Wood },
                },
            },
        };
    }
}
