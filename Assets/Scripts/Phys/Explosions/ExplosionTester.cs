using UnityEngine;

namespace Phys.Explosions
{
    /// <summary>
    /// Blow a hole wherever the mouse is. Drop it on any object in the scene, press the key and
    /// the profile below goes off under the cursor; the bracket keys grow and shrink it through
    /// <see cref="ExplosionProfile.Scaled"/>, which is the quickest way to find out what radius
    /// a given bomb actually wants to be.
    ///
    /// A test rig, not a game object: it only exists to save building a barrel every time the
    /// blast needs a look.
    /// </summary>
    [AddComponentMenu("PhysFun/Explosion Tester")]
    public sealed class ExplosionTester : MonoBehaviour
    {
        [SerializeField] private ExplosionProfile profile = ExplosionProfile.Barrel();

        [SerializeField] private KeyCode key = KeyCode.B;
        [SerializeField] private KeyCode grow = KeyCode.RightBracket;
        [SerializeField] private KeyCode shrink = KeyCode.LeftBracket;

        [Tooltip("Multiplier on the whole profile, stepped by the bracket keys.")]
        [SerializeField] private float size = 1f;

        [SerializeField] private float step = 0.25f;

        private Camera _cam;

        private void Awake() => _cam = Camera.main;

        private void Update()
        {
            if (Input.GetKeyDown(grow)) size += step;
            if (Input.GetKeyDown(shrink)) size = Mathf.Max(step, size - step);

            if (!Input.GetKeyDown(key)) return;

            if (!_cam) _cam = Camera.main;
            if (!_cam) return;

            Vector3 at = _cam.ScreenToWorldPoint(Input.mousePosition);
            at.z = 0f;

            var blast = Mathf.Approximately(size, 1f) ? profile : profile.Scaled(size);
            Debug.Log($"[Explosion] {blast.radius:F2}u, {blast.damage:F0} dmg ({size:F2}x)");
            Explosion.Detonate(at, blast);
        }
    }
}
