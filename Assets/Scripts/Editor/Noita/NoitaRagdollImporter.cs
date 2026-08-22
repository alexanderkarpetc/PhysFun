using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Ragdolls;
using Spawners;
using UnityEditor;
using UnityEngine;

namespace NoitaImport
{
    /// <summary>
    /// Writes the Unity side of a Noita corpse: a packed part sheet, a
    /// <see cref="RagdollDefinition"/> holding the hierarchy and every baked pose, and a
    /// prefab wired up with rigidbodies and hinges.
    ///
    /// Re-importing a creature reuses the existing asset files, so prefabs and scenes that
    /// already reference a corpse keep working.
    /// </summary>
    public static class NoitaRagdollImporter
    {
        public sealed class Settings
        {
            public string DataRoot = @"D:\UnityMats\noita\data";
            public string OutputRoot = "Assets/Resources/Ragdolls";
            public float PixelsPerUnit = 20f;
            public bool UseLimits = true;
            public float LimitAngle = 70f;
            public bool BuildPrefab = true;

            /// <summary>Transparent border around each packed part, keeps point filtering clean.</summary>
            public int Padding = 1;
        }

        public static bool Import(string creature, Settings settings, out string report)
        {
            var log = new StringBuilder();
            report = null;

            var build = NoitaRagdollSource.Build(settings.DataRoot, creature);
            foreach (var w in build.Warnings) log.AppendLine("  ! " + w);

            if (build.Parts.Count == 0)
            {
                report = $"{creature}: nothing to build\n{log}";
                return false;
            }

            string folder = EnsureFolder(settings.OutputRoot, creature);
            string sheetPath = $"{folder}/{creature}_parts.png";
            string defPath = $"{folder}/{creature}_ragdoll.asset";
            string prefabPath = $"{folder}/{Capitalize(creature)}Ragdoll.prefab";

            var placements = PackAtlas(build, settings, sheetPath);
            var sprites = SliceAtlas(sheetPath, placements, build, settings);

            var def = WriteDefinition(defPath, build, sprites, settings);
            if (settings.BuildPrefab) BuildPrefab(prefabPath, def, build, settings);

            log.AppendLine($"  {build.Parts.Count} parts, {build.Poses.Count} poses");
            log.Append("  ").Append(HierarchyText(build));
            report = $"{creature}: ok\n{log}";
            return true;
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Part sheet
        // ─────────────────────────────────────────────────────────────────────────────

        private struct Placement
        {
            public RectInt Crop;    // source rect in frame pixels, top-down
            public int X, Y;        // position in the atlas, top-down
        }

        private static Placement[] PackAtlas(RagdollBuild build, Settings settings, string assetPath)
        {
            int pad = Mathf.Max(0, settings.Padding);
            int n = build.Parts.Count;
            var places = new Placement[n];

            for (int i = 0; i < n; i++)
            {
                var b = build.Parts[i].Bounds;
                int x0 = Mathf.Max(0, b.xMin - pad);
                int y0 = Mathf.Max(0, b.yMin - pad);
                int x1 = Mathf.Min(build.Parts[i].W, b.xMax + pad);
                int y1 = Mathf.Min(build.Parts[i].H, b.yMax + pad);
                places[i].Crop = new RectInt(x0, y0, x1 - x0, y1 - y0);
            }

            // Shelf pack, tallest first. A corpse is a handful of tiny sprites; anything
            // cleverer than this would only save a few dozen texels.
            var order = Enumerable.Range(0, n).OrderByDescending(i => places[i].Crop.height).ToArray();

            int width = 8;
            foreach (var i in order) width = Mathf.Max(width, places[i].Crop.width + 2);
            int area = places.Sum(p => (p.Crop.width + 1) * (p.Crop.height + 1));
            while (width * width < area) width *= 2;
            width = Mathf.NextPowerOfTwo(width);

            int cx = 0, cy = 0, shelf = 0;
            foreach (var i in order)
            {
                var crop = places[i].Crop;
                if (cx + crop.width > width)
                {
                    cx = 0;
                    cy += shelf + 1;
                    shelf = 0;
                }
                places[i].X = cx;
                places[i].Y = cy;
                cx += crop.width + 1;
                shelf = Mathf.Max(shelf, crop.height);
            }

            int height = Mathf.NextPowerOfTwo(cy + shelf + 1);

            var pixels = new Color32[width * height];   // top-down while we fill it
            for (int i = 0; i < n; i++)
            {
                var part = build.Parts[i];
                var crop = places[i].Crop;
                for (int y = 0; y < crop.height; y++)
                for (int x = 0; x < crop.width; x++)
                {
                    var c = part.At(crop.xMin + x, crop.yMin + y);
                    if (c.a == 0) continue;
                    int ax = places[i].X + x, ay = places[i].Y + y;
                    if (ax >= width || ay >= height) continue;
                    pixels[ay * width + ax] = c;
                }
            }

            var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            var flipped = new Color32[pixels.Length];
            for (int y = 0; y < height; y++)
                Array.Copy(pixels, y * width, flipped, (height - 1 - y) * width, width);
            tex.SetPixels32(flipped);
            tex.Apply();

            string full = Path.GetFullPath(assetPath);
            Directory.CreateDirectory(Path.GetDirectoryName(full) ?? ".");
            File.WriteAllBytes(full, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);

            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
            return places;
        }

        private static Dictionary<string, Sprite> SliceAtlas(string assetPath, Placement[] places,
                                                             RagdollBuild build, Settings settings)
        {
            var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            var result = new Dictionary<string, Sprite>();
            if (importer == null)
            {
                Debug.LogError($"Noita ragdolls: no texture importer for {assetPath}");
                return result;
            }

            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Multiple;
            importer.filterMode = FilterMode.Point;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = true;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.spritePixelsPerUnit = settings.PixelsPerUnit;
            importer.isReadable = true;              // the fire/erase systems read corpse pixels
            importer.textureCompression = TextureImporterCompression.Uncompressed;

            // Settle the import mode before the data provider reads it, otherwise it hands
            // back a single-sprite view and the slices go nowhere.
            EditorUtility.SetDirty(importer);
            importer.SaveAndReimport();

            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
            int atlasH = tex ? tex.height : 0;

            var slices = new SliceSpec[build.Parts.Count];
            for (int i = 0; i < build.Parts.Count; i++)
            {
                var part = build.Parts[i];
                var crop = places[i].Crop;

                slices[i] = new SliceSpec
                {
                    Name = part.Name,
                    Rect = new Rect(places[i].X, atlasH - (places[i].Y + crop.height), crop.width, crop.height),
                    // The pivot is the part's own centre, so a pose can place it and a hinge
                    // can hang off a plain local offset.
                    Pivot = new Vector2(
                        (part.PivotPx.x + 0.5f - crop.xMin) / crop.width,
                        1f - (part.PivotPx.y + 0.5f - crop.yMin) / crop.height)
                };
            }

            SpriteSlicer.Apply(importer, slices);

            foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(assetPath))
                if (obj is Sprite s) result[s.name] = s;

            if (result.Count == 0)
                Debug.LogError($"Noita ragdolls: {assetPath} produced no sprites — slicing failed.");

            return result;
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Definition asset
        // ─────────────────────────────────────────────────────────────────────────────

        private static RagdollDefinition WriteDefinition(string path, RagdollBuild build,
                                                         IReadOnlyDictionary<string, Sprite> sprites,
                                                         Settings settings)
        {
            var def = AssetDatabase.LoadAssetAtPath<RagdollDefinition>(path);
            bool fresh = def == null;
            if (fresh) def = ScriptableObject.CreateInstance<RagdollDefinition>();

            def.creature = build.Creature;
            def.frameWidth = build.FrameW;
            def.frameHeight = build.FrameH;
            def.originPx = build.OriginPx;
            def.pixelsPerUnit = settings.PixelsPerUnit;
            def.defaultAnim = build.DefaultAnim;

            def.parts.Clear();
            foreach (var p in build.Parts)
            {
                sprites.TryGetValue(p.Name, out var sprite);
                def.parts.Add(new RagdollPart
                {
                    name = p.Name,
                    sprite = sprite,
                    parent = p.Parent,
                    pivotPx = p.PivotPx,
                    anchorPx = p.AnchorPx,
                    useLimits = settings.UseLimits && p.Parent >= 0,
                    limitLow = -settings.LimitAngle,
                    limitHigh = settings.LimitAngle,
                    uvColor = p.HasUv ? p.UvColor : new Color32(0, 0, 0, 0)
                });
            }

            def.poses.Clear();
            foreach (var pose in build.Poses)
                def.poses.Add(new RagdollPose
                {
                    anim = pose.Anim,
                    frame = pose.Frame,
                    positionsPx = pose.Pos,
                    rotations = pose.Rot
                });

            if (fresh) AssetDatabase.CreateAsset(def, path);
            else EditorUtility.SetDirty(def);

            return def;
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Prefab
        // ─────────────────────────────────────────────────────────────────────────────

        private static void BuildPrefab(string path, RagdollDefinition def, RagdollBuild build, Settings settings)
        {
            var root = new GameObject(Path.GetFileNameWithoutExtension(path));
            try
            {
                var ragdoll = root.AddComponent<Ragdoll>();
                var bodies = new Rigidbody2D[def.parts.Count];
                var rest = def.RestPose;

                for (int i = 0; i < def.parts.Count; i++)
                {
                    var part = def.parts[i];
                    var go = new GameObject(part.name);
                    go.transform.SetParent(root.transform, false);

                    bool posed = rest != null && rest.positionsPx != null && i < rest.positionsPx.Length;
                    Vector2 posPx = posed ? rest.positionsPx[i] : part.pivotPx;
                    float rot = posed && rest.rotations != null && i < rest.rotations.Length ? rest.rotations[i] : 0f;
                    go.transform.localPosition = def.PixelToLocal(posPx);
                    go.transform.localRotation = Quaternion.Euler(0f, 0f, rot);

                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = part.sprite;
                    sr.sortingOrder = build.Parts[i].SourceOrder;

                    var rb = go.AddComponent<Rigidbody2D>();
                    rb.interpolation = RigidbodyInterpolation2D.Interpolate;
                    rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
                    rb.angularDamping = 0.4f;
                    bodies[i] = rb;

                    var poly = go.AddComponent<PolygonCollider2D>();
                    if (poly.GetTotalPointCount() < 3) BoxFallback(poly, def, build.Parts[i]);
                    MassRecalculator.SetMass(part.sprite, rb, poly);

                    if (part.parent < 0) continue;

                    var hinge = go.AddComponent<HingeJoint2D>();
                    hinge.connectedBody = bodies[part.parent];
                    hinge.autoConfigureConnectedAnchor = false;
                    hinge.anchor = def.PixelToLocalDelta(part.anchorPx - part.pivotPx);
                    hinge.connectedAnchor = def.PixelToLocalDelta(part.anchorPx - def.parts[part.parent].pivotPx);
                    hinge.enableCollision = false;
                    hinge.useLimits = part.useLimits;
                    hinge.limits = new JointAngleLimits2D { min = part.limitLow, max = part.limitHigh };
                }

                ragdoll.EditorBind(def, bodies);
                PrefabUtility.SaveAsPrefabAsset(root, path);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }
        }

        /// <summary>A two-pixel finger has no outline worth tracing; give it its bounding box.</summary>
        private static void BoxFallback(PolygonCollider2D poly, RagdollDefinition def, PartBuild part)
        {
            var b = part.Bounds;
            Vector2 pivot = part.PivotPx;
            Vector2 tl = def.PixelToLocalDelta(new Vector2(b.xMin - 0.5f - pivot.x, b.yMin - 0.5f - pivot.y));
            Vector2 br = def.PixelToLocalDelta(new Vector2(b.xMax - 0.5f - pivot.x, b.yMax - 0.5f - pivot.y));

            poly.pathCount = 1;
            poly.SetPath(0, new[]
            {
                new Vector2(tl.x, br.y),
                new Vector2(br.x, br.y),
                new Vector2(br.x, tl.y),
                new Vector2(tl.x, tl.y)
            });
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Helpers
        // ─────────────────────────────────────────────────────────────────────────────

        private static string EnsureFolder(string root, string creature)
        {
            var parts = root.Split('/');
            string acc = parts[0];
            for (int i = 1; i < parts.Length; i++)
            {
                if (!AssetDatabase.IsValidFolder(acc + "/" + parts[i]))
                    AssetDatabase.CreateFolder(acc, parts[i]);
                acc += "/" + parts[i];
            }

            if (!AssetDatabase.IsValidFolder(acc + "/" + creature))
                AssetDatabase.CreateFolder(acc, creature);

            return acc + "/" + creature;
        }

        private static string Capitalize(string s)
            => string.IsNullOrEmpty(s) ? s : char.ToUpperInvariant(s[0]) + s.Substring(1);

        private static string HierarchyText(RagdollBuild build)
        {
            var sb = new StringBuilder();
            for (int i = 0; i < build.Parts.Count; i++)
            {
                var p = build.Parts[i];
                if (i > 0) sb.Append(", ");
                sb.Append(p.Name);
                if (p.Parent >= 0) sb.Append("→").Append(build.Parts[p.Parent].Name);
                if (!p.HasUv) sb.Append("(no uv)");
            }
            return sb.ToString();
        }
    }
}
