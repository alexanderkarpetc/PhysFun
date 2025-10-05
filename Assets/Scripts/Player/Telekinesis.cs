using UnityEngine;

namespace Player
{
    public class Telekinesis : MonoBehaviour
    {
        [Header("Refs")]
        [SerializeField] private Transform origin;     // usually player's body; if null -> this.transform
        [SerializeField] private LayerMask grabbable;  // only these layers can be grabbed

        [Header("Hold")]
        [SerializeField] private float holdDistance = 1.2f;   // distance from origin
        [SerializeField] private float followGain = 25f;      // how fast it snaps to target
        [SerializeField] private float maxHoldSpeed = 15f;    // cap velocity while holding
        [SerializeField] private float maxGrabRange = 6f;     // optional pickup range

        [Header("Throw")]
        [SerializeField] private float throwImpulse = 15f;    // impulse magnitude on LMB
        [SerializeField] private float releaseDrag = 0.5f;    // drag after release

        [Header("Collision")]
        [SerializeField] private Collider2D[] playerColliders; // optional: to avoid self-collision while holding
        [SerializeField] private bool ignorePlayerWhileHolding = true;

        Camera _cam;
        Rigidbody2D _held;
        float _savedGravity, _savedDrag, _savedAngularDrag;
        RigidbodyConstraints2D _savedConstraints;

        void Awake()
        {
            _cam = Camera.main;
            if (!origin) origin = transform;
        }

        void Update()
        {
            if (Input.GetMouseButtonDown(1))
            {
                if (_held) Release();
                else TryGrab();
            }

            if (_held && Input.GetMouseButtonDown(0))
            {
                Throw();
            }
        }

        void FixedUpdate()
        {
            if (!_held) return;

            // target point = origin + dirToMouse * holdDistance
            Vector3 mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
            Vector2 dir = ((Vector2)mouseW - (Vector2)origin.position).normalized;
            Vector2 target = (Vector2)origin.position + dir * holdDistance;

            // Proportional velocity toward target (keeps physics, collisions, external impulses)
            Vector2 toTarget = target - _held.position;
            Vector2 desiredVel = toTarget * followGain;
            if (desiredVel.sqrMagnitude > maxHoldSpeed * maxHoldSpeed)
                desiredVel = desiredVel.normalized * maxHoldSpeed;

            _held.linearVelocity = Vector2.Lerp(_held.linearVelocity, desiredVel, 0.5f);
        }

        void TryGrab()
        {
            Vector3 mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
            Vector2 p = mouseW;

            // require collider under cursor on allowed layers
            Collider2D hit = Physics2D.OverlapPoint(p, grabbable);
            if (!hit) return;

            // optional range check
            if (maxGrabRange > 0f && Vector2.Distance(hit.bounds.ClosestPoint(origin.position), origin.position) > maxGrabRange)
                return;

            Rigidbody2D rb = hit.attachedRigidbody;
            if (!rb || rb.isKinematic) return;

            _held = rb;

            // save + modify physics for holding
            _savedGravity     = _held.gravityScale;
            _savedDrag        = _held.linearDamping;
            _savedAngularDrag = _held.angularDamping;
            _savedConstraints = _held.constraints;

            _held.gravityScale = 0f;
            _held.linearDamping = 8f;
            _held.angularDamping = 8f;
            _held.angularVelocity = 0f;
            _held.constraints = _savedConstraints | RigidbodyConstraints2D.FreezeRotation;

            if (ignorePlayerWhileHolding && playerColliders != null)
            {
                foreach (var pc in playerColliders)
                    if (pc) Physics2D.IgnoreCollision(pc, hit, true);
            }
        }

        void Release()
        {
            if (!_held) return;

            // restore physics
            _held.gravityScale = _savedGravity;
            _held.linearDamping = releaseDrag;                // small drag to settle; use _savedDrag if you prefer exact restore
            _held.angularDamping = _savedAngularDrag;
            _held.constraints = _savedConstraints;

            // re-enable collisions
            if (ignorePlayerWhileHolding && playerColliders != null)
            {
                var col = _held.GetComponent<Collider2D>();
                foreach (var pc in playerColliders)
                    if (pc && col) Physics2D.IgnoreCollision(pc, col, false);
            }

            _held = null;
        }

        void Throw()
        {
            if (!_held) return;

            Vector3 mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
            Vector2 dir = ((Vector2)mouseW - (Vector2)origin.position).normalized;

            var rb = _held;   // keep reference before Release()
            Release();

            rb.AddForce(dir * throwImpulse, ForceMode2D.Impulse);
        }

        // Optional: helper to set distance at runtime
        public void SetHoldDistance(float d) => holdDistance = Mathf.Max(0.1f, d);
    }
}
