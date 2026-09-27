using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;

namespace Phys.Electricity
{
    /// <summary>A bolt between two fixed points: a strike, a jump across a join, a tap into a victim.</summary>
    public readonly struct Hop
    {
        public readonly Vector2 From;
        public readonly Vector2 To;

        /// <summary>How many conductors down the chain it happens — it fires when that one goes live.</summary>
        public readonly int Depth;

        public Hop(Vector2 from, Vector2 to, int depth)
        {
            From = from;
            To = to;
            Depth = depth;
        }
    }

    /// <summary>
    /// One discharge as the world sees it for the next half second: every conductor it got into,
    /// how far down the chain each one is, and the joins and victims the charge jumps across.
    /// Settled once by <see cref="ElectricitySystem.Strike"/>; <see cref="ArcField"/> only draws it.
    /// </summary>
    public sealed class Charge
    {
        public ElectricityProfile Profile;
        public GameObject Source;
        public Vector2 Origin;

        public readonly List<Collider2D> Conductors = new();
        public readonly List<int> Depth = new();

        /// <summary>Strike bolts (depth 0, from the origin) and jumps from one conductor to the next.</summary>
        public readonly List<Hop> Hops = new();

        /// <summary>From an energised body into whoever was touching it.</summary>
        public readonly List<Hop> Taps = new();

        internal float Age;
        internal float Life;
    }

    /// <summary>
    /// The visible charge: a sparse grid of arc cells redrawn from scratch a couple of times a
    /// frame-second, so the bolts flicker and jump the way a real discharge does instead of
    /// crawling.
    ///
    /// Each redraw, for every conductor that is live:
    /// <list type="bullet">
    /// <item>its whole outline shimmers — dim, broken, but everywhere, so the entire piece of
    ///       metal reads as charged and not just the bit that was hit,</item>
    /// <item>main bolts run end to end through it (outline vertex to the vertex farthest from
    ///       it, midpoint-displaced but kept inside the body), with short forks off them,</item>
    /// <item>and the joins to the next conductor and to anyone touching it get their own bolt.</item>
    /// </list>
    ///
    /// Conductors go live one after another by their depth in the chain, so a charge visibly
    /// runs down a line of girders rather than lighting them all on one frame. Cells don't
    /// vanish between redraws — they decay, so the last flicker leaves an afterimage under the
    /// next one.
    /// </summary>
    public sealed class ArcField
    {
        public static ArcField Instance { get; private set; } = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => Instance = new ArcField();

        /// <summary>World size of one arc cell — the same half-pixel the flames use.</summary>
        public static float CellSize = 0.025f;

        public static float TicksPerSecond = 60f;

        /// <summary>Ceiling on cells: a storm saturates instead of eating the frame.</summary>
        public static int MaxCells = 12000;

        /// <summary>Held zap overlaps charges; past this the oldest is dropped.</summary>
        public static int MaxCharges = 8;

        /// <summary>Brightness a cell loses per tick. 255 lasts ~4 ticks: two redraws of afterimage.</summary>
        public static int DecayPerTick = 64;

        /// <summary>A charge that found no metal is a snap in the air, not a half second of it.</summary>
        public static float AirOnlySeconds = 0.16f;

        private readonly List<Charge> _charges = new();

        private int[] _cx = new int[2048];
        private int[] _cy = new int[2048];
        private byte[] _lum = new byte[2048];
        private int _count;
        private readonly Dictionary<long, int> _index = new();

        private int _tick;
        private float _accum;
        private uint _rng = 0x2545F491u;

        // Scratch, shared: one redraw at a time.
        private readonly List<Vector2> _outline = new();
        private readonly List<int> _pathStarts = new();
        private readonly List<Vector2> _pathBuf = new();
        private readonly List<Vector2> _bolt = new();
        private readonly List<Vector2> _jagA = new();
        private readonly List<Vector2> _jagB = new();

        private static readonly ProfilerMarker s_step = new("Electricity.ArcField.Step");

        public int Count => _count;
        public int ChargeCount => _charges.Count;
        public int[] CellX => _cx;
        public int[] CellY => _cy;
        public byte[] Lum => _lum;

