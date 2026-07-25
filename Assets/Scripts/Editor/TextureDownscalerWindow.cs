using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Bulk-downscales selected PNG textures in place.
    ///
    /// Written for the "shrink the art, drop the PPU by the same factor" workflow: a
    /// 500x500 sprite at 100 PPU and a 100x100 sprite at 20 PPU occupy exactly the same
    /// world space, so masses, colliders and brush radii all keep working while the
    /// per-pixel systems (erasing, fire, split detection, collider retracing) get 25x
    /// less to chew on.
    ///
    /// Resampling is an area average weighted by alpha, so the RGB of fully transparent
    /// pixels — normally black — cannot bleed dark halos into the sprite's edges. Those
    /// edges are exactly what the collider tracer and the fire read, so a plain bicubic
    /// resize is not good enough here.
    /// </summary>
    public class TextureDownscalerWindow : EditorWindow
    {
        private const string BackupFolderName = "TextureBackups";

        [SerializeField] private int factor = 5;
        [SerializeField] private bool scalePixelsPerUnit = true;
        [SerializeField] private bool setPointFilter;
        [SerializeField] private bool backupOriginals = true;

        private readonly List<Entry> _entries = new();
        private int _skipped;
        private Vector2 _scroll;

        private struct Entry
        {
            public string AssetPath;
            public int Width;
            public int Height;
            public int Ppu;
            public bool MultipleSpriteMode;
        }

        [MenuItem("PhysFun/Downscale Textures...")]
        public static void Open()
        {
            var w = GetWindow<TextureDownscalerWindow>(true, "Downscale Textures");
            w.minSize = new Vector2(420f, 320f);
            w.Rescan();
        }

        private void OnEnable() => Rescan();

        private void OnSelectionChange()
        {
            Rescan();
            Repaint();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // UI
        // ─────────────────────────────────────────────────────────────────────────

        private void OnGUI()
        {
            EditorGUILayout.HelpBox(
                "Select textures (or folders of them) in the Project window. " +
                "Files are rewritten in place — this cannot be undone from the editor.",
                MessageType.None);

            EditorGUI.BeginChangeCheck();
            factor = EditorGUILayout.IntSlider("Shrink by", factor, 2, 16);
            if (EditorGUI.EndChangeCheck()) Repaint();

            scalePixelsPerUnit = EditorGUILayout.Toggle(
                new GUIContent("Divide PPU too", "Keeps every sprite the same size in world units."),
                scalePixelsPerUnit);

            setPointFilter = EditorGUILayout.Toggle(
                new GUIContent("Point filtering", "Crisp pixels instead of the default bilinear blur."),
                setPointFilter);

            backupOriginals = EditorGUILayout.Toggle(
                new GUIContent("Back up originals", "Copies the untouched files to <project>/" + BackupFolderName + "/, outside Assets."),
                backupOriginals);

            EditorGUILayout.Space();

            if (_entries.Count == 0)
            {
                EditorGUILayout.LabelField(_skipped > 0
                    ? $"No PNG textures selected ({_skipped} non-PNG skipped)."
                    : "No textures selected.");
                return;
            }

            EditorGUILayout.LabelField($"{_entries.Count} texture(s)" + (_skipped > 0 ? $"  ({_skipped} non-PNG skipped)" : ""),
                                       EditorStyles.boldLabel);

            _scroll = EditorGUILayout.BeginScrollView(_scroll);
            bool anyMultiple = false;
            foreach (var e in _entries)
            {
                Target(e, out int dw, out int dh);
                string ppu = scalePixelsPerUnit && e.Ppu > 0
                    ? $"   {e.Ppu} -> {Mathf.Max(1, Mathf.RoundToInt(e.Ppu / (float)factor))} PPU"
                    : "";
                EditorGUILayout.LabelField(
                    $"{Path.GetFileName(e.AssetPath)}",
                    $"{e.Width}x{e.Height}  ->  {dw}x{dh}{ppu}");
                anyMultiple |= e.MultipleSpriteMode;
            }
            EditorGUILayout.EndScrollView();

            if (anyMultiple)
            {
                EditorGUILayout.HelpBox(
                    "Some of these use Multiple sprite mode. Their slice rects are in pixels and " +
                    "will no longer line up — reslice them afterwards.",
                    MessageType.Warning);
            }

            EditorGUILayout.Space();
            if (GUILayout.Button($"Downscale {_entries.Count} texture(s)", GUILayout.Height(28f)))
                Confirm();
        }

        private void Confirm()
        {
            string warning = backupOriginals
                ? $"Originals are copied to <project>/{BackupFolderName}/ first."
                : "Originals will NOT be backed up.";

            if (!EditorUtility.DisplayDialog(
                    "Downscale textures",
                    $"Rewrite {_entries.Count} PNG file(s) at 1/{factor} size?\n\n{warning}",
                    "Downscale", "Cancel"))
                return;

            Execute();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Work
        // ─────────────────────────────────────────────────────────────────────────

        private void Rescan()
        {
            _entries.Clear();
            _skipped = 0;

            var textures = Selection.GetFiltered<Texture2D>(SelectionMode.DeepAssets);
            foreach (var tex in textures)
            {
                string path = AssetDatabase.GetAssetPath(tex);
                if (string.IsNullOrEmpty(path)) continue;
                if (!path.EndsWith(".png", StringComparison.OrdinalIgnoreCase)) { _skipped++; continue; }

                // Read the size out of the PNG header rather than trusting the imported
                // texture — maxTextureSize may already have shrunk what Unity holds.
                if (!TryReadPngSize(Path.GetFullPath(path), out int w, out int h)) { _skipped++; continue; }

                var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                _entries.Add(new Entry
                {
                    AssetPath = path,
                    Width = w,
                    Height = h,
                    Ppu = importer != null ? Mathf.RoundToInt(importer.spritePixelsToUnits) : 0,
                    MultipleSpriteMode = importer != null && importer.spriteImportMode == SpriteImportMode.Multiple,
                });
            }

            _entries.Sort((a, b) => string.CompareOrdinal(a.AssetPath, b.AssetPath));
        }

        private void Execute()
        {
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string backupDir = Path.Combine(projectRoot, BackupFolderName,
                                            DateTime.Now.ToString("yyyyMMdd_HHmmss"));
            int done = 0;

            try
            {
                for (int i = 0; i < _entries.Count; i++)
                {
                    var e = _entries[i];
                    EditorUtility.DisplayProgressBar("Downscaling textures", e.AssetPath,
                                                     i / (float)_entries.Count);
                    if (Process(e, backupDir)) done++;
                }
            }
            finally
            {
                EditorUtility.ClearProgressBar();
                AssetDatabase.Refresh();
            }

            Debug.Log($"Downscaled {done}/{_entries.Count} texture(s) by 1/{factor}." +
                      (backupOriginals && done > 0 ? $" Originals: {backupDir}" : ""));
            Rescan();
        }

        private bool Process(Entry entry, string backupDir)
        {
            string abs = Path.GetFullPath(entry.AssetPath);

            Texture2D src = null;
            Texture2D dst = null;
            try
            {
                byte[] bytes = File.ReadAllBytes(abs);

                // Decode the file directly: import settings (compression, maxTextureSize,
                // sprite slicing) must not influence what we resample.
                src = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!src.LoadImage(bytes))
                {
                    Debug.LogError($"Downscale: could not decode {entry.AssetPath}");
                    return false;
                }

                // Derive the target from what actually decoded, not from the header read
                // at scan time, in case the file changed underneath us.
                int sw = src.width, sh = src.height;
                int dw = Mathf.Max(1, Mathf.RoundToInt(sw / (float)factor));
                int dh = Mathf.Max(1, Mathf.RoundToInt(sh / (float)factor));
                if (dw >= sw && dh >= sh)
                {
                    Debug.LogWarning($"Downscale: {entry.AssetPath} is already too small to shrink further.");
                    return false;
                }

                var pixels = BoxDownscale(src.GetPixels32(), sw, sh, dw, dh);

                if (backupOriginals)
                {
                    string dest = Path.Combine(backupDir, entry.AssetPath.Replace('/', Path.DirectorySeparatorChar));
                    Directory.CreateDirectory(Path.GetDirectoryName(dest));
                    File.WriteAllBytes(dest, bytes);
                }

                dst = new Texture2D(dw, dh, TextureFormat.RGBA32, false);
                dst.SetPixels32(pixels);
                dst.Apply(false, false);
                File.WriteAllBytes(abs, dst.EncodeToPNG());
            }
            catch (Exception ex)
            {
                Debug.LogError($"Downscale failed for {entry.AssetPath}: {ex.Message}");
                return false;
            }
            finally
            {
                if (src) DestroyImmediate(src);
                if (dst) DestroyImmediate(dst);
            }

            var importer = AssetImporter.GetAtPath(entry.AssetPath) as TextureImporter;
            if (importer != null)
            {
                if (scalePixelsPerUnit)
                    importer.spritePixelsToUnits =
                        Mathf.Max(1f, Mathf.Round(importer.spritePixelsToUnits / factor));

                if (setPointFilter) importer.filterMode = FilterMode.Point;

                importer.SaveAndReimport();
            }

            return true;
        }

        private void Target(Entry e, out int dw, out int dh)
        {
            dw = Mathf.Max(1, Mathf.RoundToInt(e.Width / (float)factor));
            dh = Mathf.Max(1, Mathf.RoundToInt(e.Height / (float)factor));
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Resampling
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Area-average downscale. Colour is weighted by alpha, so transparent pixels
        /// contribute their coverage but not their (usually black) colour — that's what
        /// keeps dark fringes from appearing around the edges of cut-out sprites.
        /// </summary>
        public static Color32[] BoxDownscale(Color32[] src, int sw, int sh, int dw, int dh)
        {
            var dst = new Color32[dw * dh];

            for (int dy = 0; dy < dh; dy++)
            {
                int y0 = (int)((long)dy * sh / dh);
                int y1 = (int)((long)(dy + 1) * sh / dh);
                if (y1 <= y0) y1 = y0 + 1;
                if (y1 > sh) y1 = sh;

                for (int dx = 0; dx < dw; dx++)
                {
                    int x0 = (int)((long)dx * sw / dw);
                    int x1 = (int)((long)(dx + 1) * sw / dw);
                    if (x1 <= x0) x1 = x0 + 1;
                    if (x1 > sw) x1 = sw;

                    long sumA = 0;
                    double sumR = 0, sumG = 0, sumB = 0;
                    int n = 0;

                    for (int y = y0; y < y1; y++)
                    {
                        int row = y * sw;
                        for (int x = x0; x < x1; x++)
                        {
                            var p = src[row + x];
                            int a = p.a;
                            sumA += a;
                            n++;
                            sumR += p.r * a;
                            sumG += p.g * a;
                            sumB += p.b * a;
                        }
                    }

                    var outPx = new Color32(0, 0, 0, (byte)Mathf.Clamp(Mathf.RoundToInt(sumA / (float)n), 0, 255));
                    if (sumA > 0)
                    {
                        outPx.r = (byte)Mathf.Clamp(Mathf.RoundToInt((float)(sumR / sumA)), 0, 255);
                        outPx.g = (byte)Mathf.Clamp(Mathf.RoundToInt((float)(sumG / sumA)), 0, 255);
                        outPx.b = (byte)Mathf.Clamp(Mathf.RoundToInt((float)(sumB / sumA)), 0, 255);
                    }
                    dst[dy * dw + dx] = outPx;
                }
            }

            return dst;
        }

        private static bool TryReadPngSize(string absPath, out int width, out int height)
        {
            width = height = 0;
            try
            {
                using (var fs = File.OpenRead(absPath))
                {
                    var head = new byte[24];
                    if (fs.Read(head, 0, 24) < 24) return false;
                    if (head[0] != 0x89 || head[1] != 'P' || head[2] != 'N' || head[3] != 'G') return false;

                    // IHDR width/height are big-endian at offsets 16 and 20.
                    width  = (head[16] << 24) | (head[17] << 16) | (head[18] << 8) | head[19];
                    height = (head[20] << 24) | (head[21] << 16) | (head[22] << 8) | head[23];
                    return width > 0 && height > 0;
                }
            }
            catch
            {
                return false;
            }
        }
    }
}
