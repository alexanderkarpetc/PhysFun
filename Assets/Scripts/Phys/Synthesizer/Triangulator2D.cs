using System.Collections.Generic;
using UnityEngine;

// Basic ear-clipping triangulator for simple polygons (no self-intersections).
public static class Triangulator2D
{
    public static List<int> Triangulate(List<Vector2> poly)
    {
        var n = poly?.Count ?? 0;
        if (n < 3) return null;

        // Ensure CCW
        if (SignedArea(poly) < 0f) poly.Reverse();

        var indices = new List<int>(n);
        for (int i = 0; i < n; i++) indices.Add(i);

        var tris = new List<int>(Mathf.Max(0, (n - 2) * 3));
        int guard = 0, maxGuard = n * n;

        while (indices.Count > 3 && guard++ < maxGuard)
        {
            bool cutEar = false;
            for (int i = 0; i < indices.Count; i++)
            {
                int i0 = indices[(i - 1 + indices.Count) % indices.Count];
                int i1 = indices[i];
                int i2 = indices[(i + 1) % indices.Count];

                var a = poly[i0];
                var b = poly[i1];
                var c = poly[i2];

                if (Area2(a, b, c) <= 0f) continue; // not a convex ear

                bool contains = false;
                for (int j = 0; j < indices.Count; j++)
                {
                    int v = indices[j];
                    if (v == i0 || v == i1 || v == i2) continue;
                    if (PointInTri(poly[v], a, b, c)) { contains = true; break; }
                }
                if (contains) continue;

                // ear found
                tris.Add(i0); tris.Add(i1); tris.Add(i2);
                indices.RemoveAt(i);
                cutEar = true;
                break;
            }
            if (!cutEar) break; // possibly degenerate
        }

        if (indices.Count == 3)
        {
            tris.Add(indices[0]); tris.Add(indices[1]); tris.Add(indices[2]);
        }
        return tris;
    }

    static float SignedArea(List<Vector2> p)
    {
        float a = 0f;
        for (int i = 0; i < p.Count; i++)
        {
            var c = p[i];
            var n = p[(i + 1) % p.Count];
            a += (c.x * n.y - n.x * c.y);
        }
        return 0.5f * a;
    }

    static float Area2(Vector2 a, Vector2 b, Vector2 c) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);

    static bool PointInTri(Vector2 p, Vector2 a, Vector2 b, Vector2 c)
    {
        // barycentric technique (assumes CCW triangle)
        var v0 = c - a;
        var v1 = b - a;
        var v2 = p - a;

        float dot00 = Vector2.Dot(v0, v0);
        float dot01 = Vector2.Dot(v0, v1);
        float dot02 = Vector2.Dot(v0, v2);
        float dot11 = Vector2.Dot(v1, v1);
        float dot12 = Vector2.Dot(v1, v2);

        float invDen = 1f / (dot00 * dot11 - dot01 * dot01);
        float u = (dot11 * dot02 - dot01 * dot12) * invDen;
        float v = (dot00 * dot12 - dot01 * dot02) * invDen;

        return (u >= 0f) && (v >= 0f) && (u + v <= 1f);
    }
}