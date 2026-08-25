using UnityEngine;

namespace Hazards
{
    /// <summary>
    /// A belt surface. Anything dynamic resting on it is dragged along the belt's local +X,
    /// whatever it would rather be doing — which is the whole point of a disposal line: a
    /// creature that refuses to walk off a ledge still has to go where the belt takes it.
    ///
    /// The grip is applied after the riders have had their own say (collision callbacks run
    /// inside the physics step, i.e. after every FixedUpdate), so the belt wins the argument
    /// without having to know anything about who is standing on it.
    ///
    /// One length field drives the collider and the drawing together, and it does so in edit
    /// mode: stretch a belt and it is a belt, the right size, pointing the right way, saved in
    /// the scene like anything else. Play mode adds nothing to it but the dragging.
    /// </summary>
    [RequireComponent(typeof(BoxCollider2D))]
    [RequireComponent(typeof(Rigidbody2D))]
    [RequireComponent(typeof(SpriteRenderer))]
    [AddComponentMenu("PhysFun/Conveyor")]
    public sealed class Conveyor : MonoBehaviour
    {
        [Header("Belt")]
        [Tooltip("Length and thickness in world units. Drives the collider and the drawing at once.")]
        [SerializeField] private Vector2 size = new(12f, 0.8f);

        [Tooltip("Belt speed along local +X, in units/s. Negative runs it the other way, and the " +
                 "chevrons turn round to match.")]
        [SerializeField] private float speed = -1.6f;

        [Tooltip("How hard the belt grips, in units/s^2 of pull toward belt speed. This is what " +
                 "decides who wins: a rider whose own acceleration is higher can walk against the " +
                 "belt, one below it is cargo. Creatures accelerate at 20 and the player at 30, so " +
                 "40 carries both while still letting them lean into it.")]
        [SerializeField] private float grip = 40f;

        private BoxCollider2D _hull;
        private SpriteRenderer _view;
        private Rigidbody2D _rb;

        /// <summary>Belt speed along local +X. Safe to change while it is running.</summary>
        public float Speed
        {
            get => speed;
            set
            {
                speed = value;
                Apply();
            }
        }

        // ------------------------------------------------------------------ authoring

        private void Reset()
        {
            Cache();

            // A driven surface rather than scenery. It never actually moves — the riders' own
            // velocities are what get changed — but being a body is what guarantees the belt is
            // told who is standing on it, which a bare static collider is not.
            _rb.bodyType = RigidbodyType2D.Kinematic;
            _rb.gravityScale = 0f;

            Apply();
        }

        private void OnValidate() => Apply();

        private void Awake()
        {
            Cache();
            if (!Application.isPlaying) return;

            _rb.bodyType = RigidbodyType2D.Kinematic;
            _rb.linearVelocity = Vector2.zero;
            _rb.angularVelocity = 0f;
        }

        private void Cache()
        {
            if (!_hull) _hull = GetComponent<BoxCollider2D>();
            if (!_view) _view = GetComponent<SpriteRenderer>();
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
        }

        /// <summary>
        /// Push the one size onto the two things that need it, and point the chevrons the way the
        /// belt runs. Everything written here is real serialised state, not a preview.
        /// </summary>
        private void Apply()
        {
            Cache();
            if (size.x <= 0f || size.y <= 0f) return;

            // Written only where it differs: assigning the same value back would still mark the
            // scene or the prefab dirty, and merely selecting a belt should not count as an edit.
            if (_hull.size != size) _hull.size = size;
            if (_hull.offset != Vector2.zero) _hull.offset = Vector2.zero;

            // Tiled rather than stretched, so a longer belt is more chevrons rather than longer
            // ones. Needs the sprite imported as Full Rect, which BeltChevron is.
            if (_view.drawMode != SpriteDrawMode.Tiled) _view.drawMode = SpriteDrawMode.Tiled;
            if (_view.tileMode != SpriteTileMode.Continuous) _view.tileMode = SpriteTileMode.Continuous;
            if (_view.size != size) _view.size = size;

            bool back = speed < 0f;
            if (_view.flipX != back) _view.flipX = back;
        }

        // ------------------------------------------------------------------ belt

        private void OnCollisionStay2D(Collision2D c)
        {
            var rider = c.rigidbody;
            if (!rider || rider.bodyType != RigidbodyType2D.Dynamic) return;

            // Only the component along the belt is touched: gravity, and anything trying to climb
            // off sideways, are left to the physics engine.
            Vector2 along = transform.right;
            float carried = Vector2.Dot(rider.linearVelocity, along);
            float step = grip * Time.fixedDeltaTime;
            rider.linearVelocity += along * Mathf.Clamp(speed - carried, -step, step);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.matrix = transform.localToWorldMatrix;
            Gizmos.color = Color.cyan;

            float dir = Mathf.Sign(speed);
            float y = size.y * 0.5f + 0.2f;
            float to = size.x * 0.35f * dir;

            Gizmos.DrawLine(new Vector3(-to, y), new Vector3(to, y));
            Gizmos.DrawLine(new Vector3(to, y), new Vector3(to - 0.25f * dir, y + 0.12f));
            Gizmos.DrawLine(new Vector3(to, y), new Vector3(to - 0.25f * dir, y - 0.12f));
        }
    }
}
