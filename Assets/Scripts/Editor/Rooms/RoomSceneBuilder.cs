using System.Collections.Generic;
using System.IO;
using System.Linq;
using Materials;
using Phys.Terrain;
using Rooms;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace RoomsEditor
{
    /// <summary>
    /// Sets up what the floor system runs on.
    ///
    /// <b>Create Game Scene</b> copies SampleScene to Scenes/Game.unity and strips it down to what
    /// outlasts a floor - camera, player, Binny, HUD - plus a <see cref="FloorLoader"/>. SampleScene
    /// itself is left alone as the free-for-all sandbox it already is.
    ///
    /// <b>Sync Build Settings</b> puts Game first; a room is tried by pressing Play in a scene that
    /// holds it, and that only works with Game in the build.
    ///
    /// <b>New Room</b> makes a blank room prefab to paint: its own map (fill tile all round, a
    /// box of air with a shell of rock), a TerrainBuilder to see and paint it with, a socket on
    /// each side and an entry. Rooms are made by hand from there.
    /// </summary>
    public static class RoomSceneBuilder
    {
        private const string RoomsDir = "Assets/Rooms";
        private const string MapsDir = "Assets/Rooms/Maps";
        private const string SampleScenePath = "Assets/Scenes/SampleScene.unity";
        private const string GameScenePath = "Assets/Scenes/Game.unity";
        private const string RecipePath = "Assets/Rooms/Floor.asset";

        /// <summary>What survives from SampleScene into the Game scene, by root object name.</summary>
        private static readonly HashSet<string> GameKeeps = new()
        {
            "Main Camera", "EventSystem", "UIDocument", "Canvas", "HealthHud", "Player", "Binny",
        };

        [MenuItem("PhysFun/Rooms/Create Game Scene")]
        public static void CreateGameScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (File.Exists(GameScenePath) &&
                !EditorUtility.DisplayDialog("Game scene exists",
                    $"{GameScenePath} already exists. Replace it with a fresh copy of SampleScene?",
                    "Replace", "Cancel"))
                return;

            AssetDatabase.DeleteAsset(GameScenePath);
            if (!AssetDatabase.CopyAsset(SampleScenePath, GameScenePath))
            {
                Debug.LogError($"RoomSceneBuilder: could not copy {SampleScenePath}.");
                return;
            }

            var scene = EditorSceneManager.OpenScene(GameScenePath, OpenSceneMode.Single);
            var removed = new List<string>();
            foreach (var root in scene.GetRootGameObjects())
            {
                if (GameKeeps.Contains(root.name)) continue;
                removed.Add(root.name);
                Object.DestroyImmediate(root);
            }
            var missing = GameKeeps.Where(k => scene.GetRootGameObjects().All(r => r.name != k)).ToList();

            var loader = new GameObject("FloorLoader").AddComponent<FloorLoader>();
            var recipe = AssetDatabase.LoadAssetAtPath<FloorRecipe>(RecipePath);
            if (recipe)
            {
                var so = new SerializedObject(loader);
                so.FindProperty("_recipe").objectReferenceValue = recipe;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            SyncBuildSettings();

            Debug.Log("RoomSceneBuilder: Game scene written. Removed from the copy: " +
                      (removed.Count > 0 ? string.Join(", ", removed) : "nothing") +
                      (missing.Count > 0 ? ". Not found (check names): " + string.Join(", ", missing) : "."));
        }

        [MenuItem("PhysFun/Rooms/Sync Build Settings")]
        public static void SyncBuildSettings()
        {
            var list = new List<EditorBuildSettingsScene>();
            if (File.Exists(GameScenePath)) list.Add(new EditorBuildSettingsScene(GameScenePath, true));
            foreach (var s in EditorBuildSettings.scenes)                      // keep everything else
                if (list.All(l => l.path != s.path) && File.Exists(s.path)) list.Add(s);

            EditorBuildSettings.scenes = list.ToArray();
            Debug.Log("RoomSceneBuilder: Build Settings - " + string.Join(", ", list.Select(s => Path.GetFileNameWithoutExtension(s.path))));
        }

        [MenuItem("PhysFun/Rooms/New Room")]
        public static void NewRoom()
        {
            const float ppu = 40f, size = 18f, shell = 1f, opening = 1.5f;
            if (!AssetDatabase.IsValidFolder(RoomsDir)) AssetDatabase.CreateFolder("Assets", "Rooms");
            if (!AssetDatabase.IsValidFolder(MapsDir)) AssetDatabase.CreateFolder(RoomsDir, "Maps");
            string prefabPath = AssetDatabase.GenerateUniqueAssetPath($"{RoomsDir}/Room_New.prefab");
            string name = Path.GetFileNameWithoutExtension(prefabPath);

            // The map: fill all round, then a shell of room rock, then air inside it.
            var map = ScriptableObject.CreateInstance<TerrainMap>();
            int n = Mathf.RoundToInt(size * ppu);
            map.Resize(Vector2.zero, n, n, ppu);
            byte fill = (byte)map.Require("rock_hard", PhysMaterialId.Default);
            byte rock = (byte)map.Require("rock", PhysMaterialId.Default);
            var cells = map.Cells;
            int s0 = Mathf.RoundToInt(2f * ppu), s1 = n - s0, a0 = s0 + Mathf.RoundToInt(shell * ppu), a1 = n - a0;
            int floorY = a0, stubTop = floorY + Mathf.RoundToInt(opening * ppu);
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                bool inShell = x >= s0 && x < s1 && y >= s0 && y < s1;
                bool inAir = x >= a0 && x < a1 && y >= a0 && y < a1;
                bool stub = y >= floorY && y < stubTop && (x < a0 || x >= a1);
                cells[y * n + x] = inAir || stub ? (byte)0 : inShell ? rock : fill;
            }
            map.Flush();
            AssetDatabase.CreateAsset(map, AssetDatabase.GenerateUniqueAssetPath($"{MapsDir}/{name}_Map.asset"));

            var root = new GameObject(name);
            var room = root.AddComponent<Room>();
            var so = new SerializedObject(room);
            so.FindProperty("_map").objectReferenceValue = map;
            so.ApplyModifiedPropertiesWithoutUndo();

            var terrain = new GameObject("Terrain");
            terrain.transform.SetParent(root.transform, false);
            terrain.AddComponent<TerrainBuilder>().SetMap(map);

            var sockets = new GameObject("Sockets").transform;
            sockets.SetParent(root.transform, false);
            float floor = floorY / ppu, depth = a0 / ppu;
            AddSocket(sockets, "L1", SocketSide.Left, new Vector2(0f, floor), opening, depth);
            AddSocket(sockets, "R1", SocketSide.Right, new Vector2(size, floor), opening, depth);

            var entry = new GameObject("Entry");
            entry.transform.SetParent(root.transform, false);
            entry.transform.localPosition = new Vector2(a0 / ppu + 1.5f, floor);
            entry.AddComponent<RoomEntry>();

            PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            Object.DestroyImmediate(root);
            AssetDatabase.SaveAssets();
            Selection.activeObject = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            Debug.Log($"RoomSceneBuilder: {prefabPath} made. Open it, paint its map with the Terrain " +
                      "Painter, move and add sockets, then add it to the floor recipe.");
        }

        private static void AddSocket(Transform parent, string name, SocketSide side, Vector2 at, float size, float depth)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            var socket = go.AddComponent<RoomSocket>();
            var so = new SerializedObject(socket);
            so.FindProperty("_side").enumValueIndex = (int)side;
            so.FindProperty("_size").floatValue = size;
            so.FindProperty("_depth").floatValue = depth;
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
