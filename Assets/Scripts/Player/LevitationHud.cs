using UnityEngine;

namespace Player
{
    /// <summary>
    /// Noita-style levitation meter: a small bar that floats near the player, shows while
    /// flying or recharging, and hides once full. Pure IMGUI so it needs no UXML wiring —
    /// drop it on the Player and it reads <see cref="PlayerMovement"/> automatically.
    /// </summary>
    [RequireComponent(typeof(PlayerMovement))]
    public class LevitationHud : MonoBehaviour
    {
        [Header("Placement")]
        [Tooltip("World-space offset from the player where the bar is anchored (Y up).")]
        [SerializeField] private Vector2 worldOffset = new Vector2(0f, 1.1f);
        [SerializeField] private float barWidth = 46f;
        [SerializeField] private float barHeight = 6f;

        [Header("Colors")]
        [SerializeField] private Color backColor = new Color(0f, 0f, 0f, 0.55f);
        [SerializeField] private Color fullColor = new Color(0.45f, 0.85f, 1f, 0.95f);
        [SerializeField] private Color lowColor = new Color(1f, 0.7f, 0.2f, 0.95f);
        [SerializeField] private Color emptyColor = new Color(1f, 0.35f, 0.35f, 0.95f);

        [Header("Behaviour")]
        [Tooltip("Fade the bar out this many seconds after it fills up while grounded.")]
        [SerializeField] private float hideDelay = 0.6f;

        private PlayerMovement _movement;
        private Camera _cam;
        private Texture2D _px;
        private float _fullSince = -999f;

        private void Awake()
        {
            _movement = GetComponent<PlayerMovement>();
            _cam = Camera.main;
            _px = Texture2D.whiteTexture;
        }

        private void Update()
        {
            // Track how long we've been topped off so we can fade out when idle.
            if (_movement.CapacityNormalized >= 0.999f) { if (_fullSince < 0f) _fullSince = Time.unscaledTime; }
            else _fullSince = -1f;
        }

        private void OnGUI()
        {
            if (_cam == null) return;

            float t = _movement.CapacityNormalized;
            bool full = t >= 0.999f;

            // Show while flying or not full; once full, linger briefly then hide.
            float alpha = 1f;
            if (full && !_movement.IsLevitating)
            {
                float idle = _fullSince >= 0f ? Time.unscaledTime - _fullSince : hideDelay + 1f;
                if (idle > hideDelay) return;
                alpha = Mathf.Clamp01(1f - (idle / hideDelay));
            }

            Vector3 world = transform.position + (Vector3)worldOffset;
            Vector3 sp = _cam.WorldToScreenPoint(world);
            if (sp.z <= 0f) return; // behind the camera

            float x = sp.x - barWidth * 0.5f;
            float y = Screen.height - sp.y - barHeight * 0.5f; // OnGUI origin is top-left
            const float pad = 1f;

            Color fill = t <= 0.001f ? emptyColor : (t < 0.25f ? lowColor : fullColor);

            var prev = GUI.color;

            GUI.color = new Color(backColor.r, backColor.g, backColor.b, backColor.a * alpha);
            GUI.DrawTexture(new Rect(x - pad, y - pad, barWidth + pad * 2f, barHeight + pad * 2f), _px);

            GUI.color = new Color(fill.r, fill.g, fill.b, fill.a * alpha);
            GUI.DrawTexture(new Rect(x, y, barWidth * t, barHeight), _px);

            GUI.color = prev;
        }
    }
}
