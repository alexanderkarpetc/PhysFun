using Materials;
using UnityEngine;

namespace Phys.Electricity
{
    /// <summary>
    /// A source that discharges on its own: every so often it throws a bolt from its tip to the
    /// nearest thing that conducts, and the strike runs from there the way any strike does -
    /// through every touching conductor, into whoever is leaning on one. The Tesla coil in the
    /// Coil Dome (S03) is one.
    ///
    /// Only metal draws it. Nothing in range that conducts: it waits and tries again, so a room
    /// with the metal knocked out of reach goes quiet - which is the point of standing on wood.
    /// </summary>
    public sealed class ArcEmitter : MonoBehaviour
    {
        [Tooltip("Where the bolts leave from, local to this object.")]
        [SerializeField] private Vector2 _tip = new(0f, 1.4f);
        [Tooltip("How far it reaches for a conductor, world units.")]
        [SerializeField] private float _range = 6f;
        [Tooltip("Seconds between discharges, picked between these two.")]
        [SerializeField] private Vector2 _interval = new(1.2f, 2.6f);
        [SerializeField] private ElectricityProfile _profile = new();

        private static readonly Collider2D[] Hits = new Collider2D[128];
        private float _next;

        public Vector2 Tip => transform.TransformPoint(_tip);

        private void OnEnable() => _next = Time.time + Random.Range(_interval.x, _interval.y);

        private void Update()
        {
            if (Time.time < _next) return;
            _next = Time.time + Random.Range(_interval.x, _interval.y);
            Fire();
        }

        /// <summary>One bolt now, at whatever conducts nearest the tip. False if nothing does.</summary>
        public bool Fire()
        {
            var tip = Tip;
            var filter = new ContactFilter2D { useTriggers = false };
            filter.SetLayerMask(_profile.affects);
            int count = Physics2D.OverlapCircle(tip, _range, filter, Hits);

            float best = float.MaxValue;
            Vector2 target = default;
            for (int i = 0; i < count; i++)
            {
                var col = Hits[i];
                if (!col || col.transform.IsChildOf(transform)) continue;
                if (!MaterialLibrary.Of(col.gameObject).Conducts) continue;
                var p = col.ClosestPoint(tip);
                float d = (p - tip).sqrMagnitude;
                if (d < best)
                {
                    best = d;
                    target = p;
                }
            }
            if (best == float.MaxValue) return false;

            ElectricitySystem.Strike(target, _profile, gameObject, tip);
            return true;
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.47f, 0.79f, 0.84f);
            Gizmos.DrawWireSphere(transform.TransformPoint(_tip), _range);
        }
#endif
    }
}
