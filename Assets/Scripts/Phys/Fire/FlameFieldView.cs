using Unity.Profiling;
using UnityEngine;

namespace Phys.Fire
{
    /// <summary>
    /// Draws <see cref="FlameField"/> as one mesh: a soft additive glow layer and, over it,
    /// the hard one-pixel flame cells themselves.
    ///
    /// The two layers are Noita's. Its fire renderer keeps two config'd passes —
    /// RENDER_FIRE_GLOW_ALPHA and RENDER_FIRE_SHARP_ALPHA, both 0.5 in the dev build
    /// (registered at 0x4609f8 and 0x460a27) — and the reason it looks like fire rather than
    /// like orange confetti is that the sharp pixels sit inside a much wider bloom. A single
    /// flat layer of cells, which is all the old FireSystem drew, cannot get there.
    ///
    /// One mesh, two submeshes, two materials, one draw call each. Rebuilt every frame from
    /// the live cells, which is cheap next to the physics the same frame runs.
    /// </summary>
    [DefaultExecutionOrder(1100)]
    public sealed class FlameFieldView : MonoBehaviour
    {
        /// <summary>Over everything: fire is the brightest thing in the scene.</summary>
        public static int SortingOrder = 500;

        /// <summary>How many cell widths the glow spreads past the flame that casts it.</summary>
        public static float GlowSpread = 2.6f;

        /// <summary>
        /// Per-cell glow strength. Far below Noita's 0.5 because that figure applies to a
        /// blurred downsample of the whole fire buffer, not to each cell on its own — every
        /// flame here overlaps its neighbours, and the sum is what reaches 0.5.
        /// </summary>
        public static float GlowIntensity = 0.14f;

        public static float SharpAlpha = 0.93f;

        // Noita's fire runs white-hot at the source and drops through orange into a dull red
        // as the cell rises; age in ticks is the only thing driving it.
        public static Color32 Hot = new(255, 246, 209, 255);
        public static Color32 Mid = new(255, 158, 38, 255);
        public static Color32 Cool = new(176, 42, 14, 255);
        public static Color32 Smoke = new(74, 71, 69, 255);

        /// <summary>Ticks over which a flame cools from <see cref="Hot"/> to <see cref="Cool"/>.</summary>
        public static float CoolTicks = 22f;

        private static FlameFieldView _instance;

        private Mesh _mesh;
        private Material _glowMat;
        private Material _sharpMat;
        private Camera _cam;

        private Vector3[] _verts = new Vector3[4096];
        private Color32[] _colors = new Color32[4096];
        private int[] _glowIdx = new int[6144];
        private int[] _sharpIdx = new int[6144];

        public static void Install()
        {
            if (_instance) return;

            var go = new GameObject("~FlameFieldView") { hideFlags = HideFlags.HideAndDontSave };
            _instance = go.AddComponent<FlameFieldView>();
        }

        private void Awake()
        {
            _mesh = new Mesh { name = "FlameField", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            _mesh.MarkDynamic();
            _mesh.subMeshCount = 2;

            var shader = Resources.Load<Shader>("Shaders/FlameField");
            if (!shader) shader = Shader.Find("Sprites/Default");

            // Blend modes come from properties so both layers can share one shader.
            _glowMat = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            _glowMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            _glowMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.One);

            _sharpMat = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            _sharpMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            _sharpMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);

            var mf = gameObject.AddComponent<MeshFilter>();
            mf.sharedMesh = _mesh;

            var mr = gameObject.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { _glowMat, _sharpMat };
            mr.sortingOrder = SortingOrder;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
        }

        private static readonly ProfilerMarker s_mesh = new("Fire.FlameMesh");

