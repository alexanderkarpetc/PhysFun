using System.Linq;
using NoitaImport;
using Ragdolls;
using Spawners;
using UnityEditor;
using UnityEditor.U2D.Aseprite;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Cuts a corpse out of soldier.aseprite.
    ///
    /// Every other creature gets its ragdoll from Noita's data, where the animator already worked
    /// in separate limbs and the importer only has to read them back. The soldier is drawn as one
    /// 11x18 figure on a single layer, so where he comes apart is a decision rather than a fact,
    /// and that decision is the one thing this file holds: <see cref="Cuts"/> is his idle frame
    /// divided along the joints, in canvas pixels. Everything after that — part sheet, definition,
    /// prefab, hinges, masses — is <see cref="NoitaRagdollImporter"/>'s, so the soldier's body
    /// behaves like everyone else's.
    ///
    /// The cuts belong to this drawing and nothing else: the dark soldier stands on a 20px canvas
    /// with a shorter head, and his corpse was built by running this once with his rows and his
    /// paths. Another palette means reading its idle frame and doing the same.
    ///
    /// Run it after <see cref="SoldierBuilder"/>: it reads the frame through the import settings
    /// that one applies, and it is what puts the <see cref="RagdollSpawner"/> on the live soldier.
    /// Re-running overwrites what it made last time.
    /// </summary>
    public static class SoldierRagdollBuilder
    {
        private const string Source = "Assets/Sprites/Enemies/wizard.aseprite";
        private const string Creature = "wizard";
        private const string EnemyPrefabPath = "Assets/Resources/Prefabs/Enemies/Wizard.prefab";
        public const string RagdollPrefabPath = "Assets/Resources/Ragdolls/wizard/WizardRagdoll.prefab";

        /// <summary>Matches <see cref="SoldierBuilder"/>; the corpse has to be drawn at his scale.</summary>
        private const float PixelsPerUnit = 20f;

        /// <summary>Loose enough for a body to fold up, tight enough that nothing bends backwards.</summary>
        private const float LimitAngle = 55f;

        /// <summary>
        /// The Aseprite importer names its sprites Frame_0, Frame_1, … and
        /// <see cref="Ragdoll.ApplySpritePose"/> splits such a name into animation "Frame" plus an
        /// index, so a pose baked under this name is the one a dying soldier asks for.
        /// </summary>
        private const string Anim = "Frame";

        /// <summary>Where the art is pivoted, set by <see cref="SoldierBuilder"/>: canvas bottom centre.</summary>
        private static readonly Vector2 PivotAnchor = new(0.5f, 0f);

        /// <summary>One piece of the soldier: the block of the canvas it owns, and how it hangs on.</summary>
        private readonly struct Cut
        {
            public readonly string Name;

            /// <summary>Canvas pixels this piece takes, top-down. The blocks never overlap, and
            /// whatever no block claims is left out of the corpse altogether.</summary>
            public readonly RectInt[] Regions;

            /// <summary>Index into <see cref="Cuts"/>, -1 for the piece everything else hangs off.</summary>
            public readonly int Parent;

            /// <summary>Hinge with the parent, in canvas pixels — the joint you would point at.</summary>
            public readonly Vector2 Anchor;

            /// <summary>Sorting order inside the corpse, back to front.</summary>
            public readonly int Order;

            public Cut(string name, int parent, Vector2 anchor, int order, params RectInt[] regions)
            {
                Name = name;
                Regions = regions;
                Parent = parent;
                Anchor = anchor;
                Order = order;
            }

            public bool Contains(int x, int y)
            {
                foreach (var r in Regions)
                    if (x >= r.xMin && x < r.xMax && y >= r.yMin && y < r.yMax)
                        return true;
                return false;
            }
        }

        /// <summary>
        /// The wizard read off his idle frame: hat and face down to row 9, sleeves out to both sides
        /// on rows 11-13, and the robe below.
        ///
        /// The robe below the waist is cut into two legs even though the drawing has none: in one
        /// piece it is a rigid slab with a flat bottom and no joint anywhere under the shoulders, so
        /// the corpse lands on it and stands there. As two legs it buckles the way the soldier does.
        ///
        /// The seam runs straight down the middle, which halves the placket instead of leaving it
        /// on the body. Leaving it would make the torso an L, and a part gets the box its pixels
        /// fill — an L-shaped torso would get a box swallowing both legs, and he would rest on that
        /// box with his legs dangling inside it. Two pixels of trim split down the seam is cheaper.
        ///
        /// The torso comes first because a hinge needs its parent to exist already.
        /// </summary>
        private static readonly Cut[] Cuts =
        {
            new("torso", -1, Vector2.zero, 2,
                new RectInt(0, 10, 20, 1),   // shoulders
                new RectInt(9, 11, 4, 3),    // chest, the strip the sleeves leave between them
                new RectInt(0, 14, 20, 2)),  // waist
            new("leg_l", 0, new Vector2(7.5f, 15.5f), 1, new RectInt(0, 16, 10, 6)),
            new("leg_r", 0, new Vector2(12f, 15.5f), 0, new RectInt(10, 16, 10, 6)),
            new("head", 0, new Vector2(10f, 9.5f), 4, new RectInt(0, 0, 20, 10)),
            new("arm_l", 0, new Vector2(8.5f, 11.5f), 0, new RectInt(0, 11, 9, 3)),
            new("arm_r", 0, new Vector2(12.5f, 11.5f), 3, new RectInt(13, 11, 7, 3)),
        };

        [MenuItem("PhysFun/Enemies/Build Soldier Ragdoll", false, 201)]
        private static void Build()
        {
            if (AssetImporter.GetAtPath(Source) is not AsepriteImporter importer)
            {
                Debug.LogError($"[PhysFun] No Aseprite asset at {Source}.");
                return;
            }

            if (importer.pivotSpace != PivotSpaces.Canvas || importer.pivotAlignment != SpriteAlignment.BottomCenter)
            {
                Debug.LogError("[PhysFun] soldier.aseprite is not pivoted on the canvas bottom centre, so his " +
                               "frames cannot be put back where they were drawn. Run PhysFun/Enemies/Build Soldier first.");
                return;
            }

            var sprite = IdleSprite();
            if (!sprite)
            {
                Debug.LogError($"[PhysFun] {Source} has no sprites to cut up.");
                return;
            }

            var canvas = new Vector2Int(Mathf.RoundToInt(importer.canvasSize.x), Mathf.RoundToInt(importer.canvasSize.y));
            var build = CutUp(ReadFrame(sprite, canvas), canvas);
            if (build == null) return;

            var def = NoitaRagdollImporter.Write(build, new NoitaRagdollImporter.Settings
            {
                PixelsPerUnit = PixelsPerUnit,
                LimitAngle = LimitAngle,
                UseLimits = true,
                BuildPrefab = true
            });

            TightenColliders(build, def);
            AttachToEnemy();

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(RagdollPrefabPath);
            if (prefab)
            {
                Selection.activeObject = prefab;
                EditorGUIUtility.PingObject(prefab);
            }

            Debug.Log($"[PhysFun] Soldier ragdoll built: {def.parts.Count} parts, {RagdollPrefabPath}", prefab);
        }

        // ------------------------------------------------------------------ the frame

        /// <summary>The first idle frame — the pose he stands in, and the one the pieces are cut from.</summary>
        private static Sprite IdleSprite()
        {
            var sprites = AssetDatabase.LoadAllAssetRepresentationsAtPath(Source).OfType<Sprite>().ToArray();
            return sprites.FirstOrDefault(s => s.name == "Frame_0") ?? sprites.FirstOrDefault();
        }

        /// <summary>
        /// The sprite put back on the canvas it was drawn on: top-down, one entry per canvas pixel.
        ///
        /// The importer trims every frame down to its own ink and carries the alignment in the
        /// pivot instead, so the pivot is where the canvas anchor ended up inside this frame —
        /// which is all it takes to work out where the trimmed image sat.
        /// </summary>
        private static Color32[] ReadFrame(Sprite sprite, Vector2Int canvas)
        {
            var tex = Readable(sprite.texture);
            var pixels = tex.GetPixels32();
            int texW = tex.width;

            var rect = sprite.rect;
            int rx = Mathf.RoundToInt(rect.x), ry = Mathf.RoundToInt(rect.y);
            int rw = Mathf.RoundToInt(rect.width), rh = Mathf.RoundToInt(rect.height);

            // Bottom-left corner of the trimmed image in canvas pixels, y up.
            var corner = new Vector2Int(
                Mathf.RoundToInt(PivotAnchor.x * canvas.x - sprite.pivot.x),
                Mathf.RoundToInt(PivotAnchor.y * canvas.y - sprite.pivot.y));

            var frame = new Color32[canvas.x * canvas.y];
            for (int y = 0; y < rh; y++)
            for (int x = 0; x < rw; x++)
            {
                var c = pixels[(ry + y) * texW + rx + x];
                if (c.a == 0) continue;

                int cx = corner.x + x;
                int cy = canvas.y - 1 - (corner.y + y);
                if (cx < 0 || cy < 0 || cx >= canvas.x || cy >= canvas.y) continue;

                frame[cy * canvas.x + cx] = c;
            }

            Object.DestroyImmediate(tex);
            return frame;
        }

        /// <summary>
        /// A copy that can be read back. Imported sprite textures come in unreadable, and the
        /// alternative — making the soldier readable just to look at him once here — is a setting
        /// the game would then ship with.
        ///
        /// The target is sRGB, not linear: the project renders in linear space, so sampling the
        /// sprite converts its bytes and only an sRGB target converts them back. Getting this
        /// wrong does not fail, it just quietly repaints the corpse in different colours.
        /// </summary>
        private static Texture2D Readable(Texture source)
        {
            var rt = RenderTexture.GetTemporary(source.width, source.height, 0,
                RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var previous = RenderTexture.active;

            Graphics.Blit(source, rt);
            RenderTexture.active = rt;

            var copy = new Texture2D(source.width, source.height, TextureFormat.RGBA32, false);
            copy.ReadPixels(new Rect(0f, 0f, rt.width, rt.height), 0, 0);
            copy.Apply();

            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(rt);
            return copy;
        }

        // ------------------------------------------------------------------ the pieces

        /// <summary>
        /// Hand every opaque pixel to the block it falls in. What comes out is the same shape the
        /// Noita importer builds for a creature that arrived with its limbs already separate.
        /// </summary>
        private static RagdollBuild CutUp(Color32[] frame, Vector2Int canvas)
        {
            var build = new RagdollBuild
            {
                Creature = Creature,
                FrameW = canvas.x,
                FrameH = canvas.y,
                // The spawn point is the soldier's own origin: the pivot the art is drawn around.
                OriginPx = new Vector2(PivotAnchor.x * canvas.x, (1f - PivotAnchor.y) * canvas.y),
                DefaultAnim = Anim
            };

            foreach (var cut in Cuts)
            {
                var part = new PartBuild
                {
                    Name = cut.Name,
                    SourceOrder = cut.Order,
                    W = canvas.x,
                    H = canvas.y,
                    Pixels = new Color32[frame.Length],
                    Parent = cut.Parent
                };

                int minX = int.MaxValue, minY = int.MaxValue, maxX = int.MinValue, maxY = int.MinValue;
                for (int y = 0; y < canvas.y; y++)
                for (int x = 0; x < canvas.x; x++)
                {
                    if (!cut.Contains(x, y)) continue;

                    int i = y * canvas.x + x;
                    if (frame[i].a == 0) continue;

                    part.Pixels[i] = frame[i];
                    part.Solid.Add(new Vector2Int(x, y));
                    if (x < minX) minX = x;
                    if (y < minY) minY = y;
                    if (x > maxX) maxX = x;
                    if (y > maxY) maxY = y;
                }

                if (part.Solid.Count == 0)
                {
                    Debug.LogError($"[PhysFun] Nothing is drawn where the soldier's {cut.Name} should be. " +
                                   $"The art moved on the canvas, so the cuts in " +
                                   $"{nameof(SoldierRagdollBuilder)} have to move with it.");
                    return null;
                }

                part.Bounds = new RectInt(minX, minY, maxX - minX + 1, maxY - minY + 1);
                part.PivotPx = new Vector2(minX + part.Bounds.width * 0.5f - 0.5f,
                                           minY + part.Bounds.height * 0.5f - 0.5f);
                part.AnchorPx = cut.Parent < 0 ? part.PivotPx : cut.Anchor;

                build.Parts.Add(part);
            }

            build.Poses.Add(RestPose(build));
            return build;
        }

        /// <summary>
        /// The one pose there is: the idle frame the pieces were cut from, each of them where it
        /// was drawn. The walk and shoot frames are the same body redrawn rather than these pieces
        /// moved, so there is nothing to read a second pose off — <see cref="Ragdoll"/> falls back
        /// to this one whatever frame the soldier dies on.
        /// </summary>
        private static PoseBuild RestPose(RagdollBuild build)
        {
            var pose = new PoseBuild
            {
                Anim = Anim,
                Frame = 0,
                Pos = new Vector2[build.Parts.Count],
                Rot = new float[build.Parts.Count]
            };

            for (int i = 0; i < build.Parts.Count; i++) pose.Pos[i] = build.Parts[i].PivotPx;
            return pose;
        }

        /// <summary>
        /// The importer asks Unity for a collider off each part's sprite, and at this size what
        /// comes back is the sprite's whole rect, padding and all — a leg two pixels wide ends up
        /// inside a hull wider than the body. Replace every one with the box its own opaque pixels
        /// fill, which for a limb is the limb.
        /// </summary>
        private static void TightenColliders(RagdollBuild build, RagdollDefinition def)
        {
            var root = PrefabUtility.LoadPrefabContents(RagdollPrefabPath);
            try
            {
                for (int i = 0; i < def.parts.Count; i++)
                {
                    var piece = root.transform.Find(def.parts[i].name);
                    if (!piece) continue;

                    var poly = piece.GetComponent<PolygonCollider2D>();
                    if (!poly) continue;

                    var bounds = build.Parts[i].Bounds;
                    var pivot = build.Parts[i].PivotPx;

                    // Pixel edges, not centres: the box has to cover the outermost pixels whole.
                    var tl = def.PixelToLocalDelta(new Vector2(bounds.xMin - 0.5f - pivot.x, bounds.yMin - 0.5f - pivot.y));
                    var br = def.PixelToLocalDelta(new Vector2(bounds.xMax - 0.5f - pivot.x, bounds.yMax - 0.5f - pivot.y));

                    poly.pathCount = 1;
                    poly.SetPath(0, new[]
                    {
                        new Vector2(tl.x, br.y),
                        new Vector2(br.x, br.y),
                        new Vector2(br.x, tl.y),
                        new Vector2(tl.x, tl.y)
                    });

                    MassRecalculator.SetMass(def.parts[i].sprite, piece.GetComponent<Rigidbody2D>(), poly);
                }

                PrefabUtility.SaveAsPrefabAsset(root, RagdollPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        // ------------------------------------------------------------------ the live soldier

        private static void AttachToEnemy()
        {
            if (!AssetDatabase.LoadAssetAtPath<GameObject>(EnemyPrefabPath))
            {
                Debug.LogWarning($"[PhysFun] No soldier at {EnemyPrefabPath} to hand the corpse to. " +
                                 "Run PhysFun/Enemies/Build Soldier.");
                return;
            }

            var root = PrefabUtility.LoadPrefabContents(EnemyPrefabPath);
            try
            {
                if (WireSpawner(root)) PrefabUtility.SaveAsPrefabAsset(root, EnemyPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        /// <summary>
        /// Point a soldier at his corpse. Called on the built prefab from here and on the fresh one
        /// from <see cref="SoldierBuilder"/>, so rebuilding either half keeps the two tied
        /// together. Does nothing while the corpse has not been built yet.
        /// </summary>
        public static bool WireSpawner(GameObject root)
        {
            var ragdoll = AssetDatabase.LoadAssetAtPath<GameObject>(RagdollPrefabPath);
            if (!ragdoll) return false;

            var spawner = root.GetComponent<RagdollSpawner>();
            if (!spawner) spawner = root.AddComponent<RagdollSpawner>();

            var so = new SerializedObject(spawner);
            so.FindProperty("ragdollPrefab").objectReferenceValue = ragdoll;

            // The animated renderer, not the root: it carries the frame he died on and the flip.
            var renderer = root.GetComponentInChildren<SpriteRenderer>(true);
            if (renderer)
            {
                so.FindProperty("poseSource").objectReferenceValue = renderer;
                so.FindProperty("facingSource").objectReferenceValue = renderer.transform;
            }

            so.FindProperty("body").objectReferenceValue = root.GetComponent<Rigidbody2D>();
            so.ApplyModifiedPropertiesWithoutUndo();
            return true;
        }
    }
}
