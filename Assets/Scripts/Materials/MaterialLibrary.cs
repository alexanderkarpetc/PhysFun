using System.Collections.Generic;
using UnityEngine;

namespace Materials
{
    /// <summary>Every material in the game, keyed by <see cref="PhysMaterialId"/>.</summary>
    public static class MaterialLibrary
    {
        public static readonly PhysMaterial Default = new()
        {
            Id = PhysMaterialId.Default,
            DisplayName = "Default",
            Swatch = new Color32(150, 152, 158, 255),
            Density = 1f,
            Flammable = false,
        };

        public static readonly PhysMaterial Wood = new()
        {
            Id = PhysMaterialId.Wood,
            DisplayName = "Wood",
            Swatch = new Color32(158, 108, 58, 255),
            Density = 0.6f,
            // A plank stings, but it gives where a stone block does not.
            ImpactDamageMultiplier = 0.85f,
            Flammable = true,
            // Tuned for the 20 PPU art: at 20 ticks/s a pixel glows for about 3 seconds
            // and the front creeps ~5 texture px/s, which at 40 texture px per world unit
            // is the same world-space speed the 100 PPU art had. That leaves a ~15px band
            // of the object visibly ablaze instead of a thin edge eating it like paper.
            // BurnRate alone controls how long it burns; SpreadChance controls how fast
            // the fire travels.
            BurnRate = 0.017f,
            BurnRateJitter = 0.7f,
            SpreadChance = 0.32f,
            SpreadUpBias = 0.6f,
            SpreadDelayTicks = 0.5f,
            // Burns away to nothing — no charcoal remnants. Leftover chunks also cost
            // real performance: every isolated speck becomes another collider path and
            // another connected component for the split scan.
            CharAmount = 0f,
            ContactSpreadChance = 0.06f,
        };

        private static readonly PhysMaterial[] Ordered = { Default, Wood };

        public static IReadOnlyList<PhysMaterial> All => Ordered;

        public static PhysMaterial Get(PhysMaterialId id)
        {
            foreach (var m in Ordered)
                if (m.Id == id) return m;
            return Default;
        }

        /// <summary>Material of a spawned object; untagged objects are <see cref="Default"/>.</summary>
        public static PhysMaterial Of(GameObject go)
        {
            if (!go) return Default;
            var view = go.GetComponent<MaterialView>();
            return view ? view.Material : Default;
        }
    }
}
