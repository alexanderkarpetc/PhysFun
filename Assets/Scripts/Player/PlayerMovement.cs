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

        [Header("Move")]  [SerializeField] private float maxSpeed = 2f;
        [Header("Jump")]  [SerializeField] private float jumpVelocity = 2f;

        private float _moveX;
        private Camera _cam;
        private bool _grounded;

        // Animator triggers
        private static readonly int IdleTrig = Animator.StringToHash("Idle");
        private static readonly int WalkTrig = Animator.StringToHash("Walk");
        private static readonly int WalkBackTrig = Animator.StringToHash("WalkBack");
        private static readonly int JumpTrig = Animator.StringToHash("Jump");

        private enum State { Idle, Walk, WalkBack, Air }
        private State _state = State.Idle;

        private void Awake() => _cam = Camera.main;

        private void Update()
        {
            _moveX = Mathf.Clamp(Input.GetAxisRaw("Horizontal"), -1f, 1f);
            _grounded = IsOnGround();
            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);

            // Jump
            if (Input.GetKeyDown(KeyCode.Space) && _grounded)
            {
                var v = _rigidbody.linearVelocity;
                v.y = jumpVelocity;
                _rigidbody.linearVelocity = v;
                SetState(State.Air, JumpTrig);
            }

            // Ground locomotion
            if (_grounded && _state != State.Air)
            {
                if (Mathf.Abs(_moveX) > 0.01f) SetWalk(mouseW);
                else SetState(State.Idle, IdleTrig);
            }

            // Land detection (Air -> Idle/Walk/WalkBack)
            if (_state == State.Air && _grounded)
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
            v.x = _moveX * maxSpeed;
            _rigidbody.linearVelocity = v;
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
