using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;
using Unity.Profiling;
using UnityEngine;
using Random = UnityEngine.Random;

namespace Vision
{
    /// <summary>
    /// What the player has seen. The world starts dark; whatever the player has a clear line to
    /// lightens over a moment and then stays lit for the rest of the floor, so the dark only
    /// ever shrinks.
    ///
    /// Modelled on Noita's fog of war, not lifted from it. Noita keeps one byte of coverage per
    /// 32x32-pixel cell (the 1/32 at 0xd1da01 in noita_dev.exe), reads it back bilinearly
    /// (GameGetFogOfWarBilinear) and lets it change by a limited amount per frame
    /// (a biome's fog_of_war_delta). Its cells can be that coarse because a GPU light pass softens
    /// them; here the grid is finer, a cell is <see cref="CellSize"/> units, and the softening is
    /// done by the shader instead: bilinear, a small blur, then a smooth ramp.
    ///
    /// Sight is a fan of rays from the player's eye, marched through the terrain's own pixels
    /// (<see cref="TerrainSight"/>): standing terrain and shut doors stop a ray; crates, ropes,
    /// bodies, enemies and the rest of what moves do not. A ray carries on a little way into
    /// whatever stops it, fading as it goes, so the face of a wall shows as rock with darkness
    /// behind it rather than as a hard line. Rays also weaken towards the edge of
    /// <see cref="SightRadius"/>, so a far wall is only half-lit until you come closer.
    ///
    /// The work is Burst jobs (<see cref="FogRayJob"/>, <see cref="FogFillJob"/>) spread over
    /// the worker threads. They are scheduled at the end of one frame and collected at the start
    /// of the next, so they run alongside rendering and the main thread hardly waits on them;
    /// the price is that the fog on screen is one frame old, which a fade-in never shows.
    /// Seen state is one flat byte grid over the floor's terrain map. Only the part under the
    /// camera is drawn: one small R8 texture, on one quad in front of everything in the world.
    /// </summary>
    [DefaultExecutionOrder(1200)]
    public sealed class FogOfWar : MonoBehaviour
    {
        /// <summary>Run the fog at all. Off (F3) it neither draws nor looks, so it costs nothing -
        /// what was seen is kept, and sight picks up again when it comes back on.</summary>
        public static bool Enabled = true;
        public static KeyCode ToggleKey = KeyCode.F3;

        /// <summary>Side of one fog cell, in world units (5 art pixels).</summary>
        public static float CellSize = 0.25f;

        /// <summary>How far the player sees, in units. The view is ~21 by 12 units.</summary>
        public static float SightRadius = 13f;

        /// <summary>Full strength out to this fraction of <see cref="SightRadius"/>, then a
        /// smooth fall to nothing at the radius itself.</summary>
        public static float FullSightFraction = 0.55f;

        /// <summary>How far past the surface a ray still lights the wall it hit.</summary>
        public static float WallDepth = 0.6f;

        /// <summary>Always seen, walls or not, so the player is never standing in the dark.</summary>
        public static float NearRadius = 1.2f;

        public static Vector2 EyeOffset = new(0f, 0.15f);

        /// <summary>Rays in a full turn. At the sight radius neighbouring rays sit well under a
        /// cell apart, and each sweep turns by a random fraction of a ray so none is missed.</summary>
        public static int Rays = 720;
        public static int RaysPerFrame = 720;

        /// <summary>Seconds for a cell to come up from dark to fully seen.</summary>
        public static float FadeInSeconds = 0.45f;

        public static Color FogColor = new(0.02f, 0.016f, 0.027f, 1f);

        /// <summary>Over the world, fire and arcs included; under the UI, which is overlay.</summary>
        public static int SortingOrder = 1000;

        /// <summary>Art pixels per unit; the fog is drawn on that grid so it reads as pixel art.</summary>
        public static float ArtPixelsPerUnit = 20f;

        /// <summary>How far round the player the sight map must be painted for the light
        /// (Lighting.LightField sets it); 0 = only as far as the fog looks.</summary>
        public static float LightPrepareRadius;

        private static FogOfWar _instance;

