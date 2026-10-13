using UnityEngine;
using UnityEngine.UIElements;

namespace Interaction
{
    /// <summary>
    /// The player's side of <see cref="Interactable"/>: every frame it finds the nearest one in
    /// reach, draws a one-pixel outline round it, shows the prompt at the foot of the screen,
    /// and uses it when the key goes down.
    ///
    /// Nothing has to be set up for it. It installs itself after the first scene loads and
    /// lives for the whole session, reads the player from <see cref="App"/>, and puts its
    /// prompt into the player's own UIDocument (the one the levitation bar is drawn in), or
    /// any UIDocument in the scene if the player has none.
    ///
    /// The outline is four copies of the focused sprite in one flat colour
    /// (PhysFun/SpriteSilhouette), a pixel out up, down, left and right, drawn just behind it.
    /// They follow the sprite every frame, so a door that swings open, a prop that is half
    /// burnt away, keeps its outline true to what is left. They are never parented to it:
    /// whatever is outlined can be burnt or blown away at any moment, and would take them along.
    /// </summary>
    public sealed class InteractionSystem : MonoBehaviour
    {
        public static KeyCode Key = KeyCode.E;
        public static Color OutlineColor = new(1f, 0.88f, 0.55f, 1f);

        private static InteractionSystem _instance;
        private static readonly Vector2[] Offsets = { Vector2.right, Vector2.left, Vector2.up, Vector2.down };

        private Interactable _focus;
        private SpriteRenderer[] _outline;
        private Material _silhouette;

        private VisualElement _prompt;
        private Label _verb;
        private UIDocument _doc;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            if (_instance) return;
            var go = new GameObject("~InteractionSystem") { hideFlags = HideFlags.HideAndDontSave };
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<InteractionSystem>();
        }

        private void Awake()
        {
            var shader = Resources.Load<Shader>("Shaders/SpriteSilhouette");
            if (!shader) shader = Shader.Find("GUI/Text Shader");
            _silhouette = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            _outline = new SpriteRenderer[Offsets.Length];
            for (int i = 0; i < Offsets.Length; i++)
            {
                var o = new GameObject("~outline") { hideFlags = HideFlags.HideAndDontSave };
                o.transform.SetParent(transform, false);
                _outline[i] = o.AddComponent<SpriteRenderer>();
                _outline[i].sharedMaterial = _silhouette;
                _outline[i].enabled = false;
            }
        }

        private void OnDestroy()
        {
            if (_silhouette) Destroy(_silhouette);
        }

        private void Update()
        {
            var player = App.Instance.PlayerGo;
            var next = player ? Nearest(player) : null;
            if (next != _focus) Focus(next);
            if (_focus && Input.GetKeyDown(Key)) _focus.Interact(player);
        }

        private void LateUpdate()
        {
            FollowOutline();
            UpdatePrompt();
        }

        private static Interactable Nearest(GameObject player)
        {
            var col = player.GetComponent<Collider2D>();
            Vector2 at = col ? (Vector2)col.bounds.center : (Vector2)player.transform.position;
            Interactable best = null;
            float bestD = float.MaxValue;
            foreach (var it in Interactable.All)
            {
                if (!it || !it.isActiveAndEnabled) continue;
                float d = Vector2.Distance(at, it.Point);
                if (d > it.Reach || d >= bestD || !it.CanInteract(player)) continue;
                best = it;
                bestD = d;
            }
            return best;
        }

        private void Focus(Interactable next) => _focus = next;

        private void FollowOutline()
        {
            var target = _focus ? _focus.Outlined : null;
            if (!target || !target.sprite)
            {
                foreach (var o in _outline) o.enabled = false;
                return;
            }
            // one sprite pixel out, in world units - not scaled with the target (an open door
            // is squeezed sideways, its outline should not be)
            var t = target.transform;
            float px = 1f / target.sprite.pixelsPerUnit;
            for (int i = 0; i < _outline.Length; i++)
            {
                var o = _outline[i];
                o.enabled = target.enabled;
                o.sprite = target.sprite;
                o.drawMode = target.drawMode;
                if (target.drawMode != SpriteDrawMode.Simple) o.size = target.size;
                o.flipX = target.flipX;
                o.flipY = target.flipY;
                o.color = OutlineColor;
                o.sortingLayerID = target.sortingLayerID;
                o.sortingOrder = target.sortingOrder - 1;
                o.transform.SetPositionAndRotation(t.position + t.rotation * (Vector3)(Offsets[i] * px), t.rotation);
                o.transform.localScale = t.lossyScale;
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // The prompt: "[E]  Open door", centred at the foot of the screen
        // ─────────────────────────────────────────────────────────────────────

        private void UpdatePrompt()
        {
            if (!EnsurePrompt()) return;
            bool show = _focus;
            _prompt.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
            if (show) _verb.text = _focus.Verb;
        }

        private bool EnsurePrompt()
        {
            if (_prompt != null && _prompt.panel != null) return true;
            _prompt = null;
            var player = App.Instance.PlayerGo;
            _doc = player ? player.GetComponentInChildren<UIDocument>() : null;
            if (!_doc) _doc = FindAnyObjectByType<UIDocument>();
            if (!_doc || _doc.rootVisualElement == null) return false;

            var bar = new VisualElement { name = "interaction-prompt", pickingMode = PickingMode.Ignore };
            bar.style.position = Position.Absolute;
            bar.style.left = 0;
            bar.style.right = 0;
            bar.style.bottom = Length.Percent(7);
            bar.style.flexDirection = FlexDirection.Row;
            bar.style.justifyContent = Justify.Center;

            var pill = new VisualElement { pickingMode = PickingMode.Ignore };
            pill.style.flexDirection = FlexDirection.Row;
            pill.style.alignItems = Align.Center;
            pill.style.backgroundColor = new Color(0.04f, 0.05f, 0.07f, 0.78f);
            pill.style.paddingLeft = pill.style.paddingRight = 12;
            pill.style.paddingTop = pill.style.paddingBottom = 5;
            SetRadius(pill, 4);

            var key = new Label(Key.ToString()) { pickingMode = PickingMode.Ignore };
            key.style.color = OutlineColor;
            key.style.fontSize = 16;
            key.style.unityFontStyleAndWeight = FontStyle.Bold;
            key.style.paddingLeft = key.style.paddingRight = 6;
            key.style.marginRight = 10;
            key.style.borderTopWidth = key.style.borderBottomWidth = 1;
            key.style.borderLeftWidth = key.style.borderRightWidth = 1;
            key.style.borderTopColor = key.style.borderBottomColor = OutlineColor;
            key.style.borderLeftColor = key.style.borderRightColor = OutlineColor;
            SetRadius(key, 3);

            _verb = new Label { pickingMode = PickingMode.Ignore };
            _verb.style.color = new Color(0.9f, 0.9f, 0.88f);
            _verb.style.fontSize = 16;

            pill.Add(key);
            pill.Add(_verb);
            bar.Add(pill);
            _doc.rootVisualElement.Add(bar);
            _prompt = bar;
            return true;
        }

        private static void SetRadius(VisualElement e, float r)
        {
            e.style.borderTopLeftRadius = e.style.borderTopRightRadius = r;
            e.style.borderBottomLeftRadius = e.style.borderBottomRightRadius = r;
        }
    }
}
