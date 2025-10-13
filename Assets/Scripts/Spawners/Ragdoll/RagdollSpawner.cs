using UnityEngine;

namespace Spawners
{
    public class RagdollSpawner : MonoBehaviour
    {
        [SerializeField] BodyUVAsset uv;
        [SerializeField] SpriteRenderer animRenderer; // your current animated renderer
        [SerializeField] Transform root;              // where to spawn ragdoll parts

        public Vector2? GetPartLocal(UVPart part, string anim, int frame)
        {
            var f = uv.frames.Find(x => x.anim == anim && x.frame == frame);
            if (f.points == null) return null;
            foreach (var e in f.points) if (e.part == part) return e.uv;
            return null;
        }

        public Vector3 FrameSpaceToWorld(Vector2 uv01)
        {
            // convert normalized frame point to world, using current sprite bounds
            var s = animRenderer.sprite;
            var rect = s.rect; // px
            Vector2 local = new Vector2(
                (uv01.x - s.pivot.x / rect.width) * (rect.width / s.pixelsPerUnit),
                (uv01.y - s.pivot.y / rect.height) * (rect.height / s.pixelsPerUnit)
            );
            return animRenderer.transform.TransformPoint(local);
        }
    }
}