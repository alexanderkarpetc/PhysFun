using System.Collections.Generic;
using UnityEngine;

namespace Props
{
    /// <summary>
    /// A physical rope: a chain of thin rigid bodies linked by hinges, drawn as one continuous
    /// line. Colliders, so it can be hit, burnt and ground through; hinges, so it can part.
    ///
    /// The shape is drawn as <see cref="points"/> — a path laid out in the scene view — and the
    /// links are cut from it every <see cref="segmentLength"/> metres. Points are there to say
    /// where the rope goes, not how finely it is built: adding one changes the route, never the
    /// resolution. Anchor the ends to transforms to tie the rope to something that moves.
    ///
    /// A rope is a bad thing to hang weight from — see <see cref="Winch2D"/> for that.
    /// </summary>
    [DisallowMultipleComponent]
    public class Rope2D : MonoBehaviour
    {
        [Header("Path (local space)")]
        [Tooltip("Route the rope follows. Drag the dots in the scene view; the + between them adds one.")]
        public List<Vector2> points = new() { new Vector2(0f, 0f), new Vector2(0f, -3f) };

        [Header("Anchors")]
        [Tooltip("Optional. The first point rides on this transform, and the rope is tied to its body.")]
        public Transform anchorA;
        [Tooltip("Optional. Same for the last point.")]
        public Transform anchorB;
        [Tooltip("Tie the first point down. Off = that end hangs free.")]
        public bool pinStart = true;
        [Tooltip("Tie the last point down. Off = that end hangs free.")]
        public bool pinEnd;

        [Header("Links")]
        [Tooltip("Target length of one link. The path is cut into whole links, so the real length " +
                 "lands near this, not exactly on it.")]
        [Min(0.05f)] public float segmentLength = 0.3f;
        [Tooltip("Ceiling on link count, so a long path cannot quietly spawn hundreds of bodies.")]
        [Min(2)] public int maxLinks = 200;
        [Min(0.01f)] public float thickness = 0.08f;
        [Tooltip("Collider length as a fraction of the link. Below 1 the links stop grinding " +
                 "against each other, which is most of what makes a chain buzz.")]
        [Range(0.5f, 1f)] public float colliderFill = 0.85f;

        [Header("Physics")]
        [Min(0.001f)] public float massPerSegment = 0.15f;
        [Tooltip("Higher = the rope settles faster and swings less like a whip.")]
        [Min(0f)] public float angularDamping = 2f;
        [Min(0f)] public float linearDamping = 0.15f;
        [Tooltip("Links collide with the world. Off = the rope passes through everything but its anchors.")]
        public bool collideWithWorld = true;
        [Tooltip("Distant links collide with each other, so the rope can pile up and knot. " +
                 "Expensive, and the usual reason a rope shakes itself apart.")]
        public bool selfCollision;
        public PhysicsMaterial2D segmentMaterial;

        [Header("Tension")]
        [Tooltip("Run an extra length pass over the chain every step. Unity's solver gives up on " +
                 "a light rope pulled by something heavy — this is what stops it stretching.")]
        public bool inextensible = true;
        [Tooltip("Passes along the chain per step. More = stiffer rope, linear cost.")]
        [Range(1, 16)] public int tensionIterations = 6;
        [Tooltip("Share of the leftover stretch pulled out by moving the links outright. " +
                 "0 = velocity only (softer), 1 = snapped straight (can shove links through thin walls).")]
        [Range(0f, 1f)] public float stretchCorrection = 0.4f;

        [Header("Breaking")]
        [Tooltip("Load the rope parts at, in newtons. 0 = it never parts from being pulled. " +
                 "Roughly: a hanging mass of m kg pulls m * 9.81 N.")]
        [Min(0f)] public float maxTension;
        [Tooltip("Tension has to hold for this long to count. Filters out one-frame spikes from impacts.")]
        [Min(0f)] public float overloadGrace = 0.1f;
        [Tooltip("Also let Unity break the hinges on raw joint force. Redundant with maxTension " +
                 "and far less predictable — off by default.")]
        public bool breakable;
        [Min(0f)] public float breakForce = 400f;

