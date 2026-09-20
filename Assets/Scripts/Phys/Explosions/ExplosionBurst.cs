using UnityEngine;

namespace Phys.Explosions
{
    /// <summary>
    /// What a blast looks like in the frames right after it: a flash, a ring going out through
    /// the smoke, and debris thrown every way at once.
    ///
    /// Separate from <see cref="Common.ImpactBurst"/>, which sprays a cone back out of a wound
    /// and is the right shape for a bullet and the wrong one for a bomb. This one is radial, its
    /// pieces cool from white through the fire colours to ash as they fly, and they are snapped
    /// to the world's pixel grid on the way so the spray stays pixels instead of smearing
    /// between them. Nothing here is an asset: the pixel, the flash and the ring are generated
    /// once and shared, so a profile with no art wired to it still reads as an explosion.
    /// </summary>
    public sealed class ExplosionBurst : MonoBehaviour
    {
        private const float Snap = 1f / 20f;     // the world's pixel, same as every sprite's PPU
        private const int Layer = 8;

        private struct Piece
        {
            public Transform T;
            public SpriteRenderer R;
            public Vector2 Pos;
            public Vector2 Vel;
            public float Life;
            public float Age;
            public float Spin;
            public float Size;
            public float Drag;
            public float Gravity;
        }

        private Piece[] _pieces;
        private Color _hot, _mid, _cool;

        private Transform _flash;
        private SpriteRenderer _flashR;
        private float _flashLife, _flashAge, _flashSize;

        private Transform _ring;
        private SpriteRenderer _ringR;
        private float _ringLife, _ringAge, _ringSize;

        // ─────────────────────────────────────────────────────────────────────
        // Shared art, built the first time something explodes
        // ─────────────────────────────────────────────────────────────────────

        private static Sprite s_pixel, s_disc, s_ring;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode()
        {
            s_pixel = s_disc = s_ring = null;
        }

