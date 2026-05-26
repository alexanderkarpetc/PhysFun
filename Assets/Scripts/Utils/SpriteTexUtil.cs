using UnityEngine;

public static class SpriteTexUtil
{
    /// <summary>
    /// Returns a new writable Texture2D containing the sprite's pixels.
    /// Works whether or not the source texture has Read/Write enabled —
    /// non-readable sources go through a GPU blit + ReadPixels path.
    /// </summary>
    public static Texture2D CloneReadable(Sprite s)
    {
        var src = s.texture;
        if (src == null) return null;

        Rect r = s.textureRect;
        int x = Mathf.RoundToInt(r.x);
        int y = Mathf.RoundToInt(r.y);
        int w = Mathf.RoundToInt(r.width);
        int h = Mathf.RoundToInt(r.height);

        x = Mathf.Clamp(x, 0, src.width - 1);
        y = Mathf.Clamp(y, 0, src.height - 1);
        w = Mathf.Clamp(w, 1, src.width - x);
        h = Mathf.Clamp(h, 1, src.height - y);

        // Fast path: CPU-side copy when the source is Read/Write enabled.
        if (src.isReadable)
        {
            var tex = new Texture2D(w, h, TextureFormat.ARGB32, false);
            tex.SetPixels(src.GetPixels(x, y, w, h));
            tex.Apply(false, false);
            return tex;
        }

        // Slow path: blit the source into a temp RenderTexture, then ReadPixels.
        // No import settings required — works at runtime on any sprite.
        var prev = RenderTexture.active;
        var rt = RenderTexture.GetTemporary(
            src.width, src.height, 0,
            RenderTextureFormat.ARGB32,
            RenderTextureReadWrite.sRGB);

        try
        {
            Graphics.Blit(src, rt);
            RenderTexture.active = rt;

            var tex = new Texture2D(w, h, TextureFormat.ARGB32, false);
            tex.ReadPixels(new Rect(x, y, w, h), 0, 0);
            tex.Apply(false, false);
            return tex;
        }
        finally
        {
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
        }
    }
}
