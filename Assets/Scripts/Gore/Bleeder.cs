using System.Collections.Generic;
using UnityEngine;

namespace Gore
{
    /// <summary>
    /// An open wound that keeps producing blood after the thing that made it is over.
    ///
    /// Added to a piece at the moment it is torn off (see <see cref="Ragdolls.Ragdoll"/>), one
    /// component per piece however many wounds it ends up with. The wounds are kept in the
    /// piece's own local space, so a severed arm spinning through the air trails blood from the
    /// shoulder end rather than from a fixed point in the room.
    ///
    /// The rate tails off over <see cref="GoreConfig.bleedSeconds"/>: a fresh stump pumps, an
    /// old one seeps, and it eventually stops on its own instead of painting the level red
    /// forever. When the last wound has run dry the component removes itself.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class Bleeder : MonoBehaviour
    {
        private struct Wound
        {
            public Vector2 Local;    // where it is, in the piece's own space
            public float Age;
            public float Life;
            public float Debt;       // fractional drips carried between frames
        }

        private readonly List<Wound> _wounds = new();
        private Rigidbody2D _body;
        private Color32 _color;

        /// <summary>
        /// Open a wound at <paramref name="worldPoint"/> on <paramref name="go"/>, adding the
        /// component if this is the first one.
        /// </summary>
        public static void Open(GameObject go, Vector2 worldPoint, Color32 color = default, float seconds = -1f)
        {
            if (!go) return;

            var cfg = GoreConfig.Shared;
            if (seconds < 0f) seconds = cfg.bleedSeconds;
            if (seconds <= 0f) return;
            if (color.a == 0) color = cfg.dropColor;

            var bleeder = go.GetComponent<Bleeder>();
            if (!bleeder) bleeder = go.AddComponent<Bleeder>();

            bleeder._color = color;
            bleeder._wounds.Add(new Wound
            {
                Local = go.transform.InverseTransformPoint(worldPoint),
                Life = seconds * Random.Range(0.75f, 1.25f),
            });
        }

        private void Awake() => _body = GetComponentInParent<Rigidbody2D>();

        private void Update()
        {
            var cfg = GoreConfig.Shared;
            float dt = Time.deltaTime;
            Vector2 carried = _body ? _body.linearVelocity : Vector2.zero;

            for (int i = _wounds.Count - 1; i >= 0; i--)
            {
                var w = _wounds[i];
                w.Age += dt;
                if (w.Age >= w.Life)
                {
                    _wounds.RemoveAt(i);
                    continue;
                }

                // Squared falloff: the first second of a stump is worth the next five.
                float left = 1f - w.Age / w.Life;
                w.Debt += cfg.bleedRate * left * left * dt;

                int n = Mathf.FloorToInt(w.Debt);
                if (n > 0)
                {
                    w.Debt -= n;
                    Vector2 at = transform.TransformPoint(w.Local);
                    for (int d = 0; d < n; d++)
                    {
                        // Mostly falling, with some of the piece's own motion in it — blood
                        // leaving a limb that is still flying has to keep up with the limb.
                        Vector2 v = carried * 0.5f
                                    + Vector2.down * (cfg.bleedSpeed * Random.Range(0.4f, 1f))
                                    + Random.insideUnitCircle * (cfg.bleedSpeed * 0.5f);
                        BloodSystem.Drip(at, v, _color, Random.Range(0.6f, 1.3f));
                    }
                }

                _wounds[i] = w;
            }

            if (_wounds.Count == 0) Destroy(this);
        }
    }
}
