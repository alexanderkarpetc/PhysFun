using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// Where the player starts when the floor starts in this room. The transform is the
    /// point between the player's feet.
    /// </summary>
    public sealed class RoomEntry : MonoBehaviour
    {
        [SerializeField] private string _id = "start";
        [SerializeField] private bool _faceRight = true;

        public string Id => _id;
        public bool FaceRight => _faceRight;

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.47f, 0.79f, 0.84f);
            var p = transform.position;
            Gizmos.DrawWireCube(p + Vector3.up * 0.45f, new Vector3(0.55f, 0.9f, 0f));
            Gizmos.DrawLine(p + Vector3.up * 0.45f, p + new Vector3(_faceRight ? 0.5f : -0.5f, 0.45f, 0f));
        }
#endif
    }
}
