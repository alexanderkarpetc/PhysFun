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
    /// Turns soldier.aseprite into something that can stand in a scene.
    ///
    /// The .aseprite is the whole source: its tags are the states and the importer bakes them into
    /// clips, so the only things missing are the wiring — a controller whose triggers match what
    /// <see cref="RegularEnemyController"/> fires, and a prefab with a body, a hull and health.
    /// Both are built here rather than by hand, because both are derived: the clips are named by
    /// the tags and the hull is the sprite's own bounds. Re-run it whenever the art changes and it
    /// overwrites what it made last time, keeping every reference to the prefab intact.
    ///
    /// The dark soldier was made by pointing this file and <see cref="SoldierRagdollBuilder"/> at
    /// his own .aseprite for one run. His assets are checked in, so both builders are kept on the
    /// one soldier: they are the worked example for the next palette, not a pipeline.
    ///
    /// One thing the art does not carry yet is a shot: the importer only turns Aseprite user data
    /// into animation events, and there is none on the Shoot frames, so nothing calls
    /// RegularEnemyController.Shoot(). Tag a frame in Aseprite when the muzzle should flash.
    /// </summary>
    public static class SoldierBuilder
    {
        private const string Source = "Assets/Sprites/Enemies/wizard.aseprite";
        private const string ControllerDir = "Assets/Resources/Animations/Enemies/Wizard";
        private const string ControllerPath = ControllerDir + "/WizardAnimator.controller";
        private const string PrefabDir = "Assets/Resources/Prefabs/Enemies";
        private const string PrefabPath = PrefabDir + "/Wizard.prefab";

        /// <summary>The pixel scale the rest of the cast is drawn at. 18px tall becomes 0.9 units.</summary>
        private const float PixelsPerUnit = 20f;

        private const int EnemyLayer = 8;

        /// <summary>What the eye is allowed to be stopped by: the world, and the player himself.</summary>
        private const int SightMask = (1 << 0) | (1 << 7);

        /// <summary>
        /// The trigger <see cref="RegularEnemyController"/> fires, and the .aseprite tag whose clip
        /// plays for it. Usually the same word; the wizard calls his third one Attack, because that
        /// is what it looks like, while the trigger is still Shoot.
        /// </summary>
        private static readonly (string Trigger, string Tag)[] States =
        {
            ("Idle", "Idle"),
            ("Walk", "Walk"),
            ("Shoot", "Attack"),
        };

        [MenuItem("PhysFun/Enemies/Build Soldier", false, 200)]
        private static void Build()
        {
            var importer = AssetImporter.GetAtPath(Source) as AsepriteImporter;
            if (!importer)
            {
                Debug.LogError($"[PhysFun] No Aseprite asset at {Source}.");
                return;
            }

            FixImportSettings(importer);

            var clips = AssetDatabase.LoadAllAssetRepresentationsAtPath(Source)
                .OfType<AnimationClip>()
                .ToDictionary(c => c.name);

            var missing = States.Where(s => !clips.ContainsKey(s.Tag)).Select(s => s.Tag).ToArray();
            if (missing.Length > 0)
            {
                Debug.LogError($"[PhysFun] {Source} has no tag(s) named {string.Join(", ", missing)}. " +
                               "The controller needs one tag per state.");
                return;
            }

            var controller = BuildController(clips);
            var prefab = BuildPrefab(controller);

            Selection.activeObject = prefab;
            EditorGUIUtility.PingObject(prefab);
            Debug.Log($"[PhysFun] Soldier built: {PrefabPath}", prefab);
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
        private static AnimatorController BuildController(Dictionary<string, AnimationClip> clips)
        {
            EnsureFolder(ControllerDir);

            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
            if (controller) Empty(controller);
            else controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);

            var machine = controller.layers[0].stateMachine;

            // Nothing plays until the first trigger lands, so he does not walk on frame one.
            var empty = machine.AddState("Empty");
            machine.defaultState = empty;

            foreach (var (trigger, tag) in States)
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
        private static GameObject BuildPrefab(AnimatorController controller)
        {
            EnsureFolder(PrefabDir);

            var root = new GameObject("Wizard") { layer = EnemyLayer };

            var view = new GameObject("View") { layer = EnemyLayer };
            view.transform.SetParent(root.transform, false);

            var renderer = view.AddComponent<SpriteRenderer>();
            renderer.sprite = FirstSprite();

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

            WireController(root.AddComponent<RegularEnemyController>(), view.transform, body, animator, eye.transform);
            WireHealth(root.AddComponent<Damageable>());

            // The corpse is a separate build and he stands up fine without one, so this only
            // takes if PhysFun/Enemies/Build Soldier Ragdoll has already been run.
            SoldierRagdollBuilder.WireSpawner(root);

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            Object.DestroyImmediate(root);
            return prefab;
        }

        /// <summary>
        /// The first frame of Idle — what he looks like standing still, and what the hull is
        /// measured against. Sub-assets come back in no particular order, hence the name.
        /// </summary>
        private static Sprite FirstSprite()
        {
            var sprites = AssetDatabase.LoadAllAssetRepresentationsAtPath(Source).OfType<Sprite>().ToArray();
            return sprites.FirstOrDefault(s => s.name == "Frame_0") ?? sprites.FirstOrDefault();
        }

        private static void WireController(
            RegularEnemyController enemy, Transform view, Rigidbody2D body, Animator animator, Transform eye)
        {
            var so = new SerializedObject(enemy);
            so.FindProperty("_body").objectReferenceValue = view;
            so.FindProperty("_rb").objectReferenceValue = body;
            so.FindProperty("_animator").objectReferenceValue = animator;
            so.FindProperty("_eye").objectReferenceValue = eye;
            so.FindProperty("walkSpeed").floatValue = 1.5f;
            so.FindProperty("idleDuration").floatValue = 1.5f;
            so.FindProperty("walkDuration").floatValue = 2.5f;
            so.FindProperty("detectRange").floatValue = 15f;
            so.FindProperty("fovDegrees").floatValue = 130f;
            so.FindProperty("obstacleMask").intValue = SightMask;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>As tough as the shotgunner, and hurt by the same things: whatever the world throws.</summary>
        private static void WireHealth(Damageable damageable)
        {
            var so = new SerializedObject(damageable);
            so.FindProperty("maxHealth").intValue = 20;
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
