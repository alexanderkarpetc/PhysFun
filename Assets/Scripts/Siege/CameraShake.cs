using UnityEngine;

namespace Siege
{
    /// <summary>
    /// Positional kick on the camera, decaying to nothing. Kept separate from the
    /// camera's resting position so the scene can still reframe the view underneath it.
    /// </summary>
    public sealed class CameraShake : MonoBehaviour
    {
        public static CameraShake Instance { get; private set; }

        private Vector3 _rest;
        private float _trauma;
        private float _seed;

        private void Awake()
        {
            Instance = this;
            _rest = transform.position;
            _seed = Random.value * 100f;
        }

        /// <summary>Anchor the shake to wherever the camera is meant to sit.</summary>
        public void SetRest(Vector3 rest) => _rest = rest;

        public static void Kick(float amount)
        {
            if (Instance) Instance._trauma = Mathf.Min(1f, Instance._trauma + amount);
        }

        private void LateUpdate()
        {
            if (_trauma <= 0f)
            {
                transform.position = _rest;
                return;
            }

            _trauma = Mathf.Max(0f, _trauma - Time.deltaTime * 1.8f);

            // Squared so the tail is short and the hit is punchy.
            float m = _trauma * _trauma * 0.45f;
            float t = Time.time * 26f;
            transform.position = _rest + new Vector3(
                (Mathf.PerlinNoise(_seed, t) - 0.5f) * 2f * m,
                (Mathf.PerlinNoise(_seed + 13f, t) - 0.5f) * 2f * m,
                0f);
        }
    }
}
