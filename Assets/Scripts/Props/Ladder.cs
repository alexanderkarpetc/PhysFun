using System.Collections.Generic;
using UnityEngine;

namespace Props
{
    /// <summary>
    /// Something to climb instead of levitating: hold W or S on it and you go up or down at a
    /// walk, with the flight meter left alone. It runs from this object's position (its top)
    /// down <see cref="_height"/>; a ladder that goes up through a deck has its top at the
    /// deck's top, so climbing off it puts you on the deck.
    ///
    /// It has no collider on purpose. Raycasts in this project hit triggers, so even a
    /// trigger would block sight lines, stop bullets and count as ground; the player asks
    /// <see cref="At"/> instead. The rungs are a tiled SpriteRenderer sized to the ladder.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class Ladder : MonoBehaviour
    {
        [Tooltip("Length, world units, from this object's position down.")]
        [SerializeField] private float _height = 2f;
        [Tooltip("How far either side of the centre line counts as on it, world units.")]
        [SerializeField] private float _reach = 0.2f;

        private static readonly List<Ladder> All = new();

        public float Height => _height;
        public float CenterX => transform.position.x;
        public float Top => transform.position.y;
        public float Bottom => transform.position.y - _height;

        private void OnEnable() => All.Add(this);
        private void OnDisable() => All.Remove(this);

        // Not from OnValidate: resizing a SpriteRenderer there makes Unity complain (it sends
        // a message from inside validation). The export sets the size on each instance too.
        private void Awake() => Fit();

        private void Fit()
        {
            var sr = GetComponent<SpriteRenderer>();
            if (sr && sr.drawMode != SpriteDrawMode.Simple)
                sr.size = new Vector2(sr.size.x, _height);
        }

        /// <summary>The ladder at <paramref name="point"/>, or null.</summary>
        public static Ladder At(Vector2 point)
        {
            foreach (var l in All)
                if (Mathf.Abs(point.x - l.CenterX) <= l._reach && point.y <= l.Top && point.y >= l.Bottom)
                    return l;
            return null;
        }

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.9f, 0.7f, 0.3f);
            var p = transform.position;
            Gizmos.DrawWireCube(p + Vector3.down * (_height / 2f), new Vector3(_reach * 2f, _height, 0f));
        }
#endif
    }
}
