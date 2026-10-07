using System.Collections.Generic;
using System.Linq;
using Common;
using Enemy;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.U2D.Aseprite;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Turns a soldier-shaped .aseprite into something that can stand in a scene.
    ///
    /// The .aseprite is the whole source: its tags are the states and the importer bakes them into
    /// clips, so the only things missing are the wiring — a controller whose triggers match what
    /// <see cref="RegularEnemyController"/> fires, and a prefab with a body, a hull and health.
    /// Both are built here rather than by hand, because both are derived: the clips are named by
    /// the tags and the hull is the sprite's own bounds. Re-run it whenever the art changes and it
    /// overwrites what it made last time, keeping every reference to the prefab intact.
    ///
    /// What differs from one enemy to the next is a <see cref="Spec"/>; <see cref="CastBuilder"/>
    /// holds them and has the menu items. Tools/ENEMIES.md walks through adding one.
    /// </summary>
    public static class SoldierBuilder
    {
        private const string PrefabDir = "Assets/Resources/Prefabs/Enemies";

        /// <summary>The pixel scale the rest of the cast is drawn at. 18px tall becomes 0.9 units.</summary>
        private const float PixelsPerUnit = 20f;

        private const int EnemyLayer = 8;

        /// <summary>What the eye is allowed to be stopped by: the world, and the player himself.</summary>
        private const int SightMask = (1 << 0) | (1 << 7);

        /// <summary>Everything that tells one enemy apart from another at build time.</summary>
        public sealed class Spec
        {
            /// <summary>Prefab name, root object name, and the folder its controller lives in.</summary>
            public string Name;

            /// <summary>The .aseprite the frames, tags and clips come from.</summary>
            public string Source;

            /// <summary>
            /// The trigger <see cref="RegularEnemyController"/> fires, and the .aseprite tag whose clip
            /// plays for it. Usually the same word; the wizard calls his third one Attack, because that
            /// is what it looks like, while the trigger is still Shoot.
            /// </summary>
            public (string Trigger, string Tag)[] States;

            public int MaxHealth = 20;
            public float WalkSpeed = 1.5f;

            /// <summary>The corpse to hand him, if it has been built yet. Null for none.</summary>
            public string RagdollPrefabPath;

            /// <summary>
            /// A bolt he throws at the player while he can see them - the mages' magic. Null for
            /// none, which leaves the controller's cast off.
            /// </summary>
            public string BoltPrefabPath;
            public Color BoltColor = Color.white;
            public int BoltDamage = 6;
            /// <summary>Where the bolt leaves from, from the feet, facing right.</summary>
            public Vector2 CastOffset = new(0.4f, 0.5f);

            public string ControllerDir => $"Assets/Resources/Animations/Enemies/{Name}";
            public string ControllerPath => $"{ControllerDir}/{Name}Animator.controller";
            public string PrefabPath => $"{PrefabDir}/{Name}.prefab";
        }

        /// <summary>Controller and prefab for one enemy. Returns null, having said why, when the art is not there.</summary>
        public static GameObject Build(Spec spec)
        {
            var importer = AssetImporter.GetAtPath(spec.Source) as AsepriteImporter;
            if (!importer)
            {
                Debug.LogError($"[PhysFun] No Aseprite asset at {spec.Source}.");
                return null;
            }

            FixImportSettings(importer);

            var clips = AssetDatabase.LoadAllAssetRepresentationsAtPath(spec.Source)
                .OfType<AnimationClip>()
                .ToDictionary(c => c.name);

            var missing = spec.States.Where(s => !clips.ContainsKey(s.Tag)).Select(s => s.Tag).ToArray();
            if (missing.Length > 0)
            {
                Debug.LogError($"[PhysFun] {spec.Source} has no tag(s) named {string.Join(", ", missing)}. " +
                               "The controller needs one tag per state.");
                return null;
            }

            var controller = BuildController(spec, clips);
            var prefab = BuildPrefab(spec, controller);

            Debug.Log($"[PhysFun] {spec.Name} built: {spec.PrefabPath}", prefab);
            return prefab;
        }

        /// <summary>
        /// The importer's defaults are for a sprite looked at on its own, not one that has to
        /// stand next to the others: 100 pixels per unit would make him thumbnail-sized, and the
        /// model prefab it offers is a second, rival soldier with none of the physics on it.
        /// </summary>
        internal static void FixImportSettings(AsepriteImporter importer)
        {
            bool dirty = false;

            void Set<T>(T current, T wanted, System.Action<T> apply)
            {
                if (EqualityComparer<T>.Default.Equals(current, wanted)) return;
                apply(wanted);
                dirty = true;
            }

            Set(importer.spritePixelsPerUnit, PixelsPerUnit, v => importer.spritePixelsPerUnit = v);
            Set(importer.filterMode, FilterMode.Point, v => importer.filterMode = v);
            Set(importer.mipmapEnabled, false, v => importer.mipmapEnabled = v);
            Set(importer.generateAnimationClips, true, v => importer.generateAnimationClips = v);
            Set(importer.generateModelPrefab, false, v => importer.generateModelPrefab = v);
            Set(importer.pivotAlignment, SpriteAlignment.BottomCenter, v => importer.pivotAlignment = v);
            Set(importer.pivotSpace, PivotSpaces.Canvas, v => importer.pivotSpace = v);

            // Compression is left alone: the Aseprite importer already defaults to uncompressed,
            // which is the only thing pixel art can be shown at without smearing.

            if (dirty) importer.SaveAndReimport();
        }

        // ------------------------------------------------------------------ controller

        /// <summary>
        /// One state per tag, all of them reachable from Any State, because the controller is not
        /// the one deciding anything — <see cref="RegularEnemyController"/> is, and it says so by
        /// firing a trigger. Transitions are instant: at three states there is nothing to blend.
        ///
        /// An existing controller is emptied and refilled rather than deleted and remade: deleting
        /// it hands the rebuilt one a new guid, and anything already pointing at the old one — an
        /// enemy standing in an open scene, most of all — is left holding nothing, which shows up
        /// in play mode as "Animator is not playing an AnimatorController".
        /// </summary>
        internal static AnimatorController BuildController(Spec spec, Dictionary<string, AnimationClip> clips)
        {
            EnsureFolder(spec.ControllerDir);

            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(spec.ControllerPath);
            if (controller) Empty(controller);
            else controller = AnimatorController.CreateAnimatorControllerAtPath(spec.ControllerPath);

            var machine = controller.layers[0].stateMachine;

            // Nothing plays until the first trigger lands, so he does not walk on frame one.
            var empty = machine.AddState("Empty");
            machine.defaultState = empty;

            foreach (var (trigger, tag) in spec.States)
            {
                controller.AddParameter(trigger, AnimatorControllerParameterType.Trigger);

                var node = machine.AddState(trigger);
                node.motion = clips[tag];

                var transition = machine.AddAnyStateTransition(node);
                transition.AddCondition(AnimatorConditionMode.If, 0f, trigger);
                transition.hasExitTime = false;
                transition.duration = 0f;
                transition.canTransitionToSelf = false;
            }

            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();
            return controller;
        }

        /// <summary>Everything out, guid kept: what is left is the same asset, ready to be refilled.</summary>
        private static void Empty(AnimatorController controller)
        {
            while (controller.parameters.Length > 0) controller.RemoveParameter(0);

            var machine = controller.layers[0].stateMachine;
            foreach (var transition in machine.anyStateTransitions.ToArray())
                machine.RemoveAnyStateTransition(transition);
            foreach (var state in machine.states.ToArray())
                machine.RemoveState(state.state);
        }

        // ------------------------------------------------------------------ prefab

        /// <summary>
        /// Root carries everything physical; the art hangs off it in View, which is what gets
        /// flipped and what the generated clips drive — they bind the sprite to whatever object
        /// the Animator sits on, so the Animator has to live with the renderer, not with the body.
        /// </summary>
        private static GameObject BuildPrefab(Spec spec, AnimatorController controller)
        {
            EnsureFolder(PrefabDir);

            var root = new GameObject(spec.Name) { layer = EnemyLayer };

            var view = new GameObject("View") { layer = EnemyLayer };
            view.transform.SetParent(root.transform, false);

            var renderer = view.AddComponent<SpriteRenderer>();
            renderer.sprite = FirstSprite(spec.Source);

            var animator = view.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;

            // The sprite's own extents, so the hull fits the art rather than a guess at it.
            var bounds = renderer.sprite ? renderer.sprite.bounds : new Bounds(Vector3.zero, Vector3.one);

            var eye = new GameObject("Eye") { layer = EnemyLayer };
            eye.transform.SetParent(root.transform, false);
            eye.transform.localPosition = new Vector3(bounds.extents.x * 0.5f, bounds.max.y * 0.85f, 0f);

            var groundCheck = new GameObject("GroundCheck") { layer = EnemyLayer };
            groundCheck.transform.SetParent(root.transform, false);
            groundCheck.transform.localPosition = new Vector3(0f, bounds.min.y, 0f);

            var body = root.AddComponent<Rigidbody2D>();
            body.gravityScale = 1f;
            body.constraints = RigidbodyConstraints2D.FreezeRotation;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;

            // The body, not the sprite: a sickle or a reaching claw widens the sprite's bounds,
            // and a hull that wide snags on every doorway the figure itself would fit through.
            var core = CoreRect(spec.Source, fullHeight: true);
            if (core.width <= 0f) core = new Rect(bounds.min, bounds.size);

            var hull = root.AddComponent<CapsuleCollider2D>();
            hull.direction = CapsuleDirection2D.Vertical;
            hull.size = new Vector2(core.width * 0.9f, core.height);
            hull.offset = core.center;

            var brain = root.AddComponent<RegularEnemyController>();
            WireController(brain, view.transform, body, animator, eye.transform, spec.WalkSpeed);
            WireCast(brain, spec);
            WireHealth(root.AddComponent<Damageable>(), spec.MaxHealth);

            // The corpse is a separate build and he stands up fine without one, so this only
            // takes if his ragdoll has already been built.
            SoldierRagdollBuilder.WireSpawner(root, spec.RagdollPrefabPath);

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, spec.PrefabPath);
            Object.DestroyImmediate(root);
            return prefab;
        }

        /// <summary>
        /// The first frame of Idle — what he looks like standing still, and what the hull is
        /// measured against. Sub-assets come back in no particular order, hence the name.
        /// </summary>
        /// <summary>
        /// The solid middle of Frame_0, in local units from the canvas bottom centre (where the
        /// sprite is pivoted): the rows that are at least about half as wide as the widest, and
        /// across them the columns that are mostly ink. Strands, trails, tails and whatever is
        /// held out at arm's length are thin, so they fall out of both; what stays is the body
        /// something should collide with.
        ///
        /// <paramref name="fullHeight"/> keeps every row top to bottom - a walker has to stand
        /// on its feet, and its legs are never the widest thing on it.
        /// </summary>
        internal static Rect CoreRect(string source, bool fullHeight)
        {
            var importer = AssetImporter.GetAtPath(source) as AsepriteImporter;
            var sprite = FirstSprite(source);
            if (!importer || !sprite) return default;

            var canvas = new Vector2Int(Mathf.RoundToInt(importer.canvasSize.x), Mathf.RoundToInt(importer.canvasSize.y));
            var frame = SoldierRagdollBuilder.ReadFrame(sprite, canvas);
            int w = canvas.x, h = canvas.y;

            var rows = new int[h];
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
                if (frame[y * w + x].a > 0) rows[y]++;

            int widest = rows.Max();
            if (widest == 0) return default;

            var cols = new int[w];
            for (int y = 0; y < h; y++)
            {
                if (rows[y] < widest * 0.45f) continue;
                for (int x = 0; x < w; x++)
                    if (frame[y * w + x].a > 0) cols[x]++;
            }

            int deepest = cols.Max();
            int x0 = -1, x1 = -1, y0 = -1, y1 = -1;
            for (int x = 0; x < w; x++)
            {
                if (cols[x] < deepest * 0.35f) continue;
                if (x0 < 0) x0 = x;
                x1 = x;
            }

            for (int y = 0; y < h; y++)
            {
                if (rows[y] == 0 || (!fullHeight && rows[y] < widest * 0.45f)) continue;
                if (y0 < 0) y0 = y;
                y1 = y;
            }

            if (x0 < 0 || y0 < 0) return default;

            // canvas pixels are top-down; local space is y up from the bottom edge
            return Rect.MinMaxRect(
                (x0 - w * 0.5f) / PixelsPerUnit, (h - (y1 + 1)) / PixelsPerUnit,
                (x1 + 1 - w * 0.5f) / PixelsPerUnit, (h - y0) / PixelsPerUnit);
        }

        internal static Sprite FirstSprite(string source)
        {
            var sprites = AssetDatabase.LoadAllAssetRepresentationsAtPath(source).OfType<Sprite>().ToArray();
            return sprites.FirstOrDefault(s => s.name == "Frame_0") ?? sprites.FirstOrDefault();
        }

        private static void WireController(
            RegularEnemyController enemy, Transform view, Rigidbody2D body, Animator animator, Transform eye,
            float walkSpeed)
        {
            var so = new SerializedObject(enemy);
            so.FindProperty("_body").objectReferenceValue = view;
            so.FindProperty("_rb").objectReferenceValue = body;
            so.FindProperty("_animator").objectReferenceValue = animator;
            so.FindProperty("_eye").objectReferenceValue = eye;
            so.FindProperty("walkSpeed").floatValue = walkSpeed;
            so.FindProperty("idleDuration").floatValue = 1.5f;
            so.FindProperty("walkDuration").floatValue = 2.5f;
            so.FindProperty("detectRange").floatValue = 15f;
            so.FindProperty("fovDegrees").floatValue = 130f;
            so.FindProperty("obstacleMask").intValue = SightMask;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void WireCast(RegularEnemyController enemy, Spec spec)
        {
            if (string.IsNullOrEmpty(spec.BoltPrefabPath)) return;

            var bolt = AssetDatabase.LoadAssetAtPath<GameObject>(spec.BoltPrefabPath);
            var projectile = bolt ? bolt.GetComponent<Projectile>() : null;
            if (!projectile)
            {
                Debug.LogWarning($"[PhysFun] {spec.Name}: no Projectile at {spec.BoltPrefabPath}, so he will not cast.");
                return;
            }

            var so = new SerializedObject(enemy);
            so.FindProperty("_bolt").objectReferenceValue = projectile;
            so.FindProperty("_boltColor").colorValue = spec.BoltColor;
            so.FindProperty("_boltDamage").intValue = spec.BoltDamage;
            so.FindProperty("_castOffset").vector2Value = spec.CastOffset;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Hurt by the same things as the shotgunner: whatever the world throws.</summary>
        private static void WireHealth(Damageable damageable, int maxHealth)
        {
            var so = new SerializedObject(damageable);
            so.FindProperty("maxHealth").intValue = maxHealth;
            so.FindProperty("targetLayers").intValue = 1 << 0;
            so.FindProperty("deathKick").floatValue = 0.05f;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        internal static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;

            var parent = System.IO.Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, System.IO.Path.GetFileName(path));
        }
    }
}
