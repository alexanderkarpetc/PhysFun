using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace NoitaImport
{
    /// <summary>One piece of the corpse, as read off disk and analysed. Editor-side only.</summary>
    public sealed class PartBuild
    {
        public string Name;
        public int SourceOrder;

        /// <summary>Frame-sized pixel block, top-down rows (row 0 is the top of the frame).</summary>
        public Color32[] Pixels;
        public int W, H;

        public RectInt Bounds;                      // opaque bounds, top-down frame pixels
        public readonly List<Vector2Int> Solid = new();
        public readonly List<Vector2Int> Edge = new();

        public int Parent = -1;
        public Vector2 AnchorPx;                    // hinge point shared with the parent
        public Vector2 PivotPx;                     // bounds centre — what a pose positions

        public bool HasUv;
        public Color32 UvColor;

        /// <summary>Colour whose marker drives this piece's rotation — its own, or a child's.</summary>
        public bool HasTip;
        public int TipKey;
        public Vector2 Tip0;

        public Color32 At(int x, int y) => Pixels[y * W + x];
        public bool SolidAt(int x, int y) => x >= 0 && y >= 0 && x < W && y < H && Pixels[y * W + x].a > 0;
    }

    public sealed class PoseBuild
    {
        public string Anim;
        public int Frame;
        public Vector2[] Pos;   // per part, frame pixels
        public float[] Rot;     // per part, degrees, Unity CCW
    }

    /// <summary>Everything the importer needs to emit assets for one creature.</summary>
    public sealed class RagdollBuild
    {
        public string Creature;
        public List<PartBuild> Parts = new();       // topological: parents before children
        public int FrameW, FrameH;
        public Vector2 OriginPx;
        public string DefaultAnim;
        public List<PoseBuild> Poses = new();
        public List<string> Warnings = new();
    }

    /// <summary>
    /// Turns an unpacked Noita `data` folder into ragdoll data.
    ///
    /// Two separate authoring artefacts get combined here:
    /// <list type="bullet">
    /// <item>`data/ragdolls/&lt;creature&gt;/*.png` — one frame-sized image per body part, each
    /// holding just that part, drawn where it sits in the creature's first animation frame.
    /// Which piece connects to which is not written down anywhere, so it is recovered from
    /// how the parts touch.</item>
    /// <item>`data/enemies_gfx/&lt;creature&gt;_uv_src.png` — the same sheet layout as the sprite
    /// sheet, with one marker pixel per body part per frame (plus a translucent area for some
    /// of them). That is the record of where the arms and legs were on every frame, so a
    /// corpse can be built in the pose the creature died in.</item>
    /// </list>
    /// </summary>
    public static class NoitaRagdollSource
    {
        private const int MinAssignScore = -3; // marker further than ~3px from a part means "not this part"

        public static RagdollBuild Build(string dataRoot, string creature)
        {
            var build = new RagdollBuild { Creature = creature };

            var files = NoitaPaths.PartFiles(dataRoot, creature);
            if (files.Count == 0)
            {
                build.Warnings.Add("no part images found");
                return build;
            }

            // ── parts ────────────────────────────────────────────────────────────────
            int order = 0;
            foreach (var (name, path) in files)
            {
                var part = LoadPart(name, path, order);
                if (part == null)
                {
                    build.Warnings.Add($"unreadable part image: {Path.GetFileName(path)}");
                    continue;
                }
                if (part.Solid.Count == 0)
                {
                    build.Warnings.Add($"part '{name}' is fully transparent — skipped");
                    continue;
                }
                part.SourceOrder = order++;
                build.Parts.Add(part);
            }

            if (build.Parts.Count == 0)
            {
                build.Warnings.Add("every part image was empty");
                return build;
            }

            // Part names become sprite names, and a sheet cannot hold two sprites with the
            // same one.
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var p in build.Parts)
            {
                string unique = p.Name;
                for (int i = 2; !seen.Add(unique); i++) unique = $"{p.Name}_{i}";
                p.Name = unique;

                build.FrameW = Mathf.Max(build.FrameW, p.W);
                build.FrameH = Mathf.Max(build.FrameH, p.H);
            }

            // ── sheet metadata ───────────────────────────────────────────────────────
            var sheet = NoitaSpriteXml.Load(NoitaPaths.SpriteXml(dataRoot, creature));
            if (sheet != null)
            {
                build.OriginPx = new Vector2(sheet.OffsetX, sheet.OffsetY);
                build.DefaultAnim = sheet.Default?.Name;

                var anim = sheet.Default;
                if (anim != null)
                {
                    build.FrameW = Mathf.Max(build.FrameW, anim.DrawW);
                    build.FrameH = Mathf.Max(build.FrameH, anim.DrawH);

                    var delta = FindAlignment(dataRoot, creature, sheet, build.Parts, build);
                    foreach (var p in build.Parts) Shift(p, delta, build.FrameW, build.FrameH);

                    var empty = build.Parts.FindAll(p => p.Solid.Count == 0);
                    foreach (var p in empty)
                    {
                        build.Warnings.Add($"part '{p.Name}' fell outside the frame after alignment — skipped");
                        build.Parts.Remove(p);
                    }
                }
            }
            else
            {
                // No sheet: assume the creature stands on the bottom edge, centred.
                build.OriginPx = new Vector2(build.FrameW * 0.5f, build.FrameH);
                build.Warnings.Add("no sprite xml found — using a guessed origin and no per-frame poses");
            }

            if (build.Parts.Count == 0)
            {
                build.Warnings.Add("no parts left after alignment");
                return build;
            }

            // ── hierarchy ────────────────────────────────────────────────────────────
            BuildHierarchy(build);

            // ── per-frame poses from the uv sheet ────────────────────────────────────
            string uvPath = NoitaPaths.UvSheet(dataRoot, creature);
            if (sheet != null && uvPath != null)
            {
                var uv = LoadUv(uvPath, sheet, build);
                if (uv != null) SolvePoses(build, sheet, uv);
                else build.Warnings.Add("uv sheet could not be read — rest pose only");
            }
            else if (uvPath == null)
            {
                build.Warnings.Add("no *_uv_src.png — rest pose only");
            }

            if (build.Poses.Count == 0) build.Poses.Add(RestPose(build));

            return build;
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Part images
        // ─────────────────────────────────────────────────────────────────────────────

        private static PartBuild LoadPart(string name, string path, int order)
        {
            var tex = LoadTexture(path);
            if (tex == null) return null;

            var part = new PartBuild { Name = Sanitize(name), W = tex.width, H = tex.height, SourceOrder = order };
            part.Pixels = TopDown(tex);
            UnityEngine.Object.DestroyImmediate(tex);

            Measure(part);
            return part;
        }

        /// <summary>
        /// Re-stamp a part onto a frame-sized canvas, shifted by the alignment the sheet
        /// correlation found. After this every part coordinate is a frame coordinate, which
        /// is the space the uv markers use.
        /// </summary>
        private static void Shift(PartBuild part, Vector2Int delta, int frameW, int frameH)
        {
            if (delta == Vector2Int.zero && part.W == frameW && part.H == frameH) return;

            var moved = new Color32[frameW * frameH];
            for (int y = 0; y < part.H; y++)
            for (int x = 0; x < part.W; x++)
            {
                var c = part.Pixels[y * part.W + x];
                if (c.a == 0) continue;
                int nx = x + delta.x, ny = y + delta.y;
                if (nx < 0 || ny < 0 || nx >= frameW || ny >= frameH) continue;
                moved[ny * frameW + nx] = c;
            }

            part.Pixels = moved;
            part.W = frameW;
            part.H = frameH;
            part.Solid.Clear();
            part.Edge.Clear();
            Measure(part);
        }

        private static void Measure(PartBuild part)
        {
            int minX = int.MaxValue, minY = int.MaxValue, maxX = int.MinValue, maxY = int.MinValue;
            for (int y = 0; y < part.H; y++)
            for (int x = 0; x < part.W; x++)
            {
                if (part.Pixels[y * part.W + x].a == 0) continue;
                part.Solid.Add(new Vector2Int(x, y));
                if (x < minX) minX = x;
                if (y < minY) minY = y;
                if (x > maxX) maxX = x;
                if (y > maxY) maxY = y;
            }

            if (part.Solid.Count == 0) return;

            part.Bounds = new RectInt(minX, minY, maxX - minX + 1, maxY - minY + 1);
            part.PivotPx = new Vector2(minX + part.Bounds.width * 0.5f - 0.5f, minY + part.Bounds.height * 0.5f - 0.5f);

            // Distance tests only ever need the rim of a part, and the rim is a tenth of the pixels.
            foreach (var p in part.Solid)
            {
                if (part.SolidAt(p.x - 1, p.y) && part.SolidAt(p.x + 1, p.y) &&
                    part.SolidAt(p.x, p.y - 1) && part.SolidAt(p.x, p.y + 1)) continue;
                part.Edge.Add(p);
            }
            if (part.Edge.Count == 0) part.Edge.AddRange(part.Solid);
        }

        /// <summary>
        /// The part images are cut from one animation frame, but which frame — and whether it
        /// lines up with the cell the xml declares — is not written down anywhere and is off by
        /// a pixel for a fair number of creatures. Slide the parts over the default frame and
        /// keep the offset where their colours line up with the sheet.
        /// </summary>
        private static Vector2Int FindAlignment(string dataRoot, string creature, NoitaSpriteXml sheet,
                                                List<PartBuild> parts, RagdollBuild build)
        {
            var anim = sheet.Default;
            if (anim == null) return Vector2Int.zero;

            string sheetPng = SheetPng(dataRoot, creature, sheet);
            var tex = sheetPng != null ? LoadTexture(sheetPng) : null;
            if (tex == null)
            {
                build.Warnings.Add("sprite sheet png not found — part alignment not verified");
                return Vector2Int.zero;
            }

            int w = tex.width, h = tex.height;
            var px = TopDown(tex);
            UnityEngine.Object.DestroyImmediate(tex);

            var rect = anim.FrameRect(0);
            Vector2Int best = Vector2Int.zero;
            float bestScore = -1f;

            for (int dy = -2; dy <= 2; dy++)
            for (int dx = -2; dx <= 2; dx++)
            {
                int hit = 0, total = 0;
                foreach (var part in parts)
                foreach (var p in part.Solid)
                {
                    total++;
                    int sx = rect.xMin + p.x + dx, sy = rect.yMin + p.y + dy;
                    if (sx < 0 || sy < 0 || sx >= w || sy >= h) continue;
                    var c = px[sy * w + sx];
                    var q = part.At(p.x, p.y);
                    if (c.a != 0 && c.r == q.r && c.g == q.g && c.b == q.b) hit++;
                }

                float score = total > 0 ? hit / (float)total : 0f;
                if (score <= bestScore) continue;
                bestScore = score;
                best = new Vector2Int(dx, dy);
            }

            // A weak peak means the parts were cut from some other frame; leave them where the
            // artist drew them rather than snapping to a coincidence.
            if (bestScore < 0.4f)
            {
                build.Warnings.Add($"part art matches the default frame poorly ({bestScore:P0}) — using no offset");
                return Vector2Int.zero;
            }

            return best;
        }

        private static string SheetPng(string dataRoot, string creature, NoitaSpriteXml sheet)
        {
            string direct = Path.Combine(dataRoot, "enemies_gfx", creature + ".png");
            if (File.Exists(direct)) return direct;

            string declared = sheet?.SheetFile;
            if (string.IsNullOrEmpty(declared)) return null;

            declared = declared.Replace('\\', '/');
            if (declared.StartsWith("data/", StringComparison.OrdinalIgnoreCase))
                declared = declared.Substring(5);

            string full = Path.Combine(dataRoot, declared.Replace('/', Path.DirectorySeparatorChar));
            return File.Exists(full) ? full : null;
        }

        /// <summary>Reads any png on disk, including the palette + colour-key ones Noita ships.</summary>
        public static Texture2D LoadTexture(string path)
        {
            byte[] bytes;
            try { bytes = File.ReadAllBytes(path); }
            catch (Exception) { return null; }

            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, false);
            if (tex.LoadImage(bytes, false)) return tex;

            UnityEngine.Object.DestroyImmediate(tex);
            return null;
        }

        /// <summary>Texture rows come back bottom-up; every coordinate here is top-down frame space.</summary>
        private static Color32[] TopDown(Texture2D tex)
        {
            var src = tex.GetPixels32();
            int w = tex.width, h = tex.height;
            var dst = new Color32[src.Length];
            for (int y = 0; y < h; y++)
                Array.Copy(src, (h - 1 - y) * w, dst, y * w, w);
            return dst;
        }

        private static string Sanitize(string name)
        {
            var chars = name.ToCharArray();
            for (int i = 0; i < chars.Length; i++)
                if (!char.IsLetterOrDigit(chars[i]) && chars[i] != '_') chars[i] = '_';
            return new string(chars);
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Hierarchy: nothing in the data says which piece hangs off which, so grow a tree
        // outwards from the torso, always attaching whichever loose piece sits closest to
        // the ones already connected. Hands land on arms, arms on the torso, and the hinge
        // goes exactly where the two silhouettes come nearest to touching.
        // ─────────────────────────────────────────────────────────────────────────────

        private static readonly string[] RootNames =
        {
            "torso", "upper_torso", "body", "base", "torso1", "torso_1", "main", "core", "head"
        };

        private static void BuildHierarchy(RagdollBuild build)
        {
            var parts = build.Parts;

            int root = -1;
            foreach (var candidate in RootNames)
            {
                root = parts.FindIndex(p => string.Equals(p.Name, candidate, StringComparison.OrdinalIgnoreCase));
                if (root >= 0) break;
            }
            if (root < 0)
            {
                root = 0;
                for (int i = 1; i < parts.Count; i++)
                    if (parts[i].Solid.Count > parts[root].Solid.Count) root = i;
            }

            var ordered = new List<PartBuild> { parts[root] };
            parts[root].Parent = -1;

            var remaining = new List<PartBuild>(parts);
            remaining.RemoveAt(root);

            while (remaining.Count > 0)
            {
                float best = float.MaxValue;
                int bestChild = 0, bestParent = 0;
                Vector2 bestAnchor = Vector2.zero;

                for (int c = 0; c < remaining.Count; c++)
                for (int p = 0; p < ordered.Count; p++)
                {
                    float d = ClosestPair(ordered[p], remaining[c], out var anchor);
                    // Prefer the bulkier parent when two are equally close: a hand should hang
                    // off the arm, not off a fingertip-sized neighbour it happens to touch.
                    d -= ordered[p].Solid.Count * 1e-4f;
                    if (d >= best) continue;
                    best = d;
                    bestChild = c;
                    bestParent = p;
                    bestAnchor = anchor;
                }

                var child = remaining[bestChild];
                child.Parent = bestParent;
                child.AnchorPx = bestAnchor;
                ordered.Add(child);
                remaining.RemoveAt(bestChild);
            }

            build.Parts = ordered;
        }

        private static float ClosestPair(PartBuild a, PartBuild b, out Vector2 midpoint)
        {
            float best = float.MaxValue;
            midpoint = Vector2.zero;

            foreach (var p in a.Edge)
            foreach (var q in b.Edge)
            {
                float dx = p.x - q.x, dy = p.y - q.y;
                float d = dx * dx + dy * dy;
                if (d >= best) continue;
                best = d;
                midpoint = new Vector2((p.x + q.x) * 0.5f, (p.y + q.y) * 0.5f);
            }

            return Mathf.Sqrt(best);
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // uv sheet
        // ─────────────────────────────────────────────────────────────────────────────

        private sealed class UvGroup
        {
            public bool HasMarker;
            public Vector2 Marker;
            public readonly List<Vector2Int> Region = new();
        }

        private sealed class UvFrame
        {
            public readonly Dictionary<int, UvGroup> Groups = new();
        }

        private sealed class UvSheet
        {
            /// <summary>Key: "anim|frame".</summary>
            public readonly Dictionary<string, UvFrame> Frames = new();
            public UvFrame Rest;
        }

        private static int Key(Color32 c) => (c.r << 16) | (c.g << 8) | c.b;
        private static Color32 FromKey(int k) => new((byte)(k >> 16), (byte)((k >> 8) & 0xFF), (byte)(k & 0xFF), 255);
        private static string FrameKey(string anim, int frame) => anim + "|" + frame;

        private static UvSheet LoadUv(string path, NoitaSpriteXml sheet, RagdollBuild build)
        {
            var tex = LoadTexture(path);
            if (tex == null) return null;

            int w = tex.width, h = tex.height;
            var px = TopDown(tex);
            UnityEngine.Object.DestroyImmediate(tex);

            var uv = new UvSheet();
            foreach (var anim in sheet.Anims)
            {
                for (int f = 0; f < anim.Count; f++)
                {
                    var rect = anim.FrameRect(f);
                    var frame = ReadFrame(px, w, h, rect);
                    if (frame != null) uv.Frames[FrameKey(anim.Name, f)] = frame;
                }
            }

            var def = sheet.Default;
            if (def != null) uv.Frames.TryGetValue(FrameKey(def.Name, 0), out uv.Rest);
            if (uv.Rest == null)
            {
                foreach (var kv in uv.Frames) { uv.Rest = kv.Value; break; }
            }

            if (uv.Rest == null)
            {
                build.Warnings.Add("uv sheet has no usable frames");
                return null;
            }

            return uv;
        }

        private static UvFrame ReadFrame(Color32[] px, int w, int h, RectInt rect)
        {
            if (rect.xMin < 0 || rect.yMin < 0 || rect.xMax > w || rect.yMax > h) return null;

            var frame = new UvFrame();
            var markers = new Dictionary<int, List<Vector2Int>>();

            for (int y = 0; y < rect.height; y++)
            for (int x = 0; x < rect.width; x++)
            {
                var c = px[(rect.yMin + y) * w + rect.xMin + x];
                if (c.a == 0) continue;

                int key = Key(c);
                if (!frame.Groups.TryGetValue(key, out var g))
                {
                    g = new UvGroup();
                    frame.Groups[key] = g;
                }

                if (c.a == 255)
                {
                    if (!markers.TryGetValue(key, out var list)) markers[key] = list = new List<Vector2Int>();
                    list.Add(new Vector2Int(x, y));
                }
                else
                {
                    g.Region.Add(new Vector2Int(x, y));
                }
            }

            // A colour is a body-part marker when exactly one opaque pixel carries it. Held
            // items and other painted-over areas come through as a run of opaque pixels and
            // are deliberately left without a marker.
            foreach (var kv in markers)
            {
                var g = frame.Groups[kv.Key];
                if (kv.Value.Count == 1)
                {
                    g.HasMarker = true;
                    g.Marker = kv.Value[0];
                }
                else
                {
                    g.Region.AddRange(kv.Value);
                }
            }

            return frame;
        }

        /// <summary>
        /// Work out which uv colour tracks which body part, by looking at the rest frame:
        /// the colour whose translucent area covers the part, or whose marker sits on it.
        /// </summary>
        private static void AssignColors(RagdollBuild build, UvFrame rest)
        {
            var scored = new List<(float score, int key, int part)>();

            foreach (var kv in rest.Groups)
            {
                var group = kv.Value;
                if (!group.HasMarker) continue;

                for (int i = 0; i < build.Parts.Count; i++)
                {
                    var part = build.Parts[i];

                    int overlap = 0;
                    foreach (var r in group.Region)
                        if (part.SolidAt(r.x, r.y)) overlap++;

                    bool inside = part.SolidAt(Mathf.RoundToInt(group.Marker.x), Mathf.RoundToInt(group.Marker.y));

                    float near = float.MaxValue;
                    foreach (var s in part.Solid)
                    {
                        float dx = s.x - group.Marker.x, dy = s.y - group.Marker.y;
                        near = Mathf.Min(near, dx * dx + dy * dy);
                    }
                    near = Mathf.Sqrt(near);

                    float score = overlap * 10f + (inside ? 5f : 0f) - near + group.Region.Count * 0.001f;
                    scored.Add((score, kv.Key, i));
                }
            }

            scored.Sort((a, b) => b.score.CompareTo(a.score));

            var usedColor = new HashSet<int>();
            var usedPart = new HashSet<int>();
            foreach (var (score, key, part) in scored)
            {
                if (score < MinAssignScore) break;
                if (!usedColor.Add(key)) continue;
                if (!usedPart.Add(part)) { usedColor.Remove(key); continue; }

                build.Parts[part].HasUv = true;
                build.Parts[part].UvColor = FromKey(key);
                build.Parts[part].HasTip = true;
                build.Parts[part].TipKey = key;
                build.Parts[part].Tip0 = rest.Groups[key].Marker;
            }

            // A piece in the middle of a limb often has no marker of its own — the arm is
            // tracked by the hand at the end of it. Borrow the nearest descendant's marker so
            // the whole chain swings instead of only its tip.
            for (int i = 0; i < build.Parts.Count; i++)
            {
                if (build.Parts[i].HasTip) continue;
                for (int j = i + 1; j < build.Parts.Count; j++)
                {
                    if (!build.Parts[j].HasTip || !IsDescendant(build, j, i)) continue;
                    build.Parts[i].HasTip = true;
                    build.Parts[i].TipKey = build.Parts[j].TipKey;
                    build.Parts[i].Tip0 = build.Parts[j].Tip0;
                    break;
                }
            }
        }

        private static bool IsDescendant(RagdollBuild build, int node, int ancestor)
        {
            int guard = 0;
            for (int p = build.Parts[node].Parent; p >= 0 && guard++ < 64; p = build.Parts[p].Parent)
                if (p == ancestor) return true;
            return false;
        }

        // ─────────────────────────────────────────────────────────────────────────────
        // Pose solve
        // ─────────────────────────────────────────────────────────────────────────────

        /// <summary>Rigid 2D transform written as "the point <see cref="In"/> ends up at <see cref="Out"/>, rotated by <see cref="Ang"/>".</summary>
        private struct Xform
        {
            public float Ang;      // radians, pixel space (y down, so clockwise on screen)
            public Vector2 In, Out;

            public Vector2 Apply(Vector2 p)
            {
                float c = Mathf.Cos(Ang), s = Mathf.Sin(Ang);
                float dx = p.x - In.x, dy = p.y - In.y;
                return new Vector2(Out.x + dx * c - dy * s, Out.y + dx * s + dy * c);
            }

            public static Xform Identity(Vector2 at) => new() { Ang = 0f, In = at, Out = at };
        }

        private static void SolvePoses(RagdollBuild build, NoitaSpriteXml sheet, UvSheet uv)
        {
            AssignColors(build, uv.Rest);

            // The rest pose has to come first: Ragdoll falls back to poses[0].
            var defaultAnim = sheet.Default;
            var animOrder = new List<NoitaAnim>(sheet.Anims);
            if (defaultAnim != null)
            {
                animOrder.Remove(defaultAnim);
                animOrder.Insert(0, defaultAnim);
            }

            foreach (var anim in animOrder)
            {
                for (int f = 0; f < anim.Count; f++)
                {
                    if (!uv.Frames.TryGetValue(FrameKey(anim.Name, f), out var frame)) continue;
                    build.Poses.Add(SolveFrame(build, uv.Rest, frame, anim.Name, f));
                }
            }
        }

        private static PoseBuild SolveFrame(RagdollBuild build, UvFrame rest, UvFrame frame, string anim, int index)
        {
            int n = build.Parts.Count;
            var pose = new PoseBuild { Anim = anim, Frame = index, Pos = new Vector2[n], Rot = new float[n] };
            var xforms = new Xform[n];

            for (int i = 0; i < n; i++)
            {
                var part = build.Parts[i];
                Xform xf;

                if (part.Parent < 0)
                {
                    // The root only ever shifts: it is the thing everything else is measured from.
                    xf = Xform.Identity(part.PivotPx);
                    if (part.HasUv && TryMarker(rest, Key(part.UvColor), out var r0) &&
                        TryMarker(frame, Key(part.UvColor), out var rn))
                    {
                        xf.In = r0;
                        xf.Out = rn;
                    }
                }
                else
                {
                    var parent = xforms[part.Parent];
                    Vector2 a0 = part.AnchorPx;
                    Vector2 an = parent.Apply(a0);

                    float ang = parent.Ang;
                    if (part.HasTip && TryMarker(frame, part.TipKey, out var tipN))
                    {
                        Vector2 rest0 = part.Tip0 - a0;
                        Vector2 now = tipN - an;
                        if (rest0.sqrMagnitude > 0.01f && now.sqrMagnitude > 0.01f)
                        {
                            ang = Mathf.Atan2(now.y, now.x) - Mathf.Atan2(rest0.y, rest0.x);
                            ang = Mathf.Repeat(ang + Mathf.PI, Mathf.PI * 2f) - Mathf.PI;
                        }
                    }

                    xf = new Xform { Ang = ang, In = a0, Out = an };
                }

                xforms[i] = xf;
                pose.Pos[i] = xf.Apply(part.PivotPx);
                pose.Rot[i] = -xf.Ang * Mathf.Rad2Deg; // pixel space is y-down, Unity is y-up
            }

            return pose;
        }

        private static bool TryMarker(UvFrame frame, int key, out Vector2 marker)
        {
            marker = default;
            if (frame == null || !frame.Groups.TryGetValue(key, out var g) || !g.HasMarker) return false;
            marker = g.Marker;
            return true;
        }

        private static PoseBuild RestPose(RagdollBuild build)
        {
            int n = build.Parts.Count;
            var pose = new PoseBuild { Anim = build.DefaultAnim ?? "rest", Frame = 0, Pos = new Vector2[n], Rot = new float[n] };
            for (int i = 0; i < n; i++) pose.Pos[i] = build.Parts[i].PivotPx;
            return pose;
        }
    }
}
