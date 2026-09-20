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
            // Wood smoulders; it does not flash over. The two numbers that decide which of
            // those it looks like are independent, and both were set for paper:
            //
            //   BurnRate      how long one pixel stays alight. Fuel runs 255 -> 0 and a tick
            //                 takes max(1, round(BurnRate * 255)) of it, so at 20 ticks/s
            //                 0.006 is ~7 seconds a pixel — up from 3. Note the floor of 1:
            //                 below about 0.004 every value means the same 12.75 s.
            //   SpreadChance  how fast the front travels. Per tick, per neighbour, times the
            //                 up-bias and the per-pixel grain. With SpreadDelayTicks on top
            //                 as a flat wait, a pixel takes ~1.5 + 1/0.13 ≈ 9 ticks to pass
            //                 the fire on: a little over 2 texture px/s, where it was 6.
            //
            // In world terms that is a fire creeping about 0.1 units per second, so a plank a
            // unit long takes the better part of ten seconds to be eaten rather than two — and
            // because the pixels also glow more than twice as long, the band of visibly burning
            // material stays wide instead of being a thin edge chasing the object away.
            BurnRate = 0.006f,
            BurnRateJitter = 0.7f,
            SpreadChance = 0.13f,
            SpreadUpBias = 0.6f,
            SpreadDelayTicks = 1.5f,
            // Burns away to nothing — no charcoal remnants. Leftover chunks also cost
            // real performance: every isolated speck becomes another collider path and
            // another connected component for the split scan.
            CharAmount = 0f,
            // Rolled once per burn per tick, so it is a rate rather than a per-contact chance:
            // halved along with everything else, or a slow fire would still jump between objects
            // as eagerly as a fast one did.
            ContactSpreadChance = 0.03f,
            // Wood throws off a lot of flame and a fair bit of smoke, and burns warm rather
            // than fiercely: at 45 a flame off a plank catches another plank about half the
            // times it is asked, which is roughly how fire travels through a woodpile.
            GeneratesFlames = 22f,
            GeneratesSmoke = 7f,
            TemperatureOfFire = 45,
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
