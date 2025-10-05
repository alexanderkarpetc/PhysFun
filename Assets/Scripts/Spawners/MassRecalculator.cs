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

            if (collider is CircleCollider2D circle)
                rb.mass = GetArea(circle) * 100;
            else if (collider is PolygonCollider2D poly)
                rb.mass = GetArea(poly) * 100;
        }
        
        public static float GetArea(PolygonCollider2D poly)
        {
            float totalArea = 0f;

            for (int p = 0; p < poly.pathCount; p++)
            {
                var path = poly.GetPath(p); // array of points (local space)
                totalArea += Mathf.Abs(SignedPolygonArea(path));
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

        private static float SignedPolygonArea(Vector2[] path)
        {
            float area = 0f;
            for (int i = 0; i < path.Length; i++)
            {
                int j = (i + 1) % path.Length;
                area += path[i].x * path[j].y - path[j].x * path[i].y;
            }
            return area * 0.5f;
        }
    }
}