        [Header("End weight")]
        [Tooltip("Mass of the last link. Telekinesis only grabs bodies above its minMass, so a " +
                 "heavier tip makes the rope draggable and keeps it hanging straight. Keep it " +
                 "within ~10x the link mass or the chain will stretch and jitter.")]
        [Min(0f)] public float endWeightMass;

        [Header("Rendering")]
        public bool render = true;
        public Color color = new(0.62f, 0.48f, 0.28f);
        [Tooltip("Drawn width. Defaults to the collider thickness.")]
        [Min(0f)] public float renderWidth;
        public Material lineMaterial;
        public string sortingLayer = "Default";
        public int sortingOrder;

        [Header("Setup")]
        public bool buildOnAwake = true;

        [SerializeField, HideInInspector] private Transform _root;
        [SerializeField, HideInInspector] private LineRenderer _line;

        private readonly List<Rigidbody2D> _links = new();
        private HingeJoint2D _anchorJoint;   // pin of the topmost payed-out link, re-made while spooling
        private float _linkLength;           // actual link length after the path was divided up
        private Rigidbody2D _pinBodyA, _pinBodyB;   // what the ends are tied to, if anything
        private Vector2 _pinLocalA, _pinLocalB;     // tie point, in that body's space or in the world
        private bool _pinnedA, _pinnedB;
        private float _overloadFor;
        private int _worstLink = -1;
        private int _first;                  // first link off the drum; the ones before it are spooled up
        private int _severed = -1;

        /// <summary>Links in path order. Empty until built.</summary>
        public IReadOnlyList<Rigidbody2D> Links => _links;

        /// <summary>The far end of the rope — hook a load onto this.</summary>
        public Rigidbody2D FreeEnd => _links.Count > 0 ? _links[^1] : null;

        /// <summary>Length of one built link. Near <see cref="segmentLength"/>, never exactly it.</summary>
        public float LinkLength => _linkLength > 0f ? _linkLength : segmentLength;

        /// <summary>False once a link has parted, by overload or by being cut.</summary>
        public bool IsIntact => _severed < 0;

        /// <summary>Index of the link the rope parted at, or -1 while intact.</summary>
        public int SeveredAt => _severed;

        /// <summary>Raised once, with the index of the link that parted.</summary>
        public event System.Action<int> Severed;

        /// <summary>True while the rope is destroying its own links, so that does not read as a break.</summary>
        internal bool IsTearingDown { get; private set; }

        /// <summary>Length currently hanging off the anchor — the rest is spooled up.</summary>
        public float PayedOutLength => (_links.Count - _first) * LinkLength;

        private void Awake()
        {
            if (buildOnAwake && Application.isPlaying) Build();
        }

        private void LateUpdate()
        {
            if (!render || _line == null || _links.Count == 0) return;
            UpdateLine();
        }

        // ── Path ──────────────────────────────────────────────────────────────

        /// <summary>The path in world space, with the anchors moved onto their transforms.</summary>
        public List<Vector2> WorldPath()
        {
            var path = new List<Vector2>(Mathf.Max(2, points.Count));
            for (int i = 0; i < points.Count; i++) path.Add(transform.TransformPoint(points[i]));
            if (path.Count < 2) path.Add(path.Count > 0 ? path[0] + Vector2.down : Vector2.zero);

            if (anchorA) path[0] = anchorA.position;
            if (anchorB) path[^1] = anchorB.position;
            return path;
        }

        /// <summary>Total length of the drawn path.</summary>
        public float PathLength()
        {
            var p = WorldPath();
            float len = 0f;
            for (int i = 0; i < p.Count - 1; i++) len += Vector2.Distance(p[i], p[i + 1]);
            return len;
        }

        /// <summary>How many links the current path would be cut into.</summary>
        public int PlannedLinkCount() =>
            Mathf.Clamp(Mathf.RoundToInt(PathLength() / Mathf.Max(0.05f, segmentLength)), 1, maxLinks);

