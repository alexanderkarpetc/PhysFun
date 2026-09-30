using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// A way out of the room: a trigger across the opening. Walk into it and the loader swaps
    /// this room for <see cref="TargetScene"/>, putting you at its <see cref="TargetEntry"/>.
    /// It never shuts and never locks - leaving is always up to you. A doorway with no target
    /// is an opening that does not lead anywhere yet.
    /// </summary>
    [RequireComponent(typeof(BoxCollider2D))]
    public sealed class RoomDoorway : MonoBehaviour
    {
        [Tooltip("Scene name of the room this leads to, e.g. Room_Substation. Empty = not wired yet.")]
        [SerializeField] private string _targetScene;
        [Tooltip("Entry id in the target room. Empty = its first entry.")]
        [SerializeField] private string _targetEntry;

        public string TargetScene => _targetScene;
        public string TargetEntry => _targetEntry;

        private void Reset()
        {
            GetComponent<BoxCollider2D>().isTrigger = true;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            var player = App.Instance.PlayerGo;
            if (!player) return;
            var go = other.attachedRigidbody ? other.attachedRigidbody.gameObject : other.gameObject;
            if (go != player && !go.transform.IsChildOf(player.transform)) return;

            if (string.IsNullOrEmpty(_targetScene))
            {
                Debug.Log($"RoomDoorway '{name}': not wired to a room yet.", this);
                return;
            }
            if (RoomLoader.Instance) RoomLoader.Instance.Go(_targetScene, _targetEntry);
        }

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            var box = GetComponent<BoxCollider2D>();
            if (!box) return;
            Gizmos.color = string.IsNullOrEmpty(_targetScene)
                ? new Color(0.6f, 0.6f, 0.6f, 0.8f)
                : new Color(0.62f, 0.73f, 0.33f, 0.9f);
            Gizmos.matrix = transform.localToWorldMatrix;
            Gizmos.DrawWireCube(box.offset, box.size);
        }
#endif
    }
}
