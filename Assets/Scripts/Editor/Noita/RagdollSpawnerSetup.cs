using System.IO;
using System.Linq;
using Ragdolls;
using UnityEditor;
using UnityEngine;

namespace NoitaImport
{
    /// <summary>
    /// Bolts a <see cref="RagdollSpawner"/> onto a live creature and wires it to the corpse the
    /// importer built. Matching is by name: an object called "coward" finds
    /// Assets/Resources/Ragdolls/coward/CowardRagdoll.prefab.
    /// </summary>
    public static class RagdollSpawnerSetup
    {
        [MenuItem("PhysFun/Attach Ragdoll Spawner", true)]
        private static bool Validate() => Selection.gameObjects.Length > 0;

        [MenuItem("PhysFun/Attach Ragdoll Spawner")]
        private static void Attach()
        {
            foreach (var go in Selection.gameObjects)
            {
                string path = AssetDatabase.GetAssetPath(go);
                bool isAsset = !string.IsNullOrEmpty(path);

                var target = isAsset ? PrefabUtility.LoadPrefabContents(path) : go;
                try
                {
                    if (Configure(target, go.name))
                    {
                        if (isAsset) PrefabUtility.SaveAsPrefabAsset(target, path);
                        else EditorUtility.SetDirty(target);
                    }
                }
                finally
                {
                    if (isAsset) PrefabUtility.UnloadPrefabContents(target);
                }
            }

            AssetDatabase.SaveAssets();
        }

        private static bool Configure(GameObject root, string creatureName)
        {
            var spawner = root.GetComponent<RagdollSpawner>();
            if (!spawner) spawner = root.AddComponent<RagdollSpawner>();

            var so = new SerializedObject(spawner);

            var renderer = root.GetComponentInChildren<SpriteRenderer>(true);
            if (renderer)
            {
                so.FindProperty("poseSource").objectReferenceValue = renderer;
                so.FindProperty("facingSource").objectReferenceValue = renderer.transform;
            }

            var body = root.GetComponentInChildren<Rigidbody2D>(true);
            if (body) so.FindProperty("body").objectReferenceValue = body;

            var prefab = FindRagdollPrefab(creatureName);
            if (prefab) so.FindProperty("ragdollPrefab").objectReferenceValue = prefab;
            else Debug.LogWarning($"No corpse prefab found for '{creatureName}' — import it first, then assign it by hand.");

            so.ApplyModifiedPropertiesWithoutUndo();
            return true;
        }

        /// <summary>Looks for a corpse prefab whose folder or file name contains the creature name.</summary>
        private static GameObject FindRagdollPrefab(string creatureName)
        {
            string key = creatureName.Replace(" ", "").ToLowerInvariant();

            foreach (var guid in AssetDatabase.FindAssets("t:Prefab Ragdoll"))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                string file = Path.GetFileNameWithoutExtension(path).ToLowerInvariant();
                string dir = Path.GetFileName(Path.GetDirectoryName(path) ?? "").ToLowerInvariant();

                if (!file.EndsWith("ragdoll")) continue;
                if (dir != key && file != key + "ragdoll") continue;

                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab && prefab.GetComponent<Ragdoll>()) return prefab;
            }

            // Fall back to any corpse whose name merely contains the creature, so oddly named
            // enemy prefabs ("Shotgunner", "coward_variant") still find something.
            return AssetDatabase.FindAssets("t:Prefab Ragdoll")
                .Select(AssetDatabase.GUIDToAssetPath)
                .Where(p => Path.GetFileNameWithoutExtension(p).ToLowerInvariant().Contains(key))
                .Select(AssetDatabase.LoadAssetAtPath<GameObject>)
                .FirstOrDefault(p => p && p.GetComponent<Ragdoll>());
        }
    }
}