        /// <summary>
        /// Walks the path and drops a point every <paramref name="step"/> metres. Link count comes
        /// from the length of the route, not from how many points were placed along it.
        /// </summary>
        private static List<Vector2> Resample(List<Vector2> path, int count, out float step)
        {
            float total = 0f;
            for (int i = 0; i < path.Count - 1; i++) total += Vector2.Distance(path[i], path[i + 1]);
            step = total / count;

            var outPts = new List<Vector2>(count + 1) { path[0] };
            int seg = 0;
            float walked = 0f;             // distance covered inside the current path segment

            for (int i = 1; i <= count; i++)
            {
                float want = step;
                while (seg < path.Count - 1)
                {
                    float segLen = Vector2.Distance(path[seg], path[seg + 1]);
                    float left = segLen - walked;
                    if (left >= want || seg == path.Count - 2)
                    {
                        walked += want;
                        float t = segLen > 1e-5f ? Mathf.Clamp01(walked / segLen) : 1f;
                        outPts.Add(Vector2.Lerp(path[seg], path[seg + 1], t));
                        break;
                    }
                    want -= left;
                    walked = 0f;
                    seg++;
                }
            }

            while (outPts.Count < count + 1) outPts.Add(path[^1]);
            return outPts;
        }

        // ── Build ─────────────────────────────────────────────────────────────

        [ContextMenu("Rebuild Rope")]
        public void Build()
        {
            ClearBuilt();

            var path = WorldPath();
            int count = PlannedLinkCount();
            var nodes = Resample(path, count, out _linkLength);
            if (_linkLength <= 1e-4f) return;

            _root = new GameObject("RopeLinks").transform;
            _root.SetParent(transform, worldPositionStays: false);

            for (int i = 0; i < count; i++)
            {
                Vector2 from = nodes[i];
                Vector2 to = nodes[i + 1];
                Vector2 dir = to - from;
                float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;

                var go = new GameObject($"Link_{i:000}");
                go.transform.SetParent(_root, worldPositionStays: false);
                go.transform.SetPositionAndRotation((from + to) * 0.5f, Quaternion.Euler(0f, 0f, angle));
                go.layer = gameObject.layer;

                var rb = go.AddComponent<Rigidbody2D>();
                rb.useAutoMass = false;
                rb.mass = (i == count - 1 && endWeightMass > 0f) ? endWeightMass : massPerSegment;
                rb.angularDamping = angularDamping;
                rb.linearDamping = linearDamping;
                rb.interpolation = RigidbodyInterpolation2D.Interpolate;
                // Discrete on purpose: continuous detection on a crowd of small light bodies is
                // both expensive and a jitter source, and a rope link never outruns its own length.
                rb.collisionDetectionMode = CollisionDetectionMode2D.Discrete;

                var col = go.AddComponent<CapsuleCollider2D>();
                col.direction = CapsuleDirection2D.Horizontal;
                col.size = new Vector2(Mathf.Max(thickness, _linkLength * colliderFill), thickness);
                col.sharedMaterial = segmentMaterial;
                col.isTrigger = !collideWithWorld;

                var link = go.AddComponent<RopeLink>();
                link.rope = this;
                link.index = i;

                _links.Add(rb);
            }

            float half = _linkLength * 0.5f;
            for (int i = 0; i < _links.Count - 1; i++)
                Hinge(_links[i], new Vector2(half, 0f), _links[i + 1], new Vector2(-half, 0f));

            _first = 0;
            _severed = -1;
            _overloadFor = 0f;
            if (pinStart)
            {
                _anchorJoint = PinToAnchor(_links[0], new Vector2(-half, 0f), anchorA, nodes[0]);
                RecordPin(ref _pinnedA, ref _pinBodyA, ref _pinLocalA, anchorA, nodes[0]);
            }
            if (pinEnd)
            {
                PinToAnchor(_links[^1], new Vector2(half, 0f), anchorB, nodes[^1]);
                RecordPin(ref _pinnedB, ref _pinBodyB, ref _pinLocalB, anchorB, nodes[^1]);
            }

            IgnoreInternalCollisions();
            if (render) SetupLine();
        }

        [ContextMenu("Clear Rope")]
        public void ClearBuilt()
        {
            IsTearingDown = true;
            _links.Clear();
            _anchorJoint = null;
            _pinnedA = _pinnedB = false;
            _pinBodyA = _pinBodyB = null;
            _first = 0;
            _severed = -1;
            if (_root) DestroyBuilt(_root.gameObject);
            if (_line) DestroyBuilt(_line.gameObject);
            _root = null;
            _line = null;
            IsTearingDown = false;
        }

