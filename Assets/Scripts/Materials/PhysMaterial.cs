using UnityEngine;

namespace Materials
{
    public enum PhysMaterialId
    {
        Default = 0,
        Wood    = 1,
    }

    /// <summary>
    /// What a physics object is made of: how heavy it is and, when flammable,
    /// how fire eats through its pixels.
    ///
    /// Instances are shared and immutable in practice — look one up with
    /// <see cref="MaterialLibrary.Get"/> or <see cref="MaterialLibrary.Of(GameObject)"/>.
    /// </summary>
    public sealed class PhysMaterial
    {
        public PhysMaterialId Id;
        public string DisplayName;
        public Color32 Swatch;              // UI only — the sprite art is never tinted

        /// <summary>Multiplier on the collider-area mass baseline.</summary>
        public float Density = 1f;

        public bool Flammable;

        // ── Burn tuning (see Phys.Fire.FireSystem) ────────────────────────────
        // Fuel runs 1 → 0 per pixel. One "tick" is one fire simulation step.

        /// <summary>Fuel consumed per tick by a burning pixel. 1/BurnRate = pixel lifetime in ticks.</summary>
        public float BurnRate = 0.06f;

        /// <summary>±fraction of jitter on BurnRate, so pixels don't all die on the same tick.</summary>
        public float BurnRateJitter = 0.7f;

        /// <summary>Per-tick chance a burning pixel lights each unburnt neighbour.</summary>
        public float SpreadChance = 1f;

        /// <summary>Extra spread bias for the neighbour that points world-up — flames climb.</summary>
        public float SpreadUpBias = 0.6f;

        /// <summary>Fuel that must burn off before a pixel can light its neighbours.</summary>
        public float SpreadDelay = 0.03f;

        /// <summary>Fraction of the sprite left behind as charcoal. 0 = burns away completely.</summary>
        public float CharAmount;

        /// <summary>
        /// Grid size the charcoal pattern is sampled on. Chunks need to stay above the
        /// split pass's minimum piece size or they end up as orphaned specks.
        /// </summary>
        public int CharClumpSize = 12;

        /// <summary>Per-tick chance a burning edge pixel lights a touching flammable object.</summary>
        public float ContactSpreadChance = 0.06f;

        // Ember gradient, sampled as fuel drains 1 → 0.
        public Color32 EmberHot  = new(255, 244, 194, 255);
        public Color32 EmberMid  = new(255, 146, 34, 255);
        public Color32 EmberCool = new(146, 34, 12, 255);
        public Color32 Charcoal  = new(30, 26, 25, 255);
    }
}
