using UnityEngine;
using UnityEngine.SceneManagement;

namespace Rooms
{
    /// <summary>
    /// The root of a room scene. A room is one scene - terrain, props and enemies - loaded on
    /// its own next to the persistent Game scene (player, camera, HUD) and unloaded when you
    /// leave; see <see cref="RoomLoader"/>. Nothing here runs the room: you walk in, the
    /// enemies are already there, and there is no clear condition to track.
    ///
    /// Pressing Play with only a room scene open still works: the room notices there is no
    /// Game scene and loads it, and the loader then adopts the room instead of loading its
    /// own start room. That is what lets a room be edited and tried from its own scene.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class Room : MonoBehaviour
    {
        [Tooltip("Where the room sits in world units - normally the terrain map's bounds. " +
                 "Drawn as a gizmo; nothing at runtime depends on it yet.")]
        [SerializeField] private Rect _bounds;

        public Rect Bounds => _bounds;
        public Scene Scene => gameObject.scene;

        private void Awake()
        {
            if (RoomLoader.Instance || RoomLoader.GameLoading) return;
            if (!Application.CanStreamedLevelBeLoaded(RoomLoader.GameSceneName))
            {
                Debug.LogWarning($"Room: no '{RoomLoader.GameSceneName}' scene in Build Settings, " +
                                 "so this room runs without a player. Run PhysFun/Rooms/Create Game Scene.",
                    this);
                return;
            }
            RoomLoader.GameLoading = true;
            SceneManager.LoadScene(RoomLoader.GameSceneName, LoadSceneMode.Additive);
        }

        /// <summary>The entry called <paramref name="id"/>, else the first one, else null.</summary>
        public RoomEntry FindEntry(string id)
        {
            var entries = GetComponentsInChildren<RoomEntry>(true);
            foreach (var e in entries)
                if (!string.IsNullOrEmpty(id) && e.Id == id) return e;
            return entries.Length > 0 ? entries[0] : null;
        }

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.6f, 0.7f, 0.8f, 0.6f);
            Gizmos.DrawWireCube(_bounds.center, _bounds.size);
        }
#endif
    }
}
