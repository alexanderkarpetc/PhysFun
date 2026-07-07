using System.Collections.Generic;
using Spawners;
using UnityEngine;

/// <summary>
/// In-place "split into disconnected pieces" for a sprite GameObject.
/// Largest connected component stays on the original; remaining components
/// become clones at world offsets matching their canvas-pixel positions.
/// Used by both the eraser (after a stroke disconnects an object) and
/// the synthesizer (after spawning a drawing that may contain several blobs).
/// </summary>
public static class SpriteSplitHelper
{
    /// <summary>
    /// Try splitting <paramref name="go"/>'s sprite into connected components.
    /// Returns the resulting GameObjects (including <paramref name="go"/>) when a
    /// split occurred, or null otherwise.
    /// </summary>
    public static List<GameObject> TrySplitInPlace(
        GameObject go,
        int simplifyLevel,
        float alphaThreshold = 0.1f,
        int minPixels = 64)
    {
        if (!go) return null;

        var sr = go.GetComponent<SpriteRenderer>();
        if (!sr || !sr.sprite) return null;

        var sprite = sr.sprite;
        var src = sprite.texture;
        if (!src) return null;

        // Need a CPU-readable copy. CloneReadable handles both readable and non-readable sources.
        var tex = src.isReadable ? src : SpriteTexUtil.CloneReadable(sprite);
        if (!tex) return null;

        bool splitOk = SpriteSplitUtil.TrySplit(tex, alphaThreshold, minPixels, out var parts);
        if (tex != src) Object.Destroy(tex); // temporary copy — pixels already extracted
        if (!splitOk) return null;

        // Largest piece first — it gets the existing GO.
        parts.Sort((a, b) => (b.rect.width * b.rect.height).CompareTo(a.rect.width * a.rect.height));

        float ppu = sprite.pixelsPerUnit;
        // Offsets are measured from the sprite pivot — that's where the GO origin sits.
        Vector2 pivotPx = sprite.pivot;

        var rotation = go.transform.rotation;
        var parent   = go.transform.parent;

        // Precompute world positions before mutating the original (its texture/rect changes below).
        var positions = new Vector3[parts.Count];
        for (int i = 0; i < parts.Count; i++)
        {
            var r = parts[i].rect;
            float cx = r.x + r.width  * 0.5f;
            float cy = r.y + r.height * 0.5f;
            // Pixel offset → local-space metres → world-space (respecting current scale + rotation).
            Vector3 localOffset = new Vector3((cx - pivotPx.x) / ppu, (cy - pivotPx.y) / ppu, 0f);
            positions[i] = go.transform.TransformPoint(localOffset);
        }

        var result = new List<GameObject>(parts.Count);

        ApplyPart(go, sr, parts[0].tex, ppu, simplifyLevel);
        go.transform.SetPositionAndRotation(positions[0], rotation);
        result.Add(go);

        for (int i = 1; i < parts.Count; i++)
        {
            var clone = Object.Instantiate(go, positions[i], rotation, parent);
            ApplyPart(clone, clone.GetComponent<SpriteRenderer>(), parts[i].tex, ppu, simplifyLevel);
            result.Add(clone);
        }

        return result;
    }

    private static void ApplyPart(GameObject go, SpriteRenderer sr, Texture2D partTex, float ppu, int simplifyLevel)
    {
        sr.sprite = Sprite.Create(
            partTex,
            new Rect(0, 0, partTex.width, partTex.height),
            new Vector2(0.5f, 0.5f),
            ppu);

        var existing = go.GetComponent<PolygonCollider2D>();
        if (existing) Object.DestroyImmediate(existing);
        var poly = go.AddComponent<PolygonCollider2D>();
        ColliderSimplifier2D.Simplify(poly, simplifyLevel);
        MassRecalculator.SetMass(null, go.GetComponent<Rigidbody2D>(), poly);
    }
}
