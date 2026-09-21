using System.Collections.Generic;
using Materials;
using Phys.Pixels;
using Phys.Terrain;
using UnityEngine;

namespace Phys.Fracture
{
    /// <summary>
    /// Brittle materials — ice, and anything else flagged <see cref="PhysMaterial.Brittle"/>.
    ///
    /// The rest of the world loses material where it is hit: the eraser carves, fire eats, the
    /// cracker knocks a bite out. Brittle material does none of that. A hit on it runs a crack
    /// out of the impact point, aimed so that where it goes is readable before it gets there:
    ///
    ///   • hit from above and it runs down, hit from below and it runs up;
    ///   • hit side-on and it runs away from the nearer face — upper half down, lower half up;
    ///   • it keeps a fraction of the shot's slant, so a shallow hit shears a wedge.
    ///
    /// A second, shorter branch runs the other way out through the face the hit came in by.
    ///
    /// <b>The crack is traced before any of it is drawn</b>, and what happens next depends on
    /// where it got to. Both ends out in open air means the hit has cut a piece off, so the
    /// seam is opened for real: cleared pixels, wide enough to separate. Either end still
    /// buried in the material means the hit cracked the surface and no more, so it is drawn as
    /// a hairline — a bright fracture line, not one pixel of material removed.
    ///
    /// Tracing first is what makes this readable rather than arbitrary. The alternative, and
    /// the first version of this, was to carve as the crack travelled and let it stop wherever
    /// it ran out: the result is a slot gouged halfway into a slab that then does not fall,
    /// which reads as a bug in every case. Damage you can see should either mean the thing is
    /// about to come down or mean nothing at all.
    ///
    /// Both are a pixel or two wide, which is the whole point. An earlier version had to cut
    /// five or six because <see cref="TerrainSupportSystem"/> settled contact by collider
    /// distance, and a seam narrower than the simplification error on both sides went on
    /// measuring as the two halves touching — so the slab never fell and the cut read as a slot
    /// milled through the rock. That system now settles contact on pixel adjacency, and a crack
    /// is free to look like one.
    ///
    /// Reference: Noita's dev build spawns data/entities/misc/crack.xml out of an explosion and
    /// launches it along the blast direction (the spawn is at 0x731d36, the velocity set to
    /// direction * -5 just after), gated on <c>min_radius_for_cracks</c> and repeated
    /// <c>crack_count</c> times. That is the shape borrowed here: a crack is a thing that
    /// travels, not a decal. Those two gates sit on <see cref="PhysMaterial"/> in this game,
    /// and the attributes the lengths are drawn from — <c>durability</c> and
    /// <c>crackability</c> — are the same two the dev build parses into CellData at +0x104
    /// and +0x108.
    /// </summary>
    [DefaultExecutionOrder(1050)]
    public sealed class FractureSystem : MonoBehaviour
    {
        /// <summary>Ceiling on cracks running at once. Past it new hits are absorbed rather
        /// than allowed to turn one loud moment into a frame spike.</summary>
        public static int MaxActive = 24;

        /// <summary>
        /// Steps a trace may spend without finding material before it stops.
        ///
        /// It is not only the far side this covers. Every crack <em>starts</em> in open air,
        /// because the impact point is on the surface; and terrain is chunked, so a crack of
        /// any length walks off the edge of one texture and has to be given enough rope to find
        /// the next one. Those are the same allowance, refilled every time the trace finds
        /// material, so what ends a branch is running out of material and never the accident of
        /// where a chunk border happens to fall.
        /// </summary>
        private const int MissBudget = 6;

        /// <summary>Step to take while the trace has no record under it, in world units.</summary>
        private const float BlindStep = 1f / 40f;

        /// <summary>One traced branch: the points it passes through and whether it got out.</summary>
        private sealed class Branch
        {
            public readonly List<Vector2> Points = new();
            public readonly List<float> Reach = new();   // distance travelled to reach each point
            public Vector2 Bearing;
            public bool Exited;                          // ran out the far side, not out of length
            public int Cursor;                           // how much of it has been drawn

            public bool Spent => Cursor >= Points.Count;
        }

        private sealed class Crack
        {
            public Branch Main, Back;
            public PhysMaterial Mat;
            public bool Severs;          // traced clear through: draw a real cut, not a hairline
            public float Travelled;      // world units of the trace drawn so far
            public float SettleAt;       // unscaled time the piece is let go; 0 = still drawing

