using UnityEngine;

namespace Player
{
    /// <summary>
    /// Noita-style locomotion: there is no jump. Holding the levitate key applies upward
    /// thrust that burns a flight meter (see <see cref="MovementConfig"/>). The meter recharges
    /// on the ground (and drips a little in the air). Tune everything live via the config asset.
    /// </summary>
    public class PlayerMovement : MonoBehaviour
    {
        [Header("Refs")]
        [SerializeField] private Transform _body;
        [SerializeField] private Rigidbody2D _rigidbody;
        [SerializeField] private Animator _animator;
        [SerializeField] private Transform _groundCheck;
        [SerializeField] private LayerMask _groundMask;

        [Header("Config")]
        [Tooltip("Live-tunable movement profile. Edit the asset in Play mode to feel changes instantly.")]
        [SerializeField] private MovementConfig _config;

        private float _moveX;
        private Camera _cam;
        private bool _grounded;

        // Levitation state
        private bool _levitateHeld;
        private bool _levitatePrev;
        private bool _levitating;
        private bool _lockedOut;      // true after fully draining, until capacity recharges past the refire threshold
        private float _capacity;      // remaining flight, in seconds
        private float _regenTimer;    // delay before recharge resumes

        // Animator triggers
        private static readonly int IdleTrig = Animator.StringToHash("Idle");
        private static readonly int WalkTrig = Animator.StringToHash("Walk");
        private static readonly int WalkBackTrig = Animator.StringToHash("WalkBack");
        private static readonly int JumpTrig = Animator.StringToHash("Jump");

        private enum State { Idle, Walk, WalkBack, Air }
        private State _state = State.Idle;

        /// <summary>0..1 fraction of levitation capacity remaining (for HUD meters).</summary>
        public float CapacityNormalized => _config != null && _config.capacity > 0f ? _capacity / _config.capacity : 0f;
        /// <summary>True while thrust is actively being produced this frame.</summary>
        public bool IsLevitating => _levitating;

        private void Awake()
        {
            _cam = Camera.main;

            // Never NRE if the asset was not wired up in the Inspector — fall back to defaults.
            if (_config == null)
            {
                _config = ScriptableObject.CreateInstance<MovementConfig>();
                Debug.LogWarning("[PlayerMovement] No MovementConfig assigned — using built-in defaults.", this);
            }

            _capacity = _config.capacity;
            _rigidbody.gravityScale = _config.gravityScale;
        }

        private void Update()
        {
            _moveX = Mathf.Clamp(Input.GetAxisRaw("Horizontal"), -1f, 1f);
            _grounded = IsOnGround();

            // Levitate input: Space / W / Up.
            _levitateHeld = Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow);

            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);

            // Animation: airborne when not grounded, otherwise ground locomotion.
            if (!_grounded)
            {
                SetState(State.Air, JumpTrig);
            }
            else if (Mathf.Abs(_moveX) > 0.01f)
            {
                SetWalk(mouseW);
            }
            else
            {
                SetState(State.Idle, IdleTrig);
            }

            HandleTurn(mouseW);
        }

        private void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;
            var v = _rigidbody.linearVelocity;

            UpdateHorizontal(ref v, dt);
            UpdateLevitation(ref v, dt);
            ShapeGravity(v);

            // Terminal velocity clamp on the way down.
            if (v.y < -_config.maxFallSpeed) v.y = -_config.maxFallSpeed;

            _rigidbody.linearVelocity = v;
        }

        private void UpdateHorizontal(ref Vector2 v, float dt)
        {
            float target = _moveX * _config.maxSpeed;

            if (Mathf.Abs(_moveX) > 0.01f)
            {
                // Snappier when reversing direction.
                bool reversing = Mathf.Sign(_moveX) != Mathf.Sign(v.x) && Mathf.Abs(v.x) > 0.05f;
                float a = reversing ? _config.turnAccel : _config.accel;
                if (!_grounded) a *= _config.airControl;
                v.x = Mathf.MoveTowards(v.x, target, a * dt);
            }
            else if (_grounded)
            {
                v.x = Mathf.MoveTowards(v.x, 0f, _config.friction * dt);
            }
            // else: airborne with no input — preserve momentum / external impulses.
        }

        private void UpdateLevitation(ref Vector2 v, float dt)
        {
            bool justPressed = _levitateHeld && !_levitatePrev;
            _levitatePrev = _levitateHeld;

            bool canLevitate = _levitateHeld && _capacity > 0f && !_lockedOut;

            if (canLevitate)
            {
                _levitating = true;

                // Responsive initial kick when (re)engaging flight.
                if (justPressed && v.y < _config.initialHopImpulse)
                    v.y = _config.initialHopImpulse;

                // Accelerate upward toward the rise cap. Gravity fights it each step,
                // which produces the controlled, floaty Noita ascent.
                if (v.y < _config.maxRiseSpeed)
                    v.y = Mathf.MoveTowards(v.y, _config.maxRiseSpeed, _config.levitateForce * dt);

                // Burn the meter.
                _capacity -= _config.drainRate * dt;
                if (_capacity <= 0f)
                {
                    _capacity = 0f;
                    _lockedOut = true;   // must recharge past the refire threshold before flying again
                    _levitating = false;
                }

                _regenTimer = _config.regenDelay;
            }
            else
            {
                _levitating = false;

                // Recharge after a short delay.
                if (_regenTimer > 0f)
                {
                    _regenTimer -= dt;
                }
                else if (_capacity < _config.capacity)
                {
                    float rate = _grounded ? _config.groundRegenRate : _config.airRegenRate;
                    _capacity = Mathf.Min(_config.capacity, _capacity + rate * dt);
                }

                // Grounded always clears lockout; otherwise wait until we cross the refire threshold.
                if (_grounded || _capacity >= _config.refireThreshold * _config.capacity)
                    _lockedOut = false;
            }
        }

        private void ShapeGravity(Vector2 v)
        {
            // Heavier on the way down so descents feel weighty rather than floaty.
            _rigidbody.gravityScale = v.y < 0f
                ? _config.gravityScale * _config.fallGravityMult
                : _config.gravityScale;
        }

        private void SetWalk(Vector3 mouseW)
        {
            var lookForward = mouseW.x - transform.position.x >= 0f;
            if (lookForward && _moveX < 0f || !lookForward && _moveX > 0f)
                SetState(State.WalkBack, WalkBackTrig);
            else
                SetState(State.Walk, WalkTrig);
        }

        private void SetState(State next, int trigger)
        {
            if (_state == next) return;
            _state = next;
            if (_animator) _animator.SetTrigger(trigger);
        }

        private void HandleTurn(Vector3 mouseW)
        {
            var s = _body.localScale;
            s.x = (mouseW.x - transform.position.x >= 0f) ? 1f : -1f;
            _body.localScale = s;
        }

        private bool IsOnGround()
        {
            return Physics2D.OverlapCircle(_groundCheck.position, 0.1f, _groundMask) != null;
        }
    }
}
