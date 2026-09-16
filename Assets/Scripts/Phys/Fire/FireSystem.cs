using System.Collections.Generic;
using Materials;
using Phys.Pixels;
using UnityEngine;

namespace Phys.Fire
{
    /// <summary>
    /// The burning half of the fire: which pixels of an object are alight, how fast they are
    /// consumed, and — through <see cref="EmitFlames"/> — the flames they throw off. Pixels
    /// are taken by the fire one at a time, so an object is genuinely eaten away, and once
    /// enough are gone the shared <see cref="PixelSpriteRegistry"/> notices it fell apart and
    /// splits it into separate physics bodies.
    ///
    /// The flames themselves live in <see cref="FlameField"/>. That split is Noita's: a
    /// burning cell there only tracks its own fuel and spits fire cells into the empty
    /// space above it (ICell::UpdateFire at 0x7521f0, ICell::GenerateFlame at 0x751da0),
    /// and everything that looks like fire is those cells. The version of this file that
    /// tried to *be* the fire by tinting the sprite's own pixels orange could not look like
    /// anything but a tinted sprite.
    ///
    /// Ticked by <see cref="PixelSpriteDriver"/> before the pixel upload each frame.
    /// </summary>
    public sealed class FireSystem
    {
        public static FireSystem Instance { get; private set; } = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => Instance = new FireSystem();

        /// <summary>
        /// Simulation steps per second — fuel burn and spread only. Nothing animated depends
        /// on this any more: the flames run at <see cref="FlameField.TicksPerSecond"/>, so a
        /// slow burn tick no longer makes the fire *look* like it runs at 20 fps.
        /// </summary>
        public static float TicksPerSecond = 20f;

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

            /// <summary>
            /// Whether this pixel already has an entry in <see cref="Active"/>.
            ///
            /// Not the same thing as <see cref="Alight"/>: a pixel that suffocates goes out
            /// where it stands and is only dropped from the list on the next burn step, and in
            /// between a flame can relight it. Without this flag that relight appends a second
            /// entry for the same pixel — and since the step copies every lit entry into the
            /// next list, the duplicates breed. A fire that keeps relighting its own pixels
            /// doubles the list every few frames and takes the frame rate with it.
            /// </summary>
            public bool[] Listed;

            /// <summary>
            /// Noita's per-cell fire temperature (the byte at CellData+0x11, reset from
            /// temperature_of_fire). It is both how hot this pixel's flames are and its
            /// supply of air: it refills every time the pixel manages to throw off a flame
            /// and ticks down when it cannot, so a pixel sealed inside an object suffocates.
            /// </summary>
            public byte[] Heat;

            /// <summary>The sprite as it was before it caught. Char is mixed back into this,
            /// so burnt wood still looks like wood rather than like flat orange.</summary>
            public Color32[] Orig;

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

            int lit = 0;
            bool painted = false;
            ResetStepRect(b);

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
                    b.Heat[idx] = (byte)Mathf.Clamp(mat.TemperatureOfFire, 1, 255);
                    lit++;

                    if (!b.Listed[idx])
                    {
                        b.Listed[idx] = true;
                        b.Active.Add(idx);
                    }

