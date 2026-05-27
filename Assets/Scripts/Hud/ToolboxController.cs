using System.Collections.Generic;
using System.Linq;
using Spawners;
using UnityEngine;
using UnityEngine.UIElements;

[RequireComponent(typeof(UIDocument))]
public class ToolboxController : MonoBehaviour
{
    public enum Tool { None, Spawn, Erase, Crack, Synth }

    [Header("Spawn")]
    [SerializeField] private string spawnResourceFolder = "SpawnImages";

    [Header("Erase")]
    [SerializeField] private LayerMask eraseTargets = ~0;
    [SerializeField] private string[] eraseIgnoreLayers = { "Untouchable" };
    [SerializeField] private int eraseSimplifyLevel = 2;
    [SerializeField] private float eraseRebuildInterval = 0.15f;  // seconds between mid-stroke collider rebuilds

    [Header("Crack")]
    [SerializeField] private LayerMask crackTargets = ~0;
    [SerializeField] private string[] crackIgnoreLayers = { "Untouchable" };
    [SerializeField] private float crackImpactImpulse = 6f;     // outward push per shard
    [SerializeField] private float crackImpactFalloff = 0.6f;   // world meters; smaller = more concentrated burst

    [Header("Debug overlay")]
    [SerializeField] private Color eraseRingColor = new Color(1f, 0.4f, 0.4f, 0.85f);
    [SerializeField] private Color crackRingColor = new Color(0.4f, 0.7f, 1f, 0.85f);

    [Header("Synth")]
    [SerializeField] private int sketchSize = 500;
    [SerializeField] private float synthPixelsPerUnit = 100f;

    [Header("Defaults")]
    [SerializeField] private Tool startingTool = Tool.Spawn;

    private UIDocument _doc;
    private Camera _cam;

    private Tool _current = Tool.None;
    private readonly Dictionary<Tool, Button> _toolButtons = new();
    private readonly Dictionary<Tool, VisualElement> _toolPanels = new();
    private Label _activeLabel;

    // Spawn state
    private readonly List<VisualElement> _itemCells = new();
    private List<Sprite> _spawnSprites = new();
    private Sprite _selectedSprite;
    private GameObject _preview;
    private float _previewAngleDeg;
    private Slider _lodSlider;

    // Erase state
    private SpriteEraseService _eraseService;
    private Slider _eraseBrushSlider;
    private float _lastEraseRebuild;
    private int _eraseEffectiveMask;
    private int _crackEffectiveMask;

    // Crack state
    private Slider _crackRadiusSlider;
    private SliderInt _crackPiecesSlider;

    // Synth state
    private SketchCanvas _sketch;
    private VisualElement _sketchSurface;
    private SliderInt _synthBrushSlider;
    private bool _drawing;
    private bool _hasLastSketchPos;
    private Vector2Int _lastSketchPos;
    private bool _pointerOverUI;

    // Overlay
    private Texture2D _ringTex;
    private Toggle _debugToggle;

    private void Awake()
    {
        _doc = GetComponent<UIDocument>();
        _cam = Camera.main;
        _eraseService = new SpriteEraseService();
        _sketch = new SketchCanvas(sketchSize, sketchSize, new Color32(0, 0, 0, 0));
        _ringTex = BuildRingTexture(128, 2.5f);

        // *Targets minus any *IgnoreLayers (e.g. "Untouchable"), computed once.
        _eraseEffectiveMask = MaskMinusLayers(eraseTargets.value, eraseIgnoreLayers);
        _crackEffectiveMask = MaskMinusLayers(crackTargets.value, crackIgnoreLayers);
    }

    private void OnEnable()
    {
        var root = _doc.rootVisualElement;
        _activeLabel = root.Q<Label>("active-label");

        _toolButtons[Tool.Spawn] = root.Q<Button>("tool-spawn");
        _toolButtons[Tool.Erase] = root.Q<Button>("tool-erase");
        _toolButtons[Tool.Crack] = root.Q<Button>("tool-crack");
        _toolButtons[Tool.Synth] = root.Q<Button>("tool-synth");
        _toolButtons[Tool.None]  = root.Q<Button>("tool-none");

        _toolPanels[Tool.Spawn] = root.Q<VisualElement>("panel-spawn");
        _toolPanels[Tool.Erase] = root.Q<VisualElement>("panel-erase");
        _toolPanels[Tool.Crack] = root.Q<VisualElement>("panel-crack");
        _toolPanels[Tool.Synth] = root.Q<VisualElement>("panel-synth");

        foreach (var kv in _toolButtons)
        {
            var t = kv.Key;
            kv.Value.clicked += () => Select(t);
        }

        BuildSpawnPanel(root);
        BuildErasePanel(root);
        BuildCrackPanel(root);
        BuildSynthPanel(root);

        _debugToggle = root.Q<Toggle>("show-debug");

        // Track whether pointer is over the toolbox so world-space tools don't fire through UI.
        var toolboxRoot = root.Q<VisualElement>("toolbox-root");
        toolboxRoot.RegisterCallback<PointerEnterEvent>(_ => _pointerOverUI = true);
        toolboxRoot.RegisterCallback<PointerLeaveEvent>(_ => _pointerOverUI = false);

        Select(startingTool);
    }

