using UnityEngine;

namespace Common
{
    /// <summary>
    /// One place for the balance of every hit the world lands. Shared by every
    /// <see cref="Damageable"/> that does not override it, so a single asset retunes how
    /// dangerous the environment is.
    ///
    /// The model, in one line: <c>damage = scale * mass^massExponent * speed^speedExponent</c>,
    /// where <c>speed</c> is the part of the closing speed the attacker itself brought (see
    /// <see cref="ImpactSolver.Evaluate"/>).
    ///
    /// The defaults reproduce the original hand-rolled formula exactly — <c>mass * speed / 5</c>,
    /// halved for a side-on hit, ignored below 2 u/s — so the game hits as hard as it used to.
    /// Both exponents are 1 for that reason; dropping them below 1 saturates the curve (a boulder
    /// stops being thirty pebbles) if the flat scaling ever needs taming.
    /// </summary>
    [CreateAssetMenu(fileName = "ImpactDamage", menuName = "PhysFun/Impact Damage Config", order = 1)]
    public sealed class ImpactDamageConfig : ScriptableObject
    {
        /// <summary>Where <see cref="Shared"/> looks. Relative to any Resources folder.</summary>
        public const string ResourcePath = "ImpactDamage";

        [Header("Impact")]
        [Tooltip("Approach speed (u/s) a hit has to beat before it hurts at all. A pure gate: the " +
                 "speed charged for is the full one, not the excess over this.")]
        [Range(0f, 12f)] public float minSpeed = 2f;

        [Tooltip("Overall damage multiplier. The one knob to turn when the whole game is too soft or too lethal.")]
        [Range(0f, 1f)] public float scale = 0.2f;

        [Tooltip("Shapes how much the attacker's mass matters. 1 = flat, twice the mass hits twice as " +
                 "hard; 0.5 = a 4x heavier object hits only twice as hard.")]
        [Range(0f, 2f)] public float massExponent = 1f;

        [Tooltip("Shapes how much speed matters. 1 = momentum, 2 = kinetic energy.")]
        [Range(0.5f, 3f)] public float speedExponent = 1f;

        [Tooltip("Hits worth less than this are dropped entirely — no damage, no floating number.")]
        [Range(0f, 10f)] public float minDamage;

        [Tooltip("Ceiling on a single impact, so one freak collision cannot deal four digits.")]
        [Range(1f, 10000f)] public float maxDamagePerHit = 9999f;

        [Tooltip("Mass beyond this is ignored. Keeps a whole collapsing cliff from being scored as one object.")]
        [Range(1f, 100000f)] public float massCap = 100000f;

        [Tooltip("Mass credited to a body that cannot be slowed by what it hits — a kinematic " +
                 "crusher, a driven lift, a static block being moved by hand.")]
        [Range(1f, 10000f)] public float immovableMass = 500f;

        [Tooltip("Multiplier for a glancing side-on hit. Hits straight from above always land at " +
                 "full strength; 1 here removes the distinction.")]
        [Range(0f, 1f)] public float lateralMultiplier = 0.5f;

        [Tooltip("Seconds before the same body can land another impact. Stops one tumbling plank " +
                 "from billing four times on the way past.")]
        [Range(0f, 1f)] public float hitCooldown = 0.25f;

        [Header("Crush")]
        [Tooltip("Whether being pinned hurts: damage for something resting on you that never hit you " +
                 "hard enough to count as an impact. Off by default — collapses already kill " +
                 "through the impact itself, and this needs playtesting before it earns its keep.")]
        public bool crush;

        [Tooltip("How hard something has to press before it counts as crushing, measured in the " +
                 "victim's own body weights. 8 means roughly 'pinned under four times your own mass'.")]
        [Range(0.5f, 20f)] public float crushLoad = 8f;

        [Tooltip("Damage per second at exactly the threshold load. Scales up with the load beyond it.")]
        [Range(0f, 100f)] public float crushDamagePerSecond = 12f;

        [Tooltip("Cap on that scaling, in multiples of the threshold load.")]
        [Range(1f, 20f)] public float crushLoadCap = 5f;

        [Tooltip("Seconds of continuous pressure before it starts to hurt, so a hard landing or a " +
                 "single solver spike is free.")]
        [Range(0f, 2f)] public float crushGrace = 0.25f;

        [Tooltip("How often crush damage is banked and shown, in seconds. Purely readability — the " +
                 "rate is unaffected.")]
        [Range(0.05f, 1f)] public float crushTickInterval = 0.25f;

        [Header("Feedback")]
        [Tooltip("Camera kick when the player is the one hurt: trauma = scale * sqrt(damage). " +
                 "Square-rooted so a bolt still registers without a lethal blow whiting out the " +
                 "screen. 0 disables it.")]
        [Range(0f, 0.2f)] public float cameraShakeScale = 0.05f;

        [Tooltip("Log every hit that lands, with the numbers that produced it. For balancing only.")]
        public bool logHits;

        private static ImpactDamageConfig _shared;

        /// <summary>
        /// The project-wide profile: the asset at Resources/<see cref="ResourcePath"/> if there is
        /// one, otherwise the defaults above. Nothing has to be authored for the game to run.
        /// </summary>
        public static ImpactDamageConfig Shared
        {
            get
            {
                if (_shared) return _shared;

                _shared = Resources.Load<ImpactDamageConfig>(ResourcePath);
                if (!_shared)
                {
                    _shared = CreateInstance<ImpactDamageConfig>();
                    _shared.name = "ImpactDamage (built-in defaults)";
                }
                return _shared;
            }
        }
    }
}
