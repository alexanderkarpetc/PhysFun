using UnityEngine;

namespace Player
{
    public class PlayerMovement : MonoBehaviour
    {
        [Header("Refs")]
        [SerializeField] private Transform _body;
        [SerializeField] private Rigidbody2D _rigidbody;
        [SerializeField] private Animator _animator;
        [SerializeField] private Transform _groundCheck;
        [SerializeField] private LayerMask _groundMask;

        [Header("Move")]
        [SerializeField] private float maxSpeed = 2f;
        [SerializeField] private float accel = 20f;       // ground acceleration toward target
        [SerializeField] private float turnAccel = 40f;   // accel when reversing direction (snappier)
        [SerializeField] private float airControl = 0.3f;
        [SerializeField] private float friction = 10f;
        [SerializeField] private float jumpVelocity = 4.5f;

        [Header("Jump feel")]
        [SerializeField] private float jumpBuffer = 0.1f;
        [SerializeField] private float jumpCutMultiplier = 0.5f; // applied to upward velocity on early release
        [SerializeField] private float gravityMult = 0.7f;        // applied to base gravity while rising w/ hold
        [SerializeField] private float fallGravityMult = 1.3f;    // gravity scale while falling
        [SerializeField] private float lowJumpGravityMult = 1.6f; // gravity scale while rising w/o hold

        private float _moveX;
        private Camera _cam;
        private bool _grounded;
        private float _baseGravityScale;
        private float _jumpBufferTimer;
        private bool _jumpHeld;
        private bool _jumping;

        // Animator triggers
        private static readonly int IdleTrig = Animator.StringToHash("Idle");
        private static readonly int WalkTrig = Animator.StringToHash("Walk");
        private static readonly int WalkBackTrig = Animator.StringToHash("WalkBack");
        private static readonly int JumpTrig = Animator.StringToHash("Jump");

        private enum State { Idle, Walk, WalkBack, Air }
        private State _state = State.Idle;

        private void Awake()
        {
            _cam = Camera.main;
            _baseGravityScale = _rigidbody.gravityScale;
        }

        private void Update()
        {
            _moveX = Mathf.Clamp(Input.GetAxisRaw("Horizontal"), -1f, 1f);
            _grounded = IsOnGround();
            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);

            // Timers
            _jumpBufferTimer -= Time.deltaTime;

            // Jump input
            if (Input.GetKeyDown(KeyCode.Space)) _jumpBufferTimer = jumpBuffer;
            _jumpHeld = Input.GetKey(KeyCode.Space);

            // Variable jump height: cut on release while rising
            if (Input.GetKeyUp(KeyCode.Space) && _rigidbody.linearVelocity.y > 0f)
            {
                var vv = _rigidbody.linearVelocity;
                vv.y *= jumpCutMultiplier;
                _rigidbody.linearVelocity = vv;
            }

            // Execute buffered jump if grounded
            if (_jumpBufferTimer > 0f && _grounded)
            {
                var v = _rigidbody.linearVelocity;
                v.y = jumpVelocity;
                _rigidbody.linearVelocity = v;
                _jumpBufferTimer = 0f;
                _jumping = true;
                SetState(State.Air, JumpTrig);
            }

            if (_grounded && _rigidbody.linearVelocity.y <= 0.01f) _jumping = false;

            // Ground locomotion
            if (_grounded && _state != State.Air)
            {
                if (Mathf.Abs(_moveX) > 0.01f) SetWalk(mouseW);
                else SetState(State.Idle, IdleTrig);
            }

            // Land detection (Air -> Idle/Walk/WalkBack)
            if (_state == State.Air && _grounded && !_jumping)
            {
                if (Mathf.Abs(_moveX) > 0.01f) SetWalk(mouseW);
                else SetState(State.Idle, IdleTrig);
            }

            HandleTurn(mouseW);
        }

        private void SetWalk(Vector3 mouseW)
        {
            var lookForward = mouseW.x - transform.position.x >= 0f;
            if (lookForward && _moveX < 0f || !lookForward && _moveX > 0f)
                SetState(State.WalkBack, WalkBackTrig);
            else
                SetState(State.Walk, WalkTrig);
        }

        private void FixedUpdate()
        {
            var v = _rigidbody.linearVelocity;
            float target = _moveX * maxSpeed;

            if (Mathf.Abs(_moveX) > 0.01f)
            {
                // Snappier when reversing direction
                bool reversing = Mathf.Sign(_moveX) != Mathf.Sign(v.x) && Mathf.Abs(v.x) > 0.05f;
                float a = reversing ? turnAccel : accel;
                if (!_grounded) a *= airControl;
                v.x = Mathf.MoveTowards(v.x, target, a * Time.fixedDeltaTime);
            }
            else if (_grounded)
            {
                v.x = Mathf.MoveTowards(v.x, 0f, friction * Time.fixedDeltaTime);
            }
            // else: airborne with no input — preserve momentum / external impulses

            _rigidbody.linearVelocity = v;

            // Gravity shaping: heavier on the way down, heavier on early release while rising
            if (v.y < 0f)
                _rigidbody.gravityScale = _baseGravityScale * fallGravityMult;
            else if (v.y > 0f && !_jumpHeld)
                _rigidbody.gravityScale = _baseGravityScale * lowJumpGravityMult;
            else if (v.y > 0f)
                _rigidbody.gravityScale = _baseGravityScale * gravityMult;
            else
                _rigidbody.gravityScale = _baseGravityScale;
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
