using System;
using System.Collections.Generic;
using Spawners;
using UnityEngine;

namespace Phys.Pixels
{
    /// <summary>
    /// One piece produced by a split, plus the area of the pre-split texture it came from.
    /// The rect lets systems that keep per-pixel side data (fire fuel, for instance)
    /// carry that data across the split instead of throwing it away.
    /// </summary>
    public readonly struct SplitPart
    {
        public readonly GameObject Go;
        public readonly RectInt SourceRect;

        public SplitPart(GameObject go, RectInt sourceRect)
        {
            Go = go;
            SourceRect = sourceRect;
        }
    }

    /// <summary>
    /// Shared per-object pixel state for everything that edits sprites at runtime —
    /// the eraser and the fire simulation both write into the same CPU mirror, so an
    /// object being burned and carved at once stays consistent.
    ///
    /// Writers mutate <see cref="Record.Pixels"/> directly and report what they touched
    /// through <see cref="Record.MarkPixels"/>. <see cref="PixelSpriteDriver"/> then does
    /// the expensive follow-up once per frame: dirty-rect GPU uploads, budgeted collider
    /// retraces, and throttled flood-fill split detection.
    /// </summary>
    public sealed class PixelSpriteRegistry
    {
        public static PixelSpriteRegistry Instance { get; private set; } = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => Instance = new PixelSpriteRegistry();

        /// <summary>
        /// An object waits this many times the duration of its own last collider retrace
        /// (or split scan) before doing another, so each burning object costs roughly
        /// 1/40th of the frame no matter how big or ragged its sprite is. Lower = more
        /// responsive physics, higher = cheaper.
        /// </summary>
        public static float ThrottleFactor = 40f;

        public static float MinPassInterval = 0.03f;
        public static float MaxPassInterval = 2f;

        public sealed class Record
        {
            public GameObject Go;
            public Texture2D Tex;
            public Color32[] Pixels;      // CPU-side mirror of Tex
            public int Width, Height;
            public float Ppu;
            public Vector2 PivotPx;       // sprite pivot in texture pixels
            public int SolidCount;        // pixels with alpha > 0

            // Pixel-write dirty rect (inclusive bounds).
            internal int dx0 = int.MaxValue, dy0 = int.MaxValue, dx1 = -1, dy1 = -1;
            internal bool pixelsDirty;
            internal bool colliderDirty;  // collider outline no longer matches pixels
            internal bool splitDirty;     // pixels were removed — may have disconnected

            // Unscaled-time gates; see PixelSpriteRegistry.Cooldown.
            internal float colliderReadyAt;
            internal float splitReadyAt;

            /// <summary>
            /// Report a written region. <paramref name="clearedPixels"/> is how many solid
            /// pixels went fully transparent, which drives split checks and the
            /// "nothing left, delete me" pass.
            /// </summary>
            public void MarkPixels(int x0, int y0, int x1, int y1, int clearedPixels = 0, bool colliderChanged = true)
            {
                pixelsDirty = true;
                if (colliderChanged) colliderDirty = true;
                if (clearedPixels > 0)
                {
                    SolidCount -= clearedPixels;
                    splitDirty = true;
                }

                if (x0 < dx0) dx0 = x0;
                if (y0 < dy0) dy0 = y0;
                if (x1 > dx1) dx1 = x1;
                if (y1 > dy1) dy1 = y1;
            }

            /// <summary>Texture pixels covered by one world-space unit, accounting for object scale.</summary>
            public float PixelsPerWorldUnit
            {
                get
                {
                    var s = Go.transform.lossyScale;
                    float scale = (Mathf.Abs(s.x) + Mathf.Abs(s.y)) * 0.5f;
                    return scale > 1e-5f ? Ppu / scale : Ppu;
                }
            }

            public bool WorldToPixel(Vector3 world, out int px, out int py)
            {
                var local = Go.transform.InverseTransformPoint(world);
                px = Mathf.FloorToInt(local.x * Ppu + PivotPx.x);
                py = Mathf.FloorToInt(local.y * Ppu + PivotPx.y);
                return px >= 0 && py >= 0 && px < Width && py < Height;
            }

            public Vector3 PixelToWorld(int px, int py)
            {
                var local = new Vector3(
                    (px + 0.5f - PivotPx.x) / Ppu,
                    (py + 0.5f - PivotPx.y) / Ppu,
                    0f);
                return Go.transform.TransformPoint(local);
            }
        }

        /// <summary>Raised after a sprite was split, once every piece is registered.</summary>
        public event Action<GameObject, IReadOnlyList<SplitPart>> Split;

        /// <summary>Raised just before an object with no pixels left is destroyed.</summary>
        public event Action<GameObject> Consumed;

        private readonly Dictionary<GameObject, Record> _records = new();
        private readonly List<GameObject> _scratch = new();
        private readonly List<GameObject> _dead = new();
        private Color32[] _uploadBuf = Array.Empty<Color32>();

