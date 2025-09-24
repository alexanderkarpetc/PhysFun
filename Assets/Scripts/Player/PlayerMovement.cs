using UnityEngine;
using UnityEngine.InputSystem;

namespace Player
{
    public class PlayerMovement : MonoBehaviour
    {
        [Header("Refs")] [SerializeField] private Transform _body;
        [SerializeField] private Rigidbody2D _rigidbody;
        [SerializeField] private Animator _animator;
        [SerializeField] private Transform _groundCheck;
        [SerializeField] private LayerMask _groundMask;

        [Header("Move")] [SerializeField] private float maxSpeed = 2f;

        [Header("Jump")] [SerializeField] private float jumpVelocity = 2f;

        private float _moveX;
        private Camera _cam;

        // Animator params
        private static readonly int SpeedAbs = Animator.StringToHash("SpeedAbs");
        private static readonly int IsGrounded = Animator.StringToHash("IsGrounded");
        private static readonly int YVel = Animator.StringToHash("YVel");
        private static readonly int JumpTrig = Animator.StringToHash("Jump"); // optional one-shot

        private void Awake()
        {
            _cam = Camera.main;
        }

        private void Update()
        {
            // horizontal input
            _moveX = Mathf.Clamp(Input.GetAxisRaw("Horizontal"), -1f, 1f);

            // jump press
            if (Input.GetKeyDown(KeyCode.Space) && IsOnGround())
            {
                var v = _rigidbody.linearVelocity;
                v.y = jumpVelocity;
                _rigidbody.linearVelocity = v;
                if (_animator) _animator.SetTrigger(JumpTrig); // optional
            }

            HandleTurn();
            UpdateAnimator();
        }

        private void FixedUpdate()
        {
            // instant horizontal speed (no smoothing)
            var v = _rigidbody.linearVelocity;
            v.x = _moveX * maxSpeed;
            _rigidbody.linearVelocity = v;
        }

        private void HandleTurn()
        {
            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
            SetFlip(mouseW.x - transform.position.x >= 0f ? 1f : -1f);
        }

        private void SetFlip(float sign)
        {
            var s = _body.localScale;
            s.x = sign >= 0f ? 1f : -1f;
            _body.localScale = s;
        }

        private bool IsOnGround()
        {
            return Physics2D.OverlapCircle(_groundCheck.position, 0.1f, _groundMask) != null;
        }

        private void UpdateAnimator()
        {
            if (!_animator) return;
            _animator.SetFloat(SpeedAbs, Mathf.Abs(_rigidbody.linearVelocity.x));
            _animator.SetBool(IsGrounded, IsOnGround());
            _animator.SetFloat(YVel, _rigidbody.linearVelocity.y);
        }
    }
}