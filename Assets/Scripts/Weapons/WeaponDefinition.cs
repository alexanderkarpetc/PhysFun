using System;
using UnityEngine;

namespace Weapons
{
    public enum WeaponKind
    {
        Ballistic,
        Energy,
    }

    /// <summary>
    /// One gun, as data: how it looks in a hand and how it is meant to shoot.
    ///
    /// Nothing reads the firing numbers yet — <see cref="WeaponHolder"/> only puts the sprite
    /// where the hand is. They are here so that the assets are already the place those values
    /// live once projectiles exist, rather than a second pass over every weapon later.
    ///
    /// The offsets are in the weapon sprite's own local units, measured from its pivot, which the
    /// art pipeline puts on the grip. Tools/gen_weapon_sprites.py writes them out with the sprites,
    /// so re-running it keeps the muzzle on the muzzle when a gun gets redrawn.
    /// </summary>
    [CreateAssetMenu(menuName = "PhysFun/Weapon", fileName = "Weapon")]
    public sealed class WeaponDefinition : ScriptableObject
    {
        [Header("Identity")]
        public string displayName;

        public WeaponKind kind;

        [Header("Look")]
        [Tooltip("Drawn at the holder's hand, pivoted on the grip.")]
        public Sprite sprite;

        [Tooltip("What leaves the muzzle. Pivoted on its middle, drawn pointing right, so a " +
                 "shot only has to be rotated to its heading.")]
        public Sprite projectile;

        [Tooltip("Muzzle relative to the grip, in local units. Where a projectile would leave " +
                 "from, and where a muzzle flash would sit.")]
        public Vector2 muzzleOffset;

        [Tooltip("Nudge the whole gun in the hand. Zero is the hand pixel the animation keys.")]
        public Vector2 holdOffset;

        [Tooltip("Above the body, which is 0.")]
        public int sortingOrder = 1;

        [Header("Firing — data only, nothing reads this yet")]
        public FireProfile fire = FireProfile.Default;
    }

    /// <summary>What the gun would do, once something is listening.</summary>
    [Serializable]
    public struct FireProfile
    {
        [Tooltip("Per hit, before any falloff.")]
        public float damage;

        [Tooltip("Shots per second while the trigger is held.")]
        public float rate;

        [Tooltip("Rounds per trigger pull, fired one after another at Rate — a burst, not a " +
                 "volley. 1 is single shot.")]
        public int burst;

        [Tooltip("Pause after a burst finishes, before the next one may start. This is what " +
                 "sets the gap between bursts, and for a single-shot gun it is the fire rate.")]
        public float burstCooldown;

        [Tooltip("Spin-up or charge before the first round of a burst. Cancelled if the target " +
                 "is lost, so the gun has to wind up again.")]
        public float windUp;

        [Tooltip("Show an aiming beam while winding up. Telegraphs a slow, heavy shot.")]
        public bool laserSight;

        [Tooltip("Projectiles per shot. Above 1 is a shotgun spread.")]
        public int pellets;

        [Tooltip("Half-angle of the cone, in degrees.")]
        public float spread;

        [Tooltip("Units per second. Together with Gravity this is what makes one gun shoot flat " +
                 "and another lob.")]
        public float projectileSpeed;

        [Tooltip("How hard the round is pulled down, as a multiple of world gravity. 0 flies " +
                 "straight.")]
        public float gravity;

        [Tooltip("Kick back into the shooter, in impulse units.")]
        public float recoil;

        public int magazine;

        public float reloadTime;

        public static FireProfile Default => new()
        {
            damage = 5f,
            rate = 4f,
            burst = 1,
            burstCooldown = 0.25f,
            windUp = 0f,
            laserSight = false,
            pellets = 1,
            spread = 2f,
            projectileSpeed = 24f,
            gravity = 1f,
            recoil = 0.05f,
            magazine = 20,
            reloadTime = 1.4f,
        };
    }
}
