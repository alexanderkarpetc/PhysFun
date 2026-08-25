using UnityEngine;

namespace Common
{
    /// <summary>
    /// A physical bolt. It carries damage to the first thing it touches and a shove for anything
    /// with a body, so shots read the same way as everything else in a world where nothing is
    /// bolted down. Fire it with <see cref="Fire"/> right after instantiating.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class Projectile : MonoBehaviour
    {
        [SerializeField] private int damage = 6;
        [Tooltip("Impulse handed to whatever it hits, and to the corpse if the hit kills.")]
        [SerializeField] private float impactImpulse = 0.6f;
        [SerializeField] private float lifetime = 3f;
        [Tooltip("Point the sprite along the direction of travel.")]
        [SerializeField] private bool faceVelocity = true;

        private Rigidbody2D _rb;
        private float _age;
        private bool _spent;

        private void Awake()
        {
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
        }

        /// <summary>Launch it. <paramref name="dmg"/> below zero keeps the prefab value.</summary>
        public void Fire(Vector2 velocity, GameObject owner, int dmg = -1)
        {
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
            if (dmg >= 0) damage = dmg;

            _rb.linearVelocity = velocity;
            Aim(velocity);

            // Whoever fired it must never eat their own shot, whatever layer they are on.
            if (!owner) return;
            var mine = GetComponent<Collider2D>();
            if (!mine) return;
            foreach (var theirs in owner.GetComponentsInChildren<Collider2D>())
                if (theirs) Physics2D.IgnoreCollision(mine, theirs, true);
        }

        private void Update()
        {
            _age += Time.deltaTime;
            if (_age >= lifetime)
            {
                Destroy(gameObject);
                return;
            }

            if (faceVelocity) Aim(_rb.linearVelocity);
        }

        private void Aim(Vector2 velocity)
        {
            if (!faceVelocity || velocity.sqrMagnitude < 0.01f) return;
            transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(velocity.y, velocity.x) * Mathf.Rad2Deg);
        }

        private void OnCollisionEnter2D(Collision2D c)
        {
            if (_spent) return;
            _spent = true;

            Vector2 point = c.contactCount > 0 ? c.GetContact(0).point : (Vector2)transform.position;
            Vector2 dir = _rb.linearVelocity.sqrMagnitude > 0.01f
                ? _rb.linearVelocity.normalized
                : (Vector2)transform.right;

            // The floating number and the camera kick are the victim's business, not ours.
            var victim = c.collider.GetComponentInParent<Damageable>();
            if (victim)
                victim.ApplyDamage(new DamageInfo(
                    damage, DamageType.Projectile, point, dir, dir * impactImpulse, gameObject));

            // Even a miss should push the thing it lands on.
            if (c.rigidbody) c.rigidbody.AddForceAtPosition(dir * impactImpulse, point, ForceMode2D.Impulse);

            Destroy(gameObject);
        }
    }
}
