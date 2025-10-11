using System.Collections.Generic;
using UnityEngine;

namespace Spawners
{
    public static class DouglasPeucker2D
    {
        // Returns a simplified copy. Keeps first and last points.
        // todo check if this works better
        public static List<Vector2> Simplify(IList<Vector2> pts, float tolerance)
        {
            if (pts == null || pts.Count <= 2) return pts == null ? new List<Vector2>() : new List<Vector2>(pts);

            float tolSq = tolerance * tolerance;
            int n = pts.Count;

            // Marks for points to keep
            var keep = new bool[n];
            keep[0] = true;
            keep[n - 1] = true;

            // Process ranges [i, j]
            var stack = new Stack<(int i, int j)>();
            stack.Push((0, n - 1));

            while (stack.Count > 0)
            {
                var (i, j) = stack.Pop();
                if (j <= i + 1) continue;

                // Find point farthest from segment (i, j)
                int idxMax = -1;
                float maxDistSq = -1f;

                for (int k = i + 1; k < j; k++)
                {
                    float dSq = DistPointSegmentSq(pts[k], pts[i], pts[j]);
                    if (dSq > maxDistSq)
                    {
                        maxDistSq = dSq;
                        idxMax = k;
                    }
                }

                if (maxDistSq > tolSq)
                {
                    keep[idxMax] = true;
                    stack.Push((i, idxMax));
                    stack.Push((idxMax, j));
                }
                // else: all in (i, j) are within tolerance → omit them
            }

            // Build result preserving order
            var result = new List<Vector2>();
            for (int k = 0; k < n; k++)
                if (keep[k]) result.Add(pts[k]);

            // Ensure at least 2 points
            if (result.Count < 2)
                return new List<Vector2> { pts[0], pts[n - 1] };

            return result;
        }

        // Squared distance from point p to segment ab
        private static float DistPointSegmentSq(in Vector2 p, in Vector2 a, in Vector2 b)
        {
            Vector2 ab = b - a;
            float abLenSq = ab.sqrMagnitude;
            if (abLenSq <= Mathf.Epsilon) return (p - a).sqrMagnitude;

            float t = Vector2.Dot(p - a, ab) / abLenSq;
            t = Mathf.Clamp01(t);
            Vector2 proj = a + t * ab;
            return (p - proj).sqrMagnitude;
        }
    }
}
