using UnityEngine;

namespace Common
{
    /// <summary>
    /// A physical bolt. It carries damage to the first thing it touches and a shove for anything
    /// with a body, so shots read the same way as everything else in a world where nothing is
    /// bolted down. Fire it with <see cref="Fire"/> right after instantiating.
    ///
    /// It moves itself rather than riding a Rigidbody2D. A round is small and fast: at the
    /// physics rate it advances five to fifteen pixels per step, which is wider than the sprite,
    /// and interpolation draws it a further step behind where the solver has it. The result was
    /// a round that vanished several pixels short of what it hit. Sweeping a cast between frames
    /// costs one query, runs at display rate, cannot tunnel at any speed, and hands back the
    /// exact contact point to put the impact on.
    /// </summary>
    public sealed class Projectile : MonoBehaviour
    {
        [SerializeField] private int damage = 6;

        [Tooltip("Impulse handed to whatever it hits, and to the corpse if the hit kills.")]
        [SerializeField] private float impactImpulse = 0.6f;

        [SerializeField] private float lifetime = 3f;

        [Tooltip("Pull on the round, as a multiple of world gravity. 0 flies straight.")]
        [SerializeField] private float gravityScale;

        [Tooltip("Radius of the sweep. Taken from a CircleCollider2D when there is one.")]
        [SerializeField] private float radius = 0.035f;

        [Tooltip("What it can hit.")]
        [SerializeField] private LayerMask hitMask = ~0;

        [Tooltip("Point the sprite along the direction of travel.")]
        [SerializeField] private bool faceVelocity = true;

        [Header("Impact")]
        [Tooltip("One white pixel, tinted per hit. Leave empty for no burst.")]
        [SerializeField] private Sprite burstPixel;

        [SerializeField] private Color bloodColor = new(0.62f, 0.05f, 0.08f, 1f);
        [SerializeField] private Color debrisColor = new(0.45f, 0.44f, 0.42f, 1f);

        [Tooltip("How long the spent round sits on the contact point before it goes. Without " +
                 "this the frame where it touches is never drawn, and the hit reads as a miss.")]
        [SerializeField] private float linger = 0.05f;

        private Vector2 _velocity;
        private Transform _owner;
        private float _age;
        private bool _spent;

        private void Awake()
        {
            // The body and collider are along for authoring convenience; motion and hits are
            // ours, so keep the solver from moving the round behind our back.
            var rb = GetComponent<Rigidbody2D>();
            if (rb) rb.simulated = false;

            var circle = GetComponent<CircleCollider2D>();
            if (circle)
            {
                radius = circle.radius;
                circle.enabled = false;
            }
        }

        /// <summary>Launch it. <paramref name="dmg"/> below zero keeps the prefab value.</summary>
        public void Fire(Vector2 velocity, GameObject owner, int dmg = -1)
        {
            if (dmg >= 0) damage = dmg;
            Launch(velocity, owner);
        }

        /// <summary>
        /// Launch a round a weapon configured: its own look, its own damage, and its own pull
        /// towards the ground. One prefab covers every gun that way, and how far a shot drops
        /// on the way is a property of the gun rather than of the prefab it came out of.
        /// </summary>
        public void Fire(Vector2 velocity, GameObject owner, float dmg, float gravity,
                         Sprite look, float impulse = -1f, float life = -1f)
        {
            damage = Mathf.Max(1, Mathf.RoundToInt(dmg));
            gravityScale = gravity;
            if (impulse >= 0f) impactImpulse = impulse;
            if (life > 0f) lifetime = life;

            if (look)
            {
                var sr = GetComponent<SpriteRenderer>();
                if (sr) sr.sprite = look;
            }

            Launch(velocity, owner);
        }

        private void Launch(Vector2 velocity, GameObject owner)
        {
            _velocity = velocity;
            _owner = owner ? owner.transform : null;
            Aim(velocity);
        }

        private void Update()
        {
            if (_spent) return;

            float dt = Time.deltaTime;
            _age += dt;
            if (_age >= lifetime)
            {
                Destroy(gameObject);
                return;
            }

            _velocity += Physics2D.gravity * (gravityScale * dt);

            Vector2 from = transform.position;
            Vector2 step = _velocity * dt;
            float distance = step.magnitude;

            if (distance > 0.0001f && Sweep(from, step / distance, distance, out RaycastHit2D hit))
            {
                Land(hit);
                return;
            }

            transform.position = from + step;
            if (faceVelocity) Aim(_velocity);
        }

        /// <summary>First thing along the step that is not whoever fired it.</summary>
        private bool Sweep(Vector2 from, Vector2 dir, float distance, out RaycastHit2D hit)
        {
            hit = default;

            // Non-alloc would need a scratch buffer per projectile; a hit is rare enough that
            // the allocation only happens on the frame something is actually in the way.
            RaycastHit2D[] all = Physics2D.CircleCastAll(from, radius, dir, distance, hitMask);
            float best = float.MaxValue;

            foreach (var h in all)
            {
                if (!h.collider || h.collider.isTrigger) continue;
                if (_owner && h.collider.transform.IsChildOf(_owner)) continue;
                if (h.distance >= best) continue;
                best = h.distance;
                hit = h;
            }

            return hit.collider;
        }

        private void Land(RaycastHit2D hit)
        {
            _spent = true;
            _velocity = Vector2.zero;

            Vector2 point = hit.point;
            Vector2 dir = transform.right;

            // Sit the round on the surface for a moment so the frame it touches actually gets
            // drawn. Destroying on contact skips it, and the eye reads that as falling short.
            transform.position = point;

            var victim = hit.collider.GetComponentInParent<Damageable>();
            if (victim)
                victim.ApplyDamage(new DamageInfo(
                    damage, DamageType.Projectile, point, dir, dir * impactImpulse, gameObject));

            // Even a miss should push the thing it lands on.
            if (hit.rigidbody)
                hit.rigidbody.AddForceAtPosition(dir * impactImpulse, point, ForceMode2D.Impulse);

            ImpactBurst.Spawn(burstPixel, point, dir,
                              victim ? bloodColor : debrisColor,
                              victim ? 10 : 5,
                              victim ? 4f : 2.5f);

            // A round carrying a charge goes off where it stopped rather than just poking a
            // hole in it. Shell, rocket, firebomb — the round is the same one either way, and
            // what it does on arrival is a component on the prefab.
            var charge = GetComponent<Phys.Explosions.Explosive>();
            if (charge) charge.DetonateNow(point);

            Destroy(gameObject, linger);
        }

        private void Aim(Vector2 velocity)
        {
            if (!faceVelocity || velocity.sqrMagnitude < 0.01f) return;
            transform.rotation = Quaternion.Euler(
                0f, 0f, Mathf.Atan2(velocity.y, velocity.x) * Mathf.Rad2Deg);
        }
    }
}
