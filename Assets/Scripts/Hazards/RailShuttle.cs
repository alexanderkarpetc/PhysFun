using UnityEngine;

namespace Hazards
{
    /// <summary>
    /// A trolley that runs a rail on its own, end to end and back: the swing saw's carriage in
    /// the Sawpit (S05). Kinematic, so nothing in its way slows it; what is on its line is
    /// pushed, cut or hurt by whatever it carries.
    ///
    /// It only runs while there is rail over its wheels. Cut the rail (or the hangers it
    /// hangs from, so the rail drops away) and the probes at the wheels find nothing to ride
    /// on: the trolley turns into an ordinary body and falls, with whatever is jointed to it.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class RailShuttle : MonoBehaviour
    {
        [Tooltip("How far it runs west of where it starts, world units.")]
        [SerializeField] private float _left = 4f;
        [Tooltip("How far it runs east of where it starts, world units.")]
        [SerializeField] private float _right = 4f;
        [Tooltip("Units per second.")]
        [SerializeField] private float _speed = 1.6f;
        [Tooltip("Seconds it stands at each end before turning back.")]
        [SerializeField] private float _pause = 0.5f;
        [SerializeField] private bool _startEast = true;
        [Tooltip("Points, local, that must be touching rail: the wheels. With none of them on it, it falls.")]
        [SerializeField] private Vector2[] _wheels = { new(-0.35f, 1.9f), new(0.35f, 1.9f) };
        [SerializeField] private float _probe = 0.1f;

        private static readonly Collider2D[] Hits = new Collider2D[16];
        private Rigidbody2D _rb;
        private float _x0, _dir, _wait;

        public bool Fallen { get; private set; }

        private void Start()
        {
            _rb = GetComponent<Rigidbody2D>();
            _rb.bodyType = RigidbodyType2D.Kinematic;
            _x0 = _rb.position.x;
            _dir = _startEast ? 1f : -1f;
        }

        private void FixedUpdate()
        {
            if (Fallen) return;
            if (!OnRail())
            {
                Fallen = true;
                _rb.bodyType = RigidbodyType2D.Dynamic;
                return;
            }
            float dt = Time.fixedDeltaTime;
            if (_wait > 0f)
            {
                _wait -= dt;
                return;
            }
            float x = _rb.position.x + _dir * _speed * dt;
            if (x >= _x0 + _right) { x = _x0 + _right; _dir = -1f; _wait = _pause; }
            else if (x <= _x0 - _left) { x = _x0 - _left; _dir = 1f; _wait = _pause; }
            _rb.MovePosition(new Vector2(x, _rb.position.y));
        }

        private bool OnRail()
        {
            foreach (var w in _wheels)
            {
                int n = Physics2D.OverlapCircleNonAlloc(transform.TransformPoint(w), _probe, Hits);
                for (int i = 0; i < n; i++)
                {
                    var c = Hits[i];
                    if (!c || c.isTrigger) continue;
                    var body = c.attachedRigidbody;
                    if (body == _rb) continue;
                    if (body && body.bodyType == RigidbodyType2D.Dynamic) continue;   // not something loose
                    return true;
                }
            }
            return false;
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.85f, 0.82f, 0.3f);
            foreach (var w in _wheels) Gizmos.DrawWireSphere(transform.TransformPoint(w), _probe);
            var p = transform.position;
            float x0 = Application.isPlaying ? _x0 : p.x;
            Gizmos.DrawLine(new Vector3(x0 - _left, p.y), new Vector3(x0 + _right, p.y));
        }
#endif
    }
}
