using System;
using System.Collections.Generic;
using Spawners;
using UnityEngine;

/// <summary>
/// Per-pixel sprite erasing with batched GPU uploads and decoupled collider rebuilds.
///
/// Usage:
///   service.EraseCircle(go, worldPos, radius);  // call as often as you like
///   service.Flush();                            // once per frame after a batch of erases
///   service.RebuildModifiedColliders(level);    // throttled; e.g. every 0.15s + on mouse-up
/// </summary>
public class SpriteEraseService
{
    private class Record
    {
        public Texture2D tex;
        public Color32[] pixels;     // CPU-side mirror of tex
        public float ppu;

        // Pixel-write dirty rect (inclusive bounds).
        public int dx0 = int.MaxValue, dy0 = int.MaxValue;
        public int dx1 = -1, dy1 = -1;
        public bool pixelsDirty;
        public bool colliderDirty;
    }

    private readonly Dictionary<GameObject, Record> _records = new();
    private readonly List<GameObject> _scratch = new();
    private Color32[] _uploadBuf = Array.Empty<Color32>();

    // ─────────────────────────────────────────────────────────────────────────
    // Painting
    // ─────────────────────────────────────────────────────────────────────────

    public void EraseCircle(GameObject go, Vector3 worldPos, float brushRadius)
    {
        var rec = GetOrInit(go);
        if (rec == null) return;

        var local = go.transform.InverseTransformPoint(worldPos);
        int texW = rec.tex.width;
        int texH = rec.tex.height;

        int cx = Mathf.FloorToInt(local.x * rec.ppu + texW * 0.5f);
        int cy = Mathf.FloorToInt(local.y * rec.ppu + texH * 0.5f);
        int r  = Mathf.CeilToInt(brushRadius * rec.ppu);
        int r2 = r * r;

        int xmin = Mathf.Max(0, cx - r);
        int xmax = Mathf.Min(texW - 1, cx + r);
        int ymin = Mathf.Max(0, cy - r);
        int ymax = Mathf.Min(texH - 1, cy + r);
        if (xmax < xmin || ymax < ymin) return;

        var pix = rec.pixels;
        bool changed = false;

        for (int y = ymin; y <= ymax; y++)
        {
            int dy = y - cy;
            int dy2 = dy * dy;
            int row = y * texW;
            for (int x = xmin; x <= xmax; x++)
            {
                int dx = x - cx;
                if (dx * dx + dy2 > r2) continue;
                int idx = row + x;
                if (pix[idx].a == 0) continue;   // already cleared
                pix[idx].a = 0;
                changed = true;
            }
        }

        if (!changed) return;

        rec.pixelsDirty = true;
        rec.colliderDirty = true;
        if (xmin < rec.dx0) rec.dx0 = xmin;
        if (ymin < rec.dy0) rec.dy0 = ymin;
        if (xmax > rec.dx1) rec.dx1 = xmax;
        if (ymax > rec.dy1) rec.dy1 = ymax;
    }

