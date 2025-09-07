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

        var simplifiedOpen = RDP(open, tolerance);

        // Re-close
        if (simplifiedOpen.Count < 3)
            return ring;

        // Ensure orientation preserved roughly (optional)
        if (Area(open) < 0f && Area(simplifiedOpen) > 0f)
            simplifiedOpen.Reverse();

        simplifiedOpen.Add(simplifiedOpen[0]);
        return simplifiedOpen.ToArray();
    }

    static List<Vector2> RDP(List<Vector2> pts, float epsilon)
    {
        if (pts.Count < 3) return new List<Vector2>(pts);

        int index = -1;
        float maxDist = 0f;

        Vector2 a = pts[0];
        Vector2 b = pts[pts.Count - 1];

        for (int i = 1; i < pts.Count - 1; i++)
        {
            float d = PerpDistance(pts[i], a, b);
            if (d > maxDist)
            {
                index = i;
                maxDist = d;
            }
        }

        if (maxDist > epsilon)
        {
            var left = RDP(pts.GetRange(0, index + 1), epsilon);
            var right = RDP(pts.GetRange(index, pts.Count - index), epsilon);

            // merge, removing duplicate middle point
            left.RemoveAt(left.Count - 1);
            left.AddRange(right);
            return left;
        }
        else
        {
            return new List<Vector2> { a, b };
        }
    }

    static float PerpDistance(Vector2 p, Vector2 a, Vector2 b)
    {
        float l2 = (b - a).sqrMagnitude;
        if (l2 == 0f) return (p - a).magnitude;
        float t = Mathf.Clamp01(Vector2.Dot(p - a, b - a) / l2);
        Vector2 proj = a + t * (b - a);
        return (p - proj).magnitude;
    }

    static float Area(List<Vector2> pts)
    {
        float s = 0f;
        for (int i = 0, j = pts.Count - 1; i < pts.Count; j = i++)
            s += (pts[j].x * pts[i].y - pts[i].x * pts[j].y);
        return 0.5f * s;
    }
}