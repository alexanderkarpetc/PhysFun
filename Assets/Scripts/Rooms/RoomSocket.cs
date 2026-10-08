using UnityEngine;

namespace Rooms
{
    public enum SocketSide
    {
        Left,
        Right,
        Top,
        Bottom,
    }

    /// <summary>
    /// A place a corridor may join the room. The room's own map already has a short passage
    /// - the stub - running from its air out to the template edge here; when the floor is
    /// built, a corridor is cut on from the stub's mouth to another room's socket, or, if no
    /// corridor uses it, the stub is filled back in with rock.
    ///
    /// The transform sits on the template edge: at the floor of the opening for a side
    /// socket, at the middle of it for a top or bottom one.
    /// </summary>
    public sealed class RoomSocket : MonoBehaviour
    {
        [SerializeField] private SocketSide _side = SocketSide.Left;
        [Tooltip("Width of the opening across the passage, in world units: its height for a " +
                 "side socket, its width for a top or bottom one.")]
        [SerializeField] private float _size = 1.5f;
        [Tooltip("How far the stub runs in from the template edge before it meets the room's " +
                 "air. This much gets filled back in when no corridor uses the socket.")]
        [SerializeField] private float _depth = 2f;

        public SocketSide Side => _side;
        public float Size => _size;
        public float Depth => _depth;

        /// <summary>Unit vector pointing out of the room through this socket.</summary>
        public static Vector2 Outward(SocketSide side) => side switch
        {
            SocketSide.Left => Vector2.left,
            SocketSide.Right => Vector2.right,
            SocketSide.Top => Vector2.up,
            _ => Vector2.down,
        };

        /// <summary>
        /// The stub, in the same space as <paramref name="edge"/> (the socket's point on the
        /// template edge). Padded a little across the passage so filling it back in leaves no
        /// sliver of air along its sides.
        /// </summary>
        public static Rect StubRect(SocketSide side, Vector2 edge, float size, float depth)
        {
            const float pad = 0.15f;
            return side switch
            {
                SocketSide.Left => new Rect(edge.x, edge.y - pad, depth, size + 2f * pad),
                SocketSide.Right => new Rect(edge.x - depth, edge.y - pad, depth, size + 2f * pad),
                SocketSide.Top => new Rect(edge.x - size * 0.5f - pad, edge.y - depth, size + 2f * pad, depth),
                _ => new Rect(edge.x - size * 0.5f - pad, edge.y, size + 2f * pad, depth),
            };
        }

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            var p = (Vector2)transform.position;
            var r = StubRect(_side, p, _size, _depth);
            Gizmos.color = new Color(0.47f, 0.79f, 0.84f, 0.9f);
            Gizmos.DrawWireCube(r.center, r.size);
            Gizmos.DrawLine(p, p + Outward(_side) * 0.8f);
        }
#endif
    }
}
