using System.Collections.Generic;
using Phys.Pixels;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// Decides which terrain is still standing. Every <see cref="TerrainBody"/> that is
    /// anchored takes part in a reachability pass: starting from bedrock (bodies flagged as
    /// such, plus anything touching a collider on <see cref="BedrockMask"/> — the map
    /// borders), support spreads to every anchored body that touches one already supported.
    /// Whatever is left over is no longer held up by anything, so it detaches and falls.
    ///
    /// That single rule covers the whole "Noita terrain" feel: carve a lump out of a wall
    /// and the lump drops, dig a tunnel straight through and both sides stay put because
    /// each still reaches the border, blow away a pillar and everything it was holding up
    /// comes down with it.
    ///
    /// Contact is measured with <see cref="Collider2D.Distance"/> rather than tracked as
    /// pixel adjacency, so it keeps working after pieces are split, moved or retraced.
    /// </summary>
    [DefaultExecutionOrder(1100)]
    public sealed class TerrainSupportSystem : MonoBehaviour
    {
        /// <summary>Gap (world units) still counted as "touching". Collider simplification
        /// moves outlines by a fraction of a pixel, so this can't be zero.</summary>
        public static float ContactEpsilon = 0.06f;

        /// <summary>Seconds between passes when nothing announced a change. Pixel edits that
        /// only break the contact <em>between</em> two chunks raise no event, so the pass
        /// also runs on a slow poll.</summary>
        public static float PollInterval = 0.3f;

        /// <summary>Layers that count as immovable ground. Set from
        /// <see cref="TerrainBuilder"/>; defaults to the "Untouchable" map borders.</summary>
        public static int BedrockMask
        {
            get
            {
                if (_bedrockMask == UnsetMask) _bedrockMask = LayerMask.GetMask("Untouchable");
                return _bedrockMask;
            }
            set => _bedrockMask = value;
        }

        private const int UnsetMask = -1;
        private static int _bedrockMask = UnsetMask;

        private static readonly List<TerrainBody> Bodies = new();
        private static TerrainSupportSystem _instance;
        private static bool _dirty;
        private static bool _warnedNoBedrock;

        // Per-pass scratch, kept alive so a pass allocates nothing.
        private static readonly List<Collider2D> Cols = new();
        private static readonly List<Bounds> Bnds = new();
        private static readonly List<Collider2D> Anchors = new();
        private static readonly List<int> Frontier = new();
        private static bool[] _supported = new bool[64];

        private float _nextPoll;

        public static void Register(TerrainBody body)
        {
            // Support is a runtime concern; edit-mode preview chunks must not pile up here.
            if (!Application.isPlaying) return;
            if (!body || Bodies.Contains(body)) return;
            Bodies.Add(body);
            _dirty = true;
        }

        public static void Unregister(TerrainBody body)
        {
            if (Bodies.Remove(body)) _dirty = true;
        }

        /// <summary>Ask for a pass on the next <c>LateUpdate</c>.</summary>
        public static void MarkDirty() => _dirty = true;

        /// <summary>Run a pass right now — use after an interaction that must settle
        /// on this exact frame.</summary>
        public static void Refresh()
        {
            if (_instance) _instance.Recompute();
            else _dirty = true;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode()
        {
            // Play mode can be entered without a domain reload, so the statics survive.
            Bodies.Clear();
            _dirty = false;
            _warnedNoBedrock = false;
            _bedrockMask = UnsetMask;
            _instance = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            if (_instance) return;
            var go = new GameObject("~TerrainSupportSystem") { hideFlags = HideFlags.HideAndDontSave };
            _instance = go.AddComponent<TerrainSupportSystem>();

            // A split hands out new pieces that may be floating free; a consumed object
            // may have been the only thing holding its neighbours up.
            var reg = PixelSpriteRegistry.Instance;
            reg.Split += (original, parts) => _dirty = true;
            reg.Consumed += consumed => _dirty = true;
        }

        private void LateUpdate()
        {
            if (Bodies.Count == 0) { _dirty = false; return; }
            if (!_dirty && Time.unscaledTime < _nextPoll) return;
            Recompute();
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
        }

        private void Recompute()
        {
            _dirty = false;
            _nextPoll = Time.unscaledTime + PollInterval;

            for (int i = Bodies.Count - 1; i >= 0; i--)
            {
                var body = Bodies[i];
                if (!body || !body.Anchored) Bodies.RemoveAt(i);
            }

            int n = Bodies.Count;
            if (n == 0) return;

            Cols.Clear();
            Bnds.Clear();
            for (int i = 0; i < n; i++)
            {
                var col = Bodies[i].GetComponent<Collider2D>();
                Cols.Add(col);
                Bnds.Add(col
                    ? col.bounds
                    : new Bounds(Bodies[i].transform.position, Vector3.zero));
            }

            CollectAnchors();

            if (_supported.Length < n) _supported = new bool[Mathf.NextPowerOfTwo(n)];
            for (int i = 0; i < n; i++) _supported[i] = false;

            Frontier.Clear();
            for (int i = 0; i < n; i++)
            {
                if (!Bodies[i].Bedrock && !TouchesAnchor(Cols[i], Bnds[i])) continue;
                _supported[i] = true;
                Frontier.Add(i);
            }

            if (Frontier.Count == 0)
            {
                // No bedrock anywhere means the pass would sweep the whole map into the air.
                // Far more likely the mask is wrong, so leave everything standing and say so.
                if (!_warnedNoBedrock)
                {
                    _warnedNoBedrock = true;
                    Debug.LogWarning("TerrainSupportSystem: no bedrock found — terrain will never " +
                                     "fall. Check TerrainSupportSystem.BedrockMask (expects the map " +
                                     "border layer, \"Untouchable\" by default).");
                }
                return;
            }

            // Breadth-first over "touching" pairs. Each body is scanned against the rest
            // once, when it is popped, so this stays O(n²) AABB tests at worst.
            for (int q = 0; q < Frontier.Count; q++)
            {
                int i = Frontier[q];
                var ci = Cols[i];
                if (!ci) continue;
                var bi = Bnds[i];

                for (int j = 0; j < n; j++)
                {
                    if (_supported[j]) continue;
                    if (!Overlaps(bi, Bnds[j])) continue;
                    if (!Touching(ci, Cols[j])) continue;
                    _supported[j] = true;
                    Frontier.Add(j);
                }
            }

            for (int i = n - 1; i >= 0; i--)
            {
                if (_supported[i]) continue;
                var body = Bodies[i];
                Bodies.RemoveAt(i);
                if (body) body.Detach();
            }
        }

        /// <summary>Immovable colliders anywhere near the terrain, refreshed once per pass.</summary>
        private static void CollectAnchors()
        {
            Anchors.Clear();
            int mask = BedrockMask;
            if (mask == 0 || Bnds.Count == 0) return;

            var region = Bnds[0];
            for (int i = 1; i < Bnds.Count; i++) region.Encapsulate(Bnds[i]);
            region.Expand(ContactEpsilon * 4f);

            var found = Physics2D.OverlapAreaAll(region.min, region.max, mask);
            for (int i = 0; i < found.Length; i++)
                if (found[i]) Anchors.Add(found[i]);
        }

        private static bool TouchesAnchor(Collider2D col, Bounds bounds)
        {
            if (!col) return false;
            for (int i = 0; i < Anchors.Count; i++)
            {
                var anchor = Anchors[i];
                if (!anchor) continue;
                if (!Overlaps(bounds, anchor.bounds)) continue;
                if (Touching(col, anchor)) return true;
            }
            return false;
        }

        private static bool Overlaps(Bounds a, Bounds b)
        {
            float e = ContactEpsilon;
            return a.min.x - e <= b.max.x && a.max.x + e >= b.min.x &&
                   a.min.y - e <= b.max.y && a.max.y + e >= b.min.y;
        }

        private static bool Touching(Collider2D a, Collider2D b)
        {
            if (!a || !b || a == b) return false;
            var d = a.Distance(b);
            return d.isValid && d.distance <= ContactEpsilon;
        }
    }
}
