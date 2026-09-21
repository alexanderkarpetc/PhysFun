using System.Collections.Generic;
using Gore;
using Phys.Paint;
using UnityEngine;

namespace Ragdolls
{
    /// <summary>
    /// A spawned corpse. The prefab is built in the rest pose by the Noita importer; this
    /// component snaps the pieces onto whichever animation frame the creature died on and
    /// then leaves them to the physics engine.
    ///
    /// The hierarchy is deliberately flat — every piece is a direct child of the root and
    /// poses are absolute — so applying a pose never has to walk the parent chain. What
    /// holds the corpse together is the hinge joints, not the transform parenting.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class Ragdoll : MonoBehaviour
    {
        [SerializeField] private RagdollDefinition definition;

        /// <summary>Index-parallel with <see cref="RagdollDefinition.parts"/>.</summary>
        [SerializeField] private Rigidbody2D[] bodies;

        [Header("Behaviour")]
        [Tooltip("Limbs of the same corpse colliding with each other mostly produces jitter.")]
        [SerializeField] private bool selfCollision;

        [Tooltip("Seconds before the corpse despawns. 0 keeps it around.")]
        [SerializeField] private float destroyAfter;

        [Header("Gore")]
        [Tooltip("Whether a hard enough pull takes limbs off. Off leaves the corpse in one " +
                 "piece whatever happens to it.")]
        [SerializeField] private bool tearable = true;

        [Tooltip("Force a joint has to carry before the limb comes off, in newtons. 0 uses the " +
                 "shared Gore config — only fill this in for something that has to hold " +
                 "together better or worse than the rest of the world.")]
        [SerializeField] private float tearForce;

        [Tooltip("Twist a joint has to carry before the limb comes off. 0 uses the Gore config.")]
        [SerializeField] private float tearTorque;

        [Tooltip("Limbs this corpse may lose. -1 uses the Gore config.")]
        [SerializeField] private int maxTears = -1;

        [Tooltip("Blood colour for this creature. Leave at alpha 0 for the Gore config's own.")]
        [SerializeField] private Color32 bloodColor;

        private bool _flipped;

        // Every hinge holding the corpse together, and how many physics steps each has been
        // over its threshold. Cached because tearing has to look at all of them every step and
        // GetComponents allocates.
        private readonly List<AnchoredJoint2D> _joints = new();
        private readonly List<int> _strain = new();
        private int _tears;

        // Applying the death pose teleports every piece and re-creates every joint, which the
        // solver reports as an enormous load for a step or two. Nothing may tear until that has
        // settled or every corpse arrives in pieces.
        private float _tearArmedAt;

        // Colliders per piece, and where each body sits in `bodies`. Both exist for the
        // collision bookkeeping below, which has to talk about pieces rather than about the
        // flat list of colliders the constructor ignores pairs in.
        private Collider2D[][] _pieceColliders;
        private readonly Dictionary<Rigidbody2D, int> _bodyIndex = new();

        // Piece pairs whose collision has already been handed back, so a later tear does not
        // queue the same pair again.
        private bool[,] _released;

        /// <summary>A pair of colliders waiting for the two pieces to stop overlapping.</summary>
        private struct PendingPair
        {
            public Collider2D A, B;
            public float GiveUpAt;
        }

        private readonly List<PendingPair> _pending = new();
        private float _nextPendingCheck;

        /// <summary>How often the waiting pairs are looked at. They only have to settle, not be tracked.</summary>
        private const float PendingInterval = 0.2f;

        /// <summary>
        /// Seconds a pair may stay overlapped before its collision is handed back regardless.
        /// By then the corpse has come to rest, and Box2D corrects penetration at a limited
        /// speed — so a late hand-back pushes the pieces apart over a few frames instead of
        /// launching them, which is a better outcome than a limb that ghosts forever.
        /// </summary>
        private const float PendingGiveUp = 6f;

        public RagdollDefinition Definition => definition;
        public IReadOnlyList<Rigidbody2D> Bodies => bodies;

        /// <summary>Limbs this corpse has lost so far.</summary>
        public int Tears => _tears;

        private Color32 Blood => bloodColor.a == 0 ? GoreConfig.Shared.dropColor : bloodColor;

        private void Awake()
        {
            CachePieces();
            if (!selfCollision) IgnoreSelfCollisions();
            if (destroyAfter > 0f) Destroy(gameObject, destroyAfter);

            CacheJoints();
            _tearArmedAt = Time.time + 0.25f;
        }

        private void CacheJoints()
        {
            _joints.Clear();
            _strain.Clear();
            if (bodies == null) return;

            foreach (var rb in bodies)
            {
                if (!rb) continue;
                foreach (var joint in rb.GetComponents<AnchoredJoint2D>())
                {
                    _joints.Add(joint);
                    _strain.Add(0);
                }
            }
        }

        /// <summary>Pose the corpse from the sprite the creature was showing when it died.</summary>
        public void ApplySpritePose(Sprite sprite, bool flipX)
        {
            if (sprite != null && RagdollDefinition.TryParseSpriteName(sprite.name, out var anim, out int frame))
                ApplyPose(anim, frame, flipX);
            else
                ApplyPose(null, 0, flipX);
        }

        /// <summary>
        /// Move every piece onto <paramref name="anim"/>/<paramref name="frame"/>. Falls back to
        /// the rest pose when that animation was never baked.
        /// </summary>
        public void ApplyPose(string anim, int frame, bool flipX)
        {
            if (definition == null || bodies == null) return;

            var pose = definition.FindPose(anim, frame);
            if (pose == null) return;

            SetFlipped(flipX);
            float sign = flipX ? -1f : 1f;

            int count = Mathf.Min(bodies.Length, definition.parts.Count);
            for (int i = 0; i < count; i++)
            {
                var rb = bodies[i];
                if (!rb) continue;

                Vector2 px = pose.positionsPx != null && i < pose.positionsPx.Length
                    ? pose.positionsPx[i]
                    : definition.parts[i].pivotPx;
                float rot = pose.rotations != null && i < pose.rotations.Length ? pose.rotations[i] : 0f;

                Vector2 local = definition.PixelToLocal(px);
                local.x *= sign;
                rot *= sign;

                var t = rb.transform;
                t.localPosition = new Vector3(local.x, local.y, t.localPosition.z);
                t.localRotation = Quaternion.Euler(0f, 0f, rot);

                // Box2D keeps its own copy of the transform — push it across explicitly so
                // the first simulation step does not snap the corpse back to the prefab pose.
                rb.position = t.position;
                rb.rotation = t.eulerAngles.z;
            }

            RebaseJoints();

            // Teleporting every piece and re-creating every joint spikes the solver; hold the
            // tear check off until that has washed through.
            _tearArmedAt = Time.time + 0.25f;
        }

        /// <summary>
        /// A hinge measures its limits against the angle the two bodies had when the joint was
        /// created — which, for a freshly instantiated prefab, is the rest pose. Toggling the
        /// joints re-captures that reference on the death pose instead, so a corpse that died
        /// mid-stride does not immediately snap its legs back together.
        /// </summary>
        private void RebaseJoints()
        {
            foreach (var rb in bodies)
            {
                if (!rb) continue;
                foreach (var joint in rb.GetComponents<AnchoredJoint2D>())
                {
                    if (!joint.enabled) continue;
                    joint.enabled = false;
                    joint.enabled = true;
                }
            }
        }

        /// <summary>Carry the creature's momentum into the corpse.</summary>
        public void SetVelocity(Vector2 velocity)
        {
            if (bodies == null) return;
            foreach (var rb in bodies)
                if (rb) rb.linearVelocity = velocity;
        }

        /// <summary>
        /// Kick the corpse. The impulse is spread over the pieces so a light limb does not
        /// fly off on its own, and the piece nearest the hit takes an extra share.
        /// </summary>
        public void AddImpulse(Vector2 impulse, Vector2 worldPoint, float spin = 0f)
        {
            if (bodies == null || bodies.Length == 0) return;
            if (impulse == Vector2.zero && spin == 0f) return;

            Rigidbody2D closest = null;
            float bestSqr = float.MaxValue;
            foreach (var rb in bodies)
            {
                if (!rb) continue;
                float d = ((Vector2)rb.worldCenterOfMass - worldPoint).sqrMagnitude;
                if (d >= bestSqr) continue;
                bestSqr = d;
                closest = rb;
            }

            Vector2 share = impulse / bodies.Length;
            foreach (var rb in bodies)
            {
                if (!rb) continue;
                rb.AddForce(share, ForceMode2D.Impulse);
                if (spin != 0f) rb.AddTorque(Random.Range(-spin, spin), ForceMode2D.Impulse);
            }

            if (closest) closest.AddForceAtPosition(impulse * 0.5f, worldPoint, ForceMode2D.Impulse);

            // A blow past the gib threshold does not get to be a physics question. The corpse
            // came off a blast or a shell; it arrives in pieces, around the point it was hit.
            var cfg = GoreConfig.Shared;
            if (tearable && cfg.gibImpulse > 0f && cfg.gibTears > 0 &&
                impulse.magnitude >= cfg.gibImpulse)
            {
                Vector2 away = impulse.sqrMagnitude > 1e-6f ? impulse.normalized : Vector2.up;
                TearNear(worldPoint, cfg.gibTears);
                BloodSystem.Spray(worldPoint, away, cfg.deathBurst, cone: 120f, color: Blood);
            }
        }

        // ------------------------------------------------------------------ tearing

        /// <summary>
        /// Watch what the joints are carrying and let go of the ones that are being pulled
        /// apart.
        ///
        /// The measurement is the solver's own: <see cref="Joint2D.reactionForce"/> is the force
        /// the hinge had to apply this step to keep the two pieces together, so it already
        /// accounts for mass, gravity, the impulse that arrived and whatever else is hanging off
        /// the limb. Nothing here has to know what pulled — a blast, a grinder, a rope, a leg
        /// caught under a falling slab all show up as the same number, and a corpse simply comes
        /// apart when the world pulls harder than it can hold.
        /// </summary>
        private void FixedUpdate()
        {
            TickPending();

            if (!tearable || _joints.Count == 0 || Time.time < _tearArmedAt) return;

            var cfg = GoreConfig.Shared;
            int limit = maxTears >= 0 ? maxTears : cfg.maxTears;
            if (_tears >= limit) return;

            float force = tearForce > 0f ? tearForce : cfg.tearForce;
            float torque = tearTorque > 0f ? tearTorque : cfg.tearTorque;
            float forceSqr = force * force;

            for (int i = _joints.Count - 1; i >= 0; i--)
            {
                var joint = _joints[i];
                if (!joint)
                {
                    _joints.RemoveAt(i);
                    _strain.RemoveAt(i);
                    continue;
                }

                if (!joint.enabled || !joint.connectedBody) continue;

                float load = joint.reactionForce.sqrMagnitude;
                if (load < forceSqr && Mathf.Abs(joint.reactionTorque) < torque)
                {
                    _strain[i] = 0;
                    continue;
                }

                // One step over the line is a solver spike — a piece clipping into terrain, a
                // pose being rebased. Sustained load is something actually pulling.
                if (++_strain[i] < cfg.tearSteps) continue;

                if (cfg.logTears)
                    Debug.Log($"[Tear] {joint.name}: {Mathf.Sqrt(load):F0} N / " +
                              $"{Mathf.Abs(joint.reactionTorque):F0} Nm over {force:F0} / {torque:F0}", this);

                Sever(i);
                if (++_tears >= limit) return;
            }
        }

        /// <summary>
        /// Cut one joint and make a mess of it: blood out of the cut, a stain on both faces and
        /// a stump that keeps dripping on whichever piece is still moving.
        /// </summary>
        private void Sever(int index)
        {
            var joint = _joints[index];
            _joints.RemoveAt(index);
            _strain.RemoveAt(index);
            if (!joint) return;

            var own = joint.GetComponent<Rigidbody2D>();
            var other = joint.connectedBody;

            // The anchor is where the two pieces were held together, which is exactly where a
            // limb separates — so it is the wound, in both pieces' spaces at once.
            Vector2 wound = joint.transform.TransformPoint(joint.anchor);

            // Out along the way the pieces are parting, so blood follows the limb rather than
            // spraying back into the body it just left.
            Vector2 dir = Vector2.up;
            if (own && other)
            {
                Vector2 apart = own.linearVelocity - other.linearVelocity;
                if (apart.sqrMagnitude > 0.01f) dir = apart.normalized;
                else dir = ((Vector2)own.worldCenterOfMass - (Vector2)other.worldCenterOfMass).normalized;
            }

            Destroy(joint);
            Wound(own ? own.gameObject : null, wound, dir);
            Wound(other ? other.gameObject : null, wound, -dir);

            var cfg = GoreConfig.Shared;
            BloodSystem.Spray(wound, dir, cfg.tearBurst, cone: 110f, color: Blood);

            ReleaseDetached();
        }

        // ------------------------------------------------------------------ loose pieces

        /// <summary>
        /// Give back the collisions that <see cref="IgnoreSelfCollisions"/> took away, for every
        /// pair of pieces the corpse no longer holds together.
        ///
        /// Ignoring self collision is about the corpse's own joints: two pieces pinned into each
        /// other by a hinge jitter forever if they also push each other apart. A piece that has
        /// been torn off has no hinge left to argue with, so that reason is gone and it should
        /// behave like any other loose object — land on the torso, get in the way, be swept up
        /// by the same blast.
        ///
        /// Which pairs those are is a connectivity question, not a "was this the joint I just
        /// cut" one: cutting a shoulder frees the hand hanging off that arm too, and the arm has
        /// to start colliding with the legs as much as with the chest. So the remaining joints
        /// are walked into groups and every pair that ended up in two different groups is
        /// released.
        /// </summary>
        private void ReleaseDetached()
        {
            if (selfCollision || _pieceColliders == null) return;

            var group = ConnectedGroups();
            int n = _pieceColliders.Length;

            for (int a = 0; a < n; a++)
            for (int b = a + 1; b < n; b++)
            {
                if (_released[a, b]) continue;
                if (Find(group, a) == Find(group, b)) continue;

                _released[a, b] = true;
                QueuePair(a, b);
            }
        }

        /// <summary>Union-find over the surviving joints: which pieces are still one body.</summary>
        private int[] ConnectedGroups()
        {
            int n = _pieceColliders.Length;
            var parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;

            foreach (var joint in _joints)
            {
                if (!joint || !joint.connectedBody) continue;

                var own = joint.GetComponent<Rigidbody2D>();
                if (!own) continue;
                if (!_bodyIndex.TryGetValue(own, out int a)) continue;
                if (!_bodyIndex.TryGetValue(joint.connectedBody, out int b)) continue;

                a = Find(parent, a);
                b = Find(parent, b);
                if (a != b) parent[a] = b;
            }

            return parent;
        }

        private static int Find(int[] parent, int i)
        {
            while (parent[i] != i) i = parent[i] = parent[parent[i]];
            return i;
        }

        /// <summary>
        /// Queue a pair rather than switching it on here. At the moment of the cut the two
        /// pieces are still inside each other — sprites overlap at every joint — and a collision
        /// that starts fully overlapped is resolved by throwing the pieces apart. Waiting until
        /// they have drifted clear costs a cheap distance query a few times a second and is the
        /// difference between a limb coming off and a limb being fired off.
        /// </summary>
        private void QueuePair(int a, int b)
        {
            var ca = _pieceColliders[a];
            var cb = _pieceColliders[b];
            if (ca == null || cb == null) return;

            float giveUp = Time.time + PendingGiveUp;

            foreach (var x in ca)
            {
                if (!x) continue;
                foreach (var y in cb)
                {
                    if (!y) continue;
                    _pending.Add(new PendingPair { A = x, B = y, GiveUpAt = giveUp });
                }
            }
        }

        private void TickPending()
        {
            if (_pending.Count == 0 || Time.unscaledTime < _nextPendingCheck) return;
            _nextPendingCheck = Time.unscaledTime + PendingInterval;

            for (int i = _pending.Count - 1; i >= 0; i--)
            {
                var pair = _pending[i];
                if (!pair.A || !pair.B)
                {
                    _pending.RemoveAt(i);
                    continue;
                }

                // An invalid distance means a collider is disabled or has no shape yet; treat
                // it the same as still overlapping and look again next time.
                bool late = Time.time >= pair.GiveUpAt;
                var gap = Physics2D.Distance(pair.A, pair.B);
                if (!late && (!gap.isValid || gap.isOverlapped)) continue;

                Physics2D.IgnoreCollision(pair.A, pair.B, false);
                _pending.RemoveAt(i);
            }
        }

        /// <summary>Mark one face of a cut: paint it red and leave it bleeding.</summary>
        private void Wound(GameObject piece, Vector2 at, Vector2 dir)
        {
            if (!piece) return;

            var cfg = GoreConfig.Shared;
            // Pulled back into the piece, so the mark sits on the meat rather than half of it
            // hanging in the gap between the two halves.
            Vector3 inside = (Vector3)at - (Vector3)(dir * 0.04f);
            SpritePaintService.PaintCircle(piece, inside, cfg.stainRadius * 1.6f,
                                           cfg.stainColor, cfg.stainStrength, cfg.stainNoise,
                                           piece.GetInstanceID());

            Bleeder.Open(piece, at, Blood);
        }

        /// <summary>
        /// Cut every hinge, so the corpse comes apart into loose pieces. Ignores the tear limit —
        /// this is the "take it all off" entry point, for a grinder or a debug key.
        /// </summary>
        public void Dismember()
        {
            for (int i = _joints.Count - 1; i >= 0; i--)
            {
                Sever(i);
                _tears++;
            }

            // Joints the cache never saw — a corpse that was welded to something after it spawned.
            if (bodies == null) return;
            foreach (var rb in bodies)
            {
                if (!rb) continue;
                foreach (var joint in rb.GetComponents<AnchoredJoint2D>())
                    Destroy(joint);
            }
        }

        /// <summary>
        /// Take the <paramref name="count"/> joints nearest <paramref name="worldPoint"/> off.
        /// Used for a blow that is simply too big to be survived in one piece, where waiting for
        /// the joints to feel the impulse would land a frame late and look like nothing.
        /// </summary>
        public void TearNear(Vector2 worldPoint, int count)
        {
            for (int n = 0; n < count && _joints.Count > 0; n++)
            {
                int best = -1;
                float bestSqr = float.MaxValue;
                for (int i = 0; i < _joints.Count; i++)
                {
                    var joint = _joints[i];
                    if (!joint) continue;
                    float d = ((Vector2)joint.transform.TransformPoint(joint.anchor) - worldPoint).sqrMagnitude;
                    if (d >= bestSqr) continue;
                    bestSqr = d;
                    best = i;
                }

                if (best < 0) return;
                Sever(best);
                _tears++;
            }
        }

        /// <summary>
        /// Mirroring a jointed hierarchy with a negative scale confuses 2D physics, so the
        /// flip is baked into the pieces instead: sprite, collider outline and hinge anchors.
        /// </summary>
        private void SetFlipped(bool flip)
        {
            if (flip == _flipped || bodies == null) return;
            _flipped = flip;

            foreach (var rb in bodies)
            {
                if (!rb) continue;

                var sr = rb.GetComponent<SpriteRenderer>();
                if (sr) sr.flipX = flip;

                foreach (var poly in rb.GetComponents<PolygonCollider2D>())
                    MirrorPaths(poly);

                foreach (var hinge in rb.GetComponents<HingeJoint2D>())
                {
                    var a = hinge.anchor;
                    hinge.anchor = new Vector2(-a.x, a.y);
                    var c = hinge.connectedAnchor;
                    hinge.connectedAnchor = new Vector2(-c.x, c.y);

                    var limits = hinge.limits;
                    hinge.limits = new JointAngleLimits2D { min = -limits.max, max = -limits.min };
                }
            }
        }

        private static readonly List<Vector2> PathBuf = new();

        private static void MirrorPaths(PolygonCollider2D poly)
        {
            for (int p = 0; p < poly.pathCount; p++)
            {
                poly.GetPath(p, PathBuf);
                for (int i = 0; i < PathBuf.Count; i++)
                {
                    var v = PathBuf[i];
                    PathBuf[i] = new Vector2(-v.x, v.y);
                }
                PathBuf.Reverse(); // keep the winding order after the mirror
                poly.SetPath(p, PathBuf);
            }
        }

        private void CachePieces()
        {
            if (bodies == null) return;

            _pieceColliders = new Collider2D[bodies.Length][];
            _released = new bool[bodies.Length, bodies.Length];

            for (int i = 0; i < bodies.Length; i++)
            {
                var rb = bodies[i];
                if (!rb) continue;
                _pieceColliders[i] = rb.GetComponents<Collider2D>();
                _bodyIndex[rb] = i;
            }
        }

        private void IgnoreSelfCollisions()
        {
            if (_pieceColliders == null) return;

            for (int i = 0; i < _pieceColliders.Length; i++)
            for (int j = i + 1; j < _pieceColliders.Length; j++)
                SetPairIgnored(i, j, true);
        }

        /// <summary>Turn collision between two whole pieces on or off.</summary>
        private void SetPairIgnored(int a, int b, bool ignored)
        {
            var ca = _pieceColliders[a];
            var cb = _pieceColliders[b];
            if (ca == null || cb == null) return;

            foreach (var x in ca)
            {
                if (!x) continue;
                foreach (var y in cb)
                {
                    if (!y) continue;
                    Physics2D.IgnoreCollision(x, y, ignored);
                }
            }
        }

#if UNITY_EDITOR
        /// <summary>Used by the importer to wire the freshly built prefab.</summary>
        public void EditorBind(RagdollDefinition def, Rigidbody2D[] parts)
        {
            definition = def;
            bodies = parts;
        }
#endif
    }
}
