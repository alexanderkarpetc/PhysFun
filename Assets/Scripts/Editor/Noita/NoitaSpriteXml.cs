using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEngine;

namespace NoitaImport
{
    /// <summary>One RectAnimation row of a Noita sprite sheet.</summary>
    public sealed class NoitaAnim
    {
        public string Name;
        public int PosX, PosY;
        public int FrameW, FrameH;
        public int Count;
        public int PerRow;
        public float FrameWait;
        public bool Loop;

        /// <summary>
        /// Noita pads every cell by a pixel and draws one less; the ragdoll part images and
        /// the uv markers use that shrunk area, so the rect has to match it.
        /// </summary>
        public bool Shrink;

        public int DrawW => Shrink ? Mathf.Max(1, FrameW - 1) : FrameW;
        public int DrawH => Shrink ? Mathf.Max(1, FrameH - 1) : FrameH;

        public RectInt FrameRect(int index)
        {
            int perRow = Mathf.Max(1, PerRow);
            int col = index % perRow;
            int row = index / perRow;
            return new RectInt(PosX + col * FrameW, PosY + row * FrameH, DrawW, DrawH);
        }
    }

    /// <summary>
    /// The `data/enemies_gfx/&lt;creature&gt;.xml` sheet description: where each animation sits
    /// in the png and where the entity origin is inside a frame.
    /// </summary>
    public sealed class NoitaSpriteXml
    {
        public string SheetFile;

        /// <summary>Entity origin inside a frame. Several creatures sit on a half pixel.</summary>
        public float OffsetX, OffsetY;

        public string DefaultAnim;
        public readonly List<NoitaAnim> Anims = new();

        public NoitaAnim Default =>
            Anims.FirstOrDefault(a => string.Equals(a.Name, DefaultAnim, StringComparison.OrdinalIgnoreCase))
            ?? Anims.FirstOrDefault();

        // A handful of shipped sheets are not well-formed xml — duck.xml declares
        // default_animation twice, for instance — so the tags are scanned rather than parsed.
        // The files are flat and attribute-only, which makes that safe here.
        private static readonly Regex SpriteTag = new(@"<Sprite\b([^>]*)>", RegexOptions.Singleline);
        private static readonly Regex AnimTag = new(@"<RectAnimation\b([^>]*)>", RegexOptions.Singleline);
        private static readonly Regex AttrPattern = new("([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*\"([^\"]*)\"", RegexOptions.Singleline);

        public static NoitaSpriteXml Load(string path)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) return null;

            string text;
            try { text = File.ReadAllText(path); }
            catch (Exception e) { Debug.LogWarning($"Noita ragdolls: cannot read {path} — {e.Message}"); return null; }

            var spriteMatch = SpriteTag.Match(text);
            if (!spriteMatch.Success) return null;

            var head = Attributes(spriteMatch.Groups[1].Value);
            var sheet = new NoitaSpriteXml
            {
                SheetFile = Str(head, "filename", null),
                OffsetX = Float(head, "offset_x", 0f),
                OffsetY = Float(head, "offset_y", 0f),
                DefaultAnim = Str(head, "default_animation", null)
            };

            foreach (Match m in AnimTag.Matches(text))
            {
                var a = Attributes(m.Groups[1].Value);
                int count = Int(a, "frame_count", 1);
                sheet.Anims.Add(new NoitaAnim
                {
                    Name = Str(a, "name", "anim"),
                    PosX = Int(a, "pos_x", 0),
                    PosY = Int(a, "pos_y", 0),
                    FrameW = Int(a, "frame_width", 16),
                    FrameH = Int(a, "frame_height", 16),
                    Count = Mathf.Max(1, count),
                    PerRow = Mathf.Max(1, Int(a, "frames_per_row", count)),
                    FrameWait = Float(a, "frame_wait", 0.1f),
                    Loop = Int(a, "loop", 1) != 0,
                    Shrink = Int(a, "shrink_by_one_pixel", 0) != 0
                });
            }

