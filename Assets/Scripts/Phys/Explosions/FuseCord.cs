using System.Collections.Generic;
using Phys.Fire;
using UnityEngine;

namespace Phys.Explosions
{
    /// <summary>
    /// A length of burning cord. Route it in the scene the way a <see cref="Props.Rope2D"/> is
    /// routed — drag the dots, the path can be any length and any shape — light one end, and the
    /// fire crawls along it at a known speed until it runs out of cord. Whatever explosive is
    /// sitting at the end it reaches goes off.
    ///
    /// It is a separate object from the thing it sets off on purpose. A barrel is then just a
    /// barrel: give it a cord and it is something you can light from across the room, leave it
    /// bare and it only goes off when it is shot or caught in someone else's blast. The same cord
    /// works on anything with an <see cref="Explosive"/> on it.
    ///
    /// The cord draws itself as a one-pixel line, rasterised from the path at the world's PPU,
    /// and burning simply eats that line a pixel at a time. It is deliberately not a
    /// <see cref="FireSystem"/> object: fire there spreads by chance and would make the length of
    /// a fuse mean nothing. Instead the burn is its own march along the path — a fuse burns at
    /// the rate a fuse burns — and it feeds <see cref="FlameField"/> as it goes, so what you see
    /// is the ordinary fire, able to light whatever it passes, and the flames of the world are
    /// what light the cord in the first place.
    /// </summary>
    [DisallowMultipleComponent]
    [AddComponentMenu("PhysFun/Fuse Cord")]
    public sealed class FuseCord : MonoBehaviour
    {
        [Header("Path (local space)")]
        [Tooltip("Route the cord follows. Drag the dots in the scene view; the + between them " +
                 "adds one. The length of this path is the length of the fuse. The first point " +
                 "is the free end you light, the last is the end that sits on the charge.")]
        public List<Vector2> points = new() { Vector2.zero, new Vector2(0f, 0.5f) };

        [Header("Cord")]
        [Tooltip("Resolution the line is drawn at. 20 is the world's own pixel — leave it.")]
        [Min(1f)] public float pixelsPerUnit = 20f;

        [Tooltip("How fast the burn travels, in world units per second. The fuse's whole job: " +
                 "path length divided by this is the seconds you get.")]
        [Min(0.02f)] public float burnSpeed = 0.35f;

        public Color cordColor = new(0.69f, 0.55f, 0.34f);
        public Color cordShade = new(0.45f, 0.33f, 0.19f);

        [Tooltip("The free ends, drawn lighter so it is clear where the thing can be lit.")]
        public Color tipColor = new(0.91f, 0.78f, 0.49f);

        [Tooltip("First colour a pixel cools to once the fire has passed it.")]
        public Color emberColor = new(1f, 0.79f, 0.31f);

        public int sortingOrder = 2;

        [Header("Fire")]
        [Tooltip("Flames touching the cord light it. This is the whole point of a fuse — off, it " +
                 "can only be lit from script.")]
        public bool litByFire = true;

        [Tooltip("Seconds between checks for a flame on the cord. The check is skipped outright " +
                 "when nothing in the world is on fire.")]
        [Min(0.02f)] public float fireCheckInterval = 0.1f;

        [Tooltip("Flame cells thrown off the burning tip each second. Per second rather than " +
                 "per pixel, so a slow fuse still burns with a proper flame on it instead of a " +
                 "few lonely sparks.")]
        [Range(0f, 200f)] public float flameRate = 45f;

        [Range(0, 100)] public int flameHeat = 70;

        [Tooltip("Smoke cells per second off the tip.")]
        [Range(0f, 60f)] public float smokeRate = 8f;

        [Tooltip("Pixels of spark thrown off the tip each second - the crackle. 0 = none.")]
        [Range(0f, 60f)] public float sparkRate = 16f;

        [Tooltip("Colour of those sparks as they leave. They cool to the ember colour.")]
        public Color sparkColor = new(1f, 0.93f, 0.66f);

        [Header("Burn")]
        [Tooltip("The pixel actually alight. Kept near white: at one pixel wide, only the " +
                 "brightest thing on screen reads as fire.")]
        public Color hotColor = new(1f, 0.96f, 0.74f);

        [Tooltip("How long a pixel goes on glowing after the fire has passed it. This is the " +
                 "short trail of embers behind the tip, and most of what makes the burn visible.")]
        [Min(0f)] public float glowTime = 0.45f;

        [Tooltip("What a spent pixel has cooled to just before it vanishes.")]
        public Color glowColor = new(0.85f, 0.25f, 0.06f);

