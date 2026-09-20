using Phys.Explosions;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Puts a length of fuse in the scene. Two ways, because there are two jobs: a loose cord to
    /// route wherever it is wanted, and a cord attached to the explosive that is already selected
    /// — which is nearly always what is meant by "give that barrel a fuse".
    /// </summary>
    public static class FuseMenu
    {
        [MenuItem("PhysFun/Create/Fuse Cord", false, 110)]
        private static void CreateFuse()
        {
            var go = new GameObject("FuseCord", typeof(FuseCord));
            go.transform.position = SceneCentre();

            Undo.RegisterCreatedObjectUndo(go, "Create Fuse Cord");
            Select(go);
        }

        /// <summary>
        /// Run a cord to the selected explosive. It goes on as a child, so the cord travels with
        /// whatever it is stuck to, and its far end sits on the object while the lit end stands
        /// off to one side where it can be reached.
        /// </summary>
        [MenuItem("PhysFun/Attach Fuse to Selection", false, 111)]
        private static void AttachFuse()
        {
            var boom = Selection.activeGameObject.GetComponentInChildren<Explosive>();
            var host = boom.gameObject;

            var go = new GameObject("FuseCord");
            go.transform.SetParent(host.transform, false);

            // Up off the top of the thing, then a run out to the side: the lit end wants to be
            // somewhere a player can put fire on it without standing on the charge.
            float top = 0.3f;
            var sr = host.GetComponentInChildren<SpriteRenderer>();
            if (sr) top = sr.bounds.extents.y + 0.05f;

            var fuse = go.AddComponent<FuseCord>();
            fuse.points.Clear();
            fuse.points.Add(new Vector2(0f, top + 0.5f));      // the end you light
            fuse.points.Add(new Vector2(0f, top));
            fuse.points.Add(Vector2.zero);                     // the end at the charge
            fuse.targets.Add(boom);

            Undo.RegisterCreatedObjectUndo(go, "Attach Fuse");
            Select(go);
        }

        [MenuItem("PhysFun/Attach Fuse to Selection", true)]
        private static bool CanAttachFuse() =>
            Selection.activeGameObject &&
            Selection.activeGameObject.GetComponentInChildren<Explosive>();

        private static Vector3 SceneCentre()
        {
            var view = SceneView.lastActiveSceneView;
            Vector3 at = view ? view.pivot : Vector3.zero;
            at.z = 0f;
            return at;
        }

        private static void Select(GameObject go)
        {
            Selection.activeGameObject = go;
            EditorGUIUtility.PingObject(go);
        }
    }
}
