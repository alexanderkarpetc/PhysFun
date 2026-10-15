using System.Collections.Generic;
using UnityEngine;

namespace Lighting
{
    /// <summary>
    /// A light in the world - a lamp, a cresset, a candle. <see cref="LightField"/> spreads it
    /// out from here round the terrain: it fills the room it is in, bends a little way round a
    /// corner, and lights the face of a wall without going through it.
    ///
    /// Nothing about it is physical. It goes where its object goes, so a lamp on a rope swings
    /// its light about, and a lamp shot off its rope takes the light down with it.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class LightSource2D : MonoBehaviour
    {
        [Tooltip("Colour of the light. Brightness is Intensity, not this.")]
        public Color color = new(1f, 0.74f, 0.45f, 1f);

        [Tooltip("1 = as bright as the light map goes on its own (twice the art's own colour " +
                 "at the centre, with the ambient on top).")]
        [Min(0f)] public float intensity = 1f;

        [Tooltip("How far it reaches through open air, in world units. Through rock it reaches " +
                 "a fraction of this (LightField.WallCost).")]
        [Min(0.1f)] public float radius = 6f;

        [Tooltip("How much it wavers, 0 = steady. A flame is about 0.15.")]
        [Range(0f, 1f)] public float flicker = 0.12f;

        [Tooltip("How fast it wavers.")]
        [Min(0f)] public float flickerSpeed = 7f;

        [Tooltip("Where the light comes from, from this object's position (local, so it turns " +
                 "with a swinging lamp).")]
        public Vector2 offset;

        private float _seed;

        internal static readonly List<LightSource2D> All = new();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetAll() => All.Clear();

        private void Awake() => _seed = Random.value * 100f;

        private void OnEnable() => All.Add(this);

        private void OnDisable() => All.Remove(this);

        /// <summary>Where the light is now, world space.</summary>
        public Vector2 Position => transform.TransformPoint(offset);

        /// <summary>Intensity this frame, flicker included.</summary>
        public float Current
        {
            get
            {
                if (flicker <= 0f) return intensity;
                float n = Mathf.PerlinNoise(_seed, Time.time * flickerSpeed) * 2f - 1f;
                return intensity * Mathf.Max(0f, 1f + n * flicker);
            }
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(color.r, color.g, color.b, 0.6f);
            Gizmos.DrawWireSphere(Position, radius);
        }
#endif
    }
}
