using UnityEditor;
using UnityEngine;
using Cut = global::Editor.SoldierRagdollBuilder.Cut;

namespace Editor
{
    /// <summary>
    /// The hand-drawn cast that came after the soldier: one row per enemy, each built the way the
    /// wizard is — <see cref="SoldierBuilder"/> for the controller and the prefab, then
    /// <see cref="SoldierRagdollBuilder"/> for the corpse, which also hands it to the prefab.
    ///
    /// The cuts are read off each figure's first Idle frame on its own canvas, top-down. Like the
    /// wizard's, a robe below the belt is two legs, so the corpse folds instead of landing on a
    /// slab. Whatever the cuts leave unclaimed is dropped from the corpse; none of these leave any.
    /// Redraw a figure and its rows here have to follow.
    ///
    /// Their third tag is Shoot, the trigger's own name, so no state needs renaming.
    /// </summary>
    public static class CastBuilder
    {
        private const string Sprites = "Assets/Sprites/Enemies";
        private const string Prefabs = "Assets/Resources/Prefabs/Enemies";

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
        }

        private static readonly Member[] Wizards =
        {
            // Crown and face to row 7; the staff hand is two pixels on rows 9-10 and stays on the
            // body, so the staff hangs from it and flops loose instead of standing up out of him.
            new()
            {
                Name = "Bonecrown", File = "wiz_bonecrown.aseprite", Creature = "bonecrown",
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2,
                        new RectInt(0, 8, 14, 7),
                        new RectInt(14, 9, 2, 2)),     // the hand on the staff
                    new("leg_l", 0, new Vector2(7.5f, 14.5f), 1, new RectInt(0, 15, 10, 4)),
                    new("leg_r", 0, new Vector2(11f, 14.5f), 0, new RectInt(10, 15, 4, 4)),
                    new("head", 0, new Vector2(10f, 7.5f), 4, new RectInt(0, 0, 14, 8)),
                    new("staff", 0, new Vector2(15.5f, 9.5f), 5,
                        new RectInt(16, 0, 4, 19),
                        new RectInt(14, 0, 2, 9),
                        new RectInt(14, 11, 2, 8)),
                },
            },

            // The hood hangs forward to row 8 in the middle; the reaching arm, ember and all, is
            // everything right of column 12 on rows 8-11.
            new()
            {
                Name = "Hollowhood", File = "wiz_hollowhood.aseprite", Creature = "hollowhood",
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2,
                        new RectInt(0, 8, 8, 1),
                        new RectInt(12, 8, 1, 1),
                        new RectInt(0, 9, 13, 3),
                        new RectInt(0, 12, 14, 3)),
                    new("leg_l", 0, new Vector2(7f, 14.5f), 1, new RectInt(0, 15, 10, 4)),
                    new("leg_r", 0, new Vector2(11f, 14.5f), 0, new RectInt(10, 15, 10, 4)),
                    new("head", 0, new Vector2(9.5f, 8f), 4,
                        new RectInt(0, 0, 20, 8),
                        new RectInt(8, 8, 4, 1)),      // the hood's lower lip
                    new("arm_r", 0, new Vector2(12.5f, 9.5f), 3, new RectInt(13, 8, 7, 4)),
                },
            },

            // Horns and skull in the middle columns, both raised arms with their glow out to the
            // sides down to the shoulder row, and the legs start a row higher than the others'.
            new()
            {
                Name = "Ramskull", File = "wiz_ramskull.aseprite", Creature = "ramskull",
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2, new RectInt(5, 8, 9, 6)),
                    new("leg_l", 0, new Vector2(7.5f, 13.5f), 1, new RectInt(0, 14, 10, 5)),
                    new("leg_r", 0, new Vector2(11f, 13.5f), 0, new RectInt(10, 14, 10, 5)),
                    new("head", 0, new Vector2(9.5f, 7.5f), 4, new RectInt(5, 0, 9, 8)),
                    new("arm_l", 0, new Vector2(5f, 8f), 0, new RectInt(0, 0, 5, 9)),
                    new("arm_r", 0, new Vector2(14f, 8f), 3, new RectInt(14, 0, 6, 9)),
                },
            },
        };

        /// <summary>
        /// The robots and the big-headed things. These stand on a 20x24 canvas — Sentinel and the
        /// Ghast are 20px tall and would lose their tops on 22 — with the feet still three rows
        /// above the bottom edge, so they sit on the ground the way the 22px cast does. Only two of
        /// them have a soldier's body; the rest come apart where they are built to: treads under
        /// the Reaper, four legs round the mine, a bundle of feelers each side of the Gaper.
        /// </summary>
        private static readonly Member[] Monsters =
        {
            // Visor head to row 9, a ribbed chest on a two-pixel neck, the gun from column 11, and
            // two one-pixel legs split between columns 8 and 9.
            new()
            {
                Name = "Sentinel", File = "sentinel.aseprite", Creature = "sentinel",
                MaxHealth = 25, WalkSpeed = 1.3f,
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2,
                        new RectInt(6, 10, 5, 5),
                        new RectInt(6, 15, 5, 1)),     // pelvis
                    new("leg_l", 0, new Vector2(7f, 15.5f), 1, new RectInt(0, 16, 9, 5)),
                    new("leg_r", 0, new Vector2(9f, 15.5f), 0, new RectInt(9, 16, 11, 5)),
                    new("head", 0, new Vector2(8f, 9.5f), 4, new RectInt(0, 0, 20, 10)),
                    new("gun", 0, new Vector2(11f, 12.5f), 3, new RectInt(11, 11, 9, 4)),
                },
            },

            // Crowned head and neck to row 9, the dangling claw right of column 11, treads from row 17.
            new()
            {
                Name = "Reaper", File = "reaper.aseprite", Creature = "reaper",
                MaxHealth = 35, WalkSpeed = 1f,
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2, new RectInt(0, 10, 12, 7)),
                    new("head", 0, new Vector2(8f, 9.5f), 4, new RectInt(0, 0, 20, 10)),
                    new("claw", 0, new Vector2(12f, 11.5f), 3,
                        new RectInt(12, 10, 8, 7),
                        new RectInt(13, 17, 7, 1)),    // the claw's tips, level with the treads
                    new("treads", 0, new Vector2(8f, 16.5f), 1, new RectInt(0, 17, 13, 4)),
                },
            },

            // The shell and its fuse are the body; each leg is the staircase it draws, fenced off
            // row by row so the inner and outer pair on a side do not swap pixels.
            new()
            {
                Name = "Minespider", File = "minespider.aseprite", Creature = "minespider",
                MaxHealth = 10, WalkSpeed = 2.2f,
                Cuts = new Cut[]
                {
                    new("body", -1, Vector2.zero, 2,
                        new RectInt(5, 5, 11, 10),
                        new RectInt(7, 15, 5, 1)),     // belly
                    new("leg_ol", 0, new Vector2(5.5f, 14.5f), 0,
                        new RectInt(0, 15, 6, 1), new RectInt(0, 16, 5, 2), new RectInt(0, 18, 4, 3)),
                    new("leg_il", 0, new Vector2(6.5f, 15f), 1,
                        new RectInt(5, 16, 3, 2), new RectInt(4, 18, 4, 3)),
                    new("leg_ir", 0, new Vector2(11.5f, 15f), 1,
                        new RectInt(11, 16, 3, 2), new RectInt(12, 18, 4, 3)),
                    new("leg_or", 0, new Vector2(13.5f, 14.5f), 0,
                        new RectInt(13, 15, 7, 1), new RectInt(14, 16, 6, 2), new RectInt(16, 18, 4, 3)),
                },
            },

            // All head, maw included, down to row 15 and the middle of 16; the feelers below split
            // down the gap between the third and fourth strand.
            new()
            {
                Name = "Gaper", File = "gaper.aseprite", Creature = "gaper",
                MaxHealth = 20, WalkSpeed = 1f,
                Cuts = new Cut[]
                {
                    new("head", -1, Vector2.zero, 2,
                        new RectInt(0, 3, 20, 13),
                        new RectInt(7, 16, 4, 1)),
                    new("feelers_l", 0, new Vector2(6f, 15.5f), 1,
                        new RectInt(0, 16, 7, 1), new RectInt(0, 17, 9, 4)),
                    new("feelers_r", 0, new Vector2(11.5f, 15.5f), 0,
                        new RectInt(11, 16, 9, 1), new RectInt(9, 17, 11, 4)),
                },
            },

            // The skull and its lower jaw to row 11, the hanging arm left of column 6 on rows
            // 14-17, one-pixel legs from row 17.
            new()
            {
                Name = "Ghast", File = "ghast.aseprite", Creature = "ghast",
                MaxHealth = 15, WalkSpeed = 1.2f,
                Cuts = new Cut[]
                {
                    new("torso", -1, Vector2.zero, 2,
                        new RectInt(5, 11, 6, 3),
                        new RectInt(6, 14, 14, 3)),
                    new("leg_l", 0, new Vector2(7.5f, 16.5f), 1,
                        new RectInt(6, 17, 4, 1), new RectInt(0, 18, 10, 3)),
                    new("leg_r", 0, new Vector2(12f, 16.5f), 0, new RectInt(10, 17, 10, 4)),
                    new("head", 0, new Vector2(8.5f, 10.5f), 4,
                        new RectInt(0, 0, 20, 11),
                        new RectInt(11, 11, 9, 1)),    // lower jaw
                    new("arm_l", 0, new Vector2(5.5f, 13.5f), 0, new RectInt(0, 14, 6, 4)),
                },
            },
        };

        [MenuItem("PhysFun/Enemies/Build Wizards (Bonecrown, Hollowhood, Ramskull)", false, 202)]
        private static void BuildWizards() => Build(Wizards);

        [MenuItem("PhysFun/Enemies/Build Monsters (Sentinel, Reaper, Minespider, Gaper, Ghast)", false, 203)]
        private static void BuildMonsters() => Build(Monsters);

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
