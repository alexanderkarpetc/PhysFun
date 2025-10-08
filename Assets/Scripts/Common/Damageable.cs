using UnityEngine;

namespace Common
{
    public class Damageable : MonoBehaviour
    {
        [Header("Health")] [SerializeField] private int maxHealth = 100;
        [SerializeField] private LayerMask targetLayers;

        private float _health;

        private void Awake()
        {
            _health = maxHealth;
        }

        // if (_lastHitTime.TryGetValue(c.collider, out var t) && Time.time - t < perTargetCooldown) return;
        // _lastHitTime[c.collider] = Time.time;

        private void OnCollisionEnter2D(Collision2D c)
        {
            // check layer
            if ((targetLayers.value & (1 << c.collider.gameObject.layer)) == 0)
                return;
            
            var playerRb = GetComponent<Rigidbody2D>();
            float relSpeed = c.relativeVelocity.magnitude - playerRb.linearVelocity.magnitude; // will calculate how fast other object hit us
            // todo we shouldn't subtract player's speed, because if player has speed it can be withdrawn twice
            
            if (relSpeed < 2f) return; // too slow
            // if (c.rigidbody.linearVelocity.magnitude < 2f) return; // not needed but leave
            
            var playerIsBelow = c.transform.position.y > transform.position.y;

            var damage = DamageManager.CalculateImpactDamage(
                relSpeed,
                c.rigidbody.mass,
                playerIsBelow
            );
            ApplyDamage(damage);
            App.Instance.Hud.DamageHud.ShowDamage(c.transform.position, damage);
        }


        public void ApplyDamage(int amount)
        {
            _health -= amount;

            if (_health <= 0f)
            {
                Debug.Log("DIed ");
            }
        }

        public void Heal(float amount)
        {
            if (_health <= 0f) return; // dead
            _health = Mathf.Min(_health + amount, maxHealth);
        }
    }
}