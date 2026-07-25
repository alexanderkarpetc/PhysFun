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
            return view;
        }
    }
}
