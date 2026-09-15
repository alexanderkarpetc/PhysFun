using System.Collections.Generic;
using UnityEngine;

namespace Binny
{
    /// <summary>
    /// A* for a flying machine, over a grid that is never built. Cells are probed with an overlap
    /// test only when the search actually reaches them, so a trip across a room costs a few hundred
    /// queries and nothing is kept between flights. That is what lets it work in a world where the
    /// ground is destructible and half the obstacles are crates someone threw a second ago: there
    /// is no map to go stale, only what the physics says right now.
    ///
    /// The grid is anchored on wherever he is starting from, so there is no global alignment to
    /// maintain and the cell he sets off from is always (0,0).
    ///
    /// A cell is passable if his whole hull fits in it, so a gap he cannot get through is simply
    /// not a route, and it never tries to squeeze him into one.
    ///
    /// Unreachable goals do not fail: the search hands back the closest cell it could stand in,
    /// which is how Binny comes to rest against the wall that is in the way rather than either
    /// giving up where he stands or shoving through it. The caller is told which of the two it
    /// got — see the return of <see cref="TryFind"/>.
    /// </summary>
    public sealed class BinnyPathfinder
    {
        private const float Diagonal = 1.41421356f;

        private static readonly Vector2Int[] Steps =
        {
            new(1, 0), new(-1, 0), new(0, 1), new(0, -1),
            new(1, 1), new(1, -1), new(-1, 1), new(-1, -1),
        };

        private readonly Dictionary<Vector2Int, bool> _passable = new();
        private readonly Dictionary<Vector2Int, Vector2Int> _cameFrom = new();
        private readonly Dictionary<Vector2Int, float> _cost = new();
        private readonly HashSet<Vector2Int> _closed = new();
        private readonly List<(float Priority, Vector2Int Cell)> _open = new();

        private readonly List<Collider2D> _overlaps = new();
        private readonly List<RaycastHit2D> _casts = new();
        private readonly List<Vector2> _smoothed = new();

        private readonly float _cell;
        private readonly Vector2 _clearance;
        private readonly int _budget;
        private readonly int _rangeInCells;
        private readonly Transform _owner;
        private readonly ContactFilter2D _filter;

        private Vector2 _origin;

        /// <param name="cellSize">Grid step. Finer threads tighter gaps and costs more probes.</param>
        /// <param name="clearance">The box that has to be empty for him to sit in a cell — his hull plus a skin.</param>
        /// <param name="obstacles">Layers he cannot fly through.</param>
        /// <param name="budget">Cells the search may open before it settles for the best it has.</param>
        /// <param name="range">How far from the start it will look, in world units.</param>
        /// <param name="owner">His own transform, so his own colliders do not read as a wall.</param>
        public BinnyPathfinder(float cellSize, Vector2 clearance, LayerMask obstacles, int budget, float range,
            Transform owner)
        {
            _cell = Mathf.Max(0.05f, cellSize);
            _clearance = clearance;
            _budget = Mathf.Max(16, budget);
            _rangeInCells = Mathf.Max(1, Mathf.RoundToInt(range / _cell));
            _owner = owner;

            _filter = new ContactFilter2D
            {
                useLayerMask = true,
                layerMask = obstacles,
                useTriggers = false,
            };
        }

        /// <summary>
        /// Fills <paramref name="path"/> with the way from <paramref name="from"/> onwards, first
        /// point being where he already is. Returns true if it ends on the goal, false if it is the
        /// best it could get to — in which case the last point is where he should come to a stop.
        /// </summary>
        public bool TryFind(Vector2 from, Vector2 to, List<Vector2> path)
        {
            path.Clear();

            _origin = from;
            _passable.Clear();
            _cameFrom.Clear();
            _cost.Clear();
            _closed.Clear();
            _open.Clear();

            var start = Vector2Int.zero;
            var goal = CellOf(to);

            // He may well be sitting in something already — resting on a floor, a crate settled
            // against him — so the cell he is in is passable by definition. Anything else and he
            // could never set off.
            _passable[start] = true;
            _cost[start] = 0f;
            Push(start, Heuristic(start, goal));

            var best = start;
            float bestScore = Heuristic(start, goal);
            bool reached = false;
            int opened = 0;

            while (_open.Count > 0 && opened < _budget)
            {
                var current = Pop();
                if (!_closed.Add(current)) continue;
                opened++;

                if (current == goal)
                {
                    best = current;
                    reached = true;
                    break;
                }

                float score = Heuristic(current, goal);
                if (score < bestScore)
                {
                    bestScore = score;
                    best = current;
                }

                Expand(current, goal);
            }

            Rebuild(best, path);

            // Finish on the spot that was asked for rather than on the middle of its cell, so he
            // parks where he was sent and not up to half a cell off it.
            if (reached) path[path.Count - 1] = to;

            Smooth(path);
            return reached;
        }

