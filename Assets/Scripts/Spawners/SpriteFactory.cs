using UnityEngine;

namespace Spawners
{
    public static class SpriteFactory
    {
        private static float allScale = 0.5f;
        public static GameObject Create(Sprite sprite, Vector3 position, Transform parent = null, bool isTrigger = false, int simplifyLevel = 0)
        {
            var go = new GameObject(sprite.name);
            if (parent) go.transform.SetParent(parent, false);
            go.transform.position = position;

            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;

            var poly = go.AddComponent<PolygonCollider2D>();
            poly.isTrigger = isTrigger;

            go.AddComponent<Rigidbody2D>();
            go.transform.localScale = new Vector3(allScale, allScale, allScale);

            // simplify after collider is created from sprite physics shape
            ColliderSimplifier2D.Simplify(poly, simplifyLevel);

            return go;
        }
    }
}