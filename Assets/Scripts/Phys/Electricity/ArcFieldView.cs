using Unity.Profiling;
using UnityEngine;

namespace Phys.Electricity
{
    /// <summary>
    /// Draws <see cref="ArcField"/> as one mesh, the same two ways the fire is drawn: a wide
    /// additive glow and, over it, the hard one-pixel cells themselves. Same shader, same
    /// reason — a single flat layer of bright pixels reads as confetti, and what makes a bolt
    /// look like a bolt is the bloom it sits inside.
    ///
    /// The one difference from <see cref="Fire.FlameFieldView"/> is where the colour comes
    /// from: each cell's brightness. A bolt's core is written at full and burns white; its
    /// edges, forks and the shimmer over the metal are written dimmer and come out blue; and
    /// as cells decay between redraws they sink from white through blue to nothing.
    /// </summary>
    [DefaultExecutionOrder(1100)]
    public sealed class ArcFieldView : MonoBehaviour
    {
        /// <summary>Over the fire, which is already over everything else.</summary>
        public static int SortingOrder = 520;

        /// <summary>How many cell widths the glow spreads past the cell casting it.</summary>
        public static float GlowSpread = 7f;

        /// <summary>
        /// Per-cell glow strength. Higher than the fire's because a bolt is a thin line rather
        /// than a mass — there are far fewer neighbours for the glow to sum with.
        /// </summary>
        public static float GlowIntensity = 0.075f;

        public static float SharpAlpha = 1f;

        // White at the head, through a cold blue-white, into the deep blue it disappears at.
        public static Color32 Hot = new(255, 255, 255, 255);
        public static Color32 Mid = new(150, 215, 255, 255);
        public static Color32 Cool = new(52, 92, 255, 255);

        private static ArcFieldView _instance;

        private Mesh _mesh;
        private Material _glowMat;
        private Material _sharpMat;
        private Camera _cam;

        private Vector3[] _verts = new Vector3[2048];
        private Color32[] _colors = new Color32[2048];
        private int[] _glowIdx = new int[3072];
        private int[] _sharpIdx = new int[3072];

        public static void Install()
        {
            if (_instance) return;

            var go = new GameObject("~ArcFieldView") { hideFlags = HideFlags.HideAndDontSave };
            _instance = go.AddComponent<ArcFieldView>();
        }

        private void Awake()
        {
            _mesh = new Mesh { name = "ArcField", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            _mesh.MarkDynamic();
            _mesh.subMeshCount = 2;

            var shader = Resources.Load<Shader>("Shaders/FlameField");
            if (!shader) shader = Shader.Find("Sprites/Default");

            _glowMat = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            _glowMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            _glowMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.One);

            // Additive as well, unlike the fire's sharp layer: electricity is light, not
            // burning matter, so it should brighten what is behind it rather than replace it.
            _sharpMat = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            _sharpMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            _sharpMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.One);

            var mf = gameObject.AddComponent<MeshFilter>();
            mf.sharedMesh = _mesh;

            var mr = gameObject.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { _glowMat, _sharpMat };
            mr.sortingOrder = SortingOrder;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
        }

        private static readonly ProfilerMarker s_mesh = new("Electricity.ArcMesh");

        private void LateUpdate()
        {
            using var _ = s_mesh.Auto();

            var field = ArcField.Instance;
            int count = field.Count;
            if (count == 0)
            {
                if (_mesh.vertexCount > 0) _mesh.Clear();
                return;
            }

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

            float cell = ArcField.CellSize;
            float glow = cell * GlowSpread;
            var cx = field.CellX;
            var cy = field.CellY;
            var lum = field.Lum;

            int v = 0, gi = 0, si = 0;

            for (int i = 0; i < count; i++)
            {
                Vector2 p = ArcField.CellToWorld(cx[i], cy[i]);
                if (culling && (p.x < minX || p.x > maxX || p.y < minY || p.y > maxY)) continue;

                float dim = lum[i] / 255f;
                Color32 arc = ArcColour(1f - dim);

                var gc = arc;
                gc.a = (byte)(GlowIntensity * dim * 255f);
                gi = Quad(ref v, _glowIdx, gi,
                          p.x - (glow - cell) * 0.5f, p.y - (glow - cell) * 0.5f, glow, gc);

                var sc = arc;
                sc.a = (byte)(SharpAlpha * Mathf.Sqrt(dim) * 255f);
                si = Quad(ref v, _sharpIdx, si, p.x, p.y, cell, sc);
            }

            _mesh.Clear();
            if (v == 0) return;

            _mesh.subMeshCount = 2;                  // Clear() drops it back to one
            _mesh.SetVertices(_verts, 0, v);
            _mesh.SetColors(_colors, 0, v);
            _mesh.SetIndices(_glowIdx, 0, gi, MeshTopology.Triangles, 0, false);
            _mesh.SetIndices(_sharpIdx, 0, si, MeshTopology.Triangles, 1, false);

            _mesh.bounds = culling
                ? new Bounds(new Vector3((minX + maxX) * 0.5f, (minY + maxY) * 0.5f, 0f),
                             new Vector3(maxX - minX + 4f, maxY - minY + 4f, 1f))
                : new Bounds(Vector3.zero, new Vector3(1e5f, 1e5f, 1f));
        }

        private static Color32 ArcColour(float t) =>
            t < 0.3f
                ? Color32.Lerp(Hot, Mid, t / 0.3f)
                : Color32.Lerp(Mid, Cool, (t - 0.3f) / 0.7f);

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
            int verts = cells * 8;          // a cell contributes a glow quad and a sharp one
            if (_verts.Length >= verts) return;

            int n = Mathf.NextPowerOfTwo(verts);
            _verts = new Vector3[n];
            _colors = new Color32[n];
            _glowIdx = new int[n / 4 * 6];
            _sharpIdx = new int[n / 4 * 6];
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