        /// <summary>The terrain map sight is cast through, for other readers - the light. Only
        /// current when <see cref="SightFrame"/> is this frame; written in this LateUpdate, so a
        /// job reading it must be scheduled after it and collected in the next Update.</summary>
        internal static TerrainSight Sight => _instance ? _instance._sight : null;

        /// <summary>The frame the sight map was last brought up to date and painted round the
        /// player.</summary>
        internal static int SightFrame { get; private set; } = -1;

        private readonly TerrainSight _sight = new();

        // Seen: best sight so far. Shown: easing up towards it. Both cover the terrain map.
        private NativeArray<byte> _seen, _shown;
        private int2 _seenMin;
        private int _seenW, _seenH;
        private float _seenCell;
        private int _mapId = int.MinValue;

        private NativeArray<float4> _doors;

        private JobHandle _jobs;
        private bool _pending;
        private Vector2 _pendingOrigin, _pendingSize;

        private int _nextRay;
        private float _sweepTurn;
        private float _fadeCarry;

        private Mesh _quad;
        private Material _mat;
        private MeshRenderer _renderer;
        private Texture2D _tex;
        private Camera _cam;

        private static readonly int OriginId = Shader.PropertyToID("_Origin");
        private static readonly int SizeId = Shader.PropertyToID("_Size");
        private static readonly int ColorId = Shader.PropertyToID("_Color");
        private static readonly int ArtPpuId = Shader.PropertyToID("_ArtPPU");

        private static readonly ProfilerMarker s_finish = new("Fog.Finish");
        private static readonly ProfilerMarker s_schedule = new("Fog.Schedule");

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            // Earlier builds of this host were HideAndDontSave, which the editor keeps alive
            // past the end of play mode: a dead quad, frozen where it last was, drawn over the
            // next session. Sweep any such leftover before making the real one.
            foreach (var stale in Resources.FindObjectsOfTypeAll<FogOfWar>())
                if (stale) DestroyHost(stale.gameObject);
            _instance = null;

            // Hidden, but not DontSave, so leaving play mode takes it down with everything else.
            var go = new GameObject("~FogOfWar") { hideFlags = HideFlags.HideInHierarchy };
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<FogOfWar>();
        }

        private static void DestroyHost(GameObject go)
        {
            var mr = go.GetComponent<MeshRenderer>();
            if (mr && mr.sharedMaterial)
            {
                if (mr.sharedMaterial.mainTexture) Destroy(mr.sharedMaterial.mainTexture);
                Destroy(mr.sharedMaterial);
            }
            var mf = go.GetComponent<MeshFilter>();
            if (mf && mf.sharedMesh) Destroy(mf.sharedMesh);
            Destroy(go);
        }

        /// <summary>Forget everything seen. Call when the world under the fog is replaced.</summary>
        public static void Clear()
        {
            if (!_instance) return;
            _instance._jobs.Complete();
            _instance._pending = false;
            _instance._sight.Reset();   // rebuilt next frame, and the seen grid with it
        }

        /// <summary>How well a world point has been seen, 0 (never) to 1.</summary>
        public static float SeenAt(Vector2 world)
        {
            if (!_instance) return 1f;
            var f = _instance;
            if (!f._shown.IsCreated) return 0f;
            f._jobs.Complete();

            int x = Mathf.FloorToInt(world.x / f._seenCell) - f._seenMin.x;
            int y = Mathf.FloorToInt(world.y / f._seenCell) - f._seenMin.y;
            if ((uint)x >= (uint)f._seenW || (uint)y >= (uint)f._seenH) return 0f;
            return f._shown[y * f._seenW + x] / 255f;
        }

        private void Awake()
        {
            _quad = new Mesh { name = "FogQuad", hideFlags = HideFlags.HideAndDontSave };
            _quad.SetVertices(new[]
            {
                new Vector3(0f, 0f, 0f), new Vector3(1f, 0f, 0f),
                new Vector3(1f, 1f, 0f), new Vector3(0f, 1f, 0f),
            });
            _quad.SetTriangles(new[] { 0, 2, 1, 0, 3, 2 }, 0);
            _quad.bounds = new Bounds(new Vector3(0.5f, 0.5f, 0f), new Vector3(1f, 1f, 1f));

            var shader = Resources.Load<Shader>("Shaders/FogOfWar");
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
        }