        // ── Cutting ───────────────────────────────────────────────────────────

        /// <summary>Cuts the rope between links <paramref name="index"/> and index + 1.</summary>
        public void Cut(int index)
        {
            if (index < 0 || index >= _links.Count - 1) return;
            foreach (var j in _links[index].GetComponents<HingeJoint2D>())
                if (j.connectedBody == _links[index + 1])
                    DestroyBuilt(j);
            NotifyParted(index);
        }

        /// <summary>Cuts the rope at the link closest to <paramref name="worldPoint"/>.</summary>
        public void CutNearest(Vector2 worldPoint)
        {
            int best = -1;
            float bestSqr = float.MaxValue;
            for (int i = _first; i < _links.Count - 1; i++)
            {
                float d = ((Vector2)_links[i].transform.position - worldPoint).sqrMagnitude;
                if (d < bestSqr) { bestSqr = d; best = i; }
            }
            if (best >= 0) Cut(best);
        }

        /// <summary>
        /// A link's joint parted — by <see cref="Cut"/>, by overload, or by whatever chewed
        /// through it. Reported once; anything load-bearing on this rope should let go.
        /// </summary>
        internal void NotifyParted(int index)
        {
            if (_severed >= 0) return;
            _severed = index;
            Severed?.Invoke(index);
        }

        // ── Spooling ──────────────────────────────────────────────────────────

        /// <summary>
        /// How much rope hangs off the anchor; the rest is treated as wound onto the drum and
        /// switched off. Only meaningful for a rope pinned at one end (a hoist cable).
        /// Quantised to whole links — sub-link slack is taken up by the cable constraint.
        /// </summary>
        public void SetPayout(float length)
        {
            if (_links.Count == 0 || _severed >= 0) return;   // a parted rope no longer spools

            int wanted = Mathf.Clamp(Mathf.CeilToInt(length / LinkLength), 1, _links.Count);
            int first = _links.Count - wanted;
            if (first == _first) return;

            float half = LinkLength * 0.5f;

            // Reeling out: wake links back up at the anchor, in order, so they feed off the drum.
            for (int i = _first - 1; i >= first; i--)
            {
                var below = _links[i + 1].transform;
                _links[i].transform.SetPositionAndRotation(
                    below.TransformPoint(new Vector3(-LinkLength, 0f, 0f)), below.rotation);
                _links[i].gameObject.SetActive(true);
                _links[i].linearVelocity = _links[i + 1].linearVelocity;
                _links[i].angularVelocity = 0f;
            }

            // Reeling in: swallow links at the anchor.
            for (int i = _first; i < first; i++)
                _links[i].gameObject.SetActive(false);

            _first = first;

            if (_anchorJoint) DestroyBuilt(_anchorJoint);
            _anchorJoint = PinToAnchor(_links[_first], new Vector2(-half, 0f), anchorA,
                                       anchorA ? (Vector2)anchorA.position : WorldPath()[0]);
        }

        // ── Tension ───────────────────────────────────────────────────────────

        private void FixedUpdate()
        {
            if (!inextensible || _links.Count < 1) return;
            SolveTension(Time.fixedDeltaTime);
        }