                    // Relighting a pixel whose fuel has not moved paints it the colour it
                    // already is. Skipping that keeps the dirty rect — and with it the
                    // per-frame texture upload — down to what actually changed.
                    var c = Charred(b.Orig[idx], mat, b.Fuel[idx]);
                    if (!Same(rec.Pixels[idx], c))
                    {
                        rec.Pixels[idx] = c;
                        b.Touch(x, y);
                        painted = true;
                    }
                }
            }

            if (painted) rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);
            return lit > 0;
        }

        /// <summary>
        /// Set light to whatever flammable object sits at a world point. This is what a flame
        /// cell calls when it tries to ignite a neighbour (FlameField.SpendIgniteProbes,
        /// Noita's ICell::TryIgniteRandomNeighbour at 0x7520a0) — the flames, not the burning
        /// object, are what carries fire from one thing to the next.
        /// </summary>
        public void IgniteAt(Vector2 world, float radius)
        {
            var filter = new ContactFilter2D { useTriggers = false, useLayerMask = true, layerMask = ContactMask };
            _probe.Clear();
            Physics2D.OverlapCircle(world, radius + PixelSpriteRegistry.QueryMargin, filter, _probe);

            foreach (var col in _probe)
                if (col) Ignite(col.gameObject, world, radius);
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
                b.Listed[idx] = false;
                b.Active.RemoveAt(i);
                if (rec.Pixels[idx].a != 0) rec.Pixels[idx] = Scorch(b.Orig[idx], b.Mat, b.Fuel[idx]);
                b.Touch(x, y);
                doused++;
            }

            if (doused > 0)
                rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);

            // The flames standing over the doused pixels have to go too, or the fire looks
            // alive for another half second with nothing feeding it.
            FlameField.Instance.Douse(worldPos, worldRadius * 1.5f);
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
                b.Listed[idx] = false;
                if (rec.Pixels[idx].a != 0) rec.Pixels[idx] = Scorch(b.Orig[idx], b.Mat, b.Fuel[idx]);
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

        /// <summary>
        /// One grid frame of Noita's ICell::UpdateFire (0x7521f0), run for every pixel that is
        /// alight. Called by <see cref="FlameField"/> at its own 60 Hz tick, not at the burn
        /// tick, because this is what the fire actually looks like and it has to be smooth.
        ///
        /// Per pixel, per frame:
        /// <list type="number">
        /// <item>roll generates_flames% and try to put a flame in one of the three cells above
        ///       (0x751dd8 picks between up-left, up and up-right) — and only if that cell is
        ///       free, which is the whole of Noita's "can this pixel breathe" test;</item>
        /// <item>roll generates_smoke% and do the same with smoke;</item>
        /// <item>requires_oxygen: a pixel that got a flame out refills its heat, one that could
        ///       not loses a point, and at zero it stops burning (0x752549). That single rule
        ///       is why fire inside a sealed object dies instead of hollowing it out.</item>
        /// </list>
        /// </summary>
        public void EmitFlames()
        {
            if (_reg == null || _burns.Count == 0) return;

            _stepList.Clear();
            foreach (var kv in _burns)
            {
                if (!kv.Key) continue;
                if (!_reg.TryGet(kv.Key, out var rec) || rec != kv.Value.Rec) continue;
                if (kv.Value.Active.Count > 0) _stepList.Add(kv.Value);
            }

            foreach (var b in _stepList) EmitBurn(b);
        }

        private static void EmitBurn(Burn b)
        {
            var rec = b.Rec;
            var pix = rec.Pixels;
            var mat = b.Mat;
            int w = rec.Width;

            // One matrix for the whole object instead of a transform call per pixel.
            var l2w = b.Go.transform.localToWorldMatrix;
            float ppu = rec.Ppu;
            float cell = FlameField.CellSize;
            var field = FlameField.Instance;

            // World-to-pixel by hand as well, so venting costs no transform calls at all.
            var w2l = b.Go.transform.worldToLocalMatrix;

            for (int i = 0; i < b.Active.Count; i++)
            {
                int idx = b.Active[i];
                if (!b.Alight[idx] || pix[idx].a == 0) continue;

                bool rollFlame = field.NextFloat() * 100f < mat.GeneratesFlames;
                bool rollSmoke = field.NextFloat() * 100f < mat.GeneratesSmoke;
                bool vented = false;

                // Most pixels roll nothing on most frames, and those must not cost a matrix
                // multiply each: this runs over every lit pixel of every object, 60 times a second.
                if (rollFlame || rollSmoke)
                {
                    int x = idx % w, y = idx / w;
                    var world = (Vector2)l2w.MultiplyPoint3x4(new Vector3(
                        (x + 0.5f - rec.PivotPx.x) / ppu,
                        (y + 0.5f - rec.PivotPx.y) / ppu,
                        0f));

                    if (rollFlame)
                    {
                        // 0x751dd8: one of the three cells above, chosen at random.
                        var at = world + new Vector2((int)(field.NextFloat() * 3f) - 1, 1f) * cell;
                        if (!Buried(rec, w2l, at))
                        {
                            // 0x752505: the flame carries this pixel's heat, jittered 0.75..1.29.
                            int heat = Mathf.RoundToInt(b.Heat[idx] * (0.75f + 0.54f * field.NextFloat()));
                            vented = field.Emit(at, heat);
                        }
                    }

                    if (rollSmoke)
                    {
                        var at = world + new Vector2((int)(field.NextFloat() * 3f) - 1, 1f) * cell;
                        if (!Buried(rec, w2l, at)) field.EmitSmoke(at);
                    }
                }

                // 0x752549: vented pixels stay lit indefinitely, smothered ones count down.
                //
                // A pixel that goes out here is *not* repainted. It is mid-burn, its colour is
                // whatever its fuel says, and it will usually be relit within a few frames —
                // repainting it each time marked a dirty rect spanning the whole object every
                // grid frame, which is a full texture upload 60 times a second for no visible
                // change at all.
                if (vented) b.Heat[idx] = (byte)Mathf.Clamp(mat.TemperatureOfFire, 1, 255);
                else if (mat.RequiresOxygen && b.Heat[idx] > 0 && --b.Heat[idx] == 0) b.Alight[idx] = false;
            }
        }

        /// <summary>
        /// Whether a world point falls on a solid pixel of this object — Noita's
        /// <c>grid[nx,ny] != null</c> test before a flame is placed (0x751f1b), asked of the
        /// one object we already have the pixels for. Anything else the flame would have to
        /// pass through, it passes through.
        /// </summary>
        private static bool Buried(PixelSpriteRegistry.Record rec, Matrix4x4 worldToLocal, Vector2 world)
        {
            var local = worldToLocal.MultiplyPoint3x4(world);
            int px = Mathf.FloorToInt(local.x * rec.Ppu + rec.PivotPx.x);
            int py = Mathf.FloorToInt(local.y * rec.Ppu + rec.PivotPx.y);
            if (px < 0 || py < 0 || px >= rec.Width || py >= rec.Height) return false;
            return rec.Pixels[py * rec.Width + px].a != 0;
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

            // How much fuel must burn off before a pixel can light neighbours.
            float spreadThreshold = mat.SpreadDelayTicks * mat.BurnRate * 255f;
            b.Next.Clear();
            int cleared = 0;

            for (int i = 0; i < b.Active.Count; i++)
            {
                int idx = b.Active[i];

                // Every `continue` here drops this pixel's entry, so each one has to give
                // the slot back or the pixel can never be listed again.
                if (!b.Alight[idx]) { b.Listed[idx] = false; continue; }   // doused, or suffocated

                // Another tool (the eraser) may have removed this pixel out from under
                // us. Repainting it here would resurrect it, so let the flame drop.
                if (pix[idx].a == 0) { b.Alight[idx] = false; b.Listed[idx] = false; b.Fuel[idx] = 0; continue; }

                int fuel = b.Fuel[idx];
                if (fuel == 0) { b.Alight[idx] = false; b.Listed[idx] = false; continue; }

                int x = idx % w, y = idx / w;

                float rate = mat.BurnRate * (1f + mat.BurnRateJitter * (b.NextFloat() * 2f - 1f));
                int consume = Mathf.Max(1, Mathf.RoundToInt(rate * 255f));
                int left = fuel - consume;

                if (left <= 0)
                {
                    b.Fuel[idx] = 0;
                    b.Alight[idx] = false;
                    b.Listed[idx] = false;
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
                    b.Next.Add(idx);

                    // Colour is a function of fuel alone, so it only has to be written when
                    // fuel changes. All the motion in the fire is in the flames now.
                    pix[idx] = Charred(b.Orig[idx], mat, left);

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
            b.Heat[idx] = (byte)Mathf.Clamp(b.Mat.TemperatureOfFire, 1, 255);
            if (b.Listed[idx]) return;

            b.Listed[idx] = true;
            b.Next.Add(idx);
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
                // Wide enough to find the chunk across a seam; Ignite still uses the real radius.
                Physics2D.OverlapCircle(world, ContactProbeRadius + PixelSpriteRegistry.QueryMargin,
                                        filter, _probe);
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
                        b.Heat[dst] = old.Heat[src];
                        b.Orig[dst] = old.Orig[src];
                        if (old.Alight[src] && b.Fuel[dst] > 0)
                        {
                            b.Alight[dst] = true;
                            b.Listed[dst] = true;
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
                Heat = new byte[n],
                Alight = new bool[n],
                Listed = new bool[n],
                // Snapshot before anything is charred: the char ramp mixes back into it, and
                // a split has to be able to hand the piece its share of the original art.
                Orig = (Color32[])rec.Pixels.Clone(),
                // Position-derived seed: two objects lit on the same frame still flicker apart.
                Rng = (uint)(go.GetInstanceID() * 2654435761u) | 1u,
            };

            if (seedFuel)
                for (int i = 0; i < n; i++)
                    if (rec.Pixels[i].a > 0) b.Fuel[i] = 255;

            return b;
        }

        /// <summary>Colour equality. Color32 has no cheap operator==, and this runs per pixel.</summary>
        private static bool Same(Color32 a, Color32 b) =>
            a.r == b.r && a.g == b.g && a.b == b.b && a.a == b.a;

        private static void ResetStepRect(Burn b)
        {
            b.sx0 = int.MaxValue; b.sy0 = int.MaxValue;
            b.sx1 = -1; b.sy1 = -1;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Look
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Colour of a burning pixel with <paramref name="fuel"/> left.
        ///
        /// Noita never tints the burning material bright: wood that is on fire is wood going
        /// black, and every warm colour in the picture comes from the fire cells standing over
        /// it. So this is a char ramp, not an ember ramp — the object's own colour flashes hot
        /// for a moment where the fire front just arrived, then darkens the rest of the way
        /// down to charcoal and stays there. The previous version ran a bright orange gradient
        /// over the pixel's whole multi-second life, which is exactly what made a burning plank
        /// read as a plank someone had painted orange.
        /// </summary>
        private static Color32 Charred(Color32 orig, PhysMaterial mat, int fuel)
        {
            float u = 1f - fuel / 255f;      // how far through the burn this pixel is

            if (u < 0.10f)                   // the front itself: a brief flash of heat
                return Color32.Lerp(orig, mat.EmberMid, u / 0.10f);

            if (u < 0.30f)                   // cooling into a dark red glow
                return Color32.Lerp(mat.EmberMid, mat.EmberCool, (u - 0.10f) / 0.20f);

            return Color32.Lerp(mat.EmberCool, mat.Charcoal, (u - 0.30f) / 0.70f);
        }

        /// <summary>Colour left behind when a flame is put out before the pixel is spent.</summary>
        private static Color32 Scorch(Color32 orig, PhysMaterial mat, int fuel)
        {
            // Same ramp, minus the glow: nothing that was doused is still hot.
            var cold = Color32.Lerp(orig, mat.Charcoal, 0.65f);
            return Color32.Lerp(cold, mat.Charcoal, 1f - fuel / 255f);
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
