using UnityEngine;

namespace Common
{
    /// <summary>
    /// One hit, described the same way whatever caused it. Built by <see cref="ImpactSolver"/>
    /// for physics contacts and by hand for everything else, then handed to
    /// <see cref="Damageable.ApplyDamage(DamageInfo)"/>.
    /// </summary>
    public readonly struct DamageInfo
    {
        public readonly float Amount;
        public readonly DamageType Type;

        /// <summary>Where it landed, in world space. Drives the floating number and the corpse kick.</summary>
        public readonly Vector2 Point;

        /// <summary>Unit vector along the push, pointing into the victim. Zero when the hit has no direction.</summary>
        public readonly Vector2 Direction;

        /// <summary>Impulse to hand the corpse if this is the killing blow. Already scaled by the caller.</summary>
        public readonly Vector2 Impulse;

        /// <summary>What did it, when there is something to blame.</summary>
        public readonly GameObject Source;

        public DamageInfo(float amount, DamageType type, Vector2 point,
                          Vector2 direction = default, Vector2 impulse = default, GameObject source = null)
        {
            Amount = amount;
            Type = type;
            Point = point;
            Direction = direction;
            Impulse = impulse;
            Source = source;
        }
    }
}
