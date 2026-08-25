using System.Collections.Generic;
using UnityEngine;

namespace Common
{
    /// <summary>
    /// Health, and the physics that eats into it.
    ///
    /// Nearly all damage in this game comes from the world rather than from weapons, so what this
    /// component mostly watches for is <see cref="DamageType.Impact"/>: something arriving under
    /// its own steam. <see cref="DamageType.Crush"/> — something settling on top and refusing to
    /// leave — is the same idea for loads too slow to register as a hit, and stays off until
    /// <see cref="ImpactDamageConfig.crush"/> says otherwise. Bolts, explosions and anything else
    /// scripted come in through <see cref="ApplyDamage(DamageInfo)"/>.
    ///
    /// All the physics maths lives in <see cref="ImpactSolver"/> and all the balance in
    /// <see cref="ImpactDamageConfig"/>; what is left here is bookkeeping — the per-attacker
    /// cooldown, the crush timer, the floating number and the corpse.
    /// </summary>
    [DisallowMultipleComponent]
    public class Damageable : MonoBehaviour
    {
        [Header("Health")]
        [SerializeField] private int maxHealth = 100;

        [Tooltip("Layers whose bodies can hurt this one by hitting it. Crushing ignores this — " +
                 "anything heavy enough to pin you counts, whatever layer it sits on.")]
        [SerializeField] private LayerMask targetLayers;

        [Tooltip("How much of the killing blow's momentum is handed to the ragdoll.")]
        [SerializeField] private float deathKick = 0.05f;

        [Header("Physics damage")]
        [Tooltip("Balance profile. Leave empty to use the shared one (Resources/ImpactDamage, " +
                 "falling back to code defaults) — only fill it in for something that has to be " +
                 "tougher or softer than the rest of the world.")]
        [SerializeField] private ImpactDamageConfig config;

        [Tooltip("Off makes this body immune to being hit and crushed by the world. Scripted " +
                 "damage still lands.")]
        [SerializeField] private bool takesPhysicsDamage = true;

        [Tooltip("Pop a floating number for every hit that lands.")]
        [SerializeField] private bool showDamageNumbers = true;

        /// <summary>Raised for every hit that lands. Fires before death.</summary>
        public event System.Action<DamageInfo> Damaged;

        /// <summary>Raised once, after the corpse (if any) has been handed over.</summary>
        public event System.Action<DamageInfo> Died;

        private float _health;
        private bool _dead;
        private Rigidbody2D _rb;

        // Our velocity going into the current physics step. By the time a collision callback runs
        // the solver has already changed it, and ImpactSolver needs the pre-impact figure to tell
        // "a rock fell on me" apart from "I fell on a rock".
        private Vector2 _velocityBeforeStep;

        // When each body last landed a hit, so a tumbling plank cannot bill four times on the way
        // past. Keyed per body: two rocks arriving at once should both count.
        private readonly Dictionary<Rigidbody2D, float> _lastHit = new();
        private static readonly List<Rigidbody2D> PruneBuf = new();

        // Crush pressure gathered during the previous physics step. See TickCrush.
        private float _squeezeScalar;
        private Vector2 _squeezeVector;
        private bool _squeezeLive;     // something that can move is doing the pressing
        private float _crushTime;      // seconds of continuous pressure
        private float _crushDebt;      // damage earned but not yet banked
        private float _crushTick;      // seconds since the last banked tick

        public bool IsDead => _dead;
        public float Health => _health;
        public int MaxHealth => maxHealth;
        public float HealthNormalized => maxHealth > 0 ? Mathf.Clamp01(_health / maxHealth) : 0f;

        private ImpactDamageConfig Config => config ? config : ImpactDamageConfig.Shared;

        private void Awake()
        {
            _health = maxHealth;
            _rb = GetComponent<Rigidbody2D>();
        }

        // ------------------------------------------------------------------ physics

        private void OnCollisionEnter2D(Collision2D c)
        {
            if (_dead || !takesPhysicsDamage || !_rb) return;
            if ((targetLayers.value & (1 << c.collider.gameObject.layer)) == 0) return;

            var attacker = c.rigidbody;
            if (!attacker) return;   // geometry with no body of its own carries no momentum to weigh

            var cfg = Config;
            if (OnCooldown(attacker, cfg.hitCooldown)) return;

            var hit = ImpactSolver.Evaluate(c, _rb, _velocityBeforeStep, cfg);
            if (!hit.Landed) return;

            _lastHit[attacker] = Time.time;
            ApplyDamage(hit.ToDamage(attacker.gameObject, deathKick));
        }

        private void OnCollisionStay2D(Collision2D c)
        {
            if (_dead || !takesPhysicsDamage || !_rb || !Config.crush) return;

            // Every contact counts here, whatever layer it is on: the ground holding you up is
            // half of what makes being pinned measurable at all.
            _squeezeLive |= ImpactSolver.AccumulateSqueeze(c, _rb, ref _squeezeScalar, ref _squeezeVector);
        }

