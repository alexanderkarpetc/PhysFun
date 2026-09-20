using Phys.Explosions;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Lays a <see cref="FuseCord"/> out by hand in the scene view, the same way
    /// <see cref="Rope2DEditor"/> lays out a rope: drag the dots to route it, click a + between
    /// two of them to bend the route there, click a dot's × to drop it.
    ///
    /// The only number that matters while routing is at the top of the inspector — how long the
    /// cord you have drawn takes to burn. A fuse is a length of time drawn as a line, and it is
    /// hard to guess that from metres.
    /// </summary>
    [CustomEditor(typeof(FuseCord))]
    public sealed class FuseCordEditor : UnityEditor.Editor
    {
        private const float DotSize = 0.09f;
        private const float ButtonSize = 0.075f;

        public override void OnInspectorGUI()
        {
            var fuse = (FuseCord)target;

            DrawDefaultInspector();
            EditorGUILayout.Space();

            EditorGUILayout.HelpBox(
                $"{fuse.PathLength():0.00} m of cord — {fuse.BurnSeconds():0.0} s from end to end.\n" +
                $"Sets off {Wired(fuse)}.\n" +
                "Drag the dots in the scene to route it. + inserts a point, × removes one.",
                MessageType.None);

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Straighten"))
                {
                    Undo.RecordObject(fuse, "Straighten Fuse");
                    Straighten(fuse);
                }

                if (GUILayout.Button("Extend"))
                {
                    Undo.RecordObject(fuse, "Extend Fuse");
                    Extend(fuse);
                }

                if (GUILayout.Button("Snap to explosive"))
                {
                    Undo.RecordObject(fuse, "Wire Fuse");
                    Snap(fuse);
                }
            }
        }

        /// <summary>What the inspector says the thing is wired to, in words rather than in slots.</summary>
        private static string Wired(FuseCord fuse)
        {
            int named = 0;
            foreach (var t in fuse.targets)
                if (t) named++;

            if (named > 0) return named == 1 ? "one named explosive" : $"{named} named explosives";

            return fuse.triggerRadius > 0f
                ? $"whatever explosive is within {fuse.triggerRadius:0.00} m of an end"
                : "nothing — it just burns out";
        }

        private void OnSceneGUI()
        {
            var fuse = (FuseCord)target;
            if (fuse.points == null || fuse.points.Count < 2) return;

            DrawPath(fuse);
            MovePoints(fuse);
            InsertButtons(fuse);
            DeleteButtons(fuse);
        }

        private static void DrawPath(FuseCord fuse)
        {
            var path = fuse.WorldPath();
            Handles.color = fuse.cordColor;
            for (int i = 0; i < path.Count - 1; i++)
                Handles.DrawAAPolyLine(3f, path[i], path[i + 1]);

            // Which end is which matters: the burn starts at one and the bang happens at the
            // other, and on a curled-up cord you cannot tell them apart.
            Handles.color = fuse.tipColor;
            Handles.DrawWireDisc(path[0], Vector3.forward,
                                 HandleUtility.GetHandleSize(path[0]) * 0.08f);
            Handles.color = new Color(1f, 0.4f, 0.15f);
            Handles.DrawWireDisc(path[^1], Vector3.forward,
                                 HandleUtility.GetHandleSize(path[^1]) * 0.08f);
        }

        private static void MovePoints(FuseCord fuse)
        {
            for (int i = 0; i < fuse.points.Count; i++)
            {
                Vector3 world = fuse.transform.TransformPoint(fuse.points[i]);
                float size = HandleUtility.GetHandleSize(world);

                Handles.color = Color.white;
                EditorGUI.BeginChangeCheck();
                Vector3 moved = Handles.FreeMoveHandle(world, size * DotSize, Vector3.zero,
                                                       Handles.SphereHandleCap);
                if (!EditorGUI.EndChangeCheck()) continue;

                Undo.RecordObject(fuse, "Move Fuse Point");
                moved.z = fuse.transform.position.z;
                fuse.points[i] = fuse.transform.InverseTransformPoint(moved);
                EditorUtility.SetDirty(fuse);
            }
        }

        private static void InsertButtons(FuseCord fuse)
        {
            var path = fuse.WorldPath();
            Handles.color = new Color(0.4f, 0.9f, 0.5f);

            for (int i = 0; i < path.Count - 1; i++)
            {
                Vector3 mid = (path[i] + path[i + 1]) * 0.5f;
                float size = HandleUtility.GetHandleSize(mid);
                if (!Handles.Button(mid, Quaternion.identity, size * ButtonSize, size * ButtonSize,
                                    Handles.DotHandleCap)) continue;

                Undo.RecordObject(fuse, "Add Fuse Point");
                fuse.points.Insert(i + 1, fuse.transform.InverseTransformPoint(mid));
                EditorUtility.SetDirty(fuse);
                break;   // the list just changed underfoot
            }
        }

        private static void DeleteButtons(FuseCord fuse)
        {
            if (fuse.points.Count <= 2) return;   // two points is the least a cord can be
            var path = fuse.WorldPath();
            Handles.color = new Color(0.9f, 0.35f, 0.3f);

            for (int i = 1; i < path.Count - 1; i++)   // the ends are what it is lit and wired by
            {
                float size = HandleUtility.GetHandleSize(path[i]);
                Vector3 at = path[i] + (Vector3.up + Vector3.right).normalized * size * 0.22f;
                if (!Handles.Button(at, Quaternion.identity, size * ButtonSize * 0.8f,
                                    size * ButtonSize * 0.8f, Handles.DotHandleCap)) continue;

                Undo.RecordObject(fuse, "Remove Fuse Point");
                fuse.points.RemoveAt(i);
                EditorUtility.SetDirty(fuse);
                break;
            }
        }

        /// <summary>Throws the bends away and leaves a straight run between the two ends.</summary>
        private static void Straighten(FuseCord fuse)
        {
            Vector2 a = fuse.points[0];
            Vector2 b = fuse.points[^1];
            fuse.points.Clear();
            fuse.points.Add(a);
            fuse.points.Add(b);
            EditorUtility.SetDirty(fuse);
        }

        /// <summary>
        /// Another half second of cord on the lit end, carrying on the way the last stretch was
        /// already going. Routing a fuse is mostly asking for more time, so there is a button
        /// for exactly that.
        /// </summary>
        private static void Extend(FuseCord fuse)
        {
            Vector2 a = fuse.points[0];
            Vector2 b = fuse.points.Count > 1 ? fuse.points[1] : a + Vector2.up;
            Vector2 back = (a - b).normalized;
            if (back.sqrMagnitude < 0.0001f) back = Vector2.up;

            fuse.points.Insert(0, a + back * (fuse.burnSpeed * 0.5f));
            EditorUtility.SetDirty(fuse);
        }

        /// <summary>
        /// Put the far end on the nearest explosive and wire it to that one by name, so the cord
        /// keeps working if the thing is later dragged around.
        /// </summary>
        private static void Snap(FuseCord fuse)
        {
            var all = Object.FindObjectsByType<Explosive>(FindObjectsSortMode.None);
            if (all.Length == 0)
            {
                Debug.LogWarning("[FuseCord] No Explosive in the scene to wire to.", fuse);
                return;
            }

            Vector3 tail = fuse.transform.TransformPoint(fuse.points[^1]);
            Explosive best = null;
            float bestDistance = float.MaxValue;

            foreach (var boom in all)
            {
                float d = Vector3.Distance(tail, boom.transform.position);
                if (d >= bestDistance) continue;
                bestDistance = d;
                best = boom;
            }

            if (!best) return;

            fuse.points[^1] = fuse.transform.InverseTransformPoint(best.transform.position);
            if (!fuse.targets.Contains(best)) fuse.targets.Add(best);
            EditorUtility.SetDirty(fuse);
        }
    }
}