            /// <summary>
            /// Every brittle record the crack could possibly run through, collected once when
            /// the hit lands. Terrain is chunked, so a crack of any length crosses several, and
            /// looking the next one up with a physics query at each step — which is what this
            /// replaces — made the crack's reach depend on collider margins at the chunk seam
            /// instead of on the material. It died at the first border every time.
            /// </summary>
            public readonly List<PixelSpriteRegistry.Record> Records = new();

            // Pixel writes are batched per record and handed over when the crack leaves it.
            public PixelSpriteRegistry.Record Rec;
            public int X0, Y0, X1, Y1, Cleared;
            public bool HasWrites;

            public void ResetRect()
            {
                X0 = int.MaxValue; Y0 = int.MaxValue; X1 = -1; Y1 = -1;
                Cleared = 0; HasWrites = false;
            }

            public void Touch(int x, int y)
            {
                if (x < X0) X0 = x;
                if (y < Y0) Y0 = y;
                if (x > X1) X1 = x;
                if (y > Y1) Y1 = y;
                HasWrites = true;
            }

            /// <summary>Hand the written region over and start a fresh one. A hairline only
            /// repaints pixels, so it must not ask for a collider retrace or a split scan.</summary>
            public void Flush()
            {
                if (HasWrites && Rec != null && Rec.Go)
                    Rec.MarkPixels(X0, Y0, X1, Y1, Cleared, colliderChanged: Severs);
                ResetRect();
            }
        }

