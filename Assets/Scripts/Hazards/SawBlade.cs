using System.Collections.Generic;
using Common;
using Materials;
using Phys.Pixels;
using UnityEngine;

namespace Hazards
{
    /// <summary>
    /// A spinning blade that cuts: the swing saw in the Sawpit (S05). Side-on, the blade is in
    /// the plane of the world, so whatever wood its disc overlaps is gone - a log it passes
    /// through comes apart in two along the cut (the pixel split does that), a crate loses the
    /// corner it caught. Anything that can be hurt in the disc is ground like a gear grinds,
    /// by the time it spends in there.
    ///
    /// It eats loose bodies only (props, logs, crates). Terrain is many materials to a chunk,
    /// so carving it here would take the rock with the timber; the rooms keep their timber
    /// stock that the saw is meant to reach as props for that reason.
    ///
    /// Spin comes from whatever drives the blade (a motored hinge on its arbour); this only
    /// cuts. The collider is best a trigger, so the blade goes through the stock rather than
    /// shoving it down the room ahead of itself.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class SawBlade : MonoBehaviour
    {
        [Tooltip("Reach of the teeth from the centre, world units.")]
        [SerializeField] private float _radius = 0.9f;
        [Tooltip("Damage per second to something caught in the disc.")]
        [SerializeField] private float _damagePerSecond = 70f;
        [SerializeField] private float _tickInterval = 0.2f;
        [Tooltip("Impulse handed along the teeth to whatever it hurts.")]
        [SerializeField] private float _fling = 3f;

        private static readonly Collider2D[] Hits = new Collider2D[32];
        private readonly Dictionary<Damageable, float> _debt = new();
        private readonly HashSet<Damageable> _seen = new();
        private readonly HashSet<GameObject> _cut = new();
        private Rigidbody2D _rb;
        private float _tick;

        private void Awake() => _rb = GetComponent<Rigidbody2D>();

        private void FixedUpdate()
        {
            Vector2 c = transform.position;
            int n = Physics2D.OverlapCircleNonAlloc(c, _radius, Hits);
            float dt = Time.fixedDeltaTime;
            _tick += dt;
            bool pay = _tick >= _tickInterval;
            _seen.Clear();
            _cut.Clear();

            for (int i = 0; i < n; i++)
            {
                var col = Hits[i];
                if (!col || col.attachedRigidbody == _rb) continue;

                var victim = col.GetComponentInParent<Damageable>();
                if (victim && !victim.IsDead)
                {
                    if (_seen.Add(victim))
                    {
                        _debt.TryGetValue(victim, out float d);
                        _debt[victim] = d + _damagePerSecond * dt;
                    }
                    continue;
                }

                // wood, loose: carve the disc out of it
                var body = col.attachedRigidbody;
                if (!body || body.bodyType != RigidbodyType2D.Dynamic) continue;
                var go = body.gameObject;
                if (!_cut.Add(go)) continue;
                if (MaterialLibrary.Of(go).Id != PhysMaterialId.Wood) continue;
                SpriteEraseService.EraseCircle(go, c, _radius);
            }

            if (!pay) return;
            _tick = 0f;
            var keys = new List<Damageable>(_debt.Keys);
            foreach (var v in keys)
            {
                if (!v || v.IsDead || !_seen.Contains(v)) { _debt.Remove(v); continue; }
                Vector2 at = v.transform.position;
                Vector2 arm = at - c;
                Vector2 tangent = arm.sqrMagnitude > 1e-6f
                    ? new Vector2(-arm.y, arm.x).normalized * Mathf.Sign(_rb.angularVelocity == 0f ? 1f : _rb.angularVelocity)
                    : Vector2.up;
                v.ApplyDamage(new DamageInfo(_debt[v], DamageType.Grind, at, tangent, tangent * _fling, gameObject));
                _debt[v] = 0f;
            }
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.9f, 0.4f, 0.3f);
            Gizmos.DrawWireSphere(transform.position, _radius);
        }
#endif
    }
}
