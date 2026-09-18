using Common;
using UnityEngine;
using UnityEngine.UIElements;

namespace Player
{
    /// <summary>
    /// Noita-style health bar: a single slab pinned to the top of the screen with the current
    /// and maximum health written across it. Drives the elements from <see cref="HealthBar"/>
    /// UXML; needs a <see cref="UIDocument"/> on the same object.
    ///
    /// Health is polled rather than event-driven: <see cref="Damageable"/> also loses health to
    /// crush ticks and regains it through <see cref="Damageable.Heal"/>, and reading the value
    /// once a frame covers every path without the bar caring which one moved it.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public class HealthHud : MonoBehaviour
    {
        [Header("Target")]
        [Tooltip("Whose health to show. Leave empty to pick up the player once it registers " +
                 "itself with App.")]
        [SerializeField] private Damageable target;

        [Header("Behaviour")]
        [Tooltip("Fill fraction below which the bar turns a brighter red.")]
        [Range(0f, 1f)] [SerializeField] private float lowThreshold = 0.3f;

        [Tooltip("How fast the darker trailing bar catches up to the real value, in fractions " +
                 "of the total per second. 0 pins it to the fill.")]
        [SerializeField] private float ghostCatchUp = 0.6f;

        [Tooltip("Seconds the trailing bar holds still after a hit before it starts draining.")]
        [SerializeField] private float ghostHold = 0.4f;

        private UIDocument _doc;
        private VisualElement _root;
        private VisualElement _fill;
        private VisualElement _ghost;
        private Label _label;

        // The trailing bar's value, and the moment it is allowed to start sliding after a hit.
        private float _ghostValue = -1f;   // < 0 = adopt the target's value on the first frame
        private float _ghostHoldUntil;
        private float _lastValue = -1f;

        private void Awake() => _doc = GetComponent<UIDocument>();

        private void OnEnable()
        {
            var r = _doc.rootVisualElement;
            _root = r.Q<VisualElement>("health-root");
            _fill = r.Q<VisualElement>("health-fill");
            _ghost = r.Q<VisualElement>("health-ghost");
            _label = r.Q<Label>("health-label");
            if (_root != null) _root.pickingMode = PickingMode.Ignore;

            _ghostValue = -1f;
            _lastValue = -1f;
        }

        private void LateUpdate()
        {
            if (_root == null || _fill == null) return;

            var d = Target();
            if (!d)
            {
                _root.EnableInClassList("health-root--hidden", true);
                return;
            }

            _root.EnableInClassList("health-root--hidden", false);

            float t = d.HealthNormalized;
            if (_ghostValue < 0f) _ghostValue = t;

            // The trailing bar marks where health used to be: it holds still for a beat after
            // every drop, then slides down to meet the fill. Healing it never lags — a gain
            // should read straight away.
            if (_lastValue >= 0f && t < _lastValue)
                _ghostHoldUntil = Time.unscaledTime + ghostHold;
            _lastValue = t;

            if (t >= _ghostValue)
                _ghostValue = t;
            else if (Time.unscaledTime >= _ghostHoldUntil)
                _ghostValue = ghostCatchUp > 0f
                    ? Mathf.Max(t, _ghostValue - ghostCatchUp * Time.unscaledDeltaTime)
                    : t;

            _fill.style.width = Length.Percent(t * 100f);
            if (_ghost != null) _ghost.style.width = Length.Percent(_ghostValue * 100f);
            _fill.EnableInClassList("health-fill--low", t < lowThreshold);

            if (_label != null)
                _label.text = $"{Mathf.CeilToInt(Mathf.Max(0f, d.Health))} / {d.MaxHealth}";
        }

        /// <summary>
        /// The bar's subject. The player registers with <see cref="App"/> in its own Awake and
        /// can be respawned, so the lookup is repeated rather than cached once.
        /// </summary>
        private Damageable Target()
        {
            if (target) return target;

            var go = App.Instance.PlayerGo;
            if (go) target = go.GetComponent<Damageable>();
            return target;
        }
    }
}