        private static FractureSystem _instance;
        private static readonly List<Crack> Active = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode()
        {
            // Play mode can start without a domain reload, so the statics outlive the scene.
            Active.Clear();
            _instance = null;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Entry points
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Is this something a hit should crack rather than dent?</summary>
        public static bool IsBrittle(GameObject go) => go && MaterialLibrary.Of(go).Brittle;

        /// <summary>
        /// Put a hit into <paramref name="go"/>. <paramref name="force"/> is in damage units —
        /// a round's damage, a blast's damage, momentum scaled by the caller — and decides both
        /// whether the material gives at all and how far the crack reaches.
        ///
        /// Returns true when the fracture model has taken the hit over, so the caller can skip
        /// whatever it would otherwise have done to the sprite.
        /// </summary>
        public static bool Hit(GameObject go, Vector2 point, Vector2 direction, float force)
        {
            if (!go) return false;

            var mat = MaterialLibrary.Of(go);
            if (!mat.Brittle) return false;

            // Under the durability floor, nothing at all. This is the half of "brittle" that is
            // easy to forget: not just that it breaks, but that it shrugs off everything below
            // the figure at which it breaks.
            if (force < mat.Durability) return true;

            var rec = PixelSpriteRegistry.Instance.Get(go);
            if (rec == null) return false;
            if (Active.Count >= MaxActive) return true;

            // Which way it runs. A hit with real vertical in it decides outright; a side-on one
            // falls back to where it landed on the body, so the crack heads away from the nearer
            // face and takes the larger slab with it.
            float vertical;
            if (Mathf.Abs(direction.y) > mat.CrackVerticalBias)
            {
                vertical = Mathf.Sign(direction.y);
            }
            else
            {
                var sr = go.GetComponent<SpriteRenderer>();
                float mid = sr ? sr.bounds.center.y : go.transform.position.y;
                vertical = point.y >= mid ? -1f : 1f;
            }

            // Only a flattened share of the shot's own direction survives: a crack in a brittle
            // slab runs with gravity, not with the bullet.
            var lean = new Vector2(direction.x, direction.y * 0.35f);
            if (lean.sqrMagnitude > 1e-6f) lean.Normalize();

            var bearing = Vector2.Lerp(new Vector2(0f, vertical), lean, mat.CrackLean);
            if (bearing.sqrMagnitude < 1e-6f) bearing = new Vector2(0f, vertical);
            bearing.Normalize();

            float length = Mathf.Clamp(force * mat.Crackability, mat.CrackMinLength, mat.CrackMaxLength);

            // Start a little inside rather than on the surface. A contact point sits exactly on
            // the collider boundary, and a crack whose bearing runs along the face — a side hit
            // on a ledge, say — would otherwise spend its whole miss budget skimming the outside
            // of the material it is supposed to be cutting.
            var into = direction.sqrMagnitude > 1e-6f ? direction.normalized : bearing;
            var start = point + into * (2f / Mathf.Max(1f, rec.PixelsPerWorldUnit));

            var crack = new Crack { Mat = mat };
            crack.ResetRect();
            Gather(crack.Records, start, length + 4f * PixelSpriteRegistry.QueryMargin, go.layer);
            crack.Main = Trace(mat, crack.Records, start, bearing, length);
            crack.Back = Trace(mat, crack.Records, start, -bearing, length * mat.CrackBackFraction);

            // Nothing was under the hit at all — a graze along the surface. Not worth a mark.
            if (crack.Main.Points.Count == 0 && crack.Back.Points.Count == 0) return true;

            // Both ends out in the open means the pair of branches is one cut straight through
            // the material, and a piece of it is now loose. Anything less is surface damage.
            crack.Severs = crack.Main.Exited && crack.Back.Exited;

            Active.Add(crack);
            Install();
            return true;
        }

        /// <summary>
        /// A blast's share of the same thing. Noita gates this on the blast being wide enough to
        /// be worth cracking and then throws several cracks outwards from the centre; both gates
        /// are the material's here, because whether a bang cracks something is a property of the
        /// something.
        /// </summary>
        public static bool Burst(GameObject go, Vector2 center, float carveRadius, float force)
        {
            if (!go) return false;

            var mat = MaterialLibrary.Of(go);
            if (!mat.Brittle) return false;

            // Too small to crack: the blast still counts as handled, so the caller does not fall
            // back to carving a bite out of ice.
            if (carveRadius < mat.MinRadiusForCracks) return true;

            var sr = go.GetComponent<SpriteRenderer>();
            Vector2 anchor = sr ? (Vector2)sr.bounds.ClosestPoint(center) : (Vector2)go.transform.position;

            // Outwards from the blast, fanned — the direction the crack entity is launched in
            // over there.
            Vector2 outward = anchor - center;
            if (outward.sqrMagnitude < 1e-6f) outward = Vector2.down;
            outward.Normalize();

            int count = Mathf.Max(1, mat.CrackCount);
            for (int i = 0; i < count; i++)
            {
                float spread = count == 1 ? 0f : Mathf.Lerp(-50f, 50f, i / (float)(count - 1));
                Hit(go, anchor, Rotate(outward, spread * Mathf.Deg2Rad), force);
            }
            return true;
        }

        private static void Install()
        {
            if (_instance) return;
            var go = new GameObject("~FractureSystem") { hideFlags = HideFlags.HideAndDontSave };
            _instance = go.AddComponent<FractureSystem>();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Tracing — pure, writes nothing
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Walk one branch through the material and record where it went. Nothing is written:
        /// this runs in full at the moment of the hit, so that the decision between a cut and a
        /// hairline is made before the first pixel is touched.
        /// </summary>
        private static Branch Trace(PhysMaterial mat, List<PixelSpriteRegistry.Record> recs,
                                   Vector2 origin, Vector2 bearing, float length)
        {
            var b = new Branch { Bearing = bearing };

            var tip = origin;
            var dir = bearing;
            float phase = Random.value * 64f;
            float travelled = 0f;
            int misses = MissBudget;

            while (travelled < length)
            {
                // Whichever chunk holds this point, with no regard for which one held the last:
                // a chunk border is not an event as far as the crack is concerned.
                var rec = RecordAt(recs, tip);

                float step = BlindStep;
                bool solid = false;

                if (rec != null)
                {
                    float pxPerUnit = rec.PixelsPerWorldUnit;
                    if (pxPerUnit < 1e-3f) break;
                    step = 1f / pxPerUnit;
                    solid = rec.WorldToPixel(tip, out int x, out int y) &&
                            rec.Pixels[y * rec.Width + x].a != 0;
                }

                if (solid)
                {
                    misses = MissBudget;
                    b.Points.Add(tip);
                    b.Reach.Add(travelled);
                }
                else if (--misses <= 0)
                {
                    // Out of material: this end of the crack is in open air, which is what a cut
                    // needs at both ends. A branch that never bit at all counts too — that is
                    // the short one running straight back out through the face the hit came in
                    // by, and it is already outside.
                    b.Exited = true;
                    return b;
                }

                // Wander, then get pulled back onto the bearing. Without the pull a long crack
                // curls round on itself and cuts nothing.
                phase += 0.4f;
                float wobble = (Mathf.PerlinNoise(phase, 0.37f) - 0.5f) * 2f * mat.CrackWander;
                dir = Vector2.Lerp(Rotate(dir, wobble), bearing, 0.08f).normalized;

                tip += dir * step;
                travelled += step;
            }

            // Ran out of length still inside the material: it cracked the surface, no more.
            b.Exited = false;
            return b;
        }

        /// <summary>
        /// Collect every brittle sprite within reach of the hit, once. Done up front rather than
        /// per step so that what limits a crack is the material it is cutting and never the
        /// margin on a collider query at a chunk border.
        /// </summary>
        private static void Gather(List<PixelSpriteRegistry.Record> into, Vector2 center,
                                   float radius, int layer)
        {
            into.Clear();

            var found = Physics2D.OverlapCircleAll(center, radius, 1 << layer);
            foreach (var col in found)
            {
                if (!col || col.isTrigger) continue;
                var go = col.gameObject;
                if (!MaterialLibrary.Of(go).Brittle) continue;

                var rec = PixelSpriteRegistry.Instance.Get(go);
                if (rec != null && !into.Contains(rec)) into.Add(rec);
            }
        }

        /// <summary>The record holding a world point — preferring one with material under it, so
        /// that where two chunk textures overlap the crack follows the solid one.</summary>
        private static PixelSpriteRegistry.Record RecordAt(List<PixelSpriteRegistry.Record> recs, Vector2 p)
        {
            PixelSpriteRegistry.Record covering = null;

            for (int i = 0; i < recs.Count; i++)
            {
                var rec = recs[i];
                if (rec == null || !rec.Go) continue;
                if (!rec.WorldToPixel(p, out int x, out int y)) continue;
                if (rec.Pixels[y * rec.Width + x].a != 0) return rec;
                covering ??= rec;
            }

            return covering;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Drawing — replays the trace over time
        // ─────────────────────────────────────────────────────────────────────────

        private void Update()
        {
            if (Active.Count == 0) return;

            float dt = Time.deltaTime;
            float now = Time.unscaledTime;
            bool severed = false;

            for (int i = Active.Count - 1; i >= 0; i--)
            {
                var crack = Active[i];

                if (crack.SettleAt == 0f)
                {
                    crack.Travelled += crack.Mat.CrackSpeed * dt;
                    Draw(crack, crack.Main);
                    Draw(crack, crack.Back);

                    if (!crack.Main.Spent || !crack.Back.Spent) continue;

                    crack.Flush();

                    if (!crack.Severs)
                    {
                        // A hairline changes nothing structural — no retrace, no split scan, no
                        // support pass. It is paint, and the per-frame upload will carry it.
                        Active.RemoveAt(i);
                        continue;
                    }

                    // Let the cut sit for a beat. It is the readability of the whole mechanic:
                    // the player gets to see the line before the thing on the far side of it
                    // stops being part of the level.
                    crack.SettleAt = now + Mathf.Max(0f, crack.Mat.CrackSettle);
                    continue;
                }

                if (now < crack.SettleAt) continue;
                Active.RemoveAt(i);
                severed = true;
            }

            if (!severed) return;

            // Make the cut real this frame: upload, retrace colliders, run the split scan that
            // finds the freed component, then re-check what the terrain still holds up.
            PixelSpriteDriver.FinalizeNow();
            TerrainSupportSystem.Refresh();
        }

        /// <summary>Draw however much of <paramref name="b"/> the crack has now reached.</summary>
        private static void Draw(Crack crack, Branch b)
        {
            while (b.Cursor < b.Points.Count && b.Reach[b.Cursor] <= crack.Travelled)
            {
                Mark(crack, b, b.Cursor);
                b.Cursor++;
            }
        }

        private static void Mark(Crack crack, Branch b, int index)
        {
            var at = b.Points[index];

            var rec = RecordAt(crack.Records, at);
            if (rec == null) return;

            float pxPerUnit = rec.PixelsPerWorldUnit;
            if (pxPerUnit < 1e-3f) return;

            // Local heading, from the traced path rather than from the bearing, so the seam is
            // square to the crack even where it has wandered.
            Vector2 dir = index + 1 < b.Points.Count ? b.Points[index + 1] - at
                        : index > 0 ? at - b.Points[index - 1]
                        : b.Bearing;
            if (dir.sqrMagnitude < 1e-8f) dir = b.Bearing;
            dir.Normalize();
            var perp = new Vector2(-dir.y, dir.x);

            if (crack.Severs) Cut(crack, perp, at, pxPerUnit, index);
            else Hairline(crack, perp, at, pxPerUnit);
        }

        /// <summary>
        /// Open the seam across the point and frost the faces it leaves behind.
        ///
        /// A cut is only a pixel or two wide now, which is what a crack in ice actually looks
        /// like. That is only possible because <see cref="TerrainSupportSystem"/> decides
        /// contact on pixel adjacency: back when it went by collider distance, a seam had to be
        /// wider than the simplification error on both sides — five or six pixels — or the two
        /// halves went on measuring as touching and the slab never fell.
        /// </summary>
        private static void Cut(Crack crack, Vector2 perp, Vector2 at, float pxPerUnit, int index)
        {
            var mat = crack.Mat;
            float step = 1f / pxPerUnit;

            // The jitter only ever adds. A seam has to stay unbroken along its whole length —
            // one gap in it and the flood fill walks straight through and finds one piece.
            float widthPx = Mathf.Max(1f, mat.CrackWidthPixels)
                          + Mathf.PerlinNoise(index * 0.3f, 11.7f) * Mathf.Max(0f, mat.CrackWidthJitter);

            float half = widthPx * 0.5f * step;
            int steps = Mathf.Max(1, Mathf.CeilToInt(half * pxPerUnit));
            float spacing = half / steps;

            for (int i = -steps; i <= steps; i++)
                Paint(crack, at + perp * (i * spacing), clear: true, default, 0f);

            // One pixel of frost either side: the lit fracture face that tells ice apart from a
            // hole punched through it.
            for (int s = -1; s <= 1; s += 2)
                Paint(crack, at + perp * (s * (half + step)), clear: false, mat.CrackRim, 0.55f);
        }

        /// <summary>
        /// Surface damage: a bright fracture line with nothing removed. It is the honest reading
        /// of a hit that did not get through — the ice is cracked and still holding — and it is
        /// also what a crack in real ice looks like, a plane catching the light rather than a
        /// gap you can see the background through.
        /// </summary>
        private static void Hairline(Crack crack, Vector2 perp, Vector2 at, float pxPerUnit)
        {
            float step = 1f / pxPerUnit;
            for (int i = -1; i <= 1; i++)
                Paint(crack, at + perp * (i * step), clear: false, crack.Mat.CrackRim,
                      i == 0 ? 0.8f : 0.3f);
        }

        /// <summary>
        /// Write one pixel, wherever it lives. Writes go through here rather than against a
        /// cached record because a crack crosses chunks freely, and the dirty rect handed to a
        /// record has to be that record's own — so changing record flushes the previous one.
        /// </summary>
        private static void Paint(Crack crack, Vector2 world, bool clear, Color32 tint, float t)
        {
            var rec = RecordAt(crack.Records, world);
            if (rec == null) return;
            if (!rec.WorldToPixel(world, out int x, out int y)) return;

            int idx = y * rec.Width + x;
            var c = rec.Pixels[idx];
            if (c.a == 0) return;

            if (rec != crack.Rec)
            {
                crack.Flush();
                crack.Rec = rec;
            }

            if (clear)
            {
                rec.Pixels[idx] = default;
                crack.Cleared++;
            }
            else
            {
                rec.Pixels[idx] = Blend(c, tint, t);
            }

            crack.Touch(x, y);
        }

        private static Color32 Blend(Color32 a, Color32 b, float t) => new(
            (byte)Mathf.RoundToInt(Mathf.Lerp(a.r, b.r, t)),
            (byte)Mathf.RoundToInt(Mathf.Lerp(a.g, b.g, t)),
            (byte)Mathf.RoundToInt(Mathf.Lerp(a.b, b.b, t)),
            a.a);

        private static Vector2 Rotate(Vector2 v, float radians)
        {
            float c = Mathf.Cos(radians), s = Mathf.Sin(radians);
            return new Vector2(v.x * c - v.y * s, v.x * s + v.y * c);
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
        }
    }
}
