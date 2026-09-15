using System;
using System.Collections.Generic;
using System.Linq;
using Binny;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Editor
{
    /// <summary>
    /// Assembles Binny out of the loose parts in <c>GameConcepts/Binny</c>.
    ///
    /// The concept was cut into a body, a gear, a screen and two flames rather than drawn as
    /// frames, so there is no sheet to import and no clips to bake: the prefab *is* the assembly,
    /// and the only thing that has to be right is where each part sits. Those anchors are in the
    /// README as source pixels, and they are repeated here as the constants below — one place to
    /// change if the art is ever recut, and near enough to read against the table.
    ///
    /// It also fixes the import settings on the way past. Point filter, no compression and the
    /// game's own pixel scale are not negotiable for pixel art of this size, and the pngs come in
    /// with Unity's photo defaults, which smear him.
    ///
    /// Re-run it whenever the art changes: it overwrites the prefab it made last time, so anything
    /// already standing in a scene keeps its link and just gets rebuilt.
    /// </summary>
    public static class BinnyBuilder
    {
        private const string ArtDir = "Assets/GameConcepts/Binny";
        private const string PrefabDir = "Assets/Resources/Prefabs";
        private const string PrefabPath = PrefabDir + "/Binny.prefab";

        /// <summary>
        /// Twice the size the README's 41 gives, which read as a toy next to the player: at 20 the
        /// 41px chassis is a little over two world units, so he towers over him — and 20 is what
        /// every other character in the game is drawn at, so one source pixel is finally the same
        /// size on him as it is on a soldier.
        /// </summary>
        private const float PixelsPerUnit = 20f;

        /// <summary>Thrust frames per side. Four, cycled at 12fps while he flies.</summary>
        private const int ThrustFrames = 4;

        // Where each part sits in the master frame, as the top-left of its own rect in source
        // pixels. Origin is the top-left of the 42x47 sheet, y down, exactly like the README table.
        private static readonly Vector2 GearLeftAt = new(0f, 12f);    // 11x11
        private static readonly Vector2 FaceAt = new(14f, 20f);       // 14x11
        private static readonly Vector2 ThrustLeftAt = new(13f, 41f); // 5x5
        private static readonly Vector2 ThrustRightAt = new(22f, 41f);// 6x6

        /// <summary>
        /// The right-hand gear is the same wheel flipped, and the sheet has no hole cut for it —
        /// only the left one was drawn. Mirroring it across the frame puts it on the opposite
        /// shoulder with its outer teeth flush with the edge, the way the left one is.
        /// </summary>
        private static readonly Vector2 GearRightAt = new(31f, 12f);

        /// <summary>
        /// The chassis' own silhouette inside the body sprite, in pixels: the gear pokes two
        /// pixels out past it on the left, and the hull should not. This is what he shoves debris
        /// with, and what things get thrown at once there is something to throw.
        /// </summary>
        private static readonly Rect Hull = new(2f, 0f, 40f, 41f);

        /// <summary>
        /// What he has to fly round: the world (Default) and the bedrock (Untouchable). Not the
        /// player, who he is on his way to, and not the enemies — he would stop dead at the first
        /// one in a corridor, and a bin bumping into a soldier is their problem, not his.
        /// </summary>
        private const int ObstacleMask = (1 << 0) | (1 << 6);

        [MenuItem("PhysFun/Binny/Build Binny", false, 300)]
        private static void Build()
        {
            FixImports();

            var body = Load("Parts/Binny_Body.png");
            if (!body) return;

            var prefab = BuildPrefab(body);
            if (!prefab) return;

            Selection.activeObject = prefab;
            EditorGUIUtility.PingObject(prefab);
            Debug.Log($"[PhysFun] Binny built: {PrefabPath}", prefab);
        }

        // ------------------------------------------------------------------ import

        /// <summary>
        /// Every drawing of him, on the same terms. The dialogue window in UI/ is left alone: it is
        /// nine-sliced chrome with its own borders, not a part of the machine.
        /// </summary>
        private static void FixImports()
        {
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ArtDir }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (path.Contains("/UI/")) continue;

                if (AssetImporter.GetAtPath(path) is TextureImporter importer) Fix(importer);
            }

            AssetDatabase.Refresh();
        }

        private static void Fix(TextureImporter importer)
        {
            var settings = new TextureImporterSettings();
            importer.ReadTextureSettings(settings);

            bool dirty = false;

            void Set<T>(T current, T wanted, Action<T> apply)
            {
                if (EqualityComparer<T>.Default.Equals(current, wanted)) return;
                apply(wanted);
                dirty = true;
            }

            // Everything the settings block owns goes through the settings block. Setting the
            // same things on the importer first does not work: SetTextureSettings writes back the
            // whole block, so the copy read at the top of this method would undo them again.
            Set(settings.textureType, TextureImporterType.Sprite, v => settings.textureType = v);

            // Single, not Multiple: each part is one drawing, and a sliced sheet hides it behind a
            // sub-asset whose rect is the trim, not the canvas the anchors are measured against.
            Set(settings.spriteMode, (int)SpriteImportMode.Single, v => settings.spriteMode = v);
            Set(settings.spritePixelsPerUnit, PixelsPerUnit, v => settings.spritePixelsPerUnit = v);
            Set(settings.filterMode, FilterMode.Point, v => settings.filterMode = v);
            Set(settings.mipmapEnabled, false, v => settings.mipmapEnabled = v);
            Set(settings.alphaIsTransparency, true, v => settings.alphaIsTransparency = v);

            // Centre pivots throughout, so a part's position is its centre and the anchors above
            // are the only arithmetic in the layout. FullRect keeps a trimmed flame's quad the
            // size of its own canvas, which is what those anchors are measured against.
            Set(settings.spriteAlignment, (int)SpriteAlignment.Center, v => settings.spriteAlignment = v);
            Set(settings.spritePivot, new Vector2(0.5f, 0.5f), v => settings.spritePivot = v);
            Set(settings.spriteMeshType, SpriteMeshType.FullRect, v => settings.spriteMeshType = v);

            importer.SetTextureSettings(settings);

            // Compression is not in that block, so it goes on the importer — and it has to go on
            // after, for the same reason.
            Set(importer.textureCompression, TextureImporterCompression.Uncompressed,
                v => importer.textureCompression = v);

            if (!dirty) return;

            importer.SaveAndReimport();
        }

        // ------------------------------------------------------------------ prefab

        private static GameObject BuildPrefab(Sprite body)
        {
            EnsureFolder(PrefabDir);

            // The body's centre is the origin of everything: the root sits there, so he turns and
            // parks about his middle rather than about a corner of the sheet.
            var origin = new Vector2(body.rect.width * 0.5f, body.rect.height * 0.5f);

            var root = new GameObject("Binny");

            var view = new GameObject("View");
            view.transform.SetParent(root.transform, false);

            // Drawing order out of the README: thrust, body, gear, face.
            var thrustLeft = Part(view, "Thrust_L", Load("VFX/Binny_VFX_Thrust_L_01.png"), ThrustLeftAt, origin, -1);
            var thrustRight = Part(view, "Thrust_R", Load("VFX/Binny_VFX_Thrust_R_01.png"), ThrustRightAt, origin, -1);
            Part(view, "Body", body, Vector2.zero, origin, 0);
            var gearLeft = Part(view, "Gear_L", Load("Parts/Binny_Gear.png"), GearLeftAt, origin, 1);
            var gearRight = Part(view, "Gear_R", Load("Parts/Binny_Gear_Mirror.png"), GearRightAt, origin, 1);
            var face = Part(view, "Face", Load($"Faces/Binny_Face_{BinnyFace.Angry}.png"), FaceAt, origin, 2);

            var binnyView = view.AddComponent<BinnyView>();
            WireView(binnyView, face, gearLeft, gearRight, thrustLeft, thrustRight);

            // One group, so the whole machine sorts against the world as a single thing and the
            // orders above only ever fight each other.
            root.AddComponent<SortingGroup>();

            var rb = root.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Kinematic;
            rb.interpolation = RigidbodyInterpolation2D.Interpolate;
            rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;

            var hull = root.AddComponent<BoxCollider2D>();
            hull.size = Hull.size / PixelsPerUnit;
            hull.offset = new Vector2((Hull.center.x - origin.x) / PixelsPerUnit,
                                      (origin.y - Hull.center.y) / PixelsPerUnit);

            WireController(root.AddComponent<BinnyController>(), rb, binnyView, hull);

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            UnityEngine.Object.DestroyImmediate(root);
            return prefab;
        }

        /// <summary>
        /// One piece of him, hung at its anchor. The anchor is the part's top-left in sheet pixels;
        /// with centre pivots on both, the offset is the gap between the two centres, y flipped
        /// because the sheet counts downwards and the world counts up.
        /// </summary>
        private static SpriteRenderer Part(
            GameObject parent, string name, Sprite sprite, Vector2 topLeft, Vector2 origin, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent.transform, false);

            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.sortingOrder = order;

            if (sprite)
            {
                var centre = topLeft + new Vector2(sprite.rect.width, sprite.rect.height) * 0.5f;
                go.transform.localPosition = new Vector3((centre.x - origin.x) / PixelsPerUnit,
                                                         (origin.y - centre.y) / PixelsPerUnit, 0f);
            }

            return renderer;
        }

        private static void WireView(BinnyView view, SpriteRenderer face, SpriteRenderer gearLeft,
            SpriteRenderer gearRight, SpriteRenderer thrustLeft, SpriteRenderer thrustRight)
        {
            var so = new SerializedObject(view);
            so.FindProperty("_face").objectReferenceValue = face;
            so.FindProperty("_gearLeft").objectReferenceValue = gearLeft;
            so.FindProperty("_gearRight").objectReferenceValue = gearRight;
            so.FindProperty("_thrustLeft").objectReferenceValue = thrustLeft;
            so.FindProperty("_thrustRight").objectReferenceValue = thrustRight;

            Fill(so.FindProperty("_faces"), Faces());
            Fill(so.FindProperty("_thrustLeftFrames"), Thrust("L"));
            Fill(so.FindProperty("_thrustRightFrames"), Thrust("R"));

            so.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void WireController(BinnyController binny, Rigidbody2D rb, BinnyView view, Collider2D shape)
        {
            var so = new SerializedObject(binny);
            so.FindProperty("_rb").objectReferenceValue = rb;
            so.FindProperty("_view").objectReferenceValue = view;
            so.FindProperty("_shape").objectReferenceValue = shape;
            so.FindProperty("_obstacles").intValue = ObstacleMask;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void Fill(SerializedProperty list, IReadOnlyList<Sprite> sprites)
        {
            list.arraySize = sprites.Count;
            for (int i = 0; i < sprites.Count; i++)
                list.GetArrayElementAtIndex(i).objectReferenceValue = sprites[i];
        }

        /// <summary>Every face in <see cref="BinnyFace"/> order, which is the order the view indexes.</summary>
        private static Sprite[] Faces() =>
            Enum.GetValues(typeof(BinnyFace))
                .Cast<BinnyFace>()
                .Select(f => Load($"Faces/Binny_Face_{f}.png"))
                .ToArray();

        private static Sprite[] Thrust(string side) =>
            Enumerable.Range(1, ThrustFrames)
                .Select(i => Load($"VFX/Binny_VFX_Thrust_{side}_{i:00}.png"))
                .ToArray();

        private static Sprite Load(string relative)
        {
            var path = $"{ArtDir}/{relative}";
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);

            if (!sprite)
            {
                Debug.LogError($"[PhysFun] Binny is missing a part: no sprite at {path}.");
                return null;
            }

            Check(sprite, path);
            return sprite;
        }

        /// <summary>
        /// The layout is arithmetic on source pixels, so it is only right if the sprite came in on
        /// the terms <see cref="Fix"/> asked for. Anything else — the old defaults still in place,
        /// a leftover sliced sub-sprite, a pivot somewhere other than the middle — lays the parts
        /// out around a body of the wrong size, which reads as a small Binny with his gears flung
        /// off him. Cheaper to say so here than to work it out from the scene.
        /// </summary>
        private static void Check(Sprite sprite, string path)
        {
            if (!Mathf.Approximately(sprite.pixelsPerUnit, PixelsPerUnit))
                Debug.LogError($"[PhysFun] {path} imported at {sprite.pixelsPerUnit} pixels per unit, " +
                               $"not {PixelsPerUnit}. The import settings did not take.", sprite);

            var texture = sprite.texture;
            if (texture && (sprite.rect.width != texture.width || sprite.rect.height != texture.height))
                Debug.LogError($"[PhysFun] {path} is a sliced sub-sprite ({sprite.rect.size}) rather than the " +
                               $"whole {texture.width}x{texture.height} drawing. Sprite Mode must be Single.", sprite);

            var centre = sprite.rect.size * 0.5f;
            if (Vector2.Distance(sprite.pivot, centre) > 0.01f)
                Debug.LogError($"[PhysFun] {path} pivots at {sprite.pivot}, not its centre {centre}.", sprite);
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;

            var parent = System.IO.Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, System.IO.Path.GetFileName(path));
        }
    }
}
