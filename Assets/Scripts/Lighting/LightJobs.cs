using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;
using UnityEngine;

namespace Lighting
{
    /// <summary>
    /// How solid each light cell is, 0 (air) to 1 (rock), from the sight map: the share of
    /// its sight cells that are standing terrain. One row of light cells per index.
    /// </summary>
    [BurstCompile]
    internal struct LightOpacityJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<byte> Solid;
        public int SolidW, SolidH;
        public float2 SolidOrigin;
        public float SolidCell;

        [WriteOnly, NativeDisableParallelForRestriction] public NativeArray<float> Opacity;
        public int2 GridMin;            // light cell (0, 0), in light cells from the world origin
        public int GridW;
        public float Cell;

        public void Execute(int y)
        {
            int sub = math.max(1, (int)math.round(Cell / SolidCell));
            float inv = 1f / (sub * sub);
            for (int x = 0; x < GridW; x++)
            {
                float2 corner = new float2(GridMin.x + x, GridMin.y + y) * Cell;
                int sx0 = (int)math.floor((corner.x - SolidOrigin.x) / SolidCell);
                int sy0 = (int)math.floor((corner.y - SolidOrigin.y) / SolidCell);
                int n = 0;
                for (int j = 0; j < sub; j++)
                {
                    int sy = sy0 + j;
                    if ((uint)sy >= (uint)SolidH) continue;
                    int row = sy * SolidW;
                    for (int i = 0; i < sub; i++)
                    {
                        int sx = sx0 + i;
                        if ((uint)sx < (uint)SolidW && Solid[row + sx] != 0) n++;
                    }
                }
                Opacity[y * GridW + x] = n * inv;
            }
        }
    }

    /// <summary>
    /// One light per index: how far its light has to travel to reach each cell of a square
    /// round it, then how much of it arrives. Travel through rock costs <see cref="WallCost"/>
    /// times as much as through air, so a light fills its room, creeps round a corner and
    /// lights the first few pixels of a wall - the cellular lighting of Starbound and Terraria,
    /// on the light grid. The distances are a chamfer sweep: four raster passes, alternating
    /// direction, each taking the cheapest of the neighbours already visited.
    /// </summary>
    [BurstCompile]
    internal struct LightSpreadJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<float> Opacity;
        public int GridW, GridH;

        /// <summary>Per light: x, y in light cells from the grid's corner (fractional), radius
        /// in light cells.</summary>
        [ReadOnly] public NativeArray<float4> Lights;

        /// <summary>Per light, a square of Stride x Stride cells centred on the light's cell:
        /// first the distance, then (written over it) the share of the light that arrives.</summary>
        [NativeDisableParallelForRestriction] public NativeArray<float> Reach;
        public int Stride;              // 2 * MaxRadius + 1
        public float WallCost;

        public void Execute(int k)
        {
            float4 l = Lights[k];
            int half = Stride / 2;
            int cx = (int)math.floor(l.x), cy = (int)math.floor(l.y);
            int r = math.min(half, (int)math.ceil(l.z) + 1);
            int baseIdx = k * Stride * Stride;

            // The square this light needs, inside its slot (lx, ly) and the grid.
            int x0 = math.max(half - r, half - cx), x1 = math.min(half + r, half + (GridW - 1 - cx));
            int y0 = math.max(half - r, half - cy), y1 = math.min(half + r, half + (GridH - 1 - cy));
            if (x0 > x1 || y0 > y1) return;

            const float Far = 1e9f;
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                // Seeded from the light's true position, so it does not jump a cell at a time.
                float dx = (cx - half + x + 0.5f) - l.x, dy = (cy - half + y + 0.5f) - l.y;
                float d2 = dx * dx + dy * dy;
                Reach[baseIdx + y * Stride + x] = d2 <= 2f ? math.sqrt(d2) : Far;
            }

            const float Diag = 1.41421356f;
            for (int pass = 0; pass < 4; pass++)
            {
                bool forward = (pass & 1) == 0;
                int dir = forward ? 1 : -1;
                int ys = forward ? y0 : y1, ye = forward ? y1 + 1 : y0 - 1;
                int xs = forward ? x0 : x1, xe = forward ? x1 + 1 : x0 - 1;
                for (int y = ys; y != ye; y += dir)
                {
                    int gy = cy - half + y;
                    for (int x = xs; x != xe; x += dir)
                    {
                        int gx = cx - half + x;
                        int i = baseIdx + y * Stride + x;
                        float cost = 1f + WallCost * Opacity[gy * GridW + gx];
                        float d = Reach[i];

                        int py = y - dir;                       // the row already swept
                        int px = x - dir;                       // the cell already swept in this row
                        if (px >= x0 && px <= x1) d = math.min(d, Reach[i - dir] + cost);
                        if (py >= y0 && py <= y1)
                        {
                            int row = baseIdx + py * Stride;
                            d = math.min(d, Reach[row + x] + cost);
                            if (x - 1 >= x0) d = math.min(d, Reach[row + x - 1] + cost * Diag);
                            if (x + 1 <= x1) d = math.min(d, Reach[row + x + 1] + cost * Diag);
                        }
                        Reach[i] = d;
                    }
                }
            }

            // Distance to share: full at the light, a smooth fall to nothing at its radius.
            float inv = 1f / math.max(1e-3f, l.z);
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                int i = baseIdx + y * Stride + x;
                float t = math.saturate(Reach[i] * inv);
                Reach[i] = 1f - t * t * (3f - 2f * t);
            }
        }
    }

    /// <summary>
    /// Sum every light over each cell, on top of the ambient, into the light map's texels.
    /// The map is drawn as a 2x multiply, so a texel holds half the light: 0.5 leaves the
    /// world as drawn, less darkens it, more brightens and tints it. One row per index.
    /// </summary>
    [BurstCompile]
    internal struct LightGatherJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<float> Reach;
        [ReadOnly] public NativeArray<float4> Lights;
        /// <summary>Per light, its colour times its intensity.</summary>
        [ReadOnly] public NativeArray<float4> Colors;
        public int LightCount, Stride, GridW;

        public float3 Ambient;
        public float Max;

        [WriteOnly, NativeDisableParallelForRestriction] public NativeArray<Color32> Texels;

        public void Execute(int y)
        {
            int half = Stride / 2;
            for (int x = 0; x < GridW; x++)
            {
                float3 sum = Ambient;
                for (int k = 0; k < LightCount; k++)
                {
                    float4 l = Lights[k];
                    // Only the square the spread wrote this frame; the rest of the slot is stale.
                    int r = math.min(half, (int)math.ceil(l.z) + 1);
                    int ox = x - (int)math.floor(l.x), oy = y - (int)math.floor(l.y);
                    if (math.abs(ox) > r || math.abs(oy) > r) continue;
                    float a = Reach[k * Stride * Stride + (oy + half) * Stride + ox + half];
                    if (a > 0f) sum += Colors[k].xyz * a;
                }
                sum = math.min(sum, Max) * (255f * 0.5f);
                Texels[y * GridW + x] = new Color32((byte)sum.x, (byte)sum.y, (byte)sum.z, 255);
            }
        }
    }
}
