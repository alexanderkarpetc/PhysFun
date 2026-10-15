using System.Collections.Generic;
using Phys.Fire;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;
using Unity.Profiling;
using UnityEngine;
using Vision;

namespace Lighting
{
    /// <summary>
    /// Light and dark over the world, the way Starbound and Terraria do it: a grid of light
    /// cells over the view, every light spread out from where it is round the terrain
    /// (<see cref="LightSpreadJob"/>), summed on top of a dim ambient, and the result laid over
    /// everything as a 2x multiply - darker than the art where nothing reaches, the art as
    /// drawn at half strength, warmer and brighter than it next to a lamp.
    ///
    /// Lights are <see cref="LightSource2D"/>s, the light the player carries, fire
    /// (<see cref="FlameField"/>, gathered into a light per patch of flames) and short
    /// <see cref="Flash"/>es - explosions. Terrain stops light by the same pixels that stop
    /// sight: the fog's <see cref="TerrainSight"/> map, which the fog keeps painted far enough
    /// out for the light too (<see cref="FogOfWar.LightPrepareRadius"/>).
    ///
    /// The jobs are scheduled after the fog's, once the sight map is up to date for the frame,
    /// and collected at the start of the next, before anything writes the map again; the light
    /// on screen is one frame old, like the fog.
    ///
    /// F4 turns it off and on.
    /// </summary>
    [DefaultExecutionOrder(1210)]
    public sealed class LightField : MonoBehaviour
    {
        public static bool Enabled = true;
        public static KeyCode ToggleKey = KeyCode.F4;

        /// <summary>Side of a light cell, world units (4 art pixels).</summary>
        public static float CellSize = 0.2f;

        /// <summary>Light everywhere, lit or not, as a multiplier on the art (the colour space is
        /// linear, so 0.17 reads a good deal brighter than 17%).</summary>
        public static Color Ambient = new(0.17f, 0.17f, 0.22f, 1f);

        /// <summary>Brightest the art is drawn, as a multiplier.</summary>
        public static float MaxLight = 2f;

        /// <summary>A cell of rock costs this much more than a cell of air to light through:
        /// light reaches 1/(1+WallCost) as far into a wall as across a room.</summary>
        public static float WallCost = 7f;

        /// <summary>No light reaches further than this, whatever it says.</summary>
        public static float MaxRadius = 10f;

        /// <summary>Lights spread per frame; past this the dimmest and furthest are left out.</summary>
        public static int MaxLights = 64;

        /// <summary>Over the world, under the fog (1000).</summary>
        public static int SortingOrder = 990;

        public static float ArtPixelsPerUnit = 20f;

        // The light the player carries.
        public static Color PlayerColor = new(1f, 0.9f, 0.76f, 1f);
        public static float PlayerIntensity = 0.8f;
        public static float PlayerRadius = 5.5f;
        public static Vector2 PlayerOffset = new(0f, 0.5f);

        public static Color FireColor = new(1f, 0.52f, 0.2f, 1f);
        /// <summary>Flames are gathered into one light per square this big.</summary>
        public static float FireBin = 0.75f;

        private static LightField _instance;

        private struct FlashLight
        {
            public Vector2 At;
            public Color Color;
            public float Intensity, Radius, Start, Seconds;
        }

        private struct Candidate
        {
            public Vector2 At;
            public Color Color;
            public float Intensity, Radius, Score;
        }

        private static readonly List<FlashLight> Flashes = new();
        private readonly List<Candidate> _candidates = new();
        private readonly Dictionary<long, Vector3> _fireBins = new();   // x, y summed, z count

        private NativeArray<float> _opacity, _reach;
        private NativeArray<float4> _lights, _colors;
        private NativeArray<byte> _noSolid;
        private int _stride;

        private JobHandle _jobs;
        private bool _pending;
        private Vector2 _pendingOrigin, _pendingSize;

        private Mesh _quad;
        private Material _mat;
        private MeshRenderer _renderer;
        private Texture2D _tex;
        private Camera _cam;

