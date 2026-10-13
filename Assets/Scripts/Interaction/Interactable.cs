using System.Collections.Generic;
using UnityEngine;

namespace Interaction
{
    /// <summary>
    /// Something the player can use with the interact key: a door, later a lever, a chest,
    /// a winch. A subclass says what using it is called (<see cref="Verb"/>) and what it does
    /// (<see cref="Interact"/>); <see cref="InteractionSystem"/> does the rest - picks the
    /// nearest one in reach, outlines it, shows "E  Open door" at the foot of the screen, and
    /// calls it when the key is pressed.
    ///
    /// Only the player interacts. Enemies have no use for any of this, which is the point
    /// for doors: a shut one keeps them in their room.
    /// </summary>
    public abstract class Interactable : MonoBehaviour
    {
        [Tooltip("How close the player's centre has to be to Point, world units.")]
        [SerializeField] private float _reach = 0.9f;

        private static readonly List<Interactable> AllList = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode() => AllList.Clear();

        public static IReadOnlyList<Interactable> All => AllList;

        public float Reach => _reach;

        /// <summary>Where reach is measured to.</summary>
        public virtual Vector2 Point => transform.position;

        /// <summary>What pressing the key does, as the prompt shows it ("Open door").</summary>
        public abstract string Verb { get; }

        /// <summary>The sprite the outline goes round.</summary>
        public virtual SpriteRenderer Outlined => GetComponent<SpriteRenderer>();

        /// <summary>False hides the prompt and the outline (nothing to do here right now).</summary>
        public virtual bool CanInteract(GameObject who) => true;

        public abstract void Interact(GameObject who);

        protected virtual void OnEnable() => AllList.Add(this);
        protected virtual void OnDisable() => AllList.Remove(this);
    }
}
