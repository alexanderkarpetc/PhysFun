using Phys.Pixels;
using UnityEngine;

namespace Phys.Paint
{
    /// <summary>
    /// Per-pixel sprite staining: the other half of <see cref="SpriteEraseService"/>. The eraser
    /// takes material away, this only changes what the material looks like.
    ///
    /// That distinction is the whole reason it is its own service. A stain never touches alpha,
    /// so it can never free a piece, never invalidate a collider and never make an object
    /// disappear — which means it reports its write with <c>colliderChanged: false</c> and skips
    /// every expensive follow-up pass in <see cref="PixelSpriteDriver"/>. All a stain costs is
    /// its own pixels and the dirty-rect upload they ride out on, and blood lands often enough
    /// that this matters: a body coming apart over a stone floor paints hundreds of marks.
    ///
    /// Working in texture pixels is also what makes a stain stick. It is part of the sprite
    /// afterwards, so it rides the object through every rotation, split and carve for free, and
    /// a bloodied plank that burns takes its blood with it.
    /// </summary>
    public static class SpritePaintService
    {
        /// <summary>
        /// Tint every solid pixel of <paramref name="go"/> inside a world-space circle towards
        /// <paramref name="color"/>. Transparent pixels are left alone — paint lands on the
        /// object, never in the hole next to it.
        /// </summary>
        /// <param name="strength">How far the centre of the mark goes towards the colour, 0–1.</param>
        /// <param name="noise">
        /// How much of the rim is eaten away into speckle, 0–1. A stain with a clean edge reads
        /// as a decal that was pasted on; a ragged one reads as something that splashed.
        /// </param>
        /// <param name="seed">Varies the speckle, so two marks in the same place differ.</param>
        /// <returns>Pixels actually touched, so a caller can tell a hit from a miss.</returns>
        public static int PaintCircle(GameObject go, Vector3 worldPos, float worldRadius,
                                      Color32 color, float strength, float noise = 0.5f, int seed = 0)
        {
            if (!go || strength <= 0f || !CanStain(go)) return 0;

            var rec = PixelSpriteRegistry.Instance.Get(go);
            if (rec == null) return 0;

            rec.WorldToPixel(worldPos, out int cx, out int cy);

            int r = Mathf.Max(1, Mathf.CeilToInt(worldRadius * rec.PixelsPerWorldUnit));
            float inv = 1f / r;
            int r2 = r * r;

            int xmin = Mathf.Max(0, cx - r);
            int xmax = Mathf.Min(rec.Width - 1, cx + r);
            int ymin = Mathf.Max(0, cy - r);
            int ymax = Mathf.Min(rec.Height - 1, cy + r);
            if (xmax < xmin || ymax < ymin) return 0;

            var pix = rec.Pixels;
            int touched = 0;
            int tx0 = int.MaxValue, ty0 = int.MaxValue, tx1 = -1, ty1 = -1;

            for (int y = ymin; y <= ymax; y++)
            {
                int dy = y - cy;
                int dy2 = dy * dy;
                int row = y * rec.Width;

                for (int x = xmin; x <= xmax; x++)
                {
                    int dx = x - cx;
                    int d2 = dx * dx + dy2;
                    if (d2 > r2) continue;

                    int idx = row + x;
                    byte a = pix[idx].a;
                    if (a == 0) continue;            // nothing there to stain

                    // 1 dead centre, 0 at the rim. Everything below is shaped by it: the mark
                    // is opaque in the middle and thins out, and the speckle only reaches the
                    // part that was already thin.
                    float t = 1f - Mathf.Sqrt(d2) * inv;
                    if (t < Hash01(x, y, seed) * noise) continue;

                    float w = strength * (0.55f + 0.45f * t);
                    var p = pix[idx];
                    pix[idx] = new Color32(
                        (byte)(p.r + (color.r - p.r) * w),
                        (byte)(p.g + (color.g - p.g) * w),
                        (byte)(p.b + (color.b - p.b) * w),
                        a);                           // alpha is the eraser's business, not ours

                    touched++;
                    if (x < tx0) tx0 = x;
                    if (y < ty0) ty0 = y;
                    if (x > tx1) tx1 = x;
                    if (y > ty1) ty1 = y;
                }
            }

            if (touched == 0) return 0;

            // No cleared pixels and no collider change: upload the rect and nothing else.
            rec.MarkPixels(tx0, ty0, tx1, ty1, 0, colliderChanged: false);
            return touched;
        }

        /// <summary>
        /// A mark stretched along <paramref name="travel"/>: a few overlapping circles walked
        /// back up the direction the drop arrived from, shrinking as they go. What separates a
        /// splash from a dot is that it points somewhere, and a drop that came in fast should
        /// leave a longer one.
        /// </summary>
        public static int PaintSplat(GameObject go, Vector3 worldPos, Vector2 travel, float worldRadius,
                                     Color32 color, float strength, float noise = 0.5f, int seed = 0)
        {
            int touched = PaintCircle(go, worldPos, worldRadius, color, strength, noise, seed);
            if (touched == 0) return 0;   // the drop landed on something with no pixels to stain

            float speed = travel.magnitude;
            if (speed < 0.01f) return touched;

            Vector2 back = -travel / speed;
            int tail = Mathf.Clamp(Mathf.RoundToInt(speed * 0.35f), 0, 3);

            for (int i = 1; i <= tail; i++)
            {
                float f = 1f - i / (float)(tail + 1);
                Vector3 at = worldPos + (Vector3)(back * (worldRadius * 1.3f * i));
                touched += PaintCircle(go, at, worldRadius * f, color, strength * f, noise, seed + i);
            }

            return touched;
        }

        /// <summary>
        /// Whether a mark would survive on this object.
        ///
        /// Anything an <see cref="Animator"/> is driving is off limits. Staining means taking
        /// the renderer's sprite over with a writable clone of its texture, and an animation
        /// puts the original back on its next keyframe — so the mark would flicker out, and
        /// worse, every landing would clone the texture again. A living creature wears its
        /// blood by dying and leaving a corpse; the corpse is a still sprite and stains fine.
        /// </summary>
        public static bool CanStain(GameObject go) => go && !go.GetComponentInParent<Animator>();

        /// <summary>Stable per-pixel noise. Same trick as the flame view's colour jitter.</summary>
        private static float Hash01(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)(x * 73856093) ^ (uint)(y * 19349663) ^ (uint)(seed * 83492791);
                h ^= h >> 13;
                h *= 0x85EBCA6B;
                h ^= h >> 16;
                return (h & 0xFFFFFF) / 16777216f;
            }
        }
    }
}
