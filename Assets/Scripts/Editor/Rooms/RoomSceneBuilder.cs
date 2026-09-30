using System.Collections.Generic;
using System.IO;
using System.Linq;
using Rooms;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace RoomsEditor
{
    /// <summary>
    /// Sets up the scenes the room system runs on.
    ///
    /// <b>Create Game Scene</b> copies SampleScene to Scenes/Game.unity and strips it down to what
    /// outlasts a room - camera, player, Binny, HUD - plus a <see cref="RoomLoader"/>. SampleScene
    /// itself is left alone as the free-for-all sandbox it already is.
    ///
    /// <b>Sync Build Settings</b> lists Game first and every scene under Scenes/Rooms after it, so
    /// adding a room is never a trip to the Build Settings window.
    ///
    /// A room scene is made by hand: a root with a <see cref="Room"/>, a TerrainBuilder with the
    /// room's own TerrainMap, at least one <see cref="RoomEntry"/>, and colliders on the
    /// Untouchable layer touching the map's outer rock - the support pass drops any terrain
    /// that is not connected to one.
    /// </summary>
    public static class RoomSceneBuilder
    {
        private const string RoomsDir = "Assets/Scenes/Rooms";
        private const string SampleScenePath = "Assets/Scenes/SampleScene.unity";
        private const string GameScenePath = "Assets/Scenes/Game.unity";

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

            new GameObject("RoomLoader").AddComponent<RoomLoader>();
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

            if (AssetDatabase.IsValidFolder(RoomsDir))
                foreach (var guid in AssetDatabase.FindAssets("t:Scene", new[] { RoomsDir }).OrderBy(AssetDatabase.GUIDToAssetPath))
                    list.Add(new EditorBuildSettingsScene(AssetDatabase.GUIDToAssetPath(guid), true));

            foreach (var s in EditorBuildSettings.scenes)                      // keep everything else
                if (list.All(l => l.path != s.path) && File.Exists(s.path)) list.Add(s);

            EditorBuildSettings.scenes = list.ToArray();
            Debug.Log("RoomSceneBuilder: Build Settings - " + string.Join(", ", list.Select(s => Path.GetFileNameWithoutExtension(s.path))));
        }
    }
}
