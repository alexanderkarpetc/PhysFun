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


        public static readonly PhysMaterial Ice = new()
        {
            Id = PhysMaterialId.Ice,
            DisplayName = "Ice",
            Swatch = new Color32(150, 205, 226, 255),
            // Ice floats, barely. Light enough that a falling slab is survivable and heavy
            // enough that it is not — which is the whole point of dropping one on something.
            Density = 0.92f,
            // Hard and unforgiving on arrival: a slab of it lands like a rock, not like a plank.
            ImpactDamageMultiplier = 1.35f,
            Flammable = false,

            // Brittle is the opposite of the wood case above. Wood is eaten gradually by a
            // process; ice does nothing at all until it does everything at once. A hit is
            // either under the durability floor and leaves a scuff, or it is over it and runs
            // a split that either frees a slab or doesn't — and the player can see which,
            // because the split is drawn before the slab is let go.
            Brittle = true,
            Durability = 3.5f,
            // Reach, in world units per point of force, and it is the knob that decides how the
            // material reads. A crack only cuts a piece free if it reaches open air at both
            // ends, so this is really "how thick a slab can one shot shear": at 0.55 the
            // default 6-damage round reaches ~3.3 units, which goes through a pillar or a ledge
            // and leaves a hairline on anything heavier than that. Turn it down and ice becomes
            // something you have to work at with explosives; turn it up and one round drops a
            // ceiling.
            Crackability = 0.55f,
            CrackMinLength = 0.5f,
            CrackMaxLength = 6f,
            // Mostly vertical, with enough of the shot's slant left in that a shallow hit
            // shears a wedge off the face rather than a perfect column.
            CrackLean = 0.3f,
            CrackVerticalBias = 0.35f,
            CrackBackFraction = 0.4f,
            CrackWidthPixels = 2f,
            CrackWidthJitter = 1f,
            CrackWander = 0.34f,
            CrackSpeed = 9f,
            CrackSettle = 0.14f,
            CrackRim = new Color32(236, 250, 255, 255),
            MinRadiusForCracks = 0.5f,
            CrackCount = 3,
        };

        private static readonly PhysMaterial[] Ordered = { Default, Wood, Ice };

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
