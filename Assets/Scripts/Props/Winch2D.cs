using UnityEngine;

namespace Props
{
    /// <summary>
    /// The load-bearing half of a cable running over a shaft: a winch drum hauling one load,
    /// or two loads hung off the same shaft so they balance each other.
    ///
    /// A chain of links (<see cref="Rope2D"/>) is the wrong thing to hang weight from — it
    /// stretches like elastic and slips over the shaft. So the weight rides on one constraint
    /// solved here (lenA + ratio * lenB = const, exactly the pulley constraint), and the visible
    /// rope is left to do what a chain is good at: colliding, burning and parting.
    ///
    /// The two halves stay honest with each other: this component reports the cable tension,
    /// tears the rope when the tension goes past <see cref="breakTension"/>, and lets go of the
    /// load the moment the rope parts for any other reason — cut, ground down, burnt through.
    /// </summary>
    [DisallowMultipleComponent]
    public class Winch2D : MonoBehaviour
    {
        [Header("Shaft")]
        [Tooltip("Where the cable leaves the shaft on side A. Falls back to this transform.")]
        public Transform pulleyA;
        [Tooltip("Where it leaves on side B. Falls back to pulleyA — a single shaft both runs share.")]
        public Transform pulleyB;

        [Header("Loads")]
        public Rigidbody2D loadA;
        [Tooltip("Where the cable is tied to load A, in its local space.")]
        public Vector2 hookA;
        [Tooltip("Leave empty for a hoist: side B is the drum, and the motor decides its length.")]
        public Rigidbody2D loadB;
        public Vector2 hookB;
        [Tooltip("lenA + ratio * lenB is held constant. 2 = load B moves half as far, at half the pull.")]
        [Min(0.01f)] public float ratio = 1f;

        [Header("Cable")]
        [Tooltip("Held length. Left at 0, it is measured from where the loads start.")]
        public float cableLength;
        [Tooltip("Correction per step. 1 = rigid and jumpy, 0.2 = a cable with some give.")]
        [Range(0.05f, 1f)] public float stiffness = 0.6f;
        [Range(1, 8)] public int solverIterations = 4;

        [Header("Winch motor")]
        public bool motorized;
        [Tooltip("Cable metres per second at full input.")]
        [Min(0f)] public float motorSpeed = 1.2f;
        [Min(0.1f)] public float minLength = 0.5f;
        [Min(0.1f)] public float maxLength = 12f;
        [Tooltip("Tension the drum can pull against before it stalls. 0 = as strong as it needs to be.")]
        [Min(0f)] public float motorMaxTension;

        [Header("Breaking")]
        [Tooltip("Tension the cable parts at, in newtons. 0 = never parts from load.")]
        [Min(0f)] public float breakTension;
        [Tooltip("Tension held for this long counts as an overload. Filters out one-frame spikes.")]
        [Min(0f)] public float overloadGrace = 0.15f;

        [Header("Visible rope")]
        [Tooltip("The link chain along side A. Its payout follows the cable in hoist mode, and " +
                 "the load is dropped if it parts.")]
        public Rope2D ropeA;
        public Rope2D ropeB;

        [Header("Drum")]
        public Transform drum;
        [Min(0.01f)] public float drumRadius = 0.4f;

        /// <summary>-1 pays out, +1 reels in, 0 brakes. Drive this from a lever, a button, whatever.</summary>
        public float MotorInput { get; set; }

        /// <summary>Cable tension in newtons, as of the last physics step.</summary>
        public float Tension { get; private set; }

        /// <summary>True while the constraint is carrying the load.</summary>
        public bool Engaged { get; private set; }

        /// <summary>Length of the run on side A, hook to shaft.</summary>
        public float SideALength { get; private set; }

        /// <summary>How fast side A is paying out, in metres per second. Negative while reeling in.</summary>
        public float SideARate { get; private set; }

        /// <summary>Raised when the cable lets go — parted, cut, or released by hand.</summary>
        public event System.Action Snapped;

        private float _overloadFor;
        private float _drumAngle;

        private void Start()
        {
            if (!pulleyA) pulleyA = transform;
            if (!pulleyB) pulleyB = pulleyA;

            if (cableLength <= 0f) cableLength = MeasureLength();
            cableLength = Mathf.Clamp(cableLength, minLength, maxLength);

            Hook(ropeA);
            Hook(ropeB);
            Engaged = loadA != null;

            if (loadA) SideALength = Vector2.Distance(loadA.transform.TransformPoint(hookA), pulleyA.position);
        }

        private void OnDestroy()
        {
            Unhook(ropeA);
            Unhook(ropeB);
        }

        private void FixedUpdate()
        {
            if (!Engaged || !loadA) return;
            float dt = Time.fixedDeltaTime;

            if (motorized) DriveMotor(dt);

            Tension = 0f;
            for (int i = 0; i < solverIterations; i++)
                Tension += Solve(dt, i == 0);

            if (ropeA && loadB == null) ropeA.SetPayout(cableLength);

            float len = Vector2.Distance(loadA.transform.TransformPoint(hookA), pulleyA.position);
            SideARate = (len - SideALength) / dt;
            SideALength = len;

            CheckOverload(dt);
        }

        /// <summary>Drops the load: the constraint stops carrying and only the loose rope is left.</summary>
        public void Release()
        {
            if (!Engaged) return;
            Engaged = false;
            Tension = 0f;
            Snapped?.Invoke();
        }

