using UnityEditor;
using UnityEngine;
using Cut = global::Editor.SoldierRagdollBuilder.Cut;

namespace Editor
{
    /// <summary>
    /// Walking enemies drawn by hand: one row per enemy, each built by
    /// <see cref="SoldierBuilder"/> (controller and prefab) and then
    /// <see cref="SoldierRagdollBuilder"/> (the corpse, which it also hands to the prefab).
    ///
    /// The cuts are read off each figure's first Idle frame on its own canvas, top-down. A robe
    /// below the belt is two legs, so the corpse folds instead of landing on a slab. Whatever the
    /// cuts leave unclaimed is dropped from the corpse. Redraw a figure and its rows have to follow.
    ///
    /// The enemies built before this (the wizards, the monsters, the soldier) are finished assets
    /// and their rows were removed; the hooded mages stay as the worked example. Tools/ENEMIES.md
    /// is the recipe for the next one.
    /// </summary>
    public static class CastBuilder
    {
        private const string Sprites = "Assets/Sprites/Enemies";
        private const string Prefabs = "Assets/Resources/Prefabs/Enemies";
        private const string Bolt = "Assets/Resources/Prefabs/Enemies/EnemyBolt.prefab";

        private static readonly (string Trigger, string Tag)[] States =
        {
            ("Idle", "Idle"),
            ("Walk", "Walk"),
            ("Shoot", "Shoot"),
        };

        private sealed class Member
        {
            public string Name;       // prefab, controller folder
            public string File;       // .aseprite under Sprites
            public string Creature;   // ragdoll folder under Assets/Resources/Ragdolls
            public Cut[] Cuts;
            public int MaxHealth = 20;
            public float WalkSpeed = 1.5f;

            /// <summary>Casters throw the shared enemy bolt, tinted their own colour. Null for none.</summary>
            public Color? Magic;
            public int BoltDamage = 6;
            public Vector2 CastOffset = new(0.4f, 0.5f);
        }