        private void FixedUpdate()
        {
            // Collision callbacks run inside the physics step, so what sits in the accumulators
            // now is the previous step's pressure. Read it, then clear for the step ahead.
            TickCrush(Time.fixedDeltaTime);
            _squeezeScalar = 0f;
            _squeezeVector = Vector2.zero;
            _squeezeLive = false;

            // Last thing before the step runs: whatever locomotion and gravity have decided, this
            // is the speed we are carrying into any contact the step is about to produce.
            if (_rb) _velocityBeforeStep = _rb.linearVelocity;
        }

        private void TickCrush(float dt)
        {
            var cfg = Config;
            if (_dead || !takesPhysicsDamage || !cfg.crush || !_rb || dt <= 0f)
            {
                ResetCrush();
                return;
            }

            // The pressure that opposes itself instead of carrying us, in our own body weights so
            // the threshold means the same thing for a 1kg creature and a 20kg player.
            float squeeze = _squeezeScalar - _squeezeVector.magnitude;
            float weight = _rb.mass * Physics2D.gravity.magnitude * dt;
            float load = weight > 0f ? squeeze / weight : 0f;

            if (!_squeezeLive || load < cfg.crushLoad)
            {
                ResetCrush();
                return;
            }

            // A hard landing spikes the solver for a frame or two; that much is free.
            _crushTime += dt;
            if (_crushTime < cfg.crushGrace) return;

            float rate = cfg.crushDamagePerSecond * Mathf.Min(load / cfg.crushLoad, cfg.crushLoadCap);
            _crushDebt += rate * dt;
            _crushTick += dt;
            if (_crushTick < cfg.crushTickInterval) return;

            float amount = _crushDebt;
            _crushDebt = 0f;
            _crushTick = 0f;
            if (amount <= 0f) return;

            if (cfg.logHits)
                Debug.Log($"[Crush] {name}: {amount:F1} at {load:F1}x body weight", this);

            ApplyDamage(new DamageInfo(amount, DamageType.Crush, _rb.worldCenterOfMass));
        }

        private void ResetCrush()
        {
            _crushTime = 0f;
            _crushDebt = 0f;
            _crushTick = 0f;
        }

        private bool OnCooldown(Rigidbody2D attacker, float cooldown)
        {
            if (cooldown <= 0f) return false;
            if (_lastHit.TryGetValue(attacker, out float t) && Time.time - t < cooldown) return true;

            // Bodies come and go constantly here — shards, corpses, burnt props — so the table is
            // swept whenever it grows past a handful of entries.
            if (_lastHit.Count > 8) Prune(cooldown);
            return false;
        }

        private void Prune(float cooldown)
        {
            PruneBuf.Clear();
            foreach (var pair in _lastHit)
                if (!pair.Key || Time.time - pair.Value >= cooldown) PruneBuf.Add(pair.Key);
            foreach (var key in PruneBuf) _lastHit.Remove(key);
            PruneBuf.Clear();
        }

        // ------------------------------------------------------------------ damage

        /// <summary>Scripted damage with no direction to it — traps, events, debug keys.</summary>
        public void ApplyDamage(float amount, DamageType type = DamageType.Melee) =>
            ApplyDamage(new DamageInfo(amount, type, transform.position));

        public void ApplyDamage(DamageInfo info)
        {
            if (_dead || info.Amount <= 0f) return;

            _health -= info.Amount;
            Damaged?.Invoke(info);

            if (showDamageNumbers)
            {
                var hud = App.Instance.Hud.DamageHud;
                if (hud) hud.ShowDamage(info.Point, info.Amount);
            }

            Kick(info.Amount);

            if (_health > 0f) return;

            _dead = true;
            Die(info);
            Died?.Invoke(info);
        }

        public void Heal(float amount)
        {
            if (_dead) return;
            _health = Mathf.Min(_health + amount, maxHealth);
        }

        /// <summary>Getting hurt shakes the view, but only when it is the player being hurt.</summary>
        private void Kick(float amount)
        {
            float scale = Config.cameraShakeScale;
            if (scale <= 0f || amount <= 0f) return;

            var player = App.Instance.PlayerGo;
            if (player && player == gameObject) Siege.CameraShake.Kick(scale * Mathf.Sqrt(amount));
        }

        /// <summary>Hand over to the corpse when this thing has one; otherwise it just stops here.</summary>
        private void Die(DamageInfo info)
        {
            var spawner = GetComponentInChildren<Ragdolls.RagdollSpawner>();
            if (spawner) spawner.Spawn(info.Impulse, info.Point);
        }
    }
}
