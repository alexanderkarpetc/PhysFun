using UnityEngine;

namespace Props
{
    /// <summary>
    /// One link of a <see cref="Rope2D"/>. Exists so that whatever parts the link — an
    /// overloaded joint, a grinder, fire — reports back to the rope it belonged to.
    /// Added by <see cref="Rope2D.Build"/>; not meant to be placed by hand.
    /// </summary>
    public class RopeLink : MonoBehaviour
    {
        public Rope2D rope;
        public int index;

        private void OnJointBreak2D(Joint2D joint)
        {
            if (rope) rope.NotifyParted(index);
        }

        private void OnDestroy()
        {
            // A link torn out of the world counts as a parted rope; a rope tearing itself
            // down (rebuild, scene unload) does not.
            if (rope && Application.isPlaying && !rope.IsTearingDown && gameObject.scene.isLoaded)
                rope.NotifyParted(index);
        }
    }
}