        [Header("Ends")]
        [Tooltip("Explosives set off when the burn reaches an end. Anything with an Explosive " +
                 "within TriggerRadius of that end goes off too, so an unwired cord laid against " +
                 "a barrel still works.")]
        public List<Explosive> targets = new();

        [Min(0f)] public float triggerRadius = 0.25f;

        [Tooltip("Light the free end the moment it exists. For testing, and for a charge that " +
                 "is thrown already lit.")]
        public bool lightOnStart;

        [Tooltip("Clear the burnt-out cord away. Off leaves the spent line in place.")]
        public bool removeWhenSpent = true;

        // Set once it has gone off, and serialized, because Cracker clones an exploding object —
        // a shard of a barrel must not carry a live fuse.
        [HideInInspector] [SerializeField] private bool spent;

        private struct Head
        {
            public int Index;    // pixel on the path that is currently alight
            public int Step;     // +1 towards the end of the path, -1 towards its start
            public float Debt;   // pixels of travel earned but not yet taken
        }

        // Every cord currently in the scene. Fire finds a cord by looking at the flame field,
        // but a tool or a script that wants to put a light to one has nothing to hit — the cord
        // has no collider, being one pixel wide — so it asks here instead.
        private static readonly List<FuseCord> Live = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => Live.Clear();

        private struct Glow
        {
            public int Index;
            public float T;      // 1 just burnt, 0 gone out
        }

        private readonly List<Head> _heads = new();
        private readonly List<Glow> _glows = new();
        private float _flameDebt, _smokeDebt, _sparkDebt;
        private readonly List<Vector2Int> _cells = new();      // path, in cord-pixel coordinates
        private readonly Dictionary<int, int> _cellToIndex = new();
        private bool[] _alive;
        private Texture2D _tex;
        private SpriteRenderer _sr;
        private int _minX, _minY, _w, _h;
        private bool _dirty;
        private float _fireCheck;
        private int _aliveCount;

        /// <summary>Length of the routed path, in world units. Divided by the burn speed, the fuse's time.</summary>
        public float PathLength()
        {
            float total = 0f;
            for (int i = 0; i < points.Count - 1; i++)
                total += Vector2.Distance(TransformedPoint(i), TransformedPoint(i + 1));
            return total;
        }

        /// <summary>Seconds from lighting one end to the bang at the other.</summary>
        public float BurnSeconds() => PathLength() / Mathf.Max(0.02f, burnSpeed);

        /// <summary>True while any part of it is alight.</summary>
        public bool IsBurning => _heads.Count > 0;

        public bool IsSpent => spent;

        private void Awake()
        {
            // A clone of a spent cord (see the note on `spent`) has nothing to do but go away.
            if (spent)
            {
                Destroy(gameObject);
                return;
            }

            Rasterise();
            if (_cells.Count == 0) { enabled = false; return; }

            BuildView();
            if (lightOnStart) LightEnd(true);
        }

        private void OnEnable() => Live.Add(this);

        private void OnDisable() => Live.Remove(this);

        private void OnDestroy()
        {
            if (_tex) Destroy(_tex);
        }

