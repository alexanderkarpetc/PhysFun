using UnityEngine;

namespace Spawners.Ragdoll
{
    public class SimpleRagdollBinder2D : MonoBehaviour
    {
        [Header("Refs")]
        public BodyUVAsset uv;                  // from earlier step
        public SpriteRenderer animRenderer;     // current sprite of the dying unit

        public Rigidbody2D Torso, Head, Hand_L, Hand_R, Foot_L, Foot_R;
        public HingeJoint2D HeadJoint;
        public DistanceJoint2D HandL_J, HandR_J, FootL_J, FootR_J;

        void Awake()
        {
            // keep stable while posing
            // foreach (var rb in GetComponentsInChildren<Rigidbody2D>(true))
                // rb.bodyType = RigidbodyType2D.Kinematic;
        }

        public void PoseAndEnable(string anim, int frame, bool faceRight)
        {
            // 1) Get world points from UV (falls back to sprite pivot if missing)
            Vector3 wTorso = ToWorld(GetOrPivot(uv, anim, frame, UVPart.Torso));
            Vector3 wHead  = ToWorld(GetOrPivot(uv, anim, frame, UVPart.Head));
            Vector3 wHL    = ToWorld(GetOrPivot(uv, anim, frame, UVPart.LArm)); // using arms as "hands"
            Vector3 wHR    = ToWorld(GetOrPivot(uv, anim, frame, UVPart.RArm));
            Vector3 wFL    = ToWorld(GetOrPivot(uv, anim, frame, UVPart.LLeg)); // using legs as "feet"
            Vector3 wFR    = ToWorld(GetOrPivot(uv, anim, frame, UVPart.RLeg));

            // 2) Place bodies
            Torso.position = wTorso;
            Head.position  = wHead;
            Hand_L.position = wHL; Hand_R.position = wHR;
            Foot_L.position = wFL; Foot_R.position = wFR;

            // 3) Configure joints (anchors in Torso local space)
            var torsoT = Torso.transform;
            Vector2 neckOnTorso   = torsoT.InverseTransformPoint(wHead);
            Vector2 handLAnchor   = torsoT.InverseTransformPoint(wHL);
            Vector2 handRAnchor   = torsoT.InverseTransformPoint(wHR);
            Vector2 footLAnchor   = torsoT.InverseTransformPoint(wFL);
            Vector2 footRAnchor   = torsoT.InverseTransformPoint(wFR);

            // Head hinge
            HeadJoint.connectedBody = Torso;
            HeadJoint.autoConfigureConnectedAnchor = false;
            HeadJoint.connectedAnchor = neckOnTorso;   // where head meets torso
            HeadJoint.anchor = Vector2.zero;           // center of head (adjust if needed)
            HeadJoint.useLimits = true;
            HeadJoint.limits = new JointAngleLimits2D { min = -30f, max = +30f };

            // Distance joints: keep endpoint near its UV anchor on torso
            SetupDist(HandL_J, Torso, handLAnchor, Hand_L.position);
            SetupDist(HandR_J, Torso, handRAnchor, Hand_R.position);
            SetupDist(FootL_J, Torso, footLAnchor, Foot_L.position);
            SetupDist(FootR_J, Torso, footRAnchor, Foot_R.position);

            // 4) Flip if needed (optional visual)
            float sx = faceRight ? 1f : -1f;
            foreach (var sr in GetComponentsInChildren<SpriteRenderer>())
            {
                var ls = sr.transform.localScale; ls.x = Mathf.Abs(ls.x) * sx; sr.transform.localScale = ls;
            }

            // 5) Enable physics
            foreach (var rb in GetComponentsInChildren<Rigidbody2D>(true))
                rb.bodyType = RigidbodyType2D.Dynamic;
        }

        void SetupDist(DistanceJoint2D j, Rigidbody2D connected, Vector2 connectedAnchorLocal, Vector3 targetWorld)
        {
            j.connectedBody = connected;
            j.autoConfigureConnectedAnchor = false;
            j.connectedAnchor = connectedAnchorLocal;

            j.autoConfigureDistance = false;
            float dist = Vector2.Distance(connected.transform.TransformPoint(connectedAnchorLocal), targetWorld);
            j.distance = Mathf.Max(0.02f, dist); // small minimum to avoid instability
            j.maxDistanceOnly = false;           // keep within +/- distance (rope + springless)
            j.enableCollision = false;
        }

        // --- UV helpers ---
        Vector2 GetOrPivot(BodyUVAsset asset, string anim, int frame, UVPart part)
        {
            var f = asset.frames.Find(x => x.anim == anim && x.frame == frame);
            if (f.points != null)
                foreach (var e in f.points) if (e.part == part) return e.uv;

            // fallback: sprite pivot normalized
            var s = animRenderer.sprite; var r = s.rect;
            return new Vector2(s.pivot.x / r.width, s.pivot.y / r.height);
        }

        Vector3 ToWorld(Vector2 uv01)
        {
            var s = animRenderer.sprite; var r = s.rect;
            Vector2 local = new(
                (uv01.x - s.pivot.x / r.width) * (r.width / s.pixelsPerUnit),
                (uv01.y - s.pivot.y / r.height) * (r.height / s.pixelsPerUnit)
            );
            return animRenderer.transform.TransformPoint(local);
        }
    }
}
