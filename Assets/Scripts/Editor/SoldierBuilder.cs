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
    /// What differs from one enemy to the next is a <see cref="Spec"/>. The menu item builds the
    /// wizard; <see cref="CastBuilder"/> holds the specs for the rest of the hand-drawn cast.
    ///
    /// One thing the art does not carry yet is a shot: the importer only turns Aseprite user data
    /// into animation events, and there is none on the Shoot frames, so nothing calls
    /// RegularEnemyController.Shoot(). Tag a frame in Aseprite when the muzzle should flash.
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

            public string ControllerDir => $"Assets/Resources/Animations/Enemies/{Name}";
            public string ControllerPath => $"{ControllerDir}/{Name}Animator.controller";
            public string PrefabPath => $"{PrefabDir}/{Name}.prefab";
        }

        public static readonly Spec Wizard = new()
        {
            Name = "Wizard",
            Source = "Assets/Sprites/Enemies/wizard.aseprite",
            States = new[] { ("Idle", "Idle"), ("Walk", "Walk"), ("Shoot", "Attack") },
            RagdollPrefabPath = SoldierRagdollBuilder.RagdollPrefabPath,
        };

        [MenuItem("PhysFun/Enemies/Build Soldier", false, 200)]
        private static void BuildMenu()
        {
            var prefab = Build(Wizard);
            if (!prefab) return;

            Selection.activeObject = prefab;
            EditorGUIUtility.PingObject(prefab);
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
        private static void FixImportSettings(AsepriteImporter importer)
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
        private static AnimatorController BuildController(Spec spec, Dictionary<string, AnimationClip> clips)
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

            var hull = root.AddComponent<CapsuleCollider2D>();
            hull.direction = CapsuleDirection2D.Vertical;
            hull.size = new Vector2(bounds.size.x * 0.9f, bounds.size.y);
            hull.offset = bounds.center;

            WireController(root.AddComponent<RegularEnemyController>(), view.transform, body, animator, eye.transform,
                spec.WalkSpeed);
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
        private static Sprite FirstSprite(string source)
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

        /// <summary>Hurt by the same things as the shotgunner: whatever the world throws.</summary>
        private static void WireHealth(Damageable damageable, int maxHealth)
        {
            var so = new SerializedObject(damageable);
            so.FindProperty("maxHealth").intValue = maxHealth;
            so.FindProperty("targetLayers").intValue = 1 << 0;
            so.FindProperty("deathKick").floatValue = 0.05f;
            so.ApplyModifiedPropertiesWithoutUndo();
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
