using Phys.Paint;
using Unity.Profiling;
using UnityEngine;

namespace Gore
{
    /// <summary>
    /// Every drop of blood in the air, simulated and drawn in one place.
    ///
    /// Drops are not rigidbodies and not GameObjects. A wound throws dozens of them and a body
    /// coming apart throws hundreds, which is two orders of magnitude more than the scene can
    /// afford as real objects — so they live in flat arrays here, are integrated by hand, and
    /// go out as one dynamic mesh of vertex-coloured quads, the same way
    /// <see cref="Phys.Fire.FlameFieldView"/> draws fire.
    ///
    /// What they do have that a spark does not is a landing. Each moving drop sweeps a ray
    /// against the world, and where it stops it stains whatever it hit through
    /// <see cref="SpritePaintService"/> — so blood is not an effect that plays and clears, it is
    /// the game's record of what happened in a room. That is also why a drop dies on contact:
    /// the mark it leaves is the point of it, and a drop that bounced would spend its ink
    /// somewhere the player never saw it happen.
    /// </summary>
    [DefaultExecutionOrder(1050)]
    public sealed class BloodSystem : MonoBehaviour
    {
        private static BloodSystem _instance;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => _instance = null;

        /// <summary>
        /// Created on the first drop rather than at load, so a level where nothing bleeds
        /// carries no gore machinery at all.
        /// </summary>
        private static BloodSystem Instance
        {
            get
            {
                if (_instance) return _instance;
                var go = new GameObject("~BloodSystem") { hideFlags = HideFlags.HideAndDontSave };
                _instance = go.AddComponent<BloodSystem>();
                return _instance;
            }
        }

        /// <summary>Live drops. Diagnostics only.</summary>
        public static int DropCount => _instance ? _instance._count : 0;

        // Structure of arrays: the update walks all of it every frame and nothing outside
        // this class ever touches it.
        private Vector2[] _pos;
        private Vector2[] _vel;
        private float[] _age;
        private float[] _life;
        private float[] _size;      // in world pixels across
        private float[] _arm;       // seconds left of passing through the world
        private Color32[] _tint;
        private int _count;
        private int _next;          // where the next recycled slot comes from

        private Mesh _mesh;
        private Material _material;
        private Vector3[] _verts;
        private Color32[] _colors;
        private int[] _indices;

        private readonly RaycastHit2D[] _hits = new RaycastHit2D[8];
        private ContactFilter2D _filter;
        private int _seed;

        // ─────────────────────────────────────────────────────────────────────
        // Throwing blood
        // ─────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Blood out of a wound: a cone of drops around <paramref name="dir"/>, which is the
        /// way the blood travels — away from whatever caused the wound.
        /// </summary>
        public static void Spray(Vector2 point, Vector2 dir, int count, float speed = -1f,
                                 float cone = -1f, Color32 color = default)
        {
            if (count <= 0) return;

            var cfg = GoreConfig.Shared;
            if (color.a == 0) color = cfg.dropColor;
            if (speed < 0f) speed = cfg.spraySpeed;
            if (cone < 0f) cone = cfg.sprayCone;

            Vector2 axis = dir.sqrMagnitude > 1e-6f ? dir.normalized : Vector2.up;
            var sys = Instance;

            for (int i = 0; i < count; i++)
            {
                // Squared, so most of the spray is slow and a few drops carry much further. An
                // evenly spread cone reads as a firework; this reads as a burst.
                float t = Random.value;
                float v = speed * Mathf.Lerp(0.25f, 1.15f, t * t);
                Vector2 d = Quaternion.Euler(0f, 0f, Random.Range(-cone, cone)) * axis;
                sys.Add(point, d * v, color, Random.Range(0.6f, 1.6f));
            }
        }

