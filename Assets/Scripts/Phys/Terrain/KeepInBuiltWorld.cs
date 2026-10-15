using System.Collections.Generic;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// Stops whatever leaves the built part of a streaming floor (<see cref="TerrainBuilder.StreamFrom"/>),
    /// and lets it go again once the ground round it is built. Past the built chunks the rock is
    /// only cells in the map, with no colliders yet, so a ragdoll blown far enough would sail
    /// through it. Noita has the same guard for the same reason (PhysicsKeepInWorld, in
    /// physicskeepinworld_system.cpp of noita_dev.exe).
    ///
    /// A ragdoll or a rope is stopped and let go as one: half of one frozen at the edge while the
    /// rest went on would tear its joints.
    /// </summary>
    internal sealed class KeepInBuiltWorld
    {
        /// <summary>Seconds between looks for bodies that have left the built ground.</summary>
        public static float Interval = 0.25f;

        private readonly TerrainBuilder _builder;
        private readonly List<List<Rigidbody2D>> _held = new();
        private readonly HashSet<Rigidbody2D> _heldSet = new();
        private readonly List<Rigidbody2D> _scratch = new();
        private float _next;
        private int _playerLayer = -2;

        public KeepInBuiltWorld(TerrainBuilder builder) => _builder = builder;

        public void Tick()
        {
            if (Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + Interval;
            if (_playerLayer == -2) _playerLayer = LayerMask.NameToLayer("Player");

            // Let go of what now has ground round all of it.
            for (int i = _held.Count - 1; i >= 0; i--)
            {
                var group = _held[i];
                if (!GroupBuilt(group)) continue;
                Release(group);
                _held.RemoveAt(i);
            }

            foreach (var rb in Object.FindObjectsByType<Rigidbody2D>(FindObjectsSortMode.None))
            {
                if (rb.bodyType != RigidbodyType2D.Dynamic || !rb.simulated) continue;
                if (_builder.IsBuiltAround(rb.position)) continue;
                if (rb.gameObject.layer == _playerLayer) continue;   // the ground streams round them
                Hold(rb);
            }
        }

        /// <summary>Let go of everything: the floor is built, or going away.</summary>
        public void ReleaseAll()
        {
            foreach (var group in _held) Release(group);
            _held.Clear();
            _heldSet.Clear();
        }

        private void Hold(Rigidbody2D rb)
        {
            _scratch.Clear();
            Component whole = rb.GetComponentInParent<global::Ragdolls.Ragdoll>();
            if (!whole) whole = rb.GetComponentInParent<global::Props.Rope2D>();
            if (whole) whole.GetComponentsInChildren(_scratch);
            else _scratch.Add(rb);

            var group = new List<Rigidbody2D>(_scratch.Count);
            foreach (var b in _scratch)
            {
                // Only what is moving and not held already; whatever else stopped these (a
                // sleeping room) gets them back itself.
                if (!b || b.bodyType != RigidbodyType2D.Dynamic || !b.simulated) continue;
                if (!_heldSet.Add(b)) continue;
                b.simulated = false;
                group.Add(b);
            }
            if (group.Count > 0) _held.Add(group);
        }

        private void Release(List<Rigidbody2D> group)
        {
            foreach (var b in group)
            {
                _heldSet.Remove(b);
                if (b) b.simulated = true;
            }
        }

        private bool GroupBuilt(List<Rigidbody2D> group)
        {
            foreach (var b in group)
                if (b && !_builder.IsBuiltAround(b.position)) return false;
            return true;
        }
    }
}
