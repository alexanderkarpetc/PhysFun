using System.Collections;
using System.Collections.Generic;
using Phys.Fire;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Rooms
{
    /// <summary>
    /// Keeps exactly one room loaded. Lives in the Game scene, which holds everything that
    /// outlasts a room - player, Binny, camera, HUD - and swaps room scenes in and out next to
    /// it: unload the one you are in, load the one you are going to, put the player at its
    /// entry.
    ///
    /// The room scene is made the active scene while it is loaded, so everything spawned during
    /// play - debris, fragments, ragdolls, gore - lands in it and goes when it unloads. The one
    /// thing that must not go with it are the hidden system hosts (~TerrainSupportSystem,
    /// ~PixelSpriteDriver, ~FractureSystem, ~BloodSystem...), which install into whatever
    /// scene is active when they first run; they are moved to the Game scene before an unload.
    ///
    /// F2 opens a room picker, so the Game scene doubles as a sandbox for trying any room.
    /// </summary>
    [DefaultExecutionOrder(-200)]
    public sealed class RoomLoader : MonoBehaviour
    {
        public const string GameSceneName = "Game";
        public const string RoomScenePrefix = "Room_";

        /// <summary>The loader in the Game scene, once it has woken.</summary>
        public static RoomLoader Instance { get; private set; }

        /// <summary>A room asked for the Game scene and it has not arrived yet.</summary>
        public static bool GameLoading { get; internal set; }

        [Tooltip("Room loaded when Play starts in the Game scene. Ignored when a room scene " +
                 "is already open - that one is used instead.")]
        [SerializeField] private string _startRoom = "Room_DryingLoft";
        [SerializeField] private string _startEntry = "";
        [Tooltip("Doorways ignore the player for this long after arriving, so an entry placed " +
                 "near a doorway does not bounce you straight back out.")]
        [SerializeField] private float _arrivalGrace = 0.6f;
        [SerializeField] private KeyCode _menuKey = KeyCode.F2;

        private Scene _current;
        private bool _busy;
        private float _arrivedAt = -10f;
        private bool _menu;
        private readonly List<string> _rooms = new();

        public Scene Current => _current;
        public bool CanLeave => !_busy && Time.time - _arrivedAt > _arrivalGrace;

        private void Awake()
        {
            if (Instance && Instance != this)
            {
                Debug.LogWarning("RoomLoader: a second Game scene was loaded; ignoring it.", this);
                enabled = false;
                return;
            }
            Instance = this;
            GameLoading = false;
            CollectRooms();
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        private IEnumerator Start()
        {
            // Play pressed inside a room scene: that room is already here, adopt it.
            for (int i = 0; i < SceneManager.sceneCount; i++)
            {
                var s = SceneManager.GetSceneAt(i);
                if (s == gameObject.scene || !s.isLoaded || !FindRoom(s)) continue;
                _current = s;
                SceneManager.SetActiveScene(s);
                yield return null;                 // let the room's own Awake/Start run first
                Arrive(_startEntry);
                yield break;
            }

            if (string.IsNullOrEmpty(_startRoom)) yield break;
            if (!Application.CanStreamedLevelBeLoaded(_startRoom))
            {
                Debug.LogWarning($"RoomLoader: start room '{_startRoom}' is not in Build Settings. " +
                                 "Run PhysFun/Rooms/Sync Build Settings, or press " +
                                 $"{_menuKey} to pick another.", this);
                yield break;
            }
            yield return Switch(_startRoom, _startEntry);
        }

        /// <summary>Leave the current room for <paramref name="scene"/>, arriving at the entry
        /// called <paramref name="entry"/> (or its first entry).</summary>
        public void Go(string scene, string entry)
        {
            if (_busy || !CanLeave && _current.IsValid()) return;
            if (!Application.CanStreamedLevelBeLoaded(scene))
            {
                Debug.LogWarning($"RoomLoader: '{scene}' is not in Build Settings. " +
                                 "Run PhysFun/Rooms/Sync Build Settings.", this);
                return;
            }
            StartCoroutine(Switch(scene, entry));
        }

        private IEnumerator Switch(string scene, string entry)
        {
            _busy = true;
            Freeze(true);

            if (_current.IsValid() && _current.isLoaded)
            {
                RescueSystemHosts(_current);
                FlameField.Instance.Clear();       // flames live in world cells, not on objects
                SceneManager.SetActiveScene(gameObject.scene);
                yield return SceneManager.UnloadSceneAsync(_current);
            }

            yield return SceneManager.LoadSceneAsync(scene, LoadSceneMode.Additive);
            _current = SceneManager.GetSceneByName(scene);
            SceneManager.SetActiveScene(_current);
            yield return null;                     // terrain builds in the room's Awake

            Arrive(entry);
            Freeze(false);
            _busy = false;
        }

        private void Arrive(string entryId)
        {
            _arrivedAt = Time.time;
            var room = FindRoom(_current);
            var entry = room ? room.FindEntry(entryId) : null;
            if (!entry)
            {
                Debug.LogWarning($"RoomLoader: room '{_current.name}' has no RoomEntry; " +
                                 "the player stays where it is.", this);
                return;
            }

            var player = App.Instance.PlayerGo;
            if (player) PlaceOnFeet(player, entry.transform.position);

            var binny = FindAnyObjectByType<Binny.BinnyController>();
            if (binny)
                Teleport(binny.gameObject,
                         entry.transform.position + new Vector3(entry.FaceRight ? -0.8f : 0.8f, 1.4f, 0f));

            var cam = Camera.main ? Camera.main.GetComponent<Siege.CameraFollow>() : null;
            if (cam) cam.Snap();
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Moving the persistent bodies
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Stand <paramref name="go"/> with the bottom of its colliders on
        /// <paramref name="feet"/>. The player's pivot is at its chest, not its feet.</summary>
        private static void PlaceOnFeet(GameObject go, Vector3 feet)
        {
            float lift = 0f;
            var cols = go.GetComponentsInChildren<Collider2D>();
            bool any = false;
            Bounds b = default;
            foreach (var c in cols)
            {
                if (c.isTrigger) continue;
                if (!any) { b = c.bounds; any = true; }
                else b.Encapsulate(c.bounds);
            }
            if (any) lift = go.transform.position.y - b.min.y;
            Teleport(go, feet + Vector3.up * (lift + 0.02f));
        }

        private static void Teleport(GameObject go, Vector3 pos)
        {
            pos.z = go.transform.position.z;
            go.transform.position = pos;
            foreach (var rb in go.GetComponentsInChildren<Rigidbody2D>())
            {
                rb.position = rb.transform.position;
                rb.linearVelocity = Vector2.zero;
                rb.angularVelocity = 0f;
            }
        }

        /// <summary>Park the player and Binny while there is no room under them.</summary>
        private static void Freeze(bool frozen)
        {
            var player = App.Instance.PlayerGo;
            if (player) SetSimulated(player, !frozen);
            var binny = FindAnyObjectByType<Binny.BinnyController>();
            if (binny) SetSimulated(binny.gameObject, !frozen);
        }

        private static void SetSimulated(GameObject go, bool on)
        {
            foreach (var rb in go.GetComponentsInChildren<Rigidbody2D>()) rb.simulated = on;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Scene bookkeeping
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Move the hidden, never-saved system hosts out of a scene that is about to unload.
        /// They are created on first use in whichever scene is active, which during play is
        /// the room, and several install only once per play session - losing one would switch
        /// that system off for the rest of the session.
        /// </summary>
        private void RescueSystemHosts(Scene scene)
        {
            foreach (var go in Resources.FindObjectsOfTypeAll<GameObject>())
            {
                if (go.scene != scene || go.transform.parent) continue;
                if ((go.hideFlags & HideFlags.DontSave) == 0) continue;
                SceneManager.MoveGameObjectToScene(go, gameObject.scene);
            }
        }

        private static Room FindRoom(Scene scene)
        {
            if (!scene.IsValid() || !scene.isLoaded) return null;
            foreach (var root in scene.GetRootGameObjects())
            {
                var room = root.GetComponentInChildren<Room>(true);
                if (room) return room;
            }
            return null;
        }

        private void CollectRooms()
        {
            _rooms.Clear();
            for (int i = 0; i < SceneManager.sceneCountInBuildSettings; i++)
            {
                var path = SceneUtility.GetScenePathByBuildIndex(i);
                var name = System.IO.Path.GetFileNameWithoutExtension(path);
                if (name.StartsWith(RoomScenePrefix)) _rooms.Add(name);
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Room picker (F2)
        // ─────────────────────────────────────────────────────────────────────────

        private void Update()
        {
            if (Input.GetKeyDown(_menuKey)) _menu = !_menu;
        }

        private void OnGUI()
        {
            if (!_menu) return;
            float w = 240f, h = 30f + 26f * Mathf.Max(1, _rooms.Count);
            GUILayout.BeginArea(new Rect(12f, 12f, w, h), GUI.skin.box);
            GUILayout.Label($"Room: {(_current.IsValid() ? _current.name : "-")}   ({_menuKey} to close)");
            if (_rooms.Count == 0) GUILayout.Label("No Room_* scenes in Build Settings.");
            foreach (var r in _rooms)
            {
                GUI.enabled = !_busy;
                if (GUILayout.Button(r)) { _menu = false; _arrivedAt = -10f; Go(r, ""); }
                GUI.enabled = true;
            }
            GUILayout.EndArea();
        }
    }
}