        private void LateUpdate()
        {
            using var _ = s_mesh.Auto();

            var field = FlameField.Instance;
            int count = field.Count;
            if (count == 0)
            {
                if (_mesh.vertexCount > 0) _mesh.Clear();
                return;
            }

            // Cells outside the view still simulate — they just cost nothing to draw.
            float minX = 0f, maxX = 0f, minY = 0f, maxY = 0f;
            if (!_cam) _cam = Camera.main;
            bool culling = _cam && _cam.orthographic;
            if (culling)
            {
                float h = _cam.orthographicSize + 1f;
                float w = h * _cam.aspect;
                Vector3 c = _cam.transform.position;
                minX = c.x - w; maxX = c.x + w;
                minY = c.y - h; maxY = c.y + h;
            }

            EnsureCapacity(count);

            float cell = FlameField.CellSize;
            float glow = cell * GlowSpread;
            var cx = field.CellX;
            var cy = field.CellY;
            var kind = field.Kind;
            var age = field.Age;
            var life = field.Life;

            int v = 0, gi = 0, si = 0;

            for (int i = 0; i < count; i++)
            {
                Vector2 p = FlameField.CellToWorld(cx[i], cy[i]);
                if (culling && (p.x < minX || p.x > maxX || p.y < minY || p.y > maxY)) continue;

                if (kind[i] == FlameField.KindSmoke)
                {
                    // Smoke gets no glow — it is what is left when the light has gone.
                    var sc = Smoke;
                    sc.a = (byte)(Mathf.Clamp01(life[i] / (float)FlameField.SmokeLifeTicks) * 90f);
                    si = Quad(ref v, _sharpIdx, si, p.x, p.y, cell, sc);
                    continue;
                }

                Color32 flame = FlameColour(cx[i], cy[i], age[i]);

                var gc = flame;
                gc.a = (byte)(GlowIntensity * 255f);
                gi = Quad(ref v, _glowIdx, gi,
                          p.x - (glow - cell) * 0.5f, p.y - (glow - cell) * 0.5f, glow, gc);

                var fc = flame;
                fc.a = (byte)(SharpAlpha * 255f);
                si = Quad(ref v, _sharpIdx, si, p.x, p.y, cell, fc);
            }

            _mesh.Clear();
            if (v == 0) return;

            _mesh.subMeshCount = 2;                  // Clear() drops it back to one
            _mesh.SetVertices(_verts, 0, v);
            _mesh.SetColors(_colors, 0, v);
            _mesh.SetIndices(_glowIdx, 0, gi, MeshTopology.Triangles, 0, false);
            _mesh.SetIndices(_sharpIdx, 0, si, MeshTopology.Triangles, 1, false);

            // Set by hand: recalculating bounds over tens of thousands of verts every frame
            // costs more than the mesh build itself.
            _mesh.bounds = culling
                ? new Bounds(new Vector3((minX + maxX) * 0.5f, (minY + maxY) * 0.5f, 0f),
                             new Vector3(maxX - minX + 4f, maxY - minY + 4f, 1f))
                : new Bounds(Vector3.zero, new Vector3(1e5f, 1e5f, 1f));
        }

        /// <summary>
        /// Colour for a flame cell. Age does the work: a cell is white-hot the tick it is
        /// born and a dull red by the time it has drifted a dozen pixels up. The per-cell
        /// jitter is Noita's own trick (materialColour's colour seed, +/-12 per channel) and
        /// is what stops a wall of flame reading as one flat orange rectangle.
        /// </summary>
        private static Color32 FlameColour(int cx, int cy, int age)
        {
            float t = Mathf.Clamp01(age / CoolTicks);
            Color32 c = t < 0.35f
                ? Color32.Lerp(Hot, Mid, t / 0.35f)
                : Color32.Lerp(Mid, Cool, (t - 0.35f) / 0.65f);

            int j = (int)(Hash01(cx, cy) * 24f) - 12;
            return new Color32(
                (byte)Mathf.Clamp(c.r + j, 0, 255),
                (byte)Mathf.Clamp(c.g + j, 0, 255),
                (byte)Mathf.Clamp(c.b + j, 0, 255),
                255);
        }

        private int Quad(ref int v, int[] idx, int n, float x, float y, float size, Color32 c)
        {
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

            idx[n] = b;
            idx[n + 1] = b + 1;
            idx[n + 2] = b + 2;
            idx[n + 3] = b;
            idx[n + 4] = b + 2;
            idx[n + 5] = b + 3;
            return n + 6;
        }

        private void EnsureCapacity(int cells)
        {
            int verts = cells * 8;          // a flame contributes a glow quad and a sharp one
            if (_verts.Length >= verts) return;

            int n = Mathf.NextPowerOfTwo(verts);
            _verts = new Vector3[n];
            _colors = new Color32[n];
            _glowIdx = new int[n / 4 * 6];
            _sharpIdx = new int[n / 4 * 6];
        }

        private static float Hash01(int x, int y)
        {
            unchecked
            {
                uint h = (uint)(x * 73856093) ^ (uint)(y * 19349663);
                h ^= h >> 13;
                h *= 0x85EBCA6B;
                h ^= h >> 16;
                return (h & 0xFFFFFF) / 16777216f;
            }
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
            if (_mesh) Destroy(_mesh);
            if (_glowMat) Destroy(_glowMat);
            if (_sharpMat) Destroy(_sharpMat);
        }
    }
}
