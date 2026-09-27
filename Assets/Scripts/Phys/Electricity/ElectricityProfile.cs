using System;
using UnityEngine;

namespace Phys.Electricity
{
    /// <summary>
    /// Everything one discharge is: how far it looks for something to run through, what it does
    /// to whoever is touching that, and how long it crawls before it dies.
    ///
    /// The shape of it comes from the material, not from here. Electricity in this game does
    /// nothing on its own — it finds a conductor (<see cref="Materials.PhysMaterial.Conducts"/>,
    /// which today means metal) and everything that follows happens along that conductor. A zap
    /// into open air is a spark and a scorch mark; the same zap into a girder runs the length of
    /// it and hurts everyone leaning on it.
    ///
    /// Radii are world units — 1 unit is 20 px, the world's PPU.
    /// </summary>
    [Serializable]
    public sealed class ElectricityProfile
    {
        // ── Reach ─────────────────────────────────────────────────────────────
        [Header("Reach")]
        [Tooltip("How close a conductor has to be to the strike point to catch it. Also the " +
                 "radius of the bolt itself — what it burns and who it hurts directly.")]
        public float strikeRadius = 0.35f;

        [Tooltip("What the discharge can see: conductors, victims and kindling all come from this.")]
        public LayerMask affects = ~0;

        [Tooltip("Conductors past the first. A charge spreads to every conductor touching an " +
                 "energised one, and this caps how far down a chain of girders it will travel.")]
        public int maxConductors = 12;

        [Tooltip("How far past an energised body something can be and still count as touching it.")]
        public float contactGap = 0.06f;

        // ── Damage ────────────────────────────────────────────────────────────
        [Header("Damage")]
        [Tooltip("Taken by anything standing in the strike itself.")]
        public float directDamage = 22f;

        [Tooltip("Taken by anything touching a conductor the charge got into. This is the whole " +
                 "trick of the material: it is how a discharge reaches someone across the room.")]
        public float conductedDamage = 16f;

        [Tooltip("What the conductor itself takes. 0 by default — a girder does not care, and " +
                 "it is the thing doing the hurting, not the thing being hurt.")]
        public float conductorDamage;

        [Tooltip("Hits worth less than this are dropped rather than littering the screen with 1s.")]
        public float minDamage = 1f;

        // ── Fire ──────────────────────────────────────────────────────────────
        [Header("Fire")]
        [Tooltip("Percent chance, per roll, that the charge sets light to whatever flammable " +
                 "thing is touching it. Every redraw rolls twice on each live conductor's " +
                 "outline and once at each victim it is jumping into.")]
        [Range(0f, 100f)] public float igniteChancePercent = 20f;

        [Tooltip("World radius of one such attempt. Wider than the contact gap, so wood resting " +
                 "on the metal is inside it.")]
        public float igniteRadius = 0.08f;

        // ── Charge ────────────────────────────────────────────────────────────
        [Header("Charge")]
        [Tooltip("How long the metal stays live after the strike, in seconds. The damage is " +
                 "dealt at once; this is how long you watch it.")]
        public float chargeSeconds = 0.45f;

        [Tooltip("Seconds per conductor down the chain before the next one goes live — what " +
                 "makes the charge visibly run along a line of girders.")]
        public float hopDelay = 0.035f;

        [Tooltip("Seconds of solid, full-brightness bolt at the moment of the strike and at " +
                 "each conductor as the charge reaches it.")]
        public float strikeFlashSeconds = 0.1f;

        [Tooltip("Arc ticks (60 Hz) between redraws. 2 is a 30 Hz flicker; 1 is smoother and busier.")]
        public int flickerTicks = 2;

        [Tooltip("How far a bolt wanders off the straight line, as a fraction of each segment.")]
        [Range(0f, 0.6f)] public float boltRoughness = 0.22f;

        // ── Feel ──────────────────────────────────────────────────────────────
        [Header("Feel")]
        public float cameraShake = 0.5f;
    }
}
