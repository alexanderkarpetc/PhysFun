using System;
using System.Collections.Generic;
using UnityEngine;

public static class SpriteSplitUtil
{
    private const int Empty = -2;
    private const int Unvisited = -1;

    // Reused scratch buffers. A whole-texture flood fill used to allocate two bool[w*h]
    // plus a List<int> per component on every call — megabytes per second once a few
    // objects are burning. Everything below writes into these instead. Main thread only,
    // and each caller is done with the labels before the next call starts.
    private static int[] _label = Array.Empty<int>();
    private static int[] _stack = Array.Empty<int>();
    private static readonly List<Comp> Comps = new();

    private struct Comp
    {
        public int Id;
        public RectInt Bounds;
    }

    // threshold: alpha > threshold is solid. minPixels: ignore tiny crumbs.
    public static bool TrySplit(Texture2D tex, float alphaThreshold, int minPixels,
                                out List<(Texture2D tex, RectInt rect)> parts)
        => TrySplit(tex.GetPixels32(), tex.width, tex.height, alphaThreshold, minPixels, out parts);

    // Overload for callers that already hold a CPU-side pixel mirror.
    public static bool TrySplit(Color32[] src, int w, int h, float alphaThreshold, int minPixels,
                                out List<(Texture2D tex, RectInt rect)> parts)
    {
        parts = null;

        int n = w * h;
        if (n <= 0 || src == null || src.Length < n) return false;

        if (_label.Length < n)
        {
            _label = new int[n];
            _stack = new int[n];   // every pixel is pushed at most once
        }

        byte alphaByte = (byte)Mathf.RoundToInt(Mathf.Clamp01(alphaThreshold) * 255f);
        var label = _label;
        for (int i = 0; i < n; i++) label[i] = src[i].a > alphaByte ? Unvisited : Empty;

        Comps.Clear();
        int nextId = 0;

        // 4-connectivity flood fill over flat pixel indices, labelling in place.
        for (int start = 0; start < n; start++)
        {
            if (label[start] != Unvisited) continue;

            int id = nextId++;
            int sp = 0;
            _stack[sp++] = start;
            label[start] = id;

            int minX = start % w, maxX = minX;
            int minY = start / w, maxY = minY;
            int count = 0;

            while (sp > 0)
            {
                int idx = _stack[--sp];
                count++;

                int px = idx % w, py = idx / w;
                if (px < minX) minX = px;
                if (px > maxX) maxX = px;
                if (py < minY) minY = py;
                if (py > maxY) maxY = py;

                if (px + 1 < w  && label[idx + 1] == Unvisited) { label[idx + 1] = id; _stack[sp++] = idx + 1; }
                if (px - 1 >= 0 && label[idx - 1] == Unvisited) { label[idx - 1] = id; _stack[sp++] = idx - 1; }
                if (py + 1 < h  && label[idx + w] == Unvisited) { label[idx + w] = id; _stack[sp++] = idx + w; }
                if (py - 1 >= 0 && label[idx - w] == Unvisited) { label[idx - w] = id; _stack[sp++] = idx - w; }
            }

            if (count < minPixels) continue;   // crumb — stays labelled, just never emitted
            Comps.Add(new Comp
            {
                Id = id,
                Bounds = new RectInt(minX, minY, maxX - minX + 1, maxY - minY + 1),
            });
        }

        if (Comps.Count <= 1) return false;

        parts = new List<(Texture2D, RectInt)>(Comps.Count);
        foreach (var c in Comps)
            parts.Add(CreateSubTexture(src, label, w, c));

        return true;
    }

    private static (Texture2D tex, RectInt rect) CreateSubTexture(Color32[] src, int[] label, int srcW, Comp c)
    {
        var rect = c.Bounds;
        int bw = rect.width, bh = rect.height;
        var dst = new Color32[bw * bh]; // zero-init = fully transparent

        // Copy only this component's pixels — another component may overlap the bounds.
        for (int y = 0; y < bh; y++)
        {
            int srcRow = (rect.y + y) * srcW + rect.x;
            int dstRow = y * bw;
            for (int x = 0; x < bw; x++)
            {
                int s = srcRow + x;
                if (label[s] == c.Id) dst[dstRow + x] = src[s];
            }
        }

        var tex = new Texture2D(bw, bh, TextureFormat.ARGB32, false);
        tex.SetPixels32(dst);
        tex.Apply(false, false);
        return (tex, rect);
    }
}
