using System.Collections.Generic;
using UnityEngine;

public static class ColliderSimplifier2D
{
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
            var path = poly.GetPath(p);
            var simplified = SimplifyClosedPolygon(path, tol);
            if (simplified.Length >= 3)
                poly.SetPath(p, simplified);
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
    static Vector2[] SimplifyClosedPolygon(Vector2[] ring, float tolerance)
    {
        if (ring == null || ring.Length < 4) return ring; // need at least a triangle + closure
        // Ensure first != last for processing
        bool hadClosure = (ring[0] == ring[ring.Length - 1]);
        int n = hadClosure ? ring.Length - 1 : ring.Length;

        var open = new List<Vector2>(n);
        for (int i = 0; i < n; i++) open.Add(ring[i]);

        var simplifiedOpen = Spawners.DouglasPeucker2D.Simplify(open, tolerance);

        // Re-close
        if (simplifiedOpen.Count < 3)
            return ring;

        // Ensure orientation preserved roughly (optional)
        if (Area(open) < 0f && Area(simplifiedOpen) > 0f)
            simplifiedOpen.Reverse();

        simplifiedOpen.Add(simplifiedOpen[0]);
        return simplifiedOpen.ToArray();
    }

    static float Area(List<Vector2> pts)
    {
        float s = 0f;
        for (int i = 0, j = pts.Count - 1; i < pts.Count; j = i++)
            s += (pts[j].x * pts[i].y - pts[i].x * pts[j].y);
        return 0.5f * s;
    }
}