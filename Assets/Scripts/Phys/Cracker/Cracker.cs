using System.Collections.Generic;
using Spawners;
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
            int simplifyLevel = 0,
            Vector3? impactWorld = null,
            float impactImpulse = 0f,
            float impactFalloff = 1f)
        {
            if (!go || pieceCount < 2) return;

            var sr = go.GetComponent<SpriteRenderer>();
            if (!sr || !sr.sprite) return;

            var srcSprite = sr.sprite;
            var tex = GetReadableCopy(srcSprite, out bool ownsTex);
            if (!tex) { Debug.LogWarning("Crack: texture not readable"); return; }

            int w = tex.width, h = tex.height;
            float ppu = srcSprite.pixelsPerUnit;
            var src = tex.GetPixels32();

            // Pixels are on the CPU now — release the temporary copy before any early return can leak it.
            if (ownsTex) Object.Destroy(tex);

            // Solid mask
            byte alphaByte = (byte)Mathf.RoundToInt(Mathf.Clamp01(alphaThreshold) * 255f);
            bool[] solid = new bool[w * h];
            int solidCount = 0;
            for (int i = 0; i < src.Length; i++)
            {
                bool s = src[i].a > alphaByte;
                solid[i] = s; if (s) solidCount++;
            }
            if (solidCount < minPixels) return;

            // Convert impact world point into texture-pixel space (if provided).
            // The sprite pivot is where local (0,0) sits in the texture.
            Vector2? impactPx = null;
            float falloffPx = Mathf.Max(0.01f, impactFalloff) * ppu;
            if (impactWorld.HasValue)
            {
                var local = go.transform.InverseTransformPoint(impactWorld.Value);
                var pivot = srcSprite.pivot;
                impactPx = new Vector2(local.x * ppu + pivot.x, local.y * ppu + pivot.y);
            }

            // Seeds inside solid — weighted toward impact when provided.
            var rng = (seed < 0) ? new System.Random() : new System.Random(seed);
            var seeds = PickSeedsBiased(solid, w, h,
                                        Mathf.Min(pieceCount, solidCount),
                                        rng, impactPx, falloffPx);
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

                // copy (bucket pixels are inside the bucket's bounds by construction)
                foreach (var p in pixels)
                    dst[(p.y - rect.y) * bw + (p.x - rect.x)] = src[p.y * w + p.x];

                var t = new Texture2D(bw, bh, TextureFormat.ARGB32, false);
                t.SetPixels32(dst);
                t.Apply(false, false);
                parts.Add((t, rect));
            }

            if (parts.Count <= 1)
            {
                // Nothing to crack into — don't leak the piece textures already created.
                foreach (var p in parts) Object.Destroy(p.tex);
                return;
            }

            // Largest first
            parts.Sort((a, b) =>
                (b.rect.width * b.rect.height).CompareTo(a.rect.width * a.rect.height));

            // --- before changing go, cache original transform ---
            var parent = go.transform.parent;
            var origRot = go.transform.rotation;
            var origL2W = go.transform.localToWorldMatrix; // local -> world BEFORE moving

            // Offsets are measured from the sprite pivot (= the GO origin), not the texture center.
            Vector2 pivotPx = srcSprite.pivot;

            var shardWorldPos = new Vector3[parts.Count];
            for (int i = 0; i < parts.Count; i++)
            {
                var rect = parts[i].rect;
                Vector2 pieceCenterPx = rect.center;
                Vector3 localOffset = new Vector3(
                    (pieceCenterPx.x - pivotPx.x) / ppu,
                    (pieceCenterPx.y - pivotPx.y) / ppu,
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
            var allShards = new List<GameObject>(parts.Count) { go };
            for (int i = 1; i < parts.Count; i++)
            {
                var (texI, rectI) = parts[i];
                var clone = Object.Instantiate(go, shardWorldPos[i], origRot, parent);
                var cloneSr = clone.GetComponent<SpriteRenderer>();
                ApplySpriteAndCollider(cloneSr, texI, ppu, simplifyLevel);
                allShards.Add(clone);
            }

            // Radial impulses from impact: closer shards get punched harder, far ones drift.
            if (impactWorld.HasValue && impactImpulse > 0f)
            {
                Vector2 impactPt = impactWorld.Value;
                float falloffWorld = Mathf.Max(0.01f, impactFalloff);
                for (int i = 0; i < allShards.Count; i++)
                {
                    var shard = allShards[i];
                    var rb = shard.GetComponent<Rigidbody2D>();
                    if (!rb) continue;

                    Vector2 toShard = (Vector2)shard.transform.position - impactPt;
                    float dist = toShard.magnitude;
                    Vector2 dir;
                    if (dist > 1e-4f) dir = toShard / dist;
                    else { float ang = Random.value * Mathf.PI * 2f; dir = new Vector2(Mathf.Cos(ang), Mathf.Sin(ang)); }
                    float magnitude = impactImpulse / (1f + dist / falloffWorld);
                    rb.AddForce(dir * magnitude, ForceMode2D.Impulse);
                    // A little spin makes the burst feel less rigid.
                    rb.AddTorque((Random.value - 0.5f) * magnitude * 0.5f, ForceMode2D.Impulse);
                }
            }
        }

        // ----- helpers -----

        /// <summary>Readable pixels for the sprite. <paramref name="owned"/> is true when the
        /// returned texture is a temporary copy the caller must destroy.</summary>
        static Texture2D GetReadableCopy(Sprite src, out bool owned)
        {
            owned = true;
            try { var c = SpriteTexUtil.CloneReadable(src); if (c) return c; } catch { }
            owned = false;
            var t = src.texture;
            return (t && t.isReadable) ? t : null;
        }

        /// <summary>
        /// Weighted reservoir sample (A-Res). When <paramref name="impactPx"/> is set, weights fall off
        /// with distance so picks cluster near impact while still leaving some across the rest of the mask.
        /// </summary>
        static List<Vector2Int> PickSeedsBiased(bool[] solid, int w, int h, int count,
                                                System.Random rng, Vector2? impactPx, float falloffPx)
        {
            // Fall back to fast uniform sampling if no impact bias.
            if (!impactPx.HasValue) return PickSeedsInsideSolid(solid, w, h, count, rng);

            var keys = new float[count];
            var pos  = new Vector2Int[count];
            int filled = 0;

            float ix = impactPx.Value.x;
            float iy = impactPx.Value.y;
            float f2 = falloffPx * falloffPx;

            for (int y = 0; y < h; y++)
            {
                int yo = y * w;
                for (int x = 0; x < w; x++)
                {
                    if (!solid[yo + x]) continue;

                    float dx = x - ix;
                    float dy = y - iy;
                    // Weight peaks at impact, decays with squared distance. +small noise so equal-weighted
                    // pixels don't all collide on the same key.
                    float weight = 1f / (1f + (dx * dx + dy * dy) / f2);

                    double u = rng.NextDouble();
                    if (u < 1e-12) u = 1e-12;
                    float key = (float)System.Math.Pow(u, 1.0 / weight);

                    if (filled < count)
                    {
                        keys[filled] = key;
                        pos[filled] = new Vector2Int(x, y);
                        filled++;
                        if (filled == count) HeapifyMin(keys, pos, count);
                    }
                    else if (key > keys[0])
                    {
                        keys[0] = key;
                        pos[0] = new Vector2Int(x, y);
                        SiftDown(keys, pos, 0, count);
                    }
                }
            }

            var result = new List<Vector2Int>(filled);
            for (int i = 0; i < filled; i++) result.Add(pos[i]);
            return result;
        }

        static void HeapifyMin(float[] keys, Vector2Int[] pos, int n)
        {
            for (int i = n / 2 - 1; i >= 0; i--) SiftDown(keys, pos, i, n);
        }

        static void SiftDown(float[] keys, Vector2Int[] pos, int i, int n)
        {
            while (true)
            {
                int l = 2 * i + 1, r = 2 * i + 2, s = i;
                if (l < n && keys[l] < keys[s]) s = l;
                if (r < n && keys[r] < keys[s]) s = r;
                if (s == i) break;
                (keys[i], keys[s]) = (keys[s], keys[i]);
                (pos[i], pos[s]) = (pos[s], pos[i]);
                i = s;
            }
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
            var poly = go.AddComponent<PolygonCollider2D>();
            ColliderSimplifier2D.Simplify(poly, simplifyLevel);
            MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
        }
    }
}