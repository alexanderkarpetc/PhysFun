using UnityEngine;
using UnityEngine.UIElements;

namespace Player
{
    /// <summary>
    /// Noita-style levitation meter rendered with UI Toolkit. A small bar follows the player,
    /// shows while flying or recharging, and fades out once full. Drives the elements from
    /// <see cref="LevitationBar"/> UXML; needs a <see cref="UIDocument"/> on the same object.
    /// </summary>
    [RequireComponent(typeof(PlayerMovement))]
    [RequireComponent(typeof(UIDocument))]
    public class LevitationHud : MonoBehaviour
    {
        [Header("Placement")]
        [Tooltip("World-space offset from the player where the bar is anchored (Y up).")]
        [SerializeField] private Vector2 worldOffset = new Vector2(0f, 1.1f);

        [Header("Behaviour")]
        [Tooltip("Fill fraction below which the bar turns amber (matches the config refire feel).")]
        [Range(0f, 1f)] [SerializeField] private float lowThreshold = 0.25f;
        [Tooltip("Keep the bar visible this long after it fills up while grounded, then fade out.")]
        [SerializeField] private float hideDelay = 0.6f;

        private PlayerMovement _movement;
        private UIDocument _doc;
        private Camera _cam;

        private VisualElement _root;
        private VisualElement _fill;
        private float _fullSince = -1f;

        private void Awake()
        {
            _movement = GetComponent<PlayerMovement>();
            _doc = GetComponent<UIDocument>();
            _cam = Camera.main;
        }

        private void OnEnable()
        {
            var r = _doc.rootVisualElement;
            _root = r.Q<VisualElement>("levitation-root");
            _fill = r.Q<VisualElement>("levitation-fill");
            if (_root != null) _root.pickingMode = PickingMode.Ignore;
        }

        private void LateUpdate()
        {
            if (_root == null || _fill == null || _cam == null) return;
            if (_root.panel == null) return; // panel not ready yet this frame

            float t = _movement.CapacityNormalized;
            bool full = t >= 0.999f;

            // Visibility: linger briefly once full & grounded, then fade via USS transition.
            if (full && !_movement.IsLevitating)
            {
                if (_fullSince < 0f) _fullSince = Time.unscaledTime;
                bool expired = Time.unscaledTime - _fullSince > hideDelay;
                _root.EnableInClassList("levitation-root--hidden", expired);
            }
            else
            {
                _fullSince = -1f;
                _root.EnableInClassList("levitation-root--hidden", false);
            }

            // Fill amount + state color.
            _fill.style.width = Length.Percent(Mathf.Clamp01(t) * 100f);
            _fill.EnableInClassList("levitation-fill--empty", t <= 0.001f);
            _fill.EnableInClassList("levitation-fill--low", t > 0.001f && t < lowThreshold);

            // Follow the player: world -> panel coordinates, then center the bar on the anchor.
            Vector3 world = transform.position + (Vector3)worldOffset;
            Vector2 panelPos = RuntimePanelUtils.CameraTransformWorldToPanel(_root.panel, world, _cam);

            float w = _root.resolvedStyle.width;
            float h = _root.resolvedStyle.height;
            if (float.IsNaN(w)) w = 48f;
            if (float.IsNaN(h)) h = 8f;

            _root.style.left = panelPos.x - w * 0.5f;
            _root.style.top = panelPos.y - h * 0.5f;
        }
    }
}
