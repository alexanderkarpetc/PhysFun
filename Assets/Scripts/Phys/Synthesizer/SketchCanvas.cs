using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Pure painting logic for the synthesizer. Backed by a CPU-side Color32[] mirror
/// of the GPU texture. Edits are batched into a dirty rect and uploaded via
/// SetPixels32(x,y,w,h,…) — no per-pixel SetPixel and no full-texture Apply.
/// </summary>
public class SketchCanvas
{
    public Texture2D Texture { get; }
    public int Width { get; }
    public int Height { get; }

    private readonly Color32[] _pixels;
    private readonly Color32 _background;

    private int _dx0 = int.MaxValue, _dy0 = int.MaxValue;
    private int _dx1 = -1, _dy1 = -1;
    private bool _dirty;

    private Color32[] _uploadBuf = Array.Empty<Color32>();

    public SketchCanvas(int width, int height, Color32 background)
    {
        Width = width;
        Height = height;
        _background = background;

        Texture = new Texture2D(width, height, TextureFormat.ARGB32, false)
        {
            wrapMode = TextureWrapMode.Clamp,
            filterMode = FilterMode.Point
        };
        _pixels = new Color32[width * height];
        Clear();
    }

    // ─────────────────────────────────────────────────────────────────────────

    public void Clear()
    {
        for (int i = 0; i < _pixels.Length; i++) _pixels[i] = _background;
        Texture.SetPixels32(_pixels);
        Texture.Apply(false, false);
        _dirty = false;
        ResetDirtyRect();
    }

    public void StampDisc(int cx, int cy, int r, Color32 col)
    {
        int r2 = r * r;
        int xmin = Mathf.Max(0, cx - r);
        int xmax = Mathf.Min(Width - 1, cx + r);
        int ymin = Mathf.Max(0, cy - r);
        int ymax = Mathf.Min(Height - 1, cy + r);
        if (xmax < xmin || ymax < ymin) return;

        bool changed = false;
        for (int y = ymin; y <= ymax; y++)
        {
            int dy = y - cy;
            int dy2 = dy * dy;
            int row = y * Width;
            for (int x = xmin; x <= xmax; x++)
            {
                int dx = x - cx;
                if (dx * dx + dy2 > r2) continue;
                _pixels[row + x] = col;
                changed = true;
            }
        }
        if (changed) ExpandDirty(xmin, ymin, xmax, ymax);
    }

    public void DrawSegment(Vector2Int a, Vector2Int b, int r, Color32 col)
    {
        float dist = Vector2Int.Distance(a, b);
        if (dist < 1e-3f) { StampDisc(a.x, a.y, r, col); return; }
        int steps = Mathf.Max(1, Mathf.CeilToInt(dist / Mathf.Max(1f, r * 0.5f)));
        for (int i = 0; i <= steps; i++)
        {
            float t = i / (float)steps;
            int x = Mathf.RoundToInt(Mathf.Lerp(a.x, b.x, t));
            int y = Mathf.RoundToInt(Mathf.Lerp(a.y, b.y, t));
            StampDisc(x, y, r, col);
        }
    }

