using System.Collections.Generic;
using UnityEngine;

public static class SpriteSplitUtil
{
    // threshold: alpha > threshold is solid. minPixels: ignore tiny crumbs.
    public static bool TrySplit(Texture2D tex, float alphaThreshold, int minPixels,
                                out List<(Texture2D tex, RectInt rect)> parts)
        => TrySplit(tex.GetPixels32(), tex.width, tex.height, alphaThreshold, minPixels, out parts);

    // Overload for callers that already hold a CPU-side pixel mirror.
    public static bool TrySplit(Color32[] src, int w, int h, float alphaThreshold, int minPixels,
                                out List<(Texture2D tex, RectInt rect)> parts)
    {
        parts = null;

        byte alphaByte = (byte)Mathf.RoundToInt(Mathf.Clamp01(alphaThreshold) * 255f);
        var solid = new bool[w * h];
        for (int i = 0; i < src.Length; i++) solid[i] = src[i].a > alphaByte;

        var comps = FindComponents(solid, w, h, minPixels);
        if (comps.Count <= 1) return false;

        parts = new List<(Texture2D, RectInt)>(comps.Count);
        foreach (var c in comps)
            parts.Add(CreateSubTexture(src, w, c.bounds, c.pixels));

        return true;
    }

    // --- helpers ---

    struct Comp { public RectInt bounds; public List<int> pixels; }

    // 4-connectivity flood fill over flat pixel indices.
    static List<Comp> FindComponents(bool[] mask, int w, int h, int minPixels)
    {
        var seen = new bool[w * h];
        var res = new List<Comp>();
        var q = new Queue<int>(256);

        for (int y = 0; y < h; y++)
        {
            int row = y * w;
            for (int x = 0; x < w; x++)
            {
                int start = row + x;
                if (!mask[start] || seen[start]) continue;

                q.Clear();
                q.Enqueue(start);
                seen[start] = true;

                var pixels = new List<int>(256);
                int minX = x, maxX = x, minY = y, maxY = y;

                while (q.Count > 0)
                {
                    int idx = q.Dequeue();
                    pixels.Add(idx);

                    int px = idx % w, py = idx / w;
                    if (px < minX) minX = px; if (px > maxX) maxX = px;
                    if (py < minY) minY = py; if (py > maxY) maxY = py;

                    // neighbors
                    if (px + 1 < w)  TryEnq(idx + 1);
                    if (px - 1 >= 0) TryEnq(idx - 1);
                    if (py + 1 < h)  TryEnq(idx + w);
                    if (py - 1 >= 0) TryEnq(idx - w);
                }

                if (pixels.Count >= minPixels)
                {
                    var bounds = new RectInt(minX, minY, maxX - minX + 1, maxY - minY + 1);
                    res.Add(new Comp { bounds = bounds, pixels = pixels });
                }
            }
        }
        return res;

        void TryEnq(int n)
        {
            if (!mask[n] || seen[n]) return;
            seen[n] = true;
            q.Enqueue(n);
        }
    }

    static (Texture2D tex, RectInt rect) CreateSubTexture(Color32[] src, int srcW, RectInt rect, List<int> pixels)
    {
        int bw = rect.width, bh = rect.height;
        var dst = new Color32[bw * bh]; // zero-init = fully transparent

        // copy only component pixels
        for (int i = 0; i < pixels.Count; i++)
        {
            int idx = pixels[i];
            int px = idx % srcW, py = idx / srcW;
            dst[(py - rect.y) * bw + (px - rect.x)] = src[idx];
        }

        var tex = new Texture2D(bw, bh, TextureFormat.ARGB32, false);
        tex.SetPixels32(dst);
        tex.Apply(false, false);
        return (tex, rect);
    }
}
