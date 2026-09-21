using UnityEngine;

namespace Materials
{
    public enum PhysMaterialId
    {
        Default = 0,
        Wood    = 1,
        Ice     = 2,
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

        /// <summary>
        /// How hard this stuff hits when it is thrown at something. <see cref="Density"/> already
        /// carries most of it through mass; this is only the extra bite a hard material has over a
        /// soft one of the same weight. 1 = neutral.
        /// </summary>
        public float ImpactDamageMultiplier = 1f;

        public bool Flammable;

        // ── Fracture (see Phys.Fracture.FractureSystem) ───────────────────────
        // A brittle material does not lose a bite where it is hit: it splits. The two
        // numbers that decide how are Noita's own CellData attributes, same names and
        // read out of the dev build's config parser (durability at +0x104, crackability
        // at +0x108), as are the two explosion knobs further down.

        /// <summary>Whether a hit opens a running crack instead of just carving a hole.</summary>
        public bool Brittle;

        /// <summary>
        /// How much punishment the stuff absorbs before it splits at all. A hit worth less
        /// than this only scuffs it.
        /// </summary>
        public float Durability = 4f;

        /// <summary>
        /// World units of crack opened per point of hit force. This is the whole feel of the
        /// material: high means one shot runs a split the length of a pillar, low means you
        /// have to work at it.
        /// </summary>
        public float Crackability = 0.35f;

        /// <summary>Shortest and longest a single crack may run, whatever the force was.</summary>
        public float CrackMinLength = 0.5f;
        public float CrackMaxLength = 4.5f;

        /// <summary>
        /// How much of the incoming direction survives into the crack. Cracks in a brittle
        /// slab run with gravity, not with the bullet — 0 is dead vertical, 1 follows the
        /// shot. The vertical it runs along is chosen by which side the hit came from.
        /// </summary>
        public float CrackLean = 0.3f;

        /// <summary>
        /// How much vertical a hit needs before it picks the crack's direction outright.
        /// Below this the hit counts as sideways and the direction comes from where on the
        /// body it landed instead — upper half cracks downwards, lower half upwards.
        /// </summary>
        public float CrackVerticalBias = 0.35f;

        /// <summary>
        /// Length of the branch running back the other way, as a fraction of the main one.
        /// It is what turns a crack into a cut: the main branch runs into the material and
        /// this one sees the split out through the face the hit came in by.
        /// </summary>
        public float CrackBackFraction = 0.4f;

        /// <summary>
        /// How wide the split opens, in texture pixels. One is enough to free a slab — terrain
        /// contact is settled on pixel adjacency, and the flood fill that finds the loose piece
        /// is four-connected — so this is very nearly a pure look knob.
        /// </summary>
        public float CrackWidthPixels = 2f;

        /// <summary>
        /// Extra pixels of width, noised along the seam so the two faces are ragged instead of
        /// parallel. It only ever adds: a seam has to stay unbroken along its whole length, and
        /// one gap in it is one route for the flood fill to walk through and find one piece.
        /// </summary>
        public float CrackWidthJitter = 1f;

        /// <summary>Radians of wander per pixel travelled. 0 draws a laser cut.</summary>
        public float CrackWander = 0.22f;

        /// <summary>How fast the split runs, in world units per second.</summary>
        public float CrackSpeed = 9f;

        /// <summary>
        /// Beat between the crack finishing and the piece being let go, in seconds. Without
        /// it the slab is already falling by the time the eye has found the crack.
        /// </summary>
        public float CrackSettle = 0.14f;

        /// <summary>Colour the cut edge is frosted towards, so a split reads as broken.</summary>
        public Color32 CrackRim = new(236, 250, 255, 255);

        // Noita's ExplosionComponent spawns data/entities/misc/crack.xml this many times, and
        // only once the blast is wide enough to be worth it — the crack then travels outwards
        // along the blast direction. Same two knobs, moved onto the material because here it
        // is the ice that decides whether a bang cracks it, not the bomb.

        /// <summary>Blast carve radius below which an explosion only carves, never cracks.</summary>
        public float MinRadiusForCracks = 0.5f;

        /// <summary>Cracks one blast throws off.</summary>
        public int CrackCount = 3;

        // ── Burn tuning (see Phys.Fire.FireSystem) ────────────────────────────
        // Fuel runs 1 → 0 per pixel. One "tick" is one fire simulation step.

        /// <summary>Fuel consumed per tick by a burning pixel. 1/BurnRate = pixel lifetime in ticks.</summary>
        public float BurnRate = 0.017f;

        /// <summary>±fraction of jitter on BurnRate, so pixels don't all die on the same tick.</summary>
        public float BurnRateJitter = 0.7f;

        /// <summary>Per-tick chance a burning pixel lights each unburnt neighbour.</summary>
        public float SpreadChance = 0.32f;

        /// <summary>Extra spread bias for the neighbour that points world-up — flames climb.</summary>
        public float SpreadUpBias = 0.6f;

        /// <summary>
        /// Ticks a freshly-lit pixel waits before it can light its own neighbours.
        /// Counted in ticks rather than fuel so that how long a pixel burns and how fast
        /// the front travels stay independent — changing BurnRate alone changes duration
        /// without dragging the spread speed along with it.
        /// </summary>
        public float SpreadDelayTicks = 0.5f;

        /// <summary>Fraction of the sprite left behind as charcoal. 0 = burns away completely.</summary>
        public float CharAmount;

        /// <summary>
        /// Grid size the charcoal pattern is sampled on. Chunks need to stay above the
        /// split pass's minimum piece size or they end up as orphaned specks.
        /// </summary>
        public int CharClumpSize = 12;

        /// <summary>Per-tick chance a burning edge pixel lights a touching flammable object.</summary>
        public float ContactSpreadChance = 0.06f;

        // ── Flames (see Phys.Fire.FlameField) ─────────────────────────────────
        // Noita's own material attributes, same names and same 0–100 scale, read out of
        // the dev build's CellData (generates_smoke at +0x0a0, generates_flames at +0x0a4,
        // requires_oxygen at +0x0a8, temperature_of_fire at +0x09c).

        /// <summary>Percent chance per grid frame that a burning pixel throws off a flame.</summary>
        public float GeneratesFlames = 22f;

        /// <summary>Percent chance per grid frame that a burning pixel throws off smoke.</summary>
        public float GeneratesSmoke = 7f;

        /// <summary>
        /// How hot this stuff burns, 0–100. It is the flame's own temperature — which decides
        /// how readily that flame sets light to what it touches — and doubles as the pixel's
        /// air supply: it refills whenever a flame gets out and drains when one cannot.
        /// </summary>
        public int TemperatureOfFire = 45;

        /// <summary>Whether a pixel that cannot vent goes out. Off = it burns sealed in.</summary>
        public bool RequiresOxygen = true;

        // Char gradient, sampled as fuel drains 1 → 0. There is no hot end: the bright
        // colours in a fire all come from the flame cells, never from the burning material.
        public Color32 EmberMid  = new(255, 146, 34, 255);
        public Color32 EmberCool = new(146, 34, 12, 255);
        public Color32 Charcoal  = new(30, 26, 25, 255);
    }
}