    /// <summary>Push the accumulated dirty rect to the GPU. Call once per frame.</summary>
    public void Flush()
    {
        if (!_dirty) return;

        int w = _dx1 - _dx0 + 1;
        int h = _dy1 - _dy0 + 1;
        int n = w * h;
        if (_uploadBuf.Length != n) _uploadBuf = new Color32[n];

        for (int yy = 0; yy < h; yy++)
        {
            int src = (_dy0 + yy) * Width + _dx0;
            int dst = yy * w;
            Array.Copy(_pixels, src, _uploadBuf, dst, w);
        }
        Texture.SetPixels32(_dx0, _dy0, w, h, _uploadBuf);
        Texture.Apply(false, false);

        _dirty = false;
        ResetDirtyRect();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Export
    // ─────────────────────────────────────────────────────────────────────────

    /// <summary>
    /// Tight-crop the painted area (with a small margin) into a new texture.
    /// Returns null if the canvas is empty.
    /// </summary>
    public Texture2D SnapshotTrimmed(int margin = 4)
    {
        if (!FindContentBounds(out int xmin, out int ymin, out int xmax, out int ymax))
            return null;

        xmin = Mathf.Max(0, xmin - margin);
        ymin = Mathf.Max(0, ymin - margin);
        xmax = Mathf.Min(Width - 1, xmax + margin);
        ymax = Mathf.Min(Height - 1, ymax + margin);

        int w = xmax - xmin + 1;
        int h = ymax - ymin + 1;
        var dst = new Color32[w * h];
        for (int yy = 0; yy < h; yy++)
        {
            int srcIdx = (ymin + yy) * Width + xmin;
            int dstIdx = yy * w;
            Array.Copy(_pixels, srcIdx, dst, dstIdx, w);
        }

        var tex = new Texture2D(w, h, Texture.format, false);
        tex.SetPixels32(dst);
        tex.Apply(false, false);
        return tex;
    }

    public Texture2D SnapshotCopy()
    {
        var copy = new Texture2D(Width, Height, Texture.format, false);
        copy.SetPixels32(_pixels);
        copy.Apply(false, false);
        return copy;
    }

    /// <summary>
    /// Find all 4-connected non-transparent components and return each as its own
    /// tightly-cropped texture together with the original-canvas bounds. Useful
    /// when the caller wants disconnected blobs to become separate game objects.
    /// </summary>
    public List<(Texture2D tex, RectInt rect)> SnapshotComponents(int minPixels = 16, int margin = 4)
    {
        var result = new List<(Texture2D tex, RectInt rect)>();
        var seen = new bool[Width * Height];
        var queue = new Queue<int>(256);
        var pixList = new List<int>(256);

        for (int sy = 0; sy < Height; sy++)
        {
            int row = sy * Width;
            for (int sx = 0; sx < Width; sx++)
            {
                int sIdx = row + sx;
                if (seen[sIdx]) continue;
                seen[sIdx] = true;
                if (_pixels[sIdx].a == 0) continue;

                // BFS over the connected blob (4-connectivity).
                queue.Clear();
                pixList.Clear();
                queue.Enqueue(sIdx);
                int xmin = sx, xmax = sx, ymin = sy, ymax = sy;

                while (queue.Count > 0)
                {
                    int idx = queue.Dequeue();
                    pixList.Add(idx);

                    int px = idx % Width;
                    int py = idx / Width;
                    if (px < xmin) xmin = px; if (px > xmax) xmax = px;
                    if (py < ymin) ymin = py; if (py > ymax) ymax = py;

                    if (px + 1 < Width)  TryPush(idx + 1);
                    if (px - 1 >= 0)     TryPush(idx - 1);
                    if (py + 1 < Height) TryPush(idx + Width);
                    if (py - 1 >= 0)     TryPush(idx - Width);
                }

                if (pixList.Count < minPixels) continue;

                int rxmin = Mathf.Max(0, xmin - margin);
                int rymin = Mathf.Max(0, ymin - margin);
                int rxmax = Mathf.Min(Width - 1, xmax + margin);
                int rymax = Mathf.Min(Height - 1, ymax + margin);

                int rw = rxmax - rxmin + 1;
                int rh = rymax - rymin + 1;
                var dst = new Color32[rw * rh]; // zero-init = fully transparent

                for (int i = 0; i < pixList.Count; i++)
                {
                    int idx = pixList[i];
                    int px = idx % Width;
                    int py = idx / Width;
                    dst[(py - rymin) * rw + (px - rxmin)] = _pixels[idx];
                }

                var tex = new Texture2D(rw, rh, Texture.format, false);
                tex.SetPixels32(dst);
                tex.Apply(false, false);
                result.Add((tex, new RectInt(rxmin, rymin, rw, rh)));
            }
        }
        return result;

        void TryPush(int n)
        {
            if (seen[n]) return;
            seen[n] = true;
            if (_pixels[n].a == 0) return;
            queue.Enqueue(n);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────

    private bool FindContentBounds(out int xmin, out int ymin, out int xmax, out int ymax)
    {
        xmin = Width; ymin = Height; xmax = -1; ymax = -1;
        for (int y = 0; y < Height; y++)
        {
            int row = y * Width;
            for (int x = 0; x < Width; x++)
            {
                if (_pixels[row + x].a == 0) continue;
                if (x < xmin) xmin = x;
                if (y < ymin) ymin = y;
                if (x > xmax) xmax = x;
                if (y > ymax) ymax = y;
            }
        }
        return xmax >= 0;
    }

    private void ExpandDirty(int xmin, int ymin, int xmax, int ymax)
    {
        _dirty = true;
        if (xmin < _dx0) _dx0 = xmin;
        if (ymin < _dy0) _dy0 = ymin;
        if (xmax > _dx1) _dx1 = xmax;
        if (ymax > _dy1) _dy1 = ymax;
    }

    private void ResetDirtyRect()
    {
        _dx0 = int.MaxValue; _dy0 = int.MaxValue;
        _dx1 = -1; _dy1 = -1;
    }
}
