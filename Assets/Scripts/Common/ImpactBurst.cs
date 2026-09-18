using UnityEngine;

namespace Common
{
    /// <summary>
    /// A handful of pixels thrown out of a hit — blood off a body, chips off a wall.
    ///
    /// Built in code from one white pixel sprite rather than from a prefab: there is nothing to
    /// wire, and tinting the same sprite is what lets a round decide at the moment of impact
    /// whether it went into flesh or into ground.
    ///
    /// The drops are not physics bodies. A dozen rigidbodies per hit would cost more than the
    /// hit is worth and they have nothing to collide with that matters, so they are integrated
    /// here and snapped to the pixel grid on the way, which keeps the spray reading as pixels
    /// instead of smearing between them.
    /// </summary>
    public sealed class ImpactBurst : MonoBehaviour
    {
        private const float Snap = 1f / 20f;   // the world's pixel, same as every sprite's PPU

        private struct Drop
        {
            public Transform T;
            public SpriteRenderer R;
            public Vector2 Pos;
            public Vector2 Vel;
        }

        private Drop[] _drops;
        private Color _color;
        private float _age;
        private float _life = 0.5f;
        private float _gravity = 1f;

        /// <summary>Throw a burst at <paramref name="point"/>, away from where the hit came from.</summary>
        public static void Spawn(Sprite pixel, Vector2 point, Vector2 travel, Color color,
                                 int count = 8, float speed = 3.5f, float life = 0.55f,
                                 int sortingOrder = 3)
        {
            if (!pixel || count <= 0) return;

            var go = new GameObject("ImpactBurst") { layer = 8 };
            go.transform.position = point;
            go.AddComponent<ImpactBurst>()
              .Build(pixel, travel, color, count, speed, life, sortingOrder);
        }

        private void Build(Sprite pixel, Vector2 travel, Color color, int count, float speed,
                           float life, int sortingOrder)
        {
            _color = color;
            _life = life;
            _drops = new Drop[count];

            Vector2 back = travel.sqrMagnitude > 0.0001f ? -travel.normalized : Vector2.up;

            for (int i = 0; i < count; i++)
            {
                var child = new GameObject("d") { layer = gameObject.layer };
                child.transform.SetParent(transform, false);

                var sr = child.AddComponent<SpriteRenderer>();
                sr.sprite = pixel;
                sr.color = color;
                sr.sortingOrder = sortingOrder;

                // Most of it sprays back out of the wound; a quarter carries on through, which
                // is what stops the burst looking like a symmetrical firework.
                bool through = Random.value < 0.25f;
                Vector2 axis = through ? -back : back;
                float cone = through ? 25f : 70f;
                Vector2 dir = Quaternion.Euler(0f, 0f, Random.Range(-cone, cone)) * axis;

                float scale = Random.Range(1f, 2.4f);
                child.transform.localScale = new Vector3(scale, scale, 1f);

                _drops[i] = new Drop
                {
                    T = child.transform,
                    R = sr,
                    Pos = Vector2.zero,
                    Vel = dir * (speed * Random.Range(0.35f, 1f)),
                };
            }
        }

        private void Update()
        {
            float dt = Time.deltaTime;
            _age += dt;

            if (_age >= _life)
            {
                Destroy(gameObject);
                return;
            }

            float fade = 1f - _age / _life;
            Vector2 pull = Physics2D.gravity * _gravity;

            for (int i = 0; i < _drops.Length; i++)
            {
                ref Drop d = ref _drops[i];
                if (!d.T) continue;

                d.Vel += pull * dt;
                d.Vel *= 1f - Mathf.Min(0.9f, 1.5f * dt);   // air, so the spray slows and hangs
                d.Pos += d.Vel * dt;

                d.T.localPosition = new Vector3(
                    Mathf.Round(d.Pos.x / Snap) * Snap,
                    Mathf.Round(d.Pos.y / Snap) * Snap, 0f);

                Color c = _color;
                c.a *= fade * fade;
                d.R.color = c;
            }
        }
    }
}
