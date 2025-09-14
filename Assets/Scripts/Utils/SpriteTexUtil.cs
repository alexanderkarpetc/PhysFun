using UnityEngine;

public static class SpriteTexUtil
{
    // Clone only the sprite's rect from its source texture.
    public static Texture2D CloneReadable(Sprite s)
    {
        var src = s.texture;
        if (src == null) return null;
        if (!src.isReadable)
        {
            Debug.LogError($"Texture '{src.name}' is not Read/Write enabled.");
            return null;
        }

        // Use textureRect (float) -> round to ints for block copy
        Rect r = s.textureRect;
        int x = Mathf.RoundToInt(r.x);
        int y = Mathf.RoundToInt(r.y);
        int w = Mathf.RoundToInt(r.width);
        int h = Mathf.RoundToInt(r.height);

        // Clamp to source bounds to be safe
        x = Mathf.Clamp(x, 0, src.width - 1);
        y = Mathf.Clamp(y, 0, src.height - 1);
        w = Mathf.Clamp(w, 1, src.width - x);
        h = Mathf.Clamp(h, 1, src.height - y);

        // Copy sub-rect (Color[], not Color32)
        Color[] block = src.GetPixels(x, y, w, h);

        // Create new readable texture and fill it
        var tex = new Texture2D(w, h, TextureFormat.ARGB32, false);
        tex.SetPixels(block);
        tex.Apply(false, false);
        return tex;
    }
}