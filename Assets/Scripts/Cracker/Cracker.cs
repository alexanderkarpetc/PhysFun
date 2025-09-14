using System.Collections.Generic;
using UnityEngine;

namespace Cracker
{
    public static class Cracker
    {
        public static void Crack(
            GameObject go,
            int pieceCount,
            float alphaThreshold = 0.1f,
            int minPixels = 64,
            int seed = -1,
            int simplifyLevel = 0)
        {
            if (!go || pieceCount < 2) return;

            var sr = go.GetComponent<SpriteRenderer>();
            if (!sr || !sr.sprite) return;

            var srcSprite = sr.sprite;
            var tex = GetReadableCopy(srcSprite);
            if (!tex) { Debug.LogWarning("Crack: texture not readable"); return; }

            int w = tex.width, h = tex.height;
            float ppu = srcSprite.pixelsPerUnit;
            var src = tex.GetPixels32();

            // Solid mask
            bool[] solid = new bool[w * h];
            int solidCount = 0;
            for (int i = 0; i < src.Length; i++)
            {
                bool s = (src[i].a / 255f) > alphaThreshold;
                solid[i] = s; if (s) solidCount++;
            }
            if (solidCount < minPixels) return;

            // Seeds inside solid
            var rng = (seed < 0) ? new System.Random() : new System.Random(seed);
            var seeds = PickSeedsInsideSolid(solid, w, h, Mathf.Min(pieceCount, solidCount), rng);
            int S = seeds.Count;
            if (S < 2) return;

            // Buckets + bounds (correct min/max tracking)
            var buckets = new List<Vector2Int>[S];
            var minX = new int[S]; var minY = new int[S];
            var maxX = new int[S]; var maxY = new int[S];
            for (int i = 0; i < S; i++)
            {
                buckets[i] = new List<Vector2Int>(256);
                minX[i] = w; minY[i] = h;
                maxX[i] = -1; maxY[i] = -1;
            }

            // Assign each solid pixel to nearest seed
            for (int y = 0; y < h; y++)
            {
                int yOff = y * w;
                for (int x = 0; x < w; x++)
                {
                    int idx = yOff + x;
                    if (!solid[idx]) continue;

                    int best = 0, bestD2 = int.MaxValue;
                    for (int s = 0; s < S; s++)
                    {
                        int dx = x - seeds[s].x, dy = y - seeds[s].y;
                        int d2 = dx * dx + dy * dy;
                        if (d2 < bestD2) { bestD2 = d2; best = s; }
                    }

                    buckets[best].Add(new Vector2Int(x, y));
                    if (x < minX[best]) minX[best] = x;
                    if (y < minY[best]) minY[best] = y;
                    if (x > maxX[best]) maxX[best] = x;
                    if (y > maxY[best]) maxY[best] = y;
                }
            }

            // Build parts
            var parts = new List<(Texture2D tex, RectInt rect)>(S);
            for (int i = 0; i < S; i++)
            {
                var pixels = buckets[i];
                if (pixels.Count < minPixels) continue;
                if (minX[i] > maxX[i] || minY[i] > maxY[i]) continue; // empty

                var rect = new RectInt(
                    minX[i],
                    minY[i],
                    (maxX[i] - minX[i] + 1),
                    (maxY[i] - minY[i] + 1));

                int bw = rect.width, bh = rect.height;
                var dst = new Color32[bw * bh]; // zeroed (transparent)

                // copy
                foreach (var p in pixels)
                {
                    int dx = p.x - rect.x; if ((uint)dx >= (uint)bw) continue;
                    int dy = p.y - rect.y; if ((uint)dy >= (uint)bh) continue;
                    dst[dy * bw + dx] = src[p.y * w + p.x];
                }

                var t = new Texture2D(bw, bh, TextureFormat.ARGB32, false);
                t.SetPixels32(dst);
                t.Apply(false, false);
                parts.Add((t, rect));
            }

            if (parts.Count <= 1) return;

            // Largest first
            parts.Sort((a, b) =>
                (b.rect.width * b.rect.height).CompareTo(a.rect.width * a.rect.height));

            // --- before changing go, cache original transform ---
            var parent = go.transform.parent;
            var origRot = go.transform.rotation;
            var origL2W = go.transform.localToWorldMatrix; // local -> world BEFORE moving

            Vector2 texCenterPx = new Vector2(w * 0.5f, h * 0.5f);

            var shardWorldPos = new Vector3[parts.Count];
            for (int i = 0; i < parts.Count; i++)
            {
                var rect = parts[i].rect;
                Vector2 pieceCenterPx = rect.center;
                Vector3 localOffset = new Vector3(
                    (pieceCenterPx.x - texCenterPx.x) / ppu,
                    (pieceCenterPx.y - texCenterPx.y) / ppu,
                    0f);

                shardWorldPos[i] = origL2W.MultiplyPoint3x4(localOffset);
            }

// Apply largest to original and move it to its precomputed world pos
            {
                var (tex0, rect0) = parts[0];
                ApplySpriteAndCollider(sr, tex0, ppu, simplifyLevel);
                go.transform.SetPositionAndRotation(shardWorldPos[0], origRot);
            }

// Spawn others at their precomputed world positions (don’t recompute!)
            for (int i = 1; i < parts.Count; i++)
            {
                var (texI, rectI) = parts[i];
                var clone = Object.Instantiate(go, shardWorldPos[i], origRot, parent);
                var cloneSr = clone.GetComponent<SpriteRenderer>();
                ApplySpriteAndCollider(cloneSr, texI, ppu, simplifyLevel);
            }
        }

        // ----- helpers -----

        static Texture2D GetReadableCopy(Sprite src)
        {
            try { var c = SpriteTexUtil.CloneReadable(src); if (c) return c; } catch { }
            var t = src.texture;
            return (t && t.isReadable) ? t : null;
        }

        static List<Vector2Int> PickSeedsInsideSolid(bool[] solid, int w, int h, int count, System.Random rng)
        {
            var seeds = new List<Vector2Int>(count);
            int seen = 0;
            for (int y = 0; y < h; y++)
            {
                int yOff = y * w;
                for (int x = 0; x < w; x++)
                {
                    int idx = yOff + x;
                    if (!solid[idx]) continue;
                    seen++;
                    if (seeds.Count < count) seeds.Add(new Vector2Int(x, y));
                    else { int r = rng.Next(seen); if (r < count) seeds[r] = new Vector2Int(x, y); }
                }
            }
            return seeds;
        }

        static void ApplySpriteAndCollider(SpriteRenderer sr, Texture2D tex, float ppu, int simplifyLevel)
        {
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), ppu);

            var go = sr.gameObject;
            Object.DestroyImmediate(go.GetComponent<PolygonCollider2D>());
            go.AddComponent<PolygonCollider2D>();
            ColliderSimplifier2D.Simplify(go.GetComponent<PolygonCollider2D>(), simplifyLevel);
            // go.GetComponent<Rigidbody2D>().simulated = false;
        }
    }
}