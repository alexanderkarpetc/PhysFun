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
    /// pixel adjacency, so it keeps working after pieces are split, moved or retraced. It is
    /// measured once per pair and cached (see <see cref="Node"/>), so a pass costs a walk over
    /// the links rather than a test of every pair.
    ///
    /// What comes loose is welded rather than released chunk by chunk — see
    /// <see cref="TerrainPiece"/>. The chunk grid is how terrain is edited, not how it is
    /// built, and a falling slab should not be able to show the player where the seams were.
    /// </summary>
    [DefaultExecutionOrder(1100)]
    public sealed class TerrainSupportSystem : MonoBehaviour
    {
        /// <summary>
        /// How far apart two colliders may be before the pass stops considering them at all.
        ///
        /// It is a shortlist, not the answer. A traced collider is a <em>simplified</em> outline
        /// — <see cref="PixelContour.MinSimplifyPixels"/> lets it cut a couple of pixels either
        /// way — so its distance cannot settle anything at this scale: two chunks made of
        /// neighbouring pixels can measure as apart, and two halves with a crack between them
        /// can measure as overlapping. Inside this radius the pixels decide, in
        /// <see cref="PixelsTouch"/>.
        /// </summary>
        public static float ContactEpsilon = 0.06f;

        /// <summary>How close two solid pixels have to be to count as the same lump.</summary>
        public static int ContactPixels = 1;

        /// <summary>Cap on the band sampled by the pixel test, per axis. Past it the pass gives
        /// the pair the benefit of the doubt rather than spending the frame on it.</summary>
        private const int MaxBandSamples = 256;

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

        /// <summary>
        /// One anchored body in the contact graph. Which bodies touch which is the expensive
        /// question - a collider distance and a pixel scan per pair - and between two pieces of
        /// standing terrain the answer only changes when one of them changes. So each pair is
        /// asked once and the answer kept as a link; a body is only re-asked about when it is
        /// new, its pixel record has moved on (<see cref="PixelSpriteRegistry.Record.Version"/>)
        /// or its collider has changed shape. The pass itself is then a walk over the links,
        /// cheap enough to run on every poll with thousands of chunks standing - which is what
        /// a whole floor of rooms is.
        /// </summary>
        private sealed class Node
        {
            public int Id;
            public int Index;                       // in NodeList
            public TerrainBody Body;
            public Collider2D Col;
            public Bounds Bounds;
            public PixelSpriteRegistry.Record Record;
            public int Version;
            public bool Stale = true;
            public bool OnBedrock;
            public int Mark;                        // pass stamp: relinked / supported / grouped
            public readonly List<Node> Links = new();
            public readonly List<long> Cells = new();
        }

        /// <summary>Side of a cell in the spatial hash that finds a body's neighbours.</summary>
        private const float GridCell = 2f;

        private static readonly Dictionary<int, Node> Nodes = new();
        private static readonly List<Node> NodeList = new();
        private static readonly Dictionary<long, List<Node>> Grid = new();
        private static TerrainSupportSystem _instance;
        private static bool _dirty;
        private static bool _warnedNoBedrock;
        private static int _stamp;

        // Per-pass scratch, kept alive so a pass allocates as little as possible.
        private static readonly List<Node> Stale = new();
        private static readonly List<Node> Frontier = new();
        private static readonly List<Node> Loose = new();
        private static readonly HashSet<Node> Candidates = new();
        private static readonly List<Collider2D> AnchorHits = new();
        private static readonly List<List<TerrainBody>> Groups = new();

        private float _nextPoll;

        public static void Register(TerrainBody body)
        {
            // Support is a runtime concern; edit-mode preview chunks must not pile up here.
            if (!Application.isPlaying) return;
            if (!body) return;
            int id = body.GetInstanceID();
            if (Nodes.ContainsKey(id)) return;
            var node = new Node { Id = id, Body = body, Index = NodeList.Count };
            Nodes.Add(id, node);
            NodeList.Add(node);
            _dirty = true;
        }

        public static void Unregister(TerrainBody body)
        {
            if (ReferenceEquals(body, null)) return;
            if (!Nodes.Remove(body.GetInstanceID(), out var node)) return;
            Drop(node);
            _dirty = true;
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
            Nodes.Clear();
            NodeList.Clear();
            Grid.Clear();
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
            if (NodeList.Count == 0) { _dirty = false; return; }
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

            // Who is gone, and who has changed since their links were worked out.
            var reg = PixelSpriteRegistry.Instance;
            Stale.Clear();
            for (int i = NodeList.Count - 1; i >= 0; i--)
            {
                var node = NodeList[i];
                if (!node.Body || !node.Body.Anchored)
                {
                    Nodes.Remove(node.Id);
                    Drop(node);
                    continue;
                }
                reg.TryGet(node.Body.gameObject, out var rec);
                int version = rec != null ? rec.Version : 0;
                if (!node.Col) node.Col = node.Body.GetComponent<Collider2D>();
                bool reshaped = node.Col && node.Col.bounds != node.Bounds;
                if (node.Stale || reshaped || rec != node.Record || version != node.Version)
                {
                    node.Record = rec;
                    node.Version = version;
                    Stale.Add(node);
                }
            }
            if (NodeList.Count == 0) return;
            if (Stale.Count > 0) Relink();

            // Support spreads out from bedrock along the links.
            int supported = ++_stamp;
            Frontier.Clear();
            foreach (var node in NodeList)
            {
                if (!node.Body.Bedrock && !node.OnBedrock) continue;
                node.Mark = supported;
                Frontier.Add(node);
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

            for (int q = 0; q < Frontier.Count; q++)
                foreach (var next in Frontier[q].Links)
                {
                    if (next.Mark == supported) continue;
                    next.Mark = supported;
                    Frontier.Add(next);
                }

            Loose.Clear();
            foreach (var node in NodeList)
                if (node.Mark != supported) Loose.Add(node);
            if (Loose.Count == 0) return;

            // Everything the pass could not reach comes down — but as few bodies as possible.
            // Chunks are a unit of editing, not of physics: a six-chunk overhang that arrives
            // as six rigid bodies overlapping along their shared seams shoves itself apart in
            // the frame it is created, and a slab reads as a dropped stack of bricks. Chunks
            // that are still linked to each other are still one lump, so they are welded into
            // one falling body.
            int grouped = ++_stamp;
            Groups.Clear();
            foreach (var seed in Loose)
            {
                if (seed.Mark == grouped) continue;
                var bodies = new List<TerrainBody>();
                Frontier.Clear();
                Frontier.Add(seed);
                seed.Mark = grouped;
                for (int q = 0; q < Frontier.Count; q++)
                {
                    var a = Frontier[q];
                    if (a.Body) bodies.Add(a.Body);
                    foreach (var b in a.Links)
                    {
                        if (b.Mark == supported || b.Mark == grouped) continue;
                        b.Mark = grouped;
                        Frontier.Add(b);
                    }
                }
                Groups.Add(bodies);
            }

            // Off the graph first, and all of it: welding calls Release, which unregisters.
            foreach (var node in Loose)
            {
                Nodes.Remove(node.Id);
                Drop(node);
            }
            foreach (var bodies in Groups) TerrainPiece.Weld(bodies);
            Groups.Clear();
        }

        /// <summary>Work out the links of every stale node again.</summary>
        private static void Relink()
        {
            // Pull them all out first, so a pair of stale neighbours is decided once, by
            // whichever of the two comes first, and nothing stays linked to an old outline.
            foreach (var node in Stale)
            {
                Unlink(node);
                Unhash(node);
                if (!node.Col) node.Col = node.Body.GetComponent<Collider2D>();
                node.Bounds = node.Col
                    ? node.Col.bounds
                    : new Bounds(node.Body.transform.position, Vector3.zero);
                Hash(node);
            }

            int done = ++_stamp;
            int mask = BedrockMask;
            foreach (var node in Stale)
            {
                node.Mark = done;
                // A body whose collider is not there yet is asked about again next pass.
                node.Stale = !node.Col;
                if (!node.Col) continue;

                node.OnBedrock = mask != 0 && TouchesBedrock(node, mask);

                Candidates.Clear();
                foreach (var key in node.Cells)
                    if (Grid.TryGetValue(key, out var bucket))
                        foreach (var other in bucket)
                            if (other != node && other.Mark != done) Candidates.Add(other);

                foreach (var other in Candidates)
                {
                    if (!other.Col) continue;
                    if (!Overlaps(node.Bounds, other.Bounds)) continue;
                    if (!Touching(node.Col, other.Col)) continue;
                    node.Links.Add(other);
                    other.Links.Add(node);
                }
            }
        }

        private static bool TouchesBedrock(Node node, int mask)
        {
            var region = node.Bounds;
            region.Expand(ContactEpsilon * 4f);
            var filter = new ContactFilter2D
            {
                useLayerMask = true,
                layerMask = mask,
                useTriggers = Physics2D.queriesHitTriggers,
            };
            AnchorHits.Clear();
            Physics2D.OverlapArea(region.min, region.max, filter, AnchorHits);
            foreach (var anchor in AnchorHits)
            {
                if (!anchor || !Overlaps(node.Bounds, anchor.bounds)) continue;
                if (Touching(node.Col, anchor)) return true;
            }
            return false;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Graph bookkeeping
        // ─────────────────────────────────────────────────────────────────────────

        private static void Drop(Node node)
        {
            Unlink(node);
            Unhash(node);
            int last = NodeList.Count - 1;
            if (node.Index <= last && NodeList[node.Index] == node)
            {
                NodeList[node.Index] = NodeList[last];
                NodeList[node.Index].Index = node.Index;
                NodeList.RemoveAt(last);
            }
        }

        private static void Unlink(Node node)
        {
            foreach (var other in node.Links) other.Links.Remove(node);
            node.Links.Clear();
        }

        private static void Hash(Node node)
        {
            var b = node.Bounds;
            float e = ContactEpsilon;
            int x0 = Mathf.FloorToInt((b.min.x - e) / GridCell), x1 = Mathf.FloorToInt((b.max.x + e) / GridCell);
            int y0 = Mathf.FloorToInt((b.min.y - e) / GridCell), y1 = Mathf.FloorToInt((b.max.y + e) / GridCell);
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                long key = ((long)x << 32) | (uint)y;
                if (!Grid.TryGetValue(key, out var bucket)) Grid[key] = bucket = new List<Node>();
                bucket.Add(node);
                node.Cells.Add(key);
            }
        }

        private static void Unhash(Node node)
        {
            foreach (var key in node.Cells)
                if (Grid.TryGetValue(key, out var bucket))
                {
                    bucket.Remove(node);
                    if (bucket.Count == 0) Grid.Remove(key);
                }
            node.Cells.Clear();
        }

        private static bool Overlaps(Bounds a, Bounds b)
        {
            float e = ContactEpsilon;
            return a.min.x - e <= b.max.x && a.max.x + e >= b.min.x &&
                   a.min.y - e <= b.max.y && a.max.y + e >= b.min.y;
        }

        /// <summary>
        /// Are these two part of the same lump? Public because it is not only the support pass
        /// that needs the answer: a piece that has already fallen has to be able to work out
        /// when a crack has divided it, and it must reach that conclusion the same way.
        /// </summary>
        public static bool Touching(Collider2D a, Collider2D b)
        {
            if (!a || !b || a == b) return false;

            // Cheap reject first: anything this far apart cannot be one lump however the
            // outlines were traced, and that is most pairs the O(n²) walk ever looks at.
            var d = a.Distance(b);
            if (!d.isValid || d.distance > ContactEpsilon) return false;

            return PixelsTouch(a, b);
        }

        /// <summary>
        /// Are these two actually made of neighbouring pixels?
        ///
        /// This is what makes a thin crack work. The alternative — trusting collider distance —
        /// forces every cut to be wider than the simplification error on both sides, five or six
        /// pixels at terrain resolution, which looks like a slot milled through the rock rather
        /// than like something broken. It fails in the other direction too: two chunks that are
        /// genuinely pixel-adjacent along a ragged seam can measure as apart, and the pass drops
        /// a wall that was standing perfectly well.
        ///
        /// Only the strip where the two could possibly meet is scanned, and the first adjacency
        /// found ends it — which is the common case, since most pairs asked about are touching.
        /// Anything without a pixel record (bedrock, a prop) is left to the collider test.
        /// </summary>
        private static bool PixelsTouch(Collider2D a, Collider2D b)
        {
            var reg = PixelSpriteRegistry.Instance;
            if (!reg.TryGet(a.gameObject, out var ra)) return true;
            if (!reg.TryGet(b.gameObject, out var rb)) return true;

            var band = a.bounds;
            var other = b.bounds;
            band.Expand(ContactEpsilon * 2f);
            other.Expand(ContactEpsilon * 2f);
            if (!band.Intersects(other)) return false;
            band.SetMinMax(Vector3.Max(band.min, other.min), Vector3.Min(band.max, other.max));

            float pxPerUnit = ra.PixelsPerWorldUnit;
            if (pxPerUnit < 1e-3f) return true;
            float step = 1f / pxPerUnit;
            float reach = Mathf.Max(1, ContactPixels) * step;

            int nx = Mathf.CeilToInt(band.size.x * pxPerUnit) + 1;
            int ny = Mathf.CeilToInt(band.size.y * pxPerUnit) + 1;
            if (nx > MaxBandSamples || ny > MaxBandSamples) return true;

            for (int iy = 0; iy < ny; iy++)
            {
                float wy = band.min.y + iy * step;
                for (int ix = 0; ix < nx; ix++)
                {
                    var p = new Vector2(band.min.x + ix * step, wy);
                    if (!SolidAt(ra, p)) continue;

                    for (int oy = -1; oy <= 1; oy++)
                    for (int ox = -1; ox <= 1; ox++)
                        if (SolidAt(rb, p + new Vector2(ox * reach, oy * reach))) return true;
                }
            }
            return false;
        }

        private static bool SolidAt(PixelSpriteRegistry.Record rec, Vector2 world) =>
            rec.Go && rec.WorldToPixel(world, out int x, out int y) &&
            rec.Pixels[y * rec.Width + x].a != 0;
    }
}