        private static readonly int OriginId = Shader.PropertyToID("_Origin");
        private static readonly int SizeId = Shader.PropertyToID("_Size");
        private static readonly int ArtPpuId = Shader.PropertyToID("_ArtPPU");

        private static readonly ProfilerMarker s_schedule = new("Light.Schedule");
        private static readonly ProfilerMarker s_finish = new("Light.Finish");

        /// <summary>
        /// A light that flares and dies away - an explosion, a muzzle flash. It does not move.
        /// </summary>
        public static void Flash(Vector2 at, Color color, float intensity, float radius, float seconds)
        {
            if (seconds <= 0f || intensity <= 0f) return;
            Flashes.Add(new FlashLight
            {
                At = at, Color = color, Intensity = intensity, Radius = radius,
                Start = Time.time, Seconds = seconds,
            });
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            foreach (var stale in Resources.FindObjectsOfTypeAll<LightField>())
                if (stale) Destroy(stale.gameObject);
            _instance = null;
            Flashes.Clear();

            var go = new GameObject("~LightField") { hideFlags = HideFlags.HideInHierarchy };
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<LightField>();
        }

        private void Awake()
        {
            _quad = new Mesh { name = "LightQuad", hideFlags = HideFlags.HideAndDontSave };
            _quad.SetVertices(new[]
            {
                new Vector3(0f, 0f, 0f), new Vector3(1f, 0f, 0f),
                new Vector3(1f, 1f, 0f), new Vector3(0f, 1f, 0f),
            });
            _quad.SetTriangles(new[] { 0, 2, 1, 0, 3, 2 }, 0);
            _quad.bounds = new Bounds(new Vector3(0.5f, 0.5f, 0f), new Vector3(1f, 1f, 1f));

            var shader = Resources.Load<Shader>("Shaders/LightMap");
            _mat = new Material(shader ? shader : Shader.Find("Sprites/Default"))
            {
                hideFlags = HideFlags.HideAndDontSave,
            };

            gameObject.AddComponent<MeshFilter>().sharedMesh = _quad;
            _renderer = gameObject.AddComponent<MeshRenderer>();
            _renderer.sharedMaterial = _mat;
            _renderer.sortingOrder = SortingOrder;
            _renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _renderer.receiveShadows = false;
            _renderer.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
            _renderer.enabled = false;

            _noSolid = new NativeArray<byte>(1, Allocator.Persistent);
        }

        private void OnDestroy()
        {
            _jobs.Complete();
            if (_instance == this) _instance = null;
            if (_opacity.IsCreated) _opacity.Dispose();
            if (_reach.IsCreated) _reach.Dispose();
            if (_lights.IsCreated) _lights.Dispose();
            if (_colors.IsCreated) _colors.Dispose();
            if (_noSolid.IsCreated) _noSolid.Dispose();
            if (_quad) Destroy(_quad);
            if (_mat) Destroy(_mat);
            if (_tex) Destroy(_tex);
        }

        private void Update()
        {
            if (Input.GetKeyDown(ToggleKey)) Enabled = !Enabled;

            // Before any LateUpdate: the fog repaints the sight map there, and these jobs read it.
            Finish();
        }

        private void Finish()
        {
            if (!_pending) return;
            using var _ = s_finish.Auto();

            _jobs.Complete();
            _pending = false;
            _tex.Apply(false, false);

            transform.position = new Vector3(_pendingOrigin.x, _pendingOrigin.y, 0f);
            transform.localScale = new Vector3(_pendingSize.x, _pendingSize.y, 1f);
            _mat.mainTexture = _tex;
            _mat.SetVector(OriginId, _pendingOrigin);
            _mat.SetVector(SizeId, _pendingSize);
            _mat.SetFloat(ArtPpuId, ArtPixelsPerUnit);
            _renderer.sortingOrder = SortingOrder;
            _renderer.enabled = Enabled;
        }