        public static Vector2 CellToWorld(int cx, int cy) => new(cx * CellSize, cy * CellSize);

        public void Spawn(Charge charge)
        {
            if (charge?.Profile == null) return;
            if (_charges.Count >= MaxCharges) _charges.RemoveAt(0);

            var p = charge.Profile;
            int maxDepth = 0;
            foreach (int d in charge.Depth) maxDepth = Mathf.Max(maxDepth, d);

            charge.Age = 0f;
            charge.Life = charge.Conductors.Count == 0
                ? Mathf.Min(AirOnlySeconds, p.chargeSeconds)
                : p.chargeSeconds + maxDepth * p.hopDelay;

            _charges.Add(charge);
            Draw(charge);     // the strike lands on the frame it was fired, not a tick later
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Simulation
        // ─────────────────────────────────────────────────────────────────────────

        public void Tick(float deltaTime)
        {
            if (_count == 0 && _charges.Count == 0) return;

            float step = 1f / Mathf.Max(1f, TicksPerSecond);
            _accum += deltaTime;
            if (_accum > step * 2f) _accum = step * 2f;

            while (_accum >= step)
            {
                _accum -= step;
                Step(step);
            }
        }

        private void Step(float dt)
        {
            using var _ = s_step.Auto();

            _tick++;
            Fade();

            for (int i = _charges.Count - 1; i >= 0; i--)
            {
                var c = _charges[i];
                c.Age += dt;
                if (c.Age >= c.Life)
                {
                    _charges.RemoveAt(i);
                    continue;
                }

                if (_tick % Mathf.Max(1, c.Profile.flickerTicks) == 0) Draw(c);
            }
        }

        /// <summary>
        /// How lit something that went live at <paramref name="start"/> is right now: a full flash
        /// as the charge arrives, a flickering sustain, and a fade over the last third.
        /// </summary>
        private float Envelope(Charge c, float start)
        {
            float local = c.Age - start;
            if (local < 0f) return 0f;

            float m = local < c.Profile.strikeFlashSeconds ? 1f : Range(0.55f, 0.9f);

            float fade = c.Life * 0.35f;
            float remain = c.Life - c.Age;
            if (remain < fade) m *= remain / fade;
            return m;
        }

        private void Draw(Charge c)
        {
            var p = c.Profile;

            if (c.Conductors.Count == 0)
            {
                AirDischarge(c);
                return;
            }

            for (int i = 0; i < c.Conductors.Count; i++)
            {
                var col = c.Conductors[i];
                if (!col) continue;

                float m = Envelope(c, c.Depth[i] * p.hopDelay);
                if (m > 0f) DrawConductor(c, col, m);
            }

            foreach (var hop in c.Hops)
            {
                if (hop.Depth == 0)
                {
                    // The strike itself: thick and solid while it lands, then only the odd
                    // re-strike down the same channel.
                    float local = c.Age;
                    if (local < p.strikeFlashSeconds) Bolt(hop.From, hop.To, 255, true, 2);
                    else if (NextFloat() < 0.3f) Bolt(hop.From, hop.To, (int)(170 * Envelope(c, 0f)), true, 1);
                    continue;
                }

                float mh = Envelope(c, hop.Depth * p.hopDelay);
                if (mh <= 0f) continue;

                // Joins are where it crackles: a bright jump plus a burst of sparks.
                Vector2 dir = hop.To - hop.From;
                Vector2 n = dir.sqrMagnitude > 1e-6f ? dir.normalized : Random2();
                Bolt(hop.From - n * CellSize * 3f, hop.To + n * CellSize * 3f, (int)(255 * mh), true, 0);
                Sparks((hop.From + hop.To) * 0.5f, 3, CellSize * 5f, (int)(200 * mh));
            }

            foreach (var tap in c.Taps)
            {
                float mt = Envelope(c, tap.Depth * p.hopDelay);
                if (mt <= 0f) continue;

                Bolt(tap.From, tap.To, (int)(230 * mt), true, 1);
                Sparks(tap.To, 2, CellSize * 4f, (int)(180 * mt));
                TryIgnite(p, tap.To);
            }
        }

        private void AirDischarge(Charge c)
        {
            var p = c.Profile;
            float m = Envelope(c, 0f);
            int forks = 3 + (int)(NextFloat() * 3f);

            for (int i = 0; i < forks; i++)
            {
                Vector2 end = c.Origin + Random2() * (p.strikeRadius * Range(0.6f, 1.3f));
                Bolt(c.Origin, end, (int)(255 * m), i == 0, 1);
            }

            Sparks(c.Origin, 4, p.strikeRadius * 0.4f, (int)(220 * m));
            if (c.Age <= 0f) TryIgnite(p, c.Origin);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // One conductor
        // ─────────────────────────────────────────────────────────────────────────

        private void DrawConductor(Charge c, Collider2D col, float m)
        {
            var p = c.Profile;
            Outline(col);
            if (_outline.Count < 2) return;

            // Shimmer over the whole surface, so every inch of the metal reads as live.
            for (int s = 0; s < _pathStarts.Count; s++)
            {
                int a0 = _pathStarts[s];
                int a1 = s + 1 < _pathStarts.Count ? _pathStarts[s + 1] : _outline.Count;
                for (int k = a0; k < a1; k++)
                {
                    Vector2 a = _outline[k];
                    Vector2 b = _outline[k + 1 < a1 ? k + 1 : a0];
                    Line(a, b, (int)(90 * m), 0, 0.5f);
                }
            }

            Vector2 center = col.bounds.center;
            float diag = ((Vector2)col.bounds.size).magnitude;
            int mains = Mathf.Clamp(Mathf.RoundToInt(diag / 0.9f), 1, 4);

            for (int i = 0; i < mains; i++)
            {
                // Skip the odd one: a discharge stutters.
                if (i > 0 && NextFloat() < 0.3f) continue;

                int ia = (int)(NextFloat() * _outline.Count);
                int ib = Farthest(ia);

                Vector2 a = Inward(col, _outline[ia], center);
                Vector2 b = Inward(col, _outline[ib], center);

                Jagged(a, b, p.boltRoughness, col, _bolt);
                Polyline(_bolt, (int)(255 * m), 2);

                int forks = 1 + (int)(NextFloat() * 2f);
                for (int f = 0; f < forks && _bolt.Count > 2; f++) Fork(col, _bolt, (int)(150 * m));
            }

            // Where metal meets wood is where it lights.
            for (int k = 0; k < 2; k++)
                TryIgnite(p, _outline[(int)(NextFloat() * _outline.Count)]);
        }

        /// <summary>World-space outline of the collider, all paths flattened, path starts kept.</summary>
        private void Outline(Collider2D col)
        {
            _outline.Clear();
            _pathStarts.Clear();

            if (col is PolygonCollider2D poly)
            {
                var t = poly.transform;
                for (int path = 0; path < poly.pathCount; path++)
                {
                    poly.GetPath(path, _pathBuf);
                    if (_pathBuf.Count < 2) continue;

                    _pathStarts.Add(_outline.Count);
                    foreach (var pt in _pathBuf) _outline.Add(t.TransformPoint(pt + poly.offset));
                }
                if (_outline.Count >= 2) return;
                _outline.Clear();
                _pathStarts.Clear();
            }

            var b = col.bounds;
            _pathStarts.Add(0);
            _outline.Add(new Vector2(b.min.x, b.min.y));
            _outline.Add(new Vector2(b.max.x, b.min.y));
            _outline.Add(new Vector2(b.max.x, b.max.y));
            _outline.Add(new Vector2(b.min.x, b.max.y));
        }

        private int Farthest(int from)
        {
            Vector2 a = _outline[from];
            int stride = Mathf.Max(1, _outline.Count / 64);
            int best = from;
            float bestD = -1f;

            for (int i = (int)(NextFloat() * stride); i < _outline.Count; i += stride)
            {
                float d = (_outline[i] - a).sqrMagnitude;
                if (d > bestD) { bestD = d; best = i; }
            }
            return best;
        }

        /// <summary>An outline vertex pulled a pixel into the body, so the bolt runs on the metal and not along its rim.</summary>
        private static Vector2 Inward(Collider2D col, Vector2 v, Vector2 center)
        {
            Vector2 d = center - v;
            if (d.sqrMagnitude < 1e-6f) return v;
            Vector2 p = v + d.normalized * (CellSize * 2.5f);
            return col.OverlapPoint(p) ? p : v;
        }

        private void Fork(Collider2D col, List<Vector2> main, int lum)
        {
            int i = 1 + (int)(NextFloat() * (main.Count - 2));
            Vector2 start = main[i];
            Vector2 dir = (main[i + 1] - main[i - 1]);
            if (dir.sqrMagnitude < 1e-8f) return;
            dir.Normalize();

            float ang = Range(25f, 70f) * (NextFloat() < 0.5f ? -1f : 1f) * Mathf.Deg2Rad;
            float cos = Mathf.Cos(ang), sin = Mathf.Sin(ang);
            dir = new Vector2(dir.x * cos - dir.y * sin, dir.x * sin + dir.y * cos);

            float total = (main[main.Count - 1] - main[0]).magnitude;
            float len = Mathf.Clamp(total * Range(0.12f, 0.35f), CellSize * 4f, 0.8f);

            Vector2 end = start + dir * len;
            for (int tries = 0; tries < 3 && !col.OverlapPoint(end); tries++)
            {
                len *= 0.5f;
                end = start + dir * len;
            }

            // Forks may lick a little past the edge — that is what makes it crackle.
            Jagged(start, end, 0.3f, null, _jagB);
            Polyline(_jagB, lum, 0);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Bolt geometry
        // ─────────────────────────────────────────────────────────────────────────

        private void Bolt(Vector2 a, Vector2 b, int lum, bool branch, int thickness)
        {
            if (lum <= 0) return;
            Jagged(a, b, 0.28f, null, _bolt);
            Polyline(_bolt, lum, thickness);

            if (!branch || _bolt.Count < 3) return;

            int i = 1 + (int)(NextFloat() * (_bolt.Count - 2));
            Vector2 d = _bolt[i] - _bolt[i - 1];
            if (d.sqrMagnitude < 1e-8f) return;
            float len = (b - a).magnitude * Range(0.2f, 0.45f);
            float ang = Range(20f, 60f) * (NextFloat() < 0.5f ? -1f : 1f) * Mathf.Deg2Rad;
            d.Normalize();
            var dir = new Vector2(d.x * Mathf.Cos(ang) - d.y * Mathf.Sin(ang),
                                  d.x * Mathf.Sin(ang) + d.y * Mathf.Cos(ang));

            Vector2 start = _bolt[i];
            Jagged(start, start + dir * len, 0.3f, null, _jagB);
            Polyline(_jagB, lum * 3 / 5, 0);
        }

        private void Sparks(Vector2 at, int count, float reach, int lum)
        {
            if (lum <= 0) return;
            for (int i = 0; i < count; i++)
                Line(at, at + Random2() * (reach * Range(0.4f, 1f)), lum, 0, 0.2f);
        }

        /// <summary>
        /// Midpoint displacement from <paramref name="a"/> to <paramref name="b"/>, down to a few
        /// cells a segment. With a <paramref name="inside"/> collider every new point has to land
        /// on it, so a bolt through a girder bends along the girder instead of off it.
        /// </summary>
        private void Jagged(Vector2 a, Vector2 b, float roughness, Collider2D inside, List<Vector2> result)
        {
            var src = _jagA;
            src.Clear();
            src.Add(a);
            src.Add(b);

            float seg = (b - a).magnitude;
            for (int level = 0; level < 7 && seg > CellSize * 3f; level++)
            {
                result.Clear();
                for (int i = 0; i < src.Count - 1; i++)
                {
                    Vector2 p0 = src[i], p1 = src[i + 1];
                    result.Add(p0);

                    Vector2 d = p1 - p0;
                    Vector2 perp = new Vector2(-d.y, d.x);
                    Vector2 mid = (p0 + p1) * 0.5f;
                    float off = (NextFloat() * 2f - 1f) * roughness;

                    Vector2 cand = mid + perp * off;
                    if (inside && !inside.OverlapPoint(cand))
                    {
                        cand = mid + perp * (off * 0.3f);
                        if (!inside.OverlapPoint(cand)) cand = mid;
                    }
                    result.Add(cand);
                }
                result.Add(src[src.Count - 1]);

                src.Clear();
                src.AddRange(result);
                seg *= 0.5f;
            }

            result.Clear();
            result.AddRange(src);
        }

        private void Polyline(List<Vector2> pts, int lum, int thickness)
        {
            if (lum <= 0) return;
            int side = thickness >= 2 ? lum * 11 / 20 : thickness == 1 ? lum * 7 / 20 : 0;
            for (int i = 0; i < pts.Count - 1; i++) Line(pts[i], pts[i + 1], lum, side, 0f);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Cells
        // ─────────────────────────────────────────────────────────────────────────

        private void Line(Vector2 a, Vector2 b, int lum, int side, float dropout)
        {
            if (lum <= 0) return;

            int x0 = Mathf.FloorToInt(a.x / CellSize), y0 = Mathf.FloorToInt(a.y / CellSize);
            int x1 = Mathf.FloorToInt(b.x / CellSize), y1 = Mathf.FloorToInt(b.y / CellSize);

            int dx = Mathf.Abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
            int dy = -Mathf.Abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
            bool horizontal = dx >= -dy;
            int err = dx + dy;

            for (int guard = 0; guard < 4096; guard++)
            {
                if (dropout <= 0f || NextFloat() >= dropout)
                {
                    Plot(x0, y0, lum);
                    if (side > 0)
                    {
                        if (horizontal) { Plot(x0, y0 + 1, side); Plot(x0, y0 - 1, side); }
                        else            { Plot(x0 + 1, y0, side); Plot(x0 - 1, y0, side); }
                    }
                }

                if (x0 == x1 && y0 == y1) return;
                int e2 = err * 2;
                if (e2 >= dy) { err += dy; x0 += sx; }
                if (e2 <= dx) { err += dx; y0 += sy; }
            }
        }

        private void Plot(int x, int y, int lum)
        {
            if (lum > 255) lum = 255;
            long key = Key(x, y);

            if (_index.TryGetValue(key, out int i))
            {
                if (_lum[i] < lum) _lum[i] = (byte)lum;
                return;
            }

            if (_count >= MaxCells) return;
            if (_count == _cx.Length) Grow();

            _cx[_count] = x;
            _cy[_count] = y;
            _lum[_count] = (byte)lum;
            _index[key] = _count;
            _count++;
        }

        private void Fade()
        {
            for (int i = _count - 1; i >= 0; i--)
            {
                int l = _lum[i] - DecayPerTick;
                if (l > 0)
                {
                    _lum[i] = (byte)l;
                    continue;
                }

                _index.Remove(Key(_cx[i], _cy[i]));
                int last = --_count;
                if (i == last) continue;

                _cx[i] = _cx[last];
                _cy[i] = _cy[last];
                _lum[i] = _lum[last];
                _index[Key(_cx[i], _cy[i])] = i;
            }
        }

        private void Grow()
        {
            int n = _cx.Length * 2;
            System.Array.Resize(ref _cx, n);
            System.Array.Resize(ref _cy, n);
            System.Array.Resize(ref _lum, n);
        }

        private void TryIgnite(ElectricityProfile p, Vector2 world)
        {
            if (p.igniteChancePercent <= 0f) return;
            if (NextFloat() * 100f >= p.igniteChancePercent) return;
            Fire.FireSystem.Instance.IgniteAt(world, p.igniteRadius);
        }

        private static long Key(int x, int y) => ((long)x << 32) ^ (uint)y;

        private Vector2 Random2()
        {
            float a = NextFloat() * Mathf.PI * 2f;
            return new Vector2(Mathf.Cos(a), Mathf.Sin(a));
        }

        private float Range(float a, float b) => a + (b - a) * NextFloat();

        private float NextFloat()
        {
            // xorshift32, deterministic and free.
            _rng ^= _rng << 13;
            _rng ^= _rng >> 17;
            _rng ^= _rng << 5;
            return (_rng & 0xFFFFFF) / 16777216f;
        }
    }
}
