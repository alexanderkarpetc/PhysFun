using UnityEngine;

namespace Gore
{
    /// <summary>
    /// One place for how messy the game is: what blood looks like, how much of it a wound
    /// throws, and how much force it takes to pull a corpse apart.
    ///
    /// Same arrangement as <see cref="Common.ImpactDamageConfig"/> — every gore system reads
    /// <see cref="Shared"/>, which is the asset at Resources/<see cref="ResourcePath"/> when
    /// there is one and the defaults below when there is not, so nothing has to be authored
    /// for the game to run.
    /// </summary>
    [CreateAssetMenu(fileName = "Gore", menuName = "PhysFun/Gore Config", order = 2)]
    public sealed class GoreConfig : ScriptableObject
    {
        /// <summary>Where <see cref="Shared"/> looks. Relative to any Resources folder.</summary>
        public const string ResourcePath = "Gore";

        // ── Colour ───────────────────────────────────────────────────────────
        // Blood in the air and blood on a wall are deliberately not the same colour. A drop
        // is lit and moving and reads bright; the same drop soaked into stone has gone dark
        // and lost most of its saturation. Using one colour for both makes stains look like
        // stickers.

        [Header("Colour")]
        [Tooltip("Blood in flight.")]
        public Color32 dropColor = new(168, 18, 24, 255);

        [Tooltip("Blood once it has landed on something. Darker — this is what gets painted " +
                 "into the sprite and it never gets to move again.")]
        public Color32 stainColor = new(88, 12, 16, 255);

        [Tooltip("How far a stain takes the pixel it lands on towards stainColor. 1 replaces " +
                 "the colour outright; below that the surface still shows through.")]
        [Range(0f, 1f)] public float stainStrength = 0.85f;

        [Tooltip("How ragged a stain's rim is. 0 paints a clean disc, 1 eats most of the edge " +
                 "away into speckle.")]
        [Range(0f, 1f)] public float stainNoise = 0.55f;

        [Tooltip("Radius of the mark one landed drop leaves, in world units. A drop's own size " +
                 "scales it, so a fat drop leaves a fat splat.")]
        [Range(0.01f, 0.5f)] public float stainRadius = 0.075f;

        // ── Drops ────────────────────────────────────────────────────────────

        [Header("Drops")]
        [Tooltip("Ceiling on live drops. The oldest are recycled past it, so a massacre costs " +
                 "the same as a single wound.")]
        [Range(64, 8000)] public int maxDrops = 2000;

        [Tooltip("Pull on a drop, as a multiple of world gravity.")]
        [Range(0f, 3f)] public float gravity = 1f;

        [Tooltip("Air drag. Blood is heavy and does not hang the way a spark does, so this is " +
                 "low — it is here to take the edge off the fastest drops, not to slow them.")]
        [Range(0f, 4f)] public float drag = 0.35f;

        [Tooltip("Seconds a drop survives without hitting anything. It only matters for blood " +
                 "thrown into open air; everything else lands long before this.")]
        [Range(0.5f, 20f)] public float dropLife = 5f;

        [Tooltip("Seconds after birth during which a drop passes through the world. Without it " +
                 "every drop lands on the body it came out of, on the frame it was born.")]
        [Range(0f, 0.3f)] public float armTime = 0.045f;

        [Tooltip("What blood can land on and stain. Everything solid by default, minus the two " +
                 "creature layers — a live body is animated, and an animated sprite cannot hold " +
                 "a stain (see SpritePaintService.CanStain). Its corpse can, and does.")]
        public LayerMask splatMask = ~((1 << 2) | (1 << 5) | (1 << 7) | (1 << 8));

        [Tooltip("Sorting order for the drops. Over the world, under the fire (500).")]
        public int sortingOrder = 400;

        // ── Wounds ───────────────────────────────────────────────────────────

        [Header("Wounds")]
        [Tooltip("Drops thrown per point of damage. A 6-point round is about four drops; a " +
                 "crush that takes half a health bar is a fountain.")]
        [Range(0f, 5f)] public float dropsPerDamage = 0.7f;

        [Tooltip("Most drops a single hit may throw, whatever the damage was.")]
        [Range(1, 200)] public int maxDropsPerHit = 40;

        [Tooltip("How fast blood leaves a wound, in world units per second.")]
        [Range(0.5f, 20f)] public float spraySpeed = 4.5f;

        [Tooltip("Half-angle of the spray cone, in degrees, around the direction the hit came from.")]
        [Range(5f, 180f)] public float sprayCone = 55f;

        [Tooltip("Extra drops thrown by the killing blow, on top of its own damage.")]
        [Range(0, 200)] public int deathBurst = 24;

        // ── Bleeding ─────────────────────────────────────────────────────────

        [Header("Bleeding")]
        [Tooltip("Seconds a severed limb keeps dripping.")]
        [Range(0f, 60f)] public float bleedSeconds = 8f;

        [Tooltip("Drips per second at the start of a bleed. It tails off to nothing over " +
                 "bleedSeconds, so a fresh stump pumps and an old one seeps.")]
        [Range(0f, 60f)] public float bleedRate = 14f;

        [Tooltip("How fast a drip leaves the stump. Low — it should fall off the wound, not " +
                 "be fired out of it.")]
        [Range(0f, 6f)] public float bleedSpeed = 1.1f;

        // ── Tearing ──────────────────────────────────────────────────────────

        [Header("Tearing")]
        [Tooltip("Force a joint has to carry before the limb comes off, in newtons. This is " +
                 "read straight off the solver, so it is the real load holding the corpse " +
                 "together: hanging still is a few dozen, being yanked by an explosion is " +
                 "thousands.")]
        [Range(50f, 20000f)] public float tearForce = 1400f;

        [Tooltip("Same for twist, in newton-metres. A limb wrapped the wrong way round a " +
                 "grinder tears on this rather than on the pull.")]
        [Range(1f, 2000f)] public float tearTorque = 120f;

        [Tooltip("Physics steps the load has to stay over the threshold before the joint goes. " +
                 "One step of it is a solver spike, not a tear.")]
        [Range(1, 10)] public int tearSteps = 2;

        [Tooltip("Limbs one corpse may lose. A corpse that can shed every joint ends up as a " +
                 "pile of unreadable pixels; keeping a couple of joints means it still reads " +
                 "as a body afterwards.")]
        [Range(0, 16)] public int maxTears = 4;

        [Tooltip("Impulse on the killing blow above which the corpse is torn apart on arrival " +
                 "instead of waiting for the joints to feel it. 0 never gibs.")]
        [Range(0f, 20f)] public float gibImpulse = 2.5f;

        [Tooltip("Limbs a gib takes off, nearest the hit first.")]
        [Range(0, 16)] public int gibTears = 3;

        [Tooltip("Drops thrown by the cut itself, the moment a limb comes off. The stump goes " +
                 "on bleeding after this — see bleedRate.")]
        [Range(0, 200)] public int tearBurst = 30;

        [Tooltip("Log every tear with the load that caused it. For tuning tearForce.")]
        public bool logTears;

        private static GoreConfig _shared;

        public static GoreConfig Shared
        {
            get
            {
                if (_shared) return _shared;

                _shared = Resources.Load<GoreConfig>(ResourcePath);
                if (!_shared)
                {
                    _shared = CreateInstance<GoreConfig>();
                    _shared.name = "Gore (built-in defaults)";
                }
                return _shared;
            }
        }
    }
}
