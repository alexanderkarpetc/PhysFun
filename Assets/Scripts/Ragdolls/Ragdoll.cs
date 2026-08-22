using System.Collections.Generic;
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

        private bool _flipped;

        public RagdollDefinition Definition => definition;
        public IReadOnlyList<Rigidbody2D> Bodies => bodies;

        private void Awake()
        {
            if (!selfCollision) IgnoreSelfCollisions();
            if (destroyAfter > 0f) Destroy(gameObject, destroyAfter);
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
        }

        /// <summary>Cut every hinge, so the corpse comes apart into loose pieces.</summary>
        public void Dismember()
        {
            if (bodies == null) return;
            foreach (var rb in bodies)
            {
                if (!rb) continue;
                foreach (var joint in rb.GetComponents<AnchoredJoint2D>())
                    Destroy(joint);
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

        private void IgnoreSelfCollisions()
        {
            if (bodies == null) return;

            var cols = new List<Collider2D>();
            foreach (var rb in bodies)
            {
                if (!rb) continue;
                cols.AddRange(rb.GetComponents<Collider2D>());
            }

            for (int i = 0; i < cols.Count; i++)
            for (int j = i + 1; j < cols.Count; j++)
                Physics2D.IgnoreCollision(cols[i], cols[j], true);
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
