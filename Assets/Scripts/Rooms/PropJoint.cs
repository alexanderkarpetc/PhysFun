using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// A joint a room sets up between one of its props and the world, or two of its props,
    /// at this object's position: the turntable's kingpin, the trebuchet's axle, the scales'
    /// fulcrum, the guides a stamp rides in.
    ///
    /// It exists because a room prefab is written from code by <c>export_rooms.py</c>, and the
    /// props in it are nested prefab instances: adding a HingeJoint2D to one of those from a
    /// generator means hand-writing Unity's added-component bookkeeping. This is a plain child
    /// of the room that points at the props instead, and makes the real joint when the room
    /// wakes - which FloorBuilder only lets happen once the room is in place, so the anchor is
    /// read in world space where it belongs.
    /// </summary>
    public sealed class PropJoint : MonoBehaviour
    {
        public enum JointKind { Hinge, Slider, Fixed }

        [Tooltip("The prop the joint goes on (any transform inside it: its Rigidbody2D is looked up from there).")]
        [SerializeField] private Transform _body;
        [Tooltip("What it is jointed to. Empty = pinned to the world at this point.")]
        [SerializeField] private Transform _connectedTo;
        [SerializeField] private JointKind _kind = JointKind.Hinge;

        [Header("Hinge")]
        [SerializeField] private bool _useLimits;
        [SerializeField] private float _lowerAngle;
        [SerializeField] private float _upperAngle;
        [SerializeField] private bool _useMotor;
        [Tooltip("Degrees per second.")]
        [SerializeField] private float _motorSpeed;
        [SerializeField] private float _maxMotorTorque = 1000f;

        [Header("Slider")]
        [Tooltip("Direction the body slides along, in degrees (90 = straight up and down).")]
        [SerializeField] private float _slideAngle = 90f;
        [SerializeField] private bool _useTranslationLimits;
        [SerializeField] private float _lowerTranslation;
        [SerializeField] private float _upperTranslation;

        [Header("Breaking")]
        [Tooltip("Force it parts at. 0 = never.")]
        [SerializeField] private float _breakForce;

        public Joint2D Joint { get; private set; }

        private void Start()
        {
            var rb = _body ? _body.GetComponentInParent<Rigidbody2D>() : null;
            if (!rb)
            {
                Debug.LogWarning($"PropJoint '{name}': nothing to joint.", this);
                return;
            }
            var other = _connectedTo ? _connectedTo.GetComponentInParent<Rigidbody2D>() : null;
            Vector2 at = transform.position;

            switch (_kind)
            {
                case JointKind.Hinge:
                    var hinge = rb.gameObject.AddComponent<HingeJoint2D>();
                    hinge.useLimits = _useLimits;
                    if (_useLimits) hinge.limits = new JointAngleLimits2D { min = _lowerAngle, max = _upperAngle };
                    hinge.useMotor = _useMotor;
                    if (_useMotor)
                        hinge.motor = new JointMotor2D { motorSpeed = _motorSpeed, maxMotorTorque = _maxMotorTorque };
                    Joint = hinge;
                    break;
                case JointKind.Slider:
                    var slider = rb.gameObject.AddComponent<SliderJoint2D>();
                    slider.autoConfigureAngle = false;
                    slider.angle = _slideAngle;
                    slider.useLimits = _useTranslationLimits;
                    if (_useTranslationLimits)
                        slider.limits = new JointTranslationLimits2D { min = _lowerTranslation, max = _upperTranslation };
                    Joint = slider;
                    break;
                default:
                    Joint = rb.gameObject.AddComponent<FixedJoint2D>();
                    break;
            }

            var anchored = (AnchoredJoint2D)Joint;
            anchored.autoConfigureConnectedAnchor = false;
            anchored.anchor = rb.transform.InverseTransformPoint(at);
            anchored.connectedBody = other;
            anchored.connectedAnchor = other ? (Vector2)other.transform.InverseTransformPoint(at) : at;
            Joint.enableCollision = false;
            if (_breakForce > 0f) Joint.breakForce = _breakForce;
        }

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            Gizmos.color = _kind == JointKind.Hinge ? new Color(0.95f, 0.75f, 0.3f)
                         : _kind == JointKind.Slider ? new Color(0.4f, 0.85f, 0.6f) : Color.gray;
            var p = transform.position;
            Gizmos.DrawWireSphere(p, 0.12f);
            if (_kind == JointKind.Slider)
            {
                var d = Quaternion.Euler(0f, 0f, _slideAngle) * Vector3.right * 0.6f;
                Gizmos.DrawLine(p - d, p + d);
            }
            if (_body) Gizmos.DrawLine(p, _body.position);
        }
#endif
    }
}