        /// <summary>
        /// Damage worth of blood. The count comes off <see cref="GoreConfig.dropsPerDamage"/>,
        /// so how bloody the game is stays one number instead of a decision taken again at
        /// every call site.
        /// </summary>
        public static void SprayDamage(Vector2 point, Vector2 dir, float damage, Color32 color = default)
        {
            var cfg = GoreConfig.Shared;
            int n = Mathf.Clamp(Mathf.RoundToInt(damage * cfg.dropsPerDamage), 0, cfg.maxDropsPerHit);
            if (n <= 0) return;
            Spray(point, dir, n, color: color);
        }

        /// <summary>A single drop falling off something, with whatever motion it was given.</summary>
        public static void Drip(Vector2 point, Vector2 velocity, Color32 color = default, float size = 1f)
        {
            if (color.a == 0) color = GoreConfig.Shared.dropColor;
            Instance.Add(point, velocity, color, size);
        }

        private void Add(Vector2 pos, Vector2 vel, Color32 color, float size)
        {
            var cfg = GoreConfig.Shared;
            int max = Mathf.Max(16, cfg.maxDrops);
            if (_pos == null || _pos.Length != max) Allocate(max);

            int i;
            if (_count < max)
            {
                i = _count++;
            }
            else
            {
                // Full: walk a cursor rather than hunting for the oldest drop. Across a full
                // buffer the cursor is as good as the oldest, and it costs nothing to find.
                i = _next;
                _next = (_next + 1) % max;
            }

            _pos[i] = pos;
            _vel[i] = vel;
            _age[i] = 0f;
            _life[i] = cfg.dropLife * Random.Range(0.7f, 1.3f);
            _size[i] = size;
            _arm[i] = cfg.armTime;
            _tint[i] = color;
        }

        private void Allocate(int max)
        {
            _pos = new Vector2[max];
            _vel = new Vector2[max];
            _age = new float[max];
            _life = new float[max];
            _size = new float[max];
            _arm = new float[max];
            _tint = new Color32[max];
            _count = 0;
            _next = 0;

            _verts = new Vector3[max * 4];
            _colors = new Color32[max * 4];
            _indices = new int[max * 6];
        }

        // ─────────────────────────────────────────────────────────────────────
        // Simulation
        // ─────────────────────────────────────────────────────────────────────

        private void Awake()
        {
            _mesh = new Mesh { name = "Blood", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            _mesh.MarkDynamic();

            // The fire view's shader is a plain vertex-coloured quad with its blend factors
            // exposed; blood wants exactly that, over the top instead of added to it.
            var shader = Resources.Load<Shader>("Shaders/FlameField");
            if (!shader) shader = Shader.Find("Sprites/Default");

            _material = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            _material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            _material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);

            var mf = gameObject.AddComponent<MeshFilter>();
            mf.sharedMesh = _mesh;

            var mr = gameObject.AddComponent<MeshRenderer>();
            mr.sharedMaterial = _material;
            mr.sortingOrder = GoreConfig.Shared.sortingOrder;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;

            _filter = new ContactFilter2D
            {
                useTriggers = false,
                useLayerMask = true,
                layerMask = GoreConfig.Shared.splatMask,
            };
        }

        private static readonly ProfilerMarker s_step = new("Blood.Step");

        private void Update()
        {
            if (_count == 0) return;
            using var _ = s_step.Auto();

            var cfg = GoreConfig.Shared;
            float dt = Mathf.Min(Time.deltaTime, 0.05f);   // a hitch must not throw blood through a wall
            Vector2 pull = Physics2D.gravity * cfg.gravity;
            float damp = 1f - Mathf.Min(0.95f, cfg.drag * dt);

            for (int i = 0; i < _count; i++)
            {
                _age[i] += dt;
                if (_age[i] >= _life[i]) { Remove(i--); continue; }

                _vel[i] = (_vel[i] + pull * dt) * damp;

                Vector2 step = _vel[i] * dt;
                float dist = step.magnitude;

                if (_arm[i] > 0f)
                {
                    _arm[i] -= dt;
                }
                else if (dist > 1e-4f && Land(i, step / dist, dist))
                {
                    Remove(i--);
                    continue;
                }

                _pos[i] += step;
            }
        }

