using System.Collections.Generic;
using System.IO;
using Materials;
using Phys.Terrain;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Paints terrain straight into the scene view in edit mode: pick the tile art, pick the
    /// physics material, drag.
    ///
    /// Strokes write palette indices into the <see cref="TerrainMap"/> asset — that's the saved
    /// data. The chunk bodies you see are a regenerated view, patched per chunk as the brush
    /// moves and re-traced into colliders when the mouse comes up, which is what keeps a drag
    /// interactive over a map that is a few hundred thousand cells.
    /// </summary>
    public sealed class TerrainPainterWindow : EditorWindow
    {
        private const string TileFolder = "Assets/Resources/Sprites/Materials";
        private const float TileButtonSize = 52f;

        [MenuItem("Tools/PhysFun/Terrain Painter")]
        private static void Open() => GetWindow<TerrainPainterWindow>("Terrain Painter");

        [SerializeField] private TerrainBuilder builder;
        [SerializeField] private string tile = "rock";
        [SerializeField] private PhysMaterialId physMaterial = PhysMaterialId.Default;
        [SerializeField] private float brushRadius = 0.5f;
        [SerializeField] private bool squareBrush;
        [SerializeField] private bool armed;

        private readonly List<Texture2D> _tiles = new();
        private string _search = "";
        private Vector2 _paletteScroll;

        // Region editor, mirrored from the map until the user hits Apply.
        private bool _regionExpanded;
        private int _regionMapId;
        private Vector2 _regionMin;
        private Vector2 _regionSize;
        private float _regionResolution = 40f;

        /// <summary>Set once this window has changed a map, which is when undo needs to rebuild.</summary>
        private bool _editedMap;

        // Stroke state
        private bool _stroke;
        private bool _erasing;
        private RectInt _strokeRect;
        private bool _hasStrokeRect;
        private Vector3 _lastPaintPos;
        private bool _hasLastPaintPos;

        private void OnEnable()
        {
            LoadTiles();
            if (!builder) builder = FindAnyObjectByType<TerrainBuilder>();
            Tools.hidden = armed;
            SceneView.duringSceneGui += OnSceneGui;
            Undo.undoRedoPerformed += OnUndoRedo;
        }

        private void OnDisable()
        {
            SceneView.duringSceneGui -= OnSceneGui;
            Undo.undoRedoPerformed -= OnUndoRedo;
            Tools.hidden = false;
        }

        private void OnUndoRedo()
        {
            // Undo swaps the map's cell buffer out from under the chunks, so the view has to be
            // regenerated — but only once this window has actually changed a map. Otherwise every
            // unrelated undo in the editor would pay for a full terrain rebuild.
            if (!_editedMap || !builder) return;
            builder.Build();
            SceneView.RepaintAll();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Window
        // ─────────────────────────────────────────────────────────────────────────

        private void OnGUI()
        {
            builder = (TerrainBuilder)EditorGUILayout.ObjectField(
                "Builder", builder, typeof(TerrainBuilder), true);

            if (!builder)
            {
                EditorGUILayout.HelpBox("No TerrainBuilder in the scene. Add one to a GameObject " +
                                        "(the DestructibleTerrain object has it).", MessageType.Info);
                return;
            }

            if (Application.isPlaying)
            {
                EditorGUILayout.HelpBox("Painting is edit-mode only — a rebuild would throw away " +
                                        "everything the simulation has done to the terrain.",
                                        MessageType.Warning);
                return;
            }

            DrawMapSection();
            if (!builder.Map) return;

            EditorGUILayout.Space();
            DrawRegionSection();
            EditorGUILayout.Space();
            DrawBrushSection();
            EditorGUILayout.Space();
            DrawPalette();
        }

        /// <summary>
        /// The paintable region. Strokes clip to it, so this is where you go when the brush stops
        /// short of where the terrain needs to be. Resizing keeps whatever art still lands inside.
        /// </summary>
        private void DrawRegionSection()
        {
            var map = builder.Map;
            if (_regionMapId != map.GetInstanceID())
            {
                var bounds = map.LocalBounds;
                _regionMin = bounds.min;
                _regionSize = bounds.size;
                _regionResolution = map.PixelsPerUnit;
                _regionMapId = map.GetInstanceID();
            }

            _regionExpanded = EditorGUILayout.Foldout(_regionExpanded, "Region", true);
            if (!_regionExpanded) return;

            using (new EditorGUI.IndentLevelScope())
            {
                _regionMin = EditorGUILayout.Vector2Field("Min (local units)", _regionMin);
                _regionSize = EditorGUILayout.Vector2Field("Size (units)", _regionSize);
                _regionResolution = EditorGUILayout.Slider("Cells per unit", _regionResolution, 8f, 80f);

                int cellsWide = Mathf.CeilToInt(Mathf.Max(0.1f, _regionSize.x) * _regionResolution);
                int cellsHigh = Mathf.CeilToInt(Mathf.Max(0.1f, _regionSize.y) * _regionResolution);
                EditorGUILayout.LabelField($"→ {cellsWide} x {cellsHigh} cells",
                                           EditorStyles.miniLabel);

                using (new EditorGUI.DisabledScope(
                    cellsWide == map.Width && cellsHigh == map.Height &&
                    _regionMin == map.LocalBounds.min &&
                    Mathf.Approximately(_regionResolution, map.PixelsPerUnit)))
                {
                    if (GUILayout.Button("Apply region"))
                    {
                        Undo.RecordObject(map, "Resize Terrain Map");
                        map.Resize(_regionMin, cellsWide, cellsHigh, _regionResolution);
                        builder.Build();
                        Finish(map);
                    }
                }
            }
        }

        private void DrawMapSection()
        {
            var map = builder.Map;

            using (new EditorGUILayout.HorizontalScope())
            {
                var next = (TerrainMap)EditorGUILayout.ObjectField(
                    "Map", map, typeof(TerrainMap), false);
                if (next != map)
                {
                    Undo.RecordObject(builder, "Assign Terrain Map");
                    builder.SetMap(next);
                    EditorUtility.SetDirty(builder);
                    builder.Build();
                    map = next;
                }

                if (GUILayout.Button("New…", GUILayout.Width(52f))) CreateMap();
            }

            if (!map)
            {
                EditorGUILayout.HelpBox("Assign or create a Terrain Map to paint into. Without " +
                                        "one the builder falls back to its procedural features.",
                                        MessageType.Info);
                return;
            }

            EditorGUILayout.LabelField(
                $"{map.Width} x {map.Height} cells @ {map.PixelsPerUnit:0.#}/unit  •  " +
                $"{map.Palette.Count} palette entries", EditorStyles.miniLabel);

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Rebuild")) builder.Build();

                if (GUILayout.Button("Bake features"))
                {
                    Undo.RecordObject(map, "Bake Terrain Features");
                    builder.BakeFeaturesIntoMap();
                    builder.Build();
                    Finish(map);
                }

                if (GUILayout.Button("Clear") &&
                    EditorUtility.DisplayDialog("Clear terrain map",
                        "Erase every painted cell? This can be undone.", "Clear", "Cancel"))
                {
                    Undo.RecordObject(map, "Clear Terrain Map");
                    map.Clear();
                    builder.Build();
                    Finish(map);
                }
            }
        }

        private void DrawBrushSection()
        {
            EditorGUILayout.LabelField("Brush", EditorStyles.boldLabel);
            brushRadius = EditorGUILayout.Slider("Radius (units)", brushRadius, 0.05f, 6f);
            squareBrush = EditorGUILayout.Toggle("Square", squareBrush);
            physMaterial = (PhysMaterialId)EditorGUILayout.EnumPopup("Phys material", physMaterial);

            var mat = MaterialLibrary.Get(physMaterial);
            EditorGUILayout.LabelField(
                mat.Flammable ? $"density {mat.Density:0.##} • burns" : $"density {mat.Density:0.##}",
                EditorStyles.miniLabel);

            EditorGUILayout.Space(2f);
            var bg = GUI.backgroundColor;
            GUI.backgroundColor = armed ? new Color(0.55f, 0.85f, 0.55f) : bg;
            if (GUILayout.Button(armed ? "Painting — click to stop" : "Start painting",
                                 GUILayout.Height(28f)))
            {
                armed = !armed;
                Tools.hidden = armed;
                SceneView.RepaintAll();
            }
            GUI.backgroundColor = bg;

            EditorGUILayout.LabelField("Drag to paint, right-drag (or Ctrl) to erase, " +
                                       "Shift+wheel resizes the brush.", EditorStyles.miniLabel);
        }

        private void DrawPalette()
        {
            EditorGUILayout.LabelField($"Tile — {tile}", EditorStyles.boldLabel);
            using (new EditorGUILayout.HorizontalScope())
            {
                _search = EditorGUILayout.TextField("Filter", _search);
                if (GUILayout.Button("↻", GUILayout.Width(24f))) LoadTiles();
            }

            float width = Mathf.Max(TileButtonSize, EditorGUIUtility.currentViewWidth - 24f);
            int columns = Mathf.Max(1, Mathf.FloorToInt(width / TileButtonSize));

            _paletteScroll = EditorGUILayout.BeginScrollView(_paletteScroll);
            int column = 0;
            EditorGUILayout.BeginHorizontal();
            foreach (var texture in _tiles)
            {
                if (!texture) continue;
                if (!string.IsNullOrEmpty(_search) &&
                    texture.name.IndexOf(_search, System.StringComparison.OrdinalIgnoreCase) < 0)
                    continue;

                if (column >= columns)
                {
                    EditorGUILayout.EndHorizontal();
                    EditorGUILayout.BeginHorizontal();
                    column = 0;
                }

                bool selected = texture.name == tile;
                var previous = GUI.backgroundColor;
                if (selected) GUI.backgroundColor = new Color(0.4f, 0.7f, 1f);

                if (GUILayout.Button(new GUIContent(texture, texture.name),
                                     GUILayout.Width(TileButtonSize), GUILayout.Height(TileButtonSize)))
                    tile = texture.name;

                GUI.backgroundColor = previous;
                column++;
            }
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.EndScrollView();
        }

        private void LoadTiles()
        {
            _tiles.Clear();
            if (!Directory.Exists(TileFolder))
            {
                Debug.LogWarning($"TerrainPainter: {TileFolder} not found.");
                return;
            }

            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { TileFolder }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                if (texture) _tiles.Add(texture);
            }
            _tiles.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
        }

        private void CreateMap()
        {
            string path = EditorUtility.SaveFilePanelInProject(
                "New Terrain Map", "TerrainMap", "asset",
                "Where should the painted terrain be stored?");
            if (string.IsNullOrEmpty(path)) return;

            var map = CreateInstance<TerrainMap>();
            AssetDatabase.CreateAsset(map, path);
            AssetDatabase.SaveAssets();

            Undo.RecordObject(builder, "Assign Terrain Map");
            builder.SetMap(map);
            builder.Build();
            EditorUtility.SetDirty(builder);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Scene view
        // ─────────────────────────────────────────────────────────────────────────

        private void OnSceneGui(SceneView view)
        {
            if (!armed || Application.isPlaying || !builder || !builder.Map) return;

            var e = Event.current;

            // Stops the scene view from picking objects out from under the brush.
            if (e.type == EventType.Layout)
                HandleUtility.AddDefaultControl(GUIUtility.GetControlID(FocusType.Passive));

            Vector3 world = MouseWorld(e.mousePosition);
            DrawOverlay(world);
            view.Repaint();

            if (e.alt) return;   // alt-drag is the camera

            switch (e.type)
            {
                case EventType.MouseDown when e.button == 0 || e.button == 1:
                    BeginStroke(e.button == 1 || e.control);
                    PaintTo(world);
                    e.Use();
                    break;

                case EventType.MouseDrag when _stroke:
                    PaintTo(world);
                    e.Use();
                    break;

                case EventType.MouseUp when _stroke:
                    EndStroke();
                    e.Use();
                    break;

                case EventType.ScrollWheel when e.shift:
                    brushRadius = Mathf.Clamp(brushRadius - e.delta.y * 0.05f, 0.05f, 6f);
                    Repaint();
                    e.Use();
                    break;
            }
        }

        private void DrawOverlay(Vector3 world)
        {
            var map = builder.Map;

            // Paintable region.
            var bounds = map.LocalBounds;
            var t = builder.transform;
            Handles.color = new Color(0.4f, 0.7f, 1f, 0.5f);
            Handles.DrawSolidRectangleWithOutline(new[]
            {
                t.TransformPoint(new Vector3(bounds.xMin, bounds.yMin)),
                t.TransformPoint(new Vector3(bounds.xMax, bounds.yMin)),
                t.TransformPoint(new Vector3(bounds.xMax, bounds.yMax)),
                t.TransformPoint(new Vector3(bounds.xMin, bounds.yMax)),
            }, Color.clear, new Color(0.4f, 0.7f, 1f, 0.35f));

            Handles.color = _erasing && _stroke
                ? new Color(1f, 0.45f, 0.4f, 0.9f)
                : new Color(0.5f, 1f, 0.6f, 0.9f);

            if (squareBrush)
            {
                float r = brushRadius;
                Handles.DrawAAPolyLine(2f,
                    world + new Vector3(-r, -r), world + new Vector3(r, -r),
                    world + new Vector3(r, r), world + new Vector3(-r, r),
                    world + new Vector3(-r, -r));
            }
            else
            {
                Handles.DrawWireDisc(world, Vector3.forward, brushRadius, 2f);
            }
        }

        private static Vector3 MouseWorld(Vector2 guiPoint)
        {
            var ray = HandleUtility.GUIPointToWorldRay(guiPoint);

            // Terrain lives on the z = 0 plane.
            float t = Mathf.Abs(ray.direction.z) < 1e-6f ? 0f : -ray.origin.z / ray.direction.z;
            var p = ray.origin + ray.direction * t;
            p.z = 0f;
            return p;
        }

        private void BeginStroke(bool erase)
        {
            _stroke = true;
            _erasing = erase;
            _hasStrokeRect = false;
            _hasLastPaintPos = false;
            Undo.RecordObject(builder.Map, erase ? "Erase Terrain" : "Paint Terrain");
        }

        private void EndStroke()
        {
            _stroke = false;
            _hasLastPaintPos = false;

            if (_hasStrokeRect)
            {
                // Colliders are the expensive half, so the whole stroke pays for them once.
                builder.RefreshArea(_strokeRect, rebuildColliders: true);
                Finish(builder.Map);
            }
            _hasStrokeRect = false;
        }

        /// <summary>Paint from the last brush position to this one, so a fast drag leaves a
        /// continuous line instead of a dotted one.</summary>
        private void PaintTo(Vector3 world)
        {
            if (!_hasLastPaintPos)
            {
                Stamp(world);
            }
            else
            {
                float step = Mathf.Max(0.02f, brushRadius * 0.5f);
                float distance = Vector3.Distance(_lastPaintPos, world);
                int steps = Mathf.Min(256, Mathf.CeilToInt(distance / step));
                for (int i = 1; i <= steps; i++)
                    Stamp(Vector3.Lerp(_lastPaintPos, world, i / (float)steps));
            }

            _lastPaintPos = world;
            _hasLastPaintPos = true;
        }

        private void Stamp(Vector3 world)
        {
            var map = builder.Map;

            // Coordinates come back even when the point is outside the map, so a brush hanging
            // over the edge still paints the part that is inside.
            builder.WorldToCell(world, out int cx, out int cy);

            int radius = Mathf.Max(1, Mathf.RoundToInt(brushRadius * builder.CellsPerWorldUnit));
            int x0 = Mathf.Max(0, cx - radius);
            int x1 = Mathf.Min(map.Width - 1, cx + radius);
            int y0 = Mathf.Max(0, cy - radius);
            int y1 = Mathf.Min(map.Height - 1, cy + radius);
            if (x1 < x0 || y1 < y0) return;

            byte id = _erasing ? (byte)0 : (byte)map.Require(tile, physMaterial);
            var cells = map.Cells;
            int r2 = radius * radius;
            bool changed = false;

            for (int y = y0; y <= y1; y++)
            {
                int dy = y - cy;
                int row = y * map.Width;
                for (int x = x0; x <= x1; x++)
                {
                    int dx = x - cx;
                    if (!squareBrush && dx * dx + dy * dy > r2) continue;
                    if (cells[row + x] == id) continue;
                    cells[row + x] = id;
                    changed = true;
                }
            }
            if (!changed) return;

            var touched = new RectInt(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
            _strokeRect = _hasStrokeRect ? Union(_strokeRect, touched) : touched;
            _hasStrokeRect = true;

            // Texture-only refresh while dragging; colliders wait for the mouse to come up.
            builder.RefreshArea(touched, rebuildColliders: false);
        }

        private static RectInt Union(RectInt a, RectInt b)
        {
            int xMin = Mathf.Min(a.xMin, b.xMin);
            int yMin = Mathf.Min(a.yMin, b.yMin);
            int xMax = Mathf.Max(a.xMax, b.xMax);
            int yMax = Mathf.Max(a.yMax, b.yMax);
            return new RectInt(xMin, yMin, xMax - xMin, yMax - yMin);
        }

        private void Finish(TerrainMap map)
        {
            _editedMap = true;
            EditorUtility.SetDirty(map);
            AssetDatabase.SaveAssetIfDirty(map);
            Repaint();
            SceneView.RepaintAll();
        }
    }
}