        private void Expand(Vector2Int current, Vector2Int goal)
        {
            float here = _cost[current];

            foreach (var step in Steps)
            {
                var next = current + step;
                if (_closed.Contains(next)) continue;
                if (next.sqrMagnitude > _rangeInCells * _rangeInCells) continue;
                if (!IsPassable(next)) continue;

                bool diagonal = step.x != 0 && step.y != 0;

                // No cutting corners: a diagonal is only open if both of its sides are, otherwise
                // he clips the corner of whatever he is going round.
                if (diagonal &&
                    (!IsPassable(new Vector2Int(next.x, current.y)) ||
                     !IsPassable(new Vector2Int(current.x, next.y)))) continue;

                float cost = here + (diagonal ? Diagonal : 1f);
                if (_cost.TryGetValue(next, out float known) && known <= cost) continue;

                _cost[next] = cost;
                _cameFrom[next] = current;
                Push(next, cost + Heuristic(next, goal));
            }
        }

        /// <summary>Is there room for the whole of him, centred on this cell?</summary>
        private bool IsPassable(Vector2Int cell)
        {
            if (_passable.TryGetValue(cell, out bool known)) return known;

            _overlaps.Clear();
            Physics2D.OverlapBox(WorldOf(cell), _clearance, 0f, _filter, _overlaps);

            bool passable = !AnythingButHim(_overlaps);
            _passable[cell] = passable;
            return passable;
        }

        /// <summary>Could he fly this leg in a straight line without touching anything?</summary>
        private bool IsOpen(Vector2 from, Vector2 to)
        {
            var delta = to - from;
            float distance = delta.magnitude;
            if (distance < 0.0001f) return true;

            _casts.Clear();
            Physics2D.BoxCast(from, _clearance, 0f, delta / distance, _filter, _casts, distance);

            for (int i = 0; i < _casts.Count; i++)
            {
                var hit = _casts[i].collider;
                if (hit && !hit.transform.IsChildOf(_owner)) return false;
            }

            return true;
        }

        private bool AnythingButHim(List<Collider2D> hits)
        {
            for (int i = 0; i < hits.Count; i++)
            {
                var hit = hits[i];
                if (hit && !hit.transform.IsChildOf(_owner)) return true;
            }

            return false;
        }

        private void Rebuild(Vector2Int end, List<Vector2> path)
        {
            var cursor = end;
            path.Add(WorldOf(cursor));

            while (_cameFrom.TryGetValue(cursor, out var previous))
            {
                cursor = previous;
                path.Add(WorldOf(cursor));
            }

            path.Reverse();
            path[0] = _origin;
        }

        /// <summary>
        /// The grid route is a staircase. This is the same route with every corner cut that can be
        /// cut: from each point he keeps, run on to the furthest one he can still reach in a
        /// straight line and throw away everything between. What is left is a handful of long legs,
        /// which is what makes the flight read as flying rather than as following a grid.
        /// </summary>
        private void Smooth(List<Vector2> path)
        {
            if (path.Count < 3) return;

            _smoothed.Clear();
            _smoothed.Add(path[0]);

            int anchor = 0;
            while (anchor < path.Count - 1)
            {
                int furthest = anchor + 1;
                while (furthest + 1 < path.Count && IsOpen(path[anchor], path[furthest + 1])) furthest++;

                _smoothed.Add(path[furthest]);
                anchor = furthest;
            }

            path.Clear();
            path.AddRange(_smoothed);
        }

        private Vector2Int CellOf(Vector2 world)
        {
            var offset = (world - _origin) / _cell;
            return new Vector2Int(Mathf.RoundToInt(offset.x), Mathf.RoundToInt(offset.y));
        }

        private Vector2 WorldOf(Vector2Int cell) => _origin + new Vector2(cell.x, cell.y) * _cell;

        /// <summary>Octile distance: the true cost of an empty grid, so the search never wanders.</summary>
        private static float Heuristic(Vector2Int from, Vector2Int to)
        {
            int dx = Mathf.Abs(to.x - from.x);
            int dy = Mathf.Abs(to.y - from.y);

            return dx + dy + (Diagonal - 2f) * Mathf.Min(dx, dy);
        }

        // ------------------------------------------------------------------ open set

        private void Push(Vector2Int cell, float priority)
        {
            _open.Add((priority, cell));

            int child = _open.Count - 1;
            while (child > 0)
            {
                int parent = (child - 1) / 2;
                if (_open[parent].Priority <= _open[child].Priority) break;

                (_open[parent], _open[child]) = (_open[child], _open[parent]);
                child = parent;
            }
        }

        private Vector2Int Pop()
        {
            var top = _open[0];
            int last = _open.Count - 1;

            _open[0] = _open[last];
            _open.RemoveAt(last);

            int parent = 0;
            while (true)
            {
                int left = parent * 2 + 1;
                int right = left + 1;
                int smallest = parent;

                if (left < _open.Count && _open[left].Priority < _open[smallest].Priority) smallest = left;
                if (right < _open.Count && _open[right].Priority < _open[smallest].Priority) smallest = right;
                if (smallest == parent) break;

                (_open[parent], _open[smallest]) = (_open[smallest], _open[parent]);
                parent = smallest;
            }

            return top.Cell;
        }
    }
}
