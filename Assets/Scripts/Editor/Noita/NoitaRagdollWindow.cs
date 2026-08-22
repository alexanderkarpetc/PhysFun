using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace NoitaImport
{
    /// <summary>
    /// PhysFun ▸ Noita Ragdolls — picks creatures out of an unpacked Noita `data` folder and
    /// bakes each one into a part sheet, a ragdoll definition and a corpse prefab.
    /// </summary>
    public sealed class NoitaRagdollWindow : EditorWindow
    {
        private const string DataRootKey = "PhysFun.Noita.DataRoot";
        private const string OutputKey = "PhysFun.Noita.Output";
        private const string PpuKey = "PhysFun.Noita.Ppu";

        private readonly NoitaRagdollImporter.Settings _settings = new();
        private readonly HashSet<string> _selected = new();
        private List<string> _creatures = new();
        private string _filter = "";
        private Vector2 _listScroll, _logScroll;
        private string _log = "";

        [MenuItem("PhysFun/Noita Ragdolls")]
        public static void Open()
        {
            var window = GetWindow<NoitaRagdollWindow>("Noita Ragdolls");
            window.minSize = new Vector2(420f, 480f);
        }

        private void OnEnable()
        {
            _settings.DataRoot = EditorPrefs.GetString(DataRootKey, _settings.DataRoot);
            _settings.OutputRoot = EditorPrefs.GetString(OutputKey, _settings.OutputRoot);
            _settings.PixelsPerUnit = EditorPrefs.GetFloat(PpuKey, _settings.PixelsPerUnit);
            Rescan();
        }

        private void OnGUI()
        {
            DrawPaths();
            DrawOptions();
            EditorGUILayout.Space();
            DrawList();
            EditorGUILayout.Space();
            DrawActions();
            DrawLog();
        }

        private void DrawPaths()
        {
            EditorGUILayout.LabelField("Source", EditorStyles.boldLabel);

            using (new EditorGUILayout.HorizontalScope())
            {
                EditorGUI.BeginChangeCheck();
                string root = EditorGUILayout.TextField("Noita data folder", _settings.DataRoot);
                if (EditorGUI.EndChangeCheck())
                {
                    _settings.DataRoot = root;
                    EditorPrefs.SetString(DataRootKey, root);
                    Rescan();
                }

                if (GUILayout.Button("…", GUILayout.Width(28f)))
                {
                    string picked = EditorUtility.OpenFolderPanel("Unpacked Noita data folder", _settings.DataRoot, "");
                    if (!string.IsNullOrEmpty(picked))
                    {
                        _settings.DataRoot = picked;
                        EditorPrefs.SetString(DataRootKey, picked);
                        Rescan();
                        GUIUtility.ExitGUI();
                    }
                }
            }

            if (!Directory.Exists(Path.Combine(_settings.DataRoot ?? "", "ragdolls")))
                EditorGUILayout.HelpBox("No 'ragdolls' folder here — point this at the unpacked data folder.", MessageType.Warning);

            EditorGUI.BeginChangeCheck();
            _settings.OutputRoot = EditorGUILayout.TextField("Output folder", _settings.OutputRoot);
            if (EditorGUI.EndChangeCheck()) EditorPrefs.SetString(OutputKey, _settings.OutputRoot);
        }

        private void DrawOptions()
        {
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Build", EditorStyles.boldLabel);

            EditorGUI.BeginChangeCheck();
            _settings.PixelsPerUnit = EditorGUILayout.FloatField(
                new GUIContent("Pixels per unit", "Match the enemy sprite sheets — PhysFun slices those at 20."),
                _settings.PixelsPerUnit);
            if (EditorGUI.EndChangeCheck()) EditorPrefs.SetFloat(PpuKey, _settings.PixelsPerUnit);

            _settings.UseLimits = EditorGUILayout.Toggle(
                new GUIContent("Limit joints", "Off gives a fully floppy corpse that folds through itself."),
                _settings.UseLimits);

            using (new EditorGUI.DisabledScope(!_settings.UseLimits))
                _settings.LimitAngle = EditorGUILayout.Slider("Limit angle", _settings.LimitAngle, 5f, 175f);

            _settings.BuildPrefab = EditorGUILayout.Toggle("Build prefab", _settings.BuildPrefab);
        }

        private void DrawList()
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                EditorGUILayout.LabelField($"Creatures ({_creatures.Count})", EditorStyles.boldLabel, GUILayout.Width(140f));
                _filter = EditorGUILayout.TextField(_filter);
                if (GUILayout.Button("All", GUILayout.Width(40f)))
                    foreach (var c in Visible()) _selected.Add(c);
                if (GUILayout.Button("None", GUILayout.Width(50f)))
                    _selected.Clear();
                if (GUILayout.Button("Rescan", GUILayout.Width(60f)))
                    Rescan();
            }

            _listScroll = EditorGUILayout.BeginScrollView(_listScroll, GUILayout.MinHeight(160f));
            foreach (var creature in Visible())
            {
                bool on = _selected.Contains(creature);
                bool next = EditorGUILayout.ToggleLeft(creature, on);
                if (next == on) continue;
                if (next) _selected.Add(creature);
                else _selected.Remove(creature);
            }
            EditorGUILayout.EndScrollView();
        }

        private void DrawActions()
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                using (new EditorGUI.DisabledScope(_selected.Count == 0))
                    if (GUILayout.Button($"Import selected ({_selected.Count})", GUILayout.Height(26f)))
                        Run(new List<string>(_selected));

                if (GUILayout.Button("Import all", GUILayout.Height(26f)))
                    Run(new List<string>(_creatures));
            }
        }

        private void DrawLog()
        {
            if (string.IsNullOrEmpty(_log)) return;
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Last run", EditorStyles.boldLabel);
            _logScroll = EditorGUILayout.BeginScrollView(_logScroll, GUILayout.MinHeight(120f));
            EditorGUILayout.TextArea(_log, GUILayout.ExpandHeight(true));
            EditorGUILayout.EndScrollView();
        }

        private IEnumerable<string> Visible()
        {
            foreach (var c in _creatures)
                if (string.IsNullOrEmpty(_filter) || c.IndexOf(_filter, System.StringComparison.OrdinalIgnoreCase) >= 0)
                    yield return c;
        }

        private void Rescan()
        {
            _creatures = NoitaPaths.Creatures(_settings.DataRoot ?? "");
            _selected.RemoveWhere(c => !_creatures.Contains(c));
            Repaint();
        }

        private void Run(List<string> creatures)
        {
            var log = new StringBuilder();
            int ok = 0;

            try
            {
                // No StartAssetEditing here: each creature writes a png and immediately reads
                // the sprites back out of it, which only works with the database awake.
                for (int i = 0; i < creatures.Count; i++)
                {
                    string creature = creatures[i];
                    if (EditorUtility.DisplayCancelableProgressBar("Noita ragdolls", creature,
                            (i + 1f) / creatures.Count))
                        break;

                    try
                    {
                        if (NoitaRagdollImporter.Import(creature, _settings, out string report)) ok++;
                        log.AppendLine(report);
                    }
                    catch (System.Exception e)
                    {
                        log.AppendLine($"{creature}: failed — {e.Message}");
                        Debug.LogException(e);
                    }
                }
            }
            finally
            {
                EditorUtility.ClearProgressBar();
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
            }

            _log = $"{ok}/{creatures.Count} imported\n\n{log}";
            Debug.Log($"Noita ragdolls: {ok}/{creatures.Count} imported");
            Repaint();
        }
    }
}
