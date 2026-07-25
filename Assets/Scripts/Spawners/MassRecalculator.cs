using Materials;
using UnityEngine;

namespace Spawners
{
    public static class MassRecalculator
    {
        public static void SetMass(Sprite sprite, Rigidbody2D rb, Collider2D collider)
        {
            // Can be used for optimization
            // var rect = sprite.textureRect;
            // float pixelCount = rect.width * rect.height;
            // rb.mass = pixelCount * 0.0025f;   // 200x200 → 100

            if (!rb) return;

            float area;
            if (collider is CircleCollider2D circle) area = GetArea(circle);
            else if (collider is PolygonCollider2D poly) area = GetArea(poly);
            else return;

            // Material density is what makes wood lighter than the default stuff.
            float density = MaterialLibrary.Of(rb.gameObject).Density;

            // A sprite eaten down to a few pixels still needs a positive mass or
            // Rigidbody2D complains and the body goes haywire.
            rb.mass = Mathf.Max(0.01f, area * 100f * density);
        }
        
        // Reused: the array-returning GetPath allocates, and a fire-ragged sprite can
        // trace to hundreds of paths per rebuild.
        private static readonly System.Collections.Generic.List<Vector2> PathBuf = new();

        public static float GetArea(PolygonCollider2D poly)
        {
            float totalArea = 0f;

            for (int p = 0; p < poly.pathCount; p++)
            {
                poly.GetPath(p, PathBuf); // points in local space
                totalArea += Mathf.Abs(SignedPolygonArea(PathBuf));
            }

            // convert from local units to world units (scale affects it)
            Vector3 lossyScale = poly.transform.lossyScale;
            float scale = Mathf.Abs(lossyScale.x * lossyScale.y);
            return totalArea * scale;
        }

        public static float GetArea(CircleCollider2D circle)
        {
            // local radius
            float r = circle.radius;

            // apply transform scale (average x/y for uniform approximation)
            Vector3 s = circle.transform.lossyScale;
            float scale = Mathf.Abs((s.x + s.y) * 0.5f);

            float worldRadius = r * scale;
            float area = Mathf.PI * worldRadius * worldRadius;
            return area;
        }

        private static float SignedPolygonArea(System.Collections.Generic.List<Vector2> path)
        {
            float area = 0f;
            for (int i = 0; i < path.Count; i++)
            {
                int j = (i + 1) % path.Count;
                area += path[i].x * path[j].y - path[j].x * path[i].y;
            }
            return area * 0.5f;
        }
    }
}