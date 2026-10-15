using System.Collections.Generic;
using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// Where the rooms of a floor go and how they are joined - geometry only, no terrain and
    /// no objects, so it can be reasoned about (and drawn as gizmos) on its own.
    ///
    /// Rooms sit on a grid of cells a little bigger than the biggest room, grown as a tree
    /// out of the start room: each new room takes a free cell next to one already placed,
    /// preferring sides where both rooms have sockets. A few extra links between rooms that
    /// ended up side by side turn the tree into something with loops. Each link joins the
    /// pair of sockets that face each other best, and a corridor is routed between their
    /// mouths through the fill, around every room, by A* on a half-unit grid that charges
    /// for turns - so corridors come out as runs, not staircases.
    ///
    /// They are not the shortest runs, though. The grid's step cost is a noise field
    /// (<see cref="Settings.Wander"/>), and each corridor is sent through a few detour
    /// points scattered round the line between its ends, up and down as much as sideways
    /// (<see cref="Settings.Detours"/>) - so it winds, climbs and drops on its way. Ground a
    /// corridor has taken costs the next ones more, so two of them do not run side by side.
    /// </summary>
    public sealed class FloorLayout
    {
        public struct SocketShape
        {
            public SocketSide Side;
            public Vector2 Point;       // on the template edge, relative to the room's root
            public float Size;
            public float Depth;
        }

        public sealed class RoomShape
        {
            public Rect Local;          // template rectangle, relative to the room's root
            public SocketShape[] Sockets;
        }

        public struct Link
        {
            public int A, SocketA, B, SocketB;
        }

        public struct Settings
        {
            public float Gap, Jitter, Margin, CellSnap, CorridorSize;
            public int ExtraLinks;
            /// <summary>How much the noise field adds to a step: 0 = shortest way.</summary>
            public float Wander;
            /// <summary>Extra cost of a turn, in steps.</summary>
            public float TurnCost;
            /// <summary>Detour points per corridor.</summary>
            public int Detours;
            /// <summary>How far, world units, a detour point may stray off the straight line.</summary>
            public float DetourReach;
        }

        /// <summary>Where each room's root goes, in floor space.</summary>
        public Vector2[] Positions;
        /// <summary>Each room's template rectangle, in floor space.</summary>
        public Rect[] Rects;
        public Rect Bounds;
        public readonly List<Link> Links = new();
        /// <summary>One polyline per link, from socket A's mouth to socket B's. Points are the
        /// corridor's floor line where it runs level and its centre line where it climbs.</summary>
        public readonly List<List<Vector2>> Corridors = new();
        public readonly HashSet<(int room, int socket)> Used = new();

        private const float Step = 0.5f;        // routing grid
        private const float Clearance = 0.75f;  // corridors keep this far off other rooms
        private const float Crowd = 3f;         // step cost added round a corridor already routed

        private static readonly Vector2Int[] Dirs =
            { Vector2Int.right, Vector2Int.left, Vector2Int.up, Vector2Int.down };

        // ─────────────────────────────────────────────────────────────────────────
        // Placement
        // ─────────────────────────────────────────────────────────────────────────

        public static FloorLayout Plan(IReadOnlyList<RoomShape> rooms, Settings s, System.Random rng)
        {
            var plan = new FloorLayout();
            int n = rooms.Count;
            plan.Positions = new Vector2[n];
            plan.Rects = new Rect[n];
            if (n == 0) return plan;

            float maxW = 0f, maxH = 0f;
            foreach (var r in rooms)
            {
                maxW = Mathf.Max(maxW, r.Local.width);
                maxH = Mathf.Max(maxH, r.Local.height);
            }
            var cellSize = new Vector2(maxW + s.Gap, maxH + s.Gap);

            // Grow the tree on the grid.
            var at = new Vector2Int[n];
            var taken = new Dictionary<Vector2Int, int> { [Vector2Int.zero] = 0 };
            var tree = new List<(int a, int b)>();
            for (int k = 1; k < n; k++)
            {
                var options = new List<(int from, Vector2Int dir, float weight)>();
                float total = 0f;
                for (int i = 0; i < k; i++)
                foreach (var d in Dirs)
                {
                    if (taken.ContainsKey(at[i] + d)) continue;
                    float w = d.y == 0 ? 2f : 1f;
                    w *= HasSide(rooms[i], SideOf(d)) ? 1.5f : 0.3f;
                    w *= HasSide(rooms[k], SideOf(-d)) ? 1.5f : 0.3f;
                    options.Add((i, d, w));
                    total += w;
                }
                float pick = (float)rng.NextDouble() * total;
                var chosen = options[options.Count - 1];
                foreach (var o in options)
                {
                    pick -= o.weight;
                    if (pick <= 0f) { chosen = o; break; }
                }
                at[k] = at[chosen.from] + chosen.dir;
                taken[at[k]] = k;
                tree.Add((chosen.from, k));
            }

            // Each room somewhere inside its cell.
            for (int i = 0; i < n; i++)
            {
                var r = rooms[i].Local;
                var slack = new Vector2(cellSize.x - s.Gap - r.width, cellSize.y - s.Gap - r.height);
                var min = new Vector2(at[i].x * cellSize.x, at[i].y * cellSize.y) + Vector2.one * (s.Gap * 0.5f)
                          + new Vector2(slack.x * (0.5f + s.Jitter * ((float)rng.NextDouble() - 0.5f)),
                                        slack.y * (0.5f + s.Jitter * ((float)rng.NextDouble() - 0.5f)));
                min = Snap(min, s.CellSnap);
                plan.Rects[i] = new Rect(min, r.size);
                plan.Positions[i] = min - r.min;
            }

            // Links: the tree, then a few neighbours it did not join.
            var pairs = new List<(int a, int b)>(tree);
            var spare = new List<(int a, int b)>();
            for (int i = 0; i < n; i++)
            foreach (var d in Dirs)
            {
                if (!taken.TryGetValue(at[i] + d, out int j) || j <= i) continue;
                if (tree.Contains((i, j)) || tree.Contains((j, i))) continue;
                spare.Add((i, j));
            }
            Shuffle(spare, rng);
            for (int i = 0; i < Mathf.Min(s.ExtraLinks, spare.Count); i++) pairs.Add(spare[i]);

            float minX = float.MaxValue, minY = float.MaxValue, maxX = float.MinValue, maxY = float.MinValue;
            foreach (var r in plan.Rects)
            {
                minX = Mathf.Min(minX, r.xMin); minY = Mathf.Min(minY, r.yMin);
                maxX = Mathf.Max(maxX, r.xMax); maxY = Mathf.Max(maxY, r.yMax);
            }
            var bmin = Snap(new Vector2(minX - s.Margin, minY - s.Margin), s.CellSnap);
            plan.Bounds = new Rect(bmin, new Vector2(maxX + s.Margin, maxY + s.Margin) - bmin);

            var router = new Router(plan.Bounds, plan.Rects, s, rng);
            foreach (var (a, b) in pairs) plan.Join(rooms, a, b, at[b] - at[a], router);
            return plan;
        }

        private void Join(IReadOnlyList<RoomShape> rooms, int a, int b, Vector2Int dir, Router router)
        {
            var sideA = SideOf(dir);
            var sideB = SideOf(-dir);
            float best = float.MaxValue;
            int bestA = -1, bestB = -1;
            for (int i = 0; i < rooms[a].Sockets.Length; i++)
            for (int j = 0; j < rooms[b].Sockets.Length; j++)
            {
                var sa = rooms[a].Sockets[i];
                var sb = rooms[b].Sockets[j];
                if (sa.Side == Opposite(sideA) || sb.Side == Opposite(sideB)) continue;
                float score = Vector2.Distance(Mouth(a, sa), Mouth(b, sb));
                if (sa.Side != sideA) score += 8f;
                if (sb.Side != sideB) score += 8f;
                if (Used.Contains((a, i))) score += 20f;
                if (Used.Contains((b, j))) score += 20f;
                if (score < best) { best = score; bestA = i; bestB = j; }
            }
            if (bestA < 0)
            {
                Debug.LogWarning($"FloorLayout: rooms {a} and {b} have no sockets that can face each other.");
                return;
            }

            Links.Add(new Link { A = a, SocketA = bestA, B = b, SocketB = bestB });
            Used.Add((a, bestA));
            Used.Add((b, bestB));
            Corridors.Add(router.Route(Mouth(a, rooms[a].Sockets[bestA]), rooms[a].Sockets[bestA].Side,
                                       Mouth(b, rooms[b].Sockets[bestB]), rooms[b].Sockets[bestB].Side));
        }

        /// <summary>A socket's point on the template edge, in floor space.</summary>
        public Vector2 Mouth(int room, SocketShape socket) => Positions[room] + socket.Point;

        // ─────────────────────────────────────────────────────────────────────────
        // Routing
        // ─────────────────────────────────────────────────────────────────────────

        private sealed class Router
        {
            private readonly Rect _bounds;
            private readonly int _nx, _ny;
            private readonly bool[] _blocked;
            private readonly float[] _cost;             // what a step onto the cell costs
            private readonly Settings _s;
            private readonly System.Random _rng;
            private readonly int _wear;                 // cells either side a routed corridor wears

            // A* state, kept between searches: a state is fresh unless it carries this search's stamp
            private readonly float[] _g;
            private readonly int[] _prev, _stamp;
            private readonly bool[] _closed;
            private int _search;

            public Router(Rect bounds, Rect[] rooms, Settings s, System.Random rng)
            {
                float bore = s.CorridorSize;
                float half = bore * 0.5f;
                _bounds = bounds;
                _s = s;
                _rng = rng;
                _wear = Mathf.CeilToInt(bore / Step);
                _nx = Mathf.Max(1, Mathf.CeilToInt(bounds.width / Step));
                _ny = Mathf.Max(1, Mathf.CeilToInt(bounds.height / Step));
                _blocked = new bool[_nx * _ny];
                _cost = new float[_nx * _ny];
                float ox = (float)rng.NextDouble() * 500f, oy = (float)rng.NextDouble() * 500f;
                for (int y = 0; y < _ny; y++)
                for (int x = 0; x < _nx; x++)
                {
                    var p = Center(x, y);
                    // A corridor is carved as a box of `bore` rising from each point, so a point
                    // is blocked when that box would come within Clearance of a room.
                    foreach (var r in rooms)
                        if (p.x + half > r.xMin - Clearance && p.x - half < r.xMax + Clearance &&
                            p.y + bore > r.yMin - Clearance && p.y < r.yMax + Clearance)
                        {
                            _blocked[y * _nx + x] = true;
                            break;
                        }
                    if (x == 0 || y == 0 || x == _nx - 1 || y == _ny - 1) _blocked[y * _nx + x] = true;

                    // Two octaves, squared, so the field has valleys a corridor follows rather
                    // than an even fuzz it ignores.
                    float n = 0.65f * Mathf.PerlinNoise(ox + p.x * 0.22f, oy + p.y * 0.22f)
                            + 0.35f * Mathf.PerlinNoise(oy + p.x * 0.55f, ox + p.y * 0.55f);
                    _cost[y * _nx + x] = 1f + s.Wander * n * n;
                }

                int states = _nx * _ny * 4;
                _g = new float[states];
                _prev = new int[states];
                _stamp = new int[states];
                _closed = new bool[states];
            }

            private Vector2 Center(int x, int y) =>
                new(_bounds.xMin + (x + 0.5f) * Step, _bounds.yMin + (y + 0.5f) * Step);

            private Vector2Int Cell(Vector2 p) =>
                new(Mathf.Clamp(Mathf.FloorToInt((p.x - _bounds.xMin) / Step), 0, _nx - 1),
                    Mathf.Clamp(Mathf.FloorToInt((p.y - _bounds.yMin) / Step), 0, _ny - 1));

            private bool Free(Vector2Int c) =>
                c.x >= 0 && c.y >= 0 && c.x < _nx && c.y < _ny && !_blocked[c.y * _nx + c.x];

            /// <summary>The first free routing cell straight out of a socket's mouth.</summary>
            private Vector2Int Exit(Vector2 mouth, SocketSide side)
            {
                var o = RoomSocket.Outward(side);
                for (float t = Step; t < 40f; t += Step)
                {
                    var c = Cell(mouth + o * t);
                    if (!_blocked[c.y * _nx + c.x]) return c;
                }
                return Cell(mouth + o * Step);
            }

            public List<Vector2> Route(Vector2 mouthA, SocketSide sideA, Vector2 mouthB, SocketSide sideB)
            {
                var ea = Exit(mouthA, sideA);
                var eb = Exit(mouthB, sideB);

                // ea -> detours -> eb, leg by leg; a detour no leg can reach is dropped. Each
                // leg wears its ground as soon as it is laid, so the next one keeps off it
                // rather than doubling back along it.
                var cells = new List<Vector2Int> { ea };
                var from = ea;
                foreach (var stop in Detours(ea, eb))
                {
                    var leg = AStar(from, stop);
                    if (leg == null) continue;
                    Append(cells, leg);
                    Wear(leg);
                    from = stop;
                }
                var last = AStar(from, eb) ?? new List<Vector2Int> { from, new(eb.x, from.y), eb };
                Append(cells, last);
                Wear(last);

                var pts = new List<Vector2> { mouthA };
                AddLeg(pts, mouthA, Center(ea.x, ea.y), sideA);
                var corners = Corners(cells);
                for (int i = 1; i < corners.Count; i++) pts.Add(Center(corners[i].x, corners[i].y));
                AddLeg(pts, Center(eb.x, eb.y), mouthB, sideB);
                return pts;
            }

            /// <summary>Free cells along the way from a to b, each pushed off the straight line
            /// - further up and down than sideways, so corridors climb.</summary>
            private List<Vector2Int> Detours(Vector2Int a, Vector2Int b)
            {
                var stops = new List<Vector2Int>();
                float reach = _s.DetourReach / Step;
                for (int k = 1; k <= _s.Detours; k++)
                {
                    float t = k / (_s.Detours + 1f);
                    var aim = Vector2.Lerp(a, b, t) + new Vector2(
                        ((float)_rng.NextDouble() * 2f - 1f) * reach * 0.6f,
                        ((float)_rng.NextDouble() * 2f - 1f) * reach);
                    var c = new Vector2Int(Mathf.RoundToInt(aim.x), Mathf.RoundToInt(aim.y));
                    if (Nearest(ref c)) stops.Add(c);
                }
                return stops;
            }

            /// <summary>Move c onto the nearest free cell a few cells round it, if there is one.</summary>
            private bool Nearest(ref Vector2Int c)
            {
                for (int r = 0; r <= 8; r++)
                for (int dy = -r; dy <= r; dy++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)) != r) continue;
                    var n = new Vector2Int(c.x + dx, c.y + dy);
                    if (Free(n)) { c = n; return true; }
                }
                return false;
            }

            private static void Append(List<Vector2Int> cells, List<Vector2Int> leg)
            {
                foreach (var c in leg)
                    if (cells.Count == 0 || cells[cells.Count - 1] != c) cells.Add(c);
            }

            /// <summary>A routed corridor makes its ground, and the ground round it, dearer.</summary>
            private void Wear(List<Vector2Int> path)
            {
                float cap = 1f + _s.Wander + Crowd * 2f;
                foreach (var p in path)
                    for (int dy = -_wear; dy <= _wear; dy++)
                    for (int dx = -_wear; dx <= _wear; dx++)
                    {
                        int x = p.x + dx, y = p.y + dy;
                        if (x < 0 || y < 0 || x >= _nx || y >= _ny) continue;
                        int i = y * _nx + x;
                        _cost[i] = Mathf.Min(_cost[i] + Crowd, cap);
                    }
            }

            /// <summary>From a mouth to its exit cell (or back): straight out first, then the
            /// short sidestep onto the routing grid.</summary>
            private static void AddLeg(List<Vector2> pts, Vector2 from, Vector2 to, SocketSide side)
            {
                bool level = side == SocketSide.Left || side == SocketSide.Right;
                pts.Add(level ? new Vector2(to.x, from.y) : new Vector2(from.x, to.y));
                pts.Add(to);
            }

            private static List<Vector2Int> Corners(List<Vector2Int> path)
            {
                var c = new List<Vector2Int> { path[0] };
                for (int i = 1; i < path.Count - 1; i++)
                    if (path[i] - path[i - 1] != path[i + 1] - path[i]) c.Add(path[i]);
                if (path.Count > 1) c.Add(path[path.Count - 1]);
                return c;
            }

            private List<Vector2Int> AStar(Vector2Int from, Vector2Int to)
            {
                if (from == to) return new List<Vector2Int> { from };
                _search++;
                var open = new Heap();
                int origin = from.y * _nx + from.x;
                for (int d = 0; d < 4; d++)
                {
                    Touch(origin * 4 + d);
                    _g[origin * 4 + d] = 0f;
                    open.Push(origin * 4 + d, H(from, to));
                }

                int goal = to.y * _nx + to.x;
                while (open.Count > 0)
                {
                    int s = open.Pop();
                    if (_closed[s]) continue;
                    _closed[s] = true;
                    int c = s / 4, dir = s % 4;
                    if (c == goal) return Unwind(s);
                    int cx = c % _nx, cy = c / _nx;
                    for (int nd = 0; nd < 4; nd++)
                    {
                        int x = cx + Dirs[nd].x, y = cy + Dirs[nd].y;
                        if (x < 0 || y < 0 || x >= _nx || y >= _ny) continue;
                        int nc = y * _nx + x;
                        if (_blocked[nc] && nc != goal) continue;
                        float cost = _g[s] + _cost[nc] + (nd == dir || c == origin ? 0f : _s.TurnCost);
                        int ns = nc * 4 + nd;
                        Touch(ns);
                        if (cost >= _g[ns]) continue;
                        _g[ns] = cost;
                        _prev[ns] = s;
                        open.Push(ns, cost + H(new Vector2Int(x, y), to));
                    }
                }
                return null;
            }

            /// <summary>Reset a state the first time this search meets it.</summary>
            private void Touch(int s)
            {
                if (_stamp[s] == _search) return;
                _stamp[s] = _search;
                _g[s] = float.MaxValue;
                _prev[s] = -1;
                _closed[s] = false;
            }

            private List<Vector2Int> Unwind(int s)
            {
                var path = new List<Vector2Int>();
                for (; s >= 0; s = _prev[s])
                {
                    int c = s / 4;
                    var p = new Vector2Int(c % _nx, c / _nx);
                    if (path.Count == 0 || path[path.Count - 1] != p) path.Add(p);
                }
                path.Reverse();
                return path;
            }

            private static float H(Vector2Int a, Vector2Int b) => Mathf.Abs(a.x - b.x) + Mathf.Abs(a.y - b.y);
        }

        /// <summary>Binary min-heap of (state, priority), just enough for A*.</summary>
        private sealed class Heap
        {
            private readonly List<(int item, float pri)> _a = new();
            public int Count => _a.Count;

            public void Push(int item, float pri)
            {
                _a.Add((item, pri));
                int i = _a.Count - 1;
                while (i > 0)
                {
                    int p = (i - 1) / 2;
                    if (_a[p].pri <= _a[i].pri) break;
                    (_a[p], _a[i]) = (_a[i], _a[p]);
                    i = p;
                }
            }

            public int Pop()
            {
                int top = _a[0].item;
                _a[0] = _a[_a.Count - 1];
                _a.RemoveAt(_a.Count - 1);
                int i = 0;
                while (true)
                {
                    int l = i * 2 + 1, r = l + 1, m = i;
                    if (l < _a.Count && _a[l].pri < _a[m].pri) m = l;
                    if (r < _a.Count && _a[r].pri < _a[m].pri) m = r;
                    if (m == i) break;
                    (_a[m], _a[i]) = (_a[i], _a[m]);
                    i = m;
                }
                return top;
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Helpers
        // ─────────────────────────────────────────────────────────────────────────

        private static bool HasSide(RoomShape r, SocketSide side)
        {
            foreach (var s in r.Sockets)
                if (s.Side == side) return true;
            return false;
        }

        private static SocketSide SideOf(Vector2Int d) =>
            d.x > 0 ? SocketSide.Right : d.x < 0 ? SocketSide.Left : d.y > 0 ? SocketSide.Top : SocketSide.Bottom;

        private static SocketSide Opposite(SocketSide s) => s switch
        {
            SocketSide.Left => SocketSide.Right,
            SocketSide.Right => SocketSide.Left,
            SocketSide.Top => SocketSide.Bottom,
            _ => SocketSide.Top,
        };

        private static Vector2 Snap(Vector2 v, float cell) =>
            cell <= 0f ? v : new Vector2(Mathf.Round(v.x / cell) * cell, Mathf.Round(v.y / cell) * cell);

        private static void Shuffle<T>(IList<T> list, System.Random rng)
        {
            for (int i = list.Count - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                (list[i], list[j]) = (list[j], list[i]);
            }
        }
    }
}