    /// <summary>Upload dirty rectangles to GPU. Call once per frame after a batch of erases.</summary>
    public void Flush()
    {
        foreach (var kv in _records)
        {
            var rec = kv.Value;
            if (!rec.pixelsDirty) continue;

            int w = rec.dx1 - rec.dx0 + 1;
            int h = rec.dy1 - rec.dy0 + 1;
            int n = w * h;
            if (_uploadBuf.Length != n) _uploadBuf = new Color32[n];

            int texW = rec.tex.width;
            for (int yy = 0; yy < h; yy++)
            {
                int src = (rec.dy0 + yy) * texW + rec.dx0;
                int dst = yy * w;
                Array.Copy(rec.pixels, src, _uploadBuf, dst, w);
            }

            rec.tex.SetPixels32(rec.dx0, rec.dy0, w, h, _uploadBuf);
            rec.tex.Apply(false, false);

            rec.pixelsDirty = false;
            rec.dx0 = int.MaxValue; rec.dy0 = int.MaxValue;
            rec.dx1 = -1; rec.dy1 = -1;
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Collider rebuilds (expensive — throttle from the caller)
    // ─────────────────────────────────────────────────────────────────────────

    public void RebuildModifiedColliders(int simplifyLevel)
    {
        if (_records.Count == 0) return;

        // Snapshot keys: rebuilding can spawn clones and mutate the dictionary.
        _scratch.Clear();
        foreach (var kv in _records)
        {
            if (kv.Key == null) continue;
            if (kv.Value.colliderDirty) _scratch.Add(kv.Key);
        }

        foreach (var go in _scratch)
        {
            if (go == null) { _records.Remove(go); continue; }
            if (!_records.TryGetValue(go, out var rec)) continue;
            ProcessRebuild(go, rec, simplifyLevel);
            if (_records.TryGetValue(go, out rec)) rec.colliderDirty = false;
        }
    }

    /// <summary>Release tracked state for a specific GameObject (e.g. when externally destroyed).</summary>
    public void Forget(GameObject go) => _records.Remove(go);

    public void ForgetAll() => _records.Clear();

    // ─────────────────────────────────────────────────────────────────────────
    // Internals
    // ─────────────────────────────────────────────────────────────────────────

    private Record GetOrInit(GameObject go)
    {
        if (_records.TryGetValue(go, out var rec)) return rec;

        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr || !sr.sprite) return null;

        var original = sr.sprite;
        var tex = SpriteTexUtil.CloneReadable(original);
        if (!tex) return null;

        sr.sprite = Sprite.Create(tex,
            new Rect(0, 0, tex.width, tex.height),
            new Vector2(0.5f, 0.5f),
            original.pixelsPerUnit);

        rec = new Record
        {
            tex = tex,
            pixels = tex.GetPixels32(),
            ppu = original.pixelsPerUnit
        };
        _records[go] = rec;
        return rec;
    }

    private void ProcessRebuild(GameObject go, Record rec, int simplifyLevel)
    {
        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr) return;

        // Did the erase disconnect the sprite into multiple solid blobs?
        if (SpriteSplitUtil.TrySplit(go, rec.tex, rec.ppu, alphaThreshold: 0.1f, minPixels: 64, out var parts))
        {
            parts.Sort((a, b) => (b.rect.width * b.rect.height).CompareTo(a.rect.width * a.rect.height));

            float ppu = rec.ppu;
            int centerX = rec.tex.width / 2;
            int centerY = rec.tex.height / 2;
            var basePos = go.transform.position;

            // Clones for all non-largest parts.
            for (int i = 1; i < parts.Count; i++)
            {
                var clone = UnityEngine.Object.Instantiate(go, go.transform.parent);
                var b = parts[i].rect;
                float xShift = ((b.xMin + b.xMax) * 0.5f - centerX) / (2f * ppu);
                float yShift = ((b.yMin + b.yMax) * 0.5f - centerY) / (2f * ppu);
                clone.transform.position = new Vector3(basePos.x + xShift, basePos.y + yShift, basePos.z);

                ApplyPart(clone, clone.GetComponent<SpriteRenderer>(), parts[i].tex, ppu, simplifyLevel);

                // Track the new part so subsequent erases hit a cached buffer.
                _records[clone] = new Record
                {
                    tex = parts[i].tex,
                    pixels = parts[i].tex.GetPixels32(),
                    ppu = ppu
                };
            }

            // Largest part becomes the original.
            var mb = parts[0].rect;
            float xMainShift = ((mb.xMin + mb.xMax) * 0.5f - centerX) / (2f * ppu);
            float yMainShift = ((mb.yMin + mb.yMax) * 0.5f - centerY) / (2f * ppu);
            go.transform.position = new Vector3(basePos.x + xMainShift, basePos.y + yMainShift, basePos.z);

            ApplyPart(go, sr, parts[0].tex, ppu, simplifyLevel);

            // Re-cache pixels for the trimmed texture.
            rec.tex = parts[0].tex;
            rec.pixels = parts[0].tex.GetPixels32();
            rec.pixelsDirty = false;
            rec.dx0 = int.MaxValue; rec.dy0 = int.MaxValue;
            rec.dx1 = -1; rec.dy1 = -1;
            return;
        }

        // No split — just rebuild the collider against the updated texture.
        var existing = go.GetComponent<PolygonCollider2D>();
        if (existing) UnityEngine.Object.DestroyImmediate(existing);
        var poly = go.AddComponent<PolygonCollider2D>();
        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }

    private static void ApplyPart(GameObject go, SpriteRenderer sr, Texture2D partTex, float ppu, int simplifyLevel)
    {
        sr.sprite = Sprite.Create(partTex, new Rect(0, 0, partTex.width, partTex.height), new Vector2(0.5f, 0.5f), ppu);

        var existing = go.GetComponent<PolygonCollider2D>();
        if (existing) UnityEngine.Object.DestroyImmediate(existing);
        var poly = go.AddComponent<PolygonCollider2D>();
        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }
}
