using UnityEngine;

namespace Props
{
    /// <summary>
    /// The wheel a rope is thrown over: a disc on a pin, free to turn.
    ///
    /// A wheel that a real link chain drapes across needs no code at all — a dynamic body with a
    /// circle collider, a hinge to the world and some friction is the whole thing, and
    /// <see cref="Reset"/> below sets exactly that up. The code is here for the other case: when a
    /// <see cref="Winch2D"/> is carrying the load, the cable never rubs the wheel, so nothing
    /// would turn it. Then the wheel is driven from how fast the cable is running instead, which
    /// is what it would have done anyway, minus the slip.
    ///
    /// Where the rope leaves the wheel is a fixed point on the rim (<see cref="exitA"/>,
    /// <see cref="exitB"/>) — hand those to the winch as its shaft points. The arc the rope wraps
    /// over the top never changes length, so leaving it out of the cable maths costs nothing.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    [AddComponentMenu("PhysFun/Pulley Wheel")]
    public sealed class PulleyWheel2D : MonoBehaviour
    {
        [Header("Wheel")]
        [Tooltip("Left at 0, it is read off the circle collider.")]
        [SerializeField] private float radius;

        [Header("Driven by a cable")]
        [Tooltip("Leave empty to let the wheel spin on its own, from whatever actually touches it.")]
        [SerializeField] private Winch2D winch;

        [Tooltip("Which way the wheel turns as the cable pays out. Flip it if it spins backwards.")]
        [SerializeField] private bool invert;

        [Tooltip("How quickly the wheel catches up to the cable. Lower = it visibly spins up and " +
                 "coasts down rather than snapping to speed.")]
        [SerializeField, Min(0f)] private float spinUp = 20f;

        [Header("Rope exits")]
        [Tooltip("Rim points where the two runs leave the wheel. Optional — for wiring a winch to.")]
        [SerializeField] private Transform exitA;
        [SerializeField] private Transform exitB;

        private Rigidbody2D _rb;
        private float _spin;   // degrees per second

        /// <summary>Wheel radius in world units.</summary>
        public float Radius => radius > 0f ? radius : 0.5f;

        public Transform ExitA => exitA;
        public Transform ExitB => exitB;

        private void Reset()
        {
            var rb = GetComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Dynamic;
            rb.gravityScale = 0f;          // hangs on its pin, not on gravity
            rb.angularDamping = 0.05f;     // coasts, but does not spin forever
            rb.freezeRotation = false;

            if (!TryGetComponent<CircleCollider2D>(out var col))
                col = gameObject.AddComponent<CircleCollider2D>();
            radius = col.radius * Mathf.Abs(transform.lossyScale.x);

            // Pinned to the world at its centre: turns freely, goes nowhere.
            if (!TryGetComponent<HingeJoint2D>(out var hinge))
                hinge = gameObject.AddComponent<HingeJoint2D>();
            hinge.autoConfigureConnectedAnchor = false;
            hinge.connectedBody = null;
            hinge.anchor = Vector2.zero;
            hinge.connectedAnchor = transform.position;
            hinge.useLimits = false;
        }

        private void Awake()
        {
            _rb = GetComponent<Rigidbody2D>();
            if (radius <= 0f && TryGetComponent<CircleCollider2D>(out var col))
                radius = col.radius * Mathf.Abs(transform.lossyScale.x);
        }

        private void FixedUpdate()
        {
            if (!winch) return;   // free-spinning: the solver is already doing the work

            // Cable metres per second become rim degrees per second.
            float target = winch.SideARate / Radius * Mathf.Rad2Deg * (invert ? -1f : 1f);
            _spin = spinUp > 0f
                ? Mathf.Lerp(_spin, target, 1f - Mathf.Exp(-spinUp * Time.fixedDeltaTime))
                : target;

            _rb.angularVelocity = _spin;
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1f, 0.85f, 0.3f);
            Gizmos.DrawWireSphere(transform.position, Radius);
            if (exitA) Gizmos.DrawWireSphere(exitA.position, Radius * 0.12f);
            if (exitB) Gizmos.DrawWireSphere(exitB.position, Radius * 0.12f);
        }
    }
}