        /// <summary>
        /// Holds the chain to its built length, and reads off what that costs.
        ///
        /// Unity solves a hinge chain from both ends inwards a fixed number of times, so a light
        /// rope pulled by something heavy — a player walking off with the end of it — never
        /// converges: the links stretch apart, snap back, and the whole thing rings. This is a
        /// Gauss-Seidel pass over the same chain treating each link as a rope segment that can
        /// pull but not push, which is the part the hinges are bad at. The hinges are still what
        /// hold the rope together; this only takes the stretch out.
        ///
        /// The impulse each link needs is its tension, so breaking under load falls out of the
        /// same pass for free — and it is a far steadier number than joint break force, which
        /// reads whatever the solver happened to be doing that frame.
        /// </summary>
        private void SolveTension(float dt)
        {
            float rest = LinkLength;
            float half = rest * 0.5f;
            float peak = 0f;
            int worst = -1;

            for (int it = 0; it < tensionIterations; it++)
            {
                // Alternate direction each pass: a one-way sweep converges from the anchor end
                // and leaves the far end soft.
                bool forward = (it & 1) == 0;

                if (_pinnedA) Pull(null, PinPoint(_pinBodyA, _pinLocalA), _pinBodyA, _links[_first], half, dt, ref peak, ref worst, _first);

                for (int k = 0; k < _links.Count - _first - 1; k++)
                {
                    int i = forward ? _first + k : _links.Count - 2 - k;
                    if (i < _first || i == _severed) continue;   // never pull across a parted link
                    Pull(_links[i], default, null, _links[i + 1], rest, dt, ref peak, ref worst, i);
                }

                if (_pinnedB && _severed < 0)
                    Pull(null, PinPoint(_pinBodyB, _pinLocalB), _pinBodyB, _links[^1], half, dt, ref peak, ref worst, _links.Count - 1);
            }

            _worstLink = worst;
            CheckOverload(peak, dt);
        }

        /// <summary>
        /// One pull between two points that must not drift further apart than <paramref name="rest"/>.
        /// Pass <paramref name="a"/> as null for a fixed end, and give its world point instead.
        /// Returns nothing; the tension it took is folded into <paramref name="peak"/>.
        /// </summary>
        private void Pull(Rigidbody2D a, Vector2 aPoint, Rigidbody2D aBody, Rigidbody2D b,
                          float rest, float dt, ref float peak, ref int worst, int index)
        {
            Rigidbody2D bodyA = a ? a : aBody;                       // may still be null: pinned to the world
            Vector2 pa = a ? a.worldCenterOfMass : aPoint;
            Vector2 pb = b.worldCenterOfMass;

            Vector2 d = pb - pa;
            float len = d.magnitude;
            if (len < 1e-5f || len <= rest) return;                  // slack: a rope pulls, it never pushes
            Vector2 n = d / len;

            float invA = InvMass(bodyA);
            float invB = InvMass(b);
            float k = invA + invB;
            if (k <= 0f) return;

            float cdot = Vector2.Dot(n, b.linearVelocity - (bodyA ? bodyA.linearVelocity : Vector2.zero));
            float lambda = -cdot / k;
            if (lambda > 0f) lambda = 0f;                            // pull only

            b.linearVelocity += n * (lambda * invB);
            if (bodyA) bodyA.linearVelocity -= n * (lambda * invA);

            // Whatever stretch the velocity pass could not reach, take out of the positions.
            if (stretchCorrection > 0f)
            {
                float pull = (len - rest) * stretchCorrection;
                b.position -= n * (pull * invB / k);
                if (bodyA) bodyA.position += n * (pull * invA / k);
            }

            float tension = -lambda / dt;
            if (tension > peak) { peak = tension; worst = index; }
        }

        private void CheckOverload(float peak, float dt)
        {
            if (maxTension <= 0f || _severed >= 0) return;

            _overloadFor = peak > maxTension ? _overloadFor + dt : 0f;
            if (_overloadFor < overloadGrace) return;

            // Parts where it was pulling hardest, which is where a real rope goes.
            Cut(Mathf.Clamp(_worstLink, _first, _links.Count - 2));
        }

        private static float InvMass(Rigidbody2D rb) =>
            rb && rb.bodyType == RigidbodyType2D.Dynamic && rb.mass > 0f ? 1f / rb.mass : 0f;

        private static Vector2 PinPoint(Rigidbody2D body, Vector2 local) =>
            body ? (Vector2)body.transform.TransformPoint(local) : local;

        private static void RecordPin(ref bool pinned, ref Rigidbody2D body, ref Vector2 local,
                                      Transform anchor, Vector2 worldPoint)
        {
            pinned = true;
            body = anchor ? anchor.GetComponentInParent<Rigidbody2D>() : null;
            local = body ? (Vector2)body.transform.InverseTransformPoint(worldPoint) : worldPoint;
        }

        // ── Joints ────────────────────────────────────────────────────────────

