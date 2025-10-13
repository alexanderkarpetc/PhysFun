using System;
using System.Collections.Generic;
using UnityEngine;

public enum UVPart { Head, Torso, Pelvis, LArm, RArm, LLeg, RLeg, LFoot, RFoot, Custom1, Custom2 }

[Serializable] public struct BodyUVFrame {
    public string anim;       // e.g., "walk"
    public int frame;         // e.g., 3
    public List<Entry> points; // named points in local normalized space [0..1]
    [Serializable] public struct Entry { public UVPart part; public Vector2 uv; }
}

public class BodyUVAsset : ScriptableObject {
    public Texture2D sourceTexture;   // the *_uv.png
    public List<BodyUVFrame> frames = new();
}