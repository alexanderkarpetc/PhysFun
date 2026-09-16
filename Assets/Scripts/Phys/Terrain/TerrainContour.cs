using System.Collections.Generic;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// Exact outlines around the solid pixels of a terrain chunk.
    ///
    /// Unity's own sprite tracing — what <c>AddComponent&lt;PolygonCollider2D&gt;()</c> gives you —
    /// is tuned for imported art and runs at a fixed tolerance nobody gets to pick. On a 64-cell
    /// chunk it happily cuts a corner across several cells of solid ground, which reads as a
    /// collider that has nothing to do with the terrain under it. A chunk already knows exactly
    /// which cells are solid, so it traces its own and hands the paths straight to the collider.
    ///
    /// Every solid pixel contributes the sides that face a hole or the chunk border, wound
    /// counter-clockwise. Stitched end to end those unit edges give one closed loop per outline,
    /// holes and detached islands included. The result is a staircase — exact but dense, so
    /// collinear runs are collapsed on the way out and <see cref="ColliderSimplifier2D"/> is
    /// still what smooths the steps.
    /// </summary>
    public static class TerrainContour
    {
        // Edges as an intrusive linked list per lattice point, so a trace allocates nothing
        // beyond the paths it returns.
        private static readonly List<int> EdgeFrom = new();
        private static readonly List<int> EdgeTo = new();
        private static readonly List<int> NextAtPoint = new();
        private static readonly List<bool> Used = new();
        private static readonly Dictionary<int, int> FirstAtPoint = new();

        /// <summary>
        /// Closed loops around the opaque pixels of <paramref name="pixels"/>, in the local space
        /// of a sprite of that size with a centred pivot — ready for
        /// <see cref="PolygonCollider2D.SetPath"/>.
        /// </summary>
        public static void Trace(Color32[] pixels, int w, int h, float ppu,
                                 List<List<Vector2>> paths)
        {
            paths.Clear();
            if (pixels == null || w <= 0 || h <= 0 || pixels.Length < w * h) return;

            int stride = w + 1;   // lattice points per row
            Build(pixels, w, h, stride);
            Stitch(w, h, stride, ppu, paths);
        }

        /// <summary>Collect the solid/empty boundary as directed unit edges.</summary>
        private static void Build(Color32[] pixels, int w, int h, int stride)
        {
            EdgeFrom.Clear();
            EdgeTo.Clear();
            NextAtPoint.Clear();
            Used.Clear();
            FirstAtPoint.Clear();

            for (int y = 0; y < h; y++)
            {
                int row = y * w;
                for (int x = 0; x < w; x++)
                {
                    if (pixels[row + x].a == 0) continue;

                    // Counter-clockwise around the solid cell, so the solid side is on the left.
                    if (y == 0 || pixels[row - w + x].a == 0)
                        Add(Pt(x, y, stride), Pt(x + 1, y, stride));
                    if (x == w - 1 || pixels[row + x + 1].a == 0)
                        Add(Pt(x + 1, y, stride), Pt(x + 1, y + 1, stride));
                    if (y == h - 1 || pixels[row + w + x].a == 0)
                        Add(Pt(x + 1, y + 1, stride), Pt(x, y + 1, stride));
                    if (x == 0 || pixels[row + x - 1].a == 0)
                        Add(Pt(x, y + 1, stride), Pt(x, y, stride));
                }
            }
        }

        private static int Pt(int x, int y, int stride) => y * stride + x;

        private static void Add(int from, int to)
        {
            int e = EdgeFrom.Count;
            EdgeFrom.Add(from);
            EdgeTo.Add(to);
            Used.Add(false);
            NextAtPoint.Add(FirstAtPoint.TryGetValue(from, out int head) ? head : -1);
            FirstAtPoint[from] = e;
        }

        /// <summary>Walk the edges into closed loops and convert them to local-space points.</summary>
        private static void Stitch(int w, int h, int stride, float ppu,
                                   List<List<Vector2>> paths)
        {
            float halfW = w * 0.5f;
            float halfH = h * 0.5f;

            for (int seed = 0; seed < EdgeFrom.Count; seed++)
            {
                if (Used[seed]) continue;

                var loop = new List<Vector2>();
                int start = EdgeFrom[seed];
                int edge = seed;

                while (edge >= 0 && !Used[edge])
                {
                    Used[edge] = true;

                    int from = EdgeFrom[edge];
                    int to = EdgeTo[edge];
                    int fx = from % stride, fy = from / stride;

                    AppendPoint(loop, (fx - halfW) / ppu, (fy - halfH) / ppu);

                    if (to == start) break;
                    edge = PickNext(to, to % stride - fx, to / stride - fy, stride);
                }

                // The first and last points are collinear neighbours of each other across the
                // closure, so trim there too before deciding the loop is worth keeping.
                TrimClosure(loop);
                if (loop.Count >= 3) paths.Add(loop);
            }
        }

        /// <summary>
        /// The next edge out of a point, preferring the sharpest clockwise turn. Only matters
        /// where two solid regions meet at a single corner — either choice closes, this one
        /// keeps the loop hugging one region instead of crossing over.
        /// </summary>
        private static int PickNext(int at, int inDx, int inDy, int stride)
        {
            int best = -1, bestRank = int.MaxValue;

            for (int e = FirstAtPoint.TryGetValue(at, out int head) ? head : -1;
                 e >= 0;
                 e = NextAtPoint[e])
            {
                if (Used[e]) continue;

                int to = EdgeTo[e];
                int dx = to % stride - at % stride;
                int dy = to / stride - at / stride;

                int rank;
                if (dx == inDy && dy == -inDx) rank = 0;        // right
                else if (dx == inDx && dy == inDy) rank = 1;    // straight
                else if (dx == -inDy && dy == inDx) rank = 2;   // left
                else rank = 3;                                  // back the way we came

                if (rank >= bestRank) continue;
                bestRank = rank;
                best = e;
            }

            return best;
        }

        /// <summary>Add a point, dropping the previous one when it sits on the same straight run.
        /// Flat ground is thousands of collinear steps, and none of them carry information.</summary>
        private static void AppendPoint(List<Vector2> loop, float x, float y)
        {
            var p = new Vector2(x, y);
            int n = loop.Count;
            if (n >= 2 && Collinear(loop[n - 2], loop[n - 1], p)) loop[n - 1] = p;
            else loop.Add(p);
        }

        private static void TrimClosure(List<Vector2> loop)
        {
            while (loop.Count >= 3 &&
                   Collinear(loop[loop.Count - 2], loop[loop.Count - 1], loop[0]))
                loop.RemoveAt(loop.Count - 1);

            while (loop.Count >= 3 &&
                   Collinear(loop[loop.Count - 1], loop[0], loop[1]))
                loop.RemoveAt(0);
        }

        private static bool Collinear(Vector2 a, Vector2 b, Vector2 c)
        {
            // Points come off a lattice, so this is exact up to float rounding of the divide.
            float cross = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
            return Mathf.Abs(cross) < 1e-9f;
        }
    }
}
