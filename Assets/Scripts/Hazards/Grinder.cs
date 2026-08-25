using System.Collections.Generic;
using Common;
using UnityEngine;

namespace Hazards
{
    /// <summary>
    /// A driven wheel that hurts what it touches — the gears at the bottom of the pit.
    ///
    /// Kinematic on purpose: nothing it catches can slow it down, and the solver still throws
    /// bodies off its teeth for free, so most of what the thing looks like it is doing costs no
    /// code at all. Damage is charged for time spent in contact rather than for the moment of
    /// contact, because a gear is not an impact — it is a surface moving past you — which is why
    /// it does not go through <see cref="ImpactSolver"/>: that model projects everything onto the
    /// contact normal, and a wheel does its work along the tangent.
    ///
    /// It does not destroy what it grinds. Bodies come out whole and get thrown around.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    [AddComponentMenu("PhysFun/Grinder")]
    public sealed class Grinder : MonoBehaviour
    {
        [Tooltip("Degrees per second. The sign picks the direction.")]
        [SerializeField] private float spin = 200f;

        [Tooltip("Damage per second of contact.")]
        [SerializeField] private float damagePerSecond = 45f;

        [Tooltip("How often damage is banked and shown, in seconds. Readability only — the rate " +
                 "is the same either way. 0 pays out every physics step.")]
        [SerializeField] private float tickInterval = 0.2f;

        [Tooltip("Impulse handed to a corpse when the gear lands the killing blow, thrown the way " +
                 "the teeth were travelling.")]
        [SerializeField] private float fling = 2f;

        private Rigidbody2D _rb;

        // Damage owed to each thing currently in contact. Kept per victim so two creatures caught
        // at once are billed separately rather than sharing one timer.
        private readonly Dictionary<Damageable, Bite> _biting = new();
        private static readonly List<Damageable> PruneBuf = new();

        private struct Bite
        {
            public float Debt;
            public float Timer;
            public Vector2 Point;
        }

        /// <summary>Degrees per second, signed.</summary>
        public float Spin => spin;

        private void Reset()
        {
            // Authored rather than enforced, so the prefab carries a body that is already right.
            var rb = GetComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Kinematic;
            rb.gravityScale = 0f;
        }

        private void Awake()
        {
            _rb = GetComponent<Rigidbody2D>();
            _rb.bodyType = RigidbodyType2D.Kinematic;
            _rb.angularVelocity = spin;
        }

        private void OnValidate()
        {
            if (Application.isPlaying && _rb) _rb.angularVelocity = spin;
        }

        private void OnCollisionStay2D(Collision2D c)
        {
            var victim = c.collider.GetComponentInParent<Damageable>();
            if (!victim || victim.IsDead) return;

            _biting.TryGetValue(victim, out var bite);
            bite.Debt += damagePerSecond * Time.fixedDeltaTime;
            bite.Timer += Time.fixedDeltaTime;
            if (c.contactCount > 0) bite.Point = c.GetContact(0).point;

            if (bite.Timer >= tickInterval)
            {
                Vector2 tangent = Tangent(bite.Point);
                victim.ApplyDamage(new DamageInfo(
                    bite.Debt, DamageType.Grind, bite.Point, tangent, tangent * fling, gameObject));

                bite.Debt = 0f;
                bite.Timer = 0f;

                // The killing blow replaces the creature with a corpse, and a corpse is not the
                // gear's business any more.
                if (victim.IsDead) { _biting.Remove(victim); return; }
            }

            _biting[victim] = bite;
        }

        private void OnCollisionExit2D(Collision2D c)
        {
            var victim = c.collider.GetComponentInParent<Damageable>();
            if (victim) _biting.Remove(victim);

            // Corpses and burnt props leave dead keys behind; sweep once the table is worth it.
            if (_biting.Count > 8) Prune();
        }

        private void Prune()
        {
            PruneBuf.Clear();
            foreach (var pair in _biting)
                if (!pair.Key || pair.Key.IsDead) PruneBuf.Add(pair.Key);
            foreach (var key in PruneBuf) _biting.Remove(key);
            PruneBuf.Clear();
        }

        /// <summary>Which way the teeth are moving where they are touching.</summary>
        private Vector2 Tangent(Vector2 point)
        {
            Vector2 arm = point - (Vector2)transform.position;
            if (arm.sqrMagnitude < 1e-6f) return Vector2.zero;
            return new Vector2(-arm.y, arm.x).normalized * Mathf.Sign(spin);
        }
    }
}
