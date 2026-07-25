using System.Collections.Generic;
using UnityEngine;

public static class ColliderSimplifier2D
{
    // Reused across calls: a fire-ragged sprite can trace to hundreds of paths, and
    // the array-returning GetPath/SetPath overloads allocate on every one of them.
    private static readonly List<Vector2> RingBuf = new();
    private static readonly List<Vector2> OpenBuf = new();

    /// <summary>
    /// Simplify all paths of a PolygonCollider2D using RDP. level: 0..5.
    /// </summary>
    public static void Simplify(PolygonCollider2D poly, int level)
    {
        if (!poly) return;
        level = Mathf.Clamp(level, 0, 5);
        if (level == 0) return;

        float tol = ComputeTolerance(poly, level);

        int pathCount = poly.pathCount;
        for (int p = 0; p < pathCount; p++)
        {
            poly.GetPath(p, RingBuf);
            if (SimplifyClosedPolygon(RingBuf, tol, OpenBuf))
                poly.SetPath(p, OpenBuf);
        }
    }

    // --- helpers ---

    // Map level (0..5) -> world-space tolerance scaled by collider size.
    static float ComputeTolerance(PolygonCollider2D poly, int level)
    {
        // Scale tolerance to object size so it behaves consistently across scales.
        float scaleRef = Mathf.Max(poly.bounds.size.x, poly.bounds.size.y);
        // Tuned steps; increase if you want stronger reduction.
        float[] steps = { 0f, 0.005f, 0.01f, 0.02f, 0.04f, 0.08f };
        return steps[level] * scaleRef;
    }

    // RDP for a closed polygon: run on open ring and re-close.
    // Writes into <paramref name="result"/>; returns false to leave the path untouched.
    static bool SimplifyClosedPolygon(List<Vector2> ring, float tolerance, List<Vector2> result)
    {
        if (ring == null || ring.Count < 4) return false; // need at least a triangle + closure

        // Ensure first != last for processing
        bool hadClosure = ring[0] == ring[ring.Count - 1];
        int n = hadClosure ? ring.Count - 1 : ring.Count;

        result.Clear();
        for (int i = 0; i < n; i++) result.Add(ring[i]);

        var simplifiedOpen = Spawners.DouglasPeucker2D.Simplify(result, tolerance);

        // Re-close
        if (simplifiedOpen.Count < 3) return false;

        // Ensure orientation preserved roughly (optional)
        if (Area(result) < 0f && Area(simplifiedOpen) > 0f)
            simplifiedOpen.Reverse();

        result.Clear();
        result.AddRange(simplifiedOpen);
        result.Add(simplifiedOpen[0]);
        return true;
    }

    static float Area(List<Vector2> pts)
    {
        float s = 0f;
        for (int i = 0, j = pts.Count - 1; i < pts.Count; j = i++)
            s += (pts[j].x * pts[i].y - pts[i].x * pts[j].y);
        return 0.5f * s;
    }
}
