using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;

namespace Vision
{
    /// <summary>
    /// One ray of sight per index, for <see cref="FogOfWar"/>: march the terrain map until
    /// something solid, then mark every fog cell along the way, fading past the eye's full
    /// range and a little way into the wall that stopped it.
    /// </summary>
    [BurstCompile]
    internal struct FogRayJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<byte> Solid;
        public int SolidW, SolidH;
        public float2 SolidOrigin;
        public float SolidCell;

        /// <summary>Shut doors, as xMin, yMin, xMax, yMax.</summary>
        [ReadOnly] public NativeArray<float4> Doors;
        public int DoorCount;

        // Rays share cells and two may write one at once. A lost write costs that cell one
        // frame's worth of sight; the next frame's rays put it back.
        [NativeDisableParallelForRestriction] public NativeArray<byte> Seen;
        public int2 SeenMin;
        public int SeenW, SeenH;
        public float FogCell;

        public float2 Eye;
        public float Radius, Full, Depth;
        public float AngleStep, Turn;
        public int FirstRay, RayCount;

        public void Execute(int k)
        {
            int i = (FirstRay + k) % RayCount;
            float a = (i + Turn) * AngleStep;
            float2 dir = new float2(math.cos(a), math.sin(a));

            float block = March(dir);
            float end = math.min(Radius, block + Depth);
            float stride = FogCell * 0.5f;

            for (float d = 0f; d <= end; d += stride)
            {
                float s = d <= Full ? 1f : 1f - math.smoothstep(0f, 1f, (d - Full) / (Radius - Full));
                if (d > block) s *= 1f - (d - block) / Depth;
                if (s <= 0f) break;

                float2 p = Eye + dir * d;
                int cx = (int)math.floor(p.x / FogCell) - SeenMin.x;
                int cy = (int)math.floor(p.y / FogCell) - SeenMin.y;
                if ((uint)cx >= (uint)SeenW || (uint)cy >= (uint)SeenH) continue;

                byte v = (byte)math.clamp((int)math.round(s * 255f), 0, 255);
                int idx = cy * SeenW + cx;
                if (Seen[idx] < v) Seen[idx] = v;
            }
        }

        /// <summary>Distance to the first solid map cell or shut door, one map cell per step.</summary>
        private float March(float2 dir)
        {
            float inv = 1f / SolidCell;
            float2 f = (Eye - SolidOrigin) * inv;
            int n = (int)(Radius * inv);

            for (int i = 1; i <= n; i++)
            {
                float2 c = f + dir * i;
                if (c.x >= 0f && c.y >= 0f && c.x < SolidW && c.y < SolidH
                    && Solid[(int)c.y * SolidW + (int)c.x] != 0)
                    return i * SolidCell;

                if (DoorCount == 0) continue;
                float2 p = Eye + dir * (i * SolidCell);
                for (int j = 0; j < DoorCount; j++)
                {
                    float4 r = Doors[j];
                    if (p.x >= r.x && p.y >= r.y && p.x < r.z && p.y < r.w) return i * SolidCell;
                }
            }
            return Radius;
        }
    }

    /// <summary>
    /// The fog texture for the view: each cell's shown value eased up towards what has been
    /// seen, then copied out. Only cells on screen ease - one scrolled off picks up where it
    /// left off when it comes back.
    /// </summary>
    [BurstCompile]
    internal struct FogFillJob : IJob
    {
        [ReadOnly] public NativeArray<byte> Seen;
        public NativeArray<byte> Shown;
        public int2 SeenMin;
        public int SeenW, SeenH;

        [WriteOnly] public NativeArray<byte> Texels;
        public int2 ViewMin;
        public int ViewW, ViewH;
        public int Fade;

        public void Execute()
        {
            for (int y = 0; y < ViewH; y++)
            {
                int gy = ViewMin.y + y - SeenMin.y;
                int row = y * ViewW;

                for (int x = 0; x < ViewW; x++)
                {
                    int gx = ViewMin.x + x - SeenMin.x;
                    if ((uint)gx >= (uint)SeenW || (uint)gy >= (uint)SeenH)
                    {
                        Texels[row + x] = 0;
                        continue;
                    }

                    int i = gy * SeenW + gx;
                    int shown = Shown[i], seen = Seen[i];
                    if (shown < seen)
                    {
                        shown = math.min(seen, shown + Fade);
                        Shown[i] = (byte)shown;
                    }
                    Texels[row + x] = (byte)shown;
                }
            }
        }
    }
}
