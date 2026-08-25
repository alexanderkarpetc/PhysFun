namespace Common
{
    /// <summary>
    /// Where a hit came from. The world is the game's main weapon, so the physics entries carry
    /// most of the traffic: <see cref="Impact"/> for anything that arrives moving,
    /// <see cref="Crush"/> for anything that settles on top and keeps pressing, and
    /// <see cref="Grind"/> for a driven surface working away at whatever it is touching.
    /// </summary>
    public enum DamageType
    {
        Impact,
        Crush,
        Grind,
        Projectile,
        Melee,
        Explosion
    }
}
