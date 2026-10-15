using System.Collections.Generic;
using Phys.Terrain;
using UnityEngine;

namespace Props
{
    /// <summary>
    /// Clutter: the bottles, books, pots, pictures and furniture a room is filled with so it
    /// looks lived in, which must not stop anyone walking through it.
    ///
    /// It starts asleep: a static body on the Decor layer, which the player and the enemies do
    /// not collide with (<see cref="Physics2D.IgnoreLayerCollision(int, int, bool)"/>, set up
    /// here) and which no ground, sight or obstacle mask of theirs includes. Everything else
    /// still meets it - rounds, blasts, fire, falling crates, ropes, corpses, other clutter -
    /// and the first of them that does wakes it: the body turns dynamic and from then on it is
    /// an ordinary loose prop. It goes back to its own layer as soon as it is clear of every
    /// character (<see cref="Settle"/>), so what was knocked down is real wreckage you kick
    /// and stand on - but it never springs out of someone it woke up inside.
    ///
    /// What wakes it:
    /// <list type="bullet">
    /// <item>a round passing through it (<see cref="Knock"/> from Common.Projectile - clutter
    /// never stops a round, or a furnished room would be all cover), a blast
    /// (<see cref="WakeInCircle"/> from Explosion.Detonate) or fire (FireSystem.Ignite);</item>
    /// <item>a moving body knocking into it harder than <see cref="knock"/>;</item>
    /// <item>losing what it stands on - the table under it shot away, the deck burnt through.
    /// Checked a few at a time (<see cref="SupportChecksPerFrame"/>). Clutter hung on the back
    /// wall (<see cref="onWall"/>) needs nothing under it.</item>
    /// </list>
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class Decor : MonoBehaviour
    {
        public const string LayerName = "Decor";

        [Tooltip("Hung on the back wall - a picture, a tool on a nail. Needs nothing under it, " +
                 "and stays up until something hits it.")]
        public bool onWall;

        [Tooltip("Speed, units a second, a moving body must hit it at to knock it awake.")]
        [Min(0f)] public float knock = 1.2f;

        /// <summary>Sleepers whose footing is checked per physics step.</summary>
        public static int SupportChecksPerFrame = 12;

        /// <summary>How far under its feet a sleeper looks for something to stand on.</summary>
        public static float SupportProbe = 0.06f;

        private static readonly List<Decor> Sleepers = new();
        private static readonly List<Decor> Settling = new();     // awake, still on the Decor layer
        private static readonly List<Collider2D> Probe = new();
        private static int _cursor;
        private static int _layer = -2;
        private static int _player = -2, _enemy = -2;

        private Rigidbody2D _rb;
        private Collider2D[] _cols;
        private Transform[] _parts;
        private int[] _ownLayers;

        public bool Asleep { get; private set; }

        /// <summary>The Decor layer, or -1 if Tags and Layers has none.</summary>
        public static int Layer
        {
            get
            {
                if (_layer != -2) return _layer;
                _layer = LayerMask.NameToLayer(LayerName);
                if (_layer < 0)
                    Debug.LogWarning($"Decor: no '{LayerName}' layer in Tags and Layers - clutter " +
                                     "will block the player. Add it (slot 9).");
                return _layer;
            }
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            Sleepers.Clear();
            Settling.Clear();
            _cursor = 0;
            _layer = -2;
            _player = _enemy = -2;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void SetUpLayers()
        {
            int decor = Layer;
            if (decor < 0) return;
            foreach (var name in new[] { "Player", "Enemy" })
            {
                int other = LayerMask.NameToLayer(name);
                if (other >= 0) Physics2D.IgnoreLayerCollision(decor, other, true);
            }
        }

        private void Awake()
        {
            _rb = GetComponent<Rigidbody2D>();
            _cols = GetComponentsInChildren<Collider2D>(true);

            _parts = GetComponentsInChildren<Transform>(true);
            _ownLayers = new int[_parts.Length];
            int layer = Layer;
            for (int i = 0; i < _parts.Length; i++)
            {
                _ownLayers[i] = _parts[i].gameObject.layer;
                if (layer >= 0) _parts[i].gameObject.layer = layer;
            }

            _rb.bodyType = RigidbodyType2D.Static;
            Asleep = true;
        }

        private void OnEnable()
        {
            if (Asleep && !Sleepers.Contains(this)) Sleepers.Add(this);
        }

        private void OnDisable()
        {
            Sleepers.Remove(this);
            Settling.Remove(this);
        }

        /// <summary>Turn it into a loose prop, now.</summary>
        public void Wake()
        {
            if (!Asleep || !_rb) return;
            Asleep = false;
            Sleepers.Remove(this);
            _rb.bodyType = RigidbodyType2D.Dynamic;
            _rb.WakeUp();
            if (!Settling.Contains(this)) Settling.Add(this);
        }

        /// <summary>
        /// Awake clutter goes back to the layer it was made on - colliding with the player and
        /// the enemies like any loose prop - once none of its colliders overlaps a character.
        /// Until then it stays on the Decor layer, so a shelf shot down onto someone's head
        /// falls through them instead of being shoved out sideways by the solver.
        /// </summary>
        private bool Settle()
        {
            if (_player == -2) { _player = LayerMask.NameToLayer("Player"); _enemy = LayerMask.NameToLayer("Enemy"); }
            int mask = (_player >= 0 ? 1 << _player : 0) | (_enemy >= 0 ? 1 << _enemy : 0);
            var filter = new ContactFilter2D { useLayerMask = true, layerMask = mask, useTriggers = false };
            foreach (var c in _cols)
            {
                if (!c || !c.enabled || c.isTrigger) continue;
                Probe.Clear();
                if (c.Overlap(filter, Probe) > 0) return false;
            }
            for (int i = 0; i < _parts.Length; i++)
                if (_parts[i]) _parts[i].gameObject.layer = _ownLayers[i];
            return true;
        }

        /// <summary>Wake the clutter <paramref name="go"/> belongs to, if it is clutter.</summary>
        public static void WakeObject(GameObject go)
        {
            if (!go) return;
            var d = go.GetComponentInParent<Decor>();
            if (d) d.Wake();
        }

        /// <summary>Wake the clutter <paramref name="col"/> belongs to and give it a shove at
        /// <paramref name="point"/> - a round passing through it.</summary>
        public static void Knock(Collider2D col, Vector2 impulse, Vector2 point)
        {
            if (!col) return;
            var d = col.GetComponentInParent<Decor>();
            if (!d) return;
            d.Wake();
            if (d._rb && d._rb.bodyType == RigidbodyType2D.Dynamic)
                d._rb.AddForceAtPosition(impulse, point, ForceMode2D.Impulse);
        }

        /// <summary>Wake every piece of clutter with a collider inside the circle.</summary>
        public static void WakeInCircle(Vector2 centre, float radius)
        {
            int layer = Layer;
            if (layer < 0 || Sleepers.Count == 0) return;
            var filter = new ContactFilter2D { useLayerMask = true, layerMask = 1 << layer, useTriggers = false };
            Probe.Clear();
            Physics2D.OverlapCircle(centre, radius, filter, Probe);
            foreach (var c in Probe)
                if (c) WakeObject(c.gameObject);
        }

        private void OnCollisionEnter2D(Collision2D c)
        {
            if (!Asleep || !c.rigidbody || c.rigidbody.bodyType != RigidbodyType2D.Dynamic) return;
            if (c.relativeVelocity.sqrMagnitude < knock * knock) return;
            Wake();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Footing
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Something solid in a thin strip just under its lowest edge - terrain, a deck, a
        /// table, another piece of clutter it is stacked on. A static body does not fall when
        /// what holds it goes, so this is how it finds out.
        /// </summary>
        private bool HasFooting()
        {
            if (onWall || _cols.Length == 0) return true;

            Bounds b = default;
            bool any = false;
            foreach (var c in _cols)
            {
                if (!c || !c.enabled || c.isTrigger) continue;
                if (!any) { b = c.bounds; any = true; }
                else b.Encapsulate(c.bounds);
            }
            if (!any) return true;

            var centre = new Vector2(b.center.x, b.min.y - SupportProbe * 0.5f);
            var size = new Vector2(Mathf.Max(0.02f, b.size.x * 0.8f), SupportProbe);

            // Ground that is not built yet is still ground (the floor streams in round the
            // player); without this a room's clutter would drop through the world on arrival.
            if (!TerrainBuilder.IsBuilt(new Rect(centre - size * 0.5f - Vector2.one * 0.5f, size + Vector2.one)))
                return true;

            if (_player == -2) { _player = LayerMask.NameToLayer("Player"); _enemy = LayerMask.NameToLayer("Enemy"); }
            Probe.Clear();
            Physics2D.OverlapBox(centre, size, 0f, new ContactFilter2D { useTriggers = false }, Probe);
            foreach (var c in Probe)
            {
                if (!c || c.attachedRigidbody == _rb) continue;
                int l = c.gameObject.layer;
                if (l == _player || l == _enemy) continue;
                return true;
            }
            return false;
        }

        /// <summary>Every step: woken clutter clear of the characters gets its own layer back
        /// (<see cref="Settle"/>); and a few sleepers, round and round, are checked for footing -
        /// anyone left standing on nothing wakes and falls. Run by <see cref="DecorFooting"/>.</summary>
        internal static void CheckFooting()
        {
            for (int i = Settling.Count - 1; i >= 0; i--)
            {
                var s = Settling[i];
                if (!s || s.Settle()) Settling.RemoveAt(i);
            }

            int n = Mathf.Min(SupportChecksPerFrame, Sleepers.Count);
            for (int i = 0; i < n && Sleepers.Count > 0; i++)
            {
                if (_cursor >= Sleepers.Count) _cursor = 0;
                var d = Sleepers[_cursor];
                if (!d) { Sleepers.RemoveAt(_cursor); continue; }
                if (!d.HasFooting()) d.Wake();   // removes itself; the cursor now points at the next
                else _cursor++;
            }
        }
    }
}
