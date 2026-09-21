using UnityEngine;

namespace Materials
{
    /// <summary>
    /// Tags a physics object with the material it is made of. Added at spawn time by
    /// <see cref="Spawners.SpriteFactory"/>, and carried over automatically when the
    /// object is cloned by the cracker or by a pixel split.
    /// </summary>
    [DisallowMultipleComponent]
    public class MaterialView : MonoBehaviour
    {
        [SerializeField] private PhysMaterialId materialId = PhysMaterialId.Default;

        public PhysMaterialId Id
        {
            get => materialId;
            set => materialId = value;
        }

        public PhysMaterial Material => MaterialLibrary.Get(materialId);

        /// <summary>Set (or add) the material tag on <paramref name="go"/>.</summary>
        public static MaterialView Apply(GameObject go, PhysMaterialId id)
        {
            if (!go) return null;
            var view = go.GetComponent<MaterialView>();
            if (!view) view = go.AddComponent<MaterialView>();
            view.materialId = id;
            view.SyncBehaviours();
            return view;
        }

        /// <summary>
        /// Attach or drop the components the material implies. Only fracture so far: brittle
        /// stuff has to hear about physics contacts, and nothing else should pay for a
        /// collision callback it will never use.
        ///
        /// Called from <see cref="Apply"/>, which is the single place a material is ever
        /// stamped — terrain chunks, spawned props, the painter — so there is no path by
        /// which an object ends up with the wrong set.
        /// </summary>
        private void SyncBehaviours()
        {
            var body = GetComponent<Phys.Fracture.FractureBody>();
            if (Material.Brittle)
            {
                if (!body) gameObject.AddComponent<Phys.Fracture.FractureBody>();
            }
            else if (body)
            {
                // Clones inherit whatever their source had, so a shard whose material was
                // changed on the way out has to be able to lose it again.
                if (Application.isPlaying) Destroy(body); else DestroyImmediate(body);
            }
        }
    }
}