        /// <summary>Parts the visible rope and drops the load.</summary>
        [ContextMenu("Snap Cable")]
        public void Snap()
        {
            // Tear the run that is actually taking the weight, at the shaft where it bends.
            var rope = ropeA && ropeA.IsIntact ? ropeA : ropeB;
            if (rope && rope.IsIntact) rope.CutNearest(pulleyA ? pulleyA.position : transform.position);
            Release();
        }

        private void DriveMotor(float dt)
        {
            float input = Mathf.Clamp(MotorInput, -1f, 1f);
            if (Mathf.Approximately(input, 0f)) return;                    // idle = braked, length held
            if (motorMaxTension > 0f && input > 0f && Tension > motorMaxTension) return;  // stalled under load

            float before = cableLength;
            cableLength = Mathf.Clamp(cableLength - input * motorSpeed * dt, minLength, maxLength);

            if (drum)
            {
                _drumAngle += (before - cableLength) / drumRadius * Mathf.Rad2Deg;
                drum.localRotation = Quaternion.Euler(0f, 0f, _drumAngle);
            }
        }

        /// <summary>
        /// One pass of the pulley constraint. Returns the tension it applied this pass.
        /// Only ever pulls: a cable shorter than its held length is slack and does nothing.
        /// </summary>
        private float Solve(float dt, bool report)
        {
            var a = MakeRow(loadA, hookA, pulleyA.position, 1f);
            var b = loadB ? MakeRow(loadB, hookB, pulleyB.position, ratio) : default;

            float c = a.len + (loadB ? ratio * b.len : 0f) - cableLength;
            if (c <= 0f) return 0f;                                        // slack

            float k = a.scale * a.scale * (a.invM + a.invI * a.ang * a.ang);
            if (loadB) k += b.scale * b.scale * (b.invM + b.invI * b.ang * b.ang);
            if (k <= 0f) return 0f;                                        // both ends immovable

            float cdot = a.scale * Rate(a) + (loadB ? b.scale * Rate(b) : 0f);
            float bias = stiffness * c / dt;
            float lambda = Mathf.Min(0f, -(cdot + bias) / k);              // pull only, never push

            Apply(a, lambda);
            if (loadB) Apply(b, lambda);

            return report ? -lambda / dt : 0f;
        }

        private void CheckOverload(float dt)
        {
            if (breakTension <= 0f) return;

            _overloadFor = Tension > breakTension ? _overloadFor + dt : 0f;
            if (_overloadFor >= overloadGrace) Snap();
        }

        private float MeasureLength()
        {
            if (!loadA) return 0f;
            float len = Vector2.Distance(loadA.transform.TransformPoint(hookA), pulleyA.position);
            if (loadB) len += ratio * Vector2.Distance(loadB.transform.TransformPoint(hookB), pulleyB.position);
            return len;
        }

        private void Hook(Rope2D rope)
        {
            if (rope) rope.Severed += OnRopeSevered;
        }

        private void Unhook(Rope2D rope)
        {
            if (rope) rope.Severed -= OnRopeSevered;
        }

        private void OnRopeSevered(int index) => Release();

        // ── Constraint plumbing ───────────────────────────────────────────────

        private struct Row
        {
            public Rigidbody2D rb;
            public Vector2 dir;    // from the hook towards the shaft
            public float len;
            public float ang;      // angular jacobian, radians
            public float invM, invI;
            public float scale;
        }

        private static Row MakeRow(Rigidbody2D rb, Vector2 hookLocal, Vector2 pulley, float scale)
        {
            Vector2 hook = rb.transform.TransformPoint(hookLocal);
            Vector2 d = pulley - hook;
            float len = d.magnitude;
            Vector2 dir = len > 1e-4f ? d / len : Vector2.up;

            bool dynamic = rb.bodyType == RigidbodyType2D.Dynamic;
            Vector2 r = hook - rb.worldCenterOfMass;

            return new Row
            {
                rb = rb,
                dir = dir,
                len = len,
                ang = Cross(r, -dir),
                invM = dynamic && rb.mass > 0f ? 1f / rb.mass : 0f,
                invI = dynamic && rb.inertia > 0f ? 1f / rb.inertia : 0f,
                scale = scale,
            };
        }

        /// <summary>How fast this end is letting the cable out, in metres per second.</summary>
        private static float Rate(Row row) =>
            Vector2.Dot(-row.dir, row.rb.linearVelocity) + row.ang * row.rb.angularVelocity * Mathf.Deg2Rad;

        private static void Apply(Row row, float lambda)
        {
            float j = row.scale * lambda;
            row.rb.linearVelocity += row.invM * j * -row.dir;
            row.rb.angularVelocity += row.invI * j * row.ang * Mathf.Rad2Deg;
        }

        private static float Cross(Vector2 a, Vector2 b) => a.x * b.y - a.y * b.x;

        private void OnDrawGizmosSelected()
        {
            Transform pa = pulleyA ? pulleyA : transform;
            Transform pb = pulleyB ? pulleyB : pa;

            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(pa.position, drumRadius);
            if (loadA) Gizmos.DrawLine(loadA.transform.TransformPoint(hookA), pa.position);
            if (loadB) Gizmos.DrawLine(loadB.transform.TransformPoint(hookB), pb.position);
        }
    }
}