        private void OnDestroy()
        {
            _jobs.Complete();
            if (_instance == this) _instance = null;
            if (_seen.IsCreated) _seen.Dispose();
            if (_shown.IsCreated) _shown.Dispose();
            if (_doors.IsCreated) _doors.Dispose();
            _sight.Dispose();
            if (_quad) Destroy(_quad);
            if (_mat) Destroy(_mat);
            if (_tex) Destroy(_tex);
        }

        private void Update()
        {
            if (Input.GetKeyDown(ToggleKey)) Enabled = !Enabled;

            // Last frame's jobs, collected before any LateUpdate: the sight map is repainted in
            // ours, and other readers of it (Lighting.LightField) collect theirs in Update too.
            Finish();
        }

        private void LateUpdate()
        {
            var player = App.Instance.PlayerTransform;
            if (!_cam) _cam = Camera.main;
            bool fog = Enabled && player && _cam && _cam.orthographic;
            if (!fog) _renderer.enabled = false;

            // The sight map is the light's too: keep it current while either one is on.
            if (!player || (!fog && LightPrepareRadius <= 0f)) return;

            using var _ = s_schedule.Auto();

            _sight.Refresh();
            FollowMap();
            Vector2 eye = (Vector2)player.position + EyeOffset;
            _sight.Prepare(eye, Mathf.Max(SightRadius + 1f, LightPrepareRadius));
            SightFrame = Time.frameCount;
            if (!fog) return;

            if (!_seen.IsCreated)
            {
                _renderer.enabled = false;   // no terrain, nothing to hide
                return;
            }

            RevealDisc(eye, NearRadius);

            // An eye inside rock would see nothing past it; the near disc is enough.
            JobHandle rays = _sight.Solid(eye) ? default : ScheduleRays(eye);
            ScheduleFill(rays);
            JobHandle.ScheduleBatchedJobs();
        }

