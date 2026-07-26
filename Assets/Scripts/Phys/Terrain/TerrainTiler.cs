using System.Collections.Generic;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// Loads the small tileable material textures under <c>Resources/Sprites/Materials</c>
    /// and hands out their pixels so terrain can be filled with real rock/soil/brick art
    /// instead of a flat colour.
    ///
    /// Sampling is done in <em>global</em> terrain pixel coordinates, which is what keeps
    /// the pattern continuous across chunk borders — a chunk has no idea it is a chunk.
    /// </summary>
    public static class TerrainTiler
    {
        private const string ResourceFolder = "Sprites/Materials/";

        public sealed class Tile
        {
            private readonly Color32[] _pixels;
            public readonly int Width;
            public readonly int Height;

            public Tile(Color32[] pixels, int width, int height)
            {
                _pixels = pixels;
                Width = Mathf.Max(1, width);
                Height = Mathf.Max(1, height);
            }

            /// <summary>Colour for a terrain pixel, wrapping the tile over the whole map.
            /// Alpha is forced opaque — alpha is what the collider tracer reads as "solid",
            /// so a tile with soft edges would punch holes in the terrain.</summary>
            public Color32 Sample(int gx, int gy)
            {
                var c = _pixels[Wrap(gy, Height) * Width + Wrap(gx, Width)];
                c.a = 255;
                return c;
            }

            private static int Wrap(int v, int n)
            {
                int m = v % n;
                return m < 0 ? m + n : m;
            }
        }

        private static readonly Dictionary<string, Tile> Cache = new();

        /// <summary>Tile for a texture name (no folder, no extension). Never returns null —
        /// a missing texture falls back to a flat colour so a typo can't take the map out.</summary>
        public static Tile Load(string name)
        {
            if (string.IsNullOrEmpty(name)) name = "rock";
            if (Cache.TryGetValue(name, out var cached)) return cached;

            var tile = Build(name);
            Cache[name] = tile;
            return tile;
        }

        public static void ClearCache() => Cache.Clear();

        private static Tile Build(string name)
        {
            var source = Resources.Load<Texture2D>(ResourceFolder + name);
            if (!source)
            {
                Debug.LogWarning($"TerrainTiler: no texture at Resources/{ResourceFolder}{name} — " +
                                 "falling back to flat grey.");
                return Solid(new Color32(120, 118, 112, 255));
            }

            var readable = SpriteTexUtil.CloneReadable(source);
            if (!readable) return Solid(new Color32(120, 118, 112, 255));

            var tile = new Tile(readable.GetPixels32(), readable.width, readable.height);
            Object.Destroy(readable);   // pixels are on the CPU now
            return tile;
        }

        private static Tile Solid(Color32 color) => new(new[] { color }, 1, 1);
    }
}
