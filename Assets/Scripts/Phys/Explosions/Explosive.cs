using Common;
using UnityEngine;
using CrackerService = Cracker.Cracker;

namespace Phys.Explosions
{
    /// <summary>
    /// A thing that goes off. Put it on a barrel, a crate of shells, a grenade or the shell
    /// itself, tell it what sets it off, and it hands the rest to <see cref="Explosion"/>.
    ///
    /// Everything here is about the moment before the blast rather than the blast: what sets it
    /// off, and what is left of the object afterwards.
    ///
    /// A lit fuse is not among those things — that is <see cref="FuseCord"/>, a separate object
    /// laid in the scene and pointed at this one. An explosive is then only ever as complicated
    /// as it needs to be: bare, it goes off when it is shot or caught in a blast; with a cord
    /// run to it, it is something you can light from across the room. The <see cref="delay"/>
    /// here is a plain timer, for a charge that carries its own clock rather than a cord.
    /// </summary>
    [AddComponentMenu("PhysFun/Explosive")]
    public sealed class Explosive : MonoBehaviour
    {
        public enum Trigger
        {
            /// <summary>Nothing sets it off but code — <see cref="DetonateNow"/>.</summary>
            Manual,

            /// <summary>Counts <see cref="delay"/> down from the moment it exists. A thrown grenade.</summary>
            Timer,

            /// <summary>When its <see cref="Damageable"/> runs out of health.</summary>
            OnDeath,

            /// <summary>When one hit worth more than <see cref="damageToSetOff"/> lands.</summary>
            OnDamage,

            /// <summary>On touching anything hard enough. A shell that arms on contact.</summary>
            OnImpact,
        }

        [Header("Blast")]
        [Tooltip("Shared profile. Leave empty to use the one below — fill it in when several " +
                 "prefabs should go off the same way and be retuned from one place.")]
        [SerializeField] private ExplosionConfig config;

        [SerializeField] private ExplosionProfile profile = ExplosionProfile.Barrel();

        [Header("Trigger")]
        [SerializeField] private Trigger trigger = Trigger.OnDeath;

        [Tooltip("Seconds between being set off and going off. A cord run to this explosive " +
                 "supplies its own timing and ignores this.")]
        [SerializeField] private float delay = 0.6f;

        [Tooltip("OnDamage: how big one hit has to be. OnImpact: how hard the contact has to be.")]
        [SerializeField] private float damageToSetOff = 15f;

        [Tooltip("Off makes it deaf to other explosions, so it can sit inside a blast without " +
                 "joining in.")]
        [SerializeField] private bool chainable = true;

        [Header("Afterwards")]
        [Tooltip("Pieces the object itself comes apart into. 0 = it just disappears.")]
        [Range(0, 24)] [SerializeField] private int selfShards = 7;

        [Tooltip("How hard its own pieces are thrown.")]
        [SerializeField] private float selfShardImpulse = 5f;

        [Tooltip("Off leaves the object standing, blast and all. For a vent, a geyser, anything " +
                 "that goes off more than once.")]
        [SerializeField] private bool consumedByBlast = true;

        // Serialized so that it survives Instantiate: Cracker reuses this object as the largest
        // shard and clones the rest from it, and a shard of a spent barrel must not be a live one.
        [HideInInspector] [SerializeField] private bool spent;

        private Damageable _damageable;
        private float _timer = -1f;

        /// <summary>The blast this will produce.</summary>
        public ExplosionProfile Profile => config ? config.profile : profile;

        /// <summary>True between being set off and going off.</summary>
        public bool IsArmed => _timer >= 0f && !spent;

        private void Awake()
        {
            _damageable = GetComponentInParent<Damageable>();

            if (_damageable)
            {
                _damageable.Died += OnDied;
                _damageable.Damaged += OnDamaged;
            }
        }

        private void OnDestroy()
        {
            if (!_damageable) return;
            _damageable.Died -= OnDied;
            _damageable.Damaged -= OnDamaged;
        }

        private void Start()
        {
            if (trigger == Trigger.Timer) Arm(delay);
        }

        // ── being set off ─────────────────────────────────────────────────────

