using Props;
using UnityEngine;

namespace Player
{
    /// <summary>
    /// Noita-style locomotion: there is no jump. Holding the levitate key applies upward
    /// thrust that burns a flight meter (see <see cref="MovementConfig"/>). The meter recharges
    /// on the ground (and drips a little in the air). Tune everything live via the config asset.
    ///
    /// Two Terraria borrowings for built rooms: a <see cref="Ladder"/> is climbed with W / S
    /// at a walk without touching the meter (Space jumps off it), and a
    /// <see cref="OneWayPlatform"/> deck is stood on from above and dropped through by
    /// holding S.
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

        // Ladders and decks
        private bool _upHeld, _downHeld, _spaceHeld;
        private bool _climbing;
        private bool _upLatched;      // W still held from the ladder: it does not levitate until let go
        private Ladder _ladder;
        private Collider2D _bodyCol;
        private Collider2D[] _ownCols;
        private static readonly Collider2D[] GroundHits = new Collider2D[8];

        // Animator triggers
        private static readonly int IdleTrig = Animator.StringToHash("Idle");
        private static readonly int WalkTrig = Animator.StringToHash("Walk");
        private static readonly int WalkBackTrig = Animator.StringToHash("WalkBack");
        private static readonly int LevitateTrig = Animator.StringToHash("Levitate");
        private static readonly int FallTrig = Animator.StringToHash("Fall");
        // Scales walk playback so the stride matches the ground speed instead of skating.
        private static readonly int SpeedParam = Animator.StringToHash("Speed");

        private enum State { Idle, Walk, WalkBack, Levitate, Fall }
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