        /// <summary>Collect last frame's jobs and put what they drew on screen.</summary>
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
            _mat.SetColor(ColorId, FogColor);
            _mat.SetFloat(ArtPpuId, ArtPixelsPerUnit);
            _renderer.sortingOrder = SortingOrder;
            _renderer.enabled = true;
        }

        /// <summary>Size the seen grid to the terrain map, whenever that is rebuilt.</summary>
        private void FollowMap()
        {
            if (_mapId == _sight.MapId) return;
            _mapId = _sight.MapId;

            if (_seen.IsCreated) _seen.Dispose();
            if (_shown.IsCreated) _shown.Dispose();
            if (!_sight.HasMap) return;

            _seenCell = Mathf.Max(0.01f, CellSize);
            Vector2 min = _sight.Origin;
            Vector2 max = min + new Vector2(_sight.Width, _sight.Height) * _sight.CellSize;
            _seenMin = new int2(Mathf.FloorToInt(min.x / _seenCell), Mathf.FloorToInt(min.y / _seenCell));
            _seenW = Mathf.CeilToInt(max.x / _seenCell) - _seenMin.x;
            _seenH = Mathf.CeilToInt(max.y / _seenCell) - _seenMin.y;

            _seen = new NativeArray<byte>(_seenW * _seenH, Allocator.Persistent);
            _shown = new NativeArray<byte>(_seenW * _seenH, Allocator.Persistent);
        }

        private void RevealDisc(Vector2 centre, float radius)
        {
            float r = radius / _seenCell;
            int ri = Mathf.CeilToInt(r);
            int cx = Mathf.FloorToInt(centre.x / _seenCell) - _seenMin.x;
            int cy = Mathf.FloorToInt(centre.y / _seenCell) - _seenMin.y;
            for (int y = -ri; y <= ri; y++)
            for (int x = -ri; x <= ri; x++)
            {
                if (x * x + y * y > r * r) continue;
                int gx = cx + x, gy = cy + y;
                if ((uint)gx < (uint)_seenW && (uint)gy < (uint)_seenH) _seen[gy * _seenW + gx] = 255;
            }
        }

        private JobHandle ScheduleRays(Vector2 eye)
        {
            int doors = 0;
            for (int i = 0; i < _sight.DoorCount; i++)
            {
                if (!_sight.ShutDoor(i, out var r)) continue;
                if (!_doors.IsCreated || _doors.Length <= doors)
                {
                    var grown = new NativeArray<float4>(Mathf.Max(8, doors * 2), Allocator.Persistent);
                    if (_doors.IsCreated)
                    {
                        NativeArray<float4>.Copy(_doors, grown, _doors.Length);
                        _doors.Dispose();
                    }
                    _doors = grown;
                }
                _doors[doors++] = new float4(r.xMin, r.yMin, r.xMax, r.yMax);
            }
            if (!_doors.IsCreated) _doors = new NativeArray<float4>(8, Allocator.Persistent);

            int rays = Mathf.Max(8, Rays);
            int n = Mathf.Clamp(RaysPerFrame, 1, rays);

            // A new sweep: turn it by a fresh fraction of a ray, so over a few sweeps the whole
            // circle is covered, not just the same fixed spokes.
            if (_nextRay == 0) _sweepTurn = Random.value;

            float radius = SightRadius;
            var job = new FogRayJob
            {
                Solid = _sight.Map,
                SolidW = _sight.Width,
                SolidH = _sight.Height,
                SolidOrigin = _sight.Origin,
                SolidCell = _sight.CellSize,
                Doors = _doors,
                DoorCount = doors,
                Seen = _seen,
                SeenMin = _seenMin,
                SeenW = _seenW,
                SeenH = _seenH,
                FogCell = _seenCell,
                Eye = eye,
                Radius = radius,
                Full = Mathf.Min(radius * FullSightFraction, radius - 1e-3f),
                Depth = Mathf.Max(1e-3f, WallDepth),
                AngleStep = Mathf.PI * 2f / rays,
                Turn = _sweepTurn,
                FirstRay = _nextRay,
                RayCount = rays,
            };
            _nextRay = (_nextRay + n) % rays;
            return job.Schedule(n, 16);
        }

        private void ScheduleFill(JobHandle after)
        {
            float cell = _seenCell;
            float halfH = _cam.orthographicSize;
            float halfW = halfH * _cam.aspect;
            Vector3 c = _cam.transform.position;

            // A few cells of margin so the blur and the bilinear taps at the screen edge read
            // real cells, not the clamp - and so the view, drawn a frame late, still fits.
            const int margin = 4;
            int w = Mathf.CeilToInt(halfW * 2f / cell) + margin * 2 + 1;
            int h = Mathf.CeilToInt(halfH * 2f / cell) + margin * 2 + 1;
            int cx0 = Mathf.FloorToInt((c.x - halfW) / cell) - margin;
            int cy0 = Mathf.FloorToInt((c.y - halfH) / cell) - margin;

            EnsureTexture(w, h);

            _fadeCarry += Time.deltaTime * 255f / Mathf.Max(1e-3f, FadeInSeconds);
            int fade = (int)_fadeCarry;
            _fadeCarry -= fade;

            var job = new FogFillJob
            {
                Seen = _seen,
                Shown = _shown,
                SeenMin = _seenMin,
                SeenW = _seenW,
                SeenH = _seenH,
                Texels = _tex.GetPixelData<byte>(0),
                ViewMin = new int2(cx0, cy0),
                ViewW = w,
                ViewH = h,
                Fade = fade,
            };
            _jobs = job.Schedule(after);
            _pending = true;
            _pendingOrigin = new Vector2(cx0 * cell, cy0 * cell);
            _pendingSize = new Vector2(w * cell, h * cell);
        }

        private void EnsureTexture(int w, int h)
        {
            if (_tex && _tex.width == w && _tex.height == h) return;
            if (_tex) Destroy(_tex);

            _tex = new Texture2D(w, h, TextureFormat.R8, false, true)
            {
                name = "FogOfWar",
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp,
                hideFlags = HideFlags.HideAndDontSave,
            };
        }
    }
}
