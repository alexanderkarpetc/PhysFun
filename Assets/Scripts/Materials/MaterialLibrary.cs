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
            Flammable = true,
            // At 40 ticks/s these give a pixel a ~0.4s life and a front that eats roughly
            // 25 texture px per second — a 200px barrel is gone in about 8 seconds,
            // a 500px crate in around 20.
            BurnRate = 0.06f,
            BurnRateJitter = 0.7f,
            SpreadChance = 1f,
            SpreadUpBias = 0.6f,
            SpreadDelay = 0.03f,
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