            _bodyCol = _rigidbody.GetComponent<Collider2D>();
            _ownCols = System.Array.FindAll(_rigidbody.GetComponentsInChildren<Collider2D>(true), c => !c.isTrigger);
        }

        private void Update()
        {
            _moveX = Mathf.Clamp(Input.GetAxisRaw("Horizontal"), -1f, 1f);
            _grounded = IsOnGround();

            // Levitate input: Space / W / Up - except that on a ladder W / Up climb it.
            _upHeld = Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow);
            _downHeld = Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow);
            _spaceHeld = Input.GetKey(KeyCode.Space);

            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);

            // Animation: in the air it is thrust or a drop, otherwise ground locomotion.
            // The staff is not part of these - StaffAim swings it at the cursor on top.
            if (_climbing)
            {
                if (Mathf.Abs(_rigidbody.linearVelocity.y) > 0.1f) SetState(State.Walk, WalkTrig);
                else SetState(State.Idle, IdleTrig);
            }
            else if (!_grounded)
            {
                if (_levitating) SetState(State.Levitate, LevitateTrig);
                else SetState(State.Fall, FallTrig);
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
            UpdateStride();
        }

        private void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;
            var v = _rigidbody.linearVelocity;

            UpdateClimb(ref v);
            if (!_upHeld) _upLatched = false;
            _levitateHeld = _spaceHeld || (_upHeld && !_climbing && !_upLatched);
            if (_climbing)
            {
                UpdateLevitation(ref v, dt);     // no thrust on a ladder - this only recharges
                _rigidbody.gravityScale = 0f;
            }
            else
            {
                UpdateHorizontal(ref v, dt);
                UpdateLevitation(ref v, dt);
                ShapeGravity(v);
                if (_downHeld && _grounded && !_spaceHeld)
                    OneWayPlatform.DropThrough(_groundCheck.position, 0.12f, _ownCols, _config.dropThroughTime);
            }

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
            else
            {
                // Airborne, no input: brake horizontal drift so releasing the key stops you
                // (Noita-style flight). But don't fight big external launches (crack/throw
                // impulses above walk speed) — only bleed off velocity down to walk range.
                if (Mathf.Abs(v.x) <= _config.maxSpeed)
                    v.x = Mathf.MoveTowards(v.x, 0f, _config.airFriction * dt);
            }
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
                    float rate = _grounded || _climbing ? _config.groundRegenRate : _config.airRegenRate;
                    _capacity = Mathf.Min(_config.capacity, _capacity + rate * dt);
                }

                // Grounded always clears lockout; otherwise wait until we cross the refire threshold.
                if (_grounded || _climbing || _capacity >= _config.refireThreshold * _config.capacity)
                    _lockedOut = false;
            }
        }

        /// <summary>
        /// Get on a ladder with W at its foot (or anywhere along it) or S at its top, go up
        /// and down it at <see cref="MovementConfig.climbSpeed"/>, hang on it with neither.
        /// Off it with Space, by walking away at the foot, or by running out of ladder - at
        /// the top that leaves you stood on the deck it comes up through.
        /// </summary>
        private void UpdateClimb(ref Vector2 v)
        {
            if (!_bodyCol) return;
            var b = _bodyCol.bounds;
            float feet = b.min.y;
            float dir = _upHeld ? 1f : _downHeld ? -1f : 0f;

            if (!_climbing)
            {
                if (dir == 0f || _spaceHeld) return;
                // Up: a ladder where the feet are. Down: one just under them - the top of a
                // ladder that comes up through the deck being stood on.
                var ladder = Ladder.At(new Vector2(b.center.x, feet + (dir > 0f ? 0.05f : -0.08f)));
                if (!ladder) return;
                if (dir < 0f && feet - ladder.Bottom < 0.1f) return;     // already at its foot
                _ladder = ladder;
                _climbing = true;
            }

            bool onIt = _ladder && Ladder.At(new Vector2(b.center.x, feet + (dir < 0f ? -0.08f : 0.02f))) == _ladder;
            bool walkOff = _grounded && dir == 0f && Mathf.Abs(_moveX) > 0.01f;
            if (_spaceHeld || !onIt || walkOff)
            {
                _climbing = false;
                _upLatched = _upHeld;
                _ladder = null;
                return;
            }

            v.y = dir * _config.climbSpeed;
            v.x = Mathf.Abs(_moveX) > 0.01f
                ? _moveX * _config.climbSideSpeed
                : Mathf.Clamp((_ladder.CenterX - b.center.x) * 10f, -_config.climbSideSpeed, _config.climbSideSpeed);
            if (dir < 0f)
                OneWayPlatform.DropThrough(new Vector2(b.center.x, feet), 0.1f, _ownCols, _config.dropThroughTime);
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
            if (!_animator) return;

            // A trigger no transition consumed stays raised and fires later out of nowhere,
            // so only ever one of them is live at a time.
            _animator.ResetTrigger(IdleTrig);
            _animator.ResetTrigger(WalkTrig);
            _animator.ResetTrigger(WalkBackTrig);
            _animator.ResetTrigger(LevitateTrig);
            _animator.ResetTrigger(FallTrig);
            _animator.SetTrigger(trigger);
        }

        /// <summary>Play the walk cycle at the speed we are actually moving, within reason.</summary>
        private void UpdateStride()
        {
            if (!_animator) return;

            float cadence = _config.maxSpeed > 0.01f
                ? Mathf.Abs(_rigidbody.linearVelocity.x) / _config.maxSpeed
                : 1f;

            // Floored so shoving into a wall shuffles rather than freezes mid-step.
            _animator.SetFloat(SpeedParam, Mathf.Clamp(cadence, 0.35f, 1.6f));
        }

        private void HandleTurn(Vector3 mouseW)
        {
            var s = _body.localScale;
            s.x = (mouseW.x - transform.position.x >= 0f) ? 1f : -1f;
            _body.localScale = s;
        }

        private bool IsOnGround()
        {
            var filter = new ContactFilter2D
            {
                useLayerMask = true,
                layerMask = _groundMask,
                useTriggers = Physics2D.queriesHitTriggers,
            };
            int n = Physics2D.OverlapCircle(_groundCheck.position, 0.1f, filter, GroundHits);
            // A deck is not ground while coming up through it or being let down through it.
            bool rising = _rigidbody.linearVelocity.y > 0.05f;
            for (int i = 0; i < n; i++)
            {
                var c = GroundHits[i];
                if (OneWayPlatform.Is(c) && (rising || OneWayPlatform.IsPassing(c, _bodyCol))) continue;
                return true;
            }
            return false;
        }
    }
}
