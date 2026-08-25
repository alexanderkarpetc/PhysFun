using Hazards;
using Spawners;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Puts the disposal-line parts in the PhysFun menu, where someone looking for them will
    /// actually look. Each one drops a real object into the open scene at whatever the scene view
    /// is centred on, selected and undoable — the same thing dragging the prefab in would give.
    /// </summary>
    public static class HazardMenu
    {
        private const string ConveyorPrefab = "Assets/Resources/Prefabs/Hazards/Conveyor.prefab";
        private const string GrinderPrefab = "Assets/Resources/Prefabs/Hazards/Grinder.prefab";

        [MenuItem("PhysFun/Create/Conveyor", false, 100)]
        private static void CreateConveyor() => PlacePrefab(ConveyorPrefab, "Create Conveyor");

        [MenuItem("PhysFun/Create/Grinder", false, 101)]
        private static void CreateGrinder() => PlacePrefab(GrinderPrefab, "Create Grinder");

        /// <summary>
        /// The factory has no art of its own, so there is no prefab to place — it is a bare
        /// object with the component on it, parked wherever creatures should come out.
        /// </summary>
        [MenuItem("PhysFun/Create/Enemy Factory", false, 102)]
        private static void CreateFactory()
        {
            var go = new GameObject("EnemyFactory", typeof(EnemyFactory));
            go.transform.position = SceneCentre();

            Undo.RegisterCreatedObjectUndo(go, "Create Enemy Factory");
            Select(go);
        }

        private static void PlacePrefab(string path, string undoLabel)
        {
            var asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (!asset)
            {
                Debug.LogWarning($"[PhysFun] No prefab at {path}.");
                return;
            }

            var go = (GameObject)PrefabUtility.InstantiatePrefab(asset);
            go.transform.position = SceneCentre();

            Undo.RegisterCreatedObjectUndo(go, undoLabel);
            Select(go);
        }

        /// <summary>Where the scene view is looking, flattened onto the play plane.</summary>
        private static Vector3 SceneCentre()
        {
            var view = SceneView.lastActiveSceneView;
            if (!view) return Vector3.zero;

            var p = view.pivot;
            return new Vector3(p.x, p.y, 0f);
        }

        private static void Select(GameObject go)
        {
            Selection.activeGameObject = go;
            EditorGUIUtility.PingObject(go);
        }
    }
}
