using System;
using UnityEngine;

namespace Phys.Explosions
{
    /// <summary>
    /// Everything one blast is: how far it reaches, how hard it hits, how much of the world it
    /// takes with it and what it leaves burning. One profile per kind of bomb — a barrel, a
    /// grenade, a rocket — carried inline on the thing that goes off, or shared through an
    /// <see cref="ExplosionConfig"/> asset when several prefabs want the same bang.
    ///
    /// The knobs are split the way the blast is: <b>shape</b> decides who is in it,
    /// <b>damage</b> and <b>force</b> decide what happens to them, <b>terrain</b> decides how
    /// much of the level stops existing, <b>fire</b> decides what is still happening a second
    /// later, and <b>chain</b> decides whether the barrel next to it joins in.
    ///
    /// Radii are world units — 1 unit is 20 px, the world's PPU — so a radius of 1 is a hole a
    /// character could stand in.
    /// </summary>
    [Serializable]
    public sealed class ExplosionProfile
    {
        // ── Shape ─────────────────────────────────────────────────────────────
        [Header("Shape")]
        [Tooltip("Outer reach. Nothing past this is touched at all.")]
        public float radius = 1.6f;

        [Tooltip("Core. Everything inside takes the full figure — no falloff, no cover. Keeps a " +
                 "point-blank hit from being weakened by the victim's own collider geometry.")]
        public float innerRadius = 0.3f;

        [Tooltip("Shape of the drop from the core to the rim. 1 = straight line, 2 = most of the " +
                 "punch stays near the middle, 0.5 = the rim still hurts.")]
        [Range(0.2f, 4f)] public float falloff = 2f;

        [Tooltip("What the blast can reach: damage, shove and carve all draw from this.")]
        public LayerMask affects = ~0;

        [Tooltip("Geometry that shields whatever is behind it. Empty = the blast goes through walls.")]
        public LayerMask blockedBy;

        [Tooltip("What a target behind cover keeps. 0 = full shadow, 1 = cover is decorative.")]
        [Range(0f, 1f)] public float coverLeak = 0.25f;

        // ── Damage ────────────────────────────────────────────────────────────
        [Header("Damage")]
        [Tooltip("Damage at the core, before falloff.")]
        public float damage = 60f;

        [Tooltip("Hits worth less than this are dropped, so the rim does not litter the screen with 1s.")]
        public float minDamage = 1f;

        [Tooltip("Off spares whoever set it off — the launcher's owner, the barrel itself.")]
        public bool hurtsOwner = true;

        [Tooltip("Share of the blast impulse handed to a corpse when the blast is the killing blow.")]
        public float corpseKick = 0.05f;

        // ── Force ─────────────────────────────────────────────────────────────
        [Header("Force")]
        [Tooltip("Impulse at the core, in kg-units per second. It is split across a ragdoll's " +
                 "limbs, so a figure that throws a crate will only stagger a body.")]
        public float force = 6f;

        [Tooltip("Fraction of the push aimed straight up whatever direction the target lies in. " +
                 "A ground blast that only pushes outward slides things along the floor; the " +
                 "lift is what makes it throw them.")]
        [Range(0f, 1f)] public float upwardBias = 0.35f;

        [Tooltip("Random spin handed to everything it moves. Debris that tumbles reads as blown " +
                 "up; debris that slides reads as pushed.")]
        public float spin = 1.5f;

        [Tooltip("Give light and heavy things the same change in speed rather than the same " +
                 "impulse. On is more dramatic, off is more honest.")]
        public bool ignoreMass;

        // ── Terrain ───────────────────────────────────────────────────────────
        [Header("Terrain")]
        [Tooltip("Radius of the hole punched through pixel sprites and terrain. 0 leaves the " +
                 "level intact. Usually smaller than the damage radius — a grenade kills across " +
                 "a room and cracks a floor tile.")]
        public float carveRadius = 0.7f;

        [Tooltip("How many loose shards the bite comes out as. 0 erases the pixels outright, " +
                 "which is cheaper and leaves no debris to simulate.")]
        [Range(0, 24)] public int shards;

        [Tooltip("How hard those shards are thrown.")]
        public float shardImpulse = 3f;

        // ── Fire ──────────────────────────────────────────────────────────────
        [Header("Fire")]
        [Tooltip("Set light to whatever flammable thing the blast touches.")]
        public bool ignites;

        [Tooltip("How far the ignition reaches. Usually wider than the hole and narrower than " +
                 "the damage: a fuel drum should leave a burning room behind it.")]
        public float igniteRadius = 1.2f;

        [Tooltip("Ignition points scattered through that circle. More points = fire starts in " +
                 "more places at once instead of one neat blob.")]
        [Range(0, 64)] public int igniteSpots = 14;

        [Tooltip("Radius of each of those points, in world units.")]
        public float igniteBrush = 0.12f;

        [Tooltip("Flame cells thrown out as the fireball itself. They drift, light what they " +
                 "touch and die. 0 = no fireball.")]
        [Range(0, 400)] public int fireball = 90;

        [Tooltip("Smoke cells left hanging afterwards.")]
        [Range(0, 200)] public int smoke = 40;

        [Tooltip("How hot the fireball is, 0-100, on the same scale as a material's temperature " +
                 "of fire. Decides how readily those cells light what they touch.")]
        [Range(0, 100)] public int fireHeat = 70;

        // ── Feel ──────────────────────────────────────────────────────────────
        [Header("Feel")]
        [Tooltip("Camera kick at the core, falling off over ShakeRange.")]
        public float shake = 0.7f;

        [Tooltip("Distance over which that kick fades to nothing.")]
        public float shakeRange = 14f;

