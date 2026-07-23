using UnityEngine;

namespace Player
{
    /// <summary>
    /// Live-tunable movement profile for the player. Noita-style: no jumping — hold to
    /// levitate, which burns a flight meter that recharges on the ground.
    /// Edit the asset in the Inspector while in Play mode to tune the feel live.
    /// </summary>
    [CreateAssetMenu(fileName = "MovementConfig", menuName = "PhysFun/Movement Config", order = 0)]
    public class MovementConfig : ScriptableObject
    {
        [Header("Horizontal Move")]
        [Tooltip("Top horizontal speed (units/s).")]
        [Range(0f, 12f)] public float maxSpeed = 3f;
        [Tooltip("How fast we accelerate toward the target speed on the ground.")]
        [Range(0f, 120f)] public float accel = 30f;
        [Tooltip("Acceleration used when reversing direction — higher = snappier turns.")]
        [Range(0f, 200f)] public float turnAccel = 60f;
        [Tooltip("Fraction of ground accel available while airborne (Noita gives near-full air control).")]
        [Range(0f, 1f)] public float airControl = 0.85f;
        [Tooltip("Deceleration applied on the ground when there is no input.")]
        [Range(0f, 60f)] public float friction = 14f;

        [Header("Gravity")]
        [Tooltip("Base Rigidbody2D gravity scale (the pull you feel when neither rising nor levitating).")]
        [Range(0f, 8f)] public float gravityScale = 2f;
        [Tooltip("Extra gravity multiplier while falling — makes the descent feel weighty, not floaty.")]
        [Range(1f, 4f)] public float fallGravityMult = 1.4f;
        [Tooltip("Terminal velocity — max downward speed (units/s). Prevents runaway falls.")]
        [Range(2f, 40f)] public float maxFallSpeed = 16f;

        [Header("Levitation")]
        [Tooltip("Upward acceleration applied while the levitate key is held (units/s^2).")]
        [Range(0f, 120f)] public float levitateForce = 34f;
        [Tooltip("Max upward speed levitation can reach. Beyond this, thrust stops adding lift.")]
        [Range(0f, 16f)] public float maxRiseSpeed = 4.5f;
        [Tooltip("Instant upward velocity kick the moment levitation is (re)engaged — adds a responsive 'hop'.")]
        [Range(0f, 10f)] public float initialHopImpulse = 3.2f;

        [Header("Levitation Capacity")]
        [Tooltip("Full flight capacity, in seconds of sustained levitation.")]
        [Range(0.2f, 8f)] public float capacity = 1.6f;
        [Tooltip("Capacity drained per second while levitating.")]
        [Range(0f, 8f)] public float drainRate = 1f;
        [Tooltip("Capacity recharged per second while grounded.")]
        [Range(0f, 16f)] public float groundRegenRate = 4f;
        [Tooltip("Capacity recharged per second while airborne but not levitating (Noita drips a little).")]
        [Range(0f, 8f)] public float airRegenRate = 0.6f;
        [Tooltip("Delay after releasing/exhausting levitation before recharge begins (seconds).")]
        [Range(0f, 1.5f)] public float regenDelay = 0.15f;
        [Tooltip("Fraction of capacity that must recharge before you can levitate again after fully draining it (avoids stutter-flying on empty).")]
        [Range(0f, 1f)] public float refireThreshold = 0.15f;
    }
}
