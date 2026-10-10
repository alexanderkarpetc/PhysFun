using UnityEngine;

namespace Phys.Fire
{
    /// <summary>
    /// A fire that does not go out: the bed of a furnace, a brazier, a gas jet. It puts flames
    /// into the <see cref="FlameField"/> at a steady rate inside its box, and from there they are
    /// ordinary flames - they rise, they light what they touch, they die - so what the source
    /// sets alight is decided by what is near it, not by anything here. Put it somewhere walled
    /// in and it only reaches out through the openings, which is what makes a furnace a furnace.
    /// </summary>
    public sealed class FireSource : MonoBehaviour
    {
        [Tooltip("Where flames are born, local to this object (centre and size, world units).")]
        [SerializeField] private Vector2 _size = new(1f, 0.3f);
        [Tooltip("Flames per second.")]
        [SerializeField] private float _rate = 60f;
        [SerializeField, Range(1, 255)] private int _heat = 70;
        [Tooltip("Smoke puffs per second, out of the same box.")]
        [SerializeField] private float _smokeRate = 4f;

        private float _flameDebt, _smokeDebt;

        private void Update()
        {
            float dt = Time.deltaTime;
            _flameDebt += _rate * dt;
            _smokeDebt += _smokeRate * dt;
            var field = FlameField.Instance;
            while (_flameDebt >= 1f)
            {
                _flameDebt -= 1f;
                field.Emit(Point(), _heat);
            }
            while (_smokeDebt >= 1f)
            {
                _smokeDebt -= 1f;
                field.EmitSmoke(Point());
            }
        }

        private Vector2 Point() => transform.TransformPoint(new Vector2(
            (Random.value - 0.5f) * _size.x, (Random.value - 0.5f) * _size.y));

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            Gizmos.color = new Color(1f, 0.55f, 0.2f);
            Gizmos.matrix = transform.localToWorldMatrix;
            Gizmos.DrawWireCube(Vector3.zero, _size);
        }
#endif
    }
}
