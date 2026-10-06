using UnityEngine;

namespace Player
{
    /// <summary>
    /// Points the pilgrim's staff at the cursor. The staff is its own sprite under View, pivoted
    /// at the grip: the animation clips move it with the hand frame by frame and this turns it,
    /// so it sweeps the same way over idle, walk and flight. Runs after the Animator (LateUpdate)
    /// and works in View's space, so the facing flip (View.localScale.x = -1) mirrors the swing.
    /// </summary>
    public class StaffAim : MonoBehaviour
    {
        [Tooltip("How fast the staff catches up with the cursor; higher is snappier.")]
        [SerializeField] private float follow = 20f;

        private Camera _cam;
        private float _angle = float.NaN;

        private void LateUpdate()
        {
            if (!_cam) _cam = Camera.main;
            if (!_cam) return;

            Vector2 world = (Vector2)_cam.ScreenToWorldPoint(Input.mousePosition) - (Vector2)transform.position;
            if (world.sqrMagnitude < 1e-6f) return;

            // InverseTransformVector carries the parent's mirror; InverseTransformDirection ignores scale.
            Vector2 local = transform.parent ? (Vector2)transform.parent.InverseTransformVector(world) : world;
            // The sprite is drawn ring-up, so zero rotation already points along +y.
            float target = Mathf.Atan2(local.y, local.x) * Mathf.Rad2Deg - 90f;
            _angle = float.IsNaN(_angle)
                ? target
                : Mathf.LerpAngle(_angle, target, 1f - Mathf.Exp(-follow * Time.deltaTime));
            transform.localRotation = Quaternion.Euler(0f, 0f, _angle);
        }
    }
}
