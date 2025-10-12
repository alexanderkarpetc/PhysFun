// Assets/Editor/SliceFromXml.cs
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Xml.Linq;
using UnityEditor;
using UnityEngine;

public static class SliceFromXml
{
    private const string FolderPath = "Assets/Resources/Animations/Enemies/coward";

    [MenuItem("PhysFun/Slice From XML (Hardcoded)")]
    public static void Run()
    {
        string absFolder = Path.GetFullPath(FolderPath);
        if (!Directory.Exists(absFolder))
        {
            Debug.LogError($"Folder not found: {FolderPath}");
            return;
        }

        // Main XML & PNG
        string mainXmlAbs = Directory.GetFiles(absFolder, "*.xml", SearchOption.TopDirectoryOnly)
                                     .FirstOrDefault(p => !Path.GetFileName(p).ToLowerInvariant().Contains("uv"));
        string mainPngAbs = Directory.GetFiles(absFolder, "*.png", SearchOption.TopDirectoryOnly)
                                     .FirstOrDefault(p => !Path.GetFileName(p).ToLowerInvariant().Contains("uv"));

        if (mainXmlAbs == null || mainPngAbs == null)
        {
            Debug.LogError($"Missing main XML or PNG in {FolderPath}");
            return;
        }

        string mainXmlAsset = ToAssetPath(mainXmlAbs);
        string mainPngAsset = ToAssetPath(mainPngAbs);
        XDocument mainDoc   = XDocument.Load(mainXmlAsset);

        // Slice main
        SliceOneSheet(mainPngAsset, mainDoc, addUvSuffix:false);

        // UV PNGs (zero or more)
        var uvPngsAbs = Directory.GetFiles(absFolder, "*uv*.png", SearchOption.TopDirectoryOnly);
        foreach (var uvPngAbs in uvPngsAbs)
        {
            string uvPngAsset = ToAssetPath(uvPngAbs);

            // Prefer a UV xml if present; else reuse main XML
            string uvXmlAbs = Directory.GetFiles(absFolder, "*uv*.xml", SearchOption.TopDirectoryOnly)
                                       .FirstOrDefault(x => Path.GetFileNameWithoutExtension(x)
                                           .Equals(Path.GetFileNameWithoutExtension(uvPngAbs), StringComparison.OrdinalIgnoreCase));
            XDocument doc = uvXmlAbs != null ? XDocument.Load(ToAssetPath(uvXmlAbs)) : mainDoc;

            SliceOneSheet(uvPngAsset, doc, addUvSuffix:true);
        }

        AssetDatabase.Refresh();
        Debug.Log("Slicing completed.");
    }

    private static void SliceOneSheet(string pngAssetPath, XDocument doc, bool addUvSuffix)
    {
        var ti = AssetImporter.GetAtPath(pngAssetPath) as TextureImporter;
        if (ti == null) { Debug.LogError($"TextureImporter not found: {pngAssetPath}"); return; }

        ti.textureType = TextureImporterType.Sprite;
        ti.spriteImportMode = SpriteImportMode.Multiple;
        ti.filterMode = FilterMode.Point;
        ti.mipmapEnabled = false;
        ti.alphaIsTransparency = true;
        ti.wrapMode = TextureWrapMode.Clamp;
        ti.spritePixelsPerUnit = 20;
        ti.isReadable = true;

        var sprite = doc.Root;
        if (sprite == null || sprite.Name != "Sprite")
        {
            Debug.LogError("XML root <Sprite> not found.");
            return;
        }

        // Offsets (pivot); note: pivot Y inverted for Unity coords
        int offsetX = GetInt(sprite, "offset_x", 0);
        int offsetY = GetInt(sprite, "offset_y", 0);

        var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(pngAssetPath);
        if (!tex) { Debug.LogError($"Failed to load texture: {pngAssetPath}"); return; }

        int texW = tex.width, texH = tex.height;
        var metas = new List<SpriteMetaData>();

        foreach (var ra in sprite.Elements("RectAnimation"))
        {
            string name = GetString(ra, "name", "anim");
            if (addUvSuffix) name += "_uv";

            int posX = GetInt(ra, "pos_x", 0);
            int posY = GetInt(ra, "pos_y", 0);
            int frameCount = GetInt(ra, "frame_count", 1);
            int frameW = GetInt(ra, "frame_width", 16);
            int frameH = GetInt(ra, "frame_height", 16);
            int perRow = Math.Max(1, GetInt(ra, "frames_per_row", frameCount));

            for (int f = 0; f < frameCount; f++)
            {
                int col = f % perRow;
                int row = f / perRow;

                int x = posX + col * frameW;
                int yTop = posY + row * frameH;
                int yUnity = texH - (yTop + frameH); // convert top-left → bottom-left

                if (x < 0 || yUnity < 0 || x + frameW > texW || yUnity + frameH > texH)
                {
                    Debug.LogWarning($"Out of bounds: {name}_{f} on {pngAssetPath}");
                    continue;
                }

                // Pivot normalized; invert Y
                Vector2 pivot = new Vector2(
                    Mathf.Clamp01(frameW > 0 ? (float)offsetX / frameW : 0.5f),
                    Mathf.Clamp01(frameH > 0 ? 1f - (float)offsetY / frameH : 0.5f)
                );

                metas.Add(new SpriteMetaData
                {
                    alignment = (int)SpriteAlignment.Custom,
                    border = Vector4.zero,
                    name = $"{name}_{f:D2}",
                    pivot = pivot,
                    rect = new Rect(x, yUnity, frameW, frameH)
                });
            }
        }

        if (metas.Count == 0) { Debug.LogError($"No frames generated for {pngAssetPath}"); return; }

        ti.spritesheet = metas.ToArray();
        EditorUtility.SetDirty(ti);
        ti.SaveAndReimport();

        Debug.Log($"Sliced {metas.Count} sprites into {pngAssetPath}");
    }

    private static string ToAssetPath(string absPath)
    {
        absPath = absPath.Replace('\\', '/');
        string proj = Application.dataPath.Replace('\\', '/');
        if (!absPath.StartsWith(proj)) throw new Exception("File is outside project: " + absPath);
        return "Assets" + absPath.Substring(proj.Length);
    }

    private static int GetInt(XElement e, string attr, int defVal)
        => int.TryParse((string)e.Attribute(attr), out var v) ? v : defVal;

    private static string GetString(XElement e, string attr, string defVal)
        => (string)e.Attribute(attr) ?? defVal;
}
