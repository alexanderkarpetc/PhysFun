using UnityEngine;

namespace Phys.Explosions
{
    /// <summary>
    /// A blast several prefabs share. Same idea as <see cref="Common.ImpactDamageConfig"/>:
    /// retune every barrel in the level from one asset instead of from each of them.
    /// </summary>
    [CreateAssetMenu(fileName = "Explosion", menuName = "PhysFun/Explosion", order = 2)]
    public sealed class ExplosionConfig : ScriptableObject
    {
        public ExplosionProfile profile = ExplosionProfile.Barrel();
    }
}
