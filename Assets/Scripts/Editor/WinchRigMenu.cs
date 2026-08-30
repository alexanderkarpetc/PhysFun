using Props;
using UnityEditor;
using UnityEngine;

namespace Editor
{
    /// <summary>
    /// Drops a working hoist into the scene in one go: headframe, wheel, drum, cable and a
    /// stand-in load, already wired to each other.
    ///
    /// The parts are easy enough to add by hand — it is the wiring between them that is fiddly
    /// and easy to get subtly wrong (hook points in the wrong space, a cable built too short to
    /// pay out, the wheel pointed at nothing). So the rig is built at a known-good geometry:
    /// the load starts at the bottom of its travel, which is the only position where the rope
    /// has enough links in it to cover the whole run.
    /// </summary>
    public static class WinchRigMenu
    {
        private const float WheelRadius = 0.5f;
        private const float Drop = 6f;          // how far below the wheel the load starts
        private const float LoadMass = 60f;

        [MenuItem("PhysFun/Create/Winch Rig", false, 110)]
        private static void CreateWinchRig()
        {
            Vector3 centre = SceneCentre();

            var root = new GameObject("WinchRig");
            root.transform.position = centre;

            // ── Wheel, with the two points where the cable leaves the rim ─────
            var wheel = Child(root, "Wheel", Vector3.zero);
            var wheelRb = wheel.AddComponent<Rigidbody2D>();
            wheelRb.bodyType = RigidbodyType2D.Dynamic;
            wheelRb.gravityScale = 0f;
            wheelRb.angularDamping = 0.05f;

            var wheelCol = wheel.AddComponent<CircleCollider2D>();
            wheelCol.radius = WheelRadius;

            var pin = wheel.AddComponent<HingeJoint2D>();
            pin.autoConfigureConnectedAnchor = false;
            pin.connectedBody = null;
            pin.anchor = Vector2.zero;
            pin.connectedAnchor = wheel.transform.position;

            var exitLoad = Child(wheel, "ExitLoad", new Vector3(-WheelRadius, 0f, 0f));
            var exitDrum = Child(wheel, "ExitDrum", new Vector3(WheelRadius, 0f, 0f));

            var pulley = wheel.AddComponent<PulleyWheel2D>();

            // ── Drum, for show: it spins by however much cable was taken in ───
            var drum = Child(root, "Drum", new Vector3(2f, -0.5f, 0f));

            // ── Stand-in load, parked at the bottom of its travel ─────────────
            var load = Child(root, "Cage", new Vector3(-WheelRadius, -Drop, 0f));
            var loadRb = load.AddComponent<Rigidbody2D>();
            loadRb.useAutoMass = false;
            loadRb.mass = LoadMass;
            load.AddComponent<BoxCollider2D>().size = new Vector2(1.2f, 1.2f);

            var hookLocal = new Vector3(0f, 0.6f, 0f);
            var hook = Child(load, "Hook", hookLocal);

            // The run the cable actually has to cover — rim to hook, not wheel to load.
            float run = Vector2.Distance(exitLoad.transform.position, hook.transform.position);

            // ── The winch itself ──────────────────────────────────────────────
            var winch = root.AddComponent<Winch2D>();
            winch.pulleyA = exitLoad.transform;
            winch.pulleyB = exitDrum.transform;
            winch.loadA = loadRb;
            winch.hookA = hookLocal;              // local to the load, which is what the winch wants
            winch.loadB = null;                   // empty = hoist rather than balance
            winch.cableLength = 0f;               // measured from where the load starts
            winch.motorized = true;
            winch.motorSpeed = 1.2f;
            winch.minLength = 1.2f;
            winch.maxLength = run;                // the cable is only as long as it was built
            winch.breakTension = LoadMass * 9.81f * 2f;   // twice what the load pulls standing still
            winch.drum = drum.transform;
            winch.drumRadius = 0.4f;

            // ── Visible rope along the loaded run ─────────────────────────────
            var ropeGo = Child(root, "Rope", exitLoad.transform.position - centre);
            var rope = ropeGo.AddComponent<Rope2D>();
            rope.anchorA = exitLoad.transform;
            rope.anchorB = hook.transform;
            rope.pinStart = true;
            rope.pinEnd = true;
            rope.points.Clear();
            rope.points.Add(Vector2.zero);
            rope.points.Add(new Vector2(0f, -run));
            rope.maxTension = 0f;                 // it carries no weight; the winch does the breaking
            rope.Build();

            winch.ropeA = rope;

            // Without something driving MotorInput the winch just holds its length, which reads
            // as a rig that does not work. Two keys, replaceable by whatever the level uses.
            root.AddComponent<WinchInput2D>();

            // PulleyWheel2D keeps its fields private, so wire them the way the inspector would.
            var so = new SerializedObject(pulley);
            so.FindProperty("winch").objectReferenceValue = winch;
            so.FindProperty("exitA").objectReferenceValue = exitLoad.transform;
            so.FindProperty("exitB").objectReferenceValue = exitDrum.transform;
            so.FindProperty("radius").floatValue = WheelRadius;
            so.ApplyModifiedPropertiesWithoutUndo();

            Undo.RegisterCreatedObjectUndo(root, "Create Winch Rig");
            Select(root);

            Debug.Log("[PhysFun] Winch rig placed. The cage sits at the bottom of its travel on " +
                      "purpose — that is where the rope is long enough for the whole run. Drive it " +
                      "with E (haul) and Q (pay out), or set winch.MotorInput yourself: " +
                      "+1 hauls in, -1 pays out, 0 brakes.", root);
        }

        private static GameObject Child(GameObject parent, string name, Vector3 localPosition)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent.transform, worldPositionStays: false);
            go.transform.localPosition = localPosition;
            return go;
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
