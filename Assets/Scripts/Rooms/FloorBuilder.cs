using System.Collections.Generic;
using Phys.Terrain;
using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// Builds one floor: lays its rooms out (<see cref="FloorLayout"/>), then makes a single
    /// terrain out of all of them. Everything goes into the active scene, which the loader has
    /// made a fresh scene of its own, so unloading it takes the whole floor and everything
    /// spawned on it.
    ///
    /// The terrain is one runtime <see cref="TerrainMap"/> the size of the floor, built in
    /// this order:
    /// <list type="number">
    /// <item>fill everywhere - Default rock under the recipe's fill tile;</item>
    /// <item>each room's map stamped in as is (its palette remapped onto the floor's);</item>
    /// <item>the stub of every socket no corridor uses filled back in;</item>
    /// <item>the corridors cut, as a box of the corridor bore swept along each route.</item>
    /// </list>
    /// One TerrainBuilder then builds it, so there are no seams between rooms and the fill:
    /// you can dig from any room into any other. The floor's border is Untouchable bedrock,
    /// which the support pass hangs everything from.
    /// </summary>
    public static class FloorBuilder
    {
        public sealed class Result
        {
            public GameObject Root;
            public Vector3 Start;
            public bool FaceRight = true;
        }

        /// <summary>
        /// <paramref name="rooms"/> are templates - prefab assets, or rooms lying switched off
        /// in an open scene - and the first one is where the floor starts.
        /// </summary>
        public static Result Build(FloorRecipe recipe, IReadOnlyList<Room> rooms, int seed)
        {
            var rng = new System.Random(seed);
            var usable = new List<Room>();
            float ppu = 0f;
            foreach (var r in rooms)
            {
                if (!r || !r.Map) { Debug.LogWarning($"FloorBuilder: room '{(r ? r.name : "null")}' has no map; skipped."); continue; }
                if (ppu == 0f) ppu = r.Map.PixelsPerUnit;
                if (!Mathf.Approximately(r.Map.PixelsPerUnit, ppu))
                {
                    Debug.LogWarning($"FloorBuilder: room '{r.name}' is at {r.Map.PixelsPerUnit} cells per unit, " +
                                     $"not {ppu} like the rest; skipped.", r);
                    continue;
                }
                usable.Add(r);
            }
            if (usable.Count == 0) { Debug.LogError("FloorBuilder: no usable rooms."); return null; }

            // ── plan ───────────────────────────────────────────────────────────────
            var shapes = new List<FloorLayout.RoomShape>();
            foreach (var r in usable)
            {
                var sockets = r.Sockets;
                var s = new FloorLayout.SocketShape[sockets.Length];
                for (int i = 0; i < sockets.Length; i++)
                    s[i] = new FloorLayout.SocketShape
                    {
                        Side = sockets[i].Side,
                        Point = sockets[i].transform.position - r.transform.position,
                        Size = sockets[i].Size,
                        Depth = sockets[i].Depth,
                    };
                shapes.Add(new FloorLayout.RoomShape { Local = r.LocalRect, Sockets = s });
            }
            var plan = FloorLayout.Plan(shapes, new FloorLayout.Settings
            {
                Gap = recipe.Gap,
                Jitter = recipe.Jitter,
                Margin = recipe.Margin,
                ExtraLinks = recipe.ExtraLinks,
                CorridorSize = recipe.CorridorSize,
                CellSnap = 1f / ppu,
            }, rng);

            // ── terrain ────────────────────────────────────────────────────────────
            var bounds = plan.Bounds;
            int w = Mathf.CeilToInt(bounds.width * ppu);
            int h = Mathf.CeilToInt(bounds.height * ppu);
            var map = ScriptableObject.CreateInstance<TerrainMap>();
            map.name = "Floor";
            map.Resize(Vector2.zero, w, h, ppu);
            var cells = map.Cells;
            byte fill = (byte)map.Require(recipe.FillTile, recipe.FillMaterial);
            for (int i = 0; i < cells.Length; i++) cells[i] = fill;

            for (int i = 0; i < usable.Count; i++)
                Stamp(map, cells, w, h, usable[i].Map, CellOf(plan.Rects[i].min, bounds, ppu));

            for (int i = 0; i < shapes.Count; i++)
            for (int j = 0; j < shapes[i].Sockets.Length; j++)
            {
                if (plan.Used.Contains((i, j))) continue;
                var s = shapes[i].Sockets[j];
                var stub = RoomSocket.StubRect(s.Side, plan.Mouth(i, s), s.Size, s.Depth);
                FillRect(cells, w, h, stub, bounds, ppu, from: 0, to: fill);
            }

            float bore = recipe.CorridorSize;
            foreach (var route in plan.Corridors)
                for (int k = 1; k < route.Count; k++)
                    Sweep(cells, w, h, route[k - 1], route[k], bore, bounds, ppu);

            // ── objects ────────────────────────────────────────────────────────────
            var root = new GameObject($"Floor (seed {seed})");
            root.transform.position = bounds.min;
            root.AddComponent<FloorGizmos>().Set(plan);

            var terrainGo = new GameObject("Terrain");
            terrainGo.SetActive(false);                 // so it builds from the map, not its defaults
            terrainGo.transform.SetParent(root.transform, false);
            terrainGo.AddComponent<TerrainBuilder>().SetMap(map);
            terrainGo.SetActive(true);

            AddBedrock(root.transform, bounds);

            var holder = new GameObject("Rooms");
            holder.SetActive(false);                    // nothing in a room wakes before it is in place
            holder.transform.SetParent(root.transform, false);
            var placed = new List<Room>();
            for (int i = 0; i < usable.Count; i++)
            {
                var go = Object.Instantiate(usable[i].gameObject, holder.transform);
                go.name = usable[i].name;
                go.transform.position = plan.Positions[i];
                foreach (var tb in go.GetComponentsInChildren<TerrainBuilder>(true))
                {
                    if (tb.gameObject == go) Object.DestroyImmediate(tb);
                    else Object.DestroyImmediate(tb.gameObject);
                }
                go.SetActive(true);
                placed.Add(go.GetComponent<Room>());
            }
            holder.SetActive(true);

            var result = new Result { Root = root };
            var entry = placed[0].FindEntry("");
            if (entry)
            {
                result.Start = entry.transform.position;
                result.FaceRight = entry.FaceRight;
            }
            else
            {
                result.Start = plan.Rects[0].center;
                Debug.LogWarning($"FloorBuilder: start room '{usable[0].name}' has no RoomEntry; starting in its middle.");
            }
            return result;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Cells
        // ─────────────────────────────────────────────────────────────────────────

        private static Vector2Int CellOf(Vector2 p, Rect bounds, float ppu) =>
            new(Mathf.RoundToInt((p.x - bounds.xMin) * ppu), Mathf.RoundToInt((p.y - bounds.yMin) * ppu));

        private static void Stamp(TerrainMap floor, byte[] cells, int w, int h, TerrainMap room, Vector2Int at)
        {
            var remap = new byte[256];
            var palette = room.Palette;
            for (int i = 0; i < palette.Count; i++)
                remap[i + 1] = (byte)floor.Require(palette[i].tile, palette[i].physMaterial);

            var src = room.Cells;
            int rw = room.Width, rh = room.Height;
            for (int y = 0; y < rh; y++)
            {
                int fy = at.y + y;
                if (fy < 0 || fy >= h) continue;
                for (int x = 0; x < rw; x++)
                {
                    int fx = at.x + x;
                    if (fx < 0 || fx >= w) continue;
                    cells[fy * w + fx] = remap[src[y * rw + x]];
                }
            }
        }

        private static void FillRect(byte[] cells, int w, int h, Rect r, Rect bounds, float ppu, byte from, byte to)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt((r.xMin - bounds.xMin) * ppu));
            int x1 = Mathf.Min(w - 1, Mathf.CeilToInt((r.xMax - bounds.xMin) * ppu) - 1);
            int y0 = Mathf.Max(0, Mathf.FloorToInt((r.yMin - bounds.yMin) * ppu));
            int y1 = Mathf.Min(h - 1, Mathf.CeilToInt((r.yMax - bounds.yMin) * ppu) - 1);
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
                if (cells[y * w + x] == from) cells[y * w + x] = to;
        }

        /// <summary>Carve a box `bore` wide and `bore` tall standing on each point from a to b.
        /// Level runs get a flat floor at the route's height; climbs get a shaft centred on it.</summary>
        private static void Sweep(byte[] cells, int w, int h, Vector2 a, Vector2 b, float bore, Rect bounds, float ppu)
        {
            float len = Vector2.Distance(a, b);
            int steps = Mathf.Max(1, Mathf.CeilToInt(len * ppu / 4f));
            float half = bore * 0.5f;
            for (int i = 0; i <= steps; i++)
            {
                var p = Vector2.Lerp(a, b, i / (float)steps);
                var r = new Rect(p.x - half, p.y, bore, bore);
                int x0 = Mathf.Max(0, Mathf.FloorToInt((r.xMin - bounds.xMin) * ppu));
                int x1 = Mathf.Min(w - 1, Mathf.CeilToInt((r.xMax - bounds.xMin) * ppu) - 1);
                int y0 = Mathf.Max(0, Mathf.FloorToInt((r.yMin - bounds.yMin) * ppu));
                int y1 = Mathf.Min(h - 1, Mathf.CeilToInt((r.yMax - bounds.yMin) * ppu) - 1);
                for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                    cells[y * w + x] = 0;
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Bedrock
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Four Untouchable slabs just overlapping the floor's outer edge: what the
        /// support pass counts as ground, and what keeps anything from leaving the floor.</summary>
        private static void AddBedrock(Transform parent, Rect bounds)
        {
            int layer = LayerMask.NameToLayer("Untouchable");
            var go = new GameObject("Bedrock");
            if (layer >= 0) go.layer = layer;
            go.transform.SetParent(parent, false);
            go.transform.position = Vector3.zero;

            const float t = 2f, overlap = 0.05f;
            var c = bounds.center;
            Box(go, new Vector2(bounds.xMin - t * 0.5f + overlap, c.y), new Vector2(t, bounds.height + 2f * t));
            Box(go, new Vector2(bounds.xMax + t * 0.5f - overlap, c.y), new Vector2(t, bounds.height + 2f * t));
            Box(go, new Vector2(c.x, bounds.yMin - t * 0.5f + overlap), new Vector2(bounds.width + 2f * t, t));
            Box(go, new Vector2(c.x, bounds.yMax + t * 0.5f - overlap), new Vector2(bounds.width + 2f * t, t));
        }

        private static void Box(GameObject go, Vector2 center, Vector2 size)
        {
            var box = go.AddComponent<BoxCollider2D>();
            box.offset = center;
            box.size = size;
        }
    }
}
