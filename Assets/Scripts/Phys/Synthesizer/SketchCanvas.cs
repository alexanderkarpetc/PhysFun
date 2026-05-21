using UnityEngine;

public class SketchCanvas
{
    public Texture2D Texture { get; }
    public int Width { get; }
    public int Height { get; }

    private readonly Color32 _background;

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
        Clear();
    }

    public void Clear()
    {
        var px = new Color32[Width * Height];
        for (int i = 0; i < px.Length; i++) px[i] = _background;
        Texture.SetPixels32(px);
        Texture.Apply(false, false);
    }

    public void StampDisc(int cx, int cy, int r, Color32 col)
    {
        int r2 = r * r;
        int xmin = Mathf.Max(0, cx - r);
        int xmax = Mathf.Min(Width - 1, cx + r);
        int ymin = Mathf.Max(0, cy - r);
        int ymax = Mathf.Min(Height - 1, cy + r);

        for (int y = ymin; y <= ymax; y++)
        {
            int dy = y - cy;
            for (int x = xmin; x <= xmax; x++)
            {
                int dx = x - cx;
                if (dx * dx + dy * dy > r2) continue;
                Texture.SetPixel(x, y, col);
            }
        }
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

    public void Apply() => Texture.Apply(false, false);

    public Texture2D SnapshotCopy()
    {
        var copy = new Texture2D(Width, Height, Texture.format, false);
        copy.SetPixels32(Texture.GetPixels32());
        copy.Apply(false, false);
        return copy;
    }
}