        /// <summary>
        /// The five hooded mages redrawn from the user's concept paintings. They cast: the bolt
        /// leaves from where the flare blooms on their Shoot frames.
        /// Their canvases are bigger than the 20x22 cast and their feet sit on the bottom row.
        ///
        /// Every number here comes out of <c>python Tools/gen_mages.py --cuts</c>, which reads the
        /// same Frame_0 the corpse is cut from: head above the neck, the casting arm in its box,
        /// two legs below the hem split between the hips, the torso whatever is left. Change a
        /// grid in hooded_mages.py, rerun that, and paste its rows back over these.
        /// </summary>
        private static readonly Member[] HoodedMages =
        {
            new()
            {
                Name = "Crimson", File = "wiz_crimson.aseprite", Creature = "crimson",
                MaxHealth = 24, WalkSpeed = 1.3f, Magic = new Color(1f, 0.25f, 0.28f), BoltDamage = 7,
                CastOffset = new Vector2(0.475f, 0.475f),
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2, new RectInt(0, 16, 18, 6)),
                    new("leg_l", 0, new Vector2(8.5f, 21.5f), 1, new RectInt(0, 22, 12, 7)),
                    new("leg_r", 0, new Vector2(14.5f, 21.5f), 0, new RectInt(12, 22, 18, 7)),
                    new("head", 0, new Vector2(10.5f, 15.5f), 4, new RectInt(0, 0, 30, 16)),
                    new("arm_r", 0, new Vector2(18f, 19f), 3, new RectInt(18, 16, 12, 6)),
                },
            },
            new()
            {
                Name = "Bogcap", File = "wiz_bogcap.aseprite", Creature = "bogcap",
                MaxHealth = 22, WalkSpeed = 1f, Magic = new Color(0.75f, 0.95f, 0.35f), BoltDamage = 6,
                CastOffset = new Vector2(0.325f, 0.225f),
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2, new RectInt(0, 15, 19, 5)),
                    new("leg_l", 0, new Vector2(11.5f, 19.5f), 1, new RectInt(0, 20, 13, 8)),
                    new("leg_r", 0, new Vector2(14.5f, 19.5f), 0, new RectInt(13, 20, 17, 8)),
                    new("head", 0, new Vector2(13f, 14.5f), 4, new RectInt(0, 0, 30, 15)),
                    new("arm_r", 0, new Vector2(19f, 16f), 3, new RectInt(19, 15, 11, 5)),
                },
            },
            new()
            {
                Name = "Maskwraith", File = "wiz_maskwraith.aseprite", Creature = "maskwraith",
                MaxHealth = 28, WalkSpeed = 1.2f, Magic = new Color(0.75f, 0.45f, 0.85f), BoltDamage = 8,
                CastOffset = new Vector2(0.525f, 0.625f),
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2,
                        new RectInt(0, 13, 32, 1), new RectInt(0, 14, 19, 5), new RectInt(0, 19, 32, 2)),
                    new("leg_l", 0, new Vector2(10.5f, 20.5f), 1, new RectInt(0, 21, 13, 8)),
                    new("leg_r", 0, new Vector2(14.5f, 20.5f), 0, new RectInt(13, 21, 19, 8)),
                    new("head", 0, new Vector2(12.5f, 12.5f), 4, new RectInt(0, 0, 32, 13)),
                    new("arm_r", 0, new Vector2(19f, 16f), 3, new RectInt(19, 14, 13, 5)),
                },
            },
            new()
            {
                Name = "Deepminer", File = "wiz_deepminer.aseprite", Creature = "deepminer",
                MaxHealth = 26, WalkSpeed = 1.2f, Magic = new Color(1f, 0.6f, 0.2f), BoltDamage = 7,
                CastOffset = new Vector2(0.375f, 0.425f),
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2, new RectInt(0, 14, 15, 4)),
                    new("leg_l", 0, new Vector2(8.5f, 17.5f), 1, new RectInt(0, 18, 11, 7)),
                    new("leg_r", 0, new Vector2(12.5f, 17.5f), 0, new RectInt(11, 18, 19, 7)),
                    new("head", 0, new Vector2(10.5f, 13.5f), 4, new RectInt(0, 0, 30, 14)),
                    new("arm_r", 0, new Vector2(15f, 16f), 3, new RectInt(15, 14, 15, 4)),
                },
            },
            new()
            {
                Name = "Goldhood", File = "wiz_goldhood.aseprite", Creature = "goldhood",
                MaxHealth = 22, WalkSpeed = 1.4f, Magic = new Color(1f, 0.85f, 0.4f), BoltDamage = 6,
                CastOffset = new Vector2(0.45f, 0.375f),
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2, new RectInt(0, 16, 29, 1), new RectInt(0, 17, 16, 4)),
                    new("leg_l", 0, new Vector2(8.5f, 20.5f), 1, new RectInt(0, 21, 11, 8)),
                    new("leg_r", 0, new Vector2(12.5f, 20.5f), 0, new RectInt(11, 21, 18, 8)),
                    new("head", 0, new Vector2(10f, 15.5f), 4, new RectInt(0, 0, 29, 16)),
                    new("arm_r", 0, new Vector2(16f, 18f), 3, new RectInt(16, 17, 13, 4)),
                },
            },
        };

        [MenuItem("PhysFun/Enemies/Build Hooded Mages (Crimson, Bogcap, Maskwraith, Deepminer, Goldhood)", false, 204)]
        private static void BuildHoodedMages() => Build(HoodedMages);

        private static void Build(Member[] members)
        {
            GameObject last = null;
            foreach (var m in members)
            {
                var corpse = new SoldierRagdollBuilder.Spec
                {
                    Source = $"{Sprites}/{m.File}",
                    Creature = m.Creature,
                    EnemyPrefabPath = $"{Prefabs}/{m.Name}.prefab",
                    Cuts = m.Cuts,
                };

                var enemy = new SoldierBuilder.Spec
                {
                    Name = m.Name,
                    Source = corpse.Source,
                    States = States,
                    MaxHealth = m.MaxHealth,
                    WalkSpeed = m.WalkSpeed,
                    RagdollPrefabPath = corpse.RagdollPrefabPath,
                    BoltPrefabPath = m.Magic.HasValue ? Bolt : null,
                    BoltColor = m.Magic ?? Color.white,
                    BoltDamage = m.BoltDamage,
                    CastOffset = m.CastOffset,
                };

                // Enemy first: it fixes the import settings the corpse reads the frame through.
                var prefab = SoldierBuilder.Build(enemy);
                if (!prefab) continue;

                SoldierRagdollBuilder.Build(corpse);
                last = prefab;
            }

            if (!last) return;
            Selection.activeObject = last;
            EditorGUIUtility.PingObject(last);
        }
    }
}
