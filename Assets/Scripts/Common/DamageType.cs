namespace Common
{
    /// <summary>
    /// Where a hit came from. The world is the game's main weapon, so the two physics entries
    /// carry most of the traffic: <see cref="Impact"/> for anything that arrives moving,
    /// <see cref="Crush"/> for anything that settles on top and keeps pressing.
    /// </summary>
    public enum DamageType
    {
        Impact,
        Crush,
        Projectile,
        Melee,
        Explosion
    }
}
