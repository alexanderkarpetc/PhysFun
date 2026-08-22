using System;
using System.Collections.Generic;
using UnityEngine;

namespace Ragdolls
{
    /// <summary>
    /// One rigid piece of a corpse. Everything is stored in Noita frame pixels —
    /// x right, y down, origin at the top-left corner of the animation frame — because
    /// that is the space both the ragdoll part images and the uv marker sheet live in.
    /// <see cref="RagdollDefinition.PixelToLocal"/> converts to Unity units at spawn time.
    /// </summary>
    [Serializable]
    public class RagdollPart
    {
        public string name;
        public Sprite sprite;

        /// <summary>Index into <see cref="RagdollDefinition.parts"/>, -1 for the root piece.</summary>
        public int parent = -1;

        /// <summary>Sprite pivot in frame pixels, rest pose. This is the point a pose positions.</summary>
        public Vector2 pivotPx;

        /// <summary>Hinge point shared with the parent, in frame pixels, rest pose.</summary>
        public Vector2 anchorPx;

        public bool useLimits = true;
        public float limitLow = -70f;
        public float limitHigh = 70f;

        /// <summary>Colour in the uv sheet this part was matched to; alpha 0 when nothing matched.</summary>
        public Color32 uvColor;
    }

    /// <summary>Where every part sits on one animation frame, so a corpse keeps the pose it died in.</summary>
    [Serializable]
    public class RagdollPose
    {
        public string anim;
        public int frame;

        /// <summary>Per part, index-parallel with <see cref="RagdollDefinition.parts"/>: pivot position in frame pixels.</summary>
        public Vector2[] positionsPx;

        /// <summary>Per part: rotation in degrees, Unity convention (CCW positive).</summary>
        public float[] rotations;
    }

    /// <summary>
    /// Baked ragdoll for one creature: the pieces, how they hang off each other, and the
    /// pose of every animation frame. Produced by PhysFun/Noita Ragdolls, consumed by
    /// <see cref="Ragdoll"/>.
    /// </summary>
    [CreateAssetMenu(menuName = "PhysFun/Ragdoll Definition", fileName = "RagdollDefinition")]
    public class RagdollDefinition : ScriptableObject
    {
        public string creature;

        public int frameWidth = 16;
        public int frameHeight = 16;

        /// <summary>Entity origin inside the frame (Noita offset_x / offset_y). The spawn point maps here.</summary>
        public Vector2 originPx;

        public float pixelsPerUnit = 20f;

        public List<RagdollPart> parts = new();
        public List<RagdollPose> poses = new();

        public string defaultAnim;

        /// <summary>Frame pixel (pixel centre) → position in the ragdoll root's local space.</summary>
        public Vector2 PixelToLocal(Vector2 px)
        {
            float ppu = Mathf.Max(0.0001f, pixelsPerUnit);
            return new Vector2((px.x + 0.5f - originPx.x) / ppu, -(px.y + 0.5f - originPx.y) / ppu);
        }

        /// <summary>Frame pixel offset → local-space offset. No origin shift, so it survives rotation.</summary>
        public Vector2 PixelToLocalDelta(Vector2 delta)
        {
            float ppu = Mathf.Max(0.0001f, pixelsPerUnit);
            return new Vector2(delta.x / ppu, -delta.y / ppu);
        }

        public RagdollPose RestPose => poses.Count > 0 ? poses[0] : null;

        /// <summary>Exact match first, then any frame of the same animation, then the rest pose.</summary>
        public RagdollPose FindPose(string anim, int frame)
        {
            if (string.IsNullOrEmpty(anim)) return RestPose;

            RagdollPose sameAnim = null;
            for (int i = 0; i < poses.Count; i++)
            {
                var p = poses[i];
                if (!string.Equals(p.anim, anim, StringComparison.OrdinalIgnoreCase)) continue;
                if (p.frame == frame) return p;
                sameAnim ??= p;
            }
            return sameAnim ?? RestPose;
        }

        /// <summary>
        /// Split a sliced sprite name such as "walk_03" into animation and frame index.
        /// That is the naming PhysFun/Slice From XML produces, so a live enemy can hand its
        /// current sprite straight to the ragdoll.
        /// </summary>
        public static bool TryParseSpriteName(string spriteName, out string anim, out int frame)
        {
            anim = null;
            frame = 0;
            if (string.IsNullOrEmpty(spriteName)) return false;

            int split = spriteName.LastIndexOf('_');
            if (split <= 0 || split == spriteName.Length - 1) return false;

            string tail = spriteName.Substring(split + 1);
            if (!int.TryParse(tail, out frame)) return false;

            anim = spriteName.Substring(0, split);
            // The uv sheets never carry a "_uv" variant of a pose, so drop the suffix.
            if (anim.EndsWith("_uv", StringComparison.OrdinalIgnoreCase))
                anim = anim.Substring(0, anim.Length - 3);
            return true;
        }
    }
}
