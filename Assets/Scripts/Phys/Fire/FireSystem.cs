using System.Collections.Generic;
using Materials;
using Phys.Pixels;
using Unity.Profiling;
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

        /// <summary>
        /// Smallest piece, in solid pixels, that a *burning* object is allowed to break into.
        /// Anything smaller is taken by the fire instead of becoming its own physics body.
        ///
        /// A thin shape burning through does not part into a few clean halves: it crumbles,
        /// and every crumb that becomes an object brings a texture, a traced collider, a
        /// rigidbody and its own continuing fragmentation with it. Four times the registry's
        /// usual floor is enough to keep that cascade from turning a burn-through into a
        /// multi-second stall, and it matches what fire is supposed to do to small debris.
        /// </summary>
        public static int MinBurningPiece = 64;

        private sealed class Burn
        {
            public GameObject Go;
            public PixelSpriteRegistry.Record Rec;   // reference identity doubles as a staleness check
            public PhysMaterial Mat;
            public SpriteRenderer Sr;                // kept for its world bounds, nothing else

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

            /// <summary>
            /// Rect covering every pixel that has ever been alight on this object. A rekindle
            /// only looks inside it: on a terrain chunk the array is the whole map, and
            /// relighting its entire surface because a campfire went out somewhere would set
            /// the level on fire.
            /// </summary>
            public int bx0 = int.MaxValue, by0 = int.MaxValue, bx1 = -1, by1 = -1;

            /// <summary>Whether this burn has already had its one attempt at coming back.</summary>
            public bool Rekindled;

            public void Burnt(int x, int y)
            {
                if (x < bx0) bx0 = x;
                if (y < by0) by0 = y;
                if (x > bx1) bx1 = x;
                if (y > by1) by1 = y;
            }

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

        // Markers, so the next time a fire costs a frame the Profiler says which half.
        private static readonly ProfilerMarker s_burn = new("Fire.Burn");
        private static readonly ProfilerMarker s_emit = new("Fire.EmitFlames");
        private static readonly ProfilerMarker s_contact = new("Fire.IgniteFromFlames");

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
            if (_reg != null)
            {
                _reg.Split -= OnSplit;
                _reg.MinPixelsOverride = null;
            }
            _reg = registry;
            _reg.Split += OnSplit;
            _reg.MinPixelsOverride = go => IsBurning(go) ? MinBurningPiece : 0;
        }

        /// <summary>Objects the fire is tracking, live or burnt out. Diagnostics only.</summary>
        public int BurnCount => _burns.Count;

        /// <summary>Total lit pixels across every object. Diagnostics only.</summary>
        public int LitPixelCount
        {
            get
            {
                int n = 0;
                foreach (var kv in _burns) n += kv.Value.Active.Count;
                return n;
            }
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
                    b.Burnt(x, y);
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
            if (lit > 0) b.Rekindled = false;
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
                b.Rekindled = true;
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
            b.Rekindled = true;
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
            using var _ = s_emit.Auto();

            _stepList.Clear();
            foreach (var kv in _burns)
            {
                if (!kv.Key) continue;
                if (!_reg.TryGet(kv.Key, out var rec) || rec != kv.Value.Rec) continue;
                if (kv.Value.Active.Count > 0) _stepList.Add(kv.Value);
            }

            foreach (var b in _stepList) EmitBurn(b);
        }

        /// <summary>
        /// Second wind. A fire that has run out of lit pixels with no flames left over the
        /// object comes back once along the surface of the part that burned.
        ///
        /// Without it a burnt object always keeps a skeleton. The fire eats inwards from the
        /// faces, and the last of it regularly strands a few specks — pixels the front never
        /// reached, now surrounded by the holes it left, with no lit neighbour to catch from
        /// and no flame left alive to relight them. In a game where fire is supposed to
        /// destroy things, "almost all gone" is a worse answer than "gone", so the fire gets
        /// one more go at what is left.
        ///
        /// Only once per burn, only inside the area that actually burned, only if some of the
        /// material is part-burnt (an object that merely sat next to a fire stays intact), and
        /// never after the player put it out by hand.
        /// </summary>
        private static void Rekindle(Burn b)
        {
            b.Rekindled = true;
            if (b.bx1 < 0) return;

            var rec = b.Rec;
            var pix = rec.Pixels;
            var mat = b.Mat;
            int w = rec.Width, h = rec.Height;

            int x0 = Mathf.Max(0, b.bx0 - 1), x1 = Mathf.Min(w - 1, b.bx1 + 1);
            int y0 = Mathf.Max(0, b.by0 - 1), y1 = Mathf.Min(h - 1, b.by1 + 1);

            bool partBurnt = false;
            for (int y = y0; y <= y1 && !partBurnt; y++)
                for (int x = x0; x <= x1; x++)
                {
                    int idx = y * w + x;
                    if (pix[idx].a != 0 && b.Fuel[idx] > 0 && b.Fuel[idx] < 255) { partBurnt = true; break; }
                }
            if (!partBurnt) return;

            ResetStepRect(b);
            bool painted = false;

            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    int idx = y * w + x;
                    if (pix[idx].a == 0 || b.Alight[idx] || b.Fuel[idx] == 0) continue;

                    // Surface only — anything sealed inside would just suffocate again.
                    bool exposed =
                        x == 0 || y == 0 || x == w - 1 || y == h - 1 ||
                        pix[idx - 1].a == 0 || pix[idx + 1].a == 0 ||
                        pix[idx - w].a == 0 || pix[idx + w].a == 0;
                    if (!exposed) continue;

                    b.Alight[idx] = true;
                    b.Heat[idx] = (byte)Mathf.Clamp(mat.TemperatureOfFire, 1, 255);
                    if (!b.Listed[idx])
                    {
                        b.Listed[idx] = true;
                        b.Active.Add(idx);
                    }

                    var c = Charred(b.Orig[idx], mat, b.Fuel[idx]);
                    if (!Same(pix[idx], c))
                    {
                        pix[idx] = c;
                        b.Touch(x, y);
                        painted = true;
                    }
                }

            if (painted) rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);
        }

        /// <summary>Cheap reject so objects nowhere near the fire cost one AABB test a step.</summary>
        private static bool NearFlames(Burn b, Rect area)
        {
            if (!b.Sr) return true;          // nothing to ask: pay the full test

            var bb = b.Sr.bounds;
            return bb.min.x <= area.xMax && bb.max.x >= area.xMin &&
                   bb.min.y <= area.yMax && bb.max.y >= area.yMin;
        }

        private static void EmitBurn(Burn b)
        {
            var rec = b.Rec;
            var pix = rec.Pixels;
            var mat = b.Mat;
            int w = rec.Width, h = rec.Height;
            var field = FlameField.Instance;

            // "Above" has to be measured in the object's own pixels, not in world cells.
            // Noita asks its grid what sits in the cell above a burning cell; the sprite's
            // texture is the only grid we have here, and one texture pixel is not one flame
            // cell — on coarse art it is several, and a world-space step of one cell then
            // lands back inside the pixel it started from and reads as solid. That is a fire
            // where *nothing* can vent: it suffocates everywhere within a second and leaves
            // the object standing as a half-eaten shell.
            //
            // The texture's rows are not world-up either, once the object has toppled over,
            // so the step is world-up rotated into pixel space.
            Vector2 up = b.Go.transform.InverseTransformDirection(Vector3.up);
            if (up.sqrMagnitude > 1e-6f) up.Normalize();
            int ux = Mathf.RoundToInt(up.x), uy = Mathf.RoundToInt(up.y);
            if (ux == 0 && uy == 0) uy = 1;
            int px_ = -uy, py_ = ux;      // one step along the surface: the two upper diagonals

            var l2w = b.Go.transform.localToWorldMatrix;
            float ppu = rec.Ppu;

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

                    // 0x751dd8: one of the three cells above, chosen at random.
                    int k = (int)(field.NextFloat() * 3f);
                    int nx = x + ux + (k == 0 ? -px_ : k == 2 ? px_ : 0);
                    int ny = y + uy + (k == 0 ? -py_ : k == 2 ? py_ : 0);

                    // 0x751f1b: the flame only goes into an empty cell. Off the edge of the
                    // texture counts as empty — that is open air just outside the sprite.
                    bool air = nx < 0 || ny < 0 || nx >= w || ny >= h || pix[ny * w + nx].a == 0;
                    if (air)
                    {
                        var at = (Vector2)l2w.MultiplyPoint3x4(new Vector3(
                            (nx + 0.5f - rec.PivotPx.x) / ppu,
                            (ny + 0.5f - rec.PivotPx.y) / ppu,
                            0f));

                        if (rollFlame)
                        {
                            // 0x752505: the flame carries this pixel's heat, jittered 0.75..1.29.
                            int heat = Mathf.RoundToInt(b.Heat[idx] * (0.75f + 0.54f * field.NextFloat()));
                            vented = field.Emit(at, heat);
                        }

                        if (rollSmoke) field.EmitSmoke(at);
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
        /// Every flame tries to set light to one random neighbour of its own cell — Noita's
        /// ICell::TryIgniteRandomNeighbour (0x7520a0), including its roll of the flame's own
        /// temperature as a percentage (0x7520d2).
        ///
        /// This is what actually eats an object. Only its upward-facing pixels can vent, so
        /// everything else suffocates within a second of catching; what keeps a wall, an
        /// underside or a sheared edge burning is the flames sliding along it and relighting
        /// it. Noita gets that for free — a neighbour is an array index in the one world grid.
        /// Here the flame has to be resolved against each burning object's texture, which is
        /// one matrix multiply per flame per object, and cheap enough at the burn rate: the
        /// physics probes in <see cref="FlameField"/> are only needed for jumping to objects
        /// that are not already alight.
        /// </summary>
        private static void IgniteFromFlames(Burn b)
        {
            var field = FlameField.Instance;
            int n = field.Count;
            if (n == 0) return;
            using var _ = s_contact.Auto();

            var rec = b.Rec;
            var pix = rec.Pixels;
            var mat = b.Mat;
            int w = rec.Width, h = rec.Height;

            var w2l = b.Go.transform.worldToLocalMatrix;
            float ppu = rec.Ppu;
            float cell = FlameField.CellSize;

            var cx = field.CellX;
            var cy = field.CellY;
            var kind = field.Kind;
            var heat = field.Heat;

            // Cell-space box around this object. With a dozen burning pieces sharing one fire
            // the per-object AABB test is not enough on its own — without this every piece
            // would transform every flame in the blaze.
            int bx0 = int.MinValue, by0 = int.MinValue, bx1 = int.MaxValue, by1 = int.MaxValue;
            if (b.Sr)
            {
                var bb = b.Sr.bounds;
                FlameField.WorldToCell(bb.min, out bx0, out by0);
                FlameField.WorldToCell(bb.max, out bx1, out by1);
                bx0--; by0--; bx1++; by1++;      // the neighbour a flame reaches for
            }

            ResetStepRect(b);
            bool painted = false;

            for (int i = 0; i < n; i++)
            {
                if (kind[i] != FlameField.KindFire) continue;
                if (cx[i] < bx0 || cx[i] > bx1 || cy[i] < by0 || cy[i] > by1) continue;

                // The flame's own cell is air by construction, so the neighbour is what gets
                // lit — one picked at random, as in the original.
                var world = FlameField.CellToWorld(cx[i], cy[i]) +
                            new Vector2((int)(field.NextFloat() * 3f) - 1,
                                        (int)(field.NextFloat() * 3f) - 1) * cell;

                var local = w2l.MultiplyPoint3x4(world);
                int x = Mathf.FloorToInt(local.x * ppu + rec.PivotPx.x);
                int y = Mathf.FloorToInt(local.y * ppu + rec.PivotPx.y);
                if (x < 0 || y < 0 || x >= w || y >= h) continue;

                int idx = y * w + x;
                if (pix[idx].a == 0 || b.Alight[idx] || b.Fuel[idx] == 0) continue;
                if (b.NextFloat() * 101f > heat[i]) continue;      // 0x7520d2

                b.Alight[idx] = true;
                b.Heat[idx] = (byte)Mathf.Clamp(mat.TemperatureOfFire, 1, 255);
                b.Burnt(x, y);
                if (!b.Listed[idx])
                {
                    b.Listed[idx] = true;
                    b.Active.Add(idx);
                }

                var c = Charred(b.Orig[idx], mat, b.Fuel[idx]);
                if (!Same(pix[idx], c))
                {
                    pix[idx] = c;
                    b.Touch(x, y);
                    painted = true;
                }
            }

            if (painted) rec.MarkPixels(b.sx0, b.sy0, b.sx1, b.sy1, 0, colliderChanged: false);
        }

        private void Step()
        {
            using var _ = s_burn.Auto();

            // Snapshot: igniting a neighbouring object mutates the dictionary mid-step.
            _stepList.Clear();
            _dead.Clear();
            foreach (var kv in _burns)
            {
                if (!kv.Key) { _dead.Add(kv.Key); continue; }
                // A record swapped out from under us (the cracker replaces sprites
                // wholesale) means our pixel mirror is stale — let the fire die.
                if (!_reg.TryGet(kv.Key, out var rec) || rec != kv.Value.Rec) { _dead.Add(kv.Key); continue; }

                // Burns with nothing alight are kept in the list: a piece that suffocated,
                // or one that sheared off with no lit pixels, is exactly what the flames
                // around it should be able to set going again.
                _stepList.Add(kv.Value);
            }
            foreach (var go in _dead) _burns.Remove(go);

            bool anyFlames = FlameField.Instance.TryGetFireBounds(out var fireArea);

            foreach (var b in _stepList)
            {
                bool near = anyFlames && NearFlames(b, fireArea);
                if (near) IgniteFromFlames(b);

                if (b.Active.Count > 0) StepBurn(b);
                else if (!near && !b.Rekindled) Rekindle(b);
            }
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
            b.Burnt(x, y);
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
                        if (b.Fuel[dst] < 255) b.Burnt(x, y);
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
                Sr = go.GetComponent<SpriteRenderer>(),
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
