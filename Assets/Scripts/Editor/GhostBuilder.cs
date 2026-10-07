using System.Linq;
using Common;
using Enemy;
using UnityEditor;
using UnityEditor.U2D.Aseprite;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// The eight ghosts (Tools/gen_ghosts.py writes their .aseprite files) as prefabs that fly
    /// and hunt. Same shape of build as <see cref="SoldierBuilder"/> - a controller with one
    /// state per tag reachable from Any State, and a prefab whose art hangs off View - but the
    /// body is a flier: no gravity, a capsule round the core of the body rather than round the
    /// whole sprite (the tendrils and trails are not solid), the root moved into that core, a
    /// <see cref="GhostController"/> instead of a patrol, and health that does not bleed.
    ///
    /// No corpse: ghosts play Death and go. Rebuilding keeps the controller and prefab guids.
    /// </summary>
    public static class GhostBuilder
    {
        private const string Sprites = "Assets/Sprites/Enemies/Ghosts";
        private const string PrefabDir = "Assets/Resources/Prefabs/Enemies/Ghosts";
        private const string Bolt = "Assets/Resources/Prefabs/Enemies/EnemyBolt.prefab";
        private const int EnemyLayer = 8;

        private static readonly (string Trigger, string Tag)[] States =
        {
            ("Idle", "Idle"),
            ("Walk", "Walk"),
            ("Shoot", "Shoot"),
            ("Death", "Death"),
        };

        private sealed class Ghost
        {
            public string Name;
            public string File;
            public int MaxHealth = 18;
            public float FlySpeed = 2.2f;
            public GhostController.AttackKind Attack = GhostController.AttackKind.Lunge;
            public float Range = 1.2f;
            public int Damage = 8;
            /// <summary>Bolt colour for the spitters; ignored for lungers.</summary>
            public Color Magic = Color.white;
            /// <summary>Hull size as a share of the body's core (see SoldierBuilder.CoreRect).</summary>
            public float Core = 0.9f;
            /// <summary>
            /// Take every row, not only the wide ones - for a ghost that is several bodies, where
            /// no single row is the body.
            /// </summary>
            public bool Whole;
        }

        private static readonly Ghost[] All =
        {
            new() { Name = "Phantom", File = "ghost_phantom.aseprite", MaxHealth = 18, FlySpeed = 2.4f, Damage = 8 },
            new()
            {
                Name = "Howler", File = "ghost_howler.aseprite", MaxHealth = 22, FlySpeed = 1.8f,
                Attack = GhostController.AttackKind.Bolt, Range = 6f, Damage = 6, Magic = new Color(1f, 0.35f, 0.3f),
            },
            new() { Name = "Skulls", File = "ghost_skulls.aseprite", MaxHealth = 12, FlySpeed = 3.2f, Damage = 6, Whole = true },
            new() { Name = "Maw", File = "ghost_maw.aseprite", MaxHealth = 30, FlySpeed = 1.6f, Damage = 12, Range = 1.4f },
            new() { Name = "Weaver", File = "ghost_weaver.aseprite", MaxHealth = 20, FlySpeed = 2.2f, Damage = 9 },
            new()
            {
                Name = "Watcher", File = "ghost_watcher.aseprite", MaxHealth = 20, FlySpeed = 1.5f,
                Attack = GhostController.AttackKind.Bolt, Range = 8f, Damage = 7, Magic = new Color(1f, 0.25f, 0.2f),
            },
            new() { Name = "Stinger", File = "ghost_stinger.aseprite", MaxHealth = 14, FlySpeed = 2f, Damage = 7 },
            new() { Name = "Leech", File = "ghost_leech.aseprite", MaxHealth = 16, FlySpeed = 2.8f, Damage = 8 },
        };

        [MenuItem("PhysFun/Enemies/Build Ghosts (Phantom, Howler, Skulls, Maw, Weaver, Watcher, Stinger, Leech)",
            false, 205)]
        private static void BuildAll()
        {
            GameObject last = null;
            foreach (var g in All)
            {
                var prefab = Build(g);
                if (prefab) last = prefab;
            }

            if (!last) return;
            Selection.activeObject = last;
            EditorGUIUtility.PingObject(last);
        }

        private static GameObject Build(Ghost g)
        {
            string source = $"{Sprites}/{g.File}";
            var importer = AssetImporter.GetAtPath(source) as AsepriteImporter;
            if (!importer)
            {
                Debug.LogError($"[PhysFun] No Aseprite asset at {source}. Run Tools/gen_ghosts.py first.");
                return null;
            }

            SoldierBuilder.FixImportSettings(importer);

            var clips = AssetDatabase.LoadAllAssetRepresentationsAtPath(source)
                .OfType<AnimationClip>()
                .ToDictionary(c => c.name);
            var missing = States.Where(s => !clips.ContainsKey(s.Tag)).Select(s => s.Tag).ToArray();
            if (missing.Length > 0)
            {
                Debug.LogError($"[PhysFun] {source} has no tag(s) named {string.Join(", ", missing)}.");
                return null;
            }

            var spec = new SoldierBuilder.Spec { Name = g.Name, Source = source, States = States };
            var controller = SoldierBuilder.BuildController(spec, clips);
            var prefab = BuildPrefab(g, source, controller);

            Debug.Log($"[PhysFun] {g.Name} built: {PrefabDir}/{g.Name}.prefab", prefab);
            return prefab;
        }

        private static GameObject BuildPrefab(Ghost g, string source, RuntimeAnimatorController controller)
        {
            SoldierBuilder.EnsureFolder(PrefabDir);

            var root = new GameObject(g.Name) { layer = EnemyLayer };

            var view = new GameObject("View") { layer = EnemyLayer };
            view.transform.SetParent(root.transform, false);

            var renderer = view.AddComponent<SpriteRenderer>();
            renderer.sprite = SoldierBuilder.FirstSprite(source);

            var animator = view.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;

            // The root sits in the middle of the body, not at the canvas feet: a flier has no
            // ground to stand on, and the path search tests clearance around the root.
            var core = SoldierBuilder.CoreRect(source, fullHeight: g.Whole);
            if (core.width <= 0f) core = new Rect(-0.3f, 0.2f, 0.6f, 0.6f);
            view.transform.localPosition = -core.center;

            var body = root.AddComponent<Rigidbody2D>();
            body.gravityScale = 0f;
            body.constraints = RigidbodyConstraints2D.FreezeRotation;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;

            // The core only: the trails and strands are drawn, not solid. A capsule along its
            // longer side, so the leech is long and the howler tall.
            var hull = root.AddComponent<CapsuleCollider2D>();
            hull.direction = core.width > core.height ? CapsuleDirection2D.Horizontal : CapsuleDirection2D.Vertical;
            hull.size = core.size * g.Core;
            hull.offset = Vector2.zero;

            var ghost = root.AddComponent<GhostController>();
            var so = new SerializedObject(ghost);
            so.FindProperty("_body").objectReferenceValue = view.transform;
            so.FindProperty("_rb").objectReferenceValue = body;
            so.FindProperty("_animator").objectReferenceValue = animator;
            so.FindProperty("_hull").objectReferenceValue = hull;
            so.FindProperty("_flySpeed").floatValue = g.FlySpeed;
            so.FindProperty("_attack").enumValueIndex = (int)g.Attack;
            so.FindProperty("_attackRange").floatValue = g.Range;
            so.FindProperty("_damage").intValue = g.Damage;
            if (g.Attack == GhostController.AttackKind.Bolt)
            {
                var bolt = AssetDatabase.LoadAssetAtPath<GameObject>(Bolt);
                so.FindProperty("_bolt").objectReferenceValue = bolt ? bolt.GetComponent<Projectile>() : null;
                so.FindProperty("_boltColor").colorValue = g.Magic;
            }
            so.ApplyModifiedPropertiesWithoutUndo();

            var health = root.AddComponent<Damageable>();
            var hs = new SerializedObject(health);
            hs.FindProperty("maxHealth").intValue = g.MaxHealth;
            hs.FindProperty("targetLayers").intValue = 1 << 0;
            hs.FindProperty("deathKick").floatValue = 0.05f;
            hs.FindProperty("bleeds").boolValue = false;
            hs.ApplyModifiedPropertiesWithoutUndo();

            var prefab = PrefabUtility.SaveAsPrefabAsset(root, $"{PrefabDir}/{g.Name}.prefab");
            Object.DestroyImmediate(root);
            return prefab;
        }
    }
}
