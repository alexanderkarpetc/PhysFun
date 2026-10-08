using System.Collections;
using System.Collections.Generic;
using Phys.Fire;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Rooms
{
    /// <summary>
    /// Keeps exactly one floor loaded. Lives in the Game scene, which holds everything that
    /// outlasts a floor - player, Binny, camera, HUD - and builds each floor into a scene of
    /// its own made at runtime (<see cref="FloorBuilder"/>): rooms from the recipe, joined by
    /// corridors cut through fill, all one terrain.
    ///
    /// The floor scene is the active scene while it exists, so everything spawned during play
    /// - debris, fragments, ragdolls, gore - lands in it and goes when it unloads. The one
    /// thing that must not go with it are the hidden system hosts (~TerrainSupportSystem,
    /// ~PixelSpriteDriver, ~FractureSystem, ~BloodSystem...), which install into whatever
    /// scene is active when they first run; they are moved to the Game scene before an unload.
    ///
    /// When Play is pressed in a scene holding a <see cref="Room"/> (and no Game scene), the
    /// room switches itself off and loads Game, and the floor is built from that room alone -
    /// that is how a room is tried out on its own.
    ///
    /// F2 opens a menu: a new floor, or the same one again.
    /// </summary>
    [DefaultExecutionOrder(-200)]
    public sealed class FloorLoader : MonoBehaviour
    {
        public const string GameSceneName = "Game";

        /// <summary>The loader in the Game scene, once it has woken.</summary>
        public static FloorLoader Instance { get; private set; }

        /// <summary>A room asked for the Game scene and it has not arrived yet.</summary>
        public static bool GameLoading { get; internal set; }

        [SerializeField] private FloorRecipe _recipe;
        [Tooltip("Seed for the first floor. 0 = a new one every time.")]
        [SerializeField] private int _seed;
        [SerializeField] private KeyCode _menuKey = KeyCode.F2;

        private Scene _floor;
        private bool _busy;
        private bool _menu;
        private int _currentSeed;
        private int _built;
        private readonly List<Room> _testRooms = new();

        private void Awake()
        {
            if (Instance && Instance != this)
            {
                Debug.LogWarning("FloorLoader: a second Game scene was loaded; ignoring it.", this);
                enabled = false;
                return;
            }
            Instance = this;
            GameLoading = false;
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        private IEnumerator Start()
        {
            yield return null;                         // let a room scene finish switching its room off

            foreach (var room in FindObjectsByType<Room>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (room.gameObject.scene != gameObject.scene && !room.gameObject.activeSelf)
                    _testRooms.Add(room);

            if (_testRooms.Count == 0 && !_recipe)
            {
                Debug.LogWarning("FloorLoader: no FloorRecipe assigned and no room open to try.", this);
                yield break;
            }
            yield return Generate(_seed != 0 ? _seed : NewSeed());
        }

        /// <summary>Throw the current floor away and build another from <paramref name="seed"/>.</summary>
        public void Regenerate(int seed)
        {
            if (_busy) return;
            StartCoroutine(Generate(seed));
        }

        private IEnumerator Generate(int seed)
        {
            _busy = true;
            Freeze(true);

            if (_floor.IsValid() && _floor.isLoaded)
            {
                RescueSystemHosts(_floor);
                FlameField.Instance.Clear();           // flames live in world cells, not on objects
                SceneManager.SetActiveScene(gameObject.scene);
                yield return SceneManager.UnloadSceneAsync(_floor);
            }

            _floor = SceneManager.CreateScene($"Floor {++_built}");
            SceneManager.SetActiveScene(_floor);
            _currentSeed = seed;

            var recipe = _recipe ? _recipe : ScriptableObject.CreateInstance<FloorRecipe>();
            var result = FloorBuilder.Build(recipe, PickRooms(new System.Random(seed)), seed);
            yield return null;                         // let the rooms' Start run

            if (result != null) Arrive(result.Start, result.FaceRight);
            Freeze(false);
            _busy = false;
        }

        /// <summary>The rooms for one floor, the start room first: the open room being tried,
        /// or a shuffled draw from the recipe.</summary>
        private List<Room> PickRooms(System.Random rng)
        {
            if (_testRooms.Count > 0) return new List<Room>(_testRooms);

            var pool = new List<Room>();
            foreach (var r in _recipe.Rooms)
                if (r && !pool.Contains(r)) pool.Add(r);
            for (int i = pool.Count - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                (pool[i], pool[j]) = (pool[j], pool[i]);
            }
            if (_recipe.StartRoom && pool.Remove(_recipe.StartRoom)) pool.Insert(0, _recipe.StartRoom);
            if (pool.Count > _recipe.RoomCount) pool.RemoveRange(_recipe.RoomCount, pool.Count - _recipe.RoomCount);
            return pool;
        }

        private static int NewSeed() => Random.Range(1, int.MaxValue);

        private static void Arrive(Vector3 feet, bool faceRight)
        {
            var player = App.Instance.PlayerGo;
            if (player) PlaceOnFeet(player, feet);

            var binny = FindAnyObjectByType<Binny.BinnyController>();
            if (binny) Teleport(binny.gameObject, feet + new Vector3(faceRight ? -0.8f : 0.8f, 1.4f, 0f));

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

        /// <summary>Park the player and Binny while there is no floor under them.</summary>
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

        /// <summary>
        /// Move the hidden, never-saved system hosts out of a scene that is about to unload.
        /// They are created on first use in whichever scene is active, which during play is
        /// the floor, and several install only once per play session - losing one would switch
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

        // ─────────────────────────────────────────────────────────────────────────
        // Menu (F2)
        // ─────────────────────────────────────────────────────────────────────────

        private void Update()
        {
            if (Input.GetKeyDown(_menuKey)) _menu = !_menu;
        }

        private void OnGUI()
        {
            if (!_menu) return;
            GUILayout.BeginArea(new Rect(12f, 12f, 260f, 120f), GUI.skin.box);
            GUILayout.Label($"Floor seed {_currentSeed}   ({_menuKey} to close)");
            if (_testRooms.Count > 0) GUILayout.Label($"Trying room: {_testRooms[0].name}");
            GUI.enabled = !_busy;
            if (GUILayout.Button("New floor")) { _menu = false; Regenerate(NewSeed()); }
            if (GUILayout.Button("Same floor again")) { _menu = false; Regenerate(_currentSeed); }
            GUI.enabled = true;
            GUILayout.EndArea();
        }
    }
}