            return sheet.Anims.Count > 0 ? sheet : null;
        }

        /// <summary>Last write wins, which is how the duplicated attributes resolve in game.</summary>
        private static Dictionary<string, string> Attributes(string tagBody)
        {
            var dict = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (Match m in AttrPattern.Matches(tagBody))
                dict[m.Groups[1].Value] = m.Groups[2].Value;
            return dict;
        }

        private static string Str(Dictionary<string, string> a, string key, string fallback)
            => a.TryGetValue(key, out var v) && !string.IsNullOrEmpty(v) ? v : fallback;

        private static float Float(Dictionary<string, string> a, string key, float fallback)
            => a.TryGetValue(key, out var v) && float.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out var f)
                ? f
                : fallback;

        // Sizes are whole pixels in every shipped sheet, but parse them as floats anyway so a
        // stray "16.0" does not silently fall back to the default.
        private static int Int(Dictionary<string, string> a, string key, int fallback)
            => a.TryGetValue(key, out var v) && float.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out var f)
                ? Mathf.RoundToInt(f)
                : fallback;
    }

    /// <summary>Locates the files that make up one creature inside an unpacked `data` folder.</summary>
    public static class NoitaPaths
    {
        public static string RagdollDir(string dataRoot, string creature)
            => Path.Combine(dataRoot, "ragdolls", creature);

        public static string FilenamesTxt(string dataRoot, string creature)
            => Path.Combine(RagdollDir(dataRoot, creature), "filenames.txt");

        public static string UvSheet(string dataRoot, string creature)
        {
            string p = Path.Combine(dataRoot, "enemies_gfx", creature + "_uv_src.png");
            return File.Exists(p) ? p : null;
        }

        /// <summary>The sheet xml, normally in enemies_gfx; a few creatures live elsewhere in data.</summary>
        public static string SpriteXml(string dataRoot, string creature)
        {
            string p = Path.Combine(dataRoot, "enemies_gfx", creature + ".xml");
            if (File.Exists(p)) return p;

            try
            {
                foreach (var hit in Directory.EnumerateFiles(dataRoot, creature + ".xml", SearchOption.AllDirectories))
                {
                    // Entity definitions share the creature name but are not sprite sheets.
                    if (hit.IndexOf("entities", StringComparison.OrdinalIgnoreCase) >= 0) continue;
                    return hit;
                }
            }
            catch (Exception) { /* unreadable folder — treat as "no xml" */ }

            return null;
        }

        /// <summary>Every creature under `data/ragdolls` that actually has a part list.</summary>
        public static List<string> Creatures(string dataRoot)
        {
            var list = new List<string>();
            string dir = Path.Combine(dataRoot, "ragdolls");
            if (!Directory.Exists(dir)) return list;

            foreach (var sub in Directory.GetDirectories(dir))
            {
                if (!File.Exists(Path.Combine(sub, "filenames.txt"))) continue;
                list.Add(Path.GetFileName(sub));
            }
            list.Sort(StringComparer.OrdinalIgnoreCase);
            return list;
        }

        /// <summary>
        /// Resolve the part images in the order filenames.txt lists them. The unpacked folders
        /// do not always agree with the manifest — some prefix every file with the creature
        /// name — so fall back to matching on the bare file name.
        /// </summary>
        public static List<(string name, string path)> PartFiles(string dataRoot, string creature)
        {
            var result = new List<(string, string)>();
            string dir = RagdollDir(dataRoot, creature);
            if (!Directory.Exists(dir)) return result;

            var onDisk = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (var f in Directory.GetFiles(dir, "*.png"))
                onDisk[Path.GetFileName(f)] = f;

            var taken = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            string manifest = FilenamesTxt(dataRoot, creature);
            if (File.Exists(manifest))
            {
                foreach (var raw in File.ReadAllLines(manifest))
                {
                    string line = raw.Trim();
                    if (line.Length == 0) continue;

                    string file = Path.GetFileName(line.Replace('\\', '/'));
                    string bare = Path.GetFileNameWithoutExtension(file);

                    string[] candidates =
                    {
                        file,
                        creature + "_" + file,
                        file.StartsWith(creature + "_", StringComparison.OrdinalIgnoreCase)
                            ? file.Substring(creature.Length + 1)
                            : file
                    };

                    foreach (var c in candidates)
                    {
                        if (!onDisk.TryGetValue(c, out var full) || taken.Contains(c)) continue;
                        taken.Add(c);
                        result.Add((bare, full));
                        break;
                    }
                }
            }

            // Anything the manifest missed still belongs to the corpse.
            foreach (var kv in onDisk)
            {
                if (taken.Contains(kv.Key)) continue;
                result.Add((Path.GetFileNameWithoutExtension(kv.Key), kv.Value));
            }

            return result;
        }
    }
}