        /// <summary>Start the countdown. A shorter one wins; a longer one is ignored, so nothing
        /// can push back a blast that is already closer than it is.</summary>
        public void Arm(float seconds)
        {
            if (spent) return;
            if (_timer >= 0f && _timer <= seconds) return;
            _timer = Mathf.Max(0f, seconds);
        }

        /// <summary>Caught in someone else's blast.</summary>
        public void Chain(float seconds)
        {
            if (chainable) Arm(seconds);
        }

        /// <summary>Go off now, countdown or not. This is what a burnt-through fuse calls.</summary>
        public void DetonateNow() => Detonate(transform.position);

        /// <summary>Go off somewhere other than where the object sits — the contact point of a
        /// shell, rather than the middle of the sprite that carried it.</summary>
        public void DetonateNow(Vector2 at) => Detonate(at);

        private void OnDied(DamageInfo info)
        {
            if (trigger == Trigger.OnDeath) Arm(delay);
        }

        private void OnDamaged(DamageInfo info)
        {
            // A blast next door reaches this through the chain query, but a blast that damaged
            // it and is not in chain range still counts: being hit by an explosion is as good a
            // reason to go off as being near one.
            if (chainable && info.Type == DamageType.Explosion)
            {
                Arm(Profile.chainDelay);
                return;
            }

            if (trigger == Trigger.OnDamage && info.Amount >= damageToSetOff) Arm(delay);
        }

        private void OnCollisionEnter2D(Collision2D c)
        {
            if (trigger != Trigger.OnImpact || spent) return;

            // Same currency as damageToSetOff in the OnDamage case: how hard it was hit, which
            // for a contact is the impulse the solver had to apply to stop it.
            float impulse = 0f;
            for (int i = 0; i < c.contactCount; i++) impulse += c.GetContact(i).normalImpulse;
            if (impulse >= damageToSetOff) Arm(delay);
        }

        // ── the countdown ─────────────────────────────────────────────────────

        private void Update()
        {
            if (spent || _timer < 0f) return;

            _timer -= Time.deltaTime;
            if (_timer <= 0f) Detonate(transform.position);
        }

        // ── the blast ─────────────────────────────────────────────────────────

        private void Detonate(Vector2 at)
        {
            if (spent) return;
            spent = true;
            _timer = -1f;

            Explosion.Detonate(at, Profile, gameObject);

            if (!consumedByBlast)
            {
                spent = false;
                return;
            }

            // Any cord run to this one has done its job — and Cracker clones this object into
            // its own shards, so a live fuse left on it would come away on every piece.
            foreach (var cord in GetComponentsInChildren<FuseCord>(true)) cord.Snuff();

            // Cracker keeps this object as the largest piece and clones the rest off it, so the
            // object is gone either way — as a handful of debris, or outright.
            if (selfShards > 1)
                CrackerService.Crack(gameObject, selfShards, minPixels: 8, simplifyLevel: 2,
                                     impactWorld: (Vector3)at, impactImpulse: selfShardImpulse,
                                     impactFalloff: Mathf.Max(0.25f, Profile.radius * 0.5f));
            else
                Destroy(gameObject);
        }

        private void OnDrawGizmosSelected()
        {
            var p = Profile;
            if (p == null) return;

            Vector3 at = transform.position;

            Gizmos.color = new Color(1f, 0.4f, 0.1f, 0.9f);
            Gizmos.DrawWireSphere(at, p.radius);

            Gizmos.color = new Color(1f, 0.85f, 0.3f, 0.9f);
            Gizmos.DrawWireSphere(at, p.innerRadius);

            if (p.carveRadius > 0f)
            {
                Gizmos.color = new Color(0.6f, 0.6f, 0.6f, 0.8f);
                Gizmos.DrawWireSphere(at, p.carveRadius);
            }

            if (p.ignites)
            {
                Gizmos.color = new Color(1f, 0.2f, 0.05f, 0.5f);
                Gizmos.DrawWireSphere(at, p.igniteRadius);
            }

            if (p.chainRadius > 0f)
            {
                Gizmos.color = new Color(0.3f, 0.7f, 1f, 0.4f);
                Gizmos.DrawWireSphere(at, p.chainRadius);
            }
        }
    }
}
