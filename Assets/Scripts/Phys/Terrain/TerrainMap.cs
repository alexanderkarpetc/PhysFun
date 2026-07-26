using System.Collections.Generic;
using Materials;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// Hand-authored terrain: one palette index per pixel over a fixed region, plus the palette
    /// itself — which tile art and which physics material each index stands for.
    /// <see cref="TerrainBuilder"/> turns a map into chunk bodies; the Terrain Painter window
    /// edits one in the scene view.
    ///
    /// Cells are stored run-length encoded, because a painted map is mostly empty and mostly
    /// long horizontal runs: the asset stays a few KB rather than a megabyte of hex, and a
    /// stroke produces a diff you can actually read.
    /// </summary>
    [CreateAssetMenu(menuName = "PhysFun/Terrain Map", fileName = "TerrainMap")]
    public sealed class TerrainMap : ScriptableObject, ISerializationCallbackReceiver
    {
        /// <summary>What one palette index paints.</summary>
        [System.Serializable]
        public struct Entry
        {
            [Tooltip("Texture name under Resources/Sprites/Materials (no folder, no extension).")]
            public string tile;

            [Tooltip("Density, and whether this terrain burns.")]
            public PhysMaterialId physMaterial;
        }

        [Tooltip("Cells per world unit. Use the painter's Region controls to change this — " +
                 "editing it here reinterprets the existing cells and garbles the map.")]
        [SerializeField] private float pixelsPerUnit = 40f;

        [Tooltip("Bottom-left corner of the paintable region, in the builder's local space.")]
        [SerializeField] private Vector2 origin = new Vector2(-15f, -4.5f);

        [SerializeField] private int width = 1400;
        [SerializeField] private int height = 320;

        [Tooltip("Grows as you paint with new tile/material combinations.")]
        [SerializeField] private List<Entry> palette = new();

        [SerializeField, HideInInspector] private byte[] encoded;

        // Expanded lazily from `encoded`, never serialized directly.
        private byte[] _cells;

        public float PixelsPerUnit => Mathf.Max(1f, pixelsPerUnit);
        public Vector2 Origin => origin;
        public int Width => width;
        public int Height => height;
        public IReadOnlyList<Entry> Palette => palette;

        /// <summary>Region covered by the map, in the builder's local space.</summary>
        public Rect LocalBounds =>
            new Rect(origin, new Vector2(width / PixelsPerUnit, height / PixelsPerUnit));

        /// <summary>Palette index per cell, row-major from the bottom-left. 0 means empty.
        /// Callers may write into this directly; tell the builder what changed afterwards.</summary>
        public byte[] Cells
        {
            get
            {
                int n = Mathf.Max(1, width * height);
                if (_cells == null || _cells.Length != n) _cells = Decode(encoded, n);
                return _cells;
            }
        }

        /// <summary>Index for a tile+material pair, appending a palette entry the first time it
        /// is used. 1-based, since 0 is reserved for empty.</summary>
        public int Require(string tile, PhysMaterialId material)
        {
            if (string.IsNullOrEmpty(tile)) tile = "rock";

            for (int i = 0; i < palette.Count; i++)
                if (palette[i].tile == tile && palette[i].physMaterial == material)
                    return i + 1;

            if (palette.Count >= 254)
            {
                Debug.LogError("TerrainMap: palette is full (254 tile/material combinations).");
                return palette.Count;
            }

            palette.Add(new Entry { tile = tile, physMaterial = material });
            return palette.Count;
        }

        public Entry EntryAt(int id) =>
            id >= 1 && id <= palette.Count ? palette[id - 1] : default;

        /// <summary>Cell under a local-space point. Coordinates are written even when the point
        /// is outside, so a brush straddling the edge can still clamp and paint the rest.</summary>
        public bool LocalToPixel(Vector2 local, out int px, out int py)
        {
            float ppu = PixelsPerUnit;
            px = Mathf.FloorToInt((local.x - origin.x) * ppu);
            py = Mathf.FloorToInt((local.y - origin.y) * ppu);
            return px >= 0 && py >= 0 && px < width && py < height;
        }

        /// <summary>Centre of a cell, in local space.</summary>
        public Vector2 PixelToLocal(int px, int py)
        {
            float ppu = PixelsPerUnit;
            return new Vector2(origin.x + (px + 0.5f) / ppu, origin.y + (py + 0.5f) / ppu);
        }

        public void Clear()
        {
            var cells = Cells;
            System.Array.Clear(cells, 0, cells.Length);
        }

        /// <summary>
        /// Move or resize the paintable region, keeping whatever art lands inside it. Cells are
        /// copied by local position, so this also handles a change of resolution (nearest cell).
        /// </summary>
        public void Resize(Vector2 newOrigin, int newWidth, int newHeight, float newPixelsPerUnit)
        {
            newWidth = Mathf.Clamp(newWidth, 1, 16384);
            newHeight = Mathf.Clamp(newHeight, 1, 16384);
            newPixelsPerUnit = Mathf.Max(1f, newPixelsPerUnit);

            var old = Cells;
            int ow = width, oh = height;
            Vector2 oldOrigin = origin;
            float oldPpu = PixelsPerUnit;

            var next = new byte[newWidth * newHeight];
            for (int y = 0; y < newHeight; y++)
            {
                float ly = newOrigin.y + (y + 0.5f) / newPixelsPerUnit;
                int sy = Mathf.FloorToInt((ly - oldOrigin.y) * oldPpu);
                if (sy < 0 || sy >= oh) continue;

                int srcRow = sy * ow;
                int dstRow = y * newWidth;
                for (int x = 0; x < newWidth; x++)
                {
                    float lx = newOrigin.x + (x + 0.5f) / newPixelsPerUnit;
                    int sx = Mathf.FloorToInt((lx - oldOrigin.x) * oldPpu);
                    if (sx < 0 || sx >= ow) continue;
                    next[dstRow + x] = old[srcRow + sx];
                }
            }

            origin = newOrigin;
            width = newWidth;
            height = newHeight;
            pixelsPerUnit = newPixelsPerUnit;
            _cells = next;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Run-length coding
        // ─────────────────────────────────────────────────────────────────────────

        public void OnBeforeSerialize()
        {
            // A map that was loaded but never expanded has nothing new to say — re-encoding
            // a null buffer here would wipe what is on disk.
            if (_cells == null) return;
            encoded = Encode(_cells);
        }

        public void OnAfterDeserialize() => _cells = null;   // expanded on first access

        /// <summary>Runs of (value, count-lo, count-hi), counts up to 65535.</summary>
        private static byte[] Encode(byte[] cells)
        {
            var buf = new List<byte>(1024);
            int i = 0;
            while (i < cells.Length)
            {
                byte value = cells[i];
                int run = 1;
                while (i + run < cells.Length && cells[i + run] == value && run < 65535) run++;

                buf.Add(value);
                buf.Add((byte)(run & 0xFF));
                buf.Add((byte)(run >> 8));
                i += run;
            }
            return buf.ToArray();
        }

        private static byte[] Decode(byte[] data, int expected)
        {
            var cells = new byte[expected];
            if (data == null) return cells;

            int written = 0;
            for (int i = 0; i + 2 < data.Length && written < expected; i += 3)
            {
                byte value = data[i];
                int run = data[i + 1] | (data[i + 2] << 8);
                if (run <= 0) continue;

                int end = Mathf.Min(expected, written + run);
                if (value != 0)
                    for (int k = written; k < end; k++) cells[k] = value;
                written = end;
            }
            return cells;
        }
    }
}
