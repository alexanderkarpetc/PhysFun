using UnityEditor.Animations;
using UnityEngine;

namespace Player
{
    public class PlayerMovement : MonoBehaviour
    {
        [SerializeField] private Transform _body;
        [SerializeField] private Rigidbody2D _rigidbody;
        [SerializeField] private float maxSpeed = 6f;
        [SerializeField] private Animator _animatorController;

        private float _moveX;
        private static readonly int Walk = Animator.StringToHash("Walk");
        private static readonly int Idle = Animator.StringToHash("Idle");
        private int _currentAnim;

        private void Update()
        {
            HandleMove();
            HandleTurn();
        }

        private void HandleMove()
        {
            _moveX = Mathf.Clamp(Input.GetAxisRaw("Horizontal"), -1f, 1f);
            if (Mathf.Abs(_moveX) > 0.1f)
            {
                if (_currentAnim != Walk)
                {
                    _currentAnim = Walk;
                    _animatorController.SetTrigger(Walk);
                    Debug.Log("WALK");
                }
            }
            else
            {
                if (_currentAnim != Idle)
                {
                    _currentAnim = Idle;
                    _animatorController.SetTrigger(Idle);
                    Debug.Log("IDLE");
                }
            }
        }

        private void FixedUpdate()
        {
            HandleMoveRB();
        }

        private void HandleMoveRB()
        {
            // instant horizontal speed
            var v = _rigidbody.linearVelocity;
            v.x = _moveX * maxSpeed;
            _rigidbody.linearVelocity = v;
        }

        private void HandleTurn()
        {
            var mouseW = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            SetFlip(mouseW.x - transform.position.x >= 0f ? 1f : -1f);
        }

        private void SetFlip(float sign)
        {
            var s = transform.localScale;
            s.x = sign >= 0f ? 1f : -1f;
            _body.localScale = s;
        }
    }
}
