using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;

namespace Phys.Fire
{
    /// <summary>
    /// The flames themselves: a sparse world grid of one-pixel fire and smoke cells that
    /// rise, lick sideways, ignite what they touch and wink out.
    ///
    /// This is a port of Noita's own CFireCell as it is compiled into the dev build
    /// (source/grid/cells/cfirecell.cpp, CFireCell::Update at 0x7480b0), not a lookalike.
    /// Every probability in <see cref="StepFire"/> is that function's:
    ///
    /// <list type="bullet">
    /// <item>two ignition attempts on random neighbours before anything else (0x7481ca, 0x7481d8),</item>
    /// <item>rand()%101 &lt; 0x23 — only 35% of frames even try to move (0x748308),</item>
    /// <item>straight up first, and if that is blocked another 35% roll gives up for the frame
    ///       (0x748396). That roll is what makes a flame flicker in place instead of
    ///       streaming upward like a jet,</item>
    /// <item>otherwise one random horizontal direction, then its mirror (0x7483c6),</item>
    /// <item>a flame that did not move dies on rand() &amp; 0xF (0x748782). There is no lifetime
    ///       counter anywhere in CFireCell — that one roll is the whole reason a fire has a
    ///       height instead of reaching the top of the screen.</item>
    /// </list>
    ///
    /// Cells are visuals plus ignition; they do not collide with the world. Noita can ask its
    /// grid what is solid at any pixel because the world *is* that grid; here it is colliders
    /// and sprite textures, so the same question costs a physics query per flame per frame.
    /// What keeps flames out of solid objects instead is the emission rule in
    /// <see cref="FireSystem.EmitFlames"/> — Noita only ever spawns a flame into an empty cell
    /// above a burning one, so flames start outside the surface and die before they have
    /// risen far enough for it to matter.
    /// </summary>
    public sealed class FlameField
    {
        public static FlameField Instance { get; private set; } = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => Instance = new FlameField();

        public const byte KindFire = 0;
        public const byte KindSmoke = 1;

        /// <summary>
        /// World size of one flame cell — a Noita pixel. 1/40 unit matches the terrain art, so
        /// a flame cell is exactly one terrain pixel and the fire reads as part of the world
        /// rather than as an effect laid over it.
        /// </summary>
        public static float CellSize = 0.025f;

        /// <summary>Noita's grid runs at 60 Hz, and every probability below is per frame at that rate.</summary>
        public static float TicksPerSecond = 60f;

        /// <summary>Ceiling on live cells: a huge blaze saturates instead of eating the frame.</summary>
        public static int MaxCells = 9000;

        // ── CFireCell::Update ────────────────────────────────────────────────────
        public static int MoveChancePercent = 35;      // 0x748308: rand()%101 < 0x23
        public static int GiveUpChancePercent = 35;    // 0x748396: blocked overhead, skip the frame
        public static int IdleDeathOneIn = 16;         // 0x748782: rand() & 0xF

        // ── Smoke ────────────────────────────────────────────────────────────────
        // Noita's smoke is a plain gas cell (CGasCell, 0x748e00) which was not read. This is
        // the simplest thing that behaves like one: it rises, wanders, and fades out.
        public static int SmokeLifeTicks = 90;
        public static int SmokeLifeJitter = 70;
        public static int SmokeRiseChancePercent = 45;

        /// <summary>
        /// Physics probes spent per tick letting flames jump to an object that is *not* already
        /// burning — the only part of Noita's ICell::TryIgniteRandomNeighbour (0x7481ca) that
        /// needs to ask the physics world anything.
        ///
        /// Relighting the object a flame came off is not done here: that is far too common to
        /// pay an OverlapCircle for, and FireSystem.IgniteFromFlames resolves it against the
        /// burning object's own texture instead, for every flame, every burn step.
        /// </summary>
        public static int IgniteProbesPerTick = 4;

        /// <summary>World radius of one such probe. About two flame cells.</summary>
        public static float IgniteProbeRadius = 0.05f;

        private int[] _cx = new int[1024];
        private int[] _cy = new int[1024];
        private byte[] _kind = new byte[1024];
        private byte[] _heat = new byte[1024];      // flame temperature: ignition power and colour
        private byte[] _age = new byte[1024];       // ticks alive, saturating — drives the colour ramp
        private ushort[] _life = new ushort[1024];  // smoke only: ticks left
        private int _count;

        // Bounding box of the live flames, in cell coordinates.
        private int _fx0, _fy0, _fx1, _fy1;
        private bool _hasFireBounds;