        /// <summary>
        /// Put a light to whatever cord is under <paramref name="world"/>. This is what the
        /// ignite tool and anything else holding a flame calls; the cord itself is too thin to
        /// be found by a physics query.
        /// </summary>
        public static bool LightNear(Vector2 world, float radius)
        {
            bool lit = false;
            foreach (var cord in Live)
            {
                if (!cord || cord.IsSpent || cord.IsBurning) continue;
                lit |= cord.LightAt(world, radius);
            }
            return lit;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Lighting it
        // ─────────────────────────────────────────────────────────────────────

        /// <summary>Light an end: the free one the path starts at, or the one on the charge.</summary>
        public void LightEnd(bool fromStart)
        {
            if (_cells.Count == 0) return;
            AddHead(fromStart ? 0 : _cells.Count - 1, fromStart ? 1 : -1);
        }

        /// <summary>
        /// Light it wherever a flame touched it. A cord lit in the middle burns both ways, which
        /// is the honest behaviour and also the interesting one: it reaches the barrel in half
        /// the time you were counting on.
        /// </summary>
        public bool LightAt(Vector2 world, float radius = 0.06f)
        {
            int index = NearestAlive(world, radius);
            if (index < 0) return false;

            AddHead(index, 1);
            AddHead(index, -1);
            return true;
        }

        private void AddHead(int index, int step)
        {
            if (spent || index < 0 || index >= _cells.Count) return;

            // Walk to the first pixel that is still there, so a second head lit on burnt cord
            // does not sit gnawing at a hole.
            while (index >= 0 && index < _cells.Count && !_alive[index]) index += step;
            if (index < 0 || index >= _cells.Count) return;

            foreach (var h in _heads)
                if (h.Index == index && h.Step == step) return;

            _heads.Add(new Head { Index = index, Step = step });
            Paint(index, hotColor);
        }

        private int NearestAlive(Vector2 world, float radius)
        {
            float best = radius * radius;
            int found = -1;
            for (int i = 0; i < _cells.Count; i++)
            {
                if (!_alive[i]) continue;
                float d = ((Vector2)PixelWorld(i) - world).sqrMagnitude;
                if (d >= best) continue;
                best = d;
                found = i;
            }
            return found;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Burning
        // ─────────────────────────────────────────────────────────────────────

        private void Update()
        {
            if (spent) return;

            float dt = Time.deltaTime;

            if (litByFire && !IsBurning) CheckForFire();

            // Embers keep cooling after the last head has gone: the tail of the burn is part of
            // it, and a cord that vanishes the instant it is spent looks switched off.
            Cool(dt);

            if (!IsBurning)
            {
                Flush();
                if (_aliveCount == 0 && _glows.Count == 0) Finish();
                return;
            }

            Crackle(dt);

            float pixels = burnSpeed * pixelsPerUnit * dt;

            for (int i = _heads.Count - 1; i >= 0; i--)
            {
                var head = _heads[i];
                head.Debt += pixels;
                bool done = false;

                while (head.Debt >= 1f)
                {
                    head.Debt -= 1f;
                    if (Advance(ref head)) continue;
                    done = true;
                    break;
                }

                // Reaching the end sets something off, and that something may well have been
                // carrying this cord — Explosive.Snuff clears the heads out from under us.
                if (spent) return;

                if (!done) _heads[i] = head;
                else if (i < _heads.Count) _heads.RemoveAt(i);
            }

            Flush();
        }

        private void Flush()
        {
            if (!_dirty || !_tex) return;
            _tex.Apply(false, false);
            _dirty = false;
        }

        /// <summary>
        /// Fade the pixels the fire has already been over. They run from the ember colour down
        /// to nothing, which gives the tip a short glowing tail - on a one-pixel line that tail
        /// is the difference between burning and slowly disappearing.
        /// </summary>
        private void Cool(float dt)
        {
            if (_glows.Count == 0) return;

            float step = glowTime > 0f ? dt / glowTime : 1f;

            for (int i = _glows.Count - 1; i >= 0; i--)
            {
                var glow = _glows[i];
                glow.T -= step;

                if (glow.T <= 0f)
                {
                    Paint(glow.Index, Color.clear);
                    _glows.RemoveAt(i);
                    continue;
                }

                Color c = glow.T > 0.5f
                    ? Color.Lerp(emberColor, glowColor, (1f - glow.T) * 2f)
                    : glowColor;
                c.a = Mathf.Min(1f, glow.T * 2f);
                Paint(glow.Index, c);
                _glows[i] = glow;
            }
        }

        /// <summary>
        /// The flame, the smoke and the sparks off the tip, all charged by the second rather
        /// than by the pixel - how fast the fire is travelling should change where they come
        /// out, not how many of them there are.
        /// </summary>
        private void Crackle(float dt)
        {
            Vector2 tip = PixelWorld(_heads[0].Index);

            _flameDebt += flameRate * dt;
            while (_flameDebt >= 1f)
            {
                _flameDebt -= 1f;
                FlameField.Instance.Emit(tip + Random.insideUnitCircle * 0.03f, flameHeat);
            }

            _smokeDebt += smokeRate * dt;
            while (_smokeDebt >= 1f)
            {
                _smokeDebt -= 1f;
                FlameField.Instance.EmitSmoke(tip + Random.insideUnitCircle * 0.04f);
            }

            _sparkDebt += sparkRate * dt;
            if (_sparkDebt < 3f) return;

            // Thrown in twos and threes: one pixel at a time is a dotted line, a handful at
            // once is a crackle.
            int count = Mathf.FloorToInt(_sparkDebt);
            _sparkDebt -= count;
            ExplosionBurst.Sparks(tip, count, 1.6f, sparkColor, emberColor, 0.35f, 1.1f);
        }

        /// <summary>
        /// Eat the pixel under the head and step on. False when there is nothing left ahead —
        /// either the cord ran out, which is a bang, or it met a stretch that has already burnt.
        /// </summary>
        private bool Advance(ref Head head)
        {
            int at = head.Index;
            Consume(at);

            int next = at + head.Step;
            if (next < 0 || next >= _cells.Count)
            {
                Reached(PixelWorld(at));
                return false;
            }

            if (!_alive[next]) return false;   // the other head got here first

            head.Index = next;
            Paint(next, hotColor);
            return true;
        }

        private void Consume(int index)
        {
            if (!_alive[index]) return;

            _alive[index] = false;
            _aliveCount--;

            // Not cleared: handed to the ember tail, which paints it until it has cooled.
            if (glowTime > 0f) _glows.Add(new Glow { Index = index, T = 1f });
            else Paint(index, Color.clear);
        }

        /// <summary>The burn ran off the end of the cord. Whatever is sitting there goes off.</summary>
        private void Reached(Vector2 world)
        {
            foreach (var t in targets)
                if (t) t.DetonateNow();

            if (triggerRadius > 0f)
            {
                var hits = Physics2D.OverlapCircleAll(world, triggerRadius);
                foreach (var hit in hits)
                {
                    var boom = hit ? hit.GetComponentInParent<Explosive>() : null;
                    if (!boom || targets.Contains(boom)) continue;
                    boom.DetonateNow();
                }
            }

            // Nothing to set off is a legitimate outcome: the cord simply burns out. It goes out
            // with a spit of sparks and a flame, which may well be all it was laid there to do.
            FlameField.Instance.Emit(world, flameHeat);
            ExplosionBurst.Sparks(world, 8, 2.4f, sparkColor, emberColor);
        }

        private void Finish()
        {
            spent = true;
            if (removeWhenSpent) Destroy(gameObject);
        }

        /// <summary>
        /// Put it out and write it off, whether it had burnt through or not. What an explosive
        /// calls on its own cords as it goes up: the charge is spent, so the cord is too, and a
        /// shard of the thing must not come away still carrying a live fuse.
        /// </summary>
        public void Snuff()
        {
            _heads.Clear();
            Finish();
        }

        /// <summary>
        /// Is a flame lying on the cord? Asked on a timer rather than every frame, skipped
        /// entirely when nothing is burning anywhere, and rejected on the fire's own bounding box
        /// before a single cell is looked at.
        /// </summary>
        private void CheckForFire()
        {
            _fireCheck -= Time.deltaTime;
            if (_fireCheck > 0f) return;
            _fireCheck = fireCheckInterval;

            var field = FlameField.Instance;
            if (field.Count == 0) return;
            if (!field.TryGetFireBounds(out Rect fire)) return;

            var bounds = _sr.bounds;
            if (!fire.Overlaps(new Rect(bounds.min, bounds.size))) return;

            var kind = field.Kind;
            var cx = field.CellX;
            var cy = field.CellY;

            for (int i = 0; i < field.Count; i++)
            {
                if (kind[i] != FlameField.KindFire) continue;

                Vector2 world = FlameField.CellToWorld(cx[i], cy[i]);
                if (!bounds.Contains(new Vector3(world.x, world.y, bounds.center.z))) continue;

                // The flame cell is finer than a cord pixel, so the lookup is by cell rather
                // than by distance: whichever pixel of the line it is standing on is the one
                // that catches.
                if (WorldToCell(world, out int px, out int py) &&
                    _cellToIndex.TryGetValue(Key(px, py), out int index) && _alive[index])
                {
                    AddHead(index, 1);
                    AddHead(index, -1);
                    return;
                }
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // The line itself
        // ─────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Turn the routed path into a single-pixel line. Bresenham rather than a sampled curve,
        /// because the burn walks the pixels one at a time and they have to be in order and
        /// touching for that walk to mean anything.
        /// </summary>
        private void Rasterise()
        {
            _cells.Clear();
            _cellToIndex.Clear();
            if (points == null || points.Count < 2) return;

            for (int i = 0; i < points.Count - 1; i++)
            {
                Vector2Int a = ToCell(points[i]);
                Vector2Int b = ToCell(points[i + 1]);
                Line(a, b, i == 0);
            }

            if (_cells.Count == 0) return;

            _minX = int.MaxValue; _minY = int.MaxValue;
            int maxX = int.MinValue, maxY = int.MinValue;
            foreach (var c in _cells)
            {
                _minX = Mathf.Min(_minX, c.x); maxX = Mathf.Max(maxX, c.x);
                _minY = Mathf.Min(_minY, c.y); maxY = Mathf.Max(maxY, c.y);
            }

            _w = maxX - _minX + 1;
            _h = maxY - _minY + 1;

            _alive = new bool[_cells.Count];
            for (int i = 0; i < _cells.Count; i++)
            {
                _alive[i] = true;
                _cellToIndex[Key(_cells[i].x, _cells[i].y)] = i;
            }
            _aliveCount = _cells.Count;
        }

        private void Line(Vector2Int a, Vector2Int b, bool includeFirst)
        {
            int dx = Mathf.Abs(b.x - a.x), sx = a.x < b.x ? 1 : -1;
            int dy = -Mathf.Abs(b.y - a.y), sy = a.y < b.y ? 1 : -1;
            int err = dx + dy;

            int x = a.x, y = a.y;
            bool first = true;

            while (true)
            {
                if (!first || includeFirst) _cells.Add(new Vector2Int(x, y));
                first = false;

                if (x == b.x && y == b.y) break;

                int e2 = err * 2;
                if (e2 >= dy) { err += dy; x += sx; }
                if (e2 <= dx) { err += dx; y += sy; }
            }
        }

        private void BuildView()
        {
            _tex = new Texture2D(_w, _h, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
            };

            var clear = new Color32[_w * _h];
            _tex.SetPixels32(clear);

            for (int i = 0; i < _cells.Count; i++)
            {
                bool tip = i == 0 || i == _cells.Count - 1;
                // A dark pixel every third one gives a one-pixel line some twist to it.
                Color c = tip ? tipColor : (i % 3 == 2 ? cordShade : cordColor);
                Paint(i, c);
            }
            _tex.Apply(false, false);
            _dirty = false;

            var view = new GameObject("Cord") { layer = gameObject.layer };
            view.transform.SetParent(transform, false);
            view.transform.localPosition =
                new Vector3(_minX / pixelsPerUnit, _minY / pixelsPerUnit, 0f);

            _sr = view.AddComponent<SpriteRenderer>();
            _sr.sprite = Sprite.Create(_tex, new Rect(0, 0, _w, _h), Vector2.zero,
                                       pixelsPerUnit, 0, SpriteMeshType.FullRect);
            _sr.sortingOrder = sortingOrder;
        }

        private void Paint(int index, Color c)
        {
            var cell = _cells[index];
            _tex.SetPixel(cell.x - _minX, cell.y - _minY, c);
            _dirty = true;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Coordinates
        // ─────────────────────────────────────────────────────────────────────

        private Vector2Int ToCell(Vector2 local) => new(
            Mathf.FloorToInt(local.x * pixelsPerUnit),
            Mathf.FloorToInt(local.y * pixelsPerUnit));

        private bool WorldToCell(Vector2 world, out int px, out int py)
        {
            Vector2 local = transform.InverseTransformPoint(world);
            px = Mathf.FloorToInt(local.x * pixelsPerUnit);
            py = Mathf.FloorToInt(local.y * pixelsPerUnit);
            return true;
        }

        /// <summary>Centre of a path pixel, in the world.</summary>
        private Vector3 PixelWorld(int index)
        {
            var cell = _cells[index];
            return transform.TransformPoint(new Vector3(
                (cell.x + 0.5f) / pixelsPerUnit,
                (cell.y + 0.5f) / pixelsPerUnit, 0f));
        }

        private static int Key(int x, int y) => (x << 16) ^ (ushort)y;

        private Vector3 TransformedPoint(int i) => transform.TransformPoint(points[i]);

        /// <summary>The routed path in world space. Used by the editor and the gizmos.</summary>
        public List<Vector3> WorldPath()
        {
            var path = new List<Vector3>(points.Count);
            for (int i = 0; i < points.Count; i++) path.Add(TransformedPoint(i));
            return path;
        }

        private void OnDrawGizmos()
        {
            if (points == null || points.Count < 2) return;

            Gizmos.color = Application.isPlaying ? new Color(1f, 0.6f, 0.2f, 0.5f) : cordColor;
            for (int i = 0; i < points.Count - 1; i++)
                Gizmos.DrawLine(TransformedPoint(i), TransformedPoint(i + 1));

            if (triggerRadius <= 0f) return;
            Gizmos.color = new Color(1f, 0.35f, 0.15f, 0.5f);
            Gizmos.DrawWireSphere(TransformedPoint(points.Count - 1), triggerRadius);
            Gizmos.DrawWireSphere(TransformedPoint(0), triggerRadius);
        }
    }
}