        // ─────────────────────────────────────────────────────────────────────────
        // Records
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Record for <paramref name="go"/>, creating one (and swapping in a writable
        /// texture clone) on first touch. Returns null if the object has no sprite.
        /// </summary>
        public Record Get(GameObject go)
        {
            if (!go) return null;

            var sr = go.GetComponent<SpriteRenderer>();
            if (!sr || !sr.sprite) return null;

            if (_records.TryGetValue(go, out var rec))
            {
                // Something outside the registry replaced the sprite (the cracker does this).
                // The old mirror is meaningless now — rebuild from what's actually rendered.
                if (rec.Tex == sr.sprite.texture) return rec;
                DisposeRecord(rec, sr);
                _records.Remove(go);
            }

            var original = sr.sprite;
            var tex = SpriteTexUtil.CloneReadable(original);
            if (!tex) return null;

            // Preserve the original pivot so the sprite doesn't jump when the texture is swapped.
            var pivotNorm = new Vector2(
                original.pivot.x / original.rect.width,
                original.pivot.y / original.rect.height);

            sr.sprite = Sprite.Create(tex,
                new Rect(0, 0, tex.width, tex.height),
                pivotNorm,
                original.pixelsPerUnit);

            var pixels = tex.GetPixels32();
            rec = new Record
            {
                Go = go,
                Tex = tex,
                Pixels = pixels,
                Width = tex.width,
                Height = tex.height,
                Ppu = original.pixelsPerUnit,
                PivotPx = new Vector2(pivotNorm.x * tex.width, pivotNorm.y * tex.height),
                SolidCount = CountSolid(pixels),
            };
            _records[go] = rec;
            return rec;
        }

        public bool TryGet(GameObject go, out Record rec)
        {
            rec = null;
            return go && _records.TryGetValue(go, out rec);
        }

        /// <summary>Drop tracked state, freeing the owned texture when nothing renders it anymore.</summary>
        public void Forget(GameObject go)
        {
            if (!go || !_records.TryGetValue(go, out var rec)) return;
            DisposeRecord(rec, go.GetComponent<SpriteRenderer>());
            _records.Remove(go);
        }

        public void ForgetAll()
        {
            _records.Clear();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Per-frame work
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Upload dirty rectangles to the GPU. Cheap — call every frame.</summary>
        public void Flush()
        {
            foreach (var kv in _records)
            {
                var rec = kv.Value;
                if (!rec.pixelsDirty || !rec.Tex) continue;

                int w = rec.dx1 - rec.dx0 + 1;
                int h = rec.dy1 - rec.dy0 + 1;
                int n = w * h;
                if (n <= 0) { ClearDirtyRect(rec); continue; }
                if (_uploadBuf.Length != n) _uploadBuf = new Color32[n];

                for (int yy = 0; yy < h; yy++)
                {
                    int src = (rec.dy0 + yy) * rec.Width + rec.dx0;
                    int dst = yy * w;
                    Array.Copy(rec.Pixels, src, _uploadBuf, dst, w);
                }

                rec.Tex.SetPixels32(rec.dx0, rec.dy0, w, h, _uploadBuf);
                rec.Tex.Apply(false, false);
                ClearDirtyRect(rec);
            }
        }

        /// <summary>
        /// Retrace colliders of modified sprites so physics matches the pixels.
        ///
        /// Both this and <see cref="ProcessSplits"/> are self-throttling: neither the
        /// per-frame budget nor a fixed interval is enough on its own, because a single
        /// retrace of a big fire-ragged sprite can cost tens of milliseconds and the
        /// budget is only checked between objects. Each record instead earns a cooldown
        /// proportional to what its own last pass cost, so heavy objects back off on
        /// their own and light ones stay responsive.
        /// </summary>
        public void RefreshColliders(int simplifyLevel, double maxMillis = double.MaxValue, bool force = false)
        {
            if (_records.Count == 0) return;
            Flush(); // collider tracing reads the texture — make sure it's current

            float now = Time.unscaledTime;
            if (!CollectDirty(r => r.colliderDirty && (force || now >= r.colliderReadyAt))) return;

            var sw = System.Diagnostics.Stopwatch.StartNew();
            double spent = 0;
            foreach (var go in _scratch)
            {
                if (!force && spent > maxMillis) break;
                if (!_records.TryGetValue(go, out var rec)) continue;

                RebuildCollider(go, simplifyLevel);
                rec.colliderDirty = false;

                double cost = sw.Elapsed.TotalMilliseconds - spent;
                spent += cost;
                rec.colliderReadyAt = now + Cooldown(cost);
            }
        }

        /// <summary>
        /// Check whether any modified sprite fell apart into separate blobs and split
        /// it in place. Flood-fills the whole texture, so this is the throttled one.
        /// </summary>
        // 16px (a 4x4 chunk) is the smallest piece worth spawning a rigidbody for at the
        // 20 PPU art size; the old 64 was tuned when sprites were 5x larger.
        public void ProcessSplits(int simplifyLevel, int minPixels = 16, bool force = false)
        {
            if (_records.Count == 0) return;
            Flush();

            // Snapshot keys: splitting spawns clones and mutates the dictionary.
            float now = Time.unscaledTime;
            if (!CollectDirty(r => r.splitDirty && (force || now >= r.splitReadyAt))) return;

            var sw = System.Diagnostics.Stopwatch.StartNew();
            double spent = 0;
            foreach (var go in _scratch)
            {
                if (!_records.TryGetValue(go, out var rec)) continue;
                rec.splitDirty = false;
                ProcessSplit(go, rec, simplifyLevel, minPixels);

                double cost = sw.Elapsed.TotalMilliseconds - spent;
                spent += cost;
                rec.splitReadyAt = now + Cooldown(cost);
            }
        }

        /// <summary>
        /// How long an object must wait before repeating a pass that just cost
        /// <paramref name="millis"/>. Keeps each object's share of the frame near
        /// 1/<see cref="ThrottleFactor"/> regardless of its size or complexity.
        /// </summary>
        private static float Cooldown(double millis) =>
            Mathf.Clamp((float)millis * ThrottleFactor * 0.001f, MinPassInterval, MaxPassInterval);

        /// <summary>Destroy objects whose last solid pixel is gone (erased or burnt away).</summary>
        public void CollectConsumed()
        {
            if (_records.Count == 0) return;
            if (!CollectDirty(r => r.SolidCount <= 0)) return;

            foreach (var go in _scratch)
            {
                if (!_records.TryGetValue(go, out var rec)) continue;
                _records.Remove(go);
                if (rec.Tex) UnityEngine.Object.Destroy(rec.Tex);
                Consumed?.Invoke(go);
                UnityEngine.Object.Destroy(go);
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Internals
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Snapshot records matching <paramref name="predicate"/> into _scratch,
        /// dropping records whose GameObject has been destroyed externally.
        /// </summary>
        private bool CollectDirty(Func<Record, bool> predicate)
        {
            _scratch.Clear();
            _dead.Clear();
            foreach (var kv in _records)
            {
                if (!kv.Key) { _dead.Add(kv.Key); continue; }
                if (predicate(kv.Value)) _scratch.Add(kv.Key);
            }
            foreach (var key in _dead) _records.Remove(key);
            return _scratch.Count > 0;
        }

        private void ProcessSplit(GameObject go, Record rec, int simplifyLevel, int minPixels)
        {
            if (!go.GetComponent<SpriteRenderer>()) return;

            // rec.Pixels is the authoritative CPU mirror — saves a full GetPixels32 copy.
            var parts = SpriteSplitHelper.TrySplitInPlace(go, simplifyLevel,
                alphaThreshold: 0.1f, minPixels: minPixels, pixels: rec.Pixels);
            if (parts == null) return; // still one piece; RefreshColliders keeps the outline current

            // The pre-split texture belongs to the registry and no sprite references it now.
            if (rec.Tex) UnityEngine.Object.Destroy(rec.Tex);
            _records.Remove(go);

            // Re-track every piece so later edits hit a cached buffer. Pieces get fresh
            // textures and colliders from the split, so they start clean.
            foreach (var part in parts)
            {
                var sprite = part.Go.GetComponent<SpriteRenderer>().sprite;
                var tex = (Texture2D)sprite.texture;
                var pixels = tex.GetPixels32();
                _records[part.Go] = new Record
                {
                    Go = part.Go,
                    Tex = tex,
                    Pixels = pixels,
                    Width = tex.width,
                    Height = tex.height,
                    Ppu = sprite.pixelsPerUnit,
                    PivotPx = sprite.pivot,
                    SolidCount = CountSolid(pixels),
                };
            }

            Split?.Invoke(go, parts);
        }

        private static void RebuildCollider(GameObject go, int simplifyLevel)
        {
            if (!go.GetComponent<SpriteRenderer>()) return;

            var existing = go.GetComponent<PolygonCollider2D>();
            if (existing) UnityEngine.Object.DestroyImmediate(existing);
            var poly = go.AddComponent<PolygonCollider2D>();
            ColliderSimplifier2D.Simplify(poly, simplifyLevel);
            MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
        }

        /// <summary>Free a record's texture unless the renderer is still displaying it.</summary>
        private static void DisposeRecord(Record rec, SpriteRenderer sr)
        {
            if (!rec.Tex) return;
            bool stillRendered = sr && sr.sprite && sr.sprite.texture == rec.Tex;
            if (!stillRendered) UnityEngine.Object.Destroy(rec.Tex);
        }

        private static void ClearDirtyRect(Record rec)
        {
            rec.pixelsDirty = false;
            rec.dx0 = int.MaxValue; rec.dy0 = int.MaxValue;
            rec.dx1 = -1; rec.dy1 = -1;
        }

        private static int CountSolid(Color32[] pixels)
        {
            int n = 0;
            for (int i = 0; i < pixels.Length; i++)
                if (pixels[i].a > 0) n++;
            return n;
        }
    }
}
