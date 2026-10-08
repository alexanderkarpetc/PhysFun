using Phys.Terrain;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Rooms
{
    /// <summary>
    /// The root of a room template. A room is a prefab: its own <see cref="TerrainMap"/>, the
    /// <see cref="RoomSocket"/>s corridors may join it by, a <see cref="RoomEntry"/> for when the
    /// floor starts in it, and whatever lives in it - props, enemies - as children. Nothing here
    /// runs the room: you walk in, the enemies are already there.
    ///
    /// The template is the map's rectangle. Everything in the map is stamped into the floor
    /// as is: air, the room's own rock round it, and the fill tile for the rest of the box, so
    /// a room looks the same in its prefab as it does in a floor. A TerrainBuilder on a child
    /// is only there to show and paint the map; <see cref="FloorBuilder"/> strips it, because
    /// the floor builds one terrain out of every room.
    ///
    /// To try one room, drop its prefab into an empty scene and press Play. The room turns
    /// itself off before anything in it wakes, loads the Game scene, and the loader builds a
    /// floor of just that room.
    /// </summary>
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-1000)]
    public sealed class Room : MonoBehaviour
    {
        [Tooltip("This room's terrain. Its origin should be (0, 0): the template's bottom-left " +
                 "corner is then the room's own origin.")]
        [SerializeField] private TerrainMap _map;

        public TerrainMap Map => _map;

        /// <summary>The template rectangle, relative to this object's position.</summary>
        public Rect LocalRect => _map ? _map.LocalBounds : new Rect(0f, 0f, 1f, 1f);

        public RoomSocket[] Sockets => GetComponentsInChildren<RoomSocket>(true);

        private void Awake()
        {
            if (FloorLoader.Instance) return;

            // Play pressed with this room open on its own: keep it as a template, not a level.
            gameObject.SetActive(false);
            if (FloorLoader.GameLoading) return;
            if (!Application.CanStreamedLevelBeLoaded(FloorLoader.GameSceneName))
            {
                Debug.LogWarning($"Room: no '{FloorLoader.GameSceneName}' scene in Build Settings, " +
                                 "so there is nothing to play this room in. Run PhysFun/Rooms/Create Game Scene.",
                    this);
                return;
            }
            FloorLoader.GameLoading = true;
            SceneManager.LoadScene(FloorLoader.GameSceneName, LoadSceneMode.Additive);
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
            var r = LocalRect;
            Gizmos.color = new Color(0.6f, 0.7f, 0.8f, 0.6f);
            Gizmos.DrawWireCube((Vector3)r.center + transform.position, r.size);
        }
#endif
    }
}
