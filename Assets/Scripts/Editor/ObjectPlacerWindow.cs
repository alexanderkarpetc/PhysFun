using System.Collections.Generic;
using System.Linq;
using Materials;
using Spawners;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Places props into the open scene the way the in-game spawn tool places them at runtime:
    /// pick art from the palette, move the mouse, click. What lands is a real scene object —
    /// saved with the scene, undoable, selectable — not something that only exists once the
    /// game is running.
    ///
    /// Two palettes feed it. Sprites come from <c>Resources/SpawnImages</c> and are built by
    /// <see cref="SpriteFactory"/>, so a house or a beam dropped here has exactly the collider,
    /// material and mass it would have had if the player had spawned it. Prefabs come from
    /// <c>Resources/Prefabs</c> and are instantiated with their prefab link intact.
    ///
    /// The thing under the cursor is the object itself, held out of the scene until you click —
    /// so what gets placed is what you were already looking at.
    /// </summary>
    public sealed class ObjectPlacerWindow : EditorWindow
    {
        private const string SpriteFolder = "SpawnImages";               // under Resources
        private const string PrefabFolder = "Assets/Resources/Prefabs";
        private const float CellSize = 64f;

        private enum Source { Sprites, Prefabs }

        [MenuItem("Tools/PhysFun/Object Placer")]
        private static void Open() => GetWindow<ObjectPlacerWindow>("Object Placer");

        [SerializeField] private Source source = Source.Sprites;
        [SerializeField] private string selected;                // entry name, survives domain reload
        [SerializeField] private bool armed;

        [SerializeField] private Transform parent;
        [SerializeField] private PhysMaterialId physMaterial = PhysMaterialId.Default;
        [SerializeField] private int simplifyLevel;
        [SerializeField] private bool makeStatic;
        [SerializeField] private float scale = 1f;
        [SerializeField] private float angle;
        [SerializeField] private float randomAngle;              // ± degrees rolled per placement
        [SerializeField] private float randomScale;              // ± fraction rolled per placement
        [SerializeField] private float gridSnap;                 // 0 = free
        [SerializeField] private bool scatterDrag;
        [SerializeField] private float scatterSpacing = 1f;
        [SerializeField] private bool selectPlaced = true;

        private sealed class Entry
        {
            public string Name;
            public Sprite Sprite;
            public GameObject Prefab;
        }

        private readonly List<Entry> _sprites = new();
        private readonly List<Entry> _prefabs = new();
        private string _search = "";
        private Vector2 _paletteScroll;

        // Ghost state — the object that follows the cursor, plus the randoms it was rolled with.
        private GameObject _preview;
        private readonly List<(SpriteRenderer sr, Color color)> _previewColors = new();
        private Vector3 _previewBaseScale = Vector3.one;
        private float _rolledAngle;
        private float _rolledScale = 1f;
        private Vector3 _lastPlaced;
        private bool _hasLastPlaced;

        private List<Entry> Palette => source == Source.Sprites ? _sprites : _prefabs;

        private void OnEnable()
        {
            LoadPalette();
            Roll();
            SceneView.duringSceneGui += OnSceneGui;
            AssemblyReloadEvents.beforeAssemblyReload += DestroyPreview;
        }

        private void OnDisable()
        {
            SceneView.duringSceneGui -= OnSceneGui;
            AssemblyReloadEvents.beforeAssemblyReload -= DestroyPreview;
            DestroyPreview();
        }

        private void LoadPalette()
        {
            _sprites.Clear();
            foreach (var s in Resources.LoadAll<Sprite>(SpriteFolder).OrderBy(s => s.name))
                _sprites.Add(new Entry { Name = s.name, Sprite = s });

            _prefabs.Clear();
            foreach (var guid in AssetDatabase.FindAssets("t:Prefab", new[] { PrefabFolder }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (go) _prefabs.Add(new Entry { Name = go.name, Prefab = go });
            }
            _prefabs.Sort((a, b) => string.CompareOrdinal(a.Name, b.Name));
        }

        private Entry Current()
        {
            if (string.IsNullOrEmpty(selected)) return null;
            foreach (var e in Palette)
                if (e.Name == selected) return e;
            return null;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Window
        // ─────────────────────────────────────────────────────────────────────────

        private void OnGUI()
        {
            if (Application.isPlaying)
            {
                EditorGUILayout.HelpBox("Edit mode only — anything placed while the game runs is " +
                                        "thrown away when you stop.", MessageType.Warning);
                return;
            }

            DrawArmSection();
            EditorGUILayout.Space();
            DrawPlacementSection();
            EditorGUILayout.Space();
            DrawPalette();
        }

        private void DrawArmSection()
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                bool wasArmed = armed;
                armed = GUILayout.Toggle(armed, armed ? "Placing — click in the scene" : "Start placing",
                                         "Button", GUILayout.Height(28f));
                if (wasArmed && !armed) DestroyPreview();

                if (GUILayout.Button("Refresh", GUILayout.Width(70f), GUILayout.Height(28f)))
                    LoadPalette();
            }

            EditorGUILayout.LabelField("LMB place • Shift+wheel rotate • Ctrl+wheel scale • Esc stop",
                                       EditorStyles.miniLabel);
        }

        private void DrawPlacementSection()
        {
            parent = (Transform)EditorGUILayout.ObjectField("Parent", parent, typeof(Transform), true);

            // Material, collider LOD and the static flag are all things the sprite pipeline applies;
            // a prefab already carries its own.
            using (new EditorGUI.DisabledScope(source != Source.Sprites))
            {
                physMaterial = (PhysMaterialId)EditorGUILayout.EnumPopup("Material", physMaterial);
                simplifyLevel = EditorGUILayout.IntSlider("Collider LOD", simplifyLevel, 0, 5);
                makeStatic = EditorGUILayout.Toggle(
                    new GUIContent("Static", "Level geometry that should not fall — beams, walls, " +
                                             "the shell of a house."), makeStatic);
            }

            scale = Mathf.Max(0.01f, EditorGUILayout.FloatField("Scale", scale));
            angle = EditorGUILayout.FloatField("Angle", angle);
            randomAngle = EditorGUILayout.Slider("± Random angle", randomAngle, 0f, 180f);
            randomScale = EditorGUILayout.Slider("± Random scale", randomScale, 0f, 0.9f);
            gridSnap = Mathf.Max(0f, EditorGUILayout.FloatField(
                new GUIContent("Grid snap", "World units. 0 places freely."), gridSnap));

            scatterDrag = EditorGUILayout.Toggle(
                new GUIContent("Place on drag", "Hold the button down and sweep to lay a trail — " +
                                                "rubble, planks, a row of crates."), scatterDrag);
            using (new EditorGUI.DisabledScope(!scatterDrag))
                scatterSpacing = EditorGUILayout.Slider("Spacing", scatterSpacing, 0.1f, 10f);

            selectPlaced = EditorGUILayout.Toggle("Select after place", selectPlaced);
        }

        private void DrawPalette()
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                var next = (Source)GUILayout.Toolbar((int)source, new[] { "Sprites", "Prefabs" });
                if (next != source) { source = next; selected = null; DestroyPreview(); }
                _search = EditorGUILayout.TextField(_search, EditorStyles.toolbarSearchField,
                                                   GUILayout.Width(140f));
            }

            var shown = Palette
                .Where(e => string.IsNullOrEmpty(_search) ||
                            e.Name.IndexOf(_search, System.StringComparison.OrdinalIgnoreCase) >= 0)
                .ToList();

            if (shown.Count == 0)
            {
                EditorGUILayout.HelpBox(
                    source == Source.Sprites
                        ? $"Nothing in Resources/{SpriteFolder}."
                        : $"No prefabs under {PrefabFolder}.", MessageType.Info);
                return;
            }

            _paletteScroll = EditorGUILayout.BeginScrollView(_paletteScroll);

            int columns = Mathf.Max(1, Mathf.FloorToInt((position.width - 24f) / (CellSize + 6f)));
            for (int i = 0; i < shown.Count; i += columns)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    for (int c = 0; c < columns && i + c < shown.Count; c++)
                        DrawCell(shown[i + c]);
                    GUILayout.FlexibleSpace();
                }
            }

            EditorGUILayout.EndScrollView();

            var current = Current();
            EditorGUILayout.LabelField(current != null ? $"Selected: {current.Name}" : "Nothing selected",
                                       EditorStyles.miniLabel);
        }

        private void DrawCell(Entry entry)
        {
            var thumb = entry.Sprite
                ? AssetPreview.GetAssetPreview(entry.Sprite)
                : AssetPreview.GetAssetPreview(entry.Prefab);

            bool isSelected = entry.Name == selected;
            var style = new GUIStyle(isSelected ? "flow node 0 on" : "flow node 0")
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = 9,
                wordWrap = true,
            };

            // Previews are generated asynchronously; until one is ready the name stands in for it.
            var content = thumb ? new GUIContent(thumb, entry.Name) : new GUIContent(entry.Name, entry.Name);

            if (!GUILayout.Button(content, style, GUILayout.Width(CellSize), GUILayout.Height(CellSize)))
            {
                if (!thumb) Repaint();
                return;
            }

            selected = entry.Name;
            armed = true;
            DestroyPreview();   // rebuilt from the new pick on the next scene pass
            Roll();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Scene view
        // ─────────────────────────────────────────────────────────────────────────

        private void OnSceneGui(SceneView view)
        {
            if (!armed || Application.isPlaying) return;

            var entry = Current();
            if (entry == null) return;

            var e = Event.current;

            // Keeps the scene view from picking objects out from under the cursor mid-placement.
            if (e.type == EventType.Layout)
                HandleUtility.AddDefaultControl(GUIUtility.GetControlID(FocusType.Passive));

            Vector3 world = SnapToGrid(MouseWorld(e.mousePosition));
            EnsurePreview(entry);
            PosePreview(world);
            DrawOverlay(world);
            view.Repaint();

            if (e.alt) return;   // alt-drag is the camera

            switch (e.type)
            {
                case EventType.MouseDown when e.button == 0:
                    Place(world);
                    e.Use();
                    break;

                case EventType.MouseDrag when e.button == 0 && scatterDrag:
                    if (!_hasLastPlaced || Vector3.Distance(_lastPlaced, world) >= scatterSpacing)
                        Place(world);
                    e.Use();
                    break;

                case EventType.MouseUp when e.button == 0:
                    _hasLastPlaced = false;
                    break;

                case EventType.ScrollWheel when e.shift:
                    angle -= e.delta.y * 5f;
                    Repaint();
                    e.Use();
                    break;

                case EventType.ScrollWheel when e.control:
                    scale = Mathf.Clamp(scale - e.delta.y * 0.05f, 0.05f, 20f);
                    Repaint();
                    e.Use();
                    break;

                case EventType.KeyDown when e.keyCode == KeyCode.Escape:
                    armed = false;
                    DestroyPreview();
                    Repaint();
                    e.Use();
                    break;
            }
        }

        private void DrawOverlay(Vector3 world)
        {
            Handles.color = new Color(0.5f, 1f, 0.6f, 0.9f);
            Handles.DrawWireDisc(world, Vector3.forward, 0.12f, 2f);

            if (gridSnap <= 0.0001f) return;

            Handles.color = new Color(0.4f, 0.7f, 1f, 0.5f);
            float h = gridSnap * 0.5f;
            Handles.DrawAAPolyLine(1.5f,
                world + new Vector3(-h, -h), world + new Vector3(h, -h),
                world + new Vector3(h, h), world + new Vector3(-h, h),
                world + new Vector3(-h, -h));
        }

        private static Vector3 MouseWorld(Vector2 guiPoint)
        {
            var ray = HandleUtility.GUIPointToWorldRay(guiPoint);

            // The play plane is z = 0.
            float t = Mathf.Abs(ray.direction.z) < 1e-6f ? 0f : -ray.origin.z / ray.direction.z;
            var p = ray.origin + ray.direction * t;
            p.z = 0f;
            return p;
        }

        private Vector3 SnapToGrid(Vector3 world)
        {
            if (gridSnap <= 0.0001f) return world;
            return new Vector3(Mathf.Round(world.x / gridSnap) * gridSnap,
                               Mathf.Round(world.y / gridSnap) * gridSnap, 0f);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Ghost
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Fresh randoms for the next object, so a scattered row is not a stamped one.</summary>
        private void Roll()
        {
            _rolledAngle = randomAngle > 0f ? Random.Range(-randomAngle, randomAngle) : 0f;
            _rolledScale = randomScale > 0f ? 1f + Random.Range(-randomScale, randomScale) : 1f;
        }

        private void EnsurePreview(Entry entry)
        {
            if (_preview) return;

            _preview = Build(entry);
            if (!_preview) return;

            // Whatever the object's own scale is — SpriteFactory's art scale, or the prefab's
            // authored one. The window's Scale multiplies it rather than replacing it.
            _previewBaseScale = _preview.transform.localScale;

            // Held out of the scene until it is placed: hidden in the hierarchy, never saved.
            foreach (var t in _preview.GetComponentsInChildren<Transform>(true))
                t.gameObject.hideFlags = HideFlags.HideAndDontSave;

            _previewColors.Clear();
            foreach (var sr in _preview.GetComponentsInChildren<SpriteRenderer>(true))
            {
                _previewColors.Add((sr, sr.color));
                var c = sr.color; c.a *= 0.55f; sr.color = c;
            }
        }

        private GameObject Build(Entry entry)
        {
            if (entry.Sprite)
                return SpriteFactory.Create(entry.Sprite, Vector3.zero, null, false,
                                            simplifyLevel, physMaterial);

            if (entry.Prefab)
                return (GameObject)PrefabUtility.InstantiatePrefab(entry.Prefab);

            return null;
        }

        private void PosePreview(Vector3 world)
        {
            if (!_preview) return;

            _preview.transform.position = world;
            _preview.transform.rotation = Quaternion.Euler(0f, 0f, angle + _rolledAngle);
            _preview.transform.localScale = _previewBaseScale * (scale * _rolledScale);
        }

        private void DestroyPreview()
        {
            if (_preview) DestroyImmediate(_preview);
            _preview = null;
            _previewColors.Clear();
            _previewBaseScale = Vector3.one;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Placing
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Hands the ghost over to the scene and rolls a new one for the next click.</summary>
        private void Place(Vector3 world)
        {
            var entry = Current();
            if (entry == null) return;

            EnsurePreview(entry);
            PosePreview(world);
            if (!_preview) return;

            var go = _preview;
            _preview = null;

            foreach (var (sr, color) in _previewColors)
                if (sr) sr.color = color;
            _previewColors.Clear();

            foreach (var t in go.GetComponentsInChildren<Transform>(true))
                t.gameObject.hideFlags = HideFlags.None;

            if (parent) go.transform.SetParent(parent, true);

            if (entry.Sprite) FinishSpriteObject(go, entry.Sprite);

            Undo.RegisterCreatedObjectUndo(go, $"Place {entry.Name}");
            EditorSceneManager.MarkSceneDirty(go.scene);
            if (selectPlaced) Selection.activeGameObject = go;

            _lastPlaced = world;
            _hasLastPlaced = true;
            Roll();
        }

        /// <summary>
        /// Mass comes off the collider's world area, so it has to be redone once the object is at
        /// its final scale — otherwise a beam scaled up in this window weighs what the unscaled one
        /// did. Static bodies are the level itself and never move.
        /// </summary>
        private void FinishSpriteObject(GameObject go, Sprite sprite)
        {
            var rb = go.GetComponent<Rigidbody2D>();
            var col = go.GetComponent<Collider2D>();
            if (rb && col) MassRecalculator.SetMass(sprite, rb, col);
            if (rb && makeStatic) rb.bodyType = RigidbodyType2D.Static;
        }
    }
}
