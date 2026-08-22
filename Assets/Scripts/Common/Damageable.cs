using UnityEngine;

namespace Common
{
    public class Damageable : MonoBehaviour
    {
        [Header("Health")] [SerializeField] private int maxHealth = 100;
        [SerializeField] private LayerMask targetLayers;

        [Tooltip("How much of the killing blow's momentum is handed to the ragdoll.")]
        [SerializeField] private float deathKick = 0.05f;

        private float _health;
        private bool _dead;
        private Rigidbody2D _rb;

        private void Awake()
        {
            _health = maxHealth;
            _rb = GetComponent<Rigidbody2D>();
        }

        // if (_lastHitTime.TryGetValue(c.collider, out var t) && Time.time - t < perTargetCooldown) return;
        // _lastHitTime[c.collider] = Time.time;

        private void OnCollisionEnter2D(Collision2D c)
        {
            // check layer
            if ((targetLayers.value & (1 << c.collider.gameObject.layer)) == 0)
                return;

            // Static colliders carry no rigidbody — nothing to weigh the impact by.
            if (c.rigidbody == null || _rb == null) return;

            float relSpeed = c.relativeVelocity.magnitude - _rb.linearVelocity.magnitude; // will calculate how fast other object hit us
            // todo we shouldn't subtract player's speed, because if player has speed it can be withdrawn twice
            
            if (relSpeed < 2f) return; // too slow
            // if (c.rigidbody.linearVelocity.magnitude < 2f) return; // not needed but leave
            
            var playerIsBelow = c.transform.position.y > transform.position.y;

            var damage = DamageManager.CalculateImpactDamage(
                relSpeed,
                c.rigidbody.mass,
                playerIsBelow
            );
            // Send the corpse the way the thing that hit it was going.
            Vector2 impulse = c.rigidbody.linearVelocity.normalized * (c.rigidbody.mass * relSpeed * deathKick);
            Vector2 hitPoint = c.contactCount > 0 ? c.GetContact(0).point : (Vector2)c.transform.position;

            ApplyDamage(damage, impulse, hitPoint);
            if (App.Instance.Hud.DamageHud != null)
                App.Instance.Hud.DamageHud.ShowDamage(c.transform.position, damage);
        }


        public void ApplyDamage(int amount) => ApplyDamage(amount, Vector2.zero, transform.position);

        public void ApplyDamage(int amount, Vector2 impulse, Vector2 hitPoint)
        {
            if (_dead) return;

            _health -= amount;
            if (_health > 0f) return;

            _dead = true;
            Die(impulse, hitPoint);
        }

        /// <summary>Hand over to the corpse when this thing has one; otherwise it just stops here.</summary>
        private void Die(Vector2 impulse, Vector2 hitPoint)
        {
            var spawner = GetComponentInChildren<Ragdolls.RagdollSpawner>();
            if (spawner)
            {
                spawner.Spawn(impulse, hitPoint);
                return;
            }

            Debug.Log($"{name} died");
        }

        public void Heal(float amount)
        {
            if (_health <= 0f) return; // dead
            _health = Mathf.Min(_health + amount, maxHealth);
        }
    }
}