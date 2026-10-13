using System.Collections.Generic;
using Interaction;
using UnityEngine;

namespace Props
{
    /// <summary>
    /// A door you open, Terraria style. Shut, it is the slab filling the doorway: it stops
    /// bodies and blocks sight lines. Stand by it and press the interact key
    /// (<see cref="InteractionSystem"/> outlines it and prompts) and it swings open away from
    /// you - drawn as the leaf seen edge-on, a thin strip against the far face of the wall -
    /// and the doorway is clear. Again shuts it, unless something is standing in the way.
    ///
    /// Only the player opens doors. Enemies treat a shut one as a wall (their probes hit
    /// it), so each room behind one keeps to itself until you decide otherwise; an open one
    /// they will walk through like anyone else.
    ///
    /// The open leaf has no collider. Everything else in this game collides, but a leaf
    /// lying against the wall would stand 2px proud of it, right where the doorway is
    /// walked through. The door is still a pixel prop: burnt or shot apart, it is gone.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class Door : Interactable
    {
        [Tooltip("Where the open leaf goes: this far either side of the doorway's centre.")]
        [SerializeField] private float _openOffset = 0.225f;
        [Tooltip("The open leaf's width as a fraction of the shut door's - the leaf edge-on.")]
        [SerializeField] private float _leafScale = 0.34f;

        private static readonly List<Collider2D> Blockers = new();

        private Collider2D[] _cols;
        private bool _open;
        private Vector3 _shutPos;
        private Vector3 _shutScale;

        public bool IsOpen => _open;

        public override string Verb => _open ? "Close door" : "Open door";

        /// <summary>The middle of the doorway, open or shut.</summary>
        public override Vector2 Point => _open ? (Vector2)_shutPos : (Vector2)transform.position;

        private void Awake() => _cols = GetComponents<Collider2D>();

        public override void Interact(GameObject who)
        {
            if (_open) Shut();
            else Open(who ? who.transform.position.x : transform.position.x - 1f);
        }

        /// <summary>Swing open away from <paramref name="fromX"/>.</summary>
        public void Open(float fromX)
        {
            if (_open) return;
            _shutPos = transform.position;
            _shutScale = transform.localScale;
            float side = fromX < _shutPos.x ? 1f : -1f;
            transform.position = _shutPos + Vector3.right * (side * _openOffset);
            transform.localScale = new Vector3(_shutScale.x * _leafScale, _shutScale.y, _shutScale.z);
            foreach (var c in _cols) if (c) c.enabled = false;
            _open = true;
        }

        /// <summary>Shut, if nothing is standing in the doorway.</summary>
        public bool Shut()
        {
            if (!_open) return true;
            if (Blocked()) return false;
            transform.position = _shutPos;
            transform.localScale = _shutScale;
            foreach (var c in _cols) if (c) c.enabled = true;
            _open = false;
            return true;
        }

        private bool Blocked()
        {
            var r = GetComponent<SpriteRenderer>();
            Vector2 size = r && r.sprite ? (Vector2)r.sprite.bounds.size : new Vector2(0.3f, 1.5f);
            size = Vector2.Scale(size, _shutScale) * 0.9f;
            Blockers.Clear();
            Physics2D.OverlapBox(_shutPos, size, transform.eulerAngles.z,
                                 new ContactFilter2D { useTriggers = false }, Blockers);
            foreach (var b in Blockers)
            {
                if (!b || System.Array.IndexOf(_cols, b) >= 0) continue;
                var rb = b.attachedRigidbody;
                if (rb && rb.bodyType == RigidbodyType2D.Dynamic) return true;
            }
            return false;
        }
    }
}
