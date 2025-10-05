using System.Collections.Generic;
using Spawners;
using UnityEngine;

public class SpriteEraser : MonoBehaviour
{
    [Header("Settings")]
    public bool eraseEnabled = true;
    public float brushRadius = 0.2f;
    public LayerMask targetLayer;
    public float colliderUpdateInterval = 0.2f; // seconds between collider rebuilds

    Camera _cam;
    Dictionary<GameObject, Texture2D> _textures = new();
    float _lastColliderUpdate;

    void Awake()
    {
        _cam = Camera.main;
    }

    void Update()
    {
        if (!eraseEnabled) return;

        if (Input.GetMouseButton(0))
        {
            Vector3 wp = _cam.ScreenToWorldPoint(Input.mousePosition);
            wp.z = 0f;

            var hits = Physics2D.OverlapCircleAll(wp, brushRadius, targetLayer);
            foreach (var h in hits)
                EraseOnObject(h.gameObject, wp);

            foreach (var h in hits)
            {
                RebuildAndMaybeSplit(h.gameObject, simplifyLevel: 2);
            }
        }
    }

    void EraseOnObject(GameObject go, Vector3 worldPos)
    {
        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr) return;

        // Ensure we have a unique texture clone for this object
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

        // erase circle in texture space
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
                c.a = 0; // erase
                tex.SetPixel(px, py, c);
            }
        }
        tex.Apply();
    }
    void RebuildAndMaybeSplit(GameObject go, int simplifyLevel)
    {
        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr) return;

        // Use our per-instance editable texture
        if (!_textures.TryGetValue(go, out var tex))
            tex = sr.sprite.texture;

        float ppu = sr.sprite.pixelsPerUnit;

        // 2. Detect split (connected components in alpha)
        if (SpriteSplitUtil.TrySplit(go, tex, ppu, alphaThreshold: 0.1f, minPixels: 64, out var parts))
        {
            // Sort by area; keep the largest on original object
            parts.Sort((a, b) => (b.rect.width * b.rect.height).CompareTo(a.rect.width * a.rect.height));

            // Apply largest to original
            ApplyPartToObject(go, sr, parts[0].tex, parts[0].rect, ppu, simplifyLevel);
            var centerX = tex.width / 2;
            var centerY = tex.height / 2;

            // Spawn others as clones
            for (int i = 1; i < parts.Count; i++)
            {
                var clone = Instantiate(go, go.transform.parent);
                var bounds = parts[i].rect;
                var xShift = ((bounds.xMin + bounds.xMax)/2 - centerX) /(2 * ppu);
                var yShift = ((bounds.yMin + bounds.yMax)/2 - centerY) /(2 * ppu);
                clone.transform.position = new Vector2(go.transform.position.x + xShift, go.transform.position.y + yShift);
                ApplyPartToObject(clone, clone.GetComponent<SpriteRenderer>(), parts[i].tex, parts[i].rect, ppu, simplifyLevel);
                _textures[clone] = parts[i].tex; // track its editable texture
            }
            
            var mainBounds = parts[0].rect;
            var xMainShift = ((mainBounds.xMin + mainBounds.xMax)/2 - centerX) /(2 * ppu);
            var yMainShift = ((mainBounds.yMin + mainBounds.yMax)/2 - centerY) /(2 * ppu);

            go.transform.position = new Vector2(go.transform.position.x + xMainShift, go.transform.position.y + yMainShift);
            // Cache tex for original
            _textures[go] = parts[0].tex;
            return;
        }

        // Hard reset collider to avoid stale geometry
        DestroyImmediate(go.GetComponent<PolygonCollider2D>());
        var poly = go.AddComponent<PolygonCollider2D>();

        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }
    
    void ApplyPartToObject(GameObject go, SpriteRenderer sr, Texture2D partTex, RectInt subRect, float ppu, int simplifyLevel)
    {
        // Create a centered-pivot sprite from the subtexture (no pivot preservation)
        var newSprite = Sprite.Create(partTex, new Rect(0, 0, partTex.width, partTex.height), new Vector2(0.5f, 0.5f), ppu);
        sr.sprite = newSprite;

        // Rebuild collider for this piece

        DestroyImmediate(go.GetComponent<PolygonCollider2D>());
        var poly = go.AddComponent<PolygonCollider2D>();

        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }
}