        private void Hinge(Rigidbody2D a, Vector2 anchorOnA, Rigidbody2D b, Vector2 anchorOnB)
        {
            var hj = a.gameObject.AddComponent<HingeJoint2D>();
            hj.autoConfigureConnectedAnchor = false;
            hj.connectedBody = b;
            hj.anchor = anchorOnA;
            hj.connectedAnchor = anchorOnB;
            hj.enableCollision = false;
            if (breakable) hj.breakForce = breakForce;
        }

        private HingeJoint2D PinToAnchor(Rigidbody2D link, Vector2 anchorOnLink, Transform anchor, Vector2 worldPoint)
        {
            var hj = link.gameObject.AddComponent<HingeJoint2D>();
            hj.autoConfigureConnectedAnchor = false;
            hj.anchor = anchorOnLink;
            hj.enableCollision = false;

            var anchorRb = anchor ? anchor.GetComponentInParent<Rigidbody2D>() : null;
            if (anchorRb)
            {
                hj.connectedBody = anchorRb;
                hj.connectedAnchor = anchorRb.transform.InverseTransformPoint(worldPoint);
            }
            else
            {
                hj.connectedBody = null;                  // pinned to the world
                hj.connectedAnchor = worldPoint;
            }
            if (breakable) hj.breakForce = breakForce;
            return hj;
        }

        private void IgnoreInternalCollisions()
        {
            for (int i = 0; i < _links.Count; i++)
            {
                var ci = _links[i].GetComponent<Collider2D>();
                // Neighbours always overlap at the hinge; further links only when self-collision is off.
                int last = selfCollision ? Mathf.Min(i + 2, _links.Count - 1) : _links.Count - 1;
                for (int j = i + 1; j <= last; j++)
                    Physics2D.IgnoreCollision(ci, _links[j].GetComponent<Collider2D>(), true);
            }

            // Whatever the ends are tied to sits inside the first and last link. Left colliding,
            // the pinned link spends every frame being pushed out of its own anchor.
            IgnoreAnchor(anchorA, _links[0]);
            IgnoreAnchor(anchorB, _links[^1]);
        }

        private static void IgnoreAnchor(Transform anchor, Rigidbody2D link)
        {
            if (!anchor) return;
            var linkCol = link.GetComponent<Collider2D>();
            foreach (var col in anchor.GetComponentsInParent<Collider2D>())
                Physics2D.IgnoreCollision(linkCol, col, true);
        }

        // ── Rendering ─────────────────────────────────────────────────────────

        private void SetupLine()
        {
            var go = new GameObject("RopeLine");
            go.transform.SetParent(transform, worldPositionStays: false);
            _line = go.AddComponent<LineRenderer>();
            _line.useWorldSpace = true;
            _line.textureMode = LineTextureMode.Tile;
            _line.numCapVertices = 2;
            _line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _line.receiveShadows = false;
            _line.sortingLayerName = sortingLayer;
            _line.sortingOrder = sortingOrder;

            float w = renderWidth > 0f ? renderWidth : thickness;
            _line.startWidth = w;
            _line.endWidth = w;

            _line.sharedMaterial = lineMaterial ? lineMaterial : new Material(Shader.Find("Sprites/Default"));
            _line.startColor = color;
            _line.endColor = color;

            UpdateLine();
        }

        private void UpdateLine()
        {
            float half = LinkLength * 0.5f;
            int shown = _links.Count - _first;
            if (_line.positionCount != shown + 1) _line.positionCount = shown + 1;

            for (int i = 0; i < shown; i++)
                _line.SetPosition(i, _links[_first + i].transform.TransformPoint(new Vector3(-half, 0f, 0f)));

            _line.SetPosition(shown, _links[^1].transform.TransformPoint(new Vector3(half, 0f, 0f)));
        }

        private static void DestroyBuilt(Object o)
        {
            if (!o) return;
#if UNITY_EDITOR
            if (!Application.isPlaying) { DestroyImmediate(o); return; }
#endif
            Destroy(o);
        }

        private void OnDrawGizmosSelected()
        {
            if (_links.Count > 0) return;   // built: the line renderer already shows it

            var path = WorldPath();
            Gizmos.color = color;
            for (int i = 0; i < path.Count - 1; i++) Gizmos.DrawLine(path[i], path[i + 1]);
        }
    }
}
