using Spawners;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Buttons for the one thing on <see cref="EnemyFactory"/> that has to be done by hand:
    /// putting creatures in the scene while laying a line out. A context menu would do the same
    /// job, but nobody finds a context menu.
    ///
    /// What the buttons make is a real prefab instance in the open scene — the factory is a
    /// placement tool here, not a preview of one.
    /// </summary>
    [CustomEditor(typeof(EnemyFactory))]
    public sealed class EnemyFactoryEditor : UnityEditor.Editor
    {
        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();

            var factory = (EnemyFactory)target;

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Place in scene", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(
                "Drops real prefab instances at the mouth, right now, into the open scene. " +
                "They are ordinary scene objects afterwards — move them, delete them, save them. " +
                "Play mode picks them up like anything else you dragged in yourself.",
                MessageType.None);

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Drop one")) factory.Drop();
                if (GUILayout.Button("Drop a full batch")) factory.DropBatch();
            }

            if (Application.isPlaying)
                EditorGUILayout.LabelField("Alive", factory.AliveCount.ToString());
        }
    }
}
