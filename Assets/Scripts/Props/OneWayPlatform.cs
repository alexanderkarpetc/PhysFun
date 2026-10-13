using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Props
{
    /// <summary>
    /// A floor you can come up through and stand on, Terraria style: a timber deck, a beam.
    /// From below it is not there - levitate or climb up through it - and from above it holds
    /// like any floor, until whoever is on it asks to go down (the player holds S), and then
    /// it lets just them through.
    ///
    /// The one-way part is Unity's <see cref="PlatformEffector2D"/>, set up here so a prop
    /// prefab only has to carry this component. Clones made by the cracker or a pixel split
    /// run Awake again and come out one-way too. Going down is per pair of colliders
    /// (<see cref="Physics2D.IgnoreCollision(Collider2D, Collider2D, bool)"/>), and the pair is
    /// only restored once they no longer overlap - restore it any earlier and the effector
    /// sees a body inside the deck and shoves it back up on top.
    ///
    /// Raycasts still hit it, so a deck blocks sight lines the same as any floor.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class OneWayPlatform : MonoBehaviour
    {
        [Tooltip("How much of the top counts as the top, in degrees. Contacts outside it pass.")]
        [SerializeField, Range(60f, 180f)] private float _surfaceArc = 160f;

        private static readonly List<Collider2D> Hits = new();

        private Collider2D[] _cols;
        // collider of something passing through -> earliest time it may collide again
        private readonly Dictionary<Collider2D, float> _passing = new();
        private Coroutine _restore;

        private void Awake()
        {
            var effector = GetComponent<PlatformEffector2D>();
            if (!effector) effector = gameObject.AddComponent<PlatformEffector2D>();
            effector.useOneWay = true;
            effector.useOneWayGrouping = true;
            effector.surfaceArc = _surfaceArc;
            effector.useSideFriction = false;
            effector.useSideBounce = false;
            effector.useColliderMask = false;
            _cols = GetComponents<Collider2D>();
            foreach (var c in _cols)
                if (!c.isTrigger) c.usedByEffector = true;
        }

        /// <summary>True if <paramref name="col"/> belongs to a one-way platform.</summary>
        public static bool Is(Collider2D col) => col && col.GetComponent<OneWayPlatform>();

        /// <summary>True while <paramref name="who"/> is being let through <paramref name="col"/>.</summary>
        public static bool IsPassing(Collider2D col, Collider2D who) =>
            col && who && Physics2D.GetIgnoreCollision(col, who);

        /// <summary>
        /// Let <paramref name="who"/> through every platform within <paramref name="radius"/>
        /// of <paramref name="point"/> (the feet). Returns true if there was one.
        /// </summary>
        public static bool DropThrough(Vector2 point, float radius, IReadOnlyList<Collider2D> who, float minTime)
        {
            Hits.Clear();
            var filter = new ContactFilter2D { useTriggers = false };
            Physics2D.OverlapCircle(point, radius, filter, Hits);
            bool any = false;
            foreach (var hit in Hits)
            {
                var platform = hit ? hit.GetComponent<OneWayPlatform>() : null;
                if (!platform) continue;
                platform.LetThrough(who, minTime);
                any = true;
            }
            return any;
        }

        /// <summary>Stop colliding with <paramref name="who"/> for at least <paramref name="minTime"/>
        /// seconds, and until they have left the deck.</summary>
        public void LetThrough(IReadOnlyList<Collider2D> who, float minTime)
        {
            float until = Time.time + minTime;
            foreach (var w in who)
            {
                if (!w) continue;
                foreach (var c in _cols)
                    if (c && !c.isTrigger) Physics2D.IgnoreCollision(w, c, true);
                _passing[w] = _passing.TryGetValue(w, out var t) ? Mathf.Max(t, until) : until;
            }
            _restore ??= StartCoroutine(Restore());
        }

        private IEnumerator Restore()
        {
            var done = new List<Collider2D>();
            var wait = new WaitForFixedUpdate();
            while (_passing.Count > 0)
            {
                yield return wait;
                done.Clear();
                foreach (var (w, until) in _passing)
                    if (!w || (Time.time >= until && Clear(w))) done.Add(w);
                foreach (var w in done)
                {
                    _passing.Remove(w);
                    if (!w) continue;
                    foreach (var c in _cols)
                        if (c) Physics2D.IgnoreCollision(w, c, false);
                }
            }
            _restore = null;
        }

        private bool Clear(Collider2D who)
        {
            foreach (var c in _cols)
                if (c && c.enabled && who.enabled && c.Distance(who).distance < 0.02f) return false;
            return true;
        }
    }
}
