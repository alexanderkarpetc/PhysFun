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
        [Header("Grab Filters")]
        [SerializeField] private float minMass = 5f;
        [SerializeField] private float maxMass = 150f;
        [SerializeField] private float pickRadius = 0.25f; 

        Camera _cam;
        Rigidbody2D _held;
        float _savedGravity, _savedAngularDrag;
        RigidbodyConstraints2D _savedConstraints;

        private void Awake()
        {
            _cam = Camera.main;
            if (!origin) origin = transform;
        }

        private void Update()
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

        private void FixedUpdate()
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

        private void TryGrab()
        {
            // Look direction from facing (no cursor)
            Vector2 dir = (origin.localScale.x >= 0f) ? Vector2.right : Vector2.left;

            // Sweep a small capsule forward; get all hits in front up to range
            var hits = Physics2D.CircleCastAll(origin.position, pickRadius, dir, maxGrabRange, grabbable);
            if (hits == null || hits.Length == 0) return;

            Rigidbody2D bestRb = null;
            Collider2D bestCol = null;
            float bestDist = float.MaxValue;

            foreach (var h in hits)
            {
                var rb = h.rigidbody;
                var col = h.collider;
                if (!rb || rb.isKinematic) continue;

                // Mass limits
                if (rb.mass < minMass || rb.mass > maxMass) continue;

                // Skip player’s own colliders if provided
                if (playerColliders != null)
                {
                    bool self = false;
                    foreach (var pc in playerColliders) { if (pc && col && col == pc) { self = true; break; } }
                    if (self) continue;
                }

                // Closest along the cast from the player
                if (h.distance < bestDist)
                {
                    bestDist = h.distance;
                    bestRb = rb;
                    bestCol = col;
                }
            }

            if (!bestRb) return;

            // Begin holding (same as before)
            _held = bestRb;

            _savedGravity     = _held.gravityScale;
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
                    if (pc && bestCol) Physics2D.IgnoreCollision(pc, bestCol, true);
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
    }
}