    private void Update()
    {
        // Hotkeys
        if (Input.GetKeyDown(KeyCode.Alpha1)) Select(Tool.Spawn);
        else if (Input.GetKeyDown(KeyCode.Alpha2)) Select(Tool.Erase);
        else if (Input.GetKeyDown(KeyCode.Alpha3)) Select(Tool.Crack);
        else if (Input.GetKeyDown(KeyCode.Alpha4)) Select(Tool.Synth);
        else if (Input.GetKeyDown(KeyCode.Alpha5)) Select(Tool.None);

        switch (_current)
        {
            case Tool.Spawn: TickSpawn(); break;
            case Tool.Erase: if (!_pointerOverUI) TickErase(); break;
            case Tool.Crack: if (!_pointerOverUI) TickCrack(); break;
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Tool switching
    // ─────────────────────────────────────────────────────────────────────────

    private void Select(Tool tool)
    {
        // Leaving a tool: clean its transient state.
        if (_current == Tool.Spawn && tool != Tool.Spawn) CancelSpawnPreview();

        _current = tool;

        foreach (var kv in _toolButtons)
        {
            if (kv.Value == null) continue;
            if (kv.Key == tool) kv.Value.AddToClassList("selected");
            else kv.Value.RemoveFromClassList("selected");
        }

        foreach (var kv in _toolPanels)
        {
            if (kv.Value == null) continue;
            if (kv.Key == tool) kv.Value.AddToClassList("visible");
            else kv.Value.RemoveFromClassList("visible");
        }

        if (_activeLabel != null) _activeLabel.text = $"Active: {tool}";
    }

    // ─────────────────────────────────────────────────────────────────────────
    // SPAWN
    // ─────────────────────────────────────────────────────────────────────────

    private void BuildSpawnPanel(VisualElement root)
    {
        _lodSlider = root.Q<Slider>("lod-slider");
        var grid = root.Q<VisualElement>("items-grid");

        _spawnSprites = Resources.LoadAll<Sprite>(spawnResourceFolder).ToList();
        foreach (var s in _spawnSprites)
        {
            var cell = new VisualElement();
            cell.AddToClassList("item-cell");
            if (s != null && s.texture != null)
            {
                cell.style.backgroundImage = new StyleBackground(s.texture);
                // Slice the texture region for atlas-style sprites.
                var rect = s.rect;
                var tex = s.texture;
                cell.style.backgroundPositionX = new BackgroundPosition(BackgroundPositionKeyword.Center);
                cell.style.backgroundPositionY = new BackgroundPosition(BackgroundPositionKeyword.Center);
                cell.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Contain);
                cell.tooltip = s.name;
            }

            var capturedSprite = s;
            cell.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.button != 0) return;
                SelectSpawnItem(capturedSprite);
                StartSpawnPreview(capturedSprite);
                cell.CapturePointer(evt.pointerId);
            });
            cell.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (evt.button != 0) return;
                if (cell.HasPointerCapture(evt.pointerId))
                    cell.ReleasePointer(evt.pointerId);
                CommitSpawnPreview();
            });
            cell.RegisterCallback<PointerCaptureOutEvent>(_ => CommitSpawnPreview());
            _itemCells.Add(cell);
            grid.Add(cell);
        }
    }

    private void SelectSpawnItem(Sprite s)
    {
        _selectedSprite = s;
        for (int i = 0; i < _itemCells.Count; i++)
        {
            if (_spawnSprites[i] == s) _itemCells[i].AddToClassList("selected");
            else _itemCells[i].RemoveFromClassList("selected");
        }
    }

    private void StartSpawnPreview(Sprite s)
    {
        if (s == null) return;
        CancelSpawnPreview();
        _previewAngleDeg = 0f;
        _preview = SpriteFactory.Create(s, MouseWorld(), null, false, Mathf.RoundToInt(_lodSlider.value));
        var sr = _preview.GetComponent<SpriteRenderer>();
        if (sr) { var c = sr.color; c.a = 0.7f; sr.color = c; }
        var rb = _preview.GetComponent<Rigidbody2D>(); if (rb) rb.simulated = false;
    }

    private void CommitSpawnPreview()
    {
        if (_preview == null) return;
        var sr = _preview.GetComponent<SpriteRenderer>();
        if (sr) { var c = sr.color; c.a = 1f; sr.color = c; }
        var rb = _preview.GetComponent<Rigidbody2D>(); if (rb) rb.simulated = true;
        _preview = null;
    }

    private void CancelSpawnPreview()
    {
        if (_preview != null) { Destroy(_preview); _preview = null; }
    }

    private void TickSpawn()
    {
        if (_preview == null) return;
        _preview.transform.position = MouseWorld();

        float wheel = Input.mouseScrollDelta.y;
        if (Mathf.Abs(wheel) > 0.0001f)
        {
            _previewAngleDeg += wheel * 15f;
            _preview.transform.rotation = Quaternion.Euler(0f, 0f, _previewAngleDeg);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // ERASE
    // ─────────────────────────────────────────────────────────────────────────

    private void BuildErasePanel(VisualElement root)
    {
        _eraseBrushSlider = root.Q<Slider>("erase-brush");
    }

    private void TickErase()
    {
        if (Input.GetMouseButton(0))
        {
            float radius = _eraseBrushSlider != null ? _eraseBrushSlider.value : 0.2f;
            Vector3 wp = _cam.ScreenToWorldPoint(Input.mousePosition); wp.z = 0f;

            var hits = Physics2D.OverlapCircleAll(wp, radius, _eraseEffectiveMask);
            foreach (var h in hits) _eraseService.EraseCircle(h.gameObject, wp, radius);

            // Push pixel changes to GPU (subregion upload, cheap).
            _eraseService.Flush();

            // Rebuild colliders on a timer so collisions catch up without per-frame cost.
            if (Time.unscaledTime - _lastEraseRebuild > eraseRebuildInterval)
            {
                _eraseService.RebuildModifiedColliders(eraseSimplifyLevel);
                _lastEraseRebuild = Time.unscaledTime;
            }
        }

        // Always rebuild once on release so the final shape is correct.
        if (Input.GetMouseButtonUp(0))
        {
            _eraseService.RebuildModifiedColliders(eraseSimplifyLevel);
            _lastEraseRebuild = Time.unscaledTime;
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // CRACK
    // ─────────────────────────────────────────────────────────────────────────

    private void BuildCrackPanel(VisualElement root)
    {
        _crackRadiusSlider = root.Q<Slider>("crack-radius");
        _crackPiecesSlider = root.Q<SliderInt>("crack-pieces");
    }

    private void TickCrack()
    {
        // Either mouse button triggers a crack — RMB and LMB both feel natural for a one-shot impact.
        if (!Input.GetMouseButtonDown(0) && !Input.GetMouseButtonDown(1)) return;
        float radius = _crackRadiusSlider != null ? _crackRadiusSlider.value : 2f;
        int pieces = _crackPiecesSlider != null ? _crackPiecesSlider.value : 6;
        Vector3 wp = _cam.ScreenToWorldPoint(Input.mousePosition); wp.z = 0f;

        var hits = Physics2D.OverlapCircleAll(wp, radius, _crackEffectiveMask);
        foreach (var h in hits)
        {
            Cracker.Cracker.Crack(
                h.gameObject,
                pieces,
                impactWorld: wp,
                impactImpulse: crackImpactImpulse,
                impactFalloff: crackImpactFalloff);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // SYNTH (draw)
    // ─────────────────────────────────────────────────────────────────────────

    private void BuildSynthPanel(VisualElement root)
    {
        _sketchSurface = root.Q<VisualElement>("sketch-surface");
        _synthBrushSlider = root.Q<SliderInt>("synth-brush");
        var createBtn = root.Q<Button>("synth-create");
        var clearBtn  = root.Q<Button>("synth-clear");

        _sketchSurface.style.backgroundImage = new StyleBackground(_sketch.Texture);
        _sketchSurface.style.backgroundSize = new BackgroundSize(BackgroundSizeType.Contain);

        _sketchSurface.RegisterCallback<PointerDownEvent>(OnSketchPointerDown);
        _sketchSurface.RegisterCallback<PointerMoveEvent>(OnSketchPointerMove);
        _sketchSurface.RegisterCallback<PointerUpEvent>(OnSketchPointerUp);
        _sketchSurface.RegisterCallback<PointerCaptureOutEvent>(_ => { _drawing = false; _hasLastSketchPos = false; });

        createBtn.clicked += OnSynthCreate;
        clearBtn.clicked  += () => _sketch.Clear();
    }

    private void OnSketchPointerDown(PointerDownEvent evt)
    {
        if (evt.button != 0) return;
        _drawing = true;
        _hasLastSketchPos = false;
        _sketchSurface.CapturePointer(evt.pointerId);
        PaintSketchAt(evt.localPosition);
        evt.StopPropagation();
    }

    private void OnSketchPointerMove(PointerMoveEvent evt)
    {
        if (!_drawing) return;
        PaintSketchAt(evt.localPosition);
    }

    private void OnSketchPointerUp(PointerUpEvent evt)
    {
        if (evt.button != 0) return;
        _drawing = false;
        _hasLastSketchPos = false;
        if (_sketchSurface.HasPointerCapture(evt.pointerId))
            _sketchSurface.ReleasePointer(evt.pointerId);
    }

    private void PaintSketchAt(Vector2 local)
    {
        var size = _sketchSurface.contentRect.size;
        if (size.x <= 0f || size.y <= 0f) return;

        float u = Mathf.Clamp01(local.x / size.x);
        // UI Toolkit local Y grows down; texture V grows up — flip.
        float v = 1f - Mathf.Clamp01(local.y / size.y);
        int px = Mathf.FloorToInt(u * (_sketch.Width - 1));
        int py = Mathf.FloorToInt(v * (_sketch.Height - 1));

        int r = _synthBrushSlider != null ? _synthBrushSlider.value : 8;
        var col = new Color32(255, 255, 255, 255);

        var pos = new Vector2Int(px, py);
        if (!_hasLastSketchPos)
        {
            _sketch.StampDisc(px, py, r, col);
            _lastSketchPos = pos;
            _hasLastSketchPos = true;
        }
        else
        {
            _sketch.DrawSegment(_lastSketchPos, pos, r, col);
            _lastSketchPos = pos;
        }
        _sketch.Apply();
    }

    private void OnSynthCreate()
    {
        var tex = _sketch.SnapshotCopy();
        var sprite = Sprite.Create(tex,
            new Rect(0, 0, tex.width, tex.height),
            new Vector2(0.5f, 0.5f),
            synthPixelsPerUnit);
        SpriteFactory.Create(sprite, Vector3.zero, null, false, 3);
    }

    // ─────────────────────────────────────────────────────────────────────────

    private static int MaskMinusLayers(int mask, string[] ignoreNames)
    {
        if (ignoreNames == null) return mask;
        foreach (var name in ignoreNames)
        {
            if (string.IsNullOrEmpty(name)) continue;
            int layer = LayerMask.NameToLayer(name);
            if (layer >= 0) mask &= ~(1 << layer);
        }
        return mask;
    }

    private Vector3 MouseWorld()
    {
        var sp = Input.mousePosition;
        sp.z = -_cam.transform.position.z;
        var wp = _cam.ScreenToWorldPoint(sp);
        wp.z = 0f;
        return wp;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // OnGUI brush/impact ring overlay (debug visual for world-space tools)
    // ─────────────────────────────────────────────────────────────────────────

    private void OnGUI()
    {
        if (_debugToggle != null && !_debugToggle.value) return;
        if (_pointerOverUI) return;
        if (_ringTex == null || _cam == null) return;

        bool isErase = _current == Tool.Erase;
        bool isCrack = _current == Tool.Crack;
        if (!isErase && !isCrack) return;

        float worldRadius =
            isErase ? (_eraseBrushSlider != null ? _eraseBrushSlider.value : 0.2f)
                    : (_crackRadiusSlider != null ? _crackRadiusSlider.value : 2f);

        // Convert world radius -> screen pixels via the camera.
        Vector3 mouseW = _cam.ScreenToWorldPoint(Input.mousePosition);
        Vector3 edgeW  = mouseW + new Vector3(worldRadius, 0f, 0f);
        Vector3 mouseS = _cam.WorldToScreenPoint(mouseW);
        Vector3 edgeS  = _cam.WorldToScreenPoint(edgeW);
        float screenR = Mathf.Abs(edgeS.x - mouseS.x);
        if (screenR < 2f) return;

        // OnGUI uses top-left origin; Input.mousePosition is bottom-left. Flip Y.
        float gx = Input.mousePosition.x - screenR;
        float gy = (Screen.height - Input.mousePosition.y) - screenR;

        var prev = GUI.color;
        GUI.color = isErase ? eraseRingColor : crackRingColor;
        GUI.DrawTexture(new Rect(gx, gy, screenR * 2f, screenR * 2f), _ringTex);
        GUI.color = prev;
    }

    private static Texture2D BuildRingTexture(int size, float thickness)
    {
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, false)
        {
            wrapMode = TextureWrapMode.Clamp,
            filterMode = FilterMode.Bilinear,
            hideFlags = HideFlags.DontSave
        };

        var pixels = new Color32[size * size];
        float center = size * 0.5f - 0.5f;
        float ringR = center - thickness; // leave one-pixel breathing room from the edge

        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                float dx = x - center;
                float dy = y - center;
                float d = Mathf.Sqrt(dx * dx + dy * dy);
                float a = Mathf.Clamp01(1f - Mathf.Abs(d - ringR) / thickness);
                pixels[y * size + x] = new Color32(255, 255, 255, (byte)(a * 255f));
            }
        }
        tex.SetPixels32(pixels);
        tex.Apply(false, true);
        return tex;
    }
}