        [Tooltip("Pixels thrown out of the blast, in every direction. They leave white hot and " +
                 "cool through SparkColor to SparkCool as they fly.")]
        [Range(0, 300)] public int sparks = 60;

        public float sparkSpeed = 9f;

        [Tooltip("The colour of the fire in it — what the debris is halfway through its flight.")]
        public Color sparkColor = new(1f, 0.72f, 0.25f, 1f);

        [Tooltip("What the debris has cooled to by the time it fades. Ash and scorched metal.")]
        public Color sparkCool = new(0.35f, 0.16f, 0.12f, 1f);

        [Tooltip("Size of the white flash, as a fraction of the blast radius. 0 = none.")]
        [Range(0f, 2f)] public float flashScale = 0.85f;

        [Tooltip("Size of the expanding ring, against the full width of the blast. 0 = none. " +
                 "It is the only thing that says how far the blast actually reached.")]
        [Range(0f, 2f)] public float ringScale = 1f;

        [Tooltip("Optional art for one piece of debris. Empty uses a generated white pixel, " +
                 "which is what this is meant to be drawn with.")]
        public Sprite sparkPixel;

        // ── Chain ─────────────────────────────────────────────────────────────
        [Header("Chain")]
        [Tooltip("How far this blast sets off other explosives. 0 = it does not.")]
        public float chainRadius = 2f;

        [Tooltip("Pause before a caught explosive goes off. Zero makes a row of barrels one flat " +
                 "bang; a beat between them is what makes it a chain.")]
        public float chainDelay = 0.12f;

        [Tooltip("Random spread on that pause, so a cluster does not fire in lockstep.")]
        public float chainJitter = 0.06f;

        /// <summary>How much of the blast survives out to <paramref name="distance"/>.</summary>
        public float Attenuate(float distance)
        {
            if (distance <= innerRadius) return 1f;
            if (distance >= radius) return 0f;
            float t = (distance - innerRadius) / Mathf.Max(0.0001f, radius - innerRadius);
            return Mathf.Pow(1f - t, Mathf.Max(0.01f, falloff));
        }

        public ExplosionProfile Clone() => (ExplosionProfile)MemberwiseClone();

        /// <summary>
        /// The same blast, <paramref name="k"/> times as big. Every radius scales with k and the
        /// figures that should follow the size of it — damage, push, how much fire and debris —
        /// scale with it too, so one profile covers a whole family of charges and you are not
        /// re-tuning eight numbers to ask for a bigger bang. The camera kick scales by the square
        /// root: a blast ten times as wide is not ten times as alarming to watch.
        /// </summary>
        public ExplosionProfile Scaled(float k)
        {
            k = Mathf.Max(0.01f, k);
            var c = Clone();

            c.radius *= k;
            c.innerRadius *= k;
            c.carveRadius *= k;
            c.igniteRadius *= k;
            c.chainRadius *= k;
            c.shardImpulse *= k;

            c.damage *= k;
            c.force *= k;

            c.shards = Mathf.Clamp(Mathf.RoundToInt(shards * k), 0, 24);
            c.igniteSpots = Mathf.Clamp(Mathf.RoundToInt(igniteSpots * k), 0, 64);
            c.fireball = Mathf.Clamp(Mathf.RoundToInt(fireball * k), 0, 400);
            c.smoke = Mathf.Clamp(Mathf.RoundToInt(smoke * k), 0, 200);
            c.sparks = Mathf.Clamp(Mathf.RoundToInt(sparks * k), 0, 300);
            c.shake *= Mathf.Sqrt(k);

            return c;
        }

        // ── Presets ───────────────────────────────────────────────────────────
        // Starting points rather than balance: something to drop on a prefab so it already reads
        // as the thing it is called, and then tune.

        /// <summary>Small, lethal, barely scratches the level.</summary>
        public static ExplosionProfile Grenade() => new()
        {
            radius = 1.8f, innerRadius = 0.25f, damage = 70f, force = 7f,
            carveRadius = 0.45f, shards = 6, shardImpulse = 4f,
            ignites = false, fireball = 40, smoke = 25,
            shake = 0.7f, sparks = 70, chainRadius = 2f,
        };

        /// <summary>Fuel drum: wide, fiery, leaves the room burning.</summary>
        public static ExplosionProfile Barrel() => new()
        {
            radius = 2.6f, innerRadius = 0.5f, damage = 90f, force = 10f, upwardBias = 0.45f,
            carveRadius = 0.9f, shards = 8, shardImpulse = 5f,
            ignites = true, igniteRadius = 2.2f, igniteSpots = 22, fireball = 160, smoke = 70,
            shake = 1f, sparks = 110, chainRadius = 3.5f,
        };

        /// <summary>Rocket: focused, digs, throws less than it kills.</summary>
        public static ExplosionProfile Rocket() => new()
        {
            radius = 2.2f, innerRadius = 0.35f, damage = 110f, falloff = 2.5f, force = 9f,
            carveRadius = 1.1f, shards = 10, shardImpulse = 6f,
            ignites = false, fireball = 70, smoke = 40,
            shake = 1.1f, sparks = 90, chainRadius = 2.5f,
        };

        /// <summary>Firebomb: hardly kills anything on its own. The fire does the work.</summary>
        public static ExplosionProfile Firebomb() => new()
        {
            radius = 1.6f, innerRadius = 0.2f, damage = 12f, force = 2.5f,
            carveRadius = 0f, shards = 0,
            ignites = true, igniteRadius = 2f, igniteSpots = 34, igniteBrush = 0.16f,
            fireball = 220, smoke = 60, fireHeat = 85,
            shake = 0.25f, sparks = 45, sparkColor = new Color(1f, 0.55f, 0.15f, 1f),
            chainRadius = 1.5f,
        };
    }
}
