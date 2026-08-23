using Common;
using UnityEngine;

namespace Enemy
{
    /// <summary>
    /// Lives up to its name. While it has not noticed anything it wanders about; the moment it
    /// spots the player it turns tail, and it only ever stops to shoot once it has put some room
    /// between them - or when it has run out of floor and has nothing left to lose.
    ///
    /// The code owns the state machine; the animator is a jukebox that plays whatever clip it is
    /// handed. Anything the physics does to this creature (a throw, an explosion, a plank to the
    /// face) wins: while it is off the ground it makes no attempt to steer.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class CowardController : MonoBehaviour
    {
        private enum State { Idle, Patrol, Flee, Shoot, Flinch, Air }

        [Header("Refs")]
        [Tooltip("Visuals to mirror. Negative X scale means facing left.")]
        [SerializeField] private Transform _body;
        [SerializeField] private Rigidbody2D _rb;

        // All on this same object, so there is nothing to author: the animator it drives, the
        // collider the ground/wall/ledge probes are measured off, and the health that makes it
        // panic when something hurts.
        private Animator _animator;
        private Collider2D _hull;
        private Damageable _damageable;

        [Header("Senses")]
        [Tooltip("Eye position relative to the root. X is mirrored with facing.")]
        [SerializeField] private Vector2 _eyeOffset = new(0.1f, 0.42f);
        [SerializeField] private float _sightRange = 11f;
        [SerializeField] private float _fovDegrees = 140f;
        [Tooltip("Anything this close is noticed even from behind - it is a jumpy thing.")]
        [SerializeField] private float _hearRange = 3f;
        [Tooltip("Walls and props that break line of sight. Must NOT contain the player layer.")]
        [SerializeField] private LayerMask _sightBlockers;
        [Tooltip("How long it keeps panicking after losing sight of the player.")]
        [SerializeField] private float _memory = 4f;

        [Header("Wander")]
        [SerializeField] private float _walkSpeed = 1.2f;
        [SerializeField] private Vector2 _idleTime = new(0.7f, 2.2f);
        [SerializeField] private Vector2 _patrolTime = new(1f, 3f);

        [Header("Panic")]
        [SerializeField] private float _runSpeed = 3.4f;
        [Tooltip("Room it wants before it dares turn around and shoot.")]
        [SerializeField] private float _keepAway = 5f;
        [SerializeField] private float _fireRange = 10f;
        [SerializeField] private Vector2 _fireCooldown = new(0.9f, 1.7f);
        [Tooltip("Cornered it fires this often instead - nothing left to lose.")]
        [SerializeField] private float _corneredCooldown = 0.55f;
        [SerializeField] private float _flinchTime = 0.3f;

        [Header("Gun")]
        [SerializeField] private Projectile _bolt;
        [Tooltip("Muzzle relative to the root. X is mirrored with facing.")]
        [SerializeField] private Vector2 _muzzleOffset = new(0.3f, 0.24f);
        [SerializeField] private int _boltDamage = 6;
        [SerializeField] private float _boltSpeed = 13f;
        [Tooltip("Aim error in degrees. Its hands shake.")]
        [SerializeField] private float _spread = 5f;

        [Header("Ground")]
        [Tooltip("Solid ground and walls. Feeds the ground, wall and ledge probes.")]
        [SerializeField] private LayerMask _groundMask;
        [SerializeField] private float _accel = 20f;
        [Tooltip("How far ahead it feels for a wall.")]
        [SerializeField] private float _wallProbe = 0.14f;
        [Tooltip("A drop deeper than this counts as a ledge and it refuses to step off.")]
        [SerializeField] private float _ledgeDrop = 0.7f;
        [Tooltip("Ungrounded for longer than this and it gives up steering.")]
        [SerializeField] private float _airGrace = 0.12f;

        private static readonly int IdleTrig = Animator.StringToHash("Idle");
        private static readonly int WalkTrig = Animator.StringToHash("Walk");
        private static readonly int RunTrig = Animator.StringToHash("Run");
        private static readonly int ShootTrig = Animator.StringToHash("Shoot");
        private static readonly int AirTrig = Animator.StringToHash("Air");

        // Length of CowardShoot.anim. The bolt leaves on the animation event; this is only how
        // long the creature stays committed to standing still.
        private const float ShootDuration = 0.27f;
        private const float FlinchLockout = 0.6f;

        private State _state = State.Idle;
        private float _stateTimer;
        private float _fireTimer;
        private float _airTime;
        private float _alert;            // seconds of panic left
        private float _lastFlinch = -99f;
        private bool _grounded;
        private bool _seesPlayer;
        private bool _cornered;
        private bool _shotPending;
        private Vector2 _threat;         // player position, or the side a hit came from
        private int _facing = 1;
        private int _patrolDir = 1;
        private int _moveDir;
        private float _moveSpeed;
        private int _clip;

        private void Awake()
        {
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
            if (!_hull) _hull = GetComponent<Collider2D>();
            if (!_animator) _animator = GetComponent<Animator>();
            if (!_damageable) _damageable = GetComponent<Damageable>();
            if (!_body)
            {
                var view = transform.Find("View");
                _body = view ? view : transform;
            }

            _facing = _body.localScale.x < 0f ? -1 : 1;
            _patrolDir = _facing;
            _threat = transform.position;
        }

        private void OnEnable()
        {
            if (_damageable) _damageable.Damaged += OnDamaged;
            _clip = 0;
            _alert = 0f;
            Enter(State.Idle);
        }

        private void OnDisable()
        {
            if (_damageable) _damageable.Damaged -= OnDamaged;
        }

        private void Update()
        {
            float dt = Time.deltaTime;

            _grounded = GroundProbe();
            _airTime = _grounded ? 0f : _airTime + dt;
            _stateTimer -= dt;
            if (_fireTimer > 0f) _fireTimer -= dt;

            Sense(dt);

            switch (_state)
            {
                case State.Idle: TickIdle(); break;
                case State.Patrol: TickPatrol(); break;
                case State.Flee: TickFlee(); break;
                case State.Shoot: TickShoot(); break;
                case State.Flinch: TickFlinch(); break;
                case State.Air: TickAir(); break;
            }

            Animate();
        }

        private void FixedUpdate()
        {
            // Airborne it is cargo. Steering here would eat every throw and explosion.
            if (!_grounded) return;

            var v = _rb.linearVelocity;
            float target = _moveDir * _moveSpeed;

            // Do not fight a big external shove either - bleed it off instead of deleting it.
            bool launched = Mathf.Abs(v.x) > _runSpeed * 1.5f;
            float a = launched ? _accel * 0.3f : _accel;

            v.x = Mathf.MoveTowards(v.x, target, a * Time.fixedDeltaTime);
            _rb.linearVelocity = v;
        }

        // ------------------------------------------------------------------ senses

        private void Sense(float dt)
        {
            _seesPlayer = false;

            var player = App.Instance.PlayerTransform;
            if (player)
            {
                Vector2 p = player.position;
                // Spotting someone takes looking their way. Keeping tabs on someone it is
                // already running from does not - it glances over its shoulder, so a clear
                // line is enough. Without this it would be blind to whatever it flees from.
                if (LineClear(p, _sightRange) && (_alert > 0f || InView(p)))
                {
                    _seesPlayer = true;
                    _threat = p;
                    _alert = _memory;
                }
            }

            if (!_seesPlayer && _alert > 0f) _alert -= dt;
        }

        private bool InView(Vector2 target)
        {
            Vector2 to = target - EyePos;
            // Anything close enough is noticed from any angle.
            return to.magnitude <= _hearRange ||
                   Vector2.Angle(new Vector2(_facing, 0f), to) <= _fovDegrees * 0.5f;
        }

        private bool LineClear(Vector2 target, float range)
        {
            Vector2 eye = EyePos;
            Vector2 to = target - eye;
            float dist = to.magnitude;
            if (dist > range) return false;
            if (_sightBlockers.value == 0 || dist < 0.01f) return true;
            return !Physics2D.Raycast(eye, to / dist, dist, _sightBlockers);
        }

        private Vector2 EyePos =>
            (Vector2)transform.position + new Vector2(_eyeOffset.x * _facing, _eyeOffset.y);

        private Vector2 MuzzlePos =>
            (Vector2)transform.position + new Vector2(_muzzleOffset.x * _facing, _muzzleOffset.y);

        // ------------------------------------------------------------------ states

        private void TickIdle()
        {
            Hold();
            if (LeftTheGround()) return;
            if (_alert > 0f) { Enter(State.Flee); return; }

            if (_stateTimer <= 0f)
            {
                // A nervous glance over the shoulder before moving on.
                if (Random.value < 0.5f) SetFacing(-_facing);
                _patrolDir = _facing;
                Enter(State.Patrol);
            }
        }

        private void TickPatrol()
        {
            if (LeftTheGround()) return;
            if (_alert > 0f) { Enter(State.Flee); return; }

            if (!CanWalk(_patrolDir))
            {
                _patrolDir = -_patrolDir;
                Enter(State.Idle);      // pause, turn, think about it
                return;
            }

            Walk(_patrolDir, _walkSpeed);
            if (_stateTimer <= 0f) Enter(State.Idle);
        }

        private void TickFlee()
        {
            if (LeftTheGround()) return;
            if (_alert <= 0f) { Enter(State.Idle); return; }

            int away = _threat.x < transform.position.x ? 1 : -1;
            float dist = Vector2.Distance(transform.position, _threat);
            _cornered = !CanWalk(away);

            if (_cornered)
            {
                // Nowhere left to run: stand and fight, badly.
                Hold();
                SetFacing(-away);
                if (_seesPlayer && dist <= _fireRange && _fireTimer <= 0f) Enter(State.Shoot);
                return;
            }

            Walk(away, _runSpeed);

            // Enough of a head start to risk a shot over the shoulder.
            if (_seesPlayer && dist >= _keepAway && dist <= _fireRange && _fireTimer <= 0f)
                Enter(State.Shoot);
        }

        private void TickShoot()
        {
            Hold();
            if (LeftTheGround()) return;

            SetFacing(_threat.x < transform.position.x ? -1 : 1);
            if (_stateTimer > 0f) return;

            // Safety net: if the clip never raised its event, the shot still happens.
            FireIfPending();
            _fireTimer = _cornered ? _corneredCooldown : Random.Range(_fireCooldown.x, _fireCooldown.y);
            Enter(_alert > 0f ? State.Flee : State.Idle);
        }

        private void TickFlinch()
        {
            Hold();
            if (LeftTheGround()) return;
            if (_stateTimer <= 0f) Enter(_alert > 0f ? State.Flee : State.Idle);
        }

        private void TickAir()
        {
            if (_grounded) Enter(_alert > 0f ? State.Flee : State.Idle);
        }

        private bool LeftTheGround()
        {
            if (_airTime < _airGrace) return false;
            Enter(State.Air);
            return true;
        }

        private void Enter(State next)
        {
            _state = next;
            _shotPending = false;
            Hold();

            switch (next)
            {
                case State.Idle:
                    _stateTimer = Random.Range(_idleTime.x, _idleTime.y);
                    break;
                case State.Patrol:
                    _stateTimer = Random.Range(_patrolTime.x, _patrolTime.y);
                    break;
                case State.Shoot:
                    _stateTimer = ShootDuration;
                    _shotPending = true;
                    SetFacing(_threat.x < transform.position.x ? -1 : 1);
                    PlayClip(ShootTrig);   // restart it even if it was the last thing we played
                    break;
                case State.Flinch:
                    _stateTimer = _flinchTime;
                    break;
                default:
                    _stateTimer = 0f;
                    break;
            }
        }

        private void OnDamaged(int amount, Vector2 hitPoint)
        {
            // Being hurt is proof enough that something is out there.
            _alert = _memory;

            var player = App.Instance.PlayerTransform;
            // If it cannot see who did it, it runs from whichever side the hit landed on.
            _threat = _seesPlayer && player ? (Vector2)player.position : hitPoint;

            if (Time.time - _lastFlinch < FlinchLockout) return;
            _lastFlinch = Time.time;
            if (_state != State.Air) Enter(State.Flinch);
        }

        // ------------------------------------------------------------------ movement

        private void Walk(int dir, float speed)
        {
            SetFacing(dir);
            _moveDir = dir;
            _moveSpeed = speed;
        }

        private void Hold()
        {
            _moveDir = 0;
            _moveSpeed = 0f;
        }

        private void SetFacing(int dir)
        {
            if (dir == 0 || dir == _facing) return;
            _facing = dir;
            var s = _body.localScale;
            s.x = Mathf.Abs(s.x) * dir;
            _body.localScale = s;
        }

        /// <summary>Solid floor ahead and no wall in the way.</summary>
        private bool CanWalk(int dir) => !WallAhead(dir) && !LedgeAhead(dir);

        private bool GroundProbe()
        {
            var b = _hull.bounds;
            var size = new Vector2(b.size.x * 0.85f, 0.12f);
            var center = new Vector2(b.center.x, b.min.y - 0.04f);
            return Physics2D.OverlapBox(center, size, 0f, _groundMask);
        }

        private bool WallAhead(int dir)
        {
            var b = _hull.bounds;
            // Box kept clear of the floor so what it stands on never reads as a wall.
            var size = new Vector2(b.size.x * 0.5f, b.size.y * 0.6f);
            float reach = _wallProbe + b.size.x * 0.25f;
            return Physics2D.BoxCast(b.center, size, 0f, new Vector2(dir, 0f), reach, _groundMask);
        }

        private bool LedgeAhead(int dir)
        {
            var b = _hull.bounds;
            var from = new Vector2(b.center.x + dir * (b.size.x * 0.5f + _wallProbe), b.min.y + 0.05f);
            return !Physics2D.Raycast(from, Vector2.down, _ledgeDrop, _groundMask);
        }

        // ------------------------------------------------------------------ gun

        /// <summary>Animation event, raised by CowardShoot on frame 1.</summary>
        public void Shoot() => FireIfPending();

        private void FireIfPending()
        {
            if (!_shotPending) return;
            _shotPending = false;

            if (!_bolt)
            {
                Debug.LogWarning($"{name}: no bolt prefab assigned, nothing to shoot with.", this);
                return;
            }

            Vector2 muzzle = MuzzlePos;
            Vector2 dir = _threat - muzzle;
            if (dir.sqrMagnitude < 0.0001f) dir = new Vector2(_facing, 0f);
            dir = Quaternion.Euler(0f, 0f, Random.Range(-_spread, _spread)) * dir.normalized;

            var bolt = Instantiate(_bolt, muzzle, Quaternion.identity);
            bolt.Fire(dir * _boltSpeed, gameObject, _boltDamage);
        }

        // ------------------------------------------------------------------ animation

        private void Animate()
        {
            if (!_animator) return;

            int want = _state switch
            {
                State.Air => AirTrig,
                State.Shoot => ShootTrig,
                State.Patrol => WalkTrig,
                // Cornered it is still in Flee but standing still - do not slide on running legs.
                State.Flee => Mathf.Abs(_rb.linearVelocity.x) > 0.15f ? RunTrig : IdleTrig,
                _ => IdleTrig,
            };

            if (want != _clip) PlayClip(want);
        }

        private void PlayClip(int trigger)
        {
            _clip = trigger;
            if (!_animator) return;

            // A trigger no transition consumed stays raised and fires later out of nowhere,
            // so only ever one of them is live at a time.
            _animator.ResetTrigger(IdleTrig);
            _animator.ResetTrigger(WalkTrig);
            _animator.ResetTrigger(RunTrig);
            _animator.ResetTrigger(ShootTrig);
            _animator.ResetTrigger(AirTrig);
            _animator.SetTrigger(trigger);
        }

        // ------------------------------------------------------------------ gizmos

        private void OnDrawGizmosSelected()
        {
            if (!_body) _body = transform;
            if (!_hull) _hull = GetComponent<Collider2D>();

            Vector3 eye = EyePos;
            Gizmos.color = new Color(1f, 0.9f, 0.2f, 0.5f);
            Gizmos.DrawWireSphere(eye, _sightRange);

            float half = _fovDegrees * 0.5f;
            var fwd = new Vector3(_facing, 0f, 0f);
            Gizmos.color = Color.cyan;
            Gizmos.DrawLine(eye, eye + Quaternion.Euler(0f, 0f, half) * fwd * _sightRange);
            Gizmos.DrawLine(eye, eye + Quaternion.Euler(0f, 0f, -half) * fwd * _sightRange);

            Gizmos.color = new Color(1f, 0.4f, 0.1f, 0.4f);
            Gizmos.DrawWireSphere(eye, _hearRange);

            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(MuzzlePos, 0.05f);

            if (!_hull) return;
            var b = _hull.bounds;
            Gizmos.color = Color.green;
            for (int dir = -1; dir <= 1; dir += 2)
            {
                var from = new Vector3(b.center.x + dir * (b.size.x * 0.5f + _wallProbe), b.min.y + 0.05f, 0f);
                Gizmos.DrawLine(from, from + Vector3.down * _ledgeDrop);
            }
        }
    }
}
