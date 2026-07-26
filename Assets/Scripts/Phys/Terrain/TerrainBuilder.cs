using System.Collections.Generic;
using Materials;
using Phys.Pixels;
using Spawners;
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

        [ContextMenu("Rebuild")]
        public void Build()
        {
            chunkPixels = Mathf.Max(8, chunkPixels);
            ApplyBedrockMask();
            ResetContainer();

            _palette.Clear();
            if (map) LoadFromMap();
            else if (!GenerateFromFeatures()) return;

            int cols = (_cellsWidth + chunkPixels - 1) / chunkPixels;
            int rows = (_cellsHeight + chunkPixels - 1) / chunkPixels;
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

            int solid = 0, dominant = 0, dominantCount = 0;
            for (int y = 0; y < chh; y++)
            {
                int row = (py0 + y) * _cellsWidth + px0;
                for (int x = 0; x < cw; x++)
                {
                    byte id = _cells[row + x];
                    if (id == 0 || id > _palette.Count) continue;
                    solid++;
                    if (++_counts[id] <= dominantCount) continue;
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
                // Creating a chunk fills and uploads its texture on the way in — the sprite's
                // outline is generated from those pixels, so they can't be left undefined.
                chunk = CreateChunk(coord, px0, py0, cw, chh);
                _chunks[coord] = chunk;
                rebuildCollider = true;
            }
            else
            {
                FillChunk(chunk, px0, py0);
                chunk.Tex.SetPixels32(chunk.Pixels);
                chunk.Tex.Apply(false, false);
            }

            MaterialView.Apply(chunk.Go, _palette[dominant - 1].material);
            if (rebuildCollider) RetraceCollider(chunk.Go);
        }

        private void FillChunk(Chunk chunk, int px0, int py0)
        {
            var pixels = chunk.Pixels;
            for (int y = 0; y < chunk.Height; y++)
            {
                int row = (py0 + y) * _cellsWidth + px0;
                int dst = y * chunk.Width;
                for (int x = 0; x < chunk.Width; x++)
                {
                    byte id = _cells[row + x];
                    pixels[dst + x] = id == 0 || id > _palette.Count
                        ? default
                        : _palette[id - 1].tile.Sample(px0 + x, py0 + y);
                }
            }
        }

        private Chunk CreateChunk(Vector2Int coord, int px0, int py0, int cw, int chh)
        {
            var tex = new Texture2D(cw, chh, TextureFormat.ARGB32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
            };

            var chunk = new Chunk
            {
                Tex = tex,
                Pixels = new Color32[cw * chh],
                Width = cw,
                Height = chh,
            };

            FillChunk(chunk, px0, py0);
            tex.SetPixels32(chunk.Pixels);
            tex.Apply(false, false);

            var sprite = Sprite.Create(tex, new Rect(0, 0, cw, chh),
                                       new Vector2(0.5f, 0.5f), _cellsPerUnit);
            sprite.name = $"Chunk_{coord.x}_{coord.y}";

            var go = new GameObject(sprite.name) { hideFlags = GeneratedHideFlags };
            chunk.Go = go;
            go.layer = gameObject.layer;
            go.transform.SetParent(_container, false);
            go.transform.localPosition = new Vector3(
                _origin.x + (px0 + cw * 0.5f) / _cellsPerUnit,
                _origin.y + (py0 + chh * 0.5f) / _cellsPerUnit,
                0f);

            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = sortingOrder;

            var rb = go.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;

            if (Application.isPlaying)
            {
                // Hand the pixel tools the buffer we already have, instead of letting them
                // clone the texture the first time someone digs into this chunk.
                PixelSpriteRegistry.Instance.Adopt(go, tex, chunk.Pixels);
                TerrainBody.Apply(go);
            }
            else
            {
                // Preview only: still tag it so the inspector shows what it would be.
                go.AddComponent<TerrainBody>();
            }

            return chunk;
        }

        /// <summary>Re-trace the collider from the current pixels and re-derive mass.</summary>
        private void RetraceCollider(GameObject go)
        {
            var existing = go.GetComponent<PolygonCollider2D>();
            if (existing) DestroyImmediate(existing);

            // PolygonCollider2D traces the sprite's alpha on the way in.
            var poly = go.AddComponent<PolygonCollider2D>();
            ColliderSimplifier2D.Simplify(poly, simplifyLevel);
            MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
        }

        private static void DestroyChunk(Chunk chunk)
        {
            if (chunk.Go)
            {
                if (Application.isPlaying) Destroy(chunk.Go);
                else DestroyImmediate(chunk.Go);
            }
            if (chunk.Tex)
            {
                if (Application.isPlaying) Destroy(chunk.Tex);
                else DestroyImmediate(chunk.Tex);
            }
        }

        private void ResetContainer()
        {
            _chunks.Clear();

            var existing = _container ? _container : transform.Find(ContainerName);
            if (existing)
            {
                if (Application.isPlaying) Destroy(existing.gameObject);
                else DestroyImmediate(existing.gameObject);
            }

            var holder = new GameObject(ContainerName) { hideFlags = GeneratedHideFlags };
            holder.layer = gameObject.layer;
            holder.transform.SetParent(transform, false);
            _container = holder.transform;
        }

        private const string ContainerName = "Chunks";

        /// <summary>
        /// Chunks live on textures that aren't assets, so a preview built from the inspector must
        /// not end up in the saved scene. In play mode they're plain objects — DontSave would
        /// also make them survive a scene load, which is not wanted.
        /// </summary>
        private static HideFlags GeneratedHideFlags =>
            Application.isPlaying ? HideFlags.None : HideFlags.DontSave;

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