        private static readonly ProfilerMarker s_step = new("Fire.FlameField.Step");

        private readonly HashSet<long> _occupied = new();
        private uint _rng = 0x9E3779B9u;
        private float _accum;

        public int Count => _count;
        public int[] CellX => _cx;
        public int[] CellY => _cy;
        public byte[] Kind => _kind;
        public byte[] Heat => _heat;
        public byte[] Age => _age;
        public ushort[] Life => _life;

        // ─────────────────────────────────────────────────────────────────────────
        // Spawning
        // ─────────────────────────────────────────────────────────────────────────

        public static void WorldToCell(Vector2 world, out int cx, out int cy)
        {
            cx = Mathf.FloorToInt(world.x / CellSize);
            cy = Mathf.FloorToInt(world.y / CellSize);
        }

        public static Vector2 CellToWorld(int cx, int cy) =>
            new Vector2(cx * CellSize, cy * CellSize);

        /// <summary>
        /// Put a flame in the cell containing <paramref name="world"/>, unless one is already
        /// there. False means the spot was taken, which is the caller's cue that this pixel had
        /// nowhere to vent — the way a buried cell in Noita fails to generate a flame.
        /// </summary>
        public bool Emit(Vector2 world, int heat)
        {
            // Running out of budget is our problem, not the pixel's: report success so a
            // big fire throttles its flames instead of reading the cap as "no air" and
            // suffocating itself.
            if (_count >= MaxCells) return true;

            WorldToCell(world, out int cx, out int cy);
            return Add(cx, cy, KindFire, (byte)Mathf.Clamp(heat, 1, 255), 0);
        }

        public bool EmitSmoke(Vector2 world)
        {
            WorldToCell(world, out int cx, out int cy);
            return Add(cx, cy, KindSmoke, 0, SmokeLifeTicks + (int)(NextFloat() * SmokeLifeJitter));
        }

        /// <summary>Wipe the flames inside a world-space circle — what dousing a fire looks like.</summary>
        public void Douse(Vector2 world, float radius)
        {
            float r2 = radius * radius;
            for (int i = _count - 1; i >= 0; i--)
            {
                if (_kind[i] != KindFire) continue;
                if ((CellToWorld(_cx[i], _cy[i]) - world).sqrMagnitude <= r2) RemoveAt(i);
            }
        }

        public void Clear()
        {
            _count = 0;
            _occupied.Clear();
        }

