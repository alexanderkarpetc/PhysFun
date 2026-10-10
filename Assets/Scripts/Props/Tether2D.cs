using Common;
using UnityEngine;

namespace Props
{
    /// <summary>
    /// Makes a <see cref="Rope2D"/> something you can shoot through: the bell's chain, the
    /// ropes a grate hangs from.
    ///
    /// A rope's links have colliders but nothing to take damage with, so a round just knocks
    /// them aside. The rope instance is a child of this object and the <see cref="Damageable"/>
    /// sits here, so a round or a blast landing on any link finds it the way it finds anything
    /// else; a cutting hit parts the rope at the link nearest the hit, and whatever hung on it
    /// drops. An arc through the load, or something bumping into the rope, does not cut it.
    ///
    /// The rope carries the load itself. For that not to stretch, the rope it is given is a
    /// heavy one and the load is not hundreds of times heavier than a link - export_rooms
    /// sets both when it hangs a prop.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Damageable))]
    public sealed class Tether2D : MonoBehaviour
    {
        [SerializeField] private Rope2D _rope;
        [Tooltip("Damage from one hit that cuts the rope (a round, a blast, a blade, a grinder).")]
        [SerializeField] private float _cutDamage = 5f;

        private Damageable _damageable;

        private void Start()
        {
            _damageable = GetComponent<Damageable>();
            _damageable.Damaged += OnDamaged;
        }

        private void OnDestroy()
        {
            if (_damageable) _damageable.Damaged -= OnDamaged;
        }

        private void OnDamaged(DamageInfo info)
        {
            if (!_rope || !_rope.IsIntact || info.Amount < _cutDamage) return;
            switch (info.Type)
            {
                case DamageType.Projectile:
                case DamageType.Explosion:
                case DamageType.Grind:
                case DamageType.Melee:
                    _rope.CutNearest(info.Point);
                    break;
            }
        }
    }
}
