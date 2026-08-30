using Props;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Lays out a <see cref="Rope2D"/> by hand in the scene view: drag the dots to route it,
    /// click a + between two of them to bend the route there, click a dot's × to drop it.
    ///
    /// Points say where the rope goes and nothing else — how many links come out of it is the
    /// path length divided by the link length, shown live in the inspector.
    /// </summary>
    [CustomEditor(typeof(Rope2D))]
    public sealed class Rope2DEditor : UnityEditor.Editor
    {
        private const float DotSize = 0.09f;      // all sizes are fractions of the handle size,
        private const float ButtonSize = 0.075f;  // so they stay put on screen as you zoom

        public override void OnInspectorGUI()
        {
            var rope = (Rope2D)target;

            DrawDefaultInspector();

            EditorGUILayout.Space();
            EditorGUILayout.HelpBox(
                $"Path {rope.PathLength():0.00} m → {rope.PlannedLinkCount()} links " +
                $"of {rope.PathLength() / Mathf.Max(1, rope.PlannedLinkCount()):0.00} m.\n" +
                "Drag the dots in the scene to route it. + inserts a point, × removes one.",
                MessageType.None);

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Rebuild"))
                {
                    Undo.RegisterFullObjectHierarchyUndo(rope.gameObject, "Rebuild Rope");
                    rope.Build();
                }
                if (GUILayout.Button("Clear"))
                {
                    Undo.RegisterFullObjectHierarchyUndo(rope.gameObject, "Clear Rope");
                    rope.ClearBuilt();
                }
                if (GUILayout.Button("Straighten"))
                {
                    Undo.RecordObject(rope, "Straighten Rope");
                    Straighten(rope);
                }
            }
        }

        private void OnSceneGUI()
        {
            var rope = (Rope2D)target;
            if (rope.points == null || rope.points.Count < 2) return;

            DrawPath(rope);
            MovePoints(rope);
            InsertButtons(rope);
            DeleteButtons(rope);
        }

        private static void DrawPath(Rope2D rope)
        {
            var path = rope.WorldPath();
            Handles.color = rope.color;
            for (int i = 0; i < path.Count - 1; i++)
                Handles.DrawAAPolyLine(3f, path[i], path[i + 1]);
        }

        private static void MovePoints(Rope2D rope)
        {
            var path = rope.WorldPath();
            for (int i = 0; i < rope.points.Count; i++)
            {
                // An anchored end belongs to its transform, so it is shown but not draggable.
                bool anchored = (i == 0 && rope.anchorA) || (i == rope.points.Count - 1 && rope.anchorB);
                Vector3 world = anchored ? (Vector3)path[i] : rope.transform.TransformPoint(rope.points[i]);

                float size = HandleUtility.GetHandleSize(world);
                Handles.color = anchored ? Color.gray : Color.white;

                if (anchored)
                {
                    Handles.SphereHandleCap(0, world, Quaternion.identity, size * DotSize, EventType.Repaint);
                    continue;
                }

                EditorGUI.BeginChangeCheck();
                Vector3 moved = Handles.FreeMoveHandle(world, size * DotSize, Vector3.zero, Handles.SphereHandleCap);
                if (!EditorGUI.EndChangeCheck()) continue;

                Undo.RecordObject(rope, "Move Rope Point");
                moved.z = rope.transform.position.z;
                rope.points[i] = rope.transform.InverseTransformPoint(moved);
                EditorUtility.SetDirty(rope);
            }
        }

        private static void InsertButtons(Rope2D rope)
        {
            var path = rope.WorldPath();
            Handles.color = new Color(0.4f, 0.9f, 0.5f);

            for (int i = 0; i < path.Count - 1; i++)
            {
                Vector3 mid = (path[i] + path[i + 1]) * 0.5f;
                float size = HandleUtility.GetHandleSize(mid);
                if (!Handles.Button(mid, Quaternion.identity, size * ButtonSize, size * ButtonSize,
                                    Handles.DotHandleCap)) continue;

                Undo.RecordObject(rope, "Add Rope Point");
                rope.points.Insert(i + 1, rope.transform.InverseTransformPoint(mid));
                EditorUtility.SetDirty(rope);
                break;   // the list just changed underfoot
            }
        }

        private static void DeleteButtons(Rope2D rope)
        {
            if (rope.points.Count <= 2) return;   // two points is the least a rope can be
            var path = rope.WorldPath();
            Handles.color = new Color(0.9f, 0.35f, 0.3f);

            for (int i = 1; i < path.Count - 1; i++)   // ends stay: they are what the rope is tied by
            {
                float size = HandleUtility.GetHandleSize(path[i]);
                Vector3 at = path[i] + (Vector2)(Vector3.up + Vector3.right).normalized * size * 0.22f;
                if (!Handles.Button(at, Quaternion.identity, size * ButtonSize * 0.8f,
                                    size * ButtonSize * 0.8f, Handles.DotHandleCap)) continue;

                Undo.RecordObject(rope, "Remove Rope Point");
                rope.points.RemoveAt(i);
                EditorUtility.SetDirty(rope);
                break;
            }
        }

        /// <summary>Throws away the bends and leaves a straight run between the two ends.</summary>
        private static void Straighten(Rope2D rope)
        {
            Vector2 a = rope.points[0];
            Vector2 b = rope.points[^1];
            rope.points.Clear();
            rope.points.Add(a);
            rope.points.Add(b);
            EditorUtility.SetDirty(rope);
        }
    }
}
