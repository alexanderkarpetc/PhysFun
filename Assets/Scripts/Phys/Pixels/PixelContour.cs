using System.Collections.Generic;
using Spawners;
using UnityEngine;

namespace Phys.Pixels
{
    /// <summary>
    /// Exact outlines around the opaque pixels of a sprite.
    ///
    /// Unity's own sprite tracing — what <c>AddComponent&lt;PolygonCollider2D&gt;()</c> gives you —
    /// is tuned for imported art and runs at a fixed tolerance nobody gets to pick. It cuts
    /// corners across whole blocks of solid pixels, and on a nearly-erased sprite it degenerates
    /// into shapes that have nothing to do with what is left. Everything here already keeps a CPU
    /// mirror of its pixels, so outlines come from that and go straight into the collider.
    ///
    /// Every solid pixel contributes the sides that face a hole or the chunk border, wound
    /// counter-clockwise. Stitched end to end those unit edges give one closed loop per outline,
    /// holes and detached islands included. The result is a staircase — exact but dense, so
    /// collinear runs are collapsed on the way out and <see cref="ColliderSimplifier2D"/> is
    /// still what smooths the steps.
    /// </summary>
    public static class PixelContour
    {
        // Edges as an intrusive linked list per lattice point, so a trace allocates nothing
        // beyond the paths it returns.
        private static readonly List<int> EdgeFrom = new();
        private static readonly List<int> EdgeTo = new();
        private static readonly List<int> NextAtPoint = new();
        private static readonly List<bool> Used = new();
        private static readonly Dictionary<int, int> FirstAtPoint = new();

        // Scratch for ApplyCollider; tracing is single-threaded and clears it per call.
        private static readonly List<List<Vector2>> Scratch = new();

        /// <summary>
        /// Trace the pixels and put the result on the object's <see cref="PolygonCollider2D"/>,
        /// simplified and with mass re-derived. The one way a pixel sprite gets a collider —
        /// terrain chunks, split pieces and cracker shards all come through here, so an outline
        /// always means the same thing.
        /// </summary>
        public static void ApplyCollider(GameObject go, Color32[] pixels, int w, int h,
                                         float ppu, Vector2 pivotPx, int simplifyLevel)
        {
            if (!go) return;

            Trace(pixels, w, h, ppu, pivotPx, Scratch);
            var poly = go.GetComponent<PolygonCollider2D>();

            if (Scratch.Count == 0)
            {
                // Nothing solid is left. An outline kept here would go on colliding with things
                // while drawing nothing, and nothing would ever come back to fix it: a retrace
                // is only ever asked for by an edit that removed a pixel, and there are none
                // left to remove.
                if (poly) Object.DestroyImmediate(poly);
                return;
            }

            if (!poly) poly = go.AddComponent<PolygonCollider2D>();

            poly.pathCount = Scratch.Count;
            for (int i = 0; i < Scratch.Count; i++) poly.SetPath(i, Scratch[i]);

            // The trace is a staircase: exact, and far denser than physics needs.
            ColliderSimplifier2D.Simplify(poly, simplifyLevel);
            MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
        }

        /// <summary>
        /// Closed loops around the opaque pixels of <paramref name="pixels"/>, in the local space
        /// of the object that renders them — ready for <see cref="PolygonCollider2D.SetPath"/>.
        /// <paramref name="pivotPx"/> is the sprite pivot in pixels, the same value
        /// <c>Sprite.pivot</c> reports.
        /// </summary>
        public static void Trace(Color32[] pixels, int w, int h, float ppu, Vector2 pivotPx,
                                 List<List<Vector2>> paths)
        {
            paths.Clear();
            if (pixels == null || w <= 0 || h <= 0 || pixels.Length < w * h) return;

            int stride = w + 1;   // lattice points per row
            Build(pixels, w, h, stride);
            Stitch(stride, ppu, pivotPx, paths);
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
        private static void Stitch(int stride, float ppu, Vector2 pivotPx,
                                   List<List<Vector2>> paths)
        {
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

                    AppendPoint(loop, (fx - pivotPx.x) / ppu, (fy - pivotPx.y) / ppu);

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
