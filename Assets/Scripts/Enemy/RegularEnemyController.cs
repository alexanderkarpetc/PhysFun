using UnityEngine;

namespace Enemy
{
    public class SimpleBot : MonoBehaviour
    {
        [Header("Refs")]
        [SerializeField] private Transform _body;          // visuals to flip
        [SerializeField] private Rigidbody2D _rb;
        [SerializeField] private Animator _animator;
        [SerializeField] private Transform _eye;

        [Header("Patrol")]
        [SerializeField] private float walkSpeed = 2f;
        [SerializeField] private float idleDuration = 1.5f;
        [SerializeField] private float walkDuration = 2.5f;

        [SerializeField] private float detectRange = 8f;
        [SerializeField] private float fovDegrees = 150f;
        [SerializeField] private LayerMask obstacleMask;   // walls/ground

        // Animator triggers
        private static readonly int IdleTrig  = Animator.StringToHash("Idle");
        private static readonly int WalkTrig  = Animator.StringToHash("Walk");
        private static readonly int ShootTrig = Animator.StringToHash("Shoot");

        private enum State { Idle, Walk, Shoot }
        private State _state = State.Idle;

        // timers
        private float _stateTimer;

        // movement dir: +1 right, -1 left
        private int _dir = 1;

        private void OnEnable()
        {
            EnterState(State.Idle);
        }

        private void Update()
        {
            _stateTimer -= Time.deltaTime;

            bool seesPlayer = CanSeePlayer();

            // state transitions
            if (seesPlayer)
            {
                if (_state != State.Shoot)
                {
                    EnterState(State.Shoot);
                    SetVelX(0f);
                }
            }
            else
            {
                // patrol when player not visible
                if (_state == State.Shoot) EnterState(State.Idle);

                if (_state == State.Idle && _stateTimer <= 0f)
                {
                    _dir = -_dir;
                    SetScale(_dir);
                    EnterState(State.Walk);
                }
                else if (_state == State.Walk && _stateTimer <= 0f)
                {
                    EnterState(State.Idle);
                }
            }
        }

        private void FixedUpdate()
        {
            if (_state == State.Walk)
                SetVelX(_dir * walkSpeed);
            else
                SetVelX(0f);
        }

        private void EnterState(State next)
        {
            if (_state == next) return;
            _state = next;

            switch (next)
            {
                case State.Idle:
                    _stateTimer = idleDuration;
                    _animator.SetTrigger(IdleTrig);
                    break;
                case State.Walk:
                    _stateTimer = walkDuration;
                    _animator.SetTrigger(WalkTrig);
                    break;
                case State.Shoot:
                    _animator.SetTrigger(ShootTrig);
                    break;
            }
        }

        private void SetVelX(float x)
        {
            var v = _rb.linearVelocity;
            v.x = x;
            _rb.linearVelocity = v;
        }

        private void SetScale(float dirSign)
        {
            var s = _body.localScale;
            s.x = (dirSign >= 0f) ? 1f : -1f;
            _body.localScale = s;
        }

        private bool CanSeePlayer()
        {
            if (App.Instance.PlayerTransform == null) return false;

            Vector2 eyePos = _eye ? _eye.position : (Vector2)transform.position;
            Vector2 toPlayer = (Vector2)App.Instance.PlayerTransform.position - eyePos;
            float dist = toPlayer.magnitude;
            if (dist > detectRange) return false;

            // FOV check relative to facing direction
            float facing = Mathf.Sign(_body.localScale.x);                 // +1 right, -1 left
            Vector2 forward = new Vector2(facing, 0f);
            float angle = Vector2.Angle(forward, toPlayer.normalized);
            if (angle > fovDegrees * 0.5f) return false;

            // Line of sight (no obstacles)
            var hit = Physics2D.Raycast(eyePos, toPlayer.normalized, dist, obstacleMask);
            return hit.collider.gameObject == App.Instance.PlayerGo;
        }

        // called by animation event
        private void Shoot()
        {
            // TODO: spawn projectile / play muzzle flash / apply damage
            // Intentionally empty for now.
            Debug.Log("Shoot!");
        }

        // gizmos for tuning
        private void OnDrawGizmos()
        {
            Vector3 origin = _eye ? _eye.position : transform.position;
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(origin, detectRange);

            // FOV lines
            float facing = (_body ? Mathf.Sign(_body.localScale.x) : 1f);
            Vector2 forward = new Vector2(facing, 0f);
            float half = fovDegrees * 0.5f;
            Vector2 left = Quaternion.Euler(0,0, half) * forward;
            Vector2 right = Quaternion.Euler(0,0,-half) * forward;
            Gizmos.color = Color.cyan;
            Gizmos.DrawLine(origin, origin + (Vector3)(left * detectRange));
            Gizmos.DrawLine(origin, origin + (Vector3)(right * detectRange));
        }
    }
}
