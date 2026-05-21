using System.Collections.Generic;
using Spawners;
using UnityEngine;

public class SpriteEraseService
{
    private readonly Dictionary<GameObject, Texture2D> _textures = new();

    public void EraseCircle(GameObject go, Vector3 worldPos, float brushRadius)
    {
        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr) return;

        if (!_textures.TryGetValue(go, out var tex))
        {
            var sprite = sr.sprite;
            tex = SpriteTexUtil.CloneReadable(sprite);
            if (tex == null) return;

            sr.sprite = Sprite.Create(
                tex,
                new Rect(0, 0, tex.width, tex.height),
                new Vector2(0.5f, 0.5f),
                sprite.pixelsPerUnit);

            _textures[go] = tex;
        }

        var local = go.transform.InverseTransformPoint(worldPos);
        var sprite2 = sr.sprite;
        float ppu = sprite2.pixelsPerUnit;

        int cx = (int)(local.x * ppu + tex.width / 2);
        int cy = (int)(local.y * ppu + tex.height / 2);
        int r = Mathf.CeilToInt(brushRadius * ppu);

        for (int y = -r; y <= r; y++)
        {
            for (int x = -r; x <= r; x++)
            {
                if (x * x + y * y > r * r) continue;
                int px = cx + x;
                int py = cy + y;
                if (px < 0 || py < 0 || px >= tex.width || py >= tex.height) continue;

                var c = tex.GetPixel(px, py);
                c.a = 0;
                tex.SetPixel(px, py, c);
            }
        }
        tex.Apply();
    }

    public void RebuildAndMaybeSplit(GameObject go, int simplifyLevel)
    {
        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr) return;

        if (!_textures.TryGetValue(go, out var tex))
            tex = sr.sprite.texture;

        float ppu = sr.sprite.pixelsPerUnit;

        if (SpriteSplitUtil.TrySplit(go, tex, ppu, alphaThreshold: 0.1f, minPixels: 64, out var parts))
        {
            parts.Sort((a, b) => (b.rect.width * b.rect.height).CompareTo(a.rect.width * a.rect.height));

            ApplyPart(go, sr, parts[0].tex, parts[0].rect, ppu, simplifyLevel);
            int centerX = tex.width / 2;
            int centerY = tex.height / 2;

            for (int i = 1; i < parts.Count; i++)
            {
                var clone = Object.Instantiate(go, go.transform.parent);
                var bounds = parts[i].rect;
                float xShift = ((bounds.xMin + bounds.xMax) / 2f - centerX) / (2f * ppu);
                float yShift = ((bounds.yMin + bounds.yMax) / 2f - centerY) / (2f * ppu);
                clone.transform.position = new Vector2(go.transform.position.x + xShift, go.transform.position.y + yShift);
                ApplyPart(clone, clone.GetComponent<SpriteRenderer>(), parts[i].tex, parts[i].rect, ppu, simplifyLevel);
                _textures[clone] = parts[i].tex;
            }

            var mainBounds = parts[0].rect;
            float xMainShift = ((mainBounds.xMin + mainBounds.xMax) / 2f - centerX) / (2f * ppu);
            float yMainShift = ((mainBounds.yMin + mainBounds.yMax) / 2f - centerY) / (2f * ppu);
            go.transform.position = new Vector2(go.transform.position.x + xMainShift, go.transform.position.y + yMainShift);
            _textures[go] = parts[0].tex;
            return;
        }

        Object.DestroyImmediate(go.GetComponent<PolygonCollider2D>());
        var poly = go.AddComponent<PolygonCollider2D>();
        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }

    private static void ApplyPart(GameObject go, SpriteRenderer sr, Texture2D partTex, RectInt subRect, float ppu, int simplifyLevel)
    {
        var newSprite = Sprite.Create(partTex, new Rect(0, 0, partTex.width, partTex.height), new Vector2(0.5f, 0.5f), ppu);
        sr.sprite = newSprite;

        Object.DestroyImmediate(go.GetComponent<PolygonCollider2D>());
        var poly = go.AddComponent<PolygonCollider2D>();
        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }
}