        /// <summary>
        /// Sweep this frame's step. Returns true when the drop stopped, which is also when it
        /// left its mark.
        /// </summary>
        private bool Land(int i, Vector2 dir, float dist)
        {
            int n = Physics2D.Raycast(_pos[i], dir, _filter, _hits, dist);
            if (n <= 0) return false;

            // Hits come back in distance order, and triggers and the wrong layers are already
            // filtered out — but a drop born in a wound starts inside the body it came from,
            // and a query that starts inside a collider reports it at zero distance. Skipping
            // those is what lets blood leave the thing it was spilled out of; anything past
            // them is a surface the drop actually flew into.
            RaycastHit2D hit = default;
            for (int h = 0; h < n; h++)
            {
                if (!_hits[h].collider || _hits[h].distance <= 0f) continue;
                hit = _hits[h];
                break;
            }
            if (!hit.collider) return false;

            var cfg = GoreConfig.Shared;

            // Half a world pixel inside the surface. Centred on the contact point instead, half
            // the mark would fall outside the outline and find no pixels to stain.
            Vector2 at = hit.point - hit.normal * 0.025f;

            SpritePaintService.PaintSplat(
                hit.collider.gameObject, at, _vel[i], cfg.stainRadius * _size[i],
                cfg.stainColor, cfg.stainStrength, cfg.stainNoise, _seed++);

            return true;
        }

        private void Remove(int i)
        {
            int last = --_count;
            if (i != last)
            {
                _pos[i] = _pos[last];
                _vel[i] = _vel[last];
                _age[i] = _age[last];
                _life[i] = _life[last];
                _size[i] = _size[last];
                _arm[i] = _arm[last];
                _tint[i] = _tint[last];
            }
            if (_next > _count) _next = 0;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Drawing
        // ─────────────────────────────────────────────────────────────────────

        /// <summary>The world's pixel, same as every sprite's PPU. Drops snap to it.</summary>
        private const float Pixel = 1f / 20f;

        private void LateUpdate()
        {
            _mesh.Clear();
            if (_count == 0) return;

            int v = 0, n = 0;
            for (int i = 0; i < _count; i++)
            {
                // Snapped to the grid the rest of the game is drawn on, so a drop reads as a
                // pixel moving rather than as a smear sliding between two of them.
                float size = Mathf.Max(1f, Mathf.Round(_size[i] * 1.5f)) * Pixel;
                float x = Mathf.Round(_pos[i].x / Pixel) * Pixel;
                float y = Mathf.Round(_pos[i].y / Pixel) * Pixel;

                var c = _tint[i];
                // Only the last quarter of the life fades, and only blood that never landed
                // ever gets that far.
                float left = 1f - _age[i] / _life[i];
                if (left < 0.25f) c.a = (byte)(c.a * (left * 4f));

                int b = v;
                _verts[v] = new Vector3(x, y, 0f);
                _verts[v + 1] = new Vector3(x + size, y, 0f);
                _verts[v + 2] = new Vector3(x + size, y + size, 0f);
                _verts[v + 3] = new Vector3(x, y + size, 0f);
                _colors[v] = c;
                _colors[v + 1] = c;
                _colors[v + 2] = c;
                _colors[v + 3] = c;
                v += 4;

                _indices[n] = b;
                _indices[n + 1] = b + 1;
                _indices[n + 2] = b + 2;
                _indices[n + 3] = b;
                _indices[n + 4] = b + 2;
                _indices[n + 5] = b + 3;
                n += 6;
            }

            _mesh.SetVertices(_verts, 0, v);
            _mesh.SetColors(_colors, 0, v);
            _mesh.SetIndices(_indices, 0, n, MeshTopology.Triangles, 0, false);

            // Blood travels, and recalculating bounds over every drop each frame costs more
            // than the mesh build does, so the mesh simply never culls.
            _mesh.bounds = new Bounds(Vector3.zero, new Vector3(1e5f, 1e5f, 1f));
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
            if (_mesh) Destroy(_mesh);
            if (_material) Destroy(_material);
        }
    }
}
