using System.Collections.Generic;
using Binny;
using Common;
using UnityEngine;

namespace Enemy
{
    /// <summary>
    /// A ghost: a flier with no gravity that hunts the player around the rock rather than through
    /// it. It hovers until it sees the player (or is hurt), then flies at them along a path from
    /// the same lazy A* Binny uses, re-planned every few tenths of a second so falling rock and
    /// opened doors are taken into account as they happen. It keeps chasing for a few seconds
    /// after losing sight, to the last place it saw them.
    ///
    /// In range it attacks: a short wind-up, then either a lunge that hurts and shoves whatever
    /// it reaches, or a bolt for the ones that spit. The body is a normal dynamic Rigidbody2D
    /// with gravity off, so the world's impacts hurt it like anything else.
    ///
    /// No ragdoll - a ghost has nothing to fall over with. When <see cref="Damageable"/> says it
    /// died it plays Death, stops being solid, and is gone when the clip has run.
    ///
    /// Animator triggers: Idle (hovering), Walk (flying), Shoot (the attack), Death.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class GhostController : MonoBehaviour
    {
        public enum AttackKind { Lunge, Bolt }

        [Header("Refs")]
        [Tooltip("The art, flipped to face; usually the View child.")]
        [SerializeField] private Transform _body;
        [SerializeField] private Rigidbody2D _rb;
        [SerializeField] private Animator _animator;
        [SerializeField] private Collider2D _hull;

        [Header("Senses")]
        [SerializeField] private float _sightRange = 12f;
        [Tooltip("Seconds it keeps hunting after losing sight of the player.")]
        [SerializeField] private float _memory = 3f;
        [Tooltip("What blocks its eye: the world, and the player himself.")]
        [SerializeField] private LayerMask _sightBlockers = (1 << 0) | (1 << 7);

        [Header("Flight")]
        [SerializeField] private float _flySpeed = 2.2f;
        [SerializeField] private float _accel = 8f;
        [Tooltip("How far it drifts up and down while hovering.")]
        [SerializeField] private float _hoverBob = 0.12f;
        [Tooltip("What it cannot fly through. The player and other enemies are not walls.")]
        [SerializeField] private LayerMask _walls = (1 << 0) | (1 << 6);
        [SerializeField] private float _cellSize = 0.5f;
        [SerializeField] private float _replanInterval = 0.4f;
        [SerializeField] private float _planRange = 20f;
        [SerializeField] private int _planBudget = 600;

        [Header("Attack")]
        [SerializeField] private AttackKind _attack = AttackKind.Lunge;
        [Tooltip("Distance to the player at which it starts the attack.")]
        [SerializeField] private float _attackRange = 1.2f;
        [SerializeField] private float _attackCooldown = 1.4f;
        [SerializeField] private float _windup = 0.25f;
        [SerializeField] private int _damage = 8;
        [Tooltip("Impulse handed to the player on a hit.")]
        [SerializeField] private float _knockback = 3f;

        [Header("Lunge")]
        [SerializeField] private float _lungeSpeed = 7f;
        [SerializeField] private float _lungeTime = 0.25f;

        [Header("Bolt")]
        [SerializeField] private Projectile _bolt;
        [SerializeField] private Color _boltColor = Color.white;
        [SerializeField] private float _boltSpeed = 6f;

        [Header("Death")]
        [Tooltip("How long the Death clip is given before the ghost is removed.")]
        [SerializeField] private float _deathTime = 0.38f;

        private static readonly int IdleTrig = Animator.StringToHash("Idle");
        private static readonly int WalkTrig = Animator.StringToHash("Walk");
        private static readonly int ShootTrig = Animator.StringToHash("Shoot");
        private static readonly int DeathTrig = Animator.StringToHash("Death");

        private enum State { Hover, Chase, Windup, Strike, Recover, Dead }

        private State _state = State.Hover;
        private float _timer;
        private float _cooldown;
        private float _lastSeen = -999f;
        private Vector2 _lastPos;
        private bool _sees;

        private Damageable _health;
        private BinnyPathfinder _finder;
        private readonly List<Vector2> _path = new();
        private int _leg;
        private float _planTimer;

        private Vector2 _lungeDir;
        private bool _hitThisLunge;
        private Vector2 _anchor;          // where it hovers from
        private float _phase;

        private void Awake()
        {
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
            if (!_hull) _hull = GetComponent<Collider2D>();
            if (!_body) _body = transform.Find("View") ? transform.Find("View") : transform;
            if (!_animator) _animator = GetComponentInChildren<Animator>();
            _health = GetComponent<Damageable>();
            _phase = Random.value * 10f;
        }

        private void OnEnable()
        {
            if (_health)
            {
                _health.Damaged += OnDamaged;
                _health.Died += OnDied;
            }
        }

        private void OnDisable()
        {
            if (_health)
            {
                _health.Damaged -= OnDamaged;
                _health.Died -= OnDied;
            }
        }

        private void Start()
        {
            _rb.gravityScale = 0f;
            _anchor = _rb.position;

            // The box that must be empty for it to pass: its hull and a skin, so it does not
            // scrape round corners it is about to clip.
            Vector2 size = _hull ? (Vector2)_hull.bounds.size : new Vector2(0.6f, 0.6f);
            _finder = new BinnyPathfinder(_cellSize, size + new Vector2(0.1f, 0.1f), _walls, _planBudget,
                _planRange, transform);

            Play(IdleTrig);
        }

        // ----------------------------------------------------------------------- brain

        private void Update()
        {
            if (_state == State.Dead) return;

            float dt = Time.deltaTime;
            _timer -= dt;
            _cooldown -= dt;

            Sense();
            bool aware = Time.time - _lastSeen < _memory;
            var player = App.Instance.PlayerTransform;
            float dist = player ? Vector2.Distance(Center, player.position) : float.MaxValue;

            switch (_state)
            {
                case State.Hover:
                    if (aware) Enter(State.Chase);
                    break;

                case State.Chase:
                    if (!aware)
                    {
                        _anchor = _rb.position;
                        Enter(State.Hover);
                    }
                    else if (_sees && dist <= _attackRange && _cooldown <= 0f)
                    {
                        Enter(State.Windup);
                    }
                    break;

                case State.Windup:
                    if (_timer > 0f) break;
                    if (_attack == AttackKind.Lunge)
                    {
                        _lungeDir = player ? ((Vector2)player.position - Center).normalized : Facing;
                        _hitThisLunge = false;
                        Enter(State.Strike);
                    }
                    else
                    {
                        if (player) Spit(player.position);
                        Enter(State.Recover);
                    }
                    break;

                case State.Strike:
                    TryHit();
                    if (_timer <= 0f) Enter(State.Recover);
                    break;

                case State.Recover:
                    if (_timer <= 0f)
                    {
                        _cooldown = _attackCooldown;
                        Enter(State.Chase);
                    }
                    break;
            }

            Face(aware && player ? player.position.x - Center.x : _rb.linearVelocity.x);
        }

        private void Enter(State next)
        {
            _state = next;
            switch (next)
            {
                case State.Hover:
                    Play(IdleTrig);
                    break;
                case State.Chase:
                    _planTimer = 0f;
                    Play(WalkTrig);
                    break;
                case State.Windup:
                    _timer = _windup;
                    Play(ShootTrig);
                    break;
                case State.Strike:
                    _timer = _lungeTime;
                    break;
                case State.Recover:
                    _timer = 0.3f;
                    break;
            }
        }

        private void Sense()
        {
            _sees = false;
            var player = App.Instance.PlayerTransform;
            if (!player) return;

            Vector2 from = Center;
            Vector2 to = player.position;
            Vector2 d = to - from;
            float dist = d.magnitude;
            if (dist > _sightRange || dist < 1e-4f) return;

            var hit = Physics2D.Raycast(from, d / dist, dist, _sightBlockers);
            if (hit.collider && hit.collider.gameObject != App.Instance.PlayerGo &&
                !hit.collider.transform.IsChildOf(player)) return;

            _sees = true;
            _lastSeen = Time.time;
            _lastPos = to;
        }

        private void OnDamaged(DamageInfo info)
        {
            // Being hurt is as good as seeing who did it.
            _lastSeen = Time.time;
            if (App.Instance.PlayerTransform) _lastPos = App.Instance.PlayerTransform.position;
        }

        private void OnDied(DamageInfo info)
        {
            _state = State.Dead;
            Play(DeathTrig);
            _rb.linearVelocity = Vector2.zero;
            _rb.simulated = false;
            if (_hull) _hull.enabled = false;
            Destroy(gameObject, _deathTime);
        }

        // ----------------------------------------------------------------------- attack

        private void TryHit()
        {
            if (_hitThisLunge) return;
            var go = App.Instance.PlayerGo;
            if (!go || !_hull) return;

            var target = go.GetComponentInChildren<Collider2D>();
            if (!target) return;
            if (_hull.Distance(target).distance > 0.08f) return;

            _hitThisLunge = true;
            var victim = go.GetComponent<Damageable>();
            Vector2 dir = _lungeDir.sqrMagnitude > 0f ? _lungeDir : Facing;
            if (victim)
                victim.ApplyDamage(new DamageInfo(_damage, DamageType.Melee, target.bounds.center, dir,
                    dir * _knockback, gameObject));

            var body = go.GetComponent<Rigidbody2D>();
            if (body) body.AddForce(dir * _knockback, ForceMode2D.Impulse);
        }

        private void Spit(Vector2 target)
        {
            if (!_bolt) return;
            Vector2 origin = Center + Facing * (_hull ? _hull.bounds.extents.x : 0.3f);
            Vector2 dir = target - origin;
            if (dir.sqrMagnitude < 1e-4f) return;

            var bolt = Instantiate(_bolt, origin, Quaternion.identity);
            var look = bolt.GetComponent<SpriteRenderer>();
            if (look) look.color = _boltColor;
            bolt.Fire(dir.normalized * _boltSpeed, gameObject, _damage);
        }

        // ----------------------------------------------------------------------- flight

        private void FixedUpdate()
        {
            if (_state == State.Dead) return;
            float dt = Time.fixedDeltaTime;
            Vector2 want;

            switch (_state)
            {
                case State.Strike:
                    _rb.linearVelocity = _lungeDir * _lungeSpeed;
                    return;

                case State.Chase:
                    want = Steer(dt);
                    break;

                case State.Windup:
                    // A small draw back before it goes, so the lunge reads.
                    want = -Facing * 0.6f;
                    break;

                case State.Hover:
                    _phase += dt;
                    float y = _anchor.y + Mathf.Sin(_phase * 2f) * _hoverBob;
                    want = new Vector2(_anchor.x - _rb.position.x, y - _rb.position.y) * 3f;
                    break;

                default:
                    want = Vector2.zero;
                    break;
            }

            _rb.linearVelocity = Vector2.MoveTowards(_rb.linearVelocity, want, _accel * dt);
        }

        /// <summary>Velocity toward the next point of the current path, re-planned on a timer.</summary>
        private Vector2 Steer(float dt)
        {
            Vector2 goal = _lastPos;

            // Spitters hold off at their range rather than flying into the player's face.
            if (_attack == AttackKind.Bolt && _sees && Vector2.Distance(Center, goal) < _attackRange * 0.8f)
                return Vector2.zero;

            // Planned from the middle of the hull, not the root: the root is the sprite's feet,
            // and the clearance box the search tests has to sit where the body actually is.
            _planTimer -= dt;
            if (_planTimer <= 0f || _leg >= _path.Count)
            {
                _planTimer = _replanInterval;
                _finder.TryFind(Center, goal, _path);
                _leg = 1;
            }

            if (_leg >= _path.Count) return Vector2.zero;

            Vector2 to = _path[_leg] - Center;
            if (to.magnitude < _cellSize * 0.6f && _leg < _path.Count - 1)
            {
                _leg++;
                to = _path[_leg] - Center;
            }

            return to.sqrMagnitude > 1e-4f ? to.normalized * _flySpeed : Vector2.zero;
        }

        // ----------------------------------------------------------------------- helpers

        private Vector2 Center => _hull ? (Vector2)_hull.bounds.center : _rb.position;

        private Vector2 Facing => new(Mathf.Sign(_body.localScale.x), 0f);

        private void Face(float dx)
        {
            if (Mathf.Abs(dx) < 0.05f) return;
            var s = _body.localScale;
            s.x = dx > 0f ? 1f : -1f;
            _body.localScale = s;
        }

        private void Play(int trigger)
        {
            if (!_animator) return;
            _animator.ResetTrigger(IdleTrig);
            _animator.ResetTrigger(WalkTrig);
            _animator.ResetTrigger(ShootTrig);
            _animator.ResetTrigger(DeathTrig);
            _animator.SetTrigger(trigger);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, _sightRange);
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(transform.position, _attackRange);
            Gizmos.color = Color.cyan;
            for (int i = 1; i < _path.Count; i++) Gizmos.DrawLine(_path[i - 1], _path[i]);
        }
    }
}