        private void LateUpdate()
        {
            if (!_cam) _cam = Camera.main;
            FogOfWar.LightPrepareRadius = Enabled ? MaxRadius + 12f : 0f;
            if (!Enabled || !_cam || !_cam.orthographic)
            {
                _renderer.enabled = false;
                return;
            }

            using var _ = s_schedule.Auto();

            // The grid: the view, and as much again round it as a light can reach, so a lamp
            // just off screen still lights the edge of it and its walls still stop it.
            float cell = Mathf.Max(0.05f, CellSize);
            float halfH = _cam.orthographicSize, halfW = halfH * _cam.aspect;
            Vector3 c = _cam.transform.position;
            float reach = Mathf.Max(1f, MaxRadius);
            int gx0 = Mathf.FloorToInt((c.x - halfW - reach) / cell);
            int gy0 = Mathf.FloorToInt((c.y - halfH - reach) / cell);
            int w = Mathf.CeilToInt((halfW + reach) * 2f / cell) + 2;
            int h = Mathf.CeilToInt((halfH + reach) * 2f / cell) + 2;
            var gridMin = new Vector2(gx0 * cell, gy0 * cell);
            var gridRect = new Rect(gridMin, new Vector2(w * cell, h * cell));

            Gather(gridRect, c);
            int count = Mathf.Min(_candidates.Count, Mathf.Max(1, MaxLights));

            _stride = 2 * (Mathf.CeilToInt(reach / cell) + 1) + 1;
            Ensure(ref _opacity, w * h);
            Ensure(ref _reach, Mathf.Max(1, count) * _stride * _stride);
            Ensure(ref _lights, Mathf.Max(1, count));
            Ensure(ref _colors, Mathf.Max(1, count));
            EnsureTexture(w, h);

            float maxCells = reach / cell;
            for (int i = 0; i < count; i++)
            {
                var l = _candidates[i];
                Vector2 p = (l.At - gridMin) / cell;
                _lights[i] = new float4(p.x, p.y, Mathf.Min(l.Radius / cell, maxCells), 0f);
                _colors[i] = new float4(l.Color.r * l.Intensity, l.Color.g * l.Intensity, l.Color.b * l.Intensity, 0f);
            }

            var sight = FogOfWar.Sight;
            bool hasSight = sight != null && FogOfWar.SightFrame == Time.frameCount && sight.HasMap;
            var opacity = new LightOpacityJob
            {
                Solid = hasSight ? sight.Map : _noSolid,
                SolidW = hasSight ? sight.Width : 1,
                SolidH = hasSight ? sight.Height : 1,
                SolidOrigin = hasSight ? (float2)sight.Origin : new float2(1e9f, 1e9f),
                SolidCell = hasSight ? sight.CellSize : 1f,
                Opacity = _opacity,
                GridMin = new int2(gx0, gy0),
                GridW = w,
                Cell = cell,
            }.Schedule(h, 8);

            var spread = new LightSpreadJob
            {
                Opacity = _opacity,
                GridW = w,
                GridH = h,
                Lights = _lights,
                Reach = _reach,
                Stride = _stride,
                WallCost = Mathf.Max(0f, WallCost),
            }.Schedule(count, 1, opacity);

            _jobs = new LightGatherJob
            {
                Reach = _reach,
                Lights = _lights,
                Colors = _colors,
                LightCount = count,
                Stride = _stride,
                GridW = w,
                Ambient = new float3(Ambient.r, Ambient.g, Ambient.b),
                Max = Mathf.Max(0.01f, MaxLight),
                Texels = _tex.GetPixelData<Color32>(0),
            }.Schedule(h, 8, spread);
            JobHandle.ScheduleBatchedJobs();

            _pending = true;
            _pendingOrigin = gridMin;
            _pendingSize = gridRect.size;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Lights
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Every light that can reach the grid, brightest and nearest first.</summary>
        private void Gather(Rect grid, Vector2 centre)
        {
            _candidates.Clear();

            var player = App.Instance.PlayerTransform;
            if (player && PlayerIntensity > 0f)
                Add((Vector2)player.position + PlayerOffset, PlayerColor, PlayerIntensity, PlayerRadius, grid, centre, 1e6f);

            foreach (var s in LightSource2D.All)
                if (s) Add(s.Position, s.color, s.Current, s.radius, grid, centre, 0f);

            float now = Time.time;
            for (int i = Flashes.Count - 1; i >= 0; i--)
            {
                var f = Flashes[i];
                float t = (now - f.Start) / f.Seconds;
                if (t >= 1f) { Flashes.RemoveAt(i); continue; }
                float k = (1f - t) * (1f - t);
                Add(f.At, f.Color, f.Intensity * k, f.Radius * (0.6f + 0.4f * k), grid, centre, 0f);
            }

            AddFire(grid, centre);

            _candidates.Sort((a, b) => b.Score.CompareTo(a.Score));
        }

        private void Add(Vector2 at, Color color, float intensity, float radius, Rect grid, Vector2 centre, float bonus)
        {
            if (intensity <= 0.01f || radius <= 0.05f) return;
            radius = Mathf.Min(radius, MaxRadius);
            if (at.x < grid.xMin - radius || at.x > grid.xMax + radius ||
                at.y < grid.yMin - radius || at.y > grid.yMax + radius) return;

            float d = Vector2.Distance(at, centre);
            _candidates.Add(new Candidate
            {
                At = at, Color = color, Intensity = intensity, Radius = radius,
                Score = bonus + intensity * radius / (1f + d * 0.15f),
            });
        }

        /// <summary>Flames, a light per patch of them: the more fire in a patch, the brighter and
        /// further it reaches.</summary>
        private void AddFire(Rect grid, Vector2 centre)
        {
            var field = FlameField.Instance;
            if (field == null || field.Count == 0) return;

            _fireBins.Clear();
            float inv = 1f / Mathf.Max(0.1f, FireBin);
            var cx = field.CellX;
            var cy = field.CellY;
            var kind = field.Kind;
            for (int i = 0; i < field.Count; i++)
            {
                if (kind[i] != FlameField.KindFire) continue;
                Vector2 p = FlameField.CellToWorld(cx[i], cy[i]);
                if (!grid.Contains(p)) continue;
                long key = ((long)Mathf.FloorToInt(p.x * inv) << 32) ^ (uint)Mathf.FloorToInt(p.y * inv);
                _fireBins.TryGetValue(key, out var b);
                _fireBins[key] = new Vector3(b.x + p.x, b.y + p.y, b.z + 1f);
            }

            float t = Time.time;
            foreach (var kv in _fireBins)
            {
                var b = kv.Value;
                var at = new Vector2(b.x / b.z, b.y / b.z);
                float n = Mathf.PerlinNoise((kv.Key & 0xFFFF) * 0.37f, t * 9f) * 2f - 1f;
                float intensity = Mathf.Min(1.4f, 0.25f + b.z * 0.02f) * (1f + 0.2f * n);
                float radius = Mathf.Min(6f, 2.2f + b.z * 0.06f);
                Add(at, FireColor, intensity, radius, grid, centre, 0f);
            }
        }

        // ─────────────────────────────────────────────────────────────────────────

        private static void Ensure<T>(ref NativeArray<T> a, int n) where T : struct
        {
            if (a.IsCreated && a.Length >= n) return;
            if (a.IsCreated) a.Dispose();
            a = new NativeArray<T>(Mathf.NextPowerOfTwo(n), Allocator.Persistent);
        }

        private void EnsureTexture(int w, int h)
        {
            if (_tex && _tex.width == w && _tex.height == h) return;
            if (_tex) Destroy(_tex);
            _tex = new Texture2D(w, h, TextureFormat.RGBA32, false, true)
            {
                name = "LightMap",
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp,
                hideFlags = HideFlags.HideAndDontSave,
            };
        }
    }
}