        /// <summary>
        /// World-space box around every live flame, as of the last step. Burning objects test
        /// their own bounds against it before asking each flame whether it is touching them,
        /// so objects that once burned and are now nowhere near the fire cost one box test.
        /// </summary>
        public bool TryGetFireBounds(out Rect area)
        {
            area = default;
            if (!_hasFireBounds) return false;

            area = Rect.MinMaxRect(_fx0 * CellSize, _fy0 * CellSize,
                                   (_fx1 + 1) * CellSize, (_fy1 + 1) * CellSize);
            return true;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Simulation
        // ─────────────────────────────────────────────────────────────────────────

        public void Tick(float deltaTime)
        {
            float step = 1f / Mathf.Max(1f, TicksPerSecond);
            _accum += Mathf.Min(deltaTime, 0.25f);

            int steps = 0;
            while (_accum >= step && steps < 4)
            {
                _accum -= step;
                steps++;
                FireSystem.Instance.EmitFlames();   // ICell::UpdateFire, once per grid frame
                Step();
            }
            if (_accum >= step) _accum = 0f;
        }

        private void Step()
        {
            using var _ = s_step.Auto();

            // Backwards, because removal swaps the last cell down: walking down never
            // revisits a cell that was moved into a slot already passed.
            for (int i = _count - 1; i >= 0; i--)
            {
                if (_age[i] < 255) _age[i]++;

                if (_kind[i] == KindSmoke) StepSmoke(i);
                else StepFire(i);
            }

            // Recomputed after the moves, over the cells that survived them.
            _hasFireBounds = false;
            for (int i = 0; i < _count; i++)
            {
                if (_kind[i] != KindFire) continue;

                if (!_hasFireBounds)
                {
                    _fx0 = _fx1 = _cx[i];
                    _fy0 = _fy1 = _cy[i];
                    _hasFireBounds = true;
                    continue;
                }

                if (_cx[i] < _fx0) _fx0 = _cx[i];
                if (_cx[i] > _fx1) _fx1 = _cx[i];
                if (_cy[i] < _fy0) _fy0 = _cy[i];
                if (_cy[i] > _fy1) _fy1 = _cy[i];
            }

            SpendIgniteProbes();
        }

        private void StepFire(int i)
        {
            // 0x748308: rand()%101 < 0x23. Two frames in three a flame does not move at all.
            if (Below(101) < MoveChancePercent)
            {
                int x = _cx[i], y = _cy[i];

                // Straight up wins whenever it is free (0x748313).
                if (Move(i, x, y + 1)) return;

                // 0x748396: blocked overhead, and a third of the time that is the whole frame.
                if (Below(101) < GiveUpChancePercent) return;

                // 0x7483c6: one horizontal direction picked 50/50, then its mirror.
                int dir = Below(101) < 50 ? -1 : 1;
                if (Move(i, x + dir, y)) return;
                if (Move(i, x - dir, y)) return;
            }

            // 0x748782: a flame that stayed put is 1-in-16 likely to be gone.
            if (Below((uint)Mathf.Max(1, IdleDeathOneIn)) == 0) RemoveAt(i);
        }

        private void StepSmoke(int i)
        {
            if (_life[i] == 0) { RemoveAt(i); return; }
            _life[i]--;

            if (Below(101) >= SmokeRiseChancePercent) return;

            int x = _cx[i], y = _cy[i];
            int dir = (int)Below(3) - 1;
            if (Move(i, x + dir, y + 1)) return;
            if (Move(i, x, y + 1)) return;
            Move(i, x + dir, y);
        }

        /// <summary>
        /// Let a few flames set light to whatever they are sitting against. Noita's
        /// ICell::TryIgniteRandomNeighbour (0x7520a0) rolls the flame's own temperature as a
        /// percentage, so a hot flame spreads fast and a dying one barely spreads at all;
        /// that part is kept exactly.
        /// </summary>
        private void SpendIgniteProbes()
        {
            if (_count == 0) return;

            for (int n = 0; n < IgniteProbesPerTick; n++)
            {
                int i = (int)(NextFloat() * _count);
                if (i >= _count || _kind[i] != KindFire) continue;
                if (Below(101) > _heat[i]) continue;      // 0x7520d2

                FireSystem.Instance.IgniteAt(CellToWorld(_cx[i], _cy[i]), IgniteProbeRadius);
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Cell storage
        // ─────────────────────────────────────────────────────────────────────────

        private bool Add(int cx, int cy, byte kind, byte heat, int life)
        {
            if (_count >= MaxCells) return false;
            if (!_occupied.Add(Key(cx, cy))) return false;

            if (_count == _cx.Length) Grow();

            _cx[_count] = cx;
            _cy[_count] = cy;
            _kind[_count] = kind;
            _heat[_count] = heat;
            _age[_count] = 0;
            _life[_count] = (ushort)Mathf.Clamp(life, 0, ushort.MaxValue);
            _count++;
            return true;
        }

        private bool Move(int i, int nx, int ny)
        {
            if (!_occupied.Add(Key(nx, ny))) return false;

            _occupied.Remove(Key(_cx[i], _cy[i]));
            _cx[i] = nx;
            _cy[i] = ny;
            return true;
        }

        private void RemoveAt(int i)
        {
            _occupied.Remove(Key(_cx[i], _cy[i]));
            int last = --_count;
            if (i == last) return;

            _cx[i] = _cx[last];
            _cy[i] = _cy[last];
            _kind[i] = _kind[last];
            _heat[i] = _heat[last];
            _age[i] = _age[last];
            _life[i] = _life[last];
        }

        private void Grow()
        {
            int n = _cx.Length * 2;
            System.Array.Resize(ref _cx, n);
            System.Array.Resize(ref _cy, n);
            System.Array.Resize(ref _kind, n);
            System.Array.Resize(ref _heat, n);
            System.Array.Resize(ref _age, n);
            System.Array.Resize(ref _life, n);
        }

        private static long Key(int cx, int cy) => ((long)cx << 32) ^ (uint)cy;

        // ─────────────────────────────────────────────────────────────────────────
        // Noise
        // ─────────────────────────────────────────────────────────────────────────

        private uint NextUInt()
        {
            _rng ^= _rng << 13;
            _rng ^= _rng >> 17;
            _rng ^= _rng << 5;
            return _rng;
        }

        public float NextFloat() => (NextUInt() & 0xFFFFFF) / 16777216f;

        /// <summary>Noita's rolls are all rand() % n, so ours are too.</summary>
        private uint Below(uint n) => NextUInt() % n;
    }
}
