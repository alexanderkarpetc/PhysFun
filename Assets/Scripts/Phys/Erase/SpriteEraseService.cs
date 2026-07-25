using Phys.Pixels;
using UnityEngine;

/// <summary>
/// Per-pixel sprite erasing. Writes straight into the shared
/// <see cref="PixelSpriteRegistry"/> mirror; <see cref="PixelSpriteDriver"/> takes care
/// of the GPU upload, collider retrace and split detection once per frame.
///
/// Call <see cref="PixelSpriteDriver.FinalizeNow"/> when a stroke ends if you want the
/// result to settle on that exact frame instead of within the split throttle.
/// </summary>
public static class SpriteEraseService
{
    /// <summary>Clear every pixel of <paramref name="go"/> inside a world-space circle.</summary>
    public static void EraseCircle(GameObject go, Vector3 worldPos, float worldRadius)
    {
        var rec = PixelSpriteRegistry.Instance.Get(go);
        if (rec == null) return;

        rec.WorldToPixel(worldPos, out int cx, out int cy);
        int r = Mathf.CeilToInt(worldRadius * rec.PixelsPerWorldUnit);
        int r2 = r * r;

        int xmin = Mathf.Max(0, cx - r);
        int xmax = Mathf.Min(rec.Width - 1, cx + r);
        int ymin = Mathf.Max(0, cy - r);
        int ymax = Mathf.Min(rec.Height - 1, cy + r);
        if (xmax < xmin || ymax < ymin) return;

        var pix = rec.Pixels;
        int cleared = 0;

        for (int y = ymin; y <= ymax; y++)
        {
            int dy = y - cy;
            int dy2 = dy * dy;
            int row = y * rec.Width;
            for (int x = xmin; x <= xmax; x++)
            {
                int dx = x - cx;
                if (dx * dx + dy2 > r2) continue;
                int idx = row + x;
                if (pix[idx].a == 0) continue;   // already cleared
                pix[idx].a = 0;
                cleared++;
            }
        }

        if (cleared == 0) return;
        rec.MarkPixels(xmin, ymin, xmax, ymax, cleared);
    }
}
