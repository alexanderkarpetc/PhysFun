using System.Collections.Generic;
using UnityEngine;

public static class SpriteSplitUtil
{
    // threshold: alpha > threshold is solid. minPixels: ignore tiny crumbs.
    public static bool TrySplit(GameObject go, Texture2D tex, float ppu, float alphaThreshold, int minPixels,
                                out List<(Texture2D tex, RectInt rect)> parts)
    {
        parts = null;
        var solid = BuildMask(tex, alphaThreshold);
        var comps = FindComponents(solid, minPixels);
        if (comps.Count <= 1) return false;

        parts = new List<(Texture2D, RectInt)>(comps.Count);
        foreach (var c in comps)
            parts.Add(CreateSubTexture(tex, c.bounds, c.pixels));

        return true;
    }

    // --- helpers ---

    struct Comp { public RectInt bounds; public List<Vector2Int> pixels; }

    static bool[,] BuildMask(Texture2D tex, float a)
    {
        int w = tex.width, h = tex.height;
        var px = tex.GetPixels32();
        var mask = new bool[w, h];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
            mask[x, y] = px[y * w + x].a / 255f > a;
        return mask;
    }

    // 4-connectivity flood fill
    static List<Comp> FindComponents(bool[,] mask, int minPixels)
    {
        int w = mask.GetLength(0), h = mask.GetLength(1);
        var seen = new bool[w, h];
        var res = new List<Comp>();
        var q = new Queue<Vector2Int>();

        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            if (!mask[x, y] || seen[x, y]) continue;

            q.Clear();
            q.Enqueue(new Vector2Int(x, y));
            seen[x, y] = true;

            var pixels = new List<Vector2Int>(256);
            int minX = x, maxX = x, minY = y, maxY = y;

            while (q.Count > 0)
            {
                var p = q.Dequeue();
                pixels.Add(p);
                if (p.x < minX) minX = p.x; if (p.x > maxX) maxX = p.x;
                if (p.y < minY) minY = p.y; if (p.y > maxY) maxY = p.y;

                // neighbors
                TryEnq(p.x + 1, p.y);
                TryEnq(p.x - 1, p.y);
                TryEnq(p.x, p.y + 1);
                TryEnq(p.x, p.y - 1);
            }

            if (pixels.Count >= minPixels)
            {
                var bounds = new RectInt(minX, minY, maxX - minX + 1, maxY - minY + 1);
                res.Add(new Comp { bounds = bounds, pixels = pixels });
            }
        }
        return res;

        void TryEnq(int nx, int ny)
        {
            if (nx < 0 || ny < 0 || nx >= w || ny >= h) return;
            if (!mask[nx, ny] || seen[nx, ny]) return;
            seen[nx, ny] = true;
            q.Enqueue(new Vector2Int(nx, ny));
        }
    }

    static (Texture2D tex, RectInt rect) CreateSubTexture(Texture2D src, RectInt rect, List<Vector2Int> pixels)
    {
        var dst = new Texture2D(rect.width, rect.height, TextureFormat.ARGB32, false);
        var clear = new Color32[rect.width * rect.height];
        // initialize transparent
        for (int i = 0; i < clear.Length; i++) clear[i] = new Color32(0,0,0,0);
        dst.SetPixels32(clear);

        // copy only component pixels
        foreach (var p in pixels)
        {
            int sx = p.x, sy = p.y;
            var c = src.GetPixel(sx, sy);
            int dx = sx - rect.x;
            int dy = sy - rect.y;
            dst.SetPixel(dx, dy, c);
        }
        dst.Apply(false, false);
        return (dst, rect);
    }
}