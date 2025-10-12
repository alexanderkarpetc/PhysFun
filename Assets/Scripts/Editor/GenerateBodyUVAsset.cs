// Assets/Editor/GenerateBodyUVAsset.cs
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class GenerateBodyUVAsset
{
    // Hardcoded folder
    const string Folder = "Assets/Resources/Animations/Enemies/coward";

    // Map DOT colors → body parts. Use exact or near-exact colors from your UV sheet.
    static readonly (Color32 color, UVPart part)[] Legend = new[] {
        (new Color32(255,255,0,255), UVPart.Head),   // yellow
        (new Color32(  0,  0,255,255), UVPart.RArm), // blue
        (new Color32(255,  0,255,255), UVPart.LArm), // magenta
        (new Color32(  0,255,  0,255), UVPart.Torso),// green
        (new Color32(255,  0,  0,255), UVPart.LLeg), // red
        (new Color32(128,  0,  0,255), UVPart.RLeg), // dark red
        // add more as needed
    };

    const int ColorTolerance = 8; // ± per channel

    [MenuItem("Tools/Sprites/Generate BodyUV Asset (Hardcoded)")]
    public static void Run()
    {
        string absFolder = Path.GetFullPath(Folder);
        var uvPng = Directory.GetFiles(absFolder, "*uv*.png", SearchOption.TopDirectoryOnly).FirstOrDefault();
        if (uvPng == null) { Debug.LogError("No *uv*.png found."); return; }

        string uvAssetPath = ToAssetPath(uvPng);
        var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(uvAssetPath);
        if (!tex) { Debug.LogError("Failed to load UV texture."); return; }

        // ensure readable for pixel access
        var ti = (TextureImporter)AssetImporter.GetAtPath(uvAssetPath);
        bool changed = false;
        if (!ti.isReadable) { ti.isReadable = true; changed = true; }
        if (ti.spriteImportMode != SpriteImportMode.Multiple) { Debug.LogError("UV PNG must be sliced (_uv)."); return; }
        if (changed) { ti.SaveAndReimport(); }

        var sprites = AssetDatabase.LoadAllAssetRepresentationsAtPath(uvAssetPath)
                                   .OfType<Sprite>()
                                   .OrderBy(s => s.name, StringComparer.OrdinalIgnoreCase)
                                   .ToArray();
        if (sprites.Length == 0) { Debug.LogError("No sprites found on UV PNG."); return; }

        // Create/overwrite asset
        string assetPath = Path.Combine(Folder, "BodyUV.asset").Replace('\\','/');
        var asset = ScriptableObject.CreateInstance<BodyUVAsset>();
        asset.sourceTexture = tex;

        foreach (var s in sprites)
        {
            if (!TryParseAnimAndFrame(s.name, out string anim, out int frame))
            {
                Debug.LogWarning($"Skip sprite '{s.name}' (cannot parse anim/frame).");
                continue;
            }

            // read pixels within this sprite rect
            Rect r = s.rect; // in texture pixels (origin bottom-left)
            int x = Mathf.RoundToInt(r.x);
            int y = Mathf.RoundToInt(r.y);
            int w = Mathf.RoundToInt(r.width);
            int h = Mathf.RoundToInt(r.height);

            // GetPixels32 is fast and simple
            var pixels = tex.GetPixels(x, y, w, h);

            // find centroids per color in Legend
            var entries = new List<BodyUVFrame.Entry>();
            foreach (var (color, part) in Legend)
            {
                Vector2 sum = Vector2.zero;
                int count = 0;

                for (int yy = 0; yy < h; yy++)
                {
                    for (int xx = 0; xx < w; xx++)
                    {
                        var p = pixels[yy * w + xx];
                        if (Close(p, color, ColorTolerance))
                        {
                            sum += new Vector2(xx + 0.5f, yy + 0.5f); // pixel center
                            count++;
                        }
                    }
                }

                if (count > 0)
                {
                    Vector2 avg = sum / Mathf.Max(1, count);
                    // normalize to [0..1], Y up
                    var uv = new Vector2(avg.x / w, avg.y / h);
                    entries.Add(new BodyUVFrame.Entry { part = part, uv = uv });
                }
            }

            asset.frames.Add(new BodyUVFrame { anim = anim, frame = frame, points = entries });
        }

        AssetDatabase.CreateAsset(asset, assetPath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Generated BodyUV asset with {asset.frames.Count} frames at {assetPath}");
    }

    static bool Close(Color32 a, Color32 b, int tol)
    {
        return Math.Abs(a.r - b.r) <= tol &&
               Math.Abs(a.g - b.g) <= tol &&
               Math.Abs(a.b - b.b) <= tol &&
               a.a >= 8; // ignore near-transparent
    }

    static bool TryParseAnimAndFrame(string spriteName, out string anim, out int frame)
    {
        // expects names like walk_uv_03, stand_uv_00, attack_ranged_uv_1
        anim = spriteName;
        frame = 0;
        var parts = spriteName.Split('_');
        if (parts.Length < 3) return false;
        // drop trailing index
        if (!int.TryParse(parts[^1], NumberStyles.Integer, CultureInfo.InvariantCulture, out frame))
            return false;
        // drop the "_uv" segment
        anim = string.Join("_", parts.Take(parts.Length - 2)); // everything before "_uv" + index
        return true;
    }

    static string ToAssetPath(string abs)
    {
        abs = abs.Replace('\\','/');
        string proj = Application.dataPath.Replace('\\','/');
        return "Assets" + abs.Substring(proj.Length);
    }
}
