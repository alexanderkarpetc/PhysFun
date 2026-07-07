using Spawners;
using UnityEngine;

namespace Props
{
    public class DynamicObjectView : MonoBehaviour
    {
        
        [ContextMenu("SetMass")]
        public void SetMassTo100()
        {
            var rb = GetComponent<Rigidbody2D>();
            var sprite = GetComponent<SpriteRenderer>().sprite;
            var col = GetComponent<Collider2D>();
            MassRecalculator.SetMass(sprite, rb, col);

#if UNITY_EDITOR
            UnityEditor.EditorUtility.SetDirty(rb);
#endif
        }
    }
}