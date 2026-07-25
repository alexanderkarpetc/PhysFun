using System.Collections.Generic;
using Materials;
using Phys.Pixels;
using UnityEngine;

namespace Phys.Fire
{
    /// <summary>
    /// Noita-style pixel fire. Fire is not a particle effect stuck on top of a sprite —
    /// individual texture pixels are taken by the flame, glow through an ember gradient
    /// as their fuel drains, and then disappear, so an object is genuinely eaten away.
    /// Once enough pixels are gone the shared <see cref="PixelSpriteRegistry"/> notices
    /// the object fell apart and splits it into separate physics bodies for free.
    ///
    /// Ticked by <see cref="PixelSpriteDriver"/> before the pixel upload each frame.
    /// </summary>
    public sealed class FireSystem
    {
        public static FireSystem Instance { get; private set; } = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => Instance = new FireSystem();

        /// <summary>Simulation steps per second. Independent of framerate.</summary>
        public static float TicksPerSecond = 40f;

        /// <summary>Layers fire is allowed to jump to on contact.</summary>
        public static int ContactMask = ~0;

        /// <summary>World-space radius of a contact-spread probe.</summary>
        public static float ContactProbeRadius = 0.12f;

        private sealed class Burn
        {
            public GameObject Go;
            public PixelSpriteRegistry.Record Rec;   // reference identity doubles as a staleness check
            public PhysMaterial Mat;

            public byte[] Fuel;      // 255 = untouched, 0 = spent (or never flammable, e.g. charcoal)
            public bool[] Alight;
            public List<int> Active = new();
            public List<int> Next = new();

            public int Ticks;
            public uint Rng;

            // Step-scoped dirty rect over the pixels this burn repainted.
            public int sx0, sy0, sx1, sy1;

            public float NextFloat()
            {
                Rng ^= Rng << 13;
                Rng ^= Rng >> 17;
                Rng ^= Rng << 5;
                return (Rng & 0xFFFFFF) / 16777216f;
            }

            public void Touch(int x, int y)
            {
                if (x < sx0) sx0 = x;
                if (y < sy0) sy0 = y;
                if (x > sx1) sx1 = x;
                if (y > sy1) sy1 = y;
            }
        }

        private readonly Dictionary<GameObject, Burn> _burns = new();
        private readonly List<GameObject> _dead = new();
        private readonly List<Burn> _stepList = new();
        private readonly List<Collider2D> _probe = new();

        private PixelSpriteRegistry _reg;
        private float _accum;

        /// <summary>
        /// Attach to a registry. Called by <see cref="PixelSpriteDriver"/> once both
        /// singletons exist — the two reset hooks run in an undefined order, so this
        /// can't happen in the constructor.
        /// </summary>
        public void Bind(PixelSpriteRegistry registry)
        {
            if (_reg == registry) return;
            if (_reg != null) _reg.Split -= OnSplit;
            _reg = registry;
            _reg.Split += OnSplit;
        }

        public bool IsBurning(GameObject go) =>
            go && _burns.TryGetValue(go, out var b) && b.Active.Count > 0;

        // ─────────────────────────────────────────────────────────────────────────
        // Lighting things on fire
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Set alight every flammable pixel of <paramref name="go"/> inside a world-space
        /// circle. Returns false for non-flammable materials or a miss.
        /// </summary>
        public bool Ignite(GameObject go, Vector3 worldPos, float worldRadius)
        {
            if (!go || _reg == null) return false;

            var mat = MaterialLibrary.Of(go);
            if (!mat.Flammable) return false;

            var b = GetOrCreate(go, mat);
            if (b == null) return false;

            var rec = b.Rec;
            rec.WorldToPixel(worldPos, out int cx, out int cy);
            int r = Mathf.Max(1, Mathf.CeilToInt(worldRadius * rec.PixelsPerWorldUnit));
            int r2 = r * r;

            int xmin = Mathf.Max(0, cx - r);
            int xmax = Mathf.Min(rec.Width - 1, cx + r);
            int ymin = Mathf.Max(0, cy - r);
            int ymax = Mathf.Min(rec.Height - 1, cy + r);
            if (xmax < xmin || ymax < ymin) return false;

            ResetStepRect(b);
            int lit = 0;

            for (int y = ymin; y <= ymax; y++)
            {
                int dy = y - cy;
                int dy2 = dy * dy;
                int row = y * rec.Width;
                for (int x = xmin; x <= xmax; x++)
                {
                    int dx = x - cx;
                    if (dx * dx + dy2 > r2) continue;

                    int idx = row + x;
                    if (b.Alight[idx] || b.Fuel[idx] == 0) continue;
                    if (rec.Pixels[idx].a == 0) continue;

                    b.Alight[idx] = true;
                    b.Active.Add(idx);
                    rec.Pixels[idx] = Ember(b, mat, b.Fuel[idx], x, y);
                    b.Touch(x, y);
                    lit++;
                }
            }

            if (lit == 0) return false;
            rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);
            return true;
        }