        private static Sprite Pixel()
        {
            if (s_pixel) return s_pixel;

            var tex = new Texture2D(1, 1, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            tex.SetPixel(0, 0, Color.white);
            tex.Apply(false, false);
            s_pixel = Sprite.Create(tex, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 20f, 0,
                                    SpriteMeshType.FullRect);
            return s_pixel;
        }

        /// <summary>
        /// A filled circle and a hollow one, drawn at 32 px across and left on point filtering.
        /// Cheap, and the low resolution is the point: scaled up, the edge stays a staircase
        /// instead of the soft round glow that would look pasted on over pixel art.
        /// </summary>
        private static Sprite Disc(bool hollow)
        {
            if (hollow && s_ring) return s_ring;
            if (!hollow && s_disc) return s_disc;

            const int d = 32;
            const float r = d * 0.5f;
            var tex = new Texture2D(d, d, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            var px = new Color32[d * d];

            for (int y = 0; y < d; y++)
            for (int x = 0; x < d; x++)
            {
                float dist = Mathf.Sqrt((x + 0.5f - r) * (x + 0.5f - r) + (y + 0.5f - r) * (y + 0.5f - r));
                bool on = hollow ? dist <= r && dist >= r - 2.2f : dist <= r;
                px[y * d + x] = on ? new Color32(255, 255, 255, 255) : default;
            }

            tex.SetPixels32(px);
            tex.Apply(false, false);

            var sprite = Sprite.Create(tex, new Rect(0, 0, d, d), new Vector2(0.5f, 0.5f), d, 0,
                                       SpriteMeshType.FullRect);
            if (hollow) s_ring = sprite; else s_disc = sprite;
            return sprite;
        }

        // ─────────────────────────────────────────────────────────────────────

        /// <summary>Throw the whole thing — flash, ring and debris — for one blast.</summary>
        public static void Spawn(Vector2 center, ExplosionProfile p)
        {
            if (p == null) return;

            var go = new GameObject("ExplosionBurst") { layer = Layer };
            go.transform.position = center;
            go.AddComponent<ExplosionBurst>().Build(p);
        }

        /// <summary>
        /// A handful of pixels and nothing else. What a burning fuse throws off its tip — the
        /// same debris, at a size where a flash and a ring would be silly.
        /// </summary>
        public static void Sparks(Vector2 at, int count, float speed, Color hot, Color cool,
                                  float life = 0.45f, float gravity = 1.4f)
        {
            if (count <= 0) return;

            var go = new GameObject("Sparks") { layer = Layer };
            go.transform.position = at;
            go.AddComponent<ExplosionBurst>()
              .BuildPieces(null, count, speed, hot, Color.Lerp(hot, cool, 0.5f), cool,
                           life, gravity, 2.2f, 1.6f);
        }

        private void Build(ExplosionProfile p)
        {
            Color hot = Color.Lerp(p.sparkColor, Color.white, 0.55f);
            Color cool = p.sparkCool;

            BuildPieces(p.sparkPixel, p.sparks, p.sparkSpeed, hot, p.sparkColor, cool,
                        0.85f, 2.2f, 1.1f, 3.4f);

            if (p.flashScale > 0f) BuildFlash(p, hot);
            if (p.ringScale > 0f) BuildRing(p);
        }

        /// <summary>
        /// The debris. Directions are spread evenly around the circle and then jittered, rather
        /// than drawn at random: pure random leaves gaps and clumps, and a blast with a bald
        /// patch in it reads as a mistake. Speeds vary a lot, which is what fills the disc in
        /// instead of leaving an expanding ring of dots.
        /// </summary>
        private void BuildPieces(Sprite art, int count, float speed, Color hot, Color mid, Color cool,
                                 float life, float gravity, float drag, float maxSize)
        {
            _hot = hot; _mid = mid; _cool = cool;
            if (count <= 0) { _pieces = new Piece[0]; return; }

            var sprite = art ? art : Pixel();
            _pieces = new Piece[count];

            for (int i = 0; i < count; i++)
            {
                var child = new GameObject("p") { layer = gameObject.layer };
                child.transform.SetParent(transform, false);

                var sr = child.AddComponent<SpriteRenderer>();
                sr.sprite = sprite;
                sr.color = hot;
                sr.sortingOrder = 6;

                float angle = (i + Random.Range(0f, 0.85f)) / count * Mathf.PI * 2f;
                Vector2 dir = new(Mathf.Cos(angle), Mathf.Sin(angle));

                // Cubed, so most pieces are slow and near the middle and a few are flung right
                // out — the spread a real burst has, and a flat range never gives.
                float t = Random.value;
                float v = speed * Mathf.Lerp(0.15f, 1.15f, t * t * t);

                float size = Mathf.Lerp(maxSize, 1f, Mathf.Sqrt(Random.value));
                child.transform.localScale = new Vector3(size, size, 1f);

                _pieces[i] = new Piece
                {
                    T = child.transform,
                    R = sr,
                    Vel = dir * v,
                    // Fast pieces live longest, so the outliers are the ones that draw the shape.
                    Life = life * Random.Range(0.45f, 1f) * Mathf.Lerp(0.7f, 1.3f, t),
                    Spin = Random.Range(-540f, 540f),
                    Size = size,
                    Drag = drag * Random.Range(0.7f, 1.4f),
                    Gravity = gravity * Random.Range(0.6f, 1.2f),
                };

            }
        }

        private void BuildFlash(ExplosionProfile p, Color hot)
        {
            var go = new GameObject("flash") { layer = gameObject.layer };
            go.transform.SetParent(transform, false);

            _flashR = go.AddComponent<SpriteRenderer>();
            _flashR.sprite = Disc(false);
            _flashR.color = hot;
            _flashR.sortingOrder = 5;

            _flash = go.transform;
            _flashSize = p.radius * p.flashScale;
            _flashLife = 0.09f;
        }

        /// <summary>
        /// The pressure front. It is not physics — nothing is pushed by it, the impulse has
        /// already been handed out — it is the one mark that says how far the blast reached,
        /// which a cloud of fire on its own never manages to say.
        /// </summary>
        private void BuildRing(ExplosionProfile p)
        {
            var go = new GameObject("ring") { layer = gameObject.layer };
            go.transform.SetParent(transform, false);

            _ringR = go.AddComponent<SpriteRenderer>();
            _ringR.sprite = Disc(true);
            _ringR.color = p.sparkColor;
            _ringR.sortingOrder = 4;

            _ring = go.transform;
            _ringSize = p.radius * 2f * p.ringScale;
            _ringLife = 0.22f;
        }

        // ─────────────────────────────────────────────────────────────────────

        private void Update()
        {
            float dt = Time.deltaTime;
            bool alive = false;

            alive |= StepPieces(dt);
            alive |= StepFlash(dt);
            alive |= StepRing(dt);

            if (!alive) Destroy(gameObject);
        }

        private bool StepPieces(float dt)
        {
            bool alive = false;

            for (int i = 0; i < _pieces.Length; i++)
            {
                ref Piece piece = ref _pieces[i];
                if (!piece.T) continue;

                piece.Age += dt;
                if (piece.Age >= piece.Life)
                {
                    piece.R.enabled = false;
                    piece.T = null;
                    continue;
                }

                alive = true;
                float t = piece.Age / piece.Life;

                piece.Vel += Physics2D.gravity * (piece.Gravity * dt);
                piece.Vel /= 1f + piece.Drag * dt;
                piece.Pos += piece.Vel * dt;

                // Snapped on the way out, never in the maths, so a slow piece still drifts.
                piece.T.localPosition = new Vector3(
                    Mathf.Round(piece.Pos.x / Snap) * Snap,
                    Mathf.Round(piece.Pos.y / Snap) * Snap, 0f);
                piece.T.localRotation = Quaternion.Euler(0f, 0f, piece.Spin * piece.Age);

                // White hot, then the fire colours, then ash — and only then does it fade, so
                // the piece is a cooling ember rather than a dot someone turned the alpha down on.
                Color c = t < 0.28f
                    ? Color.Lerp(_hot, _mid, t / 0.28f)
                    : Color.Lerp(_mid, _cool, (t - 0.28f) / 0.72f);
                c.a = t < 0.7f ? 1f : 1f - (t - 0.7f) / 0.3f;
                piece.R.color = c;

                float shrink = Mathf.Lerp(1f, 0.55f, t);
                piece.T.localScale = new Vector3(piece.Size * shrink, piece.Size * shrink, 1f);
            }

            return alive;
        }

        private bool StepFlash(float dt)
        {
            if (!_flash) return false;

            _flashAge += dt;
            float t = _flashAge / _flashLife;
            if (t >= 1f)
            {
                Destroy(_flash.gameObject);
                _flash = null;
                return false;
            }

            // Wide at once and gone almost as fast: the eye reads the first frame and the rest
            // is what keeps it from being a single-frame pop.
            float size = _flashSize * Mathf.Lerp(0.75f, 1.1f, t);
            _flash.localScale = new Vector3(size, size, 1f);

            var c = _flashR.color;
            c.a = 1f - t * t;
            _flashR.color = c;
            return true;
        }

        private bool StepRing(float dt)
        {
            if (!_ring) return false;

            _ringAge += dt;
            float t = _ringAge / _ringLife;
            if (t >= 1f)
            {
                Destroy(_ring.gameObject);
                _ring = null;
                return false;
            }

            // Out fast, then easing off, the way a front loses to the air.
            float size = _ringSize * Mathf.Sqrt(t);
            _ring.localScale = new Vector3(size, size, 1f);

            var c = _ringR.color;
            c.a = (1f - t) * 0.75f;
            _ringR.color = c;
            return true;
        }
    }
}
