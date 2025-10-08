using UnityEngine;

namespace Player
{
    public class Telekinesis : MonoBehaviour
    {
        [Header("Refs")]
        [SerializeField] private Transform origin;     // usually player's body; if null -> this.transform
        [SerializeField] private LayerMask grabbable;  // only these layers can be grabbed
        [SerializeField] private LayerMask losBlockers; // что блокирует линию видимости (например Default | Terrain)

        [Header("Hold")]
        [SerializeField] private float holdDistance = 1.2f;
        [SerializeField] private float followGain = 25f;   // kP
        [SerializeField] private float dampGain = 8f;      // kD
        [SerializeField] private float maxHoldSpeed = 15f; // cap на скорость

        [Header("Throw")]
        [SerializeField] private float throwImpulse = 15f;    // impulse magnitude on LMB
        [SerializeField] private float releaseDrag = 0.5f;    // drag after release

        [Header("Collision")]
        [SerializeField] private Collider2D[] playerColliders; // to avoid self-collision while holding
        [Header("Grab Filters")]
        [SerializeField] private float minMass = 5f;
        [SerializeField] private float maxMass = 150f;
        [SerializeField] private float maxGrabRange = 6f;     // pickup range

        Camera _cam;
        Rigidbody2D _held;
        float _savedGravity, _savedAngularDrag, _savedDrag;
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

            // Автодроп, если вышли за пределы или потеряли LOS
            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
            Vector2 dirFromOrigin = ((Vector2)mouseW - (Vector2)origin.position);
            float distFromOrigin = dirFromOrigin.magnitude;
            if (distFromOrigin > maxGrabRange * 1.25f) { Release(); return; }

            // Проверка линии видимости между origin и объектом (по желанию)
            if (losBlockers.value != 0)
            {
                var col = _held.GetComponent<Collider2D>();
                var hit = Physics2D.Raycast(origin.position, (_held.position - (Vector2)origin.position).normalized,
                                            Vector2.Distance(origin.position, _held.position), losBlockers);
                if (hit.collider && (!col || hit.collider != col)) { Release(); return; }
            }

            // Точка удержания: на линии к курсору, на фикс. дистанции от origin
            Vector2 holdDir = distFromOrigin < 0.001f ? Vector2.right : (dirFromOrigin / distFromOrigin);
            Vector2 target = (Vector2)origin.position + holdDir * holdDistance;

            // PD-контроллер через AddForce (сохраняет физику и коллизии)
            Vector2 toTarget = target - _held.position;
            Vector2 desiredVel = toTarget * followGain;
            Vector2 velErr = desiredVel - _held.linearVelocity;
            Vector2 force = velErr * dampGain * _held.mass; // масштаб по массе

            // Кэп на итоговую скорость (мягко)
            Vector2 newVel = _held.linearVelocity + (force / _held.mass) * Time.fixedDeltaTime;
            if (newVel.sqrMagnitude > maxHoldSpeed * maxHoldSpeed)
            {
                newVel = newVel.normalized * maxHoldSpeed;
                // Подправим силу так, чтобы выйти ровно на кэп
                force = (newVel - _held.linearVelocity) * _held.mass / Time.fixedDeltaTime;
            }

            _held.AddForce(force, ForceMode2D.Force);
        }

        private void TryGrab()
        {
            var mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
            var dir = ((Vector2) mouseW - (Vector2) origin.position).normalized;

            // var hits = Physics2D.CircleCastAll(origin.position, pickRadius, dir, maxGrabRange, grabbable);

            int playerLayer = LayerMask.NameToLayer("Player");
            int layerMask = ~(1 << playerLayer); // invert mask = everything except Player
            var hit = Physics2D.Raycast(origin.position, dir, maxGrabRange, layerMask);
            if (hit.collider == null) return;
            // check layer
            if ((grabbable.value & (1 << hit.collider.gameObject.layer)) == 0) return;

            _held = hit.rigidbody;

            _savedGravity = _held.gravityScale;
            _savedAngularDrag = _held.angularDamping;
            _savedConstraints = _held.constraints;

            _held.gravityScale = 0f;
            _held.linearDamping = 8f;
            _held.angularDamping = 8f;
            _held.angularVelocity = 0f;
            _held.constraints = _savedConstraints | RigidbodyConstraints2D.FreezeRotation;

            foreach (var pc in playerColliders)
                if (pc && hit.collider)
                    Physics2D.IgnoreCollision(pc, hit.collider, true);
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
            var col = _held.GetComponent<Collider2D>();
            foreach (var pc in playerColliders)
                if (pc && col) Physics2D.IgnoreCollision(pc, col, false);

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

        // Вспомогательно: визуализация радиусов
        void OnDrawGizmosSelected()
        {
            if (!origin) origin = transform;
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(origin.position, maxGrabRange);
        }
    }
}