        /// <summary>Put out the flames inside a world-space circle, leaving the pixels scorched.</summary>
        public void Extinguish(GameObject go, Vector3 worldPos, float worldRadius)
        {
            if (!go || !_burns.TryGetValue(go, out var b)) return;

            var rec = b.Rec;
            rec.WorldToPixel(worldPos, out int cx, out int cy);
            int r = Mathf.Max(1, Mathf.CeilToInt(worldRadius * rec.PixelsPerWorldUnit));
            int r2 = r * r;

            ResetStepRect(b);
            int doused = 0;

            for (int i = b.Active.Count - 1; i >= 0; i--)
            {
                int idx = b.Active[i];
                int x = idx % rec.Width, y = idx / rec.Width;
                int dx = x - cx, dy = y - cy;
                if (dx * dx + dy * dy > r2) continue;

                b.Alight[idx] = false;
                b.Active.RemoveAt(i);
                if (rec.Pixels[idx].a != 0) rec.Pixels[idx] = Scorch(b.Mat, b.Fuel[idx]);
                b.Touch(x, y);
                doused++;
            }

            if (doused > 0)
                rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);
        }

        /// <summary>Put out every flame on an object.</summary>
        public void Extinguish(GameObject go)
        {
            if (!go || !_burns.TryGetValue(go, out var b) || b.Active.Count == 0) return;

            var rec = b.Rec;
            ResetStepRect(b);
            foreach (int idx in b.Active)
            {
                b.Alight[idx] = false;
                if (rec.Pixels[idx].a != 0) rec.Pixels[idx] = Scorch(b.Mat, b.Fuel[idx]);
                b.Touch(idx % rec.Width, idx / rec.Width);
            }
            b.Active.Clear();
            rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Simulation
        // ─────────────────────────────────────────────────────────────────────────

        public void Tick(float deltaTime)
        {
            if (_reg == null || _burns.Count == 0) return;

            float step = 1f / Mathf.Max(1f, TicksPerSecond);
            _accum += Mathf.Min(deltaTime, 0.25f);

            // Cap catch-up so a hitch can't snowball into a burst of steps.
            int steps = 0;
            while (_accum >= step && steps < 3)
            {
                _accum -= step;
                steps++;
                Step();
            }
            if (_accum >= step) _accum = 0f;
        }

        private void Step()
        {
            // Snapshot: igniting a neighbouring object mutates the dictionary mid-step.
            _stepList.Clear();
            _dead.Clear();
            foreach (var kv in _burns)
            {
                if (!kv.Key) { _dead.Add(kv.Key); continue; }
                // A record swapped out from under us (the cracker replaces sprites
                // wholesale) means our pixel mirror is stale — let the fire die.
                if (!_reg.TryGet(kv.Key, out var rec) || rec != kv.Value.Rec) { _dead.Add(kv.Key); continue; }
                if (kv.Value.Active.Count > 0) _stepList.Add(kv.Value);
            }
            foreach (var go in _dead) _burns.Remove(go);

            foreach (var b in _stepList) StepBurn(b);
        }

        private void StepBurn(Burn b)
        {
            var rec = b.Rec;
            var mat = b.Mat;
            var pix = rec.Pixels;
            int w = rec.Width, h = rec.Height;

            b.Ticks++;
            ResetStepRect(b);

            // Flames climb: weight each neighbour by how much it points world-up.
            Vector2 up = b.Go.transform.InverseTransformDirection(Vector3.up);
            if (up.sqrMagnitude > 1e-6f) up.Normalize();
            float wRight = NeighbourWeight(mat.SpreadUpBias,  up.x);
            float wLeft  = NeighbourWeight(mat.SpreadUpBias, -up.x);
            float wUp    = NeighbourWeight(mat.SpreadUpBias,  up.y);
            float wDown  = NeighbourWeight(mat.SpreadUpBias, -up.y);

            float spreadThreshold = mat.SpreadDelay * 255f;
            b.Next.Clear();
            int cleared = 0;

            for (int i = 0; i < b.Active.Count; i++)
            {
                int idx = b.Active[i];
                if (!b.Alight[idx]) continue;      // doused since the list was built

                // Another tool (the eraser) may have removed this pixel out from under
                // us. Repainting it here would resurrect it, so let the flame drop.
                if (pix[idx].a == 0) { b.Alight[idx] = false; b.Fuel[idx] = 0; continue; }

                int fuel = b.Fuel[idx];
                if (fuel == 0) { b.Alight[idx] = false; continue; }

                int x = idx % w, y = idx / w;

                float rate = mat.BurnRate * (1f + mat.BurnRateJitter * (b.NextFloat() * 2f - 1f));
                int consume = Mathf.Max(1, Mathf.RoundToInt(rate * 255f));
                int left = fuel - consume;

                if (left <= 0)
                {
                    b.Fuel[idx] = 0;
                    b.Alight[idx] = false;
                    if (LeavesChar(mat, x, y))
                    {
                        pix[idx] = mat.Charcoal;   // stays solid — a charred chunk
                    }
                    else
                    {
                        pix[idx].a = 0;            // taken by the fire
                        cleared++;
                    }
                }
                else
                {
                    b.Fuel[idx] = (byte)left;
                    pix[idx] = Ember(b, mat, left, x, y);
                    b.Next.Add(idx);

                    if (255 - left >= spreadThreshold)
                    {
                        if (x > 0)     TryIgnite(b, idx - 1, x - 1, y, wLeft);
                        if (x < w - 1) TryIgnite(b, idx + 1, x + 1, y, wRight);
                        if (y > 0)     TryIgnite(b, idx - w, x, y - 1, wDown);
                        if (y < h - 1) TryIgnite(b, idx + w, x, y + 1, wUp);
                    }
                }

                b.Touch(x, y);
            }

            (b.Active, b.Next) = (b.Next, b.Active);

            if (b.sx1 >= 0)
            {
                // Colliders only need to follow every few ticks — the outline barely moves
                // per step and retracing a PolygonCollider2D is the expensive part.
                bool retrace = cleared > 0 && b.Ticks % 5 == 0;
                rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, cleared, retrace);
            }

            TrySpreadToNeighbours(b);
        }

        private static float NeighbourWeight(float upBias, float alignment) =>
            Mathf.Clamp(1f + upBias * alignment, 0.15f, 2.5f);

        private static void TryIgnite(Burn b, int idx, int x, int y, float weight)
        {
            if (b.Alight[idx] || b.Fuel[idx] == 0) return;
            if (b.Rec.Pixels[idx].a == 0) return;

            // Static per-pixel "grain": some spots resist, some catch instantly. This is
            // what keeps the front ragged even when it advances close to a pixel per tick —
            // relying on the roll alone would give a clean expanding circle.
            float grain = 0.5f + 0.9f * Hash01(x >> 1, y >> 1, 3);
            if (b.NextFloat() >= b.Mat.SpreadChance * weight * grain) return;

            b.Alight[idx] = true;
            b.Next.Add(idx);
            b.Rec.Pixels[idx] = Ember(b, b.Mat, b.Fuel[idx], x, y);
            b.Touch(x, y);
        }

        /// <summary>Occasionally let a burning edge pixel set a touching flammable object alight.</summary>
        private void TrySpreadToNeighbours(Burn b)
        {
            if (b.Active.Count == 0) return;
            if (b.NextFloat() >= b.Mat.ContactSpreadChance) return;

            var rec = b.Rec;
            int w = rec.Width, h = rec.Height;

            for (int attempt = 0; attempt < 4; attempt++)
            {
                int idx = b.Active[(int)(b.NextFloat() * b.Active.Count)];
                int x = idx % w, y = idx / w;

                bool onEdge =
                    x == 0 || x == w - 1 || y == 0 || y == h - 1 ||
                    rec.Pixels[idx - 1].a == 0 || rec.Pixels[idx + 1].a == 0 ||
                    rec.Pixels[idx - w].a == 0 || rec.Pixels[idx + w].a == 0;
                if (!onEdge) continue;

                var world = rec.PixelToWorld(x, y);
                var filter = new ContactFilter2D { useTriggers = false, useLayerMask = true, layerMask = ContactMask };
                _probe.Clear();
                Physics2D.OverlapCircle(world, ContactProbeRadius, filter, _probe);
                foreach (var col in _probe)
                {
                    if (!col || col.gameObject == b.Go) continue;
                    Ignite(col.gameObject, world, ContactProbeRadius);
                }
                return;
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Splits
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// A burning object fell apart. Carry the fuel and flame state into each piece
        /// using the source rect, so the fire keeps burning across the break instead of
        /// resetting to pristine wood.
        /// </summary>
        private void OnSplit(GameObject original, IReadOnlyList<SplitPart> parts)
        {
            if (!_burns.TryGetValue(original, out var old)) return;
            _burns.Remove(original);

            int srcW = old.Rec.Width;
            int srcLen = old.Fuel.Length;

            foreach (var part in parts)
            {
                if (!part.Go || !_reg.TryGet(part.Go, out var rec)) continue;

                var b = NewBurn(part.Go, rec, old.Mat, seedFuel: false);
                b.Ticks = old.Ticks;
                var srcRect = part.SourceRect;

                for (int y = 0; y < rec.Height; y++)
                {
                    int srcRow = (srcRect.y + y) * srcW + srcRect.x;
                    int dstRow = y * rec.Width;
                    for (int x = 0; x < rec.Width; x++)
                    {
                        int dst = dstRow + x;
                        if (rec.Pixels[dst].a == 0) continue;

                        int src = srcRow + x;
                        if (src < 0 || src >= srcLen) continue;

                        b.Fuel[dst] = old.Fuel[src];
                        if (old.Alight[src] && b.Fuel[dst] > 0)
                        {
                            b.Alight[dst] = true;
                            b.Active.Add(dst);
                        }
                    }
                }

                _burns[part.Go] = b;
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // State
        // ─────────────────────────────────────────────────────────────────────────

        private Burn GetOrCreate(GameObject go, PhysMaterial mat)
        {
            var rec = _reg.Get(go);
            if (rec == null) return null;

            if (_burns.TryGetValue(go, out var b) && b.Rec == rec) return b;

            b = NewBurn(go, rec, mat, seedFuel: true);
            _burns[go] = b;
            return b;
        }

        private static Burn NewBurn(GameObject go, PixelSpriteRegistry.Record rec, PhysMaterial mat, bool seedFuel)
        {
            int n = rec.Pixels.Length;
            var b = new Burn
            {
                Go = go,
                Rec = rec,
                Mat = mat,
                Fuel = new byte[n],
                Alight = new bool[n],
                // Position-derived seed: two objects lit on the same frame still flicker apart.
                Rng = (uint)(go.GetInstanceID() * 2654435761u) | 1u,
            };

            if (seedFuel)
                for (int i = 0; i < n; i++)
                    if (rec.Pixels[i].a > 0) b.Fuel[i] = 255;

            return b;
        }

        private static void ResetStepRect(Burn b)
        {
            b.sx0 = int.MaxValue; b.sy0 = int.MaxValue;
            b.sx1 = -1; b.sy1 = -1;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Look
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Ember colour for a pixel with <paramref name="fuel"/> left, plus a per-tick flicker.</summary>
        private static Color32 Ember(Burn b, PhysMaterial mat, int fuel, int x, int y)
        {
            float t = fuel / 255f;
            Color32 c =
                t >= 0.5f  ? Color32.Lerp(mat.EmberMid,  mat.EmberHot,  (t - 0.5f) / 0.5f) :
                t >= 0.15f ? Color32.Lerp(mat.EmberCool, mat.EmberMid,  (t - 0.15f) / 0.35f) :
                             Color32.Lerp(mat.Charcoal,  mat.EmberCool, t / 0.15f);

            // Cheap spatial+temporal hash so the flame shimmers instead of sitting flat.
            float k = 0.80f + 0.20f * Hash01(x, y, b.Ticks);
            return new Color32(
                (byte)(c.r * k),
                (byte)(c.g * k),
                (byte)(c.b * k),
                255);
        }

        /// <summary>Colour left behind when a flame is put out before the pixel is spent.</summary>
        private static Color32 Scorch(PhysMaterial mat, int fuel)
        {
            var warm = new Color32(
                (byte)(mat.EmberCool.r * 0.45f),
                (byte)(mat.EmberCool.g * 0.45f),
                (byte)(mat.EmberCool.b * 0.45f),
                255);
            return Color32.Lerp(warm, mat.Charcoal, 1f - fuel / 255f);
        }

        /// <summary>
        /// Whether a spent pixel survives as charcoal. Sampled on a coarse grid so char
        /// forms chunks big enough to stand on their own as physics bodies after the
        /// split pass, rather than a dust of orphaned single pixels.
        /// </summary>
        private static bool LeavesChar(PhysMaterial mat, int x, int y)
        {
            if (mat.CharAmount <= 0f) return false;
            int clump = Mathf.Max(2, mat.CharClumpSize);
            if (Hash01(x / clump, y / clump, 7) >= mat.CharAmount) return false;
            // Erode the block edges a little so chunks don't read as perfect squares.
            return Hash01(x >> 1, y >> 1, 13) > 0.15f;
        }

        private static float Hash01(int x, int y, int z)
        {
            unchecked
            {
                uint h = (uint)(x * 73856093) ^ (uint)(y * 19349663) ^ (uint)(z * 83492791);
                h ^= h >> 13;
                h *= 0x85EBCA6B;
                h ^= h >> 16;
                return (h & 0xFFFFFF) / 16777216f;
            }
        }
    }
}
