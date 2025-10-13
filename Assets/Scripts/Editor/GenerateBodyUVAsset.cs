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
    const string Folder = "Assets/Resources/Animations/Enemies/coward";
    const int PPU = 20;                 // pixels per unit
    const int ColorTolerance = 8;        // ± per channel

    static readonly (Color32 color, UVPart part)[] Legend = new[] {
        (new Color32(255,255,0,255), UVPart.Head),   // yellow
        (new Color32(  0,  0,255,255), UVPart.RArm), // blue  (use as Hand_R)
        (new Color32(255,  0,255,255), UVPart.LArm), // magenta (use as Hand_L)
        (new Color32(  0,255,  0,255), UVPart.Torso),// green  (origin)
        (new Color32(255,  0,  0,255), UVPart.LLeg), // red    (Foot_L)
        (new Color32(128,  0,  0,255), UVPart.RLeg), // dark red (Foot_R)
    };

    [MenuItem("Tools/Sprites/Generate BodyUV Asset (Hardcoded)")]
    public static void Run()
    {
        string absFolder = Path.GetFullPath(Folder);
        var uvPng = Directory.GetFiles(absFolder, "*uv*.png", SearchOption.TopDirectoryOnly).FirstOrDefault();
        if (uvPng == null) { Debug.LogError("No *uv*.png found."); return; }

        string uvAssetPath = ToAssetPath(uvPng);
        var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(uvAssetPath);
        if (!tex) { Debug.LogError("Failed to load UV texture."); return; }

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

            Rect r = s.rect;                    // texture-space (origin bottom-left)
            int x = Mathf.RoundToInt(r.x);
            int y = Mathf.RoundToInt(r.y);
            int w = Mathf.RoundToInt(r.width);
            int h = Mathf.RoundToInt(r.height);

            // NOTE: GetPixels(x,y,w,h) returns Color[] (not Color32[])
            var pixels = tex.GetPixels(x, y, w, h);

            // 1) collect absolute normalized UVs per part (0..1, Y up within the frame)
            var absUv = new Dictionary<UVPart, Vector2>();
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
                    var uv01 = new Vector2(avg.x / w, avg.y / h);   // 0..1 in frame, Y up
                    absUv[part] = uv01;
                }
            }

            // 2) torso as origin: compute torso uv (fallback to sprite pivot if missing)
            Vector2 torsoUv01;
            if (!absUv.TryGetValue(UVPart.Torso, out torsoUv01))
            {
                // sprite pivot as fallback
                var pivot01 = new Vector2(s.pivot.x / r.width, s.pivot.y / r.height);
                torsoUv01 = pivot01;
                absUv[UVPart.Torso] = pivot01; // ensure torso exists
            }

            // 3) convert to torso-relative **world** offsets using PPU=100
            // worldOffset = (uv - torsoUv) ∘ (frameSize / PPU)
            Vector2 scale = new Vector2(w / (float)PPU, h / (float)PPU);

            var entries = new List<BodyUVFrame.Entry>();
            foreach (var kv in absUv)
            {
                Vector2 rel01 = kv.Value - torsoUv01;              // torso at (0,0) in frame space
                Vector2 world = new Vector2(rel01.x * scale.x, rel01.y * scale.y); // meters
                // force torso to exact zero
                if (kv.Key == UVPart.Torso) world = Vector2.zero;

                entries.Add(new BodyUVFrame.Entry { part = kv.Key, uv = world });
            }

            asset.frames.Add(new BodyUVFrame { anim = anim, frame = frame, points = entries });
        }

        AssetDatabase.CreateAsset(asset, assetPath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Generated BodyUV (torso-centered, world units @ PPU=100) with {asset.frames.Count} frames at {assetPath}");
    }

    static bool Close(Color p, Color32 target, int tol)
    {
        // compare in byte space with tolerance; ignore near-transparent pixels
        if (p.a < 0.03f) return false;
        int r = Mathf.RoundToInt(p.r * 255f);
        int g = Mathf.RoundToInt(p.g * 255f);
        int b = Mathf.RoundToInt(p.b * 255f);
        return Math.Abs(r - target.r) <= tol &&
               Math.Abs(g - target.g) <= tol &&
               Math.Abs(b - target.b) <= tol;
    }

    static bool TryParseAnimAndFrame(string spriteName, out string anim, out int frame)
    {
        // expects names like walk_uv_03, stand_uv_00, attack_ranged_uv_1
        anim = spriteName;
        frame = 0;
        var parts = spriteName.Split('_');
        if (parts.Length < 3) return false;
        if (!int.TryParse(parts[^1], NumberStyles.Integer, CultureInfo.InvariantCulture, out frame))
            return false;
        anim = string.Join("_", parts.Take(parts.Length - 2)); // before "_uv" + index
        return true;
    }

    static string ToAssetPath(string abs)
    {
        abs = abs.Replace('\\','/');
        string proj = Application.dataPath.Replace('\\','/');
        return "Assets" + abs.Substring(proj.Length);
    }
}
